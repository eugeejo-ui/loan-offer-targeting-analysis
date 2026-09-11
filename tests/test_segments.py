import pandas as pd

from segments import amount_band, intake_frame


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
