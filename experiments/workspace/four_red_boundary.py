"""Solver-free boundary obstruction for the surviving four-rook core.

The explicit root-gauged interfaces have labels [1,6,7] in the sorted
eleven-map list. Only27 outside signatures pass pair quotas;63 distinct
signatures would be needed. Exact Gram-kernel and fifth-base checks are
additional controls, not assumptions of the counting contradiction.
"""

import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations, permutations, product
import json
from math import gcd, lcm
from pathlib import Path


INTERFACES = {
    (1, 2): (0, 3, 6, 1, 4, 7, 2, 5, 8),
    (1, 3): (5, 8, 2, 3, 6, 0, 4, 7, 1),
    (2, 3): (7, 1, 4, 8, 2, 5, 6, 0, 3),
}


def rook(i, j):
    return i != j and (i//3 == j//3 or i % 3 == j % 3)


def allowed_maps():
    group = {tuple(3*sigma[b if swap else a]+tau[a if swap else b]
                   for a, b in product(range(3), repeat=2))
             for sigma, tau, swap in product(permutations(range(3)), permutations(range(3)), (0, 1))}
    assert len(group) == 72
    answer = sorted(p for p in group if all(not rook(i, p[i]) for i in range(9)))
    assert len(answer) == 11
    assert [answer.index(INTERFACES[e]) for e in ((1, 2), (1, 3), (2, 3))] == [1, 6, 7]
    return answer


def core():
    rows = [0]*36
    for base in range(4):
        for i, j in combinations(range(9), 2):
            if rook(i, j):
                a, b = 9*base+i, 9*base+j
                rows[a] |= 1 << b; rows[b] |= 1 << a
    for i, j in combinations(range(4), 2):
        mapping = tuple(range(9)) if i == 0 else INTERFACES[i, j]
        assert all(rook(x, y) == rook(mapping[x], mapping[y]) for x, y in combinations(range(9), 2))
        for x, y in enumerate(mapping):
            a, b = 9*i+x, 9*j+y
            rows[a] |= 1 << b; rows[b] |= 1 << a
    assert all(row.bit_count() == 7 for row in rows)
    assert all((rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1) <= 2
               for i, j in combinations(range(36), 2))
    return rows


def gram(rows):
    return [[12*int(i == j)+2-((rows[i] >> j) & 1)-(rows[i] & rows[j]).bit_count()
             for j in range(len(rows))] for i in range(len(rows))]


def integral_kernel(matrix):
    a = [[Fraction(x) for x in row] for row in matrix]
    n = len(a); pivots = []
    for column in range(n):
        pivot = next((r for r in range(len(pivots), n) if a[r][column]), None)
        if pivot is None:
            continue
        position = len(pivots)
        a[position], a[pivot] = a[pivot], a[position]
        scale = a[position][column]
        a[position] = [x/scale for x in a[position]]
        for r in range(n):
            if r != position and a[r][column]:
                scale = a[r][column]
                a[r] = [x-scale*y for x, y in zip(a[r], a[position])]
        pivots.append(column)
    basis = []
    for free in sorted(set(range(n))-set(pivots)):
        vector = [Fraction(0)]*n
        vector[free] = 1
        for r, pivot in enumerate(pivots):
            vector[pivot] = -a[r][free]
        scale = lcm(*(x.denominator for x in vector))
        vector = [int(x*scale) for x in vector]
        divisor = 0
        for value in vector:
            divisor = gcd(divisor, abs(value))
        vector = [x//divisor for x in vector]
        assert all(sum(x*y for x, y in zip(row, vector)) == 0 for row in matrix)
        basis.append(vector)
    return basis


def audit():
    maps = allowed_maps()
    rows = core(); G = gram(rows)
    assert all(G[i][i] == 7 for i in range(36))
    compatible = []
    for local in product(range(9), repeat=4):
        sites = tuple(9*i+x for i, x in enumerate(local))
        if all(G[i][j] > 0 for i, j in combinations(sites, 2)):
            compatible.append(sites)
    # A separate recursive listing checks the Cartesian-product enumeration.
    def extend(chosen, base):
        if base == 4:
            yield tuple(chosen)
            return
        for candidate in range(9*base, 9*base+9):
            if all(G[candidate][previous] > 0 for previous in chosen):
                yield from extend(chosen+[candidate], base+1)
    assert compatible == list(extend([], 0)) and len(compatible) == 27
    mixed = []
    for sites in compatible:
        mask = sum(1 << i for i in sites)
        if all((row & mask).bit_count()+((mask >> i) & 1) <= 2 for i, row in enumerate(rows)):
            mixed.append(sites)
    assert mixed == compatible
    occurrence = [sum(i in sites for sites in compatible) for i in range(36)]
    assert occurrence == [3]*36

    kernel = integral_kernel(G)
    assert len(kernel) == 12
    ranged = [sites for sites in mixed if all(sum(v[i] for i in sites) == 0 for v in kernel)]
    assert len(ranged) == 9 and [sites[0] for sites in ranged] == list(range(9))
    # The nine surviving columns do form one further local rook base.
    # This is only a partial-graph control, not a full SRG construction.
    extended = rows+[0]*9
    for a, sites in enumerate(ranged, 36):
        for i in sites:
            extended[i] |= 1 << a; extended[a] |= 1 << i
    for i, j in combinations(range(9), 2):
        if rook(i, j):
            extended[36+i] |= 1 << (36+j); extended[36+j] |= 1 << (36+i)
    assert all(row.bit_count() == 8 for row in extended)
    assert all((extended[i] & extended[j]).bit_count()+((extended[i] >> j) & 1) <= 2
               for i, j in combinations(range(45), 2))
    extra_labels = []
    for base in range(1, 4):
        forward = tuple(sites[base]-9*base for sites in ranged)
        backward = tuple(forward.index(x) for x in range(9))
        extra_labels.append(maps.index(backward))
    return {
        'status': 'excluded by distinct boundary-signature count',
        'core_vertices': 36, 'core_degree': 7, 'outside_vertices_required': 63,
        'outside_degree_required_at_each_core_vertex': 7,
        'interface_edge_order': [[1, 2], [1, 3], [2, 3]], 'interface_labels': [1, 6, 7],
        'interface_permutations': [[i, j, list(p)] for (i, j), p in INTERFACES.items()],
        'core_adjacency_rows': rows,
        'all_one_per_base_signatures': 9**4,
        'pair_quota_signatures': [list(sites) for sites in compatible],
        'mixed_quota_signatures': len(mixed),
        'signature_occurrences_per_core_vertex': occurrence,
        'maximum_multiplicity_per_signature': 1,
        'outside_vertices_available': len(compatible),
        'gram_rank': 24, 'gram_kernel_basis': kernel,
        'gram_range_signatures': [list(sites) for sites in ranged],
        'fifth_base_control_labels': [1, 6, 7, *extra_labels],
        'fifth_base_control_degree': 8,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    result = audit()
    if args.verify:
        assert json.loads(args.verify.read_text()) == result
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in
                     ('interface_permutations', 'core_adjacency_rows', 'pair_quota_signatures',
                      'signature_occurrences_per_core_vertex', 'gram_kernel_basis', 'gram_range_signatures')}), flush=True)
