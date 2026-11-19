"""Frozen native-row specification and exact conditional-box certificates.

This module imports no optimizer, NumPy, large selector matrix, or trace engine.
All 2,271 original native rows remain. The 17 added rows are already accepted
global consequences. The 54 selected boxes are the complete surviving H27=1
subfamily of the separately cold-checked 191-box whole-case cover.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import product
import json
from math import gcd, isfinite
from pathlib import Path
import time

ROOT = Path(__file__).resolve().parents[2]
LOGS = "experiments/logs/grids-and-triangles/"
N = 1214
INPUTS = {
    "native": (LOGS+"complement-rook-35core-case0004-native-cpsat-model.json", "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "base_model": (LOGS+"rook-case4-face112-weighted-parity-model01/model.json", "c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3"),
    "base_cold": (LOGS+"rook-case4-face112-weighted-parity-model01-cold-replay.json", "567185c755134fcf7c15bb7be762bb2a70a503254259b2eb44a92f91abb39156"),
    "boxes": (LOGS+"rook-case4-box-low-face-scan01/child/box-inputs.json.gz", "29fbaf96aa14a89089136a30951f4f597f068ae0481ab1b1f87c297395ec4aab"),
    "box_cold": (LOGS+"rook-case4-three-gram-full-rows-run01-cold/child-result.json", "cda4f7a1b27b991827cd794c917a1a9ed9442e3b77bb6044f1d191f4f084399e"),
    "box_cold_owner": (LOGS+"rook-case4-three-gram-full-rows-run01-cold/supervisor.json", "76f32ef2fb7c0d105eb49037ba3cc8522e78a47e4d39984c6107252b2c3723cd"),
    "box_capacity_cold": (LOGS+"rook-case4-box-low-face-scan01/independent-replay.json", "69fb21a3589bed904b859f1a8272aa26116ad7ab59931a4513ab16ffa60d91b0"),
    "full_rows_preparation": (LOGS+"rook-case4-three-gram-full-rows-preparation01/preparation.json", "989ab22a2c2f78cb65b622dfdb4e0aabe8f0353d4616437e736755d4640b7ac1"),
    "six_cut_preparation": (LOGS+"rook-case4-box-cut-lp-preparation01.json", "99dc881f2c7139eb336e6792f0acba6ba6499fecbed12b5fc92d746142d6eaf0"),
    "latest_point": (LOGS+"rook-case4-box-cut-lp-run01/exact/candidate.json", "7fda72c6a212a6ebe504c03a17f66c05c8545d33e4aebc651f42f817cc3a4bd9"),
    "latest_point_cold": (LOGS+"rook-case4-box-cut-lp-run01/exact/cold.json", "b69a3a38aeb911c45657871544f21897bc4f9bb6201675c1eab5f45ca8a5c317"),
    "membership": (LOGS+"rook-case4-box-hull-membership-run01/exact/certificate.json", "1c079f5616269cdc263bf150c6e3248b26d638135f2dd9dff715571e34ef8bd1"),
    "membership_cold": (LOGS+"rook-case4-box-hull-membership-run01/cold/result.json", "5ddd8a2ae81b091813dd4de8e23576cc07fa70769d220c71cf3734fd5eac187b"),
}
LIMITS = {
    "branches": 54, "one_native_call_per_branch": True,
    "requested_native_seconds_per_branch": 2.0,
    "cumulative_native_seconds": 120.0,
    "forward_seconds": 180, "forward_owner_seconds": 210,
    "cold_seconds": 60, "cold_owner_seconds": 90,
    "prepare_seconds": 60, "prepare_owner_seconds": 90,
    "maximum_transcript_bytes": 64 << 20,
    "maximum_exact_integer_bits": 4096,
    "threads": 1, "automatic_retries": 0,
    "full_pool_scans": 0, "extra_ray_solves": 0,
}
SCALES = (1, 2, 4, 8, 16, 64, 256, 4096, 65536, 1000000)
Q = [260, 399, 403, 406, 761, 762, 763, 764, 765, 803]
CAPACITY = [23]+Q


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def reference(path):
    path = Path(path).resolve()
    raw = path.read_bytes()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def write(path, value):
    path = Path(path)
    assert not path.exists(), str(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    raw = canonical(value)+b"\n"
    if path.suffix == ".gz":
        raw = gzip.compress(raw, mtime=0)
    temporary = path.with_name(path.name+".tmp")
    with temporary.open("xb") as stream:
        stream.write(raw)
    temporary.replace(path)
    return reference(path)


def read(reference_record):
    path = ROOT/reference_record["path"]
    raw = path.read_bytes()
    assert sha(raw) == reference_record["sha256"]
    if "bytes" in reference_record:
        assert len(raw) == reference_record["bytes"]
    return json.loads(gzip.decompress(raw) if path.suffix == ".gz" else raw)


def input_data():
    return {name: read({"path": path, "sha256": digest})
            for name, (path, digest) in INPUTS.items()}


def normalize_row(terms, lower, upper, family):
    assert type(lower) is type(upper) is int and lower <= upper
    coefficients = Counter()
    for a, c in terms:
        assert type(a) is type(c) is int and 0 <= a < N
        coefficients[a] += c
    return {'terms': [[a, c] for a, c in sorted(coefficients.items()) if c],
            'lower': lower, 'upper': upper, 'family': family}


def original_rows(inventory):
    rows = []
    for i, j, quota, support in inventory['Gram_rows']:
        rows.append(normalize_row([[a, 1] for a in support], quota, quota, 'Gram'))
    for original, support in inventory['original_signature_rows']:
        rows.append(normalize_row([[a, 1] for a in support], 0, 1, 'original_signature'))
    for item in inventory['triple_rows']:
        rows.append(normalize_row([[a, 1] for a in item['members']], 0, 1, 'core_triple'))
    for clause in inventory['Gram_conflict_clauses']:
        assert len(clause) == 2 and all(type(v) is int and v < 0 for v in clause)
        rows.append(normalize_row([[-v-1, 1] for v in clause], 0, 1, 'Gram_conflict'))
    for cut in inventory['uncapped_integer_cuts']:
        target, demand = cut['target_column'], cut['positive_demand']
        assert type(demand) is int and demand > 0
        assert all(type(w) is int and w > 0 for a, w in cut['positive_terms'])
        terms = [[a, w] for a, w in cut['positive_terms']] + [[target, -demand]]
        rows.append(normalize_row(terms, 0, sum(w for a, w in cut['positive_terms']), 'uncapped_row_cut'))
    assert Counter(row['family'] for row in rows) == {
        'Gram': 630, 'original_signature': 186, 'core_triple': 1365,
        'Gram_conflict': 30, 'uncapped_row_cut': 60}
    assert len(rows) == 2271
    return rows


def appended_rows(data):
    base, old = data["base_model"], data["full_rows_preparation"]
    rows = []
    for support, interval in zip(base["integer_cover_live_original_supports"], base["integer_cover_ranges"]):
        assert interval == [1, 1]
        rows.append(normalize_row([[a, 1] for a in support], *interval, "proved_unit_sum"))
    for pair in base["added_pair_rows"]:
        rows.append(normalize_row([[a, 1] for a in pair], 0, 1, "proved_pair_AMO"))
    rows.append(normalize_row([[a, 1] for a in base["third_parity_cover_original_support"]],
                              *base["third_parity_cover_range"], "inherited_H3"))
    for row in base["weighted_parity_rows"]:
        rows.append(normalize_row(row["terms"], row["lower"], row["upper"], "inherited_weighted_parity"))
    assert len(rows) == 9
    assert old["definition"]["H42_equal_five_is_not_a_premise"]
    inherited = old["appended_rows"]
    registry = data["six_cut_preparation"]["registry"]
    assert len(inherited) == 7 and len(registry) == 6
    for i, row in enumerate(inherited):
        if i < 5:
            inequality = registry[i]["certificate"]["inequality"]
            assert inequality["terms"] == row["terms"] and inequality["upper"] == row["upper"]
            assert row["lower"] == sum(min(0, c) for a, c in row["terms"])
        rows.append(normalize_row(row["terms"], row["lower"], row["upper"], row["kind"]))
    box_row = registry[5]
    assert box_row["proof_kind"] == "cold_complete_branch_box_capacity"
    assert box_row["certificate"]["inequality"] == {"terms": [[a, 1] for a in CAPACITY], "upper": 1}
    assert box_row["certificate"]["direct_replay"]["sha256"] == INPUTS["box_capacity_cold"][1]
    rows.append(normalize_row([[a, 1] for a in CAPACITY], 0, 1, "proved_complete_box_capacity"))
    assert len(rows) == 17
    return rows


def state_bounds(state):
    assert type(state) is str and set(state) <= set("01?")
    return ([int(v == "1") for v in state], [int(v != "0") for v in state])


def build():
    data = input_data()
    boxes, cold, owner = data["boxes"], data["box_cold"], data["box_cold_owner"]
    assert cold["status"] == "PASS" and cold["checked"] == 260
    assert cold["checked_fixed_points"] == 191 and cold["checked_contradictions"] == 69
    assert cold["checked_partial"] == 0 and cold["all260_nonpartial_branches_checked"]
    assert cold["prior184_contradictions_and_complete_original_branch_cover_bound"]
    assert owner["child_reaped"] and owner["exit_code"] == 0 and not owner["hard_timeout"]
    assert owner["child_result"]["sha256"] == INPUTS["box_cold"][1]
    assert boxes["coverage"] == {"feasible_boxes_claimed": False, "full_row_contradictions": 69,
        "global_new_units": 0, "original_capacity_rejections": 2391, "original_patterns": 2835,
        "partial_or_missing": 0, "prior_native_contradictions": 184, "remaining_boxes": 191}
    columns, zeros = boxes["original_column_ids"], boxes["proved_zero_columns"]
    assert len(columns) == 1102 and len(zeros) == 112
    assert columns == sorted(set(range(N))-set(zeros))
    assert zeros == data["base_model"]["fixed_zero_columns"]
    position = {a: j for j, a in enumerate(columns)}
    originals = original_rows(data["native"]["primary_inventory"])
    combined = [0]*N
    for r in (214, 344, 582):
        assert originals[r]["lower"] == originals[r]["upper"] == 1
        for a, c in originals[r]["terms"]:
            combined[a] += c
    live = {a: c for a, c in enumerate(combined) if c and a in position}
    assert Counter(live.values()) == {1: 26, 2: 9, 3: 1}
    assert [a for a, c in live.items() if c == 3] == [764]
    H = [a for a, c in live.items() if c % 2]
    assert [a for a, c in live.items() if c // 2] == Q
    all_boxes = boxes["boxes"]
    assert len(all_boxes) == 191 and len({b["index"] for b in all_boxes}) == 191
    proof_bindings = {b["index"]: b for b in boxes["all260_proof_bindings"]}
    assert sorted(proof_bindings) == list(range(260))
    selected = []
    for box in all_boxes:
        state = box["state"]
        assert len(state) == 1102
        lo, hi = state_bounds(state)
        assert sha(bytes(255 if v == "?" else int(v) for v in state)) == box["state_sha256"]
        assert all(state[position[a]] in "01" for a in live)
        actual = [a for a in live if lo[position[a]]]
        assert actual == box["selected"] and sum(live[a] for a in actual) == 3
        h = sum(lo[position[a]] for a in H)
        assert h in (1, 3)
        assert (h == 1) == (box["kind"] in ("weight3_singleton", "weight1_weight2_pair"))
        proof = proof_bindings[box["index"]]
        assert proof["terminal"] == "fixed_point" and proof["prior_branch_id"] == box["prior_branch_id"]
        if h == 1:
            selected.append({**box, "pilot_index": len(selected), "proof_binding": proof})
    assert len(selected) == 54
    assert Counter(b["kind"] for b in selected) == {"weight3_singleton": 1, "weight1_weight2_pair": 53}
    assert selected == sorted(selected, key=lambda b: b["index"])
    rows = []
    for r, row in enumerate(originals+appended_rows(data)):
        reduced = [[position[a], c] for a, c in row["terms"] if a in position]
        rows.append({"row_id": r, "family": row["family"], "original_terms": row["terms"],
                     "terms": reduced, "lower": row["lower"], "upper": row["upper"]})
    assert len(rows) == 2288
    pointers, indices, coefficients = [0], [], []
    for row in rows:
        assert row["terms"] == sorted(row["terms"])
        assert len({j for j, c in row["terms"]}) == len(row["terms"])
        assert all(abs(v) < 2**53 for v in (row["lower"], row["upper"]))
        for j, c in row["terms"]:
            assert 0 <= j < 1102 and type(c) is int and c != 0 and abs(c) < 2**53
            indices.append(j); coefficients.append(c)
        pointers.append(len(indices))
    matrix = {"variables": 1102, "rows": len(rows), "row_pointers": pointers,
              "column_indices": indices, "coefficients": coefficients,
              "row_lower": [r["lower"] for r in rows], "row_upper": [r["upper"] for r in rows]}
    return {"source_sha256": sha(Path(__file__).read_bytes()), "input_bindings": INPUTS,
        "limits": LIMITS, "original_variables": N, "variables": 1102,
        "original_column_ids": columns, "proved_zero_columns": zeros,
        "rows": rows, "matrix": matrix, "matrix_sha256": sha(canonical(matrix)),
        "all191_boxes": all_boxes, "selected54_boxes": selected,
        "whole_cover": boxes["coverage"], "partition": {"original_Gram_rows": [214, 344, 582],
            "rhs": 3, "H27": H, "Q": Q, "identity": "H27+2Q=3", "low_boxes": 54, "high_boxes": 137},
        "latest_point_sha256": INPUTS["latest_point"][1],
        "box_only_membership_certificate_sha256": INPUTS["membership"][1],
        "case4_excluded": False, "optimizer_calls": 0, "old_trace_replay_repeated": False,
        "large_cover_matrix_loaded": False, "coordinate_cover_rows_omitted_from_native_pilot": 178533,
        "feasible_native_point_would_remain_unresolved": True}


def combination(rows, variables, multipliers, lower, upper, original=False):
    assert len(lower) == len(upper) == variables
    assert all(type(a) is type(b) is int and 0 <= a <= b <= 1 for a, b in zip(lower, upper))
    assert multipliers == sorted(multipliers) and len({r for r, v in multipliers}) == len(multipliers)
    vector, bound = [0]*variables, 0
    for r, value in multipliers:
        assert type(r) is type(value) is int and 0 <= r < len(rows) and value != 0
        assert abs(value).bit_length() <= LIMITS["maximum_exact_integer_bits"]
        row = rows[r]
        bound += value*(row["upper"] if value > 0 else row["lower"])
        for j, coefficient in row["original_terms" if original else "terms"]:
            assert 0 <= j < variables and type(coefficient) is int
            vector[j] += value*coefficient
    minimum = sum(c*(lo if c >= 0 else hi) for c, lo, hi in zip(vector, lower, upper))
    assert all(abs(v).bit_length() <= LIMITS["maximum_exact_integer_bits"] for v in vector+[bound, minimum])
    return vector, bound, minimum


def exclusion(specification, pilot_index, multipliers):
    branch = specification["selected54_boxes"][pilot_index]
    assert branch["pilot_index"] == pilot_index
    lower, upper = state_bounds(branch["state"])
    vector, bound, minimum = combination(specification["rows"], 1102, multipliers, lower, upper)
    if minimum <= bound:
        return None
    full_lower, full_upper = [0]*N, [0]*N
    for j, a in enumerate(specification["original_column_ids"]):
        full_lower[a], full_upper[a] = lower[j], upper[j]
    full_vector, full_bound, full_minimum = combination(specification["rows"], N, multipliers,
                                                       full_lower, full_upper, original=True)
    assert (full_bound, full_minimum) == (bound, minimum)
    assert [full_vector[a] for a in specification["original_column_ids"]] == vector
    guards = branch["selected"]
    assert len(guards) in (1, 2) and all(lower[specification["original_column_ids"].index(a)] == 1 for a in guards)
    return {"kind": "EXACT_CONDITIONED_NATIVE_ROW_EXCLUSION", "pilot_index": pilot_index,
        "whole_cover_box_index": branch["index"], "prior_branch_id": branch["prior_branch_id"],
        "raw_pattern_id": branch["raw_id"], "state_sha256": branch["state_sha256"],
        "matrix_sha256": specification["matrix_sha256"], "cold_branch_proof": branch["proof_binding"],
        "row_multipliers": [[r, str(v)] for r, v in multipliers],
        "combined_row_upper": str(bound), "minimum_over_entire_box": str(minimum),
        "positive_gap": str(minimum-bound), "full1214_coefficients": list(map(str, full_vector)),
        "full1214_bounds_sha256": sha(canonical([full_lower, full_upper])),
        "conditional_guards": guards,
        "implied_Boolean_nogood": {"terms": [[a, 1] for a in guards], "upper": len(guards)-1},
        "numerical_ray_feasibility_assumed": False, "no_other_branch_excluded": True,
        "case4_excluded": False, "whole_graph_problem_resolved": False}


def rounded_proposals(hex_values):
    values = [float.fromhex(v) for v in hex_values]
    assert values and all(isfinite(v) for v in values)
    maximum = max(map(abs, values))
    if maximum == 0:
        return
    normalized = [v/maximum for v in values]
    seen = set()
    for scale in SCALES:
        integers = [int(round(v*scale)) for v in normalized]
        divisor = gcd(*integers)
        if not divisor:
            continue
        integers = [v//divisor for v in integers]
        for orientation in (1, -1):
            sparse = tuple((r, orientation*v) for r, v in enumerate(integers) if v)
            if sparse not in seen:
                seen.add(sparse)
                yield {"scale": scale, "orientation": orientation, "multipliers": [list(v) for v in sparse]}


def controls():
    extrema, ranged, contradictions = 0, 0, 0
    for state_tuple in product("01?", repeat=3):
        lower, upper = state_bounds("".join(state_tuple))
        vertices = list(product(*(range(lo, hi+1) for lo, hi in zip(lower, upper))))
        for coefficients in product(range(-2, 3), repeat=3):
            exact_min = sum(c*(lo if c >= 0 else hi) for c, lo, hi in zip(coefficients, lower, upper))
            assert exact_min == min(sum(c*x for c, x in zip(coefficients, point)) for point in vertices)
            extrema += 1
        rows = [{"terms": [[0, 1], [1, -2]], "lower": -1, "upper": 1},
                {"terms": [[1, 2], [2, 1]], "lower": 1, "upper": 2}]
        for a, b in product(range(-2, 3), repeat=2):
            multipliers = [[i, v] for i, v in enumerate((a, b)) if v]
            vector, bound, minimum = combination(rows, 3, multipliers, lower, upper)
            assert minimum == min(sum(c*x for c, x in zip(vector, point)) for point in vertices)
            feasible = [p for p in vertices if all(row["lower"] <= sum(c*p[j] for j, c in row["terms"]) <= row["upper"] for row in rows)]
            assert all(sum(c*x for c, x in zip(vector, p)) <= bound for p in feasible)
            if minimum > bound:
                assert not feasible
                contradictions += 1
            ranged += 1
    assert state_bounds("01?") == ([0, 1, 0], [0, 1, 1])
    assert state_bounds("?10") == ([0, 1, 0], [1, 1, 0])
    assert normalize_row([[2, 3], [2, -3], [1, 4]], 0, 4, "control")["terms"] == [[1, 4]]
    assert len(list(rounded_proposals([float(1).hex(), float(-2).hex(), float(0).hex()]))) >= 2
    rejected = 0
    for bad in ([[0, 1], [0, 2]], [[0, 0]], [[2, 1]], [[0, 1.5]]):
        try:
            combination([{"terms": [[0, 1]], "lower": 0, "upper": 1}], 1, bad, [0], [1])
        except (AssertionError, IndexError):
            rejected += 1
        else:
            raise AssertionError("bad multiplier control accepted")
    assert rejected == 4
    return {"signed_three_coordinate_extrema": extrema, "ranged_combination_controls": ranged,
            "exact_empty_box_controls": contradictions, "malformed_multiplier_rejections": rejected,
            "bound_reset_and_duplicate_term_controls": True, "native_calls": 0}


def prepare(directory):
    started = time.monotonic()
    assert not directory.exists()
    directory.mkdir(parents=True)
    spec = build()
    checked = controls()
    assert time.monotonic()-started < LIMITS["prepare_seconds"]
    spec_ref = write(directory/"specification.json.gz", spec)
    report = {"status": "PREPARED_COMPLETE_LOW54_NATIVE_ROW_PILOT_NO_OPTIMIZER",
        "source": reference(Path(__file__)), "input_bindings": INPUTS, "specification": spec_ref,
        "limits": LIMITS, "rows": len(spec["rows"]), "original_native_rows": 2271,
        "accepted_append_rows": 17, "variables": 1102,
        "nonzeros": len(spec["matrix"]["coefficients"]), "matrix_sha256": spec["matrix_sha256"],
        "whole_cover_boxes": 191, "selected_low_boxes": 54, "unselected_high_boxes": 137,
        "selected_whole_cover_indices": [b["index"] for b in spec["selected54_boxes"]],
        "free_coordinates_range": [min(b["state"].count("?") for b in spec["selected54_boxes"]),
                                   max(b["state"].count("?") for b in spec["selected54_boxes"])],
        "controls": checked, "large_matrix_loaded": False, "old_trace_replay_repeated": False,
        "native_or_solver_imported": False, "optimizer_calls": 0, "seconds": time.monotonic()-started}
    write(directory/"preparation.json", report)
    return report


def load(preparation):
    report = json.loads(Path(preparation).read_bytes())
    assert report["source"] == reference(Path(__file__)) and report["limits"] == LIMITS
    assert report["status"] == "PREPARED_COMPLETE_LOW54_NATIVE_ROW_PILOT_NO_OPTIMIZER"
    spec = read(report["specification"])
    assert spec["source_sha256"] == report["source"]["sha256"]
    assert spec["input_bindings"] == {k: list(v) for k, v in INPUTS.items()}
    assert spec["matrix_sha256"] == report["matrix_sha256"] == sha(canonical(spec["matrix"]))
    assert len(spec["selected54_boxes"]) == 54 and len(spec["all191_boxes"]) == 191
    return report, spec


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare",))
    parser.add_argument("--directory", type=Path, required=True)
    args = parser.parse_args()
    result = prepare(args.directory.resolve())
    print(json.dumps({k: result[k] for k in ("status", "rows", "variables", "nonzeros", "matrix_sha256", "seconds")}), flush=True)


if __name__ == "__main__":
    main()
