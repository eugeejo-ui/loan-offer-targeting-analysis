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
    assert round(res["rate_ratio"], 9) == 3.0 and res["ci_separated"]
    assert res["top_quartile_effort_share"] == 60.0 / 90.0 and res["identifiable"]
    flat = table.assign(k=[110, 100, 100, 100])
    assert not screen_failure_rates(flat)["identifiable"]
