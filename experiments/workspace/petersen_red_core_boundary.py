"""Standard-library certificate for the Petersen five-rook boundary.

The 45 points are (Petersen edge, coordinate in F_3). Petersen edges are
colored by the element absent from their two disjoint two-subset endpoints.
Every color class gives one rook grid. All 9^5 possible outside signatures
are enumerated using exact common-neighbor deficits. Each of the eighteen
survivors has a short integer minus-four eigenvector obstruction.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations, product
import json
from pathlib import Path
import time


def construct():
    p_vertices = tuple(combinations(range(5), 2))
    p_edges = tuple((i, j) for i, j in combinations(range(10), 2)
                    if set(p_vertices[i]).isdisjoint(p_vertices[j]))
    assert len(p_edges) == 15
    colors = tuple(next(iter(set(range(5))-set(p_vertices[i])-set(p_vertices[j])))
                   for i, j in p_edges)
    line = tuple(tuple(int(e != f and bool(set(p_edges[e]) & set(p_edges[f])))
                       for f in range(15)) for e in range(15))
    B = []
    for a in range(45):
        e, v = divmod(a, 3)
        row = []
        for b in range(45):
            f, w = divmod(b, 3)
            row.append(int((colors[e] == colors[f] and e != f and v != w)
                           or (colors[e] != colors[f] and line[e][f] and v == w)))
        B.append(row)
    rows = [sum(1 << j for j, entry in enumerate(row) if entry) for row in B]
    assert all(row.bit_count() == 8 for row in rows)
    C = [[12*int(i == j)+2-(rows[i] & rows[j]).bit_count()-B[i][j]
          for j in range(45)] for i in range(45)]
    assert all(C[i][i] == 6 for i in range(45))
    assert min(map(min, C)) >= 0
    fibers = [tuple(3*e+v for e in range(15) if colors[e] == c for v in range(3))
              for c in range(5)]
    assert all(len(fiber) == 9 for fiber in fibers)
    assert all(sum(B[a][b] for b in fibers[c]) == (4 if colors[a//3] == c else 1)
               for a in range(45) for c in range(5))
    return p_vertices, p_edges, colors, B, C, fibers


def run():
    begin = time.monotonic()
    p_vertices, p_edges, colors, B, C, fibers = construct()
    signatures = []
    examined = 0
    for signature in product(*fibers):
        examined += 1
        if all(C[a][b] > 0 for a, b in combinations(signature, 2)):
            signatures.append(signature)
    assert examined == 9**5 and len(signatures) == 18

    matchings = tuple(edges for edges in combinations(range(15), 5)
                     if len({vertex for edge in edges for vertex in p_edges[edge]}) == 10)
    assert len(matchings) == 6
    assert all(len({colors[e] for e in matching}) == 5 for matching in matchings)
    expected = {tuple(next(3*e+v for e in matching if colors[e] == c) for c in range(5))
                for matching in matchings for v in range(3)}
    assert set(signatures) == expected

    certificates = []
    for matching in matchings:
        z = [2 if e in matching else -1 for e in range(15) for _ in range(3)]
        assert sum(z) == 0
        assert all(sum(B[i][j]*z[j] for j in range(45)) == -4*z[i] for i in range(45))
        assert all(sum(C[i][j]*z[j] for j in range(45)) == 0 for i in range(45))
        covered = []
        for v in range(3):
            signature = tuple(next(3*e+v for e in matching if colors[e] == c) for c in range(5))
            assert sum(z[a] for a in signature) == 10
            assert all(C[a][b] == 1 for a, b in combinations(signature, 2))
            assert all(sum(B[i][a] for a in signature)+int(i in signature) <= 2
                       for i in range(45))
            covered.append(list(signature))
        certificates.append({'perfect_matching_edges': list(matching), 'integer_eigenvector': z,
                             'eigenvalue': -4, 'signature_inner_products': [10, 10, 10],
                             'covered_signatures': covered})
    result = {
        'core_order': 45, 'core_degree': 8, 'outside_vertices_required': 54,
        'petersen_vertices': [list(vertex) for vertex in p_vertices],
        'petersen_edges': [list(edge) for edge in p_edges], 'edge_colors': list(colors),
        'core_adjacency_rows': B,
        'candidate_signatures': examined, 'pair_quota_survivors': len(signatures),
        'perfect_matchings': len(matchings), 'maximum_distinct_outside_signatures': 18,
        'gram_range_survivors': 0,
        'common_neighbor_deficit_entry_counts': dict(sorted(Counter(x for row in C for x in row).items())),
        'certificates': certificates, 'seconds': time.monotonic()-begin,
    }
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('petersen_vertices', 'petersen_edges', 'edge_colors',
                                     'core_adjacency_rows', 'certificates')}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run()
    if args.output:
        args.output.write_text(json.dumps(result, indent=2)+'\n')
