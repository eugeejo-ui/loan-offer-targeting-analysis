"""Load the BPI 2017 event log, caching it as parquet inside this project.

The source XES lives in the sap-btm project and is read-only here: this
module never writes next to it.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import BOOL_ATTRS, CACHE_PARQUET, CASE, CASE_OUTCOMES, OUT_DIR, SOURCE_XES, TS
from segments import amount_band, channel, goal_group, intake_frame

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


def load_population(outcomes_path: Path = CASE_OUTCOMES,
                    cache: Path = CACHE_PARQUET) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Events and outcomes of the Phase 0 analysis population only."""
    oc = pd.read_parquet(outcomes_path)
    oc = oc[oc["in_population"]]
    ev = load_events(cache=cache)
    return ev[ev[CASE].isin(oc.index)], oc


def load_analysis_frame(min_goal_n: int) -> pd.DataFrame:
    """Case-level frame for segment analysis: intake axes, outcome, effort and revenue bases."""
    ev, oc = load_population()
    frame = intake_frame(ev).reindex(oc.index)
    frame["amount_band"] = amount_band(frame["case:RequestedAmount"])
    frame["channel"] = channel(frame)
    frame["goal_group"] = goal_group(frame["case:LoanGoal"], min_goal_n)
    frame["outcome"] = oc["outcome"]
    frame["reached_pending"] = oc["reached_pending"]
    effort = pd.read_parquet(OUT_DIR / "p2_case_effort.parquet")[["effort_hours", "staff_events"]]
    revenue = pd.read_parquet(OUT_DIR / "p3_accepted_offers.parquet")[
        ["r_amount", "r_amount_years", "interest_total"]]
    return frame.join(effort).join(revenue)
