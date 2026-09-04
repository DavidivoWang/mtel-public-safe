# Rule authoring

Each source begins with `@spec MTEL/0.2`. Rule names and flow names must be unique across the included program. Every rule requires one `when` expression and one action. Every flow binds rule names or `*` and selects `overlap hold` or `overlap first`.

Run authoring preflight before execution:

```bash
mtel-runtime inspect --source source/core_public.mtel
```

Preflight compiles each expression and rejects unsupported syntax. Runtime input must match the packaged nested schema.
