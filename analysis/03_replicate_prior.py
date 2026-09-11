"""Phase 0 — reproduce the prior-study figures before building on them.

Targets (CLAUDE.md §3): 8,559 multi-offer vs 22,950 single-offer cases;
conversion 59.0% vs 53.1% (metafinanz p.24/p.28, Badakhshan et al. p.18).
Literature counts success as "case reaches A_Pending" on the full log.

Run from the project root, after 02_case_outcomes.py:

    .venv\\Scripts\\python analysis/03_replicate_prior.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_events
from offers import conversion_by_offer_group, offer_table, offers_per_case

LITERATURE = {
    ("1", "n"): 22950, ("2+", "n"): 8559,
    ("1", "rate"): 0.531, ("2+", "rate"): 0.590,
}


def main() -> None:
    ev = load_events()
    oc = pd.read_parquet(OUT_DIR / "p0_case_outcomes.parquet")
    offers = offer_table(ev)
    offers.to_parquet(OUT_DIR / "p0_offers.parquet", index=False)

    n_offers = offers_per_case(offers, oc.index)
    print(f"offers={len(offers):,}  cases with 0 offers={int((n_offers == 0).sum()):,}")
    print(f"\n=== offers per case ===\n{n_offers.value_counts().sort_index().to_string()}")

    oc["success_last"] = oc["outcome"].eq("success")
    n_diff = int((oc["reached_pending"] != oc["success_last"]).sum())
    print(f"\ncases where the two success definitions differ: {n_diff:,}")

    rows = []
    for population, sub in [("full", oc), ("in_population", oc[oc["in_population"]])]:
        for success_col in ["reached_pending", "success_last"]:
            res = conversion_by_offer_group(sub, n_offers.reindex(sub.index), success_col)
            for group, r in res.iterrows():
                rows.append({"population": population, "success_def": success_col,
                             "group": group, "n": int(r["n"]),
                             "n_success": int(r["n_success"]), "rate": round(float(r["rate"]), 4)})
    table = pd.DataFrame(rows)
    table["literature"] = [
        LITERATURE.get((g, "n")) if p == "full" else None
        for p, g in zip(table["population"], table["group"])
    ]
    table["literature_rate"] = [
        LITERATURE.get((g, "rate")) if p == "full" else None
        for p, g in zip(table["population"], table["group"])
    ]
    table.to_csv(OUT_DIR / "p0_replication.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== replication ===\n{table.to_string(index=False)}")

    multi_share = (n_offers >= 2).mean()
    print(f"\nmulti-offer share (full): {multi_share:.1%}  (literature 27%)")


if __name__ == "__main__":
    main()
