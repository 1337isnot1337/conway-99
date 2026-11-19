"""Exact 324-case exclusion of a root grid with three isomorphic partners.

The three-grid classification restricts every leaf-to-leaf permutation to
one orbit of eighteen involutions. Fix one interface by common rook
relabeling and check every pair of the remaining interfaces. Each case
already exceeds a visible adjacent or nonadjacent common-neighbor quota.
A further complete product check excludes four-cycles of isomorphic
interfaces: two orbit permutations compose to a rook automorphism only
when they are equal.
"""

import argparse
from collections import Counter
from itertools import combinations, permutations, product
import json
from pathlib import Path


REPRESENTATIVE = (0, 5, 7, 8, 6, 1, 4, 2, 3)


def rook(i, j):
    return i != j and (i // 3 == j // 3 or i % 3 == j % 3)


def interface_orbit():
    automorphisms = set()
    for rows, columns in product(permutations(range(3)), repeat=2):
        automorphisms.add(tuple(3*rows[x]+columns[y]
                                for x, y in product(range(3), repeat=2)))
        automorphisms.add(tuple(3*rows[y]+columns[x]
                                for x, y in product(range(3), repeat=2)))
    assert len(automorphisms) == 72
    orbit = set()
    for q in automorphisms:
        qi = tuple(q.index(i) for i in range(9))
        orbit.add(tuple(q[REPRESENTATIVE[qi[i]]] for i in range(9)))
    assert len(orbit) == 18
    assert all(all(p[p[i]] == i for i in range(9)) for p in orbit)
    assert all(sum(p[i] == i for i in range(9)) == 1 for p in orbit)
    return sorted(orbit)


def adjacency(p13, p23):
    neighbors = [set() for _ in range(36)]
    for base in range(4):
        for x, y in combinations(range(9), 2):
            if rook(x, y):
                neighbors[9*base+x].add(9*base+y)
                neighbors[9*base+y].add(9*base+x)
    interfaces = {(0, 1): tuple(range(9)), (0, 2): tuple(range(9)),
                  (0, 3): tuple(range(9)), (1, 2): REPRESENTATIVE,
                  (1, 3): p13, (2, 3): p23}
    for (a, b), p in interfaces.items():
        for x, y in enumerate(p):
            neighbors[9*a+x].add(9*b+y)
            neighbors[9*b+y].add(9*a+x)
    assert all(len(row) == 7 for row in neighbors)
    assert all((j in neighbors[i]) == (i in neighbors[j])
               for i, j in combinations(range(36), 2))
    return neighbors


def replay_row(orbit, certificate):
    a, b = certificate['assignment']
    assert 0 <= a < 18 and 0 <= b < 18
    neighbors = adjacency(orbit[a], orbit[b])
    i, j = certificate['violating_pair']
    assert 0 <= i < j < 36
    # Direct membership loops are separate from the intersection used to
    # discover the certificate's first violating pair.
    common = [k for k in range(36) if k in neighbors[i] and k in neighbors[j]]
    adjacent = int(j in neighbors[i])
    assert common == certificate['visible_common_neighbors']
    assert adjacent == certificate['adjacent']
    assert 2-adjacent == certificate['allowed_common_neighbors']
    assert len(common) > 2-adjacent


def replay_product(orbit, certificate):
    a, b = certificate['factors']
    assert 0 <= a < 18 and 0 <= b < 18
    product_map = tuple(orbit[a][orbit[b][i]] for i in range(9))
    if a == b:
        assert certificate['status'] == 'identity'
        assert product_map == tuple(range(9))
    else:
        assert certificate['status'] == 'not a rook automorphism'
        i, j = certificate['distinguishing_pair']
        assert 0 <= i < j < 9
        image_pair = [product_map[i], product_map[j]]
        assert image_pair == certificate['image_pair']
        assert rook(i, j) != rook(*image_pair)


def audit(classification):
    orbit = interface_orbit()
    assert classification['complete'] and classification['excluded_classes'] == 58
    survivor = [row for row in classification['classes']
                if row['status'] == 'incidence survives']
    assert len(survivor) == 1
    assert survivor[0]['representative'] == list(REPRESENTATIVE)
    assert survivor[0]['orbit_members'] == [list(p) for p in orbit]
    certificates = []
    for a, b in product(range(18), repeat=2):
        neighbors = adjacency(orbit[a], orbit[b])
        violating = [(i, j) for i, j in combinations(range(36), 2)
                     if len(neighbors[i] & neighbors[j])+int(j in neighbors[i]) > 2]
        assert violating
        i, j = violating[0]
        certificate = {
            'assignment': [a, b], 'violating_pair': [i, j],
            'adjacent': int(j in neighbors[i]),
            'visible_common_neighbors': sorted(neighbors[i] & neighbors[j]),
            'allowed_common_neighbors': 2-int(j in neighbors[i]),
        }
        replay_row(orbit, certificate)
        certificates.append(certificate)
    assert len(certificates) == len({tuple(row['assignment']) for row in certificates}) == 324
    products = []
    for a, b in product(range(18), repeat=2):
        product_map = tuple(orbit[a][orbit[b][i]] for i in range(9))
        if a == b:
            certificate = {'factors': [a, b], 'status': 'identity'}
        else:
            differences = [(i, j) for i, j in combinations(range(9), 2)
                           if rook(i, j) != rook(product_map[i], product_map[j])]
            assert differences
            i, j = differences[0]
            certificate = {'factors': [a, b], 'status': 'not a rook automorphism',
                           'distinguishing_pair': [i, j],
                           'image_pair': [product_map[i], product_map[j]]}
        replay_product(orbit, certificate)
        products.append(certificate)
    assert len(products) == len({tuple(row['factors']) for row in products}) == 324
    assert Counter(row['status'] for row in products) == {
        'identity': 18, 'not a rook automorphism': 306}
    fixed_point_rows = []
    for index, p in enumerate(orbit):
        point, = [i for i in range(9) if p[i] == i]
        # With cycle interfaces 01,12,23,03 all identity and diagonal
        # 02 equal to p, these are distinct common neighbors of an edge.
        fixed_point_rows.append({'diagonal_map': index,
                                 'adjacent_pair': [point, 18+point],
                                 'forced_common_neighbors': [9+point, 27+point]})
    return {
        'status': 'every four-grid isomorphic star is excluded',
        'complete': True,
        'fixed_interface': list(REPRESENTATIVE),
        'interface_orbit': [list(p) for p in orbit],
        'interface_orbit_size': 18,
        'assignments_checked': 324,
        'excluded_by_visible_common_neighbors': 324,
        'first_violation_adjacent_counts': dict(sorted(Counter(
            str(row['adjacent']) for row in certificates).items())),
        'certificates': certificates,
        'four_cycle_product_pairs_checked': 324,
        'identity_products': 18,
        'nonisomorphic_products': 306,
        'product_certificates': products,
        'four_cycle_fixed_point_certificates': fixed_point_rows,
        'partner_graph_conclusion': 'maximum degree two; no triangles or four-cycles',
        'scope': 'uses the separate complete three-grid interface classification; no red assumption',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classification', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/two-rook-interfaces.json'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.classification.read_text()))
    if args.verify:
        saved = json.loads(args.verify.read_text())
        orbit = interface_orbit()
        for row in saved['certificates']:
            replay_row(orbit, row)
        for row in saved['product_certificates']:
            replay_product(orbit, row)
        assert saved == result
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('certificates', 'interface_orbit',
                                     'product_certificates',
                                     'four_cycle_fixed_point_certificates')}), flush=True)
