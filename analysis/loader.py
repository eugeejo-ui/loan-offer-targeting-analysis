"""Load the BPI 2017 event log, caching it as parquet inside this project.

The source XES lives in the sap-btm project and is read-only here: this
module never writes next to it.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import BOOL_ATTRS, CACHE_PARQUET, SOURCE_XES, TS

_BOOL_MAP = {True: True, False: False, "true": True, "false": False}


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df[TS] = pd.to_datetime(df[TS], utc=True)
    for col in BOOL_ATTRS:
        if col in df.columns:
            df[col] = df[col].map(_BOOL_MAP).astype("boolean")
    return df


def load_events(source: Path = SOURCE_XES, cache: Path = CACHE_PARQUET) -> pd.DataFrame:
    if cache.exists():
        return pd.read_parquet(cache)
    if not source.exists():
        raise FileNotFoundError(f"Neither cache {cache} nor source {source} exists")

    import pm4py  # imported lazily: parsing is only needed once

    log = pm4py.read_xes(str(source))
    if not isinstance(log, pd.DataFrame):
        log = pm4py.convert_to_dataframe(log)
    log = _normalize(log)
    cache.parent.mkdir(parents=True, exist_ok=True)
    log.to_parquet(cache, index=False)
    return log
