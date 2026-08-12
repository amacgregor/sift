"""Render markdown reports from suite summaries."""

from __future__ import annotations

from typing import Any


def render_markdown(summary: dict[str, Any], *, sut: str) -> str:
    lines = [
        f"# Sift report — `{sut}`",
        "",
        f"Tasks: **{summary['n_tasks']}**",
        "",
        "## Headline metrics",
        "",
        "| Metric | Value |",
        "|---|---|",
    ]

    def fmt(v: Any) -> str:
        if v is None:
            return "—"
        if isinstance(v, float):
            return f"{v:.3f}"
        return str(v)

    rows = [
        ("Triage accuracy", summary.get("triage_accuracy")),
        ("Budgeted capture @ 20%", summary.get("budgeted_capture_at_20pct")),
        ("Budget waste @ 20%", summary.get("budget_waste_at_20pct")),
        ("Findings mean coverage", summary.get("findings_mean_coverage")),
        ("Findings mean precision", summary.get("findings_mean_precision")),
        ("Findings mean F1", summary.get("findings_mean_f1")),
        ("Total cost (USD)", summary.get("total_cost_usd")),
    ]
    for name, val in rows:
        lines.append(f"| {name} | {fmt(val)} |")

    lines += ["", "## Failure codes", ""]
    fc = summary.get("failure_codes") or {}
    if not fc:
        lines.append("_None_")
    else:
        for code, n in sorted(fc.items(), key=lambda x: (-x[1], x[0])):
            lines.append(f"- `{code}`: {n}")

    lines += ["", "## Per-task", "", "| Task | Family | Triage | Findings F1 | Failures |", "|---|---|---|---|---|"]
    for t in summary.get("tasks", []):
        triage = "—"
        if t.get("triage_correct") is not None:
            mark = "✓" if t["triage_correct"] else "✗"
            triage = f"{mark} `{t.get('triage_pred')}` (gold `{t.get('triage_gold')}`)"
        f1 = fmt(t.get("findings_f1"))
        fails = ", ".join(t.get("failure_codes") or []) or "—"
        lines.append(
            f"| `{t['task_id']}` | {t['family']} | {triage} | {f1} | {fails} |"
        )

    lines += [
        "",
        "## Notes",
        "",
        "- Precision uses **valid-extras** by default (unmatched but plausible findings are not auto-penalized).",
        "- Finding match in v0.1 is lexical/anchor-based (no LLM judge) for zero-key reproducibility.",
        "- Budgeted capture ranks by SUT `triage_score` and measures recall of `needs_human` gold in the top 20% slice.",
        "",
    ]
    return "\n".join(lines)
