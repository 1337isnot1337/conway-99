"""Append complete triangle-incidence capacities to the accepted F0 model.

Preserve all 80730 variables and 297470 rows as an exact raw byte prefix; append
all 2904 side-edge and 420 local rows, followed by the accepted 84-term target
bound of 12, without any new variable. No solver mode.
The separately reviewed incidence theorem and complete inventory are mandatory,
and a separate complete protobuf replay is required before any future query.
"""
import argparse
import gzip
import hashlib
import importlib.metadata
import importlib.util
import json
import math
from pathlib import Path
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
PARENT_VARIABLES, PARENT_ROWS, PARENT_TERMS = 80730, 297470, 3310380
PARENT_RAW_BYTES = 39306083
PARENT_RAW_SHA = "2961c95ce21c39f8ea8bda29ed3ac98c5075b921dedc96f71035f1b90f77ddb6"
PARENT_ROOT_SHA = "20fef49c4a6a1b190dfc2869d77152deb4afd53b4411e6ec92a0fad53cf209b1"
LITERAL_ROOT_SHA = "f5bfd2f0af981e9b8fd96931e78bda6d2648960e8d0ddd981e2777bae88afea0"
LITERAL_SOURCE_SHA = "5cb224ef1a544eb23cc61d4d6a1a72e5266514c2483c26449945ab83abb9e615"
TARGET_TOTAL_ROOT_SHA = "10dd8fbfd42dc695bae9c83a3f61f7b9694d940a092e8e67e034781fd3eb0ebc"
TARGET_TOTAL_ROW_SHA = "36c10df91bd844086786344beb942a2fd271e2cb9fafc6712f9168d215a7a446"
PARENT_SOURCE_SHA = "18de36bc0b741f13578fbd2be43580a9bf3c1440f68918c3a63f37e65d7fc12b"
PARENT_COLD_SHA = "d955a93a7bf112f3c79ae9c6ffdd9f093b9b8d1f58df3ea25fe1bfba56f6b5e2"
EDGE_ORDER_SHA = "411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb"
MODEL_SCHEMA_SHA = "266b68151ffd6c9f5db22553442abd777031663d39e1cea649a8737f811d2eff"
EDGE_START, EDGE_STOP, TRIANGLE_START, TRIANGLE_COUNT = 540, 68934, 71382, 5364
TRIANGLE_AND_START, TRIANGLE_TARGET_START = 260042, 281498
FINAL_VARIABLES, FINAL_ROWS, INCIDENCE_RESULT_ROWS = 80730, 300795, 300794
INCIDENCE_FAMILY_ORDER = ["side_edge", "local_selector"]
INCIDENCE_FAMILY_COUNTS = {"side_edge": 2904, "local_selector": 420}
INCIDENCE_FAMILY_TERMS = {"side_edge": 10320, "local_selector": 16512}
FAMILY_ORDER = INCIDENCE_FAMILY_ORDER + ["global_target_total"]
FAMILY_COUNTS = {**INCIDENCE_FAMILY_COUNTS, "global_target_total": 1}
FAMILY_TERMS = {**INCIDENCE_FAMILY_TERMS, "global_target_total": 84}
LAYOUT = {"parent_variables": 80730, "parent_rows": 297470,
          "new_variables": 0, "replaced_rows": 0, "appended_rows": 3325, "appended_terms": 26916,
          "side_edge_start": 297470, "local_selector_start": 300374, "global_target_total_start": 300794,
          "variables": 80730, "rows": 300795,
          "triangle_variable_start": 71382, "triangle_variables": 5364}
PASS = {"controls": "PASS_TRIANGLE_INCIDENCE_MODEL_CONTROLS",
        "prepare": "PASS_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_PREPARATION"}
REQUIRED_INPUTS = {"parent_model", "parent_configuration", "parent_report", "parent_owner",
                   "parent_cold", "parent_cold_owner", "parent_root_acceptance", "domain",
                   "indicator_inventory", "incidence_inventory", "incidence_finalization", "incidence_owner",
                   "incidence_terminal_binding", "incidence_root_acceptance", "incidence_theorem_review",
                   "incidence_literal_report", "incidence_literal_finalization", "incidence_literal_owner",
                   "target_total_report", "target_total_finalization", "target_total_owner",
                   "target_total_root_acceptance", "target_total_theorem_review"}
REQUIRED_AUTHORITIES = REQUIRED_INPUTS - {"parent_model", "parent_configuration", "domain",
                                         "incidence_inventory", "incidence_finalization", "incidence_owner",
                                         "incidence_terminal_binding"}



def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha(Path(path).read_bytes())


def write_new(path, data):
    with Path(path).open("xb") as stream:
        stream.write(data)


def save(path, value):
    write_new(path, canonical(value) + b"\n")


def binding(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": sha(data)}


def same_ref(left, right):
    assert left["path"] == right["path"] and left["sha256"] == right["sha256"]
    if "bytes" in left and "bytes" in right:
        assert left["bytes"] == right["bytes"]
    if "raw_sha256" in left and "raw_sha256" in right:
        assert left["raw_sha256"] == right["raw_sha256"]


def read_bytes(ref):
    relative = Path(ref["path"])
    assert not relative.is_absolute() and ".." not in relative.parts
    data = (ROOT / relative).read_bytes()
    assert sha(data) == ref["sha256"], ref["path"]
    assert type(ref["bytes"]) is int and len(data) == ref["bytes"], ref["path"]
    return data


def read_json(ref):
    data = read_bytes(ref)
    if ref["path"].endswith(".gz"):
        data = gzip.decompress(data)
    if "raw_sha256" in ref:
        assert sha(data) == ref["raw_sha256"], ref["path"]
    return json.loads(data)


def bound_module(name, ref):
    read_bytes(ref)
    spec = importlib.util.spec_from_file_location(name, ROOT / ref["path"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module



def deadline_check(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("triangle incidence phase deadline")


def load_configuration(args):
    raw = args.configuration.read_bytes()
    assert sha(raw) == args.configuration_sha256
    cfg = json.loads(raw)
    assert cfg["schema"] == "conway99.f0.triangle-incidence-native-configuration.v1"
    assert cfg["source_sha256"] == digest(__file__) and cfg["layout"] == LAYOUT
    assert cfg["family_order"] == FAMILY_ORDER and cfg["expected_family_counts"] == FAMILY_COUNTS
    assert cfg["expected_family_terms"] == FAMILY_TERMS
    assert cfg["runtime"]["ortools"] == "9.15.6755" and cfg["runtime"]["protobuf"] == "6.33.6"
    assert cfg["runtime"]["model_schema_sha256"] == MODEL_SCHEMA_SHA
    assert cfg["limits"] == {"controls_worker_seconds": 10, "controls_owner_seconds": 15,
                             "prepare_worker_seconds": 120, "prepare_owner_seconds": 135}
    assert cfg["optimizer_calls"] == cfg["automatic_retries"] == 0
    assert cfg["native_query_authorized"] is False and cfg["independent_complete_protobuf_replay_required"] is True
    assert REQUIRED_INPUTS <= set(cfg["inputs"])
    assert cfg["inputs"]["parent_root_acceptance"]["sha256"] == PARENT_ROOT_SHA
    assert cfg["inputs"]["incidence_root_acceptance"]["sha256"] == LITERAL_ROOT_SHA
    assert cfg["inputs"]["target_total_root_acceptance"]["sha256"] == TARGET_TOTAL_ROOT_SHA
    expected = {"base": "5a1e8026683a7782fce6ec2a2947748356ac9cd5adf32dd2a0663b0dd60bfca2",
                "supervisor": "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3",
                "parent_producer": PARENT_SOURCE_SHA, "parent_cold": PARENT_COLD_SHA,
                "incidence_producer": "3357917e76a94f2c79fdc5a65e00a3413ad1e019c63e4d5ae3400f7978f12699"}
    assert set(expected) | {"checker"} <= set(cfg["sources"])
    for name, value in expected.items():
        assert cfg["sources"][name]["sha256"] == value
    for ref in cfg["sources"].values():
        read_bytes(ref)
    assert cfg["proofs"] and cfg["reviews"]
    for ref in cfg["proofs"] + cfg["reviews"]:
        read_bytes(ref)
    return cfg


def validate_owner(owner, report_ref, source_ref, configuration_ref, schema, status, mode):
    assert owner["schema"] == schema and owner["status"] == status and owner["mode"] == mode
    assert owner["report_accepted"] is True and owner["optimizer_calls"] == 0
    assert owner["CpSolver_constructed"] is False and owner["maximum_seconds"] == 135
    elapsed = owner["seconds"]
    assert type(elapsed) in (int, float) and math.isfinite(elapsed) and 0 <= elapsed <= 135
    assert owner["deadline_overrun_seconds"] == 0
    s = owner["supervision"]
    assert s["status"] == "CHILD_EXITED" and s["returncode"] == 0
    assert s["child_reaped"] is True and s["owned_process_group_stopped"] is True
    same_ref(owner["report"], report_ref)
    same_ref(owner["source"], source_ref)
    same_ref(owner["configuration"], configuration_ref)


def load_inputs(cfg):
    loaded = {name: read_json(ref) for name, ref in cfg["inputs"].items() if name != "parent_model"}
    checked = set()
    for authority in cfg["authorities"]:
        name, expected = authority["input"], authority["expected_status"]
        assert name not in checked and expected.startswith(("PASS_", "ROOT_ACCEPTS_", "OWNED_"))
        assert loaded[name][authority.get("status_field", "status")] == expected, name
        checked.add(name)
    assert REQUIRED_AUTHORITIES <= checked
    for link in cfg["authority_links"]:
        item = loaded[link["input"]]
        for field in link["fields"]:
            item = item[field]
        same_ref(item, cfg["inputs"][link["target"]])
    root, report, cold, pcfg = [loaded[name] for name in
        ("parent_root_acceptance", "parent_report", "parent_cold", "parent_configuration")]
    assert root["schema"] == "conway99.f0.combined-extensions-native-root-acceptance.v1"
    assert root["status"] == "ROOT_ACCEPTS_COMPLETE_COMBINED_EXTENSIONS_NATIVE_MODEL_AND_INDEPENDENT_COLD"
    assert report["status"] == "PASS_COMPLETE_COMBINED_EXTENSIONS_NATIVE_PREPARATION"
    assert cold["status"] == "PASS_INDEPENDENT_COMPLETE_COMBINED_EXTENSIONS_NATIVE_MODEL"
    assert pcfg["schema"] == "conway99.f0.combined-extensions-native-configuration.v1"
    assert pcfg["source_sha256"] == PARENT_SOURCE_SHA
    for record in (root, report, cold):
        assert record["model_raw_sha256"] == PARENT_RAW_SHA and record["model_raw_bytes"] == PARENT_RAW_BYTES
        assert record["variables"] == PARENT_VARIABLES and record["rows"] == PARENT_ROWS and record["optimizer_calls"] == 0
    assert root["complete_original_parent_bytes_recovered"] is True
    assert root["native_query_authorized_by_this_receipt"] is False
    for field, alias in (("configuration", "parent_configuration"), ("preparation", "parent_report"),
                         ("independent_cold", "parent_cold"), ("model_archive", "parent_model")):
        same_ref(root[field], cfg["inputs"][alias])
    for record, alias in ((report, "parent_producer"), (cold, "parent_cold")):
        same_ref(record["source"], cfg["sources"][alias])
        same_ref(record["configuration"], cfg["inputs"]["parent_configuration"])
    same_ref(cold["preparation_report"], cfg["inputs"]["parent_report"])
    same_ref(cold["preparation_owner"], cfg["inputs"]["parent_owner"])
    same_ref(root["owners"]["preparation"], cfg["inputs"]["parent_owner"])
    same_ref(root["owners"]["independent_cold"], cfg["inputs"]["parent_cold_owner"])
    validate_owner(loaded["parent_owner"], cfg["inputs"]["parent_report"], cfg["sources"]["parent_producer"],
                   cfg["inputs"]["parent_configuration"], "conway99.f0.combined-extensions-native-owner.v1",
                   "PASS_COMPLETE_COMBINED_EXTENSIONS_NATIVE_PREPARATION", "prepare")
    validate_owner(loaded["parent_cold_owner"], cfg["inputs"]["parent_cold"], cfg["sources"]["parent_cold"],
                   cfg["inputs"]["parent_configuration"], "conway99.f0.combined-extensions-independent-ci-owner.v1",
                   "OWNED_COMPLETE_COMBINED_EXTENSIONS_NATIVE_COLD_ACCEPTED", "replay")
    same_ref(pcfg["inputs"]["domain"], cfg["inputs"]["domain"])
    same_ref(pcfg["inputs"]["triangle_inventory"], cfg["inputs"]["indicator_inventory"])
    inv, final, terminal = [loaded[name] for name in
        ("incidence_inventory", "incidence_finalization", "incidence_terminal_binding")]
    assert inv["schema"] == "conway99.f0.recorded-triangle-capacity-inventory.v1"
    assert inv["status"] == "PASS_COMPLETE_SAVED_TRIANGLE_INCIDENCE_AND_SUFFICIENT_IMPLICATION_AUDIT"
    assert inv["complete_with_respect_to_saved_indicator_inventory"] is True
    assert inv["all_2904_side_proposals_preserved"] is True and inv["all_420_nonempty_local_proposals_preserved"] is True
    assert inv["native_solver_calls"] == 0 and inv["existing_native_model_changed"] is False
    assert inv["native_model_built"] is False and inv["full_model_nonredundancy_claimed"] is False
    same_ref(inv["source"], cfg["sources"]["incidence_producer"])
    for field, alias in (("domain", "domain"), ("indicator", "indicator_inventory"),
                         ("combined_configuration", "parent_configuration")):
        same_ref(inv["input_bindings"][field], cfg["inputs"][alias])
    assert final["schema"] == "conway99.f0.recorded-triangle-capacity-finalization.v1"
    assert final["status"] == "UNACCEPTED_METADATA_FINALIZATION_BUDGET_OVERRUN"
    assert final["report_sha256"] == cfg["inputs"]["incidence_inventory"]["sha256"]
    assert final["report_bytes"] == cfg["inputs"]["incidence_inventory"]["bytes"]
    assert final["optimizer_calls"] == 0
    assert final["total_milliseconds"] == 12196 > final["maximum_milliseconds"] == 10000
    failed_owner = loaded["incidence_owner"]
    assert failed_owner["schema"] == "conway99.f0.recorded-triangle-capacity-owned-execution.v1"
    assert failed_owner["status"] == "UNACCEPTED_TRIANGLE_CAPACITY_METADATA_EXECUTION"
    assert failed_owner["report_accepted"] is False and failed_owner["within_budget"] is False
    assert failed_owner["elapsed_milliseconds"] == 17209 > failed_owner["maximum_milliseconds"] == 10000
    assert failed_owner["worker_invocations"] == 1 and failed_owner["automatic_retries"] == 0
    assert failed_owner["native_solver_calls"] == 0 and failed_owner["OS_child_constructed"] is False
    same_ref(failed_owner["report"], cfg["inputs"]["incidence_inventory"])
    same_ref(failed_owner["finalization"], cfg["inputs"]["incidence_finalization"])
    same_ref(failed_owner["source"], cfg["sources"]["incidence_producer"])
    assert failed_owner["configuration"]["sha256"] == inv["configuration_sha256"]
    assert terminal["schema"] == "conway99.f0.recorded-triangle-capacity-row-key-descriptor.v1"
    assert terminal["status"] == "SAVED_COMPLETE_ROW_KEY_DIGESTS_FROM_UNACCEPTED_METADATA_OVERRUN"
    assert terminal["original_run_accepted"] is False and terminal["original_report_is_untrusted_proposal_table"] is True
    assert terminal["independent_reconstruction_from_previously_accepted_indicator_data_required"] is True
    assert terminal["overrun_waived_or_relabelled"] is False and terminal["extractor_rerun_performed"] is False
    assert terminal["family_order"] == INCIDENCE_FAMILY_ORDER
    assert terminal["family_row_counts"] == INCIDENCE_FAMILY_COUNTS and terminal["family_term_counts"] == INCIDENCE_FAMILY_TERMS
    for field, alias in (("report", "incidence_inventory"), ("finalization", "incidence_finalization"),
                         ("owner", "incidence_owner")):
        same_ref(terminal[field], cfg["inputs"][alias])
    validate_literal_inputs(cfg, loaded)
    validate_target_total_inputs(cfg, loaded)
    return loaded


def parent_model(cfg, pb):
    raw = gzip.decompress(read_bytes(cfg["inputs"]["parent_model"]))
    assert len(raw) == PARENT_RAW_BYTES and sha(raw) == PARENT_RAW_SHA
    parent = pb.CpModelProto()
    parent.ParseFromString(raw)
    assert parent.SerializeToString() == raw
    assert len(parent.variables) == PARENT_VARIABLES and len(parent.constraints) == PARENT_ROWS
    assert {field.name for field, _ in parent.ListFields()} <= {"name", "variables", "constraints"}
    assert all(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal for row in parent.constraints)
    edges = []
    for entry in parent.variables[EDGE_START:EDGE_STOP]:
        words = entry.name.split("_")
        assert len(words) == 4 and words[:2] == ["shared", "edge"]
        a, b = int(words[2]), int(words[3])
        assert 0 <= a < b < 480 and entry.name == "shared_edge_%03d_%03d" % (a, b)
        assert list(entry.domain) == [0, 1]
        edges.append([a, b])
    assert len(edges) == 68394 and sha(canonical(edges)) == EDGE_ORDER_SHA
    assert len({tuple(edge) for edge in edges}) == len(edges)
    assert all(list(parent.variables[j].domain) == [0, 1] for j in range(480))
    return raw, parent, edges



def validate_literal_inputs(cfg, loaded):
    """Use the successful independent replay; retain the failed extractor unchanged."""
    root, report, final, owner = [loaded[name] for name in
        ("incidence_root_acceptance", "incidence_literal_report",
         "incidence_literal_finalization", "incidence_literal_owner")]
    assert cfg["inputs"]["incidence_root_acceptance"]["sha256"] == LITERAL_ROOT_SHA
    assert root["schema"] == "conway99.f0.recorded-triangle-capacity-literal-root-acceptance.v1"
    assert root["status"] == "ROOT_ACCEPTS_COMPLETE_RECORDED_TRIANGLE_CAPACITY_LITERAL_ROWS"
    assert report["schema"] == "conway99.f0.recorded-triangle-capacity-literal-replay.v1"
    assert report["status"] == "PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_CAPACITY_ROWS"
    assert final["schema"] == "conway99.f0.recorded-triangle-capacity-literal-finalization.v1"
    assert final["status"] == "PASS_COMPLETE_SERIALIZATION_WITHIN_DECLARED_BOUND"
    assert owner["schema"] == "conway99.f0.recorded-triangle-capacity-literal-owned-execution.v1"
    assert owner["status"] == "PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_CAPACITY_LITERAL_EXECUTION"
    for field, alias in (("report", "incidence_literal_report"),
                         ("finalization", "incidence_literal_finalization"), ("owner", "incidence_literal_owner")):
        same_ref(root[field], cfg["inputs"][alias])
    same_ref(owner["report"], cfg["inputs"]["incidence_literal_report"])
    same_ref(owner["finalization"], cfg["inputs"]["incidence_literal_finalization"])
    assert root["source"]["sha256"] == LITERAL_SOURCE_SHA
    same_ref(report["source"], root["source"])
    for field in ("source", "configuration", "peer_review", "root_gate"):
        same_ref(owner[field], root[field])
    assert report["configuration_sha256"] == root["configuration"]["sha256"]
    assert root["input_bindings"] == report["input_bindings"]
    inputs = root["input_bindings"]
    for field, alias in (("domain", "domain"), ("indicator", "indicator_inventory"),
                         ("model_configuration", "parent_configuration"), ("model_root", "parent_root_acceptance"),
                         ("proposal", "incidence_inventory"), ("proposal_finalization", "incidence_finalization"),
                         ("proposal_owner", "incidence_owner"), ("row_descriptor", "incidence_terminal_binding"),
                         ("theorem_review", "incidence_theorem_review")):
        same_ref(inputs[field], cfg["inputs"][alias])
    same_ref(inputs["triangle_literal_root"],
             loaded["parent_configuration"]["inputs"]["triangle_literal_root_acceptance"])
    same_ref(inputs["producer_configuration"], loaded["incidence_owner"]["configuration"])
    same_ref(inputs["theorem_note"], loaded["incidence_terminal_binding"]["theorem_note"])
    same_ref(root["model_root_acceptance"], cfg["inputs"]["parent_root_acceptance"])
    assert final["report_sha256"] == cfg["inputs"]["incidence_literal_report"]["sha256"]
    assert final["report_bytes"] == cfg["inputs"]["incidence_literal_report"]["bytes"]
    assert final["original_failed_producer_remains_unaccepted"] is True
    assert final["optimizer_calls"] == owner["optimizer_calls"] == report["optimizer_calls"] == root["optimizer_calls"] == 0
    assert type(final["total_milliseconds"]) is int and 0 <= final["total_milliseconds"] < 30000
    assert final["maximum_milliseconds"] == report["maximum_milliseconds"] == 30000
    assert type(report["replay_milliseconds"]) is int and 0 <= report["replay_milliseconds"] <= final["total_milliseconds"]
    assert owner["report_accepted"] is True and owner["error"] is None
    assert type(owner["elapsed_milliseconds"]) is int and 0 <= owner["elapsed_milliseconds"] < 45000
    assert owner["maximum_milliseconds"] == 45000
    assert owner["worker_invocations"] == 1 and owner["automatic_retries"] == 0
    assert owner["producer_calls"] == owner["new_domain_or_triangle_census_calls"] == owner["native_model_builds"] == 0
    assert owner["OS_child_constructed"] is False and owner["hard_OS_preemption_claimed"] is False
    assert owner["original_failed_producer_execution_accepted"] is False
    assert root["source_finalization_milliseconds"] == final["total_milliseconds"]
    assert root["source_bound_milliseconds"] == final["maximum_milliseconds"]
    assert root["outer_owner_milliseconds"] == owner["elapsed_milliseconds"]
    assert root["outer_owner_bound_milliseconds"] == owner["maximum_milliseconds"]
    for record in (root, report):
        assert record["parent_raw_sha256"] == PARENT_RAW_SHA
        for field, count in (("parent_variables", PARENT_VARIABLES), ("parent_rows", PARENT_ROWS),
                             ("new_variables", 0), ("appended_rows", 3324),
                             ("appended_terms", 26832), ("resulting_rows", INCIDENCE_RESULT_ROWS)):
            assert type(record[field]) is int and record[field] == count
        assert record["family_order"] == INCIDENCE_FAMILY_ORDER
        assert record["family_row_counts"] == INCIDENCE_FAMILY_COUNTS and record["family_term_counts"] == INCIDENCE_FAMILY_TERMS
    assert root["parent_raw_bytes"] == PARENT_RAW_BYTES
    assert root["hashes"] == report["hashes"]
    assert set(report["hashes"]) == {"row_keys_sha256", "side_row_keys_sha256", "local_row_keys_sha256",
            "complete_edge_incidence_sha256", "side_records_sha256", "local_records_sha256", "local_empty_sha256"}
    assert all(type(value) is str and len(value) == 64 and set(value) <= set("0123456789abcdef")
               for value in report["hashes"].values())
    for field, count in (("saved_original_neighbor_rows_checked", 480), ("saved_original_edge_order_checked", 68394),
                         ("accepted_triangles_checked", 5364), ("complete_edge_incidences_checked", 6300),
                         ("existing_target_equalities_checked", 84), ("existing_singleton_AND_origins_checked", 3312),
                         ("side_rows_checked", 2904), ("local_rows_checked", 420), ("empty_local_dispositions_checked", 60)):
        assert type(report[field]) is int and report[field] == count
    assert report["every_proposed_native_key_and_origin_compared"] is True
    assert report["proposal_used_only_after_independent_row_derivation"] is True
    assert report["failed_producer_execution_accepted"] is False and report["failed_producer_overrun_waived"] is False
    assert report["failed_producer_finalization_milliseconds"] == loaded["incidence_finalization"]["total_milliseconds"]
    assert report["failed_producer_owner_milliseconds"] == loaded["incidence_owner"]["elapsed_milliseconds"]
    assert report["producer_source_executed"] is False and report["redundancy_audit_repeated"] is False
    assert report["redundancy_claims_accepted_by_this_report"] is False and report["native_model_messages_decoded"] is False
    assert report["future_complete_independent_native_replay_required"] is True
    assert report["new_domain_or_triangle_census_calls"] == report["native_model_builds"] == 0
    assert root["original_producer_execution_accepted"] is False
    assert root["original_producer_overrun_waived_or_relabelled"] is False
    assert root["redundancy_audit_accepted_by_this_receipt"] is False
    assert root["producer_rerun_calls"] == root["automatic_retries"] == root["new_domain_or_triangle_census_calls"] == 0
    assert root["literal_replay_calls"] == 1 and root["native_model_builds"] == 0
    assert root["independent_complete_native_replay_required"] is True
    assert root["native_build_authorized_by_this_receipt"] is False
    assert root["native_query_authorized_by_this_receipt"] is False
    assert root["graph_constructed"] is False and root["whole_component_excluded"] is False



def validate_target_total_inputs(cfg, loaded):
    root, report, final, owner, peer = [loaded[name] for name in
        ("target_total_root_acceptance", "target_total_report", "target_total_finalization",
         "target_total_owner", "target_total_theorem_review")]
    assert cfg["inputs"]["target_total_root_acceptance"]["sha256"] == TARGET_TOTAL_ROOT_SHA
    assert root["schema"] == "conway99.f0.target-color-twelve-root-acceptance.v1"
    assert root["status"] == "ROOT_ACCEPTS_EXACT_BOOLEAN_TWELVE_TARGET_BOUND"
    assert report["schema"] == "conway99.f0.target-color-twelve-certificate.v1"
    assert report["status"] == "PASS_EXACT_STRUCTURAL_TWELVE_TARGET_BOUND_AND_COLOR_WITNESS"
    assert final["schema"] == "conway99.f0.target-color-twelve-finalization.v1"
    assert final["status"] == "PASS_COMPLETE_STRUCTURAL_CERTIFICATE_SERIALIZATION"
    assert owner["schema"] == "conway99.f0.target-color-twelve-owner.v1"
    assert owner["status"] == "OWNED_COMPLETE_STRUCTURAL_TWELVE_TARGET_CERTIFICATE_ACCEPTED"
    assert peer["schema"] == "conway99.f0.target-color-twelve-independent-source-review.v1"
    assert peer["status"] == "PASS_COMPLETE_TWELVE_BOUND_PROOF_AND_FROZEN_SOURCE_REVIEW_UNRUN"
    assert peer["mathematical_gate_pass"] is True and peer["source_gate_pass"] is True
    assert peer["native_build_authorized"] is False and peer["query_authorized"] is False
    for field, alias in (("report", "target_total_report"), ("finalization", "target_total_finalization"),
                         ("owner", "target_total_owner"), ("peer_review", "target_total_theorem_review")):
        same_ref(root[field], cfg["inputs"][alias])
    same_ref(owner["report"], cfg["inputs"]["target_total_report"])
    same_ref(owner["finalization"], cfg["inputs"]["target_total_finalization"])
    same_ref(owner["source_review"], cfg["inputs"]["target_total_theorem_review"])
    for field in ("source", "configuration", "proof", "proof_scope_correction"):
        same_ref(owner[field], root[field])
        same_ref(peer[field], root[field])
    assert root["source"]["sha256"] == "dfb0764a29e53db9ba59b5fd291a45a612af0f690699b1892c195487014a152e"
    same_ref(report["source"], root["source"])
    assert report["configuration_sha256"] == root["configuration"]["sha256"]
    for field in ("proof", "proof_scope_correction"):
        assert any(ref["path"] == root[field]["path"] and ref["sha256"] == root[field]["sha256"]
                   for ref in cfg["proofs"])
    assert set(root["input_bindings"]) == set(report["inputs"])
    for name, ref in root["input_bindings"].items():
        same_ref(ref, report["inputs"][name])
    for field, alias in (("domain", "domain"), ("indicator", "indicator_inventory"),
                         ("combined_configuration", "parent_configuration")):
        same_ref(report["inputs"][field], cfg["inputs"][alias])
    same_ref(report["inputs"]["triangle_literal_root"],
             loaded["parent_configuration"]["inputs"]["triangle_literal_root_acceptance"])
    same_ref(root["model_root_acceptance"], cfg["inputs"]["parent_root_acceptance"])
    assert root["parent_raw_sha256"] == PARENT_RAW_SHA
    assert root["parent_variables"] == PARENT_VARIABLES and root["parent_rows"] == PARENT_ROWS
    assert final["report_sha256"] == cfg["inputs"]["target_total_report"]["sha256"]
    assert final["report_bytes"] == cfg["inputs"]["target_total_report"]["bytes"]
    assert type(final["total_milliseconds"]) is int and 0 <= final["total_milliseconds"] < 30000
    assert final["maximum_milliseconds"] == owner["worker_maximum_milliseconds"] == 30000
    assert type(report["proof_check_milliseconds"]) is int and 0 <= report["proof_check_milliseconds"] <= final["total_milliseconds"]
    assert owner["report_accepted"] is True and owner["within_budget"] is True and owner["error"] is None
    assert type(owner["elapsed_milliseconds"]) is int and 0 <= owner["elapsed_milliseconds"] < 45000
    assert owner["maximum_milliseconds"] == 45000
    assert owner["worker_invocations"] == 1 and owner["automatic_retries"] == 0
    assert owner["OS_child_constructed"] is False and owner["hard_OS_preemption_claimed"] is False
    assert owner["assignment_enumerations"] == owner["native_solver_calls"] == 0
    assert root["source_finalization_milliseconds"] == final["total_milliseconds"]
    assert root["source_bound_milliseconds"] == final["maximum_milliseconds"]
    assert root["outer_owner_milliseconds"] == owner["elapsed_milliseconds"]
    assert root["outer_owner_bound_milliseconds"] == owner["maximum_milliseconds"]
    assert report["bound"] == root["Boolean_bound"] == 12
    assert report["Boolean_bound_proved"] is True and report["all_local_conditions_checked"] is True
    assert report["private_selected_component_argument_is_Boolean"] is True
    assert report["continuous_implication_claimed"] is False and report["full_model_nonredundancy_claimed"] is False
    assert report["native_model_changed"] is False and report["original_domain_or_triangle_census_performed"] is False
    assert report["optimizer_calls"] == report["assignment_enumerations"] == final["optimizer_calls"] == final["assignment_enumerations"] == 0
    assert root["optimizer_calls"] == root["native_model_builds"] == root["automatic_retries"] == 0
    assert root["assignment_enumerations"] == root["new_domain_or_triangle_census_calls"] == 0
    assert root["structural_checker_calls"] == 1 and root["new_variables"] == 0
    assert root["additional_rows"] == 1 and root["additional_terms"] == 84
    assert root["proposed_native_row_key_sha256"] == report["proposed_row_key_sha256"] == TARGET_TOTAL_ROW_SHA
    assert root["proposed_native_row_key"] == report["proposed_native_row_key"]
    assert root["full_model_feasible_witness_claimed"] is False
    assert root["full_model_continuous_nonredundancy_claimed"] is False
    assert root["all18_original_equality_quotas_saturated_by_witness_claimed"] is False
    assert root["native_append_authorized_by_this_receipt"] is False
    assert root["independent_complete_native_replay_required"] is True
    assert root["graph_constructed"] is False and root["whole_component_excluded"] is False


def runtime_record(cfg, native):
    from ortools.sat import cp_model_pb2 as pb
    import google.protobuf
    assert importlib.metadata.version("ortools") == cfg["runtime"]["ortools"]
    assert google.protobuf.__version__ == cfg["runtime"]["protobuf"]
    assert sha(pb.DESCRIPTOR.serialized_pb) == MODEL_SCHEMA_SHA
    result = {"python": sys.version, "ortools": importlib.metadata.version("ortools"),
              "protobuf": google.protobuf.__version__, "model_schema_sha256": MODEL_SCHEMA_SHA}
    if native:
        from ortools.sat.python import cp_model
        result.update(cp_model_sha256=digest(cp_model.__file__),
                      native_helper_sha256=digest(cp_model.cmh.__file__))
        for key in ("cp_model_sha256", "native_helper_sha256"):
            assert result[key] == cfg["runtime"][key]
    return result


def key(lower, upper, entries, variables=FINAL_VARIABLES):
    assert type(lower) is type(upper) is int and -(1 << 63) <= lower <= upper < (1 << 63)
    assert all(type(v) is type(c) is int and 0 <= v < variables and c != 0
               and -(1 << 63) < c < (1 << 63) for v, c in entries)
    assert len({v for v, c in entries}) == len(entries)
    return [lower, upper, sorted([list(pair) for pair in entries])]


def constraint(pb, row):
    lower, upper, entries = row
    assert key(lower, upper, entries) == row
    result = pb.ConstraintProto()
    result.linear.vars.extend(v for v, c in entries)
    result.linear.coeffs.extend(c for v, c in entries)
    result.linear.domain.extend([lower, upper])
    return result


def variable(pb, name):
    assert type(name) is str and name
    result = pb.IntegerVariableProto()
    result.name = name
    result.domain.extend([0, 1])
    return result


def message_digest(messages):
    h = hashlib.sha256()
    for message in messages:
        raw = message.SerializeToString()
        h.update(len(raw).to_bytes(8, "big"))
        h.update(raw)
    return h.hexdigest()


def collect_incidence(triangles, edges, vertex_count):
    """Rebuild all recorded incidences without a domain or support census."""
    edge_uses, incident = {}, [[] for _ in range(vertex_count)]
    for ti, triangle in enumerate(triangles):
        assert triangle["triangle_index"] == ti
        a, b, c = triangle["vertices"]
        assert all(type(v) is int for v in (a, b, c)) and 0 <= a < b < c < vertex_count
        ids = triangle["edge_ids"]
        assert len(ids) == 3 and len(set(ids)) == 3
        assert all(type(e) is int and 0 <= e < len(edges) for e in ids)
        assert [edges[e] for e in ids] == [[a, b], [a, c], [b, c]]
        for position, (edge, third) in enumerate(zip(ids, (c, b, a))):
            edge_uses.setdefault(edge, []).append([ti, third, position])
        for vertex in (a, b, c):
            incident[vertex].append(ti)
    return edge_uses, incident


def rebuild_capacity_keys(triangles, targets, edges, k0):
    """Use the complete accepted indicator list; no implication-based pruning."""
    uses, incident = collect_incidence(triangles, edges, len(k0))
    target_ids = set()
    for target in targets:
        e = target["edge_id"]
        assert type(e) is int
        assert e in uses and e not in target_ids and target["endpoints"] == edges[e]
        assert target["triangle_indices"] == [entry[0] for entry in uses[e]]
        target_ids.add(e)
    side, local, side_origins, local_origins, empty = [], [], [], [], []
    for edge in sorted(uses):
        ids = [entry[0] for entry in uses[edge]]
        if edge in target_ids or len(ids) == 1:
            continue
        side.append(key(-1, 0, [[EDGE_START + edge, -1]] + [[TRIANGLE_START + i, 1] for i in ids]))
        side_origins.append({"edge_id": edge, "endpoints": edges[edge],
                             "triangle_indices": ids, "third_selectors": [entry[1] for entry in uses[edge]]})
    for a, ids in enumerate(incident):
        assert k0[a] in (0, 1)
        if not ids:
            empty.append(a)
            continue
        cap = 2 + k0[a]
        local.append(key(-cap, 0, [[a, -cap]] + [[TRIANGLE_START + i, 1] for i in ids]))
        local_origins.append({"selector": a, "k0": k0[a], "triangle_indices": ids})
    return {"side_edge": side, "local_selector": local}, side_origins, local_origins, uses, empty


def append_suffix(pb, parent_raw, rows):
    original, full, suffix = pb.CpModelProto(), pb.CpModelProto(), pb.CpModelProto()
    original.ParseFromString(parent_raw)
    assert original.SerializeToString() == parent_raw
    full.CopyFrom(original)
    suffix.constraints.extend(constraint(pb, row) for row in rows)
    suffix_raw = suffix.SerializeToString()
    assert {field.name for field, _ in suffix.ListFields()} <= {"constraints"}
    full.constraints.extend(suffix.constraints)
    raw = full.SerializeToString()
    assert raw == parent_raw + suffix_raw
    assert len(full.variables) == len(original.variables)
    recovered = pb.CpModelProto()
    recovered.CopyFrom(full)
    del recovered.constraints[len(original.constraints):]
    assert recovered.SerializeToString() == parent_raw
    return full, raw, suffix_raw



def ordered_json(value):
    """Match JSON.stringify for the explicitly ordered ASCII incidence records."""
    return json.dumps(value, separators=(",", ":"), allow_nan=False).encode("utf-8")


def same_constraint(message, pb, row):
    assert message.SerializeToString() == constraint(pb, row).SerializeToString()


def incidence_rows(cfg, loaded, parent, edges, pb, deadline):
    inv, rec, domain = [loaded[name] for name in ("indicator_inventory", "incidence_inventory", "domain")]
    assert inv["status"] == "PASS_EXACT_SHARED_TRIANGLE_INDICATOR_INVENTORY"
    assert domain["status"] == "complete component-zero exterior-row domain preparation"
    triangles, targets = inv["triangles"], inv["targets"]
    assert len(triangles) == inv["target_triangle_incidences"] == 5364 and len(targets) == 84
    H, A, Q = domain["signature_domain"], domain["component_adjacency_rows"], domain["row_targets"]
    assert len(H) == len(Q) == 480 and len(A) == 18
    k0 = []
    for a, h in enumerate(H):
        assert len(h) == 3 and h == sorted(set(h))
        assert all(type(v) is int and 0 <= v < 18 for v in h)
        n = sum((A[h[i]] >> h[j]) & 1 for i in range(3) for j in range(i + 1, 3))
        assert n in (0, 1) and sum(Q[a][i] for i in h) == 3 - 2 * n
        k0.append(n)
    groups, side_info, local_info, uses, empty = rebuild_capacity_keys(triangles, targets, edges, k0)
    target_positions = {t["edge_id"]: i for i, t in enumerate(targets)}
    assert len(target_positions) == 84 and len(uses) == 6300
    for ti, triangle in enumerate(triangles):
        if ti % 256 == 0:
            deadline_check(deadline)
        v, es = TRIANGLE_START + ti, triangle["edge_ids"]
        assert parent.variables[v].name == "spectral_triangle_%04d" % ti
        assert list(parent.variables[v].domain) == [0, 1]
        a, b, c = triangle["vertices"]
        assert all(set(H[u]).isdisjoint(H[w]) for u, w in ((a, b), (a, c), (b, c)))
        for j, e in enumerate(es):
            same_constraint(parent.constraints[TRIANGLE_AND_START + 4 * ti + j], pb,
                            key(0, 1, [[EDGE_START + e, 1], [v, -1]]))
        same_constraint(parent.constraints[TRIANGLE_AND_START + 4 * ti + 3], pb,
                        key(-2, 1, [[v, 1]] + [[EDGE_START + e, -1] for e in es]))
        target_edges = [e for e in es if e in target_positions]
        assert len(target_edges) == 1
        assert [origin["target_edge_id"] for origin in triangle["origins"]] == target_edges
    for index, target in enumerate(targets):
        e, ids = target["edge_id"], target["triangle_indices"]
        same_constraint(parent.constraints[TRIANGLE_TARGET_START + index], pb,
                        key(0, 0, [[EDGE_START + e, -1]] + [[TRIANGLE_START + t, 1] for t in ids]))
    assert len(rec["complete_edge_incidence"]) == 6300
    proposed_edges = {item["edge_id"]: i for i, item in enumerate(side_info)}
    singleton_count, complete_records = 0, []
    for saved, e in zip(rec["complete_edge_incidence"], sorted(uses)):
        entries = uses[e]
        assert saved["edge_id"] == e and saved["endpoints"] == edges[e]
        assert saved["triangle_indices"] == [x[0] for x in entries]
        assert saved["thirds"] == [x[1] for x in entries] and len(set(saved["thirds"])) == len(entries)
        complete = {"edge_id": e, "endpoints": edges[e], "triangle_indices": [x[0] for x in entries],
                    "thirds": [x[1] for x in entries],
                    "and_upper_native_rows": [TRIANGLE_AND_START + 4 * t + j for t, _, j in entries]}
        if e in target_positions:
            complete["disposition"] = "existing_target_equality"
            complete["existing_target_native_row"] = TRIANGLE_TARGET_START + target_positions[e]
        elif len(entries) == 1:
            complete["disposition"] = "existing_singleton_AND_upper"
            singleton_count += 1
        else:
            complete["disposition"] = "proposed_side_capacity"
            complete["proposal_index"] = proposed_edges[e]
        assert saved == complete
        complete_records.append(complete)
    assert singleton_count == 3312
    assert len(rec["side_capacity_proposals"]) == len(side_info) == 2904
    assert len(rec["local_capacity_proposals"]) == len(local_info) == 420
    assert empty == rec["local_empty_tautologies"] and len(empty) == 60
    origins = []
    for family, info, proposals in (
            ("side_edge", side_info, rec["side_capacity_proposals"]),
            ("local_selector", local_info, rec["local_capacity_proposals"])):
        for index, (expected, saved, row) in enumerate(zip(info, proposals, groups[family])):
            for field, value in expected.items():
                assert saved[field] == value
            assert saved["proposed_native_row_key"] == row
            if family == "side_edge":
                assert saved["continuous_implication_claimed"] is False and saved["full_model_independence_claimed"] is False
            else:
                a, n = expected["selector"], expected["k0"]
                assert saved["original_degree_native_row"] == 153950 + a
                assert saved["overlap_one_mixed_native_rows"] == [154430 + 18 * a + i for i in H[a]]
                assert saved["overlap_one_degree_coefficient"] == 3 - 2 * n
                assert saved["overlap_zero_degree_coefficient"] == 5 + 2 * n
                assert saved["implied_by_all_side_capacities_for_Boolean_originals"] is True
                assert saved["continuous_implication_from_edge_capacities_claimed"] is False
            origins.append({"family": family, "proposal_index": index,
                            "native_row_index": PARENT_ROWS + len(origins), **expected})
    assert {name: len(rows) for name, rows in groups.items()} == INCIDENCE_FAMILY_COUNTS
    assert {name: sum(len(row[2]) for row in rows) for name, rows in groups.items()} == INCIDENCE_FAMILY_TERMS
    side_records = [[item["edge_id"], item["endpoints"], item["triangle_indices"], item["third_selectors"], row]
                    for item, row in zip(side_info, groups["side_edge"])]
    local_records = [[item["selector"], item["k0"], item["triangle_indices"], row,
                      153950 + item["selector"], [154430 + 18 * item["selector"] + i for i in H[item["selector"]]]]
                     for item, row in zip(local_info, groups["local_selector"])]
    hashes = {"row_keys_sha256": sha(canonical(groups["side_edge"] + groups["local_selector"])),
              "side_row_keys_sha256": sha(canonical(groups["side_edge"])),
              "local_row_keys_sha256": sha(canonical(groups["local_selector"])),
              "complete_edge_incidence_sha256": sha(ordered_json(complete_records)),
              "side_records_sha256": sha(canonical(side_records)),
              "local_records_sha256": sha(canonical(local_records)), "local_empty_sha256": sha(canonical(empty))}
    assert hashes == loaded["incidence_root_acceptance"]["hashes"] == loaded["incidence_literal_report"]["hashes"]
    binding_record = loaded["incidence_terminal_binding"]
    assert binding_record["row_keys_sha256"] == hashes["row_keys_sha256"]
    assert binding_record["family_row_keys_sha256"] == {
        "side_edge": hashes["side_row_keys_sha256"], "local_selector": hashes["local_row_keys_sha256"]}
    assert binding_record["complete_edge_incidence_sha256"] == hashes["complete_edge_incidence_sha256"]
    deadline_check(deadline)
    return groups, origins, {"complete_edges": len(uses), "existing_target_equalities": 84,
            "existing_AND_constraints": 4 * len(triangles), "singleton_side_edges": singleton_count,
            "empty_local_selectors": empty, "local_k0": k0, "literal_hashes": hashes,
            "all_seven_literal_replay_hashes_independently_reconstructed": True}


def controls(cfg, args):
    from ortools.sat import cp_model_pb2 as pb
    runtime = runtime_record(cfg, False)
    toy = pb.CpModelProto()
    toy.name = "triangle-incidence-parent-prefix-control"
    toy.variables.extend(variable(pb, "old_bool_%d" % i) for i in range(3))
    signed = toy.variables.add()
    signed.name = "old_signed"
    signed.domain.extend([-7, 9])
    huge = (1 << 54) + 3
    toy.constraints.extend([constraint(pb, key(0, 1, [[0, 1], [1, 1]])),
        constraint(pb, key(-9 * huge, 7 * huge, [[3, -huge]])), constraint(pb, key(0, 0, []))])
    toy.constraints[2].name = "preserved-empty-equation"
    before = toy.SerializeToString()
    rows = [key(-1, 0, [[0, -1], [1, 1], [2, 1]]), key(-2, 0, [[0, -2], [1, 1], [2, 1]]),
            key(0, 2, [[0, 1], [1, 1], [2, 1]])]
    model, raw, suffix_raw = append_suffix(pb, before, rows)
    assert raw == before + suffix_raw and len(model.variables) == 4 and len(model.constraints) == 6
    assert list(model.variables[3].domain) == [-7, 9] and list(model.constraints[1].linear.coeffs) == [-huge]
    assert gzip.decompress(gzip.compress(raw, mtime=0)) == raw
    assert gzip.decompress(gzip.compress(suffix_raw, mtime=0)) == suffix_raw
    rejected, changed = 0, pb.CpModelProto()
    changed.CopyFrom(model)
    changed.constraints[1].linear.coeffs[0] += 1
    del changed.constraints[3:]
    assert changed.SerializeToString() != before
    rejected += 1
    changed.CopyFrom(model)
    changed.variables[1].name += "_changed"
    del changed.constraints[3:]
    assert changed.SerializeToString() != before
    rejected += 1
    changed.CopyFrom(model)
    changed.constraints[-1].linear.coeffs[0] = -3
    for test in (lambda: same_constraint(changed.constraints[-1], pb, rows[-1]),
                 lambda: key(-1, 0, [[0, 1], [0, -1]]),
                 lambda: key(-1, 0, [[0, True]]),
                 lambda: key(-1, 0, [[FINAL_VARIABLES, 1]])):
        try:
            test()
        except AssertionError:
            rejected += 1
        else:
            raise AssertionError("tampered row accepted")
    edges = [[0, 1], [0, 2], [0, 3], [1, 2], [1, 3]]
    triangles = [{"triangle_index": 0, "vertices": [0, 1, 2], "edge_ids": [0, 1, 3]},
                 {"triangle_index": 1, "vertices": [0, 1, 3], "edge_ids": [0, 2, 4]}]
    uses, incident = collect_incidence(triangles, edges, 4)
    assert uses[0] == [[0, 2, 0], [1, 3, 0]] and incident == [[0, 1], [0, 1], [0], [1]]
    try:
        collect_incidence([dict(triangles[0], edge_ids=[1, 0, 3]), triangles[1]], edges, 4)
    except AssertionError:
        rejected += 1
    else:
        raise AssertionError("wrong triangle edge order accepted")
    for mask in range(8):
        edge, first, second = [(mask >> i) & 1 for i in range(3)]
        assert (-1 <= -edge + first + second <= 0) == (first + second <= edge)
        assert (0 <= edge + first + second <= 2) == (mask != 7)
    for cap in (2, 3):
        for selector in (0, 1):
            for mask in range(16):
                count = mask.bit_count()
                assert (-cap <= count - cap * selector <= 0) == (count <= cap * selector)
    assert rejected == 7
    ordered_control = {"edge_id": 2, "endpoints": [0, 1], "triangle_indices": [0],
                       "thirds": [2], "and_upper_native_rows": [0]}
    assert ordered_json(ordered_control) == b'{"edge_id":2,"endpoints":[0,1],"triangle_indices":[0],"thirds":[2],"and_upper_native_rows":[0]}'
    assert ordered_json(ordered_control) != canonical(ordered_control)
    assert ordered_json(rows) == canonical(rows)
    deadline_check(args.deadline)
    return {"schema": "conway99.f0.triangle-incidence-model-controls.v1",
            "status": PASS["controls"], "runtime": runtime, "signed_large_integer": huge,
            "complete_parent_plus_suffix_exact": True, "old_variable_and_named_empty_row_metadata_preserved": True,
            "no_new_variables": True, "mutated_input_controls": rejected,
            "shared_edge_incidence_control_checked": True, "ordered_record_digest_control_checked": True,
            "side_capacity_boolean_cases": 8, "global_count_row_boolean_cases": 8,
            "local_capacity_boolean_cases": 64, "CpModel_constructed": False, "CpSolver_constructed": False,
            "native_optimizer_constructed": False, "native_query_run": False, "optimizer_calls": 0}



def target_total_row(cfg, loaded, parent, edges, pb, deadline):
    """Bind the accepted structural theorem and rebuild its exact native row."""
    report, root = loaded["target_total_report"], loaded["target_total_root_acceptance"]
    targets = loaded["indicator_inventory"]["targets"]
    target_ids = sorted(t["edge_id"] for t in targets)
    assert len(target_ids) == len(set(target_ids)) == 84
    assert report["edges"] == [[e, *edges[e]] for e in target_ids]
    row = key(0, 12, [[EDGE_START + e, 1] for e in target_ids])
    assert row == report["proposed_native_row_key"] == root["proposed_native_row_key"]
    assert sha(canonical(row)) == TARGET_TOTAL_ROW_SHA
    H, A = loaded["domain"]["signature_domain"], loaded["domain"]["component_adjacency_rows"]
    target_vertices = {v for e in target_ids for v in edges[e]}
    seen_colors, private_vertices, gram_rows = set(), set(), []
    assert len(report["private_Gram_rows"]) == 12
    for item in report["private_Gram_rows"]:
        u, v = item["core_edge"]
        assert type(u) is type(v) is int and 0 <= u < v < 18 and ((A[u] >> v) & 1) == 1
        assert (u, v) not in seen_colors
        seen_colors.add((u, v))
        support = [a for a, h in enumerate(H) if u in h and v in h]
        target_support = [a for a in support if a in target_vertices]
        assert item["quota"] == 1 and item["complete_support"] == support
        assert item["target_support"] == target_support and not private_vertices.intersection(target_support)
        private_vertices.update(target_support)
        native = item["native_row_id"]
        assert type(native) is int and 0 <= native < PARENT_ROWS
        same_constraint(parent.constraints[native], pb, key(1, 1, [[a, 1] for a in support]))
        gram_rows.append(native)
    assert sorted(private_vertices) == report["private_vertices"] and len(private_vertices) == 72
    assert len(set(gram_rows)) == 12
    deadline_check(deadline)
    origin = {"family": "global_target_total", "proposal_index": 0, "native_row_index": INCIDENCE_RESULT_ROWS,
              "target_edge_ids": target_ids, "target_count": 84, "upper_bound": 12}
    checks = {"bound": 12, "target_edges": 84, "private_Gram_rows_checked": gram_rows,
              "private_vertices": 72, "row_key_sha256": TARGET_TOTAL_ROW_SHA,
              "structural_theorem_root_acceptance": cfg["inputs"]["target_total_root_acceptance"],
              "structural_condition_census_repeated": False}
    return row, origin, checks


def stage(args, name):
    args.stages.append({"phase": name, "elapsed_seconds": time.monotonic() - args.started})
    deadline_check(args.deadline)



def prepare(cfg, args):
    from ortools.sat import cp_model_pb2 as pb
    runtime = runtime_record(cfg, True)
    loaded = load_inputs(cfg)
    parent_raw, original, edges = parent_model(cfg, pb)
    stage(args, "accepted_parent_and_all_proposal_receipts")
    groups, origins, checks = incidence_rows(cfg, loaded, original, edges, pb, args.deadline)
    total_row, total_origin, total_check = target_total_row(cfg, loaded, original, edges, pb, args.deadline)
    assert list(groups) == INCIDENCE_FAMILY_ORDER and len(origins) == 3324
    groups["global_target_total"] = [total_row]
    origins.append(total_origin)
    rows = [row for name in FAMILY_ORDER for row in groups[name]]
    counts = {name: len(data) for name, data in groups.items()}
    terms = {name: sum(len(row[2]) for row in data) for name, data in groups.items()}
    assert counts == FAMILY_COUNTS and terms == FAMILY_TERMS
    assert len(rows) == len(origins) == 3325 and sum(terms.values()) == 26916
    assert all(0 <= v < PARENT_VARIABLES and list(original.variables[v].domain) == [0, 1]
               for row in rows for v, _ in row[2])
    assert all(sum(abs(c) for _, c in row[2]) < (1 << 63) for row in rows)
    row_sha = sha(canonical(rows))
    family_sha = {name: sha(canonical(data)) for name, data in groups.items()}
    family_jsonl_sha = {name: sha(b"".join(canonical(row) + b"\n" for row in data)) for name, data in groups.items()}
    stage(args, "all_unfiltered_capacities_and_target_total_row_rebuilt")
    model, expected_raw, suffix_raw = append_suffix(pb, parent_raw, rows)
    assert len(model.variables) == FINAL_VARIABLES and len(model.constraints) == FINAL_ROWS
    assert expected_raw[:PARENT_RAW_BYTES] == parent_raw and expected_raw[PARENT_RAW_BYTES:] == suffix_raw
    assert all(model.variables[i].SerializeToString() == item.SerializeToString() for i, item in enumerate(original.variables))
    assert all(model.constraints[i].SerializeToString() == item.SerializeToString() for i, item in enumerate(original.constraints))
    parent_terms = sum(len(row.linear.vars) for row in original.constraints)
    total_terms = sum(len(row.linear.vars) for row in model.constraints)
    assert parent_terms == PARENT_TERMS and total_terms == PARENT_TERMS + 26916
    preservation = {
        "complete_parent_raw_prefix_preserved": True, "complete_original_parent_bytes_recovered": True,
        "all_original_variable_messages_preserved": True, "all_original_constraint_messages_preserved": True,
        "original_variable_messages_sha256": message_digest(original.variables),
        "original_constraint_messages_sha256": message_digest(original.constraints),
        "parent_variables": PARENT_VARIABLES, "parent_rows": PARENT_ROWS, "new_variables": 0, "replaced_rows": 0}
    stage(args, "constraint_only_suffix_and_whole_parent_preservation")
    base = bound_module("triangle_incidence_native_transport", cfg["sources"]["base"])
    model_path = args.directory / "model.pb"
    assert not model_path.exists()
    native_model, transport = base.transport(model, model_path, args.deadline)
    assert transport["complete_byte_comparison"] is True and transport["public_parse_return"] is True
    assert transport["native_validation"] == "" and transport["optimizer_calls"] == 0
    assert transport["CpSolver_constructed"] is False
    raw = model_path.read_bytes()
    assert raw == expected_raw
    del native_model
    stage(args, "public_native_transport_and_exact_export")
    ledger = {
        "schema": "conway99.f0.triangle-incidence-appended-row-ledger.v1",
        "source": binding(__file__), "configuration": binding(args.configuration),
        "incidence_inventory": cfg["inputs"]["incidence_inventory"],
        "incidence_terminal_binding": cfg["inputs"]["incidence_terminal_binding"],
        "target_total_report": cfg["inputs"]["target_total_report"],
        "target_total_root_acceptance": cfg["inputs"]["target_total_root_acceptance"],
        "family_order": FAMILY_ORDER, "family_counts": counts, "family_terms": terms,
        "row_keys": rows, "row_origins": origins, "row_keys_sha256": row_sha,
        "family_row_keys_sha256": family_sha, "literal_hashes": checks["literal_hashes"],
        "all_side_and_nonempty_local_proposals_preserved": True, "global_target_total_row_retained": True,
        "Boolean_implication_classification_used_to_prune": False,
        "input_extraction_execution_accepted": False,
        "independent_literal_root_acceptance": cfg["inputs"]["incidence_root_acceptance"]}
    ledger_raw = canonical(ledger) + b"\n"
    archives = {"model.pb.gz": gzip.compress(raw, compresslevel=6, mtime=0),
                "suffix.pb.gz": gzip.compress(suffix_raw, compresslevel=6, mtime=0),
                "append-rows.json.gz": gzip.compress(ledger_raw, compresslevel=6, mtime=0)}
    for name, data in archives.items():
        write_new(args.directory / name, data)
    assert gzip.decompress(archives["model.pb.gz"]) == raw
    assert parent_raw + gzip.decompress(archives["suffix.pb.gz"]) == raw
    assert gzip.decompress(archives["append-rows.json.gz"]) == ledger_raw
    artifacts = {"model": binding(model_path), "model_archive": binding(args.directory / "model.pb.gz"),
                 "suffix_archive": binding(args.directory / "suffix.pb.gz"),
                 "row_ledger": binding(args.directory / "append-rows.json.gz")}
    restoration = {"parent_raw_bytes": len(parent_raw), "parent_raw_sha256": sha(parent_raw),
                   "suffix_raw_bytes": len(suffix_raw), "suffix_raw_sha256": sha(suffix_raw)}
    manifest = {"schema": "conway99.f0.triangle-incidence-restoration.v1",
        "status": "PASS_EXACT_TRIANGLE_INCIDENCE_PARENT_AND_SUFFIX_RESTORATION",
        "source": binding(__file__), "configuration": binding(args.configuration),
        "parent_model": cfg["inputs"]["parent_model"], "parent_root_acceptance": cfg["inputs"]["parent_root_acceptance"],
        "layout": LAYOUT, "artifacts": artifacts, "restoration": restoration,
        "suffix_format": "CpModelProto containing only 3325 appended linear constraints in declared order.",
        "apply_steps": ["Verify compressed and raw identities.",
                       "Concatenate the entire accepted parent raw bytes and decompressed suffix raw bytes.",
                       "Require exact identity with the exported complete model bytes."],
        "parent_is_complete_raw_prefix": True, "complete_original_parent_bytes_recovered": True,
        "new_variables": 0, "replaced_rows": 0, "independent_full_model_replay_still_required": True}
    save(args.directory / "restoration-manifest.json", manifest)
    artifacts["restoration_manifest"] = binding(args.directory / "restoration-manifest.json")
    stage(args, "lossless_archives_full_row_ledger_and_manifest")
    return {"schema": "conway99.f0.triangle-incidence-native-preparation.v1",
        "status": PASS["prepare"], "inputs": cfg["inputs"], "authorities": cfg["authorities"],
        "authority_links": cfg["authority_links"], "runtime": runtime, "layout": LAYOUT,
        "parent_variables": PARENT_VARIABLES, "parent_rows": PARENT_ROWS, "variables": FINAL_VARIABLES, "rows": FINAL_ROWS,
        "family_order": FAMILY_ORDER, "family_counts": counts, "family_terms": terms,
        "row_keys_sha256": row_sha, "family_row_keys_sha256": family_sha, "family_row_jsonl_sha256": family_jsonl_sha,
        "parent_total_terms": parent_terms, "total_terms": total_terms, "term_change": 26916,
        "model_raw_bytes": len(raw), "model_raw_sha256": sha(raw),
        "model": {"raw_bytes": len(raw), "raw_sha256": sha(raw), "archive_bytes": len(archives["model.pb.gz"]),
                  "archive_sha256": sha(archives["model.pb.gz"])},
        "artifacts": artifacts, "restoration": restoration, "preservation": preservation,
        "incidence_check": checks, "literal_hashes": checks["literal_hashes"],
        "target_total_check": total_check, "target_total_report": cfg["inputs"]["target_total_report"],
        "target_total_root_acceptance": cfg["inputs"]["target_total_root_acceptance"], "native_transport": transport,
        "parent_is_complete_raw_prefix": True, "new_variables": 0, "replaced_rows": 0,
        "all_2904_side_rows_and_420_local_rows_retained": True, "global_target_total_row_retained": True,
        "Boolean_implication_classification_used_to_prune": False,
        "input_extraction_execution_accepted": False, "independent_literal_root_acceptance": cfg["inputs"]["incidence_root_acceptance"],
        "original_variable_ids_preserved": True, "objective_hint_assumption_or_graph_symmetry_added": False,
        "CpModel_constructed": True, "CpSolver_constructed": False, "native_optimizer_constructed": False,
        "native_query_run": False, "optimizer_calls": 0, "native_model_builds": 1,
        "independent_full_model_replay_still_required": True,
        "graph_constructed": False, "whole_component_excluded": False,
        "all_original_pair_caps_included": False, "second_component_completion_included": False,
        "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def worker(args):
    args.started = time.monotonic()
    args.stages = []
    try:
        cfg = load_configuration(args)
        result = controls(cfg, args) if args.mode == "controls" else prepare(cfg, args)
        result["source"] = binding(__file__)
        result["configuration"] = binding(args.configuration)
        result["maximum_seconds"] = cfg["limits"][args.mode + "_worker_seconds"]
        result["seconds_before_report_serialization"] = time.monotonic() - args.started
        save(args.directory / "stages.json", args.stages)
        result["stages"] = binding(args.directory / "stages.json")
        deadline_check(args.deadline)
        save(args.directory / "report.json", result)
        deadline_check(args.deadline)
    except BaseException as error:
        if not (args.directory / "stages.json").exists():
            save(args.directory / "stages.json", args.stages)
        save(args.directory / "error.json", {
            "type": type(error).__name__, "message": str(error), "traceback": traceback.format_exc(),
            "mode": args.mode, "report_accepted": False, "optimizer_calls": 0,
        })
        raise


def owned(args):
    started = time.monotonic()
    args.directory.mkdir(parents=True, exist_ok=False)
    owner = {
        "schema": "conway99.f0.triangle-incidence-native-owner.v1",
        "status": "ERROR_TRIANGLE_INCIDENCE_OWNER", "mode": args.mode,
        "source": binding(__file__), "configuration": binding(args.configuration),
        "report_accepted": False, "optimizer_calls": 0, "automatic_retries": 0,
        "CpSolver_constructed": False, "native_optimizer_constructed": False,
        "native_query_run": False, "supervision": None,
    }
    save(args.directory / "initial-owner.json", owner)
    limit = 15 if args.mode == "controls" else 135
    try:
        cfg = load_configuration(args)
        supervisor = bound_module("triangle_incidence_supervisor", cfg["sources"]["supervisor"])
        worker_limit = cfg["limits"][args.mode + "_worker_seconds"]
        command = [
            sys.executable, str(Path(__file__).resolve()), args.mode,
            "--configuration", str(args.configuration.resolve()),
            "--configuration-sha256", digest(args.configuration),
            "--directory", str(args.directory.resolve()),
            "--worker", "--deadline", str(started + worker_limit),
        ]
        assert not (args.directory / "supervisor.json").exists()
        supervision = supervisor.supervise(command, args.directory, started + limit)
        owner["supervision"] = supervision
        receipt = {
            "schema": "conway99.f0.triangle-incidence-owned-receipt.v1",
            "source": binding(__file__), "configuration": binding(args.configuration),
            "mode": args.mode, "supervision": supervision, "supervisor_record": binding(args.directory / "supervisor.json"),
            "seconds": time.monotonic() - started, "maximum_seconds": limit,
        }
        save(args.directory / "owned-receipt.json", receipt)
        owner["owned_receipt"] = binding(args.directory / "owned-receipt.json")
        assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
        assert supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
        assert time.monotonic() - started <= limit
        report_path = args.directory / "report.json"
        report = json.loads(report_path.read_bytes())
        assert report["status"] == PASS[args.mode]
        assert report["optimizer_calls"] == 0 and report["CpSolver_constructed"] is False
        assert report["native_optimizer_constructed"] is False and report["native_query_run"] is False
        same_ref(report["source"], owner["source"])
        same_ref(report["configuration"], owner["configuration"])
        owner.update(status=report["status"], report_accepted=True, report=binding(report_path),
                     CpModel_constructed=report["CpModel_constructed"])
    except BaseException as error:
        owner["error"] = {"type": type(error).__name__, "message": str(error)}
        save(args.directory / "owner-error.json", {"traceback": traceback.format_exc(), **owner["error"]})
    finally:
        elapsed = time.monotonic() - started
        owner.update(seconds=elapsed, maximum_seconds=limit, deadline_overrun_seconds=max(0.0, elapsed - limit))
        if elapsed > limit:
            owner.update(status="ERROR_TRIANGLE_INCIDENCE_OWNER_OVERRUN", report_accepted=False)
        save(args.directory / "owner.json", owner)
        print(json.dumps(owner, sort_keys=True), flush=True)
    return 0 if owner["report_accepted"] else 1

if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("controls", "prepare"))
    parser.add_argument("--configuration", required=True, type=Path)
    parser.add_argument("--configuration-sha256", required=True)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    assert not args.worker or args.deadline is not None
    if args.worker:
        worker(args)
    else:
        raise SystemExit(owned(args))
