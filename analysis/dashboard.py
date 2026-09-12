"""산출물 CSV → 대시보드가 읽는 데이터(JSON). 화면은 이 결과만 본다.

순수 함수다. 파일을 읽지 않고 프레임을 받는다 — 테스트에서 작은 프레임으로 검증한다.
"""
from __future__ import annotations

import pandas as pd

from charts import pretty_segment

SEGMENT_FIELDS = ["n", "p", "r_mean", "e_mean", "eta", "eta_I", "rank_p", "rank_eta", "rank_gap"]


def _plain(value):
    """numpy 스칼라를 파이썬 기본형으로. json.dumps가 그대로 처리할 수 있어야 한다."""
    if isinstance(value, (pd.Series, pd.Index)):
        return [_plain(v) for v in value]
    if hasattr(value, "item"):
        return value.item()
    return value


# 판정 표의 표시 이름 — 산출 스크립트(19)의 내부 라벨은 그대로 두고 화면에서만 바꾼다.
# (이름, 값 형식, 판정 문장). 값 형식: count 그대로 / correlation 부호 붙인 소수 / share 백분율.
CHECK_DISPLAY = {
    "1 customer share >= 50% in segments": (
        "고객 보유 과반 세그먼트 수 (경과시간 기준)", "count",
        "은행의 처리 시간을 0으로 단축해도 경과시간의 대부분은 잔존합니다. 전 세그먼트가 이에 해당합니다.",
    ),
    "2 Spearman(eta, bank-held median days)": (
        "효율(η)과 은행 보유 일수의 순위 상관", "correlation",
        "효율이 높은 세그먼트일수록 은행이 더 오래 보유합니다. "
        "현재 처리 순서가 효율과 반대 방향이므로 이 수치는 순서 조정의 여지를 시사합니다.",
    ),
    "3 median share of bank-held time that is hands-on work": (
        "실제 작업 시간 비중 (은행 보유 시간 대비, 세그먼트 중앙값)", "share",
        "은행이 신청을 보유한 시간의 대부분을 대기가 차지합니다. 처리 대기열의 존재를 시사하는 신호로 해석합니다.",
    ),
    "ref Spearman(eta, customer share)": (
        "참고 — 효율(η)과 고객 보유 비중의 순위 상관", "correlation",
        "은행 보유 시간의 비중은 효율 상위 세그먼트에서 더 높습니다.",
    ),
}


def _check_value(value, kind: str) -> str:
    if kind == "share":
        return f"{float(value) * 100:.2f}%"
    if kind == "correlation":
        return f"{float(value):+.3f}".replace("-", "−")
    return str(value)


def _checks(frame: pd.DataFrame) -> list[dict]:
    """판정 행을 화면 표기로 바꾼다. 표시 이름이 없는 행은 원문 그대로 남긴다."""
    rows = []
    for name, value in frame.set_index("check")["value"].items():
        label, kind, verdict = CHECK_DISPLAY.get(str(name), (str(name), "count", ""))
        rows.append({"check": label, "value": _check_value(value, kind), "verdict": verdict})
    return rows


def _segments(efficiency: pd.DataFrame) -> list[dict]:
    rows = []
    for _, row in efficiency.sort_values("eta", ascending=False).iterrows():
        entry = {"segment": row["segment"], "label": pretty_segment(row["segment"])}
        entry.update({field: _plain(row[field]) for field in SEGMENT_FIELDS if field in efficiency.columns})
        rows.append(entry)
    return rows


def _allocation(targeting: pd.DataFrame) -> list[dict]:
    return [{
        "budget": int(round(row["effort_budget_share"] * 100)),
        "by_rate": _plain(row["volume_by_success_rate"]),
        "by_eta": _plain(row["volume_by_eta"]),
        "gain": _plain(row["eta_order_gain"]),
    } for _, row in targeting.iterrows()]


def _groups(group_summary: pd.DataFrame, definition: str = "d1_later") -> list[dict]:
    names = {"single": "단일 오퍼", "multi_same": "복수 오퍼 · 같은 상담", "multi_later": "복수 오퍼 · 나중 상담"}
    part = group_summary[group_summary["definition"] == definition].set_index("group")
    return [{"name": names[key], "n": _plain(part.loc[key, "n"]), "p": _plain(part.loc[key, "p"]),
             "e_mean": _plain(part.loc[key, "e_mean"]), "eta": _plain(part.loc[key, "eta"])}
            for key in ("single", "multi_same", "multi_later") if key in part.index]


def _failures(failure_effort: pd.DataFrame) -> list[dict]:
    names = {"denied": "거절", "auto_cancel": "30일 자동 취소", "manual_cancel": "수동 취소", "success": "성사"}
    total = failure_effort["effort_total"].sum()
    return [{"name": names.get(row["failure_type"], row["failure_type"]),
             "cases": _plain(row["cases"]),
             "before": _plain(row["effort_before"] / total),
             "after": _plain(row["effort_after"] / total),
             "share": _plain(row["share_of_all_effort"])}
            for _, row in failure_effort.iterrows() if row["failure_type"] != "success"]


def _experiments(ab: pd.DataFrame) -> list[dict]:
    source = {"observed, stratified D1 (Phase 6)": "관측 D1", "observed, stratified D2 (Phase 6)": "관측 D2",
              "design minimum": "설계 최솟값", "design": "설계값",
              "D1 effect diluted by the share of affected cases": "희석"}
    rows = ab[~ab["experiment"].str.contains("diluted")]
    return [{"name": "첫 상담 단일 오퍼" if row["experiment"].startswith("first") else "접촉 정책",
             "delta": _plain(row["delta"]),
             "source": source.get(row["delta_source"], row["delta_source"]),
             "per_arm": _plain(row["n_per_arm"]),
             "months": _plain(row["months_needed"]),
             "feasible": row["verdict"] == "feasible"}
            for _, row in rows.iterrows()]


def build_payload(frames: dict) -> dict:
    """대시보드 한 페이지가 쓰는 값 전부. 없는 자료는 조용히 건너뛴다."""
    meta = frames.get("meta", {})
    efficiency = frames["efficiency"]
    alignment = frames["alignment"].set_index("combo").loc["amount_effort"]

    payload = {
        "reference_cost": _plain(meta.get("reference_cost_eur_per_hour")),
        "reference_cost_source": meta.get("reference_cost_source"),
        "alignment": {
            "rho": _plain(alignment["rho_p_eta"]),
            "ci_lo": _plain(alignment["rho_ci_lo"]),
            "ci_hi": _plain(alignment["rho_ci_hi"]),
        },
        "segments": _segments(efficiency),
        "allocation": _allocation(frames["targeting"]),
    }
    payload["segment_count"] = len(payload["segments"])
    payload["cases_in_segments"] = int(sum(s["n"] for s in payload["segments"]))

    if "population" in frames:
        payload["population"] = {k: _plain(v) for k, v in frames["population"].items()}
    if "groups" in frames:
        payload["groups"] = _groups(frames["groups"])
    if "failures" in frames:
        payload["failures"] = _failures(frames["failures"])
    if "checks" in frames:
        payload["checks"] = _checks(frames["checks"])
    if "experiments" in frames:
        payload["experiments"] = _experiments(frames["experiments"])
    if "mismatch" in frames:
        payload["mismatch"] = _segments(frames["mismatch"])
    return payload
