"""Pack loader and run CLI, using test fixtures only."""

from __future__ import annotations

from pathlib import Path

from sift.cli import main
from sift.tasks import load_tasks


def test_load_seed_fixture(seed_dir: Path):
    tasks = load_tasks(tasks_dir=seed_dir)
    assert len(tasks) >= 3
    ids = {t.meta.id for t in tasks}
    assert "T001_bulk_ai_rewrite" in ids


def test_run_heuristic_on_fixture_pack(seed_dir: Path, tmp_path: Path):
    out = tmp_path / "run"
    rc = main(
        [
            "run",
            "--sut",
            "heuristic",
            "--tasks-dir",
            str(seed_dir),
            "--task",
            "T001_bulk_ai_rewrite",
            "--task",
            "T002_authz_bugfix",
            "--out",
            str(out),
        ]
    )
    assert rc == 0
    assert (out / "report.md").is_file()
    text = (out / "report.md").read_text()
    assert "T001_bulk_ai_rewrite" in text
    assert "T002_authz_bugfix" in text
