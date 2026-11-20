"""Bounded proof-producing case4 parity / LP / saved-basis cycle.

Preparation only constructs exact inventories and tiny controls. Production
starts with a fresh parity scan of the accepted seed point. At most two new
LP rounds are possible, each justified by new exact violated parity rows.
All167115 existing extended rows remain an immutable prefix. No face,
candidate alias or numerical support is ever imposed as a universal fact.
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

ROOT = Path(__file__).resolve().parents[2]
LOGS = "experiments/logs/grids-and-triangles/"
SOURCES = {
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


def seed_point_ref():
    return {"candidate": {"path": INPUTS["point"][0], "sha256": INPUTS["point"][1]},
            "cold": {"path": INPUTS["point_cold"][0], "sha256": INPUTS["point_cold"][1]}}


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
    keys = []
    for entry in registry:
        tick(deadline)
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
    assert 0 <= state["native_seconds_before"] <= LIMITS["cumulative_native_seconds"]+1e-6
    return state, data


def scan_stage(state_path, directory):
    started = time.monotonic(); deadline = started+LIMITS["scan_seconds"]
    result = {"status": "RUNNING", "state": record_ref(state_path),
              "complete": False, "raw_prefix": 0, "distinct": 0, "duplicates": 0,
              "violations": 0, "retained": 0, "basis_files": [], "optimizer_calls": 0}
    save(directory/"result.json", result)
    certs, seen, bytes_used = [], set(), 0
    with (directory/"evaluations.jsonl").open("xb", buffering=0) as evaluations, \
         (directory/"cuts.jsonl").open("xb", buffering=0) as cuts:
        try:
            state, data = checked_state(state_path, deadline)
            result["point_key"] = data["point_key"]
            allowed = state["scan_byte_allowance"]-LIMITS["scan_result_reserve_bytes"]
            assert allowed > 0
            existing = {entry["row_key"] for entry in state["cuts"]}
            for order in range(2):
                certificate = basis.rref(data["rows"], data["orders"][order], deadline)
                check = weighted.verify_basis(data, order, certificate, deadline)
                assert certificate["rank"] == 286 and not certificate["inconsistent"]
                payload = canonical({"order": order, "certificate": weighted.pack_certificate(certificate), "check": check})
                if bytes_used+len(payload) > allowed:
                    raise TimeoutError("global transcript byte bound before complete basis")
                path = directory/f"basis-{order:02d}.json"
                path.write_bytes(payload); bytes_used += len(payload)
                result["basis_files"].append(record_ref(path))
                certs.append(certificate)
                save(directory/"result.json", result)
            for raw_id, family, indices, row in weighted.candidates(data, certs):
                tick(deadline)
                assert raw_id == result["raw_prefix"]
                if row[:2] in seen:
                    result["duplicates"] += 1
                else:
                    proposal = parity.closest_forbidden(list(basis.sites(row[0])), row[1], data["point"], data["denominator"])
                    assert proposal is not None
                    violated = proposal["strictly_violated"]
                    row_form = parity.inequality(proposal)
                    key = exact.row_key(row_form)
                    # An already appended inequality cannot reject this exact point.
                    assert not violated or key not in existing
                    retain = violated and result["retained"] < state["scan_cut_slots"]
                    cut = weighted.full_cut(data, raw_id, family, indices, row, proposal, deadline) if retain else None
                    if cut is not None:
                        exact.verify_cut(cut, data["gram"], data["zeros"], data["point"], data["denominator"], deadline)
                    line = canonical([raw_id, family, indices, proposal["distance_numerator"]])
                    cut_line = canonical(cut) if cut is not None else b""
                    if bytes_used+len(line)+len(cut_line) > allowed:
                        raise TimeoutError("global transcript byte bound before complete evaluation")
                    if cut_line: cuts.write(cut_line)
                    evaluations.write(line); bytes_used += len(line)+len(cut_line)
                    seen.add(row[:2]); result["distinct"] += 1
                    result["violations"] += int(violated); result["retained"] += int(retain)
                result["raw_prefix"] += 1
                if result["raw_prefix"] % 256 == 0: save(directory/"result.json", result)
            assert result["raw_prefix"] == LIMITS["raw_words_per_scan"]
            result.update(status="COMPLETE: fixed three-family scan at one fresh point", complete=True)
        except TimeoutError as error:
            result.update(status="PARTIAL: completed exact prefix retained; no LP continuation", reason=str(error))
        except Exception as error:
            result.update(status="ERROR: unchecked outcome not accepted", error_type=type(error).__name__, reason=str(error))
        finally:
            result["transcript_bytes"] = bytes_used
            result["artifacts"] = {name: record_ref(directory/name) for name in ("evaluations.jsonl", "cuts.jsonl")}
            result["seconds"] = time.monotonic()-started
            save(directory/"result.json", result)
    return result


def scan_cold(state_path, directory):
    start = time.monotonic(); deadline = start+LIMITS["scan_cold_seconds"]
    state, data = checked_state(state_path, deadline)
    result = read_record(directory/"result.json")
    assert result["state"] == record_ref(state_path)
    assert result["status"].startswith(("COMPLETE:", "PARTIAL:"))
    certificates, byte_count = [], 0
    for order, ref in enumerate(result["basis_files"]):
        saved = checked_ref(ref); byte_count += (ROOT/ref["path"]).stat().st_size
        assert saved["order"] == order
        certificate = weighted.unpack_certificate(saved["certificate"])
        assert weighted.verify_basis(data, order, certificate, deadline) == saved["check"]
        assert certificate["rank"] == 286 and not certificate["inconsistent"]
        certificates.append(certificate)
    for ref in result["artifacts"].values():
        checked_ref_lines = (ROOT/ref["path"]).read_bytes()
        assert sha(checked_ref_lines) == ref["sha256"]
        byte_count += len(checked_ref_lines)
    assert byte_count == result["transcript_bytes"]
    assert byte_count <= state["scan_byte_allowance"]-LIMITS["scan_result_reserve_bytes"]
    counts = dict(raw_prefix=0, distinct=0, duplicates=0, violations=0, retained=0)
    seen = set()
    with (directory/"evaluations.jsonl").open("rb") as evaluations, (directory/"cuts.jsonl").open("rb") as cuts:
        if result["raw_prefix"]:
            assert len(certificates) == 2
            for raw_id, family, indices, row in weighted.candidates(data, certificates):
                if raw_id >= result["raw_prefix"]: break
                tick(deadline)
                if row[:2] in seen:
                    counts["duplicates"] += 1
                else:
                    proposal = parity.closest_forbidden(list(basis.sites(row[0])), row[1], data["point"], data["denominator"])
                    assert json.loads(next(evaluations)) == [raw_id, family, indices, proposal["distance_numerator"]]
                    if proposal["strictly_violated"] and counts["retained"] < state["scan_cut_slots"]:
                        expected = weighted.full_cut(data, raw_id, family, indices, row, proposal, deadline)
                        assert json.loads(next(cuts)) == expected
                        exact.verify_cut(expected, data["gram"], data["zeros"], data["point"], data["denominator"], deadline)
                        counts["retained"] += 1
                    counts["distinct"] += 1
                    counts["violations"] += int(proposal["strictly_violated"])
                    seen.add(row[:2])
                counts["raw_prefix"] += 1
        assert next(evaluations, None) is None and next(cuts, None) is None
    assert all(counts[k] == result[k] for k in counts)
    assert not result["complete"] or counts["raw_prefix"] == LIMITS["raw_words_per_scan"]
    report = {"status": "PASS: exact span, current-point prefix and full original Gram cuts replayed",
              "state": record_ref(state_path), "result": record_ref(directory/"result.json"),
              "complete": result["complete"], **counts, "RREF_elimination_repeated": False,
              "optimizer_calls": 0, "seconds": time.monotonic()-start}
    assert not (directory/"cold.json").exists()
    save(directory/"cold.json", report)
    return report



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
                "native_seconds_before", "carried_covers"):
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
            "appended_signed_parity_rows_checked": len(registry),
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



def preparation_definition(data, initial_point):
    return {
        "base_model": list(INPUTS["model"]), "base_arrays": list(INPUTS["arrays"]),
        "base_complete_cold": list(INPUTS["model_cold"]),
        "immutable_extended_prefix_rows": PREFIX_ROWS, "immutable_prefix_nonzeros": PREFIX_NNZ,
        "variables": VARIABLES, "selector_variables": SELECTORS,
        "fixed_zero_original_columns": data["zeros"],
        "full_original_selectors": 1214, "original_native_rows": 2271,
        "original_coordinate_covers": 178533,
        "coordinate_cover_pool": [NATIVE_ROWS, COVER_END],
        "new_cut_rows_start_after_all_frozen_extension_rows": PREFIX_ROWS,
        "max_total_rows": PREFIX_ROWS+LIMITS["maximum_new_cuts"],
        "max_total_nonzeros": PREFIX_NNZ+SELECTORS*LIMITS["maximum_new_cuts"],
        "initial_point": initial_point, "initial_point_key": data["point_key"],
        "initial_denominator": str(data["denominator"]),
        "old_basis_rows": 286, "original_Gram_rows": 630,
        "scan_families": ["old286 singles/pairs at the current exact point",
                          "weighted exact RREF with ascending ID ties, singles/pairs",
                          "weighted exact RREF with descending ID ties, singles/pairs"],
        "column_weight_rule": "decreasing exact min(x,1-x); exact original-ID ties as declared",
        "equation_deduplication": "first identical support/RHS within each fresh-point scan",
        "forbidden_vertex_ties": "bit0 at exact half; cheapest parity flip then ascending original ID",
        "signed_cut_semantics": "sum_{forbidden ones}x - sum_{other support}x <= number_of_forbidden_ones-1",
        "every_cut_has_full_original_Gram_row_sum_and_exact_current_point_deficit": True,
        "old_equations_reevaluated_once_at_every_changed_exact_point": True,
        "repeated_point_key_excludes_t_and_reduces_common_denominator": True,
        "LP_stage_begins_only_after_a_complete_cold_checked_scan_with_new_cuts": True,
        "native_cover_insertion": "at most512 unseen rows, decreasing floating violation then ascending immutable row ID",
        "saved_basis_reconstruction": "dynamic aliases and nonbasic bounds are point proposals; one square solve only",
        "exact_acceptance": "all frozen and appended rows, boxes, original2271 rows and178533 covers, all1214 coordinates",
        "exact_face_or_infeasibility": "checked finite-box row/variable slack sum; stop instead of changing the face",
        "terminal_policy": "partial, no-cut, repeated point, cap, or failed exact work stays unresolved",
        "limits": LIMITS,
    }


def prepare(output):
    assert not output.exists()
    started = time.monotonic(); deadline = started+60
    bindings = source_bindings()
    data = with_point(domain(deadline), seed_point_ref())
    # Hash the frozen archive; do not decode/rebuild the full original matrix.
    assert sha((ROOT/INPUTS["arrays"][0]).read_bytes()) == INPUTS["arrays"][1]
    controls = exact.controls()
    tick(deadline)
    spec = preparation_definition(data, seed_point_ref())
    record = {"status": "PREPARED: bounded reusable cycle; no case RREF, scan, LP or exact solve",
              "source_bindings": bindings, "definition": spec,
              "definition_sha256": sha(canonical(spec)),
              "new_controls": controls,
              "frozen_complete_matrix_replay_bound": INPUTS["model_cold"][1],
              "full_array_decode_or_rebuild": False,
              "case_parity_equations_evaluated": 0, "case_RREF_calls": 0,
              "optimizer_calls": 0, "production_linear_solve_calls": 0,
              "seconds": time.monotonic()-started}
    save(output, record)
    return record


def checked_preparation(path, deadline):
    record = read_record(path)
    assert record["source_bindings"] == source_bindings()
    data = with_point(domain(deadline), seed_point_ref())
    definition = preparation_definition(data, seed_point_ref())
    assert record["definition"] == definition
    assert record["definition_sha256"] == sha(canonical(definition))
    return record, data


def tiny_native_preflight(preparation, output):
    """Only synthetic assembly; the complete matrix remains in its cache."""
    assert not output.exists()
    start = time.monotonic()
    prep, data = checked_preparation(preparation, start+60)
    import rook_case4_face112_weighted_parity_generation as old
    controls = old.previous.controls()
    # This existing gate builds four toy native rows, with no optimization.
    assert controls["optimizer_calls"] == 0
    runtime = old.runtime_binding()
    report = {"status": "PASS: frozen native helper and tiny row/prefix transport; no optimizer",
              "source_bindings": source_bindings(),
              "preparation": record_ref(preparation), "runtime_binding": runtime,
              "native_controls": controls, "full_matrix_loaded": False,
              "case_RREF_or_scan_called": False, "optimizer_calls": 0,
              "seconds": time.monotonic()-start}
    save(output, report)
    return report


def stage_files(directory):
    return [record_ref(p) for p in sorted(directory.iterdir())
            if p.is_file() and not p.name.endswith(".partial")]


def owned_stage(mode, state, directory, seconds):
    directory.mkdir(parents=True, exist_ok=True)
    label = mode.removeprefix("_")
    started = time.monotonic()
    with (directory/(label+".stdout.log")).open("xb") as out, \
         (directory/(label+".stderr.log")).open("xb") as err:
        try:
            completed = subprocess.run(
                [sys.executable, str(Path(__file__).resolve()), mode,
                 "--state", str(state.resolve()), "--directory", str(directory.resolve())],
                stdout=out, stderr=err, timeout=seconds, check=False)
            result = {"exit_code": completed.returncode, "hard_timeout": False}
        except subprocess.TimeoutExpired:
            result = {"exit_code": None, "hard_timeout": True}
    result.update(mode=mode, state=record_ref(state), requested_hard_seconds=seconds,
                  seconds=time.monotonic()-started)
    return result


def state_payload(point, cuts, native_seconds, carried, scan_bytes):
    nums, den = point_data(point)
    return {"source_bindings": source_bindings(), "limits": LIMITS,
            "point": point, "point_key": exact.point_key(nums, den), "cuts": cuts,
            "native_seconds_before": native_seconds, "carried_covers": sorted(set(carried)),
            "scan_cut_slots": LIMITS["maximum_new_cuts"]-len(cuts),
            "scan_byte_allowance": LIMITS["maximum_scan_transcript_bytes"]-scan_bytes}


def cycle_child(preparation, preflight, directory):
    start = time.monotonic(); global_deadline = start+LIMITS["whole_cycle_hard_seconds"]-5
    prep, data = checked_preparation(preparation, global_deadline)
    flight = read_record(preflight)
    assert flight["source_bindings"] == source_bindings() and flight["preparation"] == record_ref(preparation)
    assert flight["status"].startswith("PASS:") and flight["optimizer_calls"] == 0
    result = {"status": "RUNNING", "source_bindings": source_bindings(),
              "preparation": record_ref(preparation), "preflight": record_ref(preflight),
              "limits": LIMITS, "stages": [], "point_history": [], "new_cut_registry": [],
              "LP_rounds": 0, "native_calls": 0, "native_seconds": 0.0,
              "scan_transcript_bytes": 0, "case4_exclusion_verified": False,
              "exact_zero_face_found": False, "whole_graph_problem_resolved": False}
    result_path = directory/"result.json"
    save(result_path, result)
    point, registry, carried = seed_point_ref(), [], []
    seen_points = set()
    try:
        for scan_index in range(LIMITS["fresh_point_scans"]):
            tick(global_deadline)
            state = state_payload(point, registry, result["native_seconds"], carried, result["scan_transcript_bytes"])
            if state["point_key"] in seen_points:
                result["status"] = "UNRESOLVED: repeated exact selector point; no repeated scan"
                break
            seen_points.add(state["point_key"])
            result["point_history"].append({"point": point, "point_key": state["point_key"],
                                            "accepted_cut_registry_size": len(registry)})
            state_path = directory/f"state-scan-{scan_index:02d}.json"
            save(state_path, state)
            scan_dir = directory/f"scan-{scan_index:02d}"
            owned = owned_stage("_scan", state_path, scan_dir, LIMITS["scan_seconds"])
            result["stages"].append(owned)
            save(result_path, result)
            if owned["hard_timeout"] or owned["exit_code"] != 0:
                result["status"] = "UNRESOLVED: scan child incomplete; durable prefix retained"
                break
            scanned = read_record(scan_dir/"result.json")
            if not scanned["status"].startswith(("COMPLETE:", "PARTIAL:")):
                result["status"] = "UNRESOLVED: scan error; no unchecked cut used"
                break
            owned = owned_stage("_scan_cold", state_path, scan_dir, LIMITS["scan_cold_seconds"])
            result["stages"].append(owned)
            save(result_path, result)
            if owned["hard_timeout"] or owned["exit_code"] != 0 or not (scan_dir/"cold.json").exists():
                result["status"] = "UNRESOLVED: exact scan replay incomplete"
                break
            cold = read_record(scan_dir/"cold.json")
            assert cold["status"].startswith("PASS:") and cold["result"] == record_ref(scan_dir/"result.json")
            assert cold["retained"] == scanned["retained"]
            additions = [json.loads(line) for line in (scan_dir/"cuts.jsonl").read_bytes().splitlines()]
            assert len(additions) == cold["retained"]
            for cut in additions:
                registry.append({"certificate": cut, "row_key": exact.row_key(cut["inequality"]),
                                 "source_point": point, "scan": record_ref(scan_dir/"result.json"),
                                 "scan_cold": record_ref(scan_dir/"cold.json")})
            assert len(registry) <= LIMITS["maximum_new_cuts"]
            result["new_cut_registry"] = registry
            result["scan_transcript_bytes"] += scanned["transcript_bytes"]
            assert result["scan_transcript_bytes"] <= LIMITS["maximum_scan_transcript_bytes"]
            result["stages"][-1]["artifacts"] = stage_files(scan_dir)
            save(result_path, result)
            if not scanned["complete"]:
                result["status"] = "UNRESOLVED: partial finite scan; checked cuts retained without LP"
                break
            if not additions:
                result["status"] = "UNRESOLVED: complete finite parity family gives no new cut"
                break
            if result["LP_rounds"] >= LIMITS["new_LP_rounds"]:
                result["status"] = "UNRESOLVED: two-round LP cap; latest checked cuts retained"
                break
            if result["native_seconds"] >= LIMITS["cumulative_native_seconds"]:
                result["status"] = "UNRESOLVED: cumulative native budget used; no further solve"
                break
            if result["scan_transcript_bytes"]+LIMITS["scan_result_reserve_bytes"] >= LIMITS["maximum_scan_transcript_bytes"]:
                result["status"] = "UNRESOLVED: transcript budget used"
                break
            numeric_state = state_payload(point, registry, result["native_seconds"], carried, result["scan_transcript_bytes"])
            numeric_state_path = directory/f"state-numeric-{result['LP_rounds']:02d}.json"
            save(numeric_state_path, numeric_state)
            numeric_dir = directory/f"numeric-{result['LP_rounds']:02d}"
            owned = owned_stage("_numeric", numeric_state_path, numeric_dir, LIMITS["numerical_phase_seconds"])
            result["stages"].append(owned)
            result["LP_rounds"] += 1
            save(result_path, result)
            if owned["hard_timeout"] or owned["exit_code"] != 0 or not (numeric_dir/"result.json").exists():
                result["status"] = "UNRESOLVED: numerical child incomplete"
                break
            numerical = read_record(numeric_dir/"result.json")
            result["native_calls"] += numerical["native_calls"]
            result["native_seconds"] += numerical["native_seconds"]
            assert result["native_calls"] <= LIMITS["total_native_calls"]
            result["stages"][-1]["artifacts"] = stage_files(numeric_dir)
            save(result_path, result)
            if not numerical["complete"] or not numerical["iterations"]:
                result["status"] = "UNRESOLVED: no complete numerical proposal"
                break
            exact_state = dict(numeric_state, numerical_result=record_ref(numeric_dir/"result.json"))
            exact_state_path = directory/f"state-exact-{result['LP_rounds']-1:02d}.json"
            save(exact_state_path, exact_state)
            exact_dir = directory/f"exact-{result['LP_rounds']-1:02d}"
            owned = owned_stage("_exact", exact_state_path, exact_dir, LIMITS["exact_seconds"])
            result["stages"].append(owned)
            save(result_path, result)
            if owned["hard_timeout"] or owned["exit_code"] != 0 or not (exact_dir/"result.json").exists():
                result["status"] = "UNRESOLVED: exact stage incomplete"
                break
            outcome = read_record(exact_dir/"result.json")
            owned = owned_stage("_exact_cold", exact_state_path, exact_dir, LIMITS["exact_cold_seconds"])
            result["stages"].append(owned)
            save(result_path, result)
            if owned["hard_timeout"] or owned["exit_code"] != 0 or not (exact_dir/"cold.json").exists():
                result["status"] = "UNRESOLVED: exact arithmetic replay incomplete"
                break
            cold = read_record(exact_dir/"cold.json")
            assert cold["status"].startswith("PASS:") and cold["result"] == record_ref(exact_dir/"result.json")
            result["stages"][-1]["artifacts"] = stage_files(exact_dir)
            if outcome["exact_certificate_found"]:
                assert cold["exact_certificate_replayed"]
                result["exact_certificate"] = outcome["certificate"]
                result["exact_certificate_cold"] = record_ref(exact_dir/"cold.json")
                result["case4_exclusion_verified"] = cold["kind"] == "exact_infeasibility"
                result["exact_zero_face_found"] = cold["kind"] == "exact_zero_face"
                result["status"] = ("EXACT: case4 relaxation infeasible" if result["case4_exclusion_verified"]
                                    else "EXACT: new zero face; cycle stopped without changing the domain")
                break
            if not outcome["exact_point_found"] or not cold["exact_point_replayed"]:
                result["status"] = "UNRESOLVED: exact basis reconstruction or full acceptance failed"
                break
            point = {"candidate": outcome["candidate"], "cold": record_ref(exact_dir/"cold.json")}
            carried = numerical["carried_covers_after"]
            result["latest_exact_point"] = point
            result["latest_exact_point_registry_size"] = len(registry)
            result["status"] = "RUNNING: new exact point accepted; next declared scan pending"
            save(result_path, result)
        else:
            result["status"] = "UNRESOLVED: finite fresh-point scan cap"
    except Exception as error:
        result.update(status="UNRESOLVED: controller error; completed checked artifacts retained",
                      error_type=type(error).__name__, reason=str(error))
    finally:
        result["seconds"] = time.monotonic()-start
        result["source_and_state_artifacts"] = [record_ref(p) for p in sorted(directory.glob("state-*.json"))]
        save(result_path, result)
    return result


def run(preparation, preflight, directory):
    """One owned process group; no child survives a whole-cycle timeout."""
    import os
    import signal
    assert not directory.exists()
    directory.mkdir(parents=True)
    start = time.monotonic()
    with (directory/"controller.stdout.log").open("xb") as out, \
         (directory/"controller.stderr.log").open("xb") as err:
        process = subprocess.Popen(
            [sys.executable, str(Path(__file__).resolve()), "_cycle",
             "--preparation", str(preparation.resolve()), "--preflight", str(preflight.resolve()),
             "--directory", str(directory.resolve())], stdout=out, stderr=err, start_new_session=True)
        timed_out = False
        try:
            code = process.wait(timeout=LIMITS["whole_cycle_hard_seconds"])
        except subprocess.TimeoutExpired:
            timed_out = True
            os.killpg(process.pid, signal.SIGKILL)
            code = process.wait()
    report = {"status": "UNKNOWN: whole-cycle hard timeout" if timed_out else "owned cycle child terminated",
              "source_bindings": source_bindings(), "preparation": record_ref(preparation),
              "preflight": record_ref(preflight), "hard_seconds": LIMITS["whole_cycle_hard_seconds"],
              "hard_timeout": timed_out, "exit_code": code, "retries": 0,
              "seconds": time.monotonic()-start}
    if (directory/"result.json").exists():
        report["result"] = record_ref(directory/"result.json")
    save(directory/"supervisor.json", report)
    return report


def verify_transcript(preparation, preflight, directory, output):
    """Bindings-only final audit. Per-stage exact cold replays are not repeated."""
    assert not output.exists()
    start = time.monotonic()
    prep, data = checked_preparation(preparation, start+60)
    supervisor, result = read_record(directory/"supervisor.json"), read_record(directory/"result.json")
    assert supervisor["source_bindings"] == result["source_bindings"] == source_bindings()
    assert supervisor["preparation"] == result["preparation"] == record_ref(preparation)
    assert supervisor["preflight"] == result["preflight"] == record_ref(preflight)
    assert supervisor["result"] == record_ref(directory/"result.json")
    assert result["limits"] == LIMITS
    assert result["LP_rounds"] <= 2 and result["native_calls"] <= 60
    assert len(result["point_history"]) <= 3
    assert len({p["point_key"] for p in result["point_history"]}) == len(result["point_history"])
    validate_registry(data, result["new_cut_registry"], start+60)
    file_count = 0
    for stage in result["stages"]:
        checked_ref(stage["state"])
        for ref in stage.get("artifacts", []):
            raw = (ROOT/ref["path"]).read_bytes()
            assert sha(raw) == ref["sha256"]
            file_count += 1
    for ref in result["source_and_state_artifacts"]:
        checked_ref(ref)
    if result["case4_exclusion_verified"] or result["exact_zero_face_found"]:
        cold = checked_ref(result["exact_certificate_cold"])
        assert cold["exact_certificate_replayed"]
        assert result["case4_exclusion_verified"] == (cold["kind"] == "exact_infeasibility")
        assert result["exact_zero_face_found"] == (cold["kind"] == "exact_zero_face")
    report = {"status": "PASS: immutable chronological transcript bindings and checked cut registry",
              "source_bindings": source_bindings(), "supervisor": record_ref(directory/"supervisor.json"),
              "result": record_ref(directory/"result.json"), "stage_artifacts_checked": file_count,
              "new_cut_witnesses_checked": len(result["new_cut_registry"]),
              "completed_per_stage_arithmetic_reports_bound": True,
              "stage_arithmetic_scans_eliminations_or_optimizer_repeated": False,
              "seconds": time.monotonic()-start}
    save(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "preflight", "run", "verify",
        "_cycle", "_scan", "_scan_cold", "_numeric", "_exact", "_exact_cold"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--preflight", type=Path)
    parser.add_argument("--state", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        result = prepare(args.output)
    elif args.mode == "preflight":
        result = tiny_native_preflight(args.preparation, args.output)
    elif args.mode == "run":
        result = run(args.preparation, args.preflight, args.directory)
    elif args.mode == "verify":
        result = verify_transcript(args.preparation, args.preflight, args.directory, args.output)
    elif args.mode == "_cycle":
        result = cycle_child(args.preparation, args.preflight, args.directory)
    else:
        functions = {"_scan": scan_stage, "_scan_cold": scan_cold, "_numeric": numeric_stage,
                     "_exact": exact_stage, "_exact_cold": exact_cold}
        result = functions[args.mode](args.state, args.directory)
    print(json.dumps({k: v for k, v in result.items() if k not in
        ("source_bindings", "definition", "new_cut_registry", "point_history", "stages")}, indent=2), flush=True)


if __name__ == "__main__":
    main()
