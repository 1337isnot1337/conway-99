"""Narrow stdlib replay of the preserved setup kill; no model construction."""
import argparse
import hashlib
import json
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
RUN = LOGS / "f0-character-pool-query-run01"
BINDINGS = {
    "query": ("experiments/workspace/root_prism_free_f0_character_pool_query.py", "820f76ea30bff76e3c0d5d9b79601f6fba1ee11c0534676843315f575bafce39"),
    "supervisor_source": ("experiments/workspace/root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"),
    "preparation": ("experiments/logs/root-prism-free/f0-character-pool-query-preparation01/preparation.json", "6e0812462e4ddb9b1b331d0652edc92d14da75dd4c975eb8dbc5c8cefcd95ba1"),
    "preflight": ("experiments/logs/root-prism-free/f0-character-pool-query-preflight01.json", "41d9e155a23f7e40546b3e546e975b2ac6434a4fae28b4e95ff8faa58becb272"),
    "root_gate": ("experiments/logs/root-prism-free/f0-character-pool-query-root-source-review.json", "efd0c6750982c10b9869462b9f9633af7e396c6bd04b7369449ede72ae3e2df6"),
}
ARTIFACTS = {
    "child.stderr.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "child.stdout.log": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
    "progress.json": "f2638b5ec82da81928d7a5e7f343a28446c8696229a5a0b60f388addc885c54f",
    "result.json": "481700e73395a83275aa247d2ba1cc54c073799b6fd8592a3f2b2d66ff2d24c3",
    "supervisor.json": "91823fd85c7eafcb8b25bb9c05a6c6412265f16581b23ae61b9faafa95db7434",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def check():
    started = time.monotonic()
    data = {}
    for key, (name, expected) in BINDINGS.items():
        raw = (ROOT / name).read_bytes()
        assert sha(raw) == expected
        if name.endswith(".json"):
            data[key] = json.loads(raw)
    assert {p.name for p in RUN.iterdir()} == set(ARTIFACTS)
    sizes = {}
    for name, expected in ARTIFACTS.items():
        raw = (RUN / name).read_bytes()
        assert sha(raw) == expected
        sizes[name] = len(raw)
        if name.endswith(".json"):
            data[name] = json.loads(raw)
    prepared, preflight = data["preparation"], data["preflight"]
    assert prepared["definition"]["runner_source_sha256"] == BINDINGS["query"][1]
    assert preflight["preparation_sha256"] == BINDINGS["preparation"][1]
    assert preflight["status"] == "PASS: exact external-row query cold preflight"
    assert preflight["all18444_domains_and_full34398_target_constraints_checked"]
    assert preflight["initial34281_constraints_are_exact_full_target_subset"]
    assert preflight["all117_dense_rows_retained_in_full_target"]
    result, supervisor, progress = [data[name] for name in ("result.json", "supervisor.json", "progress.json")]
    assert result["supervision"] == supervisor
    assert result["status"] == supervisor["status"] == "ERROR_CHILD_EXIT"
    assert supervisor["returncode"] == -9 and supervisor["child_reaped"]
    assert not supervisor["production_outcome_accepted"]
    assert result["preparation_sha256"] == progress["preparation_sha256"] == BINDINGS["preparation"][1]
    assert result["runner_source_sha256"] == BINDINGS["query"][1]
    assert result["maximum_owned_child_seconds"] == 180 and result["deadline_overrun_seconds"] == 0
    assert 0 < supervisor["seconds"] <= result["owner_seconds"] < 180
    assert progress["status"] == "UNKNOWN_BEFORE_INITIALIZATION" and progress["production_solve_calls"] == 0
    assert progress["iterations"] == progress["added_pool_ids"] == []
    for value in (result, progress):
        assert not value["count_feasibility_claimed"] and not value["literal_incidence_or_graph_claimed"]
        assert not value["F0_excluded"] and not value["automatic_retry"]
        assert value["target_proto_sha256"] == prepared["definition"]["target_proto_sha256"]
        assert value["initial_proto_sha256"] == prepared["definition"]["initial_proto_sha256"]
    assert sizes["child.stderr.log"] == sizes["child.stdout.log"] == 0
    return {"status": "PASS: narrow zero-call failure replay; terminal ERROR unchanged",
            "source_sha256": sha(Path(__file__).read_bytes()),
            "bindings": {k: {"path": p, "sha256": h} for k, (p, h) in BINDINGS.items()},
            "artifacts": {p: {"sha256": h, "bytes": sizes[p]} for p, h in ARTIFACTS.items()},
            "terminal_status": result["status"], "child_returncode": -9,
            "owner_seconds": result["owner_seconds"], "supervisor_seconds": supervisor["seconds"],
            "last_durable_stage": progress["status"], "native_solve_calls": 0,
            "zero_call_basis": "The hash-bound reviewed runner creates a call directory and durable pre-call record before every native solve. No call directory exists; the initial zero-call progress is unchanged.",
            "failure_cause": "Unconfirmed. Signal9 alone does not identify an out-of-memory kill or a solver outcome.",
            "earlier_complete_preflight_bound_not_repeated": BINDINGS["preflight"][1],
            "model_or_plan_archives_loaded": False, "subject_sources_imported": False,
            "model_or_mathematical_reconstruction_repeated": False, "optimizer_calls": 0,
            "count_feasibility_claimed": False, "literal_incidence_or_graph_claimed": False,
            "F0_excluded": False, "retry_performed": False, "seconds": time.monotonic() - started}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = check()
    with args.output.open("x") as stream:
        json.dump(result, stream, indent=2)
        stream.write("\n")
    print(json.dumps(result, indent=2), flush=True)
