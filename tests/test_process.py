import pandas as pd

from process import (cancel_after_last_sent, classify_abort_context,
                     funnel_by_outcome, group_holder_summary, holder_time,
                     last_milestone_before_end, milestone_first_ts, nearest_case_events,
                     pair_durations)

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


def test_holder_time_splits_bank_and_customer():
    h = holder_time(_events())
    assert h.loc["S", "bank_days"] == 3 and h.loc["S", "customer_days"] == 13
    assert h.loc["C", "bank_days"] == 2 and h.loc["C", "customer_days"] == 30


def test_cancel_after_last_sent():
    c = cancel_after_last_sent(_events())
    assert list(c.index) == ["C"]
    assert c.loc["C", "gap_days"] == 30
    assert bool(c.loc["C", "cancel_by_system"]) is True


def test_nearest_case_events_and_classification():
    context = _ev([
        ("S", "O_Returned", T0 - pd.Timedelta(seconds=10), "User_5"),
        ("S", "A_Validating", T0 + pd.Timedelta(seconds=1), "User_5"),
        ("C", "A_Cancelled", T0 + 10 * DAY, "User_1"),
    ])
    anchors = pd.DataFrame({
        "case:concept:name": ["S", "C", "C"],
        "time:timestamp": [T0, T0 + 10 * DAY + pd.Timedelta(seconds=2), T0 + 3 * DAY],
    })
    near = nearest_case_events(anchors, context)
    assert near.loc[0, "next_act"] == "A_Validating" and near.loc[0, "next_gap_s"] == 1
    assert near.loc[1, "prev_act"] == "A_Cancelled"
    cls = classify_abort_context(near, window_s=60)
    assert list(cls) == ["case_moved_to_validation", "case_closed", "no_adjacent_transition"]


def test_classify_treats_offer_cancellation_as_closure():
    context = _ev([
        ("C", "A_Cancelled", T0, "User_1"),
        ("C", "O_Cancelled", T0 + pd.Timedelta(minutes=5), "User_1"),
    ])
    anchors = pd.DataFrame({"case:concept:name": ["C"],
                            "time:timestamp": [T0 + pd.Timedelta(minutes=5, seconds=1)]})
    cls = classify_abort_context(nearest_case_events(anchors, context), window_s=60)
    assert list(cls) == ["case_closed"]


def test_group_holder_summary():
    held = pd.DataFrame({"bank_days": [1.0, 3.0, 2.0], "customer_days": [3.0, 1.0, 2.0]},
                        index=["a", "b", "c"])
    group = pd.Series({"a": "g1", "b": "g1", "c": "g2"})
    effort = pd.Series({"a": 2.4, "b": 7.2, "c": 4.8})
    out = group_holder_summary(held, group, effort)
    assert out.loc["g1", "n"] == 2 and out.loc["g1", "customer_share"] == 0.5
    assert out.loc["g1", "bank_days_median"] == 2.0
    assert round(out.loc["g1", "bank_active_share_median"], 6) == 0.1
    assert out.loc["g2", "customer_share"] == 0.5
