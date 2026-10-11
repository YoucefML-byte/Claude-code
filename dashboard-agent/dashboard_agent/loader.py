"""Chargement d'un fichier de données et profilage des colonnes."""

from __future__ import annotations

import re
from pathlib import Path

import pandas as pd

ID_NAME_PATTERN = re.compile(r"(^|_|\b)(id|uuid|code|ref|reference|num|numero|key)($|_|\b)", re.I)


def load_table(path: str | Path, sheet: str | int | None = None) -> pd.DataFrame:
    """Charge CSV / TSV / Excel / JSON / Parquet et normalise les types."""
    path = Path(path)
    suffix = path.suffix.lower()
    if suffix in {".csv", ".txt"}:
        # sep=None laisse pandas détecter ',', ';' ou tabulation (CSV « à la française »).
        df = pd.read_csv(path, sep=None, engine="python", encoding_errors="replace")
    elif suffix == ".tsv":
        df = pd.read_csv(path, sep="\t")
    elif suffix in {".xlsx", ".xlsm", ".xls"}:
        df = pd.read_excel(path, sheet_name=sheet if sheet is not None else 0)
    elif suffix == ".json":
        df = pd.read_json(path)
    elif suffix == ".parquet":
        df = pd.read_parquet(path)
    else:
        raise ValueError(f"Format non supporté : {suffix} (attendu : csv, tsv, xlsx, json, parquet)")

    df.columns = [str(c).strip() for c in df.columns]
    df = df.dropna(axis=1, how="all")
    return normalize_types(df)


def normalize_types(df: pd.DataFrame) -> pd.DataFrame:
    """Convertit les colonnes texte qui sont en réalité des nombres ou des dates."""
    df = df.copy()
    for col in df.columns:
        s = df[col]
        # pandas >= 3 utilise un dtype "str" dédié, les versions antérieures "object".
        if not (s.dtype == object or pd.api.types.is_string_dtype(s)):
            continue
        non_null = s.dropna().astype(str).str.strip()
        if non_null.empty:
            continue

        # Nombres au format français : "1 234,56" ou "12,5 %"
        as_num = _parse_numbers(s)
        if as_num.notna().sum() >= 0.95 * len(non_null):
            df[col] = as_num
            continue

        # Dates : on n'essaie que si les valeurs contiennent des séparateurs de date.
        if non_null.str.contains(r"\d{1,4}[-/.]\d{1,2}[-/.]\d{1,4}", regex=True).mean() >= 0.9:
            sample = non_null.iloc[0]
            dayfirst = bool(re.match(r"^\d{1,2}[/.-]\d{1,2}[/.-]\d{4}", sample))
            as_date = pd.to_datetime(s, errors="coerce", dayfirst=dayfirst, format="mixed")
            if as_date.notna().sum() >= 0.9 * s.notna().sum():
                df[col] = as_date
    return df


def _parse_numbers(s: pd.Series) -> pd.Series:
    cleaned = s.astype("string").str.strip()
    for token in ("\u00a0", "\u202f", " ", "€", "%"):
        cleaned = cleaned.str.replace(token, "", regex=False)
    parsed = pd.to_numeric(cleaned.str.replace(",", ".", regex=False), errors="coerce")
    return parsed.astype("float64")  # évite les dtypes nullables (pd.NA) en aval


def infer_role(s: pd.Series) -> str:
    """Rôle analytique d'une colonne : numeric, datetime, boolean, categorical, identifier, text."""
    name = str(s.name)
    non_null = s.dropna()
    n = len(non_null)
    distinct = non_null.nunique()
    if pd.api.types.is_bool_dtype(s) or (distinct == 2 and set(map(str, non_null.unique())) <= {"0", "1", "True", "False", "oui", "non", "Oui", "Non"}):
        return "boolean"
    if pd.api.types.is_datetime64_any_dtype(s):
        return "datetime"
    if ID_NAME_PATTERN.search(name) and distinct > 50:
        return "identifier"
    if pd.api.types.is_numeric_dtype(s):
        if pd.api.types.is_integer_dtype(s) and n and distinct / n > 0.98 and distinct > 50:
            return "identifier"
        return "numeric"
    # Texte
    avg_len = non_null.astype(str).str.len().mean() if n else 0
    if avg_len > 40 and n and distinct / n > 0.5:
        return "text"
    if n and distinct / n > 0.9 and distinct > 100:
        return "identifier"
    return "categorical"


def _num(x) -> float | int | None:
    if x is None or pd.isna(x):
        return None
    x = float(x)
    return int(x) if x.is_integer() else round(x, 4)


def profile_column(s: pd.Series, top: int = 5) -> dict:
    role = infer_role(s)
    non_null = s.dropna()
    info: dict = {
        "name": str(s.name),
        "role": role,
        "dtype": str(s.dtype),
        "null_pct": round(100 * (1 - len(non_null) / len(s)), 1) if len(s) else 0.0,
        "distinct": int(non_null.nunique()),
    }
    if role == "numeric":
        info.update(
            min=_num(non_null.min()),
            max=_num(non_null.max()),
            mean=_num(non_null.mean()),
            median=_num(non_null.median()),
            sum=_num(non_null.sum()),
            negative_values=bool((non_null < 0).any()),
        )
    elif role == "datetime":
        info.update(
            min=str(non_null.min().date()) if len(non_null) else None,
            max=str(non_null.max().date()) if len(non_null) else None,
            span_days=int((non_null.max() - non_null.min()).days) if len(non_null) else 0,
        )
    elif role in {"categorical", "boolean"}:
        vc = non_null.astype(str).value_counts()
        info["top_values"] = {k: int(v) for k, v in vc.head(top).items()}
    else:
        info["examples"] = [str(v)[:60] for v in non_null.head(3)]
    return info


def profile_dataframe(df: pd.DataFrame, file_name: str = "") -> dict:
    """Profil compact envoyé au modèle : il ne voit jamais les données brutes en entier."""
    return {
        "file": file_name,
        "rows": int(len(df)),
        "columns": [profile_column(df[c]) for c in df.columns],
        "sample_rows": df.head(5).astype(str).to_dict(orient="records"),
    }
