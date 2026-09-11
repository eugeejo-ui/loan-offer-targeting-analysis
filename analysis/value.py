"""Revenue bases of a successful application and the per-effort efficiency η (P1)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import ACT, CASE, OFFER_ID

TERM_COLS = ["OfferedAmount", "NumberOfTerms", "MonthlyCost"]


def accepted_offers(events: pd.DataFrame, offers: pd.DataFrame) -> pd.DataFrame:
    """Terms of the accepted offer per case; `n_accepted` flags cases with more than one."""
    acc = events.loc[events[ACT] == "O_Accepted", [CASE, OFFER_ID]]
    terms = offers.set_index("offer_id")[TERM_COLS]
    return acc.join(terms, on=OFFER_ID).groupby(CASE).agg(
        offer_id=(OFFER_ID, "first"), n_accepted=(OFFER_ID, "size"),
        **{c: (c, "first") for c in TERM_COLS})


def implied_annual_rate(principal, monthly, terms, iterations: int = 80) -> np.ndarray:
    """Annual rate implied by an annuity, by bisection on the monthly rate.

    NaN where total payments do not exceed the principal.
    """
    p, m, n = (np.asarray(x, dtype=float) for x in (principal, monthly, terms))
    lo, hi = np.full(p.shape, 1e-9), np.full(p.shape, 0.1)
    for _ in range(iterations):
        mid = (lo + hi) / 2
        payment = p * mid / (1 - (1 + mid) ** -n)
        lo = np.where(payment < m, mid, lo)
        hi = np.where(payment >= m, mid, hi)
    rate = (1 + (lo + hi) / 2) ** 12 - 1
    return np.where(m * n > p, rate, np.nan)


def revenue_bases(acc: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "r_amount": acc["OfferedAmount"],
        "r_amount_years": acc["OfferedAmount"] * acc["NumberOfTerms"] / 12,
        "interest_total": acc["MonthlyCost"] * acc["NumberOfTerms"] - acc["OfferedAmount"],
        "implied_rate": implied_annual_rate(acc["OfferedAmount"], acc["MonthlyCost"], acc["NumberOfTerms"]),
    }, index=acc.index)


def group_eta(frame: pd.DataFrame, by: str, r_col: str, e_col: str,
              success_col: str = "reached_pending") -> pd.DataFrame:
    """η = mean R of successes × success rate / mean effort of all cases, per group."""
    g = frame.groupby(by, observed=True)
    out = pd.DataFrame({
        "n": g.size(),
        "p": g[success_col].mean(),
        "r_mean": frame[frame[success_col]].groupby(by, observed=True)[r_col].mean(),
        "e_mean": g[e_col].mean(),
    })
    out["eta"] = out["r_mean"] * out["p"] / out["e_mean"]
    return out


def bootstrap_eta(frame: pd.DataFrame, by: str, r_col: str, e_col: str,
                  success_col: str = "reached_pending", n_boot: int = 200, seed: int = 0) -> pd.DataFrame:
    """90% bootstrap interval of η per group, resampling cases within the group."""
    rng = np.random.default_rng(seed)
    rows = {}
    for key, g in frame.groupby(by, observed=True):
        success = g[success_col].to_numpy(bool)
        r, e = g[r_col].to_numpy(float), g[e_col].to_numpy(float)
        idx = rng.integers(0, len(g), size=(n_boot, len(g)))
        s = success[idx]
        n_success = s.sum(axis=1)
        r_sum = np.where(s, r[idx], 0.0).sum(axis=1)
        r_mean = np.divide(r_sum, n_success, out=np.full(n_boot, np.nan), where=n_success > 0)
        eta = r_mean * (n_success / len(g)) / e[idx].mean(axis=1)
        rows[key] = {"eta_lo": np.nanquantile(eta, 0.05), "eta_hi": np.nanquantile(eta, 0.95)}
    return pd.DataFrame.from_dict(rows, orient="index")
