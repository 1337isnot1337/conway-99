"""Replay exact obstructions to symmetric edge completion of an incidence matrix."""
import argparse
from itertools import combinations
from collections import Counter
import json
from pathlib import Path

import numpy as np
from scipy import sparse as sp

from broken_grid import canonical_cases
from completion_constraints_packing import signatures
from completion_constraints_rows import check_ray


def edge_system(B, N, k=14):
    n, exterior = N.shape
    need = np.vstack((2 - (B + np.eye(n, dtype=int)) @ N, k - N.sum(axis=0)))
    columns = np.vstack((N, np.ones(exterior, dtype=int)))
    common = N.T @ N
    pairs = [(i, j) for i, j in combinations(range(exterior), 2)
             if common[i, j] <= 1 and np.all(columns[:, i] <= need[:, j])
             and np.all(columns[:, j] <= need[:, i])]
    rows, cols = [], []
    for variable, (i, j) in enumerate(pairs):
        for a, b in ((i, j), (j, i)):
            for coordinate in np.flatnonzero(columns[:, b]):
                rows.append(a * (n + 1) + int(coordinate))
                cols.append(variable)
    E = sp.csc_matrix((np.ones(len(rows), dtype=int), (rows, cols)), shape=(exterior * (n + 1), len(pairs)))
    rhs = need.T.ravel()
    # H_ij <= 1 becomes H_ij + slack_ij = 1, with both variables nonnegative.
    augmented = sp.vstack((E, sp.eye(len(pairs), dtype=int)), format='csc')
    slack = sp.vstack((sp.csc_matrix((len(rhs), len(pairs))), sp.eye(len(pairs), dtype=int)), format='csc')
    augmented = sp.hstack((augmented, slack), format='csc')
    return pairs, E, rhs, augmented, np.r_[rhs, np.ones(len(pairs), dtype=int)]


def replay(record):
    B = list(canonical_cases())[record['case']][2]
    domains = signatures(B)
    witness = record['native_packing']['witness']
    ids = record['selected_signature_indices']
    assert Counter(ids) == Counter({int(i): int(n) for i, n in witness.items()})
    chosen = [domains[i] for i in ids]
    N = np.array([[int(i in S) for S in chosen] for i in range(len(B))], dtype=int)
    assert N.shape == (27, 72)
    quota = 12 * np.eye(27, dtype=int) + 2 - B - B @ B
    assert np.array_equal(N @ N.T, quota)
    common = N.T @ N
    np.fill_diagonal(common, 0)
    assert np.max(common) <= 2
    pairs, E, b, A, rhs = edge_system(B, N)
    assert check_ray(A, rhs, record['ray'])
    return {'case': record['case'], 'incidence_columns': N.shape[1], 'edge_variables': len(pairs),
            'status': 'integer incidence valid; symmetric edge completion exactly excluded'}


def control():
    from triangle_ball import golay
    G = golay()[0].astype(int)
    U = sorted(map(int, np.random.default_rng(123).choice(243, 27, replace=False)))
    outside = sorted(set(range(243)) - set(U))
    B = G[np.ix_(U, U)]
    N = G[np.ix_(U, outside)]
    H = G[np.ix_(outside, outside)]
    pairs, E, rhs, _, _ = edge_system(B, N, 22)
    values = np.array([H[i, j] for i, j in pairs], dtype=int)
    assert int(values.sum()) * 2 == int(H.sum())
    assert np.array_equal(E @ values, rhs)
    print(json.dumps({'positive_control': 'Golay', 'actual_exterior_edges': int(values.sum()),
                      'candidate_edges': len(pairs), 'status': 'exact pass'}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control', action='store_true')
    p.add_argument('--replay', type=Path)
    args = p.parse_args()
    if args.control:
        control()
    if args.replay:
        print(json.dumps(replay(json.loads(args.replay.read_text()))), flush=True)
