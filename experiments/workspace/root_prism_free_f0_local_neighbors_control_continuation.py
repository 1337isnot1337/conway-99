"""Finish only the two uncompleted local41 supervisor controls.

The old successful exit0 control is retained. The late exit3 UNKNOWN record
is immutable. The fresh exit3 control uses the production five-second limit.
No model is rebuilt and no production or synthetic SAT solve is performed.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
RUNNER = "experiments/workspace/root_prism_free_f0_local_neighbors_batch.py"
RUNNER_SHA = "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"
PREFIX = "experiments/logs/root-prism-free/f0-local41-batch01-controls/exit0/supervisor.json"
PREFIX_SHA = "1eb5eb54c00527bf8f1273a33b40495a17bae4823a737c939f554cdff96a3b0e"
FAILURE = "experiments/logs/root-prism-free/f0-local41-batch01-preparation-failure.json"
FAILURE_SHA = "2ac53294b1a05cd81755bcf427b77da8a5d5f8d3423613a849d03a925e03966d"
MODELS = "experiments/logs/root-prism-free/f0-local41-preparation02"
MODELS_SHA = "2213372cd8615df2c177c08d7dfd034812eeb385a75266ada1403d331d765976"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--preparation", type=Path, required=True)
    a = p.parse_args()
    assert not a.directory.exists() and not a.preparation.exists()
    assert sha((ROOT/RUNNER).read_bytes()) == RUNNER_SHA
    assert sha((ROOT/PREFIX).read_bytes()) == PREFIX_SHA
    assert sha((ROOT/FAILURE).read_bytes()) == FAILURE_SHA
    assert sha((ROOT/MODELS/"preparation.json").read_bytes()) == MODELS_SHA
    prefix = json.loads((ROOT/PREFIX).read_bytes())
    failure = json.loads((ROOT/FAILURE).read_bytes())
    assert prefix["status"] == "CHILD_EXITED" and prefix["returncode"] == 0 and prefix["child_reaped"]
    assert failure["production_queries"] == 0 and not failure["query_preparation_created"]
    spec = importlib.util.spec_from_file_location("frozen_local41_runner", ROOT/RUNNER)
    runner = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(runner)
    a.directory.mkdir(parents=True)
    report = {"status": "INCOMPLETE_CONTROL_CONTINUATION", "production_queries": 0,
              "old_successful_controls_repeated": 0, "fresh_controls": [],
              "runner_source_sha256": RUNNER_SHA,
              "helper_source_sha256": sha(Path(__file__).read_bytes())}
    runner.save(a.directory/"status.json", report)
    try:
        before = time.monotonic()
        conf = runner.configuration(ROOT/MODELS)
        conf["preparation_initialization_seconds"] = time.monotonic()-before
        report["preparation_initialization_seconds"] = conf["preparation_initialization_seconds"]
        runner.save(a.directory/"status.json", report)
        controls = [{"name": "exit0", **prefix}]
        for name, command, limit, expected in (
            ("exit3", [sys.executable, "-c", "raise SystemExit(3)"], 5, "ERROR_CHILD_EXIT"),
            ("deadline", [sys.executable, "-c", "import time; time.sleep(10)"], 0.1, "UNKNOWN_HARD_DEADLINE")):
            sub = a.directory/name
            sub.mkdir()
            value = runner.supervise(command, sub, time.monotonic()+limit)
            report["fresh_controls"].append({"name": name, **value})
            runner.save(a.directory/"status.json", report)
            assert value["status"] == expected and value["child_reaped"]
            if name == "exit3":
                assert value["returncode"] == 3
            else:
                assert value["returncode"] < 0
            controls.append({"name": name, **value})
        conf["supervisor_controls"] = controls
        conf["supervisor_control_continuation"] = {
            "helper_source_sha256": report["helper_source_sha256"],
            "prior_success": {"path": PREFIX, "sha256": PREFIX_SHA},
            "prior_failure": {"path": FAILURE, "sha256": FAILURE_SHA},
            "fresh_records": [{"path": str((a.directory/name/"supervisor.json").resolve().relative_to(ROOT)),
                              "sha256": sha((a.directory/name/"supervisor.json").read_bytes())}
                             for name in ("exit3", "deadline")]}
        conf["production_queries"] = 0
        runner.save(a.preparation, conf)
        report.update(status="PASS_COMPLETE_SUPERVISOR_CONTROLS_NO_QUERY",
                      query_preparation_sha256=sha(a.preparation.read_bytes()))
    except Exception as error:
        report.update(error_type=type(error).__name__, message=str(error))
        raise
    finally:
        runner.save(a.directory/"status.json", report)
        print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
