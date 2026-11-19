"""Small native-row model and exact box-corrected upper bounds.

For l<=A*x<=h and 0<=x<=1, every rational row multiplier u gives
c*x <= sum_i u_i*(h_i if u_i>=0 else l_i)
       +sum_j max(c_j-(A^T*u)_j,0).
This identity does not assume numerical dual feasibility. The first72
objectives cover the two proved unit parity sums; all singletons follow.
Coordinate covers are deliberately outside this necessary relaxation.
"""
import argparse
from collections import Counter
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import time

import rook_case4_complete_lp_recovery as recovery
import rook_case4_face111_two_parity_equalities as equalities

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
RECOVERY_SHA = "e577327c9cc2471f119c755a49a179b9f94f1004a22de80152a4114787a7eec6"
EQUALITIES_SHA = "195b5fc78cb6895ee7797ebf1926f1cd19d990d992d5a9e9638d44f24aa984c6"
INPUTS = {
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "equalities": (BASE+"rook-case4-face111-two-parity-equalities-certificate.json", "6272996ff8c38af719b057dea6f6796efb895fdb678c69b82cc3eaff757ec606"),
}
QUANTA = (1, 2, 4, 8, 16, 64, 256, 1024, 65536, 1048576)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def bound(rows, variables, objective, multipliers, denominator):
    assert objective == sorted(set(objective)) and all(0 <= j < variables for j in objective)
    assert len(multipliers) == len(rows)
    assert type(denominator) is int and denominator > 0
    assert all(type(v) is int for v in multipliers)
    residual = [0]*variables
    for j in objective:
        residual[j] = denominator
    constant = 0
    for coefficient, row in zip(multipliers, rows):
        constant += coefficient*(row["upper"] if coefficient >= 0 else row["lower"])
        for j, value in row["terms"]:
            residual[j] -= coefficient*value
    return constant+sum(max(v, 0) for v in residual), constant, residual


def certificate(model, objective_id, multipliers, denominator):
    divisor = math.gcd(denominator, *(abs(v) for v in multipliers))
    multipliers = [v//divisor for v in multipliers]; denominator //= divisor
    objective = model["objectives"][objective_id]
    upper, constant, residual = bound(model["rows"], model["variables"], objective["reduced_columns"], multipliers, denominator)
    assert upper < denominator*objective["required_value"]
    return {
        "kind": "NATIVE_BOX_CONTRADICTION" if upper < 0 else "BOOLEAN_COORDINATE_ZERO" if objective["required_value"] == 1 else "FORBIDDEN_BOOLEAN_PAIR",
        "objective_id": objective_id, "objective_original_columns": objective["original_columns"],
        "required_value": objective["required_value"], "denominator": str(denominator), "upper_numerator": str(upper),
        "row_bound_constant_numerator": str(constant),
        "row_multipliers": [[i, str(v)] for i, v in enumerate(multipliers) if v],
        "positive_unit_box_correction": [[j, str(v)] for j, v in enumerate(residual) if v > 0],
        "full_residual_sha256": sha(canonical(residual)),
        "all1103_unit_box_coordinates_checked": True,
        "numerical_dual_feasibility_assumed": False,
    }


def verify(model, proof):
    multipliers = [0]*len(model["rows"]); seen = set()
    for i, value in proof["row_multipliers"]:
        assert type(i) is int and 0 <= i < len(multipliers) and i not in seen
        seen.add(i); multipliers[i] = int(value)
    assert certificate(model, proof["objective_id"], multipliers, int(proof["denominator"])) == proof
    return proof["kind"]


def controls():
    checks = 0
    terms = ([[0, 1], [1, -2]], [[1, 1], [2, 1]])
    for vertex in product((0, 1), repeat=3):
        for padding in (0, 1):
            rows = []
            for support in terms:
                value = sum(c*vertex[j] for j, c in support)
                rows.append({"terms": support, "lower": value-padding, "upper": value+padding})
            for multipliers in product(range(-2, 3), repeat=2):
                for denominator in (1, 2):
                    for objective in ([0], [1], [2], [0, 2]):
                        upper, constant, residual = bound(rows, 3, objective, list(multipliers), denominator)
                        assert denominator*sum(vertex[j] for j in objective) <= upper
                        checks += 1
    assert bound([{"terms": [[0, 2], [1, 1]], "lower": 1, "upper": 1}], 2, [0], [1], 2) == (1, 1, [0, -1])
    assert bound([{"terms": [], "lower": 1, "upper": 1}], 2, [0], [-2], 1)[0] == -1
    return {"exact_signed_interval_box_controls": checks, "fractional_half_bound": True,
            "contradiction_control": True, "numerical_dual_feasibility_assumed": False}


def build():
    assert sha(Path(recovery.__file__).read_bytes()) == RECOVERY_SHA
    assert sha(Path(equalities.__file__).read_bytes()) == EQUALITIES_SHA
    data = {}
    for name, (path, expected) in INPUTS.items():
        raw = (ROOT/path).read_bytes(); assert sha(raw) == expected
        data[name] = json.loads(raw)
    proof = equalities.prove(ROOT)
    assert canonical(proof) == canonical(data["equalities"])
    inv = data["native"]["primary_inventory"]
    assert sha(canonical(inv)) == data["native"]["primary_inventory_sha256"]
    zeros = proof["proved_zero_columns"]
    kept = [a for a in range(1214) if a not in set(zeros)]
    assert len(zeros) == 111 and len(kept) == 1103
    position = {a: j for j, a in enumerate(kept)}
    original = recovery.original_rows(inv)
    rows, omitted = [], []
    for i, row in enumerate(original):
        terms, minimum, maximum, redundant = recovery.projected(row["terms"], row["lower"], row["upper"], position)
        if redundant:
            omitted.append({"original_native_row": i, "box_minimum": minimum, "box_maximum": maximum,
                            "lower": row["lower"], "upper": row["upper"]})
        else:
            rows.append({"original_native_row": i, "family": row["family"], "terms": terms,
                         "lower": row["lower"], "upper": row["upper"]})
    assert len(rows) == 1961 and len(omitted) == 310
    assert sum(len(row["terms"]) for row in rows) == 25689
    H1, H2 = map(set, proof["live_cover_supports"])
    for k, support in enumerate((H1, H2)):
        rows.append({"original_native_row": None, "family": "proved_parity_equality", "equality_id": k,
                     "terms": [[position[a], 1] for a in sorted(support)], "lower": 1, "upper": 1})
    common, A, B = sorted(H1&H2), sorted(H1-H2), sorted(H2-H1)
    assert (len(common), len(A), len(B)) == (32, 4, 10)
    patterns = [[a] for a in common]+[sorted([a, b]) for a in A for b in B]
    assert len(patterns) == 72 and len(set(map(tuple, patterns))) == 72
    objectives = []
    for columns in patterns+[[a] for a in kept if a not in set(common)]:
        objectives.append({"original_columns": columns, "reduced_columns": sorted(position[a] for a in columns),
                           "required_value": len(columns), "partition_member": len(objectives) < 72})
    assert len(objectives) == 1143
    return {
        "schema": "rook-case4-face111-native-box-bounds-v1", "source_sha256": sha(Path(__file__).read_bytes()),
        "source_dependencies": {"native_recovery": RECOVERY_SHA, "two_parity_equalities": EQUALITIES_SHA},
        "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
        "variables": len(kept), "kept_original_columns": kept, "proved_zero_original_columns": zeros,
        "rows": rows, "row_count": len(rows), "nonzeros": sum(len(row["terms"]) for row in rows),
        "all2271_original_native_rows_accounted_for": True, "omitted_native_box_tautologies": omitted,
        "lower": 0, "upper": 1, "objectives": objectives, "objective_count": len(objectives),
        "partition": {"common": common, "positive_difference_A": A, "negative_difference_B": B,
                      "patterns": patterns, "complete_Boolean_cover": True,
                      "proof": "Both support sums are one. Either the common support has its unique one, or it is zero and each disjoint part has exactly one."},
        "coordinate_covers_added": False, "conditional_positive_selector_assumptions": 0,
        "scope": "All original native rows,111 proved zeros,two proved integer equalities,and Boolean unit boxes. Every actual case4 solution satisfies this weaker model.",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--model", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--replay", action="store_true")
    args = parser.parse_args(); started = time.monotonic()
    assert not args.output.exists()
    model, tests = build(), controls()
    if args.replay:
        assert model == json.loads(args.model.read_bytes())
    else:
        assert not args.model.exists(); args.model.write_text(json.dumps(model, indent=2)+"\n")
    report = {k: v for k, v in model.items() if k not in ("rows", "objectives", "omitted_native_box_tautologies", "kept_original_columns", "proved_zero_original_columns", "partition")}
    report.update(status="PASS: exact native-box model and72-pattern Boolean partition prepared", model_sha256=sha(args.model.read_bytes()),
                  controls=tests, partition_patterns=72, optimizer_calls=0, replay=args.replay, seconds=time.monotonic()-started)
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2), flush=True)


if __name__ == "__main__":
    main()
