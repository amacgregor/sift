"""compare CLI writes per-SUT reports plus a delta table."""

from __future__ import annotations

from pathlib import Path

from sift.cli import main


def test_compare_heuristic_checklist(tmp_path: Path):
    out = tmp_path / "cmp"
    rc = main(["compare", "--suts", "heuristic,checklist", "--out", str(out)])
    assert rc == 0
    assert (out / "comparison.md").is_file()
    assert (out / "heuristic" / "report.md").is_file()
    assert (out / "checklist" / "report.md").is_file()
    text = (out / "comparison.md").read_text()
    assert "Capture @ 20%" in text
    assert "`heuristic`" in text
    assert "`checklist`" in text


def test_list_family_filter():
    # smoke: list returns 0
    assert main(["list"]) == 0
    assert main(["list", "--family", "T"]) == 0
