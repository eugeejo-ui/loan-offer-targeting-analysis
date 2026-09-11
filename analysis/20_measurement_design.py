"""Phase 9 — how long would the A/B tests behind the measurement requirements take?

Effect sizes are design parameters (the smallest change worth detecting), shown next to the
observed association from Phase 6 — they are not estimates of the true effect.

Run from the project root:

    .venv\\Scripts\\python analysis/20_measurement_design.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from design import ab_sample_size

MAX_MONTHS = 6


def main() -> None:
    oc = pd.read_parquet(OUT_DIR / "p0_case_outcomes.parquet")
    pop = oc[oc["in_population"]]
    monthly = pop.groupby(pop["submit_ts"].dt.tz_convert(None).dt.to_period("M")).size()
    per_month = float(monthly.mean())
    funnel = pd.read_csv(OUT_DIR / "p1_funnel_by_outcome.csv", index_col=0)
    sent_share = float(funnel.loc["O_Sent", "all"] / funnel.loc["A_Create Application", "all"])
    groups = pd.read_csv(OUT_DIR / "p6_group_summary.csv")
    d1 = groups[groups["definition"] == "d1_later"].set_index("group")
    single_p = float(d1.loc["single", "p"])
    # The single-offer rule only changes cases that would get several offers in the first
    # conversation, so the experiment has to randomise at that decision point.
    same_p, same_n = float(d1.loc["multi_same", "p"]), float(d1.loc["multi_same", "n"])
    same_flow, same_share = same_n / len(monthly), same_n / len(pop)
    failures = pd.read_csv(OUT_DIR / "p7_failure_effort.csv", index_col="failure_type")
    auto_rate = float(failures.loc["auto_cancel", "cases"] / funnel.loc["O_Sent", "all"])
    print(f"applications per month={per_month:,.0f}  offer-sent share={sent_share:.3f}  "
          f"single-offer success={single_p:.3f}  auto-cancel rate among offer-sent={auto_rate:.3f}")
    print(f"same-conversation multi-offer cases (D1): {same_n:,.0f} = {same_share:.1%} of applications, "
          f"{same_flow:,.0f} per month, success {same_p:.3f}")

    designs = [
        ("first-conversation single offer, randomised at the decision point",
         "cases about to get several offers in the first conversation (D1)", same_p, same_flow,
         [(0.026, "observed, stratified D1 (Phase 6)"), (0.055, "observed, stratified D2 (Phase 6)"),
          (0.02, "design minimum")]),
        ("first-conversation single offer, randomised over all applications (diluted)",
         "all applications", single_p, per_month,
         [(round(same_share * 0.026, 4), "D1 effect diluted by the share of affected cases")]),
        ("contact policy after offer", "offer-sent applications", auto_rate, per_month * sent_share,
         [(-0.01, "design"), (-0.02, "design"), (-0.03, "design")]),
    ]
    rows = []
    for name, target, base, flow, deltas in designs:
        for delta, source in deltas:
            n = ab_sample_size(base, delta)
            months = 2 * n / flow
            rows.append({"experiment": name, "target": target, "base_rate": round(base, 4),
                         "delta": delta, "delta_source": source, "n_per_arm": n,
                         "eligible_per_month": round(flow), "months_needed": round(months, 1),
                         "verdict": "feasible" if months <= MAX_MONTHS else "enlarge effect or extend"})
    table = pd.DataFrame(rows)
    table.to_csv(OUT_DIR / "p9_ab_sample_sizes.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== A/B sample size and duration (alpha 0.05 two-sided, power 0.8, 1:1) ===\n{table.to_string(index=False)}")


if __name__ == "__main__":
    main()
