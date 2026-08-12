"""Task and result schemas for ReviewGate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

TriageLabel = Literal["needs_human", "vouching_required", "likely_low_value"]
Family = Literal["T", "F", "both"]
Severity = Literal["low", "medium", "high", "critical"]


@dataclass
class GoldFinding:
    id: str
    path: str
    title: str
    severity: Severity
    rationale: str
    # Optional anchor text that must appear near a matching finding
    anchor: str | None = None


@dataclass
class Gold:
    triage_label: TriageLabel | None = None
    # 1.0 = highest priority for budgeted ranking metrics
    triage_priority: float | None = None
    findings: list[GoldFinding] = field(default_factory=list)
    rationale: str = ""


@dataclass
class TaskMeta:
    id: str
    family: Family
    title: str
    language: str
    tags: list[str]
    difficulty: int
    source: str
    license_note: str


@dataclass
class Task:
    meta: TaskMeta
    pr_title: str
    pr_body: str
    author: str
    files_changed: int
    additions: int
    deletions: int
    # Unified diff or pseudo-diff text the SUT may read
    diff: str
    # Optional extra repo context files: path -> content
    context_files: dict[str, str]
    gold: Gold

    @property
    def total_changes(self) -> int:
        return self.additions + self.deletions


@dataclass
class PredictedFinding:
    path: str
    title: str
    severity: Severity | str
    rationale: str


@dataclass
class SutOutput:
    task_id: str
    sut: str
    triage_label: TriageLabel | str | None = None
    triage_score: float | None = None  # higher = more needs human attention
    triage_reasons: list[str] = field(default_factory=list)
    findings: list[PredictedFinding] = field(default_factory=list)
    tokens_in: int = 0
    tokens_out: int = 0
    latency_ms: int = 0
    cost_usd: float = 0.0
    raw: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        return d


@dataclass
class TaskScore:
    task_id: str
    family: Family
    triage_correct: bool | None = None
    triage_gold: str | None = None
    triage_pred: str | None = None
    findings_coverage: float | None = None  # recall over gold findings
    findings_precision: float | None = None
    findings_f1: float | None = None
    matched_gold_ids: list[str] = field(default_factory=list)
    unmatched_pred_indices: list[int] = field(default_factory=list)
    failure_codes: list[str] = field(default_factory=list)
    cost_usd: float = 0.0
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
