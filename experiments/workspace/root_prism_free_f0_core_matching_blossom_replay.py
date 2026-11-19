"""Owned cold preflight/terminal replay for the strengthened blossom count query.

Only the final archived target and actual saved prefixes are loaded.
A fully checked target vector stays provisional. This module performs no
restored-parent acceptance and never constructs or calls a solver.
"""
import argparse
import gc
import hashlib
import json
from math import isfinite
from pathlib import Path
import sys
import time

import root_prism_free_f0_core_matching_blossom_query as query

QUERY_SHA = '67cd7853f00d5f99df7524046c30d72a1286106c2f5577a50d573cf1fa4a967b'
ROOT = Path(__file__).resolve().parents[2]
COMPLETED_STATES = {
    "PROVISIONAL_FULL_TARGET_WITNESS", "EXACT_REJECTED_CANDIDATE_CERTIFIED_ROWS_APPENDED",
    "UNKNOWN_CALL_LIMIT_REJECTED_CANDIDATE", "UNKNOWN_TOTAL_LIMIT_REJECTED_CANDIDATE",
    "UNPROVED_NATIVE_INFEASIBLE", "ERROR_NATIVE_MODEL_INVALID", "UNKNOWN_NATIVE_LIMIT",
    "UNKNOWN_NATIVE_BUDGET_OVERRUN", "UNKNOWN_NATIVE_BUDGET_REJECTED_CANDIDATE",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def artifact(path):
    raw = path.read_bytes()
    return {"sha256": sha(raw), "bytes": len(raw)}

def read_record(path, expected=None):
    raw = path.read_bytes()
    if expected is not None:
        assert sha(raw) == expected
    return json.loads(raw), sha(raw)

def replay(preparation_path, run_directory=None, stage=None):
    started = time.monotonic()
    from google.protobuf import text_format
    from ortools.sat import cp_model_pb2, sat_parameters_pb2
    stage = (lambda *a, **k: None) if stage is None else stage
    assert sha(Path(query.__file__).read_bytes()) == QUERY_SHA
    prepared, preparation_sha = query.check_preparation(preparation_path)
    source, plan, target, initial, _ = query.load_target(prepared, stage)
    del initial; gc.collect()
    report = {"status": "PASS: lightweight exact target/prefix cold preflight",
              "source_sha256": sha(Path(__file__).read_bytes()), "query_source_sha256": QUERY_SHA,
              "preparation_sha256": preparation_sha, "target_proto_sha256": query.TARGET_SHA,
              "initial_proto_sha256": query.INITIAL_SHA,
              "all32296_domains_and_frozen_full65811_target_bound": True,
              "initial65694_constraints_are_exact_full_target_subset": True,
              "all117_dense_rows_retained_in_full_target": True,
              "old_complete_proof_censuses_bound_not_repeated": True,
              "optimizer_calls": 0, "CpSolver_constructed": False,
              "count_feasibility_claimed": False, "literal_incidence_or_graph_claimed": False, "F0_excluded": False}
    if run_directory is None:
        report["seconds"] = time.monotonic() - started
        return report
    result, result_sha = read_record(run_directory / "result.json")
    supervisor, supervisor_sha = read_record(run_directory / "supervisor.json")
    assert result["supervision"] == supervisor and supervisor["child_reaped"]
    assert result["runner_source_sha256"] == QUERY_SHA and result["preparation_sha256"] == preparation_sha
    assert result["target_proto_sha256"] == query.TARGET_SHA and result["initial_proto_sha256"] == query.INITIAL_SHA
    assert result["maximum_owned_child_seconds"] == 300 and not result["automatic_retry"]
    assert result["maximum_cumulative_native_solve_seconds"] == query.NATIVE_SECONDS == 180
    assert not result["literal_incidence_or_graph_claimed"] and not result["F0_excluded"]
    assert not result["count_feasibility_claimed"]
    assert result.get("full_target_candidate_provisional", False) == (result["status"] == "PROVISIONAL_FULL_TARGET_WITNESS")
    child = None
    if supervisor["status"] == "CHILD_EXITED":
        assert supervisor["returncode"] == 0
        child, _ = read_record(run_directory / "child-result.json", result["child_result_sha256"])
        assert child["status"] == result["status"]
        assert child["production_solve_calls"] == result["production_solve_calls"]
        assert 0 <= child["production_solve_calls"] <= 12
        assert child["preparation_sha256"] == preparation_sha
        assert child["target_proto_sha256"] == query.TARGET_SHA and child["initial_proto_sha256"] == query.INITIAL_SHA
        assert child["count_feasibility_claimed"] == result["count_feasibility_claimed"]
        assert not child["literal_incidence_or_graph_claimed"] and not child["F0_excluded"]
    else:
        assert supervisor["status"] in ("UNKNOWN_HARD_DEADLINE", "ERROR_CHILD_EXIT", "ERROR_SUPERVISION")
        assert result["status"] == supervisor["status"] and not result["count_feasibility_claimed"]
    directories = sorted(p for p in run_directory.iterdir() if p.is_dir() and p.name.startswith("call"))
    assert len(directories) <= 12
    row_ids, added = list(plan["initial_to_target_rows"]), []
    records, provisional_calls, pending = [], [], []
    prefix_complete = True
    native_used = 0.0
    for call, directory in enumerate(directories):
        stage("saved_call_prefix_replay", call_index=call)
        assert directory.name == f"call{call:03d}" and prefix_complete
        files = {p.name: artifact(p) for p in directory.iterdir() if p.is_file()}
        entry = {"call_index": call, "artifacts": files}
        records.append(entry)
        if "prefix.json" not in files:
            assert call == len(directories) - 1 and child is None
            entry["partial_before_prefix"] = True
            prefix_complete = False
            continue
        prefix, prefix_sha = read_record(directory / "prefix.json")
        assert prefix["call_index"] == call and prefix["added_pool_ids"] == added
        assert prefix["active_target_row_ids_sha256"] == sha(query.canonical(row_ids))
        assert files["model.pb"]["sha256"] == prefix["actual_model_sha256"]
        assert files["model.pb"]["bytes"] == prefix["actual_model_bytes"]
        proto = cp_model_pb2.CpModelProto()
        proto.ParseFromString((directory / "model.pb").read_bytes())
        checked = source.exact_proto_check(proto, target, row_ids)
        assert checked == prefix["native_exact_checks"]
        if call == 0:
            assert prefix["actual_model_sha256"] == query.INITIAL_SHA and not added
        entry["exact_active_constraint_count"] = len(row_ids)
        if "record.json" not in files:
            assert call == len(directories) - 1
            if child is not None:
                assert child["status"] == "UNKNOWN_TOTAL_LIMIT_AFTER_PREFIX_SERIALIZATION"
            entry["prefix_without_native_call_record"] = True
            prefix_complete = False
            continue
        step, step_sha = read_record(directory / "record.json")
        assert step["call_index"] == call and step["prefix_sha256"] == prefix_sha
        parameters_raw = (directory / "parameters.pbtxt").read_bytes()
        assert sha(parameters_raw) == step["parameters_sha256"]
        parameters = sat_parameters_pb2.SatParameters()
        text_format.Parse(parameters_raw.decode(), parameters)
        assert parameters.num_search_workers == 1 and parameters.random_seed == 0
        assert parameters.HasField("linearization_level") and parameters.linearization_level == 0
        assert parameters.cp_model_probing_level == 0 and parameters.log_search_progress and parameters.log_to_stdout
        assert 0 < parameters.max_time_in_seconds <= 180
        assert parameters.max_time_in_seconds == step["native_max_time_seconds"]
        assert step["native_solve_wall_seconds_before"] == native_used
        assert step["native_seconds_remaining_before"] == query.NATIVE_SECONDS - native_used
        assert 0 < parameters.max_time_in_seconds <= query.NATIVE_SECONDS - native_used
        if "solve_wall_seconds" in step:
            assert isfinite(step["solve_wall_seconds"]) and step["solve_wall_seconds"] >= 0
            native_used += step["solve_wall_seconds"]
            assert step["cumulative_native_solve_wall_seconds"] == native_used
            assert step["native_budget_overrun_seconds"] == max(0.0, native_used - query.NATIVE_SECONDS)
        response, point = None, None
        if "candidate.json" in files:
            point, point_sha = read_record(directory / "candidate.json", step.get("candidate_sha256"))
            assert all(type(v) is int for v in point)
            if "candidate_values" in step:
                assert len(point) == step["candidate_values"]
            entry["saved_integer_candidate_values"] = len(point)
            if "canonical_integer_vector_sha256" in step:
                assert step["canonical_integer_vector_sha256"] == sha(query.canonical(point))
        if "response.pbtxt" in files:
            response_raw = (directory / "response.pbtxt").read_bytes()
            if "response_sha256" in step:
                assert sha(response_raw) == step["response_sha256"]
            response = cp_model_pb2.CpSolverResponse()
            text_format.Parse(response_raw.decode(), response)
            if "native_status" in step:
                assert response.status == step["native_status_code"]
                assert cp_model_pb2.CpSolverStatus.Name(response.status) == step["native_status"]
            if response.solution:
                assert point == list(response.solution)
        if step["status"] not in COMPLETED_STATES:
            assert call == len(directories) - 1 and child is None
            entry.update(partial_child_status=step["status"], acceptance_not_inferred=True)
            if point is not None:
                pending.append({"call_index": call, "candidate_sha256": files["candidate.json"]["sha256"],
                                "stage": step["status"]})
            prefix_complete = False
            continue
        assert response is not None
        if step["status"] == "UNKNOWN_NATIVE_BUDGET_OVERRUN":
            assert native_used > query.NATIVE_SECONDS and call == len(directories) - 1
            assert not step["appended_pool_ids"]
            entry["native_budget_overrun_acceptance_not_inferred"] = True
            if point is not None:
                pending.append({"call_index": call, "candidate_sha256": files["candidate.json"]["sha256"],
                                "stage": "native_budget_overrun_saved_only"})
        elif response.status in (cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL):
            assert native_used <= query.NATIVE_SECONDS
            assert point is not None and len(point) == 32296
            assert query.evaluate_proto(proto, point)
            violations = query.pool_scan(point, target, plan)
            scan, scan_sha = read_record(directory / "pool-scan.json", step["pool_scan_sha256"])
            expected_scan = {"status": "PASS: exact active-prefix and all117 external-row evaluation",
                             "candidate_sha256": files["candidate.json"]["sha256"], "prefix_sha256": prefix_sha,
                             "active_constraints_checked": len(row_ids), "external_rows_checked": 117,
                             "violations": violations, "all_arithmetic_Python_integers": True}
            assert scan == expected_scan and step["violated_external_rows"] == len(violations)
            entry["all117_external_rows_exactly_replayed"] = True
            if not violations:
                assert step["status"] == "PROVISIONAL_FULL_TARGET_WITNESS" and not step["appended_pool_ids"]
                assert call == len(directories) - 1
                if child is not None and result["status"] == "PROVISIONAL_FULL_TARGET_WITNESS":
                    assert child["provisional_call_index"] == call
                    exact = query.provisional_record(point, target, directory / "candidate.json", preparation_sha)
                    stored, _ = read_record(directory / "target-point-check.json", step["target_point_check_sha256"])
                    assert stored == exact and not exact["accepted"]
                    assert not exact["restored_original_parent_checks_passed"]
                    entry["full_target_integer_check_without_parent_acceptance"] = exact
                    provisional_calls.append(call)
                pending.append({"call_index": call, "candidate_sha256": files["candidate.json"]["sha256"],
                                "stage": "separate restored-original-parent arithmetic receipt required"})
            else:
                selected = query.choose_rows(violations, added)
                assert selected == step["selected_pool_ids"]
                if step["status"] == "EXACT_REJECTED_CANDIDATE_CERTIFIED_ROWS_APPENDED":
                    assert selected == step["appended_pool_ids"] and 0 < len(selected) <= 16
                    added.extend(selected)
                    row_ids.extend(plan["external_pool"][i]["target_constraint"] for i in selected)
                    assert len(added) == len(set(added)) <= 117
                    assert step["next_active_target_row_ids_sha256"] == sha(query.canonical(row_ids))
                    entry["all_appended_rows_are_exact_violated_target_rows"] = True
                else:
                    assert not step["appended_pool_ids"]
                    assert step["status"] in ("UNKNOWN_CALL_LIMIT_REJECTED_CANDIDATE", "UNKNOWN_TOTAL_LIMIT_REJECTED_CANDIDATE",
                                                "UNKNOWN_NATIVE_BUDGET_REJECTED_CANDIDATE")
                    if step["status"] == "UNKNOWN_NATIVE_BUDGET_REJECTED_CANDIDATE":
                        assert native_used >= query.NATIVE_SECONDS
                    assert call == len(directories) - 1
                    if step["status"] == "UNKNOWN_CALL_LIMIT_REJECTED_CANDIDATE":
                        assert call == 11
        elif response.status == cp_model_pb2.INFEASIBLE:
            assert step["status"] == "UNPROVED_NATIVE_INFEASIBLE" and not response.solution
            assert not step["appended_pool_ids"] and call == len(directories) - 1
            entry["native_infeasibility_remains_unproved"] = True
        elif response.status == cp_model_pb2.MODEL_INVALID:
            assert step["status"] == "ERROR_NATIVE_MODEL_INVALID" and call == len(directories) - 1
        else:
            assert response.status == cp_model_pb2.UNKNOWN and step["status"] == "UNKNOWN_NATIVE_LIMIT"
            assert not step["appended_pool_ids"] and call == len(directories) - 1
            if point is not None:
                pending.append({"call_index": call, "candidate_sha256": files["candidate.json"]["sha256"],
                                "stage": "native_UNKNOWN_saved_only"})
        if child is not None:
            expected = {"call_index": call, "record_sha256": step_sha, "status": step["status"],
                        "appended_pool_ids": step["appended_pool_ids"]}
            assert child["iterations"][call] == expected
        entry["terminal_step_status"] = step["status"]
    if child is not None:
        assert len(child["iterations"]) == child["production_solve_calls"]
        assert child["maximum_cumulative_native_solve_seconds"] == query.NATIVE_SECONDS
        assert child["native_solve_wall_seconds"] == result["native_solve_wall_seconds"] == native_used
        assert child["native_budget_overrun_seconds"] == result["native_budget_overrun_seconds"] == max(0.0, native_used - query.NATIVE_SECONDS)
        assert added == child["added_pool_ids"] == result["final_added_pool_ids"]
    assert bool(provisional_calls) == result.get("full_target_candidate_provisional", False)
    assert not result["count_feasibility_claimed"]
    report.update(status="PASS: exact chronological lightweight terminal replay",
                  terminal_status=result["status"], terminal_status_unchanged=True,
                  result_sha256=result_sha, supervisor_sha256=supervisor_sha,
                  call_records=records, provisional_full_target_calls=provisional_calls,
                  pending_saved_candidates_not_promoted=pending,
                  final_replayed_added_pool_ids=added,
                  count_feasibility_claimed=result["count_feasibility_claimed"],
                  no_numerical_infeasibility_promoted=True,
                  original_parent_acceptance_performed=False,
                  completed_record_native_solve_wall_seconds=native_used,
                  maximum_cumulative_native_solve_seconds=query.NATIVE_SECONDS,
                  native_budget_chronology_checked=True,
                  independent_literal_decoder_performed=False,
                  restored_parent_receipt_required_before_count_claim=True,
                  seconds=time.monotonic() - started)
    return report

def owned(preparation_path, directory, run_directory=None):
    started = time.monotonic(); deadline = started + 60
    assert query.file_sha(Path(query.__file__)) == QUERY_SHA
    _, preparation_sha = query.owner_preparation_binding(preparation_path)
    supervisor = query.load_source("supervisor")
    directory.mkdir(parents=True, exist_ok=False)
    query.save(directory / "owner-result.json", {"status": "UNKNOWN_BEFORE_CHILD", "optimizer_calls": 0})
    command = [sys.executable, str(Path(__file__).resolve()), "_worker", "--preparation", str(preparation_path.resolve()),
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    if run_directory is not None:
        command.extend(("--run-directory", str(run_directory.resolve())))
    supervision = supervisor.supervise(command, directory, deadline)
    result = {"status": supervision["status"], "supervision": supervision,
              "source_sha256": query.file_sha(Path(__file__)), "query_source_sha256": QUERY_SHA,
              "preparation_sha256": preparation_sha, "maximum_owned_seconds": 60,
              "report_accepted": False, "optimizer_calls": 0, "CpSolver_constructed": False,
              "count_feasibility_claimed": False}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        report = json.loads((directory / "report.json").read_bytes())
        assert report["status"].startswith("PASS") and not report["count_feasibility_claimed"]
        result.update(status=report["status"], report_accepted=True,
                      report_sha256=query.file_sha(directory / "report.json"))
    result.update(owner_seconds=time.monotonic() - started,
                  deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    query.save(directory / "owner-result.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("replay", "_worker"))
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode == "replay":
        owned(args.preparation, args.directory, args.run_directory)
    else:
        assert args.deadline is not None
        runtime = query.load_source("runtime")
        started, stages = time.monotonic(), []
        def stage(name, **extra):
            stages.append({"stage": name, "elapsed_seconds": time.monotonic() - started,
                           "memory": runtime.memory_snapshot(), **extra})
            query.save(args.directory / "stages.json", {"stages": stages})
            if time.monotonic() > args.deadline:
                raise TimeoutError("owned lightweight replay deadline")
        stage("child_started_before_archive_or_native_import")
        result = replay(args.preparation, args.run_directory, stage)
        result.update(terminal_memory=runtime.memory_snapshot(),
                      stages_sha256=query.file_sha(args.directory / "stages.json"))
        query.save(args.directory / "report.json", result)
