"""Joint H/Z necessary completion model for norm-16 incidence templates.

Models all 19 vertices in H union Z.  The 64 L vertices enter through exact
row-domain bipartite matching tests, but are not globally completed.  A SAT
witness proves only feasibility of this necessary relaxation.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

from coupled_shells_filter import matching_possible, row_domains


def zero_domains(chosen, residual):
    sets = [(set(p), set(n)) for p, n in chosen]
    allowed = []
    for mask in range(256):
        if mask.bit_count() < 2:
            continue
        chosen_rows = [i for i in range(8) if mask >> i & 1]
        if any(len(sets[i][0] & sets[j][0]) + len(sets[i][1] & sets[j][1]) >= 2
               for i, j in combinations(chosen_rows, 2)):
            continue
        pdeg = [2 - sum(p in sets[i][0] for i in chosen_rows) for p in range(8)]
        ndeg = [2 - sum(n in sets[i][1] for i in chosen_rows) for n in range(8)]
        if matching_possible(residual, pdeg, ndeg):
            allowed.append(mask)
    return allowed


def build_model(rows, chosen, residual):
    high_domains, core_common = row_domains(rows, chosen, residual)
    z_domains = set(zero_domains(chosen, residual))
    pool = IDPool()
    edge = {(i, j): pool.id(('edge', i, j)) for i, j in combinations(range(19), 2)}
    cnf = CNF()
    def E(i, j):
        return edge[tuple(sorted((i, j)))]
    def forbid_pattern(variables, mask):
        cnf.append([-v if mask >> i & 1 else v for i, v in enumerate(variables)])
    for i in range(8):
        other = [j for j in range(8) if j != i]
        allowed = {sum(((mask >> j) & 1) << k for k, j in enumerate(other))
                   for mask in high_domains[i]}
        for mask in range(128):
            if mask not in allowed:
                forbid_pattern([E(i, j) for j in other], mask)
        # d_Z(i) = 4 + d_H(i), after complementing the seven H-edge bits.
        cnf.extend(CardEnc.equals([E(i, z) for z in range(8, 19)] + [-E(i, j) for j in other],
                                 bound=11, vpool=pool, encoding=EncType.seqcounter).clauses)
    for z in range(8, 19):
        for mask in range(256):
            if mask not in z_domains:
                forbid_pattern([E(h, z) for h in range(8)], mask)
        # d_H(z) = 2 + d_Z(z), after complementing ten Z-edge bits.
        cnf.extend(CardEnc.equals([E(h, z) for h in range(8)]
                                 + [-E(z, w) for w in range(8, 19) if w != z],
                                 bound=12, vpool=pool, encoding=EncType.seqcounter).clauses)
    for i, j in combinations(range(19), 2):
        terms = [E(i, j)]
        for k in range(19):
            if k in (i, j):
                continue
            common = pool.id(('common', i, j, k))
            a, b = E(i, k), E(j, k)
            cnf.extend([[-common, a], [-common, b], [common, -a, -b]])
            terms.append(common)
        cap = 2 - (core_common[i][j] if j < 8 else 0)
        cnf.extend(CardEnc.atmost(terms, bound=cap, vpool=pool,
                                 encoding=EncType.seqcounter).clauses)
    # Z vertices are interchangeable. Sort their eight-bit H-neighborhoods.
    for z in range(8, 18):
        prefix = None
        for h in range(7, -1, -1):
            a, b = E(h, z), E(h, z + 1)
            cnf.append(([-prefix] if prefix else []) + [-a, b])
            if h == 0:
                break
            same = pool.id(('prefix', z, h))
            if prefix:
                cnf.extend([[-same, prefix], [-same, -a, b], [-same, a, -b],
                            [-prefix, a, b, same], [-prefix, -a, -b, same]])
            else:
                cnf.extend([[-same, -a, b], [-same, a, -b], [same, a, b], [same, -a, -b]])
            prefix = same
    return cnf, edge, high_domains, z_domains, core_common


def verify_witness(chosen, residual, high_domains, z_domains, core_common, edges):
    adjacent = [set() for _ in range(19)]
    for i, j in edges:
        assert 0 <= i < j < 19
        assert j not in adjacent[i]
        adjacent[i].add(j)
        adjacent[j].add(i)
    for h in range(8):
        mask = sum(1 << k for k in adjacent[h] if k < 8)
        assert mask in high_domains[h]
        assert len(adjacent[h] & set(range(8, 19))) == 4 + mask.bit_count()
    for z in range(8, 19):
        mask = sum(1 << h for h in adjacent[z] if h < 8)
        assert mask in z_domains
        assert len(adjacent[z] & set(range(8, 19))) == mask.bit_count() - 2
    for i, j in combinations(range(19), 2):
        known = core_common[i][j] if j < 8 else 0
        assert known + len(adjacent[i] & adjacent[j]) + int(j in adjacent[i]) <= 2
    high_edges = sum(j < 8 for i, j in edges)
    zero_edges = sum(i >= 8 for i, j in edges)
    assert zero_edges == 5 + high_edges


def solve_template(rows, orbit, seconds=10, solver_name='glucose4', save_prefix=None):
    cnf, edge, high_domains, z_domains, core_common = build_model(rows, orbit['high'], orbit['single'])
    start = time.monotonic()
    with Solver(name=solver_name, bootstrap_with=cnf.clauses) as solver:
        timer = Timer(seconds, solver.interrupt)
        timer.start()
        try:
            status = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
        result = {'status': 'sat' if status is True else 'unsat' if status is False else 'unknown',
                  'seconds': round(time.monotonic() - start, 4),
                  'variables': cnf.nv, 'clauses': len(cnf.clauses),
                  'zero_domains': len(z_domains), 'solver': solver_name}
        if status is True:
            positive = {x for x in solver.get_model() if x > 0}
            selected = [[i, j] for (i, j), v in edge.items() if v in positive]
            verify_witness(orbit['high'], orbit['single'], high_domains, z_domains, core_common, selected)
            result['edges'] = selected
        if save_prefix:
            cnf.to_file(str(save_prefix) + '.cnf')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('input', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--solver', default='glucose4')
    parser.add_argument('--core', type=int, nargs='*')
    parser.add_argument('--limit', type=int)
    args = parser.parse_args()
    data = json.loads(args.input.read_text())
    results = []
    for core in data:
        if args.core is not None and core['core'] not in args.core:
            continue
        counts = Counter()
        for i, orbit in enumerate(core['orbits'][:args.limit]):
            result = solve_template(core['rows'], orbit, args.seconds, args.solver)
            result.update(core=core['core'], orbit=i)
            results.append(result)
            counts[result['status']] += 1
            print(f"core {core['core']} orbit {i}: {result['status']} {result['seconds']}s; "
                  f"{result['zero_domains']} zero masks", flush=True)
            if args.output:
                args.output.write_text(json.dumps(results, indent=2) + '\n')
        print(f"core {core['core']}: {dict(counts)}", flush=True)


if __name__ == '__main__':
    main()
