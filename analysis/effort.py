"""Hands-on effort per case, measured as active time on workflow items (P5)."""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, LIFECYCLE, RESOURCE, SYSTEM_RESOURCE, TS

ACTIVE_FROM = ("start", "resume")


def active_segments(events: pd.DataFrame) -> pd.DataFrame:
    """One row per active stretch of a W_ item: from start/resume to the item's next event."""
    w = events[events[ACT].str.startswith("W_")].sort_values([CASE, ACT, TS], kind="stable")
    g = w.groupby([CASE, ACT], sort=False)
    seg = w.assign(end_ts=g[TS].shift(-1), end_lifecycle=g[LIFECYCLE].shift(-1))
    seg = seg[seg[LIFECYCLE].isin(ACTIVE_FROM) & seg["end_ts"].notna()]
    seg = seg.rename(columns={TS: "start_ts"})[[CASE, ACT, RESOURCE, "start_ts", "end_ts", "end_lifecycle"]]
    seg["hours"] = (seg["end_ts"] - seg["start_ts"]).dt.total_seconds() / 3600
    return seg.reset_index(drop=True)


def activity_caps(segments: pd.DataFrame, q: float = 0.99) -> pd.Series:
    return segments.groupby(ACT)["hours"].quantile(q)


def cap_hours(segments: pd.DataFrame, cap: float | pd.Series) -> pd.Series:
    limit = segments[ACT].map(cap) if isinstance(cap, pd.Series) else cap
    return segments["hours"].clip(upper=limit)


def case_effort(segments: pd.DataFrame, hours: pd.Series, cases: pd.Index) -> pd.DataFrame:
    """Total and per-activity effort hours per case; cases without work items get zero."""
    by_act = hours.groupby([segments[CASE], segments[ACT]]).sum().unstack(fill_value=0.0)
    by_act = by_act.reindex(cases, fill_value=0.0)
    by_act.insert(0, "effort_hours", by_act.sum(axis=1))
    return by_act


def staff_event_counts(events: pd.DataFrame, cases: pd.Index) -> pd.Series:
    staff = events[events[RESOURCE] != SYSTEM_RESOURCE]
    return staff.groupby(CASE).size().reindex(cases, fill_value=0).rename("staff_events")
