"""CLI entrypoint: reviewgate run|list|report."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from reviewgate import __version__
from reviewgate.report import render_markdown
from reviewgate.scorers import score_task, summarize
from reviewgate.suts import get_sut
from reviewgate.tasks import list_task_ids, load_tasks


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="reviewgate", description="PR triage & review eval harness")
    parser.add_argument("--version", action="version", version=f"reviewgate {__version__}")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_list = sub.add_parser("list", help="List task ids")
    p_list.set_defaults(func=cmd_list)

    p_run = sub.add_parser("run", help="Run SUT on tasks and score")
    p_run.add_argument("--sut", default="heuristic", choices=["heuristic", "llm"])
    p_run.add_argument("--task", action="append", dest="tasks", help="Task id (repeatable)")
    p_run.add_argument("--strict-gold", action="store_true", help="Strict precision: extras are false positives")
    p_run.add_argument("--out", type=Path, default=Path("results/latest"))
    p_run.add_argument("--model", default=None, help="Model id for llm SUT")
    p_run.set_defaults(func=cmd_run)

    args = parser.parse_args(argv)
    return args.func(args)


def cmd_list(_args: argparse.Namespace) -> int:
    for tid in list_task_ids():
        print(tid)
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    tasks = load_tasks(args.tasks)
    if not tasks:
        print("No tasks loaded", file=sys.stderr)
        return 1

    kwargs = {}
    if args.sut == "llm" and args.model:
        kwargs["model"] = args.model
    sut = get_sut(args.sut, **kwargs)

    outputs = []
    scores = []
    for task in tasks:
        print(f"→ {task.meta.id} ({task.meta.family}) via {args.sut}", flush=True)
        out = sut.run(task)
        outputs.append(out)
        sc = score_task(task, out, strict_gold=args.strict_gold)
        scores.append(sc)
        tri = sc.triage_correct
        tri_s = {True: "triage✓", False: "triage✗", None: "triage—"}[tri]
        f1 = f"f1={sc.findings_f1:.2f}" if sc.findings_f1 is not None else "f1—"
        print(f"  {tri_s}  {f1}  failures={sc.failure_codes or '[]'}")

    summary = summarize(tasks, scores, outputs)
    out_dir: Path = args.out
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2, default=str))
    (out_dir / "outputs.json").write_text(
        json.dumps([o.to_dict() for o in outputs], indent=2, default=str)
    )
    md = render_markdown(summary, sut=args.sut)
    (out_dir / "report.md").write_text(md)

    print()
    print(md)
    print(f"\nWrote {out_dir}/report.md")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
