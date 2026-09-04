# Architecture

The candidate has two public library functions: `inspect_mtel` for authoring preflight and `run_mtel` for decision execution. Both use the same parser and restricted expression compiler.

Execution order:

1. parse MTEL/0.2 source and bounded includes;
2. reject duplicate names and invalid syntax;
3. validate input against the packaged nested schema;
4. evaluate bound rules with the restricted AST evaluator;
5. apply veto, priority, source order, and overlap policy;
6. return a deterministic structured result and flat JSON audit events.

This candidate intentionally implements a limited condition-dispatch surface. It does not expose or claim the complete private runtime feature set.
