"""Render markdown reports from suite summaries or a single live review."""

from __future__ import annotations

from typing import Any

from sift.schema import SutOutput


def _fmt(v: Any) -> str:
    if v is None:
        return "—"
    if isinstance(v, float):
        return f"{v:.3f}"
    return str(v)


def render_review(out: SutOutput) -> str:
    lines = [
        f"# Sift review — `{out.sut}`",
        "",
        f"Triage: **{out.triage_label or '—'}**  score={_fmt(out.triage_score)}  "
        f"latency={out.latency_ms}ms  cost=${out.cost_usd:.4f}",
        "",
    ]
    if out.triage_reasons:
        lines.append("Reasons:")
        lines.extend(f"- {r}" for r in out.triage_reasons)
        lines.append("")
    if out.findings:
        lines += ["Findings:", ""]
        for f in out.findings:
            lines.append(f"- **{f.severity}** `{f.path}` — {f.title}")
            if f.rationale:
                lines.append(f"  {f.rationale}")
        lines.append("")
    else:
        lines += ["Findings: _none_", ""]
    return "\n".join(lines)


def render_markdown(summary: dict[str, Any], *, sut: str) -> str:
    n = summary["n_tasks"]
    lines = [
        f"# Sift report — `{sut}`",
        "",
        f"Tasks: **{n}**",
        "",
        "## Headline metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]

    rows = [
        ("Triage accuracy", summary.get("triage_accuracy")),
        ("Budgeted capture @ 20%", summary.get("budgeted_capture_at_20pct")),
        ("Budget waste @ 20%", summary.get("budget_waste_at_20pct")),
        ("Budgeted capture @ 40%", summary.get("budgeted_capture_at_40pct")),
        ("Budget waste @ 40%", summary.get("budget_waste_at_40pct")),
        ("Findings mean coverage", summary.get("findings_mean_coverage")),
        ("Findings mean precision", summary.get("findings_mean_precision")),
        ("Findings mean F1", summary.get("findings_mean_f1")),
        ("Total cost (USD)", summary.get("total_cost_usd")),
    ]
    for name, val in rows:
        lines.append(f"| {name} | {_fmt(val)} |")

    lines += ["", "## Failure codes", ""]
    fc = summary.get("failure_codes") or {}
    if not fc:
        lines.append("_None_")
    else:
        for code, n_code in sorted(fc.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- `{code}`: {n_code}")

    lines += ["", "## Per-task", "", "| Task | Family | Triage | Findings F1 | Failures |", "|---|---|---|---|---|"]
    for t in summary.get("tasks", []):
        triage = "—"
        if t.get("triage_correct") is not None:
            mark = "✓" if t["triage_correct"] else "✗"
            triage = f"{mark} `{t.get('triage_pred')}` (gold `{t.get('triage_gold')}`)"
        f1 = _fmt(t.get("findings_f1"))
        fails = ", ".join(t.get("failure_codes") or []) or "—"
        lines.append(f"| `{t['task_id']}` | {t['family']} | {triage} | {f1} | {fails} |")

    lines += [
        "",
        "## Notes",
        "",
        "- Precision uses **valid-extras** by default. `--strict-gold` treats extras as false positives.",
        "- Finding match is lexical/anchor-based. Treat F1 as harness-relative.",
        "- Budgeted capture ranks by SUT `triage_score` and measures recall of `needs_human` gold.",
        "",
    ]
    return "\n".join(lines)


def render_comparison(summaries: list[dict[str, Any]]) -> str:
    if not summaries:
        return "# Sift comparison\n\n_No summaries._\n"

    lines = [
        "# Sift comparison",
        "",
        "| Metric | " + " | ".join(f"`{s.get('sut', '?')}`" for s in summaries) + " |",
        "|" + "---|" * (len(summaries) + 1),
    ]

    keys = [
        ("n_tasks", "Tasks"),
        ("triage_accuracy", "Triage accuracy"),
        ("budgeted_capture_at_20pct", "Capture @ 20%"),
        ("budget_waste_at_20pct", "Waste @ 20%"),
        ("budgeted_capture_at_40pct", "Capture @ 40%"),
        ("budget_waste_at_40pct", "Waste @ 40%"),
        ("findings_mean_coverage", "Findings coverage"),
        ("findings_mean_precision", "Findings precision"),
        ("findings_mean_f1", "Findings F1"),
        ("total_cost_usd", "Cost (USD)"),
    ]
    for key, label in keys:
        cells = " | ".join(_fmt(s.get(key)) for s in summaries)
        lines.append(f"| {label} | {cells} |")

    if len(summaries) >= 2:
        a, b = summaries[0], summaries[1]
        by_a = {t["task_id"]: t for t in a.get("tasks", [])}
        by_b = {t["task_id"]: t for t in b.get("tasks", [])}
        lines += ["", f"## Where `{b.get('sut')}` differs from `{a.get('sut')}`", ""]
        diffs: list[str] = []
        for tid, ta in by_a.items():
            tb = by_b.get(tid)
            if not tb:
                continue
            if ta.get("triage_correct") != tb.get("triage_correct") and ta.get("triage_correct") is not None:
                diffs.append(
                    f"- `{tid}` triage: `{a.get('sut')}` "
                    f"{'✓' if ta['triage_correct'] else '✗'} `{ta.get('triage_pred')}` → "
                    f"`{b.get('sut')}` {'✓' if tb['triage_correct'] else '✗'} `{tb.get('triage_pred')}` "
                    f"(gold `{ta.get('triage_gold')}`)"
                )
            fa, fb = ta.get("findings_f1"), tb.get("findings_f1")
            if fa is not None and fb is not None and abs(fa - fb) >= 0.05:
                diffs.append(f"- `{tid}` findings F1: `{_fmt(fa)}` → `{_fmt(fb)}`")
        lines.extend(diffs or ["_No triage or F1 deltas above threshold._"])

    lines.append("")
    return "\n".join(lines)
