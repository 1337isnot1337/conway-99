"""Exact four-point cell profiles for a rooted SRG(99,14,1,2)."""
from collections import Counter
from functools import lru_cache
from itertools import combinations, combinations_with_replacement, product

import numpy as np

AXIS_PAIRS = tuple(combinations(range(7), 2))
POINT_PAIRS = tuple(combinations(range(4), 2))
THETA = ((1, 2), (1, 4), (2, 3), (2, 5), (3, 6), (4, 5), (5, 6))


def row_types(missing, cell):
    """Enumerate nonnegative cell degrees with the prescribed axis sums."""
    baseline = tuple((1, 0, 2)[len(set(cell) & set(edge))] for edge in missing)
    remaining = [sum(d for d, e in zip(baseline, missing) if a in e) for a in range(7)]

    def extend(k, prefix):
        if k == len(missing):
            if not any(remaining):
                yield prefix
            return
        a, b = missing[k]
        upper = min(remaining[a], remaining[b], 2 if cell == missing[k] else 4)
        for degree in range(upper + 1):
            remaining[a] -= degree
            remaining[b] -= degree
            if all(remaining[t] == 0 or any(t in e for e in missing[k + 1:]) for t in (a, b)):
                yield from extend(k + 1, prefix + (baseline[k] - degree,))
            remaining[a] += degree
            remaining[b] += degree

    return extend(0, ())


def graphs_on_four():
    for mask in range(64):
        edges = [e for k, e in enumerate(POINT_PAIRS) if mask & (1 << k)]
        yield tuple(tuple(b for b in range(4) if tuple(sorted((a, b))) in edges)
                    for a in range(4))


FOUR_GRAPHS = tuple(graphs_on_four())


class RootCells:
    def __init__(self, missing):
        self.missing = tuple(missing)
        self.bins = []
        types = []
        degrees = []
        for cell in AXIS_PAIRS:
            first = len(types)
            for z in row_types(self.missing, cell):
                types.append(z)
                degrees.append(tuple((1, 0, 2)[len(set(cell) & set(e))] -
                                     (z[self.missing.index(e)] if e in self.missing else 0)
                                     for e in AXIS_PAIRS))
            self.bins.append(range(first, len(types)))
        self.z = np.array(types)
        self.degrees = np.array(degrees)
        self.gram = tuple(combinations_with_replacement(range(len(self.missing)), 2))

    def cell_populations(self, i):
        cell = AXIS_PAIRS[i]
        coords = self.z
        own = self.degrees[:, i]
        allowed = {tuple(sorted(map(len, g))) for g in FOUR_GRAPHS
                   if sum(map(len, g)) <= 4}
        for sites in combinations_with_replacement(self.bins[i], 4):
            ids = list(sites)
            if cell in self.missing:
                if tuple(sorted(own[ids])) not in allowed:
                    continue
            elif any(coords[ids].sum(axis=0)):
                continue
            yield sites

    def cell_options(self, i):
        cell = AXIS_PAIRS[i]
        coords = self.z
        result = []
        for sites in self.cell_populations(i):
            ids = list(sites)
            gram = np.array([coords[ids, j] @ coords[ids, k] -
                             7 * (cell == self.missing[j]) * sum(coords[ids, k])
                             for j, k in self.gram])
            result.append((sites, self.degrees[ids].sum(axis=0), gram))
        return result

    def populations(self, domains):
        domains = domains[:]
        while True:
            before = tuple(map(len, domains))
            for i, options in enumerate(domains):
                domains[i] = [o for o in options if all(
                    i == j or any(o[1][j] == p[1][i] for p in other)
                    for j, other in enumerate(domains))]
                if not domains[i]:
                    return
            low = np.array([np.min([p[2] for p in d], axis=0) for d in domains])
            high = np.array([np.max([p[2] for p in d], axis=0) for d in domains])
            lo, hi = low.sum(axis=0), high.sum(axis=0)
            for i, options in enumerate(domains):
                domains[i] = [p for p in options if
                              np.all(lo - low[i] + p[2] <= 0) and
                              np.all(hi - high[i] + p[2] >= 0)]
                if not domains[i]:
                    return
            if before == tuple(map(len, domains)):
                break
        choices = [i for i, d in enumerate(domains) if len(d) > 1]
        if not choices:
            yield tuple(d[0][0] for d in domains)
            return
        i = min(choices, key=lambda j: len(domains[j]))
        for p in domains[i]:
            yield from self.populations(domains[:i] + [[p]] + domains[i + 1:])

    @lru_cache(maxsize=32768)
    def contributions(self, i, j, sites, other, columns):
        row = self.degrees[list(sites), j].tolist()
        col = self.degrees[list(other), i].tolist()
        if i == j:
            graphs = (g for g in FOUR_GRAPHS if list(map(len, g)) == row)
        else:
            graphs = (g for g in product(*(combinations(range(4), d) for d in row))
                      if [sum(a in r for r in g) for a in range(4)] == col)
        return {tuple(sum(int(self.z[other[a], k]) for a in r) for r in g for k in columns)
                for g in graphs}

    def permits_eigenvectors(self, population, i, columns):
        options = [self.contributions(i, j, population[i], other, columns)
                   for j, other in enumerate(population)]
        if not all(options):
            return False
        target = tuple(-4 * int(self.z[t, k]) for t in population[i] for k in columns)
        return sum_possible(options, target)


def sum_possible(options, target):
    options = sorted(options, key=len)
    dimension = len(target)
    low = [tuple(0 for _ in target)]
    high = low[:]
    for opts in options:
        low.append(tuple(low[-1][a] + min(w[a] for w in opts) for a in range(dimension)))
        high.append(tuple(high[-1][a] + max(w[a] for w in opts) for a in range(dimension)))

    @lru_cache(None)
    def visit(k, rest):
        if any(x < a or x > b for x, a, b in zip(rest, low[k], high[k])):
            return False
        if k == 0:
            return True
        return any(visit(k - 1, tuple(x - y for x, y in zip(rest, w)))
                   for w in options[k - 1])

    return visit(len(options), target)


def verify_theta():
    cells = RootCells(THETA)
    counts = Counter()
    for pop in cells.populations([cells.cell_options(i) for i in range(21)]):
        counts['populations'] += 1
        if all(cells.permits_eigenvectors(pop, i, (0, 2)) for i in range(21)):
            counts['survivors'] += 1
    assert len(cells.z) == 50 and counts == {'populations': 41}
    print('Seven-edge theta: 50 point types, 41 populations, zero compatible populations.')


if __name__ == '__main__':
    verify_theta()
