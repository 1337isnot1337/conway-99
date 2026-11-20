"""Independent exact replay of the seven-red, nine-type2-vertex exclusion.

The catalogue replay bypasses subgraph_counts.extensions. The spectral
replay uses leaf-twin quotients, a direct Sturm test, Newton sums, and full
factor multiplicities without the Krylov subtraction.
"""

import argparse
from itertools import combinations, product
import json
from pathlib import Path

import pynauty
import sympy as sp


X = sp.Symbol('x')


def certificate(neighbors):
    return pynauty.certificate(pynauty.Graph(
        len(neighbors), adjacency_dict={i: sorted(row) for i, row in enumerate(neighbors)}))


def valid(neighbors):
    if any(len(row) > 3 for row in neighbors):
        return False
    return all(len(neighbors[i] & neighbors[j]) <= (0 if j in neighbors[i] else 2)
               for i, j in combinations(range(len(neighbors)), 2))


def catalogue_replay(source):
    assert source['complete'] and source['completed_order'] == 9
    current = [()]
    levels = [1]
    for n in range(1, 10):
        found = {}
        for parent in current:
            for degree in range(min(3, n-1)+1):
                for chosen in combinations(range(n-1), degree):
                    child = [set(row) for row in parent]+[set(chosen)]
                    for v in chosen:
                        child[v].add(n-1)
                    if valid(child):
                        found.setdefault(certificate(child), child)
        current = list(found.values())
        levels.append(len(current))
    archived = []
    for rows in source['graphs']:
        neighbors = [{j for j in range(9) if mask >> j & 1} for mask in rows]
        assert len(neighbors) == 9 and valid(neighbors)
        assert all(i not in neighbors[i] and (j in neighbors[i]) == (i in neighbors[j])
                   for i in range(9) for j in range(9))
        archived.append(certificate(neighbors))
    assert len(archived) == len(set(archived)) == 408
    assert set(archived) == set(found)
    assert levels == [row['types'] for row in source['levels']]
    return levels


def quotient_polynomial(rows):
    """Collapse equal pendant leaves instead of constructing the 36-matrix."""
    degrees = [mask.bit_count() for mask in rows]
    leaves = [3-d for d in degrees]
    edge_count = sum(degrees)//2
    buckets = [i for i, count in enumerate(leaves) if count]
    quotient = sp.zeros(9+len(buckets))
    for i in range(9):
        quotient[i, i] = 1
        for j in range(9):
            if rows[i] >> j & 1:
                quotient[i, j] = 1
    for offset, i in enumerate(buckets, 9):
        quotient[i, offset] = leaves[i]
        quotient[offset, i] = 1
    zero_twins = sum(max(0, count-1) for count in leaves)
    polynomial = sp.Poly(quotient.charpoly(X).as_expr()*X**zero_twins*(X*X-1)**edge_count, X)
    assert polynomial.degree() == 36 and polynomial.LC() == 1
    return polynomial


def variations(signs):
    signs = [1 if value > 0 else -1 for value in signs if value]
    return sum(a != b for a, b in zip(signs, signs[1:]))


def forbidden_root(polynomial):
    """True iff a real root is at least three, by rational Sturm arithmetic."""
    if polynomial.eval(3) == 0:
        return True
    sturm = [polynomial, polynomial.diff()]
    while sturm[-1].degree() > 0:
        remainder = -sturm[-2].rem(sturm[-1])
        if remainder.is_zero:
            break
        sturm.append(remainder)
    at_three = variations([p.eval(3) for p in sturm])
    at_infinity = variations([p.LC() for p in sturm])
    assert at_three >= at_infinity
    return at_three > at_infinity


def traces(coefficients):
    degree = len(coefficients)-1
    a1, a2, a3 = (coefficients[1:]+[0, 0, 0])[:3]
    s1 = -a1
    s2 = -a1*s1-2*a2
    s3 = -a1*s2-a2*s1-3*a3
    return degree, s1, s2, s3


def spectral_replay(catalogue, saved):
    assert saved['complete_requested_range'] and saved['processed'] == 408
    assert saved['start'] == 0 and saved['requested_stop'] == 408
    records = {row['case']: row for row in saved['cores']}
    assert set(records) == set(range(408))
    checked_factors = checked_tuples = 0
    quadratic_survivors = cubic_survivors = 0
    for case, rows in enumerate(catalogue['graphs']):
        archived = records[case]
        edges = [[i, j] for i, j in combinations(range(9), 2) if rows[i] >> j & 1]
        assert edges == archived['edges']
        polynomial = quotient_polynomial(rows)
        factors = [(sp.Poly(f, X, domain=sp.QQ), int(m))
                   for f, m in sp.factor_list(polynomial)[1]]
        reconstructed = sp.prod(sp.Poly.from_list(row['polynomial'], X).as_expr()**row['multiplicity']
                                for row in archived['factor_information'])
        assert sp.Poly(reconstructed, X) == polynomial
        archived_factors = {tuple(row['polynomial']): row for row in archived['factor_information']}
        usable = []
        for factor, multiplicity in factors:
            coefficients = list(map(int, factor.all_coeffs()))
            d, s1, s2, s3 = traces(coefficients)
            energy = 12*d-s1-s2
            blocked = forbidden_root(factor)
            original = archived_factors[tuple(coefficients)]
            assert original['multiplicity'] == multiplicity
            assert original['outside_allowed_interval'] == blocked
            assert original['statistics'] == [d, s1, s2, s3, energy]
            checked_factors += 1
            if not blocked:
                assert energy > 0
                # Keep the entire multiplicity. No Krylov-space deduction.
                usable.append((multiplicity, d, s1, s2, s3, energy))
        case_survivors = 0
        for choices in product(*(range(row[0]+1) for row in usable)):
            checked_tuples += 1
            r = sum(m*row[1] for m, row in zip(choices, usable))
            s1 = sum(m*row[2] for m, row in zip(choices, usable))
            s2 = sum(m*row[3] for m, row in zip(choices, usable))
            s3 = sum(m*row[4] for m, row in zip(choices, usable))
            if r > 28 or 12*r-s1-s2 != 112:
                continue
            numerator = 140-3*r+s1
            if numerator % 7 or not 0 <= numerator//7 <= 28-r:
                continue
            quadratic_survivors += 1
            if s3+s2-12*s1 == 20:
                case_survivors += 1
        cubic_survivors += case_survivors
        assert case_survivors == 0, case
    return {'cores_checked': 408, 'irreducible_factors_checked': checked_factors,
            'factor_multiplicity_tuples_checked': checked_tuples,
            'quadratic_surviving_spectra_without_krylov': quadratic_survivors,
            'cubic_surviving_spectra_without_krylov': cubic_survivors}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/seven-red-type2-core-catalog.json'))
    parser.add_argument('--spectra', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/seven-red-nine-spectra.json'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    catalogue = json.loads(args.catalogue.read_text())
    saved = json.loads(args.spectra.read_text())
    result = {'catalogue_counts': catalogue_replay(catalogue),
              **spectral_replay(catalogue, saved),
              'status': 'exact agreement and exclusion without Krylov subtraction'}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
