"""Check actual graph counts and the nonnegative extension relaxation."""
import argparse
from itertools import combinations
from math import comb

import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
from pynauty import certificate

from subgraph_counts import build, identities, nauty, members


def rook_control(data):
    graphs, levels, _, _ = data
    lookup = {certificate(nauty(graphs[i])): i for level in levels[1:] for i in level}
    totals = [1, 1] + [0] * (len(graphs) - 1)
    for level in range(1, len(levels)):
        for subset in combinations(range(9), level):
            rows = tuple(sum(1 << j for j, b in enumerate(subset)
                             if a != b and (a//3 == b//3 or a%3 == b%3))
                         for a in subset)
            totals[1 + lookup[certificate(nauty(rows))]] += 1
    equations = 0
    for eq in identities(data, 9, 4):
        assert sum(value * totals[col] for col, value in eq.items()) == 0
        equations += 1
    print('rook integer identities checked', equations, flush=True)


def matrix(data, v, k):
    graphs, levels, _, _ = data
    # One variable per type, equal to its probability on a random subset
    # of the corresponding order.
    scale = [comb(v, len(graph)) for graph in graphs]
    ii, jj, vv, rhs = [], [], [], []
    for q, eq in enumerate(identities(data, v, k)):
        factors = {j-1: c * scale[j-1] for j, c in eq.items() if j}
        norm = max(abs(c) for c in factors.values())
        rhs.append(-eq.get(0, 0) / norm)
        for j, c in factors.items():
            ii.append(q)
            jj.append(j)
            vv.append(c / norm)
    return sp.coo_matrix((vv, (ii, jj)), shape=(len(rhs), len(graphs))).tocsr(), np.array(rhs)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('order', type=int)
    parser.add_argument('--rook', action='store_true')
    parser.add_argument('--parameters', nargs=2, type=int, default=[99, 14])
    parser.add_argument('--seconds', type=int, default=90)
    args = parser.parse_args()
    data = build(args.order)
    if args.rook:
        rook_control(data)
    A, b = matrix(data, *args.parameters)
    print('LP size', A.shape, 'nonzeros', A.nnz, flush=True)
    sol = linprog(np.zeros(A.shape[1]), A_eq=A, b_eq=b, bounds=(0, 1),
                  method='highs', options={'time_limit': args.seconds, 'threads': 1})
    print('LP status', sol.status, sol.message, flush=True)
    if sol.success:
        print('max residual', abs(A @ sol.x - b).max(), 'min entry', sol.x.min(), flush=True)


if __name__ == '__main__':
    main()
