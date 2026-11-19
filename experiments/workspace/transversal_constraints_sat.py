"""Integral core incidences with common-neighbor caps between exterior columns.

A satisfying assignment is only a partial adjacency matrix. Exterior-to-
exterior edges are not assigned by this program.
"""

import argparse
from itertools import combinations
import json
from pathlib import Path
import threading
import time

import numpy as np
from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

from transversal_constraints_incidence import cases


def build(edges):
    r = len(edges)
    h = r + 7
    chosen = {tuple(sorted((2*a, 2*b))) for a, b in edges}
    labels = [e for e in combinations(range(14), 2)
              if e[0] // 2 != e[1] // 2 and e not in chosen]
    n = len(labels)
    pool = IDPool()
    X = np.array([[pool.id(('x', s, w)) for w in range(n)] for s in range(r)])
    cnf = CNF()

    def card(lits, low, high):
        lits = list(map(int, lits))
        if low > high or high < 0 or low > len(lits):
            cnf.append([])
            return
        if low > 0:
            cnf.extend(CardEnc.atleast(lits, bound=low, vpool=pool, encoding=EncType.seqcounter).clauses)
        if high < len(lits):
            cnf.extend(CardEnc.atmost(lits, bound=high, vpool=pool, encoding=EncType.seqcounter).clauses)

    def conjunction(a, b):
        z = pool.id()
        cnf.extend([[-z, int(a)], [-z, int(b)], [z, -int(a), -int(b)]])
        return z

    for s, e in enumerate(edges):
        for a in range(14):
            target = 2 - int(a // 2 in e)
            card((X[s, w] for w, label in enumerate(labels) if a in label), target, target)
    for s, t in combinations(range(r), 2):
        target = 2 - len(set(edges[s]) & set(edges[t]))
        card((conjunction(X[s, w], X[t, w]) for w in range(n)), target, target)
    for w, v in combinations(range(n), 2):
        cap = 2 - len(set(labels[w]) & set(labels[v]))
        card((conjunction(X[s, w], X[s, v]) for s in range(r)), 0, cap)
    degrees = [1 + sum(i in e for e in edges) for i in range(7)]
    budget = 2 * (22-h) * (27-h) - 12 - sum((d-3)*(d-4) for d in degrees)
    allowed_degrees = [d for d in range(1, 8) if (d-3)*(d-4) <= budget]
    for w, label in enumerate(labels):
        near_degree = sum(a % 2 for a in label)
        card(X[:, w], max(0, min(allowed_degrees)-near_degree), max(allowed_degrees)-near_degree)
        for i in range(7):
            cap = 2 - int(i in [a // 2 for a in label])
            card((X[s, w] for s, e in enumerate(edges) if i in e), 0, cap)
    return cnf, X, labels


def verify(edges, labels, incidence):
    r, n = incidence.shape
    near = np.array([[int(a in label) for label in labels] for a in range(14)], dtype=np.int64)
    target = np.array([[2-int(a//2 in e) for a in range(14)] for e in edges])
    assert np.array_equal(incidence @ near.T, target)
    gram = incidence @ incidence.T
    assert np.array_equal(np.diag(gram), np.full(r, 12))
    for s, t in combinations(range(r), 2):
        assert gram[s, t] == 2 - len(set(edges[s]) & set(edges[t]))
    gram = incidence.T @ incidence + near.T @ near
    assert max(gram[np.triu_indices(n, 1)]) <= 2
    into_I = incidence.sum(axis=0) + near[1::2].sum(axis=0)
    assert min(into_I) >= 1 and max(into_I) <= 7


def run(h, case, seconds, output=None):
    atlas, edges = cases(h)[case]
    start = time.monotonic()
    cnf, X, labels = build(edges)
    print(json.dumps({'h': h, 'case': case, 'atlas': atlas, 'variables': cnf.nv,
                      'clauses': len(cnf.clauses), 'build_seconds': time.monotonic()-start}), flush=True)
    with Solver(name='glucose42', bootstrap_with=cnf, with_proof=True) as solver:
        timer = threading.Timer(seconds, solver.interrupt)
        timer.start()
        try:
            status = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
        record = {'h': h, 'case': case, 'status': status, 'seconds': time.monotonic()-start,
                  'statistics': solver.accum_stats()}
        if status:
            positive = {x for x in solver.get_model() if x > 0}
            incidence = np.array([[int(x in positive) for x in row] for row in X], dtype=np.int64)
            verify(edges, labels, incidence)
            record['verified_partial_incidence'] = True
            if output:
                Path(output).write_text(json.dumps({'h': h, 'case': case, 'atlas': atlas,
                    'edges': edges, 'labels': labels, 'incidence': incidence.tolist()}))
        elif status is False and output:
            cnf.to_file(str(output)+'.cnf')
            Path(str(output)+'.drup').write_text('\n'.join(solver.get_proof())+'\n')
            record['proof_replay'] = 'not yet independently checked'
        print(json.dumps(record), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--h', type=int, default=20)
    parser.add_argument('--case', type=int, default=0)
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--output')
    args = parser.parse_args()
    run(args.h, args.case, args.seconds, args.output)
