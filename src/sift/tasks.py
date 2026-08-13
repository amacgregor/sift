"""Load a task pack, or build a task from a live diff."""

from __future__ import annotations

import json
import os
from pathlib import Path

from sift.schema import Gold, GoldFinding, Task, TaskMeta


def resolve_tasks_dir(tasks_dir: str | Path | None = None) -> Path:
    raw = tasks_dir or os.environ.get("SIFT_TASKS_DIR")
    if raw:
        path = Path(raw).expanduser().resolve()
        if not path.is_dir():
            raise FileNotFoundError(f"Tasks directory not found: {path}")
        return path
    raise FileNotFoundError(
        "No task pack. Pass --tasks-dir / set SIFT_TASKS_DIR, or use `sift review` on a diff."
    )


def parse_diff_stats(diff: str) -> tuple[int, int, int]:
    """files_changed, additions, deletions from a unified diff."""
    files: set[str] = set()
    adds = dels = 0
    for line in diff.splitlines():
        if line.startswith("+++ b/"):
            files.add(line[6:].strip())
        elif line.startswith("--- a/"):
            files.add(line[6:].strip())
        elif line.startswith("+") and not line.startswith("+++"):
            adds += 1
        elif line.startswith("-") and not line.startswith("---"):
            dels += 1
    return max(len(files), 1 if diff.strip() else 0), adds, dels


def task_from_diff(
    diff: str,
    *,
    title: str = "",
    body: str = "",
    author: str = "unknown",
    language: str = "",
) -> Task:
    files_changed, additions, deletions = parse_diff_stats(diff)
    return Task(
        meta=TaskMeta(
            id="review",
            family="both",
            title=title or "(untitled diff)",
            language=language or "unknown",
            tags=["live"],
            difficulty=1,
            source="live",
            license_note="caller-provided",
        ),
        pr_title=title or "(untitled diff)",
        pr_body=body,
        author=author,
        files_changed=files_changed,
        additions=additions,
        deletions=deletions,
        diff=diff,
        context_files={},
        gold=Gold(),
    )


def _load_one(task_dir: Path) -> Task:
    meta_path = task_dir / "task.json"
    gold_path = task_dir / "gold.json"
    diff_path = task_dir / "diff.patch"
    context_dir = task_dir / "context"

    meta_raw = json.loads(meta_path.read_text())
    gold_raw = json.loads(gold_path.read_text()) if gold_path.exists() else {}
    diff = diff_path.read_text() if diff_path.exists() else ""

    context_files: dict[str, str] = {}
    if context_dir.is_dir():
        for p in sorted(context_dir.rglob("*")):
            if p.is_file():
                rel = str(p.relative_to(context_dir))
                context_files[rel] = p.read_text()

    findings = [
        GoldFinding(
            id=f["id"],
            path=f["path"],
            title=f["title"],
            severity=f["severity"],
            rationale=f["rationale"],
            anchor=f.get("anchor"),
        )
        for f in gold_raw.get("findings", [])
    ]

    gold = Gold(
        triage_label=gold_raw.get("triage_label"),
        triage_priority=gold_raw.get("triage_priority"),
        findings=findings,
        rationale=gold_raw.get("rationale", ""),
    )

    files_changed = meta_raw.get("files_changed")
    additions = meta_raw.get("additions")
    deletions = meta_raw.get("deletions")
    if files_changed is None or additions is None or deletions is None:
        parsed = parse_diff_stats(diff)
        files_changed = files_changed if files_changed is not None else parsed[0]
        additions = additions if additions is not None else parsed[1]
        deletions = deletions if deletions is not None else parsed[2]

    meta = TaskMeta(
        id=meta_raw["id"],
        family=meta_raw["family"],
        title=meta_raw["title"],
        language=meta_raw.get("language", "unknown"),
        tags=meta_raw.get("tags", []),
        difficulty=meta_raw.get("difficulty", 1),
        source=meta_raw.get("source", "pack"),
        license_note=meta_raw.get("license_note", ""),
    )

    return Task(
        meta=meta,
        pr_title=meta_raw.get("pr_title", meta.title),
        pr_body=meta_raw.get("pr_body", ""),
        author=meta_raw.get("author", "unknown"),
        files_changed=int(files_changed),
        additions=int(additions),
        deletions=int(deletions),
        diff=diff,
        context_files=context_files,
        gold=gold,
    )


def load_tasks(
    task_ids: list[str] | None = None,
    *,
    tasks_dir: str | Path | None = None,
) -> list[Task]:
    root = resolve_tasks_dir(tasks_dir)
    dirs = sorted(p for p in root.iterdir() if p.is_dir() and not p.name.startswith("."))
    tasks = [_load_one(d) for d in dirs if (d / "task.json").exists()]
    if task_ids:
        wanted = set(task_ids)
        tasks = [t for t in tasks if t.meta.id in wanted]
        missing = wanted - {t.meta.id for t in tasks}
        if missing:
            raise ValueError(f"Unknown task ids: {sorted(missing)}")
    return tasks


def list_task_ids(*, tasks_dir: str | Path | None = None) -> list[str]:
    return [t.meta.id for t in load_tasks(tasks_dir=tasks_dir)]
