# Phase 1 — 프로세스 현황 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 분석 모집단 29,131건에서 신청이 어디서 빠지는지, 경과시간이 은행과 고객 중 누구의 손에서 흐르는지, 30일 자동 취소 규칙이 실재하는지 확인한다. 전화 업무의 ate_abort 전후에 어떤 케이스 전이가 붙는지도 본다.

**Architecture:** 판정 로직은 새 모듈 `analysis/process.py`에 두고 pytest로 합성 이벤트에 대해 검증한다. 모집단 로딩은 `loader.load_population()` 하나로 통일한다. 실데이터 처리는 스크립트 `04~06`이 맡고 결과를 `outputs/p1_*`로 떨군다.

**Tech Stack:** Python 3.12, pandas 3.0.5, pytest (Windows PowerShell 5.1)

**Spec:** `CLAUDE.md` 5장 P2·P7, 6장 Phase 1, 2-2장 ate_abort 주의 / Phase 0 결론 `docs/00_scope.md`

## Global Constraints

- 모집단은 `outputs/p0_case_outcomes.parquet`의 `in_population == True` (29,131건)만 쓴다. 스크립트는 `loader.load_population()`으로만 불러온다.
- 결과 판정은 A_ 종료 이벤트로만 한다. CreditScore·Selected·Accepted는 쓰지 않는다 (P2 결과 누수).
- ate_abort는 **사유를 판정하지 않는다.** 인접한 케이스 전이의 분포만 보고, 결론은 "이 순서로 해석 가능한 범위"로 제한한다 (2-2장).
- 소요시간을 성사의 원인 변수로 해석하지 않는다 (P7).
- 스크립트 번호 `04~06`, 산출 파일 접두어 `p1_`.
- 차트는 만들지 않는다. 산출물 단계에서 dataviz 스킬로 일괄 제작한다 (표현 일관성).
- 문서의 수치는 스크립트 출력에서만 옮긴다.
- PowerShell 5.1: `&&` 대신 `;`. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## 사전 탐색 (계획 설계용, 수치는 Task에서 재산출)

임시 스크립트로 모집단의 흐름을 훑었다. 다음 신호가 있어서 설계에 반영했다.
- 취소 케이스 대부분이 오퍼 회신(O_Returned) 전에 멈춘다 → Task 2의 이탈 위치 표
- 취소 대부분이 시스템 계정이고, 마지막 오퍼 발송 후 약 30일에 몰린다 → Task 3의 30일 규칙 점검
- W_Call after offers의 ate_abort 다수가 1초 안에 A_Validating으로 이어진다 → Task 4의 인접 전이 분류
- A_Submitted가 일부 케이스에만 있다 → Task 2의 접수 채널 점검

## File Structure

| 파일 | 책임 |
|---|---|
| `analysis/config.py` | `CASE_OUTCOMES` 경로 상수 추가 |
| `analysis/loader.py` | `load_population()` 추가 — 모집단 이벤트와 결과를 함께 반환 |
| `analysis/process.py` | 마일스톤, 퍼널, 이탈 위치, 구간 소요, 보유 주체 시간, 취소 간격, ate_abort 인접 전이 |
| `analysis/04_process_funnel.py` | 퍼널·이탈 위치·구간 소요·A_Submitted 점검 |
| `analysis/05_holder_and_cancel.py` | 은행/고객 보유 시간, 30일 규칙 |
| `analysis/06_ate_abort_context.py` | 전화 업무 ate_abort의 인접 전이 |
| `tests/test_loader.py`, `tests/test_process.py` | 단위 테스트 (신규 8개) |
| `docs/01_process_baseline.md` | Phase 1 결론 문서 |

---

### Task 1: 모집단 로더

**Files:**
- Modify: `analysis/config.py`, `analysis/loader.py`
- Test: `tests/test_loader.py`

**Interfaces:**
- Produces: `config.CASE_OUTCOMES: Path`, `load_population(outcomes_path: Path = CASE_OUTCOMES, cache: Path = CACHE_PARQUET) -> tuple[pd.DataFrame, pd.DataFrame]` — (모집단 이벤트, 모집단 결과 테이블)

- [ ] **Step 1: 실패하는 테스트 추가** — `tests/test_loader.py` 끝에

```python
from loader import load_population  # noqa: E402


def test_load_population_filters_to_in_population(tmp_path):
    cache = tmp_path / "events.parquet"
    pd.DataFrame({
        "case:concept:name": ["a", "b"],
        "concept:name": ["A_Create Application", "A_Create Application"],
        "time:timestamp": pd.to_datetime(["2016-01-01", "2016-01-02"], utc=True),
    }).to_parquet(cache, index=False)
    outcomes = tmp_path / "outcomes.parquet"
    pd.DataFrame(
        {"outcome": ["success", "open"], "in_population": [True, False]},
        index=pd.Index(["a", "b"], name="case:concept:name"),
    ).to_parquet(outcomes)
    ev, oc = load_population(outcomes_path=outcomes, cache=cache)
    assert list(oc.index) == ["a"]
    assert list(ev["case:concept:name"]) == ["a"]
```

- [ ] **Step 2: 실패 확인** — Run: `.venv\Scripts\python -m pytest tests/test_loader.py -q` / Expected: `ImportError: cannot import name 'load_population'`

- [ ] **Step 3: 구현**

`analysis/config.py`의 `OUT_DIR` 아래에 추가:

```python
CASE_OUTCOMES = OUT_DIR / "p0_case_outcomes.parquet"
```

`analysis/loader.py`: import를 `from config import BOOL_ATTRS, CACHE_PARQUET, CASE, CASE_OUTCOMES, SOURCE_XES, TS`로 바꾸고 파일 끝에 추가:

```python
def load_population(outcomes_path: Path = CASE_OUTCOMES,
                    cache: Path = CACHE_PARQUET) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Events and outcomes of the Phase 0 analysis population only."""
    oc = pd.read_parquet(outcomes_path)
    oc = oc[oc["in_population"]]
    ev = load_events(cache=cache)
    return ev[ev[CASE].isin(oc.index)], oc
```

- [ ] **Step 4: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests/test_loader.py -q` / Expected: 4 passed

- [ ] **Step 5: 커밋**

```powershell
git add analysis/config.py analysis/loader.py tests/test_loader.py; git commit -m "feat: add analysis population loader"
```

---

### Task 2: 마일스톤·퍼널·이탈 위치·구간 소요

**Files:**
- Create: `analysis/process.py`, `analysis/04_process_funnel.py`, `tests/test_process.py`

**Interfaces:**
- Consumes: `load_population()`
- Produces (process.py):
  - 상수 `SENT`, `MILESTONES`, `END_EVENTS`, `TO_CUSTOMER`, `TO_BANK`
  - `milestone_first_ts(events) -> pd.DataFrame` — index 케이스, 컬럼 마일스톤(MILESTONES 순서), 값 최초 시각. 두 가지 O_Sent는 `O_Sent`로 합친다
  - `funnel_by_outcome(first_ts, outcome: pd.Series) -> pd.DataFrame` — index 마일스톤, 컬럼 결과별 도달 케이스 수 + `all`
  - `last_milestone_before_end(first_ts) -> pd.Series` — 종료 이벤트를 뺀 마일스톤 중 MILESTONES 순서상 가장 뒤에 도달한 것
  - `pair_durations(first_ts, pairs: list[tuple[str, str]]) -> pd.DataFrame` — 컬럼 `"{a}→{b}"`, 값 일수

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_process.py`

```python
import pandas as pd

from process import (funnel_by_outcome, last_milestone_before_end,
                     milestone_first_ts, pair_durations)

DAY = pd.Timedelta(days=1)
T0 = pd.Timestamp("2016-01-01", tz="UTC")


def _ev(rows):
    return pd.DataFrame(rows, columns=["case:concept:name", "concept:name",
                                       "time:timestamp", "org:resource"])


def _events():
    return _ev([
        ("S", "A_Create Application", T0, "User_1"),
        ("S", "O_Sent (online only)", T0 + 1 * DAY, "User_5"),
        ("S", "O_Returned", T0 + 11 * DAY, "User_5"),
        ("S", "A_Validating", T0 + 11 * DAY, "User_5"),
        ("S", "A_Incomplete", T0 + 12 * DAY, "User_5"),
        ("S", "A_Validating", T0 + 15 * DAY, "User_5"),
        ("S", "A_Pending", T0 + 16 * DAY, "User_5"),
        ("C", "A_Create Application", T0, "User_1"),
        ("C", "O_Sent (mail and online)", T0 + 2 * DAY, "User_7"),
        ("C", "A_Cancelled", T0 + 32 * DAY, "User_1"),
    ])


def test_milestone_first_ts_merges_sent_variants():
    ft = milestone_first_ts(_events())
    assert ft.loc["S", "O_Sent"] == T0 + DAY
    assert ft.loc["C", "O_Sent"] == T0 + 2 * DAY
    assert pd.isna(ft.loc["C", "O_Returned"])
    assert list(ft.columns).index("O_Sent") < list(ft.columns).index("O_Returned")


def test_funnel_by_outcome():
    ft = milestone_first_ts(_events())
    f = funnel_by_outcome(ft, pd.Series({"S": "success", "C": "cancelled"}))
    assert f.loc["O_Sent", "all"] == 2
    assert f.loc["O_Returned", "success"] == 1 and f.loc["O_Returned", "cancelled"] == 0


def test_last_milestone_before_end():
    last = last_milestone_before_end(milestone_first_ts(_events()))
    assert last["C"] == "O_Sent"
    assert last["S"] == "A_Incomplete"


def test_pair_durations_in_days():
    d = pair_durations(milestone_first_ts(_events()), [("O_Sent", "O_Returned")])
    assert d.loc["S", "O_Sent→O_Returned"] == 10
    assert pd.isna(d.loc["C", "O_Sent→O_Returned"])
```

- [ ] **Step 2: 실패 확인** — Run: `.venv\Scripts\python -m pytest tests/test_process.py -q` / Expected: `No module named 'process'`

- [ ] **Step 3: `analysis/process.py` 구현 (1차)**

```python
"""Process milestones, who holds the case over time, and the context of work-item aborts."""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import ACT, CASE, RESOURCE, SYSTEM_RESOURCE, TS

SENT = ("O_Sent (mail and online)", "O_Sent (online only)")
MILESTONES = [
    "A_Create Application", "A_Submitted", "A_Concept", "A_Accepted",
    "O_Create Offer", "O_Sent", "A_Complete", "O_Returned", "A_Validating",
    "A_Incomplete", "A_Pending", "A_Denied", "A_Cancelled",
]
END_EVENTS = ("A_Pending", "A_Denied", "A_Cancelled")
TO_CUSTOMER = SENT + ("A_Incomplete",)
TO_BANK = ("O_Returned", "A_Validating")


def milestone_first_ts(events: pd.DataFrame) -> pd.DataFrame:
    ev = events.assign(milestone=events[ACT].where(~events[ACT].isin(SENT), "O_Sent"))
    ev = ev[ev["milestone"].isin(MILESTONES)]
    wide = ev.groupby([CASE, "milestone"])[TS].min().unstack()
    return wide.reindex(columns=[m for m in MILESTONES if m in wide.columns])


def funnel_by_outcome(first_ts: pd.DataFrame, outcome: pd.Series) -> pd.DataFrame:
    reached = first_ts.notna()
    table = reached.groupby(outcome.reindex(first_ts.index)).sum().T
    table["all"] = reached.sum()
    return table


def last_milestone_before_end(first_ts: pd.DataFrame) -> pd.Series:
    pre = [m for m in first_ts.columns if m not in END_EVENTS]
    reached = first_ts[pre].notna()
    return reached.iloc[:, ::-1].idxmax(axis=1).where(reached.any(axis=1))


def pair_durations(first_ts: pd.DataFrame, pairs: list[tuple[str, str]]) -> pd.DataFrame:
    return pd.DataFrame({
        f"{a}→{b}": (first_ts[b] - first_ts[a]).dt.total_seconds() / 86400 for a, b in pairs
    })
```

- [ ] **Step 4: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests/test_process.py -q` / Expected: 4 passed

- [ ] **Step 5: `analysis/04_process_funnel.py` 작성**

```python
"""Phase 1 — where applications leave the process, and how long each stage takes.

Run from the project root:

    .venv\\Scripts\\python analysis/04_process_funnel.py
"""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, OUT_DIR, RESOURCE, SYSTEM_RESOURCE, TS
from loader import load_population
from process import (funnel_by_outcome, last_milestone_before_end,
                     milestone_first_ts, pair_durations)

STAGE_PAIRS = [
    ("A_Create Application", "O_Sent"),
    ("O_Sent", "O_Returned"),
    ("O_Returned", "A_Pending"),
    ("O_Returned", "A_Denied"),
    ("O_Sent", "A_Cancelled"),
]


def main() -> None:
    ev, oc = load_population()
    first_ts = milestone_first_ts(ev)
    print(f"population cases={len(oc):,}")

    funnel = funnel_by_outcome(first_ts, oc["outcome"])
    funnel.to_csv(OUT_DIR / "p1_funnel_by_outcome.csv", encoding="utf-8-sig")
    print(f"\n=== cases reaching each milestone ===\n{funnel.to_string()}")

    failed = oc.index[oc["outcome"] != "success"]
    last = last_milestone_before_end(first_ts.loc[failed]).rename("last_milestone")
    dropout = pd.crosstab(last, oc.loc[failed, "outcome"], margins=True)
    dropout.to_csv(OUT_DIR / "p1_dropout_last_milestone.csv", encoding="utf-8-sig")
    print(f"\n=== furthest milestone reached by cancelled / denied cases ===\n{dropout.to_string()}")

    stages = pair_durations(first_ts, STAGE_PAIRS)
    summary = stages.describe(percentiles=[0.5, 0.9]).T[["count", "50%", "90%"]].round(2)
    summary.to_csv(OUT_DIR / "p1_stage_durations.csv", encoding="utf-8-sig")
    print(f"\n=== stage durations (days) ===\n{summary.to_string()}")

    # Is A_Submitted an intake-time channel marker? Check who records it, when, and for whom.
    sub = ev[ev[ACT] == "A_Submitted"]
    sub_cases = sub[CASE].unique()
    gap_s = (sub.groupby(CASE)[TS].min() - first_ts["A_Create Application"].reindex(sub_cases)).dt.total_seconds()
    has_sub = pd.Series(oc.index.isin(sub_cases), index=oc.index, name="has_submitted")
    app_type = ev.groupby(CASE)["case:ApplicationType"].first().reindex(oc.index)
    channel = pd.crosstab(has_sub, oc["outcome"], margins=True)
    channel.to_csv(OUT_DIR / "p1_submitted_channel.csv", encoding="utf-8-sig")
    print(f"\n=== A_Submitted presence by outcome ===\n{channel.to_string()}")
    print(pd.crosstab(has_sub, oc["outcome"], normalize="index").round(3).to_string())
    print(f"\n{pd.crosstab(has_sub, app_type).to_string()}")
    print(f"A_Submitted recorded by {SYSTEM_RESOURCE}: {sub[RESOURCE].eq(SYSTEM_RESOURCE).mean():.1%}")
    print(f"seconds from A_Create Application to A_Submitted: "
          f"median {gap_s.median():.1f}, p90 {gap_s.quantile(0.9):.1f}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 실데이터 실행** — Run: `.venv\Scripts\python analysis/04_process_funnel.py`
기록 대상:
- 퍼널의 `A_Create Application` `all` = 29,131 (모집단 일치 검증)
- 취소 케이스의 `last_milestone` 분포 → **판단 지점 1**
- A_Submitted: 시스템 기록 비중, 생성 직후 여부(초 단위), 결과별·신청 유형별 비중 → **판단 지점 5**

- [ ] **Step 7: 커밋**

```powershell
git add analysis/process.py analysis/04_process_funnel.py tests/test_process.py outputs/p1_funnel_by_outcome.csv outputs/p1_dropout_last_milestone.csv outputs/p1_stage_durations.csv outputs/p1_submitted_channel.csv; git commit -m "feat: reconstruct process funnel and dropout points"
```

---

### Task 3: 은행/고객 보유 시간과 30일 규칙

**Files:**
- Modify: `analysis/process.py`, `tests/test_process.py`
- Create: `analysis/05_holder_and_cancel.py`

**Interfaces:**
- Produces:
  - `holder_time(events) -> pd.DataFrame` — index 케이스, 컬럼 `bank_days`, `customer_days`
  - `cancel_after_last_sent(events) -> pd.DataFrame` — index 취소 케이스, 컬럼 `cancel_ts`, `cancel_by_system`, `last_sent_ts`, `gap_days`

보유 주체 규칙: 케이스는 은행에서 시작한다. 오퍼 발송(O_Sent 2종)이나 보완 요청(A_Incomplete)에서 고객으로 넘어가고, 오퍼 회신(O_Returned)이나 심사 재개(A_Validating)에서 은행으로 돌아온다. 첫 종료 이벤트에서 시계를 멈춘다.

- [ ] **Step 1: 실패하는 테스트 추가** — `tests/test_process.py`: import에 `cancel_after_last_sent, holder_time`을 추가하고 끝에 다음을 붙인다

```python
def test_holder_time_splits_bank_and_customer():
    h = holder_time(_events())
    assert h.loc["S", "bank_days"] == 3 and h.loc["S", "customer_days"] == 13
    assert h.loc["C", "bank_days"] == 2 and h.loc["C", "customer_days"] == 30


def test_cancel_after_last_sent():
    c = cancel_after_last_sent(_events())
    assert list(c.index) == ["C"]
    assert c.loc["C", "gap_days"] == 30
    assert bool(c.loc["C", "cancel_by_system"]) is True
```

- [ ] **Step 2: 실패 확인** — Expected: `ImportError: cannot import name 'cancel_after_last_sent'`

- [ ] **Step 3: `analysis/process.py`에 구현 추가**

```python
def holder_time(events: pd.DataFrame) -> pd.DataFrame:
    """Split each case's elapsed time into bank-held and customer-held days.

    The case starts with the bank, passes to the customer when an offer is
    sent or documents are requested, and returns to the bank when the offer
    comes back or validation resumes. The clock stops at the first end event.
    """
    keep = ("A_Create Application",) + TO_CUSTOMER + TO_BANK + END_EVENTS
    ev = events[events[ACT].isin(keep)].sort_values([CASE, TS], kind="stable")
    rows = []
    for case, g in ev.groupby(CASE, sort=False):
        holder, since = "bank", g[TS].iloc[0]
        spent = {"bank": 0.0, "customer": 0.0}
        for act, ts in zip(g[ACT], g[TS]):
            if act in END_EVENTS:
                spent[holder] += (ts - since).total_seconds()
                break
            new = "customer" if act in TO_CUSTOMER else "bank" if act in TO_BANK else holder
            if new != holder:
                spent[holder] += (ts - since).total_seconds()
                holder, since = new, ts
        rows.append({CASE: case, "bank_days": spent["bank"] / 86400,
                     "customer_days": spent["customer"] / 86400})
    return pd.DataFrame(rows).set_index(CASE)


def cancel_after_last_sent(events: pd.DataFrame) -> pd.DataFrame:
    cancel = events[events[ACT] == "A_Cancelled"].groupby(CASE).agg(
        cancel_ts=(TS, "max"),
        cancel_by_system=(RESOURCE, lambda s: bool((s == SYSTEM_RESOURCE).any())),
    )
    last_sent = events[events[ACT].isin(SENT)].groupby(CASE)[TS].max().rename("last_sent_ts")
    out = cancel.join(last_sent)
    out["gap_days"] = (out["cancel_ts"] - out["last_sent_ts"]).dt.total_seconds() / 86400
    return out
```

- [ ] **Step 4: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests/test_process.py -q` / Expected: 6 passed

- [ ] **Step 5: `analysis/05_holder_and_cancel.py` 작성**

```python
"""Phase 1 — who holds the case (bank or customer), and whether cancellations
follow the 30-day no-response rule.

Run from the project root:

    .venv\\Scripts\\python analysis/05_holder_and_cancel.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_population
from process import cancel_after_last_sent, holder_time

RULE_DAYS = (29, 32)


def main() -> None:
    ev, oc = load_population()
    held = holder_time(ev).join(oc["outcome"])
    held["total_days"] = held["bank_days"] + held["customer_days"]
    elapsed = (oc["end_ts"] - oc["submit_ts"]).dt.total_seconds() / 86400
    print(f"max |held total - elapsed| (days): "
          f"{(held['total_days'] - elapsed.reindex(held.index)).abs().max():.4f}")

    by_outcome = held.groupby("outcome").agg(
        cases=("total_days", "size"),
        median_bank_days=("bank_days", "median"),
        median_customer_days=("customer_days", "median"),
        bank_days_sum=("bank_days", "sum"),
        customer_days_sum=("customer_days", "sum"),
    )
    by_outcome.loc["all"] = [len(held), held["bank_days"].median(), held["customer_days"].median(),
                             held["bank_days"].sum(), held["customer_days"].sum()]
    by_outcome["customer_share"] = by_outcome["customer_days_sum"] / (
        by_outcome["bank_days_sum"] + by_outcome["customer_days_sum"])
    by_outcome = by_outcome.round(3)
    by_outcome.to_csv(OUT_DIR / "p1_holder_time_by_outcome.csv", encoding="utf-8-sig")
    print(f"\n=== bank vs customer held time (days) ===\n{by_outcome.to_string()}")

    cancel = cancel_after_last_sent(ev)
    gap = cancel["gap_days"].dropna()
    in_rule = gap.between(*RULE_DAYS)
    summary = pd.Series({
        "cancelled_cases": len(cancel),
        "with_offer_sent": int(gap.size),
        "cancelled_by_system_share": round(float(cancel["cancel_by_system"].mean()), 3),
        "gap_median_days": round(float(gap.median()), 2),
        "gap_p10_days": round(float(gap.quantile(0.1)), 2),
        "gap_p90_days": round(float(gap.quantile(0.9)), 2),
        "share_within_29_32_days": round(float(in_rule.mean()), 3),
        "system_share_within_rule": round(float(cancel.loc[gap.index[in_rule], "cancel_by_system"].mean()), 3),
        "system_share_outside_rule": round(float(cancel.loc[gap.index[~in_rule], "cancel_by_system"].mean()), 3),
    })
    summary.to_csv(OUT_DIR / "p1_cancel_gap_summary.csv", header=["value"], encoding="utf-8-sig")
    print(f"\n=== cancellation vs last offer sent ===\n{summary.to_string()}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 실데이터 실행** — Run: `.venv\Scripts\python analysis/05_holder_and_cancel.py`
기록 대상:
- `max |held total - elapsed|` ≈ 0 (A_Denied 2회 케이스 1건만 차이 가능) → 보유 시간 분할 검증
- 전체 `customer_share` → **판단 지점 2**
- `share_within_29_32_days`, `system_share_within_rule` → **판단 지점 3**

- [ ] **Step 7: 커밋**

```powershell
git add analysis/process.py analysis/05_holder_and_cancel.py tests/test_process.py outputs/p1_holder_time_by_outcome.csv outputs/p1_cancel_gap_summary.csv; git commit -m "feat: split bank vs customer held time and check 30-day cancel rule"
```

---

### Task 4: 전화 업무 ate_abort의 인접 전이

**Files:**
- Modify: `analysis/process.py`, `tests/test_process.py`
- Create: `analysis/06_ate_abort_context.py`

**Interfaces:**
- Produces:
  - `nearest_case_events(anchors, context) -> pd.DataFrame` — anchors의 원래 index를 유지하고, 컬럼 `prev_act, prev_gap_s, next_act, next_gap_s`를 둔다 (같은 케이스 안에서 가장 가까운 이전/이후 이벤트)
  - `classify_abort_context(nearest, window_s: float = 60.0) -> pd.Series` — 값 `case_moved_to_validation` / `case_closed` / `no_adjacent_transition`

- [ ] **Step 1: 실패하는 테스트 추가** — import에 `classify_abort_context, nearest_case_events` 추가

```python
def test_nearest_case_events_and_classification():
    context = _ev([
        ("S", "O_Returned", T0 - pd.Timedelta(seconds=10), "User_5"),
        ("S", "A_Validating", T0 + pd.Timedelta(seconds=1), "User_5"),
        ("C", "A_Cancelled", T0 + 10 * DAY, "User_1"),
    ])
    anchors = pd.DataFrame({
        "case:concept:name": ["S", "C", "C"],
        "time:timestamp": [T0, T0 + 10 * DAY + pd.Timedelta(seconds=2), T0 + 3 * DAY],
    })
    near = nearest_case_events(anchors, context)
    assert near.loc[0, "next_act"] == "A_Validating" and near.loc[0, "next_gap_s"] == 1
    assert near.loc[1, "prev_act"] == "A_Cancelled"
    cls = classify_abort_context(near, window_s=60)
    assert list(cls) == ["case_moved_to_validation", "case_closed", "no_adjacent_transition"]
```

- [ ] **Step 2: 실패 확인** — Expected: `ImportError: cannot import name 'classify_abort_context'`

- [ ] **Step 3: `analysis/process.py`에 구현 추가**

```python
def nearest_case_events(anchors: pd.DataFrame, context: pd.DataFrame) -> pd.DataFrame:
    """Nearest context event in the same case before and after each anchor, in anchor order."""
    a = anchors[[CASE, TS]].rename_axis("anchor").reset_index().sort_values(TS, kind="stable")
    c = context[[CASE, TS, ACT]].sort_values(TS, kind="stable")
    out = a.copy()
    for direction, label in (("backward", "prev"), ("forward", "next")):
        side = c.rename(columns={TS: f"{label}_ts", ACT: f"{label}_act"})
        m = pd.merge_asof(a, side, left_on=TS, right_on=f"{label}_ts", by=CASE, direction=direction)
        out[f"{label}_act"] = m[f"{label}_act"].to_numpy()
        out[f"{label}_gap_s"] = (m[f"{label}_ts"] - m[TS]).abs().dt.total_seconds().to_numpy()
    return out.set_index("anchor").sort_index()


def classify_abort_context(nearest: pd.DataFrame, window_s: float = 60.0) -> pd.Series:
    moved = nearest["next_act"].isin(["A_Validating"]) & (nearest["next_gap_s"] <= window_s)
    closed = ((nearest["prev_act"].isin(END_EVENTS) & (nearest["prev_gap_s"] <= window_s))
              | (nearest["next_act"].isin(END_EVENTS) & (nearest["next_gap_s"] <= window_s)))
    labels = np.select([moved, closed], ["case_moved_to_validation", "case_closed"],
                       default="no_adjacent_transition")
    return pd.Series(labels, index=nearest.index, name="context")
```

- [ ] **Step 4: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests -q` / Expected: 23 passed

- [ ] **Step 5: `analysis/06_ate_abort_context.py` 작성**

```python
"""Phase 1 — which case transition sits next to a customer-contact work item's ate_abort.

The log has no call outcome codes, so this cannot say WHY a call item was
aborted; it only shows the adjacent case transition.

Run from the project root:

    .venv\\Scripts\\python analysis/06_ate_abort_context.py
"""
from __future__ import annotations

import pandas as pd

from config import ACT, LIFECYCLE, OUT_DIR
from loader import load_population
from process import classify_abort_context, nearest_case_events

CONTACT_ACTIVITIES = ["W_Call after offers", "W_Call incomplete files"]
WINDOW_S = 60.0


def main() -> None:
    ev, _ = load_population()
    aborts = ev[ev[ACT].isin(CONTACT_ACTIVITIES) & (ev[LIFECYCLE] == "ate_abort")].reset_index(drop=True)
    context = ev[ev[ACT].str.startswith(("A_", "O_"))]
    near = nearest_case_events(aborts, context)
    near["context"] = classify_abort_context(near, WINDOW_S)
    near["activity"] = aborts[ACT].to_numpy()

    table = pd.crosstab(near["activity"], near["context"], margins=True)
    table.to_csv(OUT_DIR / "p1_ate_abort_context.csv", encoding="utf-8-sig")
    print(f"=== ate_abort of contact work items: adjacent case transition (±{WINDOW_S:.0f}s) ===")
    print(table.to_string())
    print(f"\n{pd.crosstab(near['activity'], near['context'], normalize='index').round(3).to_string()}")
    moved = near[near["context"] == "case_moved_to_validation"]
    print(f"\nevent just before 'moved' aborts:\n{moved['prev_act'].value_counts().head(5).to_string()}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 실데이터 실행** — Run: `.venv\Scripts\python analysis/06_ate_abort_context.py`
기록 대상: 활동별 `case_moved_to_validation` / `case_closed` / `no_adjacent_transition` 비중 → **판단 지점 4**

- [ ] **Step 7: 커밋**

```powershell
git add analysis/process.py analysis/06_ate_abort_context.py tests/test_process.py outputs/p1_ate_abort_context.csv; git commit -m "feat: classify case transitions adjacent to contact work-item aborts"
```

---

### Task 5: Phase 1 결론 문서와 CLAUDE.md 반영

**Files:**
- Create: `docs/01_process_baseline.md`
- Modify: `CLAUDE.md` (6장 진행 현황표·Phase 1 절·영향받는 Phase 절, 12장), 이 파일의 진행 기록

- [ ] **Step 1: `docs/01_process_baseline.md` 작성** — 모든 수치 옆에 `outputs/p1_*` 출처

```markdown
# Phase 1 — 프로세스 현황

## 1. 흐름과 이탈 위치
(p1_funnel_by_outcome.csv, p1_dropout_last_milestone.csv — 취소·거절 케이스가 멈춘 마지막 마일스톤)

## 2. 구간 소요
(p1_stage_durations.csv — 중앙값·p90, 일)

## 3. 은행 보유 vs 고객 보유 — 공식 질문 1에 대한 답
(p1_holder_time_by_outcome.csv)

## 4. 30일 무응답 자동 취소 규칙
(p1_cancel_gap_summary.csv — P7 확정 여부)

## 5. 전화 업무 ate_abort의 인접 전이
(p1_ate_abort_context.csv — 사유는 판정하지 않음. 해석 가능 범위만 기술)

## 6. A_Submitted — 접수 채널 변수 후보 여부
(p1_submitted_channel.csv, 04 출력)

## 7. 다음 Phase로 넘기는 것
```

- [ ] **Step 2: CLAUDE.md 반영**
  - 6장 진행 현황표 Phase 1 행: 상태 ✅, 한 줄 결론
  - Phase 1 절: 상태, 판단 지점별 결과
  - 판단 결과가 바꾸는 절: Phase 3 제외 표(30일 규칙), Phase 7 레버, Phase 8 예비 결론, P2(접수 채널 변수 추가 여부), 2-2장(ate_abort 해석 범위)
  - 12장 결정 로그

- [ ] **Step 3: 이 파일의 "진행 기록"에 실행 중 변경과 결과 요약, 커밋 목록 추가**

- [ ] **Step 4: 사용자 보고** — 판단 지점 결과, 방향 변경, Phase 2 진행계획 착수 여부 확인. ate_abort 결과가 sap-btm 해석과 다르면 여기서 알린다

- [ ] **Step 5: 커밋**

```powershell
git add docs/01_process_baseline.md docs/plans/phase-01-process-baseline.md CLAUDE.md; git commit -m "docs: record phase 1 process baseline"
```

---

## 진행 기록

| 날짜 | 내용 |
|---|---|
| 2026-09-11 | 진행계획 작성. 사전 탐색 신호(취소 대부분 회신 전 멈춤, 30일 규칙, ate_abort–A_Validating 인접, A_Submitted 일부 케이스)를 Task 2\~4에 반영. 사용자 확인 대기 |
| 2026-09-11 | 사용자 승인, 이 대화에서 직접 실행 |
| 2026-09-11 | 실행 중 변경 ①: `06_ate_abort_context.py`에 인접 전이 없는 abort의 직전 이벤트 분석을 추가 (`p1_ate_abort_unmatched_prev.csv`) |
| 2026-09-11 | 실행 중 변경 ②: 처음 규칙으로는 오퍼 후 전화 ate_abort의 32.3%가 "인접 전이 없음"이었고, 그 대부분이 O_Cancelled 직후였다. 오퍼 취소·거절도 종료로 인정하도록 `process.CLOSING_EVENTS`를 추가하고 테스트 1개를 더함 → 테스트 24개, "인접 전이 없음" 3.7% |
| 2026-09-11 | 실행 완료 — 결론은 [`docs/01_process_baseline.md`](../01_process_baseline.md) |

**결과 요약 (판단 지점별):**
1. 이탈의 주체는 고객 — 취소 9,692건 중 8,630건이 오퍼 발송 후 회신 없이 멈춤
2. 경과시간의 82.2%가 고객 보유 → Phase 8 예비 결론 "처리 속도 개선만으로는 풀리지 않는다"
3. 30일 무응답 자동 취소 확정 (P7) — 29\~32일 구간 77.0%, 그 안 시스템 처리 99.5%, 밖 0.0%. 취소는 자동과 수동 두 유형
4. ate_abort는 케이스 진행에 따른 자동 종료와 부합 — 인접 전이 없음은 오퍼 후 전화 3.7%, 보완 요청 전화 0.1%. sap-btm 해석과 충돌
5. A_Submitted 유무를 접수 시점 변수 후보로 채택 — 생성 후 0.1초 안에 시스템 기록, 성사율 49.5% vs 64.7%

**커밋:**
- `b52b775` docs: move phase plans to docs/plans and add phase 1 plan
- `4b9a812` feat: add analysis population loader
- `55d7a83` feat: reconstruct process funnel and dropout points
- `d694461` feat: split bank vs customer held time and check 30-day cancel rule
- `91154ef` feat: classify case transitions adjacent to contact work-item aborts
- (이 기록과 결론 문서) docs: record phase 1 process baseline
