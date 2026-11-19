"""Small equality/box model and exact coordinate upper-bound certificates.

For A*x=b, 0<=x<=1 and any rational multiplier u, one has
x_t <= u*b + sum_j max(e_t[j]-(A^T*u)[j],0).
No numerical dual-feasibility claim is required. A bound below one forces
a Boolean coordinate to zero. A negative bound contradicts the unit box.
"""
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "face": (BASE+"rook-case4-face99-parity-face-certificate.json", "717c3e4103dd56bdd260f52b0f50c5a06f4245b834d92194357481d3163e229e"),
    "face_review": (BASE+"rook-case4-face99-parity-face-independent-review.json", "19edd640590413e125d97791a003d5e405f43b8c936ec631426c6eb404c01634"),
}
QUANTA = (1, 2, 4, 8, 16, 64, 256, 1024, 65536)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def bound(rows, variables, target, multipliers, denominator):
    assert 0 <= target < variables and len(multipliers) == len(rows)
    assert type(denominator) is int and denominator > 0
    assert all(type(x) is int for x in multipliers)
    residual = [0]*variables; residual[target] = denominator
    constant = 0
    for coefficient, row in zip(multipliers, rows):
        constant += coefficient*row["rhs"]
        for j in row["columns"]:
            residual[j] -= coefficient
    correction = sum(max(v, 0) for v in residual)
    return constant+correction, constant, residual


def certificate(model, target, multipliers, denominator):
    divisor = math.gcd(denominator, *(abs(v) for v in multipliers))
    multipliers = [v//divisor for v in multipliers]; denominator //= divisor
    upper, constant, residual = bound(model["rows"], len(model["kept_original_columns"]), target, multipliers, denominator)
    assert upper < denominator
    return {
        "kind": "EQUALITY_BOX_CONTRADICTION" if upper < 0 else "BOOLEAN_COORDINATE_ZERO",
        "target_reduced_column": target, "target_original_column": model["kept_original_columns"][target],
        "denominator": str(denominator), "upper_numerator": str(upper),
        "equality_constant_numerator": str(constant),
        "multipliers": [[i, str(v)] for i, v in enumerate(multipliers) if v],
        "original_Gram_row_multipliers": [[row["original_Gram_row"], str(v)] for row, v in zip(model["rows"], multipliers) if v],
        "positive_unit_box_correction": [[j, str(v)] for j, v in enumerate(residual) if v > 0],
        "full_residual_sha256": sha(canonical(residual)),
        "all_surviving_coordinates_in_bound": True,
        "integrality_needed_for_zero": 0 < upper < denominator,
    }


def verify(model, proof):
    multipliers = [0]*len(model["rows"])
    seen = set()
    for i, value in proof["multipliers"]:
        assert type(i) is int and 0 <= i < len(multipliers) and i not in seen
        seen.add(i); multipliers[i] = int(value)
    assert certificate(model, proof["target_reduced_column"], multipliers, int(proof["denominator"])) == proof
    return proof["kind"]


def controls():
    checks = 0
    templates = ([0, 1], [1, 2])
    for vertex in product((0, 1), repeat=3):
        rows = [{"columns": list(s), "rhs": sum(vertex[j] for j in s)} for s in templates]
        for multipliers in product(range(-2, 3), repeat=2):
            for denominator in (1, 2):
                for target in range(3):
                    upper, constant, residual = bound(rows, 3, target, list(multipliers), denominator)
                    assert denominator*vertex[target] <= upper
                    assert denominator*vertex[target] == constant+sum(r*x for r, x in zip(residual, vertex))
                    checks += 1
    # The repeated column represents coefficient two in this synthetic row.
    # Production Gram rows have distinct columns and coefficient one.
    half = bound([{"columns": [0, 0, 1], "rhs": 1}], 2, 0, [1], 2)
    assert half == (1, 1, [0, -1])
    impossible = bound([{"columns": [], "rhs": 1}], 2, 0, [-1], 1)
    assert impossible[0] == 0
    impossible = bound([{"columns": [], "rhs": 1}], 2, 0, [-2], 1)
    assert impossible[0] == -1
    return {"exact_box_identity_controls": checks, "half_upper_bound_control": True,
            "inconsistent_equality_control": True, "dual_feasibility_assumed": False}


def build():
    data = {}
    for name, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes(); assert sha(raw) == expected
        data[name] = json.loads(raw)
    inventory = data["native"]["primary_inventory"]
    assert inventory["case"]["index"] == 4 and inventory["primary_variables"] == 1214
    gram = inventory["Gram_rows"]
    assert [(i, j) for i, j, rhs, support in gram] == [(i, j) for i in range(35) for j in range(i, 35)]
    face = data["face"]
    zeros = face["all_zero_columns"]
    assert len(zeros) == 111 and zeros == sorted(set(zeros))
    assert len(face["prior_zero_columns"]) == 99 and len(face["new_zero_columns"]) == 12
    # Recheck the short new identity; its older zero premises have their
    # separately bound certificates and independent review.
    expansion = [0]*1214; rhs = 0
    for item in face["original_Gram_combination"]:
        i, j, quota, support = gram[item["original_native_row"]]
        assert [i, j] == item["core_pair"] and quota == item["quota"]
        coefficient = item["multiplier"]; rhs += coefficient*quota
        for a in support:
            expansion[a] += coefficient
    assert expansion == face["full_original_coefficients"] and rhs == 1
    old_zero = set(face["prior_zero_columns"])
    H2, new = set(face["H2_support"]), set(face["new_zero_columns"])
    assert H2.isdisjoint(new)
    assert all(expansion[a] == int(a in H2)+2*int(a in new) for a in range(1214) if a not in old_zero)
    kept = [a for a in range(1214) if a not in set(zeros)]
    assert len(kept) == 1103
    position = {a: j for j, a in enumerate(kept)}
    rows, row_map, lookup = [], [], {}
    for original, (i, j, quota, support) in enumerate(gram):
        assert support == sorted(set(support)) and all(type(a) is int and 0 <= a < 1214 for a in support)
        assert type(quota) is int and quota >= 0
        columns = [position[a] for a in support if a in position]
        if not columns:
            assert quota == 0; row_map.append(-1); continue
        key = tuple(columns)
        if key in lookup:
            k = lookup[key]; assert rows[k]["rhs"] == quota
        else:
            k = len(rows); lookup[key] = k
            rows.append({"columns": columns, "rhs": quota, "original_Gram_row": original})
        row_map.append(k)
    priority = sorted({a for row in face["both_integer_cover_rows"] for a, c in row["terms"] if a in position})
    order_original = priority+[a for a in kept if a not in set(priority)]
    assert len(order_original) == len(set(order_original)) == 1103
    return {
        "schema": "rook-case4-face111-Gram-box-model-v1", "source_sha256": sha(Path(__file__).read_bytes()),
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "kept_original_columns": kept, "proved_zero_original_columns": zeros,
        "rows": rows, "original_Gram_row_to_retained": row_map,
        "original_Gram_rows": 630, "distinct_nonempty_equalities": len(rows),
        "nonzeros": sum(len(r["columns"]) for r in rows), "lower": 0, "upper": 1,
        "objective_original_column_order": order_original,
        "objective_reduced_column_order": [position[a] for a in order_original],
        "priority_rule": "Surviving H1/H2 columns first, then every remaining original column in ascending order.",
        "priority_cover_columns": len(priority),
        "covers_or_other_native_inequalities_added": False,
        "conditional_positive_selector_assumptions": 0,
        "scope": "Only the original Gram equations,111 proved zeros and Boolean unit boxes. A checked upper bound applies to every stronger current case4 model.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args(); started = time.monotonic()
    assert not args.output.exists()
    model = build(); tests = controls()
    if args.replay:
        assert model == json.loads(args.model.read_bytes())
    else:
        assert not args.model.exists(); args.model.write_text(json.dumps(model, indent=2)+"\n")
    report = {k: v for k, v in model.items() if k not in ("rows", "original_Gram_row_to_retained", "objective_original_column_order", "objective_reduced_column_order", "kept_original_columns", "proved_zero_original_columns")}
    report.update(status="PASS: small Gram/box domain and exact bound identity prepared", model_sha256=sha(args.model.read_bytes()),
                  controls=tests, optimizer_calls=0, coordinate_queries=0, replay=args.replay, seconds=time.monotonic()-started)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
