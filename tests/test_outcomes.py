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
