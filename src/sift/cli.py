"""CLI entrypoint: sift run|list|compare."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sift import DATASET_VERSION, __version__
from sift.report import render_comparison, render_markdown
from sift.scorers import score_task, summarize
from sift.suts import REGISTRY, get_sut
from sift.tasks import list_task_ids, load_tasks

SUT_CHOICES = sorted(REGISTRY)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="sift", description="PR triage & review eval harness")
    parser.add_argument("--version", action="version", version=f"sift {__version__} (dataset {DATASET_VERSION})")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List task ids")
    p_list.add_argument("--family", choices=["T", "F", "both"], default=None)
    p_list.set_defaults(func=cmd_list)

    p_run = sub.add_parser("run", help="Run SUT on tasks and score")
    p_run.add_argument("--sut", default="heuristic", choices=SUT_CHOICES)
    p_run.add_argument("--task", action="append", dest="tasks", help="Task id (repeatable)")
    p_run.add_argument("--family", choices=["T", "F", "both"], default=None)
    p_run.add_argument("--strict-gold", action="store_true", help="Strict precision: extras are false positives")
    p_run.add_argument("--out", type=Path, default=Path("results/latest"))
    p_run.add_argument("--model", default=None, help="Model id for llm / llm_structured")
    p_run.set_defaults(func=cmd_run)

    p_cmp = sub.add_parser("compare", help="Run two or more SUTs and write a comparison report")
    p_cmp.add_argument(
        "--suts",
        default="heuristic,checklist",
        help="Comma-separated SUT names (default heuristic,checklist)",
    )
    p_cmp.add_argument("--task", action="append", dest="tasks", help="Task id (repeatable)")
    p_cmp.add_argument("--family", choices=["T", "F", "both"], default=None)
    p_cmp.add_argument("--strict-gold", action="store_true")
    p_cmp.add_argument("--out", type=Path, default=Path("results/compare"))
    p_cmp.add_argument("--model", default=None)
    p_cmp.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    return args.func(args)


def _load(task_ids: list[str] | None, family: str | None):
    tasks = load_tasks(task_ids)
    if family:
        tasks = [t for t in tasks if t.meta.family == family]
    return tasks


def cmd_list(args: argparse.Namespace) -> int:
    tasks = _load(None, args.family)
    for t in tasks:
        print(f"{t.meta.id}\t{t.meta.family}\t{t.meta.title}")
    return 0


def _run_one(tasks, sut_name: str, *, strict_gold: bool, model: str | None):
    kwargs = {}
    if sut_name.startswith("llm") and model:
        kwargs["model"] = model
    sut = get_sut(sut_name, **kwargs)
    outputs = []
    scores = []
    for task in tasks:
        print(f"→ {task.meta.id} ({task.meta.family}) via {sut_name}", flush=True)
        out = sut.run(task)
        outputs.append(out)
        sc = score_task(task, out, strict_gold=strict_gold)
        scores.append(sc)
        tri = sc.triage_correct
        tri_s = {True: "triage✓", False: "triage✗", None: "triage—"}[tri]
        f1 = f"f1={sc.findings_f1:.2f}" if sc.findings_f1 is not None else "f1—"
        print(f"  {tri_s}  {f1}  failures={sc.failure_codes or '[]'}")
    summary = summarize(tasks, scores, outputs)
    summary["sut"] = sut_name
    summary["dataset_version"] = DATASET_VERSION
    return outputs, scores, summary


def _write_run(out_dir: Path, summary: dict, outputs, sut_name: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (out_dir / "outputs.json").write_text(
        json.dumps([o.to_dict() for o in outputs], indent=2, default=str)
    )
    md = render_markdown(summary, sut=sut_name)
    (out_dir / "report.md").write_text(md)
    return out_dir / "report.md"


def cmd_run(args: argparse.Namespace) -> int:
    tasks = _load(args.tasks, args.family)
    if not tasks:
        print("No tasks loaded", file=sys.stderr)
        return 1
    outputs, _scores, summary = _run_one(
        tasks, args.sut, strict_gold=args.strict_gold, model=args.model
    )
    path = _write_run(args.out, summary, outputs, args.sut)
    print()
    print(path.read_text())
    print(f"\nWrote {path}")
    return 0


def cmd_compare(args: argparse.Namespace) -> int:
    names = [n.strip() for n in args.suts.split(",") if n.strip()]
    unknown = [n for n in names if n not in REGISTRY]
    if unknown:
        print(f"Unknown SUT(s): {unknown}. Choose from: {SUT_CHOICES}", file=sys.stderr)
        return 2
    if len(names) < 2:
        print("compare needs at least two SUTs", file=sys.stderr)
        return 2

    tasks = _load(args.tasks, args.family)
    if not tasks:
        print("No tasks loaded", file=sys.stderr)
        return 1

    summaries = []
    out_root: Path = args.out
    for name in names:
        outputs, _scores, summary = _run_one(
            tasks, name, strict_gold=args.strict_gold, model=args.model
        )
        _write_run(out_root / name, summary, outputs, name)
        summaries.append(summary)

    cmp_md = render_comparison(summaries)
    (out_root / "comparison.md").write_text(cmp_md)
    (out_root / "comparison.json").write_text(json.dumps(summaries, indent=2, default=str))
    print()
    print(cmp_md)
    print(f"\nWrote {out_root}/comparison.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
