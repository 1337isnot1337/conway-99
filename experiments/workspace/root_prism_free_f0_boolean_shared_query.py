"""One bounded query of the independently accepted literal Boolean model.

Preparation checks native model/parameter/response transport without CpSolver.
Production makes at most one 180-second, one-worker call inside a 300-second
owner. Every returned vector is saved and checked with Python integer
arithmetic. Native INFEASIBLE is unproved; no result constructs a full graph.
"""
import argparse
import gzip
import hashlib
import importlib.metadata
import importlib.util
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = ("experiments/workspace/root_prism_free_f0_boolean_shared_model.py",
        "5a1e8026683a7782fce6ec2a2947748356ac9cd5adf32dd2a0663b0dd60bfca2")
MODEL_SOURCE_SHA = "062737362b889823c8fd2c068bcdd08feac2737214cc7bbd1f3802ec31ea6c71"
NATIVE_SECONDS, OWNER_SECONDS, PREPARATION_SECONDS, FINALIZATION_RESERVE = 180, 300, 60, 60
PARAMETERS = {"num_search_workers": 1, "random_seed": 0, "cp_model_probing_level": 0,
              "linearization_level": 0, "max_time_in_seconds": 180.0,
              "log_search_progress": True, "log_to_stdout": True, "log_to_response": True}


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def base_module():
    path = ROOT / BASE[0]
    assert digest(path) == BASE[1]
    spec = importlib.util.spec_from_file_location("Boolean_query_frozen_transport", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def load_accepted_model(base, configuration):
    from ortools.sat import cp_model_pb2 as pb
    cfg = json.loads(configuration.read_bytes())
    assert cfg["schema"] == "conway99.f0.boolean-shared-one-call-configuration.v1"
    assert cfg["source_sha256"] == digest(__file__) and cfg["parameters"] == PARAMETERS
    assert cfg["native_seconds"] == NATIVE_SECONDS and cfg["owner_seconds"] == OWNER_SECONDS
    assert cfg["preparation_seconds"] == PREPARATION_SECONDS and cfg["finalization_reserve"] == FINALIZATION_RESERVE
    assert cfg["maximum_native_calls"] == 1
    for binding in cfg["sources"].values():
        assert digest(ROOT / binding["path"]) == binding["sha256"]
    records = {name: base.read_bound(binding) for name, binding in cfg["inputs"].items() if name != "model"}
    preparation, owner, cold, cold_owner = [records[k] for k in
        ("model_preparation", "model_preparation_owner", "model_cold", "model_cold_owner")]
    assert preparation["source_sha256"] == owner["source_sha256"] == MODEL_SOURCE_SHA
    assert preparation["configuration_sha256"] == cfg["inputs"]["model_configuration"]["sha256"]
    assert owner["report_accepted"] and owner["report_sha256"] == cfg["inputs"]["model_preparation"]["sha256"]
    assert owner["status"] == preparation["status"] == "PASS_COMPLETE_BOOLEAN_SHARED_MODEL_NATIVE_PREPARATION"
    assert owner["deadline_overrun_seconds"] == 0 and owner["supervision"]["child_reaped"]
    assert owner["supervision"]["returncode"] == 0
    assert cold["status"] == "PASS_INDEPENDENT_COMPLETE_BOOLEAN_SHARED_MODEL"
    assert cold["source"] == cold_owner["source"] == cfg["sources"]["model_cold"]
    assert cold["configuration"] == cfg["inputs"]["model_configuration"]
    assert cold_owner["schema"] == "conway99.f0.boolean-shared-independent-cold-owner.v1"
    assert cold_owner["status"] == "OWNED_COMPLETE_BOOLEAN_SHARED_MODEL_COLD_ACCEPTED"
    assert cold_owner["report_accepted"] and cold_owner["report"] == cfg["inputs"]["model_cold"]
    assert cold_owner["root_gate"] == cfg["inputs"]["model_cold_root_gate"]
    assert cold_owner["supervision"]["exit_code"] == 0 and not cold_owner["supervision"]["hard_timeout"]
    assert cold_owner["supervision"]["child_reaped"] and cold_owner["supervision"]["new_process_group"]
    assert not cold["CpSolver_constructed"] and cold["optimizer_calls"] == 0
    assert cold["complete_parent_bytes_checked"] and cold["all_appended_rows_compared_exactly"] == 150888
    for cold_key, config_key in (("report", "model_preparation"), ("owner", "model_preparation_owner"), ("model", "model")):
        assert cold["preparation_inputs"][cold_key] == cfg["inputs"][config_key]
    raw = gzip.decompress(base.read_bound(cfg["inputs"]["model"], raw=True))
    raw_sha = hashlib.sha256(raw).hexdigest()
    assert len(raw) == preparation["model"]["raw_bytes"] == cold["native_raw_model_bytes"] == 33451907
    assert raw_sha == preparation["model"]["raw_sha256"] == cold["native_raw_model_sha256"] == cfg["model_raw_sha256"]
    model = pb.CpModelProto()
    model.ParseFromString(raw)
    assert model.SerializeToString() == raw
    assert len(model.variables) == 68934 and len(model.constraints) == 168050
    assert {field.name for field, _ in model.ListFields()} <= {"name", "variables", "constraints"}
    assert all(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal for row in model.constraints)
    assert all(list(model.variables[i].domain) == [0, 1] for i in list(range(480)) + list(range(540, 68934)))
    edges = []
    for variable in model.variables[540:]:
        parts = variable.name.split("_")
        assert len(parts) == 4 and parts[:2] == ["shared", "edge"]
        a, b = map(int, parts[2:])
        assert 0 <= a < b < 480 and variable.name == "shared_edge_%03d_%03d" % (a, b)
        edges.append([a, b])
    assert base.value_sha(edges) == cold["inventory"]["edge_domain_sha256"]
    return cfg, model, edges


def parameters(base, cfg, directory):
    from google.protobuf import text_format
    from ortools.sat import sat_parameters_pb2 as sp
    from ortools.sat.python import cp_model
    runtime = cfg["runtime"]
    assert importlib.metadata.version("ortools") == runtime["ortools_version"] == "9.15.6755"
    assert importlib.metadata.version("protobuf") == runtime["protobuf_version"]
    assert digest(cp_model.__file__) == runtime["cp_model_sha256"]
    assert digest(cp_model.cmh.__file__) == runtime["native_helper_sha256"]
    schema = sp.DESCRIPTOR.serialized_pb
    assert hashlib.sha256(schema).hexdigest() == runtime["parameter_schema_sha256"]
    expected = sp.SatParameters()
    for name, value in PARAMETERS.items():
        setattr(expected, name, value)
    native = cp_model.cmh.SatParameters()
    assert native.parse_text_format(text_format.MessageToString(expected)) is True
    native_text = str(native)
    restored = sp.SatParameters()
    text_format.Parse(native_text, restored)
    assert restored.SerializeToString() == expected.SerializeToString()
    (directory / "parameters.pbtxt").write_text(native_text)
    (directory / "parameters.pb").write_bytes(restored.SerializeToString())
    (directory / "parameter-schema.pb").write_bytes(schema)
    return native, {"parameters_sha256": digest(directory / "parameters.pbtxt"),
                    "parameters_wire_sha256": digest(directory / "parameters.pb"),
                    "schema_sha256": hashlib.sha256(schema).hexdigest(), "runtime": runtime,
                    "all_explicit_parameters": PARAMETERS, "defaults_preserved_in_descriptor": True}


def inspect_vector(model, values):
    result = {"status": "REJECTED_RETURNED_VECTOR", "values": len(values), "variables": len(model.variables),
              "all_values_exact_Python_int": all(type(v) is int for v in values),
              "variable_domains_checked": 0, "linear_rows_checked": 0,
              "domain_violations": [], "linear_row_violations": []}
    if len(values) != len(model.variables) or not result["all_values_exact_Python_int"]:
        return result, []
    for index, (variable, value) in enumerate(zip(model.variables, values)):
        domain = list(variable.domain)
        assert len(domain) % 2 == 0 and domain
        if not any(lo <= value <= hi for lo, hi in zip(domain[::2], domain[1::2])):
            result["domain_violations"].append(index)
        result["variable_domains_checked"] += 1
    activities = []
    for index, constraint in enumerate(model.constraints):
        assert constraint.WhichOneof("constraint") == "linear" and not constraint.enforcement_literal
        row = constraint.linear
        assert len(row.vars) == len(row.coeffs)
        assert all(0 <= j < len(values) for j in row.vars)
        activity = sum(int(c) * values[int(j)] for j, c in zip(row.vars, row.coeffs))
        domain = list(row.domain)
        assert len(domain) % 2 == 0 and domain
        if not any(lo <= activity <= hi for lo, hi in zip(domain[::2], domain[1::2])):
            result["linear_row_violations"].append(index)
        activities.append(activity)
        result["linear_rows_checked"] += 1
    if not result["domain_violations"] and not result["linear_row_violations"]:
        result["status"] = "PASS_EXACT_INTEGER_VECTOR_ALL_DOMAINS_AND_ROWS"
    return result, activities


def controls(base):
    from google.protobuf import text_format
    from ortools.sat import cp_model_pb2 as pb
    from ortools.sat.python import cp_model
    toy = pb.CpModelProto()
    for domain in ([0, 1], [-2, 3], [0, 1]):
        toy.variables.add().domain.extend(domain)
    large = (1 << 54) + 3
    base.linear(toy, [0, 2], [1, -1], 0, 0)
    base.linear(toy, [1], [large], 2 * large, 2 * large)
    base.linear(toy, [], [], 0, 0)
    assert inspect_vector(toy, [1, 2, 1])[0]["status"].startswith("PASS_")
    assert inspect_vector(toy, [0, 2, 1])[0]["linear_row_violations"] == [0]
    assert inspect_vector(toy, [1, 4, 1])[0]["domain_violations"] == [1]
    assert not inspect_vector(toy, [1, 2.0, 1])[0]["all_values_exact_Python_int"]
    for status, values in ((pb.FEASIBLE, [0, 1, large]), (pb.INFEASIBLE, []), (pb.UNKNOWN, [])):
        expected = pb.CpSolverResponse(status=status, solution=values, wall_time=0.125, solution_info="transport control")
        native = cp_model.cmh.CpSolverResponse()
        assert native.parse_text_format(text_format.MessageToString(expected)) is True
        actual = pb.CpSolverResponse()
        text_format.Parse(str(native), actual)
        assert actual.SerializeToString() == expected.SerializeToString()
        assert list(native.solution) == values
    return {"status": "PASS_EXACT_INSPECTION_AND_NATIVE_RESPONSE_CONTROLS", "CpSolver_constructed": False,
            "optimizer_calls": 0, "large_integer": large, "negative_and_empty_rows_checked": True,
            "invalid_integer_domain_and_row_vectors_rejected": True, "response_statuses_checked": 3}


def preparation(base, args, cfg, model):
    parameter_object, parameter_record = parameters(base, cfg, args.directory)
    del parameter_object
    control_record = controls(base)
    _, native = base.transport(model, args.directory / "model.pb", args.deadline)
    assert native["public_parse_return"] is True
    base.check_time(args.deadline)
    return {"status": "PASS_BOOLEAN_SHARED_ONE_CALL_QUERY_PREFLIGHT", "native_transport": native,
            "parameters": parameter_record, "controls": control_record,
            "CpSolver_constructed": False, "production_solve_calls": 0,
            "model_cold": cfg["inputs"]["model_cold"], "model_raw_sha256": cfg["model_raw_sha256"]}


def run(base, args, cfg, model, edges):
    from google.protobuf import text_format
    from ortools.sat import cp_model_pb2 as pb
    from ortools.sat.python import cp_model
    preflight_path = args.preparation / "report.json"
    preflight = json.loads(preflight_path.read_bytes())
    preflight_owner = json.loads((args.preparation / "owner.json").read_bytes())
    assert preflight["status"] == preflight_owner["status"] == "PASS_BOOLEAN_SHARED_ONE_CALL_QUERY_PREFLIGHT"
    assert preflight["source_sha256"] == preflight_owner["source_sha256"] == digest(__file__)
    assert preflight["configuration_sha256"] == preflight_owner["configuration_sha256"] == digest(args.configuration)
    assert preflight_owner["report_accepted"] and preflight_owner["report_sha256"] == digest(preflight_path)
    assert preflight_owner["deadline_overrun_seconds"] == 0 and preflight_owner["supervision"]["child_reaped"]
    assert preflight_owner["supervision"]["returncode"] == 0 and preflight["production_solve_calls"] == 0
    parameter_object, parameter_record = parameters(base, cfg, args.directory)
    assert parameter_record == preflight["parameters"]
    native_model, native = base.transport(model, args.directory / "model.pb", args.deadline)
    assert native["public_parse_return"] is True and native["native_raw_sha256"] == cfg["model_raw_sha256"]
    result = {"status": "UNKNOWN_BEFORE_NATIVE_CALL", "model_raw_sha256": cfg["model_raw_sha256"],
              "preflight_report_sha256": digest(preflight_path), "preflight_owner_sha256": digest(args.preparation / "owner.json"),
              "native_transport": native, "parameters": parameter_record, "production_solve_calls": 0,
              "CpSolver_constructed": False, "returned_vectors": [], "graph_constructed": False,
              "whole_component_excluded": False, "independent_query_cold_required": True}
    base.save(args.directory / "result.json", result)
    if args.deadline - time.monotonic() < NATIVE_SECONDS + FINALIZATION_RESERVE:
        result["status"] = "UNKNOWN_INSUFFICIENT_REMAINING_OWNER_BUDGET_NO_CALL"
        return result
    solver = cp_model.CpSolver()
    solver.parameters = parameter_object
    result.update(status="NATIVE_CALL_ACTIVE", production_solve_calls=1, CpSolver_constructed=True,
                  native_allowance_seconds=NATIVE_SECONDS, remaining_owner_at_call=args.deadline - time.monotonic())
    base.save(args.directory / "result.json", result)
    started = time.monotonic()
    status = solver.solve(native_model)
    elapsed = time.monotonic() - started
    native_response = solver.response_proto
    native_values = list(native_response.solution)
    native_vectors = [("candidate", native_values)] if native_values else []
    native_vectors += [("additional-candidate-%03d" % index, list(item.values))
                       for index, item in enumerate(native_response.additional_solutions)]
    for name, vector in native_vectors:
        base.save(args.directory / (name + ".json"), vector)
    response_text = str(native_response)
    (args.directory / "response.pbtxt").write_text(response_text)
    (args.directory / "response-stats.txt").write_text(solver.response_stats())
    response = pb.CpSolverResponse()
    text_format.Parse(response_text, response)
    assert pb.CpSolverStatus.Name(response.status) == solver.status_name(status)
    (args.directory / "response.pb").write_bytes(response.SerializeToString())
    values = list(response.solution)
    assert values == native_values
    result.update(status="NATIVE_CALL_RETURNED", native_status=solver.status_name(status), native_seconds=elapsed,
                  native_reported_wall_seconds=response.wall_time, native_overrun_seconds=max(0, elapsed - NATIVE_SECONDS),
                  response_sha256=digest(args.directory / "response.pbtxt"), response_wire_sha256=digest(args.directory / "response.pb"))
    base.save(args.directory / "result.json", result)
    vectors = [("candidate", values)] if values else []
    vectors += [("additional-candidate-%03d" % index, list(item.values)) for index, item in enumerate(response.additional_solutions)]
    assert vectors == native_vectors
    for name, vector in vectors:
        check, activities = inspect_vector(model, vector)
        base.save(args.directory / (name + "-check.json"), check)
        activity_raw = base.canonical(activities)
        activity_path = args.directory / (name + "-row-activities.json.gz")
        activity_path.write_bytes(gzip.compress(activity_raw, compresslevel=6, mtime=0))
        result["returned_vectors"].append({"name": name, "candidate_sha256": digest(args.directory / (name + ".json")),
            "candidate_values_sha256": base.value_sha(vector), "check_sha256": digest(args.directory / (name + "-check.json")),
            "activities_sha256": digest(activity_path), "activities_raw_sha256": hashlib.sha256(activity_raw).hexdigest(),
            "check_status": check["status"], "values": len(vector)})
        if name == "candidate" and check["status"].startswith("PASS_"):
            selection = [a for a in range(480) if vector[a] == 1]
            edge_ids = [e for e in range(68394) if vector[540 + e] == 1]
            base.save(args.directory / "selection.json", selection)
            base.save(args.directory / "selected-edges.json", {"edge_ids": edge_ids, "edges": [edges[e] for e in edge_ids]})
            result.update(selection_sha256=digest(args.directory / "selection.json"), selected_edges_sha256=digest(args.directory / "selected-edges.json"))
        base.save(args.directory / "result.json", result)
        base.check_time(args.deadline)
    if result["native_overrun_seconds"] > 0:
        result["status"] = "UNKNOWN_NATIVE_BUDGET_OVERRUN"
    elif any(not row["check_status"].startswith("PASS_") for row in result["returned_vectors"]):
        result["status"] = "ERROR_EXACT_RETURNED_VECTOR_CHECK_FAILED"
    elif status in (cp_model.FEASIBLE, cp_model.OPTIMAL):
        result["status"] = "EXACT_BOOLEAN_MODEL_VECTOR_AWAITING_INDEPENDENT_COLD" if values else "ERROR_NATIVE_SAT_WITHOUT_VECTOR"
    elif status == cp_model.INFEASIBLE:
        result["status"] = "UNPROVED_NATIVE_INFEASIBLE"
    elif status == cp_model.MODEL_INVALID:
        result["status"] = "ERROR_NATIVE_MODEL_INVALID"
    else:
        result["status"] = "UNKNOWN_BOOLEAN_SHARED_NATIVE"
    return result


def main(args):
    started = time.monotonic()
    base = base_module()
    if args.worker:
        try:
            cfg, model, edges = load_accepted_model(base, args.configuration)
            report = preparation(base, args, cfg, model) if args.mode == "prepare" else run(base, args, cfg, model, edges)
            report.update(source_sha256=digest(__file__), configuration_sha256=digest(args.configuration),
                          seconds=time.monotonic() - started, peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            base.save(args.directory / ("report.json" if args.mode == "prepare" else "result.json"), report)
        except Exception as error:
            base.save(args.directory / "error.json", {"type": type(error).__name__, "message": str(error)})
            raise
        return
    args.directory.mkdir(parents=True, exist_ok=False)
    supervisor_path = ROOT / base.SUPERVISOR[0]
    assert digest(supervisor_path) == base.SUPERVISOR[1]
    spec = importlib.util.spec_from_file_location("Boolean_query_supervisor", supervisor_path)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    limit = PREPARATION_SECONDS if args.mode == "prepare" else OWNER_SECONDS
    deadline = started + limit
    command = [sys.executable, str(Path(__file__).resolve()), args.mode, "--worker", "--configuration", str(args.configuration.resolve()),
               "--directory", str(args.directory.resolve()), "--deadline", str(deadline)]
    if args.preparation is not None:
        command += ["--preparation", str(args.preparation.resolve())]
    base.save(args.directory / "owner.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    supervision = supervisor.supervise(command, args.directory, deadline)
    owner = {"source_sha256": digest(__file__), "configuration_sha256": digest(args.configuration),
             "mode": args.mode, "maximum_seconds": limit, "supervision": supervision,
             "status": supervision["status"], "report_accepted": False}
    report_path = args.directory / ("report.json" if args.mode == "prepare" else "result.json")
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= deadline:
        report = json.loads(report_path.read_bytes())
        assert report["source_sha256"] == digest(__file__) and report["configuration_sha256"] == digest(args.configuration)
        owner.update(report_accepted=True, report_sha256=digest(report_path), status=report["status"])
    owner.update(seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    if owner["deadline_overrun_seconds"]:
        owner.update(report_accepted=False, status="UNKNOWN_HARD_DEADLINE")
    base.save(args.directory / "owner.json", owner)
    print(json.dumps(owner, sort_keys=True), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("exact model and vector checks required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run"))
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--deadline", type=float)
    arguments = parser.parse_args()
    assert arguments.mode != "run" or arguments.preparation is not None
    assert not arguments.worker or arguments.deadline is not None
    main(arguments)
