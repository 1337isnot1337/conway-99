"""Append independently certified literal families to the accepted Boolean parent.

This preparation source never constructs CpSolver. The parent is preserved
byte for byte. Source-bound input and acceptance receipts select every family.
A separate protobuf-only checker must accept the resulting complete model.
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
PARENT_VARIABLES = 68934
PARENT_ROWS = 168050
PARENT_RAW_BYTES = 33451907
PARENT_RAW_SHA = "4505234d13039159c3191918f7db729819ad6ed25f46e538d91975466d660e83"
EDGE_ORDER_SHA = "411052a41a473bb7199fe277516fb60c54018dec120309622a499229579791bb"
FAMILY_ORDER = ["three_one_edge", "three_path", "four_retained", "triangle_cover", "spectral_edge_zero", "signed_one_edge"]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def digest(path):
    return sha(Path(path).read_bytes())


def save(path, value):
    data = canonical(value) + b"\n"
    with path.open("xb") as stream:
        stream.write(data)


def binding(path):
    path = Path(path).resolve()
    data = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "bytes": len(data), "sha256": sha(data)}


def read_bytes(ref):
    data = (ROOT / ref["path"]).read_bytes()
    assert sha(data) == ref["sha256"], ref["path"]
    assert "bytes" not in ref or len(data) == ref["bytes"], ref["path"]
    return data


def read_json(ref):
    data = read_bytes(ref)
    if ref["path"].endswith(".gz"):
        data = gzip.decompress(data)
    if "raw_sha256" in ref:
        assert sha(data) == ref["raw_sha256"]
    return json.loads(data)


def bound_module(name, ref):
    read_bytes(ref)
    spec = importlib.util.spec_from_file_location(name, ROOT / ref["path"])
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def deadline_check(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("strengthened literal append deadline")


def row_key(lower, upper, terms):
    assert type(lower) is type(upper) is int and lower <= upper
    assert all(type(v) is type(c) is int and 0 <= v < PARENT_VARIABLES and c != 0 for v, c in terms)
    assert len({v for v, c in terms}) == len(terms)
    return [lower, upper, sorted(terms)]


def family_rows(loaded, edges, edge_index):
    three = loaded["three_inventory"]
    one, paths = three["proposed_one_edge"], three["proposed_paths"]
    assert len(one) == 1224 and one == sorted(one)
    assert len(paths) == 57996 and paths == sorted(paths)
    for edge, third, witness in one:
        assert 0 <= edge < len(edges) and 0 <= third < 480 and third not in edges[edge]
        yield "three_one_edge", row_key(0, 1, [[third, 1], [540 + edge, 1]])
    for center, left, right, origin in paths:
        assert 0 <= left < right < len(edges) and center in edges[left] and center in edges[right]
        yield "three_path", row_key(-1, 0, [[center, -1], [540 + left, 1], [540 + right, 1]])

    four = loaded["four_inventory"]
    keys, retained = four["row_keys"], four["retained_row_ids"]
    assert len(keys) == 72468
    assert sha(canonical(keys)) == "2adfcc619820604a3f49463bd0fd8109113ab7ce13bceadcc49554533b09dd1c"
    assert retained == sorted(set(retained))
    for rid in retained:
        assert type(rid) is int and 0 <= rid < len(keys)
        a, b, positive = keys[rid]
        assert 0 <= a < b < 480 and positive == sorted(set(positive))
        assert all(type(e) is int and 0 <= e < len(edges) for e in positive)
        yield "four_retained", row_key(-2, 0, [[a, -1], [b, -1]] + [[540 + e, 1] for e in positive])

    old_zeros = {row["edge_id"] for row in loaded["overlay"]["zero_rows"]}
    assert len(old_zeros) == 1884
    triangles = loaded["triangle_forward"]["families"][0]["nonpositive_determinant_records_with_nonnegative_proper_minors"]
    assert len(triangles) == 10830
    for a, b, c, determinant, ab_minor, ac_minor, bc_minor in triangles:
        assert 0 <= a < b < c < 480 and int(determinant) < 0
        es = [edge_index[(a, b)], edge_index[(a, c)], edge_index[(b, c)]]
        if any(e in old_zeros for e in es):
            continue
        yield "triangle_cover", row_key(0, 2, [[540 + e, 1] for e in es])

    spectral = loaded["spectral_forward"]
    for a, b, edge, already_literal in spectral["edge_zero_rows"]:
        assert type(edge) is int and 0 <= edge < len(edges)
        assert edges[edge] == [a, b] and type(already_literal) is bool
        assert already_literal == (edge in old_zeros)
        if not already_literal:
            yield "spectral_edge_zero", row_key(0, 0, [[540 + edge, 1]])

    signed = loaded["signed_certificates"]
    for key in signed["row_keys"]:
        lower, upper, terms = key
        assert lower == -2 and upper == 1 and len(terms) == 4
        assert key == row_key(lower, upper, terms)
        assert sum(v < 480 and c == 1 for v, c in terms) == 1
        assert sum(v >= 540 and c == 1 for v, c in terms) == 1
        assert sum(v >= 540 and c == -1 for v, c in terms) == 2
        yield "signed_one_edge", key


def runtime(cfg):
    from ortools.sat.python import cp_model
    from ortools.sat import cp_model_pb2
    import google.protobuf
    assert importlib.metadata.version("ortools") == cfg["runtime"]["ortools"] == "9.15.6755"
    assert google.protobuf.__version__ == cfg["runtime"]["protobuf"] == "6.33.6"
    return {"python": sys.version, "ortools": importlib.metadata.version("ortools"),
            "protobuf": google.protobuf.__version__, "cp_model_sha256": digest(cp_model.__file__),
            "native_helper_sha256": digest(cp_model.cmh.__file__),
            "model_schema_sha256": sha(cp_model_pb2.DESCRIPTOR.serialized_pb)}


def prepare(cfg, args, base):
    from ortools.sat import cp_model_pb2 as pb
    started = time.monotonic()
    runtime_record = runtime(cfg)
    loaded = {name: read_json(ref) for name, ref in cfg["inputs"].items() if name != "parent_model"}
    for authority in cfg["authorities"]:
        report = loaded[authority["input"]]
        assert report[authority.get("status_field", "status")] == authority["expected_status"]
    assert loaded["parent_cold"]["native_raw_model_sha256"] == PARENT_RAW_SHA
    assert loaded["parent_cold"]["complete_parent_bytes_checked"]
    assert loaded["parent_cold"]["optimizer_calls"] == 0
    parent = gzip.decompress(read_bytes(cfg["inputs"]["parent_model"]))
    assert len(parent) == PARENT_RAW_BYTES and sha(parent) == PARENT_RAW_SHA
    model = pb.CpModelProto()
    model.ParseFromString(parent)
    assert model.SerializeToString() == parent
    assert len(model.variables) == PARENT_VARIABLES and len(model.constraints) == PARENT_ROWS
    assert {field.name for field, value in model.ListFields()} <= {"name", "variables", "constraints"}
    edges = []
    for variable in model.variables[540:]:
        prefix, kind, left, right = variable.name.split("_")
        a, b = int(left), int(right)
        assert (prefix, kind) == ("shared", "edge") and 0 <= a < b < 480
        assert variable.name == "shared_edge_%03d_%03d" % (a, b) and list(variable.domain) == [0, 1]
        edges.append([a, b])
    assert len(edges) == 68394 and sha(canonical(edges)) == EDGE_ORDER_SHA
    assert all(list(v.domain) == [0, 1] for v in model.variables[:480])
    edge_index = {tuple(edge): i for i, edge in enumerate(edges)}
    counts = {name: 0 for name in FAMILY_ORDER}
    terms = {name: 0 for name in FAMILY_ORDER}
    row_digests = {name: hashlib.sha256() for name in FAMILY_ORDER}
    last_family = -1
    for name, key in family_rows(loaded, edges, edge_index):
        index = FAMILY_ORDER.index(name)
        assert index >= last_family
        last_family = index
        lower, upper, entries = key
        constraint = model.constraints.add().linear
        constraint.vars.extend(v for v, c in entries)
        constraint.coeffs.extend(c for v, c in entries)
        constraint.domain.extend([lower, upper])
        counts[name] += 1
        terms[name] += len(entries)
        row_digests[name].update(canonical(key) + b"\n")
        if sum(counts.values()) % 4096 == 0:
            deadline_check(args.deadline)
    assert counts == cfg["expected_family_counts"]
    assert terms == cfg["expected_family_terms"]
    final_rows = PARENT_ROWS + sum(counts.values())
    assert len(model.variables) == PARENT_VARIABLES and len(model.constraints) == final_rows
    expected_raw = model.SerializeToString()
    assert expected_raw.startswith(parent)
    retained = pb.CpModelProto()
    retained.CopyFrom(model)
    del retained.constraints[PARENT_ROWS:]
    assert retained.SerializeToString() == parent
    del retained
    deadline_check(args.deadline)
    _, transport = base.transport(model, args.directory / "model.pb", args.deadline)
    raw = (args.directory / "model.pb").read_bytes()
    assert raw == expected_raw and transport["complete_byte_comparison"]
    assert transport["public_parse_return"] is True and transport["native_validation"] == ""
    archive = gzip.compress(raw, compresslevel=6, mtime=0)
    (args.directory / "model.pb.gz").write_bytes(archive)
    suffix = raw[len(parent):]
    suffix_archive = gzip.compress(suffix, compresslevel=6, mtime=0)
    (args.directory / "suffix.pb.gz").write_bytes(suffix_archive)
    assert gzip.decompress(archive) == raw and parent + gzip.decompress(suffix_archive) == raw
    deadline_check(args.deadline)
    return {"schema": "conway99.f0.strengthened-append-preparation.v1",
            "status": "PASS_COMPLETE_STRENGTHENED_LITERAL_NATIVE_PREPARATION",
            "source": binding(__file__), "configuration": binding(args.configuration),
            "inputs": cfg["inputs"], "authorities": cfg["authorities"], "runtime": runtime_record,
            "parent_raw_sha256": PARENT_RAW_SHA, "parent_raw_bytes": len(parent),
            "variables": PARENT_VARIABLES, "parent_rows": PARENT_ROWS, "rows": final_rows,
            "family_order": FAMILY_ORDER, "family_counts": counts, "family_terms": terms,
            "family_row_jsonl_sha256": {name: h.hexdigest() for name, h in row_digests.items()},
            "model": {"raw_bytes": len(raw), "raw_sha256": sha(raw), "archive_bytes": len(archive),
                      "archive_sha256": sha(archive), "suffix_raw_bytes": len(suffix),
                      "suffix_raw_sha256": sha(suffix), "suffix_archive_bytes": len(suffix_archive),
                      "suffix_archive_sha256": sha(suffix_archive)},
            "native_transport": transport, "complete_parent_bytes_preserved": True,
            "parent_is_complete_raw_prefix": True, "no_variables_added_removed_or_identified": True,
            "objective_hint_assumption_or_graph_symmetry_added": False,
            "CpSolver_constructed": False, "optimizer_calls": 0, "native_query_run": False,
            "graph_constructed": False, "whole_component_excluded": False,
            "seconds": time.monotonic() - started,
            "peak_rss_KiB": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}


def main(args):
    started = time.monotonic()
    cfg = json.loads(args.configuration.read_bytes())
    assert cfg["source_sha256"] == digest(__file__)
    assert cfg["family_order"] == FAMILY_ORDER
    assert cfg["optimizer_calls"] == 0 and not cfg["native_query_authorized"]
    base = bound_module("strengthened_append_transport", cfg["sources"]["base"])
    if args.worker:
        try:
            result = base.controls(args.directory, args.deadline) if args.mode == "controls" else prepare(cfg, args, base)
            result["source"] = binding(__file__)
            result["configuration"] = binding(args.configuration)
            result["seconds"] = time.monotonic() - started
            save(args.directory / "report.json", result)
        except Exception as error:
            save(args.directory / "error.json", {"type": type(error).__name__, "message": str(error)})
            raise
        return
    args.directory.mkdir(parents=True, exist_ok=False)
    supervisor = bound_module("strengthened_append_supervisor", cfg["sources"]["supervisor"])
    limit = cfg["limits"]["controls_owner_seconds"] if args.mode == "controls" else cfg["limits"]["prepare_owner_seconds"]
    worker_limit = cfg["limits"]["controls_worker_seconds"] if args.mode == "controls" else cfg["limits"]["prepare_worker_seconds"]
    command = [sys.executable, str(Path(__file__).resolve()), args.mode,
               "--configuration", str(args.configuration.resolve()), "--directory", str(args.directory.resolve()),
               "--worker", "--deadline", str(started + worker_limit)]
    supervision = supervisor.supervise(command, args.directory, started + limit)
    elapsed = time.monotonic() - started
    owner = {"schema": "conway99.f0.strengthened-append-owner.v1",
             "source": binding(__file__), "configuration": binding(args.configuration),
             "mode": args.mode, "supervision": supervision, "seconds": elapsed, "maximum_seconds": limit,
             "deadline_overrun_seconds": max(0, elapsed - limit), "report_accepted": False,
             "status": supervision["status"], "optimizer_calls": 0, "CpSolver_constructed": False}
    report_path = args.directory / "report.json"
    if (supervision["status"] == "CHILD_EXITED" and supervision["returncode"] == 0
            and supervision["child_reaped"] is True and supervision["owned_process_group_stopped"] is True
            and elapsed <= limit and report_path.is_file()):
        report = json.loads(report_path.read_bytes())
        assert report["optimizer_calls"] == 0
        owner.update(report_accepted=True, status=report["status"], report=binding(report_path))
    save(args.directory / "owner.json", owner)
    print(json.dumps(owner, sort_keys=True), flush=True)
    if not owner["report_accepted"]:
        raise SystemExit(1)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("assertions are required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("controls", "prepare"))
    parser.add_argument("--configuration", required=True, type=Path)
    parser.add_argument("--directory", required=True, type=Path)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    assert not args.worker or args.deadline is not None
    main(args)
