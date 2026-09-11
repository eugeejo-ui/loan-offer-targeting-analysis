"""Phase 0 — confirm attribute names, missingness and zero values.

Run from the project root:

    .venv\\Scripts\\python analysis/01_inspect_schema.py
"""
from __future__ import annotations

import pandas as pd

from config import (ACT, ACTION, CASE, INTAKE_ATTRS, LIFECYCLE, OFFER_ATTRS, ORIGIN,
                    OUT_DIR, RESOURCE, SYSTEM_RESOURCE)
from loader import load_events
from offers import CREATE_OFFER, offer_final_state, offer_table, unlinked_offer_ids
from profiling import attribute_profile, constant_within_case


def main() -> None:
    OUT_DIR.mkdir(exist_ok=True)
    ev = load_events()
    intake = [c for c in INTAKE_ATTRS if c in ev.columns]
    missing = sorted(set(INTAKE_ATTRS) - set(intake))
    print(f"intake attributes missing from log: {missing or 'none'}")
    print("intake attributes constant within every case:",
          constant_within_case(ev, CASE, intake).to_dict())

    cases = ev.groupby(CASE)[intake].first()
    offers = offer_table(ev)
    profile = pd.concat([
        attribute_profile(cases, INTAKE_ATTRS).assign(level="case"),
        attribute_profile(offers, OFFER_ATTRS).assign(level="offer"),
    ], ignore_index=True)
    profile.to_csv(OUT_DIR / "p0_attribute_profile.csv", index=False, encoding="utf-8-sig")
    print("\n=== attribute profile ===")
    print(profile.to_string(index=False))

    acts = ev[ACT].value_counts().rename_axis("activity").reset_index(name="events")
    acts.to_csv(OUT_DIR / "p0_activity_counts.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== activities ({len(acts)}) ===\n{acts.to_string(index=False)}")
    print(f"\n=== lifecycle ===\n{ev[LIFECYCLE].value_counts().to_string()}")

    system = (ev[RESOURCE] == SYSTEM_RESOURCE).groupby(ev[ORIGIN]).agg(["sum", "mean"])
    system["mean"] = (system["mean"] * 100).round(1)
    system.columns = ["system_events", "system_pct"]
    system.to_csv(OUT_DIR / "p0_system_resource_share.csv", encoding="utf-8-sig")
    print(f"\n=== {SYSTEM_RESOURCE} share by EventOrigin ===\n{system.to_string()}")

    for col in intake[1:]:
        print(f"\n{col}:\n{cases[col].value_counts(dropna=False).to_string()}")
    print(f"\noffers={len(offers):,}  unlinked OfferIDs={len(unlinked_offer_ids(ev, offers))}")

    # Can offer creation tell a customer-requested offer from a bank-initiated one?
    created = ev[ev[ACT] == CREATE_OFFER]
    by_actor = (created[RESOURCE] == SYSTEM_RESOURCE).map({True: SYSTEM_RESOURCE, False: "staff"})
    creation = pd.concat([
        created[ACTION].value_counts().rename_axis("value").reset_index(name="events").assign(field=ACTION),
        by_actor.value_counts().rename_axis("value").reset_index(name="events").assign(field="resource"),
    ], ignore_index=True)
    creation.to_csv(OUT_DIR / "p0_offer_creation_actions.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== {CREATE_OFFER}: Action / resource ===\n{creation.to_string(index=False)}")
    print(f"distinct resources creating offers: {created[RESOURCE].nunique()}")

    # CreditScore is zero for most offers and Selected/Accepted are set at creation:
    # compare them across each offer's final state before trusting them anywhere.
    offers["final_state"] = offers["offer_id"].map(offer_final_state(ev)).fillna("none")
    by_state = offers.groupby("final_state").agg(
        offers=("offer_id", "size"),
        credit_score_nonzero_pct=("CreditScore", lambda s: round(float((s > 0).mean()) * 100, 1)),
        selected_true_pct=("Selected", lambda s: round(float(s.astype(float).mean()) * 100, 1)),
        accepted_true_pct=("Accepted", lambda s: round(float(s.astype(float).mean()) * 100, 1)),
    )
    by_state.to_csv(OUT_DIR / "p0_offer_attrs_by_final_state.csv", encoding="utf-8-sig")
    print(f"\n=== offer attributes by final offer state ===\n{by_state.to_string()}")

    zero_req = (cases["case:RequestedAmount"] == 0).groupby(cases["case:ApplicationType"]).agg(["sum", "mean"])
    zero_req.columns = ["zero_requested", "zero_requested_share"]
    zero_req.to_csv(OUT_DIR / "p0_requested_amount_zero.csv", encoding="utf-8-sig")
    print(f"\n=== RequestedAmount == 0 by ApplicationType ===\n{zero_req.to_string()}")


if __name__ == "__main__":
    main()
