"""CLI: sift review | run | list | compare."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from sift import __version__
from sift.report import render_comparison, render_markdown, render_review
from sift.scorers import score_task, summarize
from sift.suts import REGISTRY, get_sut
from sift.tasks import load_tasks, task_from_diff

SUT_CHOICES = sorted(REGISTRY)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="sift",
        description="Review a diff, or score a task pack against gold.",
    )
    parser.add_argument("--version", action="version", version=f"sift {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_rev = sub.add_parser("review", help="Run a SUT on a live diff (no gold)")
    _add_sut_args(p_rev)
    p_rev.add_argument("--diff", default="-", help="Unified diff path, or - for stdin")
    p_rev.add_argument("--title", default="")
    p_rev.add_argument("--body", default="")
    p_rev.add_argument("--author", default="unknown")
    p_rev.add_argument("--json", action="store_true", dest="as_json")
    p_rev.set_defaults(func=cmd_review)

    p_list = sub.add_parser("list", help="List task ids in a pack")
    _add_pack_args(p_list)
    p_list.set_defaults(func=cmd_list)

    p_run = sub.add_parser("run", help="Run a SUT on a pack and score if gold exists")
    _add_sut_args(p_run)
    _add_pack_args(p_run)
    p_run.add_argument("--task", action="append", dest="tasks", help="Task id (repeatable)")
    p_run.add_argument("--strict-gold", action="store_true")
    p_run.add_argument("--out", type=Path, default=Path("results/latest"))
    p_run.set_defaults(func=cmd_run)

    p_cmp = sub.add_parser("compare", help="Score two or more SUTs on the same pack")
    p_cmp.add_argument("--suts", default="heuristic,llm", help="Comma-separated SUT names")
    _add_pack_args(p_cmp)
    p_cmp.add_argument("--task", action="append", dest="tasks")
    p_cmp.add_argument("--strict-gold", action="store_true")
    p_cmp.add_argument("--out", type=Path, default=Path("results/compare"))
    p_cmp.add_argument("--model", default=None)
    p_cmp.set_defaults(func=cmd_compare)

    args = parser.parse_args(argv)
    return args.func(args)


def _add_sut_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--sut", default="heuristic", choices=SUT_CHOICES)
    p.add_argument("--model", default=None, help="Model id for llm / llm_structured")


def _add_pack_args(p: argparse.ArgumentParser) -> None:
    p.add_argument("--tasks-dir", default=None, help="Task pack directory (or SIFT_TASKS_DIR)")
    p.add_argument("--family", choices=["T", "F", "both"], default=None)


def _load(args: argparse.Namespace):
    tasks = load_tasks(getattr(args, "tasks", None), tasks_dir=args.tasks_dir)
    if args.family:
        tasks = [t for t in tasks if t.meta.family == args.family]
    return tasks


def cmd_review(args: argparse.Namespace) -> int:
    if args.diff == "-":
        if sys.stdin.isatty():
            print("Pass a patch with --diff PATH or pipe a unified diff to stdin.", file=sys.stderr)
            return 2
        diff = sys.stdin.read()
    else:
        diff = Path(args.diff).read_text()
    if not diff.strip():
        print("Empty diff", file=sys.stderr)
        return 1

    task = task_from_diff(diff, title=args.title, body=args.body, author=args.author)
    kwargs = {}
    if args.sut.startswith("llm") and args.model:
        kwargs["model"] = args.model
    out = get_sut(args.sut, **kwargs).run(task)
    if args.as_json:
        print(json.dumps(out.to_dict(), indent=2, default=str))
    else:
        print(render_review(out))
    return 0


def cmd_list(args: argparse.Namespace) -> int:
    try:
        tasks = _load(args)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 2
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
    try:
        tasks = _load(args)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 2
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
    try:
        tasks = _load(args)
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        return 2
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
