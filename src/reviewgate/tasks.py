"""Load seed tasks from the tasks/ directory."""

from __future__ import annotations

import json
from pathlib import Path

from reviewgate.schema import Gold, GoldFinding, Task, TaskMeta

ROOT = Path(__file__).resolve().parents[2]
TASKS_DIR = ROOT / "tasks"


def _load_one(task_dir: Path) -> Task:
    meta_path = task_dir / "task.json"
    gold_path = task_dir / "gold.json"
    diff_path = task_dir / "diff.patch"
    context_dir = task_dir / "context"

    meta_raw = json.loads(meta_path.read_text())
    gold_raw = json.loads(gold_path.read_text())
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

    meta = TaskMeta(
        id=meta_raw["id"],
        family=meta_raw["family"],
        title=meta_raw["title"],
        language=meta_raw["language"],
        tags=meta_raw.get("tags", []),
        difficulty=meta_raw.get("difficulty", 1),
        source=meta_raw.get("source", "synthetic"),
        license_note=meta_raw.get("license_note", "synthetic CC0-equivalent"),
    )

    return Task(
        meta=meta,
        pr_title=meta_raw["pr_title"],
        pr_body=meta_raw.get("pr_body", ""),
        author=meta_raw.get("author", "unknown"),
        files_changed=meta_raw.get("files_changed", 0),
        additions=meta_raw.get("additions", 0),
        deletions=meta_raw.get("deletions", 0),
        diff=diff,
        context_files=context_files,
        gold=gold,
    )


def load_tasks(task_ids: list[str] | None = None) -> list[Task]:
    if not TASKS_DIR.is_dir():
        raise FileNotFoundError(f"Tasks directory not found: {TASKS_DIR}")

    dirs = sorted(p for p in TASKS_DIR.iterdir() if p.is_dir() and not p.name.startswith("."))
    tasks = [_load_one(d) for d in dirs]
    if task_ids:
        wanted = set(task_ids)
        tasks = [t for t in tasks if t.meta.id in wanted]
        missing = wanted - {t.meta.id for t in tasks}
        if missing:
            raise ValueError(f"Unknown task ids: {sorted(missing)}")
    return tasks


def list_task_ids() -> list[str]:
    return [t.meta.id for t in load_tasks()]
