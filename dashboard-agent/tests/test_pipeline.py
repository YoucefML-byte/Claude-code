import json
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
import pytest

from dashboard_agent.agent import TOOLS, DashboardAgent
from dashboard_agent.engine import OTHER, compute_chart, compute_dashboard, compute_kpi, validate_spec
from dashboard_agent.loader import load_table, normalize_types, profile_dataframe
from dashboard_agent.render import render_html
from dashboard_agent.spec import KPI, Chart, Dashboard, Measure

EXAMPLES = Path(__file__).resolve().parent.parent / "examples"


@pytest.fixture(scope="module")
def df():
    return load_table(EXAMPLES / "ventes.csv")


@pytest.fixture(scope="module")
def spec():
    return Dashboard.model_validate_json((EXAMPLES / "ventes.spec.json").read_text(encoding="utf-8"))


def test_french_csv_types_are_parsed(df):
    assert pd.api.types.is_datetime64_any_dtype(df["date_commande"])
    assert pd.api.types.is_float_dtype(df["chiffre_affaires"])
    roles = {c["name"]: c["role"] for c in profile_dataframe(df)["columns"]}
    assert roles["commande_id"] == "identifier"
    assert roles["client_id"] == "identifier"
    assert roles["region"] == "categorical"
    assert roles["marge"] == "numeric"


def test_normalize_handles_spaces_and_percent():
    raw = pd.DataFrame({"montant": ["1 234,50", "12,00", None], "taux": ["12,5 %", "3 %", "0 %"]})
    out = normalize_types(raw)
    assert out["montant"].tolist()[:2] == [1234.5, 12.0]
    assert out["taux"].tolist() == [12.5, 3.0, 0.0]


def test_example_spec_is_valid(df, spec):
    assert validate_spec(df, spec) == []
    data = compute_dashboard(df, spec)
    json.dumps(data)  # sérialisable (pas de NaN numpy / pd.NA)
    assert len(data["kpis"]) == len(spec.kpis)


def test_validation_reports_bad_columns_and_types(df, spec):
    bad = spec.model_copy(deep=True)
    bad.kpis[0].measure = Measure(column="inexistante", aggregation="sum")
    bad.charts[1].measure = Measure(column="region", aggregation="sum")
    bad.charts[0].time_grain = None
    errors = validate_spec(df, bad)
    assert any("inexistante" in e for e in errors)
    assert any("numérique" in e for e in errors)
    assert any("time_grain" in e for e in errors)


def test_partial_last_month_is_excluded(df):
    # Les données s'arrêtent le 17/09/2025 : septembre ne doit pas être comparé à août.
    kpi = KPI(label="CA", measure=Measure(column="chiffre_affaires", aggregation="sum"),
              trend_date_column="date_commande", rationale="r")
    out = compute_kpi(df, kpi)
    assert out["current_period"] == "2025-08-01"
    chart = Chart(type="line", title="t", rationale="r", dimension="date_commande", time_grain="month",
                  measure=Measure(column="chiffre_affaires", aggregation="sum"))
    c = compute_chart(df, chart)
    assert c["labels"][-1] == "2025-08-01"
    assert c["partial_period_excluded"] == "2025-09-01"


def test_ratio_kpi_is_ratio_of_sums(df):
    kpi = KPI(label="Taux de marge", measure=Measure(column="marge", aggregation="sum"),
              denominator=Measure(column="chiffre_affaires", aggregation="sum"), rationale="r")
    expected = df["marge"].sum() / df["chiffre_affaires"].sum()
    assert compute_kpi(df, kpi)["value"] == pytest.approx(expected)


def test_top_n_folds_into_other_with_correct_total(df):
    chart = Chart(type="horizontal_bar", title="t", rationale="r", dimension="produit", top_n=5,
                  measure=Measure(column="chiffre_affaires", aggregation="sum"))
    c = compute_chart(df, chart)
    assert len(c["labels"]) == 5 and c["labels"][-1] == OTHER
    assert sum(c["datasets"][0]["data"]) == pytest.approx(df["chiffre_affaires"].sum())


def test_html_escapes_script_injection(df, spec):
    evil = spec.model_copy(deep=True)
    evil.title = "</script><script>alert(1)</script>"
    html = render_html(compute_dashboard(df, evil))
    assert "</script><script>alert(1)" not in html


def test_tool_schemas_have_no_refs():
    for tool in TOOLS:
        assert "$ref" not in json.dumps(tool["input_schema"])


# ------------------------------------------------------------------ boucle agent (faux client)


class FakeStream:
    def __init__(self, message):
        self.message = message

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def get_final_message(self):
        return self.message


class FakeClient:
    def __init__(self, scripted):
        self.scripted = list(scripted)
        self.requests = []
        self.beta = SimpleNamespace(messages=SimpleNamespace(stream=self._stream))

    def _stream(self, **kwargs):
        self.requests.append(dict(kwargs, messages=list(kwargs["messages"])))  # instantané
        return FakeStream(self.scripted.pop(0))


def tool_call(name, payload, id_):
    return SimpleNamespace(
        stop_reason="tool_use",
        stop_details=None,
        usage=SimpleNamespace(input_tokens=10, output_tokens=5, cache_read_input_tokens=0),
        content=[SimpleNamespace(type="tool_use", id=id_, name=name, input=payload)],
    )


def test_agent_loop_recovers_from_invalid_spec(df, spec):
    good = json.loads(spec.model_dump_json())
    bad = json.loads(spec.model_dump_json())
    bad["charts"][0]["dimension"] = "colonne_fantome"
    client = FakeClient([
        tool_call("test_aggregation", {"measure": {"column": "chiffre_affaires", "aggregation": "sum"},
                                       "group_by": "region"}, "t1"),
        tool_call("submit_dashboard", bad, "t2"),
        tool_call("submit_dashboard", good, "t3"),
    ])
    result = DashboardAgent(client=client).run(df, "ventes.csv")

    assert result.turns == 3
    assert result.spec.title == spec.title
    # L'erreur de validation a bien été renvoyée au modèle pour qu'il corrige.
    last_user = client.requests[2]["messages"][-1]["content"][0]
    assert last_user["is_error"] and "colonne_fantome" in last_user["content"]
    # Réglages API attendus.
    req = client.requests[0]
    assert req["model"] == "claude-opus-5-5" and req["fallbacks"] == "default"
