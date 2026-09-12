> English · [한국어](05_expected_value.md)

# Phase 5 — Efficiency per segment

> 2026-09-11 · plan and record [`plans/phase-05-efficiency.md`](plans/phase-05-efficiency.md) · scripts `analysis/13~14` · 39 segments (at least 300 applications each, 28,243 in total)

Segment labels keep their Korean form in the data. In this document they read: **amount not stated** (금액 미기재), **new credit · A_Submitted present / absent** (신규·A_Submitted 있음/없음), **limit raise** (한도 증액), **purpose not stated** (용도 불명), **other** (기타).

## Summary — the answer to the core question

**"Are the applications most likely to convert the same ones worth the effort?" → No.**

- Across 39 segments, **the rank correlation between conversion rate and efficiency (η) is 0.669**. The bootstrap 90% interval (0.610–0.692) stays below the 0.7 decision boundary.
- The direction of the mismatch is clear: **small and mid-sized applications convert well but run at low efficiency, while large new-credit applications convert poorly and run at high efficiency.**
- Spending the same effort in η order rather than conversion order yields **13.2% more loan volume** at half the effort budget (hypothetical reallocation).
- At the reference labour cost (EUR 57.6 per hour) every segment is profitable. The least favourable one breaks even once net margin reaches **7.95%** of total interest. The conclusion is therefore not a sign flip but an **efficiency gap**: the required margin share differs **13.7x** between segments, and that ratio does not depend on the cost assumption.

The structure mirrors the earlier subscription analysis, where the target turned out to be light buyers rather than heavy ones. Here effort belongs first with **large applications rather than likely ones**.

## 1. Conversion rank vs η rank

`outputs/p5_rank_alignment.csv` (Spearman, 39 segments):

| R × E combination | ρ(conversion, η) | ρ(conversion, R̄) | ρ(conversion, Ē) |
|---|---|---|---|
| **Accepted amount × active time (primary)** | **0.669** (90% interval 0.610–0.692) | 0.454 | 0.219 |
| Amount × term × active time | 0.685 | 0.533 | 0.219 |
| Accepted amount × event count | 0.596 | 0.454 | 0.661 |
| Amount × term × event count | 0.613 | 0.533 | 0.661 |

(The interval comes from 2,000 bootstrap draws at seed 0. Across seeds 0–4 the lower bound runs 0.607–0.610 and the upper bound 0.692–0.694, below the 0.7 boundary in all five (`outputs/p5_rho_ci_seeds.csv`). The draw count was raised from 200 on 2026-09-11; the first reported interval was 0.609–0.691, and at 200 draws the upper bound moved between 0.687 and 0.699 across seeds. Record: [`plans/ops-bootstrap.md`](plans/ops-bootstrap.md))

![Segments that convert best are not the segments that are most efficient](../outputs/charts/p5_rate_vs_eta.png)

- **Verdict (rule ①):** the primary combination gives ρ = 0.669 < 0.7 and an upper bound of 0.692, which stays below the boundary across seeds (0.692–0.694) → **"different"**. All four combinations fall under 0.7. The margin to the boundary is roughly 0.006, which is not large.
- **Why they diverge:** conversion tracks loan size only weakly (0.454). Since η is the product of conversion and size, ranking by conversion alone misses the difference in size. The link between effort (Ē) and conversion is weaker still (0.219).
- **The η ranking itself is robust (rule ④):** rank correlation between the four η combinations is at least 0.975 (`outputs/p5_eta_rank_corr.csv`), so the primary ranking carries.

## 2. Segments where the two ranks disagree

Ten segments differ by at least 10 rank positions (`outputs/p5_mismatch.csv`). Rank 1 is best.

| Segment | n | Conversion | R̄ (EUR) | η | Conversion rank | η rank |
|---|---|---|---|---|---|---|
| **Converts well, runs inefficiently** | | | | | | |
| 6,500–10,000 · limit raise | 369 | 0.694 | 9,170 | 13,235 | 6 | 25 |
| 10,000–15,500 · new credit, A_Submitted absent | 960 | 0.640 | 14,485 | 13,318 | 10 | 24 |
| 6,500–10,000 · new credit, A_Submitted absent · other | 579 | 0.598 | 9,514 | 8,473 | 16 | 30 |
| 6,500 and below · new credit, A_Submitted absent | 686 | 0.520 | 6,136 | 5,512 | 24 | 35 |
| 6,500–10,000 · new credit, A_Submitted present · Home improvement | 1,015 | 0.570 | 9,820 | 10,024 | 18 | 28 |
| **Converts poorly, runs efficiently** | | | | | | |
| Above 25,000 · new credit, A_Submitted present · purpose not stated | 543 | 0.442 | 39,184 | 26,240 | 34 | 9 |
| Above 25,000 · new credit, A_Submitted present · Home improvement | 755 | 0.473 | 37,463 | 25,921 | 31 | 10 |
| Above 25,000 · new credit, A_Submitted present · Car | 336 | 0.497 | 32,334 | 21,885 | 28 | 11 |
| Above 25,000 · new credit, A_Submitted present · Existing loan takeover | 1,003 | 0.553 | 40,001 | 28,711 | 20 | 8 |
| 15,500–25,000 · new credit, A_Submitted present · purpose not stated | 477 | 0.497 | 21,776 | 16,796 | 29 | 19 |

- The high-conversion, low-efficiency side is **small and mid-sized**. Even on routes that convert well, such as limit raises or applications without the A_Submitted marker, a small loan returns little per hour of effort.
- The low-conversion, high-efficiency side is **new credit above EUR 25,000 with the A_Submitted marker**. More than one in two does not convert, but the ones that do are large.
- Quadrants against the medians: high/high 14, low/low 13, **high conversion with low efficiency 6, low conversion with high efficiency 6** (`13_rank_alignment.py` output).

## 3. Same effort, different allocation

Expected loan volume (Σ applications × conversion × R̄) when the effort budget is spent starting from the highest-conversion segments versus the highest-η segments (`outputs/p5_targeting_compare.csv`):

| Effort budget | Conversion order (million EUR) | η order (million EUR) | Gain from η order |
|---|---|---|---|
| 25% | 107.0 | 129.9 | +21.4% |
| 50% | 186.2 | 210.8 | **+13.2%** |
| 75% | 248.1 | 265.9 | +7.2% |

![Allocating the same effort in efficiency order yields 13% more loan volume](../outputs/charts/p5_targeting_curve.png)

- **Verdict (rule ③):** the gain at 50% of the budget exceeds 5% → **allocating by conversion rate is materially inefficient.**
- The tighter the effort budget, the more the order matters.
- **Caution:** this is a hypothetical reallocation computed from observed segment averages. Nothing guarantees that a segment keeps its conversion rate once effort moves (P3). The figure shows whether the order is worth changing, not the effect of an intervention.

## 4. Cost-to-margin scan and the required minimum margin share

**Scan of c/m** (`outputs/p5_cm_scan.csv`, 41 points on a log axis, 437–426,026):

| c/m (EUR per hour) | Negative segments | Share of applications | Share of effort |
|---|---|---|---|
| 4,094 and below | 0 | 0% | 0% |
| 4,863 | 3 | 11.3% | 9.6% |
| 9,677 | 11 | 31.3% | 28.2% |
| 16,214 | 20 | 56.2% | 52.9% |
| 32,266 | 38 | 97.3% | 97.0% |
| 45,516 and above | 39 | 100% | 100% |

The first segment turns negative at c/m = 4,374 (6,500 and below · new credit, A_Submitted present · purpose not stated).

**Required minimum margin share** — the share of total interest that must remain as net margin for EV ≥ 0 at the reference labour cost of EUR 57.6 per hour (`outputs/p5_margin_share.csv`):

| Segment | η_I (EUR per hour) | Required minimum margin share |
|---|---|---|
| 6,500 and below · new credit, A_Submitted present · Car | 724 | **7.95%** (highest) |
| 6,500 and below · new credit, A_Submitted present · purpose not stated | 778 | 7.40% |
| 6,500 and below · new credit, A_Submitted present · Existing loan takeover | 872 | 6.60% |
| … | | |
| Amount not stated · limit raise · purpose not stated | 7,381 | 0.78% |
| Above 25,000 · limit raise | 9,858 | **0.58%** (lowest) |

- **Verdict (rule ⑤):** even the least favourable segment is profitable once net margin reaches 7.95% of total interest. Whether that share is realistic is not judged here, since funding cost and credit loss data are absent (P6).
- **Effect of the cost assumption:** the reference figure excludes overhead such as systems, space and management. If the true hourly cost is k times the reference, every required share scales by k. The **13.7x spread between segments does not change** (`14_targeting_and_scan.py` output).
- The conclusion is therefore not "which segment loses money" but **"the same hour of effort produces 13.7x different value depending on the segment."**

## 5. Reversal scenarios (the three defined at design time)

| Scenario | Verdict | Evidence |
|---|---|---|
| Original reversal — high conversion with negative expected value | **Not observed by sign, observed by rank** | Every segment is profitable at the reference cost (chapter 4). Instead, high-conversion small and mid-sized segments sit low on η (chapter 2) |
| 1. Multi-offer reversal in small amounts | Decided in Phase 6 | The premise that small amounts rank lowest on η holds |
| 2. Large-application trap (effort rising non-linearly) | **Rejected** | Moving up the amount bands, effort rises from 0.532 to 0.735 hours (1.38x) while R̄ rises from 6,294 to 38,379 EUR (`outputs/p4_axis_groups.csv`, `p4_axis_spread.csv`). Large applications are the most efficient |
| 3. Effort spent on failures | Decided in Phase 7 | Starting point: cancellations 17.8%, rejections 16.4% of effort (Phase 2) |

## 6. Handover

- **Phase 6:** examine the incremental effect of multiple offers within segments, on η terms. Start with **small amounts**, the site of reversal scenario 1.
- **Phase 7:** split failure effort by segment and look separately at segments that convert well but run inefficiently.
- **Phase 9:** requirement 1 ("identify the band at intake") now has its basis. Segments built only from intake-time variables produce an efficiency ranking that differs from conversion, and changing the order raises loan volume by 13.2%.
- **Calculator (MVP):** `outputs/p5_calculator_input.csv`, `outputs/p5_calculator_meta.json` feed a tool where the user varies hourly cost and margin share and watches each segment's sign and rank.
