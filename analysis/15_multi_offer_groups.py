"""Phase 6 — multi-offer applications: how many, same or later conversation, and how they
compare with single-offer applications before any stratification.

Run from the project root:

    .venv\\Scripts\\python analysis/15_multi_offer_groups.py
"""
from __future__ import annotations

import pandas as pd

from config import CASE, OUT_DIR
from loader import load_analysis_frame, load_population
from offers import conversation_split, offer_first_sent, offer_group
from value import group_eta

MIN_N = 300
DEFINITIONS = {"d1_later": "created more than 1 day apart", "d2_later": "created after the first offer was sent"}


def main() -> None:
    ev, oc = load_population()
    offers = pd.read_parquet(OUT_DIR / "p0_offers.parquet")
    split = conversation_split(offers[offers[CASE].isin(oc.index)], offer_first_sent(ev))
    for d in DEFINITIONS:
        split[f"group_{d}"] = offer_group(split, d)
    split.to_parquet(OUT_DIR / "p6_case_offer_groups.parquet")
    print(f"offers per case: {split['n_offers'].value_counts().sort_index().to_dict()}")

    multi = split[split["n_offers"] >= 2]
    cross = pd.crosstab(multi["d1_later"], multi["d2_later"])
    cross.to_csv(OUT_DIR / "p6_definition_crosstab.csv", encoding="utf-8-sig")
    print(f"\n=== later conversation among {len(multi):,} multi-offer cases (rows D1, columns D2) ===\n"
          f"{cross.to_string()}")
    print(f"days between first and last offer (multi): "
          f"{multi['span_days'].describe(percentiles=[0.25, 0.5, 0.75, 0.9]).round(2).to_dict()}")

    # 상담 구분 임계의 민감도 — KPMG는 8시간을 썼다 (winner professional p.11).
    thresholds = {"1 day (this project)": 1.0, "8 hours (KPMG p.11)": 8 / 24}
    rows = []
    base = load_analysis_frame(MIN_N)
    for name, days in thresholds.items():
        alt = conversation_split(offers[offers[CASE].isin(oc.index)], offer_first_sent(ev), same_day=days)
        alt["group"] = offer_group(alt, "d1_later")
        t = group_eta(base.join(alt), "group", "r_amount", "effort_hours")
        rows.append(t.reset_index(names="group").assign(threshold=name))
    sensitivity = pd.concat(rows, ignore_index=True)[["threshold", "group", "n", "p", "e_mean", "eta"]].round(4)
    sensitivity.to_csv(OUT_DIR / "p6_threshold_sensitivity.csv", index=False, encoding="utf-8-sig")
    print()
    print("=== D1 threshold sensitivity ===")
    print(sensitivity.to_string(index=False))

    frame = load_analysis_frame(MIN_N).join(split)
    tables = []
    for d, desc in DEFINITIONS.items():
        t = group_eta(frame, f"group_{d}", "r_amount", "effort_hours")
        t = t.join(pd.crosstab(frame[f"group_{d}"], frame["outcome"], normalize="index").add_prefix("share_"))
        tables.append(t.reset_index(names="group").assign(definition=d, description=desc))
    summary = pd.concat(tables, ignore_index=True).round(4)
    summary.to_csv(OUT_DIR / "p6_group_summary.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== single vs multi (same / later conversation), before stratification ===\n"
          f"{summary.to_string(index=False)}")


if __name__ == "__main__":
    main()
