from __future__ import annotations

from typing import Any

from .audit import emit
from .errors import MTELRuntimeError
from .evaluator import evaluate_expression
from .model import Flow, Program, Rule


def _flow(program: Program, name: str) -> Flow:
    for flow in program.flows:
        if flow.name == name:
            return flow
    raise MTELRuntimeError("FLOW_NOT_FOUND", f"flow not found: {name}")


def _bound_rules(program: Program, flow: Flow) -> list[Rule]:
    if "*" in flow.bindings:
        return list(program.rules)
    names = set(flow.bindings)
    return [rule for rule in program.rules if rule.name in names]


def _complete(payload: dict[str, Any]) -> dict[str, Any]:
    emit(
        "execution_completed",
        status=payload.get("status"),
        target=(payload.get("decision") or {}).get("target"),
    )
    return payload


def _error_event_fields(error: dict[str, Any]) -> dict[str, Any]:
    """Return strict-flat scalar audit fields for a structured runtime error."""
    fields: dict[str, Any] = {
        "error_code": error.get("code"),
        "error_message": error.get("message"),
    }
    if error.get("source") is not None:
        fields["error_source"] = error.get("source")
    if error.get("line") is not None:
        fields["error_line"] = error.get("line")
    return fields


def execute(program: Program, data: dict[str, Any], flow_name: str = "default") -> dict[str, Any]:
    emit("execution_started", flow=flow_name, rule_count=len(program.rules))
    flow = _flow(program, flow_name)
    evaluations: list[dict[str, Any]] = []
    matches: list[Rule] = []
    for rule in _bound_rules(program, flow):
        result = evaluate_expression(rule.expression, data)
        evaluations.append({"rule": rule.name, **result})
        emit("condition_evaluated", rule=rule.name, state=result["state"])
        if result["state"] == "ERROR":
            error = result.get("error") or {}
            event = "condition_unsupported" if error.get("code") in {
                "UNSAFE_EXPRESSION",
                "EXPRESSION_SYNTAX",
                "EXPRESSION_LENGTH_LIMIT",
                "EXPRESSION_NODE_LIMIT",
                "EXPRESSION_DEPTH_LIMIT",
            } else "condition_error"
            emit(event, rule=rule.name, **_error_event_fields(error))
            return _complete({
                "status": "HOLD",
                "decision": {"action": "HOLD", "target": "condition_evaluation_error"},
                "error": error,
                "matched_rules": [],
                "evaluations": evaluations,
                "trace": ["parse:PASS", f"flow:{flow.name}", f"condition_error:{rule.name}"],
            })
        if result["state"] == "MATCH":
            matches.append(rule)
    if not matches:
        return _complete({
            "status": "HOLD",
            "decision": {"action": "HOLD", "target": "no_rule_matched"},
            "matched_rules": [],
            "evaluations": evaluations,
            "trace": ["parse:PASS", f"flow:{flow.name}", "arbitrate:no_match"],
        })
    vetoes = [rule for rule in matches if rule.veto]
    pool = vetoes or matches
    pool.sort(key=lambda rule: (-rule.priority, rule.index))
    top_priority = pool[0].priority
    top = [rule for rule in pool if rule.priority == top_priority]
    decisions = {(rule.action, rule.target) for rule in top}
    if len(decisions) > 1 and flow.overlap == "hold":
        return _complete({
            "status": "HOLD",
            "decision": {"action": "HOLD", "target": "rule_conflict"},
            "matched_rules": [rule.name for rule in matches],
            "evaluations": evaluations,
            "trace": ["parse:PASS", f"flow:{flow.name}", "arbitrate:conflict_hold"],
        })
    selected = top[0]
    emit(
        "rule_selected",
        rule=selected.name,
        action=selected.action,
        target=selected.target,
        priority=selected.priority,
        veto=selected.veto,
    )
    return _complete({
        "status": selected.action,
        "decision": {
            "action": selected.action,
            "target": selected.target,
            "rule": selected.name,
            "priority": selected.priority,
            "veto": selected.veto,
        },
        "matched_rules": [rule.name for rule in matches],
        "evaluations": evaluations,
        "trace": ["parse:PASS", f"flow:{flow.name}", f"selected:{selected.name}"],
    })
