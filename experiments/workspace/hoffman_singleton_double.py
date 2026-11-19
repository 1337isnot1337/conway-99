"""Construct the 99-point doubled Moore graph and check every CAISc constraint."""
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np


def hoffman_singleton():
    graph = np.zeros((50, 50), dtype=np.int16)
    def vertex(layer, i, j):
        return 25*layer + 5*i + j % 5
    def edge(a, b):
        graph[a, b] = graph[b, a] = 1
    for i in range(5):
        for j in range(5):
            edge(vertex(0, i, j), vertex(0, i, j+1))
            edge(vertex(1, i, j), vertex(1, i, j+2))
            for k in range(5):
                edge(vertex(0, i, j), vertex(1, k, i*k+j))
    assert np.array_equal(graph @ graph + graph, 6*np.eye(50, dtype=int)+1)
    return graph


def doubled():
    base = hoffman_singleton()
    graph = np.kron(base, np.ones((2, 2), dtype=np.int16))[1:, 1:].copy()
    for i in np.flatnonzero(base[0]):
        graph[2*i-1, 2*i] = graph[2*i, 2*i-1] = 1
    return graph


def read_graph6(name):
    # The graph6 order is encoded by '~' and three six-bit digits for 99.
    data = Path(__file__).with_name(name).read_bytes().strip()
    assert data[:4] == bytes((126, 63, 64, 98))
    bits = ((byte-63 >> shift) & 1 for byte in data[4:] for shift in reversed(range(6)))
    neighbors = [set() for _ in range(99)]
    for j in range(99):
        for i in range(j):
            if next(bits):
                neighbors[i].add(j)
                neighbors[j].add(i)
    assert list(bits) == [0, 0, 0]
    return neighbors


def check_graph(neighbors, totals, histogram):
    graph = np.array([[j in row for j in range(99)] for row in neighbors], dtype=np.int16)
    assert np.array_equal(graph, graph.T) and not graph.diagonal().any()
    correct = Counter()
    for i, j in combinations(range(99), 2):
        adjacent = j in neighbors[i]
        if len(neighbors[i] & neighbors[j]) == 2-adjacent:
            correct[adjacent] += 1
    observed = sum(len(r) == 14 for r in neighbors), correct[True], correct[False]
    assert observed == totals
    residual = graph @ graph + graph - 12*np.eye(99, dtype=int)-2
    assert np.count_nonzero(np.triu(residual == 0)) == sum(totals)
    assert Counter(residual[np.triu_indices(99, k=1)]) == histogram
    return residual


def verify():
    neighbors = read_graph6('hoffman-singleton-double.g6')
    original = doubled()
    assert all(row == set(np.flatnonzero(original[i])) for i, row in enumerate(neighbors))
    check_graph(neighbors, (99, 182, 4032), {-1: 588, 0: 4214, 12: 49})
    print('Doubled Hoffman–Singleton score: 99 + 182 + 4032 = 4313 out of 4950.')

    neighbors = read_graph6('hoffman-rewired-4272.g6')
    check_graph(neighbors, (99, 554, 3619), {-2: 10, -1: 498, 0: 4173, 1: 35, 2: 37, 4: 81, 5: 17})
    for a, b in ((48, 49), (97, 98)):
        neighbors[a].remove(b)
        neighbors[b].remove(a)
    for a, b in ((48, 98), (97, 49)):
        assert b not in neighbors[a]
        neighbors[a].add(b)
        neighbors[b].add(a)
    residual = check_graph(neighbors, (99, 556, 3583),
                           {-2: 13, -1: 510, 0: 4139, 1: 57, 2: 34, 4: 79, 5: 19})

    def colors(signatures):
        identifiers = {}
        return [identifiers.setdefault(tuple(s), len(identifiers)) for s in signatures]

    partition = colors(sorted(row) for row in residual)
    counts = [len(set(partition))]
    for _ in range(2):
        partition = colors((partition[i], *sorted(partition[j] for j in row))
                           for i, row in enumerate(neighbors))
        counts.append(len(set(partition)))
    assert counts == [20, 81, 99]
    print('Rewired scores: 4272 and 4238. The latter has 99 distinct invariant vertex colors.')


if __name__ == '__main__':
    verify()
