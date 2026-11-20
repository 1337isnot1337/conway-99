"""Enumerate the twelve residual neighbors of a triangle lying in four grids."""

from collections import Counter
from itertools import combinations, permutations, product

import numpy as np
import pynauty

FIBER = np.repeat(np.eye(3, dtype=np.int64), 4, axis=1)


def residual_graph(permutation, matchings):
    adjacency = np.zeros((12, 12), dtype=np.int64)
    for x in range(4):
        edges = [(x, 4+x), (x, 8+x), (4+x, 8+permutation[x])]
        edges.extend((4*i+x, 4*i+(x ^ m)) for i, m in enumerate(matchings))
        for u, v in edges:
            adjacency[u, v] = adjacency[v, u] = 1
    return adjacency


def marked_key(adjacency):
    graph = np.block([[adjacency, FIBER.T], [FIBER, np.ones((3, 3), dtype=int)-np.eye(3, dtype=int)]])
    rows = {i: np.flatnonzero(row).tolist() for i, row in enumerate(graph)}
    return pynauty.certificate(pynauty.Graph(15, adjacency_dict=rows,
                                            vertex_coloring=[set(range(12)), set(range(12, 15))]))


def verify():
    classes = {}
    labeled = 0
    for permutation in permutations(range(4)):
        for matchings in product(range(1, 4), repeat=3):
            d = residual_graph(permutation, matchings)
            counts = 12*np.eye(12, dtype=int)+2-d-d@d-FIBER.T@FIBER
            if np.any(counts < 0):
                continue
            reached = {0}
            for _ in range(12):
                reached.update(v for x in list(reached) for v in np.flatnonzero(d[x]))
            if len(reached) != 12:
                continue
            labeled += 1
            classes.setdefault(marked_key(d), (d, counts))
    assert labeled == 366 and len(classes) == 15

    census = Counter()
    for d, counts in classes.values():
        triangles = [t for t in combinations(range(12), 3) if all(d[u,v] for u,v in combinations(t,2))]
        if any(d[np.ix_(t, u)].sum() == 2 for t,u in combinations(triangles,2)):
            continue
        edges = [e for e in combinations(range(12), 2) for _ in range(counts[e])]
        incidence = np.array([[int(u in e) for u in range(12)] for e in edges])
        assert len(edges) == 60 and np.array_equal(incidence.T @ incidence, counts)
        assert np.array_equal(incidence.sum(axis=1), np.full(60, 2))
        assert np.array_equal(incidence.sum(axis=0), np.full(12, 10))
        doubles = sum(counts[e] == 2 for e in combinations(range(12), 2))
        census[len(triangles), doubles] += 1
    assert census == {(0,4):1, (0,8):3, (0,12):4, (1,9):1,
                      (2,6):1, (2,10):1, (2,14):2, (4,12):1}
    print('Four grids through a triangle: 648 labeled inputs, 366 connected quota-compatible '
          'inputs, 15 isomorphism classes, 14 after the nine-point obstruction. '
          'All 14 determine their full 60-by-12 residual incidence matrix.')


if __name__ == '__main__':
    verify()
