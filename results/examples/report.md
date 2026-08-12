# Sift report — `heuristic`

Tasks: **5**

## Headline metrics

| Metric | Value |
|---|---|
| Triage accuracy | 1.000 |
| Budgeted capture @ 20% | 1.000 |
| Budget waste @ 20% | 0.000 |
| Findings mean coverage | 1.000 |
| Findings mean precision | 1.000 |
| Findings mean F1 | 1.000 |
| Total cost (USD) | 0.000 |

## Failure codes

_None_

## Per-task

| Task | Family | Triage | Findings F1 | Failures |
|---|---|---|---|---|
| `F001_missing_tenant` | F | — | 1.000 | — |
| `F002_api_parity` | F | — | 1.000 | — |
| `T001_bulk_ai_rewrite` | T | ✓ `likely_low_value` (gold `likely_low_value`) | — | — |
| `T002_authz_bugfix` | T | ✓ `needs_human` (gold `needs_human`) | — | — |
| `T003_new_contributor_messy` | T | ✓ `vouching_required` (gold `vouching_required`) | — | — |

## Notes

- Precision uses **valid-extras** by default (unmatched but plausible findings are not auto-penalized).
- Finding match in v0.1 is lexical/anchor-based (no LLM judge) for zero-key reproducibility.
- Budgeted capture ranks by SUT `triage_score` and measures recall of `needs_human` gold in the top 20% slice.
