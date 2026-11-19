"""One owned, bounded intake of an independently accepted count vector.

Preparation reads the frozen inverse tables and runs only new adapter/schema
checks. Production run/replay require a future exact arithmetic receipt.
No native optimizer, local-subset census, or automatic retry occurs here.
"""
import argparse
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CORE = ROOT / "experiments/workspace/root_prism_free_f0_literal_lift_intake.py"
SUPERVISOR = ROOT / "experiments/workspace/root_prism_free_f0_local_neighbors_batch.py"
SUPERVISOR_SHA = "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"
OWNED_SECONDS = 60
MAX_BYTES = 64 * 1024 * 1024


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def module(path, expected, name):
    assert sha(path.read_bytes()) == expected
    spec = importlib.util.spec_from_file_location(name, path)
    value = importlib.util.module_from_spec(spec)
    sys.modules[name] = value
    spec.loader.exec_module(value)
    return value


def bound_file(path):
    path = path.resolve()
    raw = path.read_bytes()
    assert len(raw) <= MAX_BYTES
    return {"path": str(path), "sha256": sha(raw), "bytes": len(raw)}


def read_bound(record):
    raw = Path(record["path"]).read_bytes()
    assert len(raw) == record["bytes"] and sha(raw) == record["sha256"]
    return raw


def new_json(path, value):
    raw = canonical(value) + b"\n"
    with path.open("xb") as out:
        out.write(raw)
    return {"path": path.name, "sha256": sha(raw), "bytes": len(raw)}


class Artifacts:
    """Immutable stage checkpoints with one cumulative raw byte budget."""
    def __init__(self, directory):
        self.directory = directory
        self.raw_bytes = 0
        self.records = {}

    def save(self, name, value, compressed=True):
        assert name not in self.records
        raw = canonical(value) + b"\n"
        limit = MAX_BYTES if name == "worker_result" else MAX_BYTES - 1024 * 1024
        if self.raw_bytes + len(raw) > limit:
            raise RuntimeError("declared total artifact byte budget exceeded")
        self.raw_bytes += len(raw)
        stored = gzip.compress(raw, mtime=0) if compressed else raw
        filename = name + (".json.gz" if compressed else ".json")
        path = self.directory / filename
        with path.open("xb") as out:
            out.write(stored)
        self.records[name] = {"path": filename, "sha256": sha(stored),
                              "bytes": len(stored), "raw_bytes": len(raw)}
        return self.records[name]


def read_artifact(directory, metadata):
    raw = (directory / metadata["path"]).read_bytes()
    assert len(raw) == metadata["bytes"] and sha(raw) == metadata["sha256"]
    decoded = gzip.decompress(raw) if metadata["path"].endswith(".gz") else raw
    assert len(decoded) == metadata["raw_bytes"] <= MAX_BYTES
    return json.loads(decoded)


def check_preparation(preparation, core_sha):
    assert preparation["source_sha256"] == core_sha
    assert preparation["runner_source_sha256"] == sha(Path(__file__).read_bytes())
    assert preparation["limits"]["owned_seconds"] == OWNED_SECONDS
    assert preparation["limits"]["maximum_raw_output_bytes"] == MAX_BYTES
    assert preparation["production_candidates_evaluated"] == preparation["CSP_search_calls"] == 0
    assert preparation["optimizer_calls"] == 0
    assert preparation["provisional_or_native_status_is_insufficient"]


def worker(directory, request_sha, deadline):
    started = time.monotonic()
    artifacts = Artifacts(directory)
    result = {"status": "UNKNOWN_BEFORE_INITIALIZATION", "fixed_native_count_assignment_rejected": False,
              "F0_excluded": False, "exterior_Y_edges_realized": False,
              "graph_completion_claimed": False, "optimizer_calls": 0,
              "new_local_subset_enumerations": 0}
    try:
        raw = (directory / "request.json").read_bytes()
        assert sha(raw) == request_sha
        request = json.loads(raw)
        assert request["runner_source_sha256"] == sha(Path(__file__).read_bytes())
        core = module(CORE, request["intake_source_sha256"], "literal_lift_intake_core")
        assert core.LIMITS["owned_seconds"] == OWNED_SECONDS
        core.tick(deadline)
        if request["mode"] == "prepare":
            configuration = core.configuration(deadline)
            configuration["runner_source_sha256"] = sha(Path(__file__).read_bytes())
            configuration["owned_deadline_includes_imports_loading_checks_and_writes"] = True
            configuration["partial_CSP_tree_saved_before_trace_replay"] = True
            configuration["existing_supervisor_controls_reexecuted"] = False
            artifacts.save("preparation", configuration, compressed=False)
            result.update(status="PASS_PREPARATION_ONLY", production_candidates_evaluated=0,
                          CSP_search_calls=0)
        else:
            preparation = json.loads(read_bound(request["preparation"]))
            check_preparation(preparation, request["intake_source_sha256"])
            inverse, domains, context, lift, kernel = core.load_inputs(deadline)
            assert core.sha(core.canonical(domains)) == preparation["target_domains_sha256"]
            for key in ("candidate", "receipt", "query_preparation", "receipt_source"):
                read_bound(request[key])
            admission = core.admit(Path(request["candidate"]["path"]), Path(request["receipt"]["path"]),
                                   Path(request["query_preparation"]["path"]),
                                   Path(request["receipt_source"]["path"]), inverse, domains, lift)
            for key, field in (("candidate", "candidate_file_sha256"),
                               ("receipt", "acceptance_receipt_sha256"),
                               ("query_preparation", "query_preparation_sha256"),
                               ("receipt_source", "acceptance_source_sha256")):
                assert admission[field] == request[key]["sha256"]
            # The five exact acceptance gates above precede relation construction.
            artifacts.save("admission", admission)
            result["candidate_file_sha256"] = admission["candidate_file_sha256"]
            result["canonical_integer_vector_sha256"] = admission["canonical_integer_vector_sha256"]
            result["acceptance_receipt_sha256"] = admission["acceptance_receipt_sha256"]
            result["acceptance_source_sha256"] = admission["acceptance_source_sha256"]
            result["production_candidates_evaluated"] = 1
            result["initialization_seconds"] = time.monotonic() - started
            if request["mode"] == "run":
                result["CSP_search_calls"] = "not_yet_returned"
                answer = core.search(admission, inverse, context, lift, kernel, deadline,
                                     checkpoint=lambda name, value: artifacts.save(name, value))
                artifacts.save("exact_result", answer)
                result.update({key: answer[key] for key in (
                    "status", "CSP_search_calls", "fixed_native_count_assignment_rejected",
                    "F0_excluded", "exterior_Y_edges_realized", "graph_completion_claimed")})
                result["returned_tree_checked"] = True
            else:
                assert request["mode"] == "replay"
                saved_owner = json.loads(read_bound(request["saved_owner"]))
                assert saved_owner["owned_child_completed_on_time"]
                saved_directory = Path(request["saved_owner"]["path"]).parent
                saved_request_raw = (saved_directory / saved_owner["request"]["path"]).read_bytes()
                assert sha(saved_request_raw) == saved_owner["request"]["sha256"]
                saved_request = json.loads(saved_request_raw)
                assert saved_request["mode"] == "run"
                assert saved_request["intake_source_sha256"] == request["intake_source_sha256"]
                assert saved_request["runner_source_sha256"] == request["runner_source_sha256"]
                assert saved_request["preparation"]["sha256"] == request["preparation"]["sha256"]
                saved_worker = read_artifact(saved_directory, saved_owner["worker_record"])
                assert saved_owner["status"] == saved_worker["status"]
                assert saved_worker["status"] in ("EXACT_LITERAL_SELECTOR_GRAM_LIFT",
                    "EXACT_MOMENT_LIFT_WITH_FAILED_SELECTOR_EQUALITIES",
                    "FIXED_SELECTOR_COUNT_PROJECTION_UNREALIZABLE", "UNKNOWN_LITERAL_LIFT")
                assert saved_worker["returned_tree_checked"]
                assert saved_worker["candidate_file_sha256"] == admission["candidate_file_sha256"]
                assert saved_worker["acceptance_receipt_sha256"] == admission["acceptance_receipt_sha256"]
                assert saved_worker["acceptance_source_sha256"] == admission["acceptance_source_sha256"]
                answer = read_artifact(saved_directory, saved_worker["artifacts"]["exact_result"])
                assert read_artifact(saved_directory, saved_worker["artifacts"]["bundle"]) == answer["bundle"]
                assert read_artifact(saved_directory, saved_worker["artifacts"]["CSP_result"]) == answer["CSP_result"]
                checked = core.replay(admission, inverse, context, lift, kernel, answer, deadline)
                artifacts.save("exact_replay", checked)
                result.update(status="PASS_COLD_LITERAL_LIFT_REPLAY", CSP_search_calls=0,
                              certified_outcome=checked["certified_outcome"])
        core.tick(deadline)
    except TimeoutError as error:
        result.update(status="UNKNOWN_COOPERATIVE_DEADLINE", error=str(error),
                      fixed_native_count_assignment_rejected=False)
    except Exception as error:
        result.update(status="ERROR_NO_CERTIFIED_LIFT", error_type=type(error).__name__,
                      error=str(error), fixed_native_count_assignment_rejected=False)
    finally:
        result.update(seconds=time.monotonic()-started, artifacts=artifacts.records,
                      total_raw_artifact_bytes=artifacts.raw_bytes)
        artifacts.save("worker_result", result, compressed=False)


def owned(args):
    started = time.monotonic()
    deadline = started + OWNED_SECONDS
    directory = args.output.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    request = {"schema": "conway99.f0.literal_lift_intake.request.v1", "mode": args.mode,
               "runner_source_sha256": sha(Path(__file__).read_bytes()),
               "intake_source_sha256": sha(CORE.read_bytes()), "owned_seconds": OWNED_SECONDS}
    if args.mode != "prepare":
        for field in ("preparation", "candidate", "receipt", "query_preparation", "receipt_source"):
            value = getattr(args, field)
            assert value is not None, field
            request[field] = bound_file(value)
        preparation = json.loads(read_bound(request["preparation"]))
        check_preparation(preparation, request["intake_source_sha256"])
        if args.mode == "replay":
            assert args.run_directory is not None
            request["saved_owner"] = bound_file(args.run_directory / "owner-result.json")
    request_record = new_json(directory / "request.json", request)
    supervisor = module(SUPERVISOR, SUPERVISOR_SHA, "frozen_literal_lift_supervisor")
    stopped = supervisor.supervise(
        [sys.executable, str(Path(__file__).resolve()), "_worker", "--output", str(directory),
         "--request-sha", request_record["sha256"], "--deadline", str(deadline)],
        directory, deadline)
    record = {"schema": "conway99.f0.literal_lift_intake.owner.v1", "operation": args.mode,
              "status": "UNKNOWN_NO_CERTIFIED_LIFT", "request": request_record,
              "supervisor": stopped, "owned_child_completed_on_time": False,
              "fixed_native_count_assignment_rejected": False, "F0_excluded": False,
              "exterior_Y_edges_realized": False, "graph_completion_claimed": False,
              "optimizer_calls": 0, "new_local_subset_enumerations": 0}
    worker_path = directory / "worker_result.json"
    if worker_path.exists():
        worker_raw = worker_path.read_bytes()
        assert len(worker_raw) <= MAX_BYTES
        result = json.loads(worker_raw)
        record["worker_record"] = {"path": worker_path.name, "sha256": sha(worker_raw),
                                   "bytes": len(worker_raw), "raw_bytes": len(worker_raw)}
        if stopped["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
            record["owned_child_completed_on_time"] = True
            record["status"] = result["status"]
            record["fixed_native_count_assignment_rejected"] = result["fixed_native_count_assignment_rejected"]
    record["seconds"] = time.monotonic() - started
    new_json(directory / "owner-result.json", record)
    print(json.dumps({"status": record["status"], "seconds": record["seconds"],
                      "directory": str(directory)}, sort_keys=True))


def main():
    if not __debug__:
        raise RuntimeError("exact intake requires Python assertions enabled")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "replay", "_worker"))
    parser.add_argument("--output", type=Path, required=True)
    for name in ("preparation", "candidate", "receipt", "query-preparation", "receipt-source", "run-directory"):
        parser.add_argument("--" + name, type=Path)
    parser.add_argument("--request-sha")
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode == "_worker":
        assert args.request_sha is not None and args.deadline is not None
        worker(args.output.resolve(), args.request_sha, args.deadline)
    else:
        assert args.request_sha is args.deadline is None
        owned(args)


if __name__ == "__main__":
    main()
