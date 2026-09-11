"""Phase 3 — what a successful application is worth: the accepted offer's terms.

Run from the project root:

    .venv\\Scripts\\python analysis/09_revenue_base.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_population
from segments import intake_frame
from value import accepted_offers, revenue_bases

RATE_OUTLIER = 0.2


def main() -> None:
    ev, oc = load_population()
    offers = pd.read_parquet(OUT_DIR / "p0_offers.parquet")
    acc = accepted_offers(ev, offers)
    success = oc.index[oc["reached_pending"]]
    print(f"success cases={len(success):,}  with an accepted offer={int(acc.index.isin(success).sum()):,}  "
          f"accepted offers in non-success cases={int((~acc.index.isin(success)).sum()):,}")
    print(f"accepted offers per case: {acc['n_accepted'].value_counts().to_dict()}")

    bases = revenue_bases(acc).join(acc[["offer_id", "OfferedAmount", "NumberOfTerms", "MonthlyCost"]])
    bases["requested"] = intake_frame(ev)["case:RequestedAmount"].reindex(bases.index)
    bases.to_parquet(OUT_DIR / "p3_accepted_offers.parquet")

    cols = ["r_amount", "r_amount_years", "interest_total", "NumberOfTerms", "implied_rate", "requested"]
    summary = bases[cols].describe(percentiles=[0.1, 0.5, 0.9]).T.round(4)
    summary.to_csv(OUT_DIR / "p3_revenue_summary.csv", encoding="utf-8-sig")
    print(f"\n=== revenue bases of accepted offers ===\n{summary.to_string()}")

    stated = bases["requested"] > 0
    print(f"\noffered == requested (requested > 0): {(bases.loc[stated, 'r_amount'] == bases.loc[stated, 'requested']).mean():.1%}")
    print(f"offered <  requested (requested > 0): {(bases.loc[stated, 'r_amount'] < bases.loc[stated, 'requested']).mean():.1%}")
    print(f"accepted offer with requested == 0: {int((~stated).sum()):,}")
    print(f"implied annual rate > {RATE_OUTLIER:.0%}: {int((bases['implied_rate'] > RATE_OUTLIER).sum()):,} offers")


if __name__ == "__main__":
    main()
