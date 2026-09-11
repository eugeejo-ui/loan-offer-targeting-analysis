# Phase 3 — 방법론 선언 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 효율 지표 η의 구성요소(R, p, E)를 확정하고, R을 어떻게 잡느냐가 그룹 순위를 바꾸는지 검증한다. c/m 스캔 설계, 참조 범위, 제외 항목을 `docs/03_method.md` 한 문서로 선언한다.

**Architecture:** 수락 오퍼 조건에서 R 후보를 만드는 로직은 새 모듈 `analysis/value.py`에 둔다. 접수 시점 변수를 케이스 단위로 모으는 로직은 `analysis/segments.py`에 둔다(Phase 4에서 확장). 스크립트 `09`는 R 후보와 역산 금리를, `10`은 단일 접수 변수로 만든 잠정 그룹에서 η 순위의 안정성을 산출한다. 인건비 참조값은 공개 통계에서 찾아 참조선으로만 쓴다.

**Tech Stack:** Python 3.12, pandas 3.0.5, numpy, pytest (Windows PowerShell 5.1)

**Spec:** `CLAUDE.md` §5 P1·P2·P6, §6 Phase 3 / Phase 2 결론 `docs/02_effort.md` §6

## Global Constraints

- 모집단은 `loader.load_population()`으로만 불러온다 (29,131건). 성공 = `reached_pending`.
- E = `outputs/p2_case_effort.parquet`의 `effort_hours`. 세그먼트의 E는 **성사 여부와 무관하게 모든 신청의 평균**이다 (공수는 실패한 신청에도 쓰인다).
- R은 성사 케이스의 수락 오퍼에서만 계산한다. 세그먼트 축은 접수 시점의 `RequestedAmount`를 쓰고, R은 `OfferedAmount`를 쓴다. 둘을 섞지 않는다.
- 이자 총액(`MonthlyCost × NumberOfTerms − OfferedAmount`)은 R 후보가 아니다. **참조선(손익분기 인건비 상한)** 계산에만 쓴다 (P1).
- 결과 누수 속성(CreditScore, Selected, Accepted)은 쓰지 않는다 (P2).
- 이 Phase의 그룹핑은 **잠정**이다. 단일 접수 변수 하나씩으로만 묶는다. 세그먼트 정의는 Phase 4에서 한다.
- 인건비 단가와 마진율은 추정하지 않는다. 공개 통계는 참조선으로만 쓰고 계산 입력으로 쓰지 않는다 (P1, P6).
- 스크립트 번호 `09~10`, 산출 파일 접두어 `p3_`. 차트는 만들지 않는다.
- PowerShell 5.1: `&&` 대신 `;`. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## 사전 탐색 (계획 설계용, 수치는 Task에서 재산출)

- 성사 케이스는 모두 수락 오퍼(O_Accepted)가 정확히 1건이고, 성사하지 않은 케이스에는 없다. 수락 오퍼는 모두 오퍼 테이블과 연결된다
- 수락 오퍼 금액: 최소 5,000, 중앙값 15,000, 최대 75,000유로. 상환기간 중앙값 83개월. 신청 금액이 있는 경우 오퍼 금액과 같은 비중은 약 77%
- 역산 연 금리: 중앙값 약 4.9%, p10 4.2%, p90 6.5%. 최대 약 60%인 이상치가 있다

## 선언할 식 (P1)

```
EV_s = m · R̄_s · p_s − c · Ē_s
  R̄_s : 세그먼트 s의 성사 케이스가 수락한 오퍼 금액 평균 (유로)
  p_s : 세그먼트 s의 성사율 (A_Pending 도달)
  Ē_s : 세그먼트 s 모든 신청의 평균 공수 (시간, 활동별 p99 캡)
  m   : 대출 1유로당 생애 순마진 (미지)       c : 공수 1시간당 인건비 (미지)

EV_s < 0  ⇔  c/m > η_s,   η_s = R̄_s · p_s / Ē_s   (단위: 공수 1시간당 기대 대출금액, 유로/시간)
```

**참조선 — 손익분기 인건비 상한:** R 대신 성사 케이스의 이자 총액 평균을 넣은 η_I = Ī_s · p_s / Ē_s는 "은행이 이자를 전부 가진다고 가정했을 때 신청 한 건이 본전이 되는 시간당 인건비"다. 실제 손익분기 인건비는 η_I × (이자 중 순마진 비중)이므로 η_I보다 반드시 낮다. 조달비용·신용손실·중도상환을 빼지 않은 상한이라는 점을 명시한다.

## File Structure

| 파일 | 책임 |
|---|---|
| `analysis/value.py` | 수락 오퍼 조건, 역산 금리, R 후보, 그룹별 η |
| `analysis/segments.py` | 케이스 단위 접수 시점 변수(A_Submitted 유무 포함), 잠정 금액 구간 |
| `analysis/09_revenue_base.py` | 수락 오퍼 연결 점검, R 후보·역산 금리 분포 |
| `analysis/10_eta_stability.py` | 잠정 그룹별 η(R 후보 3종), R 선택에 따른 순위 안정성 |
| `tests/test_value.py`, `tests/test_segments.py` | 단위 테스트 6개 |
| `docs/03_method.md` | 방법론 선언 문서 |

---

### Task 1: value·segments 모듈

**Files:**
- Create: `analysis/value.py`, `analysis/segments.py`, `tests/test_value.py`, `tests/test_segments.py`

**Interfaces:**
- Produces (value.py):
  - `accepted_offers(events, offers) -> pd.DataFrame` — index 케이스, 컬럼 `offer_id, n_accepted, OfferedAmount, NumberOfTerms, MonthlyCost`
  - `implied_annual_rate(principal, monthly, terms, iterations=80) -> np.ndarray` — 상환액 합이 원금 이하면 NaN
  - `revenue_bases(acc) -> pd.DataFrame` — 컬럼 `r_amount, r_amount_years, interest_total, implied_rate`
  - `group_eta(frame, by, r_col, e_col, success_col="reached_pending") -> pd.DataFrame` — index 그룹, 컬럼 `n, p, r_mean, e_mean, eta`
- Produces (segments.py):
  - `intake_frame(events) -> pd.DataFrame` — index 케이스, 컬럼 `case:RequestedAmount, case:LoanGoal, case:ApplicationType, has_submitted`
  - `amount_band(requested, q=5) -> pd.Series` — 양수 신청 금액의 분위 구간(문자열), 0은 `"0 (미기재)"`

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_value.py`

```python
import numpy as np
import pandas as pd

from value import accepted_offers, group_eta, implied_annual_rate, revenue_bases

CASE = "case:concept:name"


def test_accepted_offers_takes_terms_from_offer_table():
    ev = pd.DataFrame({CASE: ["A", "A", "B"],
                       "concept:name": ["O_Create Offer", "O_Accepted", "O_Create Offer"],
                       "OfferID": [None, "Offer_1", None]})
    offers = pd.DataFrame({"offer_id": ["Offer_1", "Offer_2"], "OfferedAmount": [10000.0, 5000.0],
                           "NumberOfTerms": [60.0, 24.0], "MonthlyCost": [200.0, 230.0]})
    acc = accepted_offers(ev, offers)
    assert list(acc.index) == ["A"]
    assert acc.loc["A", "OfferedAmount"] == 10000 and acc.loc["A", "n_accepted"] == 1


def test_implied_annual_rate_recovers_known_rate():
    monthly_r = 1.05 ** (1 / 12) - 1
    payment = 10000 * monthly_r / (1 - (1 + monthly_r) ** -60)
    rate = implied_annual_rate([10000, 10000], [payment, 100], [60, 60])
    assert abs(rate[0] - 0.05) < 1e-6
    assert np.isnan(rate[1])


def test_revenue_bases():
    acc = pd.DataFrame({"OfferedAmount": [12000.0], "NumberOfTerms": [24.0], "MonthlyCost": [550.0]},
                       index=pd.Index(["A"], name=CASE))
    rb = revenue_bases(acc)
    assert rb.loc["A", "r_amount"] == 12000
    assert rb.loc["A", "r_amount_years"] == 24000
    assert rb.loc["A", "interest_total"] == 1200


def test_group_eta_uses_success_mean_r_and_all_case_effort():
    frame = pd.DataFrame({"g": ["x", "x", "y", "y"], "reached_pending": [True, False, True, True],
                          "r": [10.0, np.nan, 20.0, 40.0], "e": [1.0, 3.0, 2.0, 2.0]})
    out = group_eta(frame, "g", "r", "e")
    assert out.loc["x", "eta"] == 10 * 0.5 / 2.0
    assert out.loc["y", "eta"] == 30 * 1.0 / 2.0
```

`tests/test_segments.py`:

```python
import pandas as pd

from segments import amount_band, intake_frame


def test_intake_frame_flags_submitted():
    ev = pd.DataFrame({
        "case:concept:name": ["a", "a", "b"],
        "concept:name": ["A_Create Application", "A_Submitted", "A_Create Application"],
        "case:RequestedAmount": [1000.0, 1000.0, 0.0],
        "case:LoanGoal": ["Car", "Car", "Boat"],
        "case:ApplicationType": ["New credit", "New credit", "Limit raise"],
    })
    f = intake_frame(ev)
    assert bool(f.loc["a", "has_submitted"]) and not bool(f.loc["b", "has_submitted"])
    assert f.loc["b", "case:LoanGoal"] == "Boat"


def test_amount_band_keeps_zero_separate():
    b = amount_band(pd.Series([0, 100, 200, 300, 400], index=list("abcde"), dtype=float), q=2)
    assert b["a"] == "0 (미기재)"
    assert b["b"] == b["c"] and b["d"] == b["e"] and b["b"] != b["d"]
```

- [ ] **Step 2: 실패 확인** — Run: `.venv\Scripts\python -m pytest tests/test_value.py tests/test_segments.py -q` / Expected: `No module named 'value'`, `No module named 'segments'`

- [ ] **Step 3: `analysis/value.py` 구현**

```python
"""Revenue bases of a successful application and the per-effort efficiency η (P1)."""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import ACT, CASE, OFFER_ID

TERM_COLS = ["OfferedAmount", "NumberOfTerms", "MonthlyCost"]


def accepted_offers(events: pd.DataFrame, offers: pd.DataFrame) -> pd.DataFrame:
    """Terms of the accepted offer per case; `n_accepted` flags cases with more than one."""
    acc = events.loc[events[ACT] == "O_Accepted", [CASE, OFFER_ID]]
    terms = offers.set_index("offer_id")[TERM_COLS]
    return acc.join(terms, on=OFFER_ID).groupby(CASE).agg(
        offer_id=(OFFER_ID, "first"), n_accepted=(OFFER_ID, "size"),
        **{c: (c, "first") for c in TERM_COLS})


def implied_annual_rate(principal, monthly, terms, iterations: int = 80) -> np.ndarray:
    """Annual rate implied by an annuity, by bisection on the monthly rate.

    NaN where total payments do not exceed the principal.
    """
    p, m, n = (np.asarray(x, dtype=float) for x in (principal, monthly, terms))
    lo, hi = np.full(p.shape, 1e-9), np.full(p.shape, 0.1)
    for _ in range(iterations):
        mid = (lo + hi) / 2
        payment = p * mid / (1 - (1 + mid) ** -n)
        lo = np.where(payment < m, mid, lo)
        hi = np.where(payment >= m, mid, hi)
    rate = (1 + (lo + hi) / 2) ** 12 - 1
    return np.where(m * n > p, rate, np.nan)


def revenue_bases(acc: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame({
        "r_amount": acc["OfferedAmount"],
        "r_amount_years": acc["OfferedAmount"] * acc["NumberOfTerms"] / 12,
        "interest_total": acc["MonthlyCost"] * acc["NumberOfTerms"] - acc["OfferedAmount"],
        "implied_rate": implied_annual_rate(acc["OfferedAmount"], acc["MonthlyCost"], acc["NumberOfTerms"]),
    }, index=acc.index)


def group_eta(frame: pd.DataFrame, by: str, r_col: str, e_col: str,
              success_col: str = "reached_pending") -> pd.DataFrame:
    """η = mean R of successes × success rate / mean effort of all cases, per group."""
    g = frame.groupby(by, observed=True)
    out = pd.DataFrame({
        "n": g.size(),
        "p": g[success_col].mean(),
        "r_mean": frame[frame[success_col]].groupby(by, observed=True)[r_col].mean(),
        "e_mean": g[e_col].mean(),
    })
    out["eta"] = out["r_mean"] * out["p"] / out["e_mean"]
    return out
```

- [ ] **Step 4: `analysis/segments.py` 구현**

```python
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
```

- [ ] **Step 5: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests -q` / Expected: 35 passed (기존 29 + 6)

- [ ] **Step 6: 커밋**

```powershell
git add analysis/value.py analysis/segments.py tests/test_value.py tests/test_segments.py; git commit -m "feat: add revenue base and intake variable modules"
```

---

### Task 2: R 후보와 역산 금리

**Files:**
- Create: `analysis/09_revenue_base.py`

**Interfaces:**
- Consumes: `load_population`, `outputs/p0_offers.parquet`, `accepted_offers`, `revenue_bases`, `intake_frame`
- Produces: `outputs/p3_accepted_offers.parquet` — index 성사 케이스, 컬럼 `r_amount, r_amount_years, interest_total, implied_rate, offer_id, OfferedAmount, NumberOfTerms, MonthlyCost, requested` → **Phase 5의 R 입력**. `p3_revenue_summary.csv`

- [ ] **Step 1: `analysis/09_revenue_base.py` 작성**

```python
"""Phase 3 — what a successful application is worth: the accepted offer's terms.

Run from the project root:

    .venv\\Scripts\\python analysis/09_revenue_base.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_population
from segments import intake_frame
from value import accepted_offers, revenue_bases

RATE_OUTLIER = 0.2


def main() -> None:
    ev, oc = load_population()
    offers = pd.read_parquet(OUT_DIR / "p0_offers.parquet")
    acc = accepted_offers(ev, offers)
    success = oc.index[oc["reached_pending"]]
    print(f"success cases={len(success):,}  with an accepted offer={int(acc.index.isin(success).sum()):,}  "
          f"accepted offers in non-success cases={int((~acc.index.isin(success)).sum()):,}")
    print(f"accepted offers per case: {acc['n_accepted'].value_counts().to_dict()}")

    bases = revenue_bases(acc).join(acc[["offer_id", "OfferedAmount", "NumberOfTerms", "MonthlyCost"]])
    bases["requested"] = intake_frame(ev)["case:RequestedAmount"].reindex(bases.index)
    bases.to_parquet(OUT_DIR / "p3_accepted_offers.parquet")

    cols = ["r_amount", "r_amount_years", "interest_total", "NumberOfTerms", "implied_rate", "requested"]
    summary = bases[cols].describe(percentiles=[0.1, 0.5, 0.9]).T.round(4)
    summary.to_csv(OUT_DIR / "p3_revenue_summary.csv", encoding="utf-8-sig")
    print(f"\n=== revenue bases of accepted offers ===\n{summary.to_string()}")

    stated = bases["requested"] > 0
    print(f"\noffered == requested (requested > 0): {(bases.loc[stated, 'r_amount'] == bases.loc[stated, 'requested']).mean():.1%}")
    print(f"offered <  requested (requested > 0): {(bases.loc[stated, 'r_amount'] < bases.loc[stated, 'requested']).mean():.1%}")
    print(f"accepted offer with requested == 0: {int((~stated).sum()):,}")
    print(f"implied annual rate > {RATE_OUTLIER:.0%}: {int((bases['implied_rate'] > RATE_OUTLIER).sum()):,} offers")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/09_revenue_base.py`
기록 대상: 연결 점검(**판단 지점 1**), R 후보·이자 총액·역산 금리 분포, 오퍼 vs 신청 금액(**판단 지점 4**), 금리 이상치 수(**판단 지점 3**)

- [ ] **Step 3: 커밋**

```powershell
git add analysis/09_revenue_base.py outputs/p3_accepted_offers.parquet outputs/p3_revenue_summary.csv; git commit -m "feat: derive revenue bases from accepted offers"
```

---

### Task 3: R 선택에 따른 η 순위 안정성

**Files:**
- Create: `analysis/10_eta_stability.py`

**Interfaces:**
- Consumes: `intake_frame`, `amount_band`, `group_eta`, `outputs/p2_case_effort.parquet`, `outputs/p3_accepted_offers.parquet`
- Produces: `outputs/p3_eta_provisional.csv`(잠정 그룹별 n, p, Ē, R̄·η — R 후보 3종), `outputs/p3_eta_rank_stability.csv`

- [ ] **Step 1: `analysis/10_eta_stability.py` 작성**

```python
"""Phase 3 — does the choice of revenue base R change how groups rank on η?

Provisional groupings only (one intake variable at a time); Phase 4 defines segments.

Run from the project root, after 09_revenue_base.py:

    .venv\\Scripts\\python analysis/10_eta_stability.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_population
from segments import amount_band, intake_frame
from value import group_eta

GROUPINGS = ["case:ApplicationType", "case:LoanGoal", "has_submitted", "amount_band"]
R_COLS = ["r_amount", "r_amount_years", "interest_total"]
MIN_N = 300
MIN_RANK_CORR = 0.9


def main() -> None:
    ev, oc = load_population()
    frame = intake_frame(ev).reindex(oc.index)
    frame["amount_band"] = amount_band(frame["case:RequestedAmount"])
    frame["reached_pending"] = oc["reached_pending"]
    frame = frame.join(pd.read_parquet(OUT_DIR / "p2_case_effort.parquet")[["effort_hours"]])
    frame = frame.join(pd.read_parquet(OUT_DIR / "p3_accepted_offers.parquet")[R_COLS])

    tables, stability = [], []
    for by in GROUPINGS:
        etas = {r: group_eta(frame, by, r, "effort_hours") for r in R_COLS}
        table = etas["r_amount"][["n", "p", "e_mean"]].copy()
        for r, t in etas.items():
            table[f"r_mean_{r}"] = t["r_mean"]
            table[f"eta_{r}"] = t["eta"]
        big = table[table["n"] >= MIN_N]
        corr = big["eta_r_amount"].corr(big["eta_r_amount_years"], method="spearman")
        stability.append({"grouping": by, "groups": len(table), "groups_n_ge_min": len(big),
                          "spearman_amount_vs_amount_years": round(float(corr), 3)})
        tables.append(table.reset_index(names="group").assign(grouping=by))

    provisional = pd.concat(tables, ignore_index=True).round(4)
    provisional.to_csv(OUT_DIR / "p3_eta_provisional.csv", index=False, encoding="utf-8-sig")
    stab = pd.DataFrame(stability)
    stab.to_csv(OUT_DIR / "p3_eta_rank_stability.csv", index=False, encoding="utf-8-sig")
    print(f"=== provisional η by single intake variable ===\n{provisional.to_string(index=False)}")
    print(f"\n=== rank stability, groups with n >= {MIN_N} ===\n{stab.to_string(index=False)}")
    weakest = stab["spearman_amount_vs_amount_years"].min()
    verdict = ("R = accepted amount, amount x years as sensitivity" if weakest >= MIN_RANK_CORR
               else "carry both R candidates into Phase 5")
    print(f"weakest: {weakest:.3f} -> {verdict}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/10_eta_stability.py`
기록 대상: 그룹핑별 순위 상관(**판단 지점 2**), 잠정 η 범위(**판단 지점 6** 스캔 범위), η_I 범위(참조선)
주의: 그룹이 2개뿐인 그룹핑(ApplicationType, A_Submitted)의 순위 상관은 ±1만 나온다. 순서가 뒤집히는지만 읽는다

- [ ] **Step 3: 커밋**

```powershell
git add analysis/10_eta_stability.py outputs/p3_eta_provisional.csv outputs/p3_eta_rank_stability.csv; git commit -m "feat: check eta ranking stability across revenue bases"
```

---

### Task 4: 인건비 참조값 조사

코드는 없다. 공개 통계에서 참조값을 찾아 출처와 함께 기록한다.

- [ ] **Step 1:** 네덜란드 금융·보험업(NACE K)의 2016년 시간당 노동비용을 Eurostat 노동비용 통계에서 찾는다 (WebSearch → 통계 페이지 WebFetch)
- [ ] **Step 2:** 찾으면 값, 단위, 연도, URL을 `docs/03_method.md` 참조 범위 절에 적는다. 이 값은 **참조선**이다. η_I와 비교해 "이자를 전부 가져도 본전이 안 되는 그룹이 있는가"를 읽는 데만 쓴다
- [ ] **Step 3:** 못 찾거나 출처가 불명확하면 참조선을 생략하고, 그 사실을 문서에 적는다 (P6)

---

### Task 5: 방법론 선언 문서와 CLAUDE.md 반영

**Files:**
- Create: `docs/03_method.md`
- Modify: `CLAUDE.md` (§5 P1, §6 진행 현황표·Phase 3 절·Phase 5 절, §12), 이 파일의 진행 기록

- [ ] **Step 1: `docs/03_method.md` 작성** — 모든 수치 옆에 `outputs/p3_*` 또는 외부 출처

```markdown
# Phase 3 — 방법론 선언

## 1. 식과 구성요소 (R̄, p, Ē, η) — 정의와 단위, 데이터 출처
## 2. R의 선택 — 후보 비교와 순위 안정성 (p3_eta_rank_stability.csv)
## 3. 참조선 — 손익분기 인건비 상한 η_I와 공개 인건비 통계
## 4. c/m 스캔 설계 — 축, 범위, 결과 표현 방식
## 5. 제외 항목과 근거 (P6)
## 6. 잠정 관찰 (p3_eta_provisional.csv — Phase 4 전 참고용, 결론 아님)
## 7. 다음 Phase로 넘기는 것
```

- [ ] **Step 2: CLAUDE.md 반영** — P1에 확정된 R·E 정의, Phase 3 절(판단 지점별 결과), Phase 5 절(R 입력·스캔 범위), §6 진행 현황표, §12
- [ ] **Step 3: 이 파일의 진행 기록에 실행 중 변경·결과 요약·커밋 추가**
- [ ] **Step 4: 사용자 보고** — Phase 4 진행계획 착수 여부 확인
- [ ] **Step 5: 커밋**

```powershell
git add docs/03_method.md docs/plans/phase-03-method.md CLAUDE.md; git commit -m "docs: declare phase 3 method"
```

---

## 판단 지점

1. **R 연결:** 성사 케이스마다 수락 오퍼가 정확히 1건이고 비성사 케이스에는 없으면 → R을 모든 성사 케이스에 정의할 수 있다
2. **R 선택:** 잠정 그룹핑에서 수락 금액과 금액×기간의 η 순위 상관 최솟값(n ≥ 300 그룹)이 0.9 이상이면 → 가정이 가장 적은 **수락 금액**을 주 R로, 금액×기간은 민감도용으로 둔다. 0.9 미만이면 두 후보를 Phase 5에 모두 넘긴다
3. **역산 금리 이상치:** 연 20% 초과 오퍼는 이자 총액 기반 참조선에서만 영향을 준다. 건수를 보고하고 참조선 계산에서의 처리(포함/제외)를 정한다
4. **오퍼 금액 ≠ 신청 금액:** 차이 비중을 기록하고, 세그먼트 축(RequestedAmount)과 R(OfferedAmount)을 분리한다는 선언을 문서에 넣는다
5. **참조값:** 공개 인건비 통계를 찾으면 참조선으로만 표시하고, 못 찾으면 생략한다
6. **c/m 스캔 범위:** 로그 축으로, 잠정 η 최솟값의 1/10부터 최댓값의 10배까지 둔다. Phase 5 결과가 이 범위를 벗어나면 넓힌다

## 진행 기록

| 날짜 | 내용 |
|---|---|
| 2026-09-11 | 진행계획 작성. 사전 탐색(수락 오퍼 1:1 연결, 오퍼 조건 분포, 역산 금리)을 R 후보와 참조선 설계에 반영. 사용자 확인 대기 |
