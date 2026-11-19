"""Exact finite restrictions on the connected components of full triangles."""
from collections import Counter
from itertools import combinations

import numpy as np
import pynauty


def certificate(h):
    graph = pynauty.Graph(len(h), adjacency_dict={
        i: np.flatnonzero(row).tolist() for i, row in enumerate(h)
    })
    return pynauty.certificate(graph)


def positive_semidefinite(matrix):
    a = matrix.tolist()
    previous = 1
    while a:
        pivot = a[0][0]
        if pivot < 0 or (pivot == 0 and any(a[0])):
            return False
        if pivot == 0:
            a = [row[1:] for row in a[1:]]
            continue
        remaining = []
        for i in range(1, len(a)):
            row = []
            for j in range(1, len(a)):
                entry, rem = divmod(pivot*a[i][j] - a[i][0]*a[0][j], previous)
                assert rem == 0
                row.append(entry)
            remaining.append(row)
        a = remaining
        previous = pivot
    return True


def allowed(h):
    common = h @ h
    if np.any((h == 1) & (common > 1)):
        return False
    triangles = (common * h).sum(axis=1) // 2
    if np.any(h.sum(axis=1) - triangles > 3):
        return False
    for i, j in combinations(range(len(h)), 2):
        if h[i, j] and common[i, j]:
            k = int(np.flatnonzero(h[i] & h[j])[0])
            if j < k:
                counts = h[i] + h[j] + h[k]
                counts[[i, j, k]] -= 1
                if np.any(counts != 1):
                    return False
    return positive_semidefinite(3*np.eye(len(h), dtype=int) - 3*h + 1)


def extensions(h):
    m = len(h)
    # One grid page at the new vertex contributes one neighbor or an adjacent pair.
    groups = [(a,) for a in range(m)]
    groups += [(a, b) for a, b in combinations(range(m), 2) if h[a, b]]
    seen = set()
    for size in (1, 2, 3):
        for selection in combinations(groups, size):
            neighbors = tuple(sorted(v for group in selection for v in group))
            if len(set(neighbors)) != len(neighbors) or neighbors in seen:
                continue
            seen.add(neighbors)
            bigger = np.zeros((m+1, m+1), dtype=int)
            bigger[:m, :m] = h
            bigger[m, list(neighbors)] = bigger[list(neighbors), m] = 1
            if allowed(bigger):
                yield bigger


def candidates():
    level = [np.zeros((1, 1), dtype=int)]
    while level:
        yield from level
        next_level = {}
        for h in level:
            for bigger in extensions(h):
                next_level.setdefault(certificate(bigger), bigger)
        level = list(next_level.values())
    # The remaining components have a single full triangle on every block.
    for number in range(4, 7):
        for paired in range(number+1):
            size = 1 + number + paired
            h = np.zeros((size, size), dtype=int)
            h[0, 1:] = h[1:, 0] = 1
            for a in range(1, 1 + 2*paired, 2):
                h[a, a+1] = h[a+1, a] = 1
            yield h


def forced_triangles(h):
    """Keep each vector's coefficients and inner products with the original full lines."""
    m = len(h)
    coefficients = list(np.eye(m, dtype=int))
    rows = list(3*np.eye(m, dtype=int) - 3*h + 1)
    known = {tuple(r): i for i, r in enumerate(rows)}
    i = 0
    while i < len(rows):
        for j in np.flatnonzero(rows[i] == -2):
            new_row = -rows[i] - rows[j]
            key = tuple(new_row)
            if key in known:
                continue
            # Distinct saturated triangles from a single component are disjoint.
            if any(int(c @ new_row) not in (-2, 1) for c in coefficients):
                return None
            known[key] = len(rows)
            rows.append(new_row)
            coefficients.append(-coefficients[i] - coefficients[j])
        i += 1
    gram = np.array(coefficients) @ np.array(rows).T
    if np.any((gram == -2).sum(axis=1) > 12):
        return None
    grids = set()
    for i, j in combinations(range(len(rows)), 2):
        if gram[i, j] == -2:
            k = known.get(tuple(-rows[i] - rows[j]))
            if k is not None:
                grids.add(tuple(sorted((i, j, k))))
    degrees = Counter(i for tri in grids for i in tri)
    if any(degrees[i] > (6 if i < m else 4) for i in range(len(rows))):
        return None
    return (gram == -2).astype(int)


def best_savings(options, limit):
    table = [0]
    for t in range(1, limit+1):
        table.append(max(table[t-m] + saving for m, saving in options if m <= t))
    return table


def main():
    pairs = list(combinations(range(6), 2))
    forbidden = certificate(np.array([[int(set(e).isdisjoint(f)) for f in pairs] for e in pairs]))
    options = set()
    no_double = set()
    census = Counter()
    for h in candidates():
        census['candidates'] += 1
        forced = forced_triangles(h)
        if forced is None:
            continue
        census['consistent'] += 1
        if len(forced) == 15 and certificate(forced) == forbidden:
            continue
        census['remaining'] += 1
        triples = int(np.trace(h @ h @ h)) // 6
        doubles = int(h.sum()) // 2 - 3*triples
        entry = len(h), doubles + 2*triples
        options.add(entry)
        if doubles == 0:
            no_double.add(entry)
    best = best_savings(options, 28)
    isolated = best_savings(no_double, 24)[24]
    assert census == {'candidates': 200, 'consistent': 150, 'remaining': 48}
    assert best[24:] == [36, 36, 37, 38, 40] and isolated == 28
    print('Full components: 200 candidates, 150 pass closure, 48 remain after the 45-point exclusion.')
    print('Maximum double plus twice triple grids at 24 to 28 full triangles:', best[24:])
    print('With 24 full triangles and no double grids:', isolated)


if __name__ == '__main__':
    main()
