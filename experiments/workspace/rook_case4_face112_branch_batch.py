"""Bounded branch propagation on the complete 112-zero rook incidence face.

One owned child has a sixty-second forward budget and a sixty-five-second
hard deadline. A separate owned child has sixty seconds for cold reason
replay. Partial coverage never implies exclusion of the unqueried branches.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
PREFIX = "experiments/logs/grids-and-triangles/"
SCOPE_SOURCE = "experiments/workspace/rook_case4_face112_branch_scope.py"
SCOPE_SOURCE_SHA = "291be1d8b93acebd859fc642b953acd463e40fd62cecdb3e57c7c14e86a31e8a"
SCOPE = PREFIX + "rook-case4-face112-branch-preparation01.json"
SCOPE_SHA = "5e8bf7a32063cda146b18de2a4b3ee7c4b2a043d5076a5d4a9a9e4ca678144c2"
SCOPE_COLD = PREFIX + "rook-case4-face112-branch-preparation01-replay.json"
SCOPE_COLD_SHA = "52ce504a583c86d1dd24e3841bf37d7167df970159e8b9d4862e598d0b8bb76d"
RULE = "experiments/workspace/complement_rook_35core_case0004_primary_propagation.py"
RULE_SHA = "3e4b8a5118c0ee8e37aee03d5f265128b53af9ae8ffc169393fe2d731062d8f7"
SUPERVISOR = "experiments/workspace/root_prism_free_f0_local_neighbors_batch.py"
SUPERVISOR_SHA = "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"
SUPERVISOR_PREP = "experiments/logs/root-prism-free/f0-local41-batch02-preparation.json"
SUPERVISOR_PREP_SHA = "57bf84bdf102444aad209bf9c7fd5e62c1fc4f7bf584fa3fac8d0b75e71627ae"
SUPERVISOR_REVIEW = "experiments/logs/root-prism-free/f0-local41-batch-independent-source-review.json"
SUPERVISOR_REVIEW_SHA = "56c3f59565b6b211e4f659f3310f50676160b0631701e2addae323a0ab43bad4"
REGISTRY = PREFIX + "complement-rook-35core-case0004-lazy-native-registry.bin.gz"
REGISTRY_SHA = "c32e31d9ce6ec6168cea1c9f6c6ea4165a2ca7a8f2144a59a31e5a1d6da7b543"
RAW_SHA = "3b819e29bc9aacdb5217b151f32b35cb186aa3b8a93a37784edc912ddac36736"
N = 1214
FORWARD_SECONDS, FORWARD_HARD_SECONDS, COLD_HARD_SECONDS = 60, 65, 60


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def read_bound(path, expected, decode=True):
    raw = (ROOT / path).read_bytes()
    assert sha(raw) == expected, path
    return json.loads(raw) if decode else raw


def load_module(path, expected, name):
    read_bound(path, expected, False)
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def save_new(path, value):
    assert not path.exists()
    temporary = path.with_suffix(path.suffix + ".new")
    with temporary.open("x") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")
    path.hardlink_to(temporary)
    temporary.unlink()


def progress(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def binding(path):
    path = path.resolve()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes())}


def metadata():
    read_bound(SCOPE_SOURCE, SCOPE_SOURCE_SHA, False)
    scope = read_bound(SCOPE, SCOPE_SHA)
    cold = read_bound(SCOPE_COLD, SCOPE_COLD_SHA)
    assert cold["status"].startswith("PASS:")
    assert cold["preparation_sha256"] == SCOPE_SHA
    assert cold["retained_branch_count"] == scope["retained_branch_count"] == 64
    assert cold["all72_pattern_dispositions_checked"] and cold["all40_pair_box_checks_rebuilt"]
    assert cold["production_branch_propagations"] == scope["production_branch_propagations"] == 0
    assert scope["original_cover_pattern_count"] == 72
    assert scope["base_augmented_rows"] == 2390
    assert scope["base_and_sum_two_term_occurrences"] == 29074
    ledger = scope["full_branch_ledger"]
    assert [r["branch_id"] for r in ledger] == list(range(72))
    ids = [r["branch_id"] for r in ledger if r["disposition"] ==
           "retained_for_bounded_branch_propagation"]
    assert ids == scope["retained_branch_ids"]
    assert Counter(r["disposition"] for r in ledger) == {
        "retained_for_bounded_branch_propagation": 64,
        "excluded_by_proved_zero": 1,
        "excluded_by_certified_pair": 4,
        "excluded_by_original_native_box": 3,
    }
    for r in ledger:
        assert r["positive_columns"] == sorted(set(r["positive_columns"]))
        assert len(r["positive_columns"]) in (1, 2)
        assert r["augmented_row_count"] == 2390 + len(r["positive_columns"])
    controls = read_bound(SUPERVISOR_PREP, SUPERVISOR_PREP_SHA)
    review = read_bound(SUPERVISOR_REVIEW, SUPERVISOR_REVIEW_SHA)
    assert controls["runner_source_sha256"] == SUPERVISOR_SHA
    assert review["runner_sha256"] == SUPERVISOR_SHA
    assert review["query_preparation_sha256"] == SUPERVISOR_PREP_SHA
    assert review["complete_runner_source_read"]
    read_bound(RULE, RULE_SHA, False)
    read_bound(SUPERVISOR, SUPERVISOR_SHA, False)
    return scope


def prepare(directory):
    started = time.monotonic()
    directory.mkdir(parents=True, exist_ok=False)
    scope = metadata()
    rules = load_module(RULE, RULE_SHA, "frozen_branch_rules")
    bound = scope["complete_input_bindings"]
    inputs = bound["proof_input_bindings"]
    native = read_bound(inputs["native"]["path"], inputs["native"]["sha256"])
    equalities = read_bound(inputs["equalities"]["path"], inputs["equalities"]["sha256"])
    original = rules.rows_from_inventory(native["primary_inventory"])
    assert sha(canonical(original)) == bound["prior_original_rows_sha256"]
    rows = original + [
        rules.row([[a, 1] for a in support], 1, 1, "integer_parity_cover", i)
        for i, support in enumerate(equalities["original_cover_supports"])
    ]
    assert len(rows) == 2273
    rows += [rules.row([[a, 1] for a in pair], 0, 1, "certified_native_bound_pair", i)
             for i, pair in enumerate(bound["certified_pair_AMO_rows"])]
    assert sha(canonical(rows)) == bound["native_and_added_rows_sha256"]
    rows += [rules.row([[a, 1]], 0, 0, "proved_integer_zero", a)
             for a in scope["seed_zero_columns"]]
    assert sha(canonical(rows)) == bound["augmented_integer_rows_sha256"]
    rows.append(scope["added_sum_two_row"])
    assert sha(canonical(rows)) == scope["base_augmented_rows_sha256"]
    assert len(rows) == 2390 and sum(len(r["terms"]) for r in rows) == 29074
    for r in scope["full_branch_ledger"]:
        assert r["assumption_rows"] == [
            rules.row([[a, 1]], 1, 1, "branch_positive_assumption",
                      {"branch_id": r["branch_id"], "column": a})
            for a in r["positive_columns"]
        ]
        assert sha(canonical(rows + r["assumption_rows"])) == r["augmented_rows_sha256"]
    raw = gzip.decompress(read_bound(REGISTRY, REGISTRY_SHA, False))
    assert len(raw) == 178533 * 154 and sha(raw) == RAW_SHA == scope["registry_raw_sha256"]
    assert len(scope["initial_cover_unit_ids"]) == 14
    for i in scope["initial_cover_unit_ids"]:
        a, support = rules.cover(raw, i)
        assert not support and a in scope["seed_zero_columns"]

    rows_path = directory / "rows.json"
    save_new(rows_path, {"schema": "conway99.face112-branch-rows.v1", "rows": rows,
                         "scope_preparation_sha256": SCOPE_SHA,
                         "canonical_rows_sha256": scope["base_augmented_rows_sha256"]})
    record = {
        "schema": "conway99.face112-branch-batch-preparation.v1",
        "status": "PREPARED: complete 64-branch scope; no branch propagated",
        "source_sha256": sha(Path(__file__).read_bytes()),
        "scope": {"path": SCOPE, "sha256": SCOPE_SHA},
        "scope_replay": {"path": SCOPE_COLD, "sha256": SCOPE_COLD_SHA},
        "scope_source": {"path": SCOPE_SOURCE, "sha256": SCOPE_SOURCE_SHA},
        "rules": {"path": RULE, "sha256": RULE_SHA},
        "supervisor": {"path": SUPERVISOR, "sha256": SUPERVISOR_SHA},
        "supervisor_controls": {"path": SUPERVISOR_PREP, "sha256": SUPERVISOR_PREP_SHA},
        "supervisor_source_review": {"path": SUPERVISOR_REVIEW, "sha256": SUPERVISOR_REVIEW_SHA},
        "rows": binding(rows_path),
        "registry": {"path": REGISTRY, "sha256": REGISTRY_SHA,
                     "raw_sha256": RAW_SHA, "bytes": len(raw), "covers": 178533},
        "ordered_branch_ids": scope["retained_branch_ids"],
        "all_original_patterns": 72, "previously_excluded_patterns": 8,
        "retained_patterns": 64, "literal_primary_variables": N,
        "base_rows": 2390, "base_term_occurrences": 29074,
        "branch_row_counts": dict(Counter(r["augmented_row_count"] for r in
                                         scope["full_branch_ledger"]
                                         if r["branch_id"] in scope["retained_branch_ids"])),
        "forward_cooperative_seconds": FORWARD_SECONDS,
        "forward_owned_child_hard_seconds_including_initialization": FORWARD_HARD_SECONDS,
        "cold_owned_child_hard_seconds_including_initialization": COLD_HARD_SECONDS,
        "threads": 1, "maximum_forward_child_invocations": 1,
        "maximum_cold_child_invocations": 1,
        "timer_checks": "Unchanged engine: each integer row and each 128 cover records.",
        "saved_row_loading_only_in_children": True, "parent_domain_rebuilds_in_children": 0,
        "supervisor_controls_repeated": False,
        "branch_assignments_never_promoted_to_global_zeros_or_ones": True,
        "forward_traces_require_separate_cold_check_for_exclusion": True,
        "fixed_point_is_not_SAT_or_graph_completion": True,
        "production_branch_propagations": 0, "solver_calls": 0, "optimizer_calls": 0,
        "case4_excluded": False, "seconds": time.monotonic() - started,
    }
    save_new(directory / "preparation.json", record)
    print(json.dumps({k: record[k] for k in ("status", "retained_patterns", "base_rows",
                      "base_term_occurrences", "branch_row_counts", "seconds")}, indent=2))
    print(json.dumps({"preparation": binding(directory / "preparation.json")}, indent=2))


def checked(preparation, load_rows=True):
    encoded = preparation.read_bytes()
    conf = json.loads(encoded)
    assert conf["source_sha256"] == sha(Path(__file__).read_bytes())
    assert conf["scope"] == {"path": SCOPE, "sha256": SCOPE_SHA}
    assert conf["rules"] == {"path": RULE, "sha256": RULE_SHA}
    assert conf["supervisor"] == {"path": SUPERVISOR, "sha256": SUPERVISOR_SHA}
    assert conf["registry"]["path"] == REGISTRY and conf["registry"]["sha256"] == REGISTRY_SHA
    assert conf["registry"]["raw_sha256"] == RAW_SHA
    assert conf["forward_cooperative_seconds"] == FORWARD_SECONDS
    assert conf["forward_owned_child_hard_seconds_including_initialization"] == FORWARD_HARD_SECONDS
    assert conf["cold_owned_child_hard_seconds_including_initialization"] == COLD_HARD_SECONDS
    scope = metadata()
    assert conf["ordered_branch_ids"] == scope["retained_branch_ids"]
    payload = read_bound(conf["rows"]["path"], conf["rows"]["sha256"])
    assert payload["scope_preparation_sha256"] == SCOPE_SHA
    rows = payload["rows"]
    assert sha(canonical(rows)) == payload["canonical_rows_sha256"] == scope["base_augmented_rows_sha256"]
    assert len(rows) == 2390
    raw = None
    if load_rows:
        raw = gzip.decompress(read_bound(REGISTRY, REGISTRY_SHA, False))
        assert sha(raw) == RAW_SHA and len(raw) == 178533 * 154
    return conf, sha(encoded), scope, rows, raw


def branch_rows(base_rows, branch):
    rows = base_rows + branch["assumption_rows"]
    assert len(rows) == branch["augmented_row_count"]
    assert sha(canonical(rows)) == branch["augmented_rows_sha256"]
    return rows


def case_path(directory, branch_id):
    return directory / ("branch%02d.json" % branch_id)


def check_forward_record(record, preparation_sha, scope, branch_id):
    branch = scope["full_branch_ledger"][branch_id]
    assert branch_id in scope["retained_branch_ids"]
    assert record["mode"] == "forward"
    assert record["source_sha256"] == sha(Path(__file__).read_bytes())
    assert record["preparation_sha256"] == preparation_sha
    assert record["branch_id"] == branch_id
    assert record["positive_columns"] == branch["positive_columns"]
    assert record["augmented_rows_sha256"] == branch["augmented_rows_sha256"]
    trace = record["trace"]
    assert len(trace["values"]) == N and all(v in (-1, 0, 1) for v in trace["values"])
    assert len(trace["records"]) <= N + 1 and 0 <= trace["sweeps"] <= N + 1
    assert type(trace["complete"]) is bool
    assert trace["status"] in (
        "exact contradiction", "exact interval and guarded-cover fixed point",
        "partial exact propagation; time limit reached")
    assert trace["complete"] == (trace["status"] != "partial exact propagation; time limit reached")
    assert record["cold_checked"] is False and record["global_exclusion_claimed"] is False
    return trace


def forward_files(directory, preparation_sha, scope):
    found = []
    for branch_id in scope["retained_branch_ids"]:
        path = case_path(directory, branch_id)
        if path.exists():
            record = json.loads(path.read_bytes())
            trace = check_forward_record(record, preparation_sha, scope, branch_id)
            found.append((branch_id, path, record, trace))
    ids = [r[0] for r in found]
    assert ids == scope["retained_branch_ids"][:len(ids)], "Saved branches must form a fixed-order prefix."
    partial = [i for i, _, _, trace in found if not trace["complete"]]
    assert len(partial) <= 1 and (not partial or partial == ids[-1:])
    return found


def worker(mode, preparation, directory, hard_deadline, result_path=None):
    started = time.monotonic()
    state = {"status": "UNKNOWN_BEFORE_INITIALIZATION", "mode": mode,
             "saved_branch_ids": [], "active_branch": None}
    progress(directory / "progress.json", state)
    try:
        conf, prep_sha, scope, base_rows, raw = checked(preparation)
        rules = load_module(RULE, RULE_SHA, "frozen_branch_worker_rules")
        state["initialization_seconds"] = time.monotonic() - started
        state["preparation_sha256"] = prep_sha
        state["source_sha256"] = conf["source_sha256"]
        if mode == "forward":
            pending = [(i, None, None, None) for i in scope["retained_branch_ids"]]
            deadline = min(hard_deadline, time.monotonic() + FORWARD_SECONDS)
        else:
            assert result_path is not None
            forward = json.loads(result_path.read_bytes())
            assert forward["mode"] == "forward" and forward["preparation_sha256"] == prep_sha
            pending = [r for r in forward_files(result_path.parent, prep_sha, scope) if r[3]["complete"]]
            assert [r[0] for r in pending] == forward["saved_complete_branch_ids"]
            state["forward_result_sha256"] = sha(result_path.read_bytes())
            deadline = hard_deadline
        state["status"] = "RUNNING"
        progress(directory / "progress.json", state)
        for branch_id, forward_path, forward_record, trace in pending:
            if time.monotonic() >= deadline:
                state["status"] = "UNKNOWN_BUDGET_EXHAUSTED"
                break
            branch = scope["full_branch_ledger"][branch_id]
            state["active_branch"] = branch_id
            progress(directory / "progress.json", state)
            rows = branch_rows(base_rows, branch)
            before = time.monotonic()
            if mode == "forward":
                remaining = max(0.0, deadline - before)
                trace = rules.propagate(N, rows, raw, scope["initial_cover_unit_ids"], remaining)
                record = {
                    "mode": "forward", "source_sha256": conf["source_sha256"],
                    "preparation_sha256": prep_sha, "branch_id": branch_id,
                    "positive_columns": branch["positive_columns"],
                    "augmented_rows_sha256": branch["augmented_rows_sha256"],
                    "trace": trace, "forward_seconds": time.monotonic() - before,
                    "cold_checked": False, "global_exclusion_claimed": False,
                }
                check_forward_record(record, prep_sha, scope, branch_id)
            else:
                check = rules.verify_trace(N, rows, raw, trace)
                assert check["contradiction"] == (trace["status"] == "exact contradiction")
                if not check["contradiction"]:
                    assert all(trace["values"][a] == 0 for a in scope["seed_zero_columns"])
                    assert all(trace["values"][a] == 1 for a in branch["positive_columns"])
                if time.monotonic() >= deadline:
                    state["status"] = "UNKNOWN_COLD_CHECK_FINISHED_AFTER_DEADLINE"
                    break
                record = {
                    "mode": "cold", "source_sha256": conf["source_sha256"],
                    "preparation_sha256": prep_sha, "branch_id": branch_id,
                    "positive_columns": branch["positive_columns"],
                    "augmented_rows_sha256": branch["augmented_rows_sha256"],
                    "forward_record_sha256": sha(forward_path.read_bytes()),
                    "exact_reason_replay": check,
                    "branch_excluded": check["contradiction"],
                    "all_assignments_are_conditional_on_branch": True,
                    "global_coordinate_assignments_claimed": [],
                    "seconds": time.monotonic() - before,
                }
            if mode == "forward" and time.monotonic() >= hard_deadline:
                save_new(directory / ("late-branch%02d.json" % branch_id), record)
                state["status"] = "UNKNOWN_FORWARD_TRACE_COMPLETED_AFTER_HARD_DEADLINE"
                break
            save_new(case_path(directory, branch_id), record)
            state["saved_branch_ids"].append(branch_id)
            state["active_branch"] = None
            progress(directory / "progress.json", state)
            if mode == "forward" and not trace["complete"]:
                state["status"] = "UNKNOWN_PARTIAL_FORWARD_TRACE"
                break
        else:
            state["status"] = "ALL_REQUESTED_BRANCH_RECORDS_SAVED"
        state["seconds"] = time.monotonic() - started
        progress(directory / "progress.json", state)
    except Exception as error:
        state.update(status="ERROR_CHILD", error_type=type(error).__name__, message=str(error),
                     seconds=time.monotonic() - started)
        progress(directory / "progress.json", state)
        raise


def run_owned(mode, preparation, directory, forward_result=None):
    # Source/hash preflight does not propagate or replay a branch.
    conf, prep_sha, scope, _, _ = checked(preparation, load_rows=False)
    if mode == "cold":
        assert forward_result is not None
        prior = json.loads(forward_result.read_bytes())
        assert prior["mode"] == "forward" and prior["preparation_sha256"] == prep_sha
    directory.mkdir(parents=True, exist_ok=False)
    supervisor = load_module(SUPERVISOR, SUPERVISOR_SHA, "frozen_branch_supervisor")
    seconds = FORWARD_HARD_SECONDS if mode == "forward" else COLD_HARD_SECONDS
    deadline = time.monotonic() + seconds
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "worker",
               "--worker-mode", mode, "--preparation", str(preparation.resolve()),
               "--output", str(directory.resolve()), "--deadline", repr(deadline)]
    if forward_result is not None:
        command += ["--result", str(forward_result.resolve())]
    process = supervisor.supervise(command, directory, deadline)
    state_path = directory / "progress.json"
    state = json.loads(state_path.read_bytes()) if state_path.exists() else {}
    ordered = scope["retained_branch_ids"]
    result = {
        "schema": "conway99.face112-branch-batch-result.v1", "mode": mode,
        "source_sha256": conf["source_sha256"], "preparation_sha256": prep_sha,
        "scope_preparation_sha256": SCOPE_SHA, "supervisor": process,
        "worker_progress": state, "all_original_patterns": 72,
        "already_certified_excluded_patterns": 8,
        "ordered_retained_branch_ids": ordered,
        "solver_calls": 0, "optimizer_calls": 0,
        "global_coordinate_assignments_claimed": [], "case4_excluded": False,
        "whole_graph_problem_resolved": False,
    }
    if mode == "forward":
        found = forward_files(directory, prep_sha, scope)
        complete = [i for i, _, _, trace in found if trace["complete"]]
        partial = [i for i, _, _, trace in found if not trace["complete"]]
        saved = complete + partial
        active = state.get("active_branch")
        unsaved_active = active if active not in saved else None
        result.update(
            status=("COMPLETE_FORWARD_SCOPE_REQUIRES_COLD_REPLAY" if len(complete) == 64 else
                    "PARTIAL_FORWARD_SCOPE_NO_CASE_EXCLUSION"),
            saved_complete_branch_ids=complete, saved_partial_branch_ids=partial,
            saved_complete_outcomes=dict(Counter(trace["status"] for _, _, _, trace in found
                                                if trace["complete"])),
            active_branch_without_saved_trace=unsaved_active,
            unqueried_branch_ids=[i for i in ordered if i not in saved and i != unsaved_active],
            saved_file_bindings=[binding(path) for _, path, _, _ in found],
            unverified_forward_contradiction_ids=[i for i, _, _, trace in found
                                                  if trace["status"] == "exact contradiction"],
            accepted_branch_exclusions=[],
        )
    else:
        candidates = [r for r in forward_files(forward_result.parent, prep_sha, scope) if r[3]["complete"]]
        verified = []
        for branch_id, path, _, trace in candidates:
            cold_path = case_path(directory, branch_id)
            if not cold_path.exists():
                continue
            record = json.loads(cold_path.read_bytes())
            branch = scope["full_branch_ledger"][branch_id]
            assert record["mode"] == "cold" and record["source_sha256"] == conf["source_sha256"]
            assert record["preparation_sha256"] == prep_sha
            assert record["branch_id"] == branch_id and record["positive_columns"] == branch["positive_columns"]
            assert record["augmented_rows_sha256"] == branch["augmented_rows_sha256"]
            assert record["forward_record_sha256"] == sha(path.read_bytes())
            check = record["exact_reason_replay"]
            assert check["all_records_checked"] == len(trace["records"])
            assert check["contradiction"] == (trace["status"] == "exact contradiction")
            assert check["complete_fixed_point_rechecked"] == (not check["contradiction"])
            assert record["branch_excluded"] == check["contradiction"]
            assert record["all_assignments_are_conditional_on_branch"]
            assert record["global_coordinate_assignments_claimed"] == []
            verified.append((branch_id, cold_path, record))
        ids = [i for i, _, _ in verified]
        assert ids == [r[0] for r in candidates][:len(ids)]
        excluded = [i for i, _, r in verified if r["branch_excluded"]]
        fixed = [i for i, _, r in verified if not r["branch_excluded"]]
        result.update(
            status=("ALL_SAVED_COMPLETE_BRANCHES_COLD_CHECKED" if len(ids) == len(candidates)
                    else "PARTIAL_COLD_SCOPE_NO_UNCHECKED_EXCLUSION"),
            forward_result=binding(forward_result),
            verified_complete_branch_ids=ids,
            verified_contradiction_branch_ids=excluded,
            verified_fixed_point_branch_ids=fixed,
            remaining_complete_branch_ids=[r[0] for r in candidates if r[0] not in ids],
            not_forward_complete_branch_ids=[i for i in ordered if i not in [r[0] for r in candidates]],
            saved_file_bindings=[binding(path) for _, path, _ in verified],
            case4_excluded=(excluded == ordered),
            exact_exclusion_premise="All 72 patterns must be either initially certified or cold-refuted.",
            fixed_point_is_not_SAT_or_graph_completion=True,
        )
    save_new(directory / "result.json", result)
    print(json.dumps({k: v for k, v in result.items() if k not in
                      ("worker_progress", "saved_file_bindings", "ordered_retained_branch_ids")}, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "forward", "cold", "worker"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--worker-mode", choices=("forward", "cold"))
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.output)
    elif args.mode in ("forward", "cold"):
        assert args.preparation is not None
        run_owned(args.mode, args.preparation, args.output, args.result)
    else:
        assert args.preparation is not None and args.deadline is not None
        worker(args.worker_mode, args.preparation, args.output, args.deadline, args.result)


if __name__ == "__main__":
    main()
