#!/usr/bin/env python3
"""Compare current evidence validation with a reviewed local baseline module.

The baseline is executed Python, not data: use only a trusted AIM source snapshot.
Workloads and output are synthetic; results do not measure agent productivity.
"""

from __future__ import annotations

import argparse
import hashlib
import importlib.util
import inspect
import json
import platform
import statistics
import tempfile
import time
import tracemalloc
from pathlib import Path

import aim_runtime_contract


def measure(module, root, references, trials):
    checker = module._evidence_reference_issues
    reusable = "cache" in inspect.signature(checker).parameters

    def workload():
        cache = {}
        manifests = []
        for index, reference in enumerate(references):
            args = {"cache": cache} if reusable else {}
            issues, result = checker(root, [reference], f"criterion {index}", **args)
            if issues:
                raise ValueError(f"correctness check failed: {issues}")
            manifests.extend(result)
        if len(manifests) != len(references) or any(
            item["sha256"] != reference["sha256"] for item, reference in zip(manifests, references)
        ):
            raise ValueError("baseline and current must validate the same evidence")

    workload()  # warmup
    samples = []
    for _ in range(trials):
        start = time.perf_counter()
        workload()
        samples.append(time.perf_counter() - start)
    tracemalloc.start()
    workload()
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {"seconds": samples, "medianSeconds": statistics.median(samples),
            "peakPythonBytes": peak, "correctness": "passed"}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", required=True, type=Path)
    parser.add_argument("--trials", type=int, default=7)
    args = parser.parse_args()
    if not 3 <= args.trials <= 100:
        parser.error("trials must be between 3 and 100")
    spec = importlib.util.spec_from_file_location("aim_measurement_baseline", args.baseline)
    if spec is None or spec.loader is None:
        parser.error("baseline must be a trusted Python source file")
    baseline = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(baseline)
    results = []
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        payload = b"independent engineering evidence\n" * 8192
        (root / "proof.log").write_bytes(payload)
        reference = {"path": "proof.log", "sha256": hashlib.sha256(payload).hexdigest(), "kind": "test_log"}
        unique = []
        for index in range(64):
            name = f"proof-{index}.log"
            (root / name).write_bytes(payload)
            unique.append({**reference, "path": name})
        for references in ([reference], [reference] * 64, unique):
            results.append({"references": len(references), "uniqueFiles": len({r["path"] for r in references}),
                            "evidenceBytes": len(payload), "workloadSha256": reference["sha256"],
                            "baseline": measure(baseline, root, references, args.trials),
                            "current": measure(aim_runtime_contract, root, references, args.trials)})
    print(json.dumps({"environment": {"python": platform.python_version(), "platform": platform.platform()},
                      "baselineSha256": hashlib.sha256(args.baseline.read_bytes()).hexdigest(),
                      "currentSha256": hashlib.sha256(Path(aim_runtime_contract.__file__).read_bytes()).hexdigest(),
                      "readerSha256": hashlib.sha256((Path(__file__).parent / "aim_quality/files.py").read_bytes()).hexdigest(),
                      "trials": args.trials, "warmups": 1, "results": results}, indent=2))


if __name__ == "__main__":
    main()
