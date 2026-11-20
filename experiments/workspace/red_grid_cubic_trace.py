"""Exact cubic-trace audit for the eight-all-red-grid exclusion.

Uses integer companion matrices for the restricted spectra, and direct
integer matrix cubes for the rook-holonomy character controls. No numerical
linear algebra, SAT, or floating-point sign decision is used.
"""

import argparse
from collections import Counter
from itertools import permutations, product
import json
from pathlib import Path


def multiply(A, B):
    return [[sum(x*y for x,y in zip(row, column)) for column in zip(*B)] for row in A]


def trace(A):
    return sum(A[i][i] for i in range(len(A)))


def companion_traces(coefficients):
    assert coefficients[0] == 1
    degree = len(coefficients)-1
    M = [[0]*degree for _ in range(degree)]
    for i in range(1, degree):
        M[i][i-1] = 1
    for i in range(degree):
        M[i][-1] = -coefficients[degree-i]
    square = multiply(M, M)
    cube = multiply(square, M)
    return degree, trace(M), trace(square), trace(cube)


def holonomy_controls():
    points = list(product(range(3), repeat=2))
    rook = [[int(i != j and (p[0] == q[0] or p[1] == q[1]))
             for j,q in enumerate(points)] for i,p in enumerate(points)]
    E9 = [[3*rook[i][j]+6*int(i == j)-2 for j in range(9)] for i in range(9)]
    autos = set()
    for sigma,tau,swap in product(permutations(range(3)), permutations(range(3)), (False,True)):
        p = tuple(3*sigma[b if swap else a]+tau[a if swap else b] for a,b in points)
        assert all(rook[p[i]][p[j]] == rook[i][j] for i,j in product(range(9), repeat=2))
        autos.add(p)
    assert len(autos) == 72
    records = []
    for p in sorted(autos):
        if any(rook[i][p[i]] for i in range(9)):
            continue
        fixed = sum(i == p[i] for i in range(9))
        character9 = sum(E9[p[i]][i] for i in range(9))
        assert character9 == 6*fixed-18
        assert character9 % 9 == 0
        # Three grids with identity interfaces 0--1 and 0--2, and p on1--2.
        B = [[0]*27 for _ in range(27)]
        for block in range(3):
            for i,j in product(range(9), repeat=2):
                B[9*block+i][9*block+j] = rook[i][j]
        for i in range(9):
            B[i][9+i] = B[9+i][i] = 1
            B[i][18+i] = B[18+i][i] = 1
            B[9+i][18+p[i]] = B[18+p[i]][9+i] = 1
        cube = multiply(multiply(B, B), B)
        restricted_trace9 = sum(E9[i][j]*cube[9*block+j][9*block+i]
                                for block in range(3) for i,j in product(range(9), repeat=2))
        expected = 4*3+12*3*2-2*3*2*1+4*fixed
        assert restricted_trace9 == 9*expected
        records.append({'permutation': list(p), 'fixed_points': fixed,
                        'rook_one_character': character9//9,
                        'three_base_cubic_trace': restricted_trace9//9})
    assert len(records) == 11
    return {'rook_automorphisms': len(autos), 'allowed_holonomies': len(records),
            'fixed_point_histogram': dict(sorted(Counter(r['fixed_points'] for r in records).items())),
            'controls': records}


def run(spectra_file, output=None):
    source = json.loads(Path(spectra_file).read_text())
    assert source['partitions_checked'] == 30
    records = []
    for case in source['survivors']:
        n = case['type2_vertices']
        assert n % 3 == 0
        for spectrum in case['spectra']:
            total = [0,0,0,0]
            for factor in spectrum['factors']:
                values = companion_traces(factor['polynomial'])
                total = [a+factor['multiplicity']*b for a,b in zip(total,values)]
            rank,s1,s2,s3 = total
            assert (rank,s1,s2) == (spectrum['rank'],spectrum['trace'],spectrum['trace_square'])
            assert 12*rank-s1-s2 == 96
            assert (160-3*rank+s1) % 7 == 0
            actual = s3+s2-12*s1
            required = -4*n//3
            assert actual != required
            records.append({'cycles': case['cycles'], 'rank': rank,
                            'trace': s1, 'trace_square': s2, 'trace_cube': s3,
                            'cubic_left_side': actual, 'required_right_side': required,
                            'excluded': True})
    assert len(records) == source['spectrum_count'] == 12
    result = {'exact_holonomy_controls': holonomy_controls(),
              'spectra_checked': len(records), 'spectra_excluded': len(records),
              'surviving_spectra': 0, 'spectra': records}
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--spectra', default='experiments/logs/grids-and-triangles/eight-red-cycle-spectra.json')
    parser.add_argument('--output')
    args = parser.parse_args()
    run(args.spectra, args.output)
