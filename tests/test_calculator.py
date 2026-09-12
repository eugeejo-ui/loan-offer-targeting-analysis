import pandas as pd

from calculator import allocation_compare, breakeven_margin_shares, segment_economics, summarise

TABLE = pd.DataFrame({
    "segment": ["big", "small"],
    "n": [100, 300],
    "p": [0.5, 0.4],
    "r_mean": [40000.0, 6000.0],
    "e_mean": [0.8, 0.5],
    "eta": [25000.0, 4800.0],
    "eta_I": [5000.0, 1000.0],
})


def test_segment_economics_sign_flips_at_the_required_margin_share():
    out = segment_economics(TABLE, cost_per_hour=50.0, margin_share=0.02)
    # required share = cost / eta_I -> 1% for "big", 5% for "small"
    assert out.loc[out["segment"] == "big", "required_margin_share"].iloc[0] == 0.01
    assert out.loc[out["segment"] == "small", "required_margin_share"].iloc[0] == 0.05
    assert out.loc[out["segment"] == "big", "ev_per_case"].iloc[0] > 0
    assert out.loc[out["segment"] == "small", "ev_per_case"].iloc[0] < 0

    at_boundary = segment_economics(TABLE, cost_per_hour=50.0, margin_share=0.05)
    assert at_boundary.loc[at_boundary["segment"] == "small", "ev_per_case"].iloc[0] == 0.0
    assert not at_boundary.loc[at_boundary["segment"] == "small", "negative"].iloc[0]


def test_segment_economics_scales_ev_by_cases_and_effort():
    out = segment_economics(TABLE, cost_per_hour=50.0, margin_share=0.02).set_index("segment")
    # (0.02 * 5000 - 50) * 0.8 = 40 per case, x100 cases
    assert out.loc["big", "ev_per_case"] == 40.0
    assert out.loc["big", "ev_total"] == 4000.0


def test_summarise_reports_negative_share_of_cases_and_effort():
    out = summarise(segment_economics(TABLE, cost_per_hour=50.0, margin_share=0.02))
    assert out["negative_segments"] == 1
    assert out["negative_case_share"] == 300 / 400
    # effort = n * e_mean -> 150 of 230
    assert round(out["negative_effort_share"], 6) == round(150 / 230, 6)


def test_breakeven_margin_shares_span_first_and_last_segment():
    out = breakeven_margin_shares(TABLE, cost_per_hour=50.0)
    assert out["first_positive"] == 0.01
    assert out["all_positive"] == 0.05


def test_allocation_compare_prefers_efficiency_order():
    out = allocation_compare(TABLE, effort_budget_share=0.5)
    assert out["volume_by_eta"] >= out["volume_by_success_rate"]
    assert round(out["gain"], 9) == round(out["volume_by_eta"] / out["volume_by_success_rate"] - 1, 9)
