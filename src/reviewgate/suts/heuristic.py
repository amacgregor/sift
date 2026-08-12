"""Structural heuristic baseline (Circuit Breaker–inspired signals)."""

from __future__ import annotations

import re
import time

from reviewgate.schema import PredictedFinding, SutOutput, Task, TriageLabel


class HeuristicSut:
    """No-API baseline using size, tests, body quality, and simple diff patterns."""

    name = "heuristic"

    def run(self, task: Task) -> SutOutput:
        t0 = time.perf_counter()
        reasons: list[str] = []
        score = 0.0

        # --- structural triage signals ---
        total = max(task.total_changes, 1)
        if total >= 800:
            score -= 1.5
            reasons.append(f"very large diff ({total} LOC changed)")
        elif total >= 300:
            score -= 0.5
            reasons.append(f"large diff ({total} LOC changed)")
        elif total <= 40:
            score += 0.6
            reasons.append(f"small diff ({total} LOC changed)")

        if task.files_changed >= 25:
            score -= 1.0
            reasons.append(f"many files changed ({task.files_changed})")
        elif task.files_changed <= 3:
            score += 0.4
            reasons.append(f"focused file set ({task.files_changed})")

        body = (task.pr_body or "").strip()
        if len(body) < 40:
            score -= 0.8
            reasons.append("thin PR description")
        else:
            score += 0.3
            reasons.append("has a non-trivial description")

        if re.search(r"\b(plan|steps|root cause|fix|security|regression)\b", body, re.I):
            score += 0.7
            reasons.append("description contains plan/fix/security language")

        if re.search(r"\b(security|tenant|authz|cve|cross-tenant)\b", body, re.I):
            score += 1.0
            reasons.append("explicit security/tenant severity in description")

        if re.search(r"\b(typo|readme only|chore|formatting|lint)\b", body, re.I):
            score -= 0.5
            reasons.append("description suggests low-risk chore")

        diff_l = task.diff.lower()
        has_tests = bool(
            re.search(r"(test_|_test\.|spec\.|/tests/|\.test\.|\.spec\.)", task.diff, re.I)
        ) or any("test" in p.lower() or p.endswith(".spec.ts") for p in task.context_files)
        # also check file paths in diff headers
        if re.search(r"^\+\+\+ .*(test|spec)", task.diff, re.M | re.I):
            has_tests = True

        if has_tests:
            score += 0.8
            reasons.append("touches or adds tests")
        elif total > 80:
            score -= 0.6
            reasons.append("non-trivial change without obvious tests")

        # author novelty proxy from name
        if task.author in {"first-time-contributor", "new-user", "unknown"}:
            score += 0.2
            reasons.append("author looks new — vouching bias")

        # --- simple finding detectors (Family F) ---
        findings: list[PredictedFinding] = []

        if re.search(
            r"find_by_id\(|\.get\(id\)|WHERE\s+id\s*=\s*(?!.*tenant)",
            task.diff,
            re.I,
        ) or (
            "get_by_id" in diff_l
            and "tenant" not in diff_l
            and ("delete" in diff_l or "fetch" in diff_l or "select" in diff_l)
        ):
            # Look for tenant-less resource access in added lines
            if self._added_lines_match(
                task.diff, r"(get_by_id|find_by_id|delete_by_id|WHERE id =)"
            ) and not self._added_lines_match(task.diff, r"tenant"):
                findings.append(
                    PredictedFinding(
                        path=self._guess_path(task.diff, default="src/api.py"),
                        title="Resource access may omit tenant isolation",
                        severity="critical",
                        rationale="Added lookup/delete by id without an obvious tenant constraint.",
                    )
                )
                score += 1.2
                reasons.append("possible missing tenant/authz check")

        parity_token = self._api_parity_detail(task)
        if parity_token:
            findings.append(
                PredictedFinding(
                    path=self._guess_path(task.diff, default="src/routes.ts"),
                    title=f"API parity regression: dropped {parity_token} filter present in legacy",
                    severity="high",
                    rationale=(
                        f"Legacy behavior filtered on {parity_token}; the migrated handler no longer "
                        f"applies that constraint. Clients may see inactive or previously excluded rows."
                    ),
                )
            )
            score += 1.0
            reasons.append("possible API parity regression")

        label = self._score_to_label(score, task)
        latency = int((time.perf_counter() - t0) * 1000)

        return SutOutput(
            task_id=task.meta.id,
            sut=self.name,
            triage_label=label,
            triage_score=score,
            triage_reasons=reasons,
            findings=findings,
            latency_ms=latency,
            cost_usd=0.0,
            raw={"score": score},
        )

    def _score_to_label(self, score: float, task: Task) -> TriageLabel:
        # Large noisy PRs without security-ish signals → low value
        if score <= -1.0:
            return "likely_low_value"

        new_author = task.author in {"first-time-contributor", "new-user", "unknown"}
        securityish = bool(
            re.search(r"\b(security|tenant|authz|cve|vulnerability)\b", task.pr_body, re.I)
        )

        # New contributors default to vouching unless the change is clearly security-critical
        if new_author and not securityish:
            if score <= -0.5:
                return "likely_low_value"
            return "vouching_required"

        if score < 0.5:
            if score < 0:
                return "likely_low_value"
            return "vouching_required"
        return "needs_human"

    @staticmethod
    def _added_lines_match(diff: str, pattern: str) -> bool:
        added = "\n".join(
            line[1:] for line in diff.splitlines() if line.startswith("+") and not line.startswith("+++")
        )
        return bool(re.search(pattern, added, re.I))

    @staticmethod
    def _guess_path(diff: str, default: str) -> str:
        for line in diff.splitlines():
            if line.startswith("+++ b/"):
                return line[6:].strip()
            if line.startswith("+++ "):
                return line[4:].strip()
        return default

    def _api_parity_risk(self, task: Task) -> bool:
        return self._api_parity_detail(task) is not None

    def _api_parity_detail(self, task: Task) -> str | None:
        # Heuristic: removed filter/status/default in diff + "migrat" language
        removed = "\n".join(
            line[1:] for line in task.diff.splitlines() if line.startswith("-") and not line.startswith("---")
        )
        added = "\n".join(
            line[1:] for line in task.diff.splitlines() if line.startswith("+") and not line.startswith("+++")
        )
        removed_filter = bool(re.search(r"status\s*==|filter\(|where\(|is_active|default=", removed, re.I))
        added_lacks = not bool(re.search(r"status\s*==|is_active|default_status", added, re.I))
        migration = bool(
            re.search(r"migrat|parity|v2|replace endpoint", task.pr_body + task.diff, re.I)
        )
        if not (removed_filter and added_lacks and (migration or "legacy" in removed.lower())):
            return None
        if re.search(r"is_active", removed, re.I) and not re.search(r"is_active", added, re.I):
            return "is_active"
        if re.search(r"status", removed, re.I):
            return "status filter"
        return "filter"
