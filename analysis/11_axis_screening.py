"""Phase 4 — does each intake axis actually separate success rate, effort and η?

Run from the project root:

    .venv\\Scripts\\python analysis/11_axis_screening.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_analysis_frame
from segments import screen_axis
from value import bootstrap_eta, group_eta

AXES = ["amount_band", "channel", "goal_group"]
MIN_N = 300
MIN_ETA_RATIO = 1.25
ALTERNATIVES = [("r_amount_years", "effort_hours"), ("r_amount", "staff_events")]


def main() -> None:
    frame = load_analysis_frame(MIN_N)
    print(f"cases={len(frame):,}")
    print(f"channel: {frame['channel'].value_counts().to_dict()}")
    print(f"goal_group: {frame['goal_group'].value_counts().to_dict()}")

    tables, spreads = [], []
    for axis in AXES:
        table = group_eta(frame, axis, "r_amount", "effort_hours").join(
            bootstrap_eta(frame, axis, "r_amount", "effort_hours"))
        row = {"axis": axis, **screen_axis(table, MIN_N, MIN_ETA_RATIO)}
        for r_col, e_col in ALTERNATIVES:
            alt = group_eta(frame, axis, r_col, e_col)
            table[f"eta_{r_col}_{e_col}"] = alt["eta"]
            big = alt[alt["n"] >= MIN_N]
            row[f"eta_ratio_{r_col}_{e_col}"] = float(big["eta"].max() / big["eta"].min())
        spreads.append(row)
        tables.append(table.reset_index(names="group").assign(axis=axis))

    groups = pd.concat(tables, ignore_index=True).round(4)
    groups.to_csv(OUT_DIR / "p4_axis_groups.csv", index=False, encoding="utf-8-sig")
    spread = pd.DataFrame(spreads).round(4)
    spread.to_csv(OUT_DIR / "p4_axis_spread.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== groups by axis (R = r_amount, E = effort_hours) ===\n{groups.to_string(index=False)}")
    print(f"\n=== axis screening (eta ratio >= {MIN_ETA_RATIO} and 90% CI separated) ===\n"
          f"{spread.to_string(index=False)}")


if __name__ == "__main__":
    main()
