"""Necessary projector conditions for a coclique containing a root transversal.

The chosen outer coclique vertices are edges of a seven-vertex graph L.
This file keeps the root and its unmatched neighbors in both spectral tests.
Numerical scouting is separated from the exact checks of surviving types.
"""

from itertools import combinations, permutations
import argparse
import json
import math
from pathlib import Path

import numpy as np


EDGES = list(combinations(range(7), 2))


def matrices(edges):
    """Return h, scaled integral negative/positive Schur complements."""
    h = 7 + len(edges)
    degrees = np.zeros(7, dtype=np.int64)
    D = np.zeros((8, 8), dtype=np.int64)
    D[0, 0] = 7
    D[0, 1:] = D[1:, 0] = 1
    B = np.zeros((8, 8), dtype=np.int64)
    B[0, 1:] = B[1:, 0] = 1
    for a, b in edges:
        degrees[a] += 1
        degrees[b] += 1
        D[a + 1, b + 1] = D[b + 1, a + 1] = 1
    d = np.r_[7, 1 + degrees]
    D[np.diag_indices(8)] = d
    q = d + 3
    neg = (h + 27) * (9 * np.eye(8, dtype=np.int64) - 3 * B - D) + np.outer(q, q)
    q = d - 4
    pos = (22 - h) * (16 * np.eye(8, dtype=np.int64) + 4 * B - D) - np.outer(q, q)
    return h, neg, pos


def scout(h, batch=10000):
    """Enumerate labelled patterns; eigenvalue status alone is not a proof."""
    r = h - 7
    B = np.zeros((8, 8), dtype=np.int64)
    B[0, 1:] = B[1:, 0] = 1
    all_count = budget_count = both_count = 0
    survivors = []
    chosen = iter(combinations(range(21), r))
    while True:
        block = list(__import__('itertools').islice(chosen, batch))
        if not block:
            break
        n = len(block)
        adj = np.zeros((n, 7, 7), dtype=np.int64)
        for k, choice in enumerate(block):
            for e in choice:
                a, b = EDGES[e]
                adj[k, a, b] = adj[k, b, a] = 1
        d = np.column_stack([np.full(n, 7), 1 + adj.sum(axis=1)])
        cost = ((d - 3) * (d - 4)).sum(axis=1)
        good = cost <= 2 * (22 - h) * (27 - h)
        all_count += n
        budget_count += int(good.sum())
        if not good.any():
            continue
        keep = np.flatnonzero(good)
        d = d[good]
        adj = adj[good]
        n = len(d)
        D = np.zeros((n, 8, 8), dtype=np.int64)
        D[:, 0, 1:] = D[:, 1:, 0] = 1
        D[:, 1:, 1:] = adj
        D[:, np.arange(8), np.arange(8)] = d
        q = d + 3
        neg = (h + 27) * (9 * np.eye(8, dtype=np.int64) - 3 * B - D) + q[:, :, None] * q[:, None, :]
        q = d - 4
        pos = (22 - h) * (16 * np.eye(8, dtype=np.int64) + 4 * B - D) - q[:, :, None] * q[:, None, :]
        eig = np.minimum(np.linalg.eigvalsh(neg)[:, 0], np.linalg.eigvalsh(pos)[:, 0])
        passed = np.flatnonzero(eig > -1e-7)
        both_count += len(passed)
        for ix in passed:
            survivors.append(block[keep[ix]])
    print(json.dumps({'h': h, 'labelled': all_count, 'budget': budget_count, 'projectors': both_count}), flush=True)
    return survivors


def audit_twenty():
    """Exact coverage and projector audit, independent of numerical eigensolves."""
    import networkx as nx
    import sympy as sy
    edge_index = {e: i for i, e in enumerate(EDGES)}
    admissible = set()
    for chosen in combinations(range(21), 13):
        degrees = [0] * 7
        for i in chosen:
            a, b = EDGES[i]
            degrees[a] += 1
            degrees[b] += 1
        if 12 + sum((d-2)*(d-3) for d in degrees) <= 28:
            admissible.add(sum(1 << i for i in chosen))
    covered = set()
    representatives = []
    perms = list(permutations(range(7)))
    for atlas, graph in enumerate(nx.graph_atlas_g()):
        if len(graph) != 7 or graph.number_of_edges() != 13:
            continue
        edges = list(graph.edges())
        if 12 + sum((graph.degree(i)-2)*(graph.degree(i)-3) for i in range(7)) > 28:
            continue
        orbit = {sum(1 << edge_index[tuple(sorted((p[a], p[b])))] for a, b in edges) for p in perms}
        assert orbit <= admissible and not orbit & covered
        covered |= orbit
        h, neg, pos = matrices(edges)
        assert np.array_equal(neg @ np.r_[4, np.ones(7, dtype=np.int64)], np.zeros(8, dtype=np.int64))
        assert np.array_equal(pos @ np.r_[-3, np.ones(7, dtype=np.int64)], np.zeros(8, dtype=np.int64))
        for matrix in (neg, pos):
            # The seven unmatched-neighbor principal block is positive definite.
            # Together with the displayed nonzero-root kernel vector, this
            # proves positive semidefiniteness of the full eight-point matrix.
            assert all(sy.Matrix(matrix[1:k+1, 1:k+1]).det() > 0 for k in range(1, 8))
        representatives.append({'atlas': atlas, 'orbit': len(orbit), 'edges': edges})
    assert covered == admissible
    result = {'h': 20, 'labelled': math.comb(21, 13), 'budget': len(admissible),
              'unlabelled': len(representatives), 'projectors_exclude': 0,
              'representatives': representatives}
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('h', type=int, nargs='*')
    parser.add_argument('--audit-twenty', action='store_true')
    args = parser.parse_args()
    if args.audit_twenty:
        audit_twenty()
    for h in args.h:
        scout(h)
