"""Offer-level views. Offer attributes live only on O_Create Offer events;
that event's EventID is the offer key that later OfferID values point to."""
from __future__ import annotations

import pandas as pd

from config import ACT, CASE, EVENT_ID, OFFER_ATTRS, OFFER_ID, TS

CREATE_OFFER = "O_Create Offer"
FINAL_STATES = ("O_Accepted", "O_Refused", "O_Cancelled")


def offer_final_state(events: pd.DataFrame) -> pd.Series:
    """Last terminal state per offer, indexed by offer id."""
    final = events[events[ACT].isin(FINAL_STATES)].sort_values(TS, kind="stable")
    return final.groupby(OFFER_ID)[ACT].last()


def offer_table(events: pd.DataFrame) -> pd.DataFrame:
    created = events[events[ACT] == CREATE_OFFER]
    cols = [CASE, EVENT_ID, TS] + [c for c in OFFER_ATTRS if c in created.columns]
    return (created[cols]
            .rename(columns={EVENT_ID: "offer_id", TS: "created_ts"})
            .reset_index(drop=True))


def unlinked_offer_ids(events: pd.DataFrame, offers: pd.DataFrame) -> set[str]:
    referenced = set(events[OFFER_ID].dropna().unique())
    return referenced - set(offers["offer_id"])


def offers_per_case(offers: pd.DataFrame, cases: pd.Index) -> pd.Series:
    return (offers.groupby(CASE).size()
            .reindex(cases, fill_value=0)
            .astype(int)
            .rename("n_offers"))


def conversion_by_offer_group(outcomes: pd.DataFrame, n_offers: pd.Series,
                              success_col: str = "reached_pending") -> pd.DataFrame:
    group = pd.cut(n_offers, bins=[-1, 0, 1, float("inf")], labels=["0", "1", "2+"])
    df = pd.DataFrame({"group": group,
                       "success": outcomes[success_col].reindex(n_offers.index).astype(bool)})
    res = df.groupby("group", observed=False)["success"].agg(n="size", n_success="sum")
    res["rate"] = res["n_success"] / res["n"]
    return res


SENT_ACTIVITIES = ("O_Sent (mail and online)", "O_Sent (online only)")


def offer_first_sent(events: pd.DataFrame) -> pd.Series:
    sent = events[events[ACT].isin(SENT_ACTIVITIES)]
    return sent.groupby(OFFER_ID)[TS].min().rename("first_sent")


def conversation_split(offers: pd.DataFrame, first_sent: pd.Series, same_day: float = 1.0) -> pd.DataFrame:
    """Per case: offer count and whether extra offers came in a later conversation.

    d1_later: offers created more than `same_day` days apart.
    d2_later: an offer was created after the case's first offer had been sent.
    """
    o = offers.assign(first_sent=offers["offer_id"].map(first_sent))
    g = o.groupby(CASE)
    out = pd.DataFrame({
        "n_offers": g.size(),
        "span_days": (g["created_ts"].max() - g["created_ts"].min()).dt.total_seconds() / 86400,
        "first_sent": g["first_sent"].min(),
        "last_created": g["created_ts"].max(),
    })
    multi = out["n_offers"] >= 2
    out["d1_later"] = multi & (out["span_days"] > same_day)
    out["d2_later"] = multi & (out["last_created"] > out["first_sent"])
    return out.drop(columns=["first_sent", "last_created"])


def offer_group(split: pd.DataFrame, later_col: str) -> pd.Series:
    multi = split["n_offers"] >= 2
    label = pd.Series("single", index=split.index)
    return label.mask(multi & ~split[later_col], "multi_same").mask(split[later_col], "multi_later")
