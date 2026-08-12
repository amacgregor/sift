"""Systems under test."""

from __future__ import annotations

from typing import Callable

from reviewgate.schema import SutOutput, Task
from reviewgate.suts.heuristic import HeuristicSut
from reviewgate.suts.llm import LlmSut

SutFn = Callable[[Task], SutOutput]

REGISTRY: dict[str, type] = {
    "heuristic": HeuristicSut,
    "llm": LlmSut,
}


def get_sut(name: str, **kwargs):
    if name not in REGISTRY:
        raise ValueError(f"Unknown SUT '{name}'. Choose from: {sorted(REGISTRY)}")
    return REGISTRY[name](**kwargs)
