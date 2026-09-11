"""Phase 1 — where applications leave the process, and how long each stage takes.

Run from the project root:

    .venv\\Scripts\\python analysis/04_process_funnel.py
"""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, OUT_DIR, RESOURCE, SYSTEM_RESOURCE, TS
from loader import load_population
from process import (funnel_by_outcome, last_milestone_before_end,
                     milestone_first_ts, pair_durations)

STAGE_PAIRS = [
    ("A_Create Application", "O_Sent"),
    ("O_Sent", "O_Returned"),
    ("O_Returned", "A_Pending"),
    ("O_Returned", "A_Denied"),
    ("O_Sent", "A_Cancelled"),
]


def main() -> None:
    ev, oc = load_population()
    first_ts = milestone_first_ts(ev)
    print(f"population cases={len(oc):,}")

    funnel = funnel_by_outcome(first_ts, oc["outcome"])
    funnel.to_csv(OUT_DIR / "p1_funnel_by_outcome.csv", encoding="utf-8-sig")
    print(f"\n=== cases reaching each milestone ===\n{funnel.to_string()}")

    failed = oc.index[oc["outcome"] != "success"]
    last = last_milestone_before_end(first_ts.loc[failed]).rename("last_milestone")
    dropout = pd.crosstab(last, oc.loc[failed, "outcome"], margins=True)
    dropout.to_csv(OUT_DIR / "p1_dropout_last_milestone.csv", encoding="utf-8-sig")
    print(f"\n=== furthest milestone reached by cancelled / denied cases ===\n{dropout.to_string()}")

    stages = pair_durations(first_ts, STAGE_PAIRS)
    summary = stages.describe(percentiles=[0.5, 0.9]).T[["count", "50%", "90%"]].round(2)
    summary.to_csv(OUT_DIR / "p1_stage_durations.csv", encoding="utf-8-sig")
    print(f"\n=== stage durations (days) ===\n{summary.to_string()}")

    # Is A_Submitted an intake-time channel marker? Check who records it, when, and for whom.
    sub = ev[ev[ACT] == "A_Submitted"]
    sub_cases = sub[CASE].unique()
    gap_s = (sub.groupby(CASE)[TS].min() - first_ts["A_Create Application"].reindex(sub_cases)).dt.total_seconds()
    has_sub = pd.Series(oc.index.isin(sub_cases), index=oc.index, name="has_submitted")
    app_type = ev.groupby(CASE)["case:ApplicationType"].first().reindex(oc.index)
    channel = pd.crosstab(has_sub, oc["outcome"], margins=True)
    channel.to_csv(OUT_DIR / "p1_submitted_channel.csv", encoding="utf-8-sig")
    print(f"\n=== A_Submitted presence by outcome ===\n{channel.to_string()}")
    print(pd.crosstab(has_sub, oc["outcome"], normalize="index").round(3).to_string())
    print(f"\n{pd.crosstab(has_sub, app_type).to_string()}")
    print(f"A_Submitted recorded by {SYSTEM_RESOURCE}: {sub[RESOURCE].eq(SYSTEM_RESOURCE).mean():.1%}")
    print(f"seconds from A_Create Application to A_Submitted: "
          f"median {gap_s.median():.1f}, p90 {gap_s.quantile(0.9):.1f}")


if __name__ == "__main__":
    main()
