"""Exclude eight mutually aligned rooted grid cells by integer Gram constraints."""

from collections import Counter
from itertools import combinations, product

import numpy as np
from flint import fmpz_mat

from thirteen_grid_supports import unlabelled_graphs


AXIS_PAIRS = tuple(combinations(range(7), 2))


def disjoint(a, b):
    return a[0] not in b and a[1] not in b


def gram_matrices(labels):
    parent = list(range(len(labels)))

    def root(i):
        while parent[i] != i:
            i = parent[i]
        return i

    gram = 2*np.eye(len(labels), dtype=int)
    free = []
    for i, j in combinations(range(len(labels)), 2):
        if not disjoint(labels[i], labels[j]):
            continue
        gram[i, j] = gram[j, i] = 1
        a, b = root(i), root(j)
        if a == b:
            free.append((i, j))
        else:
            parent[a] = b
    # Reverse individual checkerboards to make spanning-forest signs positive.
    for signs in product((-1, 1), repeat=len(free)):
        for (i, j), sign in zip(free, signs):
            gram[i, j] = gram[j, i] = sign
        yield gram


def possible_rows(labels, gram, cell):
    if cell in labels:
        row = gram[labels.index(cell)]
        return [row, -row]
    active = [i for i, label in enumerate(labels) if disjoint(label, cell)]
    rows = []
    for signs in product((-1, 1), repeat=len(active)):
        row = np.zeros(len(labels), dtype=int)
        row[active] = signs
        rows.append(row)
    return rows


def projection_obstruction(labels, gram):
    """All computations use the integer adjugate of the positive Gram matrix."""
    exact = fmpz_mat(gram.tolist())
    det = int(exact.det())
    adj = np.array([[int(x*det) for x in row] for row in exact.inv().tolist()], dtype=int)
    assert np.array_equal(gram @ adj, det*np.eye(len(labels), dtype=int))
    pools = [possible_rows(labels, gram, f) for f in AXIS_PAIRS]
    costs = [[int(row @ adj @ row) for row in pool] for pool in pools]
    minimum = sum(min(c) for c in costs)
    needed = 7*len(labels)*det
    if minimum > needed:
        return 'projection norm'
    assert minimum == needed

    i, j = np.triu_indices(len(labels), 1)
    # Every actual row must minimize, and its pair products contribute to Y^t Y.
    options = [np.array([row[i]*row[j] for row, cost in zip(pool, c) if cost == min(c)])
               for pool, c in zip(pools, costs)]
    low = np.array([p.min(axis=0) for p in options])
    high = np.array([p.max(axis=0) for p in options])
    target = 7*gram[i, j]
    minimum, maximum = low.sum(axis=0), high.sum(axis=0)
    if np.any((target < minimum) | (target > maximum)):
        return 'pair interval'
    at_min, at_max = target == minimum, target == maximum
    for p, lower, upper in zip(options, low, high):
        if not np.any(np.all(p[:, at_min] == lower[at_min], axis=1) &
                      np.all(p[:, at_max] == upper[at_max], axis=1)):
            return 'incompatible pair extrema'
    raise AssertionError('eight-grid Gram survived')


def verify():
    counts = Counter()
    for edges in unlabelled_graphs():
        if len(edges) != 8:
            continue
        counts['supports'] += 1
        if max(sum(a in e for e in edges) for a in range(7)) == 6:
            counts['full star'] += 1
            continue
        labels = tuple(sorted(edges))
        for gram in gram_matrices(labels):
            counts['signings'] += 1
            if all(fmpz_mat(gram[:n, :n].tolist()).det() > 0 for n in range(2, 9)):
                counts[projection_obstruction(labels, gram)] += 1
    assert counts == {'supports': 97, 'full star': 2, 'signings': 22216,
                      'projection norm': 6, 'pair interval': 1, 'incompatible pair extrema': 1}
    print('Eight aligned grid cells: 97 supports, 22216 forest-normalized signings.')
    print('Eight positive definite cases, all excluded by the row projection equations.')


if __name__ == '__main__':
    verify()
