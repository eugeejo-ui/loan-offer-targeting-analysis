import numpy as np
import pandas as pd

from value import accepted_offers, group_eta, implied_annual_rate, revenue_bases

CASE = "case:concept:name"


def test_accepted_offers_takes_terms_from_offer_table():
    ev = pd.DataFrame({CASE: ["A", "A", "B"],
                       "concept:name": ["O_Create Offer", "O_Accepted", "O_Create Offer"],
                       "OfferID": [None, "Offer_1", None]})
    offers = pd.DataFrame({"offer_id": ["Offer_1", "Offer_2"], "OfferedAmount": [10000.0, 5000.0],
                           "NumberOfTerms": [60.0, 24.0], "MonthlyCost": [200.0, 230.0]})
    acc = accepted_offers(ev, offers)
    assert list(acc.index) == ["A"]
    assert acc.loc["A", "OfferedAmount"] == 10000 and acc.loc["A", "n_accepted"] == 1


def test_implied_annual_rate_recovers_known_rate():
    monthly_r = 1.05 ** (1 / 12) - 1
    payment = 10000 * monthly_r / (1 - (1 + monthly_r) ** -60)
    rate = implied_annual_rate([10000, 10000], [payment, 100], [60, 60])
    assert abs(rate[0] - 0.05) < 1e-6
    assert np.isnan(rate[1])


def test_revenue_bases():
    acc = pd.DataFrame({"OfferedAmount": [12000.0], "NumberOfTerms": [24.0], "MonthlyCost": [550.0]},
                       index=pd.Index(["A"], name=CASE))
    rb = revenue_bases(acc)
    assert rb.loc["A", "r_amount"] == 12000
    assert rb.loc["A", "r_amount_years"] == 24000
    assert rb.loc["A", "interest_total"] == 1200


def test_group_eta_uses_success_mean_r_and_all_case_effort():
    frame = pd.DataFrame({"g": ["x", "x", "y", "y"], "reached_pending": [True, False, True, True],
                          "r": [10.0, np.nan, 20.0, 40.0], "e": [1.0, 3.0, 2.0, 2.0]})
    out = group_eta(frame, "g", "r", "e")
    assert out.loc["x", "eta"] == 10 * 0.5 / 2.0
    assert out.loc["y", "eta"] == 30 * 1.0 / 2.0
