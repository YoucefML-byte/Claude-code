"""Calcul déterministe des KPI et des séries de graphiques à partir d'une spec."""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .loader import infer_role
from .spec import KPI, Chart, Dashboard, Measure

OTHER = "Autres"
GRAIN_FREQ = {"day": "D", "week": "W-MON", "month": "M", "quarter": "Q", "year": "Y"}
NEEDS_DIMENSION = {"line", "area", "bar", "horizontal_bar", "stacked_bar", "grouped_bar", "donut", "heatmap", "table"}
NEEDS_SERIES = {"stacked_bar", "grouped_bar", "heatmap"}
TIME_ONLY = {"line", "area"}
NUMERIC_AGGS = {"sum", "mean", "median"}
AGG_LABELS = {
    "sum": "Total",
    "mean": "Moyenne",
    "median": "Médiane",
    "count": "Nombre",
    "count_distinct": "Nombre distinct",
    "min": "Minimum",
    "max": "Maximum",
}
MAX_DONUT_SLICES = 6
MAX_SERIES = 6
MAX_SCATTER_POINTS = 1500


class SpecError(ValueError):
    """La spec référence des colonnes absentes ou des combinaisons incohérentes."""


# --------------------------------------------------------------------------- validation


def _is_numeric(df: pd.DataFrame, col: str) -> bool:
    return pd.api.types.is_numeric_dtype(df[col]) and not pd.api.types.is_bool_dtype(df[col])


def _is_date(df: pd.DataFrame, col: str) -> bool:
    return pd.api.types.is_datetime64_any_dtype(df[col])


def _check_column(df, col, where, errors) -> bool:
    if col not in df.columns:
        errors.append(f"{where} : colonne inconnue '{col}'. Colonnes disponibles : {list(df.columns)}")
        return False
    return True


def _check_measure(df, m: Measure | None, where: str, errors: list[str]) -> None:
    if m is None:
        errors.append(f"{where} : 'measure' est obligatoire.")
        return
    if m.column is None:
        if m.aggregation != "count":
            errors.append(f"{where} : une colonne est requise pour l'agrégation '{m.aggregation}'.")
        return
    if not _check_column(df, m.column, where, errors):
        return
    if m.aggregation in NUMERIC_AGGS and not _is_numeric(df, m.column):
        errors.append(f"{where} : '{m.aggregation}' exige une colonne numérique, '{m.column}' ne l'est pas.")
    if m.aggregation in {"min", "max"} and not (_is_numeric(df, m.column) or _is_date(df, m.column)):
        errors.append(f"{where} : '{m.aggregation}' exige une colonne numérique ou date.")


def validate_spec(df: pd.DataFrame, spec: Dashboard) -> list[str]:
    errors: list[str] = []
    for i, k in enumerate(spec.kpis):
        where = f"kpis[{i}] « {k.label} »"
        _check_measure(df, k.measure, where, errors)
        if k.denominator:
            _check_measure(df, k.denominator, where + " (denominator)", errors)
        if k.trend_date_column and _check_column(df, k.trend_date_column, where, errors):
            if not _is_date(df, k.trend_date_column):
                errors.append(f"{where} : trend_date_column '{k.trend_date_column}' n'est pas une date.")

    for i, c in enumerate(spec.charts):
        where = f"charts[{i}] « {c.title} » ({c.type})"
        if c.type in NEEDS_DIMENSION and not c.dimension:
            errors.append(f"{where} : 'dimension' est obligatoire pour ce type.")
        if c.type in NEEDS_SERIES and not c.series:
            errors.append(f"{where} : 'series' est obligatoire pour ce type.")
        for col in (c.dimension, c.series):
            if col:
                _check_column(df, col, where, errors)
        dim_ok = c.dimension in df.columns if c.dimension else False
        if dim_ok and _is_date(df, c.dimension) and not c.time_grain:
            errors.append(f"{where} : '{c.dimension}' est une date, précise time_grain.")
        if c.type in TIME_ONLY and dim_ok and not _is_date(df, c.dimension):
            errors.append(f"{where} : line/area sont réservés aux axes temporels ; utilise bar ou horizontal_bar.")
        if c.type == "donut" and dim_ok and _is_date(df, c.dimension):
            errors.append(f"{where} : un donut ne montre pas une évolution ; utilise line ou bar.")
        if c.series and c.type in {"donut", "table", "histogram", "scatter"}:
            errors.append(f"{where} : 'series' n'est pas supporté pour ce type ; retire-le.")
        if c.series and c.series in df.columns and _is_date(df, c.series):
            errors.append(f"{where} : 'series' doit être catégorielle, pas une date.")

        if c.type == "histogram":
            if not c.measure or not c.measure.column:
                errors.append(f"{where} : histogram exige measure.column (colonne numérique).")
            elif _check_column(df, c.measure.column, where, errors) and not _is_numeric(df, c.measure.column):
                errors.append(f"{where} : histogram exige une colonne numérique.")
        elif c.type == "scatter":
            _check_measure(df, c.measure, where + " (y)", errors)
            _check_measure(df, c.x_measure, where + " (x_measure)", errors)
            if not c.dimension:
                for m in (c.measure, c.x_measure):
                    if m and m.column and m.column in df.columns and not _is_numeric(df, m.column):
                        errors.append(f"{where} : scatter sans dimension exige deux colonnes numériques.")
        else:
            _check_measure(df, c.measure, where, errors)
    return errors


# --------------------------------------------------------------------------- calcul


def _clean(x):
    if x is None:
        return None
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.floating, float)):
        return None if math.isnan(x) or math.isinf(x) else float(x)
    return x


def measure_label(m: Measure) -> str:
    if m.column is None:
        return "Nombre de lignes"
    return f"{AGG_LABELS[m.aggregation]} {m.column}"


def measure_value(frame: pd.DataFrame, m: Measure) -> float | None:
    if m.aggregation == "count":
        return float(len(frame) if m.column is None else frame[m.column].count())
    if m.aggregation == "count_distinct":
        return float(frame[m.column].nunique())
    if frame[m.column].dropna().empty:
        return None
    return _clean(getattr(frame[m.column], m.aggregation)())


def grouped(frame: pd.DataFrame, keys, m: Measure, denominator: Measure | None = None) -> pd.Series:
    g = frame.groupby(keys, observed=True, dropna=True, sort=False)
    if m.aggregation == "count":
        out = g.size() if m.column is None else g[m.column].count()
    elif m.aggregation == "count_distinct":
        out = g[m.column].nunique()
    else:
        out = g[m.column].agg(m.aggregation)
    out = out.astype(float)
    if denominator is not None:
        den = grouped(frame, keys, denominator).replace(0, np.nan)
        out = out / den
    return out


def ratio_value(frame: pd.DataFrame, m: Measure, denominator: Measure | None) -> float | None:
    num = measure_value(frame, m)
    if denominator is None:
        return num
    den = measure_value(frame, denominator)
    if num is None or not den:
        return None
    return num / den


def bucket(series: pd.Series, grain: str) -> pd.Series:
    return series.dt.to_period(GRAIN_FREQ[grain]).dt.start_time


def dimension_values(frame: pd.DataFrame, col: str, grain: str | None) -> pd.Series:
    if _is_date(frame, col):
        return bucket(frame[col], grain or "month")
    return frame[col].astype("string")


def _fold(labels: pd.Series, ranking: pd.Series, keep: int) -> pd.Series:
    """Garde les `keep` catégories les plus fortes, regroupe le reste dans « Autres »."""
    if ranking.size <= keep:
        return labels
    top = set(ranking.sort_values(ascending=False).head(keep - 1).index)
    return labels.where(labels.isin(top), OTHER)


def _order(values: pd.Series, sort: str, is_time: bool) -> pd.Series:
    if is_time:
        return values.sort_index()
    if sort == "label":
        ordered = values.sort_index()
    else:
        ordered = values.sort_values(ascending=(sort == "value_asc"))
    if OTHER in ordered.index:  # « Autres » toujours en dernier
        ordered = pd.concat([ordered.drop(OTHER), ordered.loc[[OTHER]]])
    return ordered


def _label(x) -> str:
    return x.strftime("%Y-%m-%d") if isinstance(x, pd.Timestamp) else str(x)


def drop_partial_period(frame: pd.DataFrame, date_col: str, grain: str) -> tuple[pd.DataFrame, str | None]:
    """Retire la dernière période si elle n'est pas terminée (ex. mois en cours).

    Comparer un mois entamé à un mois complet donne une fausse chute.
    """
    if frame.empty:
        return frame, None
    periods = frame[date_col].dt.to_period(GRAIN_FREQ[grain])
    last = periods.max()
    if frame[date_col].max() < last.end_time.normalize():
        return frame.loc[periods != last], _label(last.start_time)
    return frame, None


def compute_kpi(df: pd.DataFrame, kpi: KPI) -> dict:
    out = {
        "label": kpi.label,
        "rationale": kpi.rationale,
        "format": kpi.format,
        "higher_is_better": kpi.higher_is_better,
        "value": ratio_value(df, kpi.measure, kpi.denominator),
        "delta_pct": None,
        "current_period": None,
        "previous_period": None,
        "trend": [],
        "trend_grain": kpi.trend_grain,
    }
    if not kpi.trend_date_column:
        return out

    frame = df.loc[df[kpi.trend_date_column].notna()]
    frame, _ = drop_partial_period(frame, kpi.trend_date_column, kpi.trend_grain)
    if frame.empty:
        return out
    frame = frame.assign(_period=frame[kpi.trend_date_column].dt.to_period(GRAIN_FREQ[kpi.trend_grain]))
    by_period = grouped(frame, "_period", kpi.measure, kpi.denominator).sort_index().dropna()
    tail = by_period.tail(12)
    out["trend"] = [{"period": _label(p.start_time), "value": _clean(v)} for p, v in tail.items()]
    if len(by_period) >= 2:
        cur, prev = by_period.iloc[-1], by_period.iloc[-2]
        out["current_period"] = _label(by_period.index[-1].start_time)
        out["previous_period"] = _label(by_period.index[-2].start_time)
        if prev:
            out["delta_pct"] = _clean((cur - prev) / abs(prev))
    return out


def compute_chart(df: pd.DataFrame, chart: Chart) -> dict:
    out = {
        "type": chart.type,
        "title": chart.title,
        "rationale": chart.rationale,
        "width": chart.width,
        "format": chart.format,
        "time_grain": None,
        "value_label": measure_label(chart.measure) if chart.measure else None,
    }

    if chart.type == "histogram":
        values = df[chart.measure.column].dropna().astype(float)
        counts, edges = np.histogram(values, bins=chart.bins)
        out.update(
            labels=[[_clean(edges[i]), _clean(edges[i + 1])] for i in range(len(counts))],
            datasets=[{"label": "Nombre de lignes", "data": [int(c) for c in counts]}],
            value_label=chart.measure.column,
        )
        return out

    if chart.type == "scatter":
        return _scatter(df, chart, out)

    frame = df.copy()
    is_time = _is_date(frame, chart.dimension)
    if is_time:
        out["time_grain"] = chart.time_grain
        frame = frame.loc[frame[chart.dimension].notna()]
        frame, out["partial_period_excluded"] = drop_partial_period(frame, chart.dimension, chart.time_grain)
    frame["_dim"] = dimension_values(frame, chart.dimension, chart.time_grain)
    # Un tableau classé montre le vrai top N (sans « Autres ») ; les parts restent calculées sur le total.
    if not is_time and chart.type != "table":
        keep = min(chart.top_n, MAX_DONUT_SLICES) if chart.type == "donut" else chart.top_n
        frame["_dim"] = _fold(frame["_dim"], grouped(frame, "_dim", chart.measure), keep)

    if not chart.series:
        values = _order(grouped(frame, "_dim", chart.measure), chart.sort, is_time)
        total = values.sum()
        if chart.type == "table":
            values = values.head(chart.top_n)
        out["labels"] = [_label(x) for x in values.index]
        out["datasets"] = [{"label": out["value_label"], "data": [_clean(v) for v in values]}]
        if chart.type in {"donut", "table"} and chart.measure.aggregation in {"sum", "count"}:
            out["shares"] = [_clean(v / total) if total else None for v in values]
        return out

    max_series = chart.top_n if chart.type == "heatmap" else MAX_SERIES
    frame["_series"] = frame[chart.series].astype("string")
    frame["_series"] = _fold(frame["_series"], grouped(frame, "_series", chart.measure), max_series)
    pivot = grouped(frame, ["_dim", "_series"], chart.measure).unstack("_series")

    dim_totals = _order(grouped(frame, "_dim", chart.measure), chart.sort, is_time)
    pivot = pivot.reindex(dim_totals.index)
    series_order = grouped(frame, "_series", chart.measure).sort_values(ascending=False).index.tolist()
    if OTHER in series_order:
        series_order = [s for s in series_order if s != OTHER] + [OTHER]
    pivot = pivot[series_order]

    out["labels"] = [_label(x) for x in pivot.index]
    out["datasets"] = [
        {"label": str(s), "data": [_clean(v) for v in pivot[s].tolist()]} for s in pivot.columns
    ]
    return out


def _scatter(df: pd.DataFrame, chart: Chart, out: dict) -> dict:
    x_m, y_m = chart.x_measure, chart.measure
    out.update(x_label=measure_label(x_m) if chart.dimension else x_m.column,
               value_label=measure_label(y_m) if chart.dimension else y_m.column)
    if chart.dimension:
        frame = df.assign(_dim=dimension_values(df, chart.dimension, chart.time_grain))
        xs, ys = grouped(frame, "_dim", x_m), grouped(frame, "_dim", y_m)
        points = [
            {"x": _clean(xs[k]), "y": _clean(ys[k]), "label": _label(k)}
            for k in xs.index
            if pd.notna(xs[k]) and pd.notna(ys[k])
        ]
    else:
        pts = df[[x_m.column, y_m.column]].dropna()
        if len(pts) > MAX_SCATTER_POINTS:
            pts = pts.sample(MAX_SCATTER_POINTS, random_state=0)
        points = [{"x": _clean(x), "y": _clean(y)} for x, y in pts.itertuples(index=False)]
    out["datasets"] = [{"label": chart.title, "data": points}]
    return out


def compute_dashboard(df: pd.DataFrame, spec: Dashboard) -> dict:
    errors = validate_spec(df, spec)
    if errors:
        raise SpecError("\n".join(errors))
    return {
        "title": spec.title,
        "subtitle": spec.subtitle,
        "currency": spec.currency,
        "locale": spec.locale,
        "rows": int(len(df)),
        "kpis": [compute_kpi(df, k) for k in spec.kpis],
        "charts": [compute_chart(df, c) for c in spec.charts],
        "insights": spec.insights,
    }


# --------------------------------------------------------------------------- outils de l'agent


def column_details(df: pd.DataFrame, column: str) -> dict:
    if column not in df.columns:
        raise SpecError(f"Colonne inconnue '{column}'. Colonnes : {list(df.columns)}")
    s = df[column]
    role = infer_role(s)
    info = {"column": column, "role": role, "non_null": int(s.notna().sum()), "distinct": int(s.nunique())}
    if role == "numeric":
        q = s.quantile([0, 0.05, 0.25, 0.5, 0.75, 0.95, 1]).round(4)
        info["quantiles"] = {f"p{int(k * 100)}": _clean(v) for k, v in q.items()}
        info["zeros_pct"] = round(100 * float((s == 0).mean()), 1)
    elif role == "datetime":
        per_month = s.dropna().dt.to_period("M").value_counts().sort_index()
        info["rows_per_month"] = {str(k): int(v) for k, v in per_month.items()}
    else:
        vc = s.astype("string").value_counts().head(20)
        info["top_values"] = {str(k): int(v) for k, v in vc.items()}
    return info


def preview_aggregation(
    df: pd.DataFrame,
    measure: Measure,
    denominator: Measure | None = None,
    group_by: str | None = None,
    time_grain: str | None = None,
    top_n: int = 15,
) -> dict:
    errors: list[str] = []
    _check_measure(df, measure, "measure", errors)
    if denominator:
        _check_measure(df, denominator, "denominator", errors)
    if group_by:
        _check_column(df, group_by, "group_by", errors)
    if errors:
        raise SpecError("\n".join(errors))

    result = {"overall": ratio_value(df, measure, denominator)}
    if group_by:
        is_time = _is_date(df, group_by)
        frame = df.assign(_dim=dimension_values(df, group_by, time_grain))
        values = grouped(frame, "_dim", measure, denominator)
        values = values.sort_index() if is_time else values.sort_values(ascending=False)
        result["groups_total"] = int(values.size)
        values = values.tail(top_n) if is_time else values.head(top_n)
        result["groups"] = [{"label": _label(k), "value": _clean(v)} for k, v in values.items()]
    return result
