"""Independent integer replay of five saved native-row bounds and the 663 identity.

This file imports no subject source or optimizer.  The already proved 111 zeros
and H1=H2=1 are bound premises.  Every retained/omitted native row and every
coefficient of each box bound is reconstructed from the original inventory.
"""
import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "native": (BASE + "complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "equalities": (BASE + "rook-case4-face111-two-parity-equalities-certificate.json", "6272996ff8c38af719b057dea6f6796efb895fdb678c69b82cc3eaff757ec606"),
    "model": (BASE + "rook-case4-face111-native-bounds-model01.json", "a174fde38a359f61498a0d9508beb2364ec9209f2771e9a7529a3675774008ad"),
    "certificates": (BASE + "rook-case4-face111-native-bounds-run01/certificates.jsonl", "92bd55e4987b18a17359a3d9344a58f599314cb524d5c44f881fecb5c4f4ce93"),
    "refined663": (BASE + "rook-case4-face111-native-bounds-663-denominator6.json", "4a808f495cc1e24a55e8979873fda659a6d82af48f521ffabb2c0873c067d30b"),
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def packed(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def integer(value):
    assert isinstance(value, str)
    result = int(value)
    assert str(result) == value
    return result


def original_rows(inv):
    rows = []

    def put(family, members, lower, upper):
        coefficients = Counter()
        for column, coefficient in members:
            assert type(column) is type(coefficient) is int and 0 <= column < 1214
            coefficients[column] += coefficient
        rows.append({"family": family, "terms": [[a, c] for a, c in sorted(coefficients.items()) if c],
                     "lower": lower, "upper": upper})

    assert [(i, j) for i, j, _, _ in inv["Gram_rows"]] == [(i, j) for i in range(35) for j in range(i, 35)]
    for _, _, quota, members in inv["Gram_rows"]:
        put("Gram", [(a, 1) for a in members], quota, quota)
    for _, members in inv["original_signature_rows"]:
        put("original_signature", [(a, 1) for a in members], 0, 1)
    for item in inv["triple_rows"]:
        put("core_triple", [(a, 1) for a in item["members"]], 0, 1)
    for clause in inv["Gram_conflict_clauses"]:
        assert len(clause) == 2 and all(type(v) is int and v < 0 for v in clause)
        put("Gram_conflict", [(-v - 1, 1) for v in clause], 0, 1)
    for cut in inv["uncapped_integer_cuts"]:
        demand = cut["positive_demand"]
        assert type(demand) is int and demand > 0
        assert all(type(w) is int and w > 0 for _, w in cut["positive_terms"])
        put("uncapped_row_cut", cut["positive_terms"] + [[cut["target_column"], -demand]],
            0, sum(w for _, w in cut["positive_terms"]))
    assert Counter(r["family"] for r in rows) == {
        "Gram": 630, "original_signature": 186, "core_triple": 1365,
        "Gram_conflict": 30, "uncapped_row_cut": 60}
    return rows


def reconstruct(native, equality, model):
    inv = native["primary_inventory"]
    assert digest(packed(inv)) == native["primary_inventory_sha256"]
    zeros = equality["proved_zero_columns"]
    assert zeros == sorted(set(zeros)) and len(zeros) == 111
    assert equality["new_integer_cover_ranges"] == [[1, 1], [1, 1]]
    kept = [a for a in range(1214) if a not in set(zeros)]
    assert kept == model["kept_original_columns"] and zeros == model["proved_zero_original_columns"]
    index = {a: j for j, a in enumerate(kept)}
    original = original_rows(inv)
    rows, omitted = [], []
    for row_id, row in enumerate(original):
        support = [[index[a], c] for a, c in row["terms"] if a in index]
        minimum = sum(c for _, c in support if c < 0)
        maximum = sum(c for _, c in support if c > 0)
        lower, upper = row["lower"], row["upper"]
        assert lower <= maximum and minimum <= upper
        if lower <= minimum and maximum <= upper:
            omitted.append({"original_native_row": row_id, "box_minimum": minimum,
                            "box_maximum": maximum, "lower": lower, "upper": upper})
        else:
            rows.append({"original_native_row": row_id, "family": row["family"],
                         "terms": support, "lower": lower, "upper": upper})
    assert len(rows) == 1961 and len(omitted) == 310
    assert sum(len(r["terms"]) for r in rows) == 25689
    supports = equality["live_cover_supports"]
    assert supports == [[a for a in H if a in index] for H in equality["original_cover_supports"]]
    for k, support in enumerate(supports):
        assert support == sorted(set(support))
        rows.append({"original_native_row": None, "family": "proved_parity_equality", "equality_id": k,
                     "terms": [[index[a], 1] for a in support], "lower": 1, "upper": 1})
    assert rows == model["rows"] and omitted == model["omitted_native_box_tautologies"]
    assert len(rows) == model["row_count"] == 1963
    assert sum(len(r["terms"]) for r in rows) == model["nonzeros"] == 25767
    H1, H2 = map(set, supports)
    common, left, right = sorted(H1 & H2), sorted(H1 - H2), sorted(H2 - H1)
    assert (len(common), len(left), len(right)) == (32, 4, 10)
    patterns = [[a] for a in common] + [sorted([a, b]) for a in left for b in right]
    assert patterns == model["partition"]["patterns"]
    objectives = []
    for columns in patterns + [[a] for a in kept if a not in set(common)]:
        objectives.append({"original_columns": columns, "reduced_columns": sorted(index[a] for a in columns),
                           "required_value": len(columns), "partition_member": len(objectives) < 72})
    assert objectives == model["objectives"] and len(objectives) == 1143
    return original, rows, kept, index


def check_bound(proof, rows, kept, index, model):
    objective = model["objectives"][proof["objective_id"]]
    assert objective["original_columns"] == proof["objective_original_columns"]
    assert objective["required_value"] == proof["required_value"]
    denominator = integer(proof["denominator"])
    assert denominator > 0
    multipliers = [0] * len(rows)
    row_ids = []
    for i, encoded in proof["row_multipliers"]:
        assert type(i) is int and 0 <= i < len(rows) and i not in row_ids
        row_ids.append(i)
        multipliers[i] = integer(encoded)
        assert multipliers[i] != 0
    assert row_ids == sorted(row_ids)
    assert math.gcd(denominator, *multipliers) == 1
    objective_set = set(objective["reduced_columns"])
    weighted_columns = [0] * len(kept)
    constant = 0
    for multiplier, row in zip(multipliers, rows):
        constant += multiplier * (row["upper"] if multiplier >= 0 else row["lower"])
        for j, coefficient in row["terms"]:
            weighted_columns[j] += multiplier * coefficient
    residual = [denominator * (j in objective_set) - v for j, v in enumerate(weighted_columns)]
    correction = [[j, str(v)] for j, v in enumerate(residual) if v > 0]
    upper = constant + sum(max(v, 0) for v in residual)
    assert correction == proof["positive_unit_box_correction"]
    assert digest(packed(residual)) == proof["full_residual_sha256"]
    assert constant == integer(proof["row_bound_constant_numerator"])
    assert upper == integer(proof["upper_numerator"])
    assert 0 <= upper < denominator * objective["required_value"]
    expected_kind = "BOOLEAN_COORDINATE_ZERO" if len(objective_set) == 1 else "FORBIDDEN_BOOLEAN_PAIR"
    assert proof["kind"] == expected_kind
    assert proof["all1103_unit_box_coordinates_checked"] is True
    assert proof["numerical_dual_feasibility_assumed"] is False
    direct_rows = []
    if len(objective_set) == 2:
        for i, row in enumerate(rows):
            coefficients = dict(row["terms"])
            if row["upper"] == 1 and all(c > 0 for c in coefficients.values()) and all(coefficients.get(j, 0) >= 1 for j in objective_set):
                direct_rows.append({"reduced_row": i, "original_native_row": row["original_native_row"], "family": row["family"]})
    summary = {"objective_id": proof["objective_id"], "original_columns": objective["original_columns"],
               "required_value": objective["required_value"], "upper_bound": str(Fraction(upper, denominator)),
               "upper_numerator": upper, "denominator": denominator,
               "constant_numerator": constant, "positive_box_correction_numerator": upper - constant,
               "row_multiplier_count": len(row_ids), "all_original_survivor_coordinates_checked": len(residual),
               "residual_histogram": dict(sorted(Counter(residual).items())),
               "existing_direct_capacity_witnesses": direct_rows,
               "Boolean_consequence": "zero" if len(objective_set) == 1 else "pair_sum_at_most_one"}
    return summary, multipliers, residual


def short_identity(original, rows, equality, kept, multipliers, residual):
    assert set(residual) == {-2, 0}
    assert residual[kept.index(663)] == 0
    full = [0] * 1214
    rhs = 0
    combination = []
    for row_id, multiplier in enumerate(multipliers):
        if not multiplier:
            continue
        row = rows[row_id]
        assert row["lower"] == row["upper"]
        rhs += multiplier * row["lower"]
        if row["original_native_row"] is not None:
            old_id = row["original_native_row"]
            assert old_id < 630 and row["family"] == "Gram"
            terms = original[old_id]["terms"]
            combination.append(["Gram", old_id, multiplier])
        else:
            assert row["equality_id"] == 0
            terms = [[a, 1] for a in equality["original_cover_supports"][0]]
            combination.append(["H1", 0, multiplier])
        for a, c in terms:
            full[a] += multiplier * c
    assert rhs == 4 and full[663] == 6
    support = [a for a in kept if full[a] == 2]
    assert 663 not in support
    desired = [0] * 1214
    desired[663] = 6
    for a in support:
        desired[a] = 2
    assert all(full[a] == desired[a] for a in kept)
    differences = [[a, full[a] - desired[a]] for a in range(1214) if full[a] != desired[a]]
    assert all(a in equality["proved_zero_columns"] for a, _ in differences)
    return {"identity_on_proved_face": "3*x_663 + sum_{a in S} x_a = 2",
            "S": support, "support_size": len(support), "target": 663,
            "all1214_original_integer_coefficients": full, "original_integer_right_hand_side": rhs,
            "original_row_combination": combination, "prior_zero_column_corrections": differences,
            "prior_zero_columns": equality["proved_zero_columns"],
            "division_after_zero_substitution": 2,
            "nonnegative_integer_consequence": "x_663=0; then sum_{a in S} x_a=2",
            "unit_upper_bounds_needed_for_this_identity": False,
            "numerical_point_or_dual_feasibility_needed": False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    data = {}
    for key, (name, expected) in INPUTS.items():
        raw = (ROOT / name).read_bytes()
        assert digest(raw) == expected
        data[key] = [json.loads(line) for line in raw.splitlines()] if key == "certificates" else json.loads(raw)
    original, rows, kept, index = reconstruct(data["native"], data["equalities"], data["model"])
    assert [p["objective_id"] for p in data["certificates"]] == [16, 32, 33, 35, 40]
    summaries = [check_bound(p, rows, kept, index, data["model"])[0] for p in data["certificates"]]
    refined, multipliers, residual = check_bound(data["refined663"], rows, kept, index, data["model"])
    assert refined["upper_bound"] == "2/3" and refined["positive_box_correction_numerator"] == 0
    identity = short_identity(original, rows, data["equalities"], kept, multipliers, residual)
    assert all(any(w["original_native_row"] == 580 for w in s["existing_direct_capacity_witnesses"]) for s in summaries[2:])
    assert not summaries[1]["existing_direct_capacity_witnesses"]
    report = {"status": "PASS: all five exact bounds and the full original-coordinate 663 identity",
              "source_sha256": digest(Path(__file__).read_bytes()),
              "inputs": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
              "reconstruction": {"original_native_rows": len(original), "kept_native_rows": 1961,
                                 "box_tautologies_checked": 310, "proved_parity_equalities": 2,
                                 "original_columns": 1214, "proved_zero_columns": 111,
                                 "surviving_columns": len(kept), "retained_nonzeros": 25767,
                                 "all1143_objective_definitions_checked": True},
              "certificates": summaries, "refined_663": refined, "short_identity": identity,
              "new_Boolean_zero": 663, "pair_requiring_integer_rounding": [259, 590],
              "pairs_already_implied_by_original_Gram_row580": [[259, 591], [259, 593], [259, 732]],
              "prior_zero_and_parity_proofs_rederived": False,
              "prior_premise_scope": "The hash-bound, independently reviewed 111 zeros and H1=H2=1 are premises; all new arithmetic is recomputed here.",
              "subject_sources_imported": False, "optimizer_calls": 0,
              "case4_excluded": False, "seconds": time.monotonic() - started}
    args.output.write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k not in ["short_identity", "certificates", "inputs"]}, indent=2))


if __name__ == "__main__":
    main()
