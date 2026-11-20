"""Append the independently certified recorded-triangle zeros to the F0 model.

The accepted 80730-variable, 300795-row parent is an exact byte prefix.
Append 3156 rows t_i=0 in increasing triangle index. No new variable,
old-row edit, spectral recomputation, solver, objective, hint or query.
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
VARIABLES, PARENT_ROWS, FINAL_ROWS = 80730, 300795, 303951
PARENT_TERMS, FINAL_TERMS = 3337296, 3340452
PARENT_RAW_BYTES = 39512348
PARENT_RAW_SHA = "56f6be31b4714825fb6d546ca79420e0ee0d25da05231a0eea322e514473bed8"
PARENT_ROOT_SHA = "bb744c426034992ddae1702cdb479e61d17d9a2fa5da2a614f4d6c15643908f0"
FORWARD_SHA = "31789e7cb6012e8d0f3545170bfa19daec752027b4cd1c7a6bc013749cc146f1"
ZERO_KEYS_SHA = "68cbeeb785a7d68e7141464bd3c9c9274bebddcd33875ea4c843494f2da44b4c"
MODEL_SCHEMA_SHA = "266b68151ffd6c9f5db22553442abd777031663d39e1cea649a8737f811d2eff"
HELPERS = {"base": "5a1e8026683a7782fce6ec2a2947748356ac9cd5adf32dd2a0663b0dd60bfca2",
           "supervisor": "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3"}
INPUTS = {"parent_model", "parent_configuration", "parent_report", "parent_owner",
          "parent_cold", "parent_cold_owner", "parent_root_acceptance", "gap_report",
          "gap_literal_report", "gap_literal_finalization", "gap_literal_owner", "gap_literal_root_acceptance"}
AUTHORITIES = INPUTS - {"parent_model", "parent_configuration"}
LIMITS = {"controls_worker_seconds": 10, "controls_owner_seconds": 15,
          "prepare_worker_seconds": 120, "prepare_owner_seconds": 135}
FAMILY_ORDER = ["gap_triangle_zero"]
FAMILY_COUNTS = {"gap_triangle_zero": 3156}
LAYOUT = {"parent_variables": VARIABLES, "parent_rows": PARENT_ROWS,
          "new_variables": 0, "replaced_rows": 0, "appended_rows": 3156, "appended_terms": 3156,
          "gap_triangle_zero_start": PARENT_ROWS, "variables": VARIABLES, "rows": FINAL_ROWS,
          "triangle_variable_start": 71382, "triangle_variables": 5364}
PASS = {"controls": "PASS_TRIANGLE_GAP_MODEL_CONTROLS",
        "prepare": "PASS_COMPLETE_TRIANGLE_GAP_NATIVE_PREPARATION"}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def binding(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(raw), "sha256": sha(raw)}


def write_new(path, raw):
    with Path(path).open("xb") as stream:
        stream.write(raw)


def save(path, value):
    write_new(path, canonical(value) + b"\n")


def read_bytes(ref):
    path = (ROOT / ref["path"]).resolve()
    assert path.is_relative_to(ROOT)
    raw = path.read_bytes()
    assert sha(raw) == ref["sha256"] and len(raw) == ref["bytes"], ref["path"]
    return raw


def same_ref(left, right):
    assert left["path"] == right["path"] and left["sha256"] == right["sha256"]
    if "bytes" in left and "bytes" in right:
        assert left["bytes"] == right["bytes"]


def bound_module(name, ref):
    read_bytes(ref)
    spec = importlib.util.spec_from_file_location(name, ROOT / ref["path"])
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def tick(args, phase):
    args.stages.append({"phase": phase, "elapsed_seconds": time.monotonic() - args.started})
    assert time.monotonic() <= args.deadline, phase


def load_configuration(args):
    raw = args.configuration.read_bytes()
    assert sha(raw) == args.configuration_sha256
    cfg = json.loads(raw)
    assert cfg["schema"] == "conway99.f0.triangle-gap-native-configuration.v1"
    assert cfg["source_sha256"] == binding(__file__)["sha256"]
    assert cfg["layout"] == LAYOUT and cfg["limits"] == LIMITS
    assert cfg["family_order"] == FAMILY_ORDER
    assert cfg["expected_family_counts"] == cfg["expected_family_terms"] == FAMILY_COUNTS
    assert set(cfg["inputs"]) == INPUTS
    assert cfg["inputs"]["parent_root_acceptance"]["sha256"] == PARENT_ROOT_SHA
    assert cfg["inputs"]["gap_report"]["sha256"] == FORWARD_SHA
    assert cfg["optimizer_calls"] == cfg["automatic_retries"] == 0
    assert cfg["native_query_authorized"] is False and cfg["independent_complete_protobuf_replay_required"] is True
    assert cfg["runtime"]["ortools"] == "9.15.6755" and cfg["runtime"]["protobuf"] == "6.33.6"
    assert cfg["runtime"]["model_schema_sha256"] == MODEL_SCHEMA_SHA
    assert set(HELPERS) | {"checker"} <= set(cfg["sources"])
    for name, expected in HELPERS.items():
        assert cfg["sources"][name]["sha256"] == expected
    for ref in list(cfg["sources"].values()) + cfg["proofs"] + cfg["reviews"]:
        read_bytes(ref)
    assert cfg["proofs"] and cfg["reviews"]
    return cfg


def load_inputs(cfg):
    data = {name: json.loads(read_bytes(ref)) for name, ref in cfg["inputs"].items() if name != "parent_model"}
    checked = set()
    for item in cfg["authorities"]:
        name = item["input"]
        assert name in AUTHORITIES and name not in checked
        expected_status = item["expected_status"]
        assert expected_status.startswith(("PASS_", "OWNED_", "ROOT_ACCEPTS_")) or name == "gap_report"
        assert data[name][item.get("status_field", "status")] == expected_status, name
        checked.add(name)
    assert checked == AUTHORITIES
    for link in cfg["authority_links"]:
        value = data[link["input"]]
        for field in link["fields"]:
            value = value[field]
        same_ref(value, cfg["inputs"][link["target"]])
    root, report, cold, pcfg = [data[n] for n in
        ("parent_root_acceptance", "parent_report", "parent_cold", "parent_configuration")]
    assert root["schema"] == "conway99.f0.triangle-incidence-native-root-acceptance.v1"
    assert root["status"] == "ROOT_ACCEPTS_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_MODEL_AND_INDEPENDENT_COLD"
    assert report["status"] == "PASS_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_PREPARATION"
    assert cold["status"] == "PASS_INDEPENDENT_COMPLETE_TRIANGLE_INCIDENCE_NATIVE_MODEL"
    assert pcfg["schema"] == "conway99.f0.triangle-incidence-native-configuration.v1"
    assert report["source"]["sha256"] == pcfg["source_sha256"]
    same_ref(cold["source"], pcfg["sources"]["checker"])
    for record in (root, report, cold):
        assert record["model_raw_sha256"] == PARENT_RAW_SHA and record["model_raw_bytes"] == PARENT_RAW_BYTES
        assert record["variables"] == VARIABLES and record["rows"] == PARENT_ROWS
        assert record["total_terms"] == PARENT_TERMS and record["optimizer_calls"] == 0
    assert root["complete_original_parent_bytes_recovered"] is True and root["parent_is_complete_raw_prefix"] is True
    assert root["native_query_authorized_by_this_receipt"] is False
    for field, alias in (("configuration", "parent_configuration"), ("preparation", "parent_report"),
                         ("independent_cold", "parent_cold"), ("model_archive", "parent_model")):
        same_ref(root[field], cfg["inputs"][alias])
    for record in (report, cold):
        same_ref(record["configuration"], cfg["inputs"]["parent_configuration"])
    same_ref(cold["preparation_report"], cfg["inputs"]["parent_report"])
    same_ref(cold["preparation_owner"], cfg["inputs"]["parent_owner"])
    for owner_alias, report_alias, root_key, mode in (
            ("parent_owner", "parent_report", "preparation", "prepare"),
            ("parent_cold_owner", "parent_cold", "independent_cold", "replay")):
        owner = data[owner_alias]
        assert owner["report_accepted"] is True and owner["mode"] == mode
        assert owner["optimizer_calls"] == 0 and owner["CpSolver_constructed"] is False
        assert owner["maximum_seconds"] == 135 and owner["deadline_overrun_seconds"] == 0
        assert type(owner["seconds"]) in (int, float) and math.isfinite(owner["seconds"]) and 0 <= owner["seconds"] <= 135
        sup = owner["supervision"]
        assert sup["status"] == "CHILD_EXITED" and sup["returncode"] == 0
        assert sup["child_reaped"] is True and sup["owned_process_group_stopped"] is True
        same_ref(root["owners"][root_key], cfg["inputs"][owner_alias])
        same_ref(owner["report"], cfg["inputs"][report_alias])
        same_ref(owner["source"], data[report_alias]["source"])
        same_ref(owner["configuration"], cfg["inputs"]["parent_configuration"])
    return data


def accepted_failed_indices(cfg, data):
    forward, cold, final, owner, root = [data[name] for name in
        ("gap_report", "gap_literal_report", "gap_literal_finalization", "gap_literal_owner", "gap_literal_root_acceptance")]
    assert forward["schema"] == "conway99.f0.recorded-triangle-spectral-gap-minors.v1"
    assert forward["status"] == "COMPLETE_EXACT_RECORDED_TRIANGLE_SPECTRAL_GAP_TEST" and forward["complete"] is True
    assert forward["tested_triangles"] == 5364 and forward["tested_principal_minors"] == 37548
    assert len(forward["records"]) == 5364 and forward["optimizer_calls"] == 0
    assert forward["counts"] == {"negative_diagonal": 0, "negative_pair_minor": 0,
        "negative_determinant_only": 3156, "all_principal_minors_nonnegative": 2208, "passes_with_zero_determinant": 0}
    assert cold["schema"] == "conway99.f0.recorded-triangle-spectral-gap-independent-literal-replay.v1"
    assert cold["status"] == "PASS_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_GAP_LITERAL_REPLAY" and cold["complete"] is True
    assert cold["records_verified"] == 5364 and cold["all_5364_records_independently_verified"] is True
    assert cold["all_seven_minors_per_record_independently_recomputed"] is True
    same_ref(cold["forward_report"], cfg["inputs"]["gap_report"])
    assert final["accepted"] is True and final["within_declared_bounds"] is True
    assert final["report_sha256"] == cfg["inputs"]["gap_literal_report"]["sha256"]
    assert final["report_bytes"] == cfg["inputs"]["gap_literal_report"]["bytes"]
    assert owner["schema"] == "conway99.f0.recorded-triangle-spectral-gap-independent-literal-owner.v1"
    assert owner["status"] == "OWNED_COMPLETE_INDEPENDENT_RECORDED_TRIANGLE_GAP_LITERAL_REPLAY_ACCEPTED"
    assert owner["accepted"] is True and owner["report_accepted"] is True and owner["worker_returned"] is True
    assert owner["worker_invocations"] == 1 and owner["complete_case_records"] == 5364 and owner["failed_count"] == 3156
    assert owner["worker_maximum_ms"] == 30000 and owner["outer_maximum_ms"] == 45000
    for field, limit in (("worker_elapsed_through_report_hash_ms", 30000), ("outer_elapsed_ms", 45000),
                         ("outer_elapsed_through_first_owner_serialization_ms", 45000)):
        value = owner[field]
        assert type(value) in (int, float) and math.isfinite(value) and 0 <= value <= limit
    for record, field, alias in ((owner, "report", "gap_literal_report"),
            (owner, "finalization", "gap_literal_finalization"), (owner, "forward_report", "gap_report"),
            (root, "report", "gap_literal_report"), (root, "finalization", "gap_literal_finalization"),
            (root, "owner", "gap_literal_owner"), (root, "forward_report", "gap_report"),
            (root, "parent_native_root_acceptance", "parent_root_acceptance")):
        same_ref(record[field], cfg["inputs"][alias])
    assert root["status"].startswith("ROOT_ACCEPTS_")
    indices = cold["failed_triangle_indices"]
    assert type(indices) is list and len(indices) == cold["failed_count"] == 3156
    assert all(type(i) is int and 0 <= i < 5364 for i in indices)
    assert all(a < b for a, b in zip(indices, indices[1:]))
    assert sha(canonical(indices)) == cold["failed_triangle_indices_sha256"] == root["failed_triangle_indices_sha256"]
    assert root["failed_triangle_indices"] == indices and root["failed_count"] == 3156
    assert root["proposed_indicator_zero_row_keys_sha256"] == ZERO_KEYS_SHA
    assert forward["failures"] == [[i, 64] for i in indices]
    rows = [[0, 0, [[71382 + i, 1]]] for i in indices]
    assert sha(canonical(rows)) == ZERO_KEYS_SHA
    assert cold["proposed_indicator_zero_row_keys_sha256"] == forward["proposed_indicator_zero_row_keys_sha256"] == ZERO_KEYS_SHA
    assert forward["proposed_indicator_zero_rows"] == [{"triangle_index": i, "row_key": row} for i, row in zip(indices, rows)]
    assert data["parent_root_acceptance"]["parent_raw_sha256"] == forward["accepted_native_model"]["raw_sha256"]
    return indices, rows


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
        for name, path in (("cp_model_sha256", cp_model.__file__), ("native_helper_sha256", cp_model.cmh.__file__)):
            result[name] = sha(Path(path).read_bytes())
            assert result[name] == cfg["runtime"][name]
    return result


def constraint(pb, row):
    lower, upper, terms = row
    assert type(lower) is type(upper) is int and -(1 << 63) <= lower <= upper < (1 << 63)
    assert all(type(v) is type(c) is int and 0 <= v < VARIABLES and 0 < abs(c) < (1 << 63) for v, c in terms)
    assert terms == sorted(terms) and len({v for v, _ in terms}) == len(terms)
    result = pb.ConstraintProto()
    result.linear.vars.extend(v for v, _ in terms)
    result.linear.coeffs.extend(c for _, c in terms)
    result.linear.domain.extend([lower, upper])
    return result


def append_suffix(pb, parent_raw, rows):
    parent, full, suffix = pb.CpModelProto(), pb.CpModelProto(), pb.CpModelProto()
    parent.ParseFromString(parent_raw)
    assert parent.SerializeToString() == parent_raw
    assert all(v < len(parent.variables) for row in rows for v, _ in row[2])
    full.CopyFrom(parent)
    suffix.constraints.extend(constraint(pb, row) for row in rows)
    suffix_raw = suffix.SerializeToString()
    assert {f.name for f, _ in suffix.ListFields()} <= {"constraints"}
    full.constraints.extend(suffix.constraints)
    raw = full.SerializeToString()
    assert raw == parent_raw + suffix_raw and len(full.variables) == len(parent.variables)
    restored = pb.CpModelProto()
    restored.CopyFrom(full)
    del restored.constraints[len(parent.constraints):]
    assert restored.SerializeToString() == parent_raw
    return parent, full, raw, suffix_raw


def message_digest(messages):
    result = hashlib.sha256()
    for message in messages:
        raw = message.SerializeToString()
        result.update(len(raw).to_bytes(8, "big"))
        result.update(raw)
    return result.hexdigest()


def gap_origins(pb, parent, forward, indices, args):
    origins = []
    for position, index in enumerate(indices):
        record, t = forward["records"][index], 71382 + index
        assert record["triangle_index"] == index and record["indicator_variable"] == t
        assert record["negative_minor_mask"] == 64 and record["classification"] == "negative_determinant_only"
        vertices, edge_ids = record["vertices"], record["edge_ids"]
        assert len(vertices) == len(edge_ids) == 3 and all(type(a) is int for a in vertices + edge_ids)
        a, b, c = vertices
        assert 0 <= a < b < c < 480 and len(set(edge_ids)) == 3
        expected_variable = pb.IntegerVariableProto(name="spectral_triangle_%04d" % index, domain=[0, 1])
        assert parent.variables[t].SerializeToString() == expected_variable.SerializeToString()
        expected_and = []
        for edge, (u, v) in zip(edge_ids, ((a, b), (a, c), (b, c))):
            assert 0 <= edge < 68394
            expected_edge = pb.IntegerVariableProto(name="shared_edge_%03d_%03d" % (u, v), domain=[0, 1])
            assert parent.variables[540 + edge].SerializeToString() == expected_edge.SerializeToString()
            expected_and.append([0, 1, [[540 + edge, 1], [t, -1]]])
        expected_and.append([-2, 1, sorted([[540 + e, -1] for e in edge_ids] + [[t, 1]])])
        for j, row in enumerate(expected_and):
            assert parent.constraints[260042 + 4 * index + j].SerializeToString() == constraint(pb, row).SerializeToString()
        origins.append({"family": "gap_triangle_zero", "proposal_index": position,
            "native_row_index": PARENT_ROWS + position, "triangle_index": index,
            "vertices": vertices, "edge_ids": edge_ids, "indicator_variable": t, "origin": record["origin"]})
        if position % 128 == 0:
            tick(args, "native indicator and AND bindings %d" % position)
    return origins


def controls(cfg, args):
    from ortools.sat import cp_model_pb2 as pb
    runtime = runtime_record(cfg, False)
    toy = pb.CpModelProto(name="triangle-gap-prefix-control")
    for i in range(4):
        toy.variables.add(name="old_bool_%d" % i, domain=[0, 1])
    toy.variables.add(name="old_signed", domain=[-7, 9])
    huge = (1 << 54) + 3
    old_rows = [[0, 1, [[i, 1], [3, -1]]] for i in range(3)]
    old_rows += [[-2, 1, [[0, -1], [1, -1], [2, -1], [3, 1]]],
                [-9 * huge, 7 * huge, [[4, -huge]]], [0, 0, []]]
    toy.constraints.extend(constraint(pb, row) for row in old_rows)
    toy.constraints[-1].name = "preserved_named_empty_equation"
    before = toy.SerializeToString()
    rows = [[0, 0, [[3, 1]]]]
    parent, full, raw, suffix = append_suffix(pb, before, rows)
    assert raw == before + suffix and len(full.variables) == 5 and len(full.constraints) == 7
    assert gzip.decompress(gzip.compress(raw, mtime=0)) == raw
    changed = pb.CpModelProto()
    mutations = 0
    for field in ("old_coefficient", "old_variable_name", "new_row"):
        changed.CopyFrom(full)
        if field == "old_coefficient":
            changed.constraints[4].linear.coeffs[0] += 1
        elif field == "old_variable_name":
            changed.variables[1].name += "_changed"
        else:
            changed.constraints[6].linear.domain[1] = 1
        if field == "new_row":
            assert changed.constraints[6].SerializeToString() != constraint(pb, rows[0]).SerializeToString()
        else:
            del changed.constraints[6:]
            assert changed.SerializeToString() != before
        mutations += 1
    for bad in ([0, 0, [[0, 1], [0, -1]]], [0, 0, [[VARIABLES, 1]]], [0, 0, [[0, True]]]):
        try:
            constraint(pb, bad)
        except AssertionError:
            mutations += 1
        else:
            raise AssertionError("malformed row accepted")
    for mask in range(16):
        values = [(mask >> i) & 1 for i in range(4)]
        satisfied = all(row[0] <= sum(values[v] * c for v, c in row[2]) <= row[1] for row in old_rows[:4])
        assert satisfied == (values[3] == (values[0] & values[1] & values[2]))
        assert (satisfied and values[3] == 0) == (satisfied and sum(values[:3]) <= 2)
    assert mutations == 6
    tick(args, "synthetic exact prefix suffix and AND-zero controls")
    return {"schema": "conway99.f0.triangle-gap-model-controls.v1", "status": PASS["controls"],
        "runtime": runtime, "signed_large_integer": huge, "mutation_controls": mutations,
        "AND_zero_boolean_assignments": 16, "complete_parent_plus_suffix_exact": True,
        "old_variable_and_named_empty_row_metadata_preserved": True, "no_new_variables": True,
        "CpModel_constructed": False, "CpSolver_constructed": False, "native_optimizer_constructed": False,
        "native_query_run": False, "optimizer_calls": 0, "native_model_builds": 0}


def prepare(cfg, args):
    from ortools.sat import cp_model_pb2 as pb
    runtime = runtime_record(cfg, True)
    data = load_inputs(cfg)
    indices, rows = accepted_failed_indices(cfg, data)
    parent_raw = gzip.decompress(read_bytes(cfg["inputs"]["parent_model"]))
    assert len(parent_raw) == PARENT_RAW_BYTES and sha(parent_raw) == PARENT_RAW_SHA
    parent, model, expected_raw, suffix_raw = append_suffix(pb, parent_raw, rows)
    assert len(parent.variables) == VARIABLES and len(parent.constraints) == PARENT_ROWS
    assert {f.name for f, _ in parent.ListFields()} <= {"name", "variables", "constraints"}
    assert all(row.WhichOneof("constraint") == "linear" and not row.enforcement_literal for row in parent.constraints)
    assert len(model.variables) == VARIABLES and len(model.constraints) == FINAL_ROWS
    assert sum(len(r.linear.vars) for r in parent.constraints) == PARENT_TERMS
    assert sum(len(r.linear.vars) for r in model.constraints) == FINAL_TERMS
    tick(args, "accepted parent and independently certified unit-zero suffix")
    origins = gap_origins(pb, parent, data["gap_report"], indices, args)
    assert len(origins) == len(rows) == 3156
    preservation = {"complete_parent_raw_prefix_preserved": True, "complete_original_parent_bytes_recovered": True,
        "all_original_variable_messages_preserved": True, "all_original_constraint_messages_preserved": True,
        "original_variable_messages_sha256": message_digest(parent.variables),
        "original_constraint_messages_sha256": message_digest(parent.constraints),
        "parent_variables": VARIABLES, "parent_rows": PARENT_ROWS, "new_variables": 0, "replaced_rows": 0}
    base = bound_module("triangle_gap_native_transport", cfg["sources"]["base"])
    model_path = args.directory / "model.pb"
    assert not model_path.exists()
    native_model, transport = base.transport(model, model_path, args.deadline)
    assert transport["complete_byte_comparison"] is True and transport["public_parse_return"] is True
    assert transport["native_validation"] == "" and transport["optimizer_calls"] == 0 and transport["CpSolver_constructed"] is False
    raw = model_path.read_bytes()
    assert raw == expected_raw
    del native_model
    tick(args, "public native transport validation and complete byte comparison")
    row_sha = sha(canonical(rows))
    family_sha = {"gap_triangle_zero": row_sha}
    family_jsonl = {"gap_triangle_zero": sha(b"".join(canonical(row) + b"\n" for row in rows))}
    ledger = {"schema": "conway99.f0.triangle-gap-appended-row-ledger.v1",
        "source": binding(__file__), "configuration": binding(args.configuration),
        "gap_report": cfg["inputs"]["gap_report"], "gap_literal_report": cfg["inputs"]["gap_literal_report"],
        "gap_literal_root_acceptance": cfg["inputs"]["gap_literal_root_acceptance"],
        "family_order": FAMILY_ORDER, "family_counts": FAMILY_COUNTS, "family_terms": FAMILY_COUNTS,
        "failed_triangle_indices": indices, "row_keys": rows, "row_origins": origins,
        "row_keys_sha256": row_sha, "family_row_keys_sha256": family_sha, "all_certified_zeros_retained": True}
    ledger_raw = canonical(ledger) + b"\n"
    archives = {"model.pb.gz": gzip.compress(raw, compresslevel=6, mtime=0),
                "suffix.pb.gz": gzip.compress(suffix_raw, compresslevel=6, mtime=0),
                "append-rows.json.gz": gzip.compress(ledger_raw, compresslevel=6, mtime=0)}
    for name, archive in archives.items():
        write_new(args.directory / name, archive)
    assert gzip.decompress(archives["model.pb.gz"]) == raw
    assert parent_raw + gzip.decompress(archives["suffix.pb.gz"]) == raw
    assert gzip.decompress(archives["append-rows.json.gz"]) == ledger_raw
    artifacts = {"model": binding(model_path), "model_archive": binding(args.directory / "model.pb.gz"),
        "suffix_archive": binding(args.directory / "suffix.pb.gz"), "row_ledger": binding(args.directory / "append-rows.json.gz")}
    restoration = {"parent_raw_bytes": len(parent_raw), "parent_raw_sha256": sha(parent_raw),
                   "suffix_raw_bytes": len(suffix_raw), "suffix_raw_sha256": sha(suffix_raw)}
    manifest = {"schema": "conway99.f0.triangle-gap-restoration.v1",
        "status": "PASS_EXACT_TRIANGLE_GAP_PARENT_AND_SUFFIX_RESTORATION",
        "source": binding(__file__), "configuration": binding(args.configuration),
        "parent_model": cfg["inputs"]["parent_model"], "parent_root_acceptance": cfg["inputs"]["parent_root_acceptance"],
        "layout": LAYOUT, "artifacts": artifacts, "restoration": restoration,
        "suffix_format": "CpModelProto with only 3156 appended unit-zero constraints in ascending triangle index.",
        "apply_steps": ["Verify complete archive and raw hashes.", "Concatenate accepted parent raw bytes and suffix raw bytes.",
                        "Require exact equality with the complete native model bytes."],
        "parent_is_complete_raw_prefix": True, "complete_original_parent_bytes_recovered": True,
        "new_variables": 0, "replaced_rows": 0, "independent_full_model_replay_still_required": True}
    save(args.directory / "restoration-manifest.json", manifest)
    artifacts["restoration_manifest"] = binding(args.directory / "restoration-manifest.json")
    tick(args, "complete archives row ledger and restoration manifest")
    gap_check = {"forward_records_bound": 5364, "complete_failed_indices": 3156,
        "failed_triangle_indices_sha256": sha(canonical(indices)), "native_indicator_messages_checked": 3156,
        "native_edge_variable_messages_checked": 9468, "complete_native_AND_messages_checked": 12624,
        "all_certified_zeros_retained": True, "spectral_minor_recomputations": 0, "old_family_reconstructions": 0}
    return {"schema": "conway99.f0.triangle-gap-native-preparation.v1", "status": PASS["prepare"],
        "inputs": cfg["inputs"], "authorities": cfg["authorities"], "authority_links": cfg["authority_links"],
        "runtime": runtime, "layout": LAYOUT, "parent_variables": VARIABLES, "parent_rows": PARENT_ROWS,
        "variables": VARIABLES, "rows": FINAL_ROWS, "parent_total_terms": PARENT_TERMS, "total_terms": FINAL_TERMS,
        "term_change": 3156, "family_order": FAMILY_ORDER, "family_counts": FAMILY_COUNTS, "family_terms": FAMILY_COUNTS,
        "row_keys_sha256": row_sha, "family_row_keys_sha256": family_sha, "family_row_jsonl_sha256": family_jsonl,
        "model_raw_bytes": len(raw), "model_raw_sha256": sha(raw),
        "model": {"raw_bytes": len(raw), "raw_sha256": sha(raw), "archive_bytes": len(archives["model.pb.gz"]),
                  "archive_sha256": sha(archives["model.pb.gz"])},
        "artifacts": artifacts, "restoration": restoration, "preservation": preservation, "gap_check": gap_check,
        "gap_literal_root_acceptance": cfg["inputs"]["gap_literal_root_acceptance"], "native_transport": transport,
        "parent_is_complete_raw_prefix": True, "new_variables": 0, "replaced_rows": 0, "all_certified_zeros_retained": True,
        "original_variable_ids_preserved": True, "objective_hint_assumption_or_graph_symmetry_added": False,
        "CpModel_constructed": True, "CpSolver_constructed": False, "native_optimizer_constructed": False,
        "native_query_run": False, "optimizer_calls": 0, "native_model_builds": 1,
        "independent_full_model_replay_still_required": True, "graph_constructed": False, "whole_component_excluded": False,
        "all_original_pair_caps_included": False, "second_component_completion_included": False,
        "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def worker(args):
    args.started, args.stages = time.monotonic(), []
    try:
        cfg = load_configuration(args)
        result = controls(cfg, args) if args.mode == "controls" else prepare(cfg, args)
        result.update(source=binding(__file__), configuration=binding(args.configuration),
                      maximum_seconds=LIMITS[args.mode + "_worker_seconds"],
                      seconds_before_report_serialization=time.monotonic() - args.started)
        save(args.directory / "stages.json", args.stages)
        result["stages"] = binding(args.directory / "stages.json")
        assert time.monotonic() <= args.deadline
        save(args.directory / "report.json", result)
        assert time.monotonic() <= args.deadline
    except BaseException as error:
        if not (args.directory / "stages.json").exists():
            save(args.directory / "stages.json", args.stages)
        save(args.directory / "error.json", {"type": type(error).__name__, "message": str(error),
            "traceback": traceback.format_exc(), "mode": args.mode, "report_accepted": False, "optimizer_calls": 0})
        raise


def owned(args):
    started = time.monotonic()
    args.directory.mkdir(parents=True, exist_ok=False)
    limit = 15 if args.mode == "controls" else 135
    owner = {"schema": "conway99.f0.triangle-gap-native-owner.v1", "status": "ERROR_TRIANGLE_GAP_OWNER",
        "mode": args.mode, "source": binding(__file__), "configuration": binding(args.configuration),
        "report_accepted": False, "optimizer_calls": 0, "automatic_retries": 0,
        "CpSolver_constructed": False, "native_optimizer_constructed": False, "native_query_run": False, "supervision": None}
    save(args.directory / "initial-owner.json", owner)
    try:
        cfg = load_configuration(args)
        supervisor = bound_module("triangle_gap_supervisor", cfg["sources"]["supervisor"])
        command = [sys.executable, str(Path(__file__).resolve()), args.mode,
            "--configuration", str(args.configuration.resolve()), "--configuration-sha256", args.configuration_sha256,
            "--directory", str(args.directory.resolve()), "--worker",
            "--deadline", str(started + LIMITS[args.mode + "_worker_seconds"])]
        supervision = supervisor.supervise(command, args.directory, started + limit)
        owner["supervision"] = supervision
        save(args.directory / "owned-receipt.json", {"schema": "conway99.f0.triangle-gap-owned-receipt.v1",
            "source": owner["source"], "configuration": owner["configuration"], "mode": args.mode,
            "supervision": supervision, "supervisor_record": binding(args.directory / "supervisor.json"),
            "seconds": time.monotonic() - started, "maximum_seconds": limit})
        owner["owned_receipt"] = binding(args.directory / "owned-receipt.json")
        assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
        assert supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
        assert time.monotonic() - started <= limit
        report_path = args.directory / "report.json"
        report = json.loads(report_path.read_bytes())
        assert report["status"] == PASS[args.mode] and report["optimizer_calls"] == 0
        assert report["CpSolver_constructed"] is False and report["native_optimizer_constructed"] is False and report["native_query_run"] is False
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
            owner.update(status="ERROR_TRIANGLE_GAP_OWNER_OVERRUN", report_accepted=False)
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
