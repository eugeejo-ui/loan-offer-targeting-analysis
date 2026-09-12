"""규칙 계산기의 계산 부분 — 알 수 없는 두 값이 세그먼트의 부호와 순위에 무엇을 하는가.

Phase 3·5의 정의를 그대로 쓴다. 새 지표를 만들지 않는다.
신청당 기대값 = (순마진 비중 × η_I − 시간당 비용) × Ē. η_I는 이자 총액 기준 효율이다.
화면(app/)은 이 모듈을 부르기만 한다. 여기서는 streamlit을 import하지 않는다.
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from config import OUT_DIR
from efficiency import targeting_curve, volume_at_effort_share

INPUT_CSV = OUT_DIR / "p5_calculator_input.csv"
META_JSON = OUT_DIR / "p5_calculator_meta.json"


def load_segments(path: Path = INPUT_CSV) -> pd.DataFrame:
    return pd.read_csv(path, encoding="utf-8-sig")


def load_meta(path: Path = META_JSON) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def segment_economics(table: pd.DataFrame, cost_per_hour: float, margin_share: float) -> pd.DataFrame:
    """세그먼트별 필요 최소 순마진 비중과 기대값. 부호는 margin_share × η_I 와 시간당 비용의 대소로 정해진다."""
    out = table.copy()
    out["required_margin_share"] = cost_per_hour / out["eta_I"]
    out["ev_per_case"] = (margin_share * out["eta_I"] - cost_per_hour) * out["e_mean"]
    out["ev_total"] = out["ev_per_case"] * out["n"]
    out["negative"] = out["ev_per_case"] < 0
    return out


def summarise(priced: pd.DataFrame) -> dict:
    """음수 세그먼트가 몇 개이고, 신청과 공수의 얼마를 차지하는가."""
    effort = priced["n"] * priced["e_mean"]
    negative = priced["negative"]
    return {
        "negative_segments": int(negative.sum()),
        "negative_case_share": float(priced.loc[negative, "n"].sum() / priced["n"].sum()),
        "negative_effort_share": float(effort[negative].sum() / effort.sum()),
        "ev_total": float(priced["ev_total"].sum()),
    }


def breakeven_margin_shares(table: pd.DataFrame, cost_per_hour: float) -> dict:
    """첫 세그먼트가 흑자가 되는 순마진 비중과, 모든 세그먼트가 흑자가 되는 비중."""
    required = cost_per_hour / table["eta_I"]
    return {"first_positive": float(required.min()), "all_positive": float(required.max())}


def allocation_compare(table: pd.DataFrame, effort_budget_share: float) -> dict:
    """같은 공수를 효율 순서로 쓸 때와 성사율 순서로 쓸 때의 기대 대출 규모 (관측값 기반 가상 배분)."""
    indexed = table.set_index("segment") if "segment" in table.columns else table
    out = {key: volume_at_effort_share(targeting_curve(indexed, order), effort_budget_share)
           for key, order in (("volume_by_eta", "eta"), ("volume_by_success_rate", "p"))}
    out["gain"] = out["volume_by_eta"] / out["volume_by_success_rate"] - 1
    return out
