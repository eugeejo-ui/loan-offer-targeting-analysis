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
