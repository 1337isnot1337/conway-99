"""Build and independently read the exact F0 count/product CP-SAT proto.

This program has no solve mode and never constructs a CpSolver. The native
validator and small literal proto controls do not run a search.
"""
import argparse
import gzip
import hashlib
import inspect
import json
from pathlib import Path
import time

import ortools
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

import root_prism_free_f0_population_products as mathematics

ROOT = Path(__file__).resolve().parents[2]
MATH_SHA = "147ad92071ced273139993b09633c298b7a4a8ed9298e68103f970a8f01b7a66"
SPEC_SHA = "c83ebbc1d0d4e9b5ec5ccd60ed5e52ea2be2cb24f1de570f6bff8bb158d42e0c"
ORTOOLS_VERSION = "9.15.6755"


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save_new(path, value):
    with path.open("x") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def bindings(specification):
    assert sha(Path(mathematics.__file__).read_bytes()) == MATH_SHA
    assert ortools.__version__ == ORTOOLS_VERSION
    raw = specification.read_bytes()
    assert sha(raw) == SPEC_SHA
    spec = json.loads(gzip.decompress(raw))
    assert spec["source_sha256"] == MATH_SHA
    assert spec["scope"]["all42_selector_populations_free"]
    assert not spec["scope"]["selector_orbit_subset_tables_imposed"]
    linear = mathematics.read("linear")
    assert spec["parent_count_matrix_sha256"] == linear["matrix_sha256"]
    return spec, linear


def rows(spec, linear):
    for row in linear["matrix"]["equalities"]:
        yield True, row
    for row in linear["matrix"]["inequalities"]:
        yield False, row
    for row in spec["selector_integer_refinement_rows"]:
        yield False, row
    for row in spec["product_link_equalities"]:
        yield True, row


def native_row_domain(equality, row, upper):
    if equality:
        return [row["rhs"], row["rhs"]]
    # The additional finite lower endpoint follows from variable boxes.
    lower = sum(c * upper[j] for j, c in row["terms"] if c < 0)
    assert lower <= row["rhs"]
    return [lower, row["rhs"]]


def build_proto(spec, linear):
    model = cp_model.CpModel()
    upper = spec["upper_by_variable"]
    variables = [model.new_int_var(0, u, f"N{j}" if j < 15038 else f"T{j-15038}")
                 for j, u in enumerate(upper)]
    assert len(variables) == 15941
    for equality, row in rows(spec, linear):
        expression = cp_model.LinearExpr.weighted_sum(
            [variables[j] for j, c in row["terms"]], [c for j, c in row["terms"]])
        lower, high = native_row_domain(equality, row, upper)
        model.add_linear_constraint(expression, lower, high)
    for block in spec["blocks"]:
        i, j = block["product_factors"]
        model.add_multiplication_equality(variables[block["product_variable"]],
                                          [variables[i], variables[j]])
    assert len(model.proto.constraints) == spec["native_constraints"] == 29550
    validation = model.validate()
    assert validation == "", validation
    return model


def literal_proto_check(proto, spec, linear):
    assert {field.name for field, value in proto.ListFields()} == {"variables", "constraints"}
    assert len(proto.variables) == 15941 and len(proto.constraints) == 29550
    upper = spec["upper_by_variable"]
    for j, variable in enumerate(proto.variables):
        assert list(variable.domain) == [0, upper[j]]
        assert variable.name == (f"N{j}" if j < 15038 else f"T{j-15038}")
    largest_sum, terms = 0, 0
    for index, (equality, row) in enumerate(rows(spec, linear)):
        constraint = proto.constraints[index]
        assert {field.name for field, value in constraint.ListFields()} == {"linear"}
        native = constraint.linear
        actual = sorted(zip(native.vars, native.coeffs))
        assert actual == [tuple(t) for t in row["terms"]]
        assert len(set(native.vars)) == len(native.vars)
        assert list(native.domain) == native_row_domain(equality, row, upper)
        absolute_sum = sum(abs(int(c)) * upper[j] for j, c in actual)
        assert max(absolute_sum, *(abs(int(v)) for v in native.domain)) < (1 << 62)
        largest_sum = max(largest_sum, absolute_sum)
        terms += len(actual)
    offset = spec["linear_rows_including_links"]
    assert offset == 28647
    for index, block in enumerate(spec["blocks"]):
        constraint = proto.constraints[offset + index]
        assert {field.name for field, value in constraint.ListFields()} == {"int_prod"}
        product = constraint.int_prod
        assert list(product.target.vars) == [block["product_variable"]]
        assert list(product.target.coeffs) == [1] and product.target.offset == 0
        assert len(product.exprs) == 2
        for expression, variable in zip(product.exprs, block["product_factors"]):
            assert list(expression.vars) == [variable]
            assert list(expression.coeffs) == [1] and expression.offset == 0
        i, j = block["product_factors"]
        assert upper[i] * upper[j] == upper[block["product_variable"]] <= 144
    assert terms == spec["linear_nonzeros"]
    assert largest_sum == spec["maximum_linear_absolute_box_sum"]
    return {"all15941_integer_variable_domains_checked": True,
            "all28647_linear_rows_checked": True, "all903_product_constraints_checked": True,
            "linear_nonzeros_checked": terms, "maximum_absolute_linear_box_sum": largest_sum,
            "maximum_product_upper": 144, "all_proto_int64_ranges_checked": True,
            "objective_hints_assumptions_enforcement_literals_or_search_strategy_present": False}


def evaluate_toy(proto, point):
    if any(not v.domain[0] <= x <= v.domain[-1] for v, x in zip(proto.variables, point)):
        return False
    for constraint in proto.constraints:
        kind = constraint.WhichOneof("constraint")
        if kind == "linear":
            row = constraint.linear
            value = sum(int(c) * point[j] for j, c in zip(row.vars, row.coeffs))
            if not row.domain[0] <= value <= row.domain[-1]:
                return False
        else:
            assert kind == "int_prod"
            def value(expression):
                return expression.offset + sum(int(c) * point[j] for j, c in zip(expression.vars, expression.coeffs))
            product = constraint.int_prod
            if value(product.target) != value(product.exprs[0]) * value(product.exprs[1]):
                return False
    return True


def controls(directory):
    checked = 0
    for diagonal in (False, True):
        model = cp_model.CpModel()
        a = model.new_int_var(0, 3, "a")
        b = model.new_int_var(0, 3, "b")
        target = model.new_int_var(0, 9, "t")
        count = model.new_int_var(0, 9, "p")
        model.add_multiplication_equality(target, [a, a if diagonal else b])
        model.add(2 * count == target - a) if diagonal else model.add(count == target)
        assert model.validate() == ""
        path = directory / ("toy-diagonal.pb" if diagonal else "toy-cross.pb")
        assert not path.exists() and model.export_to_file(str(path))
        proto = cp_model_pb2.CpModelProto()
        proto.ParseFromString(path.read_bytes())
        for av in range(4):
            for bv in range(4):
                for tv in range(10):
                    for pv in range(10):
                        wanted = (tv == av * av and pv == av * (av - 1) // 2) if diagonal else (tv == av * bv and pv == tv)
                        assert evaluate_toy(proto, [av, bv, tv, pv]) == wanted
                        checked += 1
    return {"serialized_native_proto_truth_assignments": checked, "optimizer_calls": 0,
            "native_model_validator_called_without_search": True}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--specification", type=Path, required=True)
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--proto", type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    directory = args.directory.resolve()
    directory.mkdir(parents=True, exist_ok=False)
    spec, linear = bindings(args.specification)
    if args.mode == "prepare":
        control = controls(directory)
        model = build_proto(spec, linear)
        path = directory / "model.pb"
        assert not path.exists() and model.export_to_file(str(path))
        del model
    else:
        assert args.proto is not None
        path = args.proto.resolve()
        control = {"repeated": False}
    proto = cp_model_pb2.CpModelProto()
    raw = path.read_bytes()
    proto.ParseFromString(raw)
    checked = literal_proto_check(proto, spec, linear)
    record = {"status": "PASS: literal native count/product proto " + args.mode,
              "source_sha256": sha(Path(__file__).read_bytes()), "mathematical_source_sha256": MATH_SHA,
              "specification": {"path": str(args.specification.resolve().relative_to(ROOT)), "sha256": SPEC_SHA},
              "proto": {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)},
              "ortools_version": ortools.__version__,
              "installed_cp_model_source_sha256": sha(Path(inspect.getfile(cp_model)).read_bytes()),
              "controls": control, "checks": checked, "seconds": time.monotonic() - started,
              "optimizer_calls": 0, "CpSolver_constructed": False,
              "count_or_graph_feasibility_claimed": False,
              "scope": "All count variables free; 903 deterministic products and 25 integer refinements. Root selector-profile tables are a separate later overlay."}
    save_new(directory / "report.json", record)
    print(json.dumps(record, indent=2))


if __name__ == "__main__":
    main()
