> English · [한국어](10_options.md)

# Phase 10 — Realisation paths and a conditional recommendation

> 2026-09-12 · plan and record [`plans/phase-10-options.md`](plans/phase-10-options.md) · no new analysis (figures cited from phases 5–9)

## Summary

- **The smallest change that meets all 17 Must requirements is path B, adding tooling around the core system.** Path A (operating rules only) meets 11 and leaves 6 partial; path C (changing the core) does what B does and additionally carries three input fields.
- **The recommendation is therefore to pilot with A and decide on B from the result.** A is not a standing way to operate; it is a way to test the premises, namely whether staffing is the real constraint and whether segments hold their conversion rate once the order changes (Phase 8).
- **Contact policy (FR4) runs in a different order.** A call-outcome code (DR1) is entered by staff on a work screen, so the core needs a field for it. The 5.5-month A/B from Phase 9 can only start once that field exists.
- **Cost is not compared.** Procurement and labour figures are absent (P6). The comparison uses scope of change, reversibility, and time to verify.

## 1. The three paths

| Path | Scope of change | Reversing it | Typical realisation |
|---|---|---|---|
| **A. Operating rules** | No system change | Withdraw the instruction | Staff assign the segment from the four intake fields, the rule table lives in a document or spreadsheet, assignment and records are manual, monthly log extracts feed the measurement |
| **B. Tooling** | Core untouched, tools alongside it | Stop using the tool | Intake data and event logs feed a tool that computes segments and priorities and automates assignment, measurement and guardrails |
| **C. Core change** | The application processing system itself | Roll back a release | Segment field at intake, offer and contact rules branching inside the system, random assignment and outcome codes built in |

## 2. Which levers each path realises

Levers and grades come from Phase 8; Phase 9 lowered the single-offer lever from "after A/B" to "pilot with before-and-after comparison".

| Lever (grade) | Path A | Path B | Path C |
|---|---|---|---|
| **Queue priority in η order** (conditional first choice) | Pilot only. Queue order set by instruction, checked by monthly aggregation | Standing operation. Priorities computed automatically, effects visible near real time | Same as B, with the order built into the queue |
| **Single offer in the first conversation** (pilot, before-and-after) | Possible. Default set by instruction, exceptions recorded by hand | Possible. The tool enforces the default and records exceptions | Possible. The offer screen enforces the default |
| **Contact policy after the offer** (after A/B) | **Not possible.** There is no field to record the call outcome (DR1) | Partial. A separate screen means double entry | Possible. The outcome code sits on the call handling screen |
| Screening filter ahead of assessment (on hold) | — | — | — |
| Faster processing alone (not recommended) | — | — | — |

## 3. The 17 Must requirements by path

Verdicts: **met** / **partial** (people fill the gap, or the signal is delayed) / **not possible** (structurally unavailable).

| ID | Requirement | A | B | C | Reason (for A) |
|---|---|---|---|---|---|
| FR1 | Segment identification at intake | met | met | met | The rule is a hierarchical table over four intake fields, so a person can look it up. The load of classifying 2,648 applications a month remains |
| FR2 | Queue priority branching by segment | met | met | met | Instructions can change the order. Whether they were followed is only visible in hindsight |
| FR5 | Random assignment | **partial** | met | met | A pre-drawn table can randomise, but the assignment log and balance check are manual and easy to miss |
| FR6 | Post-hoc measurement and feedback | met | met | met | A monthly log extract recomputed the way this project did. It costs analyst time every month |
| FR7 | Queue monitoring | **partial** | met | met | Work and waiting time separate in the log after the fact. The current state of the queue is invisible |
| DR6 | Working hours and headcount | met | met | met | Internal records; unrelated to any system change |
| DR7 | Definition of the intake route marker | met | met | met | Settled by asking the business owner |
| DR8 | Intake-time field snapshot | **partial** | met | met | Values can be copied aside, but nothing guarantees the original was not changed later |
| MR1 | Metric definitions | met | met | met | The definitions themselves are fixed in documents (phases 0–3) |
| MR4 | Refresh cycle and segment upkeep | met | met | met | Monthly recomputation and quarterly axis checks, done by hand |
| MR5 | Guardrails | **partial** | met | met | A breach surfaces only at the monthly cycle; anything in between is learned late |
| NFR1 | Explainability | met | met | met | The rule table is the explanation. This fits path A best |
| NFR2 | Audit trail | **partial** | met | met | Rule version, effective date and exception reasons recorded by hand will have gaps |
| NFR3 | Data minimisation | met | met | met | The rule reads four intake fields. No credit information |
| NFR4 | Operator editing | met | met | partial | Editing the table is the whole job. Path C meets this only if rules sit in a table outside the code |
| NFR5 | Fallback to the default rule | met | met | met | Withdraw the instruction, stop the tool, or revert the setting |
| NFR6 | Ceiling on customer impact | **partial** | met | met | The waiting ceiling for low-priority segments is checked only monthly |
| | **Total** | **11 met · 6 partial** | **17 met** | **16 met · 1 partial** | |

- **The six partials in path A share one cause:** measurement and recording happen manually, after the fact. That is workable for a pilot and weak as a standing arrangement.
- **The single partial in path C is a design choice.** Separating rules into an operator-editable table resolves NFR4; leaving them in code ties the monthly feedback loop (FR6) to the release cycle.
- **Path B is the smallest change that meets all 17** (decision rule ③).

## 4. The seven data gaps by path

| Gap | Judgement it blocks | A | B | C |
|---|---|---|---|---|
| DR1 call outcome code | Response lift from contact policy, meaning of aborted call work | not possible | partial (double entry) | met |
| DR2 cancellation reason | The lever behind 2,317 manual cancellations | partial (recording instruction) | partial (double entry) | met |
| DR3 who requested the offer | The owner of the additional-offer lever | partial (recording instruction) | partial (double entry) | met |
| DR4 post-disbursement performance | Net margin, verdict on the required margin share | not possible | met (data linkage) | met |
| DR5 funding cost and net margin | Verdict on the profitability sign | met | met | met |
| DR6 working hours and headcount | Whether staffing is the constraint (premise of FR2) | met | met | met |
| DR7 definition of the intake route marker | Interpretation of the intake route axis | met | met | met |

- **Values that staff type on a work screen (DR1–DR3) only accumulate properly if the core has a field for them.** Entering them in a separate tool means double entry, and double entry does not hold.
- **DR5, DR6 and DR7 are not system problems.** They come from finance and HR records and from asking what the marker means, and can start now on any path.

## 5. Premises and limits per path

| Path | Premise that must hold | How to check it | Limit |
|---|---|---|---|
| A | Intake staff can classify on the four fields · a monthly log extract is available | Agreement rate in the first pilot month, whether the extract request is served | Measurement and recording are manual and retrospective. Guardrails work only monthly |
| B | The core can export intake data and event logs on a schedule · assignment follows the tool's order | Export trial, operational agreement | Fields the core does not capture (DR1–DR3) stay empty. A tool queue beside the core queue splits operations |
| C | Release schedule and budget exist | Organisational decision | Costly to reverse. Unless rules are separated into a table, feedback is tied to the release cycle |

**A limit common to all paths:** the evidence is observational. The +13.2% from reordering effort is a hypothetical reallocation computed from observed segment averages, not an intervention effect (Phase 5, P3). Whether segments hold their conversion rate after the order changes is unverified.

**Time to verify** (Phase 9, `outputs/p9_ab_sample_sizes.csv`): contact policy needs 5.5 months to detect a 2 percentage point drop in the auto-cancellation rate. The single-offer rule reaches only 309 decision points a month, which puts an A/B test at 8.4–63.4 months, so a pilot with before-and-after comparison replaces it.

## 6. Conditional recommendation

### First — pilot on path A, then decide on path B

- **If the premise holds:** with staffing as the real constraint (DR6) and a monthly log extract available, apply η-order priority to one group of segments as a pilot. Efficient segments currently wait longer inside the bank (ρ +0.346), so reversing the order already points the right way. Set the guardrails (MR5) and the waiting ceiling (NFR6) alongside it.
- **If it does not hold:** with slack in staffing every application is handled in time, and reordering only redistributes waiting. In that case the 13.2% should not be expected, and the effect narrows to shorter waits for efficient segments. Better then to drop the pilot and secure DR4 and DR5 to settle the profitability sign first.
- **If the pilot moves in the direction of the rule, move to path B.** It is the smallest change meeting all 17 Must requirements, and it resolves the six partials from A — random assignment, monitoring, snapshot, guardrails, audit trail and the waiting ceiling — through automation.

### Second — verify contact policy once the core has the field

Without a call outcome code (DR1), an A/B test cannot measure what changed. This lever therefore presumes **a small piece of path C**: an outcome code on the call handling screen and a cancellation reason. Once the field exists, 5.5 months is enough to detect 2 percentage points.

### Available now, on any path

Working hours and headcount (DR6), the definition of the intake route marker (DR7) and funding cost and net margin (DR5) need no system change. DR6 decides the premise of the first lever, and DR5 turns "which segment loses money" from a required-margin-share statement into an answer with a sign.

### Not recommended

- **Faster processing alone:** customers hold the majority of elapsed time in all 39 segments (Phase 8).
- **Screening filter and lighter front-end work:** failure rates separate by segment, but the effort is not concentrated there (Phase 7).
- **A predictive model:** a rule table over four intake fields already separates η by 5.84x (Phase 4). There is no evidence a model does better, and it costs explainability (NFR1).

### Sequence

| Period | Work | Decision point |
|---|---|---|
| 0–1 month | Secure DR6 and DR7, publish the segment rule table (FR1), fix the metric definitions (MR1) | Is staffing the constraint → the premise of the first lever |
| 1–3 months | Path A pilot — η-order priority on one group, guardrails and waiting ceiling set, monthly aggregation | Does waiting move in the direction of the rule, does conversion hold |
| 3–6 months | Decide on path B from the pilot result. In parallel, request the core input fields (DR1, DR2) | Do the 17 Must requirements have to hold in standing operation |
| 6 months onward | On path B, run the contact policy A/B (5.5 months) and the single-offer pilot with before-and-after comparison | Does each lever move the way the observed association suggested |

## 7. Limits of this document

- **No cost comparison.** There are no figures for tooling or core work (P6). The comparison uses scope of change, reversibility and time to verify.
- **Organisational constraints are unknown.** Staffing, approval routes and the system roadmap are not in the log; they appear only as premises.
- **One institution, one year.** Nothing guarantees the same ordering elsewhere.
- **The path verdicts are judgements.** The met / partial / not possible marks in chapters 3 and 4 are not computed; they compare each requirement's definition against the nature of each path. The reasoning sits in each cell and in the phase results cited.
