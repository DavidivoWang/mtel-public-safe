# Troubleshooting

Normal CLI failures return structured JSON and exit code `2` without a Python traceback. Add `--debug` before the subcommand to emit a diagnostic traceback.

Common errors:

- `FLOW_DUPLICATE_NAME`: two flows use the same name;
- `UNSAFE_EXPRESSION`: a `when` expression contains an unsupported AST node;
- `SCHEMA_REQUIRED`, `SCHEMA_TYPE`, `SCHEMA_ENUM`: input violates the MTEL/0.2 contract;
- `INCLUDE_TRAVERSAL` or `INCLUDE_CYCLE`: an include crosses the source root or forms a cycle.
