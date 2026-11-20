"""Independent complete protobuf replay of the certified triangle-zero append.

Read the accepted arithmetic receipts, derive the ascending zero-indicator rows,
recover their native AND meanings, and compare every original and appended
protobuf message. No producer, native helper, CpModel, or CpSolver is imported.
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
PARENT_VARIABLES, PARENT_ROWS, PARENT_TERMS = 80730, 300795, 3337296
FINAL_ROWS, FINAL_TERMS = 303951, 3340452
PARENT_RAW_BYTES = 39512348
PARENT_RAW_SHA = "56f6be31b4714825fb6d546ca79420e0ee0d25da05231a0eea322e514473bed8"
PARENT_ROOT_SHA = "bb744c426034992ddae1702cdb479e61d17d9a2fa5da2a614f4d6c15643908f0"
PARENT_CONFIG_SHA = "79d98a25898bef1a9a3340546e0721949f79464f39756d881d8469af81ccc1fd"
PRODUCER_SHA = "a3512a083ec480d36b823273ec7ba7eb3f47ff05efaed4a3b0e62346e4fba36c"
FORWARD_SHA = "31789e7cb6012e8d0f3545170bfa19daec752027b4cd1c7a6bc013749cc146f1"
ZERO_KEYS_SHA = "68cbeeb785a7d68e7141464bd3c9c9274bebddcd33875ea4c843494f2da44b4c"
MODEL_SCHEMA_SHA = "266b68151ffd6c9f5db22553442abd777031663d39e1cea649a8737f811d2eff"
FAMILIES = ["gap_triangle_zero"]
COUNTS = TERMS = {"gap_triangle_zero": 3156}
LAYOUT = {"parent_variables": 80730, "parent_rows": 300795,
          "new_variables": 0, "replaced_rows": 0, "appended_rows": 3156, "appended_terms": 3156,
          "gap_triangle_zero_start": 300795, "variables": 80730, "rows": 303951,
          "triangle_variable_start": 71382, "triangle_variables": 5364}
SOURCES = {
    "base": "5a1e8026683a7782fce6ec2a2947748356ac9cd5adf32dd2a0663b0dd60bfca2",
    "supervisor": "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3",
    "parent_producer": "29d289399089b5e56e94b7991cd0c29e2cc530e890f78f27583cb48652824199",
    "parent_cold": "1bf43879126625fccd62f1aa3bd628af9a53089ea7cfa048607be55d027090ec",
    "gap_literal": "e9d66efc24f9f97600ec8155390c554aad066e8d25b54e7e9469a677da4fc129",
}
INPUTS = {"parent_model", "parent_configuration", "parent_report", "parent_owner",
          "parent_cold", "parent_cold_owner", "parent_root_acceptance", "gap_report",
          "gap_literal_report", "gap_literal_finalization", "gap_literal_owner", "gap_literal_root_acceptance"}
LIMITS = {"controls_worker_seconds": 10, "controls_owner_seconds": 15,
          "prepare_worker_seconds": 120, "prepare_owner_seconds": 135}


def require(condition, message):
    if not condition:
        raise AssertionError(message)


class Clock:
    def __init__(self, seconds):
        self.start = time.monotonic()
        self.seconds = seconds

    def check(self, stage):
        if time.monotonic() - self.start >= self.seconds:
            raise TimeoutError("independent triangle-gap deadline: " + stage)

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

def message_digest(messages):
    value = hashlib.sha256()
    for item in messages:
        raw = item.SerializeToString()
        value.update(len(raw).to_bytes(8, "big"))
        value.update(raw)
    return value.hexdigest()

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

def load_configuration(args, clock):
    ref = file_ref(args.configuration)
    require(ref["sha256"] == args.configuration_sha256, "configuration CLI identity")
    cfg = parse_json(read_ref(ref))
    require(cfg["schema"] == "conway99.f0.triangle-gap-native-configuration.v1", "configuration schema")
    require(cfg["source_sha256"] == PRODUCER_SHA, "frozen producer identity")
    require(cfg["layout"] == LAYOUT and cfg["limits"] == LIMITS, "fixed append layout and bounds")
    require(cfg["family_order"] == FAMILIES and cfg["expected_family_counts"] == COUNTS
            and cfg["expected_family_terms"] == TERMS, "complete zero family")
    require(set(cfg["inputs"]) == INPUTS and set(cfg["sources"]) == set(SOURCES) | {"checker"},
            "exact input and source aliases")
    equal_ref(cfg["sources"]["checker"], file_ref(__file__), "independent checker source")
    for name, expected in SOURCES.items():
        require(cfg["sources"][name]["sha256"] == expected, "source identity " + name)
    for source in cfg["sources"].values():
        read_ref(source)
        clock.check("source binding")
    require(cfg["proofs"] and cfg["reviews"], "proof and source-review references")
    for ref_to_read in cfg["proofs"] + cfg["reviews"]:
        read_ref(ref_to_read)
    require(cfg["inputs"]["parent_root_acceptance"]["sha256"] == PARENT_ROOT_SHA
            and cfg["inputs"]["parent_configuration"]["sha256"] == PARENT_CONFIG_SHA
            and cfg["inputs"]["gap_report"]["sha256"] == FORWARD_SHA, "fixed accepted inputs")
    require(cfg["optimizer_calls"] == cfg["automatic_retries"] == 0
            and cfg["native_query_authorized"] is False
            and cfg["independent_complete_protobuf_replay_required"] is True, "no query authority")
    require(cfg["runtime"]["ortools"] == importlib.metadata.version("ortools") == "9.15.6755"
            and cfg["runtime"]["protobuf"] == importlib.metadata.version("protobuf") == "6.33.6",
            "pinned protobuf runtime")
    from ortools.sat import cp_model_pb2 as pb
    require(digest(pb.DESCRIPTOR.serialized_pb) == cfg["runtime"]["model_schema_sha256"] == MODEL_SCHEMA_SHA,
            "complete model descriptor")
    no_native_imports()
    clock.check("configuration and runtime")
    return cfg, ref, pb


def accepted_receipts(cfg, clock):
    data = {}
    for name, ref in cfg["inputs"].items():
        if name != "parent_model":
            data[name] = json_ref(ref)
            clock.check("input " + name)
    seen = set()
    for authority in cfg["authorities"]:
        name, status = authority["input"], authority["expected_status"]
        require(name in INPUTS - {"parent_model", "parent_configuration"} and name not in seen,
                "unique authority input")
        require(status.startswith(("PASS_", "ROOT_ACCEPTS_", "OWNED_")) or name == "gap_report",
                "successful authority status")
        require(data[name][authority.get("status_field", "status")] == status, "authority " + name)
        seen.add(name)
    require(seen == INPUTS - {"parent_model", "parent_configuration"}, "all exact authorities")
    for link in cfg["authority_links"]:
        value = data[link["input"]]
        for field in link["fields"]:
            value = value[field]
        equal_ref(value, cfg["inputs"][link["target"]], "authority cross-reference")
    root, prep, cold, pcfg = [data[k] for k in
        ("parent_root_acceptance", "parent_report", "parent_cold", "parent_configuration")]
    require(root["schema"] == "conway99.f0.triangle-incidence-native-root-acceptance.v1"
            and root["status"] == "ROOT_ACCEPTS_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_MODEL_AND_INDEPENDENT_COLD",
            "accepted incidence parent")
    require(prep["status"] == "PASS_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_PREPARATION"
            and cold["status"] == "PASS_INDEPENDENT_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_MODEL", "parent phases")
    require(pcfg["schema"] == "conway99.f0.triangle-incidence-native-configuration.v1"
            and pcfg["source_sha256"] == SOURCES["parent_producer"], "parent producer configuration")
    equal_ref(pcfg["sources"]["checker"], cfg["sources"]["parent_cold"], "parent independent source")
    for record in (root, prep, cold):
        require(record["model_raw_sha256"] == PARENT_RAW_SHA and record["model_raw_bytes"] == PARENT_RAW_BYTES
                and record["variables"] == PARENT_VARIABLES and record["rows"] == PARENT_ROWS
                and record["total_terms"] == PARENT_TERMS and record["optimizer_calls"] == 0,
                "complete accepted parent dimensions and identity")
    require(root["complete_original_parent_bytes_recovered"] is True and root["parent_is_complete_raw_prefix"] is True
            and root["native_query_authorized_by_this_receipt"] is False, "parent acceptance scope")
    for field, alias in (("configuration", "parent_configuration"), ("preparation", "parent_report"),
                         ("independent_cold", "parent_cold"), ("model_archive", "parent_model")):
        equal_ref(root[field], cfg["inputs"][alias], "root parent binding")
    for record, source in ((prep, "parent_producer"), (cold, "parent_cold")):
        equal_ref(record["source"], cfg["sources"][source], "parent phase source")
        equal_ref(record["configuration"], cfg["inputs"]["parent_configuration"], "parent phase configuration")
    equal_ref(cold["preparation_report"], cfg["inputs"]["parent_report"], "parent cold preparation")
    equal_ref(cold["preparation_owner"], cfg["inputs"]["parent_owner"], "parent cold owned preparation")
    equal_ref(root["owners"]["preparation"], cfg["inputs"]["parent_owner"], "parent root preparation owner")
    equal_ref(root["owners"]["independent_cold"], cfg["inputs"]["parent_cold_owner"], "parent root independent owner")
    owner_ok(data["parent_owner"], cfg["inputs"]["parent_report"], cfg["sources"]["parent_producer"],
             cfg["inputs"]["parent_configuration"], "conway99.f0.triangle-incidence-native-owner.v1",
             "PASS_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_PREPARATION", "prepare")
    owner_ok(data["parent_cold_owner"], cfg["inputs"]["parent_cold"], cfg["sources"]["parent_cold"],
             cfg["inputs"]["parent_configuration"], "conway99.f0.triangle-incidence-external-cold-owner.v1",
             "PASS_TRIANGLE_INCIDENCE_EXTERNAL_COLD_REPLAY", "replay")
    clock.check("accepted complete parent receipts")
    return data


def accepted_zero_indices(cfg, data, clock):
    forward, replay, final, owner, root = [data[k] for k in
        ("gap_report", "gap_literal_report", "gap_literal_finalization", "gap_literal_owner", "gap_literal_root_acceptance")]
    require(forward["schema"] == "conway99.f0.recorded-triangle-spectral-gap-minors.v1"
            and forward["status"] == "COMPLETE_EXACT_RECORDED_TRIANGLE_SPECTRAL_GAP_TEST"
            and forward["complete"] is True, "complete forward report")
    require(forward["tested_triangles"] == len(forward["records"]) == 5364
            and forward["tested_principal_minors"] == 37548 and forward["optimizer_calls"] == 0,
            "complete forward universe")
    require(replay["schema"] == "conway99.f0.recorded-triangle-spectral-gap-independent-literal-replay.v1"
            and replay["status"] == "PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_GAP_LITERAL_REPLAY"
            and replay["complete"] is True and replay["records_verified"] == 5364,
            "complete independent arithmetic replay")
    true_fields = ("all_5364_records_independently_verified", "all_seven_minors_per_record_independently_recomputed",
                   "complete_triangle_origins_and_target_incidence_checked", "all_proposed_zero_and_cover_rows_checked")
    require(all(replay[name] is True for name in true_fields), "all literal replay claims")
    require(replay["principal_minors_recomputed"] == 37548 and replay["target_tables_checked"] == 84
            and replay["original_edges_checked"] == 68394 and replay["saved_neighbor_rows_checked"] == 480
            and replay["accepted_indicator_start"] == 71382 and replay["accepted_indicator_count"] == 5364,
            "independent complete literal dimensions")
    require(replay["optimizer_calls"] == replay["native_imports"] == replay["automatic_retries"] == 0
            and replay["native_model_built"] is False and replay["native_model_modified"] is False
            and replay["forward_source_imported_or_executed"] is False, "independent arithmetic scope")
    equal_ref(replay["source"], cfg["sources"]["gap_literal"], "independent arithmetic source")
    equal_ref(replay["forward_report"], cfg["inputs"]["gap_report"], "replayed forward report")
    require(final["schema"] == "conway99.f0.recorded-triangle-spectral-gap-independent-literal-finalization.v1"
            and final["status"] == "PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_GAP_REPLAY_AND_FINALIZATION"
            and final["accepted"] is True and final["within_declared_bounds"] is True
            and final["report_complete"] is True, "accepted literal finalization")
    require(final["report_sha256"] == cfg["inputs"]["gap_literal_report"]["sha256"]
            and final["report_bytes"] == cfg["inputs"]["gap_literal_report"]["bytes"]
            and final["maximum_ms"] == 30000 and final["maximum_report_bytes"] == 65536
            and final["report_bytes"] <= 65536 and final["automatic_retries"] == 0, "literal finalization identity")
    require(type(final["elapsed_through_report_hash_ms"]) is int
            and 0 <= final["elapsed_through_report_hash_ms"] <= 30000, "literal worker elapsed")
    require(owner["schema"] == "conway99.f0.recorded-triangle-spectral-gap-independent-literal-owner.v1"
            and owner["status"] == "OWNED_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_GAP_LITERAL_REPLAY_ACCEPTED"
            and owner["accepted"] is True and owner["report_accepted"] is True and owner["error"] is None,
            "accepted literal owner")
    require(owner["worker_invocations"] == 1 and owner["worker_returned"] is True
            and owner["complete_case_records"] == 5364 and owner["failed_count"] == 3156
            and owner["worker_maximum_ms"] == 30000 and owner["outer_maximum_ms"] == 45000
            and owner["automatic_retries"] == owner["optimizer_calls"] == owner["native_model_builds"] == owner["native_model_changes"] == 0
            and owner["exact_return_texts_preserved_before_publication"] is True
            and owner["OS_child_constructed"] is False and owner["hard_OS_preemption_claimed"] is False,
            "bounded single non-native literal execution")
    for name, maximum in (("worker_elapsed_through_report_hash_ms", 30000), ("outer_elapsed_ms", 45000),
                          ("outer_elapsed_through_first_owner_serialization_ms", 45000), ("texts_preserved_at_elapsed_ms", 45000)):
        require(type(owner[name]) is int and 0 <= owner[name] <= maximum, "literal owner time " + name)
    require(owner["worker_elapsed_through_report_hash_ms"] == final["elapsed_through_report_hash_ms"],
            "literal worker and owner elapsed agree")
    require(root["schema"] == "conway99.f0.recorded-triangle-spectral-gap-literal-root-acceptance.v1"
            and root["status"] == "ROOT_ACCEPTS_COMPLETE_RECORDED_TRIANGLE_GAP_LITERAL_ROWS",
            "root accepted literal arithmetic")
    for record, field, alias in ((owner, "report", "gap_literal_report"), (owner, "finalization", "gap_literal_finalization"),
            (owner, "forward_report", "gap_report"), (root, "report", "gap_literal_report"),
            (root, "finalization", "gap_literal_finalization"), (root, "owner", "gap_literal_owner"),
            (root, "forward_report", "gap_report"), (root, "parent_native_root_acceptance", "parent_root_acceptance")):
        equal_ref(record[field], cfg["inputs"][alias], "literal cross-reference " + field)
    equal_ref(owner["source"], replay["source"], "literal owned source")
    equal_ref(owner["configuration"], replay["configuration"], "literal owned configuration")
    indices = replay["failed_triangle_indices"]
    require(type(indices) is list and all(type(i) is int and 0 <= i < 5364 for i in indices)
            and indices == sorted(set(indices)) and len(indices) == replay["failed_count"] == 3156,
            "complete strictly ordered failed indices")
    require(root["failed_triangle_indices"] == indices and root["failed_count"] == 3156
            and digest(compact(indices)) == replay["failed_triangle_indices_sha256"] == root["failed_triangle_indices_sha256"],
            "root and arithmetic exact failed indices")
    counts = {"negative_diagonal": 0, "negative_pair_minor": 0, "negative_determinant_only": 3156,
              "all_principal_minors_nonnegative": 2208, "passes_with_zero_determinant": 0}
    require(replay["counts"] == forward["counts"] == counts, "complete classification counts")
    require(replay["complete_record_value_sha256"] == forward["records_value_sha256"], "complete arithmetic record digest")
    failed_from_records = []
    for i, record in enumerate(forward["records"]):
        require(record["triangle_index"] == i and record["indicator_variable"] == 71382 + i,
                "forward complete index order")
        if record["negative_minor_mask"]:
            require(record["negative_minor_mask"] == 64 and record["classification"] == "negative_determinant_only",
                    "certified determinant failure")
            failed_from_records.append(i)
        else:
            require(record["classification"] == "all_principal_minors_nonnegative", "remaining classifications")
    require(failed_from_records == indices and forward["failures"] == [[i, 64] for i in indices],
            "all and only recorded failed triangles")
    rows = [row_key(0, 0, [(71382 + i, 1)]) for i in indices]
    require(digest(compact(rows)) == ZERO_KEYS_SHA == replay["proposed_indicator_zero_row_keys_sha256"]
            == forward["proposed_indicator_zero_row_keys_sha256"] == root["proposed_indicator_zero_row_keys_sha256"],
            "all unit-zero row keys")
    require(forward["proposed_indicator_zero_rows"] == [{"triangle_index": i, "row_key": key}
            for i, key in zip(indices, rows)], "complete forward zero list")
    covers = [{"triangle_index": i, "row_key": row_key(0, 2, [(540 + e, 1) for e in forward["records"][i]["edge_ids"]])}
              for i in indices]
    require(covers == forward["proposed_triangle_cover_rows"]
            and digest(compact([v["row_key"] for v in covers])) == replay["proposed_triangle_cover_row_keys_sha256"]
            == forward["proposed_triangle_cover_row_keys_sha256"], "equivalent certified edge-cover keys")
    require(data["parent_root_acceptance"]["parent_raw_sha256"] == forward["accepted_native_model"]["raw_sha256"],
            "same original accepted indicator namespace")
    clock.check("complete literal certificates and exact zero keys")
    return indices, rows


def parse_parent(cfg, pb, clock):
    raw = gzip.decompress(read_ref(cfg["inputs"]["parent_model"]))
    require(len(raw) == PARENT_RAW_BYTES and digest(raw) == PARENT_RAW_SHA, "complete accepted parent raw bytes")
    parent = pb.CpModelProto()
    parent.ParseFromString(raw)
    require(parent.SerializeToString() == raw, "exact canonical parent protobuf")
    require(len(parent.variables) == PARENT_VARIABLES and len(parent.constraints) == PARENT_ROWS
            and sum(len(row.linear.vars) for row in parent.constraints) == PARENT_TERMS, "complete parent dimensions")
    require({field.name for field, _ in parent.ListFields()} <= {"name", "variables", "constraints"},
            "parent has no objective, hint or assumption")
    require(all(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal
                for row in parent.constraints), "original unconditional linear rows")
    clock.check("complete parent parse")
    return raw, parent


def native_zero_origins(parent, forward, indices, pb, clock):
    origins = []
    for position, index in enumerate(indices):
        indicator = 71382 + index
        variable = pb.IntegerVariableProto(name="spectral_triangle_%04d" % index, domain=[0, 1])
        require(parent.variables[indicator].SerializeToString() == variable.SerializeToString(),
                "complete native triangle variable")
        edge_variables = decode_and_edges(parent, 260042 + 4 * index, indicator, pb, 540, 68934)
        pairs = []
        for native_id in edge_variables:
            actual = parent.variables[native_id]
            words = actual.name.split("_")
            require(len(words) == 4 and words[:2] == ["shared", "edge"], "native edge variable name")
            a, b = int(words[2]), int(words[3])
            require(0 <= a < b < 480, "native original edge endpoints")
            expected = pb.IntegerVariableProto(name="shared_edge_%03d_%03d" % (a, b), domain=[0, 1])
            require(actual.SerializeToString() == expected.SerializeToString(), "complete native edge variable")
            pairs.append([a, b])
        vertices = sorted({v for pair in pairs for v in pair})
        require(len(vertices) == 3, "native triangle three vertices")
        a, b, c = vertices
        require(pairs == [[a, b], [a, c], [b, c]], "native exact triangle edge set")
        edge_ids = [v - 540 for v in edge_variables]
        record = forward["records"][index]
        require(record["vertices"] == vertices and record["edge_ids"] == edge_ids
                and record["indicator_variable"] == indicator, "native and certified literal triangle identity")
        origin = record["origin"]
        require(set(origin) == {"target_edge_id", "support_table_index", "support_index"}
                and type(origin["target_edge_id"]) is int and origin["target_edge_id"] in edge_ids
                and type(origin["support_table_index"]) is int and 0 <= origin["support_table_index"] < 132
                and type(origin["support_index"]) is int and 0 <= origin["support_index"] < 480,
                "literal target origin")
        origins.append({"family": "gap_triangle_zero", "proposal_index": position,
            "native_row_index": PARENT_ROWS + position, "triangle_index": index,
            "vertices": vertices, "edge_ids": edge_ids, "indicator_variable": indicator, "origin": origin})
        if position % 128 == 0:
            clock.check("recover native AND meanings")
    checks = {"forward_records_bound": 5364, "complete_failed_indices": len(indices),
        "failed_triangle_indices_sha256": digest(compact(indices)), "native_indicator_messages_checked": len(indices),
        "native_edge_variable_messages_checked": 3 * len(indices), "complete_native_AND_messages_checked": 4 * len(indices),
        "all_certified_zeros_retained": True, "spectral_minor_recomputations": 0, "old_family_reconstructions": 0}
    require(len(origins) == 3156, "every certified zero has a native origin")
    return origins, checks


def preparation_records(cfg, configuration, args, clock):
    directory = args.preparation_directory.resolve()
    directory.relative_to(ROOT)
    report_ref, owner_ref = [file_ref(directory / name) for name in ("report.json", "owner.json")]
    require(report_ref["sha256"] == args.report_sha256 and owner_ref["sha256"] == args.owner_sha256,
            "complete preparation terminal CLI identities")
    report, owner = json_ref(report_ref), json_ref(owner_ref)
    require(report["schema"] == "conway99.f0.triangle-gap-native-preparation.v1"
            and report["status"] == "PASS_COMPLETE_TRIANGLE_GAP_NATIVE_PREPARATION", "preparation status")
    source = report["source"]
    require(source["sha256"] == cfg["source_sha256"] == PRODUCER_SHA, "current producer identity")
    read_ref(source)
    equal_ref(report["configuration"], configuration, "preparation configuration")
    owner_ok(owner, report_ref, source, configuration, "conway99.f0.triangle-gap-native-owner.v1",
             "PASS_COMPLETE_TRIANGLE_GAP_NATIVE_PREPARATION", "prepare")
    require(owner["automatic_retries"] == 0 and owner["CpModel_constructed"] is True
            and owner["native_optimizer_constructed"] is False and owner["native_query_run"] is False,
            "single owned preparation and no solver")
    initial = json_ref(file_ref(directory / "initial-owner.json"))
    require(initial["schema"] == owner["schema"] and initial["status"] == "ERROR_TRIANGLE_GAP_OWNER"
            and initial["mode"] == "prepare" and initial["report_accepted"] is False
            and initial["supervision"] is None, "preserved preliminary owner")
    equal_ref(initial["source"], source, "initial owner source")
    equal_ref(initial["configuration"], configuration, "initial owner configuration")
    receipt_ref = file_ref(directory / "owned-receipt.json")
    equal_ref(owner["owned_receipt"], receipt_ref, "separate owned receipt")
    receipt = json_ref(receipt_ref)
    require(receipt["schema"] == "conway99.f0.triangle-gap-owned-receipt.v1"
            and receipt["mode"] == "prepare" and receipt["maximum_seconds"] == 135
            and 0 <= receipt["seconds"] <= owner["seconds"], "successful separate supervision")
    equal_ref(receipt["source"], source, "owned receipt source")
    equal_ref(receipt["configuration"], configuration, "owned receipt configuration")
    equal_ref(receipt["supervisor_record"], file_ref(directory / "supervisor.json"), "supervisor file")
    require(receipt["supervision"] == json_ref(receipt["supervisor_record"]) == owner["supervision"],
            "complete supervision receipts agree")
    require(not (directory / "error.json").exists() and not (directory / "owner-error.json").exists(),
            "no hidden preparation failure")
    require(report["inputs"] == cfg["inputs"] and report["authorities"] == cfg["authorities"]
            and report["authority_links"] == cfg["authority_links"] and report["layout"] == LAYOUT,
            "complete preparation inputs")
    require(report["parent_variables"] == PARENT_VARIABLES and report["parent_rows"] == PARENT_ROWS
            and report["variables"] == PARENT_VARIABLES and report["rows"] == FINAL_ROWS
            and report["parent_total_terms"] == PARENT_TERMS and report["total_terms"] == FINAL_TERMS
            and report["term_change"] == 3156, "preparation exact dimensions")
    require(report["family_order"] == FAMILIES and report["family_counts"] == COUNTS
            and report["family_terms"] == TERMS, "preparation exact family")
    true_fields = ("parent_is_complete_raw_prefix", "all_certified_zeros_retained", "original_variable_ids_preserved",
                   "CpModel_constructed", "independent_full_model_replay_still_required")
    false_fields = ("objective_hint_assumption_or_graph_symmetry_added", "CpSolver_constructed",
                    "native_optimizer_constructed", "native_query_run", "graph_constructed",
                    "whole_component_excluded", "all_original_pair_caps_included", "second_component_completion_included")
    require(all(report[name] is True for name in true_fields) and all(report[name] is False for name in false_fields),
            "preparation exact scope")
    require(report["new_variables"] == report["replaced_rows"] == report["optimizer_calls"] == 0
            and report["native_model_builds"] == 1, "one build and no solver")
    equal_ref(report["gap_literal_root_acceptance"], cfg["inputs"]["gap_literal_root_acceptance"],
              "preparation literal authority")
    require(report["maximum_seconds"] == 120 and type(report["seconds_before_report_serialization"]) in (int, float)
            and math.isfinite(report["seconds_before_report_serialization"])
            and 0 <= report["seconds_before_report_serialization"] <= 120, "bounded preparation worker")
    for name in ("ortools", "protobuf", "model_schema_sha256", "cp_model_sha256", "native_helper_sha256"):
        require(report["runtime"][name] == cfg["runtime"][name], "preparation runtime " + name)
    transport = report["native_transport"]
    require(transport["complete_byte_comparison"] is True and transport["public_parse_return"] is True
            and transport["native_validation"] == "" and transport["optimizer_calls"] == 0
            and transport["CpSolver_constructed"] is False, "public native transport receipt")
    equal_ref(report["stages"], file_ref(directory / "stages.json"), "preparation stage identity")
    stages = json_ref(report["stages"])
    expected_stages = ["accepted parent and independently certified unit-zero suffix"]
    expected_stages.extend("native indicator and AND bindings %d" % i for i in range(0, 3156, 128))
    expected_stages.extend(["public native transport validation and complete byte comparison",
                            "complete archives row ledger and restoration manifest"])
    require([item["phase"] for item in stages] == expected_stages, "complete preparation stage order")
    times = [item["elapsed_seconds"] for item in stages]
    require(times == sorted(times) and all(type(t) in (int, float) and math.isfinite(t) and 0 <= t <= 120
                                         for t in times), "bounded monotone stages")
    names = {"model": "model.pb", "model_archive": "model.pb.gz", "suffix_archive": "suffix.pb.gz",
             "row_ledger": "append-rows.json.gz", "restoration_manifest": "restoration-manifest.json"}
    require(set(report["artifacts"]) == set(names), "exact preparation artifact set")
    raw_artifacts = {}
    for key, filename in names.items():
        expected = file_ref(directory / filename)
        equal_ref(report["artifacts"][key], expected, "complete artifact " + key)
        raw_artifacts[key] = read_ref(expected)
        clock.check("preparation artifact")
    return report, owner, report_ref, owner_ref, source, raw_artifacts


def inspect_exports(cfg, report, raw, parent_raw, parent, indices, rows, origins, checks, pb, clock):
    full_raw = raw["model"]
    require(gzip.decompress(raw["model_archive"]) == full_raw, "lossless complete model archive")
    suffix_raw = gzip.decompress(raw["suffix_archive"])
    model, preservation, parent_terms, all_terms = full_model_check(
        parent_raw, parent, full_raw, suffix_raw, rows, pb, clock)
    require(len(model.variables) == PARENT_VARIABLES and len(model.constraints) == FINAL_ROWS
            and parent_terms == PARENT_TERMS and all_terms == FINAL_TERMS, "complete final model dimensions")
    require(report["preservation"] == preservation, "exact preservation receipt")
    require(report["model_raw_sha256"] == digest(full_raw) and report["model_raw_bytes"] == len(full_raw),
            "complete raw model identity")
    require(report["model"] == {"raw_bytes": len(full_raw), "raw_sha256": digest(full_raw),
                               "archive_bytes": len(raw["model_archive"]),
                               "archive_sha256": digest(raw["model_archive"])}, "complete model descriptor")
    rows_sha = digest(compact(rows))
    family_sha = {"gap_triangle_zero": rows_sha}
    jsonl_sha = {"gap_triangle_zero": digest(b"".join(compact(row) + b"\n" for row in rows))}
    require(report["row_keys_sha256"] == rows_sha == ZERO_KEYS_SHA
            and report["family_row_keys_sha256"] == family_sha and report["family_row_jsonl_sha256"] == jsonl_sha,
            "all exact row hashes")
    require(report["gap_check"] == checks, "complete producer native-premise checks")
    expected_ledger = {"schema": "conway99.f0.triangle-gap-appended-row-ledger.v1",
        "source": report["source"], "configuration": report["configuration"],
        "gap_report": cfg["inputs"]["gap_report"], "gap_literal_report": cfg["inputs"]["gap_literal_report"],
        "gap_literal_root_acceptance": cfg["inputs"]["gap_literal_root_acceptance"],
        "family_order": FAMILIES, "family_counts": COUNTS, "family_terms": TERMS,
        "failed_triangle_indices": indices, "row_keys": rows, "row_origins": origins,
        "row_keys_sha256": rows_sha, "family_row_keys_sha256": family_sha, "all_certified_zeros_retained": True}
    require(gzip.decompress(raw["row_ledger"]) == compact(expected_ledger) + b"\n",
            "complete exact row ledger and all origins")
    restoration = {"parent_raw_bytes": len(parent_raw), "parent_raw_sha256": digest(parent_raw),
                   "suffix_raw_bytes": len(suffix_raw), "suffix_raw_sha256": digest(suffix_raw)}
    require(report["restoration"] == restoration, "exact restoration identities")
    artifacts = {k: v for k, v in report["artifacts"].items() if k != "restoration_manifest"}
    expected_manifest = {"schema": "conway99.f0.triangle-gap-restoration.v1",
        "status": "PASS_EXACT_TRIANGLE_GAP_PARENT_AND_SUFFIX_RESTORATION",
        "source": report["source"], "configuration": report["configuration"],
        "parent_model": cfg["inputs"]["parent_model"], "parent_root_acceptance": cfg["inputs"]["parent_root_acceptance"],
        "layout": LAYOUT, "artifacts": artifacts, "restoration": restoration,
        "suffix_format": "CpModelProto with only 3156 appended unit-zero constraints in ascending triangle index.",
        "apply_steps": ["Verify complete archive and raw hashes.", "Concatenate accepted parent raw bytes and suffix raw bytes.",
                        "Require exact equality with the complete native model bytes."],
        "parent_is_complete_raw_prefix": True, "complete_original_parent_bytes_recovered": True,
        "new_variables": 0, "replaced_rows": 0, "independent_full_model_replay_still_required": True}
    require(raw["restoration_manifest"] == compact(expected_manifest) + b"\n", "complete exact restoration manifest")
    clock.check("lossless artifacts, row origins and restoration")
    return preservation, restoration, rows_sha, family_sha, jsonl_sha


def controls(cfg, pb, clock):
    parent = pb.CpModelProto(name="independent triangle gap controls")
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
    rows = [row_key(0, 0, [(3, 1)]), row_key(0, 0, [(4, 1)])]
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
        require((valid and values[3] == 0) == (valid and sum(values[:3]) <= 2),
                "native AND zero and edge-cover equivalence")
        and_assignments += 1
    clock.check("complete toy controls")
    no_native_imports()
    return {"schema": "conway99.f0.triangle-gap-independent-controls.v1",
            "status": "PASS_TRIANGLE_GAP_INDEPENDENT_REPLAY_CONTROLS",
            "toy_parent_variables": 5, "toy_parent_rows": 5, "toy_append_rows": 2,
            "mutations_rejected": rejected, "and_truth_assignments": and_assignments,
            "AND_zero_equivalence_assignments": and_assignments, "exact_large_wire_integer": large,
            "whole_parent_and_suffix_recovery_checked": True, "complete_ConstraintProto_comparison": True,
            "actual_model_or_inventory_decoded": False, "CpModel_constructed": False,
            "CpSolver_constructed": False, "native_optimizer_constructed": False,
            "native_query_run": False, "native_model_builds": 0, "optimizer_calls": 0}

def replay(cfg, configuration, pb, args, clock):
    data = accepted_receipts(cfg, clock)
    indices, rows = accepted_zero_indices(cfg, data, clock)
    preparation, owner, prep_ref, owner_ref, producer, raw = preparation_records(cfg, configuration, args, clock)
    parent_raw, parent = parse_parent(cfg, pb, clock)
    origins, checks = native_zero_origins(parent, data["gap_report"], indices, pb, clock)
    preservation, restoration, rows_sha, family_sha, jsonl_sha = inspect_exports(
        cfg, preparation, raw, parent_raw, parent, indices, rows, origins, checks, pb, clock)
    no_native_imports()
    return {"schema": "conway99.f0.triangle-gap-independent-cold.v1",
            "status": "PASS_INDEPENDENT_COMPLETE_TRIANGLE_GAP_NATIVE_MODEL",
            "preparation_report": prep_ref, "preparation_owner": owner_ref,
            "parent_root_acceptance": cfg["inputs"]["parent_root_acceptance"],
            "gap_literal_root_acceptance": cfg["inputs"]["gap_literal_root_acceptance"],
            "inputs": cfg["inputs"], "layout": LAYOUT,
            "variables": PARENT_VARIABLES, "rows": FINAL_ROWS, "total_terms": FINAL_TERMS,
            "parent_variables": PARENT_VARIABLES, "parent_rows": PARENT_ROWS, "parent_total_terms": PARENT_TERMS,
            "new_variables": 0, "replaced_rows": 0, "appended_rows": len(rows), "appended_terms": 3156,
            "family_order": FAMILIES, "family_counts": COUNTS, "family_terms": TERMS,
            "row_keys_sha256": rows_sha, "family_row_keys_sha256": family_sha, "family_row_jsonl_sha256": jsonl_sha,
            "gap_check": checks, "preservation": preservation, "restoration": restoration,
            "model_raw_sha256": digest(raw["model"]), "model_raw_bytes": len(raw["model"]),
            "model_archive_sha256": digest(raw["model_archive"]), "model_archive_bytes": len(raw["model_archive"]),
            "base_restoration_sha256": digest(parent_raw), "base_restoration_bytes": len(parent_raw),
            "artifacts": preparation["artifacts"], "complete_original_parent_bytes_recovered": True,
            "all_original_variable_and_constraint_messages_preserved": True,
            "all_appended_complete_constraint_messages_independently_checked": True,
            "complete_row_origins_and_lossless_restoration_checked": True,
            "all_3156_certified_zero_rows_retained": True,
            "native_AND_meanings_recovered_independently": True,
            "spectral_arithmetic_repeated": False, "spectral_producer_or_literal_checker_imported": False,
            "native_transport_or_preparation_producer_imported": False,
            "CpModel_constructed": False, "CpSolver_constructed": False,
            "native_optimizer_constructed": False, "native_query_run": False,
            "optimizer_calls": 0, "native_model_builds": 0, "native_query_authorized_by_this_report": False,
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
        failure = {"schema": "conway99.f0.triangle-gap-independent-error.v1",
                   "status": "ERROR_INDEPENDENT_TRIANGLE_GAP_REPLAY", "mode": args.mode,
                   "type": type(error).__name__, "message": str(error),
                   "traceback": traceback.format_exc(), "report_accepted": False,
                   "seconds": clock.elapsed(), "maximum_seconds": limit,
                   "optimizer_calls": 0, "native_query_run": False}
        save_new(args.directory / "error.json", compact(failure) + b"\n")
        print(json.dumps({"status": failure["status"], "message": str(error)}, sort_keys=True), flush=True)
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
