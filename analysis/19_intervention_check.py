"""Phase 8 — two premises behind the intervention choice:
(1) does "speeding up the bank alone will not solve it" hold in every segment, and
(2) does the bank's current handling order already favour high-η segments?

Durations are read only as the upper bound of what speed could save and as the current
handling order — never as a cause of success (P7). Bank-held time includes nights and weekends.

Run from the project root:

    .venv\\Scripts\\python analysis/19_intervention_check.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_population
from process import group_holder_summary, holder_time

MIN_N = 300
CUSTOMER_MAJORITY = 0.5
SEGMENT_COVERAGE = 0.9
ORDER_RHO = -0.3
QUEUE_ACTIVE_SHARE = 0.10


def main() -> None:
    ev, oc = load_population()
    segments = pd.read_parquet(OUT_DIR / "p4_segments.parquet")["segment"]
    sizes = segments.value_counts()
    keep = segments[segments.isin(sizes.index[sizes >= MIN_N])]
    effort = pd.read_parquet(OUT_DIR / "p2_case_effort.parquet")["effort_hours"]
    eta = pd.read_csv(OUT_DIR / "p5_segment_efficiency.csv", index_col="segment")["eta"]

    held = holder_time(ev).reindex(keep.index)
    table = group_holder_summary(held, keep, effort).join(eta).sort_values("eta")
    table.round(4).to_csv(OUT_DIR / "p8_segment_holder.csv", encoding="utf-8-sig")
    print(f"=== bank vs customer held time by segment ({len(table)} segments) ===\n{table.round(3).to_string()}")

    majority = int((table["customer_share"] >= CUSTOMER_MAJORITY).sum())
    rho_order = table["eta"].corr(table["bank_days_median"], method="spearman")
    rho_customer = table["eta"].corr(table["customer_share"], method="spearman")
    active = float(table["bank_active_share_median"].median())
    checks = pd.DataFrame([
        {"check": "1 customer share >= 50% in segments", "value": f"{majority}/{len(table)}",
         "result": "confirmed at segment level" if majority >= SEGMENT_COVERAGE * len(table) else "not in every segment"},
        {"check": "2 Spearman(eta, bank-held median days)", "value": round(rho_order, 3),
         "result": ("current order already favours high-eta" if rho_order <= ORDER_RHO
                    else "current order does not reflect eta -> reordering has room")},
        {"check": "3 median share of bank-held time that is hands-on work", "value": round(active, 4),
         "result": "queue signal (not business-hours adjusted)" if active < QUEUE_ACTIVE_SHARE else "no clear queue"},
        {"check": "ref Spearman(eta, customer share)", "value": round(rho_customer, 3), "result": "descriptive"},
    ])
    checks.to_csv(OUT_DIR / "p8_intervention_checks.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== premise checks ===\n{checks.to_string(index=False)}")


if __name__ == "__main__":
    main()
