"""Full incidence search with interchangeable low-signature rows ordered.

For core zero, the proved doubled-C8 restriction also makes H independent.
This wrapper leaves the frozen incidence builder unchanged.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
from itertools import combinations
import json
from pathlib import Path
from threading import Timer
import time

from pysat.formula import IDPool
from pysat.solvers import Solver
from coupled_shells_incidence import build, verify
from coupled_shells_low import low_labels
from coupled_zero_structure import add_lex
from coupled_zero_completion import matrices


def model(block, orbit_index):
    orbit = block['orbits'][orbit_index]
    cnf, edge, high, zero = build(block['rows'], orbit)
    pool = IDPool(start_from=cnf.nv+1)
    groups = defaultdict(list)
    for l, label in enumerate(low_labels(orbit['single'])):
        groups[tuple(label)].append(l)
    for label, group in groups.items():
        for l, m in zip(group, group[1:]):
            # add_lex compares in reverse order: H bits take precedence.
            left = [zero[z, l] for z in range(8, 19)]+[high[h, l] for h in range(8)]
            right = [zero[z, m] for z in range(8, 19)]+[high[h, m] for h in range(8)]
            add_lex(cnf, pool, left, right, ('low-column', label, l, m))
    if block['core'] == 0:
        cnf.extend([[-edge[i, j]] for i, j in combinations(range(8), 2)])
    return cnf, edge, high, zero


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--orbits', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-orbits.json'))
    p.add_argument('--core', type=int, default=0); p.add_argument('--orbit', type=int, default=1)
    p.add_argument('--seconds', type=float, default=60); p.add_argument('--output', type=Path)
    a = p.parse_args()
    block = next(b for b in json.loads(a.orbits.read_text()) if b['core'] == a.core)
    orbit = block['orbits'][a.orbit]
    begin = time.monotonic(); cnf, edge, high, zero = model(block, a.orbit)
    result = {'core': a.core, 'orbit': a.orbit, 'variables': cnf.nv,
              'clauses': len(cnf.clauses), 'build_seconds': time.monotonic()-begin}
    begin = time.monotonic()
    with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
        timer = Timer(a.seconds, solver.interrupt); timer.start()
        try:
            status = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
        result.update(status='sat' if status is True else 'unsat' if status is False else 'unknown',
                      seconds=time.monotonic()-begin)
        if status:
            truth = {v for v in solver.get_model() if v > 0}
            oe = [[i, j] for (i, j), v in edge.items() if v in truth]
            he = [[i, l] for (i, l), v in high.items() if v in truth]
            ze = [[i, l] for (i, l), v in zero.items() if v in truth]
            verify(block['rows'], orbit, oe, he, ze)
            B, N = matrices(block, orbit, {'edges': oe, 'low_edges': he})
            for z, l in ze:
                N[z+16, l] = 1
            result.update(edges=oe, high_low_edges=he, zero_low_edges=ze,
                          B=B.tolist(), N=N.tolist())
    if a.output:
        a.output.write_text(json.dumps(result, indent=2)+'\n')
    print({k: v for k, v in result.items() if k not in
           ('edges', 'high_low_edges', 'zero_low_edges', 'B', 'N')}, flush=True)


if __name__ == '__main__':
    main()
