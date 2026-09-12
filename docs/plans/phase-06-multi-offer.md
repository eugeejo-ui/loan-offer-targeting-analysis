# Phase 6 — 복수 오퍼 역전점 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 복수 오퍼의 성사율 우위가 ① 세그먼트로 층화한 뒤에도 남는지 ② "같은 상담"과 "나중 상담" 중 어디서 오는지 ③ 추가 공수 1시간당 얼마의 대출 규모를 더 만드는지를 확인한다. 금액 구간별로 추가 오퍼가 역전(공수는 늘고 가치는 줄어듦)하는 지점이 있는지 판정한다.

**Architecture:** 케이스별 오퍼 수와 상담 구분은 `analysis/offers.py`에, 층화 차이와 증분 효율은 `analysis/efficiency.py`에 두고 합성 데이터로 테스트한다. 스크립트 `15`는 그룹을 만들고 층화 전 비교를, `16`은 층화 차이와 금액 구간·세그먼트별 증분 효율을 산출한다.

**Tech Stack:** Python 3.12, pandas 3.0.5, numpy, pytest (Windows PowerShell 5.1)

**Spec:** `CLAUDE.md` 3장(대화 구분 불일치), 5장 P3, 6장 Phase 6, 7장 시나리오 1 / `docs/05_expected_value.md` 5장·6장

## Global Constraints

- 모집단은 Phase 4 세그먼트 중 300건 이상 39개(28,243건)이고, 층화 단위도 이 세그먼트다.
- 주 조합은 R = `r_amount`, E = `effort_hours`다. 증분의 참조선은 이자 총액(`interest_total`)과 참조 인건비 57.6유로/시간이다.
- **모든 복수 오퍼 비교는 관측된 연관이다.** 나중 상담의 오퍼는 고객이 아직 참여하고 있어야 생긴다. 따라서 그 차이는 **상한**으로만 서술한다 (P3). 같은 상담의 복수 제시가 은행의 레버에 더 가깝지만, 이것도 인과로 쓰지 않는다.
- 요청 주체는 식별할 수 없다 (Phase 0). 레버는 "추가 오퍼 생성 정책 전반"이다.
- 층화·증분 계산에서 비교 그룹마다 최소 50건이 있어야 그 층을 쓴다.
- 스크립트 번호 `15~16`, 산출 파일 접두어 `p6_`. 차트는 만들지 않는다.
- PowerShell 5.1: `&&` 대신 `;`. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## 상담 구분 정의 (3장 보고서 간 불일치 대응)

| 정의 | "나중 상담" 판정 | 근거 |
|---|---|---|
| D1 시간 기준 | 오퍼 생성 시각의 간격이 1일을 넘는다 | KPMG의 "1일 이상 떨어진 대화" 정의 |
| D2 발송 기준 | 첫 오퍼가 발송된 뒤에 추가 오퍼가 생성됐다 | 고객이 오퍼를 받아본 뒤 다시 상담했다는 순서 |

두 정의에서 결론의 방향이 같으면 "정의에 강건"이라고 판정한다.

## 사전 탐색 (계획 설계용, 수치는 Task에서 재산출)

- 복수 오퍼 7,956건 중 D1 나중 상담 4,553건, D2 나중 상담 5,458건. 두 정의가 모두 "같은 상담"이라고 본 것은 2,479건, 모두 "나중"이라고 본 것은 4,534건이다
- **층화 전 성사율:** 단일 0.534 / 같은 상담 복수 0.483(D1)·0.456(D2) / 나중 상담 복수 0.668(D1)·0.650(D2). **복수 오퍼의 우위는 전부 나중 상담에서 나오고, 같은 상담의 복수 제시는 단일보다 성사율이 낮다.** metafinanz와 같은 방향이고 Badakhshan과는 반대다
- **공수:** 나중 상담 복수는 단일보다 약 52% 많다(0.864 vs 0.569시간). 같은 상담 복수는 거의 같다(0.581)
- 세그먼트당 복수 오퍼는 중앙값 167건이고, 50건 이상인 세그먼트가 35개다

## 판정 규칙 (착수 전 고정)

1. **층화 후 우위:** 세그먼트 층화 가중 평균 Δ성사율(복수 − 단일)이 +2%p 이상이면 "층화 후에도 우위 유지", ±2%p 안이면 "층화하면 사라짐", −2%p 이하면 "역전"
2. **상담 구분:** 같은 상담·나중 상담 각각의 층화 Δ성사율 부호가 D1과 D2에서 같으면 "정의에 강건", 다르면 두 결과를 모두 적는다
3. **증분 분류** (금액 구간·세그먼트마다, 복수 vs 단일): `공수↑·가치↑` / `공수↑·가치↓`(**역전**) / `공수↓·가치↑` / `공수↓·가치↓`. 가치 = R̄ × 성사율
4. **반전 시나리오 1 판정:** 가장 작은 금액 구간(6,500유로 이하)에서
   - 복수 오퍼가 `공수↑·가치↓`이면 → **관측상 역전 확인**
   - `공수↑·가치↑`이지만 증분 η가 Phase 5 세그먼트 η의 최솟값(4,374)보다 낮으면 → **"추가 오퍼의 공수가 어느 세그먼트 평균보다도 비효율"로 부분 확인**
   - 그 외 → 기각
5. **표본:** 비교 그룹마다 50건 이상인 층만 쓴다. 층화에 쓴 층의 수를 보고한다

## File Structure

| 파일 | 책임 |
|---|---|
| `analysis/offers.py` | `offer_first_sent`, `conversation_split`, `offer_group` 추가 |
| `analysis/efficiency.py` | `stratified_diff`, `incremental_eta` 추가 |
| `analysis/15_multi_offer_groups.py` | 케이스별 오퍼 그룹(D1·D2), 정의 교차표, 층화 전 비교 |
| `analysis/16_multi_offer_increment.py` | 층화 Δ성사율·Δ공수, 금액 구간·세그먼트별 증분 η와 역전 분류 |
| `tests/test_offers.py`, `tests/test_efficiency.py` | 단위 테스트 5개 추가 |
| `docs/06_multi_offer.md` | Phase 6 결론 문서 |

---

### Task 1: 오퍼 그룹과 증분 함수

**Files:**
- Modify: `analysis/offers.py`, `analysis/efficiency.py`, `tests/test_offers.py`, `tests/test_efficiency.py`

**Interfaces:**
- Produces (offers.py):
  - `offer_first_sent(events) -> pd.Series` — index offer_id, 첫 O_Sent 시각
  - `conversation_split(offers, first_sent, same_day=1.0) -> pd.DataFrame` — index 케이스, 컬럼 `n_offers, span_days, d1_later, d2_later`
  - `offer_group(split, later_col) -> pd.Series` — `single` / `multi_same` / `multi_later`
- Produces (efficiency.py):
  - `stratified_diff(frame, group_col, base, other, strata, value_col, min_n=50) -> tuple[float, pd.DataFrame]` — 층 크기 가중 평균 차이(other − base)와 층별 표
  - `incremental_eta(frame, group_col, base, other, strata, r_col, e_col, success_col="reached_pending", min_n=50) -> pd.DataFrame` — 층별 `n_base, n_other, p_base, p_other, value_base, value_other, e_base, e_other, eta_base, delta_value, delta_effort, incremental_eta, class`

- [ ] **Step 1: 실패하는 테스트 추가** — `tests/test_offers.py` import에 `conversation_split, offer_first_sent, offer_group` 추가, 끝에

```python
def test_offer_first_sent_takes_earliest_send():
    ev = pd.DataFrame({
        "concept:name": ["O_Sent (mail and online)", "O_Sent (online only)", "O_Created"],
        "OfferID": ["Offer_1", "Offer_1", "Offer_2"],
        "time:timestamp": pd.to_datetime(["2016-01-03", "2016-01-02", "2016-01-01"], utc=True),
    })
    assert offer_first_sent(ev).to_dict() == {"Offer_1": pd.Timestamp("2016-01-02", tz="UTC")}


def test_conversation_split_and_group():
    ts = lambda d: pd.Timestamp(d, tz="UTC")  # noqa: E731
    offers = pd.DataFrame({
        "case:concept:name": ["S", "M", "M", "L", "L"],
        "offer_id": ["o1", "o2", "o3", "o4", "o5"],
        "created_ts": [ts("2016-01-01"), ts("2016-01-01 10:00"), ts("2016-01-01 11:00"),
                       ts("2016-01-01"), ts("2016-01-05")],
    })
    first_sent = pd.Series({"o1": ts("2016-01-02"), "o2": ts("2016-01-02"), "o4": ts("2016-01-02")})
    split = conversation_split(offers, first_sent)
    assert split.loc["S", "n_offers"] == 1 and not split.loc["S", "d1_later"]
    assert not split.loc["M", "d1_later"] and not split.loc["M", "d2_later"]
    assert split.loc["L", "d1_later"] and split.loc["L", "d2_later"]
    assert offer_group(split, "d1_later").to_dict() == {"L": "multi_later", "M": "multi_same", "S": "single"}
```

`tests/test_efficiency.py` import에 `incremental_eta, stratified_diff` 추가, 끝에

```python
def test_stratified_diff_weights_by_stratum_size():
    frame = pd.DataFrame({
        "s": ["a"] * 8 + ["b"] * 4,
        "g": ["base"] * 4 + ["other"] * 4 + ["base"] * 2 + ["other"] * 2,
        "v": [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1],
    })
    diff, table = stratified_diff(frame, "g", "base", "other", "s", "v", min_n=2)
    assert list(table["diff"]) == [0.25, 0.5]
    assert round(diff, 6) == round((0.25 * 8 + 0.5 * 4) / 12, 6)


def test_incremental_eta_and_class():
    frame = pd.DataFrame({
        "s": ["x"] * 4,
        "g": ["base", "base", "other", "other"],
        "reached_pending": [True, True, True, True],
        "r": [100.0, 100.0, 150.0, 150.0],
        "e": [1.0, 1.0, 2.0, 2.0],
    })
    inc = incremental_eta(frame, "g", "base", "other", "s", "r", "e", min_n=2)
    assert inc.loc["x", "eta_base"] == 100.0
    assert inc.loc["x", "incremental_eta"] == 50.0
    assert inc.loc["x", "class"] == "공수↑·가치↑"


def test_incremental_eta_flags_reversal():
    frame = pd.DataFrame({
        "s": ["x"] * 4, "g": ["base", "base", "other", "other"],
        "reached_pending": [True, True, True, False],
        "r": [100.0, 100.0, 100.0, np.nan], "e": [1.0, 1.0, 2.0, 2.0],
    })
    assert incremental_eta(frame, "g", "base", "other", "s", "r", "e", min_n=2).loc["x", "class"] == "공수↑·가치↓"
```

- [ ] **Step 2: 실패 확인** — Run: `.venv\Scripts\python -m pytest tests/test_offers.py tests/test_efficiency.py -q` / Expected: ImportError

- [ ] **Step 3: `analysis/offers.py`에 추가**

```python
SENT_ACTIVITIES = ("O_Sent (mail and online)", "O_Sent (online only)")


def offer_first_sent(events: pd.DataFrame) -> pd.Series:
    sent = events[events[ACT].isin(SENT_ACTIVITIES)]
    return sent.groupby(OFFER_ID)[TS].min().rename("first_sent")


def conversation_split(offers: pd.DataFrame, first_sent: pd.Series, same_day: float = 1.0) -> pd.DataFrame:
    """Per case: offer count and whether extra offers came in a later conversation.

    d1_later: offers created more than `same_day` days apart.
    d2_later: an offer was created after the case's first offer had been sent.
    """
    o = offers.assign(first_sent=offers["offer_id"].map(first_sent))
    g = o.groupby(CASE)
    out = pd.DataFrame({
        "n_offers": g.size(),
        "span_days": (g["created_ts"].max() - g["created_ts"].min()).dt.total_seconds() / 86400,
        "first_sent": g["first_sent"].min(),
        "last_created": g["created_ts"].max(),
    })
    multi = out["n_offers"] >= 2
    out["d1_later"] = multi & (out["span_days"] > same_day)
    out["d2_later"] = multi & (out["last_created"] > out["first_sent"])
    return out.drop(columns=["first_sent", "last_created"])


def offer_group(split: pd.DataFrame, later_col: str) -> pd.Series:
    multi = split["n_offers"] >= 2
    label = pd.Series("single", index=split.index)
    return label.mask(multi & ~split[later_col], "multi_same").mask(split[later_col], "multi_later")
```

- [ ] **Step 4: `analysis/efficiency.py`에 추가**

```python
INCREMENT_CLASSES = ["공수↑·가치↑", "공수↑·가치↓", "공수↓·가치↑"]


def stratified_diff(frame: pd.DataFrame, group_col: str, base: str, other: str, strata: str,
                    value_col: str, min_n: int = 50) -> tuple[float, pd.DataFrame]:
    """Mean difference (other − base) within strata where both groups have ≥ min_n, and its
    average weighted by the stratum's combined size."""
    sub = frame[frame[group_col].isin([base, other])]
    t = sub.groupby([strata, group_col], observed=True)[value_col].agg(["mean", "size"]).unstack(group_col)
    out = pd.DataFrame({
        "n_base": t[("size", base)], "n_other": t[("size", other)],
        "mean_base": t[("mean", base)], "mean_other": t[("mean", other)],
    })
    out = out[(out["n_base"] >= min_n) & (out["n_other"] >= min_n)]
    out["diff"] = out["mean_other"] - out["mean_base"]
    weight = out["n_base"] + out["n_other"]
    return float((out["diff"] * weight).sum() / weight.sum()), out


def _expected_value(x: pd.DataFrame, r_col: str, success_col: str) -> float:
    return x.loc[x[success_col], r_col].mean() * x[success_col].mean()


def incremental_eta(frame: pd.DataFrame, group_col: str, base: str, other: str, strata: str,
                    r_col: str, e_col: str, success_col: str = "reached_pending",
                    min_n: int = 50) -> pd.DataFrame:
    """Per stratum: extra expected loan volume per extra effort hour of `other` over `base`,
    Δ(R̄·p)/ΔĒ, next to the base group's own η."""
    rows = {}
    for key, s in frame.groupby(strata, observed=True):
        a, b = s[s[group_col] == base], s[s[group_col] == other]
        if len(a) < min_n or len(b) < min_n:
            continue
        va, vb = _expected_value(a, r_col, success_col), _expected_value(b, r_col, success_col)
        ea, eb = a[e_col].mean(), b[e_col].mean()
        rows[key] = {
            "n_base": len(a), "n_other": len(b),
            "p_base": a[success_col].mean(), "p_other": b[success_col].mean(),
            "value_base": va, "value_other": vb, "e_base": ea, "e_other": eb,
            "eta_base": va / ea, "delta_value": vb - va, "delta_effort": eb - ea,
            "incremental_eta": (vb - va) / (eb - ea) if eb != ea else np.nan,
        }
    out = pd.DataFrame.from_dict(rows, orient="index")
    if out.empty:
        return out
    more, gain = out["delta_effort"] > 0, out["delta_value"] > 0
    out["class"] = np.select([more & gain, more & ~gain, ~more & gain], INCREMENT_CLASSES, default="공수↓·가치↓")
    return out
```

- [ ] **Step 5: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests -q` / Expected: 52 passed (기존 47 + 5)

- [ ] **Step 6: 커밋**

```powershell
git add analysis/offers.py analysis/efficiency.py tests/test_offers.py tests/test_efficiency.py; git commit -m "feat: add offer conversation split and incremental efficiency"
```

---

### Task 2: 오퍼 그룹과 층화 전 비교

**Files:**
- Create: `analysis/15_multi_offer_groups.py`

**Interfaces:**
- Produces: `outputs/p6_case_offer_groups.parquet` — index 케이스, 컬럼 `n_offers, span_days, d1_later, d2_later, group_d1_later, group_d2_later` → Task 3 입력. `p6_definition_crosstab.csv`, `p6_group_summary.csv`

- [ ] **Step 1: `analysis/15_multi_offer_groups.py` 작성**

```python
"""Phase 6 — multi-offer applications: how many, same or later conversation, and how they
compare with single-offer applications before any stratification.

Run from the project root:

    .venv\\Scripts\\python analysis/15_multi_offer_groups.py
"""
from __future__ import annotations

import pandas as pd

from config import CASE, OUT_DIR
from loader import load_analysis_frame, load_population
from offers import conversation_split, offer_first_sent, offer_group
from value import group_eta

MIN_N = 300
DEFINITIONS = {"d1_later": "created more than 1 day apart", "d2_later": "created after the first offer was sent"}


def main() -> None:
    ev, oc = load_population()
    offers = pd.read_parquet(OUT_DIR / "p0_offers.parquet")
    split = conversation_split(offers[offers[CASE].isin(oc.index)], offer_first_sent(ev))
    for d in DEFINITIONS:
        split[f"group_{d}"] = offer_group(split, d)
    split.to_parquet(OUT_DIR / "p6_case_offer_groups.parquet")
    print(f"offers per case: {split['n_offers'].value_counts().sort_index().to_dict()}")

    multi = split[split["n_offers"] >= 2]
    cross = pd.crosstab(multi["d1_later"], multi["d2_later"])
    cross.to_csv(OUT_DIR / "p6_definition_crosstab.csv", encoding="utf-8-sig")
    print(f"\n=== later conversation among {len(multi):,} multi-offer cases (rows D1, columns D2) ===\n"
          f"{cross.to_string()}")
    print(f"days between first and last offer (multi): "
          f"{multi['span_days'].describe(percentiles=[0.25, 0.5, 0.75, 0.9]).round(2).to_dict()}")

    frame = load_analysis_frame(MIN_N).join(split)
    tables = []
    for d, desc in DEFINITIONS.items():
        t = group_eta(frame, f"group_{d}", "r_amount", "effort_hours")
        t = t.join(pd.crosstab(frame[f"group_{d}"], frame["outcome"], normalize="index").add_prefix("share_"))
        tables.append(t.reset_index(names="group").assign(definition=d, description=desc))
    summary = pd.concat(tables, ignore_index=True).round(4)
    summary.to_csv(OUT_DIR / "p6_group_summary.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== single vs multi (same / later conversation), before stratification ===\n"
          f"{summary.to_string(index=False)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/15_multi_offer_groups.py`
기록 대상: 두 정의의 교차표, 그룹별 n·성사율·Ē·η·결과 구성(층화 전)

- [ ] **Step 3: 커밋**

```powershell
git add analysis/15_multi_offer_groups.py outputs/p6_case_offer_groups.parquet outputs/p6_definition_crosstab.csv outputs/p6_group_summary.csv; git commit -m "feat: split multi-offer cases by conversation timing"
```

---

### Task 3: 층화 차이와 증분 효율

**Files:**
- Create: `analysis/16_multi_offer_increment.py`

**Interfaces:**
- Consumes: `p4_segments.parquet`, `p6_case_offer_groups.parquet`, `p5_segment_efficiency.csv`(η 최솟값), `stratified_diff`, `incremental_eta`
- Produces: `p6_stratified_diff.csv`, `p6_increment_by_amount.csv`, `p6_increment_by_segment.csv`

- [ ] **Step 1: `analysis/16_multi_offer_increment.py` 작성**

```python
"""Phase 6 — does the multi-offer advantage survive stratification, and what does the extra effort buy?

Observed associations only: a later offer needs a customer who is still engaged, so the
later-conversation difference is an upper bound, not an effect (P3).

Run from the project root, after 15_multi_offer_groups.py:

    .venv\\Scripts\\python analysis/16_multi_offer_increment.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from efficiency import incremental_eta, stratified_diff
from loader import load_analysis_frame

MIN_N = 300
MIN_GROUP_N = 50
REFERENCE_COST = 57.6  # EUR/hour — docs/03_method.md 3장
COMPARISONS = [("group_any", "multi"), ("group_d1_later", "multi_same"), ("group_d1_later", "multi_later"),
               ("group_d2_later", "multi_same"), ("group_d2_later", "multi_later")]


def main() -> None:
    frame = load_analysis_frame(MIN_N).join(pd.read_parquet(OUT_DIR / "p4_segments.parquet"))
    frame = frame.join(pd.read_parquet(OUT_DIR / "p6_case_offer_groups.parquet"))
    sizes = frame["segment"].value_counts()
    frame = frame[frame["segment"].isin(sizes.index[sizes >= MIN_N])].copy()
    frame["group_any"] = frame["n_offers"].ge(2).map({True: "multi", False: "single"})
    eta_floor = pd.read_csv(OUT_DIR / "p5_segment_efficiency.csv")["eta"].min()
    print(f"cases={len(frame):,}  segment η floor (Phase 5)={eta_floor:,.0f}")

    rows = []
    for col, other in COMPARISONS:
        sub = frame[frame[col].isin(["single", other])]
        for metric in ("reached_pending", "effort_hours"):
            crude = sub.loc[sub[col] == other, metric].mean() - sub.loc[sub[col] == "single", metric].mean()
            strat, used = stratified_diff(frame, col, "single", other, "segment", metric, MIN_GROUP_N)
            rows.append({"grouping": col, "comparison": f"{other} - single", "metric": metric,
                         "crude_diff": crude, "stratified_diff": strat, "strata_used": len(used)})
    diffs = pd.DataFrame(rows).round(4)
    diffs.to_csv(OUT_DIR / "p6_stratified_diff.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== differences vs single-offer, crude and stratified by segment ===\n{diffs.to_string(index=False)}")

    tables = []
    for col, other in COMPARISONS:
        inc = incremental_eta(frame, col, "single", other, "amount_band", "r_amount", "effort_hours",
                              min_n=MIN_GROUP_N)
        inc_i = incremental_eta(frame, col, "single", other, "amount_band", "interest_total", "effort_hours",
                                min_n=MIN_GROUP_N)
        inc["incremental_eta_I"] = inc_i["incremental_eta"]
        gaining = inc["class"] == "공수↑·가치↑"
        inc["incremental_min_margin_share"] = (REFERENCE_COST / inc["incremental_eta_I"]).where(gaining)
        inc["below_segment_eta_floor"] = gaining & (inc["incremental_eta"] < eta_floor)
        tables.append(inc.reset_index(names="amount_band").assign(grouping=col, comparison=f"{other} - single"))
    by_amount = pd.concat(tables, ignore_index=True).round(4)
    by_amount.to_csv(OUT_DIR / "p6_increment_by_amount.csv", index=False, encoding="utf-8-sig")
    cols = ["comparison", "grouping", "amount_band", "n_base", "n_other", "p_base", "p_other",
            "e_base", "e_other", "eta_base", "incremental_eta", "class",
            "incremental_min_margin_share", "below_segment_eta_floor"]
    print(f"\n=== incremental efficiency by amount band ===\n{by_amount[cols].to_string(index=False)}")

    by_segment = incremental_eta(frame, "group_any", "single", "multi", "segment", "r_amount", "effort_hours",
                                 min_n=MIN_GROUP_N)
    by_segment["below_segment_eta_floor"] = (by_segment["class"] == "공수↑·가치↑") & (
        by_segment["incremental_eta"] < eta_floor)
    by_segment.round(4).to_csv(OUT_DIR / "p6_increment_by_segment.csv", encoding="utf-8-sig")
    print(f"\nsegments with both groups >= {MIN_GROUP_N}: {len(by_segment)}")
    print(f"class counts (multi vs single, by segment): {by_segment['class'].value_counts().to_dict()}")
    print(f"gaining but below the segment η floor: {int(by_segment['below_segment_eta_floor'].sum())}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/16_multi_offer_increment.py`
기록 대상: 층화 Δ성사율·Δ공수(**판단 1·2**), 금액 구간별 증분 분류와 증분 η(**판단 3·4**), 세그먼트별 분류 집계, 사용한 층의 수(**판단 5**)

- [ ] **Step 3: 커밋**

```powershell
git add analysis/16_multi_offer_increment.py outputs/p6_stratified_diff.csv outputs/p6_increment_by_amount.csv outputs/p6_increment_by_segment.csv; git commit -m "feat: stratify multi-offer differences and measure incremental efficiency"
```

---

### Task 4: Phase 6 결론 문서와 CLAUDE.md 반영

**Files:**
- Create: `docs/06_multi_offer.md`
- Modify: `CLAUDE.md` (3장 대화 구분 불일치 해소, 6장 진행 현황표·Phase 6 절·Phase 9 절, 7장 시나리오 1, 12장), 이 파일의 진행 기록

- [ ] **Step 1: `docs/06_multi_offer.md` 작성** — 모든 수치 옆에 `outputs/p6_*` 출처

```markdown
# Phase 6 — 복수 오퍼 역전점
## 요약
## 1. 상담 구분 두 정의와 선행 보고서의 불일치 (p6_definition_crosstab.csv, p6_group_summary.csv)
## 2. 층화 후에도 우위가 남는가 (p6_stratified_diff.csv)
## 3. 추가 공수가 사는 것 — 금액 구간별 증분 효율 (p6_increment_by_amount.csv)
## 4. 반전 시나리오 1 판정
## 5. 선택 편향과 서술의 한계 (상한 추정)
## 6. 다음 Phase로 넘기는 것 (Phase 9 요구사항 2 — 오퍼 규칙 분기의 근거)
```

- [ ] **Step 2: CLAUDE.md 반영** — 3장의 보고서 간 불일치 해소 여부, 진행 현황표, Phase 6 절(판정별 결과), 7장 시나리오 1 상태, Phase 9 요구사항 2의 근거, 12장
- [ ] **Step 3: 이 파일의 진행 기록에 실행 중 변경·결과 요약·커밋 추가**
- [ ] **Step 4: 사용자 보고** — Phase 7 진행계획 착수 여부 확인
- [ ] **Step 5: 커밋**

```powershell
git add docs/06_multi_offer.md docs/plans/phase-06-multi-offer.md CLAUDE.md; git commit -m "docs: record phase 6 multi-offer results"
```

---

## 진행 기록

| 날짜 | 내용 |
|---|---|
| 2026-09-11 | 진행계획 작성. 사전 탐색(복수 오퍼 우위가 전부 나중 상담에서 나오고 같은 상담 복수는 단일보다 성사율이 낮음)을 설계에 반영해 상담 구분 2정의와 증분 분류를 핵심으로 둠. 판정 규칙 고정. 사용자 확인 대기 |
| 2026-09-11 | 사용자 승인, 이 대화에서 직접 실행. 계획대로 진행했고 실행 중 코드 변경 없음 |
| 2026-09-11 | 실행 완료 — 결론은 [`docs/06_multi_offer.md`](../06_multi_offer.md). CLAUDE.md 3장(보고서 불일치 정리), 7장(시나리오 1 기각), Phase 9 요구사항 2 근거 갱신 |

**결과 요약 (판정 규칙별):**
1. 복수 전체 층화 Δ성사율 +6.62%p → 우위 유지
2. 같은 상담 복수 −2.64%p(D1) / −5.49%p(D2), 나중 상담 복수 +13.31%p / +11.71%p → 정의에 강건 (metafinanz 방향)
3. 복수 전체는 6개 구간 모두 공수↑·가치↑지만, 5개 구간에서 증분 η < 그 구간 단일 η. 같은 상담 복수는 D2 기준 6개 구간 모두 가치↓
4. 반전 시나리오 1 기각 (소액 구간 증분 η 6,704 > 4,374). 약한 증분: 0(미기재) 3,485(필요 순마진 비중 71.7%), 15,500\~25,000 4,011
5. 세그먼트 35개 사용: 공수↑·가치↑ 33, 공수↓·가치↑ 2, 증분 η가 세그먼트 최솟값 미만 5

**커밋:**
- `a52676f` docs: add phase 6 multi-offer plan
- `08e074f` feat: add offer conversation split and incremental efficiency
- `08ef911` feat: split multi-offer cases by conversation timing
- (Task 3) feat: stratify multi-offer differences and measure incremental efficiency
- (이 기록과 결론 문서) docs: record phase 6 multi-offer results

## 사후 교정 (2026-09-12)

**틀린 출처 표시를 바로잡았다.** 위 설계표는 D1(오퍼 생성 간격 1일 초과)을 "KPMG의 '1일 이상 떨어진 대화' 정의"라고 적었다.
미결 문헌 항목을 정리하며 KPMG 원문(winner professional, p.11)을 직접 확인한 결과, KPMG의 기준은 **8시간**이었다 —
"When offers for the same application are created less than 8 hours apart from each other, we consider them to be requested
during 1 conversation." 1일 기준은 이 프로젝트가 선택한 값이다.

**결론에는 영향이 없다.** `conversation_split(same_day=...)`의 임계를 8시간으로 바꿔 다시 계산했다
(`analysis/15_multi_offer_groups.py` → `outputs/p6_threshold_sensitivity.csv`).

| 기준 | 나중 상담 n | 나중 상담 성사율 | 같은 상담 성사율 | 단일 성사율 | 나중 상담 η | 같은 상담 η |
|---|---|---|---|---|---|---|
| 1일 | 4,553 | 0.668 | 0.483 | 0.534 | 15,948 | 15,156 |
| 8시간 | 4,719 | 0.667 | 0.475 | 0.534 | 16,039 | 14,915 |

166건이 옮겨갈 뿐 세 그룹의 순서(나중 상담 > 단일 > 같은 상담)와 격차는 유지된다. 임계 파라미터가 판정을 실제로 바꾸는지는
`tests/test_offers.py::test_conversation_split_threshold_moves_borderline_cases`로 검증한다.

**같은 회차에 확인한 KPMG 수치:** 대화 구분별 성사율은 단일 대화 65.34% / 다회 대화 81.75%(p.11), 오퍼 건수별로는
1건 69.09% / 2건 이상 73.24%(p.12)다. 절대값은 이 프로젝트의 성사 정의와 달라 인용하지 않고, **방향만** 근거로 쓴다.
