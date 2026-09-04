# `when` evaluator design

`when` expressions are parsed with Python's AST parser but only a fixed allowlist of boolean, comparison, path, literal, list, and tuple nodes is accepted. Function calls, subscripts, comprehensions, arithmetic execution, imports, and attribute mutation are rejected.

`inspect_mtel` compiles every expression and returns `ERROR` for unsafe or invalid expressions. `run_mtel` validates input against the packaged JSON Schema before evaluation.

Evaluation states are `MATCH`, `NO_MATCH`, and `ERROR`. Runtime errors fail closed to a structured result; authoring errors fail at inspect time.
