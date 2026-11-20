"""Independent dense-integer audit of stars and short isomorphic cycles.

The necessary eighteen-map domain is supplied by the separately replayed
three-grid classification. This script rebuilds each selected adjacency
matrix directly and evaluates B^2+B using integer matrix multiplication.
"""

import argparse
from collections import Counter
from itertools import combinations, permutations, product
import json
from pathlib import Path

import numpy as np


def automorphisms():
    points = list(product(range(3), repeat=2))
    maps = set()
    for rows, columns, swap in product(permutations(range(3)),
                                       permutations(range(3)), range(2)):
        maps.add(tuple(3*rows[v if swap else u]+columns[u if swap else v]
                       for u, v in points))
    assert len(maps) == 72
    return sorted(maps)


def inverse(p):
    answer = [0]*9
    for i, j in enumerate(p):
        answer[j] = i
    return tuple(answer)


def compose(p, q):
    return tuple(p[q[i]] for i in range(9))


def adjacency(interfaces):
    bases = 1+max(max(pair) for pair in interfaces)
    r = np.fromfunction(lambda i, j: (i != j) &
                        ((i//3 == j//3) | (i % 3 == j % 3)), (9, 9), dtype=int)
    b = np.kron(np.eye(bases, dtype=np.int64), r.astype(np.int64))
    assert set(interfaces) == set(combinations(range(bases), 2))
    for (a, c), p in interfaces.items():
        for i, j in enumerate(p):
            b[9*a+i, 9*c+j] = b[9*c+j, 9*a+i] = 1
    assert np.array_equal(b, b.T) and np.all(b.sum(axis=1) == bases+3)
    return b


def violates(b):
    quotas = b @ b+b
    np.fill_diagonal(quotas, 0)
    return bool(np.max(quotas) > 2)


def audit(classification):
    survivors = [row for row in classification['classes']
                 if row['status'] == 'incidence survives']
    assert len(survivors) == 1
    representative = tuple(survivors[0]['representative'])
    p = representative
    autos = automorphisms()
    orbit = sorted({compose(compose(q, p), inverse(q)) for q in autos})
    assert [list(q) for q in orbit] == survivors[0]['orbit_members']
    assert len(orbit) == 18
    allowed = set(orbit)
    identity = tuple(range(9))
    star_count = 0
    for q, r in product(orbit, repeat=2):
        b = adjacency({(0, 1): identity, (0, 2): identity,
                       (0, 3): identity, (1, 2): p, (1, 3): q, (2, 3): r})
        assert violates(b)
        star_count += 1
    assert star_count == 324

    cycles = Counter()
    for p, q, r in product(orbit, orbit, autos):
        b = adjacency({(0, 1): identity, (1, 2): identity,
                       (2, 3): identity, (0, 2): p, (1, 3): q, (0, 3): r})
        visible = violates(b)
        # The triples rooted at bases zero and three must obey the same
        # eighteen-map restriction after their two isomorphic gauges.
        other_triples_pass = (compose(inverse(r), q) in allowed and
                              compose(p, inverse(r)) in allowed)
        assert visible or not other_triples_pass
        if other_triples_pass:
            assert r == identity and visible
        cycles['visible_quota_violation' if visible else
               'three_grid_boundary_exclusion'] += 1
    assert sum(cycles.values()) == 18*18*72
    assert cycles == {'visible_quota_violation': 23328}

    # For a five-cycle, gauge01=12=23=34=I and04=r. The distance-two
    # domains give02=p,13=q,24=s,03=t*r,14=r*w, with p,q,s,t,w in O.
    # Common rook conjugation fixes p to the representative. First check
    # every 0123 core, then all324 full extensions of every survivor.
    prefixes = []
    p = representative
    for q, t, r in product(orbit, orbit, autos):
        interfaces = {(0, 1): identity, (1, 2): identity,
                      (2, 3): identity, (0, 2): p, (1, 3): q,
                      (0, 3): compose(t, r)}
        if not violates(adjacency(interfaces)):
            prefixes.append((interfaces, r))
    assert len(prefixes) == 8
    five_extensions = 0
    for initial, r in prefixes:
        for s, w in product(orbit, repeat=2):
            interfaces = dict(initial)
            interfaces.update({(0, 4): r, (1, 4): compose(r, w),
                               (2, 4): s, (3, 4): identity})
            assert violates(adjacency(interfaces))
            five_extensions += 1
    assert five_extensions == 2592
    return {'star_assignments': star_count, 'star_visible_exclusions': star_count,
            'cycle_assignments': sum(cycles.values()),
            'cycle_exclusions': dict(sorted(cycles.items())),
            'all_four_cycles_excluded': True,
            'five_cycle_prefixes': 23328, 'five_cycle_prefix_survivors': len(prefixes),
            'five_cycle_full_extensions': five_extensions,
            'all_five_cycles_excluded': True,
            'arithmetic': 'integer adjacency multiplication; no spectral tolerance'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--classification', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/two-rook-interfaces.json'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    result = audit(json.loads(args.classification.read_text()))
    if args.verify:
        assert json.loads(args.verify.read_text()) == result
    if args.output:
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
