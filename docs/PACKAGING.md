# Packaging

The wheel contains the `mtel_runtime` package and the packaged MTEL/0.2 JSON Schema. Rule sources and example inputs remain caller-controlled files outside the wheel.

CI builds one exact wheel, records its SHA-256, installs that wheel into a clean Python 3.11 environment, and replays import, CLI, tests, and benchmark checks.
