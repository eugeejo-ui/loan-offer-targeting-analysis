# Phase 2 — 공수 측정 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 분석 모집단 29,131건 각각에 은행 직원이 실제로 손을 댄 시간(공수 E)을 측정한다. 긴 작업 구간을 어떻게 자르느냐(캡)에 따라 케이스 순위가 흔들리는지도 검증한다.

**Architecture:** 공수는 워크플로 항목(W_)의 작업 구간(start/resume → 같은 항목의 다음 이벤트) 시간 합으로 잰다 (P5). 판정 로직은 새 모듈 `analysis/effort.py`에 두고 합성 이벤트로 테스트한다. 스크립트 `07`은 구간을 만들고 분포와 캡을, `08`은 케이스 공수와 견고성을 산출한다.

**Tech Stack:** Python 3.12, pandas 3.0.5, pytest (Windows PowerShell 5.1)

**Spec:** `CLAUDE.md` §5 P5, §6 Phase 2 / Phase 1 결론 `docs/01_process_baseline.md` §7

## Global Constraints

- 모집단은 `loader.load_population()`으로만 불러온다 (29,131건).
- 공수 = W_ 항목의 작업 구간 시간. **대기 시간(suspend 상태, 고객 보유 구간)은 공수에 넣지 않는다** (Phase 1 §7).
- 이벤트 수는 보조 지표다. 시스템 계정(User_1)의 이벤트는 세지 않는다.
- ate_abort는 사유를 판정하지 않는다. 작업 구간은 abort와 무관하게 측정된다 (사전 탐색: abort는 모두 suspend 상태에서 발생).
- 스크립트 번호 `07~08`, 산출 파일 접두어 `p2_`. 차트는 만들지 않는다.
- 문서의 수치는 스크립트 출력에서만 옮긴다.
- PowerShell 5.1: `&&` 대신 `;`. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## 사전 탐색 (계획 설계용, 수치는 Task에서 재산출)

임시 스크립트로 모집단의 W_ 이벤트를 훑었다.
- 작업 구간을 끝내는 이벤트는 suspend와 complete이고, 드물게 start가 연달아 오는 경우가 있다. ate_abort·withdraw로 끝나는 구간은 없다
- 구간 길이 중앙값은 활동별 1~3분이다. 1시간 초과 구간은 0.66%인데 전체 시간의 28.5%를 차지하고, 8시간 초과 구간은 0.09%인데 9.7%를 차지한다
- 구간을 시작한 직원과 끝낸 직원이 같은 경우가 99.4%다. 긴 구간은 같은 직원이 항목을 연 채로 둔 것일 가능성이 크다
- User_1이 시작한 구간은 없다. 시스템 계정 제외는 작업시간 지표에서 자동으로 충족된다
- W_Assess potential fraud는 p99가 약 9.6시간으로 다른 활동보다 훨씬 길다. 고정 캡 하나로 자르면 원래 긴 업무를 왜곡한다

→ **주 지표는 활동별 p99 캡**으로 정하고, 캡 없음·1시간·4시간 캡과 직원 이벤트 수를 대안으로 두어 케이스 순위의 견고성을 본다.

## File Structure

| 파일 | 책임 |
|---|---|
| `analysis/effort.py` | 작업 구간 추출, 활동별 캡, 캡 적용, 케이스 공수 집계, 직원 이벤트 수 |
| `analysis/07_active_segments.py` | 구간 생성, 활동별 분포, 긴 구간의 꼬리, 활동별 p99 캡 |
| `analysis/08_case_effort.py` | 캡 방식별 케이스 공수, 순위 상관, 결과별·활동별 공수 |
| `tests/test_effort.py` | 단위 테스트 5개 |
| `docs/02_effort.md` | Phase 2 결론 문서 |

---

### Task 1: 공수 모듈

**Files:**
- Create: `analysis/effort.py`, `tests/test_effort.py`

**Interfaces:**
- Consumes: `config.ACT, CASE, LIFECYCLE, RESOURCE, SYSTEM_RESOURCE, TS`
- Produces:
  - `active_segments(events) -> pd.DataFrame` — 컬럼 `case:concept:name, concept:name, org:resource, start_ts, end_ts, end_lifecycle, hours`
  - `activity_caps(segments, q: float = 0.99) -> pd.Series` — index 활동, 값 시간
  - `cap_hours(segments, cap: float | pd.Series) -> pd.Series` — segments와 같은 index
  - `case_effort(segments, hours: pd.Series, cases: pd.Index) -> pd.DataFrame` — index 케이스, 컬럼 `effort_hours` + 활동별 시간 (W_ 항목이 없는 케이스는 0)
  - `staff_event_counts(events, cases: pd.Index) -> pd.Series` — name `staff_events`

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_effort.py`

```python
import pandas as pd

from effort import (active_segments, activity_caps, cap_hours, case_effort,
                    staff_event_counts)

H = pd.Timedelta(hours=1)
T0 = pd.Timestamp("2016-01-01 09:00", tz="UTC")
CASES = pd.Index(["A", "B"], name="case:concept:name")


def _events():
    rows = [
        ("A", "W_Call after offers", "schedule", T0, "User_1"),
        ("A", "W_Call after offers", "start", T0 + 1 * H, "User_5"),
        ("A", "W_Call after offers", "suspend", T0 + 1.1 * H, "User_5"),
        ("A", "W_Call after offers", "resume", T0 + 5 * H, "User_5"),
        ("A", "W_Call after offers", "complete", T0 + 5.2 * H, "User_5"),
        ("A", "W_Validate application", "start", T0 + 6 * H, "User_6"),
        ("A", "A_Validating", "complete", T0 + 6 * H, "User_6"),
        ("B", "A_Create Application", "complete", T0, "User_1"),
    ]
    return pd.DataFrame(rows, columns=["case:concept:name", "concept:name",
                                       "lifecycle:transition", "time:timestamp", "org:resource"])


def test_active_segments_pair_start_resume_with_next_event():
    seg = active_segments(_events())
    assert list(seg["hours"].round(6)) == [0.1, 0.2]
    assert list(seg["end_lifecycle"]) == ["suspend", "complete"]


def test_cap_hours_fixed_and_per_activity():
    seg = active_segments(_events())
    assert list(cap_hours(seg, 0.15).round(6)) == [0.1, 0.15]
    assert list(cap_hours(seg, pd.Series({"W_Call after offers": 0.05})).round(6)) == [0.05, 0.05]


def test_activity_caps_quantile():
    caps = activity_caps(active_segments(_events()), q=1.0)
    assert round(caps["W_Call after offers"], 6) == 0.2


def test_case_effort_includes_cases_without_work_items():
    seg = active_segments(_events())
    eff = case_effort(seg, seg["hours"], CASES)
    assert round(eff.loc["A", "effort_hours"], 6) == 0.3
    assert round(eff.loc["A", "W_Call after offers"], 6) == 0.3
    assert eff.loc["B", "effort_hours"] == 0


def test_staff_event_counts_excludes_system_account():
    assert staff_event_counts(_events(), CASES).to_dict() == {"A": 6, "B": 0}
```

- [ ] **Step 2: 실패 확인** — Run: `.venv\Scripts\python -m pytest tests/test_effort.py -q` / Expected: `No module named 'effort'`

- [ ] **Step 3: `analysis/effort.py` 구현**

```python
"""Hands-on effort per case, measured as active time on workflow items (P5)."""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, LIFECYCLE, RESOURCE, SYSTEM_RESOURCE, TS

ACTIVE_FROM = ("start", "resume")


def active_segments(events: pd.DataFrame) -> pd.DataFrame:
    """One row per active stretch of a W_ item: from start/resume to the item's next event."""
    w = events[events[ACT].str.startswith("W_")].sort_values([CASE, ACT, TS], kind="stable")
    g = w.groupby([CASE, ACT], sort=False)
    seg = w.assign(end_ts=g[TS].shift(-1), end_lifecycle=g[LIFECYCLE].shift(-1))
    seg = seg[seg[LIFECYCLE].isin(ACTIVE_FROM) & seg["end_ts"].notna()]
    seg = seg.rename(columns={TS: "start_ts"})[[CASE, ACT, RESOURCE, "start_ts", "end_ts", "end_lifecycle"]]
    seg["hours"] = (seg["end_ts"] - seg["start_ts"]).dt.total_seconds() / 3600
    return seg.reset_index(drop=True)


def activity_caps(segments: pd.DataFrame, q: float = 0.99) -> pd.Series:
    return segments.groupby(ACT)["hours"].quantile(q)


def cap_hours(segments: pd.DataFrame, cap: float | pd.Series) -> pd.Series:
    limit = segments[ACT].map(cap) if isinstance(cap, pd.Series) else cap
    return segments["hours"].clip(upper=limit)


def case_effort(segments: pd.DataFrame, hours: pd.Series, cases: pd.Index) -> pd.DataFrame:
    """Total and per-activity effort hours per case; cases without work items get zero."""
    by_act = hours.groupby([segments[CASE], segments[ACT]]).sum().unstack(fill_value=0.0)
    by_act = by_act.reindex(cases, fill_value=0.0)
    by_act.insert(0, "effort_hours", by_act.sum(axis=1))
    return by_act


def staff_event_counts(events: pd.DataFrame, cases: pd.Index) -> pd.Series:
    staff = events[events[RESOURCE] != SYSTEM_RESOURCE]
    return staff.groupby(CASE).size().reindex(cases, fill_value=0).rename("staff_events")
```

- [ ] **Step 4: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests -q` / Expected: 29 passed (기존 24 + 5)

- [ ] **Step 5: 커밋**

```powershell
git add analysis/effort.py tests/test_effort.py; git commit -m "feat: add effort measurement module"
```

---

### Task 2: 작업 구간 분포와 캡

**Files:**
- Create: `analysis/07_active_segments.py`

**Interfaces:**
- Consumes: `load_population`, `active_segments`, `activity_caps`
- Produces: `outputs/p2_active_segments.parquet` (Task 3 입력), `p2_segment_hours_by_activity.csv`, `p2_segment_tail.csv`, `p2_segment_caps.csv`

- [ ] **Step 1: `analysis/07_active_segments.py` 작성**

```python
"""Phase 2 — active (hands-on) stretches of workflow items, and where their time concentrates.

Run from the project root:

    .venv\\Scripts\\python analysis/07_active_segments.py
"""
from __future__ import annotations

import pandas as pd

from config import ACT, OUT_DIR, RESOURCE, SYSTEM_RESOURCE
from effort import active_segments, activity_caps
from loader import load_population

TAIL_HOURS = [0.25, 0.5, 1, 2, 4, 8]


def main() -> None:
    ev, _ = load_population()
    seg = active_segments(ev)
    seg.to_parquet(OUT_DIR / "p2_active_segments.parquet", index=False)
    print(f"active segments={len(seg):,}  "
          f"started by {SYSTEM_RESOURCE}: {seg[RESOURCE].eq(SYSTEM_RESOURCE).mean():.1%}")
    print(f"\n=== what ends a segment ===\n{seg['end_lifecycle'].value_counts().to_string()}")

    dist = seg.groupby(ACT)["hours"].describe(percentiles=[0.5, 0.9, 0.99]).round(3)
    dist["total_hours"] = seg.groupby(ACT)["hours"].sum().round(1)
    dist.to_csv(OUT_DIR / "p2_segment_hours_by_activity.csv", encoding="utf-8-sig")
    print(f"\n=== segment hours by activity ===\n{dist.to_string()}")

    total = seg["hours"].sum()
    tail = pd.DataFrame([{
        "threshold_hours": h,
        "segment_share": round(float((seg["hours"] > h).mean()), 4),
        "hours_share": round(float(seg.loc[seg["hours"] > h, "hours"].sum() / total), 3),
    } for h in TAIL_HOURS])
    tail.to_csv(OUT_DIR / "p2_segment_tail.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== long-segment tail ===\n{tail.to_string(index=False)}")

    caps = activity_caps(seg, 0.99).round(3).rename("cap_hours_p99")
    caps.to_csv(OUT_DIR / "p2_segment_caps.csv", encoding="utf-8-sig")
    print(f"\n=== per-activity cap (p99) ===\n{caps.to_string()}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/07_active_segments.py`
기록 대상: 구간 수, User_1 시작 비중(0% 기대), 구간을 끝내는 이벤트 분포, 꼬리 표 → **판단 지점 1**

- [ ] **Step 3: 커밋**

```powershell
git add analysis/07_active_segments.py outputs/p2_active_segments.parquet outputs/p2_segment_hours_by_activity.csv outputs/p2_segment_tail.csv outputs/p2_segment_caps.csv; git commit -m "feat: extract active work segments and per-activity caps"
```

---

### Task 3: 케이스 공수와 견고성

**Files:**
- Create: `analysis/08_case_effort.py`

**Interfaces:**
- Consumes: `outputs/p2_active_segments.parquet`, `activity_caps`, `cap_hours`, `case_effort`, `staff_event_counts`
- Produces: `outputs/p2_case_effort.parquet` — index 케이스, 컬럼 `effort_hours`(= 주 지표, 활동별 p99 캡), 활동별 시간, `effort_raw`, `effort_cap_p99`, `effort_cap_1h`, `effort_cap_4h`, `staff_events` → **Phase 5의 E 입력**. 그 밖에 `p2_effort_rank_corr.csv`, `p2_effort_by_outcome.csv`, `p2_effort_by_activity.csv`

- [ ] **Step 1: `analysis/08_case_effort.py` 작성**

```python
"""Phase 2 — effort per case under several capping rules, and how robust its ranking is.

Run from the project root, after 07_active_segments.py:

    .venv\\Scripts\\python analysis/08_case_effort.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from effort import activity_caps, cap_hours, case_effort, staff_event_counts
from loader import load_population

FIXED_CAPS = {"cap_1h": 1.0, "cap_4h": 4.0}
MIN_RANK_CORR = 0.9


def main() -> None:
    ev, oc = load_population()
    seg = pd.read_parquet(OUT_DIR / "p2_active_segments.parquet")
    cases = oc.index

    variants = {"raw": seg["hours"], "cap_p99": cap_hours(seg, activity_caps(seg, 0.99))}
    variants |= {name: cap_hours(seg, h) for name, h in FIXED_CAPS.items()}
    primary = case_effort(seg, variants["cap_p99"], cases)
    effort = pd.DataFrame({f"effort_{k}": case_effort(seg, v, cases)["effort_hours"]
                           for k, v in variants.items()})
    effort["staff_events"] = staff_event_counts(ev, cases)
    print(f"cases with zero effort: {int((effort['effort_cap_p99'] == 0).sum()):,}")
    print(f"total hours by variant: { {k: round(float(v.sum()), 1) for k, v in variants.items()} }")

    corr = effort.corr(method="spearman").round(3)
    corr.to_csv(OUT_DIR / "p2_effort_rank_corr.csv", encoding="utf-8-sig")
    print(f"\n=== case-level Spearman rank correlation ===\n{corr.to_string()}")
    weakest = corr.loc["effort_cap_p99"].drop("effort_cap_p99").min()
    verdict = "robust" if weakest >= MIN_RANK_CORR else "carry alternatives into Phase 5"
    print(f"weakest correlation with primary (cap_p99): {weakest:.3f} -> {verdict}")

    with_outcome = effort.join(oc["outcome"])
    by_outcome = with_outcome.groupby("outcome").agg(
        cases=("effort_cap_p99", "size"),
        median_hours=("effort_cap_p99", "median"),
        mean_hours=("effort_cap_p99", "mean"),
        total_hours=("effort_cap_p99", "sum"),
        median_staff_events=("staff_events", "median"),
    )
    by_outcome["total_share"] = by_outcome["total_hours"] / by_outcome["total_hours"].sum()
    by_outcome = by_outcome.round(3)
    by_outcome.to_csv(OUT_DIR / "p2_effort_by_outcome.csv", encoding="utf-8-sig")
    print(f"\n=== effort (cap_p99) by outcome ===\n{by_outcome.to_string()}")

    by_act = primary.drop(columns="effort_hours").sum().sort_values(ascending=False)
    by_act = pd.DataFrame({"hours": by_act.round(1), "share": (by_act / by_act.sum()).round(3)})
    by_act.to_csv(OUT_DIR / "p2_effort_by_activity.csv", encoding="utf-8-sig")
    print(f"\n=== effort (cap_p99) by activity ===\n{by_act.to_string()}")

    primary.join(effort).to_parquet(OUT_DIR / "p2_case_effort.parquet")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/08_case_effort.py`
기록 대상: 공수 0 케이스 수, 캡 방식별 총 시간, 순위 상관 표 → **판단 지점 2**, 결과별 공수와 총량 비중 → **판단 지점 4**, 활동별 비중(W_Handle leads 포함) → **판단 지점 3**

- [ ] **Step 3: 커밋**

```powershell
git add analysis/08_case_effort.py outputs/p2_case_effort.parquet outputs/p2_effort_rank_corr.csv outputs/p2_effort_by_outcome.csv outputs/p2_effort_by_activity.csv; git commit -m "feat: measure case effort and check ranking robustness"
```

---

### Task 4: Phase 2 결론 문서와 CLAUDE.md 반영

**Files:**
- Create: `docs/02_effort.md`
- Modify: `CLAUDE.md` (§6 진행 현황표·Phase 2 절·영향받는 Phase 절, §12), 이 파일의 진행 기록

- [ ] **Step 1: `docs/02_effort.md` 작성** — 모든 수치 옆에 `outputs/p2_*` 출처

```markdown
# Phase 2 — 공수 측정

## 1. 측정 정의
(작업 구간 = start/resume → 같은 항목의 다음 이벤트. 대기와 고객 보유 시간 제외. 시스템 계정 제외 여부)

## 2. 작업 구간의 분포와 긴 꼬리
(p2_segment_hours_by_activity.csv, p2_segment_tail.csv)

## 3. 캡 규칙과 그 근거
(p2_segment_caps.csv — 활동별 p99)

## 4. 견고성 — 캡 방식과 이벤트 수에 따른 순위 상관
(p2_effort_rank_corr.csv)

## 5. 케이스 공수 — 결과별·활동별
(p2_effort_by_outcome.csv, p2_effort_by_activity.csv)

## 6. 다음 Phase로 넘기는 것
```

- [ ] **Step 2: CLAUDE.md 반영** — §6 진행 현황표 Phase 2 행(✅, 한 줄 결론), Phase 2 절(판단 지점별 결과), Phase 5(E 정의 확정), Phase 7(실패 케이스 공수 출발값), §12 결정 로그

- [ ] **Step 3: 이 파일의 "진행 기록"에 실행 중 변경·결과 요약·커밋 목록 추가**

- [ ] **Step 4: 사용자 보고** — 판단 지점 결과와 방향 변경을 보고하고, Phase 3 진행계획 착수 여부를 확인한다

- [ ] **Step 5: 커밋**

```powershell
git add docs/02_effort.md docs/plans/phase-02-effort.md CLAUDE.md; git commit -m "docs: record phase 2 effort measurement"
```

---

## 판단 지점

1. **캡 규칙:** 긴 구간이 합계를 좌우하면(사전 탐색: 1시간 초과 0.66%가 시간의 28.5%) 활동별 p99 캡을 주 지표로 확정한다. 고정 캡이 아닌 이유는 사기 심사처럼 원래 긴 업무를 보존하기 위해서다
2. **견고성:** 주 지표와 대안(캡 없음, 1시간, 4시간, 직원 이벤트 수)의 케이스 순위 상관(Spearman) 최솟값이 0.9 이상이면 주 지표 하나만 Phase 5로 넘긴다. 0.9 미만이면 대안을 민감도 분석용으로 Phase 5에 함께 넘긴다
3. **W_Handle leads:** 작업 구간은 직원이 쓴 실제 시간이므로 포함한다. 비중만 보고한다
4. **결과별 공수:** 취소·거절 케이스가 전체 공수에서 차지하는 비중을 Phase 7의 출발값으로 기록한다. 여기서는 해석하지 않는다
5. **공수 0 케이스:** 있으면 원인(W_ 항목 부재, 구간 미종료)을 확인하고 Phase 5에서의 처리를 정한다

## 진행 기록

| 날짜 | 내용 |
|---|---|
| 2026-09-11 | 진행계획 작성. 사전 탐색(구간 길이 분포, 긴 꼬리, 시작·종료 직원 일치, User_1 미시작, abort는 suspend 상태에서만)을 캡 규칙과 견고성 검증 설계에 반영. 사용자 확인 대기 |
