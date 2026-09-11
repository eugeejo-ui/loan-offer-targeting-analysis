import pandas as pd

from offers import (conversation_split, conversion_by_offer_group, offer_final_state,
                    offer_first_sent, offer_group, offer_table, offers_per_case,
                    unlinked_offer_ids)


def _events():
    return pd.DataFrame({
        "case:concept:name": ["A1", "A1", "A1", "A2"],
        "concept:name": ["O_Create Offer", "O_Created", "O_Create Offer", "O_Created"],
        "EventID": ["Offer_1", "OfferState_9", "Offer_2", "OfferState_8"],
        "OfferID": [None, "Offer_1", None, "Offer_99"],
        "time:timestamp": pd.to_datetime(["2016-01-01", "2016-01-01", "2016-01-05", "2016-01-02"], utc=True),
        "OfferedAmount": [5000.0, None, 7000.0, None],
        "CreditScore": [0, None, 900, None],
    })


def test_offer_table_one_row_per_created_offer():
    offers = offer_table(_events())
    assert list(offers["offer_id"]) == ["Offer_1", "Offer_2"]
    assert list(offers["OfferedAmount"]) == [5000.0, 7000.0]
    assert "created_ts" in offers.columns


def test_unlinked_offer_ids():
    ev = _events()
    assert unlinked_offer_ids(ev, offer_table(ev)) == {"Offer_99"}


def test_offer_final_state_takes_last_terminal_event():
    ev = pd.DataFrame({
        "concept:name": ["O_Create Offer", "O_Sent (mail and online)", "O_Cancelled",
                         "O_Accepted", "O_Create Offer"],
        "OfferID": [None, "Offer_1", "Offer_1", "Offer_2", None],
        "time:timestamp": pd.to_datetime(
            ["2016-01-01", "2016-01-02", "2016-01-03", "2016-01-04", "2016-01-05"], utc=True),
    })
    assert offer_final_state(ev).to_dict() == {"Offer_1": "O_Cancelled", "Offer_2": "O_Accepted"}


def test_offers_per_case_includes_zero():
    offers = offer_table(_events())
    counts = offers_per_case(offers, pd.Index(["A1", "A2"], name="case:concept:name"))
    assert counts.to_dict() == {"A1": 2, "A2": 0}


def test_conversion_by_offer_group():
    idx = pd.Index(["c1", "c2", "c3", "c4", "c5"], name="case:concept:name")
    outcomes = pd.DataFrame({"reached_pending": [True, False, True, True, False]}, index=idx)
    n_offers = pd.Series([0, 1, 1, 2, 3], index=idx, name="n_offers")
    res = conversion_by_offer_group(outcomes, n_offers)
    assert res.loc["1", "n"] == 2 and res.loc["1", "rate"] == 0.5
    assert res.loc["2+", "n"] == 2 and res.loc["2+", "n_success"] == 1
    assert res.loc["0", "n"] == 1


def test_offer_first_sent_takes_earliest_send():
    ev = pd.DataFrame({
        "concept:name": ["O_Sent (mail and online)", "O_Sent (online only)", "O_Created"],
        "OfferID": ["Offer_1", "Offer_1", "Offer_2"],
        "time:timestamp": pd.to_datetime(["2016-01-03", "2016-01-02", "2016-01-01"], utc=True),
    })
    assert offer_first_sent(ev).to_dict() == {"Offer_1": pd.Timestamp("2016-01-02", tz="UTC")}


def test_conversation_split_and_group():
    ts = lambda d: pd.Timestamp(d, tz="UTC")  # noqa: E731
    offers = pd.DataFrame({
        "case:concept:name": ["S", "M", "M", "L", "L"],
        "offer_id": ["o1", "o2", "o3", "o4", "o5"],
        "created_ts": [ts("2016-01-01"), ts("2016-01-01 10:00"), ts("2016-01-01 11:00"),
                       ts("2016-01-01"), ts("2016-01-05")],
    })
    first_sent = pd.Series({"o1": ts("2016-01-02"), "o2": ts("2016-01-02"), "o4": ts("2016-01-02")})
    split = conversation_split(offers, first_sent)
    assert split.loc["S", "n_offers"] == 1 and not split.loc["S", "d1_later"]
    assert not split.loc["M", "d1_later"] and not split.loc["M", "d2_later"]
    assert split.loc["L", "d1_later"] and split.loc["L", "d2_later"]
    assert offer_group(split, "d1_later").to_dict() == {"L": "multi_later", "M": "multi_same", "S": "single"}
