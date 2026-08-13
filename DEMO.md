# 3-minute demo script

For a hiring manager. Do not clone on their laptop unless they ask.

## 0:00 — the claim (20s)

> I didn’t build another review-tool leaderboard. I built a small harness around
> the bottleneck I actually care about: **does this system spend scarce human
> attention on the right PRs, and are the findings substantively right?**

Open [`results/examples/comparison.md`](results/examples/comparison.md).

## 0:20 — the number that moved (60s)

Point at the table:

- heuristic capture @ 20%: **0.33**
- checklist capture @ 20%: **0.67**
- findings F1: **0.25 → 0.75**
- cost: **$0 → $0**

> Same tasks. No model. The only change is review *strategy*: size/tests/chore
> language versus a short domain catalog.

Name two tasks without scrolling the whole suite:

1. **`T006`** — a real session-fixation fix, 28 files. The size heuristic buried it
   (`vouching_required`). Checking session invariants promoted it to `needs_human`.
2. **`T008`** — “chore: drop unused column.” Context still groups payroll filings
   on that column. Heuristic said `likely_low_value`. Checklist said `needs_human`.

## 1:20 — what we refuse to claim (40s)

> Eighteen synthetic tasks. Lexical matcher, not an LLM judge. Not comparable to
> Martian CRB. Two findings are held out on purpose: a page-size contract break
> and a salvage-vs-NRV valuation bug. A 1.0 here would mean I overfit the suite.

If they want the gold rule: *nits are not gold. Every label has a written why.*

## 2:00 — live run if they want it (40s)

```bash
python -m sift.cli compare --suts heuristic,checklist
```

Or one task:

```bash
python -m sift.cli run --sut heuristic --task T008_silent_schema_drop
python -m sift.cli run --sut checklist --task T008_silent_schema_drop
```

## 2:40 — close (20s)

> The interesting result isn’t a model ranking. Changing what you look for, and
> measuring budgeted capture, moves the number more than swapping the logo on
> the API call. That’s the eval job.

If they ask about LLM SUTs: `llm` vs `llm_structured` is the same experiment with
a key. Not required for the demo.
