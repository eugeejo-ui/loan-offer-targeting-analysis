"""Phase 7 — how much effort failed applications take, by failure type and by whether it was
spent before or after the case's first offer was sent.

Run from the project root:

    .venv\\Scripts\\python analysis/17_failure_effort.py
"""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, OUT_DIR
from effort import activity_caps, cap_hours
from failures import failure_type, split_effort
from loader import load_population
from offers import offer_first_sent
from process import cancel_after_last_sent

CONTACT_LEVER_MIN_SHARE = 0.05


def main() -> None:
    ev, oc = load_population()
    ftype = failure_type(oc["outcome"], cancel_after_last_sent(ev)["cancel_by_system"])
    seg = pd.read_parquet(OUT_DIR / "p2_active_segments.parquet")
    hours = cap_hours(seg, activity_caps(seg, 0.99))
    offers = pd.read_parquet(OUT_DIR / "p0_offers.parquet")
    first_sent = (offers.assign(first_sent=offers["offer_id"].map(offer_first_sent(ev)))
                  .groupby(CASE)["first_sent"].min())

    case = split_effort(seg, hours, first_sent, oc.index).join(ftype)
    case["effort_hours"] = case["effort_before"] + case["effort_after"]
    case.to_parquet(OUT_DIR / "p7_case_failure.parquet")
    total = case["effort_hours"].sum()
    print(f"failure types: {case['failure_type'].value_counts().to_dict()}")
    print(f"total effort hours: {total:,.1f} (Phase 2: 17,957.7)")

    summary = case.groupby("failure_type").agg(
        cases=("effort_hours", "size"), mean_hours=("effort_hours", "mean"),
        effort_before=("effort_before", "sum"), effort_after=("effort_after", "sum"),
        effort_total=("effort_hours", "sum"))
    summary["share_of_all_effort"] = summary["effort_total"] / total
    summary["after_sent_share_of_all"] = summary["effort_after"] / total
    summary = summary.round(4)
    summary.to_csv(OUT_DIR / "p7_failure_effort.csv", encoding="utf-8-sig")
    print(f"\n=== effort by failure type, before / after the first offer was sent ===\n{summary.to_string()}")

    after = (seg["start_ts"] >= seg[CASE].map(first_sent)).rename("after_first_sent")
    by_act = hours.groupby([seg[CASE].map(case["failure_type"]).rename("failure_type"), seg[ACT], after]).sum()
    by_act = (by_act / total).rename("share_of_all_effort").reset_index()
    by_act = by_act[by_act["share_of_all_effort"] > 0].sort_values(
        ["failure_type", "share_of_all_effort"], ascending=[True, False]).round(4)
    by_act.to_csv(OUT_DIR / "p7_failure_effort_by_activity.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== share of all effort by failure type, activity and timing ===\n"
          f"{by_act[by_act['failure_type'] != 'success'].to_string(index=False)}")

    contact = float(summary.loc["auto_cancel", "after_sent_share_of_all"])
    verdict = ("material effort lever" if contact >= CONTACT_LEVER_MIN_SHARE
               else "small as an effort lever; its value would be converting non-responders (not measurable)")
    print(f"\nauto-cancel effort after the first offer was sent: {contact:.1%} of all effort -> {verdict}")


if __name__ == "__main__":
    main()
