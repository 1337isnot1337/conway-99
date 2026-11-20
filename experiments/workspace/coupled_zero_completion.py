"""Choose Z/L incidence over a fixed saved norm-16 partial witness.

UNSAT excludes only the supplied H/Z and H/L choices.  It does not
exclude the incidence template.  SAT is checked on the entire 35-core
and can be passed to the 64-point exterior completion constraints.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
from pathlib import Path
from threading import Timer
import time

import numpy as np
from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

from coupled_shells_low import low_labels
from coupled_shells_incidence import verify


def matrices(block, orbit, record):
    B = np.zeros((35, 35), dtype=int)
    N = np.zeros((35, 64), dtype=int)
    for p in range(8):
        for n in range(8):
            B[p, n+8] = B[n+8, p] = (block['rows'][p] >> n) & 1
    for h, (pp, nn) in enumerate(orbit['high'], 16):
        for p in pp:
            B[h, p] = B[p, h] = 1
        for n in nn:
            B[h, n+8] = B[n+8, h] = 1
    for l, (p, n) in enumerate(low_labels(orbit['single'])):
        N[p, l] = N[n+8, l] = 1
    for i, j in record['edges']:
        B[16+i, 16+j] = B[16+j, 16+i] = 1
    for h, l in record['low_edges']:
        N[16+h, l] = 1
    return B, N


def build(B, N, linear_only=False):
    cnf = CNF(); pool = IDPool()
    x = {(z, l): pool.id(('zero-low', z, l)) for z in range(24, 35) for l in range(64)}
    BB = B @ B

    def equal(lits, rhs):
        if rhs < 0 or rhs > len(lits):
            cnf.append([])
        elif lits:
            cnf.extend(CardEnc.equals(lits, bound=rhs, vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
        elif rhs:
            cnf.append([])

    def atmost(lits, rhs):
        if rhs < 0:
            cnf.append([])
        elif rhs < len(lits):
            cnf.extend(CardEnc.atmost(lits, bound=rhs, vpool=pool,
                                     encoding=EncType.seqcounter).clauses)

    def both(a, b, key):
        v = pool.id(key)
        cnf.extend([[-v, a], [-v, b], [v, -a, -b]])
        return v

    for l in range(64):
        equal([x[z, l] for z in range(24, 35)], 1+int(N[16:24, l].sum()))
    for z in range(24, 35):
        equal([x[z, l] for l in range(64)], 14-int(B[z].sum()))
        for p in range(24):
            equal([x[z, l] for l in range(64) if N[p, l]],
                  2-int(B[p, z])-int(BB[p, z]))
    for i in range(35):
        for l in range(64):
            terms = [x[z, l] for z in range(24, 35) if B[i, z]]
            constant = int(B[i, :24] @ N[:24, l])
            if i >= 24:
                terms.append(x[i, l])
            else:
                constant += int(N[i, l])
            atmost(terms, 2-constant)
    if not linear_only:
        for z, w in combinations(range(24, 35), 2):
            terms = [both(x[z, l], x[w, l], ('zz', z, w, l)) for l in range(64)]
            equal(terms, 2-int(B[z, w])-int(BB[z, w]))
        NN = N.T @ N
        for l, m in combinations(range(64), 2):
            terms = [both(x[z, l], x[z, m], ('ll', z, l, m)) for z in range(24, 35)]
            atmost(terms, 2-int(NN[l, m]))
    return cnf, x


def solve(block, orbit, record, seconds=10, linear_only=False):
    B, N = matrices(block, orbit, record)
    start = time.monotonic(); cnf, x = build(B, N, linear_only)
    result = {'core': block['core'], 'orbit': record['orbit'],
              'linear_only': linear_only, 'variables': cnf.nv,
              'clauses': len(cnf.clauses),
              'build_seconds': round(time.monotonic()-start, 4)}
    start = time.monotonic()
    with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
        timer = Timer(seconds, solver.interrupt); timer.start()
        try:
            status = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
        result.update(status='sat' if status is True else 'unsat' if status is False else 'unknown',
                      seconds=round(time.monotonic()-start, 4))
        if status:
            true = {v for v in solver.get_model() if v > 0}
            ze = [[z-16, l] for (z, l), v in x.items() if v in true]
            if not linear_only:
                verify(block['rows'], orbit, record['edges'], record['low_edges'], ze)
            result.update(edges=record['edges'], high_low_edges=record['low_edges'], zero_low_edges=ze)
            for z, l in ze:
                N[z+16, l] = 1
            if not linear_only:
                result.update(B=B.tolist(), N=N.tolist())
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--orbits', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-orbits.json'))
    p.add_argument('--old-witnesses', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-low-all.json'))
    p.add_argument('--core', type=int, nargs='*'); p.add_argument('--orbit', type=int, nargs='*')
    p.add_argument('--seconds', type=float, default=10)
    p.add_argument('--limit', type=int, default=10)
    p.add_argument('--linear-only', action='store_true')
    p.add_argument('--output', type=Path)
    a = p.parse_args()
    blocks = {b['core']: b for b in json.loads(a.orbits.read_text())}
    records = json.loads(a.old_witnesses.read_text()); output = []
    for r in records:
        if r['status'] != 'sat':
            continue
        if a.core is not None and r['core'] not in a.core:
            continue
        if a.orbit is not None and r['orbit'] not in a.orbit:
            continue
        b = blocks[r['core']]
        result = solve(b, b['orbits'][r['orbit']], r, a.seconds, a.linear_only)
        output.append(result)
        print({k: v for k, v in result.items() if k not in
               ('edges', 'high_low_edges', 'zero_low_edges', 'B', 'N')}, flush=True)
        if a.output:
            a.output.write_text(json.dumps(output, indent=2)+'\n')
        if result['status'] == 'sat' and not a.linear_only:
            break
        if len(output) >= a.limit:
            break


if __name__ == '__main__':
    main()
