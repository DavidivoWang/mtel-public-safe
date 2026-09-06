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

## 5-minute end-to-end example

This example uses the files already included in the repository. It shows one complete path from structured input to an inspectable decision.

### 1. Install the candidate

From the repository root:

```bash
python -m pip install '.[test]'
```

### 2. Look at the input

`examples/input_external_fact.json` contains:

```json
{
  "request": {"kind": "external_fact"},
  "factual_claim": {"has_evidence": false}
}
```

The input says that the request is an external-fact task and that the factual claim does not have evidence.

### 3. Run the MTEL program

```bash
python -m mtel_runtime run \
  --source source/core_public.mtel \
  --input examples/input_external_fact.json \
  --pretty
```

`source/core_public.mtel` includes the public evidence rules. The relevant rule is:

```text
rule block_unsupported_fact priority 100 veto
  when request.kind == "external_fact" and factual_claim.has_evidence == false
  -> BLOCK "evidence_required"
end
```

The returned payload will identify the selected rule and decision. The key fields are:

```json
{
  "status": "BLOCK",
  "decision": {
    "action": "BLOCK",
    "target": "evidence_required",
    "rule": "block_unsupported_fact",
    "priority": 100,
    "veto": true
  },
  "trace": [
    "parse:PASS",
    "flow:default",
    "selected:block_unsupported_fact"
  ]
}
```

The full output also includes rule evaluations and matched rules.

To emit the flat JSON audit events as the run executes, add `--log-level INFO` before the `run` subcommand:

```bash
python -m mtel_runtime --log-level INFO run \
  --source source/core_public.mtel \
  --input examples/input_external_fact.json \
  --pretty
```

### What this demonstrates

The decision path is explicit: structured input → condition evaluation → rule match → priority/veto arbitration → structured decision → trace/audit output.

This example does not depend on asking an LLM to narrate why it produced an answer. The selected rule and execution trace come from the runtime path and can be inspected independently of any later natural-language explanation.

## Install and test

```bash
python -m pip install '.[test]'
python -m pytest -q
python -m build --wheel
```

The public tree is licensed under the MIT License. Review and validation records are delivered separately and are not part of this runtime tree.
