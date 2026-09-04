from __future__ import annotations

import argparse
import json
import time

from mtel_runtime.evaluator import evaluate_expression


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--iterations", type=int, default=5000)
    args = parser.parse_args()
    expression = 'request.kind == "external_fact" and factual_claim.has_evidence == false'
    data = {"request": {"kind": "external_fact"}, "factual_claim": {"has_evidence": False}}
    started = time.perf_counter()
    for _ in range(args.iterations):
        assert evaluate_expression(expression, data)["state"] == "MATCH"
    elapsed = time.perf_counter() - started
    print(json.dumps({
        "iterations": args.iterations,
        "elapsed_seconds": elapsed,
        "microseconds_per_eval": elapsed * 1_000_000 / args.iterations,
        "evaluations_per_second": args.iterations / elapsed,
        "non_claim": "observed runner timing only"
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
