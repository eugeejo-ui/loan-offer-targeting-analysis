"""Phase 5 — what ranking by η instead of success rate is worth, where EV turns negative,
and how much of the interest must be net margin in each segment.

Run from the project root, after 13_rank_alignment.py:

    .venv\\Scripts\\python analysis/14_targeting_and_scan.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from config import OUT_DIR
from efficiency import cm_scan, min_margin_share, targeting_curve, volume_at_effort_share

REFERENCE_COST = 57.6  # EUR/hour — Eurostat lc_lci_lev, NL, NACE K, 2016 (docs/03_method.md §3)
EFFORT_BUDGETS = [0.25, 0.5, 0.75]
GRID_POINTS = 41


def main() -> None:
    table = pd.read_csv(OUT_DIR / "p5_segment_efficiency.csv", index_col="segment")

    curves = {order: targeting_curve(table, order) for order in ("p", "eta")}
    compare = pd.DataFrame([{
        "effort_budget_share": share,
        "volume_by_success_rate": volume_at_effort_share(curves["p"], share),
        "volume_by_eta": volume_at_effort_share(curves["eta"], share),
    } for share in EFFORT_BUDGETS])
    compare["eta_order_gain"] = compare["volume_by_eta"] / compare["volume_by_success_rate"] - 1
    compare = compare.round(4)
    compare.to_csv(OUT_DIR / "p5_targeting_compare.csv", index=False, encoding="utf-8-sig")
    print(f"=== expected loan volume for the same effort budget: success-rate order vs η order ===\n"
          f"{compare.to_string(index=False)}")

    grid = np.geomspace(table["eta"].min() / 10, table["eta"].max() * 10, GRID_POINTS)
    scan = cm_scan(table, grid).round(4)
    scan.to_csv(OUT_DIR / "p5_cm_scan.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== c/m scan (R = accepted amount, E = effort hours) ===\n{scan.to_string(index=False)}")
    print(f"first segment turns negative at c/m = {table['eta'].min():,.0f} ({table['eta'].idxmin()})")

    table["min_margin_share"] = min_margin_share(table, REFERENCE_COST)
    margin = table[["n", "p", "eta", "eta_I", "min_margin_share"]].sort_values(
        "min_margin_share", ascending=False).round(4)
    margin.to_csv(OUT_DIR / "p5_margin_share.csv", encoding="utf-8-sig")
    worst, best = margin["min_margin_share"].max(), margin["min_margin_share"].min()
    print(f"\n=== minimum net-margin share of interest for EV >= 0 at {REFERENCE_COST} EUR/h ===\n"
          f"{margin.head(5).to_string()}\n...\n{margin.tail(3).to_string()}")
    print(f"worst {worst:.2%}  best {best:.2%}  worst/best {worst / best:.1f}x (independent of the cost assumed)")

    calc_cols = ["n", "p", "r_mean", "e_mean", "eta", "eta_amount_effort", "eta_years_effort",
                 "eta_amount_events", "eta_years_events", "eta_I", "min_margin_share", "quadrant"]
    table[calc_cols].round(4).to_csv(OUT_DIR / "p5_calculator_input.csv", encoding="utf-8-sig")
    (OUT_DIR / "p5_calculator_meta.json").write_text(json.dumps({
        "reference_cost_eur_per_hour": REFERENCE_COST,
        "reference_cost_source": "Eurostat lc_lci_lev, geo=NL, nace_r2=K, time=2016, lcstruct=D1_D4_MD5",
        "primary_combo": {"R": "r_amount", "E": "effort_hours"},
        "segments": len(table),
        "note": "Observed segment values; allocation comparisons are hypothetical, not intervention effects.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
