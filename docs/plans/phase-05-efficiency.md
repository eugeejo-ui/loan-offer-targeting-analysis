# Phase 5 — 효율 지표 산출 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 핵심 질문 "성사율이 높은 신청과 이익이 되는 신청은 같은가"에 두 가지로 답한다. ① 세그먼트 간 성사율 순위와 η 순위의 상관(부트스트랩 구간 포함) ② 같은 공수를 성사율 순서로 쓸 때와 η 순서로 쓸 때 확보되는 대출 규모의 차이. 여기에 c/m 스캔, 세그먼트별 필요 최소 순마진 비중, 계산기 입력 데이터를 더한다.

**Architecture:** 세그먼트 단위 계산은 새 모듈 `analysis/efficiency.py`에 두고 합성 데이터로 테스트한다. 스크립트 `13`은 순위 정합을 산출한다(케이스 재표집 부트스트랩 포함). `14`는 배분 비교, c/m 스캔, 필요 순마진 비중, 계산기 입력을 만든다.

**Tech Stack:** Python 3.12, pandas 3.0.5, numpy, pytest (Windows PowerShell 5.1)

**Spec:** `CLAUDE.md` §5 P1, §6 Phase 5 / `docs/03_method.md` §1·§3·§4 / `docs/04_segments.md` §3·§5

## Global Constraints

- 세그먼트는 `outputs/p4_segments.parquet`를 쓰고, **300건 이상 39개만** 쓴다(small 5개, 888건 제외).
- 주 조합은 R = `r_amount`, E = `effort_hours`다. 민감도 조합은 R 2종 × E 2종의 나머지 3개다 (Phase 2·3).
- 성사 = `reached_pending`. 결과 누수 속성은 쓰지 않는다.
- 인건비 c와 마진율 m은 추정하지 않는다. 참조 인건비 57.6유로/시간(Eurostat `lc_lci_lev`, NL, K, 2016)은 **필요 최소 순마진 비중을 읽는 눈금**으로만 쓴다 (P1·P6).
- c/m 스캔 범위: 로그 축, 주 조합 η의 최솟값 1/10 ~ 최댓값 10배, 41점 (Phase 3 §4).
- "배분 비교"는 관측된 세그먼트 값으로 계산한 가상 배분이다. 개입 효과가 아니다 (P3). 문서에서도 그렇게 적는다.
- 스크립트 번호 `13~14`, 산출 파일 접두어 `p5_`. 차트는 만들지 않는다.
- PowerShell 5.1: `&&` 대신 `;`. 커밋 메시지 끝에 `Co-Authored-By: Claude Opus 5 <noreply@anthropic.com>`.

## 판정 규칙 (착수 전 고정)

1. **순위 정합 ρ(p, η)** (주 조합, 39개 세그먼트, Spearman)
   - ρ ≥ 0.9 → "성사율 순위와 효율 순위는 사실상 같다". 핵심 질문의 답은 "같다"이고, 반전은 관측되지 않은 것으로 보고한다
   - 0.7 ≤ ρ < 0.9 → "대체로 같지만 어긋나는 구간이 있다". 어긋남 목록이 결과다
   - ρ < 0.7 → "다르다"
   - 부트스트랩 90% 구간을 함께 적는다. 구간이 경계를 걸치면 두 판정을 모두 적는다
2. **어긋남 목록:** 성사율 순위와 η 순위의 차이가 **10계단 이상**인 세그먼트
3. **배분 비교:** 공수 예산 50%에서 η 순서 배분의 대출 규모가 성사율 순서보다 **5% 이상** 많으면 "성사율 기준 배분은 실질적으로 비효율"로 본다. 25%·75%도 함께 보고한다
4. **순위 견고성:** η 4조합 간 Spearman 최솟값이 0.9 이상이면 주 조합 순위를 채택한다. 미만이면 크게 움직이는 세그먼트를 표시한다
5. **부호:** 참조 인건비에서 가장 불리한 세그먼트의 필요 최소 순마진 비중을 보고한다. 부호가 바뀌려면 순마진 비중이 그 값 아래로 내려가야 한다. 이 비중이 현실적인지는 판정하지 않는다 (근거 없음, P6). "부호 불일치 미관측, 효율 격차가 결론"인지는 이 값과 함께 서술한다

## File Structure

| 파일 | 책임 |
|---|---|
| `analysis/efficiency.py` | 순위 정합, 사분면, c/m 스캔, 필요 순마진 비중, 배분 곡선, 순위 상관 부트스트랩 |
| `analysis/13_rank_alignment.py` | 세그먼트 효율 표, ρ(p, η) 4조합 + 구간, 어긋남 목록, η 조합 간 순위 상관 |
| `analysis/14_targeting_and_scan.py` | 배분 비교, c/m 스캔, 필요 최소 순마진 비중, 계산기 입력 |
| `tests/test_efficiency.py` | 단위 테스트 7개 |
| `docs/05_expected_value.md` | Phase 5 결론 문서 |

---

### Task 1: efficiency 모듈

**Files:**
- Create: `analysis/efficiency.py`, `tests/test_efficiency.py`

**Interfaces:**
- Produces:
  - `rank_alignment(table, a="p", b="eta") -> pd.DataFrame` — `rank_{a}`, `rank_{b}`(내림차순, 1 = 최고), `rank_gap = rank_a − rank_b` 추가
  - `quadrant(table, a="p", b="eta") -> pd.Series` — 중앙값 기준 `성사율↑·효율↑` / `성사율↑·효율↓` / `성사율↓·효율↑` / `성사율↓·효율↓`
  - `cm_scan(table, grid, eta_col="eta") -> pd.DataFrame` — 컬럼 `c_over_m, negative_segments, application_share, effort_share`
  - `min_margin_share(table, cost: float) -> pd.Series` — `cost / eta_I`
  - `targeting_curve(table, order_col) -> pd.DataFrame` — order_col 내림차순 누적 `effort_share`, `volume`(= Σ n·p·R̄)
  - `volume_at_effort_share(curve, share) -> float` — 선형 보간
  - `bootstrap_rank_corr(frame, by, r_col, e_col, success_col="reached_pending", n_boot=200, seed=0) -> np.ndarray`

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_efficiency.py`

```python
import numpy as np
import pandas as pd

from efficiency import (bootstrap_rank_corr, cm_scan, min_margin_share, quadrant,
                        rank_alignment, targeting_curve, volume_at_effort_share)


def _table():
    return pd.DataFrame({"n": [10, 10], "p": [0.5, 0.5], "r_mean": [100.0, 10.0],
                         "e_mean": [1.0, 1.0], "eta": [50.0, 5.0], "eta_I": [100.0, 50.0]},
                        index=pd.Index(["A", "B"], name="segment"))


def test_rank_alignment_gap():
    t = pd.DataFrame({"p": [0.9, 0.5, 0.1], "eta": [1.0, 2.0, 3.0]}, index=list("xyz"))
    out = rank_alignment(t)
    assert list(out["rank_p"]) == [1, 2, 3] and list(out["rank_eta"]) == [3, 2, 1]
    assert list(out["rank_gap"]) == [-2, 0, 2]


def test_quadrant_labels():
    t = pd.DataFrame({"p": [0.9, 0.9, 0.1, 0.1], "eta": [9.0, 1.0, 9.0, 1.0]}, index=list("abcd"))
    assert list(quadrant(t)) == ["성사율↑·효율↑", "성사율↑·효율↓", "성사율↓·효율↑", "성사율↓·효율↓"]


def test_cm_scan_counts_negative_segments():
    scan = cm_scan(_table(), [1.0, 10.0, 60.0])
    assert list(scan["negative_segments"]) == [0, 1, 2]
    assert list(scan["application_share"]) == [0.0, 0.5, 1.0]


def test_min_margin_share():
    assert list(min_margin_share(_table(), cost=10.0)) == [0.1, 0.2]


def test_targeting_curve_and_volume_at_budget():
    curve = targeting_curve(_table(), "eta")
    assert list(curve["segment"]) == ["A", "B"]
    assert list(curve["volume"]) == [500.0, 550.0]
    assert volume_at_effort_share(curve, 0.5) == 500.0
    assert volume_at_effort_share(curve, 0.25) == 250.0


def test_targeting_order_matters():
    curve = targeting_curve(_table(), "r_mean")
    assert volume_at_effort_share(curve, 0.5) == 500.0
    reverse = targeting_curve(_table().assign(neg=[-1, 1]), "neg")
    assert volume_at_effort_share(reverse, 0.5) == 50.0


def test_bootstrap_rank_corr_shape_and_bounds():
    rng = np.random.default_rng(1)
    frame = pd.DataFrame({
        "seg": np.repeat(list("abcd"), 50),
        "reached_pending": rng.random(200) < np.repeat([0.2, 0.4, 0.6, 0.8], 50),
        "r": np.repeat([10.0, 20.0, 30.0, 40.0], 50),
        "e": np.ones(200),
    })
    rhos = bootstrap_rank_corr(frame, "seg", "r", "e", n_boot=10)
    assert len(rhos) == 10
    assert np.all((rhos >= -1) & (rhos <= 1))
```

- [ ] **Step 2: 실패 확인** — Run: `.venv\Scripts\python -m pytest tests/test_efficiency.py -q` / Expected: `No module named 'efficiency'`

- [ ] **Step 3: `analysis/efficiency.py` 구현**

```python
"""Segment-level efficiency: does success rate rank segments the way η does, and what is the gap worth?"""
from __future__ import annotations

import numpy as np
import pandas as pd

QUADRANTS = ["성사율↑·효율↑", "성사율↑·효율↓", "성사율↓·효율↑"]


def rank_alignment(table: pd.DataFrame, a: str = "p", b: str = "eta") -> pd.DataFrame:
    out = table.copy()
    out[f"rank_{a}"] = out[a].rank(ascending=False, method="min").astype(int)
    out[f"rank_{b}"] = out[b].rank(ascending=False, method="min").astype(int)
    out["rank_gap"] = out[f"rank_{a}"] - out[f"rank_{b}"]
    return out


def quadrant(table: pd.DataFrame, a: str = "p", b: str = "eta") -> pd.Series:
    high_a, high_b = table[a] >= table[a].median(), table[b] >= table[b].median()
    labels = np.select([high_a & high_b, high_a & ~high_b, ~high_a & high_b], QUADRANTS,
                       default="성사율↓·효율↓")
    return pd.Series(labels, index=table.index, name="quadrant")


def cm_scan(table: pd.DataFrame, grid, eta_col: str = "eta") -> pd.DataFrame:
    """For each c/m, segments whose η falls below it (negative EV) and their share of applications and effort."""
    effort = table["n"] * table["e_mean"]
    rows = []
    for cm in grid:
        negative = table[eta_col] < cm
        rows.append({
            "c_over_m": float(cm),
            "negative_segments": int(negative.sum()),
            "application_share": float(table.loc[negative, "n"].sum() / table["n"].sum()),
            "effort_share": float(effort[negative].sum() / effort.sum()),
        })
    return pd.DataFrame(rows)


def min_margin_share(table: pd.DataFrame, cost: float) -> pd.Series:
    """Share of gross interest that must be net margin for EV ≥ 0 at hourly cost `cost`."""
    return (cost / table["eta_I"]).rename("min_margin_share")


def targeting_curve(table: pd.DataFrame, order_col: str) -> pd.DataFrame:
    """Serve segments in descending order_col; cumulative effort share and expected loan volume."""
    t = table.sort_values(order_col, ascending=False, kind="stable")
    effort = t["n"] * t["e_mean"]
    volume = t["n"] * t["p"] * t["r_mean"]
    return pd.DataFrame({
        "segment": t.index,
        "effort_share": (effort.cumsum() / effort.sum()).to_numpy(),
        "volume": volume.cumsum().to_numpy(),
    })


def volume_at_effort_share(curve: pd.DataFrame, share: float) -> float:
    xs = np.concatenate([[0.0], curve["effort_share"].to_numpy()])
    ys = np.concatenate([[0.0], curve["volume"].to_numpy()])
    return float(np.interp(share, xs, ys))


def bootstrap_rank_corr(frame: pd.DataFrame, by: str, r_col: str, e_col: str,
                        success_col: str = "reached_pending", n_boot: int = 200,
                        seed: int = 0) -> np.ndarray:
    """Spearman ρ between segment success rate and η, resampling cases within each segment."""
    rng = np.random.default_rng(seed)
    groups = [(g[success_col].to_numpy(bool), g[r_col].to_numpy(float), g[e_col].to_numpy(float))
              for _, g in frame.groupby(by, observed=True)]
    rhos = np.empty(n_boot)
    for b in range(n_boot):
        p, eta = [], []
        for s, r, e in groups:
            idx = rng.integers(0, len(s), len(s))
            hit = s[idx]
            rate = hit.mean()
            r_mean = r[idx][hit].mean() if hit.any() else np.nan
            p.append(rate)
            eta.append(r_mean * rate / e[idx].mean())
        rhos[b] = pd.Series(p).corr(pd.Series(eta), method="spearman")
    return rhos
```

- [ ] **Step 4: 통과 확인** — Run: `.venv\Scripts\python -m pytest tests -q` / Expected: 47 passed (기존 40 + 7)

- [ ] **Step 5: 커밋**

```powershell
git add analysis/efficiency.py tests/test_efficiency.py; git commit -m "feat: add segment efficiency module"
```

---

### Task 2: 순위 정합 — 핵심 질문

**Files:**
- Create: `analysis/13_rank_alignment.py`

**Interfaces:**
- Consumes: `load_analysis_frame`, `outputs/p4_segments.parquet`, `value.group_eta`, `efficiency.*`
- Produces: `outputs/p5_segment_efficiency.csv`(index `segment`; n, p, r_mean, e_mean, eta, 순위, 사분면, η 4조합, η_I — **Task 3과 계산기의 입력**), `p5_rank_alignment.csv`, `p5_eta_rank_corr.csv`, `p5_mismatch.csv`

- [ ] **Step 1: `analysis/13_rank_alignment.py` 작성**

```python
"""Phase 5 — do success rate and η rank the segments the same way? (the core question)

Run from the project root:

    .venv\\Scripts\\python analysis/13_rank_alignment.py
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from config import OUT_DIR
from efficiency import bootstrap_rank_corr, quadrant, rank_alignment
from loader import load_analysis_frame
from value import group_eta

MIN_N = 300
MIN_RANK_GAP = 10
COMBOS = {
    "amount_effort": ("r_amount", "effort_hours"),
    "years_effort": ("r_amount_years", "effort_hours"),
    "amount_events": ("r_amount", "staff_events"),
    "years_events": ("r_amount_years", "staff_events"),
}


def main() -> None:
    frame = load_analysis_frame(MIN_N).join(pd.read_parquet(OUT_DIR / "p4_segments.parquet"))
    sizes = frame["segment"].value_counts()
    frame = frame[frame["segment"].isin(sizes.index[sizes >= MIN_N])]
    print(f"segments used={frame['segment'].nunique()}  cases={len(frame):,}")

    tables = {k: group_eta(frame, "segment", r, e) for k, (r, e) in COMBOS.items()}
    table = rank_alignment(tables["amount_effort"])
    table["quadrant"] = quadrant(table)
    for k, t in tables.items():
        table[f"eta_{k}"] = t["eta"]
    table["eta_I"] = group_eta(frame, "segment", "interest_total", "effort_hours")["eta"]
    table.sort_values("eta", ascending=False).round(4).to_csv(
        OUT_DIR / "p5_segment_efficiency.csv", encoding="utf-8-sig")

    rhos = bootstrap_rank_corr(frame, "segment", "r_amount", "effort_hours")
    lo, hi = np.nanquantile(rhos, [0.05, 0.95])
    alignment = pd.DataFrame([{
        "combo": k,
        "rho_p_eta": t["p"].corr(t["eta"], method="spearman"),
        "rho_p_r_mean": t["p"].corr(t["r_mean"], method="spearman"),
        "rho_p_e_mean": t["p"].corr(t["e_mean"], method="spearman"),
    } for k, t in tables.items()]).round(3)
    alignment.loc[alignment["combo"] == "amount_effort", ["rho_ci_lo", "rho_ci_hi"]] = [round(lo, 3), round(hi, 3)]
    alignment.to_csv(OUT_DIR / "p5_rank_alignment.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== rank alignment between success rate and η (39 segments) ===\n{alignment.to_string(index=False)}")

    eta_cols = [f"eta_{k}" for k in COMBOS]
    eta_corr = table[eta_cols].corr(method="spearman").round(3)
    eta_corr.to_csv(OUT_DIR / "p5_eta_rank_corr.csv", encoding="utf-8-sig")
    print(f"\n=== η rank stability across R x E combos ===\n{eta_corr.to_string()}")

    mismatch = table[table["rank_gap"].abs() >= MIN_RANK_GAP].sort_values("rank_gap")
    cols = ["n", "p", "r_mean", "e_mean", "eta", "rank_p", "rank_eta", "rank_gap", "quadrant"]
    mismatch[cols].round(4).to_csv(OUT_DIR / "p5_mismatch.csv", encoding="utf-8-sig")
    print(f"\n=== segments whose success-rate rank and η rank differ by >= {MIN_RANK_GAP} ===\n"
          f"{mismatch[cols].round(3).to_string()}")
    print(f"\nquadrants: {table['quadrant'].value_counts().to_dict()}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/13_rank_alignment.py`
기록 대상: ρ(p, η)와 90% 구간(**판단 지점 1**), 어긋남 목록(**판단 지점 2**), η 4조합 순위 상관(**판단 지점 4**), ρ(p, R̄)·ρ(p, Ē)로 본 어긋남의 원인, 사분면 분포

- [ ] **Step 3: 커밋**

```powershell
git add analysis/13_rank_alignment.py outputs/p5_segment_efficiency.csv outputs/p5_rank_alignment.csv outputs/p5_eta_rank_corr.csv outputs/p5_mismatch.csv; git commit -m "feat: measure rank alignment between success rate and eta"
```

---

### Task 3: 배분 비교·c/m 스캔·필요 순마진 비중·계산기 입력

**Files:**
- Create: `analysis/14_targeting_and_scan.py`

**Interfaces:**
- Consumes: `outputs/p5_segment_efficiency.csv`
- Produces: `p5_targeting_compare.csv`, `p5_cm_scan.csv`, `p5_margin_share.csv`, `p5_calculator_input.csv`, `p5_calculator_meta.json` → **계산기(MVP) 입력**

- [ ] **Step 1: `analysis/14_targeting_and_scan.py` 작성**

```python
"""Phase 5 — what ranking by η instead of success rate is worth, where EV turns negative,
and how much of the interest must be net margin in each segment.

Run from the project root, after 13_rank_alignment.py:

    .venv\\Scripts\\python analysis/14_targeting_and_scan.py
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from config import OUT_DIR
from efficiency import cm_scan, min_margin_share, targeting_curve, volume_at_effort_share

REFERENCE_COST = 57.6  # EUR/hour — Eurostat lc_lci_lev, NL, NACE K, 2016 (docs/03_method.md §3)
EFFORT_BUDGETS = [0.25, 0.5, 0.75]
GRID_POINTS = 41


def main() -> None:
    table = pd.read_csv(OUT_DIR / "p5_segment_efficiency.csv", index_col="segment")

    curves = {order: targeting_curve(table, order) for order in ("p", "eta")}
    compare = pd.DataFrame([{
        "effort_budget_share": share,
        "volume_by_success_rate": volume_at_effort_share(curves["p"], share),
        "volume_by_eta": volume_at_effort_share(curves["eta"], share),
    } for share in EFFORT_BUDGETS])
    compare["eta_order_gain"] = compare["volume_by_eta"] / compare["volume_by_success_rate"] - 1
    compare = compare.round(4)
    compare.to_csv(OUT_DIR / "p5_targeting_compare.csv", index=False, encoding="utf-8-sig")
    print(f"=== expected loan volume for the same effort budget: success-rate order vs η order ===\n"
          f"{compare.to_string(index=False)}")

    grid = np.geomspace(table["eta"].min() / 10, table["eta"].max() * 10, GRID_POINTS)
    scan = cm_scan(table, grid).round(4)
    scan.to_csv(OUT_DIR / "p5_cm_scan.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== c/m scan (R = accepted amount, E = effort hours) ===\n{scan.to_string(index=False)}")
    print(f"first segment turns negative at c/m = {table['eta'].min():,.0f} ({table['eta'].idxmin()})")

    table["min_margin_share"] = min_margin_share(table, REFERENCE_COST)
    margin = table[["n", "p", "eta", "eta_I", "min_margin_share"]].sort_values(
        "min_margin_share", ascending=False).round(4)
    margin.to_csv(OUT_DIR / "p5_margin_share.csv", encoding="utf-8-sig")
    worst, best = margin["min_margin_share"].max(), margin["min_margin_share"].min()
    print(f"\n=== minimum net-margin share of interest for EV >= 0 at {REFERENCE_COST} EUR/h ===\n"
          f"{margin.head(5).to_string()}\n...\n{margin.tail(3).to_string()}")
    print(f"worst {worst:.2%}  best {best:.2%}  worst/best {worst / best:.1f}x (independent of the cost assumed)")

    calc_cols = ["n", "p", "r_mean", "e_mean", "eta", "eta_amount_effort", "eta_years_effort",
                 "eta_amount_events", "eta_years_events", "eta_I", "min_margin_share", "quadrant"]
    table[calc_cols].round(4).to_csv(OUT_DIR / "p5_calculator_input.csv", encoding="utf-8-sig")
    (OUT_DIR / "p5_calculator_meta.json").write_text(json.dumps({
        "reference_cost_eur_per_hour": REFERENCE_COST,
        "reference_cost_source": "Eurostat lc_lci_lev, geo=NL, nace_r2=K, time=2016, lcstruct=D1_D4_MD5",
        "primary_combo": {"R": "r_amount", "E": "effort_hours"},
        "segments": len(table),
        "note": "Observed segment values; allocation comparisons are hypothetical, not intervention effects.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 실데이터 실행** — Run: `.venv\Scripts\python analysis/14_targeting_and_scan.py`
기록 대상: 예산 25·50·75%에서 η 순서 배분의 이득(**판단 지점 3**), c/m 스캔에서 첫 음수 지점과 음수 세그먼트의 신청·공수 비중, 필요 최소 순마진 비중의 최악·최선·배율(**판단 지점 5**)

- [ ] **Step 3: 커밋**

```powershell
git add analysis/14_targeting_and_scan.py outputs/p5_targeting_compare.csv outputs/p5_cm_scan.csv outputs/p5_margin_share.csv outputs/p5_calculator_input.csv outputs/p5_calculator_meta.json; git commit -m "feat: compare targeting orders, scan c/m and derive margin thresholds"
```

---

### Task 4: Phase 5 결론 문서와 CLAUDE.md 반영

**Files:**
- Create: `docs/05_expected_value.md`
- Modify: `CLAUDE.md` (§6 진행 현황표·Phase 5 절·Phase 6·8·9 절, §7 반전 시나리오, §12), 이 파일의 진행 기록

- [ ] **Step 1: `docs/05_expected_value.md` 작성** — 모든 수치 옆에 `outputs/p5_*` 출처

```markdown
# Phase 5 — 효율 지표 산출
## 요약 (핵심 질문에 대한 답)
## 1. 성사율 순위 vs η 순위 (p5_rank_alignment.csv)
## 2. 어긋나는 세그먼트와 그 이유 (p5_mismatch.csv — R̄·Ē 분해)
## 3. 같은 공수, 다른 배분 (p5_targeting_compare.csv — 가상 배분임을 명시)
## 4. c/m 스캔과 필요 최소 순마진 비중 (p5_cm_scan.csv, p5_margin_share.csv)
## 5. R·E 조합에 따른 견고성 (p5_eta_rank_corr.csv)
## 6. 반전 시나리오 점검 (CLAUDE.md §7의 1·2·3)
## 7. 다음 Phase로 넘기는 것
```

- [ ] **Step 2: CLAUDE.md 반영** — 진행 현황표, Phase 5 절(판단 지점별 결과), §7 반전 시나리오 상태, Phase 6(출발값), Phase 8·9(시사점), §12
- [ ] **Step 3: 이 파일의 진행 기록에 실행 중 변경·결과 요약·커밋 추가**
- [ ] **Step 4: 사용자 보고** — 핵심 질문에 대한 답, Phase 6 진행계획 착수 여부 확인
- [ ] **Step 5: 커밋**

```powershell
git add docs/05_expected_value.md docs/plans/phase-05-efficiency.md CLAUDE.md; git commit -m "docs: record phase 5 efficiency results"
```

---

## 진행 기록

| 날짜 | 내용 |
|---|---|
| 2026-09-11 | 진행계획 작성. 판정 규칙(ρ 0.9/0.7 경계, 어긋남 10계단, 배분 이득 5%, 순위 견고성 0.9)을 착수 전에 고정. 사용자 확인 대기 |
