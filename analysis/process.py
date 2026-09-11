"""Process milestones, who holds the case over time, and the context of work-item aborts."""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import ACT, CASE, RESOURCE, SYSTEM_RESOURCE, TS

SENT = ("O_Sent (mail and online)", "O_Sent (online only)")
MILESTONES = [
    "A_Create Application", "A_Submitted", "A_Concept", "A_Accepted",
    "O_Create Offer", "O_Sent", "A_Complete", "O_Returned", "A_Validating",
    "A_Incomplete", "A_Pending", "A_Denied", "A_Cancelled",
]
END_EVENTS = ("A_Pending", "A_Denied", "A_Cancelled")
TO_CUSTOMER = SENT + ("A_Incomplete",)
TO_BANK = ("O_Returned", "A_Validating")


def milestone_first_ts(events: pd.DataFrame) -> pd.DataFrame:
    ev = events.assign(milestone=events[ACT].where(~events[ACT].isin(SENT), "O_Sent"))
    ev = ev[ev["milestone"].isin(MILESTONES)]
    wide = ev.groupby([CASE, "milestone"])[TS].min().unstack()
    return wide.reindex(columns=[m for m in MILESTONES if m in wide.columns])


def funnel_by_outcome(first_ts: pd.DataFrame, outcome: pd.Series) -> pd.DataFrame:
    reached = first_ts.notna()
    table = reached.groupby(outcome.reindex(first_ts.index)).sum().T
    table["all"] = reached.sum()
    return table


def last_milestone_before_end(first_ts: pd.DataFrame) -> pd.Series:
    pre = [m for m in first_ts.columns if m not in END_EVENTS]
    reached = first_ts[pre].notna()
    return reached.iloc[:, ::-1].idxmax(axis=1).where(reached.any(axis=1))


def pair_durations(first_ts: pd.DataFrame, pairs: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame({
        f"{a}→{b}": (first_ts[b] - first_ts[a]).dt.total_seconds() / 86400 for a, b in pairs
    })
