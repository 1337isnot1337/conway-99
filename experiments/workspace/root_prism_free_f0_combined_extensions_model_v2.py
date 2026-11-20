"""Build one exact combined extension of the accepted F0 Boolean model.

Only the 23,010 retained-four constraints are replaced. All old variable messages
and every other old constraint message are preserved. The public native transport
is unchanged. This source has no solver mode; separate complete protobuf replay
is mandatory before any later query. Construction uses accepted finite receipts.
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
PARENT_VARIABLES, PARENT_ROWS = 68934, 257594
PARENT_RAW_BYTES = 38374405
PARENT_RAW_SHA = "4a9b24ab1a0a1758ffedab226a9c45fe7765fafc40e76e23a039c9ccd098aee2"
EDGE_ORDER_SHA = "411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb"
MODEL_SCHEMA_SHA = "266b68151ffd6c9f5db22553442abd777031663d39e1cea649a8737f811d2eff"
FOUR_START, FOUR_COUNT = 227270, 23010
STAR_START, TRIANGLE_START, FOREST_START = 68934, 71382, 76746
FINAL_VARIABLES, FINAL_ROWS = 80730, 297470
FAMILY_ORDER = ["star_replacement", "star_definition", "triangle_and", "triangle_target", "forest"]
FAMILY_COUNTS = dict(zip(FAMILY_ORDER, [23010, 2448, 21456, 84, 15888]))
FAMILY_TERMS = dict(zip(FAMILY_ORDER, [69030, 22380, 53640, 5448, 59280]))
LAYOUT = {
    "parent_variables": PARENT_VARIABLES, "parent_rows": PARENT_ROWS,
    "replacement_start": FOUR_START, "replacement_count": FOUR_COUNT,
    "star_variable_start": STAR_START, "star_variables": 2448,
    "triangle_variable_start": TRIANGLE_START, "triangle_variables": 5364,
    "forest_variable_start": FOREST_START, "forest_variables": 3984,
    "star_definition_start": 257594, "triangle_and_start": 260042,
    "triangle_target_start": 281498, "forest_row_start": 281582,
    "new_variables": 11796, "appended_rows": 39876,
    "variables": FINAL_VARIABLES, "rows": FINAL_ROWS,
}
PASS = {"controls": "PASS_COMBINED_EXTENSIONS_MODEL_CONTROLS",
        "prepare": "PASS_COMPLETE_COMBINED_EXTENSIONS_NATIVE_PREPARATION"}
REQUIRED_INPUTS = {
    "parent_model", "parent_report", "parent_owner", "parent_cold", "parent_cold_owner",
    "parent_root_acceptance", "domain", "overlay", "four_inventory",
    "four_certificate_replay", "four_root_acceptance", "star_inventory",
    "star_finalization", "star_root_acceptance", "triangle_support_ledger",
    "triangle_literal_replay", "triangle_literal_finalization", "triangle_inventory",
    "triangle_finalization", "triangle_literal_root_acceptance", "forest_inventory",
    "forest_finalization", "forest_literal_replay", "forest_literal_finalization",
    "forest_literal_root_acceptance", "spectral_cold", "spectral_root_acceptance",
    "triangle_forward", "triangle_root_acceptance",
}
REQUIRED_AUTHORITIES = REQUIRED_INPUTS - {
    "parent_model", "domain", "overlay", "four_inventory", "triangle_support_ledger", "triangle_forward"
}


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
        raise TimeoutError("combined extension phase deadline")


def load_configuration(args):
    raw = args.configuration.read_bytes()
    if args.configuration_sha256:
        assert sha(raw) == args.configuration_sha256
    cfg = json.loads(raw)
    assert cfg["schema"] == "conway99.f0.combined-extensions-native-configuration.v1"
    assert cfg["source_sha256"] == digest(__file__)
    assert cfg["layout"] == LAYOUT
    assert cfg["family_order"] == FAMILY_ORDER
    assert cfg["expected_family_counts"] == FAMILY_COUNTS
    assert cfg["expected_family_terms"] == FAMILY_TERMS
    assert cfg["runtime"]["ortools"] == "9.15.6755"
    assert cfg["runtime"]["protobuf"] == "6.33.6"
    assert cfg["runtime"]["model_schema_sha256"] == MODEL_SCHEMA_SHA
    assert cfg["limits"]["controls_worker_seconds"] == 10
    assert cfg["limits"]["controls_owner_seconds"] == 15
    assert cfg["limits"]["prepare_worker_seconds"] == 120
    assert cfg["limits"]["prepare_owner_seconds"] == 135
    assert cfg["optimizer_calls"] == 0 and cfg["automatic_retries"] == 0
    assert cfg["native_query_authorized"] is False
    assert cfg["independent_complete_protobuf_replay_required"] is True
    assert REQUIRED_INPUTS <= set(cfg["inputs"])
    assert {"base", "supervisor", "checker"} <= set(cfg["sources"])
    assert cfg["sources"]["base"]["sha256"] == "5a1e8026683a7782fce6ec2a2947748356ac9cd5adf32dd2a0663b0dd60bfca2"
    assert cfg["sources"]["supervisor"]["sha256"] == "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3"
    for ref in cfg["sources"].values():
        read_bytes(ref)
    for ref in cfg.get("proofs", []) + cfg.get("reviews", []):
        read_bytes(ref)
    return cfg


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


def validate_owner(owner, report_ref):
    assert owner["report_accepted"] is True and owner["optimizer_calls"] == 0
    assert owner["seconds"] <= owner["maximum_seconds"]
    assert owner.get("deadline_overrun_seconds", 0) == 0
    supervision = owner["supervision"]
    assert supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
    assert supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
    same_ref(owner["report"], report_ref)


def load_inputs(cfg):
    loaded = {name: read_json(ref) for name, ref in cfg["inputs"].items() if name != "parent_model"}
    checked = set()
    for authority in cfg["authorities"]:
        name = authority["input"]
        assert name not in checked
        expected = authority["expected_status"]
        assert expected.startswith(("PASS_", "ROOT_ACCEPTS_", "OWNED_", "COMPLETE_"))
        assert loaded[name][authority.get("status_field", "status")] == expected, name
        checked.add(name)
    assert REQUIRED_AUTHORITIES <= checked
    for link in cfg.get("authority_links", []):
        value = loaded[link["input"]]
        for field in link["fields"]:
            value = value[field]
        same_ref(value, cfg["inputs"][link["target"]])
    root, report, cold = [loaded[name] for name in ("parent_root_acceptance", "parent_report", "parent_cold")]
    assert root["status"] == "ROOT_ACCEPTS_COMPLETE_STRENGTHENED_NATIVE_MODEL_AND_INDEPENDENT_COLD"
    assert report["status"] == "PASS_COMPLETE_STRENGTHENED_LITERAL_NATIVE_PREPARATION"
    assert cold["status"] == "PASS_INDEPENDENT_COMPLETE_STRENGTHENED_LITERAL_NATIVE_APPEND"
    for record in (root, cold):
        assert record["model_raw_sha256"] == PARENT_RAW_SHA and record["model_raw_bytes"] == PARENT_RAW_BYTES
        assert record["variables"] == PARENT_VARIABLES and record["rows"] == PARENT_ROWS
    assert report["model"]["raw_sha256"] == PARENT_RAW_SHA
    assert report["model"]["raw_bytes"] == PARENT_RAW_BYTES and report["optimizer_calls"] == 0
    same_ref(root["preparation"], cfg["inputs"]["parent_report"])
    same_ref(root["independent_cold"], cfg["inputs"]["parent_cold"])
    same_ref(root["model_archive"], cfg["inputs"]["parent_model"])
    same_ref(cold["producer_report"], cfg["inputs"]["parent_report"])
    same_ref(cold["producer_owner"], cfg["inputs"]["parent_owner"])
    validate_owner(loaded["parent_owner"], cfg["inputs"]["parent_report"])
    validate_owner(loaded["parent_cold_owner"], cfg["inputs"]["parent_cold"])
    for alias in ("parent_owner", "parent_cold_owner"):
        assert any(item["owner"]["sha256"] == cfg["inputs"][alias]["sha256"]
                   and item["owner"]["path"] == cfg["inputs"][alias]["path"] for item in root["owners"])
    assert loaded["star_inventory"]["complete"] is True
    assert loaded["forest_inventory"]["complete"] is True
    for name in ("star_inventory", "forest_inventory"):
        assert loaded[name]["original_model_raw_sha256"] == PARENT_RAW_SHA
        for old, new in (("domain", "domain"), ("overlay", "overlay"),
                         ("native_cold", "parent_cold"), ("native_root_acceptance", "parent_root_acceptance")):
            same_ref(loaded[name]["inputs"][old], cfg["inputs"][new])
    same_ref(loaded["triangle_inventory"]["inputs"]["ledger"], cfg["inputs"]["triangle_support_ledger"])
    same_ref(loaded["triangle_inventory"]["inputs"]["model_acceptance"], cfg["inputs"]["parent_root_acceptance"])
    same_ref(loaded["triangle_literal_replay"]["inputs"]["support_ledger"], cfg["inputs"]["triangle_support_ledger"])
    return loaded


def parent_model(cfg, pb):
    raw = gzip.decompress(read_bytes(cfg["inputs"]["parent_model"]))
    assert len(raw) == PARENT_RAW_BYTES and sha(raw) == PARENT_RAW_SHA
    model = pb.CpModelProto()
    model.ParseFromString(raw)
    assert model.SerializeToString() == raw
    assert len(model.variables) == PARENT_VARIABLES and len(model.constraints) == PARENT_ROWS
    assert {field.name for field, value in model.ListFields()} <= {"name", "variables", "constraints"}
    edges = []
    for entry in model.variables[540:]:
        parts = entry.name.split("_")
        assert len(parts) == 4 and parts[:2] == ["shared", "edge"]
        a, b = int(parts[2]), int(parts[3])
        assert 0 <= a < b < 480 and entry.name == "shared_edge_%03d_%03d" % (a, b)
        assert list(entry.domain) == [0, 1]
        edges.append([a, b])
    assert len(edges) == 68394 and sha(canonical(edges)) == EDGE_ORDER_SHA
    assert len({tuple(edge) for edge in edges}) == len(edges)
    assert all(list(entry.domain) == [0, 1] for entry in model.variables[:480])
    return raw, model, edges


def star_rows(loaded, parent, edges, pb):
    data, four = loaded["star_inventory"]["derived"], loaded["four_inventory"]
    channels, replacements = data["channels"], data["replacements"]
    assert len(channels) == 2448 and len(replacements) == FOUR_COUNT
    assert [r[0] for r in replacements] == four["retained_row_ids"]
    assert len(data["origin_links"]) == 46020
    assert channels == sorted(channels, key=lambda r: (r[0], r[1]))
    assert len({(r[0], tuple(r[1])) for r in channels}) == len(channels)
    witnesses = {}
    for witness in data["mixed_witnesses"]:
        k, center, site = witness["mixed_index"], witness["center"], witness["site"]
        assert k == 18 * center + site and 0 <= center < 480 and 0 <= site < 18
        assert k not in witnesses and witness["selector_coefficient"] == -1
        es = witness["positive_original_edge_ids"]
        assert es == sorted(set(es)) and all(type(e) is int and 0 <= e < 68394 for e in es)
        assert all(center in edges[e] for e in es)
        expected = constraint(pb, key(0, 0, [[center, -1]] + [[540 + e, 1] for e in es]))
        row_index = 154430 + k
        assert witness["native_row_index"] == row_index
        assert parent.constraints[row_index].SerializeToString() == expected.SerializeToString()
        witnesses[k] = set(es)
    assert len(witnesses) == 1002
    definitions, variables = [], []
    for k, (center, star, quota_keys, origin_count) in enumerate(channels):
        assert type(center) is int and 0 <= center < 480 and star
        assert star == sorted(set(star)) and quota_keys == sorted(set(quota_keys)) and quota_keys
        assert type(origin_count) is int and origin_count > 0
        assert all(type(e) is int and 0 <= e < 68394 and center in edges[e] for e in star)
        for qkey in quota_keys:
            assert type(qkey) is int and qkey // 18 == center and set(star) <= witnesses[qkey]
        variables.append(variable(pb, "four_star_channel_%04d" % k))
        definitions.append(key(0, 0, [[center, -1], [STAR_START + k, 1]] + [[540 + e, 1] for e in star]))
    result = []
    for rank, (rid, edge, left, right) in enumerate(replacements):
        assert type(rid) is type(edge) is type(left) is type(right) is int
        assert 0 <= rid < len(four["row_keys"]) and 0 <= edge < 68394
        assert 0 <= left < len(channels) and 0 <= right < len(channels) and left != right
        a, b = edges[edge]
        assert channels[left][0] == a and channels[right][0] == b
        positive = [edge] + channels[left][1] + channels[right][1]
        old = key(-2, 0, [[a, -1], [b, -1]] + [[540 + e, 1] for e in positive])
        assert four["row_keys"][rid] == [a, b, sorted(positive)]
        assert parent.constraints[FOUR_START + rank].SerializeToString() == constraint(pb, old).SerializeToString()
        result.append(key(-2, 0, [[540 + edge, 1], [STAR_START + left, -1], [STAR_START + right, -1]]))
    return variables, result, definitions


def triangle_rows(loaded, edges, pb):
    inventory = loaded["triangle_inventory"]
    triangles, targets = inventory["triangles"], inventory["targets"]
    assert inventory["live_targets"] == 84 and inventory["already_zero_targets"] == 48
    assert inventory["unique_surviving_support_triples"] == 5364
    assert inventory["target_triangle_incidences"] == 5364
    assert len(triangles) == 5364 and len(targets) == 84
    assert [t["vertices"] for t in triangles] == sorted(t["vertices"] for t in triangles)
    assert len({tuple(t["vertices"]) for t in triangles}) == len(triangles)
    assert [t["edge_id"] for t in targets] == sorted({t["edge_id"] for t in targets})
    variables, and_rows, equalities, uses = [], [], [], [[] for t in triangles]
    for k, triangle in enumerate(triangles):
        a, b, c = triangle["vertices"]
        assert type(a) is type(b) is type(c) is int and 0 <= a < b < c < 480
        assert triangle["triangle_index"] == k and triangle["proposed_variable_index"] == PARENT_VARIABLES + k
        es = triangle["edge_ids"]
        assert len(es) == 3 and all(type(e) is int and 0 <= e < 68394 for e in es)
        assert [edges[e] for e in es] == [[a, b], [a, c], [b, c]]
        t = TRIANGLE_START + k
        variables.append(variable(pb, "spectral_triangle_%04d" % k))
        for edge in es:
            and_rows.append(key(0, 1, [[540 + edge, 1], [t, -1]]))
        and_rows.append(key(-2, 1, [[t, 1]] + [[540 + e, -1] for e in es]))
    for target in targets:
        edge, indices = target["edge_id"], target["triangle_indices"]
        assert type(edge) is int and 0 <= edge < 68394 and target["endpoints"] == edges[edge]
        assert indices and indices == sorted(set(indices))
        assert all(type(i) is int and 0 <= i < len(triangles) for i in indices)
        for i in indices:
            assert edge in triangles[i]["edge_ids"]
            uses[i].append(edge)
        equalities.append(key(0, 0, [[540 + edge, -1]] + [[TRIANGLE_START + i, 1] for i in indices]))
    for triangle, used in zip(triangles, uses):
        origins = triangle["origins"]
        assert len(used) == 1 and [origin["target_edge_id"] for origin in origins] == used
    return variables, and_rows, equalities


def forest_rows(loaded, pb):
    data = loaded["forest_inventory"]["derived"]
    counts = data["counts"]
    assert counts["accepted_pairs"] == counts["extended_pairs"] == 48
    assert counts["endpoint_forest_skipped_pairs"] == 0 and counts["accepted_zero_union"] == 1956
    assert counts["new_variables"] == 3984 and counts["new_rows"] == 15888 and counts["new_terms"] == 59280
    records, old_rows = data["proposed_native_variables"], data["proposed_native_row_keys"]
    assert len(records) == 3984 and len(old_rows) == len(data["row_origins"]) == 15888
    assert len(data["pairs"]) == 48
    variables = []
    for k, (old_index, name, domain, pair_index, candidate) in enumerate(records):
        assert old_index == PARENT_VARIABLES + k and domain == [0, 1]
        assert type(pair_index) is int and 0 <= pair_index < 48
        a, b = data["pairs"][pair_index]["anchor_pair"]
        assert type(candidate) is int and -1 <= candidate < 480
        expected = "cap1_total_%d_%d" % (a, b) if candidate == -1 else "cap1_wedge_%d_%d_%d" % (a, b, candidate)
        assert name == expected
        variables.append(variable(pb, name))
    rows = []
    shift = FOREST_START - PARENT_VARIABLES
    for lower, upper, entries in old_rows:
        assert key(lower, upper, entries, PARENT_VARIABLES + len(records)) == [lower, upper, entries]
        rows.append(key(lower, upper, [[v + shift if v >= PARENT_VARIABLES else v, c] for v, c in entries]))
    assert len({v.name for v in variables}) == len(variables)
    return variables, rows


def apply_patch(pb, parent_raw, patch_raw, replacement_start, replacement_count):
    parent = pb.CpModelProto()
    parent.ParseFromString(parent_raw)
    assert parent.SerializeToString() == parent_raw
    patch = pb.CpModelProto()
    patch.ParseFromString(patch_raw)
    assert patch.SerializeToString() == patch_raw
    assert {field.name for field, value in patch.ListFields()} <= {"variables", "constraints"}
    assert len(patch.constraints) == replacement_count
    assert 0 <= replacement_start <= len(parent.constraints) - replacement_count
    parent.variables.extend(patch.variables)
    for k, replacement in enumerate(patch.constraints):
        parent.constraints[replacement_start + k].CopyFrom(replacement)
    return parent


def recover_parent(pb, full, original, replacement_start, replacement_count):
    recovered = pb.CpModelProto()
    recovered.CopyFrom(full)
    del recovered.variables[len(original.variables):]
    del recovered.constraints[len(original.constraints):]
    for k in range(replacement_count):
        recovered.constraints[replacement_start + k].CopyFrom(original.constraints[replacement_start + k])
    return recovered.SerializeToString()


def message_digest(messages):
    h = hashlib.sha256()
    for message in messages:
        raw = message.SerializeToString()
        h.update(len(raw).to_bytes(8, "big"))
        h.update(raw)
    return h.hexdigest()


def controls(cfg, args):
    from ortools.sat import cp_model_pb2 as pb
    runtime = runtime_record(cfg, False)
    original = pb.CpModelProto()
    original.name = "exact-prefix-patch-control"
    original.variables.extend([variable(pb, "old_bool_0"), variable(pb, "old_bool_1")])
    signed = original.variables.add()
    signed.name = "old_signed"
    signed.domain.extend([-7, 9])
    huge = (1 << 54) + 3
    original.constraints.extend([
        constraint(pb, key(0, 1, [[0, 1], [1, 1]])),
        constraint(pb, key(-9 * huge, 7 * huge, [[2, -huge]])),
        constraint(pb, key(0, 0, [])),
    ])
    original.constraints[2].name = "preserved-empty-equation"
    parent_raw = original.SerializeToString()
    patch = pb.CpModelProto()
    patch.variables.extend([variable(pb, "new_bool_0"), variable(pb, "new_bool_1")])
    patch.constraints.extend([constraint(pb, key(-1, 0, [[0, -1], [3, 1]]))])
    patch_raw = patch.SerializeToString()
    prefix = apply_patch(pb, parent_raw, patch_raw, 0, 1)
    prefix_raw = prefix.SerializeToString()
    suffix = pb.CpModelProto()
    suffix.constraints.extend([constraint(pb, key(0, 0, [[1, -1], [4, 1]])),
                               constraint(pb, key(-2, 0, [[3, -1], [4, -1]]))])
    suffix_raw = suffix.SerializeToString()
    prefix.constraints.extend(suffix.constraints)
    full = prefix.SerializeToString()
    assert full == prefix_raw + suffix_raw and not full.startswith(parent_raw)
    assert recover_parent(pb, prefix, original, 0, 1) == parent_raw
    assert list(prefix.constraints[1].linear.coeffs) == [-huge]
    assert prefix.variables[2].SerializeToString() == original.variables[2].SerializeToString()
    assert prefix.constraints[2].SerializeToString() == original.constraints[2].SerializeToString()
    assert gzip.decompress(gzip.compress(patch_raw, mtime=0)) == patch_raw
    assert gzip.decompress(gzip.compress(suffix_raw, mtime=0)) == suffix_raw
    negative_controls = 0
    wrong = pb.CpModelProto()
    wrong.CopyFrom(prefix)
    wrong.constraints[1].linear.coeffs[0] += 1
    assert recover_parent(pb, wrong, original, 0, 1) != parent_raw
    negative_controls += 1
    wrong.CopyFrom(prefix)
    wrong.variables[1].name += "_changed"
    assert recover_parent(pb, wrong, original, 0, 1) != parent_raw
    negative_controls += 1
    assert prefix_raw + suffix_raw[:-1] != full
    negative_controls += 1
    deadline_check(args.deadline)
    return {"schema": "conway99.f0.combined-extensions-model-controls.v1",
            "status": PASS["controls"], "runtime": runtime,
            "signed_large_integer": huge, "patch_and_suffix_exact": True,
            "original_full_bytes_recovered": True, "mutated_input_controls": negative_controls,
            "new_variable_before_constraint_serialization_checked": True,
            "CpModel_constructed": False, "CpSolver_constructed": False,
            "native_optimizer_constructed": False, "native_query_run": False, "optimizer_calls": 0}


def stage(args, name):
    args.stages.append({"phase": name, "elapsed_seconds": time.monotonic() - args.started})
    deadline_check(args.deadline)


def prepare(cfg, args):
    from ortools.sat import cp_model_pb2 as pb
    runtime = runtime_record(cfg, True)
    loaded = load_inputs(cfg)
    parent_raw, original, edges = parent_model(cfg, pb)
    stage(args, "accepted_inputs_and_parent_decoded")
    star_vars, replacements, definitions = star_rows(loaded, original, edges, pb)
    triangle_vars, triangle_and, triangle_target = triangle_rows(loaded, edges, pb)
    forest_vars, forest = forest_rows(loaded, pb)
    groups = dict(zip(FAMILY_ORDER, [replacements, definitions, triangle_and, triangle_target, forest]))
    counts = {name: len(rows) for name, rows in groups.items()}
    terms = {name: sum(len(row[2]) for row in rows) for name, rows in groups.items()}
    assert counts == FAMILY_COUNTS and terms == FAMILY_TERMS
    row_hashes = {}
    for name, rows in groups.items():
        h = hashlib.sha256()
        for row in rows:
            h.update(canonical(row) + b"\n")
        row_hashes[name] = h.hexdigest()
    stage(args, "complete_literal_row_and_variable_lists")
    patch = pb.CpModelProto()
    patch.variables.extend(star_vars + triangle_vars + forest_vars)
    patch.constraints.extend(constraint(pb, row) for row in replacements)
    assert len(patch.variables) == 11796 and len(patch.constraints) == FOUR_COUNT
    patch_raw = patch.SerializeToString()
    model = apply_patch(pb, parent_raw, patch_raw, FOUR_START, FOUR_COUNT)
    assert len(model.variables) == FINAL_VARIABLES and len(model.constraints) == PARENT_ROWS
    edited_prefix_raw = model.SerializeToString()
    suffix = pb.CpModelProto()
    for name in FAMILY_ORDER[1:]:
        suffix.constraints.extend(constraint(pb, row) for row in groups[name])
    assert len(suffix.constraints) == 39876
    suffix_raw = suffix.SerializeToString()
    model.constraints.extend(suffix.constraints)
    assert len(model.constraints) == FINAL_ROWS
    assert len({entry.name for entry in patch.variables}) == LAYOUT["new_variables"]
    expected_raw = model.SerializeToString()
    assert expected_raw == edited_prefix_raw + suffix_raw
    assert not expected_raw.startswith(parent_raw)
    assert recover_parent(pb, model, original, FOUR_START, FOUR_COUNT) == parent_raw
    for k, entry in enumerate(original.variables):
        assert entry.SerializeToString() == model.variables[k].SerializeToString()
    unchanged = []
    for k, entry in enumerate(original.constraints):
        if not FOUR_START <= k < FOUR_START + FOUR_COUNT:
            assert entry.SerializeToString() == model.constraints[k].SerializeToString()
            unchanged.append(entry)
    parent_terms = sum(len(row.linear.vars) for row in original.constraints)
    final_terms = sum(len(row.linear.vars) for row in model.constraints)
    assert final_terms - parent_terms == -192096
    preservation = {
        "original_variable_messages_sha256": message_digest(original.variables),
        "unreplaced_parent_constraint_messages_sha256": message_digest(unchanged),
        "unreplaced_parent_constraints": len(unchanged),
        "complete_original_parent_bytes_recovered": True,
        "all_original_variable_messages_preserved": True,
        "all_unreplaced_parent_constraint_messages_preserved": True,
        "only_declared_replacement_span_changed": True,
    }
    del unchanged
    stage(args, "protobuf_patch_suffix_and_parent_recovery_checked")
    base = bound_module("combined_extensions_native_transport", cfg["sources"]["base"])
    model_path = args.directory / "model.pb"
    assert not model_path.exists()
    native_model, transport = base.transport(model, model_path, args.deadline)
    assert transport["complete_byte_comparison"] is True
    assert transport["public_parse_return"] is True and transport["native_validation"] == ""
    raw = model_path.read_bytes()
    assert raw == expected_raw
    del native_model
    stage(args, "public_native_transport_and_exact_export")
    archives = {
        "model.pb.gz": gzip.compress(raw, compresslevel=6, mtime=0),
        "prefix-patch.pb.gz": gzip.compress(patch_raw, compresslevel=6, mtime=0),
        "suffix.pb.gz": gzip.compress(suffix_raw, compresslevel=6, mtime=0),
    }
    for filename, data in archives.items():
        write_new(args.directory / filename, data)
    assert gzip.decompress(archives["model.pb.gz"]) == raw
    restored_prefix = apply_patch(pb, parent_raw, gzip.decompress(archives["prefix-patch.pb.gz"]), FOUR_START, FOUR_COUNT)
    assert restored_prefix.SerializeToString() + gzip.decompress(archives["suffix.pb.gz"]) == raw
    artifacts = {
        "model": binding(model_path),
        "model_archive": binding(args.directory / "model.pb.gz"),
        "patch_archive": binding(args.directory / "prefix-patch.pb.gz"),
        "suffix_archive": binding(args.directory / "suffix.pb.gz"),
    }
    restoration = {
        "parent_raw_bytes": len(parent_raw), "parent_raw_sha256": sha(parent_raw),
        "patch_raw_bytes": len(patch_raw), "patch_raw_sha256": sha(patch_raw),
        "edited_prefix_raw_bytes": len(edited_prefix_raw), "edited_prefix_raw_sha256": sha(edited_prefix_raw),
        "suffix_raw_bytes": len(suffix_raw), "suffix_raw_sha256": sha(suffix_raw),
    }
    manifest = {
        "schema": "conway99.f0.combined-extensions-restoration.v1",
        "status": "PASS_EXACT_COMBINED_PATCH_AND_SUFFIX_RESTORATION",
        "source": binding(__file__), "configuration": binding(args.configuration),
        "parent_model": cfg["inputs"]["parent_model"], "layout": LAYOUT,
        "artifacts": artifacts, "restoration": restoration,
        "patch_variables": 11796, "patch_constraints": FOUR_COUNT, "suffix_constraints": 39876,
        "patch_format": "CpModelProto with only appended variables and replacement constraints in declared order.",
        "suffix_format": "CpModelProto with only the appended constraints; its raw bytes are the exact edited-prefix suffix.",
        "apply_steps": [
            "Verify all compressed and raw identities before use.",
            "Decode the accepted parent and the decompressed prefix patch.",
            "Append patch.variables after all original variables.",
            "Copy patch.constraints[k] into parent.constraints[227270+k] for 0 <= k < 23010.",
            "Serialize that edited prefix and check its bytes and SHA256.",
            "Concatenate the edited-prefix raw bytes and the decompressed suffix raw bytes.",
            "Check the complete result against the exported model raw bytes and SHA256.",
        ],
        "parent_is_complete_raw_prefix": False,
        "edited_prefix_is_complete_raw_prefix": True,
        "complete_original_parent_bytes_recovered": True,
        "independent_full_model_replay_still_required": True,
    }
    save(args.directory / "restoration-manifest.json", manifest)
    artifacts["restoration_manifest"] = binding(args.directory / "restoration-manifest.json")
    stage(args, "lossless_archives_and_restoration_manifest_saved")
    return {
        "schema": "conway99.f0.combined-extensions-native-preparation.v1",
        "status": PASS["prepare"], "inputs": cfg["inputs"], "authorities": cfg["authorities"],
        "authority_links": cfg.get("authority_links", []), "runtime": runtime, "layout": LAYOUT,
        "parent_variables": PARENT_VARIABLES, "parent_rows": PARENT_ROWS,
        "variables": FINAL_VARIABLES, "rows": FINAL_ROWS,
        "family_order": FAMILY_ORDER, "family_counts": counts, "family_terms": terms,
        "family_row_jsonl_sha256": row_hashes,
        "parent_total_terms": parent_terms, "total_terms": final_terms, "term_change": -192096,
        "model_raw_bytes": len(raw), "model_raw_sha256": sha(raw),
        "model": {"raw_bytes": len(raw), "raw_sha256": sha(raw),
                  "archive_bytes": len(archives["model.pb.gz"]), "archive_sha256": sha(archives["model.pb.gz"])},
        "artifacts": artifacts, "restoration": restoration, "preservation": preservation,
        "native_transport": transport, "parent_is_complete_raw_prefix": False,
        "edited_prefix_is_complete_raw_prefix": True,
        "original_variable_ids_preserved": True, "objective_hint_assumption_or_graph_symmetry_added": False,
        "CpModel_constructed": True, "CpSolver_constructed": False, "native_optimizer_constructed": False,
        "native_query_run": False, "optimizer_calls": 0, "native_model_builds": 1,
        "independent_full_model_replay_still_required": True,
        "graph_constructed": False, "whole_component_excluded": False,
        "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }


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
        "schema": "conway99.f0.combined-extensions-native-owner.v1",
        "status": "ERROR_COMBINED_EXTENSIONS_OWNER", "mode": args.mode,
        "source": binding(__file__), "configuration": binding(args.configuration),
        "report_accepted": False, "optimizer_calls": 0, "automatic_retries": 0,
        "CpSolver_constructed": False, "native_optimizer_constructed": False,
        "native_query_run": False, "supervision": None,
    }
    save(args.directory / "initial-owner.json", owner)
    limit = 15 if args.mode == "controls" else 135
    try:
        cfg = load_configuration(args)
        supervisor = bound_module("combined_extensions_supervisor", cfg["sources"]["supervisor"])
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
            "schema": "conway99.f0.combined-extensions-owned-receipt.v1",
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
            owner.update(status="ERROR_COMBINED_EXTENSIONS_OWNER_OVERRUN", report_accepted=False)
        save(args.directory / "owner.json", owner)
        print(json.dumps(owner, sort_keys=True), flush=True)
    return 0 if owner["report_accepted"] else 1


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("controls", "prepare"))
    parser.add_argument("--configuration", required=True, type=Path)
    parser.add_argument("--configuration-sha256")
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    assert not args.worker or args.deadline is not None
    if args.worker:
        worker(args)
    else:
        raise SystemExit(owned(args))
