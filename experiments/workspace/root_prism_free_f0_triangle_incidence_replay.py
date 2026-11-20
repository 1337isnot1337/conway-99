"""Independent protobuf-only replay of the triangle-incidence append.

Reconstruct triangle meanings from accepted native AND rows, compare the complete
saved indicator incidence, and inspect every appended constraint and all preserved
parent messages. The timed-out metadata extractor is only an untrusted proposal.
No producer, transport helper, CpModel, CpSolver, or native module is imported.
"""
import argparse
import gzip
import hashlib
import importlib.metadata
import json
import math
from pathlib import Path
import resource
import sys
import time
import traceback

ROOT = Path(__file__).resolve().parents[2]
PARENT_VARIABLES, PARENT_ROWS, PARENT_TERMS = 80730, 297470, 3310380
FINAL_ROWS, FINAL_TERMS = 300795, 3337296
PARENT_RAW_BYTES = 39306083
PARENT_RAW_SHA = "2961c95ce21c39f8ea8bda29ed3ac98c5075b921dedc96f71035f1b90f77ddb6"
PARENT_ROOT_SHA = "20fef49c4a6a1b190dfc2869d77152deb4afd53b4411e6ec92a0fad53cf209b1"
PARENT_CONFIG_SHA = "3fcf3a742a53cf200810aea92cfa594c2ef4623e54aa5679e8afbeda00409059"
MODEL_SCHEMA_SHA = "266b68151ffd6c9f5db22553442abd777031663d39e1cea649a8737f811d2eff"
EDGE_ORDER_SHA = "411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb"
DOMAIN_RAW_SHA = "fa3bd2e5bb541d58cb647aa1d3df95a9d3c17e394836a657ad4f4bf6eb5f6bfe"
EDGE_START, EDGE_STOP, TRIANGLE_START, TRIANGLE_COUNT = 540, 68934, 71382, 5364
AND_START, TARGET_START = 260042, 281498
CAP_FAMILIES = ["side_edge", "local_selector"]
CAP_COUNTS = {"side_edge": 2904, "local_selector": 420}
CAP_TERMS = {"side_edge": 10320, "local_selector": 16512}
FAMILIES = CAP_FAMILIES + ["global_target_total"]
COUNTS = {**CAP_COUNTS, "global_target_total": 1}
TERMS = {**CAP_TERMS, "global_target_total": 84}
LAYOUT = {"parent_variables": 80730, "parent_rows": 297470,
          "new_variables": 0, "replaced_rows": 0, "appended_rows": 3325, "appended_terms": 26916,
          "side_edge_start": 297470, "local_selector_start": 300374, "global_target_total_start": 300794,
          "variables": 80730, "rows": 300795,
          "triangle_variable_start": 71382, "triangle_variables": 5364}
SOURCES = {
    "base": "5a1e8026683a7782fce6ec2a2947748356ac9cd5adf32dd2a0663b0dd60bfca2",
    "supervisor": "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3",
    "parent_producer": "18de36bc0b741f13578fbd2be43580a9bf3c1440f68918c3a63f37e65d7fc12b",
    "parent_cold": "d955a93a7bf112f3c79ae9c6ffdd9f093b9b8d1f58df3ea25fe1bfba56f6b5e2",
    "incidence_producer": "3357917e76a94f2c79fdc5a65e00a3413ad1e019c63e4d5ae3400f7978f12699",
}
INPUTS = {"parent_model", "parent_configuration", "parent_report", "parent_owner",
          "parent_cold", "parent_cold_owner", "parent_root_acceptance", "domain",
          "indicator_inventory", "incidence_inventory", "incidence_finalization", "incidence_owner",
          "incidence_terminal_binding", "incidence_root_acceptance", "incidence_theorem_review",
          "incidence_literal_report", "incidence_literal_finalization", "incidence_literal_owner",
          "target_total_report", "target_total_finalization", "target_total_owner",
          "target_total_root_acceptance", "target_total_theorem_review"}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class Clock:
    def __init__(self, seconds):
        self.start = time.monotonic()
        self.seconds = seconds

    def check(self, stage):
        if time.monotonic() - self.start >= self.seconds:
            raise TimeoutError("independent triangle-incidence deadline: " + stage)

    def elapsed(self):
        return time.monotonic() - self.start


def compact(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def reject_constant(text):
    raise ValueError("nonfinite JSON constant: " + text)


def parse_json(raw):
    return json.loads(raw, parse_constant=reject_constant)


def relative_path(text):
    path = (ROOT / text).resolve()
    path.relative_to(ROOT)
    require(not Path(text).is_absolute() and ".." not in Path(text).parts, "relative repository path")
    return path


def file_ref(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": digest(raw), "bytes": len(raw)}


def read_ref(ref):
    raw = relative_path(ref["path"]).read_bytes()
    require(type(ref["bytes"]) is int and len(raw) == ref["bytes"], "reference byte count")
    require(digest(raw) == ref["sha256"], "reference SHA256: " + ref["path"])
    return raw


def equal_ref(first, second, name):
    require(first["path"] == second["path"] and first["sha256"] == second["sha256"], name)
    if "bytes" in first and "bytes" in second:
        require(first["bytes"] == second["bytes"], name + " bytes")


def json_ref(ref):
    raw = read_ref(ref)
    if ref["path"].endswith(".gz"):
        raw = gzip.decompress(raw)
    if "raw_sha256" in ref:
        require(digest(raw) == ref["raw_sha256"], "raw JSON identity")
    return parse_json(raw)


def save_new(path, raw):
    with Path(path).open("xb") as output:
        output.write(raw)


def no_native_imports():
    require(not any(name.startswith("ortools.sat.python") for name in sys.modules),
            "no native model/helper/solver import")


def row_key(lower, upper, pairs):
    require(type(lower) is type(upper) is int and -(1 << 63) <= lower <= upper < (1 << 63),
            "integer row domain")
    require(all(type(j) is type(c) is int and 0 <= j < PARENT_VARIABLES and c != 0
                and -(1 << 63) < c < (1 << 63) for j, c in pairs), "exact row terms")
    require(len({j for j, _ in pairs}) == len(pairs), "distinct row variables")
    return [lower, upper, sorted([list(item) for item in pairs])]


def expected_constraint(pb, key):
    lower, upper, pairs = key
    require(row_key(lower, upper, pairs) == key, "canonical expected row")
    row = pb.ConstraintProto()
    row.linear.domain.extend((lower, upper))
    for j, c in pairs:
        row.linear.vars.append(j)
        row.linear.coeffs.append(c)
    return row


def compare_row(actual, pb, key, label):
    require(actual.SerializeToString() == expected_constraint(pb, key).SerializeToString(),
            "complete ConstraintProto: " + label)


def owner_ok(owner, report_ref, source_ref, config_ref, schema, status, mode):
    require(owner["schema"] == schema and owner["status"] == status and owner["mode"] == mode,
            "owner header")
    require(owner["report_accepted"] is True and owner["maximum_seconds"] == 135,
            "owner acceptance and bound")
    require(owner["optimizer_calls"] == 0 and owner["CpSolver_constructed"] is False,
            "owner optimizer absence")
    require(type(owner["seconds"]) in (int, float) and math.isfinite(owner["seconds"])
            and 0 <= owner["seconds"] <= 135 and owner["deadline_overrun_seconds"] == 0, "owner time")
    child = owner["supervision"]
    require(child["status"] == "CHILD_EXITED" and child["returncode"] == 0
            and child["child_reaped"] is True and child["owned_process_group_stopped"] is True,
            "child exit and complete reap")
    require(0 <= child["seconds"] <= owner["seconds"], "supervision time")
    equal_ref(owner["report"], report_ref, "owned report")
    equal_ref(owner["source"], source_ref, "owned source")
    equal_ref(owner["configuration"], config_ref, "owned configuration")


def load_configuration(args, clock):
    ref = file_ref(args.configuration)
    require(ref["sha256"] == args.configuration_sha256, "configuration CLI identity")
    cfg = parse_json(read_ref(ref))
    require(cfg["schema"] == "conway99.f0.triangle-incidence-native-configuration.v1", "configuration schema")
    require(cfg["layout"] == LAYOUT and cfg["family_order"] == FAMILIES
            and cfg["expected_family_counts"] == COUNTS and cfg["expected_family_terms"] == TERMS,
            "fixed family layout")
    require(INPUTS <= set(cfg["inputs"]), "complete configured input namespace")
    require(set(SOURCES) | {"checker"} <= set(cfg["sources"]), "complete source namespace")
    equal_ref(cfg["sources"]["checker"], file_ref(__file__), "independent source identity")
    for name, expected in SOURCES.items():
        require(cfg["sources"][name]["sha256"] == expected, "frozen source " + name)
    for source in cfg["sources"].values():
        read_ref(source)
        clock.check("source bindings")
    require(cfg["proofs"] and cfg["reviews"], "proof and review bindings")
    for proof in cfg["proofs"] + cfg["reviews"]:
        read_ref(proof)
    require(cfg["limits"] == {"controls_worker_seconds": 10, "controls_owner_seconds": 15,
                             "prepare_worker_seconds": 120, "prepare_owner_seconds": 135},
            "preparation limits")
    require(cfg["optimizer_calls"] == cfg["automatic_retries"] == 0
            and cfg["native_query_authorized"] is False
            and cfg["independent_complete_protobuf_replay_required"] is True, "no optimizer authority")
    require(cfg["inputs"]["parent_root_acceptance"]["sha256"] == PARENT_ROOT_SHA
            and cfg["inputs"]["parent_configuration"]["sha256"] == PARENT_CONFIG_SHA, "accepted parent bindings")
    require(cfg["runtime"]["ortools"] == importlib.metadata.version("ortools") == "9.15.6755"
            and cfg["runtime"]["protobuf"] == importlib.metadata.version("protobuf") == "6.33.6",
            "pinned protobuf runtime")
    from ortools.sat import cp_model_pb2 as pb
    require(digest(pb.DESCRIPTOR.serialized_pb) == cfg["runtime"]["model_schema_sha256"] == MODEL_SCHEMA_SHA,
            "complete model descriptor")
    clock.check("configuration and runtime")
    no_native_imports()
    return cfg, ref, pb


def accepted_parent_receipts(cfg, clock):
    data = {}
    for name, ref in cfg["inputs"].items():
        if name != "parent_model":
            data[name] = json_ref(ref)
            clock.check("input " + name)
    seen = set()
    for authority in cfg["authorities"]:
        name, expected = authority["input"], authority["expected_status"]
        require(name not in seen and expected.startswith(("PASS_", "ROOT_ACCEPTS_", "OWNED_")),
                "declared successful authority")
        require(data[name][authority.get("status_field", "status")] == expected, "authority " + name)
        seen.add(name)
    untrusted = {"incidence_inventory", "incidence_terminal_binding", "incidence_finalization", "incidence_owner"}
    require(INPUTS - {"parent_model", "parent_configuration", "domain"} - untrusted <= seen,
            "complete successful authority statuses")
    require(not (untrusted & seen), "untrusted extraction records are not successful authorities")
    for link in cfg["authority_links"]:
        current = data[link["input"]]
        for field in link["fields"]:
            current = current[field]
        equal_ref(current, cfg["inputs"][link["target"]], "authority cross-reference")
    root, prep, cold, pcfg = [data[k] for k in
        ("parent_root_acceptance", "parent_report", "parent_cold", "parent_configuration")]
    require(root["schema"] == "conway99.f0.combined-extensions-native-root-acceptance.v1"
            and root["status"] == "ROOT_ACCEPTS_COMPLETE_COMBINED_EXTENSIONS_NATIVE_MODEL_AND_INDEPENDENT_COLD",
            "root accepted parent")
    require(prep["status"] == "PASS_COMPLETE_COMBINED_EXTENSIONS_NATIVE_PREPARATION"
            and cold["status"] == "PASS_INDEPENDENT_COMPLETE_COMBINED_EXTENSIONS_NATIVE_MODEL", "parent phases")
    require(pcfg["schema"] == "conway99.f0.combined-extensions-native-configuration.v1"
            and pcfg["source_sha256"] == SOURCES["parent_producer"], "parent producer configuration")
    for record in (root, prep, cold):
        require(record["model_raw_sha256"] == PARENT_RAW_SHA and record["model_raw_bytes"] == PARENT_RAW_BYTES
                and record["variables"] == PARENT_VARIABLES and record["rows"] == PARENT_ROWS
                and record["optimizer_calls"] == 0, "accepted parent identity")
    require(root["complete_original_parent_bytes_recovered"] is True
            and root["native_query_authorized_by_this_receipt"] is False, "parent acceptance scope")
    for field, alias in (("configuration", "parent_configuration"), ("preparation", "parent_report"),
                         ("independent_cold", "parent_cold"), ("model_archive", "parent_model")):
        equal_ref(root[field], cfg["inputs"][alias], "root parent cross-link")
    for record, name in ((prep, "parent_producer"), (cold, "parent_cold")):
        equal_ref(record["source"], cfg["sources"][name], "parent phase source")
        equal_ref(record["configuration"], cfg["inputs"]["parent_configuration"], "parent phase configuration")
    for field, alias in (("preparation_report", "parent_report"), ("preparation_owner", "parent_owner")):
        equal_ref(cold[field], cfg["inputs"][alias], "parent cold input")
    equal_ref(root["owners"]["preparation"], cfg["inputs"]["parent_owner"], "root preparation owner")
    equal_ref(root["owners"]["independent_cold"], cfg["inputs"]["parent_cold_owner"], "root cold owner")
    owner_ok(data["parent_owner"], cfg["inputs"]["parent_report"], cfg["sources"]["parent_producer"],
             cfg["inputs"]["parent_configuration"], "conway99.f0.combined-extensions-native-owner.v1",
             "PASS_COMPLETE_COMBINED_EXTENSIONS_NATIVE_PREPARATION", "prepare")
    owner_ok(data["parent_cold_owner"], cfg["inputs"]["parent_cold"], cfg["sources"]["parent_cold"],
             cfg["inputs"]["parent_configuration"], "conway99.f0.combined-extensions-independent-ci-owner.v1",
             "OWNED_COMPLETE_COMBINED_EXTENSIONS_NATIVE_COLD_ACCEPTED", "replay")
    for name, previous in (("domain", "domain"), ("indicator_inventory", "triangle_inventory")):
        equal_ref(pcfg["inputs"][previous], cfg["inputs"][name], "accepted literal input")
    validate_proposal_receipts(data, cfg)
    clock.check("accepted parent and untrusted proposal receipts")
    return data


def validate_proposal_receipts(data, cfg):
    inv, failed_final, failed_owner, descriptor = [data[name] for name in
        ("incidence_inventory", "incidence_finalization", "incidence_owner", "incidence_terminal_binding")]
    require(inv["schema"] == "conway99.f0.recorded-triangle-capacity-inventory.v1"
            and inv["status"] == "PASS_COMPLETE_SAVED_TRIANGLE_INCIDENCE_AND_SUFFICIENT_IMPLICATION_AUDIT",
            "untrusted proposal format, not execution acceptance")
    for field in ("complete_with_respect_to_saved_indicator_inventory",
                  "all_2904_side_proposals_preserved", "all_420_nonempty_local_proposals_preserved"):
        require(inv[field] is True, "proposal coverage assertion")
    require(inv["native_solver_calls"] == 0 and inv["existing_native_model_changed"] is False
            and inv["native_model_built"] is False and inv["full_model_nonredundancy_claimed"] is False,
            "proposal scope")
    equal_ref(inv["source"], cfg["sources"]["incidence_producer"], "untrusted proposal source")
    for field, alias in (("domain", "domain"), ("indicator", "indicator_inventory"),
                         ("combined_configuration", "parent_configuration")):
        equal_ref(inv["input_bindings"][field], cfg["inputs"][alias], "proposal frozen input")
    require(failed_final["schema"] == "conway99.f0.recorded-triangle-capacity-finalization.v1"
            and failed_final["status"] == "UNACCEPTED_METADATA_FINALIZATION_BUDGET_OVERRUN",
            "preserved original failed finalization")
    require(failed_final["report_sha256"] == cfg["inputs"]["incidence_inventory"]["sha256"]
            and failed_final["report_bytes"] == cfg["inputs"]["incidence_inventory"]["bytes"]
            and failed_final["total_milliseconds"] == 12196
            and failed_final["maximum_milliseconds"] == 10000 and failed_final["optimizer_calls"] == 0,
            "original overrun identity")
    require(failed_owner["schema"] == "conway99.f0.recorded-triangle-capacity-owned-execution.v1"
            and failed_owner["status"] == "UNACCEPTED_TRIANGLE_CAPACITY_METADATA_EXECUTION"
            and failed_owner["report_accepted"] is False and failed_owner["within_budget"] is False,
            "preserved original failed owner")
    require(failed_owner["elapsed_milliseconds"] == 17209 and failed_owner["maximum_milliseconds"] == 10000
            and failed_owner["worker_invocations"] == 1 and failed_owner["automatic_retries"] == 0
            and failed_owner["native_solver_calls"] == 0 and failed_owner["OS_child_constructed"] is False,
            "original failure has no retry or native execution")
    for field, alias in (("report", "incidence_inventory"), ("finalization", "incidence_finalization")):
        equal_ref(failed_owner[field], cfg["inputs"][alias], "failed owner reference")
    equal_ref(failed_owner["source"], cfg["sources"]["incidence_producer"], "failed owner source")
    require(failed_owner["configuration"]["sha256"] == inv["configuration_sha256"], "failed configuration")
    require(descriptor["schema"] == "conway99.f0.recorded-triangle-capacity-row-key-descriptor.v1"
            and descriptor["status"] == "SAVED_COMPLETE_ROW_KEY_DIGESTS_FROM_UNACCEPTED_METADATA_OVERRUN",
            "untrusted digest descriptor")
    require(descriptor["original_run_accepted"] is False
            and descriptor["original_report_is_untrusted_proposal_table"] is True
            and descriptor["independent_reconstruction_from_previously_accepted_indicator_data_required"] is True
            and descriptor["overrun_waived_or_relabelled"] is False
            and descriptor["extractor_rerun_performed"] is False, "failed execution never relabelled")
    for field, alias in (("report", "incidence_inventory"), ("finalization", "incidence_finalization"),
                         ("owner", "incidence_owner")):
        equal_ref(descriptor[field], cfg["inputs"][alias], "descriptor original reference")
    require(descriptor["family_order"] == CAP_FAMILIES and descriptor["family_row_counts"] == CAP_COUNTS
            and descriptor["family_term_counts"] == CAP_TERMS, "descriptor two-family scope")
    root, report, final, owner = [data[name] for name in
        ("incidence_root_acceptance", "incidence_literal_report",
         "incidence_literal_finalization", "incidence_literal_owner")]
    require(cfg["inputs"]["incidence_root_acceptance"]["sha256"]
            == "f5bfd2f0af981e9b8fd96931e78bda6d2648960e8d0ddd981e2777bae88afea0",
            "actual separate literal root receipt")
    require(root["schema"] == "conway99.f0.recorded-triangle-capacity-literal-root-acceptance.v1"
            and root["status"] == "ROOT_ACCEPTS_COMPLETE_RECORDED_TRIANGLE_CAPACITY_LITERAL_ROWS",
            "independent literal authority")
    require(report["schema"] == "conway99.f0.recorded-triangle-capacity-literal-replay.v1"
            and report["status"] == "PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_CAPACITY_ROWS",
            "actual separate literal report")
    require(final["schema"] == "conway99.f0.recorded-triangle-capacity-literal-finalization.v1"
            and final["status"] == "PASS_COMPLETE_SERIALIZATION_WITHIN_DECLARED_BOUND",
            "actual separate literal finalization")
    require(owner["schema"] == "conway99.f0.recorded-triangle-capacity-literal-owned-execution.v1"
            and owner["status"] == "PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_CAPACITY_LITERAL_EXECUTION",
            "actual separate literal owner")
    for field, alias in (("report", "incidence_literal_report"),
                         ("finalization", "incidence_literal_finalization"),
                         ("owner", "incidence_literal_owner")):
        equal_ref(root[field], cfg["inputs"][alias], "literal root terminal reference")
    for field in ("source", "configuration", "root_gate", "peer_review"):
        equal_ref(root[field], owner[field], "literal owner/root authority reference")
    equal_ref(root["source"], report["source"], "literal report source")
    require(report["configuration_sha256"] == root["configuration"]["sha256"], "literal configuration SHA")
    equal_ref(owner["report"], cfg["inputs"]["incidence_literal_report"], "literal owned report")
    equal_ref(owner["finalization"], cfg["inputs"]["incidence_literal_finalization"], "literal owned final")
    require(root["input_bindings"] == report["input_bindings"], "complete literal input map")
    for field, alias in (("domain", "domain"), ("indicator", "indicator_inventory"),
                         ("model_configuration", "parent_configuration"),
                         ("model_root", "parent_root_acceptance"),
                         ("proposal", "incidence_inventory"), ("proposal_finalization", "incidence_finalization"),
                         ("proposal_owner", "incidence_owner"), ("row_descriptor", "incidence_terminal_binding"),
                         ("theorem_review", "incidence_theorem_review")):
        equal_ref(root["input_bindings"][field], cfg["inputs"][alias], "literal proven input")
    equal_ref(root["input_bindings"]["producer_configuration"], failed_owner["configuration"],
              "literal original failed configuration")
    equal_ref(root["input_bindings"]["triangle_literal_root"],
              data["parent_configuration"]["inputs"]["triangle_literal_root_acceptance"],
              "previously accepted indicator support")
    equal_ref(root["model_root_acceptance"], cfg["inputs"]["parent_root_acceptance"], "literal native parent")
    require(any(item["path"] == root["input_bindings"]["theorem_note"]["path"]
                and item["sha256"] == root["input_bindings"]["theorem_note"]["sha256"]
                for item in cfg["proofs"]), "literal row theorem included in frozen proofs")
    require(owner["report_accepted"] is True and owner["worker_invocations"] == 1
            and owner["automatic_retries"] == 0 and owner["error"] is None
            and owner["maximum_milliseconds"] == 45000
            and 0 <= owner["elapsed_milliseconds"] <= 45000, "literal owner success and bound")
    require(final["report_sha256"] == cfg["inputs"]["incidence_literal_report"]["sha256"]
            and final["report_bytes"] == cfg["inputs"]["incidence_literal_report"]["bytes"]
            and final["maximum_milliseconds"] == 30000
            and 0 <= report["replay_milliseconds"] <= final["total_milliseconds"] <= 30000,
            "literal completed serialization within bound")
    require(root["source_finalization_milliseconds"] == final["total_milliseconds"]
            and root["outer_owner_milliseconds"] == owner["elapsed_milliseconds"], "literal receipt times")
    require(root["original_producer_execution_accepted"] is False
            and root["original_producer_overrun_waived_or_relabelled"] is False
            and root["redundancy_audit_accepted_by_this_receipt"] is False
            and root["independent_complete_native_replay_required"] is True
            and root["native_build_authorized_by_this_receipt"] is False
            and root["native_query_authorized_by_this_receipt"] is False, "literal root scope")
    require(report["failed_producer_execution_accepted"] is False
            and report["failed_producer_overrun_waived"] is False
            and report["producer_source_executed"] is False
            and report["redundancy_claims_accepted_by_this_report"] is False
            and report["every_proposed_native_key_and_origin_compared"] is True
            and report["future_complete_independent_native_replay_required"] is True, "literal report scope")
    require(final["original_failed_producer_remains_unaccepted"] is True
            and owner["original_failed_producer_execution_accepted"] is False, "no old failure waiver")
    for record in (root, report, final, owner):
        require(record["optimizer_calls"] == 0, "literal zero optimizers")
    for record in (root, report):
        require(record["parent_raw_sha256"] == PARENT_RAW_SHA
                and record["parent_variables"] == PARENT_VARIABLES and record["parent_rows"] == PARENT_ROWS
                and record["new_variables"] == 0 and record["appended_rows"] == 3324
                and record["appended_terms"] == 26832 and record["resulting_rows"] == 300794
                and record["family_order"] == CAP_FAMILIES and record["family_row_counts"] == CAP_COUNTS
                and record["family_term_counts"] == CAP_TERMS, "literal fixed dimensions")
    require(root["hashes"] == report["hashes"] and len(root["hashes"]) == 7, "seven literal exact digests")
    require(root["root_recomputed_all_seven_complete_hashes_from_saved_proposal"] is True
            and root["literal_replay_calls"] == 1 and root["producer_rerun_calls"] == 0
            and root["automatic_retries"] == 0, "separate complete literal verification")



def ordered_json(value):
    """JSON.stringify-compatible order for the accepted complete incidence digest."""
    return json.dumps(value, separators=(",", ":"), ensure_ascii=True, allow_nan=False).encode("utf-8")


def parse_parent(cfg, pb, clock):
    raw = gzip.decompress(read_ref(cfg["inputs"]["parent_model"]))
    require(len(raw) == PARENT_RAW_BYTES and digest(raw) == PARENT_RAW_SHA, "whole accepted parent bytes")
    parent = pb.CpModelProto()
    parent.ParseFromString(raw)
    require(parent.SerializeToString() == raw, "canonical parent protobuf")
    require(len(parent.variables) == PARENT_VARIABLES and len(parent.constraints) == PARENT_ROWS,
            "parent dimensions")
    require({field.name for field, _ in parent.ListFields()} <= {"name", "variables", "constraints"},
            "parent has no objective, assumption or hint")
    require(all(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
                for row in parent.constraints), "parent unconditional linear rows")
    edges = []
    incident = [[] for _ in range(480)]
    for j in range(EDGE_START, EDGE_STOP):
        item = parent.variables[j]
        words = item.name.split("_")
        require(len(words) == 4 and words[:2] == ["shared", "edge"], "original edge variable name")
        a, b = int(words[2]), int(words[3])
        require(0 <= a < b < 480 and item.name == "shared_edge_%03d_%03d" % (a, b)
                and list(item.domain) == [0, 1], "original literal edge")
        edge_id = j - EDGE_START
        edges.append([a, b])
        incident[a].append((edge_id, b))
        incident[b].append((edge_id, a))
    require(len(edges) == 68394 and digest(compact(edges)) == EDGE_ORDER_SHA,
            "complete original native edge order")
    require(all(list(parent.variables[a].domain) == [0, 1] for a in range(480)),
            "original Boolean selectors")
    clock.check("parent decode and edge namespace")
    return raw, parent, edges, incident


def decode_and_edges(parent, first_row, indicator, pb, edge_low, edge_high):
    """Recover the three native edge IDs from the existing upper AND rows."""
    edge_variables = []
    for offset in range(3):
        actual = parent.constraints[first_row + offset]
        require(actual.WhichOneof("constraint") == "linear", "native AND upper kind")
        ids = list(actual.linear.vars)
        require(len(ids) == 2 and edge_low <= ids[0] < edge_high and ids[1] == indicator,
                "native AND upper namespace")
        edge = ids[0]
        compare_row(actual, pb, row_key(0, 1, [(edge, 1), (indicator, -1)]), "triangle AND upper")
        edge_variables.append(edge)
    require(edge_variables == sorted(set(edge_variables)) and len(edge_variables) == 3,
            "three ordered distinct triangle edges")
    compare_row(parent.constraints[first_row + 3], pb,
                row_key(-2, 1, [(edge, -1) for edge in edge_variables] + [(indicator, 1)]),
                "triangle AND lower")
    return edge_variables


def domain_data(cfg, data, edges, clock):
    domain_raw = gzip.decompress(read_ref(cfg["inputs"]["domain"]))
    require(digest(domain_raw) == DOMAIN_RAW_SHA, "frozen raw domain")
    domain = data["domain"]
    require(parse_json(domain_raw) == domain, "exact domain JSON")
    h, arows, core = domain["signature_domain"], domain["component_adjacency_rows"], domain["component_core_rows"]
    require(len(h) == 480 and len(arows) == 18 and len(core) == 21, "fixed incidence dimensions")
    for i in range(18):
        require(type(arows[i]) is int and arows[i] == core[i + 3] >> 3, "core adjacency restriction")
        require(arows[i].bit_count() == 3 and not ((arows[i] >> i) & 1), "cubic simple component")
        for j in range(18):
            require(((arows[i] >> j) & 1) == ((arows[j] >> i) & 1), "symmetric component")
    masks, k0, q = [], [], []
    for a, triple in enumerate(h):
        require(len(triple) == 3 and triple == sorted(set(triple))
                and all(type(i) is int and 0 <= i < 18 for i in triple), "saved distinct signature")
        mask = sum(1 << i for i in triple)
        masks.append(mask)
        k = sum((arows[i] >> j) & 1 for position, i in enumerate(triple) for j in triple[position + 1:])
        require(k in (0, 1), "signature internal matching")
        k0.append(k)
        target = [2 - int(bool(mask & (1 << i))) - (arows[i] & mask).bit_count() for i in range(18)]
        require(target == domain["row_targets"][a] and sum(target[i] for i in triple) == 3 - 2 * k,
                "exact mixed targets and overlap-one total")
        q.append(target)
    require(len(set(masks)) == 480, "distinct saved signatures")
    for left, right in edges:
        require((masks[left] & masks[right]).bit_count() <= 1, "all original edges have overlap zero or one")
    clock.check("signature metadata and original edge overlaps")
    return h, masks, k0, q


def reconstruct_rows(cfg, data, parent, edges, incident, pb, clock):
    indicator = data["indicator_inventory"]
    require(indicator["status"] == "PASS_EXACT_SHARED_TRIANGLE_INDICATOR_INVENTORY"
            and len(indicator["triangles"]) == TRIANGLE_COUNT and len(indicator["targets"]) == 84,
            "accepted indicator dimensions")
    h, masks, k0, q = domain_data(cfg, data, edges, clock)
    by_edge, local = {}, [[] for _ in range(480)]
    triangle_vertices, triangle_edges = [None] * TRIANGLE_COUNT, [None] * TRIANGLE_COUNT
    seen_triangles = set()
    # Deliberately start from the accepted native definitions, in reverse triangle order.
    for t in range(TRIANGLE_COUNT - 1, -1, -1):
        native_var = TRIANGLE_START + t
        expected_var = pb.IntegerVariableProto(name="spectral_triangle_%04d" % t, domain=[0, 1])
        require(parent.variables[native_var].SerializeToString() == expected_var.SerializeToString(),
                "complete existing triangle variable")
        ev = decode_and_edges(parent, AND_START + 4 * t, native_var, pb, EDGE_START, EDGE_STOP)
        eids = [j - EDGE_START for j in ev]
        vertices = sorted({a for eid in eids for a in edges[eid]})
        require(len(vertices) == 3, "native AND edges form three vertices")
        a, b, c = vertices
        require([edges[eid] for eid in eids] == [[a, b], [a, c], [b, c]], "native AND edges form the triangle")
        require(tuple(vertices) not in seen_triangles, "distinct native triangles")
        seen_triangles.add(tuple(vertices))
        saved = indicator["triangles"][t]
        require(saved["triangle_index"] == t and saved["proposed_variable_index"] == 68934 + t
                and saved["vertices"] == vertices and saved["edge_ids"] == eids
                and len(saved["origins"]) == 1, "saved indicator agrees with native definition")
        triangle_vertices[t], triangle_edges[t] = vertices, eids
        for offset, eid in enumerate(eids):
            left, right = edges[eid]
            require(masks[left] & masks[right] == 0, "triangle pairwise signature disjointness")
            third = next(v for v in vertices if v != left and v != right)
            by_edge.setdefault(eid, []).append((t, third, AND_START + 4 * t + offset))
        for v in vertices:
            local[v].append(t)
        if t % 256 == 0:
            clock.check("native AND reconstruction")
    require(triangle_vertices == sorted(triangle_vertices), "complete saved triangle order")
    for entries in by_edge.values():
        entries.sort()
        require(len({third for _, third, _ in entries}) == len(entries), "distinct third vertices per edge")
    for entries in local:
        entries.sort()
    require(len(by_edge) == 6300, "complete native-derived edge incidence")
    target_ids = {}
    previous = -1
    target_multiplicity = [0] * TRIANGLE_COUNT
    for index, target in enumerate(indicator["targets"]):
        eid = target["edge_id"]
        require(type(eid) is int and previous < eid < len(edges) and eid in by_edge, "sorted target edges")
        previous = eid
        ids = [entry[0] for entry in by_edge[eid]]
        require(target["endpoints"] == edges[eid] and target["triangle_indices"] == ids,
                "complete native-derived target incidence")
        expected = row_key(0, 0, [(EDGE_START + eid, -1)] + [(TRIANGLE_START + t, 1) for t in ids])
        compare_row(parent.constraints[TARGET_START + index], pb, expected, "existing target equality")
        for t in ids:
            require(indicator["triangles"][t]["origins"][0]["target_edge_id"] == eid, "saved target origin")
            target_multiplicity[t] += 1
        target_ids[eid] = index
    require(target_multiplicity == [1] * TRIANGLE_COUNT, "every recorded triangle has exactly one target")
    proposal = data["incidence_inventory"]
    groups = {family: [] for family in CAP_FAMILIES}
    origins, all_edges, side_records, local_records, empty = [], [], [], [], []
    singleton_count = 0
    for eid in sorted(by_edge):
        entries = by_edge[eid]
        ids, thirds, upper_rows = [[entry[j] for entry in entries] for j in range(3)]
        rec = {"edge_id": eid, "endpoints": edges[eid], "triangle_indices": ids,
               "thirds": thirds, "and_upper_native_rows": upper_rows}
        if eid in target_ids:
            rec.update(disposition="existing_target_equality",
                       existing_target_native_row=TARGET_START + target_ids[eid])
        elif len(entries) == 1:
            rec["disposition"] = "existing_singleton_AND_upper"
            singleton_count += 1
        else:
            index = len(groups["side_edge"])
            rec.update(disposition="proposed_side_capacity", proposal_index=index)
            key = row_key(-1, 0, [(EDGE_START + eid, -1)] + [(TRIANGLE_START + t, 1) for t in ids])
            groups["side_edge"].append(key)
            saved = proposal["side_capacity_proposals"][index]
            require([saved["edge_id"], saved["endpoints"], saved["triangle_indices"],
                     saved["third_selectors"], saved["proposed_native_row_key"]]
                    == [eid, edges[eid], ids, thirds, key], "complete side proposal and origins")
            origins.append({"family": "side_edge", "proposal_index": index,
                            "native_row_index": PARENT_ROWS + len(origins),
                            "edge_id": eid, "endpoints": edges[eid],
                            "triangle_indices": ids, "third_selectors": thirds})
            side_records.append([eid, edges[eid], ids, thirds, key])
        all_edges.append(rec)
    require(all_edges == proposal["complete_edge_incidence"] and singleton_count == 3312,
            "every complete edge disposition and AND origin")
    mixed_rows_checked = degree_rows_checked = 0
    for a, ids in enumerate(local):
        if not ids:
            empty.append(a)
            continue
        cap, index = 2 + k0[a], len(groups["local_selector"])
        key = row_key(-cap, 0, [(a, -cap)] + [(TRIANGLE_START + t, 1) for t in ids])
        saved = proposal["local_capacity_proposals"][index]
        mixed_ids = [154430 + 18 * a + i for i in h[a]]
        require([saved["selector"], saved["k0"], saved["triangle_indices"], saved["proposed_native_row_key"],
                 saved["original_degree_native_row"], saved["overlap_one_mixed_native_rows"],
                 saved["overlap_one_degree_coefficient"], saved["overlap_zero_degree_coefficient"]]
                == [a, k0[a], ids, key, 153950 + a, mixed_ids, 3 - 2 * k0[a], 5 + 2 * k0[a]],
                "complete local proposal and equation origins")
        degree_key = row_key(0, 0, [(a, -8)] + [(EDGE_START + eid, 1) for eid, _ in incident[a]])
        compare_row(parent.constraints[153950 + a], pb, degree_key, "original degree meaning")
        degree_rows_checked += 1
        for i in h[a]:
            pairs = [(EDGE_START + eid, 1) for eid, b in incident[a] if masks[b] & (1 << i)]
            if q[a][i]:
                pairs.append((a, -q[a][i]))
            compare_row(parent.constraints[154430 + 18 * a + i], pb,
                        row_key(0, 0, pairs), "original mixed meaning")
            mixed_rows_checked += 1
        groups["local_selector"].append(key)
        origins.append({"family": "local_selector", "proposal_index": index,
                        "native_row_index": PARENT_ROWS + len(origins),
                        "selector": a, "k0": k0[a], "triangle_indices": ids})
        local_records.append([a, k0[a], ids, key, 153950 + a, mixed_ids])
    require(empty == proposal["local_empty_tautologies"] and len(empty) == 60, "all empty local dispositions")
    require({name: len(rows) for name, rows in groups.items()} == CAP_COUNTS, "complete family counts")
    require({name: sum(len(row[2]) for row in rows) for name, rows in groups.items()} == CAP_TERMS,
            "complete family term counts")
    require(len(proposal["side_capacity_proposals"]) == COUNTS["side_edge"]
            and len(proposal["local_capacity_proposals"]) == COUNTS["local_selector"], "no omitted proposals")
    rows = groups["side_edge"] + groups["local_selector"]
    hashes = {"row_keys_sha256": digest(compact(rows)),
              "side_row_keys_sha256": digest(compact(groups["side_edge"])),
              "local_row_keys_sha256": digest(compact(groups["local_selector"])),
              "complete_edge_incidence_sha256": digest(ordered_json(all_edges)),
              "side_records_sha256": digest(compact(side_records)),
              "local_records_sha256": digest(compact(local_records)),
              "local_empty_sha256": digest(compact(empty))}
    descriptor = data["incidence_terminal_binding"]
    require(hashes["row_keys_sha256"] == descriptor["row_keys_sha256"]
            and hashes["side_row_keys_sha256"] == descriptor["family_row_keys_sha256"]["side_edge"]
            and hashes["local_row_keys_sha256"] == descriptor["family_row_keys_sha256"]["local_selector"]
            and hashes["complete_edge_incidence_sha256"] == descriptor["complete_edge_incidence_sha256"],
            "complete untrusted descriptor digests independently rederived")
    require(hashes == data["incidence_root_acceptance"]["hashes"], "all seven accepted independent literal hashes")
    checks = {"complete_edges": 6300, "existing_target_equalities": 84,
              "existing_AND_constraints": 21456, "singleton_side_edges": 3312,
              "empty_local_selectors": empty, "local_k0": k0, "literal_hashes": hashes,
              "all_seven_literal_replay_hashes_independently_reconstructed": True}
    clock.check("complete native-derived row inventory")
    return rows, groups, origins, hashes, checks, {
        "original_degree_rows_rechecked": degree_rows_checked,
        "original_mixed_rows_rechecked": mixed_rows_checked,
        "complete_native_triangle_variable_messages_checked": TRIANGLE_COUNT,
        "complete_native_AND_constraint_messages_checked": 21456,
        "complete_native_target_equality_messages_checked": 84,
        "original_native_edge_variables_checked": 68394,
        "original_edge_overlap_zero_or_one_checked": 68394,
    }


def target_total_receipts(cfg, data):
    root, report, final, owner, review = [data[name] for name in
        ("target_total_root_acceptance", "target_total_report", "target_total_finalization",
         "target_total_owner", "target_total_theorem_review")]
    require(cfg["inputs"]["target_total_root_acceptance"]["sha256"]
            == "10dd8fbfd42dc695bae9c83a3f61f7b9694d940a092e8e67e034781fd3eb0ebc",
            "actual twelve-bound root receipt")
    require(root["schema"] == "conway99.f0.target-color-twelve-root-acceptance.v1"
            and root["status"] == "ROOT_ACCEPTS_EXACT_BOOLEAN_TWELVE_TARGET_BOUND", "twelve-bound authority")
    require(report["schema"] == "conway99.f0.target-color-twelve-certificate.v1"
            and report["status"] == "PASS_EXACT_STRUCTURAL_TWELVE_TARGET_BOUND_AND_COLOR_WITNESS",
            "actual structural report")
    require(final["schema"] == "conway99.f0.target-color-twelve-finalization.v1"
            and final["status"] == "PASS_COMPLETE_STRUCTURAL_CERTIFICATE_SERIALIZATION",
            "complete structural finalization")
    require(owner["schema"] == "conway99.f0.target-color-twelve-owner.v1"
            and owner["status"] == "OWNED_COMPLETE_STRUCTURAL_TWELVE_TARGET_CERTIFICATE_ACCEPTED",
            "complete structural owner")
    require(review["status"] == "PASS_COMPLETE_TWELVE_BOUND_PROOF_AND_FROZEN_SOURCE_REVIEW_UNRUN"
            and review["mathematical_gate_pass"] is True and review["source_gate_pass"] is True
            and review["concrete_blockers"] == [], "complete theorem review")
    for field, alias in (("report", "target_total_report"), ("finalization", "target_total_finalization"),
                         ("owner", "target_total_owner"), ("peer_review", "target_total_theorem_review")):
        equal_ref(root[field], cfg["inputs"][alias], "twelve-bound root reference")
    for field in ("source", "configuration", "proof", "proof_scope_correction"):
        equal_ref(owner[field], root[field], "twelve-bound owner reference")
    equal_ref(owner["source_review"], root["peer_review"], "twelve-bound owner review")
    equal_ref(owner["report"], cfg["inputs"]["target_total_report"], "twelve-bound owned report")
    equal_ref(owner["finalization"], cfg["inputs"]["target_total_finalization"], "twelve-bound owned final")
    equal_ref(report["source"], root["source"], "twelve-bound report source")
    equal_ref(root["model_root_acceptance"], cfg["inputs"]["parent_root_acceptance"], "twelve-bound native parent")
    require(report["configuration_sha256"] == root["configuration"]["sha256"]
            and root["input_bindings"] == report["inputs"], "twelve-bound complete inputs")
    for field, alias in (("domain", "domain"), ("indicator", "indicator_inventory"),
                         ("combined_configuration", "parent_configuration")):
        equal_ref(report["inputs"][field], cfg["inputs"][alias], "twelve-bound actual input")
    equal_ref(report["inputs"]["triangle_literal_root"],
              data["parent_configuration"]["inputs"]["triangle_literal_root_acceptance"],
              "twelve-bound accepted indicator support")
    require(any(item["path"] == root["proof"]["path"] and item["sha256"] == root["proof"]["sha256"]
                for item in cfg["proofs"]), "corrected twelve-bound proof included")
    require(owner["report_accepted"] is True and owner["within_budget"] is True
            and owner["worker_invocations"] == 1 and owner["automatic_retries"] == 0
            and owner["error"] is None and owner["maximum_milliseconds"] == 45000
            and owner["worker_maximum_milliseconds"] == 30000
            and 0 <= owner["elapsed_milliseconds"] <= 45000, "structural owner bound")
    require(final["report_sha256"] == cfg["inputs"]["target_total_report"]["sha256"]
            and final["report_bytes"] == cfg["inputs"]["target_total_report"]["bytes"]
            and final["maximum_milliseconds"] == 30000
            and 0 <= report["proof_check_milliseconds"] <= final["total_milliseconds"] <= 30000,
            "structural serialized result bound")
    require(root["source_finalization_milliseconds"] == final["total_milliseconds"]
            and root["outer_owner_milliseconds"] == owner["elapsed_milliseconds"], "structural receipt times")
    require(root["parent_raw_sha256"] == PARENT_RAW_SHA and root["parent_variables"] == PARENT_VARIABLES
            and root["parent_rows"] == PARENT_ROWS and root["Boolean_bound"] == 12
            and root["new_variables"] == 0 and root["additional_rows"] == 1
            and root["additional_terms"] == 84, "structural row dimensions")
    require(root["native_append_authorized_by_this_receipt"] is False
            and root["independent_complete_native_replay_required"] is True
            and root["full_model_feasible_witness_claimed"] is False
            and root["full_model_continuous_nonredundancy_claimed"] is False
            and root["all18_original_equality_quotas_saturated_by_witness_claimed"] is False,
            "Boolean theorem and restricted witness scope")
    require(report["Boolean_bound_proved"] is True and report["continuous_implication_claimed"] is False
            and report["full_model_nonredundancy_claimed"] is False and report["bound"] == 12
            and report["all_local_conditions_checked"] is True, "structural report scope")
    require(root["optimizer_calls"] == report["optimizer_calls"] == final["optimizer_calls"] == 0
            and owner["native_solver_calls"] == 0
            and root["assignment_enumerations"] == report["assignment_enumerations"]
            == final["assignment_enumerations"] == owner["assignment_enumerations"] == 0,
            "structural check had no assignment search or optimizer")
    return root, report


def add_target_total(cfg, data, parent, edges, pb, rows, groups, origins, clock):
    root, report = target_total_receipts(cfg, data)
    domain, inventory = data["domain"], data["indicator_inventory"]
    h, core, component = (domain["signature_domain"], domain["component_core_rows"],
                          domain["component_adjacency_rows"])
    target_edges = [[t["edge_id"], *edges[t["edge_id"]]] for t in inventory["targets"]]
    require(target_edges == sorted(target_edges) and len(target_edges) == 84
            and target_edges == report["edges"], "complete exact target-edge namespace")
    neighbors = {}
    for edge, a, b in target_edges:
        neighbors.setdefault(a, set()).add(b)
        neighbors.setdefault(b, set()).add(a)
        native_var = EDGE_START + edge
        for offset, selector in enumerate((a, b)):
            compare_row(parent.constraints[17162 + 2 * edge + offset], pb,
                        row_key(-1, 0, [(selector, -1), (native_var, 1)]), "target endpoint activation")
    vertices = sorted(neighbors)
    require(len(vertices) == 84, "all target vertices")
    color_pair = {}
    for a in vertices:
        present = [(i, j) for pos, i in enumerate(h[a]) for j in h[a][pos + 1:]
                   if (component[i] >> j) & 1]
        require(len(present) == 1, "one original core edge per target signature")
        color_pair[a] = present[0]
    colors = sorted(set(color_pair.values()))
    require(len(colors) == 18, "eighteen target colors")
    color_id = {pair: index for index, pair in enumerate(colors)}
    color = {a: color_id[color_pair[a]] for a in vertices}
    private = {a for a in vertices if color_pair[a][0] < 6 <= color_pair[a][1]}
    shared = set(vertices) - private
    pn = {a: sorted(neighbors[a] & private) for a in vertices}
    sn = {a: sorted(neighbors[a] & shared) for a in vertices}
    centers = {a for a in private if len(pn[a]) == 3}
    exposed = {a for a in private if sn[a]}
    require(len(private) == 72 and len(shared) == 12 and len(centers) == 12 and len(exposed) == 24,
            "private/shared structure")
    require(all(a in private or b in private for _, a, b in target_edges), "no shared-shared target edge")
    require(all(not (neighbors[a] & centers) for a in centers), "independent centers")
    require(all(not sn[a] for a in centers), "unexposed centers")
    require(all(len({color[b] for b in pn[a]}) <= 1 for a in private - centers),
            "one private-neighbor color for each noncenter")
    require(all(len(sn[a]) <= 1 for a in private), "one shared edge per private vertex")
    require(all(len(set(pn[a]) & exposed) <= 1 for a in centers), "one exposed leaf per center")
    require(all(not (a in exposed and b in exposed) for _, a, b in target_edges
                if a in private and b in private), "no exposed-exposed private edge")
    require(all(len(neighbors[a]) == 2 and len({color[b] for b in neighbors[a]}) == 1 for a in shared),
            "shared-neighbor metadata")
    # Rebuild all original Gram supports to recover the exact native row indices.
    gram, ordinal, native = {}, 0, 4440
    for i in range(18):
        for j in range(i, 18):
            support = [a for a, signature in enumerate(h) if i in signature and j in signature]
            rhs = 12 * int(i == j) + 2 - (core[i + 3] & core[j + 3]).bit_count() - ((core[i + 3] >> (j + 3)) & 1)
            gram[(i, j)] = {"original": ordinal, "native": native if support else None,
                            "quota": rhs, "support": support}
            if support:
                native += 1
            else:
                require(rhs == 0, "omitted Gram zero row")
            ordinal += 1
    require(ordinal == 171 and native == 4590, "complete original Gram ordering")
    color_records, private_gram = [], []
    for index, pair in enumerate(colors):
        metadata = gram[pair]
        selected = [a for a in vertices if color_pair[a] == pair]
        is_private = pair[0] < 6 <= pair[1]
        require(metadata["quota"] == 1 and metadata["native"] is not None
                and len(selected) == (6 if is_private else 2), "color size and quota")
        compare_row(parent.constraints[metadata["native"]], pb,
                    row_key(1, 1, [(a, 1) for a in metadata["support"]]), "actual native color Gram quota")
        color_records.append({"color_index": index, "core_edge": list(pair), "private": is_private,
                              "vertices": selected, "gram": metadata})
        if is_private:
            private_gram.append({"core_edge": list(pair), "original_row_id": metadata["original"],
                                 "native_row_id": metadata["native"], "quota": 1,
                                 "complete_support": metadata["support"], "target_support": selected})
    require(len(private_gram) == 12 and color_records == report["colors"]
            and private_gram == report["private_Gram_rows"], "complete color proof records")
    nodes = [{"selector": a, "signature": h[a], "color_index": color[a],
              "private": a in private, "center": a in centers, "exposed": a in exposed,
              "private_neighbors": pn[a], "shared_neighbors": sn[a],
              "private_neighbor_color_indices": sorted({color[b] for b in pn[a]})} for a in vertices]
    require(nodes == report["nodes"] and sorted(private) == report["private_vertices"]
            and sorted(shared) == report["shared_vertices"] and sorted(centers) == report["centers"]
            and sorted(exposed) == report["exposed_private_vertices"], "complete structural node records")
    witness = report["color_relaxation_attaining_witness"]
    chosen = witness["selected"]
    require(len(chosen) == len(set(chosen)) == 16 and set(chosen) <= set(vertices), "restricted witness vertices")
    require(all(sum(a in chosen for a in rec["vertices"]) <= 1 for rec in color_records),
            "restricted witness at-most-one color inequalities")
    witness_edges = [edge for edge, a, b in target_edges if a in chosen and b in chosen]
    require(len(set(chosen) & private) == 12 and len(witness_edges) == witness["edge_count"] == 12
            and witness_edges == witness["edge_ids"] and witness["full_model_feasible_claimed"] is False,
            "restricted witness attainment")
    require(all(sum(1 if a in private else 3 for a in rec["vertices"]) == 6 for rec in color_records)
            and len(target_edges) == 6 * 14, "exact fractional color-only control")
    key = row_key(0, 12, [(EDGE_START + edge, 1) for edge, _, _ in target_edges])
    key_sha = digest(compact(key))
    require(key == report["proposed_native_row_key"] == root["proposed_native_row_key"]
            and key_sha == report["proposed_row_key_sha256"] == root["proposed_native_row_key_sha256"]
            == "36c10df91bd844086786344beb942a2fd271e2cb9fafc6712f9168d215a7a446",
            "exact global target row")
    groups["global_target_total"] = [key]
    rows.append(key)
    origins.append({"family": "global_target_total", "proposal_index": 0, "native_row_index": 300794,
                    "target_edge_ids": [edge for edge, _, _ in target_edges], "target_count": 84,
                    "upper_bound": 12})
    clock.check("complete twelve-bound native premises and row")
    return {"complete_target_edges": 84, "complete_target_vertices": 84,
            "original_Gram_rows_rechecked": 18, "private_quota_one_Gram_rows": 12,
            "private_Gram_rows_checked": [item["native_row_id"] for item in private_gram],
            "original_endpoint_rows_rechecked": 168, "all_seven_structural_conditions_rechecked": True,
            "private_vertices": 72, "shared_vertices": 12, "centers": 12,
            "exposed_private_vertices": 24, "Boolean_bound": 12,
            "proposed_native_row_key_sha256": key_sha,
            "witness_scope": "At-most-one target-color inequalities and endpoint activations only.",
            "full_model_feasible_witness_claimed": False,
            "new_domain_or_triangle_census_calls": 0}


def message_digest(messages):
    value = hashlib.sha256()
    for item in messages:
        raw = item.SerializeToString()
        value.update(len(raw).to_bytes(8, "big"))
        value.update(raw)
    return value.hexdigest()


def preparation_records(cfg, configuration, args, clock):
    directory = args.preparation_directory.resolve()
    directory.relative_to(ROOT)
    report_ref, owner_ref = [file_ref(directory / name) for name in ("report.json", "owner.json")]
    require(report_ref["sha256"] == args.report_sha256 and owner_ref["sha256"] == args.owner_sha256,
            "complete preparation terminal CLI identities")
    report, owner = json_ref(report_ref), json_ref(owner_ref)
    require(report["schema"] == "conway99.f0.triangle-incidence-native-preparation.v1"
            and report["status"] == "PASS_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_PREPARATION",
            "successful preparation schema")
    source = report["source"]
    require(source["sha256"] == cfg["source_sha256"], "configured current producer source")
    read_ref(source)
    equal_ref(report["configuration"], configuration, "preparation configuration")
    owner_ok(owner, report_ref, source, configuration,
             "conway99.f0.triangle-incidence-native-owner.v1",
             "PASS_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_PREPARATION", "prepare")
    require(owner["automatic_retries"] == 0 and owner["CpModel_constructed"] is True
            and owner["native_optimizer_constructed"] is False and owner["native_query_run"] is False,
            "preparation owner zero optimizer")
    initial = json_ref(file_ref(directory / "initial-owner.json"))
    require(initial["schema"] == owner["schema"] and initial["status"] == "ERROR_TRIANGLE_INCIDENCE_OWNER"
            and initial["mode"] == "prepare" and initial["report_accepted"] is False
            and initial["supervision"] is None, "preserved preliminary owner")
    equal_ref(initial["source"], source, "initial owner source")
    equal_ref(initial["configuration"], configuration, "initial owner configuration")
    receipt_ref = file_ref(directory / "owned-receipt.json")
    equal_ref(owner["owned_receipt"], receipt_ref, "separate owned receipt")
    receipt = json_ref(receipt_ref)
    require(receipt["schema"] == "conway99.f0.triangle-incidence-owned-receipt.v1"
            and receipt["mode"] == "prepare" and receipt["maximum_seconds"] == 135
            and 0 <= receipt["seconds"] <= owner["seconds"], "separate successful supervision")
    equal_ref(receipt["source"], source, "owned receipt source")
    equal_ref(receipt["configuration"], configuration, "owned receipt configuration")
    equal_ref(receipt["supervisor_record"], file_ref(directory / "supervisor.json"), "supervisor file")
    supervision = json_ref(receipt["supervisor_record"])
    require(receipt["supervision"] == supervision == owner["supervision"], "all supervision receipts match")
    require(not (directory / "error.json").exists() and not (directory / "owner-error.json").exists(),
            "no hidden preparation failure")
    require(report["inputs"] == cfg["inputs"] and report["authorities"] == cfg["authorities"]
            and report["authority_links"] == cfg["authority_links"] and report["layout"] == LAYOUT,
            "complete preparation input and authority maps")
    require(report["parent_variables"] == PARENT_VARIABLES and report["parent_rows"] == PARENT_ROWS
            and report["variables"] == PARENT_VARIABLES and report["rows"] == FINAL_ROWS
            and report["parent_total_terms"] == PARENT_TERMS and report["total_terms"] == FINAL_TERMS
            and report["term_change"] == LAYOUT["appended_terms"], "preparation dimensions")
    require(report["family_order"] == FAMILIES and report["family_counts"] == COUNTS
            and report["family_terms"] == TERMS, "preparation complete family counts")
    true_fields = ("parent_is_complete_raw_prefix", "all_2904_side_rows_and_420_local_rows_retained",
                   "global_target_total_row_retained",
                   "original_variable_ids_preserved", "CpModel_constructed",
                   "independent_full_model_replay_still_required")
    false_fields = ("Boolean_implication_classification_used_to_prune", "input_extraction_execution_accepted",
                    "objective_hint_assumption_or_graph_symmetry_added", "CpSolver_constructed",
                    "native_optimizer_constructed", "native_query_run", "graph_constructed",
                    "whole_component_excluded", "all_original_pair_caps_included",
                    "second_component_completion_included")
    require(all(report[name] is True for name in true_fields)
            and all(report[name] is False for name in false_fields), "preparation exact scope flags")
    require(report["new_variables"] == report["replaced_rows"] == report["optimizer_calls"] == 0
            and report["native_model_builds"] == 1, "one preparation, no solver")
    equal_ref(report["independent_literal_root_acceptance"], cfg["inputs"]["incidence_root_acceptance"],
              "preparation separate literal authority")
    equal_ref(report["target_total_report"], cfg["inputs"]["target_total_report"], "preparation target theorem report")
    equal_ref(report["target_total_root_acceptance"], cfg["inputs"]["target_total_root_acceptance"],
              "preparation target theorem root authority")
    require(report["maximum_seconds"] == 120
            and 0 <= report["seconds_before_report_serialization"] <= 120, "preparation worker bound")
    for name in ("ortools", "protobuf", "model_schema_sha256", "cp_model_sha256", "native_helper_sha256"):
        require(report["runtime"][name] == cfg["runtime"][name], "preparation runtime " + name)
    transport = report["native_transport"]
    require(transport["complete_byte_comparison"] is True and transport["public_parse_return"] is True
            and transport["native_validation"] == "" and transport["optimizer_calls"] == 0
            and transport["CpSolver_constructed"] is False, "native transport receipt")
    equal_ref(report["stages"], file_ref(directory / "stages.json"), "complete preparation stage file")
    stages = json_ref(report["stages"])
    expected_stages = ["accepted_parent_and_all_proposal_receipts",
                       "all_unfiltered_capacities_and_target_total_row_rebuilt",
                       "constraint_only_suffix_and_whole_parent_preservation",
                       "public_native_transport_and_exact_export",
                       "lossless_archives_full_row_ledger_and_manifest"]
    require([item["phase"] for item in stages] == expected_stages, "complete preparation stage order")
    times = [item["elapsed_seconds"] for item in stages]
    require(times == sorted(times) and all(type(t) in (int, float) and math.isfinite(t) and 0 <= t <= 120
                                         for t in times), "bounded monotone stages")
    names = {"model": "model.pb", "model_archive": "model.pb.gz", "suffix_archive": "suffix.pb.gz",
             "row_ledger": "append-rows.json.gz", "restoration_manifest": "restoration-manifest.json"}
    require(set(report["artifacts"]) == set(names), "complete preparation artifacts")
    raw_artifacts = {}
    for key, filename in names.items():
        expected = file_ref(directory / filename)
        equal_ref(report["artifacts"][key], expected, "preparation artifact " + key)
        raw_artifacts[key] = read_ref(expected)
        clock.check("preparation artifact " + key)
    return report, owner, report_ref, owner_ref, source, raw_artifacts


def full_model_check(parent_raw, parent, full_raw, suffix_raw, rows, pb, clock):
    """Inspect whole old messages and complete new messages, including metadata."""
    require(full_raw == parent_raw + suffix_raw, "exact complete parent plus suffix bytes")
    model, suffix = pb.CpModelProto(), pb.CpModelProto()
    model.ParseFromString(full_raw)
    suffix.ParseFromString(suffix_raw)
    require(model.SerializeToString() == full_raw and suffix.SerializeToString() == suffix_raw,
            "canonical complete and suffix protobuf bytes")
    require(len(model.variables) == len(parent.variables)
            and len(model.constraints) == len(parent.constraints) + len(rows), "exact native dimensions")
    require({field.name for field, _ in suffix.ListFields()} == {"constraints"}
            and len(suffix.constraints) == len(rows), "suffix contains only appended constraints")
    for index, original in enumerate(parent.variables):
        require(model.variables[index].SerializeToString() == original.SerializeToString(),
                "complete original variable message")
    for index, original in enumerate(parent.constraints):
        require(model.constraints[index].SerializeToString() == original.SerializeToString(),
                "complete original constraint message")
        if index % 8192 == 0:
            clock.check("original message prefix")
    for offset, key in enumerate(rows):
        compare_row(model.constraints[len(parent.constraints) + offset], pb, key, "new complete model row")
        compare_row(suffix.constraints[offset], pb, key, "new complete suffix row")
        if offset % 512 == 0:
            clock.check("appended row messages")
    recovered = pb.CpModelProto()
    recovered.CopyFrom(model)
    del recovered.constraints[len(parent.constraints):]
    require(recovered.SerializeToString() == parent_raw, "recover exact full original parent message")
    expected_suffix = pb.CpModelProto()
    for key in rows:
        expected_suffix.constraints.add().CopyFrom(expected_constraint(pb, key))
    require(expected_suffix.SerializeToString() == suffix_raw, "all suffix fields are exactly expected")
    parent_terms = sum(len(row.linear.vars) for row in parent.constraints)
    all_terms = sum(len(row.linear.vars) for row in model.constraints)
    require(all_terms - parent_terms == sum(len(key[2]) for key in rows), "exact appended coefficient count")
    clock.check("complete protobuf preservation and row inspection")
    return model, {"complete_parent_raw_prefix_preserved": True,
                   "complete_original_parent_bytes_recovered": True,
                   "all_original_variable_messages_preserved": True,
                   "all_original_constraint_messages_preserved": True,
                   "original_variable_messages_sha256": message_digest(parent.variables),
                   "original_constraint_messages_sha256": message_digest(parent.constraints),
                   "parent_variables": len(parent.variables), "parent_rows": len(parent.constraints),
                   "new_variables": 0, "replaced_rows": 0}, parent_terms, all_terms


def inspect_exports(cfg, configuration, source, report, raw, parent_raw, parent,
                    rows, groups, origins, hashes, incidence_checks, target_checks, pb, clock):
    full_raw = raw["model"]
    require(gzip.decompress(raw["model_archive"]) == full_raw, "lossless complete archive")
    suffix_raw = gzip.decompress(raw["suffix_archive"])
    model, preservation, parent_terms, all_terms = full_model_check(
        parent_raw, parent, full_raw, suffix_raw, rows, pb, clock)
    require(len(model.variables) == PARENT_VARIABLES and len(model.constraints) == FINAL_ROWS
            and parent_terms == PARENT_TERMS and all_terms == FINAL_TERMS, "complete final model dimensions")
    require(report["preservation"] == preservation, "complete preservation report")
    require(report["model_raw_sha256"] == digest(full_raw) and report["model_raw_bytes"] == len(full_raw),
            "flat model identity")
    require(report["model"] == {"raw_bytes": len(full_raw), "raw_sha256": digest(full_raw),
                               "archive_bytes": len(raw["model_archive"]),
                               "archive_sha256": digest(raw["model_archive"])}, "full model identity")
    rows_sha = digest(compact(rows))
    family_sha = {name: digest(compact(value)) for name, value in groups.items()}
    jsonl_sha = {name: digest(b"".join(compact(key) + b"\n" for key in value))
                 for name, value in groups.items()}
    require(report["row_keys_sha256"] == rows_sha and report["family_row_keys_sha256"] == family_sha
            and report["family_row_jsonl_sha256"] == jsonl_sha, "all complete proposed-row hashes")
    require(report["literal_hashes"] == hashes and report["incidence_check"] == incidence_checks,
            "all independent incidence meanings")
    expected_target_check = {"bound": 12, "target_edges": 84,
        "private_Gram_rows_checked": target_checks["private_Gram_rows_checked"],
        "private_vertices": 72, "row_key_sha256": target_checks["proposed_native_row_key_sha256"],
        "structural_theorem_root_acceptance": cfg["inputs"]["target_total_root_acceptance"],
        "structural_condition_census_repeated": False}
    require(report["target_total_check"] == expected_target_check, "producer exact target-row premise receipt")
    expected_ledger = {
        "schema": "conway99.f0.triangle-incidence-appended-row-ledger.v1",
        "source": report["source"], "configuration": report["configuration"],
        "incidence_inventory": cfg["inputs"]["incidence_inventory"],
        "incidence_terminal_binding": cfg["inputs"]["incidence_terminal_binding"],
        "family_order": FAMILIES, "family_counts": COUNTS, "family_terms": TERMS,
        "row_keys": rows, "row_origins": origins, "row_keys_sha256": rows_sha,
        "family_row_keys_sha256": family_sha, "literal_hashes": hashes,
        "all_side_and_nonempty_local_proposals_preserved": True,
        "Boolean_implication_classification_used_to_prune": False,
        "input_extraction_execution_accepted": False,
        "independent_literal_root_acceptance": cfg["inputs"]["incidence_root_acceptance"],
        "target_total_report": cfg["inputs"]["target_total_report"],
        "target_total_root_acceptance": cfg["inputs"]["target_total_root_acceptance"],
        "global_target_total_row_retained": True}
    ledger_raw = gzip.decompress(raw["row_ledger"])
    require(ledger_raw == compact(expected_ledger) + b"\n", "complete row ledger bytes and origins")
    restoration = {"parent_raw_bytes": len(parent_raw), "parent_raw_sha256": digest(parent_raw),
                   "suffix_raw_bytes": len(suffix_raw), "suffix_raw_sha256": digest(suffix_raw)}
    require(report["restoration"] == restoration, "restoration exact raw identities")
    artifacts = {name: value for name, value in report["artifacts"].items() if name != "restoration_manifest"}
    expected_manifest = {
        "schema": "conway99.f0.triangle-incidence-restoration.v1",
        "status": "PASS_EXACT_TRIANGLE_INCIDENCE_PARENT_AND_SUFFIX_RESTORATION",
        "source": report["source"], "configuration": report["configuration"],
        "parent_model": cfg["inputs"]["parent_model"],
        "parent_root_acceptance": cfg["inputs"]["parent_root_acceptance"],
        "layout": LAYOUT, "artifacts": artifacts, "restoration": restoration,
        "suffix_format": "CpModelProto containing only 3325 appended linear constraints in declared order.",
        "apply_steps": ["Verify compressed and raw identities.",
                        "Concatenate the entire accepted parent raw bytes and decompressed suffix raw bytes.",
                        "Require exact identity with the exported complete model bytes."],
        "parent_is_complete_raw_prefix": True, "complete_original_parent_bytes_recovered": True,
        "new_variables": 0, "replaced_rows": 0, "independent_full_model_replay_still_required": True}
    require(raw["restoration_manifest"] == compact(expected_manifest) + b"\n",
            "complete restoration manifest bytes")
    clock.check("lossless artifacts, complete ledgers and restoration")
    return preservation, restoration, rows_sha, family_sha, jsonl_sha


def controls(cfg, pb, clock):
    parent = pb.CpModelProto(name="independent triangle incidence controls")
    for name in ("edge0", "edge1", "edge2", "indicator", "selector"):
        parent.variables.add(name=name, domain=[0, 1])
    for edge in range(3):
        parent.constraints.add().CopyFrom(expected_constraint(pb, row_key(0, 1, [(edge, 1), (3, -1)])))
    parent.constraints.add().CopyFrom(expected_constraint(
        pb, row_key(-2, 1, [(0, -1), (1, -1), (2, -1), (3, 1)])))
    require(decode_and_edges(parent, 0, 3, pb, 0, 3) == [0, 1, 2], "tiny native AND recovery")
    large = (1 << 53) + 1
    parent.constraints.add().CopyFrom(expected_constraint(pb, row_key(-large, large, [(4, large)])))
    old_raw = parent.SerializeToString()
    rows = [row_key(-1, 0, [(0, -1), (3, 1)]), row_key(-2, 0, [(3, 1), (4, -2)])]
    suffix = pb.CpModelProto()
    for key in rows:
        suffix.constraints.add().CopyFrom(expected_constraint(pb, key))
    suffix_raw = suffix.SerializeToString()
    full_raw = old_raw + suffix_raw
    accepted, preservation, _, _ = full_model_check(old_raw, parent, full_raw, suffix_raw, rows, pb, clock)
    require(accepted.constraints[4].linear.coeffs[0] == large
            and list(accepted.constraints[4].linear.domain) == [-large, large], "integer wire precision")
    require(preservation["complete_original_parent_bytes_recovered"] is True, "tiny exact restoration")
    rejected = []
    def must_reject(label, call):
        try:
            call()
        except AssertionError:
            rejected.append(label)
            return
        raise AssertionError("mutation unexpectedly accepted: " + label)

    old_changed = pb.CpModelProto()
    old_changed.CopyFrom(parent)
    old_changed.variables[0].name += "_changed"
    must_reject("original variable bytes", lambda: full_model_check(
        old_raw, parent, old_changed.SerializeToString() + suffix_raw, suffix_raw, rows, pb, clock))
    old_changed.CopyFrom(parent)
    old_changed.constraints[0].linear.coeffs[0] = 2
    must_reject("original constraint bytes", lambda: full_model_check(
        old_raw, parent, old_changed.SerializeToString() + suffix_raw, suffix_raw, rows, pb, clock))
    for label, mutation in (
        ("new coefficient", lambda item: item.linear.coeffs.__setitem__(0, -2)),
        ("new domain", lambda item: item.linear.domain.__setitem__(1, 1)),
        ("new name metadata", lambda item: setattr(item, "name", "unapproved")),
        ("new enforcement", lambda item: item.enforcement_literal.append(4)),
    ):
        changed = pb.CpModelProto()
        changed.CopyFrom(suffix)
        mutation(changed.constraints[0])
        changed_raw = changed.SerializeToString()
        must_reject(label, lambda value=changed_raw: full_model_check(
            old_raw, parent, old_raw + value, value, rows, pb, clock))
    changed = pb.CpModelProto(name="unapproved suffix name")
    changed.constraints.extend(suffix.constraints)
    changed_raw = changed.SerializeToString()
    must_reject("suffix global metadata", lambda: full_model_check(
        old_raw, parent, old_raw + changed_raw, changed_raw, rows, pb, clock))
    changed = pb.CpModelProto()
    changed.constraints.extend(reversed(suffix.constraints))
    changed_raw = changed.SerializeToString()
    must_reject("new row order", lambda: full_model_check(
        old_raw, parent, old_raw + changed_raw, changed_raw, rows, pb, clock))
    and_changed = pb.CpModelProto()
    and_changed.CopyFrom(parent)
    and_changed.constraints[3].linear.domain[0] = -3
    must_reject("AND lower meaning", lambda: decode_and_edges(and_changed, 0, 3, pb, 0, 3))
    and_changed.CopyFrom(parent)
    and_changed.constraints[0].linear.coeffs[1] = 1
    must_reject("AND upper meaning", lambda: decode_and_edges(and_changed, 0, 3, pb, 0, 3))
    # Exhaust the complete four-variable truth table for the decoded triangle AND.
    and_assignments = 0
    for mask in range(16):
        values = [(mask >> bit) & 1 for bit in range(4)]
        valid = True
        for row in parent.constraints[:4]:
            activity = sum(coefficient * values[index]
                           for index, coefficient in zip(row.linear.vars, row.linear.coeffs))
            valid &= row.linear.domain[0] <= activity <= row.linear.domain[1]
        require(bool(valid) == (values[3] == (values[0] & values[1] & values[2])), "exact AND truth table")
        and_assignments += 1
    rounded_cases = 0
    for k0 in (0, 1):
        for x in (0, 1):
            for triangle_total in range(6):
                if 2 * triangle_total <= (5 + 2 * k0) * x:
                    require(triangle_total <= (2 + k0) * x, "integer local rounding")
                rounded_cases += 1
    ordered_control = [{"z": 1, "a": [2]}]
    require(ordered_json(ordered_control) != compact(ordered_control)
            and parse_json(ordered_json(ordered_control)) == parse_json(compact(ordered_control)),
            "ordered incidence digest differs from sorted-key JSON for the same object")
    clock.check("complete toy controls")
    no_native_imports()
    return {"schema": "conway99.f0.triangle-incidence-independent-controls.v1",
            "status": "PASS_TRIANGLE_INCIDENCE_INDEPENDENT_REPLAY_CONTROLS",
            "toy_parent_variables": 5, "toy_parent_rows": 5, "toy_append_rows": 2,
            "mutations_rejected": rejected, "and_truth_assignments": and_assignments,
            "local_integer_rounding_cases": rounded_cases, "exact_large_wire_integer": large,
            "whole_parent_and_suffix_recovery_checked": True, "complete_ConstraintProto_comparison": True,
            "actual_model_or_inventory_decoded": False, "CpModel_constructed": False,
            "CpSolver_constructed": False, "native_optimizer_constructed": False,
            "native_query_run": False, "native_model_builds": 0, "optimizer_calls": 0}


def replay(cfg, configuration, pb, args, clock):
    data = accepted_parent_receipts(cfg, clock)
    preparation, owner, prep_ref, owner_ref, producer, raw = preparation_records(cfg, configuration, args, clock)
    parent_raw, parent, edges, incident = parse_parent(cfg, pb, clock)
    rows, groups, origins, hashes, checks, meaning_checks = reconstruct_rows(
        cfg, data, parent, edges, incident, pb, clock)
    target_checks = add_target_total(cfg, data, parent, edges, pb, rows, groups, origins, clock)
    require({family: len(value) for family, value in groups.items()} == COUNTS
            and {family: sum(len(key[2]) for key in value) for family, value in groups.items()} == TERMS,
            "complete three-family reconstruction")
    require(len(rows) == len(origins) == LAYOUT["appended_rows"], "complete independent row origins")
    preservation, restoration, rows_sha, family_sha, jsonl_sha = inspect_exports(
        cfg, configuration, producer, preparation, raw, parent_raw, parent,
        rows, groups, origins, hashes, checks, target_checks, pb, clock)
    no_native_imports()
    return {"schema": "conway99.f0.triangle-incidence-independent-cold.v1",
            "status": "PASS_INDEPENDENT_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_MODEL",
            "preparation_report": prep_ref, "preparation_owner": owner_ref,
            "parent_root_acceptance": cfg["inputs"]["parent_root_acceptance"],
            "independent_literal_root_acceptance": cfg["inputs"]["incidence_root_acceptance"],
            "target_total_root_acceptance": cfg["inputs"]["target_total_root_acceptance"],
            "inputs": cfg["inputs"], "layout": LAYOUT,
            "variables": PARENT_VARIABLES, "rows": FINAL_ROWS, "total_terms": FINAL_TERMS,
            "parent_variables": PARENT_VARIABLES, "parent_rows": PARENT_ROWS,
            "parent_total_terms": PARENT_TERMS, "new_variables": 0, "replaced_rows": 0,
            "appended_rows": len(rows), "appended_terms": LAYOUT["appended_terms"],
            "family_order": FAMILIES, "family_counts": COUNTS, "family_terms": TERMS,
            "row_keys_sha256": rows_sha, "family_row_keys_sha256": family_sha,
            "family_row_jsonl_sha256": jsonl_sha, "literal_hashes": hashes,
            "all_seven_literal_hashes_rederived_from_native_AND_meanings": True,
            "incidence_check": checks, "native_premise_checks": meaning_checks,
            "target_total_check": target_checks, "preservation": preservation, "restoration": restoration,
            "model_raw_sha256": digest(raw["model"]), "model_raw_bytes": len(raw["model"]),
            "model_archive_sha256": digest(raw["model_archive"]),
            "model_archive_bytes": len(raw["model_archive"]),
            "base_restoration_sha256": digest(parent_raw), "base_restoration_bytes": len(parent_raw),
            "artifacts": preparation["artifacts"],
            "complete_original_parent_bytes_recovered": True,
            "all_original_variable_and_constraint_messages_preserved": True,
            "all_appended_complete_constraint_messages_independently_checked": True,
            "complete_row_origins_and_lossless_restoration_checked": True,
            "all_side_and_nonempty_local_proposals_retained": True,
            "global_target_total_row_independently_checked": True,
            "Boolean_implication_classification_used_to_prune": False,
            "original_failed_extractor_execution_accepted": False,
            "original_extractor_overrun_waived": False,
            "original_extractor_or_literal_producer_imported": False,
            "native_transport_or_preparation_producer_imported": False,
            "CpModel_constructed": False, "CpSolver_constructed": False,
            "native_optimizer_constructed": False, "native_query_run": False,
            "optimizer_calls": 0, "native_model_builds": 0,
            "native_query_authorized_by_this_report": False,
            "all_original_pair_caps_included": False, "second_component_completion_included": False,
            "graph_constructed": False, "whole_component_excluded": False,
            "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("controls", "replay"))
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--configuration-sha256", required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation-directory", type=Path)
    parser.add_argument("--report-sha256")
    parser.add_argument("--owner-sha256")
    args = parser.parse_args()
    limit = 10 if args.mode == "controls" else 120
    clock = Clock(limit)
    args.directory = args.directory.resolve()
    args.directory.relative_to(ROOT)
    args.directory.mkdir(parents=True, exist_ok=False)
    try:
        if args.mode == "replay":
            require(args.preparation_directory is not None and args.report_sha256 and args.owner_sha256,
                    "complete preparation references required")
        else:
            require(args.preparation_directory is None and args.report_sha256 is None and args.owner_sha256 is None,
                    "controls use no actual preparation")
        cfg, configuration, pb = load_configuration(args, clock)
        result = controls(cfg, pb, clock) if args.mode == "controls" else replay(
            cfg, configuration, pb, args, clock)
        result.update(source=file_ref(__file__), configuration=configuration, mode=args.mode,
                      maximum_seconds=limit, seconds_before_report_serialization=clock.elapsed(),
                      automatic_retries=0)
        clock.check("before final report serialization")
        serialized = compact(result) + b"\n"
        require(len(serialized) <= 1048576, "independent report byte bound")
        save_new(args.directory / "report.json", serialized)
        clock.check("after complete report write")
        print(json.dumps({"status": result["status"], "report": file_ref(args.directory / "report.json"),
                          "seconds": clock.elapsed(), "optimizer_calls": 0}, sort_keys=True), flush=True)
        return 0
    except BaseException as error:
        failure = {"schema": "conway99.f0.triangle-incidence-independent-error.v1",
                   "status": "ERROR_INDEPENDENT_TRIANGLE_INCIDENCE_REPLAY", "mode": args.mode,
                   "type": type(error).__name__, "message": str(error),
                   "traceback": traceback.format_exc(), "report_accepted": False,
                   "seconds": clock.elapsed(), "maximum_seconds": limit,
                   "optimizer_calls": 0, "native_query_run": False}
        save_new(args.directory / "error.json", compact(failure) + b"\n")
        print(json.dumps({"status": failure["status"], "message": str(error)}, sort_keys=True), flush=True)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
