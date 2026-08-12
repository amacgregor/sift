"""Optional single-shot LLM SUT (requires openai extra + API key)."""

from __future__ import annotations

import json
import os
import re
import time
from typing import Any

from sift.schema import PredictedFinding, SutOutput, Task

SYSTEM = """You evaluate pull requests for two things:
1) Triage: should a human spend review attention on this PR?
   Labels: needs_human | vouching_required | likely_low_value
2) Findings: substantive defects only (not nits). Prefer security, correctness,
   API parity, data integrity. Empty list is OK.

Return ONLY valid JSON with this shape:
{
  "triage_label": "...",
  "triage_score": 0.0,
  "triage_reasons": ["..."],
  "findings": [
    {"path": "...", "title": "...", "severity": "low|medium|high|critical", "rationale": "..."}
  ]
}
"""


class LlmSut:
    name = "llm"

    def __init__(self, model: str | None = None):
        self.model = model or os.environ.get("SIFT_MODEL", "gpt-4o-mini")

    def run(self, task: Task) -> SutOutput:
        try:
            from openai import OpenAI
        except ImportError as e:
            raise RuntimeError(
                "LLM SUT requires: pip install 'sift[llm]' and OPENAI_API_KEY"
            ) from e

        if not os.environ.get("OPENAI_API_KEY"):
            raise RuntimeError("OPENAI_API_KEY is not set")

        client = OpenAI()
        user = self._build_prompt(task)
        t0 = time.perf_counter()
        resp = client.chat.completions.create(
            model=self.model,
            temperature=0,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM},
                {"role": "user", "content": user},
            ],
        )
        latency = int((time.perf_counter() - t0) * 1000)
        content = resp.choices[0].message.content or "{}"
        usage = resp.usage
        tokens_in = getattr(usage, "prompt_tokens", 0) or 0
        tokens_out = getattr(usage, "completion_tokens", 0) or 0
        # rough default pricing placeholder; report tokens either way
        cost = (tokens_in * 0.15 + tokens_out * 0.60) / 1_000_000

        data = self._parse(content)
        findings = [
            PredictedFinding(
                path=f.get("path", "unknown"),
                title=f.get("title", "untitled"),
                severity=f.get("severity", "medium"),
                rationale=f.get("rationale", ""),
            )
            for f in data.get("findings", [])
            if isinstance(f, dict)
        ]

        return SutOutput(
            task_id=task.meta.id,
            sut=self.name,
            triage_label=data.get("triage_label"),
            triage_score=float(data["triage_score"]) if data.get("triage_score") is not None else None,
            triage_reasons=list(data.get("triage_reasons") or []),
            findings=findings,
            tokens_in=tokens_in,
            tokens_out=tokens_out,
            latency_ms=latency,
            cost_usd=cost,
            raw={"model": self.model, "response": data},
        )

    def _build_prompt(self, task: Task) -> str:
        ctx = ""
        for path, body in list(task.context_files.items())[:6]:
            ctx += f"\n--- context: {path} ---\n{body[:4000]}\n"
        return f"""Task: {task.meta.id} ({task.meta.family})
Language: {task.meta.language}
Author: {task.author}
Files changed: {task.files_changed}
Additions/deletions: {task.additions}/{task.deletions}

PR title: {task.pr_title}

PR body:
{task.pr_body}

Diff:
{task.diff[:12000]}
{ctx}
"""

    def _parse(self, content: str) -> dict[str, Any]:
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            m = re.search(r"\{.*\}", content, re.S)
            if m:
                return json.loads(m.group(0))
            return {}
