"""Exact fixed-incidence checks for cores with rook-isomorphic interfaces.

The case48 certificate excludes one 72-column incidence assignment, not
all assignments of that 27-vertex core. Replay needs only the standard
library. The two-grid audit records its forced 81 exterior columns.
"""

import argparse
from collections import Counter
from itertools import combinations, product
import json
from pathlib import Path


def rook(x, y):
    return x != y and (x//3 == y//3 or x % 3 == y % 3)


def core(bases=2, third_map=None):
    assert bases in (2, 3)
    assert (third_map is None) == (bases == 2)
    if third_map is not None:
        assert sorted(third_map) == list(range(9))
    n = 9*bases
    rows = [0]*n
    for base in range(bases):
        for x, y in combinations(range(9), 2):
            if rook(x, y):
                a, b = 9*base+x, 9*base+y
                rows[a] |= 1 << b
                rows[b] |= 1 << a
    for a, b in combinations(range(bases), 2):
        mapping = third_map if a else range(9)
        for x, y in enumerate(mapping):
            i, j = 9*a+x, 9*b+y
            rows[i] |= 1 << j
            rows[j] |= 1 << i
    assert all(row.bit_count() == bases+3 for row in rows)
    assert all((rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1) <= 2
               for i, j in combinations(range(n), 2))
    return rows


def gram(rows):
    return [[12*int(i == j)+2-((rows[i] >> j) & 1)-(rows[i] & rows[j]).bit_count()
             for j in range(len(rows))] for i in range(len(rows))]


def check_incidence(rows, signatures):
    n = len(rows)
    assert len(signatures) == 99-n
    assert all(len(s) == n//9 and len(set(s)) == len(s)
               and {i//9 for i in s} == set(range(n//9)) for s in signatures)
    target = gram(rows)
    assert all(sum(i in s and j in s for s in signatures) == target[i][j]
               for i in range(n) for j in range(n))
    need = []
    for sites in signatures:
        mask = sum(1 << i for i in sites)
        row = [2-(adj & mask).bit_count()-int(i in sites) for i, adj in enumerate(rows)]
        assert min(row) >= 0
        need.append(row+[14-len(sites)])
    return need


def allowed_edges(signatures, need):
    """All edges allowed by visible core common-neighbor bounds."""
    answer = []
    for a, b in combinations(range(len(signatures)), 2):
        if len(set(signatures[a]) & set(signatures[b])) > 1:
            continue
        if all(need[a][i] >= 1 for i in signatures[b]) and all(need[b][i] >= 1 for i in signatures[a]):
            answer.append((a, b))
    return answer


def two_grid_audit():
    rows = core()
    signatures = [(i, 9+i) for i in range(9)]
    signatures += [(i, 9+j) for i, j in product(range(9), repeat=2)
                   if i != j and not rook(i, j) for copy in range(2)]
    need = check_incidence(rows, signatures)
    assert Counter(Counter(signatures).values()) == {1: 9, 2: 36}
    pairs = allowed_edges(signatures, need)
    assert len(pairs) == 3060
    return {'status': 'forced incidence verified; edge completion unresolved',
            'core_vertices': 18, 'core_degree': 5, 'outside_vertices': 81,
            'single_diagonal_signatures': 9, 'double_nondiagonal_signatures': 36,
            'outside_degree': 12, 'candidate_outside_edges': len(pairs),
            'signatures': [list(s) for s in signatures]}


def replay_fixed(record):
    source = record['source']
    rows = core(3, source['map'])
    signatures = [tuple(source['signatures'][i]) for i in source['selected']]
    assert len(set(signatures)) == len(signatures) == 72
    need = check_incidence(rows, signatures)
    edges = allowed_edges(signatures, need)
    assert [list(e) for e in edges] == record['edge_pairs']
    n = len(rows)
    equations = len(signatures)*(n+1)
    ray = record['ray']
    assert len(ray) == equations+len(edges)
    assert all(type(x) is int for x in ray)
    coefficients = []
    for edge, (a, b) in enumerate(edges):
        upper = ray[equations+edge]
        assert upper >= 0  # The slack variable in edge + slack = 1.
        value = upper
        for x, y in ((a, b), (b, a)):
            value += sum(ray[x*(n+1)+i] for i in signatures[y])
            value += ray[x*(n+1)+n]
        assert value >= 0
        coefficients.append(value)
    rhs = [value for row in need for value in row]+[1]*len(edges)
    contradiction = sum(a*b for a, b in zip(ray, rhs))
    assert contradiction < 0
    return {'status': 'this fixed incidence has no nonnegative real edge completion',
            'core_vertices': n, 'outside_vertices': len(signatures),
            'candidate_outside_edges': len(edges), 'equations': equations,
            'certificate_nonzero_entries': sum(x != 0 for x in ray),
            'certificate_upper_bound_entries': sum(x != 0 for x in ray[equations:]),
            'certificate_dot_rhs': contradiction,
            'minimum_edge_coefficient': min(coefficients)}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--two-grid-audit', action='store_true')
    parser.add_argument('--fixed-certificate', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    results = {}
    if args.two_grid_audit:
        results['two_grid'] = two_grid_audit()
    if args.fixed_certificate:
        results['fixed_incidence'] = replay_fixed(json.loads(args.fixed_certificate.read_text()))
    assert results
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(results, indent=2)+'\n')
    print(json.dumps({key: {k: v for k, v in value.items() if k != 'signatures'}
                      for key, value in results.items()}), flush=True)
