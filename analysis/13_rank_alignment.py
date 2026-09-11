"""Phase 5 — do success rate and η rank the segments the same way? (the core question)

Run from the project root:

    .venv\\Scripts\\python analysis/13_rank_alignment.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from efficiency import quadrant, rank_alignment, rank_corr_interval
from loader import load_analysis_frame
from value import group_eta

MIN_N = 300
MIN_RANK_GAP = 10
SEEDS = 5  # the main interval is seed 0; seeds 1-4 show how much the bound moves with the draws alone
BOUNDARY = 0.7  # Phase 5 rule ①
COMBOS = {
    "amount_effort": ("r_amount", "effort_hours"),
    "years_effort": ("r_amount_years", "effort_hours"),
    "amount_events": ("r_amount", "staff_events"),
    "years_events": ("r_amount_years", "staff_events"),
}


def main() -> None:
    frame = load_analysis_frame(MIN_N).join(pd.read_parquet(OUT_DIR / "p4_segments.parquet"))
    sizes = frame["segment"].value_counts()
    frame = frame[frame["segment"].isin(sizes.index[sizes >= MIN_N])]
    print(f"segments used={frame['segment'].nunique()}  cases={len(frame):,}")

    tables = {k: group_eta(frame, "segment", r, e) for k, (r, e) in COMBOS.items()}
    table = rank_alignment(tables["amount_effort"])
    table["quadrant"] = quadrant(table)
    for k, t in tables.items():
        table[f"eta_{k}"] = t["eta"]
    table["eta_I"] = group_eta(frame, "segment", "interest_total", "effort_hours")["eta"]
    table.sort_values("eta", ascending=False).round(4).to_csv(
        OUT_DIR / "p5_segment_efficiency.csv", encoding="utf-8-sig")

    seeds = rank_corr_interval(frame, "segment", "r_amount", "effort_hours", seeds=range(SEEDS))
    seeds.round(3).to_csv(OUT_DIR / "p5_rho_ci_seeds.csv", index=False, encoding="utf-8-sig")
    lo, hi = seeds.loc[seeds["seed"] == 0, ["rho_ci_lo", "rho_ci_hi"]].iloc[0]
    alignment = pd.DataFrame([{
        "combo": k,
        "rho_p_eta": t["p"].corr(t["eta"], method="spearman"),
        "rho_p_r_mean": t["p"].corr(t["r_mean"], method="spearman"),
        "rho_p_e_mean": t["p"].corr(t["e_mean"], method="spearman"),
    } for k, t in tables.items()]).round(3)
    alignment.loc[alignment["combo"] == "amount_effort", ["rho_ci_lo", "rho_ci_hi"]] = [round(lo, 3), round(hi, 3)]
    alignment.to_csv(OUT_DIR / "p5_rank_alignment.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== rank alignment between success rate and η (39 segments) ===\n{alignment.to_string(index=False)}")
    print(f"\n=== 90% interval of ρ(success rate, η) by seed (n_boot per seed = 2000) ===\n"
          f"{seeds.round(3).to_string(index=False)}\n"
          f"upper bound {seeds['rho_ci_hi'].min():.3f}~{seeds['rho_ci_hi'].max():.3f}, "
          f"seeds with upper >= {BOUNDARY}: {int((seeds['rho_ci_hi'] >= BOUNDARY).sum())}/{SEEDS}")

    eta_cols = [f"eta_{k}" for k in COMBOS]
    eta_corr = table[eta_cols].corr(method="spearman").round(3)
    eta_corr.to_csv(OUT_DIR / "p5_eta_rank_corr.csv", encoding="utf-8-sig")
    print(f"\n=== η rank stability across R x E combos ===\n{eta_corr.to_string()}")

    mismatch = table[table["rank_gap"].abs() >= MIN_RANK_GAP].sort_values("rank_gap")
    cols = ["n", "p", "r_mean", "e_mean", "eta", "rank_p", "rank_eta", "rank_gap", "quadrant"]
    mismatch[cols].round(4).to_csv(OUT_DIR / "p5_mismatch.csv", encoding="utf-8-sig")
    print(f"\n=== segments whose success-rate rank and η rank differ by >= {MIN_RANK_GAP} ===\n"
          f"{mismatch[cols].round(3).to_string()}")
    print(f"\nquadrants: {table['quadrant'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
