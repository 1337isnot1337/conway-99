"""Exact GF(2)/GF(3) bit-plane checks for an integer equality system.

No optimizer. A consistent result carries a complete modular point. An
inconsistent result carries an original-row combination with zero left
side and nonzero right side. A timeout reports only the processed prefix.
"""
import hashlib
from itertools import product
import json
import time


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":")).encode()


def add3(left, right):
    a, b = left
    c, d = right
    az, bz = ~(a | b), ~(c | d)
    return ((az & c) | (a & bz) | (b & d),
            (az & d) | (b & bz) | (a & c))


def encode(row, variables, prime):
    planes = [0] * (prime - 1)
    for j, c in row["terms"] + [[variables, row["rhs"]]]:
        assert 0 <= j <= variables
        c %= prime
        if c:
            assert not any(x >> j & 1 for x in planes)
            planes[c - 1] |= 1 << j
    return tuple(planes)


def sparse_combination(planes, count, prime):
    answer = []
    for coefficient, plane in enumerate(planes, 1):
        while plane:
            bit = plane & -plane
            j = bit.bit_length() - 1
            assert j < count
            answer.append([j, coefficient])
            plane ^= bit
    return sorted(answer)


def verify_contradiction(rows, variables, prime, terms):
    total = [0] * (variables + 1)
    assert len({i for i, _ in terms}) == len(terms)
    for i, multiplier in terms:
        assert 0 <= i < len(rows) and 1 <= multiplier < prime
        for j, c in rows[i]["terms"]:
            total[j] = (total[j] + multiplier * c) % prime
        total[-1] = (total[-1] + multiplier * rows[i]["rhs"]) % prime
    assert not any(total[:-1]) and total[-1]
    return {"zero_left_coordinates_checked": variables,
            "nonzero_right_residue": total[-1],
            "original_rows_in_combination": len(terms)}


def verify_point(rows, variables, prime, point):
    assert len(point) == variables and all(type(v) is int and 0 <= v < prime for v in point)
    for i, row in enumerate(rows):
        assert (sum(c * point[j] for j, c in row["terms"]) - row["rhs"]) % prime == 0, i
    return {"all_equalities_checked": len(rows), "variables": variables,
            "bounds_or_integer_feasibility_claimed": False}


def eliminate(rows, variables, prime, deadline):
    assert prime in (2, 3)
    mask = (1 << variables) - 1
    basis = {}
    order = sorted(range(len(rows)), key=lambda i: (sum(c % prime != 0 for _, c in rows[i]["terms"]), i))
    processed, reductions = 0, 0
    started = time.monotonic()
    for original in order:
        if time.monotonic() >= deadline:
            return {"status": "TIME_LIMIT: equality prefix only", "prime": prime,
                    "processed_equalities": processed, "total_equalities": len(rows),
                    "prefix_rank": len(basis), "bit_plane_reductions": reductions,
                    "seconds": time.monotonic() - started}
        row = encode(rows[original], variables, prime)
        provenance = (1 << original,) if prime == 2 else (1 << original, 0)
        while True:
            occupied = row[0] if prime == 2 else row[0] | row[1]
            left = occupied & mask
            if not left:
                if occupied >> variables & 1:
                    terms = sparse_combination(provenance, len(rows), prime)
                    check = verify_contradiction(rows, variables, prime, terms)
                    return {"status": "INCONSISTENT: exact modular row combination",
                            "prime": prime, "processed_equalities": processed + 1,
                            "total_equalities": len(rows), "prefix_rank": len(basis),
                            "original_row_combination": terms, "direct_check": check,
                            "bit_plane_reductions": reductions,
                            "seconds": time.monotonic() - started}
                break
            pivot = left.bit_length() - 1
            if pivot not in basis:
                if prime == 3 and row[1] >> pivot & 1:
                    row = (row[1], row[0])
                    provenance = (provenance[1], provenance[0])
                basis[pivot] = (row, provenance)
                break
            other, other_provenance = basis[pivot]
            if prime == 2:
                row = (row[0] ^ other[0],)
                provenance = (provenance[0] ^ other_provenance[0],)
            else:
                # Normalize pivots to 1. Subtract the pivot coefficient:
                # subtraction of one swaps planes, subtraction of two adds.
                if row[0] >> pivot & 1:
                    other = (other[1], other[0])
                    other_provenance = (other_provenance[1], other_provenance[0])
                row = add3(row, other)
                provenance = add3(provenance, other_provenance)
                assert not (row[0] & row[1]) and not (provenance[0] & provenance[1])
            reductions += 1
            if reductions % 4096 == 0 and time.monotonic() >= deadline:
                return {"status": "TIME_LIMIT: equality prefix only", "prime": prime,
                        "processed_equalities": processed, "total_equalities": len(rows),
                        "prefix_rank": len(basis), "bit_plane_reductions": reductions,
                        "seconds": time.monotonic() - started}
        processed += 1
    # Ascending pivots are a triangular back-substitution because the leading
    # coordinate of every stored row is its largest nonzero variable index.
    solution = [0] * variables
    solution_planes = [0] * (prime - 1)
    for pivot in sorted(basis):
        row, _ = basis[pivot]
        rhs = sum(coefficient * ((plane >> variables) & 1)
                  for coefficient, plane in enumerate(row, 1))
        total = sum(a * b * (ra & sb).bit_count()
                    for a, ra in enumerate(row, 1)
                    for b, sb in enumerate(solution_planes, 1))
        value = (rhs - total) % prime
        solution[pivot] = value
        if value:
            solution_planes[value - 1] |= 1 << pivot
    check = verify_point(rows, variables, prime, solution)
    echelon = [{"pivot": pivot,
                "augmented_row_planes_hex": [hex(v) for v in basis[pivot][0]],
                "original_row_combination_planes_hex": [hex(v) for v in basis[pivot][1]]}
               for pivot in sorted(basis)]
    return {"status": "CONSISTENT: complete exact modular point", "prime": prime,
            "processed_equalities": processed, "total_equalities": len(rows),
            "computed_rank": len(basis), "pivot_columns": sorted(basis),
            "point": solution, "direct_check": check,
            "echelon_certificate": echelon,
            "echelon_sha256": hashlib.sha256(canonical(echelon)).hexdigest(),
            "bit_plane_reductions": reductions, "seconds": time.monotonic() - started}


def controls():
    addition_checks = 0
    for a, b in product(range(3), repeat=2):
        x = (int(a == 1), int(a == 2))
        y = (int(b == 1), int(b == 2))
        answer = add3(x, y)
        assert answer == (int((a + b) % 3 == 1), int((a + b) % 3 == 2))
        addition_checks += 1
    systems, explicit_points = 0, 0
    for prime in (2, 3):
        candidates = [{"terms": [[j, c] for j, c in enumerate(coefficients[:2]) if c],
                       "rhs": coefficients[2]}
                      for coefficients in product(range(prime), repeat=3)]
        for left, right in product(candidates, repeat=2):
            rows = [left, right]
            points = [p for p in product(range(prime), repeat=2)
                      if all((sum(c * p[j] for j, c in r["terms"]) - r["rhs"]) % prime == 0 for r in rows)]
            actual = eliminate(rows, 2, prime, time.monotonic() + 2)
            assert actual["status"].startswith("CONSISTENT") == bool(points)
            if points:
                assert len(points) == prime ** (2 - actual["computed_rank"])
            else:
                verify_contradiction(rows, 2, prime, actual["original_row_combination"])
            systems += 1
            explicit_points += prime ** 2
    return {"GF3_single_coordinate_additions": addition_checks,
            "all_two_equation_two_variable_systems_checked": systems,
            "explicit_point_checks": explicit_points, "optimizer_calls": 0}
