"""Segment-level efficiency: does success rate rank segments the way η does, and what is the gap worth?"""
from __future__ import annotations

import numpy as np
import pandas as pd

QUADRANTS = ["성사율↑·효율↑", "성사율↑·효율↓", "성사율↓·효율↑"]


def rank_alignment(table: pd.DataFrame, a: str = "p", b: str = "eta") -> pd.DataFrame:
    out = table.copy()
    out[f"rank_{a}"] = out[a].rank(ascending=False, method="min").astype(int)
    out[f"rank_{b}"] = out[b].rank(ascending=False, method="min").astype(int)
    out["rank_gap"] = out[f"rank_{a}"] - out[f"rank_{b}"]
    return out


def quadrant(table: pd.DataFrame, a: str = "p", b: str = "eta") -> pd.Series:
    high_a, high_b = table[a] >= table[a].median(), table[b] >= table[b].median()
    labels = np.select([high_a & high_b, high_a & ~high_b, ~high_a & high_b], QUADRANTS,
                       default="성사율↓·효율↓")
    return pd.Series(labels, index=table.index, name="quadrant")


def cm_scan(table: pd.DataFrame, grid, eta_col: str = "eta") -> pd.DataFrame:
    """For each c/m, segments whose η falls below it (negative EV) and their share of applications and effort."""
    effort = table["n"] * table["e_mean"]
    rows = []
    for cm in grid:
        negative = table[eta_col] < cm
        rows.append({
            "c_over_m": float(cm),
            "negative_segments": int(negative.sum()),
            "application_share": float(table.loc[negative, "n"].sum() / table["n"].sum()),
            "effort_share": float(effort[negative].sum() / effort.sum()),
        })
    return pd.DataFrame(rows)


def min_margin_share(table: pd.DataFrame, cost: float) -> pd.Series:
    """Share of gross interest that must be net margin for EV ≥ 0 at hourly cost `cost`."""
    return (cost / table["eta_I"]).rename("min_margin_share")


def targeting_curve(table: pd.DataFrame, order_col: str) -> pd.DataFrame:
    """Serve segments in descending order_col; cumulative effort share and expected loan volume."""
    t = table.sort_values(order_col, ascending=False, kind="stable")
    effort = t["n"] * t["e_mean"]
    volume = t["n"] * t["p"] * t["r_mean"]
    return pd.DataFrame({
        "segment": t.index,
        "effort_share": (effort.cumsum() / effort.sum()).to_numpy(),
        "volume": volume.cumsum().to_numpy(),
    })


def volume_at_effort_share(curve: pd.DataFrame, share: float) -> float:
    xs = np.concatenate([[0.0], curve["effort_share"].to_numpy()])
    ys = np.concatenate([[0.0], curve["volume"].to_numpy()])
    return float(np.interp(share, xs, ys))


def bootstrap_rank_corr(frame: pd.DataFrame, by: str, r_col: str, e_col: str,
                        success_col: str = "reached_pending", n_boot: int = 200,
                        seed: int = 0) -> np.ndarray:
    """Spearman ρ between segment success rate and η, resampling cases within each segment."""
    rng = np.random.default_rng(seed)
    groups = [(g[success_col].to_numpy(bool), g[r_col].to_numpy(float), g[e_col].to_numpy(float))
              for _, g in frame.groupby(by, observed=True)]
    rhos = np.empty(n_boot)
    for b in range(n_boot):
        p, eta = [], []
        for s, r, e in groups:
            idx = rng.integers(0, len(s), len(s))
            hit = s[idx]
            rate = hit.mean()
            r_mean = r[idx][hit].mean() if hit.any() else np.nan
            p.append(rate)
            eta.append(r_mean * rate / e[idx].mean())
        rhos[b] = pd.Series(p).corr(pd.Series(eta), method="spearman")
    return rhos
