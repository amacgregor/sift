# Sift

Separate signal from noise in AI-era code review.

**Eval harness for the scarce layer around AI code review:** whether systems
allocate **human attention** correctly, and whether **findings are substantively
right** — with **cost** as a first-class metric.

Not another 50-tool bug-finding leaderboard. A small, rigorous harness for
**triage + verification**.

```text
Family T  →  Is this PR worth a human's time?
Family F  →  Did we catch real issues without drowning in noise?
```

## Quick start (no API key)

```bash
cd sift
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

# list seed tasks
python -m sift.cli list

# run structural baseline on all tasks
python -m sift.cli run --sut heuristic --out results/latest
```

Open `results/latest/report.md`.

### Optional LLM SUT

```bash
pip install -e ".[llm]"
export OPENAI_API_KEY=...
python -m sift.cli run --sut llm --out results/llm
```

## Seed tasks (v0.1)

| ID | Family | What it tests |
|---|---|---|
| `T001_bulk_ai_rewrite` | T | Huge low-signal rewrite → `likely_low_value` |
| `T002_authz_bugfix` | T | Focused security fix + tests → `needs_human` |
| `T003_new_contributor_messy` | T | Real small fix, new author → `vouching_required` |
| `F001_missing_tenant` | F | New admin purge without tenant scope |
| `F002_api_parity` | F | v2 migration drops `is_active` filter |

## Design locks

| Decision | Choice |
|---|---|
| Runner | Tiny custom Python CLI (Inspect-shaped tasks later) |
| Name | `sift` |
| Precision | Valid-extras default; `--strict-gold` optional |
| Languages | Python + TypeScript fixtures |
| License | MIT |
| Shield data | Not included |

Full research, goals, and scope: [`../HARNESS.md`](../HARNESS.md).

## Why this exists

Frontier labs and AI-native teams are not short on model demos. They are short on people who can **measure** whether agentic review systems work under real attention constraints.

Sift is a portfolio-grade, demoable artifact for that claim:

1. Explicit gold + rationales  
2. Budgeted capture (attention is scarce)  
3. Precision policy you can defend  
4. Failure taxonomy  
5. Heuristic vs LLM comparison path  

## Project layout

```text
tasks/           seed fixtures (task.json, gold.json, diff.patch, context/)
src/sift/  runner, SUTs, scorers, report
tests/           smoke tests for heuristic suite
results/         run outputs (gitignored except examples)
METHODOLOGY.md   scoring and limitations
```

## Status

**v0.1 scaffold** — 5 seed tasks, heuristic + optional LLM SUTs, markdown report.  
Next: grow to 12–25 tasks, LLM-as-judge scorer, structured-review strategy ablation.

## License

MIT — see [LICENSE](./LICENSE).
