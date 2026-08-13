# Methodology

Package `sift==0.3.0`.

## Two modes

| Mode | Input | Output |
|---|---|---|
| **Review** | A unified diff (+ optional title/body) | Triage label, score, findings. No gold. |
| **Pack** | A directory of tasks you supply | Same, plus scores if `gold.json` is present |

The repository does not ship a benchmark. `tests/fixtures/seed/` exists so the
loader and scorer have something to unit-test against. Do not cite numbers from
that directory as a result.

## Metrics (pack mode only)

| Family | Question | Gold |
|---|---|---|
| **T — Triage** | Is this PR worth scarce human attention? | `needs_human` \| `vouching_required` \| `likely_low_value` |
| **F — Findings** | Did the system surface substantive defects? | Curated issue list (not nits) |

- **Triage accuracy** — exact label match
- **Budgeted capture @ 20% / 40%** — fraction of gold `needs_human` in the top slice, ranked by `triage_score`
- **Budget waste** — fraction of that slice that is gold `likely_low_value`
- **Findings coverage / precision / F1** — lexical/anchor match to gold
- **Cost (USD)** — first-class

**Precision default: valid-extras.** Unmatched predictions with a non-trivial rationale
are not automatic false positives. `--strict-gold` flips that.

Finding match is lexical. No LLM judge. F1 is harness-relative.

## Gold rules (if you write a pack)

1. Nits, style-only, and questions are not gold findings.
2. Every gold label has a written `rationale`.
3. The SUT must not be written against the pack. If you add a detector for a fixture
   you just authored, you are scoring the detector, not the strategy.

## SUTs

| SUT | Strategy |
|---|---|
| `heuristic` | Size, files, tests, chore/security language; two shallow diff patterns |
| `llm` | One-shot JSON |
| `llm_structured` | Same model, invariant-first prompt |

## Failure codes

| Code | Meaning |
|---|---|
| `WRONG_TRIAGE_UP` | Predicted higher urgency than gold |
| `WRONG_TRIAGE_DOWN` | Predicted lower urgency than gold |
| `MISS_DOMAIN` | Missed domain/security gold finding |
| `MISS_CONTEXT` | Missed finding needing broader context |
| `NOISE` | Low-quality extra finding |
| `HALLUCINATED_BUG` | Serious finding with zero gold coverage |

## Relation to StructPR Shield

Methods are adjacent to Shield’s triage thesis. No private Shield or LiORA data
is in this repo.
