# Phase 4 — 세그먼트 정의 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 접수 시점 변수로 만든 축이 성사율·공수·η를 실제로 가르는지 먼저 선별한다. 살아남은 축만 교차해서, 각 셀이 최소 크기를 넘는 세그먼트를 정의한다. 평탄한 축은 기각하고, 기각 자체를 결과로 기록한다.

**Architecture:** 축 파생(접수 경로, 용도 그룹), 계층형 교차(`build_segments`), 축 판정(`screen_axis`)은 `analysis/segments.py`에 둔다. η의 부트스트랩 신뢰구간은 `analysis/value.py`에 둔다. 케이스 단위 분석 프레임은 `loader.load_analysis_frame()` 하나로 만든다. 스크립트 `11`은 축을 선별하고, `12`는 세그먼트를 만든다.

**Tech Stack:** Python 3.12, pandas 3.0.5, numpy, pytest (Windows PowerShell 5.1)

**Spec:** `CLAUDE.md` 5장 P2, 6장 Phase 4 / `docs/03_method.md` 6장·7장

## Global Constraints

- 모집단은 29,131건이고, 축은 **접수 시점 변수만** 쓴다 (P2): 신청 금액, 대출 용도, 신청 유형, A_Submitted 유무.
- 결과 누수 속성과 처리 중 변수(오퍼 건수 등)는 축으로 쓰지 않는다.
- 판정의 주 조합은 R = `r_amount`, E = `effort_hours`다. `r_amount_years`와 `staff_events`는 민감도용으로 함께 보고한다 (Phase 2·3 결정).
- 최소 셀 크기 `MIN_N = 300`건.
- 부트스트랩: 그룹 안 케이스 복원추출 200회, 90% 구간(5~95백분위), 시드 0.
- 스크립트 번호 `11~12`, 산출 파일 접두어 `p4_`. 차트는 만들지 않는다.
- PowerShell 5.1: `&&` 대신 `;`. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## 축 설계

| 축 | 원천 | 수준 | 처리 |
|---|---|---|---|
| `amount_band` 신청 금액 구간 | RequestedAmount | 6 | 양수 금액 5분위 + "0 (미기재)" (Phase 0·3) |
| `channel` 접수 경로 | ApplicationType × A_Submitted | 3 | 한도 증액 / 신규·A_Submitted / 신규·표식 없음. 한도 증액에는 표식이 없으므로 두 변수를 한 축으로 합쳐 구조적 중첩을 없앤다 (Phase 1) |
| `goal_group` 용도 그룹 | LoanGoal | 규칙에 따름 | "Other, see explanation"·"Unknown"·"Not speficied" → "용도 불명". 그 뒤에도 300건 미만인 용도 → "기타 소수 용도" (Phase 0·3) |

## 판정 규칙 (착수 전 고정)

- **축 유지:** n ≥ 300인 그룹 중 η 최고/최저 비율이 **1.25배 이상**이고, 최고 그룹의 90% 구간 하한이 최저 그룹의 상한보다 **높아야** 한다. 둘 다 충족하면 유지하고, 아니면 기각한다.
- **교차 순서:** 유지된 축을 η 비율이 큰 순서로 교차한다.
- **계층형 최소 셀:** 한 단계 더 쪼갠 셀이 300건 이상이면 쪼갠다. 300건에 못 미치는 형제 셀들은 "상위 셀 | 기타"로 묶는다. 이 나머지 묶음이 300건 미만이면 `small`로 표시하고, Phase 5 순위에서 빼고 따로 보고한다.

## File Structure

| 파일 | 책임 |
|---|---|
| `analysis/segments.py` | `channel`, `goal_group`, `build_segments`, `screen_axis` 추가 |
| `analysis/value.py` | `bootstrap_eta` 추가 |
| `analysis/loader.py` | `load_analysis_frame` 추가 — 케이스 단위 축·결과·공수·R |
| `analysis/11_axis_screening.py` | 축별 그룹 표, 신뢰구간, 격차, 유지 판정 |
| `analysis/12_segments.py` | 유지 축 교차, 세그먼트 표(η 4조합, η_I, 신뢰구간) |
| `tests/test_segments.py`, `tests/test_value.py` | 단위 테스트 5개 추가 |
| `docs/04_segments.md` | Phase 4 결론 문서 |

---

### Task 1: 축 파생·교차·판정·신뢰구간 함수

**Files:**
- Modify: `analysis/segments.py`, `analysis/value.py`, `tests/test_segments.py`, `tests/test_value.py`

**Interfaces:**
- Produces (segments.py):
  - `channel(frame) -> pd.Series` — `case:ApplicationType`, `has_submitted`로 3수준 라벨
  - `goal_group(goal: pd.Series, min_n: int) -> pd.Series`
  - `build_segments(frame, axes: list[str], min_n: int) -> pd.Series` — `"수준 | 수준"` 라벨, 나머지 묶음은 `"... | 기타"`
  - `screen_axis(table, min_n, min_ratio) -> dict` — table은 `group_eta` 결과에 `eta_lo, eta_hi`를 붙인 것. 키 `groups_n_ge_min, p_range, e_ratio, eta_ratio, ci_separated, retained`
- Produces (value.py):
  - `bootstrap_eta(frame, by, r_col, e_col, success_col="reached_pending", n_boot=200, seed=0) -> pd.DataFrame` — index 그룹, 컬럼 `eta_lo, eta_hi`

- [ ] **Step 1: 실패하는 테스트 추가** — `tests/test_segments.py`: import를 `from segments import amount_band, build_segments, channel, goal_group, intake_frame, screen_axis`로 바꾸고 끝에 추가

```python
def test_channel_combines_type_and_submitted():
    frame = pd.DataFrame({"case:ApplicationType": ["Limit raise", "New credit", "New credit"],
                          "has_submitted": [False, True, False]}, index=list("abc"))
    assert channel(frame).to_dict() == {"a": "한도 증액", "b": "신규·A_Submitted", "c": "신규·표식 없음"}


def test_goal_group_merges_uninformative_and_small():
    goal = pd.Series(["Car"] * 4 + ["Unknown", "Not speficied", "Other, see explanation", "Boat"])
    out = goal_group(goal, min_n=2)
    assert list(out) == ["Car"] * 4 + ["용도 불명"] * 3 + ["기타 소수 용도"]


def test_build_segments_falls_back_for_small_cells():
    frame = pd.DataFrame({
        "a": ["x"] * 6 + ["y"] * 5 + ["z"],
        "b": ["p", "p", "p", "q", "q", "q", "p", "p", "p", "p", "q", "p"],
    })
    seg = build_segments(frame, ["a", "b"], min_n=3)
    assert list(seg) == ["x | p"] * 3 + ["x | q"] * 3 + ["y | p"] * 4 + ["y | 기타", "기타"]


def test_screen_axis_requires_ratio_and_ci_separation():
    table = pd.DataFrame({"n": [500, 400, 10], "p": [0.6, 0.4, 0.9], "e_mean": [1.0, 0.8, 2.0],
                          "eta": [20.0, 10.0, 99.0], "eta_lo": [18.0, 9.0, 1.0],
                          "eta_hi": [22.0, 11.0, 200.0]}, index=["a", "b", "c"])
    res = screen_axis(table, min_n=300, min_ratio=1.25)
    assert res["groups_n_ge_min"] == 2 and res["eta_ratio"] == 2.0 and res["retained"]
    table.loc["a", "eta_lo"] = 10.5
    assert not screen_axis(table, min_n=300, min_ratio=1.25)["retained"]
```

`tests/test_value.py`: import에 `bootstrap_eta` 추가, 끝에

```python
def test_bootstrap_eta_constant_group_has_degenerate_interval():
    frame = pd.DataFrame({"g": ["x"] * 5, "reached_pending": [True] * 5,
                          "r": [10.0] * 5, "e": [2.0] * 5})
    ci = bootstrap_eta(frame, "g", "r", "e", n_boot=20)
    assert ci.loc["x", "eta_lo"] == 5.0 and ci.loc["x", "eta_hi"] == 5.0
```

- [ ] **Step 2: 실패 확인** — Run: `.venv\Scripts\python -m pytest tests/test_segments.py tests/test_value.py -q` / Expected: ImportError (`channel`, `bootstrap_eta`)

- [ ] **Step 3: `analysis/segments.py`에 추가** (import에 `from value import group_eta` 불필요 — screen_axis는 표만 받는다)

```python
CHANNEL_LABELS = {
    ("Limit raise", False): "한도 증액",
    ("New credit", True): "신규·A_Submitted",
    ("New credit", False): "신규·표식 없음",
}
UNINFORMATIVE_GOALS = ("Other, see explanation", "Unknown", "Not speficied")


def channel(frame: pd.DataFrame) -> pd.Series:
    """Application type and the A_Submitted marker as one intake axis (the marker exists only for new credit)."""
    keys = zip(frame["case:ApplicationType"], frame["has_submitted"].astype(bool))
    return pd.Series([CHANNEL_LABELS.get(k, "기타") for k in keys], index=frame.index)


def goal_group(goal: pd.Series, min_n: int) -> pd.Series:
    out = goal.where(~goal.isin(UNINFORMATIVE_GOALS), "용도 불명")
    counts = out.value_counts()
    return out.where(~out.isin(counts.index[counts < min_n]), "기타 소수 용도")


def build_segments(frame: pd.DataFrame, axes: list[str], min_n: int) -> pd.Series:
    """Cross axes in order. A cell is split further only where the child has at least min_n cases;
    children below min_n are pooled as "<parent> | 기타" (which may itself stay below min_n)."""
    label = pd.Series("전체", index=frame.index, dtype="object")
    active = pd.Series(True, index=frame.index)
    for axis in axes:
        candidate = label + " | " + frame[axis].astype(str)
        size = candidate.map(candidate[active].value_counts())
        deeper = active & (size >= min_n)
        remainder = active & ~deeper & label.isin(set(label[deeper]))
        label = label.mask(deeper, candidate).mask(remainder, label + " | 기타")
        active = deeper
    return label.str.removeprefix("전체 | ")


def screen_axis(table: pd.DataFrame, min_n: int, min_ratio: float) -> dict:
    """Keep an axis only if η differs enough across groups (n ≥ min_n) and the extremes' intervals separate."""
    big = table[table["n"] >= min_n]
    top, bottom = big["eta"].idxmax(), big["eta"].idxmin()
    eta_ratio = float(big["eta"].max() / big["eta"].min())
    separated = bool(big.loc[top, "eta_lo"] > big.loc[bottom, "eta_hi"])
    return {
        "groups_n_ge_min": len(big),
        "p_range": float(big["p"].max() - big["p"].min()),
        "e_ratio": float(big["e_mean"].max() / big["e_mean"].min()),
        "eta_ratio": eta_ratio,
        "ci_separated": separated,
        "retained": eta_ratio >= min_ratio and separated,
    }
```

- [ ] **Step 4: `analysis/value.py`에 추가**

```python
def bootstrap_eta(frame: pd.DataFrame, by: str, r_col: str, e_col: str,
                  success_col: str = "reached_pending", n_boot: int = 200, seed: int = 0) -> pd.DataFrame:
    """90% bootstrap interval of η per group, resampling cases within the group."""
    rng = np.random.default_rng(seed)
    rows = {}
    for key, g in frame.groupby(by, observed=True):
        success = g[success_col].to_numpy(bool)
        r, e = g[r_col].to_numpy(float), g[e_col].to_numpy(float)
        idx = rng.integers(0, len(g), size=(n_boot, len(g)))
        s = success[idx]
        n_success = s.sum(axis=1)
        r_sum = np.where(s, r[idx], 0.0).sum(axis=1)
        r_mean = np.divide(r_sum, n_success, out=np.full(n_boot, np.nan), where=n_success > 0)
        eta = r_mean * (n_success / len(g)) / e[idx].mean(axis=1)
        rows[key] = {"eta_lo": np.nanquantile(eta, 0.05), "eta_hi": np.nanquantile(eta, 0.95)}
    return pd.DataFrame.from_dict(rows, orient="index")
```

- [ ] **Step 5: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests -q` / Expected: 40 passed (기존 35 + 5)

- [ ] **Step 6: 커밋**

```powershell
git add analysis/segments.py analysis/value.py tests/test_segments.py tests/test_value.py; git commit -m "feat: add segment axes, hierarchical crossing and eta bootstrap"
```

---

### Task 2: 분석 프레임과 축 선별

**Files:**
- Modify: `analysis/loader.py`
- Create: `analysis/11_axis_screening.py`

**Interfaces:**
- Produces: `load_analysis_frame(min_goal_n: int) -> pd.DataFrame` — index 모집단 케이스, 컬럼 `case:RequestedAmount, case:LoanGoal, case:ApplicationType, has_submitted, amount_band, channel, goal_group, outcome, reached_pending, effort_hours, staff_events, r_amount, r_amount_years, interest_total`
- Produces: `outputs/p4_axis_groups.csv`, `outputs/p4_axis_spread.csv`(Task 3 입력: `axis, retained, eta_ratio, ...`)

- [ ] **Step 1: `analysis/loader.py`에 추가** — import에 `OUT_DIR` 추가, 파일 상단에 `from segments import amount_band, channel, goal_group, intake_frame`

```python
def load_analysis_frame(min_goal_n: int) -> pd.DataFrame:
    """Case-level frame for segment analysis: intake axes, outcome, effort and revenue bases."""
    ev, oc = load_population()
    frame = intake_frame(ev).reindex(oc.index)
    frame["amount_band"] = amount_band(frame["case:RequestedAmount"])
    frame["channel"] = channel(frame)
    frame["goal_group"] = goal_group(frame["case:LoanGoal"], min_goal_n)
    frame["outcome"] = oc["outcome"]
    frame["reached_pending"] = oc["reached_pending"]
    effort = pd.read_parquet(OUT_DIR / "p2_case_effort.parquet")[["effort_hours", "staff_events"]]
    revenue = pd.read_parquet(OUT_DIR / "p3_accepted_offers.parquet")[
        ["r_amount", "r_amount_years", "interest_total"]]
    return frame.join(effort).join(revenue)
```

- [ ] **Step 2: `analysis/11_axis_screening.py` 작성**

```python
"""Phase 4 — does each intake axis actually separate success rate, effort and η?

Run from the project root:

    .venv\\Scripts\\python analysis/11_axis_screening.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_analysis_frame
from segments import screen_axis
from value import bootstrap_eta, group_eta

AXES = ["amount_band", "channel", "goal_group"]
MIN_N = 300
MIN_ETA_RATIO = 1.25
ALTERNATIVES = [("r_amount_years", "effort_hours"), ("r_amount", "staff_events")]


def main() -> None:
    frame = load_analysis_frame(MIN_N)
    print(f"cases={len(frame):,}")
    print(f"channel: {frame['channel'].value_counts().to_dict()}")
    print(f"goal_group: {frame['goal_group'].value_counts().to_dict()}")

    tables, spreads = [], []
    for axis in AXES:
        table = group_eta(frame, axis, "r_amount", "effort_hours").join(
            bootstrap_eta(frame, axis, "r_amount", "effort_hours"))
        row = {"axis": axis, **screen_axis(table, MIN_N, MIN_ETA_RATIO)}
        for r_col, e_col in ALTERNATIVES:
            alt = group_eta(frame, axis, r_col, e_col)
            table[f"eta_{r_col}_{e_col}"] = alt["eta"]
            big = alt[alt["n"] >= MIN_N]
            row[f"eta_ratio_{r_col}_{e_col}"] = float(big["eta"].max() / big["eta"].min())
        spreads.append(row)
        tables.append(table.reset_index(names="group").assign(axis=axis))

    groups = pd.concat(tables, ignore_index=True).round(4)
    groups.to_csv(OUT_DIR / "p4_axis_groups.csv", index=False, encoding="utf-8-sig")
    spread = pd.DataFrame(spreads).round(4)
    spread.to_csv(OUT_DIR / "p4_axis_spread.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== groups by axis (R = r_amount, E = effort_hours) ===\n{groups.to_string(index=False)}")
    print(f"\n=== axis screening (eta ratio >= {MIN_ETA_RATIO} and 90% CI separated) ===\n{spread.to_string(index=False)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: 실데이터 실행** — Run: `.venv\Scripts\python analysis/11_axis_screening.py`
기록 대상: 접수 경로·용도 그룹의 구성, 축별 p 범위·E 비율·η 비율·구간 분리·유지 여부(**판단 지점 1**), 대안 R/E에서 η 비율(**판단 지점 5**)

- [ ] **Step 4: 커밋**

```powershell
git add analysis/loader.py analysis/11_axis_screening.py outputs/p4_axis_groups.csv outputs/p4_axis_spread.csv; git commit -m "feat: screen intake axes for eta separation"
```

---

### Task 3: 세그먼트 교차

**Files:**
- Create: `analysis/12_segments.py`

**Interfaces:**
- Consumes: `outputs/p4_axis_spread.csv`, `load_analysis_frame`, `build_segments`, `group_eta`, `bootstrap_eta`
- Produces: `outputs/p4_segments.parquet` — index 케이스, 컬럼 `segment` → **Phase 5·6·7의 세그먼트 입력**. `outputs/p4_segment_table.csv` — 세그먼트별 n, p, R̄, Ē, η(주 조합) + 90% 구간 + η 대안 3조합 + η_I + `small`

- [ ] **Step 1: `analysis/12_segments.py` 작성**

```python
"""Phase 4 — cross the retained axes into segments of at least MIN_N applications.

Run from the project root, after 11_axis_screening.py:

    .venv\\Scripts\\python analysis/12_segments.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_analysis_frame
from segments import build_segments
from value import bootstrap_eta, group_eta

MIN_N = 300
ALTERNATIVES = [("r_amount_years", "effort_hours"), ("r_amount", "staff_events"),
                ("r_amount_years", "staff_events")]


def main() -> None:
    spread = pd.read_csv(OUT_DIR / "p4_axis_spread.csv")
    axes = spread.loc[spread["retained"]].sort_values("eta_ratio", ascending=False)["axis"].tolist()
    print(f"retained axes in crossing order: {axes or 'none'}")

    frame = load_analysis_frame(MIN_N)
    frame["segment"] = build_segments(frame, axes, MIN_N)
    frame[["segment"]].to_parquet(OUT_DIR / "p4_segments.parquet")

    table = group_eta(frame, "segment", "r_amount", "effort_hours").join(
        bootstrap_eta(frame, "segment", "r_amount", "effort_hours"))
    for r_col, e_col in ALTERNATIVES:
        table[f"eta_{r_col}_{e_col}"] = group_eta(frame, "segment", r_col, e_col)["eta"]
    table["eta_I"] = group_eta(frame, "segment", "interest_total", "effort_hours")["eta"]
    table["small"] = table["n"] < MIN_N
    table = table.sort_values("eta", ascending=False).round(4)
    table.to_csv(OUT_DIR / "p4_segment_table.csv", encoding="utf-8-sig")
    print(f"\n=== segments (sorted by η, R = r_amount, E = effort_hours) ===\n{table.to_string()}")
    print(f"\nsegments={len(table)}  small (< {MIN_N})={int(table['small'].sum())}  "
          f"cases in small segments={int(table.loc[table['small'], 'n'].sum()):,}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/12_segments.py`
기록 대상: 교차 순서, 세그먼트 수, small 세그먼트 수·케이스 수(**판단 지점 4**), η 최고/최저 세그먼트와 구간, η_I 범위

- [ ] **Step 3: 커밋**

```powershell
git add analysis/12_segments.py outputs/p4_segments.parquet outputs/p4_segment_table.csv; git commit -m "feat: cross retained axes into segments"
```

---

### Task 4: Phase 4 결론 문서와 CLAUDE.md 반영

**Files:**
- Create: `docs/04_segments.md`
- Modify: `CLAUDE.md` (6장 진행 현황표·Phase 4 절·Phase 5·6·7 절, 12장), 이 파일의 진행 기록

- [ ] **Step 1: `docs/04_segments.md` 작성** — 모든 수치 옆에 `outputs/p4_*` 출처

```markdown
# Phase 4 — 세그먼트 정의
## 1. 축 설계 (금액 구간 / 접수 경로 / 용도 그룹 — 파생 규칙)
## 2. 축 선별 — 격차와 신뢰구간 (p4_axis_spread.csv, p4_axis_groups.csv)
## 3. 기각된 축과 그 의미 (해당 시)
## 4. 세그먼트 교차 결과 (p4_segment_table.csv)
## 5. R·E 대안에서의 차이
## 6. 다음 Phase로 넘기는 것
```

- [ ] **Step 2: CLAUDE.md 반영** — 진행 현황표, Phase 4 절(판단 지점별 결과), Phase 5(세그먼트 입력), Phase 6(층화 변수 = 세그먼트), Phase 7, 12장
- [ ] **Step 3: 이 파일의 진행 기록에 실행 중 변경·결과 요약·커밋 추가**
- [ ] **Step 4: 사용자 보고** — Phase 5 진행계획 착수 여부 확인
- [ ] **Step 5: 커밋**

```powershell
git add docs/04_segments.md docs/plans/phase-04-segments.md CLAUDE.md; git commit -m "docs: record phase 4 segments"
```

---

## 판단 지점

1. **축 선별:** 축마다 η 비율 ≥ 1.25배이고 극단 그룹의 90% 구간이 분리되면 유지한다. 아니면 기각하고, 기각을 결과로 기록한다 (Amplitude 8/8 기각과 같은 처리)
2. **용도 처리:** 정보 없는 3종을 "용도 불명"으로 합친 뒤 300건 미만을 "기타 소수 용도"로 합친다. 합친 그룹이 η 극단에 오면 해석에 주의 표시를 한다
3. **접수 경로:** 신청 유형과 A_Submitted를 3수준 한 축으로 합친다
4. **최소 셀:** 300건 이상만 쪼갠다. 나머지 묶음이 300건 미만이면 `small`로 표시하고 Phase 5 순위에서 뺀다. small 세그먼트에 속한 케이스 수를 보고한다
5. **R·E 민감도:** 대안 조합에서 η 비율이 1.25배 아래로 떨어지는 축이 있으면 표시한다. 축의 유지 여부는 주 조합으로 판정한다

## 진행 기록

| 날짜 | 내용 |
|---|---|
| 2026-09-11 | 진행계획 작성. 판정 규칙(η 비율 1.25배 + 90% 구간 분리, 최소 셀 300, 계층형 교차)을 착수 전에 고정. 사용자 확인 대기 |
| 2026-09-11 | 사용자 승인, 이 대화에서 직접 실행. 계획대로 진행했고 실행 중 코드 변경 없음 |
| 2026-09-11 | 실행 완료 — 결론은 [`docs/04_segments.md`](../04_segments.md). 결과가 Phase 5 설계를 바꿈: 성사율 순위 vs η 순위 상관을 Phase 5 첫 과제로 추가 |

**결과 요약 (판단 지점별):**
1. 세 축 모두 유지 — η 비율 금액 5.84배, 경로 2.21배, 용도 1.50배, 모두 90% 구간 분리. 기각 없음
2. 최하위 세그먼트가 "용도 불명" 병합 그룹 → 주의 표시. 결론(소액 · 신규·A_Submitted 최하위)은 용도와 무관
3. 접수 경로 3수준 구성: 18,842 / 7,127 / 3,162
4. 세그먼트 44개, small 5개(888건) → Phase 5 순위 제외
5. 대안 R·E에서도 세 축 모두 1.25배 이상

**커밋:**
- `2d0d211` docs: add phase 4 segments plan
- `3e1faeb` feat: add segment axes, hierarchical crossing and eta bootstrap
- `59c867d` feat: screen intake axes for eta separation
- (Task 3) feat: cross retained axes into segments
- (이 기록과 결론 문서) docs: record phase 4 segments
