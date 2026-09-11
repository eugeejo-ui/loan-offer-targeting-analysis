"""Phase 0 — parse the XES once and cache it; confirm the log's size.

Run from the project root:

    .venv\\Scripts\\python analysis/00_build_cache.py
"""
from __future__ import annotations

from config import ACT, CACHE_PARQUET, CASE, LIFECYCLE, TS
from loader import load_events


def main() -> None:
    fresh = not CACHE_PARQUET.exists()
    ev = load_events()
    print(f"{'built' if fresh else 'read'} cache: {CACHE_PARQUET}")
    print(f"events={len(ev):,}  cases={ev[CASE].nunique():,}  "
          f"activities={ev[ACT].nunique()}  lifecycle states={ev[LIFECYCLE].nunique()}")
    print(f"time range: {ev[TS].min()} -> {ev[TS].max()}")
    print(f"columns ({len(ev.columns)}): {list(ev.columns)}")


if __name__ == "__main__":
    main()
