"""Exact support cuts for the 191 cold-checked whole-case H27 boxes.

Preparation reads only small frozen artifacts and the prepared 260 x 1102
state archive. It does not import a propagation module, load the full row
matrix, repeat trace reasons, or invoke an optimizer. The numerical LP is a
coefficient proposal; every accepted cut uses exact minima over every box.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import importlib.metadata
import itertools
import json
import math
from pathlib import Path
import platform
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
PREP = BASE + "rook-case4-three-gram-full-rows-preparation01/"
RUN = BASE + "rook-case4-three-gram-full-rows-run01/"
COLD = BASE + "rook-case4-three-gram-full-rows-run01-cold/"
POINT = BASE + "rook-case4-full-span-cycle-run01/"
FULL_SOURCE = "fc8d48f1632442daee5d186156874ba50fe46fc55e01a36010525f27bf21cfd1"
INPUTS = {
    "full_source": ("experiments/workspace/rook_case4_three_gram_full_rows.py", FULL_SOURCE),
    "full_source_gate": (BASE + "rook-case4-three-gram-full-rows-root-source-gate01.json", "841c76523792a0ea51b236520f86f4e52a13bbb9872f043f207d3701298fc5c4"),
    "preparation": (PREP + "preparation.json", "989ab22a2c2f78cb65b622dfdb4e0aabe8f0353d4616437e736755d4640b7ac1"),
    "prepared_states": (PREP + "states.npz", "fd900adaabee2f2f4264fd71bf787ba391cffb97363a7393a1180975a58917d6"),
    "preparation_owner": (PREP + "supervisor.json", "33edbe96b0c30c453fb6b47cd830d713cb8d8920a4c19a196a187c8eabc6047a"),
    "forward": (RUN + "child-result.json", "5e6699c39de0ab165fa6396108ce8c11a9a9e4ca250ef557b7d3f16e7a1ac180"),
    "forward_owner": (RUN + "supervisor.json", "88e1fdee61b3edabd758cc76321cd4aafd468bb327989f49f360db0a868e609b"),
    "cold": (COLD + "child-result.json", "cda4f7a1b27b991827cd794c917a1a9ed9442e3b77bb6044f1d191f4f084399e"),
    "cold_owner": (COLD + "supervisor.json", "76f32ef2fb7c0d105eb49037ba3cc8522e78a47e4d39984c6107252b2c3723cd"),
    "publication": (BASE + "rook-case4-three-gram-full-rows-run01-git-blobs.json", "0999b217466ca0437d63e753a7c7886352fb9688976db45c215d5830d44ccea0"),
    "point": (POINT + "exact-01/candidate.json", "819d0e909ecf7e357404eb063ba744bc8e4c0e38e0ee63848b1712b02b248b04"),
    "point_cold": (POINT + "exact-01/cold.json", "cd59a3db0586c02a204fe8e3f23df4970b72416ff235319060a8fa1cb34e5bb8"),
    "point_terminal": (POINT + "result.json", "408da79724822a1197fbda868fe73e5de70fd36b2b55a448716be2573944df32"),
}
VARIABLES, BOXES = 1102, 191
LIMITS = {
    "preparation_seconds": 60, "preparation_cold_seconds": 60,
    "proposed_native_calls": 1, "proposed_native_seconds": 60,
    "proposed_query_owner_seconds": 120, "proposed_exact_replay_seconds": 60,
    "maximum_new_cuts": 1, "maximum_abs_integer_coefficient": 1 << 24,
    "maximum_record_bytes": 8 * 1024 * 1024, "automatic_retries": 0,
}
ROUND_SCALES = (1, 2, 4, 8, 16, 64, 256, 4096, 65536, 1048576)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def file_sha(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def ref(path):
    return {"path": str(path.resolve().relative_to(ROOT)), "sha256": file_sha(path), "bytes": path.stat().st_size}


def write(path, value):
    raw = canonical(value) + b"\n"
    assert len(raw) <= LIMITS["maximum_record_bytes"]
    if path.suffix == ".gz":
        raw = gzip.compress(raw, mtime=0)
    with path.open("xb") as stream:
        stream.write(raw)


def bound_bytes(name):
    path, digest = INPUTS[name]
    raw = (ROOT / path).read_bytes()
    assert len(raw) <= LIMITS["maximum_record_bytes"] and sha(raw) == digest, name
    return raw


def bound_json(name):
    return json.loads(bound_bytes(name))


def referenced_json(reference, expected):
    assert reference["path"] == expected
    path = ROOT / expected
    assert path.resolve().is_relative_to(ROOT)
    raw = path.read_bytes()
    assert len(raw) == reference["bytes"] and sha(raw) == reference["sha256"]
    return json.loads(raw)


def definition():
    return {"source_sha256": file_sha(Path(__file__)), "inputs": INPUTS,
            "variables": VARIABLES, "boxes": BOXES, "original_variables": 1214,
            "global_zero_premises": 112, "limits": LIMITS, "round_scales": ROUND_SCALES,
            "scope": "Necessary case4 inequality from all cold-checked final branch boxes",
            "old_trace_reason_replay": False, "large_matrix_loaded": False,
            "native_status_is_not_a_certificate": True}


def owner_gate(owner, mode, result_hash):
    assert owner["status"] == "CHILD_COMPLETE" and owner["mode"] == mode
    assert owner["source_sha256"] == FULL_SOURCE
    assert owner["exit_code"] == 0 and owner["child_reaped"] and not owner["hard_timeout"]
    assert owner["child_result"]["sha256"] == result_hash


def coverage_gate(forward, cold):
    assert forward["status"] == "COMPLETE_FULL260_PREFIX"
    assert forward["recorded"] == 260 and forward["unprocessed_UNKNOWN"] == forward["partial"] == 0
    assert forward["all260_nonpartial_terminals"] and forward["all260_attempts_recorded"]
    assert cold["status"] == "PASS" and cold["all_saved_records_checked"]
    assert cold["all260_nonpartial_branches_checked"] and cold["checked"] == 260
    assert cold["checked_partial"] == 0
    assert forward["contradictions"] == cold["checked_contradictions"] == 69
    assert forward["fixed_points"] == cold["checked_fixed_points"] == BOXES
    assert cold["prior184_contradictions_and_complete_original_branch_cover_bound"]
    assert not cold["case4_excluded"] and not cold["whole_graph_problem_resolved"]


def decimal_integer(value):
    assert type(value) in (int, str)
    if type(value) is str:
        assert value and value == str(int(value))
    return int(value)


def recover_inputs():
    """Bind completed proofs and restore boxes, without rechecking reasons."""
    import numpy as np
    assert np.__version__ == "2.3.5"
    bound_bytes("full_source")
    bound_bytes("full_source_gate")
    prepared, forward, cold = (bound_json(k) for k in ("preparation", "forward", "cold"))
    prep_owner, owner, cold_owner = (bound_json(k) for k in ("preparation_owner", "forward_owner", "cold_owner"))
    owner_gate(prep_owner, "prepare", INPUTS["preparation"][1])
    owner_gate(owner, "run", INPUTS["forward"][1])
    owner_gate(cold_owner, "replay", INPUTS["cold"][1])
    coverage_gate(forward, cold)
    assert prepared["status"] == "PREPARED_FULL260_NO_CASE_PROPAGATION"
    assert prepared["definition"]["source_sha256"] == FULL_SOURCE
    assert prepared["matrix"] == {"columns": 1102, "rows": 166020, "nonzeros": 10767637,
                                  "maximum_int64_activity_bound": 12479691283,
                                  "all_parent_array_prefixes_equal": True}
    assert prepared["all184_prior_native_contradictions_bound"] and prepared["all444_native_record_hashes_checked"]
    assert prepared["projected_only112_global_zeros"] and not prepared["former_H5_conditional_states_loaded"]
    assert all(d["definition"] == prepared["definition"] for d in (forward, cold))
    assert all(d["preparation"]["sha256"] == INPUTS["preparation"][1] for d in (owner, forward, cold))
    assert cold["forward_owner"]["sha256"] == INPUTS["forward_owner"][1]
    assert owner["records_preserved"] == forward["records"] and len(forward["records"]) == 260
    assert cold_owner["replay_checks_preserved"] == cold["checks"] and len(cold["checks"]) == 260
    publication = bound_json("publication")
    assert publication["status"] == "COMPLETE_FROZEN_TERMINAL_PUBLICATION_MAP"
    assert publication["file_count"] == 532 and publication["checked_branches"] == 260
    assert publication["checked_contradictions"] == 69 and publication["checked_fixed_point_boxes"] == BOXES
    bound_bytes("prepared_states")
    with np.load(ROOT / INPUTS["prepared_states"][0], allow_pickle=False) as archive:
        assert set(archive.files) == {"states", "original_column_ids"}
        states, originals = archive["states"], archive["original_column_ids"]
    assert states.dtype == np.dtype("int8") and states.shape == (260, VARIABLES)
    assert originals.dtype == np.dtype("uint16") and originals.shape == (VARIABLES,)
    assert np.all((states >= -1) & (states <= 1))
    ids = list(map(int, originals))
    assert ids == sorted(set(ids)) and all(0 <= a < 1214 for a in ids)
    zeros = sorted(set(range(1214)) - set(ids))
    assert len(zeros) == 112 and len(prepared["branches"]) == 260
    positions = {a: j for j, a in enumerate(ids)}
    boxes, provenance, statuses = [], [], Counter()
    for i in range(260):
        branch = prepared["branches"][i]
        rref, cref = forward["records"][i], cold["checks"][i]
        record = referenced_json(rref, RUN + f"branch-{i:03d}.json")
        check = referenced_json(cref, COLD + f"check-{i:03d}.json")
        assert branch["index"] == record["index"] == check["index"] == i
        assert record["prior_branch_id"] == check["prior_branch_id"] == branch["prior_branch_id"]
        assert record["raw_id"] == branch["raw_id"] and record["selected"] == branch["selected"]
        assert record["initial_state_sha256"] == branch["initial_state_sha256"] == sha(states[i].tobytes())
        assert check["status"] == "PASS" and check["original_record"] == rref
        status = record["terminal"]["status"]
        assert status == check["terminal"] and check["forces"] == len(record["trace"])
        assert status == "fixed_point" or status.startswith("contradiction")
        statuses["fixed_point" if status == "fixed_point" else "contradiction"] += 1
        provenance.append({"index": i, "prior_branch_id": branch["prior_branch_id"],
                           "terminal": status, "forward_record": rref, "cold_check": cref})
        if status != "fixed_point":
            continue
        state = list(map(int, states[i]))
        for rid, original, value in record["trace"]:
            assert type(rid) is type(original) is type(value) is int
            assert 0 <= rid < 166020 and original in positions and value in (0, 1)
            j = positions[original]
            assert state[j] == -1
            state[j] = value
        assert sha(bytes(v & 255 for v in state)) == record["final_state_sha256"]
        assert state.count(0) == record["final_zero_count"] and state.count(1) == record["final_one_count"]
        boxes.append({"index": i, "prior_branch_id": branch["prior_branch_id"],
                      "raw_id": branch["raw_id"], "kind": branch["kind"], "selected": branch["selected"],
                      "state": "".join("?" if v == -1 else str(v) for v in state),
                      "state_sha256": record["final_state_sha256"]})
    assert statuses == {"contradiction": 69, "fixed_point": BOXES} and len(boxes) == BOXES
    point, point_cold, terminal = (bound_json(k) for k in ("point", "point_cold", "point_terminal"))
    assert point_cold["status"] == "PASS: full exact selector point and positive t replayed"
    assert point_cold["exact_point_replayed"] and point_cold["candidate_sha256"] == INPUTS["point"][1]
    assert point_cold["registry_sha256"] == point["registry_sha256"]
    assert point_cold["point_key"] == point["exact_check"]["point_key"]
    assert terminal["latest_exact_point"] == {
        "candidate": {"path": INPUTS["point"][0], "sha256": INPUTS["point"][1]},
        "cold": {"path": INPUTS["point_cold"][0], "sha256": INPUTS["point_cold"][1]}}
    assert terminal["latest_exact_point_accepted_cut_count"] == terminal["registered_cut_count"] == 5
    assert terminal["later_cuts_not_satisfied_by_latest_point"] == 0
    assert point["matrix_binding"]["original_column_ids"] == {
        "dtype": "uint16", "shape": [VARIABLES], "sha256": sha(originals.tobytes())}
    denominator = decimal_integer(point["common_denominator"])
    extended = list(map(decimal_integer, point["extended_numerators"]))
    full = list(map(decimal_integer, point["exact_check"]["original1214_selector_numerators"]))
    assert denominator == 3461944222 and len(extended) == VARIABLES + 1 and len(full) == 1214
    numerators, floor = extended[:-1], extended[-1]
    assert 0 < floor <= min(numerators) and all(0 < n <= denominator for n in numerators)
    assert [full[a] for a in ids] == numerators and all(full[a] == 0 for a in zeros)
    assert len(terminal["registry"]) == 5
    registry_checks = []
    for r in terminal["registry"]:
        row = r["certificate"]["inequality"]
        value = sum(decimal_integer(c) * full[a] for a, c in row["terms"])
        slack = decimal_integer(row["upper"]) * denominator - value
        assert slack >= 0
        registry_checks.append({"row_key": r["row_key"], "slack_numerator": str(slack)})
    assert len(prepared["appended_rows"]) == 7
    row_checks = []
    for i, row in enumerate(prepared["appended_rows"]):
        assert all(type(a) is type(c) is int and a in positions for a, c in row["terms"])
        value = sum(c * full[a] for a, c in row["terms"])
        lo, hi = row["lower"] * denominator, row["upper"] * denominator
        assert lo <= value <= hi
        row_checks.append({"id": i, "kind": row["kind"], "terms": len(row["terms"]),
                           "value_numerator": str(value), "lower_slack_numerator": str(value - lo),
                           "upper_slack_numerator": str(hi - value)})
    return {"definition": definition(), "original_column_ids": ids, "proved_zero_columns": zeros,
            "boxes": boxes, "all260_proof_bindings": provenance,
            "point": {"denominator": str(denominator), "numerators": list(map(str, numerators)),
                      "original1214_numerators": list(map(str, full)), "t_numerator": str(floor),
                      "point_key": point_cold["point_key"], "registry_sha256": point["registry_sha256"]},
            "point_compatibility": {"status": "PASS", "registry_rows": registry_checks,
                                    "all_seven_proved_rows": row_checks},
            "coverage": {"original_patterns": 2835, "original_capacity_rejections": 2391,
                         "prior_native_contradictions": 184, "full_row_contradictions": 69,
                         "remaining_boxes": BOXES, "partial_or_missing": 0,
                         "global_new_units": 0, "feasible_boxes_claimed": False},
            "old_reason_or_fixed_point_replay_repeated": False, "large_matrix_loaded": False,
            "optimizer_calls": 0}


def linear_model(spec):
    n = len(spec["original_column_ids"])
    ptr, col, coef, lower = [0], [], [], []
    for box in spec["boxes"]:
        state = box["state"]
        assert len(state) == n and set(state) <= {"0", "1", "?"}
        terms = [(j, -1) for j, v in enumerate(state) if v == "1"]
        terms += [(n + j, 1) for j, v in enumerate(state) if v != "0"]
        terms += [(2 * n, 1)]
        assert terms == sorted(terms) and len(set(j for j, c in terms)) == len(terms)
        col.extend(j for j, c in terms)
        coef.extend(c for j, c in terms)
        ptr.append(len(col))
        lower.append(-n - state.count("1"))  # Exact redundant box minimum.
    nums = list(map(decimal_integer, spec["point"]["numerators"]))
    denominator = decimal_integer(spec["point"]["denominator"])
    return {"variables": 2 * n + 1, "rows": len(spec["boxes"]), "nonzeros": len(col),
            "variable_layout": {"p": [0, n], "n": [n, 2 * n], "t": 2 * n},
            "column_lower": [0] * (2 * n) + [-n], "column_upper": [1] * (2 * n) + [n],
            "row_pointers": ptr, "column_indices": col, "coefficients": coef,
            "row_lower": lower, "row_upper": [0] * len(spec["boxes"]),
            "objective_numerators": list(map(str, nums + [-v for v in nums] + [-denominator])),
            "objective_denominator": str(denominator), "objective_sense": "minimize"}


def box_minimum(coefficients, state):
    assert len(coefficients) == len(state) and set(state) <= {"0", "1", "?"}
    return sum(c for c, v in zip(coefficients, state) if v == "1" or (v == "?" and c < 0))


def primitive(coefficients):
    g = math.gcd(*coefficients)
    return [c // g for c in coefficients] if g else list(coefficients)


def exact_cut(spec, coefficients):
    assert len(coefficients) == len(spec["original_column_ids"])
    assert all(type(c) is int and abs(c) <= LIMITS["maximum_abs_integer_coefficient"] for c in coefficients)
    c = primitive(coefficients)
    assert spec["boxes"]
    minima = [box_minimum(c, b["state"]) for b in spec["boxes"]]
    alpha = min(minima)
    denominator = decimal_integer(spec["point"]["denominator"])
    value = sum(a * decimal_integer(n) for a, n in zip(c, spec["point"]["numerators"]))
    deficit = alpha * denominator - value
    terms = [[a, coefficient] for a, coefficient in zip(spec["original_column_ids"], c) if coefficient]
    return {"status": "EXACT_VIOLATED_BOX_HULL_CUT" if deficit > 0 else "NO_EXACT_VIOLATION",
            "projected_integer_coefficients": c, "original1214_inequality": {"terms": terms, "lower": alpha},
            "box_minima": [{"index": b["index"], "minimum": m} for b, m in zip(spec["boxes"], minima)],
            "attaining_box_indices": [b["index"] for b, m in zip(spec["boxes"], minima) if m == alpha],
            "point_value_numerator": str(value), "denominator": str(denominator),
            "deficit_numerator": str(deficit), "all_boxes_checked": len(minima),
            "candidate_sha256": INPUTS["point"][1], "case4_excluded": False,
            "valid_on_all_integer_case4_solutions": deficit > 0,
            "point_or_box_is_an_integer_solution_claimed": False}


def nearest_integer(value):
    """Nearest integer; exact halves round away from zero."""
    sign = -1 if value < 0 else 1
    q = abs(value)
    return sign * ((2 * q.numerator + q.denominator) // (2 * q.denominator))


def separate_from_hex(spec, values_hex):
    n = len(spec["original_column_ids"])
    assert len(values_hex) == 2 * n + 1
    values = []
    for text in values_hex:
        assert type(text) is str and len(text) <= 128
        number = float.fromhex(text)
        assert math.isfinite(number)
        values.append(Fraction.from_float(number))
    signed = [values[j] - values[n + j] for j in range(n)]
    attempts, seen = [], set()
    for scale in ROUND_SCALES:
        coefficients = primitive([nearest_integer(v * scale) for v in signed])
        if max(map(abs, coefficients), default=0) > LIMITS["maximum_abs_integer_coefficient"]:
            attempts.append({"scale": scale, "status": "COEFFICIENT_BOUND_REFUSAL"})
            continue
        key = tuple(coefficients)
        if key in seen:
            attempts.append({"scale": scale, "status": "DUPLICATE_INTEGER_DIRECTION"})
            continue
        seen.add(key)
        certificate = exact_cut(spec, coefficients)
        attempts.append({"scale": scale, "status": certificate["status"],
                         "deficit_numerator": certificate["deficit_numerator"],
                         "terms": len(certificate["original1214_inequality"]["terms"])})
        if certificate["status"] == "EXACT_VIOLATED_BOX_HULL_CUT":
            return {"status": "EXACT_VIOLATED_BOX_HULL_CUT", "attempts": attempts,
                    "accepted_scale": scale, "certificate": certificate}
    return {"status": "UNRESOLVED_NO_EXACT_CUT", "attempts": attempts, "certificate": None}


def controls():
    extrema, vertices_checked, overlaps, model_rows = 0, 0, 0, 0
    for n in range(1, 5):
        for state_tuple in itertools.product("01?", repeat=n):
            state = "".join(state_tuple)
            vertices = [v for v in itertools.product((0, 1), repeat=n)
                        if all(s == "?" or int(s) == a for s, a in zip(state, v))]
            for c in itertools.product((-2, -1, 0, 1, 2), repeat=n):
                assert box_minimum(c, state) == min(sum(a * b for a, b in zip(c, v)) for v in vertices)
                extrema += 1
                vertices_checked += len(vertices)
    for state in map("".join, itertools.product("01?", repeat=2)):
        lo, hi = [int(v == "1") for v in state], [int(v != "0") for v in state]
        for p0, p1, n0, n1 in itertools.product(range(3), repeat=4):
            p, minus = (p0, p1), (n0, n1)
            conservative = sum(lo[j] * p[j] - hi[j] * minus[j] for j in range(2))
            actual = box_minimum([p[j] - minus[j] for j in range(2)], state)
            assert actual - conservative == sum((hi[j] - lo[j]) * min(p[j], minus[j]) for j in range(2))
            overlaps += 1
        toy = {"original_column_ids": [3, 7], "boxes": [{"state": state}],
               "point": {"numerators": ["1", "1"], "denominator": "2"}}
        model = linear_model(toy)
        for p0, p1, n0, n1 in itertools.product((0, 1), repeat=4):
            for t in range(-2, 3):
                v = [p0, p1, n0, n1, t]
                activity = sum(a * v[j] for a, j in zip(model["coefficients"], model["column_indices"]))
                assert activity == t - sum(lo[j] * v[j] for j in range(2)) + sum(hi[j] * v[2 + j] for j in range(2))
                assert model["row_lower"][0] <= activity
                model_rows += 1
    toy = {"original_column_ids": [1, 4, 8], "boxes": [{"index": 2, "state": "0?0"}, {"index": 5, "state": "100"}],
           "point": {"numerators": ["2", "1", "0"], "denominator": "2"}}
    negative = exact_cut(toy, [-1, -1, 0])
    assert negative["original1214_inequality"] == {"terms": [[1, -1], [4, -1]], "lower": -1}
    assert negative["deficit_numerator"] == "1"
    proposal = [0.0, 0.0, 0.0, 1.0, 1.0, 0.0, -1.0]
    assert separate_from_hex(toy, [x.hex() for x in proposal])["certificate"] == negative
    toy["point"] = {"numerators": ["1", "1", "0"], "denominator": "2"}
    for c in itertools.product((-2, -1, 0, 1, 2), repeat=3):
        assert decimal_integer(exact_cut(toy, list(c))["deficit_numerator"]) <= 0
    for a, b, expected in [(1, 2, 1), (-1, 2, -1), (3, 2, 2), (-3, 2, -2), (1, 3, 0), (-1, 3, 0)]:
        assert nearest_integer(Fraction(a, b)) == expected
    huge = 1 << 80
    assert nearest_integer(Fraction(2 * huge + 1, 2)) == huge + 1
    return {"status": "PASS", "literal_box_extrema": extrema, "literal_vertices_checked": vertices_checked,
            "overlap_identities": overlaps, "literal_native_row_orientations": model_rows,
            "convex_combination_no_false_cuts": 125, "signed_positive_gap_control": True,
            "exact_dyadic_rounding_and_large_integer_controls": True, "optimizer_calls": 0}


def runtime_inventory():
    result = {"python": platform.python_version(), "implementation": platform.python_implementation(),
              "byteorder": sys.byteorder, "packages": {}}
    wanted = {"highspy": ("highspy/__init__.py", "highspy/highs.py", "highspy/_core."),
              "numpy": ("numpy/__init__.py", "numpy/_core/_multiarray_umath.")}
    for name, suffixes in wanted.items():
        dist = importlib.metadata.distribution(name)
        files = []
        for relative in dist.files:
            text = str(relative)
            if text in suffixes or any(text.startswith(prefix) and text.endswith(".so") for prefix in suffixes):
                path = Path(dist.locate_file(relative))
                files.append({"installed_path": str(path.resolve()), "sha256": file_sha(path), "bytes": path.stat().st_size})
        assert len(files) == (3 if name == "highspy" else 2)
        result["packages"][name] = {"version": dist.version, "files": files}
    assert result["packages"]["numpy"]["version"] == "2.3.5"
    assert result["packages"]["highspy"]["version"] == "1.16.0"
    return result


def prepare(directory):
    started = time.monotonic()
    control = controls()
    spec = recover_inputs()
    model = linear_model(spec)
    runtime = runtime_inventory()
    assert model["variables"] == 2205 and model["rows"] == BOXES
    assert len(model["column_indices"]) == model["nonzeros"] < 422000
    assert time.monotonic() - started <= LIMITS["preparation_seconds"]
    write(directory / "specification.json.gz", spec)
    write(directory / "model.json.gz", model)
    report = {"status": "PREPARED_191_BOX_SEPARATOR_NO_OPTIMIZER", "definition": definition(),
              "specification": ref(directory / "specification.json.gz"), "specification_canonical_sha256": sha(canonical(spec)),
              "model": ref(directory / "model.json.gz"), "model_canonical_sha256": sha(canonical(model)),
              "columns": model["variables"], "rows": model["rows"], "nonzeros": model["nonzeros"],
              "controls": control, "runtime": runtime, "coverage": spec["coverage"],
              "point_compatibility": spec["point_compatibility"], "original_coordinate_map_sha256": sha(canonical(spec["original_column_ids"])),
              "proposed_native_options": {"threads": 1, "solver": "simplex", "time_limit": 60.0,
                                           "random_seed": 0, "parallel": "off"},
              "solver_object_created": False, "native_calls": 0, "old_reason_replay_repeated": False,
              "large_matrix_loaded": False, "seconds": time.monotonic() - started}
    write(directory / "preparation.json", report)
    return report


def load_preparation(path):
    prep = json.loads(path.read_bytes())
    assert prep["status"] == "PREPARED_191_BOX_SEPARATOR_NO_OPTIMIZER"
    assert canonical(prep["definition"]) == canonical(definition()) and prep["controls"]["status"] == "PASS"
    objects = []
    for name in ("specification", "model"):
        reference = prep[name]
        expected = path.parent / (name + ".json.gz")
        assert reference == ref(expected)
        obj = json.loads(gzip.decompress(expected.read_bytes()))
        assert sha(canonical(obj)) == prep[name + "_canonical_sha256"]
        objects.append(obj)
    spec, model = objects
    assert model == linear_model(spec)
    return prep, spec, model


def replay_preparation(preparation, directory):
    started = time.monotonic()
    prep, saved, model = load_preparation(preparation)
    actual = recover_inputs()
    assert canonical(actual) == canonical(saved) and linear_model(actual) == model
    assert runtime_inventory() == prep["runtime"]
    assert time.monotonic() - started <= LIMITS["preparation_cold_seconds"]
    report = {"status": "PASS_PREPARATION_AND_ALL191_SAVED_BOXES", "preparation": ref(preparation),
              "source_sha256": file_sha(Path(__file__)), "specification_canonical_sha256": sha(canonical(actual)),
              "model_canonical_sha256": sha(canonical(model)), "all260_terminal_bindings_checked": True,
              "all191_final_box_states_restored": True, "point_map_and_seven_rows_checked": True,
              "old_trace_reason_or_fixed_point_replay_repeated": False, "large_matrix_loaded": False,
              "optimizer_calls": 0, "seconds": time.monotonic() - started}
    write(directory / "replay.json", report)
    return report


def main():
    assert not sys.flags.optimize
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--directory", type=Path, required=True)
    parser.add_argument("--preparation", type=Path)
    args = parser.parse_args()
    args.directory.mkdir(parents=True, exist_ok=False)
    result = prepare(args.directory) if args.mode == "prepare" else replay_preparation(args.preparation, args.directory)
    print(json.dumps({k: v for k, v in result.items() if k in ("status", "columns", "rows", "nonzeros", "seconds")}, sort_keys=True))


if __name__ == "__main__":
    main()
