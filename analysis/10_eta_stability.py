"""Phase 3 — does the choice of revenue base R change how groups rank on η?

Provisional groupings only (one intake variable at a time); Phase 4 defines segments.

Run from the project root, after 09_revenue_base.py:

    .venv\\Scripts\\python analysis/10_eta_stability.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_population
from segments import amount_band, intake_frame
from value import group_eta

GROUPINGS = ["case:ApplicationType", "case:LoanGoal", "has_submitted", "amount_band"]
R_COLS = ["r_amount", "r_amount_years", "interest_total"]
MIN_N = 300
MIN_RANK_CORR = 0.9


def main() -> None:
    ev, oc = load_population()
    frame = intake_frame(ev).reindex(oc.index)
    frame["amount_band"] = amount_band(frame["case:RequestedAmount"])
    frame["reached_pending"] = oc["reached_pending"]
    frame = frame.join(pd.read_parquet(OUT_DIR / "p2_case_effort.parquet")[["effort_hours"]])
    frame = frame.join(pd.read_parquet(OUT_DIR / "p3_accepted_offers.parquet")[R_COLS])

    tables, stability = [], []
    for by in GROUPINGS:
        etas = {r: group_eta(frame, by, r, "effort_hours") for r in R_COLS}
        table = etas["r_amount"][["n", "p", "e_mean"]].copy()
        for r, t in etas.items():
            table[f"r_mean_{r}"] = t["r_mean"]
            table[f"eta_{r}"] = t["eta"]
        big = table[table["n"] >= MIN_N]
        corr = big["eta_r_amount"].corr(big["eta_r_amount_years"], method="spearman")
        stability.append({"grouping": by, "groups": len(table), "groups_n_ge_min": len(big),
                          "spearman_amount_vs_amount_years": round(float(corr), 3)})
        tables.append(table.reset_index(names="group").assign(grouping=by))

    provisional = pd.concat(tables, ignore_index=True).round(4)
    provisional.to_csv(OUT_DIR / "p3_eta_provisional.csv", index=False, encoding="utf-8-sig")
    stab = pd.DataFrame(stability)
    stab.to_csv(OUT_DIR / "p3_eta_rank_stability.csv", index=False, encoding="utf-8-sig")
    print(f"=== provisional η by single intake variable ===\n{provisional.to_string(index=False)}")
    print(f"\n=== rank stability, groups with n >= {MIN_N} ===\n{stab.to_string(index=False)}")
    weakest = stab["spearman_amount_vs_amount_years"].min()
    verdict = ("R = accepted amount, amount x years as sensitivity" if weakest >= MIN_RANK_CORR
               else "carry both R candidates into Phase 5")
    print(f"weakest: {weakest:.3f} -> {verdict}")


if __name__ == "__main__":
    main()
