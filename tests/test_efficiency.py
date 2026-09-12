import numpy as np
import pandas as pd

from efficiency import (bootstrap_rank_corr, cm_scan, incremental_eta, margin_share_spread, min_margin_share,
                        quadrant, rank_alignment, rank_corr_interval, stratified_diff, targeting_curve,
                        volume_at_effort_share)


def _table():
    return pd.DataFrame({"n": [10, 10], "p": [0.5, 0.5], "r_mean": [100.0, 10.0],
                         "e_mean": [1.0, 1.0], "eta": [50.0, 5.0], "eta_I": [100.0, 50.0]},
                        index=pd.Index(["A", "B"], name="segment"))


def test_rank_alignment_gap():
    t = pd.DataFrame({"p": [0.9, 0.5, 0.1], "eta": [1.0, 2.0, 3.0]}, index=list("xyz"))
    out = rank_alignment(t)
    assert list(out["rank_p"]) == [1, 2, 3] and list(out["rank_eta"]) == [3, 2, 1]
    assert list(out["rank_gap"]) == [-2, 0, 2]


def test_quadrant_labels():
    t = pd.DataFrame({"p": [0.9, 0.9, 0.1, 0.1], "eta": [9.0, 1.0, 9.0, 1.0]}, index=list("abcd"))
    assert list(quadrant(t)) == ["성사율↑·효율↑", "성사율↑·효율↓", "성사율↓·효율↑", "성사율↓·효율↓"]


def test_cm_scan_counts_negative_segments():
    scan = cm_scan(_table(), [1.0, 10.0, 60.0])
    assert list(scan["negative_segments"]) == [0, 1, 2]
    assert list(scan["application_share"]) == [0.0, 0.5, 1.0]


def test_min_margin_share():
    assert list(min_margin_share(_table(), cost=10.0)) == [0.1, 0.2]


def test_targeting_curve_and_volume_at_budget():
    curve = targeting_curve(_table(), "eta")
    assert list(curve["segment"]) == ["A", "B"]
    assert list(curve["volume"]) == [500.0, 550.0]
    assert volume_at_effort_share(curve, 0.5) == 500.0
    assert volume_at_effort_share(curve, 0.25) == 250.0


def test_targeting_order_matters():
    curve = targeting_curve(_table(), "r_mean")
    assert volume_at_effort_share(curve, 0.5) == 500.0
    reverse = targeting_curve(_table().assign(neg=[-1, 1]), "neg")
    assert volume_at_effort_share(reverse, 0.5) == 50.0


def test_bootstrap_rank_corr_shape_and_bounds():
    rng = np.random.default_rng(1)
    frame = pd.DataFrame({
        "seg": np.repeat(list("abcd"), 50),
        "reached_pending": rng.random(200) < np.repeat([0.2, 0.4, 0.6, 0.8], 50),
        "r": np.repeat([10.0, 20.0, 30.0, 40.0], 50),
        "e": np.ones(200),
    })
    rhos = bootstrap_rank_corr(frame, "seg", "r", "e", n_boot=10)
    assert len(rhos) == 10
    assert np.all((rhos >= -1) & (rhos <= 1))


def test_rank_corr_interval_one_row_per_seed_matching_direct_quantiles():
    rng = np.random.default_rng(2)
    frame = pd.DataFrame({
        "seg": np.repeat(list("abcd"), 40),
        "reached_pending": rng.random(160) < 0.5,
        "r": rng.uniform(1, 10, 160),
        "e": rng.uniform(0.5, 2, 160),
    })
    out = rank_corr_interval(frame, "seg", "r", "e", n_boot=20, seeds=[0, 1])
    assert list(out["seed"]) == [0, 1]
    assert (out["rho_ci_lo"] <= out["rho_ci_hi"]).all()
    lo, hi = np.nanquantile(bootstrap_rank_corr(frame, "seg", "r", "e", n_boot=20, seed=1), [0.05, 0.95])
    assert out.loc[1, "rho_ci_lo"] == lo and out.loc[1, "rho_ci_hi"] == hi


def test_margin_share_spread_divides_before_rounding():
    table = pd.DataFrame({"eta_I": [9857.5807, 724.3395]}, index=["big", "small"])
    out = margin_share_spread(table, cost_per_hour=57.6)
    assert round(out["best"], 9) == round(57.6 / 9857.5807, 9)
    assert round(out["worst"], 9) == round(57.6 / 724.3395, 9)
    # rounding the shares to 4 decimals first (0.0795 / 0.0058) would report 13.7
    assert round(out["ratio"], 2) == 13.61


def test_stratified_diff_weights_by_stratum_size():
    frame = pd.DataFrame({
        "s": ["a"] * 8 + ["b"] * 4,
        "g": ["base"] * 4 + ["other"] * 4 + ["base"] * 2 + ["other"] * 2,
        "v": [0, 0, 1, 1, 1, 1, 1, 0, 0, 0, 0, 1],
    })
    diff, table = stratified_diff(frame, "g", "base", "other", "s", "v", min_n=2)
    assert list(table["diff"]) == [0.25, 0.5]
    assert round(diff, 6) == round((0.25 * 8 + 0.5 * 4) / 12, 6)


def test_incremental_eta_and_class():
    frame = pd.DataFrame({
        "s": ["x"] * 4,
        "g": ["base", "base", "other", "other"],
        "reached_pending": [True, True, True, True],
        "r": [100.0, 100.0, 150.0, 150.0],
        "e": [1.0, 1.0, 2.0, 2.0],
    })
    inc = incremental_eta(frame, "g", "base", "other", "s", "r", "e", min_n=2)
    assert inc.loc["x", "eta_base"] == 100.0
    assert inc.loc["x", "incremental_eta"] == 50.0
    assert inc.loc["x", "class"] == "공수↑·가치↑"


def test_incremental_eta_flags_reversal():
    frame = pd.DataFrame({
        "s": ["x"] * 4, "g": ["base", "base", "other", "other"],
        "reached_pending": [True, True, True, False],
        "r": [100.0, 100.0, 100.0, np.nan], "e": [1.0, 1.0, 2.0, 2.0],
    })
    assert incremental_eta(frame, "g", "base", "other", "s", "r", "e", min_n=2).loc["x", "class"] == "공수↑·가치↓"
