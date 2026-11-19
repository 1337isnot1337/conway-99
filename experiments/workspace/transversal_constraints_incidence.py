"""Exterior signature relaxation for a fixed transversal coclique.

No automorphism is imposed on a completed graph. The seven-axis graph records
only which outer vertices belong to the independent set.
"""

from itertools import combinations
from pathlib import Path
import argparse
import json
import time

import networkx as nx
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
import sympy as sy
from transversal_constraints import matrices


def cases(h):
    r = h - 7
    out = []
    for atlas_index, graph in enumerate(nx.graph_atlas_g()):
        if len(graph) != 7 or graph.number_of_edges() != r:
            continue
        degrees = np.array([graph.degree(i) for i in range(7)])
        cost = 12 + int(((degrees - 2) * (degrees - 3)).sum())
        if cost <= 2 * (22 - h) * (27 - h):
            out.append((atlas_index, list(graph.edges())))
    return out


def build(edges, integer_degree_profile=None, spectral=True, degree_cuts=False):
    r = len(edges)
    h = r + 7
    # Even near labels are the unmatched neighbors; odd labels form I.
    outer = [e for e in combinations(range(14), 2) if e[0] // 2 != e[1] // 2]
    chosen = {tuple(sorted((2*a, 2*b))) for a, b in edges}
    labels = [e for e in outer if e not in chosen]
    n = len(labels)
    pair_keys = list(combinations(range(r), 2))
    rhs = [1] * n
    # Complete codegree identities between each selected vertex and all anchors.
    rhs += [2 - int(a // 2 in e) for e in edges for a in range(14)]
    rhs += [2 - len(set(edges[a]) & set(edges[b])) for a, b in pair_keys]
    degree_offset = len(rhs)
    if integer_degree_profile is not None:
        known = [7] + [1 + sum(i in e for e in edges) for i in range(7)]
        rhs += [integer_degree_profile[k-1] - known.count(k) for k in range(1, 8)]
    all_subsets = np.arange(1 << r, dtype=np.int64)
    bits = ((all_subsets[:, None] >> np.arange(r)) & 1).astype(np.int8)
    inc = np.array([[int(a in e) for a in range(7)] for e in edges], dtype=np.int8)
    degrees = bits @ inc
    sizes = bits.sum(axis=1)
    core_degrees = 1 + inc.sum(axis=0)
    if degree_cuts:
        assert h == 20 and max(core_degrees) < 7
        remaining_budget = 28 - 12 - int(((core_degrees-3)*(core_degrees-4)).sum())
    if spectral:
        _, neg, pos = matrices(edges)
        inverses = []
        for matrix in (neg[1:, 1:], pos[1:, 1:]):
            assert all(sy.Matrix(matrix[:k, :k]).det() > 0 for k in range(1, 8))
            exact = sy.Matrix(matrix).inv()
            denominator = int(sy.ilcm(*(v.q for v in exact)))
            numerator = np.array(exact * denominator, dtype=np.int64)
            assert np.array_equal(matrix @ numerator, denominator * np.eye(7, dtype=np.int64))
            inverses.append((numerator, denominator))
    I = []
    J = []
    V = []
    variables = []
    column = 0
    for w, label in enumerate(labels):
        cap = np.full(7, 2)
        cap[[a // 2 for a in label]] = 1
        near_degree = sum(a % 2 for a in label)
        good = np.all(degrees <= cap, axis=1) & (sizes + near_degree >= 1) & (sizes + near_degree <= 7)
        if degree_cuts:
            d = sizes + near_degree
            good &= (d >= 2) & ((d-3)*(d-4) <= remaining_budget)
            permits_six = all(a % 2 == 0 and core_degrees[a//2] == 5 for a in label)
            if not permits_six:
                good &= d != 6
        if spectral:
            d = sizes + near_degree
            adjacent = np.zeros(7, dtype=np.int64)
            common = degrees.astype(np.int64).copy()
            for a in label:
                if a % 2:
                    common[:, a // 2] += 1
                else:
                    adjacent[a // 2] = 1
            qn = -(h + 27) * (3 * adjacent + common) + (d[:, None] + 3) * (core_degrees + 3)
            qp = (22 - h) * (4 * adjacent - common) - (d[:, None] - 4) * (core_degrees - 4)
            cn = (h + 27) * (9 - d) + (d + 3) ** 2
            cp = (22 - h) * (16 - d) - (d - 4) ** 2
            for q, c, (numerator, denominator) in zip((qn, qp), (cn, cp), inverses):
                # The asserted bound covers every integer multiplication/sum.
                bound = 49 * int(abs(q).max()) ** 2 * int(abs(numerator).max())
                bound = max(bound, int(abs(c).max()) * denominator)
                assert bound < 2**63
                good &= np.einsum('ij,ij->i', q @ numerator, q) <= denominator * c
        for mask in np.flatnonzero(good):
            rows = [w]
            support = np.flatnonzero(bits[mask])
            for s in support:
                rows.extend(n + 14 * int(s) + a for a in label)
            for j, (s, t) in enumerate(pair_keys):
                if bits[mask, s] and bits[mask, t]:
                    rows.append(n + 14 * r + j)
            if integer_degree_profile is not None:
                rows.append(degree_offset + int(sizes[mask]) + near_degree - 1)
            I.extend(rows)
            J.extend([column] * len(rows))
            V.extend([1] * len(rows))
            variables.append((w, int(mask)))
            column += 1
    A = sp.csc_matrix((np.array(V, dtype=np.int64), (I, J)), shape=(len(rhs), column))
    return A, np.array(rhs, dtype=np.int64), labels, variables


def run(h, selected=None, seconds=30, degree_cuts=False):
    for index, (atlas, edges) in enumerate(cases(h)):
        if selected is not None and index not in selected:
            continue
        if degree_cuts and any(sum(i in e for e in edges) == 6 for i in range(7)):
            continue
        start = time.monotonic()
        A, b, labels, variables = build(edges, degree_cuts=degree_cuts)
        result = linprog(np.zeros(A.shape[1]), A_eq=A, b_eq=b,
                         bounds=(0, 1), method='highs',
                         options={'time_limit': seconds, 'threads': 1})
        record = {'h': h, 'case': index, 'atlas': atlas, 'edges': edges,
                  'shape': A.shape, 'status': result.status,
                  'integer_degree_cuts': degree_cuts,
                  'seconds': round(time.monotonic()-start, 3)}
        if result.x is not None:
            record['residual'] = float(max(abs(A @ result.x - b)))
        print(json.dumps(record), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--h', type=int, default=20)
    parser.add_argument('--cases', type=int, nargs='*')
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--integer-degree-cuts', action='store_true')
    args = parser.parse_args()
    run(args.h, args.cases, args.seconds, args.integer_degree_cuts)
