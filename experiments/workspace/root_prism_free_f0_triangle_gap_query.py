"""One gated query of the independently accepted triangle-gap model.

Preserve every model byte. Use the explicit no-LP full-subsolver portfolio,
four workers, one 600-second solver clock, a 610-second measured native
allowance and a 720-second process-group owner. Save exact native response
text and every native vector before parsing. A native answer is not a graph
completion or a component exclusion.
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
import traceback

ROOT = Path(__file__).resolve().parents[2]
MODEL_SOURCE_SHA = "a3512a083ec480d36b823273ec7ba7eb3f47ff05efaed4a3b0e62346e4fba36c"
MODEL_COLD_SHA = "8881d15ce768ca14f8c06d0e00803989a19d49bc3be55bba4e6fbca43e1dd87f"
MODEL_CI_SHA = "bb35593aacf5f71540e2399b2880c8fe15ef074d946a4a96cc529da613c9d048"
BASE_SHA = "5a1e8026683a7782fce6ec2a2947748356ac9cd5adf32dd2a0663b0dd60bfca2"
SUPERVISOR_SHA = "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3"
PARENT_RAW_SHA = "56f6be31b4714825fb6d546ca79420e0ee0d25da05231a0eea322e514473bed8"
PARENT_RAW_BYTES, PARENT_VARIABLES, PARENT_ROWS, PARENT_TERMS = 39512348, 80730, 300795, 3337296
VARIABLES, ROWS, TOTAL_TERMS, EDGE_STOP = 80730, 303951, 3340452, 68934
FAMILY_ORDER = ["gap_triangle_zero"]
FAMILY_COUNTS = {"gap_triangle_zero": 3156}
FAMILY_TERMS = {"gap_triangle_zero": 3156}
EDGE_SHA = "411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb"
LIMITS = {"solver_seconds": 600, "native_allowance_seconds": 610, "owner_seconds": 720,
          "preparation_seconds": 60, "preparation_owner_seconds": 75, "finalization_reserve_seconds": 60}
PARAMETERS = {"num_search_workers": 4, "random_seed": 0, "cp_model_presolve": True,
              "cp_model_probing_level": 0, "linearization_level": 0, "symmetry_level": 0,
              "subsolvers": ["no_lp", "quick_restart_no_lp", "portfolio_no_lp"], "num_full_subsolvers": 3,
              "max_time_in_seconds": 600.0, "log_search_progress": True,
              "log_to_stdout": True, "log_to_response": True}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha(Path(path).read_bytes())


def binding(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(data), "bytes": len(data)}


def read_bytes(ref):
    path = (ROOT / ref["path"]).resolve()
    path.relative_to(ROOT)
    data = path.read_bytes()
    assert sha(data) == ref["sha256"]
    assert "bytes" not in ref or len(data) == ref["bytes"]
    return data


def read_json(ref):
    data = read_bytes(ref)
    if ref["path"].endswith(".gz"):
        data = gzip.decompress(data)
    return json.loads(data)


def same_reference(first, second):
    assert (first["path"], first["sha256"]) == (second["path"], second["sha256"])
    for ref in (first, second):
        if "bytes" in ref:
            assert (ROOT / ref["path"]).stat().st_size == ref["bytes"]


def save(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def check_time(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("triangle gap query phase deadline")


def bound_module(name, ref):
    read_bytes(ref)
    spec = importlib.util.spec_from_file_location(name, ROOT / ref["path"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def configuration(path):
    cfg = json.loads(Path(path).read_bytes())
    assert cfg["schema"] == "conway99.f0.triangle-gap-query-configuration.v1"
    assert cfg["source_sha256"] == digest(__file__)
    assert cfg["parameters"] == PARAMETERS and cfg["limits"] == LIMITS
    assert cfg["maximum_native_calls"] == 1 and cfg["automatic_retries"] == 0
    assert cfg["native_query_authorized_by_configuration_alone"] is False
    assert cfg["variables"] == VARIABLES and cfg["rows"] == ROWS
    assert set(cfg["inputs"]) == {"model", "model_configuration", "model_preparation",
                                 "model_preparation_owner", "model_cold", "model_cold_owner",
                                 "model_root_acceptance"}
    assert set(cfg["sources"]) == {"base", "supervisor", "model_producer", "model_cold", "model_ci"}
    assert cfg["sources"]["base"]["sha256"] == BASE_SHA
    assert cfg["sources"]["supervisor"]["sha256"] == SUPERVISOR_SHA
    assert cfg["sources"]["model_producer"]["sha256"] == MODEL_SOURCE_SHA
    assert cfg["sources"]["model_cold"]["sha256"] == MODEL_COLD_SHA
    assert cfg["sources"]["model_ci"]["sha256"] == MODEL_CI_SHA
    # These are actual accepted output identities, filled only after native cold.
    assert type(cfg["model_raw_sha256"]) is str and len(cfg["model_raw_sha256"]) == 64
    assert all(c in "0123456789abcdef" for c in cfg["model_raw_sha256"])
    assert type(cfg["model_raw_bytes"]) is int and cfg["model_raw_bytes"] > 0
    for ref in list(cfg["sources"].values()) + list(cfg["inputs"].values()):
        assert type(ref["path"]) is str and type(ref["bytes"]) is int and ref["bytes"] > 0
        assert type(ref["sha256"]) is str and len(ref["sha256"]) == 64
    for ref in cfg["sources"].values():
        read_bytes(ref)
    return cfg


def accepted_model(cfg):
    from ortools.sat import cp_model_pb2 as pb
    records = {name: read_json(ref) for name, ref in cfg["inputs"].items() if name != "model"}
    preparation, owner, cold, cold_owner = [records[name] for name in
        ("model_preparation", "model_preparation_owner", "model_cold", "model_cold_owner")]
    model_cfg, root_acceptance = records["model_configuration"], records["model_root_acceptance"]
    assert model_cfg["schema"] == "conway99.f0.triangle-gap-native-configuration.v1"
    assert model_cfg["source_sha256"] == MODEL_SOURCE_SHA
    same_reference(model_cfg["sources"]["checker"], cfg["sources"]["model_cold"])
    for name in ("base", "supervisor"):
        same_reference(model_cfg["sources"][name], cfg["sources"][name])
    assert model_cfg["native_query_authorized"] is False and model_cfg["optimizer_calls"] == 0
    assert model_cfg["independent_complete_protobuf_replay_required"] is True
    assert root_acceptance["schema"] == "conway99.f0.triangle-gap-native-root-acceptance.v1"
    assert root_acceptance["status"] == "ROOT_ACCEPTS_COMPLETE_TRIANGLE_GAP_NATIVE_MODEL_AND_INDEPENDENT_COLD"
    for field, alias in (("configuration", "model_configuration"), ("preparation", "model_preparation"),
                         ("independent_cold", "model_cold"), ("model_archive", "model")):
        same_reference(root_acceptance[field], cfg["inputs"][alias])
    same_reference(root_acceptance["driver_source"], cfg["sources"]["model_ci"])
    same_reference(root_acceptance["owners"]["preparation"], cfg["inputs"]["model_preparation_owner"])
    same_reference(root_acceptance["owners"]["independent_cold"], cfg["inputs"]["model_cold_owner"])
    assert root_acceptance["model_raw_sha256"] == cfg["model_raw_sha256"]
    assert root_acceptance["model_raw_bytes"] == cfg["model_raw_bytes"]
    assert root_acceptance["variables"] == VARIABLES and root_acceptance["rows"] == ROWS
    assert root_acceptance["total_terms"] == TOTAL_TERMS
    assert root_acceptance["optimizer_calls"] == 0 and root_acceptance["native_query_authorized_by_this_receipt"] is False
    assert root_acceptance["complete_original_parent_bytes_recovered"] is True
    assert preparation["schema"] == "conway99.f0.triangle-gap-native-preparation.v1"
    assert owner["schema"] == "conway99.f0.triangle-gap-native-owner.v1"
    assert preparation["status"] == owner["status"] == "PASS_COMPLETE_TRIANGLE_GAP_NATIVE_PREPARATION"
    assert preparation["source"]["sha256"] == owner["source"]["sha256"] == MODEL_SOURCE_SHA
    assert owner["mode"] == "prepare" and preparation["maximum_seconds"] == 120
    assert 0 <= owner["seconds"] <= owner["maximum_seconds"] == 135
    assert cold["schema"] == "conway99.f0.triangle-gap-independent-cold.v1"
    assert cold["status"] == "PASS_INDEPENDENT_COMPLETE_TRIANGLE_GAP_NATIVE_MODEL"
    assert cold_owner["schema"] == "conway99.f0.triangle-gap-external-cold-owner.v1"
    assert cold_owner["status"] == "PASS_TRIANGLE_GAP_EXTERNAL_COLD_REPLAY"
    assert cold["source"]["sha256"] == cold_owner["source"]["sha256"] == MODEL_COLD_SHA
    assert cold_owner["mode"] == "replay" and cold["maximum_seconds"] == 120
    assert 0 <= cold_owner["seconds"] <= cold_owner["maximum_seconds"] == 135
    for record in (preparation, owner, cold, cold_owner):
        same_reference(record["configuration"], cfg["inputs"]["model_configuration"])
        assert record["optimizer_calls"] == 0 and record["CpSolver_constructed"] is False
    for receipt, alias in ((owner, "model_preparation"), (cold_owner, "model_cold")):
        same_reference(receipt["report"], cfg["inputs"][alias])
        assert receipt["report_accepted"] is True and receipt["deadline_overrun_seconds"] == 0
        supervision = receipt["supervision"]
        assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
        assert supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
    same_reference(cold["preparation_report"], cfg["inputs"]["model_preparation"])
    same_reference(cold["preparation_owner"], cfg["inputs"]["model_preparation_owner"])
    assert preparation["inputs"] == cold["inputs"] == model_cfg["inputs"]
    assert preparation["authorities"] == model_cfg["authorities"]
    assert preparation["authority_links"] == model_cfg["authority_links"]
    assert preparation["layout"] == cold["layout"] == model_cfg["layout"]
    assert preparation["family_order"] == cold["family_order"] == FAMILY_ORDER
    assert preparation["family_counts"] == cold["family_counts"] == FAMILY_COUNTS
    assert preparation["family_terms"] == cold["family_terms"] == FAMILY_TERMS
    for field in ("row_keys_sha256", "family_row_keys_sha256", "family_row_jsonl_sha256"):
        assert preparation[field] == cold[field]
    assert preparation["gap_check"] == cold["gap_check"]
    assert preparation["model_raw_sha256"] == cold["model_raw_sha256"] == cfg["model_raw_sha256"]
    assert preparation["model_raw_bytes"] == cold["model_raw_bytes"] == cfg["model_raw_bytes"]
    assert preparation["parent_variables"] == cold["parent_variables"] == PARENT_VARIABLES
    assert preparation["parent_rows"] == cold["parent_rows"] == PARENT_ROWS
    assert preparation["parent_total_terms"] == cold["parent_total_terms"] == PARENT_TERMS
    assert preparation["total_terms"] == cold["total_terms"] == TOTAL_TERMS
    assert preparation["term_change"] == cold["appended_terms"] == sum(FAMILY_TERMS.values()) == 3156
    assert cold["appended_rows"] == sum(FAMILY_COUNTS.values()) == 3156
    assert preparation["new_variables"] == cold["new_variables"] == preparation["replaced_rows"] == cold["replaced_rows"] == 0
    assert preparation["CpModel_constructed"] is True and preparation["native_model_builds"] == 1
    assert preparation["native_optimizer_constructed"] is False and preparation["native_query_run"] is False
    assert preparation["parent_is_complete_raw_prefix"] is True
    assert preparation["all_certified_zeros_retained"] is True
    assert cold["CpModel_constructed"] is False and cold["native_optimizer_constructed"] is False
    assert cold["native_model_builds"] == 0 and cold["native_query_run"] is False
    assert cold["base_restoration_sha256"] == PARENT_RAW_SHA and cold["base_restoration_bytes"] == PARENT_RAW_BYTES
    for field in ("complete_original_parent_bytes_recovered", "all_original_variable_and_constraint_messages_preserved",
                  "all_appended_complete_constraint_messages_independently_checked",
                  "complete_row_origins_and_lossless_restoration_checked", "all_3156_certified_zero_rows_retained",
                  "native_AND_meanings_recovered_independently"):
        assert cold[field] is True
    for field in ("spectral_arithmetic_repeated", "spectral_producer_or_literal_checker_imported",
                  "native_transport_or_preparation_producer_imported", "native_query_authorized_by_this_report"):
        assert cold[field] is False
    same_reference(preparation["gap_literal_root_acceptance"], model_cfg["inputs"]["gap_literal_root_acceptance"])
    same_reference(cold["gap_literal_root_acceptance"], model_cfg["inputs"]["gap_literal_root_acceptance"])
    gap = cold["gap_check"]
    assert gap["forward_records_bound"] == 5364 and gap["complete_failed_indices"] == 3156
    assert gap["native_indicator_messages_checked"] == 3156 and gap["native_edge_variable_messages_checked"] == 9468
    assert gap["complete_native_AND_messages_checked"] == 12624 and gap["all_certified_zeros_retained"] is True
    assert gap["spectral_minor_recomputations"] == gap["old_family_reconstructions"] == 0
    assert gap["failed_triangle_indices_sha256"] == "cb049b7390dfd13617d01675b0cce593377ba5bebfc6084767a49033f7ad4dbe"
    assert cold["row_keys_sha256"] == "68cbeeb785a7d68e7141464bd3c9c9274bebddcd33875ea4c843494f2da44b4c"
    same_reference(preparation["artifacts"]["model_archive"], cfg["inputs"]["model"])
    same_reference(cold["artifacts"]["model_archive"], cfg["inputs"]["model"])
    archive = read_bytes(cfg["inputs"]["model"])
    assert sha(archive) == preparation["model"]["archive_sha256"] == cold["model_archive_sha256"]
    assert len(archive) == preparation["model"]["archive_bytes"] == cold["model_archive_bytes"]
    raw = gzip.decompress(archive)
    assert len(raw) == cfg["model_raw_bytes"] == preparation["model"]["raw_bytes"] == cold["model_raw_bytes"]
    assert sha(raw) == cfg["model_raw_sha256"] == preparation["model"]["raw_sha256"] == cold["model_raw_sha256"]
    assert preparation["variables"] == cold["variables"] == VARIABLES and preparation["rows"] == cold["rows"] == ROWS
    assert sha(pb.DESCRIPTOR.serialized_pb) == cfg["runtime"]["model_schema_sha256"] == preparation["runtime"]["model_schema_sha256"]
    model = pb.CpModelProto()
    model.ParseFromString(raw)
    assert model.SerializeToString() == raw and len(model.variables) == VARIABLES and len(model.constraints) == ROWS
    assert {field.name for field, _ in model.ListFields()} <= {"name", "variables", "constraints"}
    assert all(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal for row in model.constraints)
    edges = []
    for variable in model.variables[540:EDGE_STOP]:
        prefix, word, left, right = variable.name.split("_")
        a, b = int(left), int(right)
        assert (prefix, word) == ("shared", "edge") and 0 <= a < b < 480
        assert variable.name == "shared_edge_%03d_%03d" % (a, b) and list(variable.domain) == [0, 1]
        edges.append([a, b])
    assert len(edges) == 68394 and sha(canonical(edges)) == EDGE_SHA
    assert all(list(v.domain) == [0, 1] for v in model.variables[:480])
    return model, edges


def parameters(cfg, directory):
    from google.protobuf import text_format
    from ortools.sat import sat_parameters_pb2 as sp
    from ortools.sat.python import cp_model
    runtime = cfg["runtime"]
    assert importlib.metadata.version("ortools") == runtime["ortools_version"] == "9.15.6755"
    assert importlib.metadata.version("protobuf") == runtime["protobuf_version"] == "6.33.6"
    assert digest(cp_model.__file__) == runtime["cp_model_sha256"]
    assert digest(cp_model.cmh.__file__) == runtime["native_helper_sha256"]
    schema = sp.DESCRIPTOR.serialized_pb
    assert sha(schema) == runtime["parameter_schema_sha256"]
    expected = sp.SatParameters()
    for name, value in PARAMETERS.items():
        if name == "subsolvers":
            expected.subsolvers.extend(value)
        else:
            setattr(expected, name, value)
    native = cp_model.cmh.SatParameters()
    assert native.parse_text_format(text_format.MessageToString(expected)) is True
    exported = str(native).encode("utf-8")
    restored = sp.SatParameters()
    text_format.Parse(exported.decode("utf-8"), restored)
    assert restored.SerializeToString() == expected.SerializeToString()
    (directory / "parameters.pbtxt").write_bytes(exported)
    (directory / "parameters.pb").write_bytes(restored.SerializeToString())
    (directory / "parameter-schema.pb").write_bytes(schema)
    return native, {"all_explicit_parameters": PARAMETERS,
                    "parameters_text": binding(directory / "parameters.pbtxt"),
                    "parameters_wire": binding(directory / "parameters.pb"),
                    "parameter_schema": binding(directory / "parameter-schema.pb"),
                    "defaults_preserved_in_descriptor": True, "runtime": runtime,
                    "native_symmetry_disabled_explicitly": True}


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
        if status == pb.FEASIBLE:
            expected.additional_solutions.add().values.extend([large, -large, 0])
        native = cp_model.cmh.CpSolverResponse()
        assert native.parse_text_format(text_format.MessageToString(expected)) is True
        actual = pb.CpSolverResponse()
        text_format.Parse(str(native), actual)
        assert actual.SerializeToString() == expected.SerializeToString()
        assert list(native.solution) == values
        assert [list(v.values) for v in native.additional_solutions] == [list(v.values) for v in expected.additional_solutions]
    passed = [inspect_vector(toy, [1, 2, 1])[0]]
    failed = [inspect_vector(toy, [0, 2, 1])[0]]
    cases = [
        ("FEASIBLE", [1], passed, 0, "EXACT_BOOLEAN_MODEL_VECTOR_AWAITING_INDEPENDENT_COLD"),
        ("OPTIMAL", [1], passed, 0, "EXACT_BOOLEAN_MODEL_VECTOR_AWAITING_INDEPENDENT_COLD"),
        ("FEASIBLE", [], [], 0, "ERROR_NATIVE_SAT_WITHOUT_VECTOR"),
        ("INFEASIBLE", [], [], 0, "UNPROVED_NATIVE_INFEASIBLE"),
        ("UNKNOWN", [], [], 0, "UNKNOWN_TRIANGLE_GAP_NATIVE"),
        ("MODEL_INVALID", [], [], 0, "ERROR_NATIVE_MODEL_INVALID"),
        ("INFEASIBLE", [1], passed, 0, "ERROR_NATIVE_STATUS_VECTOR_CONTRADICTION"),
        ("FEASIBLE", [1], failed, 0, "ERROR_EXACT_RETURNED_VECTOR_CHECK_FAILED"),
        ("FEASIBLE", [1], passed, 0.01, "UNKNOWN_NATIVE_BUDGET_OVERRUN")]
    for status, primary, checked, overrun, expected in cases:
        assert classification(status, primary, checked, overrun) == expected
    return {"status": "PASS_EXACT_INSPECTION_AND_NATIVE_RESPONSE_CONTROLS", "CpSolver_constructed": False,
            "optimizer_calls": 0, "large_integer": large, "negative_and_empty_rows_checked": True,
            "invalid_integer_domain_and_row_vectors_rejected": True, "response_statuses_checked": 3, "additional_integer_vector_roundtrip_checked": True, "terminal_classification_controls": len(cases)}




def prepare(base, args, cfg, model):
    native_parameters, parameter_record = parameters(cfg, args.directory)
    del native_parameters
    control_record = controls(base)
    check_time(args.deadline)
    native_model, transport_record = base.transport(model, args.directory / "model.pb", args.deadline)
    del native_model
    assert transport_record["public_parse_return"] is True
    assert transport_record["native_raw_sha256"] == cfg["model_raw_sha256"]
    check_time(args.deadline)
    return {"status": "PASS_TRIANGLE_GAP_QUERY_PREFLIGHT",
            "native_transport": transport_record, "parameters": parameter_record, "controls": control_record,
            "CpSolver_constructed": False, "production_solve_calls": 0, "optimizer_calls": 0,
            "model_cold": cfg["inputs"]["model_cold"], "model_raw_sha256": cfg["model_raw_sha256"],
            "model_raw_bytes": cfg["model_raw_bytes"], "variables": VARIABLES, "rows": ROWS}


def query_authority(args, cfg):
    report_ref = binding(args.preparation / "report.json")
    owner_ref = binding(args.preparation / "owner.json")
    report, owner = read_json(report_ref), read_json(owner_ref)
    assert report["status"] == owner["status"] == "PASS_TRIANGLE_GAP_QUERY_PREFLIGHT"
    for record in (report, owner):
        same_reference(record["source"], binding(__file__))
        same_reference(record["configuration"], binding(args.configuration))
        assert record["production_solve_calls"] == record["optimizer_calls"] == 0
        assert record["CpSolver_constructed"] is False
    same_reference(owner["report"], report_ref)
    assert owner["report_accepted"] is True and owner["deadline_overrun_seconds"] == 0
    assert owner["seconds"] <= owner["maximum_seconds"] == LIMITS["preparation_owner_seconds"]
    supervision = owner["supervision"]
    assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
    assert supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
    same_reference(report["model_cold"], cfg["inputs"]["model_cold"])
    assert report["model_raw_sha256"] == cfg["model_raw_sha256"] and report["model_raw_bytes"] == cfg["model_raw_bytes"]
    assert report["native_transport"]["complete_byte_comparison"] is True
    assert report["native_transport"]["native_validation"] == "" and report["native_transport"]["public_parse_return"] is True
    gate_ref = binding(args.gate)
    assert gate_ref["sha256"] == args.gate_sha256
    gate = read_json(gate_ref)
    assert gate["status"] == "AUTHORIZE_ONE_TRIANGLE_GAP_MODEL_QUERY"
    same_reference(gate["source"], binding(__file__))
    same_reference(gate["configuration"], binding(args.configuration))
    same_reference(gate["preflight_report"], report_ref)
    same_reference(gate["preflight_owner"], owner_ref)
    same_reference(gate["model_cold"], cfg["inputs"]["model_cold"])
    assert gate["model_raw_sha256"] == cfg["model_raw_sha256"]
    assert gate["limits"] == LIMITS and gate["parameters"] == PARAMETERS
    assert gate["maximum_native_calls"] == 1 and gate["automatic_retries"] == 0
    assert gate["independent_terminal_cold_required"] is True
    return report, {"preflight_report": report_ref, "preflight_owner": owner_ref, "root_gate": gate_ref}


def classification(native_status, primary, checks, native_overrun):
    if native_overrun > 0:
        return "UNKNOWN_NATIVE_BUDGET_OVERRUN"
    if any(check["status"] != "PASS_EXACT_INTEGER_VECTOR_ALL_DOMAINS_AND_ROWS" for check in checks):
        return "ERROR_EXACT_RETURNED_VECTOR_CHECK_FAILED"
    if native_status in ("INFEASIBLE", "MODEL_INVALID") and checks:
        return "ERROR_NATIVE_STATUS_VECTOR_CONTRADICTION"
    if native_status in ("FEASIBLE", "OPTIMAL"):
        return "EXACT_BOOLEAN_MODEL_VECTOR_AWAITING_INDEPENDENT_COLD" if primary else "ERROR_NATIVE_SAT_WITHOUT_VECTOR"
    if native_status == "INFEASIBLE":
        return "UNPROVED_NATIVE_INFEASIBLE"
    if native_status == "MODEL_INVALID":
        return "ERROR_NATIVE_MODEL_INVALID"
    assert native_status == "UNKNOWN"
    return "UNKNOWN_TRIANGLE_GAP_NATIVE"


def run(base, args, cfg, model, edges):
    from google.protobuf import text_format
    from ortools.sat import cp_model_pb2 as pb
    from ortools.sat.python import cp_model
    preflight, authority = query_authority(args, cfg)
    native_parameters, parameter_record = parameters(cfg, args.directory)
    assert parameter_record["all_explicit_parameters"] == preflight["parameters"]["all_explicit_parameters"] == PARAMETERS
    assert parameter_record["runtime"] == preflight["parameters"]["runtime"] == cfg["runtime"]
    for key in ("parameters_text", "parameters_wire", "parameter_schema"):
        previous, current = preflight["parameters"][key], parameter_record[key]
        assert read_bytes(previous) == read_bytes(current)
    native_model, transport_record = base.transport(model, args.directory / "model.pb", args.deadline)
    assert transport_record["public_parse_return"] is True and transport_record["native_raw_sha256"] == cfg["model_raw_sha256"]
    result = {"status": "UNKNOWN_BEFORE_NATIVE_CALL", **authority,
              "model_raw_sha256": cfg["model_raw_sha256"], "model_raw_bytes": cfg["model_raw_bytes"],
              "native_transport": transport_record, "parameters": parameter_record,
              "production_solve_calls": 0, "optimizer_calls": 0, "CpSolver_constructed": False,
              "returned_vectors": [], "all_returned_vectors_checked": False,
              "graph_constructed": False, "whole_component_excluded": False,
              "independent_terminal_cold_required": True, "original_pair_caps_checked": False,
              "second_component_completion_checked": False, "native_INFEASIBLE_is_unproved": True}
    result.update(source=binding(__file__), configuration=binding(args.configuration))
    save(args.directory / "result.json", result)
    remaining = args.deadline - time.monotonic()
    result["remaining_owner_before_call"] = remaining
    if remaining < LIMITS["native_allowance_seconds"] + LIMITS["finalization_reserve_seconds"]:
        result["status"] = "UNKNOWN_INSUFFICIENT_REMAINING_OWNER_BUDGET_NO_CALL"
        return result
    solver = cp_model.CpSolver()
    solver.parameters = native_parameters
    result.update(status="NATIVE_CALL_ACTIVE", production_solve_calls=1, optimizer_calls=1, CpSolver_constructed=True,
                  solver_clock_seconds=LIMITS["solver_seconds"], native_allowance_seconds=LIMITS["native_allowance_seconds"])
    save(args.directory / "result.json", result)
    started = time.monotonic()
    native_code = solver.solve(native_model)
    elapsed = time.monotonic() - started
    native_response = solver.response_proto
    # Preserve the exact native text before parsing or arithmetic. The pinned
    # public binding has no binary-export method for CpSolverResponse.
    native_text = str(native_response).encode("utf-8")
    text_path = args.directory / "response-native.pbtxt"
    text_path.write_bytes(native_text)
    result.update(status="NATIVE_TEXT_SAVED", native_seconds=elapsed,
                  native_overrun_seconds=max(0, elapsed - LIMITS["native_allowance_seconds"]),
                  response_native_text=binding(text_path))
    save(args.directory / "result.json", result)
    snapshot = {"native_status": solver.status_name(native_code),
                "primary": list(native_response.solution),
                "additional": [list(item.values) for item in native_response.additional_solutions]}
    snapshot_path = args.directory / "native-vectors.json"
    save(snapshot_path, snapshot)
    vectors = ([("candidate", snapshot["primary"])] if snapshot["primary"] else [])
    vectors += [("additional-candidate-%03d" % i, values) for i, values in enumerate(snapshot["additional"])]
    for name, values in vectors:
        save(args.directory / (name + ".json"), values)
    stats_path = args.directory / "response-stats.txt"
    stats_path.write_bytes(solver.response_stats().encode("utf-8"))
    result.update(status="NATIVE_VECTORS_SAVED", native_status=snapshot["native_status"],
                  native_vectors=binding(snapshot_path), response_stats=binding(stats_path),
                  native_vector_files=[binding(args.directory / (name + ".json")) for name, _ in vectors])
    save(args.directory / "result.json", result)
    response = pb.CpSolverResponse()
    text_format.Parse(native_text.decode("utf-8"), response)
    assert pb.CpSolverStatus.Name(response.status) == snapshot["native_status"]
    assert list(response.solution) == snapshot["primary"]
    assert [list(item.values) for item in response.additional_solutions] == snapshot["additional"]
    wire_path = args.directory / "response-reconstructed.pb"
    wire_path.write_bytes(response.SerializeToString())
    result.update(status="NATIVE_RESPONSE_PARSED", response_reconstructed_wire=binding(wire_path),
                  wire_reconstructed_from_native_text=True, original_native_binary_export_available=False,
                  native_reported_wall_seconds=response.wall_time)
    save(args.directory / "result.json", result)
    checks = []
    for name, values in vectors:
        check, activities = inspect_vector(model, values)
        checks.append(check)
        check_path = args.directory / (name + "-check.json")
        save(check_path, check)
        activity_raw = canonical(activities)
        activity_path = args.directory / (name + "-row-activities.json.gz")
        activity_path.write_bytes(gzip.compress(activity_raw, compresslevel=6, mtime=0))
        result["returned_vectors"].append({
            "name": name, "candidate": binding(args.directory / (name + ".json")),
            "candidate_values_sha256": sha(canonical(values)), "check": binding(check_path),
            "activities": binding(activity_path), "activities_raw_sha256": sha(activity_raw),
            "activities_raw_bytes": len(activity_raw), "check_status": check["status"], "values": len(values)})
        if name == "candidate" and check["status"] == "PASS_EXACT_INTEGER_VECTOR_ALL_DOMAINS_AND_ROWS":
            selected = [a for a in range(480) if values[a] == 1]
            chosen = [e for e in range(68394) if values[540 + e] == 1]
            save(args.directory / "selection.json", selected)
            save(args.directory / "selected-edges.json", {"edge_ids": chosen, "edges": [edges[e] for e in chosen]})
            result.update(selection=binding(args.directory / "selection.json"),
                          selected_edges=binding(args.directory / "selected-edges.json"))
        save(args.directory / "result.json", result)
        check_time(args.deadline)
    result["all_returned_vectors_checked"] = True
    result["status"] = classification(snapshot["native_status"], snapshot["primary"], checks, result["native_overrun_seconds"])
    return result


def worker(args):
    started = time.monotonic()
    stages = []
    def stage(name):
        stages.append({"stage": name, "seconds": time.monotonic() - started})
        save(args.directory / "stages.json", stages)
        check_time(args.deadline)
    try:
        stage("started")
        cfg = configuration(args.configuration)
        model, edges = accepted_model(cfg)
        stage("accepted_model_loaded")
        base = bound_module("strengthened_query_public_transport", cfg["sources"]["base"])
        report = prepare(base, args, cfg, model) if args.mode == "_prepare" else run(base, args, cfg, model, edges)
        report.update(schema="conway99.f0.triangle-gap-query-terminal.v1",
                      source=binding(__file__), configuration=binding(args.configuration),
                      inputs=cfg["inputs"], limits=LIMITS,
                      variables=VARIABLES, rows=ROWS, graph_constructed=False, whole_component_excluded=False,
                      seconds=time.monotonic() - started, peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        check_time(args.deadline)
        save(args.directory / ("report.json" if args.mode == "_prepare" else "result.json"), report)
    except Exception as error:
        save(args.directory / "error.json", {"status": "ERROR_QUERY_WORKER", "type": type(error).__name__,
             "message": str(error), "traceback": traceback.format_exc(), "graph_constructed": False,
             "whole_component_excluded": False, "seconds": time.monotonic() - started})
        raise


def owned(args):
    started = time.monotonic()
    cfg = configuration(args.configuration)
    maximum = LIMITS["preparation_owner_seconds"] if args.mode == "prepare" else LIMITS["owner_seconds"]
    deadline = started + maximum
    worker_deadline = started + LIMITS["preparation_seconds"] if args.mode == "prepare" else deadline
    args.directory.mkdir(parents=True, exist_ok=False)
    source_ref, config_ref = binding(__file__), binding(args.configuration)
    initial = {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False, "source": source_ref,
               "configuration": config_ref, "mode": args.mode, "maximum_seconds": maximum,
               "graph_constructed": False, "whole_component_excluded": False}
    save(args.directory / "owned-start.json", initial)
    command = [sys.executable, str(Path(__file__).resolve()), "_" + args.mode,
               "--configuration", str(args.configuration.resolve()), "--directory", str(args.directory.resolve()),
               "--deadline", str(worker_deadline)]
    if args.mode == "run":
        assert args.preparation is not None and args.gate is not None and args.gate_sha256 is not None
        command += ["--preparation", str(args.preparation.resolve()), "--gate", str(args.gate.resolve()),
                    "--gate-sha256", args.gate_sha256]
    owner = dict(initial)
    try:
        supervisor = bound_module("strengthened_query_owned_supervisor", cfg["sources"]["supervisor"])
        supervision = supervisor.supervise(command, args.directory, deadline)
        save(args.directory / "owned-supervision.json", supervision)
        owner.update(status=supervision["status"], supervision=supervision,
                     preliminary_receipt=binding(args.directory / "owned-start.json"),
                     supervision_receipt=binding(args.directory / "owned-supervision.json"))
        report_path = args.directory / ("report.json" if args.mode == "prepare" else "result.json")
        if (supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
                and supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
                and time.monotonic() <= deadline):
            report = json.loads(report_path.read_bytes())
            same_reference(report["source"], source_ref)
            same_reference(report["configuration"], config_ref)
            assert report["variables"] == VARIABLES and report["rows"] == ROWS
            assert report["graph_constructed"] is False and report["whole_component_excluded"] is False
            if args.mode == "prepare":
                assert report["status"] == "PASS_TRIANGLE_GAP_QUERY_PREFLIGHT"
                assert report["production_solve_calls"] == report["optimizer_calls"] == 0 and report["CpSolver_constructed"] is False
            else:
                assert report["production_solve_calls"] in (0, 1) and report["optimizer_calls"] == report["production_solve_calls"]
                assert report["status"] not in ("UNKNOWN_BEFORE_NATIVE_CALL", "NATIVE_CALL_ACTIVE", "NATIVE_TEXT_SAVED",
                                                "NATIVE_VECTORS_SAVED", "NATIVE_RESPONSE_PARSED")
                same_reference(report["root_gate"], binding(args.gate))
                assert report["root_gate"]["sha256"] == args.gate_sha256
            owner.update(status=report["status"], report=binding(report_path), report_accepted=True,
                         production_solve_calls=report["production_solve_calls"], optimizer_calls=report["optimizer_calls"],
                         CpSolver_constructed=report["CpSolver_constructed"])
    except Exception as error:
        owner.update(status="ERROR_QUERY_OWNER", error={"type": type(error).__name__, "message": str(error),
                                                       "traceback": traceback.format_exc()}, report_accepted=False)
    owner.update(schema="conway99.f0.triangle-gap-query-owner.v1",
                 seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - deadline))
    if owner["deadline_overrun_seconds"]:
        owner.update(status="UNKNOWN_HARD_DEADLINE", report_accepted=False)
    save(args.directory / "owner.json", owner)
    print(json.dumps(owner, sort_keys=True), flush=True)
    if not owner["report_accepted"]:
        raise SystemExit(1)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "_prepare", "_run"))
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--gate-sha256")
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    if args.mode.startswith("_"):
        assert args.deadline is not None
        worker(args)
    else:
        owned(args)
