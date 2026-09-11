# Phase 0 — 데이터 확인과 범위 확정

> 2026-09-11 · 진행계획·기록 [`plans/phase-00-data-scope.md`](plans/phase-00-data-scope.md) · 스크립트 `analysis/00~03` · 테스트 15 passed

## 1. 분석 모집단

| 항목 | 값 | 출처 |
|---|---|---|
| 전체 케이스 | 31,509 | `outputs/p0_cutoff.json` |
| 관측 종료 | 2017-02-01 14:11 UTC | `outputs/p0_cutoff.json` |
| 컷오프 (접수월 완료율 ≥ 0.99) | 2016-11 | `outputs/p0_cutoff.json` |
| 제외 (2016-12 접수) | 2,366 (7.5%) | `02_case_outcomes.py` 출력 |
| 관측창 안 미종료 (제외) | 12 | `02_case_outcomes.py` 출력 |
| **분석 모집단 (`in_population`)** | **29,131** | `outputs/p0_cutoff.json` |

접수월별 완료율과 종료 케이스의 소요일 (`outputs/p0_monthly_completion.csv`):

| 접수월 | 케이스 | 미종료 | 완료율 | 중앙값(일) | p90(일) |
|---|---|---|---|---|---|
| 2016-01 | 2,194 | 0 | 1.000 | 17.7 | 43.0 |
| 2016-02 | 2,412 | 0 | 1.000 | 17.8 | 33.6 |
| 2016-03 | 2,454 | 0 | 1.000 | 17.0 | 32.7 |
| 2016-04 | 2,177 | 0 | 1.000 | 18.9 | 34.6 |
| 2016-05 | 2,068 | 0 | 1.000 | 16.9 | 38.2 |
| 2016-06 | 3,001 | 0 | 1.000 | 20.3 | 36.7 |
| 2016-07 | 3,039 | 0 | 1.000 | 20.1 | 36.0 |
| 2016-08 | 3,085 | 0 | 1.000 | 21.7 | 35.8 |
| 2016-09 | 3,042 | 0 | 1.000 | 21.1 | 34.8 |
| 2016-10 | 2,995 | 1 | 1.000 | 18.9 | 34.8 |
| 2016-11 | 2,676 | 11 | 0.996 | 18.8 | 34.4 |
| 2016-12 | 2,366 | 86 | 0.964 | 16.9 | 32.5 |

**컷오프 판단:** 11월은 완료율 기준을 넘고, p90 소요일(34.4일)도 10월(34.8일)과 차이가 없다. 절단 편향 신호가 없으므로 컷오프를 앞당기지 않는다. 12월은 완료율이 기준 아래이고 중앙값과 p90이 모두 낮아서, 빨리 끝난 건만 남은 절단 패턴과 부합한다. 그래서 제외한다.

## 2. 결과 정의

종료 이벤트 패턴 (`outputs/p0_end_patterns.csv`):

| 패턴 | 케이스 |
|---|---|
| A_Pending | 17,228 |
| A_Cancelled | 10,431 |
| A_Denied | 3,751 |
| A_Denied>A_Denied | 1 |
| (종료 없음) | 98 |

- 서로 다른 종료 이벤트가 섞인 케이스(예: A_Pending 후 A_Cancelled)는 없다. "마지막 종료 이벤트 = 결과" 규칙을 유지한다.
- 결과 라벨: 성사 17,228 / 취소 10,431 / 거절 3,752 / 미종료 98 (`02_case_outcomes.py` 출력)
- 정합성 확인: A_Pending 17,228건 = O_Accepted 17,228건 (`outputs/p0_activity_counts.csv`)
- **주 성공 정의 = A_Pending 도달.** 문헌 정의(A_Pending 도달)와 결과 라벨 정의(마지막 종료 이벤트)가 다른 케이스는 0건이다 (`03_replicate_prior.py` 출력).

## 3. 변수 목록 — 시점과 누수 여부로 세 층 (P2)

속성 품질 (`outputs/p0_attribute_profile.csv`, 케이스 31,509건 / 오퍼 42,995건 기준):

| 층 | 속성 | dtype | 결측률 | 0값 비율 | 고유값 |
|---|---|---|---|---|---|
| 접수 시점 | case:RequestedAmount | float | 0% | 9.77% | 701 |
| 접수 시점 | case:LoanGoal | str | 0% | — | 14 |
| 접수 시점 | case:ApplicationType | str | 0% | — | 2 |
| 처리 중 | OfferedAmount | float | 0% | 0.00% | 663 |
| 처리 중 | MonthlyCost | float | 0% | 0.00% | 5,816 |
| 처리 중 | NumberOfTerms | float | 0% | 0.00% | 147 |
| 처리 중 | FirstWithdrawalAmount | float | 0% | 29.74% | 5,930 |
| **결과 누수** | CreditScore | float | 0% | 64.51% | 520 |
| **결과 누수** | Selected | boolean | 0% | — | 2 |
| **결과 누수** | Accepted | boolean | 0% | — | 2 |

- 접수 시점 3종은 모든 케이스 안에서 값이 일정하다 (`01_inspect_schema.py` 출력).
- ApplicationType: New credit 28,120 / Limit raise 3,389 (`01_inspect_schema.py` 출력).
- 오퍼: 케이스당 1~10건. 오퍼가 없는 케이스는 0건이고, OfferID 연결 누락도 0건이다 (`03_replicate_prior.py`, `01_inspect_schema.py` 출력).

**결과 누수 판정 근거** — 오퍼 최종 상태별 속성 (`outputs/p0_offer_attrs_by_final_state.csv`):

| 최종 상태 | 오퍼 | CreditScore > 0 | Selected = true | Accepted = true |
|---|---|---|---|---|
| O_Accepted | 17,228 | 88.6% | 100.0% | 81.4% |
| O_Cancelled | 20,898 | 0.0% | 4.7% | 68.8% |
| O_Refused | 4,695 | 0.0% | 75.0% | 35.2% |
| (최종 상태 없음) | 174 | 0.0% | 25.9% | 57.5% |

CreditScore는 `O_Create Offer` 이벤트에 기록돼 있지만, 수락된 오퍼에서만 0이 아니다. 오퍼 생성 시점에 알 수 없는 결과가 값에 반영돼 있다는 뜻이다. Selected와 Accepted도 최종 상태에 따라 크게 갈린다. 세 속성은 설명용으로도 쓰지 않는다.

## 4. 선행 수치 재현

`outputs/p0_replication.csv`, 성공 = A_Pending 도달:

| 항목 | 문헌 | 재현 (전체 31,509) | 분석 모집단 (29,131) |
|---|---|---|---|
| 단일 오퍼 케이스 | 22,950 | 22,950 | 21,175 |
| 복수 오퍼 케이스 | 8,559 | 8,559 | 7,956 |
| 단일 오퍼 성사율 | 53.1% | 53.06% | 53.42% |
| 복수 오퍼 성사율 | 59.0% | 59.00% | 58.90% |
| 복수 오퍼 비중 | 27% | 27.2% | — |

문헌(metafinanz p.24·p.28, Badakhshan et al. p.18)과 건수가 정확히 일치하고, 성사율도 반올림 범위 안에서 일치한다. 오퍼 계수 방식(O_Create Offer 건수)과 성공 정의가 문헌과 같다는 뜻이다.

## 5. 주의점

- **요청 주체 식별 불가:** O_Create Offer 42,995건 모두 Action이 `Created`이고 직원 계정(120명)이 생성했다 (`outputs/p0_offer_creation_actions.csv`). 추가 오퍼가 고객 요청인지 은행 선제 제시인지 로그로 구분할 수 없다.
- **RequestedAmount 0값:** Limit raise 766건(22.6%), New credit 2,314건(8.2%) (`outputs/p0_requested_amount_zero.csv`). 금액 미기재로 보고 소액 구간과 섞지 않는다.
- **LoanGoal의 정보 없는 범주:** "Other, see explanation" 2,985 / "Unknown" 2,365 / "Not speficied" 1,065 (원문 표기 그대로) (`01_inspect_schema.py` 출력). 용도 축에서 따로 처리해야 한다.
- **시스템 계정(User_1) 비중:** Application 27.5% / Offer 5.1% / Workflow 9.4% (`outputs/p0_system_resource_share.csv`). Phase 2 공수 측정에서 제외 대상이다.
- **최종 상태가 없는 오퍼 174건:** 미종료 케이스와 겹칠 가능성이 있다. 분석 모집단 기준으로 Phase 1에서 확인한다.
- **p90 소요일이 33~43일에 몰려 있다.** 30일 무응답 자동 취소 규칙(P7)과 부합하는지는 Phase 1에서 확인한다. 여기서는 판단하지 않는다.

## 6. 다음 Phase로 넘기는 것

- **모집단:** `outputs/p0_case_outcomes.parquet`의 `in_population == True` (29,131건)
- **결과 라벨:** `outcome` (success / cancelled / denied). 주 성공 정의는 `reached_pending`
- **오퍼 테이블:** `outputs/p0_offers.parquet` (오퍼 42,995건, 생성 시점 속성). 최종 상태는 `offers.offer_final_state`로 붙인다
- **사용 가능한 변수:** 접수 시점 3종(규칙용), 처리 중 4종과 오퍼 건수(설명용). 결과 누수 3종은 사용 금지
- **Phase 6 출발값:** 분석 모집단 기준 단일 53.42% / 복수 58.90%. 레버는 "추가 오퍼 생성 정책 전반"
