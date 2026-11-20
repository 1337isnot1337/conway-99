"""Unrestricted exterior-incidence test for complete bootstrap seed layers.

The test is a relaxation. A feasible incidence count is not a completed graph.
Every reported exclusion must include an exact rational Farkas certificate.
"""
from __future__ import annotations

import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations
import json
from pathlib import Path
import time

import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog

from percolation_layers import canon, incidence, plans, seed


def catalog(kind: int) -> list[tuple[int, ...]]:
    B = seed(kind)
    result = {}
    for S in plans(B):
        result.setdefault(canon(B, S), S)
    return list(result.values())


def core(kind: int, case: int):
    B = seed(kind)
    S = catalog(kind)[case]
    N = incidence(B, S)
    need = 2 - (B + np.eye(len(B), dtype=int)) @ N
    candidates = [
        (len(B) + i, len(B) + j)
        for i, j in combinations(range(len(S)), 2)
        if N[:, i] @ N[:, j] < 2
        and np.all(N[:, i] <= need[:, j])
        and np.all(N[:, j] <= need[:, i])
    ]
    return np.block([[B, N], [N.T, np.zeros((len(S), len(S)), dtype=int)]]), candidates


def exterior_signatures(B: np.ndarray, complete_seed: int, k: int = 14):
    """Enumerate all possible exterior neighbor sets, using integer tests only."""
    n = len(B)
    cap = 2 - B - B @ B
    np.fill_diagonal(cap, 0)
    if np.any(cap < 0):
        return []
    compatible = [sum(1 << int(j) for j in np.flatnonzero(cap[i] > 0)) for i in range(n)]
    masks = []

    def extend(chosen: int, available: int, limits: np.ndarray):
        masks.append(chosen)
        if chosen.bit_count() >= k:
            return
        while available:
            bit = available & -available
            available -= bit
            i = bit.bit_length() - 1
            new_limits = limits + B[i]
            new_limits[i] += 1
            if np.max(new_limits) > 2:
                continue
            allowed = available & compatible[i]
            if i < complete_seed:
                allowed &= ~((1 << complete_seed) - 1)
            extend(chosen | bit, allowed, new_limits)

    extend(0, (1 << n) - 1, np.zeros(n, dtype=int))
    return masks


def incidence_equations(B: np.ndarray, masks: list[int], k: int = 14, v: int = 99):
    n = len(B)
    pairs = [(i, j) for i in range(n) for j in range(i, n)]
    index = {p: z for z, p in enumerate(pairs)}
    rows, cols = [], []
    for col, mask in enumerate(masks):
        sites = [i for i in range(n) if mask >> i & 1]
        for a, i in enumerate(sites):
            for j in sites[a:]:
                rows.append(index[i, j])
                cols.append(col)
        rows.append(len(pairs))
        cols.append(col)
    E = sp.csc_matrix((np.ones(len(rows), dtype=int), (rows, cols)), shape=(len(pairs) + 1, len(masks)))
    target = (k - 2) * np.eye(n, dtype=int) + 2 - B - B @ B
    rhs = np.array([int(target[i, j]) for i, j in pairs] + [v - n], dtype=int)
    return E, rhs


def exact_farkas(E, rhs):
    """Return an exactly checked integral dual ray, or None."""
    import highspy
    h = highspy.Highs()
    h.setOptionValue('output_flag', False)
    h.setOptionValue('presolve', 'off')
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = E.shape[1], E.shape[0]
    lp.col_cost_ = np.zeros(E.shape[1])
    lp.col_lower_ = np.zeros(E.shape[1])
    lp.col_upper_ = np.full(E.shape[1], highspy.kHighsInf)
    lp.row_lower_ = rhs.astype(float)
    lp.row_upper_ = rhs.astype(float)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = E.indptr
    lp.a_matrix_.index_ = E.indices
    lp.a_matrix_.value_ = E.data.astype(float)
    h.passModel(lp)
    h.run()
    if h.getModelStatus() != highspy.HighsModelStatus.kInfeasible:
        return None
    status, exists, ray = h.getDualRay()
    if not exists:
        return None
    from math import lcm, gcd
    for maxden in (1, 2, 4, 16, 64, 256, 4096, 100000):
        rat = [Fraction(float(x)).limit_denominator(maxden) for x in ray]
        mult = lcm(*(x.denominator for x in rat))
        y = np.array([int(x * mult) for x in rat], dtype=object)
        common = 0
        for x in y:
            common = gcd(common, abs(int(x)))
        if common:
            y //= common
        for sign in (1, -1):
            z = sign * y
            value = sum(int(a) * int(b) for a, b in zip(z, rhs))
            if value >= 0:
                continue
            if all(sum(int(z[E.indices[t]]) * int(E.data[t]) for t in range(E.indptr[c], E.indptr[c + 1])) >= 0 for c in range(E.shape[1])):
                return [int(x) for x in z]
    return None


def test(B, complete_seed=8, k=14, v=99, seconds=20):
    masks = exterior_signatures(B, complete_seed, k)
    if not masks:
        return {'status': 'common-neighbor violation'}
    E, rhs = incidence_equations(B, masks, k, v)
    opt = linprog(np.zeros(len(masks)), A_eq=E, b_eq=rhs, bounds=(0, None), method='highs', options={'time_limit': seconds})
    result = {'status': 'unresolved', 'signatures': len(masks), 'lp_status': int(opt.status)}
    if opt.status == 2:
        ray = exact_farkas(E, rhs)
        if ray is not None:
            result.update(status='exact incidence exclusion', dual=ray)
    elif opt.success:
        result['status'] = 'real incidence feasible'
        result['max_residual'] = float(np.max(np.abs(E @ opt.x - rhs)))
    return result


def controls():
    G = np.array([[int(i != j and (i // 3 == j // 3 or i % 3 == j % 3)) for j in range(9)] for i in range(9)], dtype=int)
    U = [0, 1, 3, 4, 2, 6, 5, 7]
    B = G[np.ix_(U, U)]
    actual = sum(int(G[8, x]) << i for i, x in enumerate(U))
    masks = exterior_signatures(B, 4, 4)
    assert actual in masks
    E, b = incidence_equations(B, masks, 4, 9)
    w = np.zeros(len(masks), dtype=int)
    w[masks.index(actual)] = 1
    assert np.array_equal(E @ w, b)
    from triangle_ball import golay
    G = golay()[0].astype(int)
    U = [0, 1, 3, 9]
    while True:
        more = [i for i in range(len(G)) if i not in U and sum(G[i, U]) >= 2]
        if not more:
            break
        previous = len(U)
        U.extend(more)
        if len(U) > 20:
            U = U[:previous]
            break
    B = G[np.ix_(U, U)]
    # Empty complete seed permits every true signature on this arbitrary core.
    masks = exterior_signatures(B, 0, 22)
    lookup = {m: i for i, m in enumerate(masks)}
    w = np.zeros(len(masks), dtype=int)
    for x in set(range(len(G))) - set(U):
        m = sum(int(G[x, y]) << i for i, y in enumerate(U))
        assert m in lookup
        w[lookup[m]] += 1
    E, b = incidence_equations(B, masks, 22, 243)
    assert np.array_equal(E @ w, b)
    # Independent one-variable contradictory system tests certificate orientation.
    E = sp.csc_matrix([[1], [1]])
    b = np.array([0, 1])
    ray = exact_farkas(E, b)
    assert ray is not None
    print(json.dumps({'rook': 'exact pass', 'golay_vertices': len(U), 'golay': 'exact pass', 'farkas': 'exact pass'}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control', action='store_true')
    p.add_argument('--kind', type=int, default=1)
    p.add_argument('--case', type=int, default=4)
    p.add_argument('--mask', type=int, default=0)
    p.add_argument('--seconds', type=float, default=20)
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    if args.control:
        controls()
    else:
        B, edges = core(args.kind, args.case)
        for z, (i, j) in enumerate(edges):
            if args.mask >> z & 1:
                B[i, j] = B[j, i] = 1
        result = test(B, seconds=args.seconds)
        result.update(kind=args.kind, case=args.case, mask=args.mask, unknown_edges=len(edges))
        if args.out:
            args.out.write_text(json.dumps(result) + '\n')
        print(json.dumps(result), flush=True)
