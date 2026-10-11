"""Boucle agentique : Claude explore les données avec des outils puis soumet une spec de dashboard."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Callable, Optional

import anthropic
import pandas as pd
from pydantic import BaseModel, ConfigDict, ValidationError

from .engine import SpecError, column_details, preview_aggregation, validate_spec
from .loader import profile_dataframe
from .prompts import SYSTEM_PROMPT, initial_message
from .spec import Dashboard, Measure, TimeGrain, inline_json_schema

DEFAULT_MODEL = "claude-opus-5-5"
MAX_TURNS = 25
MAX_NUDGES = 2
MAX_STREAM_RETRIES = 2


class AgentError(RuntimeError):
    pass


class ColumnInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    column: str


class AggregationInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    measure: Measure
    denominator: Optional[Measure] = None
    group_by: Optional[str] = None
    time_grain: Optional[TimeGrain] = None
    top_n: int = 15


TOOLS = [
    {
        "name": "get_column_details",
        "description": (
            "Détails d'une colonne : quantiles pour une mesure, top 20 des valeurs pour une "
            "catégorie, nombre de lignes par mois pour une date. Sert à lever une ambiguïté "
            "sur le sens ou la qualité d'une colonne."
        ),
        "eager_input_streaming": True,
        "input_schema": {
            "type": "object",
            "properties": {"column": {"type": "string", "description": "Nom exact de la colonne."}},
            "required": ["column"],
            "additionalProperties": False,
        },
    },
    {
        "name": "test_aggregation",
        "description": (
            "Calcule une agrégation sur les données réelles : valeur globale et, si group_by est "
            "fourni, valeur par groupe (triée décroissante, ou chronologique pour une date). "
            "Sert à vérifier qu'un KPI est plausible et à étayer chaque constat."
        ),
        "eager_input_streaming": True,
        "input_schema": inline_json_schema(AggregationInput),
    },
    {
        "name": "submit_dashboard",
        "description": (
            "Soumet la spécification finale du dashboard. Elle est validée contre les données ; "
            "en cas d'erreur, la liste des problèmes est renvoyée et il faut soumettre à nouveau."
        ),
        "eager_input_streaming": True,
        "input_schema": inline_json_schema(Dashboard),
    },
]


@dataclass
class AgentResult:
    spec: Dashboard
    turns: int
    usage: dict = field(default_factory=dict)


def _short(obj: dict, limit: int = 140) -> str:
    text = json.dumps(obj, ensure_ascii=False)
    return text if len(text) <= limit else text[: limit - 1] + "…"


class DashboardAgent:
    def __init__(
        self,
        client: anthropic.Anthropic | None = None,
        model: str = DEFAULT_MODEL,
        effort: str = "high",
        on_event: Callable[[str], None] = lambda _msg: None,
    ):
        self.client = client or anthropic.Anthropic()
        self.model = model
        self.effort = effort
        self.on_event = on_event

    # ----------------------------------------------------------------- outils

    def _run_tool(self, df: pd.DataFrame, name: str, raw_input) -> tuple[str, bool, Dashboard | None]:
        """Retourne (contenu, is_error, spec finale éventuelle)."""
        try:
            if name == "get_column_details":
                args = ColumnInput.model_validate(raw_input)
                return json.dumps(column_details(df, args.column), ensure_ascii=False), False, None
            if name == "test_aggregation":
                args = AggregationInput.model_validate(raw_input)
                result = preview_aggregation(
                    df, args.measure, args.denominator, args.group_by, args.time_grain, args.top_n
                )
                return json.dumps(result, ensure_ascii=False), False, None
            if name == "submit_dashboard":
                spec = Dashboard.model_validate(raw_input)
                errors = validate_spec(df, spec)
                if errors:
                    return "La spécification a des erreurs :\n- " + "\n- ".join(errors), True, None
                return "Dashboard accepté.", False, spec
            return f"Outil inconnu : {name}", True, None
        except ValidationError as e:
            # Couvre aussi une entrée tronquée ou mal formée (eager_input_streaming).
            return f"Entrée invalide pour {name} : {e}", True, None
        except SpecError as e:
            return str(e), True, None

    # ----------------------------------------------------------------- appel modèle

    def _call(self, messages: list) -> anthropic.types.beta.BetaMessage:
        for attempt in range(MAX_STREAM_RETRIES + 1):
            try:
                with self.client.beta.messages.stream(
                    model=self.model,
                    max_tokens=64000,
                    system=SYSTEM_PROMPT,
                    tools=TOOLS,
                    messages=messages,
                    thinking={"type": "adaptive"},
                    output_config={"effort": self.effort},
                    cache_control={"type": "ephemeral"},
                    # Si un classifieur de sécurité refuse à tort, l'API relance sur un autre modèle.
                    betas=["server-side-fallback-2026-07-01"],
                    fallbacks="default",
                ) as stream:
                    return stream.get_final_message()
            except ValueError:
                # JSON d'outil impossible à parser pendant le streaming : on relance la requête.
                if attempt == MAX_STREAM_RETRIES:
                    raise
                self.on_event("Réponse mal formée, nouvelle tentative…")
        raise AssertionError("unreachable")

    # ----------------------------------------------------------------- boucle

    def run(self, df: pd.DataFrame, file_name: str = "", objective: str | None = None) -> AgentResult:
        profile = profile_dataframe(df, file_name)
        messages: list = [
            {"role": "user", "content": initial_message(json.dumps(profile, ensure_ascii=False, default=str), objective)}
        ]
        usage = {"input_tokens": 0, "output_tokens": 0, "cache_read_input_tokens": 0}
        nudges = 0

        for turn in range(1, MAX_TURNS + 1):
            response = self._call(messages)
            for key in usage:
                usage[key] += getattr(response.usage, key, 0) or 0

            if response.stop_reason == "refusal":
                category = getattr(response.stop_details, "category", None) if response.stop_details else None
                raise AgentError(f"Le modèle a refusé la requête (catégorie : {category}).")
            if response.stop_reason == "max_tokens":
                raise AgentError("Réponse tronquée (max_tokens atteint) ; réessaie avec un effort plus bas.")

            messages.append({"role": "assistant", "content": response.content})
            tool_uses = [b for b in response.content if b.type == "tool_use"]

            if not tool_uses:
                if nudges >= MAX_NUDGES:
                    raise AgentError("Le modèle a terminé sans soumettre de dashboard.")
                nudges += 1
                messages.append({"role": "user", "content": "Appelle maintenant submit_dashboard avec la spécification complète."})
                continue

            results, final = [], None
            for block in tool_uses:
                self.on_event(f"→ {block.name} {_short(block.input) if block.name != 'submit_dashboard' else ''}".rstrip())
                content, is_error, spec = self._run_tool(df, block.name, block.input)
                if is_error:
                    self.on_event(f"  ✗ {content.splitlines()[0][:160]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": content, "is_error": is_error})
                final = final or spec

            if final is not None:
                return AgentResult(spec=final, turns=turn, usage=usage)
            messages.append({"role": "user", "content": results})

        raise AgentError(f"Aucun dashboard valide après {MAX_TURNS} tours.")
