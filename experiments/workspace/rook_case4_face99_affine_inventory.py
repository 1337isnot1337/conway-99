"""Exact native-equality inventory on the proved case4 zero face.

Preparation only: no elimination, lattice normal form, optimizer or solver.
Every native lower==upper row is retained in a provenance ledger. The saved
rational point is used only as an exact consistency control, not a premise
restricting the affine domain.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from math import gcd, isqrt
from pathlib import Path
import time

import rook_case4_complete_lp_recovery as original
import rook_case4_transportation_seed as seed

ROOT = Path(__file__).resolve().parents[2]
BASE = "experiments/logs/grids-and-triangles/"
SOURCE_BINDINGS = {
    "rook_case4_complete_lp_recovery.py": "e577327c9cc2471f119c755a49a179b9f94f1004a22de80152a4114787a7eec6",
    "rook_case4_transportation_seed.py": "9eedacb4b62db8ad7058e291d04f83141fca306971ed278a58548ead4cd1e8a1",
}
INPUTS = {
    "native": (BASE+"complement-rook-35core-case0004-native-cpsat-model.json",
               "a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476"),
    "seed": (BASE+"rook-case4-transportation-seed-certificate.json",
             "64d8e375280bc067097913de2dd6e2995c19de2a4807f63cecdcd80b811a85cf"),
    "point": (BASE+"rook-case4-face99-basis-run01/candidate.json",
              "0b627484317e65562500fbbbbd594e4a95dbfa809576fae52f6c7ccdbe7191e7"),
    "point_replay": (BASE+"rook-case4-face99-basis-run01-replay.json",
                     "2804da9ac0e976d7dc566b3be9cabef861ed24727221db72d4fc5da26f3a438d"),
}
PRIMARY_SHA = "5a6af30f47826df629a3795ceea0a0a91b853cf8149860355ce1bd17ac0094b2"
SMALL_PRIMES = (2, 3, 5, 7)
DENOMINATOR = 1661041997


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def checked_json(root, path, expected):
    raw = (root/path).read_bytes()
    assert sha(raw) == expected
    return json.loads(raw)


def check_time(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError("affine inventory preparation deadline")


def prime_by_trial(n):
    assert type(n) is int and n >= 2
    return all(n % d for d in range(2, isqrt(n)+1))


def factor_integer(n):
    assert type(n) is int and n >= 1
    initial, factors, trial = n, [], 2
    while trial*trial <= n:
        exponent = 0
        while n % trial == 0:
            n //= trial
            exponent += 1
        if exponent:
            factors.append([trial, exponent])
        trial = 3 if trial == 2 else trial+2
    if n > 1:
        factors.append([n, 1])
    product = 1
    for p, exponent in factors:
        assert prime_by_trial(p) and exponent >= 1
        product *= p**exponent
    assert product == initial
    return factors


def equalities(rows, kept):
    position = {a: i for i, a in enumerate(kept)}
    ledger, equations, lookup = [], [], {}
    for original_id, row in enumerate(rows):
        if row["lower"] != row["upper"]:
            continue
        assert type(row["lower"]) is int
        terms = [[position[a], c] for a, c in row["terms"] if a in position]
        removed = [[a, c] for a, c in row["terms"] if a not in position]
        assert terms == sorted(terms) and len({a for a, c in terms}) == len(terms)
        assert all(type(c) is int and c for a, c in terms)
        rhs = row["lower"]
        record = {"original_native_row": original_id, "family": row["family"],
                  "original_terms": row["terms"], "right_hand_side": rhs,
                  "removed_proved_zero_terms": removed, "remaining_terms": terms}
        if not terms:
            assert rhs == 0, "empty native equality contradicts the fixed face"
            record["equation_id"] = None
            record["disposition"] = "exact_zero_equals_zero"
        else:
            key = (tuple(map(tuple, terms)), rhs)
            if key not in lookup:
                lookup[key] = len(equations)
                equations.append({"equation_id": len(equations), "terms": terms,
                                  "right_hand_side": rhs,
                                  "representative_original_native_row": original_id,
                                  "all_original_native_rows": []})
            index = lookup[key]
            equations[index]["all_original_native_rows"].append(original_id)
            record["equation_id"] = index
            record["disposition"] = "exact_duplicate_or_representative"
        ledger.append(record)
    assert sorted(i for item in equations for i in item["all_original_native_rows"]) == \
        [item["original_native_row"] for item in ledger if item["equation_id"] is not None]
    return ledger, equations


def modular_point(equations, numerators, denominator, prime):
    assert prime_by_trial(prime) and gcd(denominator, prime) == 1
    inverse = pow(denominator, -1, prime)
    point = [(a*inverse) % prime for a in numerators]
    for row in equations:
        assert (sum(c*point[a] for a, c in row["terms"])-row["right_hand_side"]) % prime == 0
    return {"prime": prime, "denominator_mod_prime": denominator % prime,
            "inverse_denominator_mod_prime": inverse,
            "coordinates": point, "all_unique_equations_checked": len(equations)}


def controls():
    for n in range(1, 101):
        factor_integer(n)
    toy = [
        {"terms": [[0, 1], [1, 1]], "lower": 1, "upper": 1, "family": "toy"},
        {"terms": [[1, 1]], "lower": 1, "upper": 1, "family": "toy"},
        {"terms": [[0, -3]], "lower": 0, "upper": 0, "family": "toy"},
        {"terms": [[1, 1]], "lower": 0, "upper": 1, "family": "inequality"},
    ]
    ledger, eqs = equalities(toy, [1])
    assert len(ledger) == 3 and len(eqs) == 1
    assert eqs[0]["all_original_native_rows"] == [0, 1]
    assert ledger[2]["equation_id"] is None
    assert modular_point(eqs, [1], 1, 2)["coordinates"] == [1]
    fractional = [{"terms": [[0, 3]], "right_hand_side": 1}]
    for p in (2, 5, 7):
        modular_point(fractional, [1], 3, p)
    return {"factorization_controls": 100,
            "exact_zero_substitution_duplicate_and_inequality_controls": True,
            "rational_modular_consistency_controls": 4,
            "elimination_calls": 0}


def build(root, seconds):
    started = time.monotonic()
    deadline = started+seconds
    sources = {}
    for name, expected in SOURCE_BINDINGS.items():
        assert sha(Path(__file__).with_name(name).read_bytes()) == expected
        sources[name] = expected
    loaded = {name: checked_json(root, *item) for name, item in INPUTS.items()}
    check_time(deadline)
    native = loaded["native"]
    assert native["complete"] and native["case_index"] == 4
    inventory = native["primary_inventory"]
    assert sha(canonical(inventory)) == native["primary_inventory_sha256"] == PRIMARY_SHA
    original_rows = original.original_rows(inventory)
    assert len(original_rows) == 2271
    seed_proof = seed.prove(root)
    assert canonical(seed_proof) == canonical(loaded["seed"])
    zeros = seed_proof["seed_zero_columns"]
    assert len(zeros) == len(set(zeros)) == 99
    kept = [a for a in range(1214) if a not in set(zeros)]
    assert len(kept) == 1115
    ledger, equations = equalities(original_rows, kept)
    check_time(deadline)

    saved_point = loaded["point"]
    denominator = int(saved_point["common_denominator"])
    assert denominator == DENOMINATOR
    extended = list(map(int, saved_point["extended_numerators"]))
    assert len(extended) == 1116 and extended[-1] > 0
    assert all(0 < value < denominator for value in extended[:-1])
    full = [0]*1214
    for a, value in zip(kept, extended[:-1]):
        full[a] = value
    for row in original_rows:
        total = sum(c*full[a] for a, c in row["terms"])
        assert row["lower"]*denominator <= total <= row["upper"]*denominator
    assert loaded["point_replay"]["status"].startswith("PASS")
    factors = factor_integer(denominator)
    assert factors == [[19, 1], [601, 1], [145463, 1]]
    congruence_controls = [modular_point(equations, extended[:-1], denominator, p) for p in SMALL_PRIMES]
    prime_plan = [p for p, exponent in factors]+list(SMALL_PRIMES)
    m, n = len(equations), len(kept)
    maximum_norm_squared = max(sum(c*c for a, c in row["terms"])+row["right_hand_side"]**2 for row in equations)
    hadamard_squared_bound = 1
    for row in equations:
        hadamard_squared_bound *= max(1, sum(c*c for a, c in row["terms"])+row["right_hand_side"]**2)
    determinant_bit_bound = (hadamard_squared_bound.bit_length()+1)//2
    max_prime = max(prime_plan)
    integer_vector_update_bound = (max_prime-1)**2+(max_prime-1)
    integer_dot_bound = m*(max_prime-1)**2
    assert max(integer_vector_update_bound, integer_dot_bound) < 2**63
    budget = {"planned_prime_order": prime_plan,
              "priority_inconsistency_primes": [p for p, exponent in factors],
              "small_primes_already_proved_consistent": list(SMALL_PRIMES),
              "dense_augmented_matrix_shape": [m, n+1],
              "dense_row_combination_witness_shape": [m, m],
              "int64_matrix_plus_witness_bytes": 8*m*(n+1+m),
              "conservative_entry_updates_per_prime": m*min(m, n)*(n+1+m),
              "maximum_planned_prime": max_prime,
              "modular_vector_update_absolute_bound": integer_vector_update_bound,
              "modular_dense_dot_absolute_bound": integer_dot_bound,
              "all_proposed_int64_arithmetic_bounds_below_2pow63": True,
              "maximum_augmented_row_norm_squared": maximum_norm_squared,
              "augmented_minor_Hadamard_absolute_bit_bound": determinant_bit_bound,
              "elimination_started": False,
              "proposed_modular_phase_seconds": 60,
              "rational_rowspace_phase_requires_separate_gate": True,
              "HNF_or_SNF_not_prepared_or_run": True}
    result = {"schema": "rook-case4-face99-native-affine-inventory-v1",
              "status": "PASS: complete exact native equality inventory; no elimination",
              "source_sha256": sha(Path(__file__).read_bytes()),
              "source_bindings": sources,
              "input_bindings": {k: {"path": p, "sha256": h} for k, (p, h) in INPUTS.items()},
              "primary_inventory_sha256": PRIMARY_SHA,
              "original_native_rows_sha256": sha(canonical(original_rows)),
              "zero_columns": zeros, "zero_provenance": seed_proof["seed_reasons"],
              "original_column_ids": kept,
              "all_native_rows": 2271, "all_native_equality_rows": len(ledger),
              "equality_family_counts": dict(Counter(row["family"] for row in ledger)),
              "empty_equalities_after_substitution": sum(row["equation_id"] is None for row in ledger),
              "unique_nonempty_equality_rows": m,
              "unique_equality_nonzeros": sum(len(row["terms"]) for row in equations),
              "equality_provenance": ledger, "equations": equations,
              "saved_point_control": {"denominator": denominator,
                  "prime_factorization": factors, "all_factors_prime_by_complete_trial_division": True,
                  "all2271_native_rows_checked_exactly": True,
                  "all99_zeros_and_all1115_strictly_positive_coordinates_checked": True,
                  "point_values_are_not_affine_constraints": True,
                  "extended_t_is_not_an_affine_variable_or_constraint": True},
              "modular_consistency_controls": congruence_controls,
              "arithmetic_proposal": budget,
              "controls": controls(),
              "scope": "Only all native lower==upper rows after the99 proved zeros. Inequalities, binary bounds and covers are not promoted to equalities. No new zero or one assumption.",
              "optimizer_calls": 0, "solver_calls": 0, "elimination_calls": 0,
              "new_unit_conclusions": [], "case4_excluded": False}
    check_time(deadline)
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("prepare", "replay"))
    parser.add_argument("--root", type=Path, default=ROOT)
    parser.add_argument("--certificate", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--seconds", type=int, default=30)
    args = parser.parse_args()
    assert 0 < args.seconds <= 30 and not args.output.exists()
    started = time.monotonic()
    result = build(args.root, args.seconds)
    raw = canonical(result)
    if args.mode == "prepare":
        assert not args.certificate.exists()
        args.certificate.write_bytes(gzip.compress(raw, mtime=0))
    else:
        assert canonical(json.loads(gzip.decompress(args.certificate.read_bytes()))) == raw
    report = {"status": "PASS: affine inventory "+("prepared" if args.mode == "prepare" else "cold replayed"),
              "source_sha256": result["source_sha256"],
              "certificate_gzip_sha256": sha(args.certificate.read_bytes()),
              "certificate_raw_sha256": sha(raw),
              "certificate_bytes": args.certificate.stat().st_size,
              "all_native_equality_rows": result["all_native_equality_rows"],
              "equality_family_counts": result["equality_family_counts"],
              "empty_equalities_after_substitution": result["empty_equalities_after_substitution"],
              "unique_nonempty_equality_rows": result["unique_nonempty_equality_rows"],
              "unique_equality_nonzeros": result["unique_equality_nonzeros"],
              "arithmetic_proposal": result["arithmetic_proposal"],
              "saved_point_control": result["saved_point_control"],
              "controls": result["controls"],
              "elimination_calls": 0, "optimizer_calls": 0, "solver_calls": 0,
              "seconds": time.monotonic()-started}
    args.output.write_text(json.dumps(report, indent=2)+"\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
