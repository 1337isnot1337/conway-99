"""Classify the incidences on the four corners, four tips, and six pair vertices."""
import json
from itertools import combinations, product
from pathlib import Path

import numpy as np
import pynauty

from broken_grid import canonical_cases


def quota(a):
    return 12 * np.eye(len(a), dtype=int) + 2 - a - a @ a


def profiles(core):
    residual = quota(core)
    pairs = [(i, j) for i, j in combinations(range(8, 14), 2)
             for _ in range(residual[i, j])]
    assert len(pairs) == 4
    assert not any(all(residual[i, j] for i, j in combinations(triple, 2))
                   for triple in combinations(range(8, 14), 3))
    seen = set()
    for anchors in product(range(8), repeat=4):
        doubles = tuple(sorted((v, *pair) for v, pair in zip(anchors, pairs)))
        if doubles in seen:
            continue
        seen.add(doubles)
        singles = residual[:8, 8:14].copy()
        for v, i, j in doubles:
            singles[v, i-8] -= 1
            singles[v, j-8] -= 1
        if singles.min() < 0:
            continue
        rows = list(doubles)
        rows.extend((v, i+8) for v in range(8) for i in range(6)
                    for _ in range(singles[v, i]))
        for v in range(8):
            rows.extend([(v,)] * (residual[v, v] - sum(r[0] == v for r in rows)))
        if len(rows) != 72:
            continue
        incidence = np.zeros((85, 14), dtype=np.int16)
        incidence[:13] = core[14:, :14]
        for i, row in enumerate(rows, 13):
            incidence[i, list(row)] = 1
        a = core[:14, :14]
        if np.array_equal(incidence.T @ incidence, quota(a)) and np.max(incidence @ a + incidence) <= 2:
            yield incidence


def profile_key(core, incidence):
    graph = {i: list(np.flatnonzero(core[i, :14])) for i in range(14)}
    for i, row in enumerate(incidence, 14):
        graph[i] = list(np.flatnonzero(row))
        for j in graph[i]:
            graph[j].append(i)
    colors = [set(range(lo, hi)) for lo, hi in ((0, 4), (4, 8), (8, 14), (14, 27), (27, 99))]
    return pynauty.certificate(pynauty.Graph(99, adjacency_dict=graph, vertex_coloring=colors))


def verify_example(core, record):
    rows = record['rows']
    b = np.array([[(row >> j) & 1 for j in range(27)] for row in rows], dtype=np.int16)
    assert b.shape == (72, 27) and np.array_equal(b.T @ b, quota(core))
    assert max(rows) < 1 << 27 and np.triu(b @ b.T, 1).max() <= 2
    required = 2 - b - b @ core
    assert required.min() >= 0
    # The chosen exterior point must have the indicated number of neighbors
    # attached to the marked core vertex. Even the pairwise eligible pool is too small.
    w, i = record['failed_quota']
    possible = [j for j, row in enumerate(b) if j != w and row[i] and row @ b[w] <= 1
                and np.all(required[w] >= row) and np.all(required[j] >= b[w])]
    assert len(possible) < required[w, i]
    return len(possible), required[w, i]


def main():
    path = Path(__file__).with_name('incomplete-grid-incidences.json')
    examples = json.loads(path.read_text())
    assert set(examples) == {str(i) for i in range(8)}
    counts = []
    for i, (_, _, core) in enumerate(canonical_cases()):
        seen = set()
        total = 0
        for b in profiles(core):
            total += 1
            seen.add(profile_key(core, b))
        counts.append((total, len(seen)))
        verify_example(core, examples[str(i)])
    assert counts == [(157, 157), (224, 120), (90, 27), (219, 116),
                      (256, 76), (225, 36), (340, 90), (256, 39)]
    print('Incomplete-grid profiles by core:', counts)
    print(f'661 marked profiles; verified {len(examples)} integral allocations and their failed adjacency quotas.')


if __name__ == '__main__':
    main()
