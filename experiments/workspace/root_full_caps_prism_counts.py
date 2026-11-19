"""Exact prism/anchor multiplicities on the nine-rook and 243-Golay controls.

No search, new graph assumption, or solver is used. Prisms are enumerated
as pairs of disjoint triangles, independently of the rooted count formula.
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations, product
import json
from pathlib import Path

from triangle_ball import golay


def compact_hash(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def bits(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length()-1
        mask ^= bit


def audit(matrix, name):
    n = len(matrix)
    rows = [sum(1 << j for j in range(n) if matrix[i][j]) for i in range(n)]
    k = rows[0].bit_count()
    assert n == 1+k*k//2
    assert all(row.bit_count() == k and not row >> i & 1 for i, row in enumerate(rows))
    triangles = []
    for a, b in combinations(range(n), 2):
        edge = int(rows[a] >> b & 1)
        assert edge == int(rows[b] >> a & 1)
        common = rows[a] & rows[b]
        assert common.bit_count()+edge == 2
        if edge:
            c, = bits(common)
            if b < c:
                triangles.append((a, b, c))
    assert len(triangles) == n*k//6
    masks = [sum(1 << v for v in triangle) for triangle in triangles]
    prisms = set()
    root_count, triangle_count = [0]*n, [0]*len(triangles)
    oriented = Counter()
    for i, j in combinations(range(len(triangles)), 2):
        if masks[i] & masks[j]:
            continue
        first, second = triangles[i], triangles[j]
        if any((rows[v] & masks[j]).bit_count() != 1 for v in first):
            continue
        if any((rows[v] & masks[i]).bit_count() != 1 for v in second):
            continue
        prism = masks[i] | masks[j]
        assert prism not in prisms
        assert all((rows[v] & prism).bit_count() == 3 for v in bits(prism))
        prisms.add(prism)
        triangle_count[i] += 1
        triangle_count[j] += 1
        for v in first:
            partner, = bits(rows[v] & masks[j])
            oriented[v, partner] += 1
            oriented[partner, v] += 1
        for v in bits(prism):
            root_count[v] += 1
    anchored = []
    positive_terms = 0
    for root in range(n):
        near = list(bits(rows[root]))
        pairs = []
        for b in near:
            mate, = bits(rows[root] & rows[b])
            if b < mate:
                pairs.append((b, mate))
        assert len(pairs) == k//2
        total = 0
        for anchor in near:
            count = 0
            for b, mate in pairs:
                if anchor in (b, mate):
                    continue
                left, = bits((rows[anchor] & rows[b]) & ~(1 << root))
                right, = bits((rows[anchor] & rows[mate]) & ~(1 << root))
                assert left != right and not rows[root] >> left & 1 and not rows[root] >> right & 1
                if rows[left] >> right & 1:
                    vertices = (root, anchor, b, mate, left, right)
                    assert len(set(vertices)) == 6
                    assert sum(1 << v for v in vertices) in prisms
                    count += 1
                    positive_terms += 1
            assert count == oriented[root, anchor] == oriented[anchor, root]
            assert 0 <= count <= (k-2)//2
            total += count
            anchored.append([root, anchor, count])
        assert total == root_count[root]
    assert positive_terms == sum(root_count) == sum(oriented.values()) == 6*len(prisms)
    assert sum(triangle_count) == 2*len(prisms)
    return {'name': name, 'vertices': n, 'degree': k,
            'pair_equations_checked': n*(n-1)//2,
            'triangles': len(triangles), 'prisms': len(prisms),
            'oriented_edge_equalities_checked': len(anchored),
            'positive_rooted_terms': positive_terms,
            'anchor_count_histogram': dict(sorted(Counter(c for _, _, c in anchored).items())),
            'root_prism_count_histogram': dict(sorted(Counter(root_count).items())),
            'triangle_prism_count_histogram': dict(sorted(Counter(triangle_count).items())),
            'sixfold_vertex_and_twofold_triangle_multiplicities_exact': True,
            'anchor_count_is_symmetric_under_root_edge_reversal': True,
            'adjacency_sha256': compact_hash(rows),
            'prism_vertex_sets_sha256': compact_hash([list(bits(mask)) for mask in sorted(prisms)]),
            'all_oriented_counts_sha256': compact_hash(anchored)}


def generate():
    coordinates = list(product(range(3), repeat=2))
    rook = [[int(i != j and (a[0] == b[0] or a[1] == b[1]))
             for j, b in enumerate(coordinates)] for i, a in enumerate(coordinates)]
    rook_result = audit(rook, 'nine-vertex rook graph')
    matrix, _, _ = golay()
    golay_result = audit(matrix, 'existing 243-vertex Golay control')
    assert rook_result['prisms'] == 6 and golay_result['prisms'] == 8910
    assert rook_result['anchor_count_histogram'] == {1: 36}
    assert golay_result['anchor_count_histogram'] == {10: 5346}
    directory = Path(__file__).resolve().parent
    return {'status': 'exact prism/anchor multiplicity controls pass',
            'source_hashes': {name: hashlib.sha256((directory/name).read_bytes()).hexdigest()
                              for name in ['root_full_caps_prism_counts.py', 'triangle_ball.py']},
            'controls': [rook_result, golay_result], 'solver_called': False,
            'new_graph_constraints': 0,
            'scope': 'positive controls and multiplicity identities, no 99-graph exclusion'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = generate()
    if args.write:
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps(result, indent=2)+'\n')
    else:
        assert json.loads(args.certificate.read_text()) == json.loads(json.dumps(result))
    print(json.dumps(result), flush=True)
