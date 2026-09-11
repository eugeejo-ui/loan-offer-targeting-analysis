import pandas as pd

from segments import amount_band, build_segments, channel, goal_group, intake_frame, screen_axis


def test_intake_frame_flags_submitted():
    ev = pd.DataFrame({
        "case:concept:name": ["a", "a", "b"],
        "concept:name": ["A_Create Application", "A_Submitted", "A_Create Application"],
        "case:RequestedAmount": [1000.0, 1000.0, 0.0],
        "case:LoanGoal": ["Car", "Car", "Boat"],
        "case:ApplicationType": ["New credit", "New credit", "Limit raise"],
    })
    f = intake_frame(ev)
    assert bool(f.loc["a", "has_submitted"]) and not bool(f.loc["b", "has_submitted"])
    assert f.loc["b", "case:LoanGoal"] == "Boat"


def test_amount_band_keeps_zero_separate():
    b = amount_band(pd.Series([0, 100, 200, 300, 400], index=list("abcde"), dtype=float), q=2)
    assert b["a"] == "0 (미기재)"
    assert b["b"] == b["c"] and b["d"] == b["e"] and b["b"] != b["d"]


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
