"""Exact closest-forbidden-vertex separation for one Boolean parity row.

Only integer numerators and a positive common denominator are accepted.
The control command reads no case4 point or domain and calls no optimizer.
"""
import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
import time


def closest_forbidden(support, rhs, numerators, denominator):
    assert type(rhs) is int and rhs in (0, 1)
    assert type(denominator) is int and denominator > 0
    assert support == sorted(set(support))
    assert all(type(i) is int and 0 <= i < len(numerators) for i in support)
    assert all(type(numerators[i]) is int and 0 <= numerators[i] <= denominator for i in support)
    ones = [i for i in support if 2*numerators[i] > denominator]
    nearest_parity = len(ones) % 2
    cost = sum(min(numerators[i], denominator-numerators[i]) for i in support)
    base_cost, flipped, penalty = cost, None, 0
    if nearest_parity == rhs:
        if not support:
            return None  # The empty support with RHS0 has no forbidden vertex.
        flipped = min(support, key=lambda i: (abs(denominator-2*numerators[i]), i))
        penalty = abs(denominator-2*numerators[flipped])
        ones = sorted(set(ones) ^ {flipped})
        cost += penalty
    assert len(ones) % 2 == 1-rhs
    ones_set = set(ones)
    direct_cost = sum(denominator-numerators[i] if i in ones_set else numerators[i] for i in support)
    assert direct_cost == cost
    return {"support": support, "parity_rhs": rhs, "forbidden_ones": ones,
            "nearest_rounding_parity": nearest_parity, "flipped_coordinate": flipped,
            "base_cost_numerator": base_cost, "parity_adjustment_numerator": penalty,
            "distance_numerator": cost, "denominator": denominator,
            "strictly_violated": cost < denominator}


def inequality(certificate):
    support, rhs, ones = (certificate[k] for k in ("support", "parity_rhs", "forbidden_ones"))
    assert support == sorted(set(support)) and ones == sorted(set(ones))
    assert set(ones) <= set(support) and len(ones) % 2 == 1-rhs
    selected = set(ones)
    return {"terms": [[i, 1 if i in selected else -1] for i in support],
            "upper": len(ones)-1}


def check_exact(certificate, numerators, denominator):
    actual = closest_forbidden(certificate["support"], certificate["parity_rhs"], numerators, denominator)
    assert actual == certificate
    row = inequality(certificate)
    gap = sum(c*numerators[i] for i, c in row["terms"])-row["upper"]*denominator
    assert gap == denominator-certificate["distance_numerator"]
    assert (gap > 0) == certificate["strictly_violated"]
    return {"inequality": row, "exact_violation_numerator": gap}


def controls():
    started = time.monotonic()
    formula_cases, vertex_distances, valid_vertex_checks = 0, 0, 0
    empty_controls, tie_controls = 0, 0
    for denominator, maximum_size in ((1, 8), (2, 6), (3, 5)):
        for n in range(maximum_size+1):
            support = [2*i+1 for i in range(n)]  # Deliberately nonconsecutive IDs.
            vertices = list(product((0, 1), repeat=n))
            for selected_values in product(range(denominator+1), repeat=n):
                numerators = [0]*(2*n+1)
                for i, value in zip(support, selected_values):
                    numerators[i] = value
                brute = {0: [], 1: []}
                for vertex in vertices:
                    distance = sum(denominator-value if bit else value
                                   for value, bit in zip(selected_values, vertex))
                    brute[sum(vertex) % 2].append(distance)
                    vertex_distances += 1
                for rhs in (0, 1):
                    formula_cases += 1
                    certificate = closest_forbidden(support, rhs, numerators, denominator)
                    costs = brute[1-rhs]
                    if not costs:
                        assert certificate is None and n == 0 and rhs == 0
                        empty_controls += 1
                        continue
                    assert certificate["distance_numerator"] == min(costs)
                    check = check_exact(certificate, numerators, denominator)
                    if any(2*value == denominator for value in selected_values):
                        tie_controls += 1
                    for vertex in vertices:
                        if sum(vertex) % 2 != rhs:
                            continue
                        values = {i: bit for i, bit in zip(support, vertex)}
                        row = check["inequality"]
                        assert sum(c*values[i] for i, c in row["terms"]) <= row["upper"]
                        valid_vertex_checks += 1
    assert formula_cases == 5938
    large_integer_controls = 0
    for denominator in ((1 << 130)+1, 1 << 131, 1661041997):
        numerators = [0, 1, denominator//2, denominator-1, denominator]
        support = list(range(5))
        for rhs in (0, 1):
            certificate = closest_forbidden(support, rhs, numerators, denominator)
            check_exact(certificate, numerators, denominator)
            expected = min(sum(denominator-n if bit else n for n, bit in zip(numerators, vertex))
                           for vertex in product((0, 1), repeat=5) if sum(vertex) % 2 != rhs)
            assert certificate["distance_numerator"] == expected
            large_integer_controls += 1
    impossible_empty = closest_forbidden([], 1, [], 1)
    assert inequality(impossible_empty) == {"terms": [], "upper": -1}
    assert impossible_empty["strictly_violated"]
    # A box-interior rational point can violate parity despite obeying its
    # underlying real unit box. This is a Boolean condition, not an equality.
    example = closest_forbidden([0, 1], 0, [9, 1], 10)
    assert example["forbidden_ones"] == [0] and example["distance_numerator"] == 2
    assert inequality(example) == {"terms": [[0, 1], [1, -1]], "upper": 0}
    return {"status": "PASS: exact parity-distance formula and forbidden-vertex inequalities",
        "formula_cases": formula_cases, "direct_vertex_distance_evaluations": vertex_distances,
        "valid_parity_vertex_inequality_checks": valid_vertex_checks,
        "empty_tautology_controls": empty_controls, "half-coordinate_tie_controls": tie_controls,
        "large_integer_controls": large_integer_controls, "empty_inconsistent_parity_control": True,
        "strict_rational_separator_control": example,
        "case4_point_or_domain_read": False, "optimizer_calls": 0,
        "seconds": time.monotonic()-started}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = controls()
    result["source_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2)+"\n")
    print(json.dumps(result, indent=2))
