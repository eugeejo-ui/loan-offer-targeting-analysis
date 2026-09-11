import numpy as np
import pandas as pd

from efficiency import (bootstrap_rank_corr, cm_scan, min_margin_share, quadrant,
                        rank_alignment, targeting_curve, volume_at_effort_share)


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
