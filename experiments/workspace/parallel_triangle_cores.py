"""Enumerate the 39-point neighborhoods of the third parallel grid line."""
from collections import Counter
from functools import lru_cache
from itertools import combinations

import pynauty


@lru_cache(None)
def matchings(vertices):
    if not vertices:
        return ((),)
    a, *others = vertices
    return tuple(((a, b),) + tail for b in others
                 for tail in matchings(tuple(c for c in others if c != b)))


def partitions(total, lower=2):
    if total == 0:
        yield ()
    for first in range(lower, total + 1):
        for tail in partitions(total - first, first):
            yield (first,) + tail


def colored_matchings():
    for common_count in range(6):
        first_free = 2 * common_count
        common = tuple((a, a + 1) for a in range(0, first_free, 2))
        first = tuple((a, a + 1) for a in range(first_free, 10, 2))
        for parts in partitions(5 - common_count):
            second = []
            a = first_free
            for size in parts:
                for i in range(size):
                    second.append(tuple(sorted((a + 2*i + 1, a + 2*((i+1) % size)))))
                a += 2 * size
            for third in matchings(tuple(range(first_free, 10))):
                if not set(third).intersection(first + tuple(second)):
                    yield common_count, (common + first, common + tuple(second), common + third)


def core_key(matchings):
    edges = [(i, j) for i, j in combinations(range(9), 2) if i//3 == j//3 or i%3 == j%3]
    for i in range(10):
        for c in range(3):
            edges.append((6 + c, 9 + 3*i + c))
            for d in range(c):
                edges.append((9 + 3*i + d, 9 + 3*i + c))
    for c, matching in enumerate(matchings):
        edges.extend((9 + 3*i + c, 9 + 3*j + c) for i, j in matching)
    adj = {i: [] for i in range(39)}
    for i, j in edges:
        adj[i].append(j)
        adj[j].append(i)
    colors = [set(range(6)), set(range(6, 9)), set(range(9, 39))]
    graph = pynauty.Graph(39, adjacency_dict=adj, vertex_coloring=colors)
    return pynauty.certificate(graph)


def main():
    seen = {}
    for count, matchings in colored_matchings():
        key = core_key(matchings)
        assert seen.setdefault(key, count) == count
    totals = Counter(seen.values())
    assert totals == {0: 23, 1: 8, 2: 2, 3: 1, 5: 1}
    print('Parallel triangle cores by additional grids:', sorted(totals.items()))


if __name__ == '__main__':
    main()
