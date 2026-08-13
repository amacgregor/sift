# Methodology

Dataset **0.2.0**. Package `sift==0.2.0`.

## What Sift measures

Two families of tasks:

| Family | Question | Gold |
|---|---|---|
| **T — Triage** | Is this PR worth scarce human attention? | `needs_human` \| `vouching_required` \| `likely_low_value` + priority |
| **F — Findings** | Did the system surface substantive defects? | Curated issue list (not nits) |

Headline metrics:

- **Triage accuracy** — exact label match
- **Budgeted capture @ 20% / 40%** — of gold `needs_human` tasks, how many appear in the top slice of the queue ranked by SUT `triage_score`
- **Budget waste @ 20% / 40%** — fraction of that top slice that is gold `likely_low_value`
- **Findings coverage / precision / F1** — substance match to gold findings
- **Cost (USD)** — first-class; heuristic and checklist are $0

@20% is the Circuit Breaker–style scarce-budget headline. @40% is reported because N=10 triage tasks makes a 2-slot cut noisy; both are in every report.

## Precision policy

**Default: valid-extras.** Unmatched predictions with non-trivial rationale are not automatic false positives (ReviewBench-style). Use `--strict-gold` to treat every unmatched prediction as a false positive.

## Finding match

Lexical/anchor overlap (path soft-match + token overlap). **No LLM judge in 0.2.0** so the suite is reproducible with zero API keys. Treat F1 as harness-relative, not cross-paper comparable to Martian CRB.

An optional LLM judge remains out of scope until the lexical matcher is the documented limitation rather than an accident.

## Gold curation rules

1. Nits, style-only, and pure questions are never gold findings.
2. Every gold label has a written `rationale` in `gold.json`.
3. Seed tasks are **synthetic** fixtures with known defects — no training-data leakage from famous public PRs.
4. At least one finding is held out so that neither cheap SUT is supposed to score 1.0 (`F007`, `F008`).
5. Dataset version is the package version (`0.2.0`).

## Systems under test

| SUT | Strategy | Key? |
|---|---|---|
| `heuristic` | Structural: size, files, tests, chore/security language, two shallow diff patterns (tenant-less id access, dropped `is_active`/status filter) | No |
| `checklist` | Heuristic + explicit catalog: CSRF removal, naive `datetime.now()` on cutoffs, check-then-act money, header logging, dropped columns still referenced, session rotation on privilege change | No |
| `llm` | One-shot JSON review | Yes |
| `llm_structured` | Same model; must list files → invariants → findings before deciding | Yes |

The career-relevant experiment is **heuristic vs checklist** (strategy, $0) and, if a key is present, **llm vs llm_structured** (same model, different procedure).

## Failure codes

| Code | Meaning |
|---|---|
| `WRONG_TRIAGE_UP` | Predicted higher urgency than gold |
| `WRONG_TRIAGE_DOWN` | Predicted lower urgency than gold |
| `MISS_DOMAIN` | Missed domain/security gold finding |
| `MISS_CONTEXT` | Missed finding needing broader context / contract |
| `NOISE` | Low-quality extra finding |
| `HALLUCINATED_BUG` | Serious finding with zero gold coverage |

## 0.2.0 result (checked in)

See [`results/examples/comparison.md`](results/examples/comparison.md).

| Metric | heuristic | checklist |
|---|---|---|
| Triage accuracy | 0.600 | 0.800 |
| Capture @ 20% | 0.333 | 0.667 |
| Capture @ 40% | 0.333 | 1.000 |
| Findings F1 | 0.250 | 0.750 |
| Cost | $0 | $0 |

Designed misses that remain after the checklist: `F007` (page-size contract), `F008` (salvage vs NRV), plus two over-admits on triage (`T007`, `T009`).

## Limitations

- Eighteen synthetic tasks — directional, not a leaderboard
- Diffs are fixtures, not full mega-repos
- Lexical matcher underestimates semantic matches an LLM judge would credit
- English-only
- Checklist catalog is small and public; it can be overfit by a SUT author who reads this file. That is accepted for a portfolio slice; an online/held-out track is future work
- No continuous GitHub scrape
- Optional LLM SUTs are not part of the checked-in numbers (no key in CI)

## Relation to StructPR Shield

Methods are public and adjacent to Shield’s triage thesis. **No private Shield calibration data** is included. Product thresholds and customer repos stay private. If Shield is ever scored on this suite, it is allowed to lose.
