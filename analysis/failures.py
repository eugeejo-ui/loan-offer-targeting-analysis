"""Failed applications: their type, when their effort was spent, and whether intake segments tell them apart."""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import CASE

FAILURE_TYPES = ("denied", "auto_cancel", "manual_cancel")


def failure_type(outcome: pd.Series, cancel_by_system: pd.Series) -> pd.Series:
    """success / denied / auto_cancel (cancelled by the system account) / manual_cancel."""
    system = cancel_by_system.reindex(outcome.index).fillna(False).astype(bool)
    cancelled = outcome == "cancelled"
    out = outcome.astype(object).copy()
    out[cancelled & system] = "auto_cancel"
    out[cancelled & ~system] = "manual_cancel"
    return out.rename("failure_type")


def split_effort(segments: pd.DataFrame, hours: pd.Series, cut: pd.Series, cases: pd.Index) -> pd.DataFrame:
    """Effort hours per case before and after a per-case cut time; cases without a cut count as before."""
    after = (segments["start_ts"] >= segments[CASE].map(cut)).rename("after")
    by = hours.groupby([segments[CASE], after]).sum().unstack(fill_value=0.0)
    by = by.reindex(columns=[False, True], fill_value=0.0).reindex(cases, fill_value=0.0)
    by.columns = ["effort_before", "effort_after"]
    return by


def wilson_interval(k, n, z: float = 1.645) -> tuple[np.ndarray, np.ndarray]:
    k, n = np.asarray(k, dtype=float), np.asarray(n, dtype=float)
    p = k / n
    denom = 1 + z ** 2 / n
    centre = (p + z ** 2 / (2 * n)) / denom
    half = z * np.sqrt(p * (1 - p) / n + z ** 2 / (4 * n ** 2)) / denom
    return centre - half, centre + half


def top_concentration(rate: pd.Series, weight: pd.Series, top: float = 0.25) -> float:
    """Share of total weight held by the top `top` fraction of groups ranked by rate."""
    order = rate.sort_values(ascending=False).index
    k = max(1, int(np.ceil(len(order) * top)))
    return float(weight.reindex(order[:k]).sum() / weight.sum())


def screen_failure_rates(table: pd.DataFrame, min_ratio: float = 1.5, min_concentration: float = 0.4,
                         top: float = 0.25) -> dict:
    """table: per group n, k (cases of the failure type) and effort (hours spent on those cases)."""
    rate = table["k"] / table["n"]
    lo, hi = (pd.Series(x, index=table.index) for x in wilson_interval(table["k"], table["n"]))
    ratio = float(rate.max() / rate.min())
    separated = bool(lo[rate.idxmax()] > hi[rate.idxmin()])
    concentration = top_concentration(rate, table["effort"], top)
    return {
        "rate_min": float(rate.min()), "rate_max": float(rate.max()), "rate_ratio": ratio,
        "ci_separated": separated, "top_quartile_effort_share": concentration,
        "identifiable": ratio >= min_ratio and separated and concentration >= min_concentration,
    }
