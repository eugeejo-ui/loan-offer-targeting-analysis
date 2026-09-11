"""Phase 6 — does the multi-offer advantage survive stratification, and what does the extra effort buy?

Observed associations only: a later offer needs a customer who is still engaged, so the
later-conversation difference is an upper bound, not an effect (P3).

Run from the project root, after 15_multi_offer_groups.py:

    .venv\\Scripts\\python analysis/16_multi_offer_increment.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from efficiency import incremental_eta, stratified_diff
from loader import load_analysis_frame

MIN_N = 300
MIN_GROUP_N = 50
REFERENCE_COST = 57.6  # EUR/hour — docs/03_method.md §3
COMPARISONS = [("group_any", "multi"), ("group_d1_later", "multi_same"), ("group_d1_later", "multi_later"),
               ("group_d2_later", "multi_same"), ("group_d2_later", "multi_later")]


def main() -> None:
    frame = load_analysis_frame(MIN_N).join(pd.read_parquet(OUT_DIR / "p4_segments.parquet"))
    frame = frame.join(pd.read_parquet(OUT_DIR / "p6_case_offer_groups.parquet"))
    sizes = frame["segment"].value_counts()
    frame = frame[frame["segment"].isin(sizes.index[sizes >= MIN_N])].copy()
    frame["group_any"] = frame["n_offers"].ge(2).map({True: "multi", False: "single"})
    eta_floor = pd.read_csv(OUT_DIR / "p5_segment_efficiency.csv")["eta"].min()
    print(f"cases={len(frame):,}  segment η floor (Phase 5)={eta_floor:,.0f}")

    rows = []
    for col, other in COMPARISONS:
        sub = frame[frame[col].isin(["single", other])]
        for metric in ("reached_pending", "effort_hours"):
            crude = sub.loc[sub[col] == other, metric].mean() - sub.loc[sub[col] == "single", metric].mean()
            strat, used = stratified_diff(frame, col, "single", other, "segment", metric, MIN_GROUP_N)
            rows.append({"grouping": col, "comparison": f"{other} - single", "metric": metric,
                         "crude_diff": crude, "stratified_diff": strat, "strata_used": len(used)})
    diffs = pd.DataFrame(rows).round(4)
    diffs.to_csv(OUT_DIR / "p6_stratified_diff.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== differences vs single-offer, crude and stratified by segment ===\n{diffs.to_string(index=False)}")

    tables = []
    for col, other in COMPARISONS:
        inc = incremental_eta(frame, col, "single", other, "amount_band", "r_amount", "effort_hours",
                              min_n=MIN_GROUP_N)
        inc_i = incremental_eta(frame, col, "single", other, "amount_band", "interest_total", "effort_hours",
                                min_n=MIN_GROUP_N)
        inc["incremental_eta_I"] = inc_i["incremental_eta"]
        gaining = inc["class"] == "공수↑·가치↑"
        inc["incremental_min_margin_share"] = (REFERENCE_COST / inc["incremental_eta_I"]).where(gaining)
        inc["below_segment_eta_floor"] = gaining & (inc["incremental_eta"] < eta_floor)
        tables.append(inc.reset_index(names="amount_band").assign(grouping=col, comparison=f"{other} - single"))
    by_amount = pd.concat(tables, ignore_index=True).round(4)
    by_amount.to_csv(OUT_DIR / "p6_increment_by_amount.csv", index=False, encoding="utf-8-sig")
    cols = ["comparison", "grouping", "amount_band", "n_base", "n_other", "p_base", "p_other",
            "e_base", "e_other", "eta_base", "incremental_eta", "class",
            "incremental_min_margin_share", "below_segment_eta_floor"]
    print(f"\n=== incremental efficiency by amount band ===\n{by_amount[cols].to_string(index=False)}")

    by_segment = incremental_eta(frame, "group_any", "single", "multi", "segment", "r_amount", "effort_hours",
                                 min_n=MIN_GROUP_N)
    by_segment["below_segment_eta_floor"] = (by_segment["class"] == "공수↑·가치↑") & (
        by_segment["incremental_eta"] < eta_floor)
    by_segment.round(4).to_csv(OUT_DIR / "p6_increment_by_segment.csv", encoding="utf-8-sig")
    print(f"\nsegments with both groups >= {MIN_GROUP_N}: {len(by_segment)}")
    print(f"class counts (multi vs single, by segment): {by_segment['class'].value_counts().to_dict()}")
    print(f"gaining but below the segment η floor: {int(by_segment['below_segment_eta_floor'].sum())}")


if __name__ == "__main__":
    main()
