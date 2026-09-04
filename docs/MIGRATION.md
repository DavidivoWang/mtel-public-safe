# Migration to MTEL/0.2

MTEL/0.2 requires explicit `@spec`, unique rule and flow names, bounded local includes, one `when` and one action per rule, and schema-valid runtime input. Existing sources should first pass `mtel-runtime inspect`; runtime inputs should then be checked against `when_input_v0_2.schema.json`.

No automatic migration tool is included.
