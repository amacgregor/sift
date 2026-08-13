"""Domain-checklist SUT — same structural signals, plus a short defect catalog.

This is the zero-key strategy ablation: changing *what you look for* moves
coverage and budgeted capture without changing the model.
"""

from __future__ import annotations

import re

from sift.schema import PredictedFinding, SutOutput, Task
from sift.suts.heuristic import HeuristicSut


class ChecklistSut(HeuristicSut):
    """Heuristic triage/findings plus explicit domain checks."""

    name = "checklist"

    def run(self, task: Task) -> SutOutput:
        base = super().run(task)
        extra = self._catalog_findings(task)
        findings = list(base.findings)
        seen = {(f.path, f.title) for f in findings}
        reasons = list(base.triage_reasons)
        score = float(base.triage_score or 0.0)

        for f in extra:
            key = (f.path, f.title)
            if key in seen:
                continue
            findings.append(f)
            seen.add(key)
            reasons.append(f"checklist: {f.title}")
            if f.severity in {"high", "critical"}:
                score += 2.5
            else:
                score += 0.6

        label = self._score_to_label(score, task)
        # A critical catalog hit should not stay buried as low-value.
        if any(f.severity == "critical" for f in findings) and label == "likely_low_value":
            label = "needs_human"
            reasons.append("critical checklist hit overrides low-value label")

        return SutOutput(
            task_id=task.meta.id,
            sut=self.name,
            triage_label=label,
            triage_score=score,
            triage_reasons=reasons,
            findings=findings,
            latency_ms=base.latency_ms,
            cost_usd=0.0,
            raw={"score": score, "base_score": base.triage_score, "catalog_n": len(extra)},
        )

    def _catalog_findings(self, task: Task) -> list[PredictedFinding]:
        added = self._added(task.diff)
        removed = self._removed(task.diff)
        ctx = "\n".join(task.context_files.values())
        blob = f"{task.diff}\n{ctx}\n{task.pr_body}"
        path = self._guess_path(task.diff, default="unknown")
        out: list[PredictedFinding] = []

        csrf_call = r"csrf\.(validate|protect|check)|if not csrf|csrf_token"
        if re.search(csrf_call, removed, re.I) and not re.search(csrf_call, added, re.I):
            out.append(
                PredictedFinding(
                    path=path,
                    title="CSRF validation removed from a state-changing handler",
                    severity="critical",
                    rationale=(
                        "Deleted csrf check on a POST that still mutates money or session state. "
                        "A comment that 'the gateway handles it' is not a substitute if the route "
                        "is also mounted internally."
                    ),
                )
            )

        if re.search(r"datetime\.(now|utcnow)\(\)", added) and re.search(
            r"payroll|period|cutoff|jurisdiction|timezone|america/", blob, re.I
        ):
            out.append(
                PredictedFinding(
                    path=path,
                    title="Naive datetime.now() used for a jurisdiction-sensitive cutoff",
                    severity="high",
                    rationale=(
                        "Period close / cutoff uses the host clock. Filing and remittance days "
                        "are jurisdiction wall-clock facts, not server-local midnight."
                    ),
                )
            )

        if (
            re.search(r"SELECT\s+balance|row\[.balance.\]|balance\s*>=", added, re.I)
            and re.search(r"UPDATE\s+\w+\s+SET\s+balance", added, re.I)
            and not re.search(r"FOR UPDATE|WHERE\s+balance\s*>=|BEGIN|transaction", added, re.I)
        ):
            out.append(
                PredictedFinding(
                    path=path,
                    title="Check-then-act balance debit without a lock",
                    severity="critical",
                    rationale=(
                        "Read balance, then write balance - amount in a separate statement. "
                        "Concurrent requests can double-spend. Use a single guarded UPDATE or a ledger append."
                    ),
                )
            )

        if re.search(r"console\.log|logger\.|log\.(info|debug|warning)", added, re.I) and re.search(
            r"authorization|req\.headers|request\.headers|cookie", added, re.I
        ):
            out.append(
                PredictedFinding(
                    path=path,
                    title="Logs request headers that include Authorization",
                    severity="high",
                    rationale=(
                        "Authorization and Cookie values in application logs are credential leakage. "
                        "Redact them even for 'temporary' debug."
                    ),
                )
            )

        dropped_cols = re.findall(
            r"DROP\s+COLUMN\s+([A-Za-z_][A-Za-z0-9_]*)", removed + added, flags=re.I
        )
        for col in dropped_cols:
            if re.search(rf"\b{re.escape(col)}\b", ctx):
                out.append(
                    PredictedFinding(
                        path=path,
                        title=f"Dropped column {col} is still referenced in remaining code",
                        severity="critical",
                        rationale=(
                            f"{col} is dropped in this PR but still appears in repo context "
                            "(reports or models). That is a live schema break, not unused cleanup."
                        ),
                    )
                )

        if re.search(r"session\.rotate|httponly|session fixation|samesite", blob, re.I) and re.search(
            r"privilege|promote|role|login", blob, re.I
        ):
            # triage boost via a finding so large real security fixes surface
            out.append(
                PredictedFinding(
                    path=path,
                    title="Privilege change rotates or hardens the session — verify completeness",
                    severity="high",
                    rationale=(
                        "Session fixation / cookie flag work is high-attention even when the PR is large. "
                        "Confirm every privilege-changing path rotates the session id."
                    ),
                )
            )

        return out

    @staticmethod
    def _added(diff: str) -> str:
        return "\n".join(
            line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")
        )

    @staticmethod
    def _removed(diff: str) -> str:
        return "\n".join(
            line[1:] for line in diff.splitlines() if line.startswith("-") and not line.startswith("---")
        )
