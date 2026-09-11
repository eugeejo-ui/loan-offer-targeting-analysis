"""Phase 2 — active (hands-on) stretches of workflow items, and where their time concentrates.

Run from the project root:

    .venv\\Scripts\\python analysis/07_active_segments.py
"""
from __future__ import annotations

import pandas as pd

from config import ACT, OUT_DIR, RESOURCE, SYSTEM_RESOURCE
from effort import active_segments, activity_caps
from loader import load_population

TAIL_HOURS = [0.25, 0.5, 1, 2, 4, 8]


def main() -> None:
    ev, _ = load_population()
    seg = active_segments(ev)
    seg.to_parquet(OUT_DIR / "p2_active_segments.parquet", index=False)
    print(f"active segments={len(seg):,}  "
          f"started by {SYSTEM_RESOURCE}: {seg[RESOURCE].eq(SYSTEM_RESOURCE).mean():.1%}")
    print(f"\n=== what ends a segment ===\n{seg['end_lifecycle'].value_counts().to_string()}")

    dist = seg.groupby(ACT)["hours"].describe(percentiles=[0.5, 0.9, 0.99]).round(3)
    dist["total_hours"] = seg.groupby(ACT)["hours"].sum().round(1)
    dist.to_csv(OUT_DIR / "p2_segment_hours_by_activity.csv", encoding="utf-8-sig")
    print(f"\n=== segment hours by activity ===\n{dist.to_string()}")

    total = seg["hours"].sum()
    tail = pd.DataFrame([{
        "threshold_hours": h,
        "segment_share": round(float((seg["hours"] > h).mean()), 4),
        "hours_share": round(float(seg.loc[seg["hours"] > h, "hours"].sum() / total), 3),
    } for h in TAIL_HOURS])
    tail.to_csv(OUT_DIR / "p2_segment_tail.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== long-segment tail ===\n{tail.to_string(index=False)}")

    caps = activity_caps(seg, 0.99).round(3).rename("cap_hours_p99")
    caps.to_csv(OUT_DIR / "p2_segment_caps.csv", encoding="utf-8-sig")
    print(f"\n=== per-activity cap (p99) ===\n{caps.to_string()}")


if __name__ == "__main__":
    main()
