"""Independent direct-matrix audit of the eight-red residual-cycle spectra.

Builds cycle matrices instead of using the Chebyshev recurrence, and uses
Cartesian products instead of the search recursion in eight_red_cycle_spectra.
This checks the necessary spectral census, not the surrounding graph proof.
"""

import argparse
from collections import Counter
from itertools import combinations_with_replacement, product
import json
from pathlib import Path

import sympy as sp


def audit(path):
    source = json.loads(path.read_text())
    x = sp.Symbol('x')
    cycle_factors = {}
    for length in range(6, 28, 3):
        matrix = sp.eye(length)
        for i in range(length):
            matrix[i, (i+1) % length] = 1
            matrix[(i+1) % length, i] = 1
        polynomial = matrix.charpoly(x).as_expr()
        factorization = sp.factor_list(polynomial, x)[1]
        assert sp.expand(sp.prod(f**m for f, m in factorization)) == polynomial
        cycle_factors[length] = Counter({tuple(map(int, sp.Poly(f, x).all_coeffs())): int(m)
                                        for f, m in factorization})
        assert cycle_factors[length][(1, -3)] == 1
        del cycle_factors[length][(1, -3)]

    partitions = {()}
    for count in range(1, 5):
        partitions.update(p for p in combinations_with_replacement(range(6, 28, 3), count)
                          if sum(p) <= 27)
    archived = {tuple(case['cycles']): case for case in source['all_cases']}
    assert set(archived) == partitions
    total_spectra = 0
    survivors = []
    for cycles in sorted(partitions, key=lambda c: (sum(c), c)):
        n = sum(cycles)
        capacities = Counter({(1, 0): 27-n-int(n < 27)})
        for length in cycles:
            capacities.update(cycle_factors[length])
        capacities += Counter()  # Remove zero capacities.
        items = sorted(capacities.items())
        statistics = []
        for coefficients, capacity in items:
            degree = len(coefficients)-1
            trace = -coefficients[1]
            square_trace = trace*trace-(2*coefficients[2] if degree > 1 else 0)
            statistics.append((degree, trace, square_trace))
        found = set()
        for multiplicities in product(*(range(m+1) for _, m in items)):
            rank = sum(m*t[0] for m, t in zip(multiplicities, statistics))
            trace = sum(m*t[1] for m, t in zip(multiplicities, statistics))
            square_trace = sum(m*t[2] for m, t in zip(multiplicities, statistics))
            if rank > 26 or 12*rank-trace-square_trace != 96:
                continue
            numerator = 160-3*rank+trace
            if numerator % 7 or not 0 <= numerator//7 <= 32-rank:
                continue
            factors = tuple((coefficients, m) for (coefficients, _), m in zip(items, multiplicities) if m)
            found.add((rank, trace, square_trace, factors))
        recorded = set()
        for spectrum in archived[cycles]['spectra']:
            factors = tuple(sorted((tuple(f['polynomial']), f['multiplicity'])
                                   for f in spectrum['factors']))
            recorded.add((spectrum['rank'], spectrum['trace'], spectrum['trace_square'], factors))
        assert found == recorded, cycles
        total_spectra += len(found)
        if found:
            survivors.append({'cycles': list(cycles), 'spectra': len(found)})
    assert total_spectra == source['spectrum_count']
    return {'direct_cycle_matrices_checked': len(cycle_factors),
            'independent_partitions_checked': len(partitions),
            'independent_spectra_checked': total_spectra,
            'survivors': survivors,
            'status': 'exact agreement'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('spectra', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit(args.spectra)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result), flush=True)
