"""Joint high/zero model with the 64 low-to-high incidences.

This remains a necessary completion model: low-to-zero and low-to-low edges
are not chosen.  All represented adjacency bits and partial codegrees are
checked directly on every SAT witness.
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
from coupled_shells_zero import build_model, verify_witness


def low_labels(residual):
    return [(p, n) for p in range(8) for n in range(8) for _ in range(residual[p][n])]


def extend_model(rows, orbit):
    cnf, edge, high_domains, z_domains, core_common = build_model(rows, orbit['high'], orbit['single'])
    pool = IDPool(start_from=cnf.nv + 1)
    labels = low_labels(orbit['single'])
    assert len(labels) == 64
    sig = [set(p) | {n + 8 for n in ns} for p, ns in orbit['high']]
    lsig = [{p, n + 8} for p, n in labels]
    low = {(h, l): pool.id(('low', h, l)) for h in range(8) for l in range(64)}
    def E(i, j):
        return edge[tuple(sorted((i, j)))]
    def AND(a, b, key):
        v = pool.id(key)
        cnf.extend([[-v, a], [-v, b], [v, -a, -b]])
        return v
    def equal(lits, bound):
        cnf.extend(CardEnc.equals(lits, bound=bound, vpool=pool, encoding=EncType.seqcounter).clauses)
    def atmost(lits, bound):
        cnf.extend(CardEnc.atmost(lits, bound=bound, vpool=pool, encoding=EncType.seqcounter).clauses)
    atmost([E(i, j) for i, j in combinations(range(8), 2)], 1)
    A = [[0] * 16 for _ in range(16)]
    for p in range(8):
        for n in range(8):
            A[p][n + 8] = A[n + 8][p] = rows[p] >> n & 1
    for l in range(64):
        for p in range(16):
            cap = 2 - int(p in lsig[l]) - sum(A[p][q] for q in lsig[l])
            atmost([low[h, l] for h in range(8) if p in sig[h]], cap)
    for h in range(8):
        for p in range(16):
            rhs = 2 - int(p in sig[h]) - sum(A[p][q] for q in sig[h])
            lits = [E(h, k) for k in range(8) if k != h and p in sig[k]]
            lits += [low[h, l] for l in range(64) if p in lsig[l]]
            equal(lits, rhs)
        for l in range(64):
            overlap = len(sig[h] & lsig[l])
            if overlap >= 2:
                cnf.append([-low[h, l]])
            else:
                terms = [low[h, l]]
                terms += [AND(E(h, k), low[k, l], ('hl-common', h, l, k))
                          for k in range(8) if k != h]
                atmost(terms, 2 - overlap)
    for h, k in combinations(range(8), 2):
        terms = [E(h, k)]
        terms += [AND(E(h, v), E(k, v), ('hh-old-common', h, k, v))
                  for v in range(19) if v not in (h, k)]
        terms += [AND(low[h, l], low[k, l], ('hh-low-common', h, k, l)) for l in range(64)]
        equal(terms, 2 - core_common[h][k])
    for l, m in combinations(range(64), 2):
        cap = 2 - len(lsig[l] & lsig[m])
        terms = [AND(low[h, l], low[h, m], ('ll-common', l, m, h)) for h in range(8)]
        atmost(terms, cap)
    for l in range(64):
        for z in range(8, 19):
            terms = [AND(low[h, l], E(h, z), ('lz-common', l, z, h)) for h in range(8)]
            atmost(terms, 2)
    return cnf, edge, low, labels, high_domains, z_domains, core_common


def verify(rows, orbit, old_edges, low_edges, high_domains, z_domains, core_common):
    verify_witness(orbit['high'], orbit['single'], high_domains, z_domains, core_common, old_edges)
    labels = low_labels(orbit['single'])
    adjacent = [set() for _ in range(99)]
    def put(i, j):
        adjacent[i].add(j)
        adjacent[j].add(i)
    for p in range(8):
        for n in range(8):
            if rows[p] >> n & 1:
                put(p, n + 8)
    for h, (pp, nn) in enumerate(orbit['high'], 16):
        for p in pp: put(h, p)
        for n in nn: put(h, n + 8)
    for l, (p, n) in enumerate(labels, 35):
        put(l, p); put(l, n + 8)
    for i, j in old_edges: put(16 + i, 16 + j)
    for h, l in low_edges: put(16 + h, 35 + l)
    for i, j in combinations(range(99), 2):
        known = len(adjacent[i] & adjacent[j])
        assert known + int(j in adjacent[i]) <= 2, (i, j)
        if i < 24 and j < 24:
            assert known + int(j in adjacent[i]) == 2, (i, j, known)
    for i in range(24): assert len(adjacent[i]) == 14, i


def solve(rows, orbit, seconds=10):
    obstruction = four_high_obstruction(orbit['high'])
    if obstruction:
        return {'status': 'counting_obstruction', 'certificate': obstruction}
    cnf, edge, low, labels, hd, zd, cc = extend_model(rows, orbit)
    start = time.monotonic()
    with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
        timer = Timer(seconds, solver.interrupt); timer.start()
        try:
            status = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
        result = {'status': 'sat' if status is True else 'unsat' if status is False else 'unknown',
                  'seconds': round(time.monotonic() - start, 4), 'variables': cnf.nv,
                  'clauses': len(cnf.clauses)}
        if status:
            truth = {x for x in solver.get_model() if x > 0}
            oe = [[i, j] for (i, j), v in edge.items() if v in truth]
            le = [[h, l] for (h, l), v in low.items() if v in truth]
            verify(rows, orbit, oe, le, hd, zd, cc)
            result.update(edges=oe, low_edges=le)
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument('input', type=Path); p.add_argument('--output', type=Path)
    p.add_argument('--core', type=int, nargs='*'); p.add_argument('--limit', type=int)
    p.add_argument('--seconds', type=float, default=10)
    p.add_argument('--start', type=int, default=0)
    p.add_argument('--stop', type=int)
    a = p.parse_args(); data = json.loads(a.input.read_text()); result = []
    from collections import Counter
    for block in data:
        if a.core is not None and block['core'] not in a.core: continue
        counts = Counter()
        for i, orbit in enumerate(block['orbits'][:a.limit]):
            if i < a.start or (a.stop is not None and i >= a.stop): continue
            r = solve(block['rows'], orbit, a.seconds); r.update(core=block['core'], orbit=i)
            result.append(r); counts[r['status']] += 1
            print(f"core {block['core']} orbit {i}: {r['status']} {r.get('seconds', 0)}s", flush=True)
            if a.output: a.output.write_text(json.dumps(result, indent=2) + '\n')
        print(f"core {block['core']}: {dict(counts)}", flush=True)


if __name__ == '__main__': main()
