"""Heuristic and checklist SUTs against the v0.2 seed set (no API key)."""

from __future__ import annotations

from sift.scorers import score_task, summarize
from sift.suts import get_sut
from sift.tasks import list_task_ids, load_tasks


def _run(name: str):
    tasks = load_tasks()
    sut = get_sut(name)
    outputs = [sut.run(t) for t in tasks]
    scores = [score_task(t, o) for t, o in zip(tasks, outputs)]
    return tasks, outputs, scores, summarize(tasks, scores, outputs)


def test_seed_task_count():
    ids = list_task_ids()
    assert len(ids) == 18
    assert "T001_bulk_ai_rewrite" in ids
    assert "T010_lockfile_bump" in ids
    assert "F001_missing_tenant" in ids
    assert "F008_inventory_salvage" in ids


def test_heuristic_known_wins_and_designed_misses():
    _tasks, _outs, scores, summary = _run("heuristic")
    by_id = {s.task_id: s for s in scores}

    assert summary["n_tasks"] == 18
    assert summary["total_cost_usd"] == 0.0

    assert by_id["T001_bulk_ai_rewrite"].triage_correct is True
    assert by_id["T002_authz_bugfix"].triage_correct is True
    assert by_id["T003_new_contributor_messy"].triage_correct is True
    assert by_id["T004_readme_typo"].triage_correct is True
    assert by_id["T005_drive_by_reformat"].triage_correct is True
    assert by_id["T010_lockfile_bump"].triage_correct is True

    # Size/chore proxies fail on purpose
    assert by_id["T006_large_security_fix"].triage_correct is False
    assert by_id["T007_chore_with_tests"].triage_correct is False
    assert by_id["T008_silent_schema_drop"].triage_correct is False

    assert by_id["F001_missing_tenant"].findings_coverage == 1.0
    assert by_id["F002_api_parity"].findings_coverage == 1.0
    assert by_id["F008_inventory_salvage"].findings_coverage == 0.0

    # Suite is no longer a perfect 1.0 — that was the scaffold smell
    assert summary["budgeted_capture_at_20pct"] < 1.0
    assert summary["findings_mean_coverage"] < 1.0


def test_checklist_improves_strategy_without_raising_cost():
    _ht, _ho, h_scores, h_sum = _run("heuristic")
    _ct, _co, c_scores, c_sum = _run("checklist")
    h = {s.task_id: s for s in h_scores}
    c = {s.task_id: s for s in c_scores}

    assert c_sum["total_cost_usd"] == 0.0
    assert c["T006_large_security_fix"].triage_correct is True
    assert c["T008_silent_schema_drop"].triage_correct is True
    assert c["F003_csrf_dropped"].findings_coverage == 1.0
    assert c["F006_auth_header_log"].findings_coverage == 1.0

    # Residual domain miss: salvage vs NRV
    assert c["F008_inventory_salvage"].findings_coverage == 0.0

    assert c_sum["budgeted_capture_at_20pct"] >= h_sum["budgeted_capture_at_20pct"]
    assert c_sum["findings_mean_coverage"] > h_sum["findings_mean_coverage"]

    # Heuristic still wins the easy structural ones; checklist must not regress them
    assert c["T001_bulk_ai_rewrite"].triage_correct is True
    assert c["T002_authz_bugfix"].triage_correct is True
    assert h["F001_missing_tenant"].findings_coverage == 1.0
    assert c["F001_missing_tenant"].findings_coverage == 1.0
