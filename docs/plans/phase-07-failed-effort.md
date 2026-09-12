# Phase 7 — 실패 케이스 공수 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase 8이 개입 수단의 크기를 비교할 수 있도록 두 가지를 확정한다. ① 실패 공수를 유형(거절, 30일 자동 취소, 수동 취소)과 시점(첫 오퍼 발송 전/후)으로 나눠 **접촉 정책이 다룰 수 있는 공수의 크기**를 잰다. ② 실패 유형이 **접수 시점 세그먼트로 식별되는지**, 그리고 실패 공수가 저효율 세그먼트에 몰리는지를 판정한다.

**Architecture:** 실패 유형 판정, 시점별 공수 분할, 비율 구간, 집중도, 식별 판정은 새 모듈 `analysis/failures.py`에 두고 합성 데이터로 테스트한다. 스크립트 `17`은 케이스 단위 실패 공수를, `18`은 세그먼트 단위 식별·집중도와 η와의 관계를 산출한다.

**Tech Stack:** Python 3.12, pandas 3.0.5, numpy, pytest (Windows PowerShell 5.1)

**Spec:** `CLAUDE.md` 6장 Phase 7·8, 7장 시나리오 3 / Phase 1 4장(자동·수동 취소), Phase 2 5장(결과별 공수), Phase 5(세그먼트 η)

## 순서 변경 (2026-09-11 사용자 승인)

원래 설계에서는 Phase 7을 핵심 경로 이후로 두었다. 하지만 Phase 8이 비교할 개입 수단 4개 중 2개(오퍼 발송 후 접촉 정책, 심사 앞단 필터)는 Phase 7 없이는 크기를 잴 수 없다. 그래서 Phase 7을 Phase 8 앞으로 당긴다. 범위는 Phase 8에 필요한 두 질문으로 좁힌다.

## Global Constraints

- 공수는 Phase 2 정의(작업 구간, 활동별 p99 캡)를 그대로 쓴다. 전체 합이 Phase 2 총 공수(17,957.7시간)와 일치해야 한다.
- 실패 유형: 거절 = A_Denied / **자동 취소** = A_Cancelled를 시스템 계정(User_1)이 기록 / **수동 취소** = 그 외 A_Cancelled. Phase 1에서 시스템 취소의 99.5%가 마지막 오퍼 발송 후 29~32일에 있었다.
- 시점 기준: 케이스의 첫 오퍼 발송 시각(`offers.offer_first_sent`의 케이스별 최솟값). 오퍼가 발송되지 않은 케이스의 공수는 전부 "발송 전"이다.
- 식별 판정은 Phase 4 세그먼트(300건 이상 39개)로 한다. 접수 시점 변수만 쓴다 (P2).
- 통화 결과·취소 사유는 로그에 없다. 접촉 정책이 회신을 늘리는 효과는 **측정하지 않는다** (2-2장와 같은 원칙).
- 스크립트 번호 `17~18`, 산출 파일 접두어 `p7_`. 차트는 만들지 않는다.
- PowerShell 5.1: `&&` 대신 `;`. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## 사전 탐색 (계획 설계용, 수치는 Task에서 재산출)

- 유형별 건수: 성사 15,998 / 자동 취소 7,375 / 거절 3,441 / 수동 취소 2,317
- 자동 취소 공수 약 1,903시간 중 첫 오퍼 발송 **후**는 약 626시간(전체 공수의 약 3.5%)이고, 거의 전부 W_Call after offers다
- 거절 공수 약 2,939시간은 대부분 발송 후에 들었다. 심사(W_Validate application)가 전체 공수의 약 7.2%, 사기 심사(W_Assess potential fraud)가 약 2.9%다
- 세그먼트별 비율 범위: 자동 취소 11.7~38.2%, 거절 3.8~17.6%, 수동 취소 4.6~11.0%

## 판정 규칙 (착수 전 고정)

1. **접촉 정책의 공수 레버:** 자동 취소 신청에서 첫 오퍼 발송 **후**에 든 공수가 전체 공수의 5% 이상이면 "공수 레버로 의미 있음". 미만이면 "공수를 줄이는 수단으로는 작다. 가치는 회신 전환에 있고 로그로는 측정할 수 없다 → A/B 검증 대상"으로 기록한다
2. **접수 시점 식별 (유형별):** 세그먼트 비율의 최고/최저가 1.5배 이상이고, 극단 두 세그먼트의 Wilson 90% 구간이 분리되고, 비율 상위 25% 세그먼트가 그 유형 공수의 40% 이상을 차지하면 → "접수 시점에 차등 처리할 근거 있음"
3. **저효율 = 실패 공수 소모처인가:** 세그먼트 η와 "세그먼트 공수 중 실패 공수 비중"의 Spearman ρ가 −0.5 이하이면 확인
4. **반전 시나리오 3:** 실패 공수의 규모(34.2%)는 Phase 2에서 이미 확인됐다. 이 기준은 그 결과를 본 뒤에 정한 것이 아니라 **규모가 아닌 회수 가능성**을 묻는 것임을 명시한다. 레버로 다룰 수 있는 몫(① 자동 취소의 발송 후 공수 + ② 거절이 식별 가능할 때 거절률 상위 25% 세그먼트의 거절 공수)이 전체 공수의 10% 이상이면 "확인 — 레버로 다룰 수 있는 규모", 미만이면 "규모는 크지만 회수할 수 있는 몫은 작다"
5. **수동 취소:** 사유가 없으므로 레버를 지정하지 않는다. 규모와 식별 여부만 보고한다

## File Structure

| 파일 | 책임 |
|---|---|
| `analysis/failures.py` | `failure_type`, `split_effort`, `wilson_interval`, `top_concentration`, `screen_failure_rates` |
| `analysis/17_failure_effort.py` | 케이스별 실패 유형과 발송 전/후 공수, 유형·활동별 공수 비중, 판정 1 |
| `analysis/18_failure_segments.py` | 세그먼트별 유형 비율·구간·공수 비중, 식별 판정, η와의 상관, 시나리오 3 |
| `tests/test_failures.py` | 단위 테스트 5개 |
| `docs/07_failed_effort.md` | Phase 7 결론 문서 |

---

### Task 1: failures 모듈

**Files:**
- Create: `analysis/failures.py`, `tests/test_failures.py`

**Interfaces:**
- Produces:
  - `FAILURE_TYPES = ("denied", "auto_cancel", "manual_cancel")`
  - `failure_type(outcome: pd.Series, cancel_by_system: pd.Series) -> pd.Series` — name `failure_type`, 값 `success / denied / auto_cancel / manual_cancel`
  - `split_effort(segments, hours: pd.Series, cut: pd.Series, cases: pd.Index) -> pd.DataFrame` — 컬럼 `effort_before, effort_after`
  - `wilson_interval(k, n, z=1.645) -> tuple[np.ndarray, np.ndarray]` — 90% 구간
  - `top_concentration(rate: pd.Series, weight: pd.Series, top=0.25) -> float`
  - `screen_failure_rates(table, min_ratio=1.5, min_concentration=0.4, top=0.25) -> dict` — table 컬럼 `n, k, effort`. 키 `rate_min, rate_max, rate_ratio, ci_separated, top_quartile_effort_share, identifiable`

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_failures.py`

```python
import numpy as np
import pandas as pd

from failures import (failure_type, screen_failure_rates, split_effort, top_concentration,
                      wilson_interval)

CASE = "case:concept:name"


def test_failure_type_splits_cancellations_by_system_account():
    outcome = pd.Series({"a": "success", "b": "denied", "c": "cancelled", "d": "cancelled"})
    system = pd.Series({"c": True, "d": False})
    assert failure_type(outcome, system).to_dict() == {
        "a": "success", "b": "denied", "c": "auto_cancel", "d": "manual_cancel"}


def test_split_effort_before_and_after_cut():
    t = lambda h: pd.Timestamp("2016-01-01", tz="UTC") + pd.Timedelta(hours=h)  # noqa: E731
    seg = pd.DataFrame({CASE: ["A", "A", "B"], "start_ts": [t(1), t(5), t(1)]})
    hours = pd.Series([0.2, 0.3, 0.4])
    cut = pd.Series({"A": t(3)})
    out = split_effort(seg, hours, cut, pd.Index(["A", "B", "C"], name=CASE))
    assert out.loc["A"].tolist() == [0.2, 0.3]
    assert out.loc["B"].tolist() == [0.4, 0.0]
    assert out.loc["C"].tolist() == [0.0, 0.0]


def test_wilson_interval_known_value():
    lo, hi = wilson_interval([50], [100])
    assert round(float(lo[0]), 3) == 0.419 and round(float(hi[0]), 3) == 0.581


def test_top_concentration():
    rate = pd.Series({"a": 0.9, "b": 0.5, "c": 0.1, "d": 0.2})
    weight = pd.Series({"a": 10.0, "b": 20.0, "c": 30.0, "d": 40.0})
    assert top_concentration(rate, weight, top=0.25) == 0.1
    assert top_concentration(rate, weight, top=0.5) == 0.3


def test_screen_failure_rates_identifiable():
    table = pd.DataFrame({"n": [1000, 1000, 1000, 1000], "k": [300, 100, 100, 100],
                          "effort": [60.0, 10.0, 10.0, 10.0]}, index=list("abcd"))
    res = screen_failure_rates(table)
    assert res["rate_ratio"] == 3.0 and res["ci_separated"]
    assert res["top_quartile_effort_share"] == 60.0 / 90.0 and res["identifiable"]
    flat = table.assign(k=[110, 100, 100, 100])
    assert not screen_failure_rates(flat)["identifiable"]
```

- [ ] **Step 2: 실패 확인** — Run: `.venv\Scripts\python -m pytest tests/test_failures.py -q` / Expected: `No module named 'failures'`

- [ ] **Step 3: `analysis/failures.py` 구현**

```python
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
```

- [ ] **Step 4: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests -q` / Expected: 57 passed (기존 52 + 5)

- [ ] **Step 5: 커밋**

```powershell
git add analysis/failures.py tests/test_failures.py; git commit -m "feat: add failure type and concentration module"
```

---

### Task 2: 케이스 단위 실패 공수

**Files:**
- Create: `analysis/17_failure_effort.py`

**Interfaces:**
- Consumes: `load_population`, `process.cancel_after_last_sent`, `p2_active_segments.parquet`, `effort.activity_caps/cap_hours`, `p0_offers.parquet`, `offers.offer_first_sent`
- Produces: `outputs/p7_case_failure.parquet`(index 케이스, 컬럼 `effort_before, effort_after, failure_type, effort_hours` → Task 3 입력), `p7_failure_effort.csv`, `p7_failure_effort_by_activity.csv`

- [ ] **Step 1: `analysis/17_failure_effort.py` 작성**

```python
"""Phase 7 — how much effort failed applications take, by failure type and by whether it was
spent before or after the case's first offer was sent.

Run from the project root:

    .venv\\Scripts\\python analysis/17_failure_effort.py
"""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, OUT_DIR
from effort import activity_caps, cap_hours
from failures import failure_type, split_effort
from loader import load_population
from offers import offer_first_sent
from process import cancel_after_last_sent

CONTACT_LEVER_MIN_SHARE = 0.05


def main() -> None:
    ev, oc = load_population()
    ftype = failure_type(oc["outcome"], cancel_after_last_sent(ev)["cancel_by_system"])
    seg = pd.read_parquet(OUT_DIR / "p2_active_segments.parquet")
    hours = cap_hours(seg, activity_caps(seg, 0.99))
    offers = pd.read_parquet(OUT_DIR / "p0_offers.parquet")
    first_sent = (offers.assign(first_sent=offers["offer_id"].map(offer_first_sent(ev)))
                  .groupby(CASE)["first_sent"].min())

    case = split_effort(seg, hours, first_sent, oc.index).join(ftype)
    case["effort_hours"] = case["effort_before"] + case["effort_after"]
    case.to_parquet(OUT_DIR / "p7_case_failure.parquet")
    total = case["effort_hours"].sum()
    print(f"failure types: {case['failure_type'].value_counts().to_dict()}")
    print(f"total effort hours: {total:,.1f} (Phase 2: 17,957.7)")

    summary = case.groupby("failure_type").agg(
        cases=("effort_hours", "size"), mean_hours=("effort_hours", "mean"),
        effort_before=("effort_before", "sum"), effort_after=("effort_after", "sum"),
        effort_total=("effort_hours", "sum"))
    summary["share_of_all_effort"] = summary["effort_total"] / total
    summary["after_sent_share_of_all"] = summary["effort_after"] / total
    summary = summary.round(4)
    summary.to_csv(OUT_DIR / "p7_failure_effort.csv", encoding="utf-8-sig")
    print(f"\n=== effort by failure type, before / after the first offer was sent ===\n{summary.to_string()}")

    after = (seg["start_ts"] >= seg[CASE].map(first_sent)).rename("after_first_sent")
    by_act = hours.groupby([seg[CASE].map(case["failure_type"]).rename("failure_type"), seg[ACT], after]).sum()
    by_act = (by_act / total).rename("share_of_all_effort").reset_index()
    by_act = by_act[by_act["share_of_all_effort"] > 0].sort_values(
        ["failure_type", "share_of_all_effort"], ascending=[True, False]).round(4)
    by_act.to_csv(OUT_DIR / "p7_failure_effort_by_activity.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== share of all effort by failure type, activity and timing ===\n"
          f"{by_act[by_act['failure_type'] != 'success'].to_string(index=False)}")

    contact = float(summary.loc["auto_cancel", "after_sent_share_of_all"])
    verdict = ("material effort lever" if contact >= CONTACT_LEVER_MIN_SHARE
               else "small as an effort lever; its value would be converting non-responders (not measurable)")
    print(f"\nauto-cancel effort after the first offer was sent: {contact:.1%} of all effort -> {verdict}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/17_failure_effort.py`
기록 대상: 총 공수가 Phase 2와 일치하는지, 유형별 공수·발송 전후 분할(**판정 1**), 유형·활동별 비중

- [ ] **Step 3: 커밋**

```powershell
git add analysis/17_failure_effort.py outputs/p7_case_failure.parquet outputs/p7_failure_effort.csv outputs/p7_failure_effort_by_activity.csv; git commit -m "feat: split failed-case effort by type and offer timing"
```

---

### Task 3: 세그먼트 단위 식별과 집중도

**Files:**
- Create: `analysis/18_failure_segments.py`

**Interfaces:**
- Consumes: `p7_case_failure.parquet`, `p4_segments.parquet`, `p5_segment_efficiency.csv`, `failures.*`
- Produces: `p7_segment_failures.csv`(세그먼트별 유형 비율·Wilson 구간·유형별 공수 비중·실패 공수 비중·η), `p7_failure_screening.csv`(유형별 식별 판정), `p7_addressable_effort.csv`(시나리오 3)

- [ ] **Step 1: `analysis/18_failure_segments.py` 작성**

```python
"""Phase 7 — can failure types be told apart at intake, where does failed effort concentrate,
and are low-η segments the ones that burn effort on failures?

Run from the project root, after 17_failure_effort.py:

    .venv\\Scripts\\python analysis/18_failure_segments.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import OUT_DIR
from failures import FAILURE_TYPES, screen_failure_rates, wilson_interval

MIN_N = 300
TOP = 0.25
ADDRESSABLE_MIN_SHARE = 0.10


def main() -> None:
    case = pd.read_parquet(OUT_DIR / "p7_case_failure.parquet").join(pd.read_parquet(OUT_DIR / "p4_segments.parquet"))
    sizes = case["segment"].value_counts()
    case = case[case["segment"].isin(sizes.index[sizes >= MIN_N])]
    eta = pd.read_csv(OUT_DIR / "p5_segment_efficiency.csv", index_col="segment")["eta"]
    n = case.groupby("segment").size()
    effort_all = case.groupby("segment")["effort_hours"].sum()
    table = pd.DataFrame({"n": n, "effort_hours": effort_all}).join(eta)

    screens, type_effort = [], {}
    for t in FAILURE_TYPES:
        is_t = case["failure_type"] == t
        k = is_t.groupby(case["segment"]).sum()
        eff = case.loc[is_t].groupby("segment")["effort_hours"].sum().reindex(n.index, fill_value=0.0)
        lo, hi = wilson_interval(k, n)
        table[f"rate_{t}"], table[f"rate_{t}_lo"], table[f"rate_{t}_hi"] = k / n, lo, hi
        table[f"effort_share_{t}"] = eff / effort_all
        type_effort[t] = eff
        screens.append({"failure_type": t, **screen_failure_rates(pd.DataFrame({"n": n, "k": k, "effort": eff}))})
    table["failed_effort_share"] = sum(type_effort.values()) / effort_all
    table.sort_values("eta").round(4).to_csv(OUT_DIR / "p7_segment_failures.csv", encoding="utf-8-sig")
    screening = pd.DataFrame(screens).round(4)
    screening.to_csv(OUT_DIR / "p7_failure_screening.csv", index=False, encoding="utf-8-sig")
    print(f"=== can intake segments tell failure types apart? ({len(n)} segments) ===\n{screening.to_string(index=False)}")

    rho = table["eta"].corr(table["failed_effort_share"], method="spearman")
    print(f"\nSpearman(segment η, failed share of segment effort): {rho:.3f}")
    cols = ["n", "eta", "failed_effort_share", "rate_denied", "rate_auto_cancel", "rate_manual_cancel"]
    ordered = table.sort_values("eta")
    print(f"\nlowest η:\n{ordered[cols].head(5).round(3).to_string()}\n\nhighest η:\n{ordered[cols].tail(5).round(3).to_string()}")

    total = case["effort_hours"].sum()
    contact = case.loc[case["failure_type"] == "auto_cancel", "effort_after"].sum() / total
    denied_ok = bool(screening.set_index("failure_type").loc["denied", "identifiable"])
    k_top = max(1, int(np.ceil(len(n) * TOP)))
    top_denied = table["rate_denied"].sort_values(ascending=False).index[:k_top]
    front = (type_effort["denied"].reindex(top_denied).sum() / total) if denied_ok else 0.0
    addressable = pd.DataFrame([
        {"lever": "contact policy (auto-cancel effort after first offer sent)", "share_of_all_effort": contact},
        {"lever": f"front filter (denied effort in top {TOP:.0%} denial-rate segments, if identifiable)",
         "share_of_all_effort": front},
        {"lever": "total addressable", "share_of_all_effort": contact + front},
    ]).round(4)
    addressable.to_csv(OUT_DIR / "p7_addressable_effort.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== effort a lever could address (scenario 3) ===\n{addressable.to_string(index=False)}")
    print(f"scenario 3: {'confirmed' if contact + front >= ADDRESSABLE_MIN_SHARE else 'large in size, small in recoverable share'}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/18_failure_segments.py`
기록 대상: 유형별 식별 판정(**판정 2·5**), η와 실패 공수 비중의 상관(**판정 3**), 레버로 다룰 수 있는 공수(**판정 4**)

- [ ] **Step 3: 커밋**

```powershell
git add analysis/18_failure_segments.py outputs/p7_segment_failures.csv outputs/p7_failure_screening.csv outputs/p7_addressable_effort.csv; git commit -m "feat: test intake identifiability of failure types"
```

---

### Task 4: Phase 7 결론 문서와 CLAUDE.md 반영

**Files:**
- Create: `docs/07_failed_effort.md`
- Modify: `CLAUDE.md` (6장 진행 현황표·Phase 7 절·Phase 8 절, 7장 시나리오 3, 12장), 이 파일의 진행 기록

- [ ] **Step 1: `docs/07_failed_effort.md` 작성** — 모든 수치 옆에 `outputs/p7_*` 출처

```markdown
# Phase 7 — 실패 케이스 공수
## 요약 (Phase 8이 쓸 두 가지 크기)
## 1. 실패 유형과 공수 — 발송 전/후 (p7_failure_effort.csv, p7_failure_effort_by_activity.csv)
## 2. 접촉 정책이 다룰 수 있는 공수 (판정 1)
## 3. 접수 시점에 실패 유형을 가려낼 수 있나 (p7_failure_screening.csv, p7_segment_failures.csv)
## 4. 저효율 세그먼트와 실패 공수 (판정 3)
## 5. 반전 시나리오 3 판정 (p7_addressable_effort.csv)
## 6. Phase 8로 넘기는 것 — 개입 수단 4개의 크기 표
```

- [ ] **Step 2: CLAUDE.md 반영** — 진행 현황표, Phase 7 절(판정별 결과), Phase 8 절(수단 4개의 크기 표), 7장 시나리오 3, 12장
- [ ] **Step 3: 이 파일의 진행 기록에 실행 중 변경·결과 요약·커밋 추가**
- [ ] **Step 4: 사용자 보고** — Phase 8 진행계획 착수 여부 확인
- [ ] **Step 5: 커밋**

```powershell
git add docs/07_failed_effort.md docs/plans/phase-07-failed-effort.md CLAUDE.md; git commit -m "docs: record phase 7 failed effort"
```

---

## 진행 기록

| 날짜 | 내용 |
|---|---|
| 2026-09-11 | 사용자 승인으로 Phase 7을 Phase 8 앞으로 당김. 진행계획 작성. 사전 탐색(자동 취소의 발송 후 공수 약 3.5%, 거절 공수 중 심사·사기 심사 비중, 세그먼트별 유형 비율 범위)을 판정 규칙에 반영. 사용자 확인 대기 |
| 2026-09-11 | 사용자 승인, 이 대화에서 직접 실행 |
| 2026-09-11 | 실행 중 변경 ①: `test_screen_failure_rates_identifiable`이 실패함. 원인 확인 결과 0.3/0.1 = 2.9999999999999996의 부동소수점 비교 문제(코드 결함 아님) → 테스트를 반올림 비교로 수정 |
| 2026-09-11 | 실행 중 변경 ②: 거절이 "식별 불가"로 나온 원인이 비율 차이가 아니라 집중도 조건이라, 18에 집중도 조건을 뺀 민감도 출력 1줄을 추가함. 판정은 사전 규칙 그대로 유지 |
| 2026-09-11 | 실행 완료 — 결론은 [`docs/07_failed_effort.md`](../07_failed_effort.md). CLAUDE.md Phase 8 절에 개입 수단 4개의 크기 표, 7장 시나리오 3 갱신 |

**결과 요약 (판정 규칙별):**
1. 자동 취소의 발송 후 공수 3.5% < 5% → 공수 레버로는 작음 (발송 전 신청서 완성 공수 6.8%가 더 큼)
2. 거절 4.64배·자동 취소 3.27배 비율 차이, 구간 분리. 공수 집중 34.0%·35.8% < 40% → 규칙상 차등 처리 근거 미충족
3. ρ(η, 실패 공수 비중) = −0.651 → 저효율 = 실패 공수 소모처 확인
4. 시나리오 3: 회수 가능 몫 3.47% < 10% → "규모는 크지만 회수 가능한 몫은 작다" (완화 시 9.1%)
5. 수동 취소는 기준 충족(41.4%)이지만 사유가 없어 레버 미지정

**커밋:**
- `d3d71e8` docs: move phase 7 ahead of phase 8 and add its plan
- `7685e7a` feat: split failed-case effort by type and offer timing
- (Task 1) feat: add failure type and concentration module
- (Task 3) feat: test intake identifiability of failure types
- (이 기록과 결론 문서) docs: record phase 7 failed effort
