"""Independently replay one bounded triangle-incidence model query.

Decode only immutable protobuf messages. Do not import a producer, transport
helper, CpModel, CpSolver, or native solver module. Recompute every returned
vector's variable domains and complete linear row activities with Python ints.
"""
import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import re
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
BASE_RAW_SHA = "2961c95ce21c39f8ea8bda29ed3ac98c5075b921dedc96f71035f1b90f77ddb6"
BASE_RAW_BYTES, BASE_VARIABLES, BASE_ROWS = 39306083, 80730, 297470
ORIGINAL_EDGE_STOP = 68934
VARIABLES, ROWS = 80730, 300795
FAMILY_ORDER = ["side_edge", "local_selector", "global_target_total"]
FAMILY_COUNTS = dict(zip(FAMILY_ORDER, [2904, 420, 1]))
FAMILY_TERMS = dict(zip(FAMILY_ORDER, [10320, 16512, 84]))
EDGE_SHA = "411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb"
MODEL_SOURCE_SHA = "29d289399089b5e56e94b7991cd0c29e2cc530e890f78f27583cb48652824199"
MODEL_COLD_SHA = "1bf43879126625fccd62f1aa3bd628af9a53089ea7cfa048607be55d027090ec"
MODEL_CI_SHA = "ab120aaa21b22e0e21e425eb1e8612399c5ab2aa87f5190253b42f7099b9e1a7"
MODEL_COLD_OWNER_SCHEMA = "conway99.f0.triangle-incidence-external-cold-owner.v1"
MODEL_COLD_OWNER_STATUS = "PASS_TRIANGLE_INCIDENCE_EXTERNAL_COLD_REPLAY"
MODEL_ROOT_SCHEMA = "conway99.f0.triangle-incidence-native-root-acceptance.v1"
MODEL_ROOT_STATUS = "ROOT_ACCEPTS_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_MODEL_AND_INDEPENDENT_COLD"
BASE_SOURCE_SHA = "5a1e8026683a7782fce6ec2a2947748356ac9cd5adf32dd2a0663b0dd60bfca2"
SUPERVISOR_SHA = "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3"
LIMITS = {"solver_seconds": 600, "native_allowance_seconds": 610, "owner_seconds": 720,
          "preparation_seconds": 60, "preparation_owner_seconds": 75, "finalization_reserve_seconds": 60}
PARAMETERS = {"num_search_workers": 4, "num_full_subsolvers": 3,
              "subsolvers": ["no_lp", "quick_restart_no_lp", "portfolio_no_lp"],
              "random_seed": 0, "cp_model_presolve": True,
              "cp_model_probing_level": 0, "linearization_level": 0, "symmetry_level": 0,
              "max_time_in_seconds": 600.0, "log_search_progress": True,
              "log_to_stdout": True, "log_to_response": True}
MAXIMUM_SECONDS = 120


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def read(ref):
    path = (ROOT / ref["path"]).resolve()
    path.relative_to(ROOT)
    raw = path.read_bytes()
    assert sha(raw) == ref["sha256"]
    assert "bytes" not in ref or len(raw) == ref["bytes"]
    return raw


def reject_constant(value):
    raise ValueError("nonfinite JSON number: " + value)


def value(ref):
    raw = read(ref)
    if ref["path"].endswith(".gz"):
        raw = gzip.decompress(raw)
    return json.loads(raw, parse_constant=reject_constant)


def same_ref(first, second):
    assert first["path"] == second["path"] and first["sha256"] == second["sha256"]
    for ref in (first, second):
        if "bytes" in ref:
            assert (ROOT / ref["path"]).stat().st_size == ref["bytes"]


def save(path, item):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(canonical(item) + b"\n")


def clock(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("independent triangle incidence query replay deadline")


def native_absent():
    assert "ortools.sat.python.cp_model" not in sys.modules
    assert "ortools.sat.python.cp_model_helper" not in sys.modules


def interval_contains(domain, number):
    assert len(domain) > 0 and len(domain) % 2 == 0
    offset = 0
    while offset < len(domain):
        assert domain[offset] <= domain[offset + 1]
        if domain[offset] <= number and number <= domain[offset + 1]:
            return True
        offset += 2
    return False


def exact_vector(model, point, deadline):
    """Independent indexed loops, with no imported producer or NumPy arithmetic."""
    result = {"status": "REJECTED_RETURNED_VECTOR", "values": len(point), "variables": len(model.variables),
              "all_values_exact_Python_int": all(type(x) is int for x in point),
              "variable_domains_checked": 0, "linear_rows_checked": 0,
              "domain_violations": [], "linear_row_violations": []}
    if not result["all_values_exact_Python_int"] or len(point) != len(model.variables):
        return result, []
    for j in range(len(point)):
        if not interval_contains(model.variables[j].domain, point[j]):
            result["domain_violations"].append(j)
        result["variable_domains_checked"] += 1
    activities = []
    for r in range(len(model.constraints)):
        if r % 4096 == 0:
            clock(deadline)
        constraint = model.constraints[r]
        assert constraint.WhichOneof("constraint") == "linear" and len(constraint.enforcement_literal) == 0
        linear = constraint.linear
        assert len(linear.vars) == len(linear.coeffs)
        total = 0
        for k in range(len(linear.vars)):
            j, coefficient = linear.vars[k], linear.coeffs[k]
            assert 0 <= j < len(point)
            total += coefficient * point[j]
        activities.append(total)
        if not interval_contains(linear.domain, total):
            result["linear_row_violations"].append(r)
        result["linear_rows_checked"] += 1
    if len(result["domain_violations"]) == 0 and len(result["linear_row_violations"]) == 0:
        result["status"] = "PASS_EXACT_INTEGER_VECTOR_ALL_DOMAINS_AND_ROWS"
    return result, activities


def terminal_status(status, primary, checks, overrun):
    # Re-derive the terminal convention; this does not call the query source.
    if overrun > 0:
        answer = "UNKNOWN_NATIVE_BUDGET_OVERRUN"
    elif any(c["status"] != "PASS_EXACT_INTEGER_VECTOR_ALL_DOMAINS_AND_ROWS" for c in checks):
        answer = "ERROR_EXACT_RETURNED_VECTOR_CHECK_FAILED"
    elif status in {"INFEASIBLE", "MODEL_INVALID"} and len(checks) != 0:
        answer = "ERROR_NATIVE_STATUS_VECTOR_CONTRADICTION"
    elif status == "FEASIBLE" or status == "OPTIMAL":
        answer = "EXACT_BOOLEAN_MODEL_VECTOR_AWAITING_INDEPENDENT_COLD" if len(primary) != 0 else "ERROR_NATIVE_SAT_WITHOUT_VECTOR"
    else:
        answers = {"INFEASIBLE": "UNPROVED_NATIVE_INFEASIBLE",
                   "MODEL_INVALID": "ERROR_NATIVE_MODEL_INVALID",
                   "UNKNOWN": "UNKNOWN_TRIANGLE_INCIDENCE_NATIVE"}
        assert status in answers
        answer = answers[status]
    return answer


def supervisor_pass(owner, limit):
    assert owner["report_accepted"] is True and owner["maximum_seconds"] == limit
    assert type(owner["seconds"]) in (int, float) and math.isfinite(owner["seconds"]) and 0 <= owner["seconds"] <= limit
    assert owner.get("deadline_overrun_seconds", 0) == 0
    supervision = owner["supervision"]
    assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
    assert supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
    assert 0 <= supervision["seconds"] <= owner["seconds"]


def read_model(cfg):
    """Bind the accepted triangle-incidence model without importing its constructor."""
    from ortools.sat import cp_model_pb2 as pb
    assert set(cfg["inputs"]) == {"model", "model_configuration", "model_preparation",
                                 "model_preparation_owner", "model_cold", "model_cold_owner",
                                 "model_root_acceptance"}
    assert set(cfg["sources"]) == {"base", "supervisor", "model_producer", "model_cold", "model_ci"}
    for name, expected in (("model_producer", MODEL_SOURCE_SHA), ("model_cold", MODEL_COLD_SHA),
                           ("model_ci", MODEL_CI_SHA), ("base", BASE_SOURCE_SHA), ("supervisor", SUPERVISOR_SHA)):
        assert cfg["sources"][name]["sha256"] == expected
        read(cfg["sources"][name])
    assert cfg["variables"] == VARIABLES and cfg["rows"] == ROWS
    assert type(cfg["model_raw_sha256"]) is str and re.fullmatch("[0-9a-f]{64}", cfg["model_raw_sha256"])
    assert type(cfg["model_raw_bytes"]) is int and cfg["model_raw_bytes"] > 0
    records = {name: value(ref) for name, ref in cfg["inputs"].items() if name != "model"}
    prep, prep_owner, cold, cold_owner, root = [records[name] for name in
        ("model_preparation", "model_preparation_owner", "model_cold", "model_cold_owner", "model_root_acceptance")]
    model_cfg = records["model_configuration"]
    assert model_cfg["schema"] == "conway99.f0.triangle-incidence-native-configuration.v1"
    assert model_cfg["source_sha256"] == MODEL_SOURCE_SHA
    same_ref(model_cfg["sources"]["checker"], cfg["sources"]["model_cold"])
    same_ref(model_cfg["sources"]["base"], cfg["sources"]["base"])
    same_ref(model_cfg["sources"]["supervisor"], cfg["sources"]["supervisor"])
    assert model_cfg["optimizer_calls"] == 0 and model_cfg["native_query_authorized"] is False
    assert model_cfg["independent_complete_protobuf_replay_required"] is True
    headers = [
        (prep, "conway99.f0.triangle-incidence-native-preparation.v1", "PASS_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_PREPARATION"),
        (prep_owner, "conway99.f0.triangle-incidence-native-owner.v1", "PASS_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_PREPARATION"),
        (cold, "conway99.f0.triangle-incidence-independent-cold.v1", "PASS_INDEPENDENT_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_MODEL"),
        (cold_owner, MODEL_COLD_OWNER_SCHEMA, MODEL_COLD_OWNER_STATUS),
        (root, MODEL_ROOT_SCHEMA, MODEL_ROOT_STATUS),
    ]
    for record, schema, status in headers:
        assert record["schema"] == schema and record["status"] == status and record["optimizer_calls"] == 0
    assert root["native_query_authorized_by_this_receipt"] is False
    assert root["complete_original_parent_bytes_recovered"] is True
    for record, source in ((prep, "model_producer"), (prep_owner, "model_producer"),
                           (cold, "model_cold"), (cold_owner, "model_cold")):
        same_ref(record["source"], cfg["sources"][source])
        same_ref(record["configuration"], cfg["inputs"]["model_configuration"])
        assert record["CpSolver_constructed"] is False
    same_ref(prep_owner["report"], cfg["inputs"]["model_preparation"])
    same_ref(cold_owner["report"], cfg["inputs"]["model_cold"])
    same_ref(cold["preparation_report"], cfg["inputs"]["model_preparation"])
    same_ref(cold["preparation_owner"], cfg["inputs"]["model_preparation_owner"])
    for field, alias in (("configuration", "model_configuration"), ("preparation", "model_preparation"),
                         ("independent_cold", "model_cold"), ("model_archive", "model")):
        same_ref(root[field], cfg["inputs"][alias])
    same_ref(root["owners"]["preparation"], cfg["inputs"]["model_preparation_owner"])
    same_ref(root["owners"]["independent_cold"], cfg["inputs"]["model_cold_owner"])
    supervisor_pass(prep_owner, 135)
    supervisor_pass(cold_owner, 135)
    assert prep_owner["mode"] == "prepare" and cold_owner["mode"] == "replay"
    assert prep["maximum_seconds"] == cold["maximum_seconds"] == 120
    assert prep["CpModel_constructed"] is True and prep["native_model_builds"] == 1
    assert prep["native_optimizer_constructed"] is False and prep["native_query_run"] is False
    assert cold["CpModel_constructed"] is False and cold["native_optimizer_constructed"] is False
    assert cold["native_model_builds"] == 0 and cold["native_query_run"] is False
    assert cold["original_extractor_or_literal_producer_imported"] is False
    assert cold["native_transport_or_preparation_producer_imported"] is False
    assert cold["native_query_authorized_by_this_report"] is False
    assert prep["inputs"] == cold["inputs"] == model_cfg["inputs"]
    assert prep["authorities"] == model_cfg["authorities"]
    assert prep["layout"] == cold["layout"] == model_cfg["layout"]
    assert prep["family_order"] == cold["family_order"] == FAMILY_ORDER
    assert prep["family_counts"] == cold["family_counts"] == FAMILY_COUNTS
    assert prep["family_terms"] == cold["family_terms"] == FAMILY_TERMS
    for field in ("row_keys_sha256", "family_row_keys_sha256", "family_row_jsonl_sha256", "literal_hashes"):
        assert prep[field] == cold[field]
    assert cold["base_restoration_sha256"] == BASE_RAW_SHA and cold["base_restoration_bytes"] == BASE_RAW_BYTES
    assert cold["parent_variables"] == BASE_VARIABLES and cold["parent_rows"] == BASE_ROWS
    assert cold["new_variables"] == cold["replaced_rows"] == 0
    assert cold["appended_rows"] == 3325 and cold["appended_terms"] == sum(FAMILY_TERMS.values()) == 26916
    assert cold["total_terms"] == prep["total_terms"] == 3337296
    assert prep["term_change"] == 26916 and cold["parent_total_terms"] == prep["parent_total_terms"] == 3310380
    for flag in ("complete_original_parent_bytes_recovered", "all_original_variable_and_constraint_messages_preserved",
                 "all_appended_complete_constraint_messages_independently_checked",
                 "complete_row_origins_and_lossless_restoration_checked",
                 "all_side_and_nonempty_local_proposals_retained",
                 "global_target_total_row_independently_checked",
                 "all_seven_literal_hashes_rederived_from_native_AND_meanings"):
        assert cold[flag] is True
    assert cold["original_failed_extractor_execution_accepted"] is False
    assert cold["original_extractor_overrun_waived"] is False
    assert cold["Boolean_implication_classification_used_to_prune"] is False
    same_ref(prep["independent_literal_root_acceptance"], model_cfg["inputs"]["incidence_root_acceptance"])
    same_ref(cold["independent_literal_root_acceptance"], model_cfg["inputs"]["incidence_root_acceptance"])
    same_ref(prep["target_total_root_acceptance"], model_cfg["inputs"]["target_total_root_acceptance"])
    same_ref(cold["target_total_root_acceptance"], model_cfg["inputs"]["target_total_root_acceptance"])
    assert prep["preservation"] == cold["preservation"] and prep["restoration"] == cold["restoration"]
    assert prep["incidence_check"] == cold["incidence_check"]
    assert cold["incidence_check"]["complete_edges"] == 6300
    assert cold["incidence_check"]["existing_AND_constraints"] == 21456
    assert cold["incidence_check"]["existing_target_equalities"] == 84
    assert cold["incidence_check"]["singleton_side_edges"] == 3312
    assert cold["target_total_check"]["all_seven_structural_conditions_rechecked"] is True
    assert cold["target_total_check"]["Boolean_bound"] == 12
    assert cold["target_total_check"]["original_Gram_rows_rechecked"] == 18
    assert cold["target_total_check"]["original_endpoint_rows_rechecked"] == 168
    for record in (prep, cold, root):
        assert record["variables"] == VARIABLES and record["rows"] == ROWS
        assert record["model_raw_sha256"] == cfg["model_raw_sha256"]
        assert record["model_raw_bytes"] == cfg["model_raw_bytes"]
    for record in (prep, cold):
        same_ref(record["artifacts"]["model_archive"], cfg["inputs"]["model"])
    archive = read(cfg["inputs"]["model"])
    assert len(archive) == prep["model"]["archive_bytes"] == cold["model_archive_bytes"]
    assert sha(archive) == prep["model"]["archive_sha256"] == cold["model_archive_sha256"]
    raw = gzip.decompress(archive)
    assert len(raw) == cfg["model_raw_bytes"] == prep["model"]["raw_bytes"]
    assert sha(raw) == cfg["model_raw_sha256"] == prep["model"]["raw_sha256"]
    assert sha(pb.DESCRIPTOR.serialized_pb) == cfg["runtime"]["model_schema_sha256"]
    assert prep["runtime"]["model_schema_sha256"] == cfg["runtime"]["model_schema_sha256"]
    model = pb.CpModelProto()
    model.ParseFromString(raw)
    assert model.SerializeToString() == raw
    assert len(model.variables) == VARIABLES and len(model.constraints) == ROWS
    assert set(f.name for f, _ in model.ListFields()) <= {"name", "variables", "constraints"}
    assert all(c.WhichOneof("constraint") == "linear" and not c.enforcement_literal for c in model.constraints)
    edges = []
    for j in range(540, ORIGINAL_EDGE_STOP):
        variable = model.variables[j]
        words = variable.name.split("_")
        assert len(words) == 4 and words[:2] == ["shared", "edge"]
        a, b = int(words[2]), int(words[3])
        assert 0 <= a < b < 480 and variable.name == "shared_edge_%03d_%03d" % (a, b)
        assert list(variable.domain) == [0, 1]
        edges.append([a, b])
    assert sha(canonical(edges)) == EDGE_SHA and len(edges) == 68394
    assert all(list(model.variables[j].domain) == [0, 1] for j in range(480))
    return model, edges


def check_runtime_and_parameters(record, cfg):
    from google.protobuf import text_format
    from ortools.sat import cp_model_pb2 as pb, sat_parameters_pb2 as sp
    runtime = cfg["runtime"]
    assert record["all_explicit_parameters"] == PARAMETERS == cfg["parameters"]
    assert record["runtime"] == runtime and record["native_symmetry_disabled_explicitly"] is True
    assert record["defaults_preserved_in_descriptor"] is True
    assert importlib.metadata.version("ortools") == runtime["ortools_version"] == "9.15.6755"
    assert importlib.metadata.version("protobuf") == runtime["protobuf_version"] == "6.33.6"
    assert sha(pb.DESCRIPTOR.serialized_pb) == runtime["model_schema_sha256"]
    distribution = importlib.metadata.distribution("ortools")
    python_files = [f for f in distribution.files if str(f) == "ortools/sat/python/cp_model.py"]
    native_files = [f for f in distribution.files
                    if str(f).startswith("ortools/sat/python/cp_model_helper.") and str(f).endswith(".so")]
    assert len(python_files) == len(native_files) == 1
    assert sha(distribution.locate_file(python_files[0]).read_bytes()) == runtime["cp_model_sha256"]
    assert sha(distribution.locate_file(native_files[0]).read_bytes()) == runtime["native_helper_sha256"]
    descriptor = read(record["parameter_schema"])
    assert descriptor == sp.DESCRIPTOR.serialized_pb and sha(descriptor) == runtime["parameter_schema_sha256"]
    expected = sp.SatParameters()
    for field, setting in PARAMETERS.items():
        if field == "subsolvers":
            expected.subsolvers.extend(setting)
        else:
            setattr(expected, field, setting)
    text_message, wire_message = sp.SatParameters(), sp.SatParameters()
    text_format.Parse(read(record["parameters_text"]).decode("utf-8"), text_message)
    wire = read(record["parameters_wire"])
    wire_message.ParseFromString(wire)
    assert text_message.SerializeToString() == wire_message.SerializeToString() == wire == expected.SerializeToString()
    native_absent()


def controls():
    from ortools.sat import cp_model_pb2 as pb
    deadline = time.monotonic() + 10
    toy = pb.CpModelProto()
    for domain in ([0, 1], [-3, -1, 1, 3], [0, 1]):
        toy.variables.add().domain.extend(domain)
    large = (1 << 54) + 3
    for variables, coefficients, domain in [
            ([0, 2], [1, -1], [0, 0]), ([1], [-large], [-2 * large, -2 * large]), ([], [], [0, 0])]:
        row = toy.constraints.add().linear
        row.vars.extend(variables)
        row.coeffs.extend(coefficients)
        row.domain.extend(domain)
    good, activities = exact_vector(toy, [1, 2, 1], deadline)
    assert good["status"] == "PASS_EXACT_INTEGER_VECTOR_ALL_DOMAINS_AND_ROWS"
    assert activities == [0, -2 * large, 0]
    assert exact_vector(toy, [1, 0, 1], deadline)[0]["domain_violations"] == [1]
    assert exact_vector(toy, [0, 2, 1], deadline)[0]["linear_row_violations"] == [0]
    assert exact_vector(toy, [1, 2.0, 1], deadline)[1] == []
    assert exact_vector(toy, [True, 2, 1], deadline)[1] == []
    assert exact_vector(toy, [1, 2], deadline)[0]["linear_rows_checked"] == 0
    from google.protobuf import text_format
    for status in (pb.UNKNOWN, pb.MODEL_INVALID, pb.FEASIBLE, pb.INFEASIBLE, pb.OPTIMAL):
        expected = pb.CpSolverResponse(status=status, wall_time=0.25)
        if status in (pb.FEASIBLE, pb.OPTIMAL):
            expected.solution.extend([large, -large, 0])
            expected.additional_solutions.add().values.extend([-large, large, 1])
        restored = pb.CpSolverResponse()
        text_format.Parse(text_format.MessageToString(expected), restored)
        assert restored.SerializeToString() == expected.SerializeToString()
    passed, failed = [good], [exact_vector(toy, [0, 2, 1], deadline)[0]]
    assert terminal_status("FEASIBLE", [1], passed, 0) == "EXACT_BOOLEAN_MODEL_VECTOR_AWAITING_INDEPENDENT_COLD"
    assert terminal_status("OPTIMAL", [], [], 0) == "ERROR_NATIVE_SAT_WITHOUT_VECTOR"
    assert terminal_status("INFEASIBLE", [], [], 0) == "UNPROVED_NATIVE_INFEASIBLE"
    assert terminal_status("UNKNOWN", [], [], 0) == "UNKNOWN_TRIANGLE_INCIDENCE_NATIVE"
    assert terminal_status("MODEL_INVALID", [], [], 0) == "ERROR_NATIVE_MODEL_INVALID"
    assert terminal_status("INFEASIBLE", [1], passed, 0) == "ERROR_NATIVE_STATUS_VECTOR_CONTRADICTION"
    assert terminal_status("FEASIBLE", [1], failed, 0) == "ERROR_EXACT_RETURNED_VECTOR_CHECK_FAILED"
    assert terminal_status("FEASIBLE", [1], passed, 0.1) == "UNKNOWN_NATIVE_BUDGET_OVERRUN"
    from ortools.sat import sat_parameters_pb2 as sp
    explicit = sp.SatParameters()
    for field, setting in PARAMETERS.items():
        if field == "subsolvers":
            explicit.subsolvers.extend(setting)
        else:
            setattr(explicit, field, setting)
    assert list(explicit.subsolvers) == ["no_lp", "quick_restart_no_lp", "portfolio_no_lp"]
    assert explicit.num_full_subsolvers == 3 and explicit.num_search_workers == 4
    repeated_text, repeated_wire = sp.SatParameters(), sp.SatParameters()
    text_format.Parse(text_format.MessageToString(explicit), repeated_text)
    repeated_wire.ParseFromString(explicit.SerializeToString())
    assert repeated_text.SerializeToString() == repeated_wire.SerializeToString() == explicit.SerializeToString()
    changed_order = sp.SatParameters()
    changed_order.CopyFrom(explicit)
    del changed_order.subsolvers[:]
    changed_order.subsolvers.extend(reversed(PARAMETERS["subsolvers"]))
    assert changed_order.SerializeToString() != explicit.SerializeToString()
    native_absent()
    return {"status": "PASS_TRIANGLE_INCIDENCE_QUERY_INDEPENDENT_INTEGER_AND_RESPONSE_CONTROLS",
            "large_integer": large, "disconnected_domain_boolean_float_length_and_row_controls_checked": True,
            "signed_and_empty_rows_checked": True, "response_statuses_checked": 5,
            "primary_and_additional_integer_vectors_checked": True, "classification_controls": 8,
            "all_explicit_parameter_text_wire_roundtrip_checked": True,
            "repeated_subsolver_order_and_full_worker_count_checked": True,
            "producer_imports": 0, "native_imports": 0, "optimizer_calls": 0,
            "CpModel_constructed": False, "CpSolver_constructed": False}


def replay(args):
    started = time.monotonic()
    deadline = started + MAXIMUM_SECONDS
    config_ref = binding(args.configuration)
    assert config_ref["sha256"] == args.configuration_sha256
    cfg = value(config_ref)
    assert cfg["schema"] == "conway99.f0.triangle-incidence-query-configuration.v1"
    assert cfg["parameters"] == PARAMETERS and cfg["limits"] == LIMITS
    assert cfg["maximum_native_calls"] == 1 and cfg["automatic_retries"] == 0
    assert cfg["native_query_authorized_by_configuration_alone"] is False
    for ref in cfg["sources"].values():
        read(ref)
    gate_ref = binding(args.gate)
    assert gate_ref["sha256"] == args.gate_sha256
    gate = value(gate_ref)
    assert gate["status"] == "AUTHORIZE_ONE_TRIANGLE_INCIDENCE_MODEL_QUERY"
    same_ref(gate["terminal_cold_source"], binding(__file__))
    same_ref(gate["configuration"], config_ref)
    assert gate["source"]["sha256"] == cfg["source_sha256"]
    read(gate["source"])
    assert gate["limits"] == LIMITS and gate["parameters"] == PARAMETERS
    assert gate["maximum_native_calls"] == 1 and gate["automatic_retries"] == 0
    assert gate["independent_terminal_cold_required"] is True and gate["model_raw_sha256"] == cfg["model_raw_sha256"]
    same_ref(gate["model_cold"], cfg["inputs"]["model_cold"])
    model, edges = read_model(cfg)
    clock(deadline)
    result_ref, owner_ref = binding(args.directory / "result.json"), binding(args.directory / "owner.json")
    assert result_ref["sha256"] == args.result_sha256 and owner_ref["sha256"] == args.owner_sha256
    result, owner = value(result_ref), value(owner_ref)
    assert result["schema"] == "conway99.f0.triangle-incidence-query-terminal.v1"
    assert owner["schema"] == "conway99.f0.triangle-incidence-query-owner.v1"
    supervisor_pass(owner, LIMITS["owner_seconds"])
    same_ref(owner["report"], result_ref)
    assert owner["mode"] == "run" and owner["status"] == result["status"]
    for record in (result, owner):
        same_ref(record["source"], gate["source"])
        same_ref(record["configuration"], config_ref)
        assert record["graph_constructed"] is False and record["whole_component_excluded"] is False
    assert canonical(value(owner["supervision_receipt"])) == canonical(owner["supervision"])
    initial = value(owner["preliminary_receipt"])
    assert initial["status"] == "UNKNOWN_BEFORE_CHILD" and initial["report_accepted"] is False and initial["mode"] == "run"
    same_ref(initial["source"], gate["source"])
    same_ref(initial["configuration"], config_ref)
    same_ref(result["root_gate"], gate_ref)
    same_ref(result["preflight_report"], gate["preflight_report"])
    same_ref(result["preflight_owner"], gate["preflight_owner"])
    preflight, pre_owner = value(gate["preflight_report"]), value(gate["preflight_owner"])
    assert preflight["schema"] == "conway99.f0.triangle-incidence-query-terminal.v1"
    assert pre_owner["schema"] == "conway99.f0.triangle-incidence-query-owner.v1"
    supervisor_pass(pre_owner, LIMITS["preparation_owner_seconds"])
    assert preflight["status"] == pre_owner["status"] == "PASS_TRIANGLE_INCIDENCE_QUERY_PREFLIGHT"
    assert pre_owner["mode"] == "prepare"
    same_ref(pre_owner["report"], gate["preflight_report"])
    for record in (preflight, pre_owner):
        same_ref(record["source"], gate["source"])
        same_ref(record["configuration"], config_ref)
        assert record["production_solve_calls"] == record["optimizer_calls"] == 0 and record["CpSolver_constructed"] is False
    same_ref(preflight["model_cold"], cfg["inputs"]["model_cold"])
    assert preflight["model_raw_sha256"] == result["model_raw_sha256"] == cfg["model_raw_sha256"]
    assert preflight["model_raw_bytes"] == result["model_raw_bytes"] == cfg["model_raw_bytes"]
    assert result["variables"] == preflight["variables"] == VARIABLES and result["rows"] == preflight["rows"] == ROWS
    assert canonical(result["inputs"]) == canonical(cfg["inputs"]) and result["limits"] == LIMITS
    assert result["independent_terminal_cold_required"] is True and result["native_INFEASIBLE_is_unproved"] is True
    assert result["original_pair_caps_checked"] is False and result["second_component_completion_checked"] is False
    for report in (preflight, result):
        transport = report["native_transport"]
        assert transport["complete_byte_comparison"] is True and transport["public_parse_return"] is True
        assert transport["native_validation"] == "" and transport["native_raw_sha256"] == cfg["model_raw_sha256"]
        assert transport["native_raw_bytes"] == cfg["model_raw_bytes"] and transport["optimizer_calls"] == 0
        assert transport["CpSolver_constructed"] is False
    check_runtime_and_parameters(result["parameters"], cfg)
    assert preflight["parameters"]["all_explicit_parameters"] == PARAMETERS
    assert preflight["parameters"]["runtime"] == cfg["runtime"]
    for key in ("parameters_text", "parameters_wire", "parameter_schema"):
        assert read(result["parameters"][key]) == read(preflight["parameters"][key])
    native_model_path = args.directory / "model.pb"
    assert native_model_path.stat().st_size == cfg["model_raw_bytes"] and sha(native_model_path.read_bytes()) == cfg["model_raw_sha256"]
    calls = result["production_solve_calls"]
    assert type(calls) is int and calls in (0, 1)
    assert owner["production_solve_calls"] == owner["optimizer_calls"] == result["optimizer_calls"] == calls
    assert owner["CpSolver_constructed"] is result["CpSolver_constructed"] is bool(calls)
    vector_checks = []
    if calls == 0:
        assert result["status"] == "UNKNOWN_INSUFFICIENT_REMAINING_OWNER_BUDGET_NO_CALL"
        assert result["remaining_owner_before_call"] < LIMITS["native_allowance_seconds"] + LIMITS["finalization_reserve_seconds"]
        assert result["returned_vectors"] == [] and result["all_returned_vectors_checked"] is False
        assert not any((args.directory / name).exists() for name in
                       ("response-native.pbtxt", "response-reconstructed.pb", "native-vectors.json", "candidate.json"))
    else:
        assert result["solver_clock_seconds"] == LIMITS["solver_seconds"]
        assert result["native_allowance_seconds"] == LIMITS["native_allowance_seconds"]
        assert result["remaining_owner_before_call"] >= LIMITS["native_allowance_seconds"] + LIMITS["finalization_reserve_seconds"]
        elapsed = result["native_seconds"]
        assert type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed <= owner["supervision"]["seconds"]
        assert result["native_overrun_seconds"] == max(0, elapsed - LIMITS["native_allowance_seconds"])
        assert result["wire_reconstructed_from_native_text"] is True and result["original_native_binary_export_available"] is False
        from google.protobuf import text_format
        from ortools.sat import cp_model_pb2 as pb
        text_message, wire_message = pb.CpSolverResponse(), pb.CpSolverResponse()
        text_format.Parse(read(result["response_native_text"]).decode("utf-8"), text_message)
        wire = read(result["response_reconstructed_wire"])
        wire_message.ParseFromString(wire)
        assert wire == wire_message.SerializeToString() == text_message.SerializeToString()
        snapshot = value(result["native_vectors"])
        assert set(snapshot) == {"native_status", "primary", "additional"}
        assert snapshot["native_status"] == result["native_status"] == pb.CpSolverStatus.Name(text_message.status)
        assert canonical(snapshot["primary"]) == canonical(list(text_message.solution))
        assert canonical(snapshot["additional"]) == canonical([list(item.values) for item in text_message.additional_solutions])
        assert result["native_reported_wall_seconds"] == text_message.wall_time
        read(result["response_stats"])
        vectors = [("candidate", list(text_message.solution))] if text_message.solution else []
        vectors.extend(("additional-candidate-%03d" % i, list(item.values)) for i, item in enumerate(text_message.additional_solutions))
        actual_files = {p.name for p in args.directory.iterdir()
                        if re.fullmatch(r"(candidate|additional-candidate-[0-9]+)\.json", p.name)}
        assert actual_files == {name + ".json" for name, _ in vectors}
        assert len(result["returned_vectors"]) == len(result["native_vector_files"]) == len(vectors)
        checks = []
        for k, (name, point) in enumerate(vectors):
            record = result["returned_vectors"][k]
            assert record["name"] == name
            expected_ref = binding(args.directory / (name + ".json"))
            same_ref(record["candidate"], expected_ref)
            same_ref(result["native_vector_files"][k], expected_ref)
            saved_point = value(record["candidate"])
            assert type(saved_point) is list and all(type(x) is int for x in saved_point)
            assert canonical(saved_point) == canonical(point)
            assert record["candidate_values_sha256"] == sha(canonical(point)) and record["values"] == len(point)
            checked, activities = exact_vector(model, point, deadline)
            assert canonical(value(record["check"])) == canonical(checked)
            assert record["check_status"] == checked["status"]
            raw_activities = gzip.decompress(read(record["activities"]))
            assert raw_activities == canonical(activities)
            assert len(raw_activities) == record["activities_raw_bytes"] and sha(raw_activities) == record["activities_raw_sha256"]
            checks.append(checked)
            vector_checks.append({"name": name, "candidate": record["candidate"], "status": checked["status"],
                                  "variable_domains_checked": checked["variable_domains_checked"],
                                  "linear_rows_checked": checked["linear_rows_checked"],
                                  "all_saved_activities_equal": True})
            if name == "candidate" and checked["status"] == "PASS_EXACT_INTEGER_VECTOR_ALL_DOMAINS_AND_ROWS":
                assert value(result["selection"]) == [i for i in range(480) if point[i] == 1]
                selected_edges = [e for e in range(68394) if point[540 + e] == 1]
                assert value(result["selected_edges"]) == {"edge_ids": selected_edges, "edges": [edges[e] for e in selected_edges]}
        assert result["all_returned_vectors_checked"] is True
        derived_status = terminal_status(snapshot["native_status"], snapshot["primary"], checks, result["native_overrun_seconds"])
        assert derived_status == result["status"]
    native_absent()
    clock(deadline)
    return {"schema": "conway99.f0.triangle-incidence-query-independent-cold.v1",
            "status": "PASS_INDEPENDENT_TRIANGLE_INCIDENCE_QUERY_TERMINAL_REPLAY",
            "source": binding(__file__), "configuration": config_ref, "root_gate": gate_ref,
            "query_result": result_ref, "query_owner": owner_ref, "query_source": gate["source"],
            "model_cold": cfg["inputs"]["model_cold"], "model_root_acceptance": cfg["inputs"]["model_root_acceptance"],
            "model_raw_sha256": cfg["model_raw_sha256"], "model_raw_bytes": cfg["model_raw_bytes"], "variables": VARIABLES, "rows": ROWS,
            "native_answer_classification": result["status"], "native_status": result.get("native_status"),
            "query_native_calls": calls, "query_native_seconds": result.get("native_seconds"),
            "query_native_overrun_seconds": result.get("native_overrun_seconds", 0),
            "returned_vectors_independently_checked": len(vector_checks), "vectors": vector_checks,
            "complete_parameters_checked": True, "complete_response_messages_checked": calls == 1,
            "all_available_native_vectors_and_saved_row_activities_checked": True,
            "graph_constructed": False, "whole_component_excluded": False,
            "original_pair_caps_checked": False, "second_component_completion_checked": False,
            "native_INFEASIBLE_is_unproved": True, "producer_imports": 0, "native_imports": 0,
            "CpModel_constructed": False, "CpSolver_constructed": False, "optimizer_calls": 0,
            "maximum_seconds": MAXIMUM_SECONDS, "seconds_before_serialization": time.monotonic() - started,
            "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def main(args):
    started = time.monotonic()
    try:
        report = controls() if args.mode == "controls" else replay(args)
        save(args.output, report)
        limit = 10 if args.mode == "controls" else MAXIMUM_SECONDS
        if time.monotonic() - started >= limit:
            raise TimeoutError("complete independent replay and serialization exceeded bound")
        native_absent()
    except Exception as error:
        error_path = args.output.with_name(args.output.name + ".error.json")
        if not error_path.exists():
            save(error_path, {"status": "ERROR_INDEPENDENT_TRIANGLE_INCIDENCE_QUERY_REPLAY",
                 "type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc(),
                 "source": binding(__file__), "seconds": time.monotonic() - started,
                 "graph_constructed": False, "whole_component_excluded": False})
        raise


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("controls", "run"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--configuration", type=Path)
    parser.add_argument("--configuration-sha256")
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--result-sha256")
    parser.add_argument("--owner-sha256")
    parser.add_argument("--gate", type=Path)
    parser.add_argument("--gate-sha256")
    args = parser.parse_args()
    if args.mode == "run":
        assert all(getattr(args, name) is not None for name in
                   ("configuration", "configuration_sha256", "directory", "result_sha256",
                    "owner_sha256", "gate", "gate_sha256"))
    main(args)
