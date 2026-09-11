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
CLOSING_EVENTS = END_EVENTS + ("O_Cancelled", "O_Refused")
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


def holder_time(events: pd.DataFrame) -> pd.DataFrame:
    """Split each case's elapsed time into bank-held and customer-held days.

    The case starts with the bank, passes to the customer when an offer is
    sent or documents are requested, and returns to the bank when the offer
    comes back or validation resumes. The clock stops at the first end event.
    """
    keep = ("A_Create Application",) + TO_CUSTOMER + TO_BANK + END_EVENTS
    ev = events[events[ACT].isin(keep)].sort_values([CASE, TS], kind="stable")
    rows = []
    for case, g in ev.groupby(CASE, sort=False):
        holder, since = "bank", g[TS].iloc[0]
        spent = {"bank": 0.0, "customer": 0.0}
        for act, ts in zip(g[ACT], g[TS]):
            if act in END_EVENTS:
                spent[holder] += (ts - since).total_seconds()
                break
            new = "customer" if act in TO_CUSTOMER else "bank" if act in TO_BANK else holder
            if new != holder:
                spent[holder] += (ts - since).total_seconds()
                holder, since = new, ts
        rows.append({CASE: case, "bank_days": spent["bank"] / 86400,
                     "customer_days": spent["customer"] / 86400})
    return pd.DataFrame(rows).set_index(CASE)


def cancel_after_last_sent(events: pd.DataFrame) -> pd.DataFrame:
    cancel = events[events[ACT] == "A_Cancelled"].groupby(CASE).agg(
        cancel_ts=(TS, "max"),
        cancel_by_system=(RESOURCE, lambda s: bool((s == SYSTEM_RESOURCE).any())),
    )
    last_sent = events[events[ACT].isin(SENT)].groupby(CASE)[TS].max().rename("last_sent_ts")
    out = cancel.join(last_sent)
    out["gap_days"] = (out["cancel_ts"] - out["last_sent_ts"]).dt.total_seconds() / 86400
    return out


def nearest_case_events(anchors: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    """Nearest context event in the same case before and after each anchor, in anchor order."""
    a = anchors[[CASE, TS]].rename_axis("anchor").reset_index().sort_values(TS, kind="stable")
    c = context[[CASE, TS, ACT]].sort_values(TS, kind="stable")
    out = a.copy()
    for direction, label in (("backward", "prev"), ("forward", "next")):
        side = c.rename(columns={TS: f"{label}_ts", ACT: f"{label}_act"})
        m = pd.merge_asof(a, side, left_on=TS, right_on=f"{label}_ts", by=CASE, direction=direction)
        out[f"{label}_act"] = m[f"{label}_act"].to_numpy()
        out[f"{label}_gap_s"] = (m[f"{label}_ts"] - m[TS]).abs().dt.total_seconds().to_numpy()
    return out.set_index("anchor").sort_index()


def classify_abort_context(nearest: pd.DataFrame, window_s: float = 60.0) -> pd.Series:
    """Label the case transition adjacent to an abort; offer cancellation/refusal counts as closure."""
    moved = nearest["next_act"].isin(["A_Validating"]) & (nearest["next_gap_s"] <= window_s)
    closed = ((nearest["prev_act"].isin(CLOSING_EVENTS) & (nearest["prev_gap_s"] <= window_s))
              | (nearest["next_act"].isin(CLOSING_EVENTS) & (nearest["next_gap_s"] <= window_s)))
    labels = np.select([moved, closed], ["case_moved_to_validation", "case_closed"],
                       default="no_adjacent_transition")
    return pd.Series(labels, index=nearest.index, name="context")
