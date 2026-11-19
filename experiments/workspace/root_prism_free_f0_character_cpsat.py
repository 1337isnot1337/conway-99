"""Immutable signed-character overlay on the full F0 count/product model.

This is preparation and exact replay only. No CpSolver is constructed here.
The 118 local signed-population IDs are explicitly translated to fresh native
variable IDs. All old variables, rows, products and 42 tables stay unchanged.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import time

from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

import root_prism_free_f0_population_profile_cpsat as parent

ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / "experiments/logs/root-prism-free"
PARENT_SHA = "a5b4485f4f30cdcb640d7cb63a5d4b1df4828e8f092f164fdad5a4a21260a67b"
PARENT_PROTO_SHA = "500ab3e32622fe59eb45044a5d2610b087c030786df821ee06b85c8f0f3d21ef"
PARENT_ARCHIVE_SHA = "e1bd3e50c48f0a600a202aabbeecc80627fc4b6b1096ef32cdd8c17c8ed7d431"
INPUTS = {
    "parent_preparation": ("f0-population-profile-cpsat01/report.json", "6e8ffe6be93bae81e4cf2b0879520453166082796eaf6055c9e21b5ee8bb6305"),
    "parent_cold": ("f0-population-profile-cpsat01-cold/report.json", "de7dd1b32377755f9a1748553507909d001f5bc7984044ce4c290a351623a485"),
    "product_review": ("f0-population-products-root-source-review.json", "643c8b2b832c317c83f69d22690161bf47d4e4800920b9155a3a6aad01b543f0"),
    "characters": ("f0-character-populations01.json.gz", "139d06a3383f8fc79d677972ce052ce29966e8b3406e7d1e7d1077aea7c2cef6"),
    "character_cold": ("f0-character-populations01-cold.json", "1fdc14c0bda54f0b5e63b23a3b7d5f85d9afd92ea418b4931d53b644444e814b"),
    "character_review": ("f0-character-populations-literature-review.json", "f5164ac7a59cd75c9fdd3c74364e772701038c9c8347c15ae9b6c7990c110149"),
    "gram": ("f0-character-Gram-equalities01.json", "084764b528f9a75269c8e21bb0b55b480a552022b024db72a4357aca083770c7"),
    "gram_cold": ("f0-character-Gram-equalities01-cold.json", "482ccc5f26d4668ef1f45fab6200eeb2328b92e0b949b7e026052c1354cd1f7f"),
    "gram_review": ("f0-character-Gram-literature-review.json", "3e5c3b3e834f3f33f2043397d168a36e94e6355a45c38a57e5065547e0abdddb"),
}
OLD_VARIABLES, OLD_CONSTRAINTS = 15941, 29592
SIGNED_OFFSET, SIGNED_COUNT = 15941, 118
PRODUCT_OFFSET, PRODUCT_COUNT = 16059, 2385
VARIABLES, CONSTRAINTS = 18444, 34436


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    parent.parent.save_new(path, value)


def signed_variable(local):
    assert type(local) is int and 0 <= local < SIGNED_COUNT
    return SIGNED_OFFSET + local


def read_inputs():
    assert sha(Path(parent.__file__).read_bytes()) == PARENT_SHA
    data = {"parent": parent.read_inputs()}
    for key, (name, expected) in INPUTS.items():
        raw = (LOGS / name).read_bytes()
        assert sha(raw) == expected
        data[key] = json.loads(gzip.decompress(raw) if name.endswith(".gz") else raw)
    for key in INPUTS:
        if key not in ("characters", "gram"):
            assert data[key]["status"].startswith("PASS")
    assert data["parent_preparation"]["raw_proto_sha256"] == PARENT_PROTO_SHA
    assert data["parent_cold"]["raw_proto_sha256"] == PARENT_PROTO_SHA
    characters = data["characters"]
    populations, products = characters["signed_populations"], characters["product_equations"]
    assert len(populations) == SIGNED_COUNT and len(products) == PRODUCT_COUNT
    assert len(characters["local_tables"]) == 42
    assert sum(len(t["profiles"]) for t in characters["local_tables"]) == 19331
    assert len(data["gram"]["equations"]) == 32
    assert not characters["graph_automorphism_assumed"]
    bounds = [[0, u] for u in data["parent"]["specification"]["upper_by_variable"]]
    for i, population in enumerate(populations):
        assert population["signed_population"] == i
        members, signs = population["literal_selectors"], population["signs"]
        assert len(members) in (6, 12) and len(signs) == len(members)
        assert all(s in (-1, 1) for s in signs) and sum(signs) == 0
        assert population["raw_lower"] == -len(members) // 2
        assert population["raw_upper"] == len(members) // 2
        bounds.append([population["raw_lower"], population["raw_upper"]])
    for equation in products:
        a, b = equation["signed_population_factors"]
        assert populations[a]["character"] == populations[b]["character"] == equation["character"]
        assert equation["selector_orbits"] == [populations[a]["selector_orbit"], populations[b]["selector_orbit"]]
        magnitude = bounds[signed_variable(a)][1] * bounds[signed_variable(b)][1]
        bounds.append([0 if a == b else -magnitude, magnitude])
        terms = equation["count_terms"]
        assert terms == sorted(terms) and len({j for j, c in terms}) == len(terms)
        assert all(type(j) is int and 0 <= j < 15038 and type(c) is int and c for j, c in terms)
    assert len(bounds) == VARIABLES
    for i, table in enumerate(characters["local_tables"]):
        old = data["parent"]["profiles"]["tables"][i]
        assert table["selector_orbit"] == old["selector_orbit"] == i
        assert table["count_columns"] == old["count_columns"]
        ids = table["signed_population_columns"]
        assert ids == [p["signed_population"] for p in populations if p["selector_orbit"] == i]
        columns = table_columns(table)
        tuples = [p["counts_and_signed_populations"] for p in table["profiles"]]
        assert len(tuples) == len({tuple(t) for t in tuples})
        projected = Counter()
        for profile in table["profiles"]:
            values = profile["counts_and_signed_populations"]
            assert len(values) == len(columns)
            assert all(type(v) is int and bounds[j][0] <= v <= bounds[j][1] for j, v in zip(columns, values))
            projected[tuple(values[:len(table["count_columns"])])] += profile["literal_subset_count"]
        assert dict(projected) == {tuple(p["counts"]): p["literal_subset_count"] for p in old["profiles"]}
    for i, row in enumerate(data["gram"]["equations"]):
        assert row["equation"] == i and row["rhs"] == 0
        assert row["signed_population_terms"] == sorted(row["signed_population_terms"])
        assert len({j for j, c in row["signed_population_terms"]}) == len(row["signed_population_terms"])
        assert all(populations[j]["character"] == row["character"] and type(c) is int and c
                   for j, c in row["signed_population_terms"])
    data["bounds"] = bounds
    return data


def table_columns(table):
    return table["count_columns"] + [signed_variable(j) for j in table["signed_population_columns"]]


def new_linear_rows(data):
    for i, equation in enumerate(data["characters"]["product_equations"]):
        yield {"terms": equation["count_terms"] + [[PRODUCT_OFFSET + i, -1]], "rhs": 0}
    for row in data["gram"]["equations"]:
        yield {"terms": [[signed_variable(j), c] for j, c in row["signed_population_terms"]], "rhs": 0}


def build(data):
    model = parent.build(data["parent"])
    assert len(model.proto.variables) == OLD_VARIABLES and len(model.proto.constraints) == OLD_CONSTRAINTS
    for i, (lower, upper) in enumerate(data["bounds"][OLD_VARIABLES:], OLD_VARIABLES):
        name = f"L{i-SIGNED_OFFSET}" if i < PRODUCT_OFFSET else f"C{i-PRODUCT_OFFSET}"
        variable = model.new_int_var(lower, upper, name)
        assert variable.index == i
    variables = [model.get_int_var_from_proto_index(i) for i in range(VARIABLES)]
    for row in new_linear_rows(data):
        model.add(cp_model.LinearExpr.weighted_sum([variables[j] for j, c in row["terms"]],
                                                   [c for j, c in row["terms"]]) == 0)
    for i, equation in enumerate(data["characters"]["product_equations"]):
        factors = [variables[signed_variable(j)] for j in equation["signed_population_factors"]]
        model.add_multiplication_equality(variables[PRODUCT_OFFSET + i], factors)
    for table in data["characters"]["local_tables"]:
        model.add_allowed_assignments([variables[j] for j in table_columns(table)],
                                      [p["counts_and_signed_populations"] for p in table["profiles"]])
    assert len(model.proto.variables) == VARIABLES and len(model.proto.constraints) == CONSTRAINTS
    validation = model.validate()
    assert validation == "", validation
    return model


def check_proto(proto, data):
    assert {f.name for f, value in proto.ListFields()} == {"variables", "constraints"}
    assert len(proto.variables) == VARIABLES and len(proto.constraints) == CONSTRAINTS
    archive = (LOGS / "f0-population-profile-cpsat01/model.pb.gz").read_bytes()
    assert sha(archive) == PARENT_ARCHIVE_SHA
    raw = gzip.decompress(archive)
    assert sha(raw) == PARENT_PROTO_SHA
    frozen = cp_model_pb2.CpModelProto()
    frozen.ParseFromString(raw)
    prefix = cp_model_pb2.CpModelProto()
    prefix.variables.extend(proto.variables[:OLD_VARIABLES])
    prefix.constraints.extend(proto.constraints[:OLD_CONSTRAINTS])
    assert prefix == frozen
    parent_checked = parent.check_proto(prefix, data["parent"])
    for i in range(OLD_VARIABLES, VARIABLES):
        variable = proto.variables[i]
        assert list(variable.domain) == data["bounds"][i]
        assert variable.name == (f"L{i-SIGNED_OFFSET}" if i < PRODUCT_OFFSET else f"C{i-PRODUCT_OFFSET}")
    terms, largest = 0, 0
    rows = list(new_linear_rows(data))
    assert len(rows) == 2417
    for offset, row in enumerate(rows):
        constraint = proto.constraints[OLD_CONSTRAINTS + offset]
        assert {f.name for f, value in constraint.ListFields()} == {"linear"}
        native = constraint.linear
        actual = sorted(zip(native.vars, native.coeffs))
        assert actual == [tuple(t) for t in row["terms"]] and len(set(native.vars)) == len(native.vars)
        assert list(native.domain) == [0, 0]
        absolute_sum = sum(abs(c) * max(abs(v) for v in data["bounds"][j]) for j, c in actual)
        assert absolute_sum < (1 << 62)
        largest = max(largest, absolute_sum)
        terms += len(actual)
    product_start = OLD_CONSTRAINTS + len(rows)
    for i, equation in enumerate(data["characters"]["product_equations"]):
        constraint = proto.constraints[product_start + i]
        assert {f.name for f, value in constraint.ListFields()} == {"int_prod"}
        native = constraint.int_prod
        assert list(native.target.vars) == [PRODUCT_OFFSET + i]
        assert list(native.target.coeffs) == [1] and native.target.offset == 0
        assert len(native.exprs) == 2
        for expression, j in zip(native.exprs, equation["signed_population_factors"]):
            assert list(expression.vars) == [signed_variable(j)]
            assert list(expression.coeffs) == [1] and expression.offset == 0
        assert max(abs(v) for v in data["bounds"][PRODUCT_OFFSET + i]) <= 36
    table_start = product_start + PRODUCT_COUNT
    table_entries = 0
    for i, table in enumerate(data["characters"]["local_tables"]):
        table_entries += parent.check_table(proto.constraints[table_start + i], table_columns(table),
                                           [p["counts_and_signed_populations"] for p in table["profiles"]])
    assert table_start + 42 == CONSTRAINTS
    return {"parent_checks": parent_checked, "all15941_parent_variables_and29592_constraints_unchanged": True,
            "signed_variables_checked": 118, "new_product_auxiliaries_checked": 2385,
            "new_linear_rows_checked": 2417, "new_linear_terms": terms,
            "maximum_new_linear_absolute_box_sum": largest, "maximum_new_absolute_product": 36,
            "new_product_constraints_checked": 2385, "new_joint_tables_checked": 42,
            "new_joint_tuples_checked": 19331, "new_joint_integer_entries": table_entries,
            "variables": VARIABLES, "constraints": CONSTRAINTS,
            "all_int64_ranges_checked": True, "objective_hints_assumptions_or_strategy_added": False}


def inspect(point, data):
    assert len(point) == VARIABLES and all(type(v) is int for v in point)
    assert all(lower <= v <= upper for v, (lower, upper) in zip(point, data["bounds"]))
    checked = parent.inspect(point[:OLD_VARIABLES], data["parent"])
    for i, equation in enumerate(data["characters"]["product_equations"]):
        a, b = [signed_variable(j) for j in equation["signed_population_factors"]]
        product = point[a] * point[b]
        assert point[PRODUCT_OFFSET + i] == product
        assert sum(c * point[j] for j, c in equation["count_terms"]) == product
    for row in data["gram"]["equations"]:
        assert sum(c * point[signed_variable(j)] for j, c in row["signed_population_terms"]) == 0
    for table in data["characters"]["local_tables"]:
        actual = tuple(point[j] for j in table_columns(table))
        assert actual in {tuple(p["counts_and_signed_populations"]) for p in table["profiles"]}
    return {"status": "PASS: exact signed-character count witness only", "parent_check": checked,
            "all18444_integer_domains_checked": True, "additional_products_and_links_checked": 2385,
            "additional_character_Gram_rows_checked": 32, "joint_profile_tables_checked": 42,
            "literal_incidence_or_graph_claimed": False, "full_PSD_claimed": False}


def evaluate_proto(proto, values):
    assert len(values) == len(proto.variables)
    for variable, value in zip(proto.variables, values):
        domain = list(variable.domain)
        if not any(a <= value <= b for a, b in zip(domain[::2], domain[1::2])):
            return False
    def expression(expr):
        return expr.offset + sum(c * values[j] for j, c in zip(expr.vars, expr.coeffs))
    for constraint in proto.constraints:
        kind = constraint.WhichOneof("constraint")
        if kind == "linear":
            row = constraint.linear
            value = sum(c * values[j] for j, c in zip(row.vars, row.coeffs))
            if not any(a <= value <= b for a, b in zip(row.domain[::2], row.domain[1::2])):
                return False
        elif kind == "int_prod":
            item = constraint.int_prod
            assert len(item.exprs) == 2
            if expression(item.target) != expression(item.exprs[0]) * expression(item.exprs[1]):
                return False
        else:
            assert kind == "table" and not constraint.table.negated and not constraint.table.vars
            table = constraint.table
            actual = tuple(expression(e) for e in table.exprs)
            width = len(actual)
            allowed = {tuple(table.values[i:i + width]) for i in range(0, len(table.values), width)}
            if actual not in allowed:
                return False
    return True


def controls(directory):
    checked = 0
    for diagonal in (False, True):
        model = cp_model.CpModel()
        a = model.new_int_var(-2, 2, "a")
        b = model.new_int_var(-2, 2, "b")
        target = model.new_int_var(0 if diagonal else -4, 4, "t")
        model.add_multiplication_equality(target, [a, a if diagonal else b])
        assert model.validate() == ""
        path = directory / ("signed-diagonal.pb" if diagonal else "signed-cross.pb")
        assert model.export_to_file(str(path))
        proto = cp_model_pb2.CpModelProto()
        proto.ParseFromString(path.read_bytes())
        for av, bv, tv in itertools.product(range(-2, 3), range(-2, 3), range(-4, 5)):
            assert evaluate_proto(proto, [av, bv, tv]) == (tv == av * (av if diagonal else bv))
            checked += 1
    model = cp_model.CpModel()
    n, l, pair, square = [model.new_int_var(a, b, name) for a, b, name in
                          [(0, 2, "N"), (-1, 1, "L"), (0, 1, "P"), (0, 1, "C")]]
    allowed = [[0, 0, 0], [1, -1, 0], [1, 1, 0], [2, 0, 1]]
    model.add_allowed_assignments([n, l, pair], allowed)
    model.add_multiplication_equality(square, [l, l])
    model.add(n - 2 * pair == square)
    assert model.validate() == ""
    path = directory / "signed-local-table.pb"
    assert model.export_to_file(str(path))
    proto = cp_model_pb2.CpModelProto()
    proto.ParseFromString(path.read_bytes())
    table_checks = 0
    for nv, lv, pv, cv in itertools.product(range(3), range(-1, 2), range(2), range(2)):
        wanted = [nv, lv, pv] in allowed and cv == lv * lv and nv - 2 * pv == cv
        assert evaluate_proto(proto, [nv, lv, pv, cv]) == wanted
        table_checks += 1
    return {"signed_product_proto_assignments": checked, "joint_table_square_proto_assignments": table_checks,
            "negative_factors_and_negative_products_checked": True, "optimizer_calls": 0}


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
        control = controls(directory)
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
        control = {"repeated": False}
    proto = cp_model_pb2.CpModelProto()
    proto.ParseFromString(raw)
    checked = check_proto(proto, data)
    report = {"status": "PASS: complete signed-character native overlay " + args.mode,
              "source_sha256": sha(Path(__file__).read_bytes()), "parent_source_sha256": PARENT_SHA,
              "inputs": {k: {"path": str((LOGS / p).relative_to(ROOT)), "sha256": h} for k, (p, h) in INPUTS.items()},
              "parent_proto_sha256": PARENT_PROTO_SHA, "raw_proto_sha256": sha(raw), "raw_proto_bytes": len(raw),
              "archive": {"path": str(archive.relative_to(ROOT)), "sha256": sha(archive.read_bytes()), "bytes": archive.stat().st_size},
              "namespaces": {"original_counts": [0, 15038], "trivial_products": [15038, 15941],
                             "signed_populations": [15941, 16059], "signed_products": [16059, 18444]},
              "checks": checked, "controls": control, "ortools_version": parent.parent.ortools.__version__,
              "all92_old_PSD_directions_preserved": True, "all25_integer_refinements_preserved": True,
              "character_Gram_independent_strength_claimed": False,
              "optimizer_calls": 0, "CpSolver_constructed": False,
              "count_or_graph_feasibility_claimed": False, "seconds": time.monotonic() - started}
    save(directory / "report.json", report)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
