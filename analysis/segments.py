"""Intake-time variables per case (P2) and the provisional requested-amount band."""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, INTAKE_ATTRS

ZERO_BAND = "0 (미기재)"


def intake_frame(events: pd.DataFrame) -> pd.DataFrame:
    frame = events.groupby(CASE)[INTAKE_ATTRS].first()
    submitted = events.loc[events[ACT] == "A_Submitted", CASE].unique()
    frame["has_submitted"] = frame.index.isin(submitted)
    return frame


def amount_band(requested: pd.Series, q: int = 5) -> pd.Series:
    """Quantile bands of positive requested amounts; zero (not stated) is its own band."""
    band = pd.Series(ZERO_BAND, index=requested.index, dtype="object")
    positive = requested > 0
    band[positive] = pd.qcut(requested[positive], q, duplicates="drop").astype(str)
    return band


CHANNEL_LABELS = {
    ("Limit raise", False): "한도 증액",
    ("New credit", True): "신규·A_Submitted",
    ("New credit", False): "신규·표식 없음",
}
UNINFORMATIVE_GOALS = ("Other, see explanation", "Unknown", "Not speficied")


def channel(frame: pd.DataFrame) -> pd.Series:
    """Application type and the A_Submitted marker as one intake axis (the marker exists only for new credit)."""
    keys = zip(frame["case:ApplicationType"], frame["has_submitted"].astype(bool))
    return pd.Series([CHANNEL_LABELS.get(k, "기타") for k in keys], index=frame.index)


def goal_group(goal: pd.Series, min_n: int) -> pd.Series:
    out = goal.where(~goal.isin(UNINFORMATIVE_GOALS), "용도 불명")
    counts = out.value_counts()
    return out.where(~out.isin(counts.index[counts < min_n]), "기타 소수 용도")


def build_segments(frame: pd.DataFrame, axes: list[str], min_n: int) -> pd.Series:
    """Cross axes in order. A cell is split further only where the child has at least min_n cases;
    children below min_n are pooled as "<parent> | 기타" (which may itself stay below min_n)."""
    label = pd.Series("전체", index=frame.index, dtype="object")
    active = pd.Series(True, index=frame.index)
    for axis in axes:
        candidate = label + " | " + frame[axis].astype(str)
        size = candidate.map(candidate[active].value_counts())
        deeper = active & (size >= min_n)
        remainder = active & ~deeper & label.isin(set(label[deeper]))
        label = label.mask(deeper, candidate).mask(remainder, label + " | 기타")
        active = deeper
    return label.str.removeprefix("전체 | ")


def screen_axis(table: pd.DataFrame, min_n: int, min_ratio: float) -> dict:
    """Keep an axis only if η differs enough across groups (n ≥ min_n) and the extremes' intervals separate."""
    big = table[table["n"] >= min_n]
    top, bottom = big["eta"].idxmax(), big["eta"].idxmin()
    eta_ratio = float(big["eta"].max() / big["eta"].min())
    separated = bool(big.loc[top, "eta_lo"] > big.loc[bottom, "eta_hi"])
    return {
        "groups_n_ge_min": len(big),
        "p_range": float(big["p"].max() - big["p"].min()),
        "e_ratio": float(big["e_mean"].max() / big["e_mean"].min()),
        "eta_ratio": eta_ratio,
        "ci_separated": separated,
        "retained": eta_ratio >= min_ratio and separated,
    }
