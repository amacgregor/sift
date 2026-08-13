# Changelog

## 0.3.0 — 2026-08-13

- The product is a harness, not a planted suite.
- `sift review` runs a SUT on a live unified diff. No pack, no gold.
- `--tasks-dir` / `SIFT_TASKS_DIR` required for pack mode. Nothing in the package
  points at a default `tasks/` tree.
- Seed PRs moved to `tests/fixtures/seed/` (test data only).
- Removed the `checklist` SUT. It was a regex catalog of those fixtures.

## 0.2.0 — 2026-08-13

- 18 synthetic tasks and a checklist ablation. Retracted as a product result.

## 0.1.0 — 2026-08-12

- Scaffold, heuristic + one-shot LLM SUT, lexical scorer.
