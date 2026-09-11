"""Phase 0 — classify case outcomes and fix the observation window.

Run from the project root:

    .venv\\Scripts\\python analysis/02_case_outcomes.py
"""
from __future__ import annotations

import json

from config import OUT_DIR, TS
from loader import load_events
from outcomes import case_outcomes, choose_cutoff, monthly_completion

THRESHOLD = 0.99


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    ev = load_events()
    oc = case_outcomes(ev)
    obs_end = ev[TS].max()

    patterns = oc["end_pattern"].fillna("(none)").value_counts()
    patterns.rename_axis("end_pattern").reset_index(name="cases").to_csv(
        OUT_DIR / "p0_end_patterns.csv", index=False, encoding="utf-8-sig")
    print(f"observation ends: {obs_end}")
    print(f"\n=== end patterns ===\n{patterns.to_string()}")
    print(f"\n=== outcomes ===\n{oc['outcome'].value_counts().to_string()}")

    monthly = monthly_completion(oc)
    monthly.to_csv(OUT_DIR / "p0_monthly_completion.csv", encoding="utf-8-sig")
    print(f"\n=== completion by submission month ===\n{monthly.round(3).to_string()}")

    cutoff = choose_cutoff(monthly, THRESHOLD)
    oc["in_window"] = oc["submit_ts"].dt.tz_convert(None).dt.to_period("M") <= cutoff
    n_out = int((~oc["in_window"]).sum())
    print(f"\ncutoff month (completion >= {THRESHOLD}): {cutoff}")
    print(f"excluded cases: {n_out:,} / {len(oc):,} ({n_out / len(oc):.1%})")
    print(f"open cases left inside window: {int(((oc['outcome'] == 'open') & oc['in_window']).sum()):,}")
    oc["in_population"] = oc["in_window"] & (oc["outcome"] != "open")
    print(f"analysis population (in window and closed): {int(oc['in_population'].sum()):,}")

    oc.to_parquet(OUT_DIR / "p0_case_outcomes.parquet")
    (OUT_DIR / "p0_cutoff.json").write_text(json.dumps({
        "threshold": THRESHOLD,
        "cutoff_month": str(cutoff),
        "n_cases": len(oc),
        "n_excluded": n_out,
        "n_population": int(oc["in_population"].sum()),
        "observation_end": str(obs_end),
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
