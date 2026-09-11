"""Phase 4 — cross the retained axes into segments of at least MIN_N applications.

Run from the project root, after 11_axis_screening.py:

    .venv\\Scripts\\python analysis/12_segments.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_analysis_frame
from segments import build_segments
from value import bootstrap_eta, group_eta

MIN_N = 300
ALTERNATIVES = [("r_amount_years", "effort_hours"), ("r_amount", "staff_events"),
                ("r_amount_years", "staff_events")]


def main() -> None:
    spread = pd.read_csv(OUT_DIR / "p4_axis_spread.csv")
    axes = spread.loc[spread["retained"]].sort_values("eta_ratio", ascending=False)["axis"].tolist()
    print(f"retained axes in crossing order: {axes or 'none'}")

    frame = load_analysis_frame(MIN_N)
    frame["segment"] = build_segments(frame, axes, MIN_N)
    frame[["segment"]].to_parquet(OUT_DIR / "p4_segments.parquet")

    table = group_eta(frame, "segment", "r_amount", "effort_hours").join(
        bootstrap_eta(frame, "segment", "r_amount", "effort_hours"))
    for r_col, e_col in ALTERNATIVES:
        table[f"eta_{r_col}_{e_col}"] = group_eta(frame, "segment", r_col, e_col)["eta"]
    table["eta_I"] = group_eta(frame, "segment", "interest_total", "effort_hours")["eta"]
    table["small"] = table["n"] < MIN_N
    table = table.sort_values("eta", ascending=False).round(4)
    table.to_csv(OUT_DIR / "p4_segment_table.csv", encoding="utf-8-sig")
    print(f"\n=== segments (sorted by η, R = r_amount, E = effort_hours) ===\n{table.to_string()}")
    print(f"\nsegments={len(table)}  small (< {MIN_N})={int(table['small'].sum())}  "
          f"cases in small segments={int(table.loc[table['small'], 'n'].sum()):,}")


if __name__ == "__main__":
    main()
