import json

import pandas as pd

from dashboard import build_payload

FRAMES = {
    "efficiency": pd.DataFrame({
        "segment": ["(25000.0, 450000.0] | 한도 증액", "금액 미기재 | 신규·A_Submitted 없음 | 용도 불명"],
        "n": [762, 410],
        "p": [0.748, 0.739],
        "r_mean": [39050.35, 23954.46],
        "e_mean": [0.6857, 0.5647],
        "eta": [42602.59, 31347.63],
        "eta_I": [9857.58, 7380.73],
        "rank_p": [2, 3],
        "rank_eta": [1, 5],
        "rank_gap": [1, -2],
    }),
    "alignment": pd.DataFrame({"combo": ["amount_effort"], "rho_p_eta": [0.669],
                               "rho_ci_lo": [0.610], "rho_ci_hi": [0.692]}),
    "targeting": pd.DataFrame({"effort_budget_share": [0.25, 0.5, 0.75],
                               "volume_by_success_rate": [1.07e8, 1.8616e8, 2.4812e8],
                               "volume_by_eta": [1.299e8, 2.108e8, 2.6588e8],
                               "eta_order_gain": [0.214, 0.1323, 0.0716]}),
    "meta": {"reference_cost_eur_per_hour": 57.6, "reference_cost_source": "Eurostat", "segments": 39},
}


def test_build_payload_is_json_serialisable_with_plain_types():
    payload = build_payload(FRAMES)
    text = json.dumps(payload, ensure_ascii=False)
    assert "numpy" not in text
    assert json.loads(text)["alignment"]["rho"] == 0.669


def test_build_payload_sorts_segments_by_efficiency_and_labels_them():
    payload = build_payload(FRAMES)
    segments = payload["segments"]
    assert [s["eta"] for s in segments] == sorted((s["eta"] for s in segments), reverse=True)
    assert segments[0]["label"] == "25,000 초과 · 한도 증액"
    assert segments[1]["label"] == "금액 미기재 · 신규·A_Submitted 없음 · 용도 불명"


def test_build_payload_carries_the_allocation_rows_and_reference_cost():
    payload = build_payload(FRAMES)
    assert [row["budget"] for row in payload["allocation"]] == [25, 50, 75]
    assert payload["allocation"][1]["gain"] == 0.1323
    assert payload["reference_cost"] == 57.6
