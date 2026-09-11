import pandas as pd

from process import (funnel_by_outcome, last_milestone_before_end,
                     milestone_first_ts, pair_durations)

DAY = pd.Timedelta(days=1)
T0 = pd.Timestamp("2016-01-01", tz="UTC")


def _ev(rows):
    return pd.DataFrame(rows, columns=["case:concept:name", "concept:name",
                                       "time:timestamp", "org:resource"])


def _events():
    return _ev([
        ("S", "A_Create Application", T0, "User_1"),
        ("S", "O_Sent (online only)", T0 + 1 * DAY, "User_5"),
        ("S", "O_Returned", T0 + 11 * DAY, "User_5"),
        ("S", "A_Validating", T0 + 11 * DAY, "User_5"),
        ("S", "A_Incomplete", T0 + 12 * DAY, "User_5"),
        ("S", "A_Validating", T0 + 15 * DAY, "User_5"),
        ("S", "A_Pending", T0 + 16 * DAY, "User_5"),
        ("C", "A_Create Application", T0, "User_1"),
        ("C", "O_Sent (mail and online)", T0 + 2 * DAY, "User_7"),
        ("C", "A_Cancelled", T0 + 32 * DAY, "User_1"),
    ])


def test_milestone_first_ts_merges_sent_variants():
    ft = milestone_first_ts(_events())
    assert ft.loc["S", "O_Sent"] == T0 + DAY
    assert ft.loc["C", "O_Sent"] == T0 + 2 * DAY
    assert pd.isna(ft.loc["C", "O_Returned"])
    assert list(ft.columns).index("O_Sent") < list(ft.columns).index("O_Returned")


def test_funnel_by_outcome():
    ft = milestone_first_ts(_events())
    f = funnel_by_outcome(ft, pd.Series({"S": "success", "C": "cancelled"}))
    assert f.loc["O_Sent", "all"] == 2
    assert f.loc["O_Returned", "success"] == 1 and f.loc["O_Returned", "cancelled"] == 0


def test_last_milestone_before_end():
    last = last_milestone_before_end(milestone_first_ts(_events()))
    assert last["C"] == "O_Sent"
    assert last["S"] == "A_Incomplete"


def test_pair_durations_in_days():
    d = pair_durations(milestone_first_ts(_events()), [("O_Sent", "O_Returned")])
    assert d.loc["S", "O_Sent→O_Returned"] == 10
    assert pd.isna(d.loc["C", "O_Sent→O_Returned"])
