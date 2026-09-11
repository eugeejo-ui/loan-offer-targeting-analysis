import pandas as pd

from effort import (active_segments, activity_caps, cap_hours, case_effort,
                    staff_event_counts)

H = pd.Timedelta(hours=1)
T0 = pd.Timestamp("2016-01-01 09:00", tz="UTC")
CASES = pd.Index(["A", "B"], name="case:concept:name")


def _events():
    rows = [
        ("A", "W_Call after offers", "schedule", T0, "User_1"),
        ("A", "W_Call after offers", "start", T0 + 1 * H, "User_5"),
        ("A", "W_Call after offers", "suspend", T0 + 1.1 * H, "User_5"),
        ("A", "W_Call after offers", "resume", T0 + 5 * H, "User_5"),
        ("A", "W_Call after offers", "complete", T0 + 5.2 * H, "User_5"),
        ("A", "W_Validate application", "start", T0 + 6 * H, "User_6"),
        ("A", "A_Validating", "complete", T0 + 6 * H, "User_6"),
        ("B", "A_Create Application", "complete", T0, "User_1"),
    ]
    return pd.DataFrame(rows, columns=["case:concept:name", "concept:name",
                                       "lifecycle:transition", "time:timestamp", "org:resource"])


def test_active_segments_pair_start_resume_with_next_event():
    seg = active_segments(_events())
    assert list(seg["hours"].round(6)) == [0.1, 0.2]
    assert list(seg["end_lifecycle"]) == ["suspend", "complete"]


def test_cap_hours_fixed_and_per_activity():
    seg = active_segments(_events())
    assert list(cap_hours(seg, 0.15).round(6)) == [0.1, 0.15]
    assert list(cap_hours(seg, pd.Series({"W_Call after offers": 0.05})).round(6)) == [0.05, 0.05]


def test_activity_caps_quantile():
    caps = activity_caps(active_segments(_events()), q=1.0)
    assert round(caps["W_Call after offers"], 6) == 0.2


def test_case_effort_includes_cases_without_work_items():
    seg = active_segments(_events())
    eff = case_effort(seg, seg["hours"], CASES)
    assert round(eff.loc["A", "effort_hours"], 6) == 0.3
    assert round(eff.loc["A", "W_Call after offers"], 6) == 0.3
    assert eff.loc["B", "effort_hours"] == 0


def test_staff_event_counts_excludes_system_account():
    assert staff_event_counts(_events(), CASES).to_dict() == {"A": 6, "B": 0}
