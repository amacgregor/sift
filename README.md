# Sift

A small harness for **PR triage and review findings**.

You point it at a **diff**. It runs a strategy (structural heuristic, or an LLM).
It prints a label, a score, and any findings. If you also have a task pack with
gold labels, it can score a SUT. The pack is data you bring. It is not this repo.

## Review a real diff (the default path)

```bash
cd sift
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"

git diff main | python -m sift.cli review --title "fix: …" --body "…"
# or
python -m sift.cli review --diff path/to/change.patch --title "…"
```

No task pack. No gold. The heuristic looks at size, file count, description, tests,
and a couple of shallow diff patterns (tenant-less `get_by_id`, dropped `is_active`
filter). It does not know about any fixture in this repository.

```bash
python -m sift.cli review --diff change.patch --json
```

## Score a pack (optional)

A pack is a directory of task folders (`task.json`, `diff.patch`, optional `gold.json`
and `context/`). Nothing in the installed package points at one.

```bash
python -m sift.cli list --tasks-dir /path/to/pack
python -m sift.cli run --sut heuristic --tasks-dir /path/to/pack --out results/latest
python -m sift.cli compare --suts heuristic,llm --tasks-dir /path/to/pack
```

Or `export SIFT_TASKS_DIR=/path/to/pack`.

`tests/fixtures/seed/` is **test data** for the loader and scorer. It is not a
benchmark and not a product result.

## SUTs

| Name | What it is | Key |
|---|---|---|
| `heuristic` | Structural signals | No |
| `llm` | One-shot JSON review | Yes |
| `llm_structured` | Same model; file → invariant → finding | Yes |

```bash
pip install -e ".[llm]"
export OPENAI_API_KEY=…
python -m sift.cli review --sut llm --diff change.patch
```

## Pack format

```text
my-pack/
  some_id/
    task.json      # id, family (T|F|both), title, pr_title, pr_body, …
    diff.patch     # unified diff
    gold.json      # optional: triage_label, findings[]
    context/       # optional extra files
```

If `files_changed` / `additions` / `deletions` are omitted, they are parsed from the
diff.

## What this is not

- Not a leaderboard
- Not an independent measurement of “review quality”
- Not a catalog of planted bugs with a matching regex SUT

Metrics and gold rules: [`METHODOLOGY.md`](./METHODOLOGY.md).

## License

MIT — see [LICENSE](./LICENSE).
