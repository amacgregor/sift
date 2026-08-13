"""Heuristic responds to structural signals, not task ids."""

from __future__ import annotations

from sift.schema import Gold, Task, TaskMeta
from sift.suts.heuristic import HeuristicSut


def _task(**kwargs) -> Task:
    defaults = dict(
        meta=TaskMeta(
            id="x",
            family="T",
            title="t",
            language="python",
            tags=[],
            difficulty=1,
            source="test",
            license_note="",
        ),
        pr_title="t",
        pr_body="",
        author="core-maintainer",
        files_changed=2,
        additions=10,
        deletions=4,
        diff="",
        context_files={},
        gold=Gold(),
    )
    defaults.update(kwargs)
    return Task(**defaults)


def test_large_unexplained_diff_is_low_value():
    out = HeuristicSut().run(
        _task(
            pr_body="Updated several modules.",
            files_changed=34,
            additions=920,
            deletions=640,
        )
    )
    assert out.triage_label == "likely_low_value"
    assert out.triage_score is not None and out.triage_score < 0


def test_small_tested_security_fix_is_needs_human():
    out = HeuristicSut().run(
        _task(
            pr_body="Root cause: missing authz. Plan: add tenant scope. Security fix. Added regression tests.",
            files_changed=2,
            additions=20,
            deletions=5,
            diff="+++ b/tests/test_auth.py\n+def test_cross_tenant():\n+    pass\n",
        )
    )
    assert out.triage_label == "needs_human"


def test_new_author_without_security_is_vouching():
    out = HeuristicSut().run(
        _task(
            author="first-time-contributor",
            pr_body="hi this fixes a crash when the list is empty. tested locally.",
            files_changed=2,
            additions=18,
            deletions=4,
            diff="+++ b/src/list.test.ts\n+test('empty', () => {})\n",
        )
    )
    assert out.triage_label == "vouching_required"
