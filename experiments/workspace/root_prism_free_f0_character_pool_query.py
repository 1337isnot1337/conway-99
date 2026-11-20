"""Owned exact dense-row generation for the frozen F0 count target.

At most12 CP-SAT calls share one180-second owner deadline, including child
imports, construction, serialization and exact arithmetic. A call after the
first requires a strictly larger prefix of certified target rows. Every
returned integer vector is saved before its acceptance checks. Infeasible
native status remains unproved; no graph or literal incidence is certified.
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
LOGS = ROOT / "experiments/logs/root-prism-free"
SOURCES = {
    "model": ("root_prism_free_f0_character_pool_model.py", "b3029a3a197ec31305f74dead2b28f51beaf219cb2e9e289dc8f250db42a6943"),
    "supervisor": ("root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"),
}
INPUTS = {
    "model_preparation": ("f0-character-pool-model01/report.json", "ed912b419cdfe1a4b4b228382ec1cfbb58a7688476c06ea14e851a3290992f30"),
    "model_cold": ("f0-character-pool-model01-cold.json", "24a450d6d6c3bf537e6c049aaad2bf843e154a0586e463a2fc14eaff48eac2c8"),
    "model_root_review": ("f0-character-pool-model-root-source-review.json", "009257a87f45c480e741961d3329174b33c263849911d3da185ff36669470bbf"),
    "plan": ("f0-character-pool-model01/plan.json.gz", "b3179e520d5913530c7d3cfae27529b5717be26c763de024b725c38959aa2aef"),
    "target_archive": ("f0-character-pool-model01/target.pb.gz", "1a26b2ec303121e44d0100a586c568ba85387137341ccd503471a6994cba1a2f"),
    "initial_archive": ("f0-character-pool-model01/initial.pb.gz", "5710bf3f31c076d8afa4cfc6f2207123d25d53d19dcc284607102de1a3f22dac"),
    "prior_supervisor_controls": ("f0-character-query-preparation01/preparation.json", "c480e2df6dbec03d95d3c8c1f387933b28c7e212c9e86a33d0b7f349451d4384"),
}
TARGET_SHA = "0612fd82507ac454209ba5f376654248461fc8c0506b9a4a382f5e628487d9ae"
INITIAL_SHA = "36bd4fe3650ede346bab0885abcb9cef7a96cb0e150dffc8fcf51bbe695e7d4d"
CP_MODEL_SHA = "b5f2a3ae5c418d11af23cb77a766fa10103c8bb71703dafa1ecad74823603f25"
SECONDS, MAX_CALLS, MAX_APPEND, FINALIZATION_RESERVE = 180, 12, 16, 8


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def load_source(key):
    filename, expected = SOURCES[key]
    path = ROOT / "experiments/workspace" / filename
    assert sha(path.read_bytes()) == expected
    spec = importlib.util.spec_from_file_location("frozen_character_pool_" + key, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configuration():
    sources, inputs, records = {}, {}, {}
    for key, (filename, expected) in SOURCES.items():
        path = ROOT / "experiments/workspace" / filename
        assert sha(path.read_bytes()) == expected
        sources[key] = {"path": str(path.relative_to(ROOT)), "sha256": expected}
    for key, (filename, expected) in INPUTS.items():
        path = LOGS / filename
        raw = path.read_bytes()
        assert sha(raw) == expected
        inputs[key] = {"path": str(path.relative_to(ROOT)), "sha256": expected}
        if not filename.endswith(".gz"):
            records[key] = json.loads(raw)
            assert records[key]["status"].startswith("PASS")
    model = records["model_preparation"]
    assert model["source_sha256"] == SOURCES["model"][1]
    assert model["plan"]["sha256"] == INPUTS["plan"][1]
    assert model["models"]["target"]["raw_proto_sha256"] == TARGET_SHA
    assert model["models"]["initial"]["raw_proto_sha256"] == INITIAL_SHA
    assert records["model_cold"]["preparation_sha256"] == INPUTS["model_preparation"][1]
    old_controls = records["prior_supervisor_controls"]
    assert old_controls["definition"]["sources"]["supervisor"]["sha256"] == SOURCES["supervisor"][1]
    assert old_controls["controls"]["status"] == "PASS"
    assert [c["status"] for c in old_controls["controls"]["owned_child_stop_controls"]] == [
        "CHILD_EXITED", "ERROR_CHILD_EXIT", "UNKNOWN_HARD_DEADLINE"]
    return {"schema": "conway99.f0-character-external-row-query.v1",
            "runner_source_sha256": sha(Path(__file__).read_bytes()), "sources": sources, "inputs": inputs,
            "target_proto_sha256": TARGET_SHA, "initial_proto_sha256": INITIAL_SHA,
            "variables": 18444, "target_constraints": 34398, "initial_constraints": 34281,
            "external_rows": 117, "maximum_owned_child_seconds": SECONDS,
            "maximum_production_solve_calls": MAX_CALLS, "maximum_rows_appended_per_candidate": MAX_APPEND,
            "finalization_reserve_seconds": FINALIZATION_RESERVE,
            "num_search_workers": 1, "random_seed": 0, "cp_model_probing_level": 0,
            "probing_change_separate_from_mathematical_target": True,
            "row_selection": "First at most16 violated external rows in the frozen pool-ID order.",
            "second_or_later_call_requires_a_strictly_larger_exact_target_prefix": True,
            "all_imports_construction_serialization_search_and_acceptance_within_owner_deadline": True,
            "all_returned_integer_values_saved_before_exact_checks": True,
            "no_visitation_clauses_or_unproved_candidate_restrictions": True,
            "no_hint_objective_or_fixed_candidate": True,
            "full_target_and_restored_original_parent_required_for_acceptance": True,
            "native_infeasibility_unproved_without_independent_certificate": True,
            "late_or_failed_child_never_accepted": True,
            "pending_saved_candidate_may_be_checked_by_a_separate_arithmetic_task": True,
            "exact_witness_scope": "Necessary integer count, product and table system; no literal incidence or graph.",
            "ortools_version": "9.15.6755", "installed_cp_model_source_sha256": CP_MODEL_SHA,
            "automatic_retry": False, "warm_start_or_speedup_claimed": False}


def check_preparation(path):
    raw = path.read_bytes()
    prepared = json.loads(raw)
    assert prepared["status"] == "PASS: external-row query preparation; no production solve"
    assert prepared["definition"] == configuration()
    assert prepared["controls"]["status"] == "PASS"
    assert prepared["optimizer_calls"] == prepared["CpSolver_constructed"] == 0
    return prepared, sha(raw)


def load_target(prepared):
    from ortools.sat import cp_model_pb2
    source = load_source("model")
    data = source.load_inputs()
    plan, target = source.derive(data)
    raw = (ROOT / prepared["definition"]["inputs"]["plan"]["path"]).read_bytes()
    assert sha(raw) == INPUTS["plan"][1] and json.loads(gzip.decompress(raw)) == plan
    for name, expected, row_ids in (("target", TARGET_SHA, list(range(34398))),
                                     ("initial", INITIAL_SHA, plan["initial_to_target_rows"])):
        path = ROOT / prepared["definition"]["inputs"][name + "_archive"]["path"]
        archive = path.read_bytes()
        assert sha(archive) == INPUTS[name + "_archive"][1]
        raw = gzip.decompress(archive)
        assert sha(raw) == expected
        proto = cp_model_pb2.CpModelProto()
        proto.ParseFromString(raw)
        source.exact_proto_check(proto, target, row_ids)
    return source, data, plan, target


def native_parameters(cmh, seconds):
    assert 0 < seconds <= SECONDS
    params = cmh.SatParameters()
    params.num_search_workers = 1
    params.random_seed = 0
    params.cp_model_probing_level = 0
    params.max_time_in_seconds = seconds
    params.log_search_progress = True
    params.log_to_stdout = True
    return params


def choose_rows(violations, added):
    ids = [record["pool_id"] for record in violations]
    assert ids == sorted(set(ids)) and all(0 <= i < 117 for i in ids)
    assert not set(ids).intersection(added)
    assert all(type(r["gap"]) is int and r["gap"] > 0 for r in violations)
    return ids[:MAX_APPEND]


def controls():
    from google.protobuf import text_format
    from ortools.sat import cp_model_pb2, sat_parameters_pb2
    from ortools.sat.python import cp_model
    import ortools
    assert ortools.__version__ == "9.15.6755" and sha(Path(cp_model.__file__).read_bytes()) == CP_MODEL_SHA
    native = native_parameters(cp_model.cmh, 17.25)
    params = sat_parameters_pb2.SatParameters()
    text_format.Parse(str(native), params)
    assert params.num_search_workers == 1 and params.random_seed == 0 and params.cp_model_probing_level == 0
    assert params.max_time_in_seconds == 17.25 and params.log_search_progress and params.log_to_stdout
    response = cp_model.cmh.CpSolverResponse()
    response.status = cp_model.FEASIBLE
    response.solution.extend([0, -6, 36, 144])
    copy = cp_model_pb2.CpSolverResponse()
    text_format.Parse(str(response), copy)
    assert list(copy.solution) == [0, -6, 36, 144]
    cases = 0
    for start in range(118):
        added = list(range(start))
        violations = [{"pool_id": i, "gap": (1 << 54) + i} for i in range(start, 117)]
        selected = choose_rows(violations, added)
        assert selected == list(range(start, min(117, start + MAX_APPEND)))
        assert len(selected) <= MAX_APPEND and not set(selected).intersection(added)
        assert not selected or set(added) < set(added + selected)
        cases += 1
    refused = False
    try:
        choose_rows([{"pool_id": 1, "gap": 1}], [1])
    except AssertionError:
        refused = True
    assert refused
    return {"status": "PASS", "exact_prefix_growth_cases": cases,
            "already_active_violated_row_refused": True, "large_integer_gaps_not_converted_to_float": True,
            "probing_zero_parameter_and_signed_response_roundtrips": True,
            "unchanged_owned_supervisor_controls_bound": INPUTS["prior_supervisor_controls"][1],
            "optimizer_calls": 0, "CpSolver_constructed": 0}


def worker(preparation_path, directory, deadline):
    started = time.monotonic()
    prepared, preparation_sha = check_preparation(preparation_path)
    result = {"status": "UNKNOWN_BEFORE_INITIALIZATION", "preparation_sha256": preparation_sha,
              "target_proto_sha256": TARGET_SHA, "initial_proto_sha256": INITIAL_SHA,
              "production_solve_calls": 0, "iterations": [], "added_pool_ids": [],
              "count_feasibility_claimed": False, "literal_incidence_or_graph_claimed": False,
              "F0_excluded": False, "automatic_retry": False}
    save(directory / "progress.json", result)
    try:
        source, data, plan, target = load_target(prepared)
        row_ids = list(plan["initial_to_target_rows"])
        model = source.build_native(target, row_ids)
        variables = [model.get_int_var_from_proto_index(i) for i in range(18444)]
        from google.protobuf import text_format
        from ortools.sat import cp_model_pb2
        from ortools.sat.python import cp_model
        import ortools
        assert ortools.__version__ == "9.15.6755" and sha(Path(cp_model.__file__).read_bytes()) == CP_MODEL_SHA
        added = []
        result["construction_seconds"] = time.monotonic() - started
        solver = cp_model.CpSolver()
        for call in range(MAX_CALLS):
            if deadline - time.monotonic() <= FINALIZATION_RESERVE:
                result["status"] = "UNKNOWN_TOTAL_LIMIT_BEFORE_NEXT_CALL"
                break
            step_directory = directory / f"call{call:03d}"
            step_directory.mkdir()
            native_path = step_directory / "model.pb"
            assert model.export_to_file(str(native_path))
            native_raw = native_path.read_bytes()
            native_proto = cp_model_pb2.CpModelProto()
            native_proto.ParseFromString(native_raw)
            native_checked = source.exact_proto_check(native_proto, target, row_ids)
            if call == 0:
                assert sha(native_raw) == INITIAL_SHA and not added
            else:
                assert result["iterations"][-1]["appended_pool_ids"]
            prefix = {"call_index": call, "added_pool_ids": list(added),
                      "active_target_row_ids_sha256": sha(canonical(row_ids)),
                      "actual_model_sha256": sha(native_raw), "actual_model_bytes": len(native_raw),
                      "native_exact_checks": native_checked}
            save(step_directory / "prefix.json", prefix)
            remaining = deadline - time.monotonic() - FINALIZATION_RESERVE
            if remaining <= 0:
                result["status"] = "UNKNOWN_TOTAL_LIMIT_AFTER_PREFIX_SERIALIZATION"
                break
            params = native_parameters(cp_model.cmh, min(SECONDS, remaining))
            solver.parameters = params
            (step_directory / "parameters.pbtxt").write_text(str(params))
            step = {"call_index": call, "status": "NATIVE_CALL_ACTIVE",
                    "prefix_sha256": sha((step_directory / "prefix.json").read_bytes()),
                    "parameters_sha256": sha((step_directory / "parameters.pbtxt").read_bytes()),
                    "native_max_time_seconds": min(SECONDS, remaining), "appended_pool_ids": []}
            save(step_directory / "record.json", step)
            result.update(status="UNKNOWN_NATIVE_CALL_ACTIVE", production_solve_calls=call + 1)
            save(directory / "progress.json", result)
            call_started = time.monotonic()
            status = solver.solve(model)
            step["solve_wall_seconds"] = time.monotonic() - call_started
            native_response = solver.response_proto
            # The candidate is durable before parsing response text or any scan.
            point = list(native_response.solution)
            if point:
                assert all(type(v) is int for v in point)
                save(step_directory / "candidate.json", point)
                step.update(candidate_sha256=sha((step_directory / "candidate.json").read_bytes()),
                            candidate_values=len(point), status="RETURNED_INTEGER_CANDIDATE_UNCHECKED")
                save(step_directory / "record.json", step)
            response_text = str(native_response)
            (step_directory / "response.pbtxt").write_text(response_text)
            response = cp_model_pb2.CpSolverResponse()
            text_format.Parse(response_text, response)
            assert point == list(response.solution)
            assert cp_model_pb2.CpSolverStatus.Name(response.status) == status.name
            step.update(native_status=status.name, native_status_code=int(response.status),
                        response_sha256=sha((step_directory / "response.pbtxt").read_bytes()),
                        native_wall_seconds=response.wall_time, native_conflicts=response.num_conflicts,
                        native_branches=response.num_branches, native_booleans=response.num_booleans,
                        native_integer_propagations=response.num_integer_propagations)
            save(step_directory / "record.json", step)
            if status.name in ("FEASIBLE", "OPTIMAL"):
                assert len(point) == 18444
                assert source.parent.evaluate_proto(native_proto, point)
                violations = source.pool_scan(point, target, plan)
                scan = {"status": "PASS: exact active-prefix and all117 external-row evaluation",
                        "candidate_sha256": step["candidate_sha256"], "prefix_sha256": step["prefix_sha256"],
                        "active_constraints_checked": len(row_ids), "external_rows_checked": 117,
                        "violations": violations, "all_arithmetic_Python_integers": True}
                save(step_directory / "pool-scan.json", scan)
                step.update(pool_scan_sha256=sha((step_directory / "pool-scan.json").read_bytes()),
                            violated_external_rows=len(violations))
                if not violations:
                    step["status"] = "FULL_NATIVE_TARGET_PASSED_PARENT_CHECK_PENDING"
                    save(step_directory / "record.json", step)
                    exact = source.inspect(point, data, plan, target)
                    save(step_directory / "exact-point-check.json", exact)
                    step.update(status="EXACT_COUNT_WITNESS",
                                exact_point_check_sha256=sha((step_directory / "exact-point-check.json").read_bytes()))
                    result.update(status="EXACT_COUNT_WITNESS", count_feasibility_claimed=True,
                                  accepted_call_index=call)
                else:
                    selected = choose_rows(violations, added)
                    assert selected
                    step["selected_pool_ids"] = selected
                    if call + 1 == MAX_CALLS:
                        step["status"] = result["status"] = "UNKNOWN_CALL_LIMIT_REJECTED_CANDIDATE"
                    elif deadline - time.monotonic() <= FINALIZATION_RESERVE:
                        step["status"] = result["status"] = "UNKNOWN_TOTAL_LIMIT_REJECTED_CANDIDATE"
                    else:
                        step["status"] = "EXACT_REJECTED_CANDIDATE_APPEND_PENDING"
                        save(step_directory / "record.json", step)
                        for pool_id in selected:
                            target_id = plan["external_pool"][pool_id]["target_constraint"]
                            assert target_id not in row_ids
                            source.append_constraint(model, variables, target.constraints[target_id])
                            row_ids.append(target_id)
                            added.append(pool_id)
                        assert len(model.proto.constraints) == 34281 + len(added)
                        assert model.validate() == ""
                        step.update(status="EXACT_REJECTED_CANDIDATE_CERTIFIED_ROWS_APPENDED",
                                    appended_pool_ids=selected,
                                    next_active_target_row_ids_sha256=sha(canonical(row_ids)))
                        result.update(status="UNKNOWN_NEXT_STRICT_PREFIX_PENDING", added_pool_ids=list(added))
            elif status.name == "INFEASIBLE":
                assert not point
                step["status"] = result["status"] = "UNPROVED_NATIVE_INFEASIBLE"
            elif status.name == "MODEL_INVALID":
                step["status"] = result["status"] = "ERROR_NATIVE_MODEL_INVALID"
            else:
                assert status.name == "UNKNOWN"
                step["status"] = result["status"] = "UNKNOWN_NATIVE_LIMIT"
            save(step_directory / "record.json", step)
            result["iterations"].append({"call_index": call,
                                         "record_sha256": sha((step_directory / "record.json").read_bytes()),
                                         "status": step["status"], "appended_pool_ids": step["appended_pool_ids"]})
            save(directory / "progress.json", result)
            if step["status"] != "EXACT_REJECTED_CANDIDATE_CERTIFIED_ROWS_APPENDED":
                break
        if time.monotonic() > deadline:
            result.update(status="UNKNOWN_LATE_CHILD", count_feasibility_claimed=False)
    except Exception as error:
        result.update(status="ERROR_NO_ACCEPTED_OUTCOME", count_feasibility_claimed=False,
                      error_type=type(error).__name__, message=str(error))
        raise
    finally:
        result["child_seconds"] = time.monotonic() - started
        save(directory / "child-result.json", result)


def run(preparation_path, directory):
    started = time.monotonic()
    deadline = started + SECONDS
    _, preparation_sha = check_preparation(preparation_path)
    supervisor = load_source("supervisor")
    directory.mkdir(parents=True, exist_ok=False)
    result = {"status": "UNKNOWN_BEFORE_CHILD", "preparation_sha256": preparation_sha,
              "target_proto_sha256": TARGET_SHA, "initial_proto_sha256": INITIAL_SHA,
              "runner_source_sha256": sha(Path(__file__).read_bytes()),
              "maximum_owned_child_seconds": SECONDS, "count_feasibility_claimed": False,
              "literal_incidence_or_graph_claimed": False, "F0_excluded": False, "automatic_retry": False}
    save(directory / "result.json", result)
    command = [sys.executable, str(Path(__file__).resolve()), "_worker", "--preparation", str(preparation_path.resolve()),
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    supervision = supervisor.supervise(command, directory, deadline)
    result["supervision"] = supervision
    if supervision["status"] == "CHILD_EXITED":
        raw = (directory / "child-result.json").read_bytes()
        child = json.loads(raw)
        assert child["preparation_sha256"] == preparation_sha
        assert child["target_proto_sha256"] == TARGET_SHA and child["initial_proto_sha256"] == INITIAL_SHA
        assert 0 <= child["production_solve_calls"] <= MAX_CALLS
        assert not child["F0_excluded"] and not child["literal_incidence_or_graph_claimed"]
        accepted = child["status"] == "EXACT_COUNT_WITNESS"
        assert child["count_feasibility_claimed"] == accepted
        result.update(status=child["status"], child_result_sha256=sha(raw),
                      production_solve_calls=child["production_solve_calls"], count_feasibility_claimed=accepted,
                      final_added_pool_ids=child["added_pool_ids"])
    else:
        result["status"] = supervision["status"]
    result["owner_seconds"] = time.monotonic() - started
    result["deadline_overrun_seconds"] = max(0, time.monotonic() - deadline)
    save(directory / "result.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "_worker"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode == "prepare":
        args.directory.mkdir(parents=True, exist_ok=False)
        report = {"status": "PASS: external-row query preparation; no production solve",
                  "definition": configuration(), "controls": controls(),
                  "optimizer_calls": 0, "CpSolver_constructed": 0}
        save(args.directory / "preparation.json", report)
        print(json.dumps(report, indent=2), flush=True)
    elif args.mode == "run":
        assert args.preparation is not None
        run(args.preparation, args.directory)
    else:
        assert args.preparation is not None and args.deadline is not None
        worker(args.preparation, args.directory, args.deadline)
