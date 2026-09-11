"""Phase 1 — who holds the case (bank or customer), and whether cancellations
follow the 30-day no-response rule.

Run from the project root:

    .venv\\Scripts\\python analysis/05_holder_and_cancel.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_population
from process import cancel_after_last_sent, holder_time

RULE_DAYS = (29, 32)


def main() -> None:
    ev, oc = load_population()
    held = holder_time(ev).join(oc["outcome"])
    held["total_days"] = held["bank_days"] + held["customer_days"]
    elapsed = (oc["end_ts"] - oc["submit_ts"]).dt.total_seconds() / 86400
    print(f"max |held total - elapsed| (days): "
          f"{(held['total_days'] - elapsed.reindex(held.index)).abs().max():.4f}")

    by_outcome = held.groupby("outcome").agg(
        cases=("total_days", "size"),
        median_bank_days=("bank_days", "median"),
        median_customer_days=("customer_days", "median"),
        bank_days_sum=("bank_days", "sum"),
        customer_days_sum=("customer_days", "sum"),
    )
    by_outcome.loc["all"] = [len(held), held["bank_days"].median(), held["customer_days"].median(),
                             held["bank_days"].sum(), held["customer_days"].sum()]
    by_outcome["customer_share"] = by_outcome["customer_days_sum"] / (
        by_outcome["bank_days_sum"] + by_outcome["customer_days_sum"])
    by_outcome = by_outcome.round(3)
    by_outcome.to_csv(OUT_DIR / "p1_holder_time_by_outcome.csv", encoding="utf-8-sig")
    print(f"\n=== bank vs customer held time (days) ===\n{by_outcome.to_string()}")

    cancel = cancel_after_last_sent(ev)
    gap = cancel["gap_days"].dropna()
    in_rule = gap.between(*RULE_DAYS)
    summary = pd.Series({
        "cancelled_cases": len(cancel),
        "with_offer_sent": int(gap.size),
        "cancelled_by_system_share": round(float(cancel["cancel_by_system"].mean()), 3),
        "gap_median_days": round(float(gap.median()), 2),
        "gap_p10_days": round(float(gap.quantile(0.1)), 2),
        "gap_p90_days": round(float(gap.quantile(0.9)), 2),
        "share_within_29_32_days": round(float(in_rule.mean()), 3),
        "system_share_within_rule": round(float(cancel.loc[gap.index[in_rule], "cancel_by_system"].mean()), 3),
        "system_share_outside_rule": round(float(cancel.loc[gap.index[~in_rule], "cancel_by_system"].mean()), 3),
    })
    summary.to_csv(OUT_DIR / "p1_cancel_gap_summary.csv", header=["value"], encoding="utf-8-sig")
    print(f"\n=== cancellation vs last offer sent ===\n{summary.to_string()}")


if __name__ == "__main__":
    main()
