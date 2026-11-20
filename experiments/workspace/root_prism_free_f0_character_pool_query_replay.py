"""Cold full-target/prefix/candidate replay for the external-row query.

This module never constructs a solver. It preserves the owner's terminal
status, including late or incomplete child outputs. The exact original-parent
acceptance gate is repeated only for a timely accepted count witness.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

from google.protobuf import text_format
from ortools.sat import cp_model_pb2, sat_parameters_pb2

import root_prism_free_f0_character_pool_query as query

QUERY_SHA = "820f76ea30bff76e3c0d5d9b79601f6fba1ee11c0534676843315f575bafce39"
ROOT = Path(__file__).resolve().parents[2]
COMPLETED_STATES = {
    "EXACT_COUNT_WITNESS", "EXACT_REJECTED_CANDIDATE_CERTIFIED_ROWS_APPENDED",
    "UNKNOWN_CALL_LIMIT_REJECTED_CANDIDATE", "UNKNOWN_TOTAL_LIMIT_REJECTED_CANDIDATE",
    "UNPROVED_NATIVE_INFEASIBLE", "ERROR_NATIVE_MODEL_INVALID", "UNKNOWN_NATIVE_LIMIT",
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


def replay(preparation_path, run_directory=None):
    started = time.monotonic()
    assert sha(Path(query.__file__).read_bytes()) == QUERY_SHA
    prepared, preparation_sha = query.check_preparation(preparation_path)
    source, data, plan, target = query.load_target(prepared)
    report = {"status": "PASS: exact external-row query cold preflight",
              "source_sha256": sha(Path(__file__).read_bytes()), "query_source_sha256": QUERY_SHA,
              "preparation_sha256": preparation_sha, "target_proto_sha256": query.TARGET_SHA,
              "initial_proto_sha256": query.INITIAL_SHA,
              "all18444_domains_and_full34398_target_constraints_checked": True,
              "initial34281_constraints_are_exact_full_target_subset": True,
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
    assert result["maximum_owned_child_seconds"] == 180 and not result["automatic_retry"]
    assert not result["literal_incidence_or_graph_claimed"] and not result["F0_excluded"]
    assert result["count_feasibility_claimed"] == (result["status"] == "EXACT_COUNT_WITNESS")
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
    records, exact_candidate_calls, pending = [], [], []
    prefix_complete = True
    for call, directory in enumerate(directories):
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
        assert parameters.cp_model_probing_level == 0 and parameters.log_search_progress and parameters.log_to_stdout
        assert 0 < parameters.max_time_in_seconds <= 180
        assert parameters.max_time_in_seconds == step["native_max_time_seconds"]
        response, point = None, None
        if "candidate.json" in files:
            point, point_sha = read_record(directory / "candidate.json", step.get("candidate_sha256"))
            assert all(type(v) is int for v in point)
            if "candidate_values" in step:
                assert len(point) == step["candidate_values"]
            entry["saved_integer_candidate_values"] = len(point)
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
        if response.status in (cp_model_pb2.FEASIBLE, cp_model_pb2.OPTIMAL):
            assert point is not None and len(point) == 18444
            assert source.parent.evaluate_proto(proto, point)
            violations = source.pool_scan(point, target, plan)
            scan, scan_sha = read_record(directory / "pool-scan.json", step["pool_scan_sha256"])
            expected_scan = {"status": "PASS: exact active-prefix and all117 external-row evaluation",
                             "candidate_sha256": files["candidate.json"]["sha256"], "prefix_sha256": prefix_sha,
                             "active_constraints_checked": len(row_ids), "external_rows_checked": 117,
                             "violations": violations, "all_arithmetic_Python_integers": True}
            assert scan == expected_scan and step["violated_external_rows"] == len(violations)
            entry["all117_external_rows_exactly_replayed"] = True
            if not violations:
                assert step["status"] == "EXACT_COUNT_WITNESS" and not step["appended_pool_ids"]
                assert call == len(directories) - 1
                if child is not None and result["status"] == "EXACT_COUNT_WITNESS":
                    assert child["accepted_call_index"] == call
                    exact = source.inspect(point, data, plan, target)
                    stored, _ = read_record(directory / "exact-point-check.json", step["exact_point_check_sha256"])
                    assert stored == exact
                    entry["full_target_and_original_parent_integer_check"] = exact
                    exact_candidate_calls.append(call)
                else:
                    pending.append({"call_index": call, "candidate_sha256": files["candidate.json"]["sha256"],
                                    "stage": "late_or_failed_owner; no original-parent acceptance promoted"})
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
                    assert step["status"] in ("UNKNOWN_CALL_LIMIT_REJECTED_CANDIDATE", "UNKNOWN_TOTAL_LIMIT_REJECTED_CANDIDATE")
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
        assert added == child["added_pool_ids"] == result["final_added_pool_ids"]
    assert bool(exact_candidate_calls) == result["count_feasibility_claimed"]
    report.update(status="PASS: exact chronological external-row terminal replay",
                  terminal_status=result["status"], terminal_status_unchanged=True,
                  result_sha256=result_sha, supervisor_sha256=supervisor_sha,
                  call_records=records, exact_accepted_count_calls=exact_candidate_calls,
                  pending_saved_candidates_not_promoted=pending,
                  final_replayed_added_pool_ids=added,
                  count_feasibility_claimed=result["count_feasibility_claimed"],
                  no_numerical_infeasibility_promoted=True,
                  seconds=time.monotonic() - started)
    return report


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preparation", type=Path, required=True)
    parser.add_argument("--run-directory", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.preparation, args.run_directory)
    with args.output.open("xb") as stream:
        stream.write(query.canonical(result) + b"\n")
    print(json.dumps(result, indent=2), flush=True)
