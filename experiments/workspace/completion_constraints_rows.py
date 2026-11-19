"""Exact certificates excluding exterior signatures with no possible neighborhood.

The neighbors of a proposed exterior vertex already share that vertex.
Their signatures therefore form a pair packing on the fixed core.
"""
import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path

import numpy as np
from scipy import sparse as sp
from scipy.optimize import linprog

from broken_grid import canonical_cases
from completion_constraints import exact_farkas
from completion_constraints_packing import signatures


def prepare(B, domains):
    N = np.zeros((len(domains), len(B)), dtype=np.int16)
    for i, S in enumerate(domains):
        N[i, list(S)] = 1
    Q = N @ (B + np.eye(len(B), dtype=int))
    pairs = list(combinations(range(len(B)), 2))
    pair_incidence = sp.csr_matrix(np.array([N[:, i] * N[:, j] for i, j in pairs], dtype=np.int16))
    return N, Q, pairs, pair_incidence


def row_system(data, source, k=14):
    N, Q, pairs, pair_incidence = data
    allowed = (N @ N[source] <= 1) & ((Q == 2) @ N[source] == 0) & (N @ (Q[source] == 2) == 0)
    ids = np.flatnonzero(allowed)
    E = sp.csr_matrix(np.vstack((N[ids].T, np.ones(len(ids), dtype=int))))
    rhs = np.r_[2 - Q[source], k - int(N[source].sum())]
    I = pair_incidence[:, ids]
    active = np.flatnonzero(np.asarray(I.sum(axis=1)).ravel())
    I = I[active]
    # Turn pair-packing inequalities into equations with nonnegative slacks.
    augmented = sp.vstack((E, I), format='csc')
    slack = sp.vstack((sp.csc_matrix((E.shape[0], len(active))), sp.eye(len(active), dtype=int)), format='csc')
    augmented = sp.hstack((augmented, slack), format='csc')
    return ids, E, rhs, I, augmented, np.r_[rhs, np.ones(len(active), dtype=int)]


def check_ray(A, b, ray):
    if len(ray) != len(b):
        return False
    if sum(int(x) * int(y) for x, y in zip(ray, b)) >= 0:
        return False
    for col in range(A.shape[1]):
        if sum(int(ray[A.indices[t]]) * int(A.data[t]) for t in range(A.indptr[col], A.indptr[col + 1])) < 0:
            return False
    return True


def scan(case, limit=None):
    B = list(canonical_cases())[case][2]
    domains = signatures(B)
    data = prepare(B, domains)
    sources = [i for i, S in enumerate(domains) if sum(8 <= x < 14 for x in S) == 2]
    if limit is not None:
        sources = sources[:limit]
    status = Counter()
    certificates = []
    for source in sources:
        ids, E, rhs, I, A, b = row_system(data, source)
        result = linprog(np.zeros(len(ids)), A_eq=E, b_eq=rhs, A_ub=I, b_ub=np.ones(I.shape[0]), bounds=(0, None), method='highs')
        if result.status == 2:
            ray = exact_farkas(A, b)
            if ray is None:
                status['unverified infeasibility'] += 1
            else:
                assert check_ray(A, b, ray)
                status['exact exclusion'] += 1
                certificates.append({'source': source, 'signature': list(domains[source]), 'ray': ray})
        elif result.success:
            status['real row feasible'] += 1
        else:
            status['unknown'] += 1
    return {'case': case, 'sources_tested': len(sources), 'status': dict(status), 'certificates': certificates}


def replay(record):
    B = list(canonical_cases())[record['case']][2]
    domains = signatures(B)
    data = prepare(B, domains)
    for certificate in record['certificates']:
        source = certificate['source']
        assert list(domains[source]) == certificate['signature']
        *_, A, b = row_system(data, source)
        assert check_ray(A, b, certificate['ray'])
    return len(record['certificates'])


def control():
    from triangle_ball import golay
    G = golay()[0].astype(int)
    U = sorted(map(int, np.random.default_rng(123).choice(243, 27, replace=False)))
    outside = sorted(set(range(243)) - set(U))
    actual = {x: tuple(map(int, np.flatnonzero(G[x, U]))) for x in outside}
    domains = sorted(set(actual.values()))
    index = {S: i for i, S in enumerate(domains)}
    B = G[np.ix_(U, U)]
    data = prepare(B, domains)
    for x in outside:
        source = index[actual[x]]
        ids, E, rhs, I, _, _ = row_system(data, source, 22)
        lookup = {int(z): i for i, z in enumerate(ids)}
        count = np.zeros(len(ids), dtype=int)
        for y in outside:
            if G[x, y]:
                count[lookup[index[actual[y]]]] += 1
        assert np.array_equal(E @ count, rhs)
        assert np.all(I @ count <= 1)
    print(json.dumps({'positive_control': 'Golay', 'actual_exterior_rows_checked': len(outside), 'status': 'exact pass'}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control', action='store_true')
    p.add_argument('--case', type=int, default=5)
    p.add_argument('--limit', type=int)
    p.add_argument('--out', type=Path)
    p.add_argument('--replay', type=Path)
    args = p.parse_args()
    if args.control:
        control()
    elif args.replay:
        record = json.loads(args.replay.read_text())
        print(json.dumps({'exact_certificates_replayed': replay(record), 'case': record['case']}), flush=True)
    else:
        record = scan(args.case, args.limit)
        if args.out:
            args.out.write_text(json.dumps(record, indent=2) + '\n')
        print(json.dumps({k: v for k, v in record.items() if k != 'certificates'}), flush=True)
