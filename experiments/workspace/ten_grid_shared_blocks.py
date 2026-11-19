"""Exact four-point block tests for a root with ten grids of degrees 0,2,3,3,4,4,4."""

from collections import Counter
from functools import lru_cache
from itertools import combinations, product

import numpy as np

from root_cell_profiles import AXIS_PAIRS, FOUR_GRAPHS, RootCells
from ten_grid_cell_sums import cell_sum_matrices

MISSING = ((0, 3), (0, 5), (0, 6), (1, 4), (1, 5), (1, 6),
           (2, 5), (2, 6), (3, 6), (4, 6), (5, 6))
PIVOTS = (2, 5, 8, 9)
TRANSFORM = np.array([
    [ 0,-1, 1, 0, 0, 0, 1,-1, 0, 0, 0],
    [ 0, 0, 0, 0,-1, 1, 1,-1, 0, 0, 0],
    [-1, 1, 0, 0, 0, 0, 0, 0, 1, 0,-1],
    [ 0, 0, 0,-1, 1, 0, 0, 0, 0, 1,-1],
])


def pack(values):
    return sum(int(x) << (8*k) for k, x in enumerate(values))


@lru_cache(maxsize=150000)
def attainable(options, target):
    """Exact meet-in-the-middle sum of small integer vectors packed in base 256."""
    left, right = {0}, {0}
    for choices in sorted(options, key=len):
        if not choices:
            return False
        if len(choices) == 1:
            target -= choices[0]
            continue
        if len(left) > len(right):
            left, right = right, left
        left = {x+y for x in left for y in choices}
    return any(target-x in right for x in left)


@lru_cache(None)
def edge_blocks(row, col, internal):
    if internal:
        graphs = (g for g in FOUR_GRAPHS if tuple(map(len, g)) == row)
    else:
        graphs = (g for g in product(*(combinations(range(4), d) for d in row))
                  if tuple(sum(b in neighbors for neighbors in g) for b in range(4)) == col)
    return tuple(tuple(sum(1 << b for b in neighbors) for neighbors in g) for g in graphs)


class MarkedCells:
    def __init__(self, model):
        self.z = model.z[:, PIVOTS]
        self.degree = model.degrees
        self.lower = np.maximum(self.degree[:, None, :]+self.degree[None, :, :]-4, 0).sum(axis=2)
        self.target = [pack(tuple(-4*v)+(2, 2, 2)) for v in self.z]

    @lru_cache(maxsize=20000)
    def blocks(self, i, j, p, t):
        """Report each block's four marked sums at both ends in a common order."""
        row = tuple(self.degree[list(p), j])
        col = tuple(self.degree[list(t), i])
        same = i == j
        bad = [sum(1 << b for b, v in enumerate(t) if self.lower[u, v] > 1) for u in p]

        def values(population):
            z = list(map(pack, self.z[list(population)]))
            return [sum(w for k, w in enumerate(z) if (mask >> k) & 1) for mask in range(16)]

        source, target = values(p), values(t)
        def marked(g, weights, opposite):
            result = []
            for a in range(4):
                common = []
                for b in range(4):
                    if a == b:
                        continue
                    v = (g[a] & g[b]).bit_count()
                    if same:
                        v += ((g[a] >> b) & 1) + ((a ^ b) != opposite)
                    common.append(v)
                result.append(weights[g[a]] + (pack(common) << (8*len(PIVOTS))))
            return tuple(result)

        options = set()
        for g in edge_blocks(row, col, same):
            if any(x & y for x, y in zip(g, bad)):
                continue
            back = tuple(sum(1 << a for a in range(4) if (g[a] >> b) & 1) for b in range(4))
            for opposite in (range(1, 4) if same else (0,)):
                forward = marked(g, target, opposite)
                options.add((forward, forward if same else marked(back, source, opposite)))
        return tuple(sorted(options))

    @lru_cache(maxsize=40000)
    def site_options(self, i, j, p, t, a):
        return frozenset(x[a] for x, _ in self.blocks(i, j, p, t))

    def permits(self, i, p, groups):
        for a, u in enumerate(p):
            if a and u == p[a-1]:
                continue
            choices = []
            for j, targets in enumerate(groups):
                if i != j and not self.degree[u, j]:
                    continue
                values = set()
                for t in ((p,) if i == j else targets):
                    values.update(self.site_options(i, j, p, t, a))
                choices.append(tuple(sorted(values)))
            if not attainable(tuple(choices), self.target[u]):
                return False
        return True

    def consistent_blocks(self, population):
        domains, cells = {}, [dict() for _ in population]
        for i, p in enumerate(population):
            for j in range(i, len(population)):
                if j != i and not self.degree[list(p), j].any():
                    continue
                options = self.blocks(i, j, p, population[j])
                pair = (i, j)
                domains[pair] = set(range(len(options)))
                cells[i][pair] = [x for x, y in options]
                if j != i:
                    cells[j][pair] = [y for x, y in options]
        while True:
            size = sum(map(len, domains.values()))
            for i, p in enumerate(population):
                for a, u in enumerate(p):
                    sums = {key: tuple(sorted({rows[k][a] for k in domains[key]}))
                            for key, rows in cells[i].items()}
                    for key, vals in sums.items():
                        rest = tuple(v for pair, v in sums.items() if pair != key)
                        allowed = {w for w in vals if attainable(rest, self.target[u]-w)}
                        if not allowed:
                            return False
                        domains[key] = {k for k in domains[key] if cells[i][key][k][a] in allowed}
            if sum(map(len, domains.values())) == size:
                return True


def populations_by_gram(groups, z, matrix):
    tri = np.triu_indices(len(PIVOTS))
    target = tuple((7*matrix[np.ix_(PIVOTS, PIVOTS)])[tri])
    domains = []
    for group in groups:
        by_gram = {}
        for p in group:
            v = z[list(p)]
            by_gram.setdefault(tuple((v.T @ v)[tri]), []).append(p)
        domains.append(by_gram)
    order = sorted(range(len(groups)), key=lambda i: len(domains[i]))
    lo = [(0,)*len(target)]
    hi = lo[:]
    for i in order:
        columns = list(zip(*domains[i]))
        lo.append(tuple(a+min(c) for a, c in zip(lo[-1], columns)))
        hi.append(tuple(a+max(c) for a, c in zip(hi[-1], columns)))
    selected = [None]*len(groups)
    def visit(k, rest):
        if any(x < a or x > b for x, a, b in zip(rest, lo[k], hi[k])):
            return
        if not k:
            yield from product(*selected)
            return
        i = order[k-1]
        for gram, choices in domains[i].items():
            selected[i] = choices
            yield from visit(k-1, tuple(a-b for a,b in zip(rest, gram)))
    yield from visit(len(order), target)


def verify():
    model = RootCells(MISSING)
    marked = MarkedCells(model)
    assert np.array_equal(marked.z @ TRANSFORM, model.z)
    by_sum, halves = [], {}
    for i in range(len(AXIS_PAIRS)):
        rows = {}
        for p in model.cell_populations(i):
            rows.setdefault(tuple(model.z[list(p)].sum(axis=0)), []).append(p)
            halves[p] = tuple(sorted({pack(marked.z[u]+marked.z[v]) for u,v in combinations(p,2)}))
        by_sum.append(rows)
    axes = [[j for j,e in enumerate(AXIS_PAIRS) if a in e] for a in range(7)]
    counts = Counter()
    for matrix in cell_sum_matrices(by_sum, MISSING, PIVOTS, TRANSFORM):
        counts['matrices'] += 1
        groups = [rows[tuple(matrix[MISSING.index(e)]) if e in MISSING else (0,)*len(MISSING)]
                  for rows,e in zip(by_sum,AXIS_PAIRS)]
        while all(groups):
            before = sum(map(len, groups))
            for i in sorted(range(len(groups)),key=lambda j: len(groups[j])):
                groups[i] = [p for p in groups[i] if marked.permits(i,p,groups)]
                if not groups[i]:
                    break
            if before == sum(map(len, groups)):
                break
        if not all(groups):
            continue
        counts['nonempty'] += 1
        order = sorted(range(len(groups)), key=lambda j: len(groups[j]))
        for pop in populations_by_gram(groups, marked.z, matrix):
            counts['gram'] += 1
            if not all(attainable(tuple(halves[pop[j]] for j in ids), 0) for ids in axes):
                continue
            counts['near'] += 1
            singletons = [(p,) for p in pop]
            if all(marked.permits(i, pop[i], singletons) for i in order):
                counts['marked'] += 1
                assert not marked.consistent_blocks(pop)
    assert counts == dict(matrices=9, nonempty=4, gram=63783, near=31658, marked=262), counts
    print('Nine matrices, four with nonempty marked-site domains. Across all 262 final '
          'populations, shared four-point blocks exclude every extension.')


if __name__ == '__main__':
    verify()
