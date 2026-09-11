"""Attribute-quality checks run before any analysis relies on a column."""
from __future__ import annotations

import pandas as pd


def attribute_profile(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    n = len(df)
    for col in cols:
        present = col in df.columns
        s = df[col] if present else pd.Series(dtype="object")
        non_null = int(s.notna().sum())
        numeric = pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)
        zero_pct = round(float((s.dropna() == 0).mean()) * 100, 2) if numeric and non_null else None
        rows.append({
            "attribute": col,
            "present": present,
            "dtype": str(s.dtype),
            "non_null": non_null,
            "non_null_pct": round(non_null / n * 100, 2) if n else 0.0,
            "zero_pct": zero_pct,
            "n_unique": int(s.nunique()),
        })
    return pd.DataFrame(rows)


def constant_within_case(df: pd.DataFrame, case_col: str, cols: list[str]) -> pd.Series:
    return (df.groupby(case_col)[cols].nunique(dropna=True) <= 1).all()
