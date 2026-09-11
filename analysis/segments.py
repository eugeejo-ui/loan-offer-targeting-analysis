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
