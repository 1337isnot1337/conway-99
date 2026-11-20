"""Exact boundary signatures for the five-rook Petersen interface core."""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations, product
import json
from math import lcm
from pathlib import Path
import time

import numpy as np
import sympy as sp


def build_core():
    vertices = tuple(combinations(range(5), 2))
    edges = tuple((i, j) for i, j in combinations(range(10), 2)
                  if not set(vertices[i]) & set(vertices[j]))
    assert len(edges) == 15
    colors = tuple(next(iter(set(range(5))-set(vertices[i])-set(vertices[j])))
                   for i, j in edges)
    line = np.array([[int(a != b and bool(set(edges[a]) & set(edges[b])))
                      for b in range(15)] for a in range(15)], dtype=np.int64)
    fibers = [[e for e in range(15) if colors[e] == c] for c in range(5)]
    # Gauge every matching to the color-zero fiber to the identity.
    for c in range(1, 5):
        fibers[c] = [next(e for e in fibers[c] if line[r, e]) for r in fibers[0]]
    assert all(len(set(f)) == 3 for f in fibers)
    maps = {}
    for i, j in combinations(range(5), 2):
        maps[i, j] = tuple(next(b for b in range(3) if line[fibers[i][a], fibers[j][b]])
                           for a in range(3))
    assert all(maps[0, j] == (0, 1, 2) for j in range(1, 5))
    points = tuple(product(range(3), repeat=2))
    rook = np.array([[int(x != z and (x[0] == z[0] or x[1] == z[1]))
                      for z in points] for x in points], dtype=np.int64)
    B = np.zeros((45, 45), dtype=np.int64)
    for i in range(5):
        B[9*i:9*i+9, 9*i:9*i+9] = rook
    matching_labels = []
    for (i, j), p in maps.items():
        label = []
        for x, y in points:
            u, v = (x+y) % 3, (x-y) % 3
            target = (2*(p[u]+v) % 3, 2*(p[u]-v) % 3)
            z = points.index(target)
            label.append(z)
            B[9*i+3*x+y, 9*j+z] = B[9*j+z, 9*i+3*x+y] = 1
        matching_labels.append([i, j, label])
    assert np.all(B.sum(axis=0) == 8)
    caps = B@B+B
    assert max(caps[i, j] for i, j in combinations(range(45), 2)) <= 2
    C = 12*np.eye(45, dtype=np.int64)+2*np.ones((45, 45), dtype=np.int64)-caps
    assert np.all(C >= 0) and np.all(np.diag(C) == 6)
    return B, C, matching_labels


def integral_nullspace(C):
    columns = []
    for vector in sp.Matrix(C).nullspace():
        multiple = lcm(*(v.q for v in vector))
        columns.append([int(v*multiple) for v in vector])
    result = np.array(columns, dtype=np.int64).T
    assert np.all(C@result == 0)
    return result


def audit():
    begin = time.monotonic()
    B, C, matching_labels = build_core()
    null = integral_nullspace(C)
    candidates = np.array(list(product(range(9), repeat=5)), dtype=np.int64)
    candidates += 9*np.arange(5, dtype=np.int64)
    counts = {'all_one_per_base_signatures': len(candidates)}
    mask = np.ones(len(candidates), dtype=bool)
    for i, j in combinations(range(5), 2):
        mask &= C[candidates[:, i], candidates[:, j]] > 0
    candidates = candidates[mask]
    counts['pair_quota_compatible'] = len(candidates)
    if len(candidates):
        H = np.zeros((len(candidates), 45), dtype=np.int64)
        H[np.arange(len(candidates))[:, None], candidates] = 1
        mask = np.all(H@B+H <= 2, axis=1)
        candidates, H = candidates[mask], H[mask]
        counts['cross_degree_compatible'] = len(candidates)
        mask = np.all(H@null == 0, axis=1)
        candidates, H = candidates[mask], H[mask]
        counts['gram_range_compatible'] = len(candidates)
    else:
        counts['cross_degree_compatible'] = counts['gram_range_compatible'] = 0
        H = np.zeros((0, 45), dtype=np.int64)
    result = {'core_order': 45, 'core_degree': 8,
              'boundary_count': 54, 'boundary_degree_at_core': 6,
              'boundary_degree_at_outside': 5,
              'gram_rank': 45-null.shape[1], 'gram_nullity': null.shape[1],
              'matching_permutations': matching_labels,
              'signature_counts': counts, 'signatures': candidates.tolist(),
              'gram_entry_counts': dict(sorted(Counter(map(int, C.flat)).items())),
              'seconds': time.monotonic()-begin}
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('matching_permutations', 'signatures')}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = audit()
    if args.output:
        args.output.write_text(json.dumps(result, indent=2)+'\n')
