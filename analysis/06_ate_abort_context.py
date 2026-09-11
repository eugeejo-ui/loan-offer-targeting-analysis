"""Phase 1 — which case transition sits next to a customer-contact work item's ate_abort.

The log has no call outcome codes, so this cannot say WHY a call item was
aborted; it only shows the adjacent case transition.

Run from the project root:

    .venv\\Scripts\\python analysis/06_ate_abort_context.py
"""
from __future__ import annotations

import pandas as pd

from config import ACT, LIFECYCLE, OUT_DIR
from loader import load_population
from process import classify_abort_context, nearest_case_events

CONTACT_ACTIVITIES = ["W_Call after offers", "W_Call incomplete files"]
WINDOW_S = 60.0


def main() -> None:
    ev, _ = load_population()
    aborts = ev[ev[ACT].isin(CONTACT_ACTIVITIES) & (ev[LIFECYCLE] == "ate_abort")].reset_index(drop=True)
    context = ev[ev[ACT].str.startswith(("A_", "O_"))]
    near = nearest_case_events(aborts, context)
    near["context"] = classify_abort_context(near, WINDOW_S)
    near["activity"] = aborts[ACT].to_numpy()

    table = pd.crosstab(near["activity"], near["context"], margins=True)
    table.to_csv(OUT_DIR / "p1_ate_abort_context.csv", encoding="utf-8-sig")
    print(f"=== ate_abort of contact work items: adjacent case transition (±{WINDOW_S:.0f}s) ===")
    print(table.to_string())
    print(f"\n{pd.crosstab(near['activity'], near['context'], normalize='index').round(3).to_string()}")
    moved = near[near["context"] == "case_moved_to_validation"]
    print(f"\nevent just before 'moved' aborts:\n{moved['prev_act'].value_counts().head(5).to_string()}")

    rest = near[near["context"] == "no_adjacent_transition"].copy()
    rest["prev_gap_h"] = rest["prev_gap_s"] / 3600
    rest["next_gap_h"] = rest["next_gap_s"] / 3600
    rest_prev = (rest.groupby("activity")["prev_act"].value_counts()
                 .groupby(level=0).head(4).rename("aborts").reset_index())
    rest_prev.to_csv(OUT_DIR / "p1_ate_abort_unmatched_prev.csv", index=False, encoding="utf-8-sig")
    print(f"\n=== aborts with no adjacent transition: previous case event ===\n{rest_prev.to_string(index=False)}")
    print(f"\nshare with no later case event: "
          f"{rest.groupby('activity')['next_act'].apply(lambda s: s.isna().mean()).round(3).to_dict()}")
    print(f"median hours since previous case event: "
          f"{rest.groupby('activity')['prev_gap_h'].median().round(1).to_dict()}")


if __name__ == "__main__":
    main()
