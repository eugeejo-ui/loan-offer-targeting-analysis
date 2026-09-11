# Phase 0 — 데이터 확인과 범위 확정 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** BPI 2017 로그의 속성·결측·0값을 확인하고, 케이스 결과 정의와 관측창 컷오프를 확정하고, 선행 수치(27% / 53.1% / 59.0%)를 재현한다. 결과는 `docs/00_scope.md`에 쓰고 CLAUDE.md에 반영한다.

**Architecture:** 판정 로직은 `analysis/`의 작은 모듈(config, loader, profiling, outcomes, offers)에 두고 pytest로 합성 데이터에 대해 검증한다. 실데이터는 번호가 붙은 스크립트(00~03)가 모듈을 호출해 `outputs/p0_*`로 떨군다. 원본 XES는 한 번만 파싱해 parquet로 캐시한다.

**Tech Stack:** Python 3.12, pandas, pm4py, pyarrow, pytest (Windows PowerShell 5.1)

**Spec:** `C:\loan-offer-targeting-analysis\CLAUDE.md` — §4 데이터, §5 P2·P4, §6 Phase 0

## 실행 중 변경 (2026-09-11, 결과는 `docs/00_scope.md`)

- `offers.offer_final_state()`와 테스트 1개를 추가했다 (결과 누수 판정용). 테스트는 총 15개
- `01_inspect_schema.py`에 오퍼 최종 상태별 속성(`p0_offer_attrs_by_final_state.csv`)과 RequestedAmount 0값(`p0_requested_amount_zero.csv`) 점검을 추가했다
- `02_case_outcomes.py`에 `in_population`(관측창 안 + 종료) 컬럼을 추가했다. `03_replicate_prior.py`는 `in_window` 대신 이 컬럼을 쓴다

## Global Constraints

- 원본 `C:\sap-btm-financial-prospecting\data\bpi2017\BPI Challenge 2017.xes`는 **읽기 전용**이다. 그 폴더에 어떤 파일도 쓰지 않는다 (sap-btm 로더의 gz 해제 로직은 가져오지 않는다).
- 파이썬은 이 프로젝트 전용 `.venv`만 쓴다 (`py -3.12`로 생성). sap-btm venv는 쓰지 않는다.
- 종료 이벤트는 `A_Pending`(성사) / `A_Denied`(거절) / `A_Cancelled`(취소) 3종이다. 셋 다 없으면 `open`이다.
- 관측창 컷오프 임계값은 접수월 완료율 **0.99** (P4).
- Phase 0 산출 파일은 `outputs/p0_*` 접두어를 쓴다.
- 문서의 수치는 스크립트 출력에서만 옮긴다.
- PowerShell 5.1에서는 `&&`를 쓸 수 없다. 명령은 `;`로 잇는다.
- 커밋 단계는 로컬 git 사용이 승인된 경우에만 수행한다 (CLAUDE.md §11 미결 사항).

## 헤더 확인으로 이미 알게 된 사실 (2026-09-11, XES 직접 확인)

- 케이스 속성: `concept:name`(= `Application_…`), `RequestedAmount`(float), `ApplicationType`, `LoanGoal` → pm4py DataFrame에서는 `case:` 접두어가 붙는다.
- 이벤트 공통 속성: `concept:name`, `lifecycle:transition`, `time:timestamp`, `org:resource`, `EventOrigin`, `EventID`, `Action`.
- 오퍼 속성 `OfferedAmount`, `CreditScore`(int), `MonthlyCost`, `NumberOfTerms`(int), `FirstWithdrawalAmount`, `Selected`(bool), `Accepted`(bool)는 **`O_Create Offer` 이벤트에만** 붙는다. 이 이벤트의 `EventID`(= `Offer_…`)가 오퍼 식별자이고, 이후 오퍼 상태 이벤트(O_Created, O_Sent, O_Accepted …)는 `OfferID`로 이를 가리킨다.
- `A_Create Application`의 리소스는 `User_1`(시스템 계정으로 추정)이다.

## File Structure

| 파일 | 책임 |
|---|---|
| `requirements.txt`, `.gitignore` | 환경 |
| `analysis/config.py` | 경로·컬럼명·상수 (다른 모든 모듈이 import) |
| `analysis/loader.py` | XES → DataFrame → parquet 캐시 |
| `analysis/profiling.py` | 속성 결측·0값·고유값 프로파일, 케이스 내 상수성 |
| `analysis/outcomes.py` | 케이스 결과 판정, 접수월별 완료율, 컷오프 선택 |
| `analysis/offers.py` | 오퍼 테이블, 케이스당 오퍼 수, 오퍼 그룹별 성사율, OfferID 연결 검사 |
| `analysis/00_build_cache.py` | 캐시 생성 + 규모 확인 |
| `analysis/01_inspect_schema.py` | 속성 프로파일 출력 |
| `analysis/02_case_outcomes.py` | 결과 판정·컷오프 출력 |
| `analysis/03_replicate_prior.py` | 선행 수치 재현 |
| `tests/conftest.py`, `tests/test_*.py` | 모듈 단위 테스트 |
| `docs/00_scope.md` | Phase 0 결론 문서 |

---

### Task 1: 프로젝트 환경 구성

**Files:**
- Create: `requirements.txt`, `.gitignore`, `analysis/config.py`, `tests/conftest.py`

**Interfaces:**
- Produces: `config` 모듈 상수 — `ROOT, SOURCE_XES, CACHE_PARQUET, OUT_DIR, CASE, ACT, TS, LIFECYCLE, RESOURCE, ORIGIN, EVENT_ID, OFFER_ID, END_LABELS, INTAKE_ATTRS, OFFER_ATTRS, BOOL_ATTRS, SYSTEM_RESOURCE`

- [ ] **Step 1: requirements.txt 작성**

```text
pandas>=2.2
pm4py>=2.7
pyarrow>=15
matplotlib>=3.8
pytest>=8
```

- [ ] **Step 2: .gitignore 작성**

```text
.venv/
data/
__pycache__/
*.pyc
.pytest_cache/
```

- [ ] **Step 3: venv 생성 및 설치**

Run:
```powershell
py -3.12 -m venv .venv; .venv\Scripts\python -m pip install --upgrade pip; .venv\Scripts\python -m pip install -r requirements.txt
```
Expected: 오류 없이 설치 완료

- [ ] **Step 4: analysis/config.py 작성**

```python
"""Paths and column names shared by every analysis module and script."""
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SOURCE_XES = Path(r"C:\sap-btm-financial-prospecting\data\bpi2017\BPI Challenge 2017.xes")
CACHE_PARQUET = ROOT / "data" / "bpi2017_events.parquet"
OUT_DIR = ROOT / "outputs"

CASE = "case:concept:name"
ACT = "concept:name"
TS = "time:timestamp"
LIFECYCLE = "lifecycle:transition"
RESOURCE = "org:resource"
ORIGIN = "EventOrigin"
EVENT_ID = "EventID"
OFFER_ID = "OfferID"
ACTION = "Action"

END_LABELS = {"A_Pending": "success", "A_Denied": "denied", "A_Cancelled": "cancelled"}
INTAKE_ATTRS = ["case:RequestedAmount", "case:LoanGoal", "case:ApplicationType"]
OFFER_ATTRS = [
    "OfferedAmount", "CreditScore", "MonthlyCost", "NumberOfTerms",
    "FirstWithdrawalAmount", "Selected", "Accepted",
]
BOOL_ATTRS = ["Selected", "Accepted"]
SYSTEM_RESOURCE = "User_1"
```

- [ ] **Step 5: tests/conftest.py 작성**

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "analysis"))
```

- [ ] **Step 6: 설치 확인**

Run:
```powershell
.venv\Scripts\python -c "import pandas, pm4py, pyarrow, sys; sys.path.insert(0, 'analysis'); import config; print(pandas.__version__, pm4py.__version__, pyarrow.__version__, config.SOURCE_XES.exists())"
```
Expected: 버전 3개와 `True`

- [ ] **Step 7: (git 승인 시) 초기화 및 커밋**

```powershell
git init; git add requirements.txt .gitignore CLAUDE.md docs analysis tests; git commit -m "chore: set up phase 0 environment"
```

---

### Task 2: 로더와 parquet 캐시

**Files:**
- Create: `analysis/loader.py`, `analysis/00_build_cache.py`
- Test: `tests/test_loader.py`

**Interfaces:**
- Consumes: `config.SOURCE_XES, config.CACHE_PARQUET, config.TS, config.BOOL_ATTRS`
- Produces: `load_events(source: Path = SOURCE_XES, cache: Path = CACHE_PARQUET) -> pd.DataFrame`, `_normalize(df: pd.DataFrame) -> pd.DataFrame`

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_loader.py`

```python
import pandas as pd
import pytest

from loader import _normalize, load_events


def test_load_events_prefers_cache(tmp_path):
    cache = tmp_path / "events.parquet"
    pd.DataFrame({
        "time:timestamp": pd.to_datetime(["2016-01-01"], utc=True),
        "concept:name": ["A_Create Application"],
    }).to_parquet(cache, index=False)
    df = load_events(source=tmp_path / "missing.xes", cache=cache)
    assert list(df["concept:name"]) == ["A_Create Application"]


def test_load_events_raises_without_cache_or_source(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_events(source=tmp_path / "missing.xes", cache=tmp_path / "missing.parquet")


def test_normalize_parses_timestamp_and_booleans():
    df = pd.DataFrame({
        "time:timestamp": ["2016-01-01T09:51:15.304Z"],
        "Accepted": ["true"],
        "Selected": [float("nan")],
    })
    out = _normalize(df)
    assert str(out["time:timestamp"].dt.tz) == "UTC"
    assert bool(out["Accepted"].iloc[0]) is True
    assert out["Selected"].isna().iloc[0]
```

- [ ] **Step 2: 실패 확인**

Run: `.venv\Scripts\python -m pytest tests/test_loader.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'loader'`

- [ ] **Step 3: analysis/loader.py 구현**

```python
"""Load the BPI 2017 event log, caching it as parquet inside this project.

The source XES lives in the sap-btm project and is read-only here: this
module never writes next to it.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

from config import BOOL_ATTRS, CACHE_PARQUET, SOURCE_XES, TS

_BOOL_MAP = {True: True, False: False, "true": True, "false": False}


def _normalize(df: pd.DataFrame) -> pd.DataFrame:
    df[TS] = pd.to_datetime(df[TS], utc=True)
    for col in BOOL_ATTRS:
        if col in df.columns:
            df[col] = df[col].map(_BOOL_MAP).astype("boolean")
    return df


def load_events(source: Path = SOURCE_XES, cache: Path = CACHE_PARQUET) -> pd.DataFrame:
    if cache.exists():
        return pd.read_parquet(cache)
    if not source.exists():
        raise FileNotFoundError(f"Neither cache {cache} nor source {source} exists")

    import pm4py  # imported lazily: parsing is only needed once

    log = pm4py.read_xes(str(source))
    if not isinstance(log, pd.DataFrame):
        log = pm4py.convert_to_dataframe(log)
    log = _normalize(log)
    cache.parent.mkdir(parents=True, exist_ok=True)
    log.to_parquet(cache, index=False)
    return log
```

- [ ] **Step 4: 통과 확인**

Run: `.venv\Scripts\python -m pytest tests/test_loader.py -v`
Expected: 3 passed

- [ ] **Step 5: analysis/00_build_cache.py 작성**

```python
"""Phase 0 — parse the XES once and cache it; confirm the log's size.

Run from the project root:

    .venv\\Scripts\\python analysis/00_build_cache.py
"""
from __future__ import annotations

from config import ACT, CACHE_PARQUET, CASE, LIFECYCLE, TS
from loader import load_events


def main() -> None:
    fresh = not CACHE_PARQUET.exists()
    ev = load_events()
    print(f"{'built' if fresh else 'read'} cache: {CACHE_PARQUET}")
    print(f"events={len(ev):,}  cases={ev[CASE].nunique():,}  "
          f"activities={ev[ACT].nunique()}  lifecycle states={ev[LIFECYCLE].nunique()}")
    print(f"time range: {ev[TS].min()} -> {ev[TS].max()}")
    print(f"columns ({len(ev.columns)}): {list(ev.columns)}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 실데이터로 실행** (최초 파싱 수 분 소요)

Run: `.venv\Scripts\python analysis/00_build_cache.py`
Expected: `events=1,202,267  cases=31,509  activities=26  lifecycle states=7` (sap-btm 확인값). 다르면 멈추고 원인을 CLAUDE.md §12에 기록한다.

- [ ] **Step 7: (git 승인 시) 커밋**

```powershell
git add analysis/loader.py analysis/00_build_cache.py tests/test_loader.py; git commit -m "feat: add cached BPI 2017 loader"
```

---

### Task 3: 속성 프로파일 (결측·0값·시스템 계정)

**Files:**
- Create: `analysis/profiling.py`, `analysis/offers.py`(offer_table, unlinked_offer_ids만 먼저), `analysis/01_inspect_schema.py`
- Test: `tests/test_profiling.py`, `tests/test_offers.py`

**Interfaces:**
- Consumes: `loader.load_events`, `config.*`
- Produces:
  - `attribute_profile(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame` — 컬럼 `attribute, present, dtype, non_null, non_null_pct, zero_pct, n_unique`
  - `constant_within_case(df: pd.DataFrame, case_col: str, cols: list[str]) -> pd.Series` (컬럼명 → bool)
  - `offer_table(events: pd.DataFrame) -> pd.DataFrame` — 컬럼 `case:concept:name, offer_id, created_ts, *OFFER_ATTRS`
  - `unlinked_offer_ids(events: pd.DataFrame, offers: pd.DataFrame) -> set[str]`

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_profiling.py`

```python
import numpy as np
import pandas as pd

from profiling import attribute_profile, constant_within_case


def test_attribute_profile_counts_nulls_and_zeros():
    df = pd.DataFrame({"amt": [0.0, 5000.0, np.nan, 0.0], "goal": ["Car", None, "Car", "Home"]})
    prof = attribute_profile(df, ["amt", "goal", "absent"]).set_index("attribute")
    assert prof.loc["amt", "non_null"] == 3
    assert prof.loc["amt", "zero_pct"] == round(2 / 3 * 100, 2)
    assert prof.loc["goal", "zero_pct"] is None or pd.isna(prof.loc["goal", "zero_pct"])
    assert prof.loc["goal", "n_unique"] == 2
    assert not prof.loc["absent", "present"]


def test_constant_within_case():
    df = pd.DataFrame({
        "case": ["a", "a", "b", "b"],
        "goal": ["Car", "Car", "Home", "Home"],
        "score": [1, 2, 3, 3],
    })
    res = constant_within_case(df, "case", ["goal", "score"])
    assert res["goal"] and not res["score"]
```

- [ ] **Step 2: 실패하는 테스트 작성** — `tests/test_offers.py`

```python
import pandas as pd

from offers import offer_table, unlinked_offer_ids


def _events():
    return pd.DataFrame({
        "case:concept:name": ["A1", "A1", "A1", "A2"],
        "concept:name": ["O_Create Offer", "O_Created", "O_Create Offer", "O_Created"],
        "EventID": ["Offer_1", "OfferState_9", "Offer_2", "OfferState_8"],
        "OfferID": [None, "Offer_1", None, "Offer_99"],
        "time:timestamp": pd.to_datetime(["2016-01-01", "2016-01-01", "2016-01-05", "2016-01-02"], utc=True),
        "OfferedAmount": [5000.0, None, 7000.0, None],
        "CreditScore": [0, None, 900, None],
    })


def test_offer_table_one_row_per_created_offer():
    offers = offer_table(_events())
    assert list(offers["offer_id"]) == ["Offer_1", "Offer_2"]
    assert list(offers["OfferedAmount"]) == [5000.0, 7000.0]
    assert "created_ts" in offers.columns


def test_unlinked_offer_ids():
    ev = _events()
    assert unlinked_offer_ids(ev, offer_table(ev)) == {"Offer_99"}
```

- [ ] **Step 3: 실패 확인**

Run: `.venv\Scripts\python -m pytest tests/test_profiling.py tests/test_offers.py -v`
Expected: FAIL — `No module named 'profiling'` / `'offers'`

- [ ] **Step 4: analysis/profiling.py 구현**

```python
"""Attribute-quality checks run before any analysis relies on a column."""
from __future__ import annotations

import pandas as pd


def attribute_profile(df: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    rows = []
    n = len(df)
    for col in cols:
        present = col in df.columns
        s = df[col] if present else pd.Series(dtype="object")
        non_null = int(s.notna().sum())
        numeric = pd.api.types.is_numeric_dtype(s) and not pd.api.types.is_bool_dtype(s)
        zero_pct = round(float((s.dropna() == 0).mean()) * 100, 2) if numeric and non_null else None
        rows.append({
            "attribute": col,
            "present": present,
            "dtype": str(s.dtype),
            "non_null": non_null,
            "non_null_pct": round(non_null / n * 100, 2) if n else 0.0,
            "zero_pct": zero_pct,
            "n_unique": int(s.nunique()),
        })
    return pd.DataFrame(rows)


def constant_within_case(df: pd.DataFrame, case_col: str, cols: list[str]) -> pd.Series:
    return (df.groupby(case_col)[cols].nunique(dropna=True) <= 1).all()
```

- [ ] **Step 5: analysis/offers.py 구현 (1차)**

```python
"""Offer-level views. Offer attributes live only on O_Create Offer events;
that event's EventID is the offer key that later OfferID values point to."""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, EVENT_ID, OFFER_ATTRS, OFFER_ID, TS

CREATE_OFFER = "O_Create Offer"


def offer_table(events: pd.DataFrame) -> pd.DataFrame:
    created = events[events[ACT] == CREATE_OFFER]
    cols = [CASE, EVENT_ID, TS] + [c for c in OFFER_ATTRS if c in created.columns]
    return (created[cols]
            .rename(columns={EVENT_ID: "offer_id", TS: "created_ts"})
            .reset_index(drop=True))


def unlinked_offer_ids(events: pd.DataFrame, offers: pd.DataFrame) -> set[str]:
    referenced = set(events[OFFER_ID].dropna().unique())
    return referenced - set(offers["offer_id"])
```

- [ ] **Step 6: 통과 확인**

Run: `.venv\Scripts\python -m pytest tests/test_profiling.py tests/test_offers.py -v`
Expected: 4 passed

- [ ] **Step 7: analysis/01_inspect_schema.py 작성**

```python
"""Phase 0 — confirm attribute names, missingness and zero values.

Run from the project root:

    .venv\\Scripts\\python analysis/01_inspect_schema.py
"""
from __future__ import annotations

import pandas as pd

from config import (ACT, ACTION, CASE, INTAKE_ATTRS, LIFECYCLE, OFFER_ATTRS, ORIGIN,
                    OUT_DIR, RESOURCE, SYSTEM_RESOURCE)
from loader import load_events
from offers import CREATE_OFFER, offer_table, unlinked_offer_ids
from profiling import attribute_profile, constant_within_case


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    ev = load_events()
    intake = [c for c in INTAKE_ATTRS if c in ev.columns]
    missing = sorted(set(INTAKE_ATTRS) - set(intake))
    print(f"intake attributes missing from log: {missing or 'none'}")
    print("intake attributes constant within every case:",
          constant_within_case(ev, CASE, intake).to_dict())

    cases = ev.groupby(CASE)[intake].first()
    offers = offer_table(ev)
    profile = pd.concat([
        attribute_profile(cases, INTAKE_ATTRS).assign(level="case"),
        attribute_profile(offers, OFFER_ATTRS).assign(level="offer"),
    ], ignore_index=True)
    profile.to_csv(OUT_DIR / "p0_attribute_profile.csv", index=False, encoding="utf-8-sig")
    print("\n=== attribute profile ===")
    print(profile.to_string(index=False))

    acts = ev[ACT].value_counts().rename_axis("activity").reset_index(name="events")
    acts.to_csv(OUT_DIR / "p0_activity_counts.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== activities ({len(acts)}) ===\n{acts.to_string(index=False)}")
    print(f"\n=== lifecycle ===\n{ev[LIFECYCLE].value_counts().to_string()}")

    system = (ev[RESOURCE] == SYSTEM_RESOURCE).groupby(ev[ORIGIN]).agg(["sum", "mean"])
    system["mean"] = (system["mean"] * 100).round(1)
    system.columns = ["system_events", "system_pct"]
    system.to_csv(OUT_DIR / "p0_system_resource_share.csv", encoding="utf-8-sig")
    print(f"\n=== {SYSTEM_RESOURCE} share by EventOrigin ===\n{system.to_string()}")

    for col in intake[1:]:
        print(f"\n{col}:\n{cases[col].value_counts(dropna=False).to_string()}")
    print(f"\noffers={len(offers):,}  unlinked OfferIDs={len(unlinked_offer_ids(ev, offers))}")

    # Can offer creation tell a customer-requested offer from a bank-initiated one?
    created = ev[ev[ACT] == CREATE_OFFER]
    by_actor = (created[RESOURCE] == SYSTEM_RESOURCE).map({True: SYSTEM_RESOURCE, False: "staff"})
    creation = pd.concat([
        created[ACTION].value_counts().rename_axis("value").reset_index(name="events").assign(field=ACTION),
        by_actor.value_counts().rename_axis("value").reset_index(name="events").assign(field="resource"),
    ], ignore_index=True)
    creation.to_csv(OUT_DIR / "p0_offer_creation_actions.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== {CREATE_OFFER}: Action / resource ===\n{creation.to_string(index=False)}")
    print(f"distinct resources creating offers: {created[RESOURCE].nunique()}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 8: 실데이터로 실행하고 확인할 것을 기록**

Run: `.venv\Scripts\python analysis/01_inspect_schema.py`
Expected / 기록 대상:
- intake 속성 누락 `none`, 세 속성 모두 케이스 내 상수 `True` → 아니면 P2의 "접수 시점 변수" 전제가 흔들린다. 즉시 멈추고 보고한다
- `CreditScore`의 `zero_pct`, `case:RequestedAmount`의 `zero_pct` → 00_scope.md "주의점"에 기록
- `unlinked OfferIDs=0` 기대 → 0이 아니면 오퍼 연결 규칙을 재검토한다
- User_1 비중 → Phase 2의 시스템 계정 제외 판단 근거
- `p0_offer_creation_actions.csv` → Action·리소스로 고객 요청과 은행 선제 제시가 구분되는지 본다 (CLAUDE.md Phase 0 판단 지점 6). 구분 신호가 없으면 Phase 6 레버를 "추가 오퍼 생성 정책 전반"으로 기록한다

- [ ] **Step 9: (git 승인 시) 커밋**

```powershell
git add analysis/profiling.py analysis/offers.py analysis/01_inspect_schema.py tests/test_profiling.py tests/test_offers.py outputs/p0_attribute_profile.csv outputs/p0_activity_counts.csv outputs/p0_system_resource_share.csv; git commit -m "feat: profile BPI 2017 attributes"
```

---

### Task 4: 케이스 결과 판정과 관측창 컷오프

**Files:**
- Create: `analysis/outcomes.py`, `analysis/02_case_outcomes.py`
- Test: `tests/test_outcomes.py`

**Interfaces:**
- Consumes: `loader.load_events`, `config.CASE, ACT, TS, END_LABELS, OUT_DIR`
- Produces:
  - `case_outcomes(events: pd.DataFrame) -> pd.DataFrame` — index `case:concept:name`, 컬럼 `submit_ts, end_pattern, n_end, outcome, end_ts, reached_pending`
  - `monthly_completion(outcomes: pd.DataFrame) -> pd.DataFrame` — index `submit_month`(Period[M]), 컬럼 `n, n_open, completion_rate, median_days_closed, p90_days_closed`
  - `choose_cutoff(monthly: pd.DataFrame, threshold: float = 0.99) -> pd.Period`
  - 파일 `outputs/p0_case_outcomes.parquet` (위 컬럼 + `in_window`)

- [ ] **Step 1: 실패하는 테스트 작성** — `tests/test_outcomes.py`

```python
import pandas as pd
import pytest

from outcomes import case_outcomes, choose_cutoff, monthly_completion


def _events():
    rows = [
        ("A1", "A_Create Application", "2016-01-01"),
        ("A1", "A_Pending", "2016-01-20"),
        ("A2", "A_Create Application", "2016-01-03"),
        ("A2", "A_Cancelled", "2016-02-10"),
        ("A3", "A_Create Application", "2016-02-01"),
        ("A3", "A_Pending", "2016-02-15"),
        ("A3", "A_Cancelled", "2016-02-20"),
        ("A4", "A_Create Application", "2016-02-05"),
        ("A4", "W_Call after offers", "2016-02-06"),
    ]
    df = pd.DataFrame(rows, columns=["case:concept:name", "concept:name", "time:timestamp"])
    df["time:timestamp"] = pd.to_datetime(df["time:timestamp"], utc=True)
    return df


def test_case_outcomes_labels_last_end_event_and_keeps_pattern():
    oc = case_outcomes(_events())
    assert oc.loc["A1", "outcome"] == "success"
    assert oc.loc["A2", "outcome"] == "cancelled"
    assert oc.loc["A3", "outcome"] == "cancelled"
    assert oc.loc["A3", "end_pattern"] == "A_Pending>A_Cancelled"
    assert oc.loc["A3", "n_end"] == 2
    assert bool(oc.loc["A3", "reached_pending"]) is True
    assert oc.loc["A4", "outcome"] == "open"
    assert oc.loc["A4", "n_end"] == 0


def test_monthly_completion():
    monthly = monthly_completion(case_outcomes(_events()))
    jan, feb = pd.Period("2016-01", "M"), pd.Period("2016-02", "M")
    assert monthly.loc[jan, "n"] == 2 and monthly.loc[jan, "completion_rate"] == 1.0
    assert monthly.loc[feb, "n_open"] == 1 and monthly.loc[feb, "completion_rate"] == 0.5


def _monthly(rates):
    idx = pd.period_range("2016-01", periods=len(rates), freq="M")
    return pd.DataFrame({"completion_rate": rates}, index=idx)


def test_choose_cutoff_stops_before_first_month_below_threshold():
    assert choose_cutoff(_monthly([1.0, 0.995, 0.99, 0.97, 0.5])) == pd.Period("2016-03", "M")


def test_choose_cutoff_all_months_pass():
    assert choose_cutoff(_monthly([1.0, 0.999])) == pd.Period("2016-02", "M")


def test_choose_cutoff_first_month_fails():
    with pytest.raises(ValueError):
        choose_cutoff(_monthly([0.9, 1.0]))
```

- [ ] **Step 2: 실패 확인**

Run: `.venv\Scripts\python -m pytest tests/test_outcomes.py -v`
Expected: FAIL — `No module named 'outcomes'`

- [ ] **Step 3: analysis/outcomes.py 구현**

```python
"""Case outcome classification and the observation-window cutoff (P4).

A case's outcome is the label of its LAST end event; the full ordered
sequence of end events is kept in `end_pattern` so cases with more than
one end event stay visible rather than silently resolved.
"""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, END_LABELS, TS

CREATE_APPLICATION = "A_Create Application"


def case_outcomes(events: pd.DataFrame) -> pd.DataFrame:
    ev = events.sort_values([CASE, TS], kind="stable")
    first_ts = ev.groupby(CASE)[TS].min()
    created_ts = ev[ev[ACT] == CREATE_APPLICATION].groupby(CASE)[TS].min()

    ends = ev[ev[ACT].isin(END_LABELS)]
    last_end = ends.groupby(CASE).tail(1).set_index(CASE)

    out = pd.DataFrame(index=first_ts.index)
    out["submit_ts"] = created_ts.reindex(out.index).combine_first(first_ts)
    out["end_pattern"] = ends.groupby(CASE)[ACT].agg(">".join).reindex(out.index)
    out["n_end"] = ends.groupby(CASE).size().reindex(out.index, fill_value=0).astype(int)
    out["outcome"] = last_end[ACT].map(END_LABELS).reindex(out.index).fillna("open")
    out["end_ts"] = last_end[TS].reindex(out.index)
    out["reached_pending"] = out["end_pattern"].fillna("").str.contains("A_Pending", regex=False)
    out.index.name = CASE
    return out


def monthly_completion(outcomes: pd.DataFrame) -> pd.DataFrame:
    df = outcomes.copy()
    df["submit_month"] = df["submit_ts"].dt.tz_convert(None).dt.to_period("M")
    df["closed"] = df["outcome"] != "open"
    df["days_to_end"] = (df["end_ts"] - df["submit_ts"]).dt.total_seconds() / 86400
    g = df.groupby("submit_month")
    return pd.DataFrame({
        "n": g.size(),
        "n_open": g["closed"].apply(lambda s: int((~s).sum())),
        "completion_rate": g["closed"].mean(),
        "median_days_closed": g["days_to_end"].median(),
        "p90_days_closed": g["days_to_end"].quantile(0.9),
    })


def choose_cutoff(monthly: pd.DataFrame, threshold: float = 0.99) -> pd.Period:
    """Latest submission month such that it and every earlier month meet the threshold."""
    monthly = monthly.sort_index()
    ok = monthly["completion_rate"] >= threshold
    if not ok.iloc[0]:
        raise ValueError("The first submission month is already below the completion threshold")
    if ok.all():
        return monthly.index[-1]
    first_fail = monthly.index.get_loc((~ok).idxmax())
    return monthly.index[first_fail - 1]
```

- [ ] **Step 4: 통과 확인**

Run: `.venv\Scripts\python -m pytest tests/test_outcomes.py -v`
Expected: 5 passed

- [ ] **Step 5: analysis/02_case_outcomes.py 작성**

```python
"""Phase 0 — classify case outcomes and fix the observation window.

Run from the project root:

    .venv\\Scripts\\python analysis/02_case_outcomes.py
"""
from __future__ import annotations

import json

from config import OUT_DIR, TS
from loader import load_events
from outcomes import case_outcomes, choose_cutoff, monthly_completion

THRESHOLD = 0.99


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    ev = load_events()
    oc = case_outcomes(ev)
    obs_end = ev[TS].max()

    patterns = oc["end_pattern"].fillna("(none)").value_counts()
    patterns.rename_axis("end_pattern").reset_index(name="cases").to_csv(
        OUT_DIR / "p0_end_patterns.csv", index=False, encoding="utf-8-sig")
    print(f"observation ends: {obs_end}")
    print(f"\n=== end patterns ===\n{patterns.to_string()}")
    print(f"\n=== outcomes ===\n{oc['outcome'].value_counts().to_string()}")

    monthly = monthly_completion(oc)
    monthly.to_csv(OUT_DIR / "p0_monthly_completion.csv", encoding="utf-8-sig")
    print(f"\n=== completion by submission month ===\n{monthly.round(3).to_string()}")

    cutoff = choose_cutoff(monthly, THRESHOLD)
    oc["in_window"] = oc["submit_ts"].dt.tz_convert(None).dt.to_period("M") <= cutoff
    n_out = int((~oc["in_window"]).sum())
    print(f"\ncutoff month (completion >= {THRESHOLD}): {cutoff}")
    print(f"excluded cases: {n_out:,} / {len(oc):,} ({n_out / len(oc):.1%})")
    print(f"open cases left inside window: {int(((oc['outcome'] == 'open') & oc['in_window']).sum()):,}")

    oc.to_parquet(OUT_DIR / "p0_case_outcomes.parquet")
    (OUT_DIR / "p0_cutoff.json").write_text(json.dumps({
        "threshold": THRESHOLD,
        "cutoff_month": str(cutoff),
        "n_cases": len(oc),
        "n_excluded": n_out,
        "observation_end": str(obs_end),
    }, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 실데이터로 실행하고 판단할 것을 기록**

Run: `.venv\Scripts\python analysis/02_case_outcomes.py`
판단 기준:
- **종료 이벤트가 2개 이상인 패턴**(예: `A_Pending>A_Cancelled`)이 있으면 건수를 기록한다. "마지막 종료 이벤트 = 결과" 규칙을 유지할지 판단하고, 근거를 CLAUDE.md §12에 남긴다
- **컷오프 직전 몇 달의 `p90_days_closed`가 급락하면** 완료율 기준만으로는 절단 편향이 남아 있다는 신호다. 이 경우 컷오프를 한 달 앞당기는 안을 검토하고 사유를 기록한다
- 제외 비율을 기록한다 (00_scope.md에 필수 기재)

- [ ] **Step 7: (git 승인 시) 커밋**

```powershell
git add analysis/outcomes.py analysis/02_case_outcomes.py tests/test_outcomes.py outputs/p0_end_patterns.csv outputs/p0_monthly_completion.csv outputs/p0_cutoff.json; git commit -m "feat: classify case outcomes and fix observation window"
```

---

### Task 5: 선행 수치 재현

**Files:**
- Modify: `analysis/offers.py` (함수 2개 추가)
- Create: `analysis/03_replicate_prior.py`
- Test: `tests/test_offers.py` (테스트 2개 추가)

**Interfaces:**
- Consumes: `offer_table`, `outputs/p0_case_outcomes.parquet`(Task 4)
- Produces:
  - `offers_per_case(offers: pd.DataFrame, cases: pd.Index) -> pd.Series` (name `n_offers`, 오퍼 0건 포함)
  - `conversion_by_offer_group(outcomes: pd.DataFrame, n_offers: pd.Series, success_col: str = "reached_pending") -> pd.DataFrame` — index `group`("0","1","2+"), 컬럼 `n, n_success, rate`
  - 파일 `outputs/p0_offers.parquet`, `outputs/p0_replication.csv`

- [ ] **Step 1: 실패하는 테스트 추가** — `tests/test_offers.py` 끝에

```python
from offers import conversion_by_offer_group, offers_per_case


def test_offers_per_case_includes_zero():
    offers = offer_table(_events())
    counts = offers_per_case(offers, pd.Index(["A1", "A2"], name="case:concept:name"))
    assert counts.to_dict() == {"A1": 2, "A2": 0}


def test_conversion_by_offer_group():
    idx = pd.Index(["c1", "c2", "c3", "c4", "c5"], name="case:concept:name")
    outcomes = pd.DataFrame({"reached_pending": [True, False, True, True, False]}, index=idx)
    n_offers = pd.Series([0, 1, 1, 2, 3], index=idx, name="n_offers")
    res = conversion_by_offer_group(outcomes, n_offers)
    assert res.loc["1", "n"] == 2 and res.loc["1", "rate"] == 0.5
    assert res.loc["2+", "n"] == 2 and res.loc["2+", "n_success"] == 1
    assert res.loc["0", "n"] == 1
```

- [ ] **Step 2: 실패 확인**

Run: `.venv\Scripts\python -m pytest tests/test_offers.py -v`
Expected: FAIL — `cannot import name 'conversion_by_offer_group'`

- [ ] **Step 3: analysis/offers.py 끝에 구현 추가**

```python
def offers_per_case(offers: pd.DataFrame, cases: pd.Index) -> pd.Series:
    return (offers.groupby(CASE).size()
            .reindex(cases, fill_value=0)
            .astype(int)
            .rename("n_offers"))


def conversion_by_offer_group(outcomes: pd.DataFrame, n_offers: pd.Series,
                              success_col: str = "reached_pending") -> pd.DataFrame:
    group = pd.cut(n_offers, bins=[-1, 0, 1, float("inf")], labels=["0", "1", "2+"])
    df = pd.DataFrame({"group": group,
                       "success": outcomes[success_col].reindex(n_offers.index).astype(bool)})
    res = df.groupby("group", observed=False)["success"].agg(n="size", n_success="sum")
    res["rate"] = res["n_success"] / res["n"]
    return res
```

- [ ] **Step 4: 통과 확인**

Run: `.venv\Scripts\python -m pytest tests -v`
Expected: 전체 통과 (loader 3, profiling 2, offers 4, outcomes 5 = 14 passed)

- [ ] **Step 5: analysis/03_replicate_prior.py 작성**

```python
"""Phase 0 — reproduce the prior-study figures before building on them.

Targets (CLAUDE.md §3): 8,559 multi-offer vs 22,950 single-offer cases;
conversion 59.0% vs 53.1% (metafinanz p.24/p.28, Badakhshan et al. p.18).
Literature counts success as "case reaches A_Pending" on the full log.

Run from the project root, after 02_case_outcomes.py:

    .venv\\Scripts\\python analysis/03_replicate_prior.py
"""
from __future__ import annotations

import pandas as pd

from config import OUT_DIR
from loader import load_events
from offers import conversion_by_offer_group, offer_table, offers_per_case

LITERATURE = {
    ("1", "n"): 22950, ("2+", "n"): 8559,
    ("1", "rate"): 0.531, ("2+", "rate"): 0.590,
}


def main() -> None:
    ev = load_events()
    oc = pd.read_parquet(OUT_DIR / "p0_case_outcomes.parquet")
    offers = offer_table(ev)
    offers.to_parquet(OUT_DIR / "p0_offers.parquet", index=False)

    n_offers = offers_per_case(offers, oc.index)
    print(f"offers={len(offers):,}  cases with 0 offers={int((n_offers == 0).sum()):,}")
    print(f"\n=== offers per case ===\n{n_offers.value_counts().sort_index().to_string()}")

    oc["success_last"] = oc["outcome"].eq("success")
    n_diff = int((oc["reached_pending"] != oc["success_last"]).sum())
    print(f"\ncases where the two success definitions differ: {n_diff:,}")

    rows = []
    for population, sub in [("full", oc), ("in_window", oc[oc["in_window"]])]:
        for success_col in ["reached_pending", "success_last"]:
            res = conversion_by_offer_group(sub, n_offers.reindex(sub.index), success_col)
            for group, r in res.iterrows():
                rows.append({"population": population, "success_def": success_col,
                             "group": group, "n": int(r["n"]),
                             "n_success": int(r["n_success"]), "rate": round(float(r["rate"]), 4)})
    table = pd.DataFrame(rows)
    table["literature"] = [
        LITERATURE.get((g, "n")) if p == "full" else None
        for p, g in zip(table["population"], table["group"])
    ]
    table["literature_rate"] = [
        LITERATURE.get((g, "rate")) if p == "full" else None
        for p, g in zip(table["population"], table["group"])
    ]
    table.to_csv(OUT_DIR / "p0_replication.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== replication ===\n{table.to_string(index=False)}")

    multi_share = (n_offers >= 2).mean()
    print(f"\nmulti-offer share (full): {multi_share:.1%}  (literature 27%)")


if __name__ == "__main__":
    main()
```

- [ ] **Step 6: 실데이터로 실행하고 판단할 것을 기록**

Run: `.venv\Scripts\python analysis/03_replicate_prior.py`
판단 기준:
- full 모집단에서 건수가 문헌값(22,950 / 8,559)과 같고 성사율이 ±0.5%p 안이면 **재현 성공**으로 기록한다
- 다르면 멈추지 않는다. 원인 후보(오퍼 수를 O_Create Offer로 셀 때와 OfferID 고유값으로 셀 때의 차이, A_Pending 도달 vs 마지막 종료 이벤트)를 확인하고 정의 차이로 기록한 뒤 진행한다 (CLAUDE.md §6 Phase 0 판정)
- in_window 모집단의 성사율 차이(복수 − 단일)를 기록한다 → Phase 6의 출발값
- 두 성공 정의의 차이 건수와 재현 결과를 보고 주 정의 하나를 정한다 → CLAUDE.md §12에 기록하고 Phase 5 p_s에 고정

- [ ] **Step 7: (git 승인 시) 커밋**

```powershell
git add analysis/offers.py analysis/03_replicate_prior.py tests/test_offers.py outputs/p0_replication.csv; git commit -m "feat: reproduce prior single vs multi offer conversion"
```

---

### Task 6: Phase 0 결론 문서와 CLAUDE.md 갱신

**Files:**
- Create: `docs/00_scope.md`
- Modify: `CLAUDE.md` §4, §6 Phase 0, §11, §12

**Interfaces:**
- Consumes: `outputs/p0_attribute_profile.csv`, `p0_system_resource_share.csv`, `p0_end_patterns.csv`, `p0_monthly_completion.csv`, `p0_cutoff.json`, `p0_replication.csv`, 각 스크립트 콘솔 출력
- Produces: Phase 1이 쓰는 모집단 정의(`p0_case_outcomes.parquet`의 `in_window`), 결과 정의, 변수 목록

- [ ] **Step 1: docs/00_scope.md 작성** — 아래 6개 절, 모든 수치 옆에 출처 파일명

```markdown
# Phase 0 — 데이터 확인과 범위 확정

## 1. 분석 모집단
- 전체 케이스 수, 관측 종료 시각 (p0_cutoff.json)
- 컷오프 접수월과 근거: 완료율 0.99 기준 + p90 소요일 추이 (p0_monthly_completion.csv)
- 제외 건수와 비율 (p0_cutoff.json)

## 2. 결과 정의
- 종료 이벤트 패턴별 건수 (p0_end_patterns.csv)
- 복수 종료 이벤트 처리 규칙과 그 이유

## 3. 변수 목록 — 시점 2층 (P2)
| 층 | 속성 | dtype | 결측률 | 0값 비율 | 비고 |
(p0_attribute_profile.csv — 접수 시점 3종 / 처리 중 7종)

## 4. 선행 수치 재현
| 항목 | 문헌 | 재현 (full) | 재현 (in_window) | 차이의 원인 |
(p0_replication.csv)

## 5. 주의점
- CreditScore 0값, RequestedAmount 0값, User_1 비중, Accepted/Selected가 오퍼 생성 시점에 기록된다는 점

## 6. 다음 Phase로 넘기는 것
- 모집단: p0_case_outcomes.parquet 의 in_window == True
- 결과 라벨, 사용 가능한 접수 시점 변수, 복수 오퍼 성사율 차이(in_window)
```

- [ ] **Step 2: CLAUDE.md 갱신**
  - §4: "Phase 0에서 확인할 속성 … 미확인" 블록을 확인된 속성명·결측·0값 요약으로 교체하고, 출처로 `docs/00_scope.md`를 적는다
  - §6 Phase 0: 상태 ⬜ → ✅, "넘기는 것"에 실제 컷오프 월과 모집단 크기를 적는다
  - §11: 해소된 항목에 체크한다
  - §12: 결정 로그에 행을 추가한다 (컷오프 결정, 결과 정의 규칙, 재현 결과, 앞으로의 Phase에 영향을 주는 이상점)

- [ ] **Step 3: 사용자 보고** — 컷오프·제외율·재현 결과·Phase 1에 넘기는 변화를 요약해 보고하고, Phase 1 착수 전에 방향 확인을 받는다

- [ ] **Step 4: (git 승인 시) 커밋**

```powershell
git add docs/00_scope.md CLAUDE.md; git commit -m "docs: record phase 0 scope decisions"
```
