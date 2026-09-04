from __future__ import annotations

import re
from pathlib import Path

from .errors import MTELRuntimeError
from .model import Flow, Program, Rule

SPEC = "MTEL/0.2"
MAX_SOURCE_FILES = 32
MAX_INCLUDE_DEPTH = 8
MAX_RULES = 500
MAX_SOURCE_BYTES = 1024 * 1024
RULE_RE = re.compile(r"^rule\s+([A-Za-z_][A-Za-z0-9_.-]*)(?:\s+priority\s+(\d+))?(?:\s+(veto))?$")
FLOW_RE = re.compile(r"^flow\s+([A-Za-z_][A-Za-z0-9_.-]*)$")
ACTION_RE = re.compile(r'^->\s+(PASS|ROUTE|HOLD|BLOCK)\s+"([^"]*)"$')
INCLUDE_RE = re.compile(r'^include\s+"([^"]+)"$')
BIND_RE = re.compile(r"^bind\s+([A-Za-z_*][A-Za-z0-9_.*-]*)$")
OVERLAP_RE = re.compile(r"^overlap\s+(hold|first)$")


class _State:
    def __init__(self, root: Path):
        self.root = root
        self.spec: str | None = None
        self.rules: list[Rule] = []
        self.flows: list[Flow] = []
        self.files: list[str] = []
        self.total_bytes = 0


def _error(code: str, message: str, source: Path, line: int | None = None) -> MTELRuntimeError:
    return MTELRuntimeError(code, message, str(source), line)


def _safe_include(root: Path, current: Path, value: str, line: int) -> Path:
    candidate = (current.parent / value).resolve()
    try:
        candidate.relative_to(root)
    except ValueError as exc:
        raise _error("INCLUDE_TRAVERSAL", "include must stay under source root", current, line) from exc
    if candidate.suffix != ".mtel":
        raise _error("INCLUDE_EXTENSION", "include must reference a .mtel file", current, line)
    return candidate


def _parse_file(path: Path, state: _State, stack: tuple[Path, ...]) -> None:
    path = path.resolve()
    if path in stack:
        raise _error("INCLUDE_CYCLE", "include cycle detected", path)
    if len(stack) >= MAX_INCLUDE_DEPTH:
        raise _error("INCLUDE_DEPTH", "maximum include depth exceeded", path)
    if not path.is_file():
        raise _error("SOURCE_NOT_FOUND", "source file not found", path)
    rel = str(path.relative_to(state.root)).replace("\\", "/")
    if rel in state.files:
        return
    if len(state.files) >= MAX_SOURCE_FILES:
        raise _error("SOURCE_FILE_LIMIT", "maximum source file count exceeded", path)
    raw = path.read_text(encoding="utf-8")
    state.total_bytes += len(raw.encode("utf-8"))
    if state.total_bytes > MAX_SOURCE_BYTES:
        raise _error("SOURCE_SIZE_LIMIT", "maximum total source bytes exceeded", path)
    state.files.append(rel)
    lines = raw.splitlines()
    i = 0
    while i < len(lines):
        line_no = i + 1
        line = lines[i].split("#", 1)[0].strip()
        i += 1
        if not line:
            continue
        if line.startswith("@spec "):
            spec = line[6:].strip()
            if spec != SPEC:
                raise _error("SPEC_UNSUPPORTED", f"expected {SPEC}", path, line_no)
            if state.spec is None:
                state.spec = spec
            elif state.spec != spec:
                raise _error("SPEC_CONFLICT", "conflicting spec versions", path, line_no)
            continue
        include_match = INCLUDE_RE.match(line)
        if include_match:
            _parse_file(_safe_include(state.root, path, include_match.group(1), line_no), state, stack + (path,))
            continue
        rule_match = RULE_RE.match(line)
        if rule_match:
            name, priority_text, veto_text = rule_match.groups()
            expression: str | None = None
            action: str | None = None
            target = ""
            while i < len(lines):
                child_no = i + 1
                child = lines[i].split("#", 1)[0].strip()
                i += 1
                if not child:
                    continue
                if child == "end":
                    break
                if child.startswith("when "):
                    if expression is not None:
                        raise _error("RULE_DUPLICATE_WHEN", "rule has more than one when", path, child_no)
                    expression = child[5:].strip()
                    continue
                action_match = ACTION_RE.match(child)
                if action_match:
                    if action is not None:
                        raise _error("RULE_DUPLICATE_ACTION", "rule has more than one action", path, child_no)
                    action, target = action_match.groups()
                    continue
                raise _error("RULE_SYNTAX", "unsupported rule statement", path, child_no)
            else:
                raise _error("RULE_UNTERMINATED", "rule is missing end", path, line_no)
            if not expression:
                raise _error("RULE_MISSING_WHEN", "rule is missing when", path, line_no)
            if not action:
                raise _error("RULE_MISSING_ACTION", "rule is missing action", path, line_no)
            if any(rule.name == name for rule in state.rules):
                raise _error("RULE_DUPLICATE_NAME", f"duplicate rule {name}", path, line_no)
            if len(state.rules) >= MAX_RULES:
                raise _error("RULE_LIMIT", "maximum rule count exceeded", path, line_no)
            state.rules.append(Rule(name, expression, action, target, int(priority_text or 0), bool(veto_text), rel, line_no, len(state.rules)))
            continue
        flow_match = FLOW_RE.match(line)
        if flow_match:
            flow_name = flow_match.group(1)
            if any(flow.name == flow_name for flow in state.flows):
                raise _error("FLOW_DUPLICATE_NAME", f"duplicate flow {flow_name}", path, line_no)
            bindings: list[str] = []
            overlap = "hold"
            while i < len(lines):
                child_no = i + 1
                child = lines[i].split("#", 1)[0].strip()
                i += 1
                if not child:
                    continue
                if child == "end":
                    break
                bind_match = BIND_RE.match(child)
                if bind_match:
                    bindings.append(bind_match.group(1))
                    continue
                overlap_match = OVERLAP_RE.match(child)
                if overlap_match:
                    overlap = overlap_match.group(1)
                    continue
                raise _error("FLOW_SYNTAX", "unsupported flow statement", path, child_no)
            else:
                raise _error("FLOW_UNTERMINATED", "flow is missing end", path, line_no)
            state.flows.append(Flow(flow_name, tuple(bindings or ["*"]), overlap))
            continue
        raise _error("TOP_LEVEL_SYNTAX", "unsupported top-level statement", path, line_no)


def parse_program(source_path: str | Path) -> Program:
    source = Path(source_path).resolve()
    state = _State(source.parent)
    _parse_file(source, state, ())
    if state.spec is None:
        raise _error("SPEC_MISSING", "source is missing @spec", source)
    if not state.flows:
        state.flows.append(Flow("default", ("*",), "hold"))
    names = {rule.name for rule in state.rules}
    for flow in state.flows:
        for binding in flow.bindings:
            if binding != "*" and binding not in names:
                raise _error("FLOW_UNKNOWN_RULE", f"unknown bound rule {binding}", source)
    return Program(state.spec, tuple(state.rules), tuple(state.flows), tuple(state.files))
