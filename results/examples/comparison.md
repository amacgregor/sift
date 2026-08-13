# Sift comparison

Same tasks, different strategy. The interesting result is the delta — not a model ranking.

| Metric | `heuristic` | `checklist` |
|---|---|---|
| Tasks | 18 | 18 |
| Triage accuracy | 0.600 | 0.800 |
| Capture @ 20% | 0.333 | 0.667 |
| Waste @ 20% | 0.000 | 0.000 |
| Capture @ 40% | 0.333 | 1.000 |
| Waste @ 40% | 0.250 | 0.000 |
| Findings coverage | 0.250 | 0.750 |
| Findings precision | 0.375 | 0.750 |
| Findings F1 | 0.250 | 0.750 |
| Cost (USD) | 0.000 | 0.000 |

## Where `checklist` differs from `heuristic`

- `F003_csrf_dropped` findings F1: `0.000` → `1.000`
- `F004_jurisdiction_tz` findings F1: `0.000` → `1.000`
- `F005_check_then_act` findings F1: `0.000` → `1.000`
- `F006_auth_header_log` findings F1: `0.000` → `1.000`
- `T006_large_security_fix` triage: `heuristic` ✗ `vouching_required` → `checklist` ✓ `needs_human` (gold `needs_human`)
- `T008_silent_schema_drop` triage: `heuristic` ✗ `likely_low_value` → `checklist` ✓ `needs_human` (gold `needs_human`)

## How to read this

If capture and coverage move when you swap *strategy* (structural heuristic vs domain checklist) and cost stays $0, the suite is doing its job. That is the ReviewBench lesson: harness and review strategy move scores as much as the model logo.
