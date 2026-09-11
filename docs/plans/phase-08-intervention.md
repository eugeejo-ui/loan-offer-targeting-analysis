# Phase 8 — 개입 가능 여부 판정 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Phase 1~7의 결과를 모아 개입 수단마다 조건부 권고를 내린다 (P8). 권고의 전제 가운데 데이터로 확인할 수 있는 두 가지를 먼저 검증한다. ① "처리 속도 개선만으로는 풀리지 않는다"가 세그먼트 단위에서도 성립하는가 ② 현재 은행의 처리 순서가 η를 반영하고 있는가(반영하지 않아야 순서 변경 수단에 여지가 있다). 끝으로 수단마다 필요한 역량과 데이터 공백을 추려 Phase 9·10에 넘긴다.

**Architecture:** 세그먼트별 보유 주체 요약 함수 하나를 `analysis/process.py`에 추가하고 테스트한다. 스크립트 `19`가 두 전제를 검증한다. 나머지는 이미 나온 산출물(`p5_*`, `p6_*`, `p7_*`)을 인용하는 판정 문서다.

**Tech Stack:** Python 3.12, pandas 3.0.5, pytest (Windows PowerShell 5.1)

**Spec:** `CLAUDE.md` §5 P3·P7·P8, §6 Phase 8(개입 수단 4개의 크기 표) / `docs/01`·`05`·`06`·`07`

## Global Constraints

- 세그먼트는 Phase 4의 300건 이상 39개(28,243건)다.
- 보유 주체 규칙은 Phase 1과 같다(`process.holder_time`): 오퍼 발송·보완 요청 시 고객에게 넘어가고, 오퍼 회신·심사 재개 시 은행으로 돌아온다.
- **소요시간은 원인 변수로 쓰지 않는다** (P7). 은행 보유 시간은 "속도를 올리면 줄어들 수 있는 몫의 상한"과 "현재 처리 순서"를 읽는 데만 쓴다.
- 은행 보유 시간에는 야간·주말이 섞여 있다(영업시간 보정 없음). 작업 비중은 "대기열이 있다는 신호"로만 읽는다.
- 권고는 조건부 형식이다 (P8): "전제 X가 성립하면 A, 아니면 B". 가상 배분·관측 연관·측정 불가 같은 **근거의 성격**을 권고 옆에 함께 적는다.
- 스크립트 번호 `19`, 산출 파일 접두어 `p8_`. 차트는 만들지 않는다.
- PowerShell 5.1: `&&` 대신 `;`. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## 판정 규칙 (착수 전 고정)

1. **처리 속도 결론의 세그먼트 확인:** 고객 보유 비중이 50% 이상인 세그먼트가 39개 중 90%(35개) 이상이면 "세그먼트 단위에서도 확인"
2. **현재 처리 순서:** ρ(세그먼트 η, 은행 보유 일수 중앙값)가 −0.3 이하이면 "효율이 높은 세그먼트를 이미 빨리 처리하고 있다" → 순서 변경의 여지가 작다. −0.3보다 크면 "현재 처리 순서는 η를 반영하지 않는다" → 순서 변경 수단의 전제가 성립한다
3. **대기열 신호:** 세그먼트별 "은행 보유 시간 중 실제 작업 시간 비중"의 중앙값이 10% 미만이면 "은행 쪽에 대기열이 있다" → 처리 순서가 누가 기다리는지를 정한다는 전제를 뒷받침한다 (영업시간 미보정 한계를 함께 적는다)
4. **수단별 권고 등급:**
   - **채택 권고:** 전제가 데이터로 확인됐고, 근거가 관측값 기반 계산이다
   - **조건부:** 전제 하나 이상이 데이터로 확인되지 않았다. 확인 방법을 적는다
   - **검증 후:** 근거가 관측 연관뿐이거나 효과를 측정할 수 없다 → A/B 설계를 적는다
   - **보류:** 사전 규칙상 근거가 미충족이다
5. **데이터 공백:** 수단의 효과를 재는 데 필요하지만 로그에 없는 필드를 목록으로 만든다 → Phase 9 데이터 요구

## File Structure

| 파일 | 책임 |
|---|---|
| `analysis/process.py` | `group_holder_summary` 추가 |
| `analysis/19_intervention_check.py` | 세그먼트별 보유 주체·은행 보유 일수·작업 비중, η와의 상관, 판정 1~3 |
| `tests/test_process.py` | 단위 테스트 1개 추가 |
| `docs/08_intervention.md` | 판정 문서 — 두 전제, 수단 매트릭스, 조건부 권고, 필요 역량·데이터 공백 |

---

### Task 1: 세그먼트별 보유 주체 요약

**Files:**
- Modify: `analysis/process.py`, `tests/test_process.py`

**Interfaces:**
- Produces: `group_holder_summary(held: pd.DataFrame, group: pd.Series, effort_hours: pd.Series) -> pd.DataFrame` — index 그룹, 컬럼 `n, customer_share, bank_days_median, customer_days_median, bank_active_share_median`. `customer_share` = 고객 보유 일수 합 / 전체 일수 합, `bank_active_share` = 공수 시간 / (은행 보유 일수 × 24)의 케이스별 값

- [ ] **Step 1: 실패하는 테스트 추가** — `tests/test_process.py` import에 `group_holder_summary` 추가, 끝에

```python
def test_group_holder_summary():
    held = pd.DataFrame({"bank_days": [1.0, 3.0, 2.0], "customer_days": [3.0, 1.0, 2.0]},
                        index=["a", "b", "c"])
    group = pd.Series({"a": "g1", "b": "g1", "c": "g2"})
    effort = pd.Series({"a": 2.4, "b": 7.2, "c": 4.8})
    out = group_holder_summary(held, group, effort)
    assert out.loc["g1", "n"] == 2 and out.loc["g1", "customer_share"] == 0.5
    assert out.loc["g1", "bank_days_median"] == 2.0
    assert round(out.loc["g1", "bank_active_share_median"], 6) == 0.1
    assert out.loc["g2", "customer_share"] == 0.5
```

- [ ] **Step 2: 실패 확인** — Run: `.venv\Scripts\python -m pytest tests/test_process.py -q` / Expected: ImportError

- [ ] **Step 3: `analysis/process.py`에 추가**

```python
def group_holder_summary(held: pd.DataFrame, group: pd.Series, effort_hours: pd.Series) -> pd.DataFrame:
    """Per group: customer share of elapsed days, median bank/customer days, and the median share
    of bank-held time that was hands-on work (effort hours / bank-held hours)."""
    df = held.assign(group=group.reindex(held.index), effort=effort_hours.reindex(held.index))
    df["bank_active_share"] = df["effort"] / (df["bank_days"] * 24)
    g = df.groupby("group")
    out = pd.DataFrame({
        "n": g.size(),
        "customer_share": g["customer_days"].sum() / (g["customer_days"].sum() + g["bank_days"].sum()),
        "bank_days_median": g["bank_days"].median(),
        "customer_days_median": g["customer_days"].median(),
        "bank_active_share_median": g["bank_active_share"].median(),
    })
    out.index.name = None
    return out
```

(검산: g1의 은행 작업 비중은 a = 2.4/24 = 0.1, b = 7.2/72 = 0.1 → 중앙값 0.1)

- [ ] **Step 4: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests -q` / Expected: 58 passed

- [ ] **Step 5: 커밋**

```powershell
git add analysis/process.py tests/test_process.py; git commit -m "feat: summarize bank vs customer held time by group"
```

---

### Task 2: 두 전제의 검증

**Files:**
- Create: `analysis/19_intervention_check.py`

**Interfaces:**
- Consumes: `load_population`, `process.holder_time`, `group_holder_summary`, `p4_segments.parquet`, `p2_case_effort.parquet`, `p5_segment_efficiency.csv`
- Produces: `outputs/p8_segment_holder.csv`(세그먼트별 n, η, 고객 보유 비중, 은행/고객 보유 일수 중앙값, 은행 작업 비중), `outputs/p8_intervention_checks.csv`(판정 1~3 값과 결과)

- [ ] **Step 1: `analysis/19_intervention_check.py` 작성**

```python
"""Phase 8 — two premises behind the intervention choice:
(1) does "speeding up the bank alone will not solve it" hold in every segment, and
(2) does the bank's current handling order already favour high-η segments?

Durations are read only as the upper bound of what speed could save and as the current
handling order — never as a cause of success (P7). Bank-held time includes nights and weekends.

Run from the project root:

    .venv\\Scripts\\python analysis/19_intervention_check.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_population
from process import group_holder_summary, holder_time

MIN_N = 300
CUSTOMER_MAJORITY = 0.5
SEGMENT_COVERAGE = 0.9
ORDER_RHO = -0.3
QUEUE_ACTIVE_SHARE = 0.10


def main() -> None:
    ev, oc = load_population()
    segments = pd.read_parquet(OUT_DIR / "p4_segments.parquet")["segment"]
    sizes = segments.value_counts()
    keep = segments[segments.isin(sizes.index[sizes >= MIN_N])]
    effort = pd.read_parquet(OUT_DIR / "p2_case_effort.parquet")["effort_hours"]
    eta = pd.read_csv(OUT_DIR / "p5_segment_efficiency.csv", index_col="segment")["eta"]

    held = holder_time(ev).reindex(keep.index)
    table = group_holder_summary(held, keep, effort).join(eta).sort_values("eta")
    table.round(4).to_csv(OUT_DIR / "p8_segment_holder.csv", encoding="utf-8-sig")
    print(f"=== bank vs customer held time by segment ({len(table)} segments) ===\n{table.round(3).to_string()}")

    majority = int((table["customer_share"] >= CUSTOMER_MAJORITY).sum())
    rho_order = table["eta"].corr(table["bank_days_median"], method="spearman")
    rho_customer = table["eta"].corr(table["customer_share"], method="spearman")
    active = float(table["bank_active_share_median"].median())
    checks = pd.DataFrame([
        {"check": "1 customer share >= 50% in segments", "value": f"{majority}/{len(table)}",
         "result": "confirmed at segment level" if majority >= SEGMENT_COVERAGE * len(table) else "not in every segment"},
        {"check": "2 Spearman(eta, bank-held median days)", "value": round(rho_order, 3),
         "result": ("current order already favours high-eta" if rho_order <= ORDER_RHO
                    else "current order does not reflect eta -> reordering has room")},
        {"check": "3 median share of bank-held time that is hands-on work", "value": round(active, 4),
         "result": "queue signal (not business-hours adjusted)" if active < QUEUE_ACTIVE_SHARE else "no clear queue"},
        {"check": "ref Spearman(eta, customer share)", "value": round(rho_customer, 3), "result": "descriptive"},
    ])
    checks.to_csv(OUT_DIR / "p8_intervention_checks.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== premise checks ===\n{checks.to_string(index=False)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/19_intervention_check.py`
기록 대상: 세그먼트별 고객 보유 비중 범위(**판정 1**), ρ(η, 은행 보유 일수)(**판정 2**), 은행 작업 비중 중앙값(**판정 3**)

- [ ] **Step 3: 커밋**

```powershell
git add analysis/19_intervention_check.py outputs/p8_segment_holder.csv outputs/p8_intervention_checks.csv; git commit -m "feat: check intervention premises by segment"
```

---

### Task 3: 판정 문서와 CLAUDE.md 반영

**Files:**
- Create: `docs/08_intervention.md`
- Modify: `CLAUDE.md` (§6 진행 현황표·Phase 8 절·Phase 9·10 절, §10, §12), 이 파일의 진행 기록

- [ ] **Step 1: `docs/08_intervention.md` 작성** — 모든 수치 옆에 출처

```markdown
# Phase 8 — 개입 가능 여부 판정
## 요약 — 무엇을 권고하고 무엇을 권고하지 않는가
## 1. 처리 속도는 해법이 아니다 — 세그먼트 단위 확인 (p8_segment_holder.csv)
## 2. 현재 처리 순서는 효율을 반영하는가 (p8_intervention_checks.csv)
## 3. 개입 수단 매트릭스 — 크기 · 근거의 성격 · 전제 · 등급
## 4. 조건부 권고 (P8 형식)
## 5. 권고하지 않는 것과 그 이유 (처리 속도 개선 단독, 앞단 필터, 무응답 신청 앞단 경량화)
## 6. Phase 9·10으로 넘기는 것 — 수단별 필요 역량, 데이터 공백
```

- [ ] **Step 2: CLAUDE.md 반영** — 진행 현황표, Phase 8 절(판정별 결과·수단 등급), Phase 9 절(필요 역량·데이터 공백), Phase 10 절(수단별 경로 입력), §10 면접 답변("무엇을 권고하나"), §12
- [ ] **Step 3: 이 파일의 진행 기록에 실행 중 변경·결과 요약·커밋 추가**
- [ ] **Step 4: 사용자 보고** — Phase 9 진행계획 착수 여부 확인
- [ ] **Step 5: 커밋**

```powershell
git add docs/08_intervention.md docs/plans/phase-08-intervention.md CLAUDE.md; git commit -m "docs: record phase 8 intervention judgement"
```

---

## 수단 매트릭스 초안 (Task 3에서 판정 결과로 확정)

| 수단 | 크기 | 근거의 성격 | 전제 | 예상 등급 |
|---|---|---|---|---|
| 공수 배분 순서 (η 순 우선 처리) | 공수 예산 50%에서 대출 규모 +13.2% | 관측값 기반 가상 배분 | 접수 시점 세그먼트 판별 가능(Phase 4 확인) · 현재 순서가 η 미반영(판정 2) · 공수가 제약(판정 3 신호) | 판정 2·3 결과에 따라 채택 권고 또는 조건부 |
| 첫 상담 단일 오퍼 | 같은 상담 복수의 성사율 −2.6~−5.5%p | 관측 연관 | 음(−) 연관이 인과일 것 | 검증 후 (A/B) |
| 오퍼 발송 후 접촉 정책 | 공수 절감 3.5%, 회신 전환 효과 미상 | 측정 불가 | 접촉이 회신을 늘릴 것 | 검증 후 (A/B) |
| 심사 앞단 필터 | 규칙상 근거 미충족 | 비율 차이만 확인 | 거절 공수가 식별 가능한 곳에 몰릴 것 | 보류 |
| 처리 속도 개선 단독 | 은행 보유 시간이 경과시간의 약 18% | 구조적 상한 | 고객 보유가 작을 것 | 판정 1이 확인되면 권고하지 않음 |

## 진행 기록

| 날짜 | 내용 |
|---|---|
| 2026-09-11 | 진행계획 작성. 새 분석은 권고의 전제 두 가지(세그먼트별 고객 보유, 현재 처리 순서)로 제한하고 나머지는 Phase 1~7 인용으로 구성. 판정 규칙 고정. 사용자 확인 대기 |
