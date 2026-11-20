"""Append the42 exact local profile tables to the frozen product parent.

No solve mode exists. Native models are built through public constructors;
the internal-proto mutation path is deliberately not used.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

import root_prism_free_f0_population_products_cpsat as parent

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
PARENT_SHA = "528f480b08adc5f1040807eec3eb96a75a8ea755eee28aec234f9d660034ff42"
PARENT_PROTO_SHA = "aa43ef31991213634b0cc812b61a5d1247c1915c6690def64a54247854ee8589"
INPUTS = {
    "profiles": ("f0-selector-orbit-profiles01.json.gz", "93c891e7eef037e5869e5c8e13c3cf31d0ad253cb6caf5cd38930b09715e085d"),
    "profile_cold": ("f0-selector-orbit-profiles01-cold.json", "cb10cd7dc77236d9caed7c7b8a410a33f7b998bea8d257b500d3c9f8561a76f8"),
    "independent_profile_audit": ("f0-selector-orbit-profiles-independent-audit.json", "e532fe58350ad856104333fba05b8601d776cbb98b76b3ce855ce8fa2a4be9a2"),
    "parent_cold": ("f0-population-products-cpsat01-cold/report.json", "fb287608e94737614fd58d51405855a551867cf121f201586b1c860ff4508930"),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def read_inputs():
    assert sha(Path(parent.__file__).read_bytes()) == PARENT_SHA
    data = {}
    for key, (name, expected) in INPUTS.items():
        raw = (LOGS / name).read_bytes()
        assert sha(raw) == expected
        data[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    assert all(data[k]["status"].startswith("PASS") for k in INPUTS if k != "profiles")
    specification = LOGS / "f0-population-products02-specification.json.gz"
    spec, linear = parent.bindings(specification)
    tables = data["profiles"]["tables"]
    assert len(tables) == 42 and sum(len(t["profiles"]) for t in tables) == 5733
    diagonal = {b["selector_orbits"][0]: b for b in spec["blocks"] if b["selector_orbits"][0] == b["selector_orbits"][1]}
    for i, table in enumerate(tables):
        assert table["selector_orbit"] == i
        assert table["count_columns"] == [i] + sorted(diagonal[i]["retained_pair_variables"])
        tuples = [p["counts"] for p in table["profiles"]]
        assert len(tuples) == len({tuple(t) for t in tuples})
        for values in tuples:
            assert len(values) == len(table["count_columns"])
            assert all(type(v) is int and 0 <= v <= spec["upper_by_variable"][j]
                       for j, v in zip(table["count_columns"], values))
            assert 2 * sum(values[1:]) == values[0] * (values[0] - 1)
    data.update(specification=spec, linear=linear)
    return data


def build(data):
    model = parent.build_proto(data["specification"], data["linear"])
    assert len(model.proto.variables) == 15941 and len(model.proto.constraints) == 29550
    for table in data["profiles"]["tables"]:
        variables = [model.get_int_var_from_proto_index(j) for j in table["count_columns"]]
        model.add_allowed_assignments(variables, [p["counts"] for p in table["profiles"]])
    assert len(model.proto.variables) == 15941 and len(model.proto.constraints) == 29592
    assert model.validate() == ""
    return model


def check_table(constraint, columns, tuples):
    assert {f.name for f, value in constraint.ListFields()} == {"table"}
    table = constraint.table
    assert not table.negated and not table.vars
    assert len(table.exprs) == len(columns)
    for expression, j in zip(table.exprs, columns):
        assert list(expression.vars) == [j] and list(expression.coeffs) == [1] and expression.offset == 0
    assert list(table.values) == [v for values in tuples for v in values]
    return len(table.values)


def check_proto(proto, data):
    assert {f.name for f, value in proto.ListFields()} == {"variables", "constraints"}
    assert len(proto.variables) == 15941 and len(proto.constraints) == 29592
    raw = (LOGS / "f0-population-products-cpsat01/model.pb").read_bytes()
    assert sha(raw) == PARENT_PROTO_SHA
    frozen = cp_model_pb2.CpModelProto()
    frozen.ParseFromString(raw)
    prefix = cp_model_pb2.CpModelProto()
    prefix.variables.extend(proto.variables)
    prefix.constraints.extend(proto.constraints[:29550])
    assert prefix == frozen
    checked = parent.literal_proto_check(prefix, data["specification"], data["linear"])
    entries = 0
    for index, table in enumerate(data["profiles"]["tables"]):
        entries += check_table(proto.constraints[29550 + index], table["count_columns"],
                               [p["counts"] for p in table["profiles"]])
    return {"parent_checks": checked, "all_parent_variables_and29550_constraints_unchanged": True,
            "tables_checked": 42, "tuples_checked": 5733, "tuple_integer_entries": entries,
            "variables": 15941, "constraints": 29592,
            "objective_hints_assumptions_or_strategy_added": False}


def inspect(point, data):
    assert len(point) == 15941 and all(type(x) is int for x in point)
    spec = data["specification"]
    assert all(0 <= v <= u for v, u in zip(point, spec["upper_by_variable"]))
    checked = parent.mathematics.inspect(point[:15038], spec, data["linear"])
    for block in spec["blocks"]:
        i, j = block["product_factors"]
        assert point[block["product_variable"]] == point[i] * point[j]
    for table in data["profiles"]["tables"]:
        assert tuple(point[j] for j in table["count_columns"]) in {tuple(p["counts"]) for p in table["profiles"]}
    return {"status": "PASS: exact product/profile count witness only", "original_count_check": checked,
            "product_auxiliaries_checked": 903, "local_profile_tables_checked": 42,
            "graph_or_literal_incidence_claimed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--archive", type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    directory = args.directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    data = read_inputs()
    if args.mode == "prepare":
        model = build(data)
        path = directory / "model.pb"
        assert model.export_to_file(str(path))
        raw = path.read_bytes()
        archive = directory / "model.pb.gz"
        with archive.open("xb") as stream:
            stream.write(gzip.compress(raw, mtime=0))
    else:
        assert args.archive is not None
        archive = args.archive.resolve()
        raw = gzip.decompress(archive.read_bytes())
    proto = cp_model_pb2.CpModelProto()
    proto.ParseFromString(raw)
    checked = check_proto(proto, data)
    report = {"status": "PASS: immutable42-table overlay " + args.mode,
              "source_sha256": sha(Path(__file__).read_bytes()), "parent_source_sha256": PARENT_SHA,
              "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k,(p,h) in INPUTS.items()},
              "parent_proto_sha256": PARENT_PROTO_SHA,
              "raw_proto_sha256": sha(raw), "raw_proto_bytes": len(raw),
              "archive": {"path": str(archive.relative_to(ROOT)), "sha256": sha(archive.read_bytes()), "bytes": archive.stat().st_size},
              "checks": checked, "ortools_version": parent.ortools.__version__,
              "optimizer_calls": 0, "CpSolver_constructed": False,
              "count_or_graph_feasibility_claimed": False, "seconds": time.monotonic() - started}
    parent.save_new(directory / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
