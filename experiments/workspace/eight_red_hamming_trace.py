"""Exact local and arithmetic control of the all-three-triangle obstruction.

This does not enumerate 27-vertex graphs or assume a linear base projection.
It verifies the rook function identity and the integer trace contradiction
used in research/grids-and-triangles/eight_red_hamming_trace.md.
"""

import argparse
from fractions import Fraction
from itertools import combinations, permutations, product
import json
from pathlib import Path


def rank(matrix):
    a = [[Fraction(x) for x in row] for row in matrix]
    pivot = 0
    for col in range(len(a[0])):
        row = next((r for r in range(pivot, len(a)) if a[r][col]), None)
        if row is None:
            continue
        a[pivot], a[row] = a[row], a[pivot]
        scale = a[pivot][col]
        a[pivot] = [x / scale for x in a[pivot]]
        for r in range(len(a)):
            if r != pivot and a[r][col]:
                scale = a[r][col]
                a[r] = [x - scale*y for x, y in zip(a[r], a[pivot])]
        pivot += 1
    return pivot


def check():
    points = list(product(range(3), repeat=2))
    adjacent = [{j for j, y in enumerate(points)
                 if x != y and (x[0] == y[0] or x[1] == y[1])}
                for x in points]
    basis = [[int(x[0] == 0)-int(x[0] == 2),
              int(x[0] == 1)-int(x[0] == 2),
              int(x[1] == 0)-int(x[1] == 2),
              int(x[1] == 1)-int(x[1] == 2)] for x in points]
    assert rank(basis) == 4
    assert all(sum(row[c] for row in basis) == 0 for c in range(4))
    assert all(sum(basis[j][c] for j in adjacent[i]) == basis[i][c]
               for i in range(9) for c in range(4))
    transversals = [triple for triple in combinations(range(9), 3)
                    if all(j not in adjacent[i] for i, j in combinations(triple, 2))]
    expected = {tuple(3*i+p[i] for i in range(3)) for p in permutations(range(3))}
    assert set(transversals) == expected and len(transversals) == 6
    local_checks = 0
    for triple in transversals:
        assert all(sum(basis[i][c] for i in triple) == 0 for c in range(4))
        for i in triple:
            for c in range(4):
                selected = sum(basis[j][c] for j in adjacent[i])
                omitted = sum(basis[j][c] for j in triple if j != i)
                assert selected + omitted == 0
            local_checks += 1

    red_bases, eigenspace_per_base, fiber_size = 8, 4, 3
    w_dimension = red_bases * eigenspace_per_base
    gram_trace = fiber_size * w_dimension
    assert gram_trace % 12 == 0
    t_rank = gram_trace // 12
    invariant_dimension = w_dimension + t_rank
    invariant_trace = w_dimension
    numerator = invariant_trace + 4 * invariant_dimension
    assert numerator % 7 != 0
    return {
        'hypothesis': 'eight all-red grids, every remainder vertex in three internal triangles',
        'status': 'excluded by invariant-space trace',
        'rook_eigenvalue_one_dimension': rank(basis),
        'rook_transversals': len(transversals),
        'local_function_identities_checked': local_checks,
        'red_eigenspace_dimension': w_dimension,
        'trace_T_star_T': gram_trace,
        'forced_rank_T': t_rank,
        'invariant_dimension': invariant_dimension,
        'invariant_trace': invariant_trace,
        'required_eigenvalue_three_multiplicity': str(Fraction(numerator, 7)),
        'integer_contradiction': f'7r = {numerator}',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = check()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
