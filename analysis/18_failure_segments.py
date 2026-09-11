"""Phase 7 — can failure types be told apart at intake, where does failed effort concentrate,
and are low-η segments the ones that burn effort on failures?

Run from the project root, after 17_failure_effort.py:

    .venv\\Scripts\\python analysis/18_failure_segments.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import OUT_DIR
from failures import FAILURE_TYPES, screen_failure_rates, wilson_interval

MIN_N = 300
TOP = 0.25
ADDRESSABLE_MIN_SHARE = 0.10


def main() -> None:
    case = pd.read_parquet(OUT_DIR / "p7_case_failure.parquet").join(pd.read_parquet(OUT_DIR / "p4_segments.parquet"))
    sizes = case["segment"].value_counts()
    case = case[case["segment"].isin(sizes.index[sizes >= MIN_N])]
    eta = pd.read_csv(OUT_DIR / "p5_segment_efficiency.csv", index_col="segment")["eta"]
    n = case.groupby("segment").size()
    effort_all = case.groupby("segment")["effort_hours"].sum()
    table = pd.DataFrame({"n": n, "effort_hours": effort_all}).join(eta)

    screens, type_effort = [], {}
    for t in FAILURE_TYPES:
        is_t = case["failure_type"] == t
        k = is_t.groupby(case["segment"]).sum()
        eff = case.loc[is_t].groupby("segment")["effort_hours"].sum().reindex(n.index, fill_value=0.0)
        lo, hi = wilson_interval(k, n)
        table[f"rate_{t}"], table[f"rate_{t}_lo"], table[f"rate_{t}_hi"] = k / n, lo, hi
        table[f"effort_share_{t}"] = eff / effort_all
        type_effort[t] = eff
        screens.append({"failure_type": t, **screen_failure_rates(pd.DataFrame({"n": n, "k": k, "effort": eff}))})
    table["failed_effort_share"] = sum(type_effort.values()) / effort_all
    table.sort_values("eta").round(4).to_csv(OUT_DIR / "p7_segment_failures.csv", encoding="utf-8-sig")
    screening = pd.DataFrame(screens).round(4)
    screening.to_csv(OUT_DIR / "p7_failure_screening.csv", index=False, encoding="utf-8-sig")
    print(f"=== can intake segments tell failure types apart? ({len(n)} segments) ===\n{screening.to_string(index=False)}")

    rho = table["eta"].corr(table["failed_effort_share"], method="spearman")
    print(f"\nSpearman(segment η, failed share of segment effort): {rho:.3f}")
    cols = ["n", "eta", "failed_effort_share", "rate_denied", "rate_auto_cancel", "rate_manual_cancel"]
    ordered = table.sort_values("eta")
    print(f"\nlowest η:\n{ordered[cols].head(5).round(3).to_string()}\n\nhighest η:\n{ordered[cols].tail(5).round(3).to_string()}")

    total = case["effort_hours"].sum()
    contact = case.loc[case["failure_type"] == "auto_cancel", "effort_after"].sum() / total
    denied_ok = bool(screening.set_index("failure_type").loc["denied", "identifiable"])
    k_top = max(1, int(np.ceil(len(n) * TOP)))
    top_denied = table["rate_denied"].sort_values(ascending=False).index[:k_top]
    front = (type_effort["denied"].reindex(top_denied).sum() / total) if denied_ok else 0.0
    addressable = pd.DataFrame([
        {"lever": "contact policy (auto-cancel effort after first offer sent)", "share_of_all_effort": contact},
        {"lever": f"front filter (denied effort in top {TOP:.0%} denial-rate segments, if identifiable)",
         "share_of_all_effort": front},
        {"lever": "total addressable", "share_of_all_effort": contact + front},
    ]).round(4)
    addressable.to_csv(OUT_DIR / "p7_addressable_effort.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== effort a lever could address (scenario 3) ===\n{addressable.to_string(index=False)}")
    print(f"top {TOP:.0%} denial-rate segments: {list(top_denied)}")
    # Sensitivity only (verdict above is unchanged): the front-filter share if the concentration
    # condition were dropped and only the rate spread were required.
    front_relaxed = type_effort["denied"].reindex(top_denied).sum() / total
    print(f"sensitivity — front filter without the concentration condition: {front_relaxed:.1%} of all effort; "
          f"total with contact policy: {contact + front_relaxed:.1%}")
    print(f"scenario 3: {'confirmed' if contact + front >= ADDRESSABLE_MIN_SHARE else 'large in size, small in recoverable share'}")


if __name__ == "__main__":
    main()
