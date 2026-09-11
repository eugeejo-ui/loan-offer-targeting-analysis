"""Case outcome classification and the observation-window cutoff (P4).

A case's outcome is the label of its LAST end event; the full ordered
sequence of end events is kept in `end_pattern` so cases with more than
one end event stay visible rather than silently resolved.
"""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, END_LABELS, TS

CREATE_APPLICATION = "A_Create Application"


def case_outcomes(events: pd.DataFrame) -> pd.DataFrame:
    ev = events.sort_values([CASE, TS], kind="stable")
    first_ts = ev.groupby(CASE)[TS].min()
    created_ts = ev[ev[ACT] == CREATE_APPLICATION].groupby(CASE)[TS].min()

    ends = ev[ev[ACT].isin(END_LABELS)]
    last_end = ends.groupby(CASE).tail(1).set_index(CASE)

    out = pd.DataFrame(index=first_ts.index)
    out["submit_ts"] = created_ts.reindex(out.index).combine_first(first_ts)
    out["end_pattern"] = ends.groupby(CASE)[ACT].agg(">".join).reindex(out.index)
    out["n_end"] = ends.groupby(CASE).size().reindex(out.index, fill_value=0).astype(int)
    out["outcome"] = last_end[ACT].map(END_LABELS).reindex(out.index).fillna("open")
    out["end_ts"] = last_end[TS].reindex(out.index)
    out["reached_pending"] = out["end_pattern"].fillna("").str.contains("A_Pending", regex=False)
    out.index.name = CASE
    return out


def monthly_completion(outcomes: pd.DataFrame) -> pd.DataFrame:
    df = outcomes.copy()
    df["submit_month"] = df["submit_ts"].dt.tz_convert(None).dt.to_period("M")
    df["closed"] = df["outcome"] != "open"
    df["days_to_end"] = (df["end_ts"] - df["submit_ts"]).dt.total_seconds() / 86400
    g = df.groupby("submit_month")
    return pd.DataFrame({
        "n": g.size(),
        "n_open": g["closed"].apply(lambda s: int((~s).sum())),
        "completion_rate": g["closed"].mean(),
        "median_days_closed": g["days_to_end"].median(),
        "p90_days_closed": g["days_to_end"].quantile(0.9),
    })


def choose_cutoff(monthly: pd.DataFrame, threshold: float = 0.99) -> pd.Period:
    """Latest submission month such that it and every earlier month meet the threshold."""
    monthly = monthly.sort_index()
    ok = monthly["completion_rate"] >= threshold
    if not ok.iloc[0]:
        raise ValueError("The first submission month is already below the completion threshold")
    if ok.all():
        return monthly.index[-1]
    first_fail = monthly.index.get_loc((~ok).idxmax())
    return monthly.index[first_fail - 1]
