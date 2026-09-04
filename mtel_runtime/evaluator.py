from __future__ import annotations

import ast
from typing import Any

from .errors import MTELRuntimeError

MAX_EXPRESSION_CHARS = 2048
MAX_AST_NODES = 256
MAX_AST_DEPTH = 32
MAX_PATH_DEPTH = 12
ALLOWED = (
    ast.Expression, ast.BoolOp, ast.And, ast.Or, ast.UnaryOp, ast.Not,
    ast.Compare, ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.In, ast.NotIn, ast.Name, ast.Attribute, ast.Constant, ast.List,
    ast.Tuple, ast.Load,
)


def _depth(node: ast.AST) -> int:
    children = list(ast.iter_child_nodes(node))
    return 1 if not children else 1 + max(_depth(child) for child in children)


def _validate(tree: ast.AST) -> None:
    nodes = list(ast.walk(tree))
    if len(nodes) > MAX_AST_NODES:
        raise MTELRuntimeError("EXPRESSION_NODE_LIMIT", "expression AST node limit exceeded")
    if _depth(tree) > MAX_AST_DEPTH:
        raise MTELRuntimeError("EXPRESSION_DEPTH_LIMIT", "expression AST depth limit exceeded")
    for node in nodes:
        if not isinstance(node, ALLOWED):
            raise MTELRuntimeError("UNSAFE_EXPRESSION", f"unsupported expression node: {type(node).__name__}")


def compile_expression(expression: str) -> ast.Expression:
    if len(expression) > MAX_EXPRESSION_CHARS:
        raise MTELRuntimeError("EXPRESSION_LENGTH_LIMIT", "expression length limit exceeded")
    try:
        tree = ast.parse(expression, mode="eval")
    except SyntaxError as exc:
        raise MTELRuntimeError("EXPRESSION_SYNTAX", str(exc.msg)) from exc
    _validate(tree)
    return tree


def _path(node: ast.AST) -> tuple[str, ...] | None:
    parts: list[str] = []
    current = node
    while isinstance(current, ast.Attribute):
        parts.append(current.attr)
        current = current.value
    if isinstance(current, ast.Name):
        parts.append(current.id)
        parts.reverse()
        return tuple(parts)
    return None


def _resolve_path(parts: tuple[str, ...], data: dict[str, Any]) -> Any:
    if len(parts) > MAX_PATH_DEPTH:
        raise MTELRuntimeError("PATH_DEPTH_LIMIT", "input path depth limit exceeded")
    value: Any = data
    for part in parts:
        if not isinstance(value, dict) or part not in value:
            raise MTELRuntimeError("UNKNOWN_PATH", f"input path not found: {'.'.join(parts)}")
        value = value[part]
    return value


def _value(node: ast.AST, data: dict[str, Any]) -> Any:
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name) and node.id in {"true", "false", "null"}:
        return {"true": True, "false": False, "null": None}[node.id]
    path = _path(node)
    if path is not None:
        return _resolve_path(path, data)
    if isinstance(node, ast.List):
        return [_value(item, data) for item in node.elts]
    if isinstance(node, ast.Tuple):
        return tuple(_value(item, data) for item in node.elts)
    if isinstance(node, ast.BoolOp):
        if isinstance(node.op, ast.And):
            return all(bool(_value(item, data)) for item in node.values)
        return any(bool(_value(item, data)) for item in node.values)
    if isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
        return not bool(_value(node.operand, data))
    if isinstance(node, ast.Compare):
        left = _value(node.left, data)
        for operator, comparator_node in zip(node.ops, node.comparators):
            right = _value(comparator_node, data)
            try:
                ok = (
                    left == right if isinstance(operator, ast.Eq) else
                    left != right if isinstance(operator, ast.NotEq) else
                    left < right if isinstance(operator, ast.Lt) else
                    left <= right if isinstance(operator, ast.LtE) else
                    left > right if isinstance(operator, ast.Gt) else
                    left >= right if isinstance(operator, ast.GtE) else
                    left in right if isinstance(operator, ast.In) else
                    left not in right
                )
            except (TypeError, ValueError) as exc:
                raise MTELRuntimeError("TYPE_MISMATCH", "comparison operands are incompatible") from exc
            if not ok:
                return False
            left = right
        return True
    raise MTELRuntimeError("UNSAFE_EXPRESSION", "unsupported expression")


def evaluate_expression(expression: str, data: dict[str, Any]) -> dict[str, Any]:
    try:
        tree = compile_expression(expression)
        matched = bool(_value(tree.body, data))
        return {"state": "MATCH" if matched else "NO_MATCH"}
    except MTELRuntimeError as exc:
        return {"state": "ERROR", "error": exc.to_dict()}
