"""Systems under test."""

from __future__ import annotations

from typing import Callable

from sift.schema import SutOutput, Task
from sift.suts.checklist import ChecklistSut
from sift.suts.heuristic import HeuristicSut
from sift.suts.llm import LlmSut, LlmStructuredSut

SutFn = Callable[[Task], SutOutput]

REGISTRY: dict[str, type] = {
    "heuristic": HeuristicSut,
    "checklist": ChecklistSut,
    "llm": LlmSut,
    "llm_structured": LlmStructuredSut,
}


def get_sut(name: str, **kwargs):
    if name not in REGISTRY:
        raise ValueError(f"Unknown SUT '{name}'. Choose from: {sorted(REGISTRY)}")
    return REGISTRY[name](**kwargs)
