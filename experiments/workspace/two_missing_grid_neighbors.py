"""Exclude two missing cells among the ten pairs disjoint from a grid."""

from collections import Counter, defaultdict
from functools import lru_cache
from itertools import combinations, permutations, product

import numpy as np

from central_grid_neighborhood import (
    CHARACTERS, INVERSE, OPPOSITES, PAIRS, PERMS,
    gram_possible, local_states, transformations,
)


MISSING = (0, 1)  # Number the two missing cells first in each layout.
GRID = tuple(range(2, 10))


def partial_assignments(neighbors, grid=GRID):
    full = local_states()
    states = {i: sorted({(r[0],)+tuple(p if j in grid else -1
                                        for p, j in zip(r[1:], neighbors[i])) for r in full})
              for i in grid}
    table = {(i, j, p): sum(1 << k for k, r in enumerate(states[i])
                            if r[1+neighbors[i].index(j)] == p)
             for i in grid for j in neighbors[i] if j in grid for p in range(24)}

    def extend(assigned, remaining):
        if not remaining:
            yield tuple(assigned.get(i) for i in range(10))
            return
        i = min(remaining, key=lambda j: remaining[j].bit_count())
        choices = remaining[i]
        while choices:
            bit = choices & -choices
            choices ^= bit
            row = states[i][bit.bit_length()-1]
            new = remaining.copy()
            del new[i]
            for j, p in zip(neighbors[i], row[1:]):
                if j in new:
                    new[j] &= table[j, i, INVERSE[p]]
                    if not new[j]:
                        break
            else:
                yield from extend(assigned | {i: row}, new)

    return extend({}, {i: (1 << len(states[i]))-1 for i in grid})


def representatives(pairs, neighbors, expected, missing=MISSING):
    grid = tuple(range(len(missing), 10))
    pool = set(partial_assignments(neighbors, grid))
    assert len(pool) == expected
    actions = [t for t in transformations(pairs, neighbors) if set(t[0][:len(missing)]) == set(missing)]
    for case in sorted(pool):
        if case not in pool:
            continue
        for order, slots, perm, colors in actions:
            image = [None]*10
            for i in grid:
                known = [case[i][1+k] for k in slots[i]]
                image[order[i]] = (colors[case[i][0]],)+tuple(perm[p] if p >= 0 else -1 for p in known)
            pool.discard(tuple(image))
        yield case


def cycle_graphs():
    graphs = set()
    for tail in permutations(range(1, 8)):
        order = (0,)+tail
        for cycles in ((order,), (order[:4], order[4:])):
            edges = frozenset(tuple(sorted(pair)) for cycle in cycles
                              for pair in zip(cycle, cycle[1:]+cycle[:1]))
            if sum(i < 4 and j < 4 for i, j in edges) <= 2:
                graphs.add(edges)
    return graphs


def cubic_graphs():
    """Each missing cell has the same number of internal edges, at most two."""
    for k in (0, 1, 2):
        for left in combinations(combinations(range(4), 2), k):
            degrees = [3-sum(i in edge for edge in left) for i in range(4)]
            for right in combinations(combinations(range(4), 2), k):
                targets = [3-sum(i in edge for edge in right) for i in range(4)]
                for columns in product(*(combinations(range(4), n) for n in degrees)):
                    if any(sum(i in row for row in columns) != targets[i] for i in range(4)):
                        continue
                    cross = [(i, 4+j) for i, row in enumerate(columns) for j in row]
                    yield tuple(left)+tuple((4+i, 4+j) for i, j in right)+tuple(cross)


def by_neighbor_coordinates(graphs):
    result = defaultdict(list)
    for edges in graphs:
        key = tuple(tuple(sorted((j if i == u else i) % 4 for i, j in edges if u in (i, j)))
                    for u in range(8))
        result[key].append(edges)
    return result


def known_edges(case, neighbors):
    matrix = np.zeros((44, 44), dtype=int)
    for i in GRID + (10,):
        opposite = OPPOSITES[0 if i == 10 else case[i][0]]
        for x in range(4):
            for y in set(range(4))-{x, opposite[x]}:
                matrix[4*i+x, 4*i+y] = 1
    for i in range(10):
        for x in range(4):
            matrix[4*i+x, 40+x] = matrix[40+x, 4*i+x] = 1
    for i in GRID:
        for j, p in zip(neighbors[i], case[i][1:]):
            if j in GRID:
                for x, y in enumerate(PERMS[p]):
                    matrix[4*i+x, 4*j+y] = 1
    return matrix


def far_completions(case, factors, neighbors):
    base = known_edges(case, neighbors)
    if np.any(base+base@base > 12*np.eye(44, dtype=int)+2):
        return
    splits = None
    for i in GRID:
        missing = [j for j in neighbors[i] if j in MISSING]
        if not missing:
            continue
        remaining = []
        for x in range(4):
            targets = [x, OPPOSITES[0][x], OPPOSITES[case[i][0]][x]]
            for j, p in zip(neighbors[i], case[i][1:]):
                if j in GRID:
                    targets.remove(PERMS[INVERSE[p]][x])
            remaining.append(targets)
        if len(missing) == 1:
            j, = missing
            for x, (y,) in enumerate(remaining):
                base[4*j+x, 4*i+y] = base[4*i+y, 4*j+x] = 1
        else:
            assert splits is None
            center = i
            splits = product(*(set(permutations(v)) for v in remaining))
    # Disjoint missing labels have no common Petersen neighbor.
    for split in splits if splits is not None else ((),):
        matrix = base.copy()
        for x, targets in enumerate(split):
            for j, y in zip(MISSING, targets):
                matrix[4*j+x, 4*center+y] = matrix[4*center+y, 4*j+x] = 1
        demand = []
        for v in range(8):
            needed = [0, 1, 2, 3, OPPOSITES[0][v % 4]]
            for y in np.flatnonzero(matrix[v, 8:40]):
                if y % 4 not in needed:
                    break
                needed.remove(y % 4)
            else:
                demand.append(tuple(sorted(needed)))
                continue
            break
        for edges in factors.get(tuple(demand), ()):
            completed = matrix.copy()
            for x, y in edges:
                completed[x, y] = completed[y, x] = 1
            yield completed


@lru_cache(None)
def signed_axes(cells, colors):
    choices = []
    for characters in product(*[set(range(3))-{color} for color in colors]):
        for tail in product((-1, 1), repeat=3):
            values = np.array((1,)+tail)[:, None]*CHARACTERS[list(characters)]
            if np.any(values.sum(axis=0)):
                continue
            incidence = np.zeros((44, 2), dtype=int)
            for i, row in zip(cells, values):
                for x, sign in enumerate(row):
                    incidence[4*i+x, int(sign < 0)] = 1
            choices.append((characters, incidence, incidence@incidence.T))
    return cells, choices


def near_completions(case, matrix, quota, pairs, missing_count=2, gram_test=gram_possible):
    central = np.zeros((44, 4), dtype=int)
    for a in range(2):
        for x, sign in enumerate(CHARACTERS[a+1]):
            central[40+x, 2*a+int(sign < 0)] = 1
    remaining = quota-central@central.T
    if not gram_test(remaining):
        return
    domains = []
    for a in range(5):
        cells = tuple(i for i, pair in enumerate(pairs) if a in pair)
        colors = tuple(case[i][0] if i >= missing_count else -1 for i in cells)
        cells, choices = signed_axes(cells, colors)
        allowed = [option for option in choices if gram_test(remaining-option[2])]
        if not allowed:
            return
        domains.append((a, cells, allowed))
    domains.sort(key=lambda group: len(group[2]))

    def extend(k, residual, characters, selected):
        if k == 5:
            full = np.zeros((59, 59), dtype=int)
            full[:44, :44] = matrix
            for axis, incidence in selected:
                full[:44, 44+2*axis:46+2*axis] = incidence
            full[:44, 54:58] = central
            full[44:58, :44] = full[:44, 44:58].T
            for i in range(44, 58, 2):
                full[i, i+1] = full[i+1, i] = 1
            full[58, 44:58] = full[44:58, 58] = 1
            yield full
            return
        axis, cells, allowed = domains[k]
        for choice, incidence, gram in allowed:
            if any(characters.get(i) == c for i, c in zip(cells, choice)):
                continue
            reduced = residual-gram
            if gram_test(reduced):
                yield from extend(k+1, reduced, characters | dict(zip(cells, choice)),
                                  selected+[(axis, incidence)])

    yield from extend(0, remaining, {}, [])


def verify(missing, expected, totals):
    pairs = missing+tuple(pair for pair in PAIRS if pair not in missing)
    neighbors = [tuple(j for j, g in enumerate(pairs) if not set(f) & set(g)) for f in pairs]
    intersect = bool(set(missing[0]) & set(missing[1]))
    factors = by_neighbor_coordinates(cycle_graphs() if intersect else cubic_graphs())
    counts = Counter()
    for case in representatives(pairs, neighbors, expected):
        counts['classes'] += 1
        for matrix in far_completions(case, factors, neighbors):
            quota = 12*np.eye(44, dtype=int)+2-matrix-matrix@matrix
            if np.any(quota < 0):
                continue
            counts['nonnegative'] += 1
            if not gram_possible(quota):
                continue
            counts['far Gram'] += 1
            for full in near_completions(case, matrix, quota, pairs):
                counts['near labelings'] += 1
                residual = 12*np.eye(59, dtype=int)+2-full-full@full
                assert not gram_possible(residual)
    assert [counts[k] for k in ('classes', 'nonnegative', 'far Gram', 'near labelings')] == totals
    print(f"Missing labels {missing}: {expected} assignments, {dict(counts)}, no extension.")


if __name__ == '__main__':
    verify(((0, 1), (0, 2)), 101164, [7738, 1272, 843, 96])
    verify(((0, 1), (2, 3)), 33033, [1490, 371, 287, 0])
