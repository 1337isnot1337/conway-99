"""Finite exterior domains and lazy common-neighbor caps for one core.

SAT yields only a verified incidence completion of the determined core.
It does not assign edges between exterior vertices.
"""

import argparse
from collections import defaultdict
from itertools import combinations
import json
from pathlib import Path
import time

import numpy as np
from ortools.sat.python import cp_model

from transversal_constraints_incidence import build, cases


def verify(edges, labels, incidence, axes=7):
    r, n = incidence.shape
    near = np.array([[int(a in label) for label in labels] for a in range(2*axes)], dtype=np.int64)
    target = np.array([[2-int(a//2 in e) for a in range(2*axes)] for e in edges])
    assert np.array_equal(incidence @ near.T, target)
    gram = incidence @ incidence.T
    assert np.array_equal(np.diag(gram), np.full(r, 2*axes-2))
    for s, t in combinations(range(r), 2):
        assert gram[s, t] == 2 - len(set(edges[s]) & set(edges[t]))
    gram = incidence.T @ incidence + near.T @ near
    assert max(gram[np.triu_indices(n, 1)]) <= 2
    into_I = incidence.sum(axis=0) + near[1::2].sum(axis=0)
    assert min(into_I) >= 1 and max(into_I) <= axes


def controls():
    from triangle_ball import golay
    rook = np.array([[int(i != j and (i//3 == j//3 or i%3 == j%3))
                      for j in range(9)] for i in range(9)], dtype=np.int64)
    for A in (rook, golay()[0].astype(np.int64)):
        root = 0
        neighbors = set(np.flatnonzero(A[root]))
        near_vertices = []
        while neighbors:
            a = min(neighbors)
            b = next(b for b in neighbors if A[a, b])
            near_vertices.extend([a, b])
            neighbors -= {a, b}
        axes = len(near_vertices)//2
        T = near_vertices[1::2]
        far = [v for v in range(len(A)) if v != root and v not in near_vertices]
        labels_by_vertex = {v: tuple(np.flatnonzero(A[v, near_vertices])) for v in far}
        candidates = [v for v in far if not A[v, T].any()]
        S = []
        for v in candidates:
            if not S or not A[v, S].any():
                S.append(v)
        rest = [v for v in far if v not in S]
        edges = [tuple(a//2 for a in labels_by_vertex[v]) for v in S]
        labels = [labels_by_vertex[v] for v in rest]
        incidence = A[np.ix_(S, rest)]
        verify(edges, labels, incidence, axes)
        print(json.dumps({'control_vertices': len(A), 'axes': axes,
                          'coclique': len(T)+len(S), 'selected_rows': len(S),
                          'exterior_labels': len(rest), 'exact_incidence_control': True}), flush=True)


def run(case, seconds, output=None):
    atlas, edges = cases(20)[case]
    A, b, labels, variables = build(edges, degree_cuts=True)
    del A, b
    r = len(edges)
    n = len(labels)
    domains = defaultdict(list)
    for w, mask in variables:
        domains[w].append([(mask >> s) & 1 for s in range(r)])
    model = cp_model.CpModel()
    X = [[model.new_bool_var(f'x{s}_{w}') for w in range(n)] for s in range(r)]
    for w in range(n):
        model.add_allowed_assignments([X[s][w] for s in range(r)], domains[w])
    for s, e in enumerate(edges):
        for a in range(14):
            model.add(sum(X[s][w] for w, label in enumerate(labels) if a in label) == 2-int(a//2 in e))
    for s, t in combinations(range(r), 2):
        products = []
        for w in range(n):
            z = model.new_bool_var('')
            model.add_multiplication_equality(z, [X[s][w], X[t][w]])
            products.append(z)
        model.add(sum(products) == 2-len(set(edges[s]) & set(edges[t])))
    near = np.array([[int(a in label) for label in labels] for a in range(14)], dtype=np.int64)
    fixed_gram = near.T @ near
    start = time.monotonic()
    rounds = 0
    cuts = 0
    while time.monotonic()-start < seconds:
        solver = cp_model.CpSolver()
        solver.parameters.num_workers = 2
        solver.parameters.max_time_in_seconds = max(0.1, seconds-(time.monotonic()-start))
        solver.parameters.random_seed = 1
        status = solver.solve(model)
        rounds += 1
        record = {'h': 20, 'case': case, 'atlas': atlas, 'round': rounds,
                  'status': solver.status_name(status), 'cuts': cuts,
                  'seconds': round(time.monotonic()-start, 3),
                  'conflicts': solver.num_conflicts, 'branches': solver.num_branches}
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(json.dumps(record), flush=True)
            return
        incidence = np.array([[solver.value(x) for x in row] for row in X], dtype=np.int64)
        gram = incidence.T @ incidence + fixed_gram
        violations = np.argwhere(np.triu(gram, 1) > 2)
        record['column_pair_violations'] = len(violations)
        print(json.dumps(record), flush=True)
        if not len(violations):
            verify(edges, labels, incidence)
            if output:
                Path(output).write_text(json.dumps({'h': 20, 'case': case, 'atlas': atlas,
                    'edges': [list(e) for e in edges], 'labels': [list(e) for e in labels],
                    'incidence': incidence.tolist()})+'\n')
            print('verified partial core incidence; exterior edges remain unassigned', flush=True)
            return
        for w, v in violations:
            cap = 2-fixed_gram[w, v]
            support = np.flatnonzero(incidence[:, w]*incidence[:, v])[:cap+1]
            model.add_bool_or([X[s][u].Not() for s in support for u in (w, v)])
            cuts += 1


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--control', action='store_true')
    parser.add_argument('--case', type=int, default=0)
    parser.add_argument('--seconds', type=int, default=45)
    parser.add_argument('--output')
    args = parser.parse_args()
    if args.control:
        controls()
    else:
        run(args.case, args.seconds, args.output)
