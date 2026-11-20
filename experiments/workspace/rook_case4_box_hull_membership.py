"""Exact preparation and certificates for membership in 191 branch boxes.

The production model has 191 mixture weights.  Every coordinate contributes
two endpoint inequalities.  Input recovery reuses completed cold proof
bindings; it never propagates a branch or loads the original large matrix.
This module has no numerical optimizer dependency.
"""

from fractions import Fraction
import gzip
import hashlib
from itertools import product
import json
import math
from pathlib import Path
import struct
import sys
import time


ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
INPUTS = {
    "boxes": (BASE + "rook-case4-box-low-face-scan01/child/box-inputs.json.gz",
              "29fbaf96aa14a89089136a30951f4f597f068ae0481ab1b1f87c297395ec4aab"),
    "box_replay": (BASE + "rook-case4-box-low-face-scan01/independent-replay.json",
                   "69fb21a3589bed904b859f1a8272aa26116ad7ab59931a4513ab16ffa60d91b0"),
    "box_replay_owner": (BASE + "rook-case4-box-low-face-scan01/replay-supervisor.json",
                         "b4698735b836178796a30c8594e5ee8145e280bcbe39b635b7d0fb750cac34fa"),
    "full_preparation": (BASE + "rook-case4-three-gram-full-rows-preparation01/preparation.json",
                         "989ab22a2c2f78cb65b622dfdb4e0aabe8f0353d4616437e736755d4640b7ac1"),
    "full_cold": (BASE + "rook-case4-three-gram-full-rows-run01-cold/child-result.json",
                  "cda4f7a1b27b991827cd794c917a1a9ed9442e3b77bb6044f1d191f4f084399e"),
    "full_cold_owner": (BASE + "rook-case4-three-gram-full-rows-run01-cold/supervisor.json",
                        "76f32ef2fb7c0d105eb49037ba3cc8522e78a47e4d39984c6107252b2c3723cd"),
    "point": (BASE + "rook-case4-box-cut-lp-run01/exact/candidate.json",
              "7fda72c6a212a6ebe504c03a17f66c05c8545d33e4aebc651f42f817cc3a4bd9"),
    "point_cold": (BASE + "rook-case4-box-cut-lp-run01/exact/cold.json",
                   "b69a3a38aeb911c45657871544f21897bc4f9bb6201675c1eab5f45ca8a5c317"),
    "point_terminal": (BASE + "rook-case4-box-cut-lp-run01/result.json",
                       "3785d201b021eb8347c123c536830a46f8533cb4127c74d7710f8f21814e2190"),
    "point_bindings": (BASE + "rook-case4-box-cut-lp-run01-bindings.json",
                       "3788903bb955677532e40ca5d4c3b18609e162ad367ddae7bf57bd03e3c3dc57"),
    "clique_evaluation": (BASE + "rook-case4-box-cut-lp-clique-evaluation01.json",
                          "d5a3651a38f6cf68159dca6ef6485341eab9acfef8b85b112e414012e2774426"),
}
LIMITS = {
    "preparation_seconds": 30, "native_calls": 1, "native_seconds": 60,
    "native_owner_seconds": 90, "exact_seconds": 60, "exact_owner_seconds": 90,
    "cold_seconds": 60, "cold_owner_seconds": 90, "whole_owner_seconds": 300,
    "maximum_basis_dimension": 191, "maximum_exact_output_bits": 2048,
    "maximum_record_bytes": 16 * 1024 * 1024, "threads": 1,
    "maximum_abs_cut_coefficient": 1 << 20, "automatic_retries": 0,
}
SCALES = (1, 2, 4, 8, 16, 64, 256, 4096, 65536, 1048576)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def reference(path):
    raw = path.read_bytes()
    return {"path": str(path.resolve().relative_to(ROOT)), "sha256": sha(raw), "bytes": len(raw)}


def read(binding):
    path, digest = binding
    raw = (ROOT / path).read_bytes()
    assert len(raw) <= LIMITS["maximum_record_bytes"] and sha(raw) == digest, path
    raw = gzip.decompress(raw) if path.endswith(".gz") else raw
    assert len(raw) <= LIMITS["maximum_record_bytes"]
    return json.loads(raw)


def write(path, value):
    raw = canonical(value) + b"\n"
    assert len(raw) <= LIMITS["maximum_record_bytes"]
    if path.suffix == ".gz":
        raw = gzip.compress(raw, mtime=0)
    with path.open("xb") as stream:
        stream.write(raw)


def integer(value):
    assert type(value) in (int, str)
    if type(value) is str:
        assert value == str(int(value))
    return int(value)


def load_inputs():
    data = {key: read(binding) for key, binding in INPUTS.items()}
    boxes, replay, owner = (data[k] for k in ("boxes", "box_replay", "box_replay_owner"))
    assert replay["status"] == "PASS_INDEPENDENT_H27_LOW_FACE_CUT_AND_CAPACITY_EQUIVALENCE"
    assert replay["all260_cold_record_bindings_checked"]
    assert replay["inputs"]["boxes"][1] == INPUTS["boxes"][1]
    assert owner["status"] == "CHILD_COMPLETE" and owner["exit_code"] == 0
    assert owner["child_reaped"] and not owner["hard_timeout"]
    assert owner["independent-replay.json"]["sha256"] == INPUTS["box_replay"][1]
    cold, cold_owner = data["full_cold"], data["full_cold_owner"]
    assert cold["status"] == "PASS" and cold["checked"] == 260
    assert cold["all260_nonpartial_branches_checked"] and cold["all_saved_records_checked"]
    assert cold["checked_partial"] == 0 and cold["checked_contradictions"] == 69
    assert cold["checked_fixed_points"] == 191
    assert cold["prior184_contradictions_and_complete_original_branch_cover_bound"]
    assert cold_owner["status"] == "CHILD_COMPLETE" and cold_owner["exit_code"] == 0
    assert cold_owner["child_reaped"] and not cold_owner["hard_timeout"]
    assert cold_owner["child_result"]["sha256"] == INPUTS["full_cold"][1]
    assert boxes["coverage"] == {
        "feasible_boxes_claimed": False, "full_row_contradictions": 69,
        "global_new_units": 0, "original_capacity_rejections": 2391,
        "original_patterns": 2835, "partial_or_missing": 0,
        "prior_native_contradictions": 184, "remaining_boxes": 191,
    }
    proofs = boxes["all260_proof_bindings"]
    assert len(proofs) == 260 and [r["index"] for r in proofs] == list(range(260))
    assert [r["cold_check"] for r in proofs] == cold["checks"]
    fixed = [r["index"] for r in proofs if r["terminal"] == "fixed_point"]
    assert len(fixed) == 191
    ids, zeros = boxes["original_column_ids"], boxes["proved_zero_columns"]
    assert len(ids) == 1102 and len(zeros) == 112
    assert zeros == sorted(set(zeros)) and ids == sorted(set(range(1214)) - set(zeros))
    assert [box["index"] for box in boxes["boxes"]] == fixed
    states = []
    for box in boxes["boxes"]:
        state = box["state"]
        assert len(state) == 1102 and set(state) <= set("01?")
        assert sha(bytes(255 if c == "?" else int(c) for c in state)) == box["state_sha256"]
        states.append(state)
    point, pcold, terminal = (data[k] for k in ("point", "point_cold", "point_terminal"))
    assert pcold["exact_point_replayed"] and pcold["candidate_sha256"] == INPUTS["point"][1]
    assert pcold["full_face_rows_checked"] == 167121
    assert pcold["registry_sha256"] == point["registry_sha256"]
    assert terminal["status"] == "EXACT_SIX_CUT_POSITIVE_SELECTOR_POINT"
    assert terminal["latest_point_accepted_cuts"] == 6
    assert terminal["latest_exact_point"] == {
        "candidate": {"path": INPUTS["point"][0], "sha256": INPUTS["point"][1]},
        "cold": {"path": INPUTS["point_cold"][0], "sha256": INPUTS["point_cold"][1]},
    }
    assert data["point_bindings"]["status"] == "PASS_SIX_CUT_TERMINAL_BINDINGS"
    assert point["matrix_binding"]["original_column_ids"] == {
        "dtype": "uint16", "shape": [1102], "sha256": sha(struct.pack("<1102H", *ids)),
    }
    denominator = integer(point["common_denominator"])
    full = list(map(integer, point["exact_check"]["original1214_selector_numerators"]))
    extended = list(map(integer, point["extended_numerators"]))
    nums = [full[j] for j in ids]
    assert denominator == 2594289631 and len(full) == 1214 and len(extended) == 1103
    assert extended[:-1] == nums and all(full[j] == 0 for j in zeros)
    assert 0 < extended[-1] <= min(nums) and max(nums) <= denominator
    assert pcold["point_key"] == point["exact_check"]["point_key"]
    registry_checks = []
    assert len(terminal["registry"]) == 6
    for entry in terminal["registry"]:
        row = entry["certificate"]["inequality"]
        value = sum(integer(c) * full[a] for a, c in row["terms"])
        slack = integer(row["upper"]) * denominator - value
        assert slack >= 0
        registry_checks.append({"row_key": entry["row_key"], "slack_numerator": str(slack)})
    prepared = data["full_preparation"]
    assert prepared["definition"] == cold["definition"]
    assert prepared["matrix"]["rows"] == 166020 and len(prepared["appended_rows"]) == 7
    prior_rows = []
    for i, row in enumerate(prepared["appended_rows"]):
        activity = sum(integer(c) * full[a] for a, c in row["terms"])
        lo, hi = integer(row["lower"]) * denominator, integer(row["upper"]) * denominator
        prior_rows.append({"index": i, "value_numerator": str(activity),
                           "lower_slack_numerator": str(activity - lo),
                           "upper_slack_numerator": str(hi - activity),
                           "satisfied": lo <= activity <= hi})
    cliques = data["clique_evaluation"]
    assert cliques["inputs"]["point"] == list(INPUTS["point"])
    assert cliques["rows_checked"] == 1216 and cliques["all_rows_satisfied"]
    return {"original_column_ids": ids, "proved_zero_columns": zeros,
            "box_ids": fixed, "states": states, "numerators": nums,
            "original1214_numerators": full, "denominator": denominator,
            "point_key": pcold["point_key"], "t_numerator": extended[-1],
            "registry_checks": registry_checks, "prior_seven_row_checks": prior_rows}


def build_rows(states, nums, denominator, ids=None):
    count, dimension = len(states), len(nums)
    assert count > 0 and all(len(s) == dimension and set(s) <= set("01?") for s in states)
    assert denominator > 0 and all(0 <= n <= denominator for n in nums)
    ids = list(range(dimension)) if ids is None else ids
    assert len(ids) == dimension
    rows = [{"kind": "mixture_sum", "original_column": None,
             "columns": list(range(count)), "lower_numerator": denominator,
             "upper_numerator": denominator}]
    for j, original in enumerate(ids):
        rows.append({"kind": "forced_one", "original_column": original,
                     "columns": [b for b, state in enumerate(states) if state[j] == "1"],
                     "lower_numerator": 0, "upper_numerator": nums[j]})
        rows.append({"kind": "forced_zero", "original_column": original,
                     "columns": [b for b, state in enumerate(states) if state[j] == "0"],
                     "lower_numerator": 0, "upper_numerator": denominator - nums[j]})
    assert all(r["columns"] == sorted(set(r["columns"])) for r in rows)
    return rows


def build_model(domain):
    rows = build_rows(domain["states"], domain["numerators"], domain["denominator"],
                      domain["original_column_ids"])
    assert len(rows) == 2205
    definition = {"source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS,
                  "limits": LIMITS, "cut_rounding_scales": SCALES,
                  "point_key": domain["point_key"], "box_ids": domain["box_ids"],
                  "variables": 191, "coordinate_constraints": 2204, "rows": 2205,
                  "global_zero_coordinates": 112, "remaining_coordinates": 1102,
                  "scope": "membership in the convex hull of the191 accepted axis-aligned boxes"}
    matrix = {"variable_count": 191, "coordinate_count": 1102,
              "rhs_denominator": domain["denominator"], "rows": rows,
              "variable_lower": 0, "variable_upper": 1, "all_coefficients": 1,
              "objective": "zero", "original_column_ids": domain["original_column_ids"]}
    return {"schema": "conway99.rook-case4.box-hull-membership-model.v1",
            "definition": definition, "definition_sha256": sha(canonical(definition)),
            "matrix": matrix, "matrix_sha256": sha(canonical(matrix)),
            "nonzeros": sum(len(r["columns"]) for r in rows),
            "empty_coordinate_rows": sum(not r["columns"] for r in rows[1:]),
            "prior_seven_row_checks": domain["prior_seven_row_checks"],
            "registry_checks": domain["registry_checks"]}


def inspect_masses(states, point_nums, point_den, masses, mass_den):
    assert type(mass_den) is int and mass_den > 0 and len(masses) == len(states)
    assert all(type(m) is int and 0 <= m <= mass_den for m in masses)
    assert sum(masses) == mass_den
    assert max([mass_den.bit_length()] + [abs(m).bit_length() for m in masses]) <= LIMITS["maximum_exact_output_bits"]
    slacks, degenerate = [], 0
    for j, n in enumerate(point_nums):
        lower = sum(m for m, state in zip(masses, states) if state[j] == "1")
        upper = mass_den - sum(m for m, state in zip(masses, states) if state[j] == "0")
        low_slack, high_slack = n * mass_den - point_den * lower, point_den * upper - n * mass_den
        assert 0 <= lower <= upper <= mass_den and low_slack >= 0 and high_slack >= 0
        if lower == upper:
            assert low_slack == high_slack == 0
            degenerate += 1
        else:
            # theta_j = low_slack / (point_den * (upper-lower)) lies in [0,1].
            assert low_slack <= point_den * (upper - lower)
        slacks.append([str(low_slack), str(high_slack)])
    return {"status": "EXACT_BOX_HULL_MEMBERSHIP", "mixture_sum_checked": True,
            "nonnegative_masses_checked": len(masses), "positive_masses": sum(m > 0 for m in masses),
            "coordinate_endpoint_inequalities_checked": 2 * len(point_nums),
            "coordinatewise_interpolation_proved": True, "degenerate_weighted_intervals": degenerate,
            "cross_multiplied_endpoint_slacks": slacks,
            "boolean_or_original_model_solution_claimed": False}


def box_minimum(state, coefficients):
    assert len(state) == len(coefficients) and set(state) <= set("01?")
    return sum(c if flag == "1" else min(c, 0) if flag == "?" else 0
               for flag, c in zip(state, coefficients))


def separator_certificate(domain, coefficients):
    assert len(coefficients) == len(domain["numerators"])
    assert all(type(c) is int for c in coefficients)
    assert max(map(abs, coefficients), default=0) <= LIMITS["maximum_abs_cut_coefficient"]
    extrema = [box_minimum(state, coefficients) for state in domain["states"]]
    alpha = min(extrema)
    point_value = sum(c * n for c, n in zip(coefficients, domain["numerators"]))
    gap = alpha * domain["denominator"] - point_value
    terms = [[a, c] for a, c in zip(domain["original_column_ids"], coefficients) if c]
    return {"status": "EXACT_BOX_HULL_SEPARATOR" if gap > 0 else "NO_EXACT_SEPARATOR",
            "coefficients": coefficients, "original1214_terms": terms,
            "lower": alpha, "all_box_minima": extrema, "point_value_numerator": str(point_value),
            "point_denominator": str(domain["denominator"]), "deficit_numerator": str(gap),
            "scope": "necessary inequality for every solution covered by the frozen boxes",
            "case4_excluded": False}


def rounded_ray_proposals(ray_hex, coordinate_count):
    assert len(ray_hex) == 1 + 2 * coordinate_count
    ray = [Fraction.from_float(float.fromhex(s)) for s in ray_hex]
    signed = [ray[2 + 2*j] - ray[1 + 2*j] for j in range(coordinate_count)]
    maximum = max(map(abs, signed), default=Fraction(0))
    if maximum == 0:
        return []
    proposals, seen = [], set()
    for scale in SCALES:
        for orientation in (1, -1):
            c = [round(orientation * scale * v / maximum) for v in signed]
            divisor = math.gcd(*c)
            if divisor:
                c = [v // divisor for v in c]
            key = tuple(c)
            if key not in seen and any(c):
                seen.add(key)
                proposals.append({"scale": scale, "orientation": orientation, "coefficients": c})
    assert len(proposals) <= 2 * len(SCALES)
    return proposals


def basis_system(matrix, numerical):
    """Use the saved basis only as a candidate face, never a proof premise."""
    basis, codes = numerical["basis"], numerical["basis_codes"]
    assert basis["valid"]
    col_status, row_status = basis["column_status"], basis["row_status"]
    n, rows, den = matrix["variable_count"], matrix["rows"], matrix["rhs_denominator"]
    assert len(col_status) == n and len(row_status) == len(rows)
    basic = [j for j, status in enumerate(col_status) if status == codes["kBasic"]]
    fixed = {}
    for j, status in enumerate(col_status):
        if status == codes["kBasic"]:
            continue
        if status in (codes["kLower"], codes["kZero"]):
            fixed[j] = 0
        elif status == codes["kUpper"]:
            fixed[j] = 1
        else:
            raise ValueError("unsupported nonbasic column status")
    active = [i for i, status in enumerate(row_status) if status != codes["kBasic"]]
    assert len(active) == len(basic) <= LIMITS["maximum_basis_dimension"]
    positions = {j: k for k, j in enumerate(basic)}
    coefficients, rhs, sides = [], [], []
    for i in active:
        row, status = rows[i], row_status[i]
        if status == codes["kLower"]:
            endpoint, side = row["lower_numerator"], "lower"
        elif status == codes["kUpper"]:
            endpoint, side = row["upper_numerator"], "upper"
        elif status == codes["kZero"] and row["lower_numerator"] <= 0 <= row["upper_numerator"]:
            endpoint, side = 0, "zero_proposal"
        else:
            raise ValueError("unsupported nonbasic row status")
        vector = [0] * len(basic)
        shift = 0
        for j in row["columns"]:
            if j in fixed:
                shift += den * fixed[j]
            else:
                vector[positions[j]] = 1
        coefficients.append(vector)
        rhs.append(endpoint - shift)
        sides.append({"row": i, "side": side, "endpoint_numerator": endpoint})
    return {"basic_columns": basic, "fixed_columns": [[j, fixed[j]] for j in sorted(fixed)],
            "active_rows": sides, "coefficients": coefficients, "rhs": rhs,
            "variable_rescaling": "y=D*lambda", "dimension": len(basic),
            "basis_restrictions_are_candidate_assumptions": True}


def masses_from_solution(matrix, system, values):
    den, n = matrix["rhs_denominator"], matrix["variable_count"]
    assert len(values) == len(system["basic_columns"])
    lambdas = [None] * n
    for j, value in system["fixed_columns"]:
        lambdas[j] = Fraction(value)
    for j, value in zip(system["basic_columns"], values):
        lambdas[j] = Fraction(value) / den
    assert all(v is not None for v in lambdas)
    for row, rhs in zip(system["coefficients"], system["rhs"]):
        assert sum(a * Fraction(v) for a, v in zip(row, values)) == rhs
    common = math.lcm(*(v.denominator for v in lambdas))
    masses = [v.numerator * (common // v.denominator) for v in lambdas]
    divisor = math.gcd(common, *masses)
    return [m // divisor for m in masses], common // divisor


def tiny_solve(coefficients, rhs):
    """Independent Fraction elimination, confined to controls of order <=3."""
    n = len(rhs)
    assert n <= 3 and len(coefficients) == n and all(len(r) == n for r in coefficients)
    a = [[Fraction(v) for v in row] + [Fraction(b)] for row, b in zip(coefficients, rhs)]
    for j in range(n):
        pivot = next((i for i in range(j, n) if a[i][j]), None)
        if pivot is None:
            raise ValueError("singular control")
        a[j], a[pivot] = a[pivot], a[j]
        q = a[j][j]
        a[j] = [v / q for v in a[j]]
        for i in range(n):
            if i != j:
                q = a[i][j]
                a[i] = [v - q * w for v, w in zip(a[i], a[j])]
    return [row[-1] for row in a]


def controls():
    started = time.monotonic()
    endpoint_tests = 0
    for flags in product("01?", repeat=3):
        state = "".join(flags)
        vertices = list(product(*[(0, 1) if c == "?" else (int(c),) for c in state]))
        for c in product(range(-2, 3), repeat=3):
            assert box_minimum(state, c) == min(sum(a*b for a, b in zip(c, v)) for v in vertices)
            endpoint_tests += 1
    mixture_tests = 0
    states2 = ["".join(s) for s in product("01?", repeat=2)]
    for a, b in product(states2, repeat=2):
        for theta in product((Fraction(0), Fraction(1, 2), Fraction(1)), repeat=2):
            components = [[Fraction(int(s[j])) if s[j] != "?" else theta[j] for j in range(2)]
                          for s in (a, b)]
            point = [(components[0][j] + 2*components[1][j]) / 3 for j in range(2)]
            d = math.lcm(*(v.denominator for v in point))
            nums = [int(v*d) for v in point]
            assert inspect_masses([a, b], nums, d, [1, 2], 3)["coordinatewise_interpolation_proved"]
            mixture_tests += 1
    domain = {"states": ["00", "11"], "numerators": [2, 1], "denominator": 4,
              "original_column_ids": [0, 1]}
    cert = separator_certificate(domain, [-1, 1])
    assert cert["lower"] == 0 and cert["deficit_numerator"] == "1"
    ray = [0.0, 1.0, 0.0, -1.0, 0.0]
    assert any(p["coefficients"] == [-1, 1] for p in rounded_ray_proposals([v.hex() for v in ray], 2))
    domain2 = {"states": ["?0", "0?"], "numerators": [3, 3], "denominator": 4,
               "original_column_ids": [0, 1]}
    cert2 = separator_certificate(domain2, [-1, -1])
    assert cert2["lower"] == -1 and cert2["deficit_numerator"] == "2"
    rows = build_rows(["00", "11"], [2, 2], 3)
    matrix = {"variable_count": 2, "rhs_denominator": 3, "rows": rows}
    codes = {"kLower": 0, "kBasic": 1, "kUpper": 2, "kZero": 3, "kNonbasic": 4}
    numeric = {"basis_codes": codes, "basis": {"valid": True, "column_status": [1, 1],
               "row_status": [2, 2, 1, 1, 1]}}
    system = basis_system(matrix, numeric)
    assert system["coefficients"] == [[1, 1], [0, 1]] and system["rhs"] == [3, 2]
    masses, den = masses_from_solution(matrix, system, tiny_solve(system["coefficients"], system["rhs"]))
    assert (masses, den) == ([1, 2], 3)
    inspect_masses(["00", "11"], [2, 2], 3, masses, den)
    fixed_matrix = {"variable_count": 2, "rhs_denominator": 2,
                    "rows": build_rows(["??", "00"], [1, 1], 2)}
    fixed_numeric = {"basis_codes": codes, "basis": {"valid": True, "column_status": [2, 0],
                     "row_status": [1] * 5}}
    fixed_system = basis_system(fixed_matrix, fixed_numeric)
    fm, fd = masses_from_solution(fixed_matrix, fixed_system, [])
    assert (fm, fd) == ([1, 0], 1)
    inspect_masses(["??", "00"], [1, 1], 2, fm, fd)
    rejected = 0
    for bad in ([2, 2], [-1, 4], [0, 3]):
        try:
            inspect_masses(["00", "11"], [2, 2], 3, bad, 3)
        except AssertionError:
            rejected += 1
    try:
        tiny_solve([[0, 1], [0, 1]], [2, 2])
    except ValueError:
        rejected += 1
    assert rejected == 4
    return {"status": "PASS_EXACT_BOX_MEMBERSHIP_CONTROLS", "signed_endpoint_tests": endpoint_tests,
            "interpolation_distributions": mixture_tests, "strict_separator_controls": 2,
            "basis_and_fixed_bound_controls": 2, "deliberate_rejections": rejected,
            "numerical_optimizers": 0, "seconds": time.monotonic() - started}


def prepare(directory):
    started = time.monotonic()
    directory.mkdir(parents=True, exist_ok=False)
    control = controls()
    domain = load_inputs()
    model = build_model(domain)
    d, k = domain["denominator"], 191
    # For a k-square 0/1 system, det(A)^2 <= k^k.  Shifted RHS magnitudes
    # are at most (k+1)D.  These are proposal bounds, never a rank claim.
    det_square = k ** k
    numerator_square = det_square * ((k + 1) * d) ** 2
    arithmetic = {"maximum_basis_dimension": k, "coefficient_abs_bound": 1,
                  "shifted_rhs_abs_bound": (k + 1) * d,
                  "hadamard_det_squared_bound": str(det_square),
                  "cramer_numerator_squared_bound": str(numerator_square),
                  "lambda_denominator_bits_bound": d.bit_length() + (det_square.bit_length() + 1)//2,
                  "no_case_rank_or_basis_assumed": True,
                  "temporary_native_exact_integer_sizes_not_claimed_bounded": True}
    write(directory / "controls.json", control)
    write(directory / "model.json.gz", model)
    assert time.monotonic() - started < LIMITS["preparation_seconds"]
    report = {"status": "PREPARED_191_WEIGHT_BOX_HULL_MEMBERSHIP_NO_OPTIMIZER",
              "source_sha256": sha(Path(__file__).read_bytes()), "inputs": INPUTS,
              "limits": LIMITS, "model": reference(directory / "model.json.gz"),
              "controls": reference(directory / "controls.json"),
              "definition_sha256": model["definition_sha256"], "matrix_sha256": model["matrix_sha256"],
              "variables": 191, "rows": 2205, "nonzeros": model["nonzeros"],
              "empty_coordinate_rows": model["empty_coordinate_rows"],
              "point_denominator": str(d), "point_key": domain["point_key"],
              "prior_seven_row_checks": domain["prior_seven_row_checks"],
              "arithmetic": arithmetic, "optimizer_calls": 0, "native_imports": 0,
              "large_matrix_loads": 0, "old_trace_replays": 0,
              "seconds": time.monotonic() - started}
    write(directory / "preparation.json", report)
    return report


if __name__ == "__main__":
    assert __debug__ and len(sys.argv) == 3 and sys.argv[1] == "prepare"
    result = prepare(Path(sys.argv[2]))
    print(json.dumps({"status": result["status"], "variables": result["variables"],
                      "rows": result["rows"], "nonzeros": result["nonzeros"],
                      "seconds": result["seconds"]}))
