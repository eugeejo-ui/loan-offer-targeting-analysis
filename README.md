> English · [한국어](README.ko.md)

# Loan offer targeting — where conversion and efficiency disagree

**Are the applications most likely to convert the same ones worth the effort?** This repository tests that question against the loan handling log of a Dutch financial institute (BPI Challenge 2017: 31,509 applications, 1.2 million events). The answer is **no**, and the gap is carried through to allocation rules and system requirements.

## Headline findings

- Across 39 segments built only from information available at intake, **the rank correlation between conversion rate and effort efficiency is 0.669**. The bootstrap 90% interval, 0.610–0.692, sits below the 0.7 decision boundary fixed before the analysis began.
- Spending the same effort in efficiency order rather than conversion order yields **13.2% more loan volume** at half the effort budget.
- Conversion leaders are small and mid-sized applications; efficiency leaders are large new-credit applications. Conversion tracks loan size only weakly (rank correlation 0.454), so ranking by conversion alone misses the difference in size.

![Segments that convert best are not the segments that run most efficiently](outputs/charts/p5_rate_vs_eta.png)

## 1. Context and positioning

The data is the 2016 loan handling log of a Dutch financial institute — 1,202,267 events, 31,509 applications and 26 activities, published as BPI Challenge 2017 by 4TU.ResearchData.

The bank put three questions to the challenge: throughput times per part of the process, the influence of incompleteness on the outcome, and conversion for single versus multiple offers. All three stop at time and conversion; none asks what the effort returns. **The bank asked about conversion; this project asks about economics.**

Two earlier pieces of work lead into this one.

| Earlier work | Perspective | Question | Relationship to this project |
|---|---|---|---|
| [sap-btm-financial-prospecting](https://github.com/eugeejo-ui/sap-btm-financial-prospecting) | Vendor (pre-sales) | Where does the time disappear? | It used the same BPI 2017 log to establish that the problem exists. This project decides whom that effort should go to |
| Subscription target redefinition (B2C streaming) | Business operations | How should the conversion target be redrawn? | The expected-value structure was carried over from it. There the finding was "light buyers, not heavy ones"; here it is "large applications, not likely ones" |

## 2. Scope and metric

**Population.** The observation window stops at the last intake month with at least 99% of cases closed, leaving **29,131 applications** filed between January and November 2016 with a settled outcome. Success is defined as reaching the offer acceptance stage (A_Pending), and that definition reproduces the published figures (single offer 53.06%, multiple offers 59.00%).

**Effort.** Only hands-on staff time is counted. Waiting on the customer is excluded, and abandoned stretches are capped at the per-activity 99th percentile. Total effort across the population is **17,957.7 hours**.

**Metric.** Efficiency is η = R̄ × p ÷ Ē, where R̄ is the mean accepted offer amount among converted applications, p is the conversion rate, and Ē is the mean effort across all applications in the segment. Margin rate and hourly cost are absent from the log, so the two unknowns are folded into a single ratio (hourly cost ÷ margin rate). Expected value turns negative when that ratio exceeds η, which means **the segment ranking holds regardless of what the two unknowns turn out to be.**

**Segments.** Three intake-time axes — amount tier, intake route and loan purpose — cross into 44 segments, of which the 39 with at least 300 applications (28,243 in total) carry the ranking. All three axes separate efficiency (highest to lowest: 5.84x, 2.21x and 1.50x).

## 3. Hypotheses and decision rules

Three reversal scenarios and every decision boundary were fixed before the analysis, so that no criterion could be adjusted after seeing the numbers.

| Hypothesis | Verdict | Evidence |
|---|---|---|
| Multiple offers reverse on efficiency in the small-amount tier | **Rejected** | The incremental efficiency of an extra offer in that tier (6,704) exceeds the tier average (4,974) |
| Effort rises non-linearly with the amount requested | **Rejected** | Moving up the amount tiers, effort rises 1.38x while loan size rises about sixfold |
| Failed applications consume a large share of effort | **Scale confirmed, recovery rejected** | Failure accounts for 34.2% of effort, but only 3.5% is reachable by any available lever |

The core question was bounded the same way: a rank correlation of 0.9 or above reads as "the same", 0.7 to 0.9 as "broadly the same with exceptions", and below 0.7 as "different".

## 4. How it was tested

The work ran in eleven stages. Each stage fixed its plan and decision rules before execution. Conclusions are in [`docs/`](docs/); plans and execution records are in [`docs/plans/`](docs/plans/).

| Stage | Question | Result |
|---|---|---|
| [0 Data and scope](docs/00_scope.md) | Population, success definition, attribute quality | 29,131 applications. Credit score and two other attributes carry post-hoc outcome information and were barred from use |
| [1 Process baseline](docs/01_process_baseline.md) | Where applications drop out, and who holds the elapsed time | 8,630 of 9,692 cancellations stop after the offer is sent and before the customer replies. Customers hold 82.2% of elapsed time |
| [2 Effort](docs/02_effort.md) | Hands-on time per case | The top 1% of work stretches held 28.5% of all time, so a per-activity cap applies. Rank correlation across capping methods is at least 0.996 |
| [3 Method](docs/03_method.md) | Components of η and exclusions | Total interest never flips the sign, so results are expressed as a **required minimum margin share** instead |
| [4 Segments](docs/04_segments.md) | Do intake-time axes separate efficiency? | All three axes retained; none rejected. Best to worst spans roughly tenfold |
| [5 Efficiency](docs/05_expected_value.md) | **The core question** | ρ = 0.669, i.e. "different". Allocating in efficiency order adds 13.2% of loan volume |
| [6 Multiple offers](docs/06_multi_offer.md) | What the extra effort buys | The advantage comes entirely from later conversations (+13.31%p); offering several in the first conversation converts below a single offer (−2.64%p) |
| [7 Failure effort](docs/07_failed_effort.md) | How much failure effort is recoverable | 34.2% in scale, 3.5% recoverable. Low-efficiency segments carry the larger failure share (ρ = −0.651) |
| [8 Intervention](docs/08_intervention.md) | What can actually be changed | Customers hold the majority of elapsed time in all 39 segments. The current handling order runs against efficiency (ρ = +0.346) |
| [9 Requirements](docs/09_requirements.md) | What operating the rule demands | 26 product-neutral requirements, each with evidence and an acceptance test, plus the measurement periods they imply |
| [10 Realisation paths](docs/10_options.md) | How to realise it | Three paths compared against the 17 Must requirements |

The 30-day automatic cancellation rule was verified first, so that a pattern created by a rule would not be read as a finding. Of the cancellations that followed a sent offer, 77.0% fall 29–32 days after the last send, and 99.5% of those were processed by the system account. Duration is therefore never used as a cause of conversion.

![Cancellations cluster 30 days after the last offer is sent](outputs/charts/p1_cancel_gap.png)

The same effort produces different volume depending on the order it is spent in. The tighter the budget, the more the order matters (+21.4% at 25% of the budget, +13.2% at 50%, +7.2% at 75%).

![Spending the same effort in efficiency order adds 13% of loan volume](outputs/charts/p5_targeting_curve.png)

The multi-offer advantage survives stratification (+6.62%p) but comes entirely from later conversations, where effort also rises. Applications given several offers in the first conversation convert below single-offer applications.

![The multi-offer advantage appears only in later conversations](outputs/charts/p6_multi_offer.png)

Failure effort is large in scale, yet the part a contact policy can address is 3.5% of all effort.

![Failed applications absorb 34% of effort](outputs/charts/p7_failure_effort.png)

The current handling order runs against efficiency: the more efficient the segment, the longer it waits at the bank (ρ = +0.346). Of the time the bank holds an application, 0.61% is hands-on work and the rest is queueing.

![The more efficient the segment, the longer it waits at the bank](outputs/charts/p8_eta_vs_bank_wait.png)

Each recommended lever was costed in months of measurement against monthly intake. The contact policy resolves in 5.5 months; the single-offer rule needs 8.4 to 37.5 months because only 309 decision points arise per month.

![Contact policy is testable within six months; the single-offer rule is not](outputs/charts/p9_ab_duration.png)

## 5. Results

**The answer to the core question is no.** The rank correlation between conversion and efficiency is 0.669, and the 90% interval of 0.610–0.692 stays below the 0.7 boundary. Across random seeds the upper bound holds between 0.692 and 0.694.

The direction of the disagreement is consistent. Small and mid-sized applications convert well and run inefficiently; new-credit applications above EUR 25,000 do the opposite. Ten segments differ by at least ten rank positions.

**The conclusion is an efficiency gap, not a sign flip.** At the reference labour cost (EUR 57.6 per hour, Eurostat) every segment is profitable. What differs is the net margin share required to break even: from 0.58% to 7.95%, a **13.6x spread** that does not depend on the cost assumption. The same hour of effort is worth 13.6 times more in one segment than in another.

## 6. Recommendations

1. **Reorder the handling queue by intake-time segment — conditional, first priority.** If staffing is genuinely the constraint, order the queue by efficiency. Today the more efficient applications wait longer, so reversing the order already moves in the right direction. If staffing is not the constraint, reordering only redistributes waiting time and the 13.2% should not be expected.
2. **Single offer in the first conversation — pilot rule with before-and-after comparison.** Random assignment would take 8.4 to 37.5 months, so a reversible pilot replaces it.
3. **Contact policy after an offer is sent — A/B once the input field exists.** A 2%p reduction in the automatic cancellation rate resolves in 5.5 months, but nothing can be measured until contact outcome codes are recorded.
4. **Faster processing on its own — not recommended.** Customers hold the majority of elapsed time (73.2–89.4%) in all 39 segments.

The requirements are stated without product names: 26 in total (7 functional, 8 data, 5 measurement, 6 non-functional). Three realisation paths were compared against the 17 Must requirements. Policy and operating changes alone satisfy 11 and partially satisfy 6; a tool alongside the core system satisfies all 17; changing the core system also covers the missing input fields but is expensive to reverse. The recommendation is to **pilot through operating changes and move to a tool for steady-state operation**.

## 7. Why it matters

- **The conclusion does not rest on assumptions.** Segment ranking and allocation gain are fixed even without knowing the margin rate or the hourly cost, because the two unknowns were folded into a single ratio.
- **No predictive model is required.** A 39-row rule table built from four intake-time variables is sufficient, and it keeps explainability and audit traceability intact.
- **Rejections are recorded as results.** Two of the three pre-registered hypotheses were rejected, with the evidence and the reason for reframing kept alongside them.
- **Observation is never promoted to causation.** Every comparison is an observed association, and the measurement design and duration needed before any rule changes are set out in full.

## 8. Limitations

- All results are observed associations, not intervention effects. The allocation comparison is a hypothetical reallocation computed from observed segment averages.
- The multi-offer advantage carries selection bias: later conversations only exist where the customer has not already dropped out, so the figure reads as an upper bound.
- Post-disbursement outcomes (arrears, default, early repayment) and funding cost are absent, so the sign of profit cannot be settled directly.
- The log covers a single institution and a single year.
- Seven fields needed to measure effects are missing from the log; they are carried forward as data requirements.

## 9. Reproducing the analysis

Python 3.12.

```
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python analysis/00_build_cache.py
.venv\Scripts\python -m pytest tests -q
```

The source log is not included in the repository. Download the BPI Challenge 2017 data from 4TU.ResearchData, point `analysis/config.py` at it, build the parquet cache with `00_build_cache.py`, then run the numbered scripts in order. Decision logic lives in modules and is verified against synthetic data; there are 76 tests.

## 10. Repository layout

- `analysis/` — decision-logic modules and numbered execution scripts
- `tests/` — 76 module-level tests
- `docs/` — 11 stage conclusion documents in Korean; the three core documents are also in English
- `docs/plans/` — plans and execution records per stage
- `app/dashboard/` — a single-page dashboard with the results and the calculator. `analysis/22_build_dashboard.py` builds it to `outputs/dashboard/index.html`
- `outputs/` — derived CSV and parquet files, and the seven charts

Charts and dashboard text are in Korean; the English documents carry the same figures.

## 11. Sources

- van Dongen, B.F. (2017). *BPI Challenge 2017*. 4TU.ResearchData. doi:10.4121/uuid:5f3067df-f10b-45da-b98b-86ae4c7a310b
- Challenge page and the bank's questions in full: https://ais.win.tue.nl/bpi/2017/challenge.html
- Scheithauer, Henne, Kerciku, Waldenmaier, Riedel (metafinanz). *Suggestions for Improving a Bank's Loan Application Process based on a Process Mining Analysis*.
- Blevi, Delporte, Robbrecht (KPMG). *Process mining on the loan application process of a Dutch Financial Institute*.
- Badakhshan, Maciel, Wurm. *Process Mining in the Financial Industry: A Case Study — The BPI Challenge 2017*.
- Carmona, Cofré, Naranjo, Vásquez, Lee, Salazar Fernández, Arias. *Analysis of Loan Application Process Using Process Mining*.
- Reference labour cost: Eurostat `lc_lci_lev`, hourly labour cost in Dutch financial and insurance activities, 2016: EUR 57.6.
