"""Finish only the uncompleted scope of the first face112 branch attempt.

The complete engine, row inventory and owned-child supervisor are reused.
No completed forward branch or completed cold check is repeated.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = "experiments/logs/grids-and-triangles/"
BASE_PATH = "experiments/workspace/rook_case4_face112_branch_batch.py"
BASE_SHA = "cda346ce4bb34a9ccc1f5fc603485124bc0cb389b8b9cc48d169b08297a6bd60"
BASE_PREP = LOGS + "rook-case4-face112-branch-batch-preparation01/preparation.json"
BASE_PREP_SHA = "47ebe7180723ab95bdf5370c29a0be6abe80005dc5e0bd7e3df51926282b87ea"
OLD_FORWARD = LOGS + "rook-case4-face112-branch-batch01/result.json"
OLD_FORWARD_SHA = "186df7589b3baf14adda7fcce8409e89e149b5268ff432f12128b7301d09ab4b"
OLD_COLD = LOGS + "rook-case4-face112-branch-batch01-cold/result.json"
OLD_COLD_SHA = "b789fc8ee377e1899d4de553ad7c48019fdea8913599fb3c8605bf28cb80205e"
NEW_FORWARD_IDS = [55, 56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 68, 69, 70]
OLD_COLD_IDS = [29, 30, 31, 34, 36, 37, 38, 39, 41, 42, 43, 44, 45, 46, 47, 48,
                49, 50, 51, 52, 53, 54]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_sha():
    return sha(Path(__file__).read_bytes())


def read(path, expected=None):
    encoded = path.read_bytes()
    if expected is not None:
        assert sha(encoded) == expected, str(path)
    return json.loads(encoded), sha(encoded)


def frozen_base():
    assert sha((ROOT/BASE_PATH).read_bytes()) == BASE_SHA
    spec = importlib.util.spec_from_file_location("frozen_branch_base", ROOT/BASE_PATH)
    base = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(base)
    return base


def old_scope(base, include_raw=False):
    conf, prep_sha, scope, rows, raw = base.checked(ROOT/BASE_PREP, load_rows=include_raw)
    assert prep_sha == BASE_PREP_SHA
    old_forward, _ = read(ROOT/OLD_FORWARD, OLD_FORWARD_SHA)
    old_cold, _ = read(ROOT/OLD_COLD, OLD_COLD_SHA)
    assert old_forward["source_sha256"] == old_cold["source_sha256"] == BASE_SHA
    assert old_forward["preparation_sha256"] == old_cold["preparation_sha256"] == BASE_PREP_SHA
    assert old_cold["forward_result"] == {"path": OLD_FORWARD, "sha256": OLD_FORWARD_SHA}
    found = base.forward_files((ROOT/OLD_FORWARD).parent, BASE_PREP_SHA, scope)
    assert [base.binding(p) for _, p, _, _ in found] == old_forward["saved_file_bindings"]
    assert len(old_forward["saved_complete_branch_ids"]) == 50
    assert old_forward["saved_partial_branch_ids"] == [55]
    assert old_forward["saved_complete_outcomes"] == {"exact interval and guarded-cover fixed point": 50}
    assert len(old_cold["verified_complete_branch_ids"]) == 28
    assert not old_cold["verified_contradiction_branch_ids"]
    assert old_cold["verified_complete_branch_ids"] == old_cold["verified_fixed_point_branch_ids"]
    checked = []
    for item in old_cold["saved_file_bindings"]:
        record, _ = read(ROOT/item["path"], item["sha256"])
        assert record["source_sha256"] == BASE_SHA and record["preparation_sha256"] == BASE_PREP_SHA
        assert record["mode"] == "cold"
        checked.append(record["branch_id"])
    assert checked == old_cold["verified_complete_branch_ids"]
    complete = set(old_forward["saved_complete_branch_ids"])
    cold_done = set(checked)
    assert cold_done <= complete
    assert NEW_FORWARD_IDS == [i for i in scope["retained_branch_ids"] if i not in complete]
    assert OLD_COLD_IDS == [i for i in old_forward["saved_complete_branch_ids"] if i not in cold_done]
    assert set(NEW_FORWARD_IDS).isdisjoint(complete)
    assert set(OLD_COLD_IDS).isdisjoint(cold_done)
    assert complete | set(NEW_FORWARD_IDS) == set(scope["retained_branch_ids"])
    assert cold_done | set(OLD_COLD_IDS) == complete
    return scope, rows, raw, old_forward, old_cold, {i: (p, r, t) for i, p, r, t in found}


def prepare(output):
    started = time.monotonic()
    base = frozen_base()
    scope, _, _, forward, cold, _ = old_scope(base)
    record = {
        "schema": "conway99.face112-branch-continuation-preparation.v1",
        "status": "PREPARED: exact uncompleted scope only; no production call",
        "source_sha256": source_sha(),
        "frozen_base_source": {"path": BASE_PATH, "sha256": BASE_SHA},
        "base_preparation": {"path": BASE_PREP, "sha256": BASE_PREP_SHA},
        "old_forward": {"path": OLD_FORWARD, "sha256": OLD_FORWARD_SHA},
        "old_cold": {"path": OLD_COLD, "sha256": OLD_COLD_SHA},
        "scope_preparation_sha256": base.SCOPE_SHA,
        "unchanged_engine_sha256": base.RULE_SHA,
        "unchanged_supervisor_sha256": base.SUPERVISOR_SHA,
        "all_retained_branch_ids": scope["retained_branch_ids"],
        "already_complete_forward_ids_never_repeated": forward["saved_complete_branch_ids"],
        "already_complete_cold_ids_never_repeated": cold["verified_complete_branch_ids"],
        "forward_ids": NEW_FORWARD_IDS,
        "old_cold_ids": OLD_COLD_IDS,
        "new_cold_ids": "Exactly the complete forward results of this continuation, at most14.",
        "one_prior_partial_trace_restarted": 55,
        "prior_partial_trace_preserved": base.binding((ROOT/OLD_FORWARD).parent/"branch55.json"),
        "maximum_new_propagations": 14, "maximum_new_cold_checks": 36,
        "forward_cooperative_seconds": 60, "forward_hard_seconds_including_initialization": 65,
        "old_cold_hard_seconds_including_initialization": 60,
        "new_cold_hard_seconds_including_initialization": 60,
        "maximum_owned_children_by_stage": {"forward": 1, "cold-old": 1, "cold-new": 1},
        "threads_per_child": 1, "supervisor_controls_repeated": False,
        "native_rows_or_cover_domains_rebuilt": False,
        "literal_primary_variables": 1214, "common_rows": 2390, "all_covers": 178533,
        "branch_assumptions_are_conditional": True,
        "production_propagations": 0, "cold_reason_checks": 0,
        "solver_calls": 0, "optimizer_calls": 0, "case4_excluded": False,
        "seconds": time.monotonic()-started,
    }
    base.save_new(output, record)
    print(json.dumps(record, indent=2))
    print(json.dumps({"preparation_sha256": sha(output.read_bytes())}))


def configuration(path, include_raw=False):
    base = frozen_base()
    conf, prep_sha = read(path)
    assert conf["source_sha256"] == source_sha()
    assert conf["frozen_base_source"] == {"path": BASE_PATH, "sha256": BASE_SHA}
    assert conf["base_preparation"] == {"path": BASE_PREP, "sha256": BASE_PREP_SHA}
    assert conf["old_forward"] == {"path": OLD_FORWARD, "sha256": OLD_FORWARD_SHA}
    assert conf["old_cold"] == {"path": OLD_COLD, "sha256": OLD_COLD_SHA}
    assert conf["forward_ids"] == NEW_FORWARD_IDS and conf["old_cold_ids"] == OLD_COLD_IDS
    assert conf["forward_cooperative_seconds"] == 60
    assert conf["forward_hard_seconds_including_initialization"] == 65
    assert conf["old_cold_hard_seconds_including_initialization"] == 60
    assert conf["new_cold_hard_seconds_including_initialization"] == 60
    assert conf["maximum_owned_children_by_stage"] == {"forward": 1, "cold-old": 1, "cold-new": 1}
    scope, rows, raw, old_forward, old_cold, old_files = old_scope(base, include_raw)
    assert conf["all_retained_branch_ids"] == scope["retained_branch_ids"]
    assert conf["already_complete_forward_ids_never_repeated"] == old_forward["saved_complete_branch_ids"]
    assert conf["already_complete_cold_ids_never_repeated"] == old_cold["verified_complete_branch_ids"]
    return base, conf, prep_sha, scope, rows, raw, old_files


def validate_trace(trace):
    assert len(trace["values"]) == 1214 and all(v in (-1, 0, 1) for v in trace["values"])
    assert len(trace["records"]) <= 1215 and 0 <= trace["sweeps"] <= 1215
    assert type(trace["complete"]) is bool
    assert trace["status"] in ("exact contradiction", "exact interval and guarded-cover fixed point",
                               "partial exact propagation; time limit reached")
    assert trace["complete"] == (trace["status"] != "partial exact propagation; time limit reached")


def new_forward_files(base, directory, prep_sha, scope):
    found = []
    for i in NEW_FORWARD_IDS:
        path = base.case_path(directory, i)
        if not path.exists():
            continue
        record, _ = read(path)
        branch = scope["full_branch_ledger"][i]
        assert record["stage"] == "forward" and record["source_sha256"] == source_sha()
        assert record["preparation_sha256"] == prep_sha and record["base_preparation_sha256"] == BASE_PREP_SHA
        assert record["branch_id"] == i and record["positive_columns"] == branch["positive_columns"]
        assert record["augmented_rows_sha256"] == branch["augmented_rows_sha256"]
        assert not record["cold_checked"] and not record["global_exclusion_claimed"]
        validate_trace(record["trace"])
        found.append((i, path, record, record["trace"]))
    assert [i for i, _, _, _ in found] == NEW_FORWARD_IDS[:len(found)]
    partial = [i for i, _, _, trace in found if not trace["complete"]]
    assert len(partial) <= 1 and (not partial or partial == [found[-1][0]])
    return found


def pending(base, stage, result_path, prep_sha, scope, old_files):
    if stage == "forward":
        return [(i, None, None, None) for i in NEW_FORWARD_IDS]
    if stage == "cold-old":
        return [(i, *old_files[i]) for i in OLD_COLD_IDS]
    assert stage == "cold-new" and result_path is not None
    result, _ = read(result_path)
    assert result["stage"] == "forward" and result["source_sha256"] == source_sha()
    assert result["preparation_sha256"] == prep_sha and result["ordered_scope_ids"] == NEW_FORWARD_IDS
    found = new_forward_files(base, result_path.parent, prep_sha, scope)
    assert [base.binding(path) for _, path, _, _ in found] == result["saved_file_bindings"]
    complete = [r for r in found if r[3]["complete"]]
    assert [r[0] for r in complete] == result["saved_complete_branch_ids"]
    return complete


def worker(stage, preparation, directory, deadline, result_path):
    started = time.monotonic()
    base = frozen_base()
    state = {"stage": stage, "status": "UNKNOWN_BEFORE_INITIALIZATION",
             "saved_branch_ids": [], "active_branch": None}
    base.progress(directory/"progress.json", state)
    try:
        _, conf, prep_sha, scope, common_rows, raw, old_files = configuration(preparation, True)
        rules = base.load_module(base.RULE, base.RULE_SHA, "frozen_continuation_rules")
        jobs = pending(base, stage, result_path, prep_sha, scope, old_files)
        state.update(initialization_seconds=time.monotonic()-started, source_sha256=source_sha(),
                     preparation_sha256=prep_sha, pending_branch_ids=[r[0] for r in jobs], status="RUNNING")
        stop = min(deadline, time.monotonic()+60) if stage == "forward" else deadline
        base.progress(directory/"progress.json", state)
        for i, path, prior, trace in jobs:
            if time.monotonic() >= stop:
                state["status"] = "UNKNOWN_BUDGET_EXHAUSTED"
                break
            state["active_branch"] = i
            base.progress(directory/"progress.json", state)
            branch = scope["full_branch_ledger"][i]
            rows = base.branch_rows(common_rows, branch)
            before = time.monotonic()
            record = {"stage": stage, "source_sha256": source_sha(),
                      "preparation_sha256": prep_sha, "base_preparation_sha256": BASE_PREP_SHA,
                      "branch_id": i, "positive_columns": branch["positive_columns"],
                      "augmented_rows_sha256": branch["augmented_rows_sha256"]}
            if stage == "forward":
                trace = rules.propagate(1214, rows, raw, scope["initial_cover_unit_ids"],
                                        max(0.0, stop-time.monotonic()))
                validate_trace(trace)
                record.update(trace=trace, forward_seconds=time.monotonic()-before,
                              cold_checked=False, global_exclusion_claimed=False)
                if time.monotonic() >= deadline:
                    base.save_new(directory/("late-branch%02d.json" % i), record)
                    state["status"] = "UNKNOWN_LATE_FORWARD_TRACE"
                    break
            else:
                assert trace["complete"]
                check = rules.verify_trace(1214, rows, raw, trace)
                if not check["contradiction"]:
                    assert all(trace["values"][a] == 0 for a in scope["seed_zero_columns"])
                    assert all(trace["values"][a] == 1 for a in branch["positive_columns"])
                if time.monotonic() >= deadline:
                    state["status"] = "UNKNOWN_LATE_COLD_CHECK"
                    break
                record.update(forward_record=base.binding(path), exact_reason_replay=check,
                              branch_excluded=check["contradiction"],
                              all_assignments_are_conditional=True,
                              global_coordinate_assignments_claimed=[], seconds=time.monotonic()-before)
            base.save_new(base.case_path(directory, i), record)
            state["saved_branch_ids"].append(i)
            state["active_branch"] = None
            base.progress(directory/"progress.json", state)
            if stage == "forward" and not trace["complete"]:
                state["status"] = "UNKNOWN_PARTIAL_FORWARD_TRACE"
                break
        else:
            state["status"] = "ALL_REQUESTED_RECORDS_SAVED"
        state["seconds"] = time.monotonic()-started
        base.progress(directory/"progress.json", state)
    except Exception as error:
        state.update(status="ERROR_CHILD", error_type=type(error).__name__, message=str(error),
                     seconds=time.monotonic()-started)
        base.progress(directory/"progress.json", state)
        raise


def launch(stage, preparation, directory, result_path):
    base, conf, prep_sha, scope, _, _, old_files = configuration(preparation)
    jobs = pending(base, stage, result_path, prep_sha, scope, old_files)
    ids = [r[0] for r in jobs]
    assert (stage != "forward" or ids == NEW_FORWARD_IDS)
    assert (stage != "cold-old" or ids == OLD_COLD_IDS)
    directory.mkdir(parents=True, exist_ok=False)
    supervisor = base.load_module(base.SUPERVISOR, base.SUPERVISOR_SHA, "frozen_continuation_supervisor")
    deadline = time.monotonic() + (65 if stage == "forward" else 60)
    command = [sys.executable, "-B", str(Path(__file__).resolve()), "worker",
               "--stage", stage, "--preparation", str(preparation.resolve()),
               "--output", str(directory.resolve()), "--deadline", repr(deadline)]
    if result_path is not None:
        command += ["--result", str(result_path.resolve())]
    process = supervisor.supervise(command, directory, deadline)
    state_path = directory/"progress.json"
    state = read(state_path)[0] if state_path.exists() else {}
    result = {"schema": "conway99.face112-branch-continuation-result.v1",
              "stage": stage, "source_sha256": source_sha(), "preparation_sha256": prep_sha,
              "base_preparation_sha256": BASE_PREP_SHA, "ordered_scope_ids": ids,
              "supervisor": process, "worker_progress": state,
              "old_forward_result": {"path": OLD_FORWARD, "sha256": OLD_FORWARD_SHA},
              "old_cold_result": {"path": OLD_COLD, "sha256": OLD_COLD_SHA},
              "solver_calls": 0, "optimizer_calls": 0,
              "global_coordinate_assignments_claimed": [], "case4_excluded": False}
    if stage == "forward":
        found = new_forward_files(base, directory, prep_sha, scope)
        complete = [i for i, _, _, trace in found if trace["complete"]]
        partial = [i for i, _, _, trace in found if not trace["complete"]]
        saved = [r[0] for r in found]
        active = state.get("active_branch")
        result.update(status=("COMPLETE_CONTINUATION_FORWARD_REQUIRES_COLD"
                              if len(complete) == len(ids) else "PARTIAL_CONTINUATION_FORWARD"),
                      saved_complete_branch_ids=complete, saved_partial_branch_ids=partial,
                      active_without_saved_trace=active if active not in saved else None,
                      unqueried_branch_ids=[i for i in ids if i not in saved and i != active],
                      saved_file_bindings=[base.binding(path) for _, path, _, _ in found],
                      unverified_contradiction_ids=[i for i, _, _, trace in found
                                                  if trace["status"] == "exact contradiction"],
                      accepted_branch_exclusions=[])
    else:
        verified = []
        for i, path, _, trace in jobs:
            cold_path = base.case_path(directory, i)
            if not cold_path.exists():
                continue
            record, _ = read(cold_path)
            branch = scope["full_branch_ledger"][i]
            assert record["stage"] == stage and record["source_sha256"] == source_sha()
            assert record["preparation_sha256"] == prep_sha
            assert record["branch_id"] == i and record["positive_columns"] == branch["positive_columns"]
            assert record["augmented_rows_sha256"] == branch["augmented_rows_sha256"]
            assert record["forward_record"] == base.binding(path)
            check = record["exact_reason_replay"]
            assert check["all_records_checked"] == len(trace["records"])
            assert check["contradiction"] == (trace["status"] == "exact contradiction")
            assert check["complete_fixed_point_rechecked"] == (not check["contradiction"])
            assert record["branch_excluded"] == check["contradiction"]
            assert record["all_assignments_are_conditional"]
            assert record["global_coordinate_assignments_claimed"] == []
            verified.append((i, cold_path, record))
        done = [r[0] for r in verified]
        assert done == ids[:len(done)]
        result.update(status=("ALL_CONTINUATION_COLD_SCOPE_CHECKED" if done == ids
                              else "PARTIAL_CONTINUATION_COLD_SCOPE"),
                      verified_branch_ids=done,
                      verified_contradiction_ids=[i for i, _, r in verified if r["branch_excluded"]],
                      verified_fixed_point_ids=[i for i, _, r in verified if not r["branch_excluded"]],
                      remaining_unchecked_ids=[i for i in ids if i not in done],
                      saved_file_bindings=[base.binding(path) for _, path, _ in verified],
                      fixed_point_is_not_SAT_or_graph_completion=True)
        if result_path is not None:
            result["continuation_forward_result"] = base.binding(result_path)
    base.save_new(directory/"result.json", result)
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ("worker_progress", "saved_file_bindings")}, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "worker"))
    parser.add_argument("--stage", choices=("forward", "cold-old", "cold-new"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--result", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode == "prepare":
        prepare(args.output)
    elif args.mode == "run":
        assert args.stage is not None and args.preparation is not None
        launch(args.stage, args.preparation, args.output, args.result)
    else:
        assert args.stage is not None and args.preparation is not None and args.deadline is not None
        worker(args.stage, args.preparation, args.output, args.deadline, args.result)
