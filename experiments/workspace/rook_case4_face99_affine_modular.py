"""Bounded exact modular row-space audit of the frozen case4 affine domain.

NumPy int64 proposes row-reduction certificates with explicitly checked
arithmetic bounds. A separate Python-integer verifier checks both row-space
inclusions, every contradiction and every fixed-coordinate congruence.
Preparation runs only tiny controls. Case4 elimination requires run mode.
"""
import argparse
import gzip
import hashlib
from itertools import product
import json
import os
from pathlib import Path
import sys
import time

for _name in ("OMP_NUM_THREADS", "OPENBLAS_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS"):
    os.environ[_name] = "1"

import rook_case4_face99_affine_inventory as inv

ROOT = inv.ROOT
BASE = "experiments/logs/grids-and-triangles/"
INVENTORY_SOURCE_SHA = "aff911d07c002d621933ef5371520a5d9c13842a278ab7ac4874279137d93207"
INVENTORY_PATH = BASE+"rook-case4-face99-affine-inventory01.json.gz"
INVENTORY_SHA = "61288003fb0b4dae4e37d936cd9c6343e4cbfaec75076c14ea05fa4ede290929"
INVENTORY_RAW_SHA = "06024df62d4723f287cce4abf6b3a6d26ae8a3e93e991e994c8843620af20528"
COLD_PATH = BASE+"rook-case4-face99-affine-inventory01-cold.json"
COLD_SHA = "96f8a1f6e5f09a6a5978bf6ffd1ac06dd1e59a8d8d34fb104337ab25fc8dbc6f"
PRIMES = (19, 601, 145463, 2, 3, 5, 7)
LIMITS = {"production_batch_seconds": 60, "cold_replay_seconds": 60,
          "maximum_prime_calls": 7, "maximum_certificate_bytes": 20 << 20,
          "automatic_retries": 0, "optimizer_calls": 0, "solver_calls": 0}
sha, canonical = inv.sha, inv.canonical


def tick(deadline):
    if time.monotonic() >= deadline:
        raise TimeoutError("exact modular batch or verifier deadline")


def save_new(path, value):
    assert not path.exists()
    path.write_text(json.dumps(value, indent=2)+"\n")


def checkpoint(path, value):
    tmp = path.with_name(path.name+".tmp")
    tmp.write_text(json.dumps(value, indent=2)+"\n")
    tmp.replace(path)


def bindings():
    assert sha(Path(inv.__file__).read_bytes()) == INVENTORY_SOURCE_SHA
    for name, expected in inv.SOURCE_BINDINGS.items():
        assert sha(Path(__file__).with_name(name).read_bytes()) == expected
    return {"source_sha256": sha(Path(__file__).read_bytes()),
            "inventory_source_sha256": INVENTORY_SOURCE_SHA,
            "inventory_dependency_source_hashes": inv.SOURCE_BINDINGS,
            "inventory_gzip_sha256": INVENTORY_SHA, "inventory_raw_sha256": INVENTORY_RAW_SHA,
            "inventory_cold_sha256": COLD_SHA}


def runtime():
    import numpy as np
    import numpy._core._multiarray_umath as core
    return {"python": sys.version, "numpy_version": np.__version__,
            "numpy_native_module_sha256": sha(Path(core.__file__).read_bytes()),
            "runtime_installed_or_modified": False}


def load_inventory():
    bound = bindings()
    raw = (ROOT/INVENTORY_PATH).read_bytes()
    assert sha(raw) == INVENTORY_SHA
    plain = gzip.decompress(raw)
    assert sha(plain) == INVENTORY_RAW_SHA
    data = json.loads(plain)
    assert data["source_sha256"] == INVENTORY_SOURCE_SHA
    cold = inv.checked_json(ROOT, COLD_PATH, COLD_SHA)
    assert cold["status"].startswith("PASS") and cold["certificate_raw_sha256"] == INVENTORY_RAW_SHA
    native = inv.checked_json(ROOT, *inv.INPUTS["native"])
    old = inv.original.original_rows(native["primary_inventory"])
    assert sha(canonical(old)) == data["original_native_rows_sha256"]
    seed = inv.checked_json(ROOT, *inv.INPUTS["seed"])
    assert data["zero_columns"] == seed["seed_zero_columns"]
    kept = [a for a in range(1214) if a not in set(data["zero_columns"])]
    ledger, equations = inv.equalities(old, kept)
    assert data["original_column_ids"] == kept and len(kept) == 1115
    assert data["equality_provenance"] == ledger and data["equations"] == equations
    assert len(ledger) == 632 and len(equations) == 396
    assert data["arithmetic_proposal"]["planned_prime_order"] == list(PRIMES)
    assert all(inv.prime_by_trial(p) for p in PRIMES)
    return bound, data, old


def eliminate(equations, n, p, deadline):
    """Exact bounded integer arithmetic; no floating-point matrix operation."""
    import numpy as np
    m = len(equations)
    assert inv.prime_by_trial(p)
    assert max((p-1)**2+(p-1), m*(p-1)**2) < 2**63
    matrix = np.zeros((m, n+1), dtype=np.int64)
    for i, row in enumerate(equations):
        for j, c in row["terms"]:
            matrix[i, j] = c % p
        matrix[i, n] = row["right_hand_side"] % p
    transform = np.eye(m, dtype=np.int64)
    pivots = []
    for column in range(n):
        tick(deadline)
        r = len(pivots)
        if r == m:
            break
        choices = np.flatnonzero(matrix[r:, column])
        if not len(choices):
            continue
        chosen = r+int(choices[0])
        if chosen != r:
            matrix[[r, chosen]] = matrix[[chosen, r]]
            transform[[r, chosen]] = transform[[chosen, r]]
        inverse = pow(int(matrix[r, column]), -1, p)
        matrix[r] = (matrix[r]*inverse) % p
        transform[r] = (transform[r]*inverse) % p
        factors = matrix[:, column].copy()
        factors[r] = 0
        affected = np.flatnonzero(factors)
        if len(affected):
            matrix[affected] = (matrix[affected]-factors[affected, None]*matrix[r]) % p
            transform[affected] = (transform[affected]-factors[affected, None]*transform[r]) % p
        pivots.append(column)
    tick(deadline)
    bad = np.flatnonzero(np.all(matrix[:, :n] == 0, axis=1) & (matrix[:, n] != 0))
    if len(bad):
        i = int(bad[0])
        return {"kind": "modular_inconsistency", "prime": p, "variables": n,
                "combination": transform[i].tolist(), "nonzero_right_hand_side": int(matrix[i, n])}
    r = len(pivots)
    assert not np.any(matrix[r:])
    return {"kind": "consistent_complete_rowspace", "prime": p, "variables": n,
            "pivot_columns": pivots, "reduced_rows": matrix[:r].tolist(),
            "row_combinations": transform[:r].tolist()}


def linear_combination(equations, coefficients, n, p):
    assert len(coefficients) == len(equations)
    assert all(type(c) is int and 0 <= c < p for c in coefficients)
    out = [0]*(n+1)
    for row, multiplier in zip(equations, coefficients):
        if multiplier:
            for j, c in row["terms"]:
                out[j] += multiplier*c
            out[n] += multiplier*row["right_hand_side"]
    return [a % p for a in out]


def verify(equations, n, proof, deadline=float("inf")):
    """Pure Python integers; no NumPy, rank computation or row reduction."""
    p = proof["prime"]
    assert inv.prime_by_trial(p) and proof["variables"] == n
    if proof["kind"] == "modular_inconsistency":
        actual = linear_combination(equations, proof["combination"], n, p)
        assert not any(actual[:n]) and actual[n] == proof["nonzero_right_hand_side"] != 0
        return {"kind": "modular_inconsistency", "prime": p,
                "contradiction_right_hand_side": actual[n], "fixed_coordinates": [],
                "direct_integer_row_combination_checked": True}
    assert proof["kind"] == "consistent_complete_rowspace"
    pivots, rows, combinations = (proof[k] for k in ("pivot_columns", "reduced_rows", "row_combinations"))
    r = len(rows)
    assert len(pivots) == len(combinations) == r <= min(n, len(equations))
    assert pivots == sorted(set(pivots)) and all(0 <= j < n for j in pivots)
    fixed = []
    for k, (pivot, row, combination) in enumerate(zip(pivots, rows, combinations)):
        tick(deadline)
        assert len(row) == n+1 and all(type(v) is int and 0 <= v < p for v in row)
        assert all(v == 0 for v in row[:pivot]) and row[pivot] == 1
        assert all(row[j] == int(k == i) for i, j in enumerate(pivots))
        assert linear_combination(equations, combination, n, p) == row
        if sum(v != 0 for v in row[:n]) == 1:
            fixed.append({"coordinate": pivot, "residue": row[n], "basis_row": k})
    # Reverse inclusion proves completeness: every original row is the
    # combination of RREF rows specified by its coefficients at pivot sites.
    pivot_to_basis = {j: i for i, j in enumerate(pivots)}
    for equation in equations:
        tick(deadline)
        reconstructed = [0]*(n+1)
        expected = [0]*(n+1)
        for j, c in equation["terms"]:
            expected[j] = c % p
            if j in pivot_to_basis:
                source = rows[pivot_to_basis[j]]
                for a, value in enumerate(source):
                    reconstructed[a] += (c % p)*value
        expected[n] = equation["right_hand_side"] % p
        assert [value % p for value in reconstructed] == expected
    point = [0]*n
    for pivot, row in zip(pivots, rows):
        point[pivot] = row[n]
    assert all((sum(c*point[a] for a, c in row["terms"])-row["right_hand_side"]) % p == 0 for row in equations)
    return {"kind": "consistent_complete_rowspace", "prime": p, "rank": r,
            "nullity": n-r, "fixed_coordinates": fixed,
            "both_rowspace_inclusions_checked_with_Python_integers": True,
            "modular_point": point}


def controls():
    exhaustive, assignments, signed = 0, 0, 0
    for coefficients in product((0, 1), repeat=6):
        for rhs in product((0, 1), repeat=2):
            equations = [{"terms": [[j, coefficients[3*i+j]] for j in range(3) if coefficients[3*i+j]],
                          "right_hand_side": rhs[i]} for i in range(2)]
            for p in (2, 3):
                proof = eliminate(equations, 3, p, float("inf"))
                checked = verify(equations, 3, proof)
                points = []
                for x in product(range(p), repeat=3):
                    assignments += 1
                    if all((sum(c*x[j] for j, c in row["terms"])-row["right_hand_side"]) % p == 0 for row in equations):
                        points.append(x)
                assert bool(points) == (checked["kind"] == "consistent_complete_rowspace")
                if points:
                    expected = [(j, points[0][j]) for j in range(3) if all(x[j] == points[0][j] for x in points)]
                    assert [(v["coordinate"], v["residue"]) for v in checked["fixed_coordinates"]] == expected
                exhaustive += 1
    for p in PRIMES:
        for equations, n in (
            ([{"terms": [[0, 2]], "right_hand_side": 1}], 1),
            ([{"terms": [[0, p]], "right_hand_side": 1}], 1),
            ([{"terms": [[0, -1], [1, p-1]], "right_hand_side": p-1},
              {"terms": [[0, p-2], [1, -1]], "right_hand_side": 2-p}], 2),
            ([], 3),
            ([{"terms": [], "right_hand_side": 0}], 0),
            ([{"terms": [], "right_hand_side": 1}], 0),
        ):
            verify(equations, n, eliminate(equations, n, p, float("inf")))
            signed += 1
    equations = [{"terms": [[0, 1]], "right_hand_side": 1}]
    forged = eliminate(equations, 1, 5, float("inf"))
    forged["reduced_rows"][0][-1] = 2
    try:
        verify(equations, 1, forged)
    except AssertionError:
        rejected = True
    else:
        rejected = False
    assert rejected
    return {"complete_two_equation_binary_matrix_controls": exhaustive,
            "field_assignments_enumerated": assignments,
            "large_prime_signed_and_empty_controls": signed,
            "forged_certificate_rejected": True, "case4_eliminations": 0}


def lift_conclusions(data, old, proof, checked):
    n, p = len(data["original_column_ids"]), proof["prime"]
    if checked["kind"] == "modular_inconsistency":
        requests = [(None, checked["contradiction_right_hand_side"], proof["combination"])]
    else:
        requests = [(v["coordinate"], v["residue"], proof["row_combinations"][v["basis_row"]])
                    for v in checked["fixed_coordinates"]]
    answer = []
    for coordinate, residue, combination in requests:
        full, rhs, native_terms = [0]*1214, 0, []
        for multiplier, row in zip(combination, data["equations"]):
            if multiplier:
                native_id = row["representative_original_native_row"]
                native_terms.append([native_id, multiplier])
                for a, c in old[native_id]["terms"]:
                    full[a] += multiplier*c
                rhs += multiplier*old[native_id]["lower"]
        full = [a % p for a in full]
        remaining = [[a, full[a]] for a in data["original_column_ids"] if full[a]]
        original_coordinate = None if coordinate is None else data["original_column_ids"][coordinate]
        assert remaining == ([] if coordinate is None else [[original_coordinate, 1]])
        assert rhs % p == residue
        answer.append({"prime": p, "original_coordinate": original_coordinate, "residue": residue,
                       "original_native_row_combination": native_terms,
                       "full1214_coefficient_support_mod_prime": [[a, c] for a, c in enumerate(full) if c],
                       "removed_known_zero_coefficient_support": [[a, full[a]] for a in data["zero_columns"] if full[a]],
                       "remaining_coefficient_support": remaining,
                       "right_hand_side_mod_prime": rhs % p,
                       "binary_value": residue if coordinate is not None and residue in (0, 1) else None,
                       "binary_obstruction": coordinate is None or residue not in (0, 1)})
    return answer


def prepare(output):
    start = time.monotonic()
    bound, data, old = load_inventory()
    record = {"status": "PASS: certificate-bearing modular audit prepared; no case4 elimination",
              "bindings": bound, "limits": LIMITS, "runtime": runtime(),
              "prime_order": list(PRIMES), "rows": 396, "variables": 1115,
              "all_native_equalities": 632, "known_zeros": 99,
              "arithmetic_bounds": data["arithmetic_proposal"], "controls": controls(),
              "case4_eliminations": 0, "no_new_zero_assumptions": True,
              "rational_rowspace_HNF_and_optimizer_not_run": True,
              "seconds": time.monotonic()-start}
    save_new(output, record)
    return record


def checked_preparation(path):
    prep = json.loads(path.read_bytes())
    bound, data, old = load_inventory()
    assert prep["bindings"] == bound and prep["limits"] == LIMITS
    assert prep["runtime"] == runtime() and prep["prime_order"] == list(PRIMES)
    assert prep["rows"] == 396 and prep["variables"] == 1115 and prep["case4_eliminations"] == 0
    return prep, data, old


def run(preparation, directory):
    start = time.monotonic(); deadline = start+LIMITS["production_batch_seconds"]
    assert not directory.exists()
    directory.mkdir(parents=True)
    report = {"status": "RUNNING: exact modular audit", "bindings": bindings(),
              "preparation_sha256": sha(preparation.read_bytes()), "limits": LIMITS,
              "completed_primes": [], "prime_records": [], "pending_unverified_proposal": None,
              "no_new_zero_assumptions": True, "case4_exclusion_candidate": False,
              "optimizer_calls": 0, "solver_calls": 0, "automatic_retries": 0}
    path = directory/"result.json"
    checkpoint(path, report)
    try:
        prep, data, old = checked_preparation(preparation)
        units = {}
        for p in PRIMES:
            tick(deadline)
            before = time.monotonic()
            proposal = eliminate(data["equations"], 1115, p, deadline)
            raw = canonical(proposal)
            assert len(raw) <= LIMITS["maximum_certificate_bytes"]
            certificate = directory/("prime-"+str(p)+".json.gz")
            certificate.write_bytes(gzip.compress(raw, mtime=0))
            report["pending_unverified_proposal"] = {"prime": p, "file": certificate.name,
                "sha256": sha(certificate.read_bytes()), "raw_sha256": sha(raw)}
            checkpoint(path, report)
            proof_check = verify(data["equations"], 1115, proposal, deadline)
            conclusions = lift_conclusions(data, old, proposal, proof_check)
            if p in inv.SMALL_PRIMES:
                assert proof_check["kind"] == "consistent_complete_rowspace"
            record = {**report["pending_unverified_proposal"], "verification": proof_check,
                      "conclusions": conclusions, "elapsed_seconds": time.monotonic()-before}
            report["prime_records"].append(record)
            report["completed_primes"].append(p)
            report["pending_unverified_proposal"] = None
            for conclusion in conclusions:
                if conclusion["binary_obstruction"]:
                    report["case4_exclusion_candidate"] = True
                else:
                    a, value = conclusion["original_coordinate"], conclusion["binary_value"]
                    if a in units and units[a] != value:
                        report["case4_exclusion_candidate"] = True
                    units[a] = value
            checkpoint(path, report)
            print(json.dumps({"prime": p, "status": proof_check["kind"],
                              "rank": proof_check.get("rank"), "fixed_coordinates": len(conclusions)}), flush=True)
            if report["case4_exclusion_candidate"]:
                break
        report["complete_all_planned_primes"] = report["completed_primes"] == list(PRIMES)
        report["binary_unit_conclusions"] = [[a, value] for a, value in sorted(units.items())]
        report["status"] = ("EXACT_BINARY_OBSTRUCTION: independent cold replay pending"
                            if report["case4_exclusion_candidate"] else "COMPLETE_EXACT_MODULAR_AUDIT: cold replay pending")
    except TimeoutError as error:
        report.update(status="PARTIAL: time budget; only completed prime certificates accepted", reason=str(error),
                      complete_all_planned_primes=False)
    except Exception as error:
        report.update(status="ERROR: no unchecked conclusion promoted", error_type=type(error).__name__, reason=str(error))
        raise
    finally:
        report["elapsed_seconds"] = time.monotonic()-start
        checkpoint(path, report)
    return report


def replay(preparation, directory, output):
    start = time.monotonic(); deadline = start+LIMITS["cold_replay_seconds"]
    prep, data, old = checked_preparation(preparation)
    result = json.loads((directory/"result.json").read_bytes())
    assert result["bindings"] == bindings() and result["limits"] == LIMITS
    assert result["preparation_sha256"] == sha(preparation.read_bytes())
    assert result["completed_primes"] == list(PRIMES[:len(result["prime_records"])])
    assert [v["prime"] for v in result["prime_records"]] == result["completed_primes"]
    records, units, obstruction = [], {}, False
    for record in result["prime_records"]:
        tick(deadline)
        packed = (directory/record["file"]).read_bytes()
        assert sha(packed) == record["sha256"]
        raw = gzip.decompress(packed)
        assert len(raw) <= LIMITS["maximum_certificate_bytes"] and sha(raw) == record["raw_sha256"]
        proof = json.loads(raw)
        assert proof["prime"] == record["prime"]
        checked = verify(data["equations"], 1115, proof, deadline)
        conclusions = lift_conclusions(data, old, proof, checked)
        assert checked == record["verification"] and conclusions == record["conclusions"]
        for conclusion in conclusions:
            if conclusion["binary_obstruction"]:
                obstruction = True
            else:
                a, value = conclusion["original_coordinate"], conclusion["binary_value"]
                if a in units and units[a] != value:
                    obstruction = True
                units[a] = value
        records.append({"prime": proof["prime"], "kind": checked["kind"],
                        "rank": checked.get("rank"), "fixed_coordinates": len(conclusions)})
    assert obstruction == result["case4_exclusion_candidate"]
    if result.get("complete_all_planned_primes"):
        assert result["completed_primes"] == list(PRIMES)
    if "binary_unit_conclusions" in result:
        assert result["binary_unit_conclusions"] == [[a, v] for a, v in sorted(units.items())]
    report = {"status": "PASS: exact Python-integer affine rowspace and conclusion replay",
              "bindings": bindings(), "result_sha256": sha((directory/"result.json").read_bytes()),
              "completed": records, "complete_all_planned_primes": result.get("complete_all_planned_primes", False),
              "binary_unit_conclusions": [[a, v] for a, v in sorted(units.items())],
              "case4_obstruction_verified": obstruction,
              "pending_unverified_proposal_used": False, "elimination_calls": 0,
              "optimizer_calls": 0, "solver_calls": 0, "seconds": time.monotonic()-start}
    save_new(output, report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "run", "replay"))
    parser.add_argument("--preparation", type=Path)
    parser.add_argument("--directory", type=Path)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare":
        assert args.output is not None
        result = prepare(args.output)
    else:
        assert args.preparation is not None and args.directory is not None
        if args.mode == "run":
            result = run(args.preparation, args.directory)
        else:
            assert args.output is not None
            result = replay(args.preparation, args.directory, args.output)
    print(json.dumps({k: result[k] for k in ("status", "seconds", "elapsed_seconds", "complete_all_planned_primes", "case4_obstruction_verified") if k in result}, indent=2))


if __name__ == "__main__":
    main()
