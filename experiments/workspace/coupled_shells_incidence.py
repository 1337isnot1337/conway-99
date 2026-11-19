"""Full exterior-incidence Gram test on the 35-point P/N/H/Z core.

All adjacency entries are chosen except those between the 64 L vertices.
A SAT witness has correct degree and pair common-neighbor equations on the
entire 35-point core, and no partial pair exceeds its allowed common-neighbor
count.  It is not a 99-vertex strongly regular graph.
"""
from __future__ import annotations

import argparse
from itertools import combinations
import json
from pathlib import Path
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

from coupled_shells import four_high_obstruction
from coupled_shells_low import extend_model, low_labels


def build(rows, orbit):
    cnf, edge, high_low, labels, hd, zd, cc = extend_model(rows, orbit)
    pool = IDPool(start_from=cnf.nv + 1)
    zero_low = {(z, l): pool.id(('zero-low', z, l)) for z in range(8, 19) for l in range(64)}
    sig = [set(p) | {n + 8 for n in ns} for p, ns in orbit['high']]
    lsig = [{p, n + 8} for p, n in labels]
    def E(i, j): return edge[tuple(sorted((i, j)))]
    def T(i, l): return high_low[i, l] if i < 8 else zero_low[i, l]
    def AND(a, b, key):
        v = pool.id(key)
        cnf.extend([[-v, a], [-v, b], [v, -a, -b]])
        return v
    def equal(lits, bound):
        cnf.extend(CardEnc.equals(lits, bound=bound, vpool=pool, encoding=EncType.seqcounter).clauses)
    def atmost(lits, bound):
        cnf.extend(CardEnc.atmost(lits, bound=bound, vpool=pool, encoding=EncType.seqcounter).clauses)
    for l in range(64):
        # d_Z(l) = 1 + d_H(l).
        equal([T(z, l) for z in range(8, 19)] + [-T(h, l) for h in range(8)], 9)
    for z in range(8, 19):
        equal([E(z, v) for v in range(19) if v != z] + [T(z, l) for l in range(64)], 14)
        for p in range(16):
            equal([E(z, h) for h in range(8) if p in sig[h]]
                  + [T(z, l) for l in range(64) if p in lsig[l]], 2)
    for i, j in combinations(range(19), 2):
        if j < 8:
            continue  # Already exact in the high/low model.
        terms = [E(i, j)]
        terms += [AND(E(i, k), E(j, k), ('core-common', i, j, k))
                  for k in range(19) if k not in (i, j)]
        terms += [AND(T(i, l), T(j, l), ('core-low-common', i, j, l)) for l in range(64)]
        equal(terms, 2)
    for i in range(19):
        for l in range(64):
            terms = [T(i, l)]
            terms += [AND(E(i, j), T(j, l), ('mixed-common', i, l, j))
                      for j in range(19) if j != i]
            cap = 2 - (len(sig[i] & lsig[l]) if i < 8 else 0)
            atmost(terms, cap)
    for l, m in combinations(range(64), 2):
        terms = [AND(T(i, l), T(i, m), ('low-common', l, m, i)) for i in range(19)]
        atmost(terms, 2 - len(lsig[l] & lsig[m]))
    return cnf, edge, high_low, zero_low


def verify(rows, orbit, old_edges, high_edges, zero_edges):
    adjacent = [set() for _ in range(99)]
    def put(i, j):
        assert i != j and j not in adjacent[i]
        adjacent[i].add(j); adjacent[j].add(i)
    for p in range(8):
        for n in range(8):
            if rows[p] >> n & 1: put(p, n + 8)
    for h, (pp, nn) in enumerate(orbit['high'], 16):
        for p in pp: put(h, p)
        for n in nn: put(h, n + 8)
    for l, (p, n) in enumerate(low_labels(orbit['single']), 35):
        put(l, p); put(l, n + 8)
    for i, j in old_edges: put(16 + i, 16 + j)
    for h, l in high_edges: put(16 + h, 35 + l)
    for z, l in zero_edges: put(16 + z, 35 + l)
    for i, j in combinations(range(99), 2):
        total = len(adjacent[i] & adjacent[j]) + int(j in adjacent[i])
        assert total <= 2, (i, j, total)
        if j < 35: assert total == 2, (i, j, total)
    for i in range(35): assert len(adjacent[i]) == 14, (i, len(adjacent[i]))
    return [sum(1 << j for j in n) for n in adjacent]


def solve(rows, orbit, seconds=30):
    obstruction = four_high_obstruction(orbit['high'])
    if obstruction: return {'status': 'counting_obstruction', 'certificate': obstruction}
    cnf, edge, high, zero = build(rows, orbit)
    start = time.monotonic()
    with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
        timer = Timer(seconds, solver.interrupt); timer.start()
        try: status = solver.solve_limited(expect_interrupt=True)
        finally: timer.cancel()
        result = {'status': 'sat' if status is True else 'unsat' if status is False else 'unknown',
                  'seconds': round(time.monotonic() - start, 4),
                  'variables': cnf.nv, 'clauses': len(cnf.clauses)}
        if status:
            true = {v for v in solver.get_model() if v > 0}
            oe = [[i, j] for (i, j), v in edge.items() if v in true]
            he = [[i, l] for (i, l), v in high.items() if v in true]
            ze = [[i, l] for (i, l), v in zero.items() if v in true]
            verify(rows, orbit, oe, he, ze)
            result.update(edges=oe, high_low_edges=he, zero_low_edges=ze)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', type=Path); p.add_argument('--output', type=Path)
    p.add_argument('--core', type=int, required=True); p.add_argument('--orbit', type=int, required=True)
    p.add_argument('--seconds', type=float, default=30)
    a = p.parse_args(); block = next(d for d in json.loads(a.input.read_text()) if d['core'] == a.core)
    result = solve(block['rows'], block['orbits'][a.orbit], a.seconds)
    result.update(core=a.core, orbit=a.orbit)
    print({k: v for k, v in result.items() if not k.endswith('edges')}, flush=True)
    if a.output: a.output.write_text(json.dumps(result, indent=2) + '\n')


if __name__ == '__main__': main()
