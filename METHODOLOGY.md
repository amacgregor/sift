# Methodology

## What Sift measures

Two families of tasks:

| Family | Question | Gold |
|---|---|---|
| **T — Triage** | Is this PR worth scarce human attention? | `needs_human` \| `vouching_required` \| `likely_low_value` + priority |
| **F — Findings** | Did the system surface substantive defects? | Curated issue list (not nits) |

Headline metrics:

- **Triage accuracy** — exact label match
- **Budgeted capture @ 20%** — of gold `needs_human` tasks, how many appear in the top 20% of the queue ranked by SUT `triage_score`
- **Budget waste @ 20%** — fraction of that top slice that is gold `likely_low_value`
- **Findings coverage / precision / F1** — substance match to gold findings
- **Cost (USD)** — first-class; heuristic is $0

## Precision policy

**Default: valid-extras.** Unmatched predictions with non-trivial rationale are not automatic false positives (ReviewBench-style). Use `--strict-gold` to treat every unmatched prediction as a false positive.

## Finding match (v0.1)

Lexical/anchor overlap scorer (path soft-match + token overlap). **No LLM judge in v0.1** so the suite is reproducible with zero API keys. An LLM judge adapter is planned; until then, treat F1 as harness-relative, not cross-paper comparable to Martian CRB.

## Gold curation rules

1. Nits, style-only, and pure questions are never gold findings.
2. Every gold label has a written `rationale` in `gold.json`.
3. Seed tasks are **synthetic** fixtures with known defects — no training-data leakage from famous public PRs.
4. Dataset version is the git tag / package version (`0.1.0` for this seed set).

## Failure codes

| Code | Meaning |
|---|---|
| `WRONG_TRIAGE_UP` | Predicted higher urgency than gold |
| `WRONG_TRIAGE_DOWN` | Predicted lower urgency than gold |
| `MISS_DOMAIN` | Missed domain/security gold finding |
| `MISS_CONTEXT` | Missed finding needing broader context |
| `NOISE` | Low-quality extra finding |
| `HALLUCINATED_BUG` | Serious finding with zero gold coverage |

## Limitations

- Five tasks only — directional, not a leaderboard
- Synthetic diffs, not full mega-repos
- Lexical matcher underestimates semantic matches an LLM judge would credit
- English-only
- No online continuous track yet

## Relation to StructPR Shield

Methods are public and adjacent to Shield’s triage thesis. **No private Shield calibration data** is included. Product thresholds and customer repos stay private.
