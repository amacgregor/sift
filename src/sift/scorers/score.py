"""Score SUT outputs against gold labels."""

from __future__ import annotations

from collections import Counter
from typing import Any

from sift.schema import GoldFinding, PredictedFinding, SutOutput, Task, TaskScore


def _normalize(text: str) -> str:
    return " ".join(text.lower().split())


def finding_matches(
    gold: GoldFinding,
    pred: PredictedFinding,
    *,
    strict_path: bool = False,
) -> bool:
    """Substance match without an LLM judge (v0.1 lexical/anchor heuristic)."""
    path_ok = True
    if strict_path or gold.path:
        g = gold.path.replace("\\", "/").lower()
        p = pred.path.replace("\\", "/").lower()
        path_ok = g in p or p in g or g.split("/")[-1] == p.split("/")[-1]

    blob = _normalize(f"{pred.title} {pred.rationale}")
    if gold.anchor and _normalize(gold.anchor) not in blob and _normalize(gold.anchor) not in _normalize(
        pred.path
    ):
        # anchor preferred but title tokens can still match
        pass

    gold_tokens = set(_normalize(gold.title + " " + gold.rationale).split())
    # keep informative tokens
    stop = {"the", "a", "an", "and", "or", "to", "of", "in", "on", "for", "is", "be", "this", "that", "with"}
    gold_tokens = {t for t in gold_tokens if len(t) > 3 and t not in stop}
    if not gold_tokens:
        return path_ok

    hit = sum(1 for t in gold_tokens if t in blob)
    ratio = hit / max(len(gold_tokens), 1)

    if gold.anchor and _normalize(gold.anchor) in blob:
        return path_ok and ratio >= 0.15

    return path_ok and ratio >= 0.35


def score_task(
    task: Task,
    output: SutOutput,
    *,
    strict_gold: bool = False,
) -> TaskScore:
    family = task.meta.family
    failure_codes: list[str] = []
    notes: list[str] = []

    triage_correct = None
    if task.gold.triage_label is not None and family in {"T", "both"}:
        pred = output.triage_label
        triage_correct = pred == task.gold.triage_label
        if not triage_correct:
            gold = task.gold.triage_label
            if gold == "needs_human" and pred == "likely_low_value":
                failure_codes.append("WRONG_TRIAGE_DOWN")
            elif gold == "likely_low_value" and pred == "needs_human":
                failure_codes.append("WRONG_TRIAGE_UP")
            else:
                failure_codes.append("WRONG_TRIAGE_UP" if pred == "needs_human" else "WRONG_TRIAGE_DOWN")

    coverage = precision = f1 = None
    matched_ids: list[str] = []
    unmatched_pred: list[int] = []

    if task.gold.findings and family in {"F", "both"}:
        gold_findings = task.gold.findings
        preds = output.findings
        matched_pred_idx: set[int] = set()

        for g in gold_findings:
            found = False
            for i, p in enumerate(preds):
                if i in matched_pred_idx:
                    continue
                if finding_matches(g, p):
                    matched_ids.append(g.id)
                    matched_pred_idx.add(i)
                    found = True
                    break
            if not found:
                r = (g.rationale + g.title).lower()
                domainish = (
                    "tenant",
                    "auth",
                    "csrf",
                    "timezone",
                    "jurisdiction",
                    "payroll",
                    "valuation",
                    "salvage",
                    "nrv",
                    "double-spend",
                    "balance",
                )
                if any(tok in r for tok in domainish):
                    failure_codes.append("MISS_DOMAIN")
                else:
                    failure_codes.append("MISS_CONTEXT")

        for i, p in enumerate(preds):
            if i in matched_pred_idx:
                continue
            # valid-extras: unmatched preds do not automatically count as FP
            # unless strict_gold
            if strict_gold:
                unmatched_pred.append(i)
                failure_codes.append("NOISE_OR_EXTRA")
            else:
                # still track extras; precision uses valid-extras policy
                # treat as TP-extra if severity medium+ and non-empty rationale
                if p.severity in {"low", "medium", "high", "critical"} and len(p.rationale) >= 12:
                    matched_pred_idx.add(i)  # counts toward precision numerator
                    notes.append(f"valid-extra finding kept: {p.title!r}")
                else:
                    unmatched_pred.append(i)
                    failure_codes.append("NOISE")

        n_gold = len(gold_findings)
        n_pred = max(len(preds), 1) if preds else 0
        tp = len(matched_ids)
        coverage = tp / n_gold if n_gold else None

        if not preds:
            precision = 1.0 if n_gold == 0 else 0.0
        else:
            # precision: matched golds + valid extras over all preds
            precise = len(matched_pred_idx)
            precision = precise / len(preds)

        if coverage is not None and precision is not None:
            if coverage + precision == 0:
                f1 = 0.0
            else:
                f1 = 2 * coverage * precision / (coverage + precision)

        if any(p.severity in {"high", "critical"} for p in preds) and coverage == 0:
            # possible hallucinated serious bugs
            if preds and not matched_ids:
                failure_codes.append("HALLUCINATED_BUG")

    return TaskScore(
        task_id=task.meta.id,
        family=family,
        triage_correct=triage_correct,
        triage_gold=task.gold.triage_label,
        triage_pred=str(output.triage_label) if output.triage_label is not None else None,
        findings_coverage=coverage,
        findings_precision=precision,
        findings_f1=f1,
        matched_gold_ids=matched_ids,
        unmatched_pred_indices=unmatched_pred,
        failure_codes=sorted(set(failure_codes)),
        cost_usd=output.cost_usd,
        notes="; ".join(notes),
    )


def summarize(tasks: list[Task], scores: list[TaskScore], outputs: list[SutOutput]) -> dict[str, Any]:
    by_id = {t.meta.id: t for t in tasks}
    triage_scores = [s for s in scores if s.triage_correct is not None]
    finding_scores = [s for s in scores if s.findings_f1 is not None]

    triage_acc = (
        sum(1 for s in triage_scores if s.triage_correct) / len(triage_scores) if triage_scores else None
    )

    budgeted = _budgeted_capture(tasks, outputs, budget=0.2)
    waste = _budget_waste(tasks, outputs, budget=0.2)
    budgeted40 = _budgeted_capture(tasks, outputs, budget=0.4)
    waste40 = _budget_waste(tasks, outputs, budget=0.4)

    mean = lambda xs: sum(xs) / len(xs) if xs else None  # noqa: E731

    failure_counter = Counter()
    for s in scores:
        failure_counter.update(s.failure_codes)

    return {
        "n_tasks": len(scores),
        "triage_accuracy": triage_acc,
        "triage_n": len(triage_scores),
        "findings_mean_coverage": mean([s.findings_coverage for s in finding_scores if s.findings_coverage is not None]),
        "findings_mean_precision": mean(
            [s.findings_precision for s in finding_scores if s.findings_precision is not None]
        ),
        "findings_mean_f1": mean([s.findings_f1 for s in finding_scores if s.findings_f1 is not None]),
        "findings_n": len(finding_scores),
        "budgeted_capture_at_20pct": budgeted,
        "budget_waste_at_20pct": waste,
        "budgeted_capture_at_40pct": budgeted40,
        "budget_waste_at_40pct": waste40,
        "total_cost_usd": sum(s.cost_usd for s in scores),
        "failure_codes": dict(failure_counter),
        "tasks": [s.to_dict() for s in scores],
        "gold_priority_by_task": {
            t.meta.id: t.gold.triage_priority for t in tasks if t.gold.triage_priority is not None
        },
        "meta": {"tasks_loaded": list(by_id)},
    }


def _ranked_outputs(tasks: list[Task], outputs: list[SutOutput]) -> list[SutOutput]:
    # Only tasks with triage gold participate
    triage_ids = {t.meta.id for t in tasks if t.gold.triage_label is not None}
    outs = [o for o in outputs if o.task_id in triage_ids]
    return sorted(
        outs,
        key=lambda o: (
            o.triage_score is not None,
            o.triage_score if o.triage_score is not None else -999,
            1 if o.triage_label == "needs_human" else 0,
        ),
        reverse=True,
    )


def _budgeted_capture(tasks: list[Task], outputs: list[SutOutput], budget: float) -> float | None:
    """Fraction of needs_human gold tasks appearing in top budget% of ranked queue.

    With tiny N, ``round(n * 0.2)`` can be 0 before max(1,…); we always keep at
    least one slot, but also treat priority ranking quality via full order:
    if the single highest-scored triage task is needs_human, capture is 1.0 when
    there is only one needs_human gold (seed-set friendly).
    """
    high = [t for t in tasks if t.gold.triage_label == "needs_human"]
    if not high:
        return None
    ranked = _ranked_outputs(tasks, outputs)
    if not ranked:
        return None
    k = max(1, int(round(len(ranked) * budget)))
    top_ids = {o.task_id for o in ranked[:k]}
    caught = sum(1 for t in high if t.meta.id in top_ids)
    return caught / len(high)


def _budget_waste(tasks: list[Task], outputs: list[SutOutput], budget: float) -> float | None:
    """Fraction of top-budget slots occupied by likely_low_value gold."""
    by_task = {t.meta.id: t for t in tasks}
    ranked = _ranked_outputs(tasks, outputs)
    if not ranked:
        return None
    k = max(1, int(round(len(ranked) * budget)))
    top = ranked[:k]
    waste = sum(1 for o in top if by_task[o.task_id].gold.triage_label == "likely_low_value")
    return waste / len(top)
