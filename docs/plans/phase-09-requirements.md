# Phase 9 — 요구사항 도출 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase 1~8의 업무 분석을 **제품 이름 없는 시스템 요구사항**으로 옮긴다. 요구사항은 기능·데이터·측정·비기능 네 층으로 나눈다. 각 요구사항은 근거(Phase·산출 파일·수치)와 수용 기준을 가진다. 측정 요구는 A/B 실험의 필요 표본과 기간을 실제 월 유입량으로 계산해 실행 가능성까지 판정한다.

**Architecture:** 표본 크기 계산 함수 하나를 새 모듈 `analysis/design.py`에 두고 테스트한다. 스크립트 `20`이 월 유입량과 기준 비율을 기존 산출물에서 읽어 실험별 필요 표본·기간을 만든다. 나머지는 요구사항 문서다.

**Tech Stack:** Python 3.12 (표준 라이브러리 `statistics.NormalDist`), pandas 3.0.5, pytest (Windows PowerShell 5.1)

**Spec:** `CLAUDE.md` §1(축 D), §5 P2·P6·P8, §6 Phase 9 / `docs/08_intervention.md` §3~§6(수단 등급·필요 역량·데이터 공백)

## 사용자 결정 (2026-09-11)

- **계산기(MVP)는 산출물 단계로 미룬다.** Phase 9는 요구사항 문서까지만 한다. 계산기가 검증할 규칙이 이 문서에서 확정된다.

## Global Constraints

- **제품·벤더 이름을 쓰지 않는다** (§6 Phase 9 원칙). 기능은 조건과 수용 기준으로만 쓴다. 검증 단계에서 문서를 벤더명으로 검색해 0건인지 확인한다.
- **근거 없는 요구사항은 쓰지 않는다** (P6). 요구사항마다 근거 Phase와 산출 파일, 수치를 적는다.
- 접수 시점 규칙에는 **접수 시점 변수만** 쓴다. 결과 누수 속성(CreditScore·Selected·Accepted)은 규칙 입력으로 금지한다 (P2).
- 우선순위는 Phase 8 등급을 따른다. 1순위 수단과 전 수단 공통 역량 = Must, A/B 검증 대상 수단 = Should, 보류 수단 = Won't(이번 범위 아님).
- A/B 표본은 두 비율 비교(양측, α = 0.05, 검정력 0.8, 1:1 배정)로 계산한다. 탐지 목표 효과 크기는 **추정값이 아니라 설계 파라미터**다. 관측 연관(Phase 6)과 여러 후보값을 나란히 제시한다.
- 스크립트 번호 `20`, 산출 파일 접두어 `p9_`. 차트는 만들지 않는다.
- PowerShell 5.1: `&&` 대신 `;`. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## 요구사항 구조 (문서 골격)

| 층 | 내용 | 주 입력 |
|---|---|---|
| **FR 기능** | FR1 접수 시점 세그먼트 판별 / FR2 처리 대기열 우선순위의 세그먼트별 분기 / FR3 오퍼 제시 규칙 분기 / FR4 오퍼 발송 후 접촉 규칙 분기와 결과 기록 / FR5 무작위 배정 / FR6 사후 측정과 규칙 되먹임 / FR7 대기열 모니터링(은행 보유 시간의 작업·대기 분리) | Phase 4·5·6·7·8 |
| **DR 데이터** | 데이터 공백 7종(통화 결과 코드, 취소 사유, 오퍼 요청 주체, 실행 이후 성과, 조달비용·순마진, 근무시간·인원, A_Submitted 업무 정의) + 접수 시점에 확정돼야 하는 기존 필드(신청 금액, 용도, 신청 유형, 접수 경로 표식) | Phase 0·1·8 |
| **MR 측정** | 지표 정의(η, 성사율 = A_Pending 도달, 공수 = 활동별 p99 캡 작업시간, 보유 주체 분할, 30일 자동 취소율, 필요 최소 순마진 비중) / A/B 설계와 필요 표본·기간 / 갱신 주기 | Phase 0·2·3·5·7, 스크립트 20 |
| **NFR 비기능** | 규칙의 설명 가능성(세그먼트 라벨이 사람이 읽을 수 있음), 감사 추적(어떤 규칙이 언제 적용됐는지), 개인정보 최소화(접수 시점 변수 4종만), 규칙 표의 운영자 수정 가능성, 적용 실패 시 기본 규칙으로 복귀 | Phase 3·4·8 |

**설계 원칙 — 가장 단순한 충족 수단을 막지 않는다:** 현재 근거로는 세그먼트가 접수 시점 변수 4개로 만든 39개 규칙표다. 예측 모델은 요구하지 않는다. 요구사항은 "규칙표로도, 모델로도 충족할 수 있는 조건"으로 쓴다. 어느 쪽을 쓸지는 Phase 10에서 정한다.

## 판정 규칙 (착수 전 고정)

1. **추적성:** 모든 FR·DR·MR은 근거(Phase·산출 파일·수치)와 수용 기준을 가진다. 근거를 댈 수 없는 항목은 쓰지 않는다
2. **제품 중립:** 문서에서 벤더·제품명 검색 결과가 0건이어야 한다
3. **우선순위:** Phase 8 등급을 MoSCoW로 옮긴다 — 1순위 수단과 FR1·FR5·FR6 = Must / A/B 대상 수단(FR3·FR4) = Should / 보류 수단 = Won't
4. **A/B 실행 가능성:** 실험별로 설계 효과 크기에서 필요한 표본을 월 유입량으로 채우는 기간이 6개월 이하이면 "실행 가능", 초과면 "효과 크기를 키우거나 기간을 늘려야 함"
5. **계산기:** 이번 Phase에서 만들지 않는다. 산출물 단계에서 이 문서의 FR1·FR2·MR 정의를 입력으로 만든다

## File Structure

| 파일 | 책임 |
|---|---|
| `analysis/design.py` | `ab_sample_size` |
| `analysis/20_measurement_design.py` | 월 유입량, 실험별 기준 비율, 설계 효과 크기별 필요 표본·기간 |
| `tests/test_design.py` | 단위 테스트 1개 |
| `docs/09_requirements.md` | 요구사항 문서 (FR·DR·MR·NFR, 추적 매트릭스, MoSCoW, A/B 설계, 범위 밖) |

---

### Task 1: 표본 크기 함수

**Files:**
- Create: `analysis/design.py`, `tests/test_design.py`

**Interfaces:**
- Produces: `ab_sample_size(p_base: float, delta: float, alpha: float = 0.05, power: float = 0.8) -> int` — 한 군당 필요 케이스 수 (양측 두 비율 z검정, 1:1)

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_design.py`

```python
from design import ab_sample_size


def test_ab_sample_size_known_value():
    # p1 = 0.5 → p2 = 0.6, alpha 0.05 two-sided, power 0.8: 387.3 → 388 per arm
    assert ab_sample_size(0.5, 0.1) == 388
    assert ab_sample_size(0.5, -0.1) == ab_sample_size(0.4, 0.1)
```

- [ ] **Step 2: 실패 확인** — Run: `.venv\Scripts\python -m pytest tests/test_design.py -q` / Expected: `No module named 'design'`

- [ ] **Step 3: `analysis/design.py` 구현**

```python
"""Experiment design helpers for the measurement requirements (Phase 9)."""
from __future__ import annotations

import math
from statistics import NormalDist


def ab_sample_size(p_base: float, delta: float, alpha: float = 0.05, power: float = 0.8) -> int:
    """Cases per arm to detect a change from p_base to p_base + delta
    (two-sided two-proportion z-test, equal arms)."""
    p1, p2 = p_base, p_base + delta
    p_bar = (p1 + p2) / 2
    z_a = NormalDist().inv_cdf(1 - alpha / 2)
    z_b = NormalDist().inv_cdf(power)
    n = (z_a * math.sqrt(2 * p_bar * (1 - p_bar))
         + z_b * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2 / delta ** 2
    return math.ceil(n)
```

- [ ] **Step 4: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests -q` / Expected: 59 passed

- [ ] **Step 5: 커밋**

```powershell
git add analysis/design.py tests/test_design.py; git commit -m "feat: add A/B sample size helper"
```

---

### Task 2: A/B 필요 표본과 기간

**Files:**
- Create: `analysis/20_measurement_design.py`

**Interfaces:**
- Consumes: `p0_case_outcomes.parquet`(월 유입량), `p1_funnel_by_outcome.csv`(오퍼 발송 케이스 수), `p6_group_summary.csv`(단일 오퍼 성사율), `p7_failure_effort.csv`(자동 취소 건수), `design.ab_sample_size`
- Produces: `outputs/p9_ab_sample_sizes.csv` — 실험, 대상, 기준 비율, 설계 효과 크기(와 그 출처), 한 군당 필요 표본, 월 대상 건수, 필요 개월 수, 판정

- [ ] **Step 1: `analysis/20_measurement_design.py` 작성**

```python
"""Phase 9 — how long would the A/B tests behind the measurement requirements take?

Effect sizes are design parameters (the smallest change worth detecting), shown next to the
observed association from Phase 6 — they are not estimates of the true effect.

Run from the project root:

    .venv\\Scripts\\python analysis/20_measurement_design.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from design import ab_sample_size

MAX_MONTHS = 6


def main() -> None:
    oc = pd.read_parquet(OUT_DIR / "p0_case_outcomes.parquet")
    pop = oc[oc["in_population"]]
    monthly = pop.groupby(pop["submit_ts"].dt.tz_convert(None).dt.to_period("M")).size()
    per_month = float(monthly.mean())
    funnel = pd.read_csv(OUT_DIR / "p1_funnel_by_outcome.csv", index_col=0)
    sent_share = float(funnel.loc["O_Sent", "all"] / funnel.loc["A_Create Application", "all"])
    groups = pd.read_csv(OUT_DIR / "p6_group_summary.csv")
    single_p = float(groups.loc[(groups["definition"] == "d1_later") & (groups["group"] == "single"), "p"].iloc[0])
    failures = pd.read_csv(OUT_DIR / "p7_failure_effort.csv", index_col="failure_type")
    auto_rate = float(failures.loc["auto_cancel", "cases"] / funnel.loc["O_Sent", "all"])
    print(f"applications per month={per_month:,.0f}  offer-sent share={sent_share:.3f}  "
          f"single-offer success={single_p:.3f}  auto-cancel rate among offer-sent={auto_rate:.3f}")

    designs = [
        ("first-conversation single offer", "all applications", single_p, per_month,
         [(0.026, "observed, stratified D1 (Phase 6)"), (0.055, "observed, stratified D2 (Phase 6)"),
          (0.02, "design minimum")]),
        ("contact policy after offer", "offer-sent applications", auto_rate, per_month * sent_share,
         [(-0.01, "design"), (-0.02, "design"), (-0.03, "design")]),
    ]
    rows = []
    for name, target, base, flow, deltas in designs:
        for delta, source in deltas:
            n = ab_sample_size(base, delta)
            months = 2 * n / flow
            rows.append({"experiment": name, "target": target, "base_rate": round(base, 4),
                         "delta": delta, "delta_source": source, "n_per_arm": n,
                         "eligible_per_month": round(flow), "months_needed": round(months, 1),
                         "verdict": "feasible" if months <= MAX_MONTHS else "enlarge effect or extend"})
    table = pd.DataFrame(rows)
    table.to_csv(OUT_DIR / "p9_ab_sample_sizes.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== A/B sample size and duration (alpha 0.05 two-sided, power 0.8, 1:1) ===\n{table.to_string(index=False)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/20_measurement_design.py`
기록 대상: 월 유입량, 기준 비율, 실험별 필요 표본·기간·판정(**판정 4**)

- [ ] **Step 3: 커밋**

```powershell
git add analysis/20_measurement_design.py outputs/p9_ab_sample_sizes.csv; git commit -m "feat: size A/B tests for measurement requirements"
```

---

### Task 3: 요구사항 문서와 CLAUDE.md 반영

**Files:**
- Create: `docs/09_requirements.md`
- Modify: `CLAUDE.md` (§6 진행 현황표·Phase 9 절·Phase 10 절, §8 산출물, §11, §12), 이 파일의 진행 기록

- [ ] **Step 1: `docs/09_requirements.md` 작성** — 요구사항마다 ID·조건·수용 기준·근거(Phase·파일·수치)·우선순위

```markdown
# Phase 9 — 요구사항
## 요약
## 0. 읽는 법 (제품 중립, 조건 + 수용 기준, 근거 추적)
## 1. 기능 요구 FR1~FR7
## 2. 데이터 요구 DR (공백 7종 + 접수 시점 확정 필드)
## 3. 측정 요구 MR (지표 정의 · A/B 설계와 필요 표본 · 갱신 주기) (p9_ab_sample_sizes.csv)
## 4. 비기능 요구 NFR
## 5. 추적 매트릭스 — 요구사항 ↔ 개입 수단 ↔ 근거 ↔ 수용 기준
## 6. 우선순위 (MoSCoW)
## 7. 범위 밖 — 이번에 요구하지 않는 것과 이유 (보류 수단, 예측 모델, 제품 선택)
## 8. Phase 10으로 넘기는 것
```

- [ ] **Step 2: 제품 중립 검증** — Grep로 `docs/09_requirements.md`에서 `SAP|Signavio|Celonis|LeanIX|WalkMe|IBM|Pega|Salesforce|Appian|UiPath|Camunda|Oracle|Microsoft|AWS|Azure` 검색 → 0건 (판정 2)
- [ ] **Step 3: CLAUDE.md 반영** — 진행 현황표, Phase 9 절(판정별 결과, 요구사항 목록 요약), Phase 10 절(입력), §8(계산기 연기), §11(계산기 항목), §12
- [ ] **Step 4: 이 파일의 진행 기록에 실행 중 변경·결과 요약·커밋 추가**
- [ ] **Step 5: 사용자 보고** — Phase 10 또는 산출물 단계 착수 여부 확인
- [ ] **Step 6: 커밋**

```powershell
git add docs/09_requirements.md docs/plans/phase-09-requirements.md CLAUDE.md; git commit -m "docs: record phase 9 requirements"
```

---

## 진행 기록

| 날짜 | 내용 |
|---|---|
| 2026-09-11 | 사용자 결정: 계산기는 산출물 단계로 미룸. 진행계획 작성 — 요구사항 4층 구조, A/B 필요 표본·기간 계산 추가, 판정 규칙 고정. 사용자 확인 대기 |
