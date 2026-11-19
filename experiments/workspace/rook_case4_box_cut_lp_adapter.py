"""Single-round LP kernels with a distinct exact branch-box proof kind.

The numerical, basis, finite-box and cold functions are source-identical to
the reviewed v4 implementations, apart from registry proof dispatch and
accurate acceptance metadata. No old module is modified. This module has
no scan, multi-round cycle, or CLI production entry point.
"""
import argparse
import gzip
import hashlib
from itertools import combinations
import json
from math import gcd
from pathlib import Path
import subprocess
import sys
import time

import rook_case4_parity_cycle_exact as exact
import rook_case4_face112_h3_weighted_parity as weighted
import rook_case4_box_cut_lp_proof as box_proof

ROOT = Path(__file__).resolve().parents[2]
LOGS = "experiments/logs/grids-and-triangles/"
SOURCES = {
    "box_proof": ("experiments/workspace/rook_case4_box_cut_lp_proof.py", "091946b8444aa1c3b49f2955b076e00f7241a96926a9b9d2a4afb210fe4067c3"),
    "exact": ("experiments/workspace/rook_case4_parity_cycle_exact.py",
              "2f10a42f546623cb1840d228101537e6f4f4bc584776407140ae0c36b08c99b7"),
    "weighted": ("experiments/workspace/rook_case4_face112_h3_weighted_parity.py",
                 "c38a4ec1d95eca5382e34c7182af38c980bf61785585207dd314a1a6546b5756"),
    "basis": ("experiments/workspace/rook_case4_weighted_parity_basis.py",
              "bb507d8d97a064bd8c56aac763b44e026c50598048b213db9399662eaaec7415"),
    "parity": ("experiments/workspace/rook_case4_parity_polytope.py",
               "048df509b05601f15d6cb4230750b36d221276cce66e625b0cf9c720ecb89062"),
    "generation": ("experiments/workspace/rook_case4_face112_weighted_parity_generation.py",
                   "fb4c4b853708740e1a1726cb4455a5c82a7ae3659439407f4a00a33c67c71ec7"),
    "finite_box": ("experiments/workspace/rook_case4_finite_box_certificates.py",
                   "353db5bb5d2c6b3d11b18889a853af364ea3d6c4d04bb78c56f0c4ee89d86de7"),
}
INPUTS = {
    "native": (LOGS+"complement-rook-35core-case0004-native-cpsat-model.json",
               "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "old_basis": (LOGS+"rook-case4-face112-parity-preparation01/basis.json.gz",
                  "ad03018a2bb30dfb79fb126b76aa9863b16217eeb42f0b1e78fdaabde610c00d"),
    "old_span_cold": (LOGS+"rook-case4-face112-h3-weighted-parity-run01-replay.json",
                      "1cc5086c7d1b5102c9df8825127e8dfd06317c03517402cb85fdf49678069544"),
    "model": (LOGS+"rook-case4-face112-weighted-parity-model01/model.json",
              "c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3"),
    "arrays": (LOGS+"rook-case4-face112-weighted-parity-model01/arrays.npz",
               "59a06470793e6959a67ae30dfb29ecf0de4c8aa74661e1335d7676aa612c1e7e"),
    "model_cold": (LOGS+"rook-case4-face112-weighted-parity-model01-cold-replay.json",
                   "567185c755134fcf7c15bb7be762bb2a70a503254259b2eb44a92f91abb39156"),
    "point": (LOGS+"rook-case4-face112-weighted-parity-basis-run01/candidate.json",
              "3cd4d391e5b372f6ff0d2df11ebd16fccec1b7122527864fef76e33eae72312b"),
    "point_cold": (LOGS+"rook-case4-face112-weighted-parity-basis-run01-replay.json",
                   "e6b8cacf16a38b4529f73d96aa7212ac6f71244846f8d0f38973cd865667c0d4"),
    "known_numeric_control": (LOGS+"rook-case4-face112-weighted-parity-generation-run01/iteration-00-numeric.json.gz",
                              "b024197a41afb7412b5010deafcf136cbf1bf3ca1b08aed2ffd1965e4cb9ee00"),
    "known_basis_control": (LOGS+"rook-case4-face112-weighted-parity-basis-preparation01/proposal.json.gz",
                            "ddf80d0fc6c9061ce0b76fb92bdc6e0a7143a50e2f3c615145d8dc5d40177dcc"),
}
SELECTORS, VARIABLES = 1102, 1103
SELECTOR_ROWS, PREFIX_ROWS, PREFIX_NNZ = 166013, 167115, 10769496
NATIVE_ROWS, COVER_END = 1960, 166004
LIMITS = {
    "fresh_point_scans": 3, "new_LP_rounds": 2,
    "total_native_calls": 60, "native_calls_per_round": 30,
    "cumulative_native_seconds": 120,
    "numerical_phase_seconds": 180, "total_numerical_phase_seconds": 360,
    "scan_seconds": 60, "scan_cold_seconds": 60,
    "exact_seconds": 60, "exact_cold_seconds": 60,
    "maximum_declared_stage_seconds": 960,
    "whole_cycle_hard_seconds": 1080,
    "maximum_new_cuts": 64, "maximum_scan_transcript_bytes": 64 << 20,
    "scan_result_reserve_bytes": 1 << 20, "raw_words_per_scan": 123123,
    "covers_per_native_call": 512, "added_covers_per_round": 29*512,
    "violation_tolerance": 1e-7, "threads": 1,
    "maximum_dynamic_exact_dimension": 512,
    "maximum_exact_output_bits": 4096,
    "automatic_retries": 0,
}
basis, parity = weighted.basis, weighted.parity
sha, canonical, tick = exact.sha, exact.canonical, exact.tick


def save(path, value):
    raw = json.dumps(value, indent=2, allow_nan=False).encode()+b"\n"
    temporary = path.with_name(path.name+".partial")
    temporary.write_bytes(raw)
    temporary.replace(path)

def save_gzip(path, value):
    raw = canonical(value)
    compressed = gzip.compress(raw, mtime=0)
    with path.open("xb") as stream:
        stream.write(compressed)
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(compressed),
            "raw_sha256": sha(raw), "bytes": len(compressed)}

def read_record(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if str(path).endswith(".gz") else raw)

def record_ref(path):
    path = path.resolve()
    return {"path": str(path.relative_to(ROOT)), "sha256": sha(path.read_bytes())}

def checked_ref(ref):
    path = ROOT/ref["path"]
    raw = path.read_bytes()
    assert sha(raw) == ref["sha256"]
    return read_record(path)

def source_bindings():
    refs = {}
    for key, (path, expected) in SOURCES.items():
        actual = sha((ROOT/path).read_bytes())
        assert expected is not None and actual == expected, ("source", key)
        refs[key] = {"path": path, "sha256": actual}
    assert Path(exact.__file__).resolve() == ROOT/SOURCES["exact"][0]
    assert Path(weighted.__file__).resolve() == ROOT/SOURCES["weighted"][0]
    return {"cycle_source_sha256": sha(Path(__file__).read_bytes()),
            "helpers": refs, "input_bindings": {k: list(v) for k, v in INPUTS.items()}}

def read_input(name):
    path, expected = INPUTS[name]
    raw = (ROOT/path).read_bytes()
    assert sha(raw) == expected, ("input", name)
    return json.loads(gzip.decompress(raw) if path.endswith(".gz") else raw)

def point_data(ref):
    point, cold = checked_ref(ref["candidate"]), checked_ref(ref["cold"])
    assert cold["status"].startswith("PASS:") and cold["exact_point_replayed"]
    assert cold["candidate_sha256"] == ref["candidate"]["sha256"]
    nums = list(map(int, point["exact_check"]["original1214_selector_numerators"]))
    den = int(point["common_denominator"])
    assert len(nums) == 1214 and den > 0 and all(0 <= v <= den for v in nums)
    return nums, den

def domain(deadline):
    source_bindings()
    native, model = read_input("native"), read_input("model")
    inventory = native["primary_inventory"]
    assert sha(canonical(inventory).rstrip(b"\n")) == native["primary_inventory_sha256"]
    gram = inventory["Gram_rows"]
    assert len(gram) == 630 and inventory["primary_variables"] == 1214
    assert [(i, j) for i, j, q, s in gram] == [(i, j) for i in range(35) for j in range(i, 35)]
    zeros = model["fixed_zero_columns"]
    assert len(zeros) == 112 and zeros == sorted(set(zeros))
    kept = [j for j in range(1214) if j not in set(zeros)]
    assert len(kept) == SELECTORS
    active = sum(1 << j for j in kept)
    masks, quotas = [], []
    for i, j, q, support in gram:
        assert type(q) is int and q >= 0 and support == sorted(set(support))
        assert all(type(a) is int and 0 <= a < 1214 for a in support)
        masks.append(sum(1 << a for a in support)); quotas.append(q)
    old = read_input("old_basis")
    assert old["known_zero_columns"] == zeros and len(old["basis"]) == 286
    span = read_input("old_span_cold")
    assert span["status"].startswith("PASS:") and span["complete_declared_families"]
    cold = read_input("model_cold")
    assert cold["status"].startswith("PASS:") and cold["model_sha256"] == INPUTS["model"][1]
    rows = []
    for i, item in enumerate(old["basis"]):
        tick(deadline)
        assert item["basis_index"] == i
        witness = int(item["lift"]["original_native_row_combination_hex"], 16)
        assert 0 < witness < 1 << 630
        mask, rhs = 0, 0
        for j in basis.sites(witness):
            mask ^= masks[j]; rhs ^= quotas[j] % 2
        assert hex(mask) == item["lift"]["full_original_parity_hex"]
        assert hex(mask & active) == item["lift"]["active_original_support_hex"]
        assert rhs == item["lift"]["parity_rhs"]
        rows.append((mask & active, rhs, witness))
    return {"gram": gram, "gram_masks": masks, "quotas": quotas, "zeros": zeros,
            "kept": kept, "active": active, "rows": rows, "model": model}

def with_point(data, ref):
    nums, den = point_data(ref)
    assert all(nums[a] == 0 for a in data["zeros"])
    assert all(nums[a] > 0 for a in data["kept"])
    for _, _, quota, support in data["gram"]:
        assert sum(nums[a] for a in support) == quota*den
    weights = {j: min(nums[j], den-nums[j]) for j in data["kept"]}
    return dict(data, point=nums, denominator=den,
                point_key=exact.point_key(nums, den),
                orders=[sorted(data["kept"], key=lambda j: (-weights[j], j)),
                        sorted(data["kept"], key=lambda j: (-weights[j], -j))])

def validate_registry(data, registry, deadline):
    assert len(registry) <= LIMITS["maximum_new_cuts"]
    assert registry == box_proof.frozen_registry() and len(registry) == 6
    keys = []
    for entry in registry:
        tick(deadline)
        if entry.get("proof_kind") == box_proof.PROOF_KIND:
            checked = box_proof.verify_entry(entry, data["gram"], data["zeros"], deadline)
        else:
            assert "proof_kind" not in entry
            nums, den = point_data(entry["source_point"])
            checked = exact.verify_cut(entry["certificate"], data["gram"], data["zeros"], nums, den, deadline)
        key = exact.row_key(checked["inequality"])
        assert entry["row_key"] == key
        keys.append(key)
    assert len(keys) == len(set(keys))

def load_matrix(data, registry, deadline):
    """Read the frozen prefix; no original cover-support reconstruction."""
    import rook_case4_face112_weighted_parity_generation as old
    assert sha(Path(old.__file__).read_bytes()) == SOURCES["generation"][1]
    assert sha((ROOT/INPUTS["arrays"][0]).read_bytes()) == INPUTS["arrays"][1]
    loaded_model, loaded_base, prefix, pool = old.load_inputs(ROOT/INPUTS["model"][0], ROOT/INPUTS["arrays"][0])
    del loaded_model, loaded_base
    assert len(prefix["row_lower"]) == PREFIX_ROWS and len(prefix["coefficients"]) == PREFIX_NNZ
    assert list(map(int, prefix["original_column_ids"])) == data["kept"]
    assert pool == list(range(NATIVE_ROWS, COVER_END))
    validate_registry(data, registry, deadline)
    rows = [entry["certificate"]["inequality"] for entry in registry]
    arrays = exact.append_rows(prefix, rows, prefix["original_column_ids"])
    return old, arrays, pool

def checked_state(path, deadline):
    state = read_record(path)
    assert state["source_bindings"] == source_bindings()
    assert state["limits"] == LIMITS
    data = with_point(domain(deadline), state["point"])
    assert data["point_key"] == state["point_key"]
    validate_registry(data, state["cuts"], deadline)
    assert state["scan_cut_slots"] == LIMITS["maximum_new_cuts"]-len(state["cuts"])
    assert 0 < state["scan_byte_allowance"] <= LIMITS["maximum_scan_transcript_bytes"]
    assert 0 <= state["native_seconds_before"]  # Actual timer overshoot is retained; no later native call is allowed after the budget.
    return state, data

def numerical_scan(matrix, arrays, values, pool, active):
    import numpy as np
    from rook_case4_cover_generation import choose_rows
    point = np.asarray(values, dtype=float)
    assert point.shape == (VARIABLES,) and np.all(np.isfinite(point))
    activity = matrix @ point
    violation = np.maximum(np.maximum(arrays["row_lower"]-activity, activity-arrays["row_upper"]), 0.0)
    assert np.all(np.isfinite(violation))
    selected, count = choose_rows(violation, pool, active, LIMITS["covers_per_native_call"],
                                  LIMITS["violation_tolerance"])
    return {"rows_scanned": len(arrays["row_lower"]),
            "nonzeros_scanned": len(arrays["coefficients"]),
            "maximum_violation": float(np.max(violation)),
            "violations_above_tolerance": int(np.count_nonzero(violation > LIMITS["violation_tolerance"])),
            "unseen_cover_violations": count, "selected_cover_rows": selected,
            "numeric_feasibility_is_not_exact": True}

def float_matrix(arrays):
    import numpy as np
    from scipy.sparse import csr_matrix
    for name in ("coefficients", "row_lower", "row_upper"):
        assert np.all(np.abs(arrays[name]) < 2**53)
    return csr_matrix((arrays["coefficients"].astype(float), arrays["column_indices"],
                       arrays["row_pointers"]), shape=(len(arrays["row_lower"]), VARIABLES))

def initial_rows(registry_count, carried):
    assert carried == sorted(set(carried))
    assert all(NATIVE_ROWS <= r < COVER_END for r in carried)
    return list(range(NATIVE_ROWS))+list(range(COVER_END, PREFIX_ROWS+registry_count))+carried

def numeric_stage(state_path, directory):
    import highspy
    start = time.monotonic(); deadline = start+LIMITS["numerical_phase_seconds"]
    result = {"status": "RUNNING", "state": record_ref(state_path), "iterations": [],
              "native_calls": 0, "native_seconds": 0.0, "complete": False,
              "automatic_retry": False, "optimizer_outcomes_are_not_certificates": True}
    save(directory/"result.json", result)
    try:
        state, data = checked_state(state_path, deadline)
        old, arrays, pool = load_matrix(data, state["cuts"], deadline)
        assert state["native_seconds_before"] < LIMITS["cumulative_native_seconds"]
        result["matrix_binding"] = exact.matrix_binding(arrays)
        result["registry_sha256"] = sha(canonical(state["cuts"]))
        result["runtime_binding"] = old.runtime_binding()
        flight = checked_ref(state["native_preflight"])
        assert flight["source_bindings"] == source_bindings()
        assert result["runtime_binding"] == flight["runtime_binding"], "native runtime differs from frozen preflight"
        matrix = float_matrix(arrays)
        solver = highspy.Highs()
        for name, value in old.OPTIONS+[["log_file", str(directory/"highs.log")]]:
            assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
        rows = initial_rows(len(state["cuts"]), state["carried_covers"])
        active = set(rows)
        old.set_model(solver, matrix, arrays, rows, VARIABLES)
        added = 0
        result["bootstrap_seconds"] = time.monotonic()-start
        for call in range(LIMITS["native_calls_per_round"]):
            remaining = min(LIMITS["cumulative_native_seconds"]-state["native_seconds_before"]-result["native_seconds"],
                            deadline-time.monotonic())
            if remaining <= 0:
                result["stop_reason"] = "cumulative native or phase time exhausted"
                break
            before = time.monotonic()-start
            numeric = old.native_once(solver, rows, remaining, call)
            numeric["phase_elapsed_before_call"] = before
            ref = save_gzip(directory/f"numeric-{call:02d}.json.gz", numeric)
            item = {"numeric": ref, "scan": None, "added_cover_rows": []}
            result["iterations"].append(item)
            result["native_calls"] += 1
            result["native_seconds"] += numeric["solver_and_existing_ray_seconds"]
            result["status"] = "native result durable; full pool check pending"
            save(directory/"result.json", result)
            if not numeric["optimal"] or not numeric["solution_value_valid"]:
                result["stop_reason"] = "nonoptimal/infeasible result; no native retry"
                break
            values = numeric["column_values"]
            if len(values) != VARIABLES or any(v is None for v in values):
                result["stop_reason"] = "invalid numerical proposal"
                break
            scan = numerical_scan(matrix, arrays, values, pool, active)
            item["scan"] = scan
            additions = scan["selected_cover_rows"]
            if not additions:
                result["stop_reason"] = "no uninserted cover violation; exact acceptance required"
                break
            if (call+1 == LIMITS["native_calls_per_round"] or time.monotonic() >= deadline or
                state["native_seconds_before"]+result["native_seconds"] >= LIMITS["cumulative_native_seconds"]):
                result["stop_reason"] = "budget reached with unresolved cover violations"
                break
            assert not active.intersection(additions)
            assert added+len(additions) <= LIMITS["added_covers_per_round"]
            old.append_rows(solver, matrix, arrays, additions)
            rows.extend(additions); active.update(additions); added += len(additions)
            item["added_cover_rows"] = additions
            save(directory/"result.json", result)
        result["carried_covers_after"] = sorted(r for r in active if NATIVE_ROWS <= r < COVER_END)
        result["complete"] = True
        result["status"] = "TERMINAL: saved numerical proposals only"
    except Exception as error:
        result.update(status="ERROR: no unchecked outcome promoted", reason_type=type(error).__name__, reason=str(error))
    finally:
        result["seconds"] = time.monotonic()-start
        save(directory/"result.json", result)
    return result

def numeric_records(state, arrays):
    result = checked_ref(state["numerical_result"])
    parent_state = checked_ref(result["state"])
    for key in ("source_bindings", "limits", "point", "point_key", "cuts",
                "native_seconds_before", "carried_covers", "native_preflight"):
        assert parent_state[key] == state[key], ("numeric state ancestry", key)
    assert result["complete"] and result["matrix_binding"] == exact.matrix_binding(arrays)
    assert result["registry_sha256"] == sha(canonical(state["cuts"]))
    assert 0 < len(result["iterations"]) <= LIMITS["native_calls_per_round"]
    records = [checked_ref(item["numeric"]) for item in result["iterations"]]
    return result, records

def expanded_numeric(record, rows):
    active = record["active_original_row_ids"]
    assert len(active) == len(set(active)) and all(0 <= r < rows for r in active)
    numeric = {k: record[k] for k in ("optimal", "numerically_infeasible", "solution_value_valid",
                                     "solution_dual_valid", "column_values")}
    for name in ("dual_ray", "row_duals"):
        values = record[name]
        if values is None or len(values) != len(active) or any(v is None for v in values):
            numeric[name] = None
        else:
            full = [0.0]*rows
            for r, value in zip(active, values):
                full[r] = value
            numeric[name] = full
    return numeric

def finite_bound(arrays, numeric, deadline):
    import rook_case4_finite_box_certificates as box
    values = (numeric.get("dual_ray") if numeric["numerically_infeasible"] else
              numeric.get("row_duals") if numeric["optimal"] and numeric["solution_dual_valid"] else None)
    if values is None:
        return None, []
    objective = not numeric["numerically_infeasible"]
    attempts = []
    for multipliers, gamma, proposal in box.integer_candidates(values, objective, deadline):
        tick(deadline)
        check = box.check_bound(arrays, VARIABLES, multipliers, gamma, min(60, deadline-time.monotonic()))
        B = int(check["objective_upper_bound_numerator"])
        attempts.append({"proposal": proposal, "gamma": str(gamma), "B": str(B), "support": len(multipliers)})
        if B > 0 or (B == 0 and gamma == 0):
            continue
        implications = None
        if B == 0:
            implications = box.face_implications(check, multipliers, SELECTOR_ROWS, arrays["original_column_ids"])
            if implications["positive_t_residual_contradicts_original_feasibility"]:
                gamma = 0
                check = box.check_bound(arrays, VARIABLES, multipliers, 0, min(60, deadline-time.monotonic()))
                B = int(check["objective_upper_bound_numerator"])
                assert B < 0
                implications = None
        stable = {k: v for k, v in check.items() if k != "check_seconds"}
        return {"kind": "exact_infeasibility" if B < 0 else "exact_zero_face",
                "multipliers": [[i, str(v)] for i, v in multipliers], "gamma": str(gamma),
                "check": stable, "face_implications": implications}, attempts
    return None, attempts

def inspect_point(data, arrays, registry, nums, den, deadline):
    import rook_case4_finite_box_certificates as box
    import rook_case4_complete_lp_recovery as recovery
    assert len(nums) == VARIABLES and den > 0 and nums[-1] > 0
    assert den.bit_length() <= LIMITS["maximum_exact_output_bits"]
    assert all(type(v) is int and abs(v).bit_length() <= LIMITS["maximum_exact_output_bits"] for v in nums)
    check = box.check_point(arrays, VARIABLES, nums, den, min(60, deadline-time.monotonic()))
    assert check["strictly_positive_t"]
    restored = [0]*1214
    for j, a in enumerate(arrays["original_column_ids"]):
        restored[int(a)] = nums[j]
    assert all(restored[a] == 0 for a in data["zeros"])
    assert all(restored[a] > 0 for a in data["kept"])
    inventory, metadata, cover_bytes = recovery.checked_inputs(ROOT)
    original = recovery.original_rows(inventory)
    assert len(original) == 2271
    for i, row in enumerate(original):
        if i % 64 == 0: tick(deadline)
        value = sum(c*restored[a] for a, c in row["terms"])
        assert row["lower"]*den <= value <= row["upper"]*den, ("original native", i)
    for i in range(178533):
        if i % 256 == 0: tick(deadline)
        target, bits = recovery.registry_entry(cover_bytes, i)
        assert sum(restored[a] for a in recovery.members(bits)) >= restored[target], ("original cover", i)
    model = data["model"]
    for support in model["integer_cover_live_original_supports"]:
        assert sum(restored[a] for a in support) == den
    for a, b in model["added_pair_rows"]:
        assert restored[a]+restored[b] <= den
    assert den <= sum(restored[a] for a in model["third_parity_cover_original_support"]) <= 3*den
    for row in model["weighted_parity_rows"]:
        value = sum(c*restored[a] for a, c in row["terms"])
        assert row["lower"]*den <= value <= row["upper"]*den
    for entry in registry:
        row = entry["certificate"]["inequality"]
        assert sum(c*restored[a] for a, c in row["terms"]) <= row["upper"]*den
    assert sum(restored) == 64*den
    tick(deadline)
    return {"status": "PASS: every complete-pool and original-coordinate obligation",
            "full_face_rows_checked": len(arrays["row_lower"]),
            "original_native_rows_checked": 2271, "original_coordinate_covers_checked": 178533,
            "fixed_zero_selectors": 112, "positive_surviving_selectors": SELECTORS,
            "all_parity_equalities_pair_AMOs_H3_and_inherited_weighted_cuts_checked": True,
            "appended_signed_parity_rows_checked": sum("proof_kind" not in e for e in registry),
            "appended_box_cover_rows_checked": sum(e.get("proof_kind") == box_proof.PROOF_KIND for e in registry),
            "appended_proved_rows_checked": len(registry),
            "t_numerator": str(nums[-1]), "common_denominator": str(den),
            "original1214_selector_numerators": list(map(str, restored)),
            "point_key": exact.point_key(restored, den),
            "binary_incidence_or_graph_claimed": False}

def exact_stage(state_path, directory):
    started = time.monotonic(); deadline = started+LIMITS["exact_seconds"]
    result = {"status": "UNKNOWN: exact stage unfinished", "state": record_ref(state_path),
              "exact_point_found": False, "exact_certificate_found": False,
              "optimizer_calls": 0, "linear_solve_calls": 0}
    save(directory/"result.json", result)
    try:
        state, data = checked_state(state_path, deadline)
        old, arrays, pool = load_matrix(data, state["cuts"], deadline)
        numeric_result, records = numeric_records(state, arrays)
        last = records[-1]
        numeric = expanded_numeric(last, len(arrays["row_lower"]))
        certificate, attempts = finite_bound(arrays, numeric, deadline)
        result["bound_attempts"] = attempts
        if certificate is not None:
            assert {r for r, v in certificate["multipliers"]} <= set(last["active_original_row_ids"])
            certificate["matrix_binding"] = exact.matrix_binding(arrays)
            certificate["registry_sha256"] = sha(canonical(state["cuts"]))
            result["certificate"] = save_gzip(directory/"certificate.json.gz", certificate)
            result.update(status="EXACT_CERTIFICATE: independent arithmetic replay pending",
                          exact_certificate_found=True, kind=certificate["kind"])
        else:
            proposal = exact.basis_proposal(arrays, last, SELECTORS, SELECTOR_ROWS,
                                             LIMITS["maximum_dynamic_exact_dimension"], deadline)
            result["basis_proposal"] = save_gzip(directory/"basis-proposal.json.gz", proposal)
            result["linear_solve_calls"] = 1
            save(directory/"result.json", result)
            nums, den, solve = exact.solve_proposal(proposal, LIMITS["maximum_exact_output_bits"], deadline)
            result["linear_solve"] = solve
            candidate = {"status": "CANDIDATE: complete exact acceptance pending",
                         "common_denominator": str(den), "extended_numerators": list(map(str, nums))}
            save(directory/"candidate.json", candidate)
            check = inspect_point(data, arrays, state["cuts"], nums, den, deadline)
            candidate.update(status="EXACT_FULL_SELECTOR_POINT: independent replay pending", exact_check=check,
                             registry_sha256=sha(canonical(state["cuts"])),
                             matrix_binding=exact.matrix_binding(arrays))
            save(directory/"candidate.json", candidate)
            result.update(status="EXACT_FULL_SELECTOR_POINT: independent replay pending",
                          exact_point_found=True, candidate=record_ref(directory/"candidate.json"))
    except Exception as error:
        result.update(status="UNKNOWN: exact reconstruction or acceptance failed",
                      error_type=type(error).__name__, reason=str(error))
    finally:
        result["seconds"] = time.monotonic()-started
        save(directory/"result.json", result)
    return result

def replay_numeric(state, arrays, pool, deadline):
    result, records = numeric_records(state, arrays)
    assert result["runtime_binding"] == checked_ref(state["native_preflight"])["runtime_binding"]
    matrix = float_matrix(arrays)
    rows = initial_rows(len(state["cuts"]), state["carried_covers"])
    active = set(rows)
    spent, added = 0.0, 0
    for i, (item, numeric) in enumerate(zip(result["iterations"], records)):
        tick(deadline)
        assert numeric["call_index"] == i and numeric["active_original_row_ids"] == rows
        request = numeric["requested_solver_and_existing_ray_seconds"]
        assert 0 < request <= LIMITS["cumulative_native_seconds"]-state["native_seconds_before"]-spent+1e-9
        assert request <= LIMITS["numerical_phase_seconds"]-numeric["phase_elapsed_before_call"]+1e-9
        spent += numeric["solver_and_existing_ray_seconds"]
        if item["scan"] is not None:
            assert numeric["optimal"] and numeric["solution_value_valid"]
            assert numerical_scan(matrix, arrays, numeric["column_values"], pool, active) == item["scan"]
        additions = item["added_cover_rows"]
        if additions:
            assert i+1 < len(records)
            assert additions == item["scan"]["selected_cover_rows"]
            assert not active.intersection(additions) and len(additions) <= LIMITS["covers_per_native_call"]
            rows.extend(additions); active.update(additions); added += len(additions)
            assert added <= LIMITS["added_covers_per_round"]
    assert spent == result["native_seconds"] and len(records) == result["native_calls"]
    assert result["carried_covers_after"] == sorted(r for r in active if NATIVE_ROWS <= r < COVER_END)
    return {"native_calls_checked": len(records), "native_seconds_recorded": spent,
            "native_optimizer_repeated": False, "exact_prefix_and_pool_scans_replayed": True}

def exact_cold(state_path, directory):
    import rook_case4_finite_box_certificates as box
    start = time.monotonic(); deadline = start+LIMITS["exact_cold_seconds"]
    state, data = checked_state(state_path, deadline)
    old, arrays, pool = load_matrix(data, state["cuts"], deadline)
    result = read_record(directory/"result.json")
    assert result["state"] == record_ref(state_path) and result["optimizer_calls"] == 0
    assert 0 <= result["linear_solve_calls"] <= 1
    numerical = replay_numeric(state, arrays, pool, deadline)
    report = {"status": "PASS: terminal bindings; no mathematical outcome accepted",
              "state": record_ref(state_path), "result": record_ref(directory/"result.json"),
              "exact_point_replayed": False, "exact_certificate_replayed": False,
              "numerical_prefix_replay": numerical, "linear_solve_calls": 0, "optimizer_calls": 0}
    if result["exact_certificate_found"]:
        certificate = checked_ref(result["certificate"])
        assert certificate["matrix_binding"] == exact.matrix_binding(arrays)
        assert certificate["registry_sha256"] == sha(canonical(state["cuts"]))
        multipliers = [[i, int(v)] for i, v in certificate["multipliers"]]
        gamma = int(certificate["gamma"])
        check = box.check_bound(arrays, VARIABLES, multipliers, gamma, min(60, deadline-time.monotonic()))
        assert {k: v for k, v in check.items() if k != "check_seconds"} == certificate["check"]
        B = int(check["objective_upper_bound_numerator"])
        if certificate["kind"] == "exact_infeasibility":
            assert B < 0
            assert certificate["face_implications"] is None
        else:
            assert certificate["kind"] == "exact_zero_face" and gamma > 0 and B == 0
            implication = box.face_implications(check, multipliers, SELECTOR_ROWS, arrays["original_column_ids"])
            # Integer-key dictionaries become string-key dictionaries in JSON.
            assert json.loads(json.dumps(implication)) == certificate["face_implications"]
            assert not implication["positive_t_residual_contradicts_original_feasibility"]
        report.update(status="PASS: exact finite-box certificate replayed",
                      exact_certificate_replayed=True, kind=certificate["kind"])
    elif result["exact_point_found"]:
        candidate = checked_ref(result["candidate"])
        assert candidate["registry_sha256"] == sha(canonical(state["cuts"]))
        assert candidate["matrix_binding"] == exact.matrix_binding(arrays)
        numeric_result, records = numeric_records(state, arrays)
        proposal = exact.basis_proposal(arrays, records[-1], SELECTORS, SELECTOR_ROWS,
                                        LIMITS["maximum_dynamic_exact_dimension"], deadline)
        assert checked_ref(result["basis_proposal"]) == proposal
        nums, den = list(map(int, candidate["extended_numerators"])), int(candidate["common_denominator"])
        exact.verify_proposal_point(proposal, nums, den)
        check = inspect_point(data, arrays, state["cuts"], nums, den, deadline)
        assert check == candidate["exact_check"]
        report.update(status="PASS: full exact selector point and positive t replayed",
                      exact_point_replayed=True, candidate_sha256=result["candidate"]["sha256"],
                      registry_sha256=candidate["registry_sha256"],
                      point_key=check["point_key"], full_face_rows_checked=len(arrays["row_lower"]))
    report["seconds"] = time.monotonic()-start
    assert not (directory/"cold.json").exists()
    save(directory/"cold.json", report)
    return report

def state_payload(point, cuts, native_seconds, carried, scan_bytes):
    nums, den = point_data(point)
    return {"source_bindings": source_bindings(), "limits": LIMITS,
            "point": point, "point_key": exact.point_key(nums, den), "cuts": cuts,
            "native_seconds_before": native_seconds, "carried_covers": sorted(set(carried)),
            "scan_cut_slots": LIMITS["maximum_new_cuts"]-len(cuts),
            "scan_byte_allowance": LIMITS["maximum_scan_transcript_bytes"]-scan_bytes}
