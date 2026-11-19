"""Complete Boolean shared-edge extension of the accepted 540-variable parent.

Preserve the full parent, append all 68,394 eligible Boolean edges, both
endpoint activations, all 480 degree equations and all 8,640 mixed equations.
No graph symmetry, selector fixing, objective, hint, CpSolver or query.
This frozen base also supplies small actual public protobuf transport controls.
Proof-bound motif/clique overlays belong in a separate successor source.
"""
import argparse
import gzip
import hashlib
import importlib.util
from itertools import combinations
import json
from pathlib import Path
import resource
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
CONTROL_OWNER_SECONDS = 30
PARENT_SOURCE_SHA = "094c143d63011c0fee6dab95e2850634fd70fb1f7564b8c3e682cb02ef2f21c8"
SUPERVISOR = ("experiments/workspace/root_prism_free_f0_fixed_selection_exterior_query.py",
              "bbe476e5a7a13800c08265d4db541b7e8c7edf2277be03f6d06db134926891e3")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def digest(path):
    with Path(path).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def value_sha(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def save(path, value):
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_bytes(canonical(value) + b"\n")
    temporary.replace(path)


def check_time(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("Boolean shared-model preparation deadline reached")


def read_bound(binding, raw=False):
    path = ROOT / binding["path"]
    data = path.read_bytes()
    assert hashlib.sha256(data).hexdigest() == binding["sha256"]
    if raw:
        return data
    return json.loads(gzip.decompress(data) if path.suffix == ".gz" else data)


def load_context(configuration):
    cfg = json.loads(configuration.read_bytes())
    assert cfg["schema"] == "conway99.f0.boolean-shared-model-configuration.v1"
    assert cfg["base_builder_sha256"] == digest(__file__)
    loaded = {key: read_bound(binding) for key, binding in cfg["inputs"].items()
              if key not in {"parent_model", "registry", "replayed_registry"}}
    for key in ("registry", "replayed_registry"):
        assert digest(ROOT / cfg["inputs"][key]["path"]) == cfg["inputs"][key]["sha256"]
    assert cfg["inputs"]["registry"]["sha256"] == cfg["inputs"]["replayed_registry"]["sha256"]
    run, owner, cold, cold_owner, record = [loaded[k] for k in ("parent_run", "parent_owner", "parent_cold", "parent_cold_owner", "parent_iteration")]
    for receipt, report, key in [(owner, run, "parent_run"), (cold_owner, cold, "parent_cold")]:
        assert receipt["report_accepted"] and receipt["report_sha256"] == cfg["inputs"][key]["sha256"]
        assert receipt["source_sha256"] == PARENT_SOURCE_SHA and receipt["status"] == report["status"]
        assert receipt["deadline_overrun_seconds"] == 0 and receipt["supervision"]["child_reaped"]
        assert receipt["supervision"]["returncode"] == 0
    assert run["status"] == "UNKNOWN_MASTER_NATIVE" and run["production_solve_calls"] == 2
    assert cold["status"] == "PASS_COMPLETE_CALLED_PREFIXES_AND_EXACT_CERTIFICATES"
    assert cold["run_result_sha256"] == cfg["inputs"]["parent_run"]["sha256"]
    assert cold["run_owner_sha256"] == cfg["inputs"]["parent_owner"]["sha256"]
    assert cold["run_owner_accepted"] and not cold["run_outcome_relabelled"]
    assert not run["whole_component_excluded"] and not run["graph_constructed"]
    assert record["index"] == 1 and record["native_status"] == "UNKNOWN" and not record["direct_checked"]
    assert record["registry_rows"] == run["final_registry_rows"] == cold["final_replayed_registry_rows"] == 12481
    assert record["registry_sha256"] == run["final_registry_sha256"] == cold["final_replayed_registry_sha256"] == cfg["parent_registry_value_sha256"]
    assert record["prefix"]["archive_sha256"] == cfg["inputs"]["parent_model"]["sha256"]
    raw = gzip.decompress(read_bound(cfg["inputs"]["parent_model"], raw=True))
    assert len(raw) == record["prefix"]["raw_bytes"] == 24078662
    assert hashlib.sha256(raw).hexdigest() == record["prefix"]["raw_sha256"] == cfg["parent_model_raw_sha256"]
    assert record["prefix"]["rows"] == 17162
    assert run["definition"]["shared_definition"]["inputs"]["domain"] == [cfg["inputs"]["domain"]["path"], cfg["inputs"]["domain"]["sha256"]]
    domain = loaded["domain"]
    core = domain["component_core_rows"]
    assert len(core) == 21 and all(type(row) is int for row in core)
    assert all(not (core[i] >> i & 1) for i in range(21))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    adjacency = [(row >> 3) & ((1 << 18) - 1) for row in core[3:]]
    gram = [[12 * int(i == j) + 2 - (core[i + 3] & core[j + 3]).bit_count() - (core[i + 3] >> (j + 3) & 1)
             for j in range(18)] for i in range(18)]
    triples = []
    for h in combinations(range(18), 3):
        if max(sum(i // 6 == f for i in h) for f in range(3)) > 2:
            continue
        if any(gram[i][j] == 0 for i, j in combinations(h, 2)):
            continue
        if any(sum(int(i == j or adjacency[i] >> j & 1) for j in h) > 2 for i in range(18)):
            continue
        triples.append(list(h))
    assert len(triples) == 480 and triples == domain["signature_domain"]
    targets = [[2 - int(i in h) - sum(adjacency[i] >> j & 1 for j in h) for i in range(18)] for h in triples]
    assert targets == domain["row_targets"] and all(sum(q) == 24 and all(v in (0, 1, 2) for v in q) for q in targets)
    masks = [sum(1 << i for i in h) for h in triples]
    edges, neighbors, incident = [], [[] for _ in triples], [[] for _ in triples]
    for a, b in combinations(range(480), 2):
        if (masks[a] & masks[b]).bit_count() > 1:
            continue
        if any(targets[a][i] == 0 for i in triples[b]) or any(targets[b][i] == 0 for i in triples[a]):
            continue
        edge_id = len(edges)
        edges.append([a, b])
        neighbors[a].append(b); neighbors[b].append(a)
        incident[a].append((b, edge_id)); incident[b].append((a, edge_id))
    assert len(edges) == 68394 and neighbors == domain["possible_neighbor_signature_ids"]
    return {"configuration": cfg, "parent_raw": raw, "core": core, "triples": triples,
            "targets": targets, "gram": gram, "edges": edges, "neighbors": neighbors, "incident": incident}


def linear(proto, variables, coefficients, lower, upper):
    assert len(variables) == len(coefficients) and type(lower) is int and type(upper) is int and lower <= upper
    row = proto.constraints.add().linear
    row.vars.extend(variables)
    row.coeffs.extend(coefficients)
    row.domain.extend([lower, upper])


def expected_base(ctx, pb, deadline):
    parent = pb.CpModelProto()
    parent.ParseFromString(ctx["parent_raw"])
    assert parent.SerializeToString() == ctx["parent_raw"]
    assert len(parent.variables) == 540 and len(parent.constraints) == 17162
    assert all(list(parent.variables[a].domain) == [0, 1] for a in range(480))
    assert all(row.WhichOneof("constraint") == "linear" for row in parent.constraints)
    assert {field.name for field, _ in parent.ListFields()} <= {"name", "variables", "constraints"}
    expected = pb.CpModelProto()
    expected.CopyFrom(parent)
    for a, b in ctx["edges"]:
        variable = expected.variables.add()
        variable.name = "shared_edge_%03d_%03d" % (a, b)
        variable.domain.extend([0, 1])
    for edge_id, (a, b) in enumerate(ctx["edges"]):
        y = 540 + edge_id
        linear(expected, [a, y], [-1, 1], -1, 0)
        linear(expected, [b, y], [-1, 1], -1, 0)
    for a in range(480):
        variables = [a] + [540 + edge_id for _, edge_id in ctx["incident"][a]]
        linear(expected, variables, [-8] + [1] * (len(variables) - 1), 0, 0)
    empty_mixed = 0
    for a in range(480):
        for i in range(18):
            variables = [540 + edge_id for b, edge_id in ctx["incident"][a] if i in ctx["triples"][b]]
            coefficients = [1] * len(variables)
            target = ctx["targets"][a][i]
            if target:
                variables.insert(0, a)
                coefficients.insert(0, -target)
            if not variables:
                empty_mixed += 1
            linear(expected, variables, coefficients, 0, 0)
        check_time(deadline)
    assert len(expected.variables) == 68934 and len(expected.constraints) == 163070
    retained = pb.CpModelProto()
    retained.CopyFrom(expected)
    del retained.variables[540:]
    del retained.constraints[17162:]
    assert retained.SerializeToString() == ctx["parent_raw"]
    assert all(list(expected.variables[j].domain) == [0, 1] for j in range(540, 68934))
    inventory = {"variables": 68934, "original_variables": 540, "Boolean_edges": 68394,
                 "rows": 163070, "complete_parent_rows": 17162, "parent_selector_registry_rows": 12481,
                 "endpoint_activation_rows": 136788, "degree_rows": 480, "mixed_rows": 8640,
                 "explicit_empty_mixed_rows": empty_mixed, "complete_parent_bytes_preserved_as_submodel": True,
                 "signature_domain_sha256": value_sha(ctx["triples"]), "edge_domain_sha256": value_sha(ctx["edges"]),
                 "targets_sha256": value_sha(ctx["targets"]), "selector_fix_or_graph_symmetry": False,
                 "objective_hint_or_assumption": False, "CpSolver_constructed": False, "optimizer_calls": 0}
    return expected, inventory


def transport(expected, path, deadline):
    from google.protobuf import text_format
    from ortools.sat.python import cp_model
    started = time.monotonic()
    text = text_format.MessageToString(expected, use_short_repeated_primitives=True)
    model = cp_model.CpModel()
    parse_result = model.proto.parse_text_format(text)
    validation_error = model.validate()
    assert validation_error == "", validation_error
    assert model.export_to_file(str(path))
    raw = path.read_bytes()
    assert raw == expected.SerializeToString()
    check_time(deadline)
    return model, {"public_parse_return_type": type(parse_result).__name__, "public_parse_return": parse_result,
                   "text_format_characters": len(text), "native_raw_bytes": len(raw),
                   "native_raw_sha256": hashlib.sha256(raw).hexdigest(), "complete_byte_comparison": True,
                   "native_validation": validation_error, "seconds": time.monotonic() - started,
                   "CpSolver_constructed": False, "optimizer_calls": 0}


def controls(directory, deadline):
    from google.protobuf import text_format
    from ortools.sat import cp_model_pb2 as pb
    from ortools.sat.python import cp_model
    expected = pb.CpModelProto()
    for index, domain in enumerate(([0, 1], [0, 1], [0, 1], [-7, 9])):
        variable = expected.variables.add()
        variable.name = "transport_control_%d" % index
        variable.domain.extend(domain)
    linear(expected, [0, 2], [-1, 1], -1, 0)
    linear(expected, [1, 2], [-1, 1], -1, 0)
    linear(expected, [0, 1, 2], [1, 1, -2], 0, 0)
    linear(expected, [], [], 0, 0)
    coefficient = (1 << 54) + 3
    linear(expected, [3], [-coefficient], -9 * coefficient, 7 * coefficient)
    _, valid = transport(expected, directory / "valid-control.pb", deadline)
    bad = pb.CpModelProto()
    bad.CopyFrom(expected)
    bad.constraints[0].linear.vars[1] = 99
    bad_model = cp_model.CpModel()
    bad_model.proto.parse_text_format(text_format.MessageToString(bad, use_short_repeated_primitives=True))
    error = bad_model.validate()
    assert error
    assert bad_model.export_to_file(str(directory / "invalid-control.pb"))
    assert (directory / "invalid-control.pb").read_bytes() == bad.SerializeToString()
    check_time(deadline)
    return {"status": "PASS_PUBLIC_NATIVE_TEXT_TRANSPORT_EXACT_BYTES_AND_INVALID_INDEX_REJECTION",
            "source_sha256": digest(__file__), "valid_control": valid, "invalid_index_error": error,
            "Boolean_and_signed_domains_checked": True, "coefficient_above_binary64_exact_range_checked": coefficient,
            "empty_linear_equation_retained": True, "CpSolver_constructed": False, "optimizer_calls": 0}


def main(args):
    started = time.monotonic()
    if args.worker:
        try:
            cfg = json.loads(args.configuration.read_bytes())
            assert cfg["base_builder_sha256"] == digest(__file__)
            report = controls(args.directory, args.deadline)
            report.update(configuration_sha256=digest(args.configuration), seconds=time.monotonic() - started,
                          peak_rss_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            save(args.directory / "report.json", report)
        except Exception as error:
            save(args.directory / "error.json", {"type": type(error).__name__, "message": str(error)})
            raise
        return
    args.directory.mkdir(parents=True, exist_ok=False)
    path = ROOT / SUPERVISOR[0]
    assert digest(path) == SUPERVISOR[1]
    spec = importlib.util.spec_from_file_location("Boolean_shared_supervisor", path)
    supervisor = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(supervisor)
    command = [sys.executable, str(Path(__file__).resolve()), "--worker", "--configuration", str(args.configuration.resolve()),
               "--directory", str(args.directory.resolve()), "--deadline", str(started + CONTROL_OWNER_SECONDS)]
    save(args.directory / "owner.json", {"status": "UNKNOWN_BEFORE_CHILD", "report_accepted": False})
    supervision = supervisor.supervise(command, args.directory, started + CONTROL_OWNER_SECONDS)
    owner = {"source_sha256": digest(__file__), "maximum_seconds": CONTROL_OWNER_SECONDS, "supervision": supervision,
             "status": supervision["status"], "report_accepted": False, "CpSolver_constructed": False, "optimizer_calls": 0}
    if supervision["status"] == "CHILD_EXITED" and time.monotonic() <= started + CONTROL_OWNER_SECONDS:
        report = json.loads((args.directory / "report.json").read_bytes())
        owner.update(report_accepted=True, report_sha256=digest(args.directory / "report.json"), status=report["status"])
    owner.update(seconds=time.monotonic() - started, deadline_overrun_seconds=max(0, time.monotonic() - started - CONTROL_OWNER_SECONDS))
    if owner["deadline_overrun_seconds"]:
        owner.update(report_accepted=False, status="UNKNOWN_HARD_DEADLINE")
    save(args.directory / "owner.json", owner)
    print(json.dumps(owner, sort_keys=True), flush=True)


if __name__ == "__main__":
    if not __debug__:
        raise RuntimeError("native transport assertions required")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--configuration", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--worker", action="store_true")
    parser.add_argument("--deadline", type=float)
    args = parser.parse_args()
    assert not args.worker or args.deadline is not None
    main(args)
