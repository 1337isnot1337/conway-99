"""Replay only the uncompleted suffix of the frozen F0 conflict inventory.

The first bounded cold replay stopped after twenty complete centers.
This separate gate never recomputes those centers and preserves both
original attempts. It has its own ten-second bound.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    "source": ("experiments/workspace/root_prism_free_f0_local_conflict_inventory.py",
               "6e7a638c0c9045f82aceb37d4eceb749ad8911be4b65abeb52dd7be829f18036"),
    "preparation": ("experiments/logs/root-prism-free/f0-local-conflict-inventory01-model-preparation.json",
                    "a1cd24f263b9712aeb7f4ecb1b69467f698c83527199c4fc063a3c63ccee5406"),
    "record": ("experiments/logs/root-prism-free/f0-local-conflict-inventory01.json.gz",
               "cbfdad339ab84cb7eeb6b221e10be3c4c1db4fb70932de3a28e62ee4642cb7e0"),
    "prefix_replay": ("experiments/logs/root-prism-free/f0-local-conflict-inventory01-replay.json",
                      "4717dc11e6f40007d58befc3ae968ceaaadb805c0548f797817846b3a0843be9"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=float, default=10)
    args = parser.parse_args()
    assert 0 < args.seconds <= 10 and not args.output.exists()
    started = time.monotonic()
    deadline = started+args.seconds
    suffix = []
    inputs = {}
    report = {}
    try:
        for name, (path, digest) in INPUTS.items():
            raw = (ROOT/path).read_bytes()
            assert sha(raw) == digest
            inputs[name] = raw
        spec = importlib.util.spec_from_file_location("frozen_f0_local_conflict_inventory", ROOT/INPUTS["source"][0])
        subject = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(subject)
        saved = json.loads(inputs["preparation"])
        full = json.loads(gzip.decompress(inputs["record"]))
        prefix = json.loads(inputs["prefix_replay"])
        assert prefix["status"] == "INCOMPLETE_NO_COMPLETE_INVENTORY_CLAIM"
        assert prefix["error_type"] == "TimeoutError"
        prior = prefix["completed_center_records"]
        assert len(prior) == 20 and prior == full["representative_records"][:20]
        assert prefix["source_sha256"] == saved["source_sha256"] == INPUTS["source"][1]
        assert len(full["representative_records"]) == 42
        # Revalidate every frozen input and transport. The already executed
        # small controls are immutable preparation data, not new center work.
        data = subject.load(deadline)
        assert subject.preparation(data, saved["controls"]) == saved
        for row in saved["representatives"][20:]:
            subject.tick(deadline, "next suffix center")
            rebuilt = subject.center_inventory(data, row["center"], deadline)
            assert rebuilt == full["representative_records"][20+len(suffix)]
            suffix.append(rebuilt)
        subject.tick(deadline, "complete suffix")
        assert len(suffix) == 22 and prior+suffix == full["representative_records"]
        expected = {
            "schema": "conway99.f0-local-conflict-inventory.v1",
            "status": "COMPLETE_LISTED_LOCAL_CONFLICT_INVENTORY",
            "source_sha256": saved["source_sha256"],
            "preparation_sha256": INPUTS["preparation"][1],
            "inputs": saved["inputs"], "center_transports": saved["center_transports"],
            "representative_records": prior+suffix, "complete_centers": 42,
            "literal_centers_covered": 480, "point_loaded": False, "optimizer_calls": 0,
            "maximal_clique_search": False, "odd_cycle_search": False,
            "local_feasibility_solve": False, "graph_existence_resolved": False,
            "scope": saved["scope"], "homogeneous_coverage_scope": saved["homogeneous_coverage_scope"],
        }
        assert expected == full
        report = {
            "status": "PASS: complete cold replay by immutable prefix and fresh suffix",
            "prefix_centers": 20, "fresh_suffix_centers": 22, "complete_centers": 42,
            "literal_centers_covered": 480, "production_record_raw_sha256": sha(subject.canonical(expected)),
            "suffix_center_hashes": [[row["center"], sha(subject.canonical(row))] for row in suffix],
            "already_completed_centers_recomputed": 0, "point_loaded": False, "optimizer_calls": 0,
            "maximal_clique_search": False, "odd_cycle_search": False, "local_feasibility_solve": False,
        }
    except Exception as error:
        report = {
            "status": "INCOMPLETE_NO_COMPLETE_REPLAY_CLAIM", "error_type": type(error).__name__,
            "message": str(error), "completed_suffix_center_records": suffix,
            "point_loaded": False, "optimizer_calls": 0,
        }
    report["source_sha256"] = sha(Path(__file__).read_bytes())
    report["inputs"] = {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()}
    report["seconds"] = time.monotonic()-started
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps({k: v for k, v in report.items() if k != "completed_suffix_center_records"}, indent=2))
    if not report["status"].startswith("PASS:"):
        raise SystemExit(1)


if __name__ == "__main__":
    main()
