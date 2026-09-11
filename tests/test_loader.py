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
