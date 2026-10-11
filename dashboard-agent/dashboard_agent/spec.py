"""Spécification d'un dashboard : ce que l'agent décide (KPI, visuels), jamais les chiffres.

Les valeurs sont toujours recalculées par pandas à partir de cette spec, ce qui évite
qu'un chiffre « inventé » par le modèle se retrouve dans le dashboard.
"""

from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

Aggregation = Literal["sum", "mean", "median", "count", "count_distinct", "min", "max"]
TimeGrain = Literal["day", "week", "month", "quarter", "year"]
NumberFormat = Literal["number", "decimal", "currency", "percent"]
ChartType = Literal[
    "line",
    "area",
    "bar",
    "horizontal_bar",
    "stacked_bar",
    "grouped_bar",
    "donut",
    "scatter",
    "histogram",
    "heatmap",
    "table",
]


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Measure(Strict):
    column: Optional[str] = Field(
        None, description="Colonne mesurée. null avec aggregation='count' = nombre de lignes."
    )
    aggregation: Aggregation


class KPI(Strict):
    label: str = Field(description="Libellé court, en casse de phrase, sans deux-points.")
    measure: Measure
    denominator: Optional[Measure] = Field(
        None, description="Si renseigné, le KPI vaut measure / denominator (ex. panier moyen, taux de marge)."
    )
    format: NumberFormat = "number"
    higher_is_better: bool = True
    trend_date_column: Optional[str] = Field(
        None, description="Colonne date pour l'évolution vs période précédente et la sparkline."
    )
    trend_grain: TimeGrain = "month"
    rationale: str = Field(description="Pourquoi ce KPI compte pour le métier (1 phrase).")


class Chart(Strict):
    type: ChartType
    title: str = Field(description="Titre qui énonce la question à laquelle répond le graphique.")
    rationale: str = Field(description="Pourquoi ce type de visuel est le bon pour ces données (1 phrase).")
    dimension: Optional[str] = Field(
        None, description="Axe des catégories ou du temps (x). Requis sauf pour histogram et scatter sans regroupement."
    )
    time_grain: Optional[TimeGrain] = Field(None, description="Obligatoire si dimension est une date.")
    measure: Optional[Measure] = Field(None, description="Valeur affichée (axe y). Pour histogram : la colonne à distribuer.")
    x_measure: Optional[Measure] = Field(None, description="scatter uniquement : mesure en abscisse.")
    series: Optional[str] = Field(
        None, description="Seconde dimension : couleurs de stacked_bar / grouped_bar / line multi-séries, lignes de heatmap."
    )
    top_n: int = Field(10, ge=2, le=30, description="Nombre max de catégories ; le reste est regroupé dans « Autres ».")
    sort: Literal["value_desc", "value_asc", "label"] = "value_desc"
    bins: int = Field(20, ge=5, le=60, description="histogram uniquement.")
    format: NumberFormat = "number"
    width: Literal["half", "full"] = "half"


class Dashboard(Strict):
    title: str
    subtitle: str = Field(description="Une phrase : périmètre des données et public visé.")
    currency: str = Field("EUR", description="Code ISO 4217 utilisé pour le format currency.")
    locale: str = Field("fr-FR", description="Locale BCP 47 pour le formatage des nombres et dates.")
    kpis: list[KPI] = Field(min_length=2, max_length=8)
    charts: list[Chart] = Field(min_length=1, max_length=12)
    insights: list[str] = Field(
        default_factory=list,
        max_length=6,
        description="Constats clés, chacun vérifié avec test_aggregation. Pas de chiffre non vérifié.",
    )


def inline_json_schema(model: type[BaseModel]) -> dict:
    """Schéma JSON sans $ref/$defs, pour un input_schema d'outil autonome."""
    schema = model.model_json_schema()
    defs = schema.pop("$defs", {})

    def resolve(node):
        if isinstance(node, dict):
            if "$ref" in node:
                return resolve(defs[node["$ref"].split("/")[-1]])
            # Retire les annotations "title" de pydantic, pas les propriétés nommées "title".
            return {k: resolve(v) for k, v in node.items() if not (k == "title" and isinstance(v, str))}
        if isinstance(node, list):
            return [resolve(v) for v in node]
        return node

    return resolve(schema)
