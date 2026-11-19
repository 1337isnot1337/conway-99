"""One exact reconstruction of the saved two-weighted-cut selector basis.

The813 x_j=t aliases are candidate-point assumptions, not universal faces.
Acceptance checks all167115 face rows and every original1214-coordinate
obligation, both unit sums, four pair bounds, H3 and both new parity rows.
Preparation records the290-square system without elimination; no optimizer.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import importlib.metadata
from itertools import product
import json
from math import gcd
from pathlib import Path
import subprocess
import sys
import time

import rook_case4_face112_weighted_parity_model as face

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
FILES = {
    "builder": ("experiments/workspace/rook_case4_face112_weighted_parity_model.py", "06463fe26a178b9e0d1a004f47c474c6463bf52b769699c8481047dbc01a6300"),
    "recovery": ("experiments/workspace/rook_case4_complete_lp_recovery.py", "e577327c9cc2471f119c755a49a179b9f94f1004a22de80152a4114787a7eec6"),
    "model": (BASE+"rook-case4-face112-weighted-parity-model01/model.json", "c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3"),
    "arrays": (BASE+"rook-case4-face112-weighted-parity-model01/arrays.npz", "59a06470793e6959a67ae30dfb29ecf0de4c8aa74661e1335d7676aa612c1e7e"),
    "numeric": (BASE+"rook-case4-face112-weighted-parity-generation-run01/iteration-00-numeric.json.gz", "b024197a41afb7412b5010deafcf136cbf1bf3ca1b08aed2ffd1965e4cb9ee00"),
    "terminal": (BASE+"rook-case4-face112-weighted-parity-generation-run01/result.json", "c6537ce8337084ab131991b2608e59fa37fa38ae59f9c9f478e01dd2e5c6892d"),
    "cold_replay": (BASE+"rook-case4-face112-weighted-parity-generation-run01-replay.json", "00591861439cf247245dbba5c16b7e5e10d8528a3d2139d6cce5c27a1c4e6866"),
}
NUMERIC_RAW_SHA = "d73d5d8463b194c057c8f9c96d2cb0dd3e1d4cc9acc40f76701440bad0805831"
SELECTORS, BASE_ROWS, FULL_ROWS = 1102, 166013, 167115
NATIVE_ROWS, COVER_END = 1960, 166004
VARIABLES, DIMENSION, ALIASES = 1103, 290, 813
SECONDS, MAX_OUTPUT_BITS = 60, 4096


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return (json.dumps(value, sort_keys=True, separators=(",", ":"))+"\n").encode()


def save(path, value):
    temporary = path.with_name(path.name+".partial")
    temporary.write_bytes(json.dumps(value, indent=2).encode()+b"\n")
    temporary.replace(path)


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("bounded exact basis reconstruction/check")


def bindings(root):
    output = {}
    for name, (path, expected) in FILES.items():
        raw = (root/path).read_bytes()
        assert sha(raw) == expected, ("input hash", name)
        output[name] = {"path": path, "sha256": expected}
    assert Path(face.__file__).resolve() == (root/FILES["builder"][0]).resolve()
    assert sha(Path(face.recovery.__file__).read_bytes()) == FILES["recovery"][1]
    return {"source_sha256": sha(Path(__file__).read_bytes()), "inputs": output,
            "python_flint_version": importlib.metadata.version("python-flint")}


def fold(terms, aliases, positions, t):
    values = Counter()
    for j, coefficient in terms:
        values[positions[t if j in aliases else j]] += coefficient
    return [[j, values[j]] for j in sorted(values) if values[j]]


def controls():
    count = 0
    for mask in range(8):
        aliases = {j for j in range(3) if mask >> j & 1}
        free = [j for j in range(4) if j not in aliases]
        positions = {j: i for i, j in enumerate(free)}
        for coefficients in product((-1, 0, 1), repeat=4):
            terms = [[j, c] for j, c in enumerate(coefficients) if c]
            folded = fold(terms, aliases, positions, 3)
            for reduced in product((-1, 0, 1), repeat=len(free)):
                original = [reduced[positions[3 if j in aliases else j]] for j in range(4)]
                assert sum(c*original[j] for j, c in terms) == sum(c*reduced[j] for j, c in folded)
                count += 1
    assert count == 15552
    return {"exact_alias_substitution_controls": count, "optimizer_calls": 0,
            "production_linear_systems_solved": 0}


def proposal(root):
    source = bindings(root)
    model, arrays = face.load(root/FILES["model"][0], root/FILES["arrays"][0])
    raw = gzip.decompress((root/FILES["numeric"][0]).read_bytes())
    assert sha(raw) == NUMERIC_RAW_SHA
    numeric = json.loads(raw)
    terminal = json.loads((root/FILES["terminal"][0]).read_bytes())
    cold = json.loads((root/FILES["cold_replay"][0]).read_bytes())
    assert cold["result_sha256"] == FILES["terminal"][1]
    assert cold["exact_rational_point_verified"] is False
    assert terminal["exact_rational_point_found"] is False and terminal["production_run_calls"] == 1
    assert numeric["basis_valid"] and numeric["optimal"] and numeric["solution_value_valid"]
    assert numeric["column_basis_status"] == ["HighsBasisStatus.kBasic"]*VARIABLES
    expected_active = list(range(NATIVE_ROWS)) + list(range(COVER_END, FULL_ROWS))
    assert numeric["active_original_row_ids"] == expected_active
    active = numeric["nonbasic_original_row_status"]
    assert len(active) == VARIABLES and len({r for r, s in active}) == VARIABLES
    assert all(r in set(numeric["active_original_row_ids"]) for r, s in active)
    assert all(s in ("HighsBasisStatus.kLower", "HighsBasisStatus.kUpper") for r, s in active)
    aliases = {r-BASE_ROWS for r, s in active if r >= BASE_ROWS}
    assert len(aliases) == ALIASES and all(0 <= j < SELECTORS for j in aliases)
    assert all(s == "HighsBasisStatus.kLower" for r, s in active if r >= BASE_ROWS)
    free = [j for j in range(VARIABLES) if j not in aliases]
    assert len(free) == DIMENSION and free[-1] == SELECTORS
    positions = {j: k for k, j in enumerate(free)}
    rows = []
    sides = Counter()
    for row, side in active:
        if row >= BASE_ROWS:
            continue
        kind = int(arrays["row_origin_kind"][row])
        assert ((0 <= row < NATIVE_ROWS and kind == 0) or
                (row == COVER_END and kind == 2) or
                (row == BASE_ROWS-3 and kind == 4) or
                (row == BASE_ROWS-1 and kind == 5))
        first, last = map(int, arrays["row_pointers"][row:row+2])
        terms = [[int(arrays["column_indices"][p]), int(arrays["coefficients"][p])]
                 for p in range(first, last)]
        bound = int(arrays["row_lower" if side.endswith("kLower") else "row_upper"][row])
        folded = fold(terms, aliases, positions, SELECTORS)
        assert folded and all(abs(c) < 2**53 for j, c in folded)
        rows.append({"original_face_row": row, "row_origin_kind": kind,
                     "row_origin_index": int(arrays["row_origin_index"][row]),
                     "side": side, "rhs": bound, "full_terms": terms, "reduced_terms": folded})
        sides[side] += 1
    assert len(rows) == DIMENSION
    assert dict(sides) == {"HighsBasisStatus.kLower": 158, "HighsBasisStatus.kUpper": 132}
    assert [r["original_face_row"] for r in rows if r["row_origin_kind"] != 0] == [COVER_END, BASE_ROWS-3, BASE_ROWS-1]
    assert model["weighted_parity_row_ids"] == [BASE_ROWS-2,BASE_ROWS-1]
    assert [[r["lower"],r["upper"]] for r in model["weighted_parity_rows"]] == [[0,4],[1,17]]
    assert model["third_parity_cover_range"] == [1,3]
    spec = {"schema": "rook-case4-face112-weighted-parity-artifact-only-basis-v1", "bindings": source,
            "all_saved_active_row_IDs_and_sides": active,
            "candidate_alias_selector_indices": sorted(aliases),
            "candidate_alias_original1214_columns": [int(arrays["original_column_ids"][j]) for j in sorted(aliases)],
            "remaining_extended_variable_indices": free,
            "remaining_original1214_columns_or_t": [int(arrays["original_column_ids"][j]) if j < SELECTORS else "t" for j in free],
            "rows": rows, "square_dimension": DIMENSION,
            "dense_cells": DIMENSION**2, "sparse_nonzeros": sum(len(r["reduced_terms"]) for r in rows),
            "restoration": "Every candidate alias x_j is set equal to t; all other coordinates come from the exact square solve.",
            "candidate_face_is_not_a_universal_restriction": True,
            "all167115_rows_and_original1214_model_required": True,
            "fixed_zero_original_columns": model["fixed_zero_columns"],
            "both_unit_sum_supports": model["integer_cover_live_original_supports"],
            "all_four_pair_bounds": model["added_pair_rows"],
            "third_parity_cover_support": model["third_parity_cover_original_support"],
            "third_parity_cover_range": [1,3],
            "weighted_parity_original_rows": model["weighted_parity_rows"]}
    return spec, arrays


def prepared(directory, root):
    record = json.loads((directory/"preparation.json").read_bytes())
    raw = gzip.decompress((directory/"proposal.json.gz").read_bytes())
    assert sha(raw) == record["proposal_raw_sha256"]
    assert sha((directory/"proposal.json.gz").read_bytes()) == record["proposal_gzip_sha256"]
    current, arrays = proposal(root)
    assert raw == canonical(current)
    assert record["bindings"] == current["bindings"]
    return record, current, arrays


def inspect(root, spec, arrays, nums, den, deadline):
    assert type(den) is int and den > 0 and den.bit_length() <= MAX_OUTPUT_BITS
    assert len(nums) == VARIABLES and all(type(v) is int and abs(v).bit_length() <= MAX_OUTPUT_BITS for v in nums)
    assert all(0 <= v <= den for v in nums) and nums[-1] > 0
    for j in spec["candidate_alias_selector_indices"]:
        assert nums[j] == nums[-1]
    values = [nums[j] for j in spec["remaining_extended_variable_indices"]]
    for row in spec["rows"]:
        assert sum(c*values[j] for j, c in row["reduced_terms"]) == row["rhs"]*den
    pointers, columns, coefficients = arrays["row_pointers"], arrays["column_indices"], arrays["coefficients"]
    for row in range(BASE_ROWS):
        if row % 256 == 0:
            tick(deadline)
        first, last = map(int, pointers[row:row+2])
        value = sum(int(coefficients[p])*nums[int(columns[p])] for p in range(first, last))
        assert int(arrays["row_lower"][row])*den <= value <= int(arrays["row_upper"][row])*den, ("face row", row)
    assert all(0 <= x-nums[-1] <= den for x in nums[:-1])
    restored = [0]*1214
    for j, a in enumerate(arrays["original_column_ids"]):
        restored[int(a)] = nums[j]
    assert len(spec["fixed_zero_original_columns"]) == 112
    assert all(restored[a] == 0 for a in spec["fixed_zero_original_columns"])
    assert len(spec["both_unit_sum_supports"]) == 2 and len(spec["all_four_pair_bounds"]) == 4
    for support in spec["both_unit_sum_supports"]:
        assert sum(restored[a] for a in support) == den
    for a, b in spec["all_four_pair_bounds"]:
        assert restored[a] + restored[b] <= den
    assert spec["third_parity_cover_range"] == [1,3] and len(spec["third_parity_cover_support"]) == 27
    assert den <= sum(restored[a] for a in spec["third_parity_cover_support"]) <= 3*den
    assert [len(r["terms"]) for r in spec["weighted_parity_original_rows"]] == [48,50]
    for row in spec["weighted_parity_original_rows"]:
        value = sum(c*restored[a] for a,c in row["terms"])
        assert row["lower"]*den <= value <= row["upper"]*den
    inventory, metadata, registry = face.recovery.checked_inputs(root)
    native = face.recovery.original_rows(inventory)
    assert len(native) == 2271
    for i, row in enumerate(native):
        if i % 64 == 0:
            tick(deadline)
        value = sum(c*restored[a] for a, c in row["terms"])
        assert row["lower"]*den <= value <= row["upper"]*den, ("original native row", i)
    for i in range(178533):
        if i % 256 == 0:
            tick(deadline)
        target, bits = face.recovery.registry_entry(registry, i)
        value = sum(restored[a] for a in face.recovery.members(bits))
        assert value >= restored[target], ("original coordinate cover", i)
    assert sum(restored) == 64*den
    return {"status": "PASS: full exact face and original selector point",
            "face_rows_checked": FULL_ROWS, "face_variable_bounds_checked": VARIABLES,
            "original_native_rows_checked": 2271, "original_coordinate_covers_checked": 178533,
            "original1214_bounds_and_all112_zeros_checked": True, "population": 64,
            "both_parity_equalities_checked": True, "all_four_pair_bounds_checked": True,
            "third_parity_cover_original27_support_checked": True,
            "both_weighted_parity_original_rows_checked": True,
            "strictly_positive_t": True, "t_numerator": str(nums[-1]), "common_denominator": str(den),
            "common_denominator_bits": den.bit_length(), "maximum_numerator_bits": max(abs(v).bit_length() for v in nums),
            "original1214_selector_numerators": list(map(str, restored)),
            "binary_incidence_or_graph_claimed": False}


def prepare(directory, root):
    assert not directory.exists()
    directory.mkdir(parents=True)
    start = time.monotonic()
    spec, arrays = proposal(root)
    raw = canonical(spec)
    compressed = gzip.compress(raw, mtime=0)
    (directory/"proposal.json.gz").write_bytes(compressed)
    record = {"status": "PREPARED_ARTIFACT_ONLY_290_SQUARE_RECONSTRUCTION_NO_ELIMINATION",
              "bindings": spec["bindings"], "proposal_raw_sha256": sha(raw),
              "proposal_gzip_sha256": sha(compressed), "proposal_raw_bytes": len(raw),
              "candidate_aliases": ALIASES, "square_dimension": DIMENSION,
              "sparse_nonzeros": spec["sparse_nonzeros"], "dense_cells": spec["dense_cells"],
              "controls": controls(), "production_linear_solve_calls": 0, "optimizer_calls": 0,
              "hard_exact_child_seconds": SECONDS, "maximum_output_integer_bits": MAX_OUTPUT_BITS,
              "internal_flint_integer_bits_not_claimed_bounded": True,
              "exact_acceptance_requires_every_original_row": True,
              "elapsed_seconds": time.monotonic()-start}
    save(directory/"preparation.json", record)
    return record


def solve_child(preparation, root, directory):
    started = time.monotonic(); deadline = started+SECONDS
    record = {"status": "UNKNOWN: exact reconstruction has not completed", "optimizer_calls": 0,
              "production_linear_solve_calls": 0, "exact_point_found": False}
    output = directory/"child-result.json"
    save(output, record)
    try:
        prep, spec, arrays = prepared(preparation, root)
        record.update(bindings=spec["bindings"], preparation_sha256=sha((preparation/"preparation.json").read_bytes()))
        tick(deadline)
        from flint import fmpq_mat
        matrix = [[0]*DIMENSION for _ in range(DIMENSION)]
        for i, row in enumerate(spec["rows"]):
            for j, c in row["reduced_terms"]:
                matrix[i][j] = c
        record["production_linear_solve_calls"] = 1
        record["linear_solve_method"] = "fmpq_mat.solve, algorithm=dixon"
        save(output, record)
        solve_start = time.monotonic()
        try:
            solved = fmpq_mat(matrix).solve(fmpq_mat([[r["rhs"]] for r in spec["rows"]]), algorithm="dixon")
        except Exception as error:
            raise ArithmeticError("exact square solve stopped: "+type(error).__name__+": "+str(error)) from error
        numerator_matrix, denominator = solved.numer_denom()
        reduced_nums = [int(numerator_matrix[i, 0]) for i in range(DIMENSION)]
        den = int(denominator)
        assert den > 0
        divisor = gcd(den, *reduced_nums)
        reduced_nums, den = [v//divisor for v in reduced_nums], den//divisor
        if den.bit_length() > MAX_OUTPUT_BITS or any(abs(v).bit_length() > MAX_OUTPUT_BITS for v in reduced_nums):
            raise ArithmeticError("exact output integer bit limit")
        record["linear_solve_seconds"] = time.monotonic()-solve_start
        nums = [reduced_nums[-1]]*VARIABLES
        for j, value in zip(spec["remaining_extended_variable_indices"], reduced_nums):
            nums[j] = value
        candidate = {"status": "CANDIDATE: full exact acceptance pending", "common_denominator": str(den),
                     "extended_numerators": list(map(str, nums)), "production_linear_solve_calls": 1}
        save(directory/"candidate.json", candidate)
        tick(deadline)
        checked = inspect(root, spec, arrays, nums, den, deadline)
        candidate.update(status="EXACT_FULL_SELECTOR_POINT: independent replay pending", exact_check=checked)
        save(directory/"candidate.json", candidate)
        record.update(status="EXACT_FULL_SELECTOR_POINT: independent replay pending", exact_point_found=True,
                      candidate_sha256=sha((directory/"candidate.json").read_bytes()))
    except (ArithmeticError, AssertionError, TimeoutError, ValueError, ZeroDivisionError) as error:
        record.update(status="UNKNOWN: exact system or complete acceptance failed",
                      reason_type=type(error).__name__, reason=str(error))
    except Exception as error:
        record.update(status="ERROR: no unchecked outcome promoted", reason_type=type(error).__name__, reason=str(error))
        raise
    finally:
        record["elapsed_seconds"] = time.monotonic()-started
        save(output, record)
    return record


def query(preparation, root, directory):
    assert not directory.exists()
    prep, spec, arrays = prepared(preparation, root)
    del arrays
    directory.mkdir(parents=True)
    record = {"status": "RUNNING: one owned exact child", "bindings": spec["bindings"],
              "preparation_sha256": sha((preparation/"preparation.json").read_bytes()),
              "hard_exact_child_seconds": SECONDS, "automatic_retry": False, "optimizer_calls": 0,
              "exact_point_found": False, "case4_excluded": False}
    save(directory/"result.json", record)
    start = time.monotonic()
    with (directory/"child.stdout.log").open("w") as out, (directory/"child.stderr.log").open("w") as err:
        try:
            done = subprocess.run([sys.executable, str(Path(__file__).resolve()), "_solve",
                                   "--preparation", str(preparation.resolve()), "--root", str(root.resolve()),
                                   "--directory", str(directory.resolve())], stdout=out, stderr=err,
                                  timeout=SECONDS, check=False)
            record["child_exit_code"] = done.returncode
            child = json.loads((directory/"child-result.json").read_bytes())
            record["child_result_sha256"] = sha((directory/"child-result.json").read_bytes())
            assert child["production_linear_solve_calls"] <= 1 and child["optimizer_calls"] == 0
            record["status"] = child["status"] if done.returncode == 0 else "ERROR: exact child failed"
            record["exact_point_found"] = done.returncode == 0 and child["exact_point_found"]
        except subprocess.TimeoutExpired:
            record.update(status="UNKNOWN:60-second exact child hard timeout", hard_timeout=True)
        finally:
            record["elapsed_child_seconds"] = time.monotonic()-start
            save(directory/"result.json", record)
    return record


def replay(preparation, root, directory, output):
    assert not output.exists()
    started = time.monotonic(); deadline = started+SECONDS
    prep, spec, arrays = prepared(preparation, root)
    record = json.loads((directory/"result.json").read_bytes())
    assert record["bindings"] == spec["bindings"]
    assert record["preparation_sha256"] == sha((preparation/"preparation.json").read_bytes())
    assert record["optimizer_calls"] == 0
    report = {"status": "PASS: terminal bindings; no exact point claimed", "bindings": spec["bindings"],
              "terminal_sha256": sha((directory/"result.json").read_bytes()),
              "exact_point_replayed": False, "linear_solve_called": False, "optimizer_called": False}
    if record["exact_point_found"]:
        child_raw = (directory/"child-result.json").read_bytes()
        assert sha(child_raw) == record["child_result_sha256"]
        child = json.loads(child_raw)
        raw = (directory/"candidate.json").read_bytes()
        assert sha(raw) == child["candidate_sha256"]
        candidate = json.loads(raw)
        nums, den = list(map(int, candidate["extended_numerators"])), int(candidate["common_denominator"])
        checked = inspect(root, spec, arrays, nums, den, deadline)
        assert checked == candidate["exact_check"]
        report.update(status="PASS: full exact selector point and positive t replayed", exact_point_replayed=True,
                      candidate_sha256=sha(raw), common_denominator_bits=den.bit_length(),
                      full_face_rows_checked=FULL_ROWS, original_native_rows_checked=2271,
                      original_coordinate_covers_checked=178533, binary_graph_claimed=False)
    report["elapsed_seconds"] = time.monotonic()-started
    save(output, report)
    return report


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("mode", choices=("prepare", "query", "_solve", "replay"))
    p.add_argument("--root", type=Path, default=ROOT)
    p.add_argument("--preparation", type=Path)
    p.add_argument("--directory", type=Path, required=True)
    p.add_argument("--output", type=Path)
    args = p.parse_args()
    if args.mode == "prepare":
        record = prepare(args.directory, args.root)
    elif args.mode == "query":
        assert args.preparation is not None
        record = query(args.preparation, args.root, args.directory)
    elif args.mode == "_solve":
        assert args.preparation is not None
        record = solve_child(args.preparation, args.root, args.directory)
    else:
        assert args.preparation is not None and args.output is not None
        record = replay(args.preparation, args.root, args.directory, args.output)
    print(json.dumps(record, indent=2), flush=True)


if __name__ == "__main__":
    main()
