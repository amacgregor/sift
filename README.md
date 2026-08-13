# Sift

Separate signal from noise in AI-era code review.

An eval harness for the **attention and verification layer**: whether systems
allocate scarce human review correctly, and whether findings are substantively
right — with **cost as a first-class metric**.

Not another 50-tool bug-finding leaderboard. A small, finished slice.

```text
Family T  →  Is this PR worth a human's time?
Family F  →  Did we catch real issues without drowning in noise?
```

## Quick start (no API key, ~30 seconds)

```bash
git clone https://github.com/amacgregor/sift.git
cd sift
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

python -m sift.cli compare --suts heuristic,checklist
```

Open `results/compare/comparison.md`. That file is the demo.

Checked-in sample: [`results/examples/comparison.md`](results/examples/comparison.md).

## What the seed set shows

18 synthetic tasks (10 triage, 8 findings). Two zero-key systems under test:

| SUT | What it is |
|---|---|
| `heuristic` | Size, file count, tests, chore language — Circuit Breaker–style structure |
| `checklist` | The same signals, plus a short domain catalog (CSRF, tenancy, TZ, races, secrets, live schema) |

Same tasks, $0, strategy change only:

| Metric | heuristic | checklist |
|---|---|---|
| Triage accuracy | 0.60 | 0.80 |
| Budgeted capture @ 20% | 0.33 | 0.67 |
| Findings F1 | 0.25 | 0.75 |
| Cost (USD) | 0.00 | 0.00 |

What moved:

- A **large real session-fixation fix** (`T006`) was buried by the size heuristic and surfaced once session invariants were checked.
- A **“unused column” chore** (`T008`) was scored low-value until context showed payroll reports still group on that column.
- CSRF, naive `datetime.now()` on a pay-period close, a wallet race, and an `Authorization` header log went from F1 0 → 1.

What still misses on purpose:

- `F007` — default page size 20 → 1000 (implicit API contract).
- `F008` — salvage inventory valued at replacement cost instead of NRV.
- `T007` / `T009` — tests and “real feature” energy still over-admit some low/mid work.

A perfect 1.0 on this suite is a smell. The seed set is built so cheap strategies fail.

## Why this exists

Frontier labs and AI-native teams are not short on model demos. They are short on
people who can **measure** whether agentic review systems work under real
attention constraints.

Sift is a portfolio-grade, demoable artifact for that claim:

1. Explicit gold + written rationales
2. Budgeted capture (attention is the scarce resource)
3. A precision policy you can defend (valid-extras, `--strict-gold` for sensitivity)
4. A failure taxonomy (`WRONG_TRIAGE_DOWN`, `MISS_DOMAIN`, …)
5. Heuristic vs checklist vs (optional) LLM — strategy, not logo

## Commands

```bash
python -m sift.cli list
python -m sift.cli list --family T
python -m sift.cli run --sut heuristic --out results/latest
python -m sift.cli run --sut checklist --out results/checklist
python -m sift.cli compare --suts heuristic,checklist --out results/compare
```

Optional LLM SUTs (needs `pip install -e ".[llm]"` and `OPENAI_API_KEY`):

```bash
python -m sift.cli run --sut llm --model gpt-4o-mini
python -m sift.cli run --sut llm_structured --model gpt-4o-mini
```

`llm` is one-shot JSON. `llm_structured` forces file → invariant → finding order
on the **same model**. That is the second ablation; the first one does not need a key.

## Task set (dataset 0.2.0)

| ID | Family | Gold / point |
|---|---|---|
| `T001_bulk_ai_rewrite` | T | `likely_low_value` — volume, no plan |
| `T002_authz_bugfix` | T | `needs_human` — small, tested security fix |
| `T003_new_contributor_messy` | T | `vouching_required` |
| `T004_readme_typo` | T | `likely_low_value` |
| `T005_drive_by_reformat` | T | `likely_low_value` |
| `T006_large_security_fix` | T | `needs_human` — size is a bad proxy |
| `T007_chore_with_tests` | T | `likely_low_value` — tests inflate rank |
| `T008_silent_schema_drop` | T | `needs_human` — “unused” column is live |
| `T009_midsize_feature` | T | `vouching_required` |
| `T010_lockfile_bump` | T | `likely_low_value` |
| `F001_missing_tenant` | F | Purge by id, no tenant |
| `F002_api_parity` | F | v2 drops `is_active` |
| `F003_csrf_dropped` | F | CSRF removed, “gateway handles it” |
| `F004_jurisdiction_tz` | F | `datetime.now()` closes Quebec pay periods |
| `F005_check_then_act` | F | Wallet debit race |
| `F006_auth_header_log` | F | Logs `Authorization` |
| `F007_default_page_size` | F | Contract break; residual miss |
| `F008_inventory_salvage` | F | NRV vs replacement cost; residual miss |

Gold process, metrics, limitations: [`METHODOLOGY.md`](./METHODOLOGY.md).  
3-minute walkthrough: [`DEMO.md`](./DEMO.md).

## Design locks

| Decision | Choice |
|---|---|
| Runner | Tiny custom Python CLI (Inspect-shaped later) |
| Name | `sift` |
| Precision | Valid-extras default; `--strict-gold` optional |
| Languages | Python + TypeScript fixtures |
| License | MIT |
| Shield / LiORA data | **Not included** |

## Status

**0.2.0** — 18 tasks, heuristic + checklist ablation, optional LLM / structured-LLM
SUTs, comparison report. Finding match is lexical (no LLM judge) so the suite is
reproducible with zero keys.

## License

MIT — see [LICENSE](./LICENSE).
