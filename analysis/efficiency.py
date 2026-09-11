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


INCREMENT_CLASSES = ["공수↑·가치↑", "공수↑·가치↓", "공수↓·가치↑"]


def stratified_diff(frame: pd.DataFrame, group_col: str, base: str, other: str, strata: str,
                    value_col: str, min_n: int = 50) -> tuple[float, pd.DataFrame]:
    """Mean difference (other − base) within strata where both groups have ≥ min_n, and its
    average weighted by the stratum's combined size."""
    sub = frame[frame[group_col].isin([base, other])]
    t = sub.groupby([strata, group_col], observed=True)[value_col].agg(["mean", "size"]).unstack(group_col)
    out = pd.DataFrame({
        "n_base": t[("size", base)], "n_other": t[("size", other)],
        "mean_base": t[("mean", base)], "mean_other": t[("mean", other)],
    })
    out = out[(out["n_base"] >= min_n) & (out["n_other"] >= min_n)]
    out["diff"] = out["mean_other"] - out["mean_base"]
    weight = out["n_base"] + out["n_other"]
    return float((out["diff"] * weight).sum() / weight.sum()), out


def _expected_value(x: pd.DataFrame, r_col: str, success_col: str) -> float:
    return x.loc[x[success_col], r_col].mean() * x[success_col].mean()


def incremental_eta(frame: pd.DataFrame, group_col: str, base: str, other: str, strata: str,
                    r_col: str, e_col: str, success_col: str = "reached_pending",
                    min_n: int = 50) -> pd.DataFrame:
    """Per stratum: extra expected loan volume per extra effort hour of `other` over `base`,
    Δ(R̄·p)/ΔĒ, next to the base group's own η."""
    rows = {}
    for key, s in frame.groupby(strata, observed=True):
        a, b = s[s[group_col] == base], s[s[group_col] == other]
        if len(a) < min_n or len(b) < min_n:
            continue
        va, vb = _expected_value(a, r_col, success_col), _expected_value(b, r_col, success_col)
        ea, eb = a[e_col].mean(), b[e_col].mean()
        rows[key] = {
            "n_base": len(a), "n_other": len(b),
            "p_base": a[success_col].mean(), "p_other": b[success_col].mean(),
            "value_base": va, "value_other": vb, "e_base": ea, "e_other": eb,
            "eta_base": va / ea, "delta_value": vb - va, "delta_effort": eb - ea,
            "incremental_eta": (vb - va) / (eb - ea) if eb != ea else np.nan,
        }
    out = pd.DataFrame.from_dict(rows, orient="index")
    if out.empty:
        return out
    more, gain = out["delta_effort"] > 0, out["delta_value"] > 0
    out["class"] = np.select([more & gain, more & ~gain, ~more & gain], INCREMENT_CLASSES, default="공수↓·가치↓")
    return out
