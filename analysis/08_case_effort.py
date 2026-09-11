"""Phase 2 — effort per case under several capping rules, and how robust its ranking is.

Run from the project root, after 07_active_segments.py:

    .venv\\Scripts\\python analysis/08_case_effort.py
"""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, LIFECYCLE, OUT_DIR
from effort import activity_caps, cap_hours, case_effort, staff_event_counts
from loader import load_population

FIXED_CAPS = {"cap_1h": 1.0, "cap_4h": 4.0}
MIN_RANK_CORR = 0.9


def main() -> None:
    ev, oc = load_population()
    seg = pd.read_parquet(OUT_DIR / "p2_active_segments.parquet")
    cases = oc.index

    variants = {"raw": seg["hours"], "cap_p99": cap_hours(seg, activity_caps(seg, 0.99))}
    variants |= {name: cap_hours(seg, h) for name, h in FIXED_CAPS.items()}
    primary = case_effort(seg, variants["cap_p99"], cases)
    effort = pd.DataFrame({f"effort_{k}": case_effort(seg, v, cases)["effort_hours"]
                           for k, v in variants.items()})
    effort["staff_events"] = staff_event_counts(ev, cases)
    zero = effort.index[effort["effort_cap_p99"] == 0]
    zero_w = ev[ev[CASE].isin(zero) & ev[ACT].str.startswith("W_")]
    print(f"cases with zero effort: {len(zero):,}  by outcome: {oc.loc[zero, 'outcome'].value_counts().to_dict()}")
    print(f"  their W_ events by lifecycle: {zero_w[LIFECYCLE].value_counts().to_dict()}")
    print(f"  their W_ events by activity: {zero_w[ACT].value_counts().to_dict()}")
    print(f"total hours by variant: { {k: round(float(v.sum()), 1) for k, v in variants.items()} }")

    corr = effort.corr(method="spearman").round(3)
    corr.to_csv(OUT_DIR / "p2_effort_rank_corr.csv", encoding="utf-8-sig")
    print(f"\n=== case-level Spearman rank correlation ===\n{corr.to_string()}")
    weakest = corr.loc["effort_cap_p99"].drop("effort_cap_p99").min()
    verdict = "robust" if weakest >= MIN_RANK_CORR else "carry alternatives into Phase 5"
    print(f"weakest correlation with primary (cap_p99): {weakest:.3f} -> {verdict}")

    with_outcome = effort.join(oc["outcome"])
    by_outcome = with_outcome.groupby("outcome").agg(
        cases=("effort_cap_p99", "size"),
        median_hours=("effort_cap_p99", "median"),
        mean_hours=("effort_cap_p99", "mean"),
        total_hours=("effort_cap_p99", "sum"),
        median_staff_events=("staff_events", "median"),
    )
    by_outcome["total_share"] = by_outcome["total_hours"] / by_outcome["total_hours"].sum()
    by_outcome = by_outcome.round(3)
    by_outcome.to_csv(OUT_DIR / "p2_effort_by_outcome.csv", encoding="utf-8-sig")
    print(f"\n=== effort (cap_p99) by outcome ===\n{by_outcome.to_string()}")

    by_act = primary.drop(columns="effort_hours").sum().sort_values(ascending=False)
    by_act = pd.DataFrame({"hours": by_act.round(1), "share": (by_act / by_act.sum()).round(3)})
    by_act.to_csv(OUT_DIR / "p2_effort_by_activity.csv", encoding="utf-8-sig")
    print(f"\n=== effort (cap_p99) by activity ===\n{by_act.to_string()}")

    primary.join(effort).to_parquet(OUT_DIR / "p2_case_effort.parquet")


if __name__ == "__main__":
    main()
