"""Smoke tests: heuristic SUT runs and scores all seed tasks."""

from __future__ import annotations

from sift.scorers import score_task, summarize
from sift.suts import get_sut
from sift.tasks import list_task_ids, load_tasks


def test_seed_task_count():
    ids = list_task_ids()
    assert len(ids) == 5
    assert "T001_bulk_ai_rewrite" in ids
    assert "F001_missing_tenant" in ids


def test_heuristic_runs_all_tasks():
    tasks = load_tasks()
    sut = get_sut("heuristic")
    outputs = [sut.run(t) for t in tasks]
    scores = [score_task(t, o) for t, o in zip(tasks, outputs)]
    summary = summarize(tasks, scores, outputs)

    assert summary["n_tasks"] == 5
    assert summary["total_cost_usd"] == 0.0

    by_id = {s.task_id: s for s in scores}

    # T001 should be low-value
    assert by_id["T001_bulk_ai_rewrite"].triage_correct is True

    # T002 security fix should be needs_human
    assert by_id["T002_authz_bugfix"].triage_correct is True

    # T003 new contributor messy → vouching
    assert by_id["T003_new_contributor_messy"].triage_correct is True

    # F001 missing tenant should get full findings coverage
    assert by_id["F001_missing_tenant"].findings_coverage is not None
    assert by_id["F001_missing_tenant"].findings_coverage >= 1.0

    # F002 API parity should be detected by heuristic
    assert by_id["F002_api_parity"].findings_coverage is not None
    assert by_id["F002_api_parity"].findings_coverage >= 1.0

    # Ranking metric is stricter than label accuracy on tiny N — security
    # fix should outrank noise when budget is a single slot (~20% of 3).
    assert summary["budgeted_capture_at_20pct"] == 1.0
    assert summary["budget_waste_at_20pct"] == 0.0
