"""One bounded direct540 search and separately owned exact cold replay.

The accepted cold model record is the artifact authority. The original
preparation owner timeout is preserved. There is no external pool, objective,
hint, visit block, count variable or automatic same-model retry.
"""
import argparse
import ast
import gzip
import hashlib
import importlib.util
import json
from math import isfinite
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
SECONDS, NATIVE_SECONDS, FINALIZATION_RESERVE = 300, 180, 8
PREPARATION_SECONDS, COLD_SECONDS = 60, 60
CP_MODEL_SHA = "b5f2a3ae5c418d11af23cb77a766fa10103c8bb71703dafa1ecad74823603f25"
SOURCES = {
    "builder": ("root_prism_free_f0_direct_literal_model.py", "b500336db29820777afb59076384a48382fa54453fce5b232a072719893cea40"),
    "old_query": ("root_prism_free_f0_full_fourier_query.py", "a8eff9c09fdd2a31482d23e3c83b11424fab32462e9b1431c3d899b6b8034955"),
    "supervisor": ("root_prism_free_f0_local_neighbors_batch.py", "b8e5323f92fa105ff2c0ed5b1667ac25d7c92f85f8cac45b170ddc56208f8278"),
}
INPUTS = {
    "raw_preparation": ("f0-direct-literal-model01/report.json", "36521e821a363281d2792f115dce6577fb4f27dd40309a08f27160a527f73a62"),
    "old_owner": ("f0-direct-literal-model01/owner-result.json", "c5a7826dcd4260830730801ea9457dca2766c5cc1a643adf7a06951e4532b156"),
    "cold": ("f0-direct-literal-model01-cold/report.json", "2c67cbf7eaae08cad0bfd6d47c32de0606b91486a2731f452806de0c3add8254"),
    "cold_owner": ("f0-direct-literal-model01-cold/owner-result.json", "2da83ed1808634d2bf02e7ef44465ad38c4f198fde9202d719d4b2596c22e863"),
    "model_gate": ("f0-direct-literal-model-root-gate01.json", "03eb052cc54eb49269c9b8682bbe17887e36f9290a383173cc865e08958b973a"),
    "plan": ("f0-direct-literal-model01/plan.json.gz", "bd921d7d8f16c64bd866e0ec319b1cc3db37450cf5a6c884a37a9f40044c48d7"),
    "model": ("f0-direct-literal-model01/model.pb.gz", "34724b46df693d930de465d2d3b7473ae8742a322aa7006e21e0aa780f1c1bd6"),
    "cuts": ("f0-literal-cut-export-ci01/literal-rows.json.gz", "051282b7c8256fa3cad6edd9e9490290cfdfa5f6bef46b609bc32bdd63189b63"),
}
RAW_HASHES = {
    "plan": "4d8ab190ce417a29ef9eb9a0fefcc03f5f608855e38826188d64aaf0e80c82a8",
    "model": "de9e9f0f9deb2e7dc1c41866c959c5264de2b7fef7d11d3c9c0d8772aa0bbe3e",
    "cuts": "3877ba7ec41c4f85f2d1623cfc5d20fa0d258c8c8319fa5dcd7313f580ac305e",
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def memory():
    result = {"peak_rss_KiB": int(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)}
    path = Path("/proc/self/status")
    if path.exists():
        for line in path.read_text().splitlines():
            if line.startswith("VmRSS:"):
                result["current_rss_KiB"] = int(line.split()[1])
    return result


def source_module(key):
    name, expected = SOURCES[key]
    path = ROOT / "experiments/workspace" / name
    assert file_sha(path) == expected
    spec = importlib.util.spec_from_file_location("direct540_" + key, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def read(key, binary=False):
    name, expected = INPUTS[key]
    payload = (LOGS / name).read_bytes()
    assert sha(payload) == expected, key
    raw = gzip.decompress(payload) if name.endswith(".gz") else payload
    if key in RAW_HASHES:
        assert sha(raw) == RAW_HASHES[key], key
    return raw if binary else json.loads(raw)


def definition():
    for name, expected in SOURCES.values():
        assert file_sha(ROOT / "experiments/workspace" / name) == expected
    return {
        "schema": "conway99.f0.direct540-one-call-query.v1",
        "source_sha256": file_sha(Path(__file__)),
        "sources": {k: {"path": "experiments/workspace/" + p, "sha256": h} for k, (p, h) in SOURCES.items()},
        "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k, (p, h) in INPUTS.items()},
        "raw_hashes": RAW_HASHES, "variables": 540, "linear_rows": 4681, "linear_terms": 454152,
        "maximum_owner_seconds": SECONDS, "maximum_native_solve_seconds": NATIVE_SECONDS,
        "maximum_native_solve_calls": 1, "finalization_reserve_seconds": FINALIZATION_RESERVE,
        "maximum_preparation_owner_seconds": PREPARATION_SECONDS, "maximum_cold_owner_seconds": COLD_SECONDS,
        "num_search_workers": 1, "random_seed": 0, "cp_model_probing_level": 0, "linearization_level": 0,
        "external_pool": 0, "objective_hint_assumptions_or_selector_fixing": False,
        "native_model_source": SOURCES["builder"][1], "native_model_raw_sha256": RAW_HASHES["model"],
        "accepted_model_cold_is_artifact_validation_authority": True,
        "original_preparation_owner_UNKNOWN_remains_unchanged": True,
        "save_full540_vector_before_any_expensive_check": True,
        "accepted_candidate_requires_direct172_equations90_motifs4416_exact_cuts": True,
        "native_infeasibility_status_is_unproved": True,
        "exterior_graph_or_matching_claimed": False, "automatic_retry": False,
    }


def native_parameters(cmh, seconds):
    assert 0 < seconds <= NATIVE_SECONDS
    params = cmh.SatParameters()
    params.num_search_workers = 1
    params.random_seed = 0
    params.cp_model_probing_level = 0
    params.linearization_level = 0
    params.max_time_in_seconds = seconds
    params.log_search_progress = True
    params.log_to_stdout = True
    return params


def native_time_budget(deadline, now, used):
    assert all(isfinite(v) for v in (deadline, now, used)) and used >= 0
    return max(0.0, min(NATIVE_SECONDS - used, deadline - now - FINALIZATION_RESERVE))


def native_parameter_controls():
    """Check installed native fields and text/wire serialization, without a solver."""
    from google.protobuf import text_format
    from ortools.sat import sat_parameters_pb2
    from ortools.sat.python import cp_model
    import ortools
    assert ortools.__version__ == "9.15.6755"
    assert file_sha(Path(cp_model.__file__)) == CP_MODEL_SHA
    field = sat_parameters_pb2.SatParameters.DESCRIPTOR.fields_by_name["linearization_level"]
    checks = []
    for seconds in (0.25, 10.0, 172.0):
        native = native_parameters(cp_model.cmh, seconds)
        assert native.linearization_level == 0
        text = str(native)
        parsed = sat_parameters_pb2.SatParameters()
        text_format.Parse(text, parsed)
        expected = {"num_search_workers": 1, "random_seed": 0,
                    "cp_model_probing_level": 0, "linearization_level": 0,
                    "max_time_in_seconds": seconds, "log_search_progress": True,
                    "log_to_stdout": True}
        assert {f.name: value for f, value in parsed.ListFields()} == expected
        assert parsed.HasField("linearization_level") and parsed.linearization_level == 0
        wire = parsed.SerializeToString(deterministic=True)
        restored = sat_parameters_pb2.SatParameters()
        restored.ParseFromString(wire)
        assert restored == parsed
        checks.append({"seconds": seconds, "exact_explicit_fields": expected,
                       "text_sha256": sha(text.encode()), "wire_sha256": sha(wire)})
    return {"status": "PASS", "installed_version": ortools.__version__,
            "field_number": field.number, "field_type": field.type,
            "installed_default_linearization_level": field.default_value,
            "roundtrips": checks, "CpSolver_constructed": False,
            "model_constructed": False, "optimizer_calls": 0}


def source_controls():
    def functions(path):
        tree = ast.parse(path.read_text())
        return {n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, ast.FunctionDef)}
    old = functions(ROOT / "experiments/workspace" / SOURCES["old_query"][0])
    new = functions(Path(__file__))
    names = ["native_parameters", "native_time_budget", "native_parameter_controls"]
    assert all(old[name] == new[name] for name in names)
    cases = [(1000, 0, 0, 180), (1000, 900, 0, 92), (1000, 993, 0, 0),
             (1000, 900, 179, 1), (1000, 900, 181, 0)]
    for deadline, now, used, expected in cases:
        assert native_time_budget(deadline, now, used) == expected
    for used in (-1.0, float("inf"), float("nan")):
        try:
            native_time_budget(1000, 900, used)
        except AssertionError:
            pass
        else:
            raise AssertionError("invalid native clock accepted")
    return {"status": "PASS", "AST_identical_reviewed_functions": names,
            "function_AST_sha256": {n: sha(new[n].encode()) for n in names},
            "native_budget_cases": len(cases), "invalid_clock_controls": 3,
            "solver_calls": 0}


def load_artifacts(stage):
    raw_preparation, old_owner, cold, cold_owner = [read(k) for k in ("raw_preparation", "old_owner", "cold", "cold_owner")]
    read("model_gate")
    assert old_owner["status"] == "UNKNOWN_HARD_DEADLINE" and not old_owner["report_accepted"]
    assert old_owner["supervision"]["child_reaped"]
    assert raw_preparation["status"].startswith("PASS") and raw_preparation["native_public_constructor_byte_identity"]
    assert cold["status"].startswith("PASS") and cold["preparation_sha256"] == INPUTS["raw_preparation"][1]
    assert cold["complete_plan_and_protobuf_byte_equality"]
    assert cold_owner["report_accepted"] and cold_owner["report_sha256"] == INPUTS["cold"][1]
    assert cold_owner["supervision"]["status"] == "CHILD_EXITED" and cold_owner["supervision"]["child_reaped"]
    assert cold_owner["deadline_overrun_seconds"] == 0
    plan, model_raw, cuts = read("plan"), read("model", binary=True), read("cuts")
    assert plan["definition"] == raw_preparation["definition"] == cold["definition"]
    assert plan["definition"]["source_sha256"] == SOURCES["builder"][1]
    assert plan["counts"] == raw_preparation["counts"] == cold["counts"]
    assert plan["counts"]["variables"] == 540 and plan["counts"]["linear_constraints"] == 4681
    assert plan["counts"]["linear_terms"] == 454152 and plan["counts"]["external_pool"] == 0
    assert len(cuts) == 4416 and sum(len(r["terms"]) for r in cuts) == 442308
    for key in ("plan", "model"):
        assert raw_preparation["outputs"][key]["sha256"] == INPUTS[key][1]
        assert raw_preparation["outputs"][key]["raw_sha256"] == RAW_HASHES[key]
    stage("frozen_artifacts_bound_to_accepted_exact_cold")
    return plan, model_raw, cuts


def import_native(stage):
    stage("before_native_import")
    import ortools
    from ortools.sat import cp_model_pb2
    from ortools.sat.python import cp_model
    assert ortools.__version__ == "9.15.6755"
    assert file_sha(Path(cp_model.__file__)) == CP_MODEL_SHA
    stage("native_import_complete")
    return cp_model, cp_model_pb2


def checked_proto(pb2, raw, plan):
    proto = pb2.CpModelProto()
    proto.ParseFromString(raw)
    assert {f.name for f, _ in proto.ListFields()} == {"variables", "constraints"}
    assert len(proto.variables) == 540 and len(proto.constraints) == 4681
    terms = 0
    for j, (v, old) in enumerate(zip(proto.variables, plan["variables"])):
        assert old["id"] == j and list(v.domain) == old["domain"]
        assert v.name == ("f0_literal_" if j < 480 else "f0_radix_") + str(j)
    for constraint, row in zip(proto.constraints, plan["linear_constraints"]):
        assert {f.name for f, _ in constraint.ListFields()} == {"linear"}
        assert list(constraint.linear.vars) == [j for j, c in row["terms"]]
        assert list(constraint.linear.coeffs) == [c for j, c in row["terms"]]
        assert list(constraint.linear.domain) == row["domain"]
        terms += len(row["terms"])
    assert terms == 454152 and sha(proto.SerializeToString()) == RAW_HASHES["model"]
    return proto


def construct_native(cp_model, proto, directory, stage):
    model = cp_model.CpModel()
    variables = [model.new_int_var_from_domain(cp_model.Domain.from_flat_intervals(list(v.domain)), v.name)
                 for v in proto.variables]
    assert [v.index for v in variables] == list(range(540))
    for constraint in proto.constraints:
        row = constraint.linear
        expr = cp_model.LinearExpr.weighted_sum([variables[j] for j in row.vars], list(row.coeffs))
        model.add_linear_expression_in_domain(expr, cp_model.Domain.from_flat_intervals(list(row.domain)))
    assert model.validate() == ""
    export = directory / "actual-model.pb"
    assert model.export_to_file(str(export)) and file_sha(export) == RAW_HASHES["model"]
    stage("public_native_constructor_validator_and_complete_byte_identity_passed")
    return model


def inspect(values, plan, cuts):
    builder = source_module("builder")
    result = builder.inspect(values, plan, cuts)
    assert result["status"].startswith("PASS")
    assert result["checked_original_equations"] == 172
    assert result["checked_motif_conflicts"] == 90 and result["checked_original_big_integer_cuts"] == 4416
    return result


def checked_preparation(directory):
    raw = (directory / "report.json").read_bytes()
    report = json.loads(raw)
    owner = json.loads((directory / "owner-result.json").read_bytes())
    assert owner["report_accepted"] and owner["report_sha256"] == sha(raw)
    assert owner["supervision"]["status"] == "CHILD_EXITED" and owner["supervision"]["child_reaped"]
    assert owner["deadline_overrun_seconds"] == 0
    assert report["status"] == "PASS: direct540 query preparation and optimizer-free native preflight"
    assert report["definition"] == definition()
    assert report["source_controls"] == source_controls()
    assert report["actual_model_raw_sha256"] == RAW_HASHES["model"]
    return report, sha(raw)


def prepare(directory, deadline, stage):
    plan, raw, cuts = load_artifacts(stage)
    cp_model, pb2 = import_native(stage)
    controls = {"source": source_controls(), "native": native_parameter_controls()}
    proto = checked_proto(pb2, raw, plan)
    construct_native(cp_model, proto, directory, stage)
    report = {"status": "PASS: direct540 query preparation and optimizer-free native preflight",
              "definition": definition(), "source_controls": controls["source"],
              "native_parameter_controls": controls["native"],
              "actual_model_raw_sha256": RAW_HASHES["model"],
              "complete_model_plan_comparison": True,
              "public_native_constructor_byte_identity": True,
              "optimizer_calls": 0, "CpSolver_constructed": False}
    return report


def run(directory, preparation, deadline, stage):
    _, preparation_sha = checked_preparation(preparation)
    result = {"status": "UNKNOWN_BEFORE_INITIALIZATION", "production_solve_calls": 0,
              "query_preparation_sha256": preparation_sha, "model_raw_sha256": RAW_HASHES["model"],
              "direct_literal_witness_accepted": False, "matching_or_exterior_checked": False,
              "graph_exists_claimed": False}
    save(directory / "result.json", result)
    plan, raw, cuts = load_artifacts(stage)
    cp_model, pb2 = import_native(stage)
    proto = checked_proto(pb2, raw, plan)
    model = construct_native(cp_model, proto, directory, stage)
    remaining = native_time_budget(deadline, time.monotonic(), 0)
    if remaining <= 0:
        result["status"] = "UNKNOWN_INITIALIZATION_LIMIT"
        return result
    solver = cp_model.CpSolver()
    params = native_parameters(cp_model.cmh, remaining)
    solver.parameters = params
    (directory / "parameters.pbtxt").write_text(str(params))
    record = {"status": "NATIVE_CALL_ACTIVE", "call_index": 0,
              "parameters_sha256": file_sha(directory / "parameters.pbtxt"),
              "actual_model_raw_sha256": RAW_HASHES["model"], "native_max_time_seconds": remaining}
    save(directory / "call.json", record)
    result["production_solve_calls"] = 1
    save(directory / "result.json", result)
    stage("native_call_entering")
    started = time.monotonic()
    status = solver.solve(model)
    elapsed = time.monotonic() - started
    response = solver.response_proto
    values = list(response.solution)
    if values:
        assert len(values) == 540 and all(type(v) is int for v in values)
        save(directory / "candidate.json", values)
        result.update(candidate_sha256=file_sha(directory / "candidate.json"),
                      candidate_values_sha256=sha(canonical(values)), saved_candidate_variables=540)
    (directory / "response.pbtxt").write_text(str(response))
    record.update(status="NATIVE_CALL_RETURNED", native_status=solver.status_name(status),
                  native_solve_wall_seconds=elapsed,
                  native_budget_overrun_seconds=max(0, elapsed - NATIVE_SECONDS),
                  response_sha256=file_sha(directory / "response.pbtxt"))
    save(directory / "call.json", record)
    result.update(native_status=record["native_status"], native_solve_wall_seconds=elapsed,
                  native_budget_overrun_seconds=record["native_budget_overrun_seconds"],
                  call_record_sha256=file_sha(directory / "call.json"))
    save(directory / "result.json", result)
    stage("native_call_returned_and_any_full_vector_saved")
    if elapsed > NATIVE_SECONDS:
        result["status"] = "UNKNOWN_NATIVE_BUDGET_OVERRUN"
    elif status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        assert values
        check = inspect(values, plan, cuts)
        check.update(candidate_file_sha256=result["candidate_sha256"],
                     query_preparation_sha256=preparation_sha,
                     source_sha256=file_sha(Path(__file__)),
                     exact_inspector_source_sha256=SOURCES["builder"][1])
        save(directory / "direct-check.json", check)
        save(directory / "selection.json", check["selected"])
        result.update(status="EXACT_DIRECT_LITERAL_INCIDENCE",
                      direct_literal_witness_accepted=True,
                      direct_check_sha256=file_sha(directory / "direct-check.json"),
                      selection_sha256=file_sha(directory / "selection.json"))
    elif status == cp_model.INFEASIBLE:
        result["status"] = "UNPROVED_NATIVE_INFEASIBLE"
    elif status == cp_model.MODEL_INVALID:
        result["status"] = "ERROR_NATIVE_MODEL_INVALID"
    else:
        result["status"] = "UNKNOWN_NATIVE"
    result["automatic_retry"] = False
    return result


def cold(directory, preparation, saved_directory, stage):
    _, preparation_sha = checked_preparation(preparation)
    plan, raw, cuts = load_artifacts(stage)
    owner = json.loads((saved_directory / "owner-result.json").read_bytes())
    assert owner["source_sha256"] == file_sha(Path(__file__))
    assert owner["query_preparation_sha256"] == preparation_sha
    if not (saved_directory / "result.json").exists():
        assert not owner["report_accepted"] and owner["supervision"]["child_reaped"]
        assert all(not (saved_directory / name).exists() for name in
                   ("call.json", "candidate.json", "response.pbtxt", "actual-model.pb"))
        stage("early_child_failure_replayed_without_a_native_call")
        return {"status": "PASS: direct540 zero-call failure replay",
                "source_sha256": file_sha(Path(__file__)), "query_preparation_sha256": preparation_sha,
                "run_owner_sha256": file_sha(saved_directory / "owner-result.json"),
                "original_owner_status": owner["status"], "production_solve_calls_replayed": 0,
                "saved_candidate_checked_exactly": False, "run_outcome_relabelled": False,
                "optimizer_calls": 0, "CpSolver_constructed": False, "graph_exists_claimed": False}
    run_raw = (saved_directory / "result.json").read_bytes()
    run_result = json.loads(run_raw)
    assert run_result["query_preparation_sha256"] == preparation_sha
    assert run_result["model_raw_sha256"] == RAW_HASHES["model"]
    assert run_result["production_solve_calls"] in (0, 1)
    assert owner["source_sha256"] == file_sha(Path(__file__))
    if (saved_directory / "actual-model.pb").exists():
        assert file_sha(saved_directory / "actual-model.pb") == RAW_HASHES["model"]
    check, call = None, None
    if run_result["production_solve_calls"] == 1:
        from google.protobuf import text_format
        from ortools.sat import sat_parameters_pb2, cp_model_pb2
        call = json.loads((saved_directory / "call.json").read_bytes())
        params_raw = (saved_directory / "parameters.pbtxt").read_bytes()
        assert sha(params_raw) == call["parameters_sha256"]
        params = sat_parameters_pb2.SatParameters()
        text_format.Parse(params_raw.decode(), params)
        expected = {"num_search_workers": 1, "random_seed": 0, "cp_model_probing_level": 0,
                    "linearization_level": 0, "max_time_in_seconds": call["native_max_time_seconds"],
                    "log_search_progress": True, "log_to_stdout": True}
        assert {f.name: v for f, v in params.ListFields()} == expected
        assert 0 < call["native_max_time_seconds"] <= NATIVE_SECONDS
        assert call["actual_model_raw_sha256"] == RAW_HASHES["model"] and call["call_index"] == 0
        if call["status"] == "NATIVE_CALL_RETURNED":
            response_raw = (saved_directory / "response.pbtxt").read_bytes()
            assert sha(response_raw) == call["response_sha256"]
            response = cp_model_pb2.CpSolverResponse()
            text_format.Parse(response_raw.decode(), response)
            assert cp_model_pb2.CpSolverStatus.Name(response.status) == call["native_status"]
            assert run_result["native_status"] == call["native_status"]
            assert run_result["call_record_sha256"] == file_sha(saved_directory / "call.json")
            elapsed = call["native_solve_wall_seconds"]
            assert isfinite(elapsed) and elapsed >= 0
            assert call["native_budget_overrun_seconds"] == max(0, elapsed - NATIVE_SECONDS)
            assert run_result["native_solve_wall_seconds"] == elapsed
            assert run_result["native_budget_overrun_seconds"] == call["native_budget_overrun_seconds"]
            if elapsed > NATIVE_SECONDS:
                assert run_result["status"] == "UNKNOWN_NATIVE_BUDGET_OVERRUN"
        else:
            assert call["status"] == "NATIVE_CALL_ACTIVE" and not owner["report_accepted"]
            response = None
    else:
        response = None
        assert not (saved_directory / "call.json").exists()
    if (saved_directory / "candidate.json").exists():
        candidate_raw = (saved_directory / "candidate.json").read_bytes()
        values = json.loads(candidate_raw)
        if "candidate_sha256" in run_result:
            assert run_result["candidate_sha256"] == sha(candidate_raw)
            assert run_result["candidate_values_sha256"] == sha(canonical(values))
        if response is not None:
            assert list(response.solution) == values
        check = inspect(values, plan, cuts)
        check.update(candidate_file_sha256=sha(candidate_raw), query_preparation_sha256=preparation_sha,
                     source_sha256=file_sha(Path(__file__)), exact_inspector_source_sha256=SOURCES["builder"][1])
        save(directory / "saved-candidate-direct-check.json", check)
        if run_result["direct_literal_witness_accepted"]:
            assert run_result["direct_check_sha256"] == file_sha(saved_directory / "direct-check.json")
            assert run_result["selection_sha256"] == file_sha(saved_directory / "selection.json")
            assert json.loads((saved_directory / "direct-check.json").read_bytes()) == check
            assert json.loads((saved_directory / "selection.json").read_bytes()) == check["selected"]
    else:
        assert not run_result["direct_literal_witness_accepted"]
        if response is not None:
            assert not response.solution
    if run_result["direct_literal_witness_accepted"]:
        assert check is not None and run_result["status"] == "EXACT_DIRECT_LITERAL_INCIDENCE"
        assert call["native_budget_overrun_seconds"] == 0
        assert call["native_status"] in ("OPTIMAL", "FEASIBLE")
    if owner["report_accepted"]:
        assert owner["supervision"]["status"] == "CHILD_EXITED" and owner["supervision"]["child_reaped"]
        assert owner["deadline_overrun_seconds"] == 0
        assert owner["report_sha256"] == sha(run_raw)
    stage("saved_terminal_scope_parameters_and_any_candidate_replayed")
    return {"status": "PASS: direct540 cold terminal replay",
            "source_sha256": file_sha(Path(__file__)), "query_preparation_sha256": preparation_sha,
            "run_result_sha256": sha(run_raw), "run_owner_sha256": file_sha(saved_directory / "owner-result.json"),
            "original_run_status": run_result["status"], "original_owner_status": owner["status"],
            "production_solve_calls_replayed": run_result["production_solve_calls"],
            "saved_candidate_checked_exactly": check is not None, "run_outcome_relabelled": False,
            "query_owner_witness_accepted": bool(owner["report_accepted"] and run_result["direct_literal_witness_accepted"]),
            "native_infeasibility_remains_unproved": True, "graph_exists_claimed": False,
            "optimizer_calls": 0, "CpSolver_constructed": False}


def worker(mode, directory, deadline, preparation=None, saved_directory=None):
    started, stages = time.monotonic(), []
    def stage(label):
        stages.append({"stage": label, "elapsed_seconds": time.monotonic() - started, "memory": memory()})
        save(directory / "stages.json", {"stages": stages})
        if time.monotonic() > deadline:
            raise TimeoutError("direct540 owned phase deadline")
    try:
        stage("started")
        if mode == "prepare":
            report = prepare(directory, deadline, stage)
        elif mode == "run":
            report = run(directory, preparation, deadline, stage)
        else:
            assert mode == "cold" and saved_directory is not None
            report = cold(directory, preparation, saved_directory, stage)
        report.update(seconds=time.monotonic() - started, terminal_memory=memory(),
                      stages_sha256=file_sha(directory / "stages.json"))
        save(directory / ("result.json" if mode == "run" else "report.json"), report)
    except Exception as error:
        save(directory / "error.json", {"error_type": type(error).__name__, "message": str(error), "memory": memory()})
        raise


def owned(mode, directory, preparation=None, saved_directory=None):
    started = time.monotonic()
    limit = SECONDS if mode == "run" else COLD_SECONDS if mode == "cold" else PREPARATION_SECONDS
    deadline = started + limit
    supervisor = source_module("supervisor")
    directory.mkdir(parents=True, exist_ok=False)
    if mode != "prepare":
        assert preparation is not None
    command = [sys.executable, str(Path(__file__).resolve()), "_" + mode,
               "--directory", str(directory.resolve()), "--deadline", str(deadline)]
    if preparation is not None:
        command.extend(("--preparation", str(preparation.resolve())))
    if saved_directory is not None:
        command.extend(("--saved-directory", str(saved_directory.resolve())))
    save(directory / "owner-result.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    supervision = supervisor.supervise(command, directory, deadline)
    result = {"status": supervision["status"], "supervision": supervision, "report_accepted": False,
              "source_sha256": file_sha(Path(__file__)), "maximum_owner_seconds": limit,
              "query_preparation_sha256": file_sha(preparation / "report.json") if preparation is not None else None}
    report_path = directory / ("result.json" if mode == "run" else "report.json")
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        report = json.loads(report_path.read_bytes())
        if mode != "run":
            assert report["status"].startswith("PASS")
        result.update(status=report["status"], report_accepted=True, report_sha256=file_sha(report_path))
    result.update(owner_seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    save(directory / "owner-result.json", result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "cold", "_prepare", "_run", "_cold"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--saved-directory", type=Path)
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode.startswith("_"):
        assert args.deadline is not None
        worker(args.mode[1:], args.directory, args.deadline, args.preparation, args.saved_directory)
    else:
        owned(args.mode, args.directory, args.preparation, args.saved_directory)
