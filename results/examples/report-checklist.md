# Sift report — `checklist`

Tasks: **18** · dataset `0.2.0`

## Headline metrics

| Metric | Value |
|---|---|
| Triage accuracy | 0.800 |
| Budgeted capture @ 20% | 0.667 |
| Budget waste @ 20% | 0.000 |
| Budgeted capture @ 40% | 1.000 |
| Budget waste @ 40% | 0.000 |
| Findings mean coverage | 0.750 |
| Findings mean precision | 0.750 |
| Findings mean F1 | 0.750 |
| Total cost (USD) | 0.000 |

## Failure codes

- `WRONG_TRIAGE_UP`: 2
- `MISS_CONTEXT`: 1
- `MISS_DOMAIN`: 1

## Per-task

| Task | Family | Triage | Findings F1 | Failures |
|---|---|---|---|---|
| `F001_missing_tenant` | F | — | 1.000 | — |
| `F002_api_parity` | F | — | 1.000 | — |
| `F003_csrf_dropped` | F | — | 1.000 | — |
| `F004_jurisdiction_tz` | F | — | 1.000 | — |
| `F005_check_then_act` | F | — | 1.000 | — |
| `F006_auth_header_log` | F | — | 1.000 | — |
| `F007_default_page_size` | F | — | 0.000 | MISS_CONTEXT |
| `F008_inventory_salvage` | F | — | 0.000 | MISS_DOMAIN |
| `T001_bulk_ai_rewrite` | T | ✓ `likely_low_value` (gold `likely_low_value`) | — | — |
| `T002_authz_bugfix` | T | ✓ `needs_human` (gold `needs_human`) | — | — |
| `T003_new_contributor_messy` | T | ✓ `vouching_required` (gold `vouching_required`) | — | — |
| `T004_readme_typo` | T | ✓ `likely_low_value` (gold `likely_low_value`) | — | — |
| `T005_drive_by_reformat` | T | ✓ `likely_low_value` (gold `likely_low_value`) | — | — |
| `T006_large_security_fix` | T | ✓ `needs_human` (gold `needs_human`) | — | — |
| `T007_chore_with_tests` | T | ✗ `needs_human` (gold `likely_low_value`) | — | WRONG_TRIAGE_UP |
| `T008_silent_schema_drop` | T | ✓ `needs_human` (gold `needs_human`) | — | — |
| `T009_midsize_feature` | T | ✗ `needs_human` (gold `vouching_required`) | — | WRONG_TRIAGE_UP |
| `T010_lockfile_bump` | T | ✓ `likely_low_value` (gold `likely_low_value`) | — | — |

## Notes

- Precision uses **valid-extras** by default (unmatched but plausible findings are not auto-penalized).
- Finding match is lexical/anchor-based unless an LLM judge is wired later. Treat F1 as harness-relative.
- Budgeted capture ranks by SUT `triage_score` and measures recall of `needs_human` gold in the top slice.
- A perfect 1.0 on this suite is a smell: the seed set is built so cheap strategies miss.
