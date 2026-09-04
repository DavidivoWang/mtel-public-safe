# MTEL Public-Safe Candidate v0.2.2

This repository contains a **smaller reconstructed MTEL/0.2 condition-dispatch candidate**. It is not a claim that the full private MTEL runtime or all of its historical capabilities were repaired or released.

## Public library functions

- `run_mtel(source_path, input_data, flow="default")` parses, validates the input contract, evaluates conditions, arbitrates matching rules, and returns a structured decision.
- `inspect_mtel(source_path)` parses the source and compiles every `when` expression without executing a decision.

## Verified design boundaries

- restricted expression AST; no calls, imports, subscripts, file, network, or tool access;
- duplicate rule and flow names are rejected;
- local includes are bounded and traversal/cycles are rejected;
- input is validated against the packaged MTEL/0.2 schema before rule evaluation;
- normal errors are structured and omit Python traceback;
- `--debug` enables diagnostic traceback output;
- JSON audit events are emitted as strict-flat objects with scalar values when log level is `INFO`.

## Install and test

```bash
python -m pip install '.[test]'
python -m pytest -q
python -m build --wheel
```

The public tree is licensed under the MIT License. Review and validation records are delivered separately and are not part of this runtime tree.
