from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Rule:
    name: str
    expression: str
    action: str
    target: str
    priority: int
    veto: bool
    source: str
    line: int
    index: int


@dataclass(frozen=True)
class Flow:
    name: str
    bindings: tuple[str, ...]
    overlap: str


@dataclass(frozen=True)
class Program:
    spec: str
    rules: tuple[Rule, ...]
    flows: tuple[Flow, ...]
    source_files: tuple[str, ...]
