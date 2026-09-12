> English · [한국어](README.ko.md)

# Loan Offer Targeting — where conversion rate and efficiency disagree

**Are the applications most likely to convert the same ones worth the effort?** This analysis answers that question from the loan application log of a Dutch financial institution (BPI Challenge 2017: 31,509 applications, 1.2 million events). They are not the same, and the work carries that gap through to allocation rules and system requirements.

## Headline result

Splitting applications into 39 segments using only information available at intake, **the rank correlation between conversion rate and effort efficiency is 0.669**, with a bootstrap 90% interval of 0.610–0.692 that stays below the 0.7 decision boundary. Spending the same effort in efficiency order yields **13.2% more loan volume** at half the effort budget.

High conversion sits with small and mid-sized applications. The efficient ones are large new-credit applications, which convert at below-average rates. Conversion tracks loan size only weakly (rank correlation 0.454), so ranking by conversion alone misses the difference in size.

![Segments that convert best are not the segments that are most efficient](outputs/charts/p5_rate_vs_eta.png)

## The metric

Efficiency is defined as η = R̄ × p / Ē, where R̄ is the mean accepted offer amount among converted applications, p is the conversion rate, and Ē is mean effort across all applications in the segment. Margin rate and hourly cost are unknown, so the two unknowns collapse into a single ratio: expected value turns negative when hourly cost ÷ margin rate exceeds η. Segment ranking holds regardless of either unknown.

Effort is the sum of active work intervals on work items. Waiting time is excluded, and abandoned intervals are capped at the per-activity 99th percentile. Total effort across the population is 17,957.7 hours.

## Findings

| Topic | Result |
|---|---|
| Population | 29,131 applications submitted between January and November 2016 with a settled outcome. The observation window is cut at 99% monthly completion |
| Replication | 53.06% for single-offer and 59.00% for multi-offer applications, matching the published figures |
| Where applications drop out | 8,630 of 9,692 cancellations stopped after the offer was sent and before the customer replied |
| The 30-day rule | 77.0% of cancellations with a sent offer fall 29–32 days after the last offer, and 99.5% of those were processed by the system account. This is why elapsed time is not treated as a cause of conversion |
| Segments | All three intake axes separate η — amount 5.84x, intake route 2.21x, purpose 1.50x between the extremes. Crossing them gives 44 segments, 39 of which hold at least 300 applications |
| Profitability sign | Every segment is profitable at the reference labour cost of EUR 57.6 per hour. The minimum net margin share required runs from 0.58% to 7.95%, and the 13.7x spread between segments is independent of the cost assumption |
| Multiple offers | The stratified +6.62%p conversion advantage comes entirely from later conversations (+13.31%p). Multiple offers within the first conversation convert below single offers (−2.64%p) |
| Effort on failures | Failed applications consume 34.2% of all effort, but only 3.5% of it is recoverable through available levers |
| The bottleneck | Customers hold 82.2% of elapsed time. Customer time is the majority in all 39 segments |
| Current processing order | The more efficient the segment, the longer it waits for bank processing (ρ = +0.346). Only 0.61% of bank-held time is hands-on work |

Evidence and decision rules for each phase live in [`docs/`](docs/); plans and execution records are kept in [`docs/plans/`](docs/plans/).

## Recommendations

Each recommendation states the condition it rests on.

1. **Prioritise the processing queue by intake segment — conditional first choice.** If staffing is the real constraint, order the queue by efficiency. If there is slack, reordering only redistributes waiting time and the 13.2% gain should not be expected.
2. **Single offer in the first conversation — pilot before deciding.** Only 309 applications a month reach that decision point, which puts an A/B test at 8.4 to 63.4 months. A reversible pilot rule with before-and-after comparison replaces it.
3. **Contact policy after the offer — A/B once the field exists.** A rule that cuts the auto-cancellation rate by 2 percentage points is detectable in 5.5 months. Without a recorded call-outcome code, however, there is no way to measure what changed.
4. **Faster processing on its own is not recommended.** Customers hold the majority of elapsed time in every segment.

Requirements are written without naming products: 26 of them across function (7), data (8), measurement (5) and non-functional (6). Three realisation paths were compared. Changing rules and operations alone meets 11 of the 17 Must requirements and leaves 6 partial. Adding tooling around the core system meets all 17. Covering the missing input fields as well means changing the core, which is the costliest to reverse. See [`docs/09_requirements.md`](docs/09_requirements.md) and [`docs/10_options.md`](docs/10_options.md).

## Limitations

- These are observed associations, not intervention effects. The allocation comparison is a hypothetical reallocation computed from observed segment averages.
- The multi-offer advantage carries selection bias. A later conversation only happens if the customer is still there, so the figure is an upper bound.
- Post-disbursement performance (arrears, default, early repayment) and funding cost are absent, so the profitability sign cannot be settled directly.
- The log covers one institution and one year.

## Reproducing

Built against Python 3.12.

```
py -3.12 -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python analysis/00_build_cache.py
.venv\Scripts\python -m pytest tests -q
```

The raw log is not included in this repository. Download the BPI Challenge 2017 data from 4TU.ResearchData, point the path in `analysis/config.py` at it, and build the parquet cache with `00_build_cache.py`. Run the remaining scripts in numeric order. Decision logic lives in modules and is verified against synthetic data; the suite has 63 tests.

## Repository layout

- `analysis/` — decision-logic modules and numbered execution scripts
- `tests/` — module-level tests
- `docs/` — 11 phase conclusion documents
- `docs/plans/` — phase plans and execution records
- `outputs/` — generated CSV and parquet files, plus 7 charts

## References

- van Dongen, B.F. (2017). BPI Challenge 2017. 4TU.ResearchData.
- Scheithauer et al. (metafinanz). Suggestions for Improving a Bank's Loan Application Process based on a Process Mining Analysis.
- Blevi, Delporte, Robbrecht (KPMG). Process mining on the loan application process of a Dutch Financial Institute.
- Badakhshan, Maciel, Wurm. Process Mining in the Financial Industry: A Case Study.
