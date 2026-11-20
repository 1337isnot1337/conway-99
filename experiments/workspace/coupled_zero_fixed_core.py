"""Free all low incidences while holding a saved 35-vertex core fixed.

This imports the frozen incidence builder without changing it.  UNSAT
rejects the supplied core but does not reject its full incidence class.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from threading import Timer
import time

from pysat.solvers import Solver

from coupled_shells_incidence import build, verify
from coupled_zero_completion import matrices


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--orbits', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-orbits.json'))
    p.add_argument('--points', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-low-all.json'))
    p.add_argument('--output', type=Path)
    p.add_argument('--core', type=int, default=0)
    p.add_argument('--orbit', type=int, default=1)
    p.add_argument('--seconds', type=float, default=45)
    a = p.parse_args()
    block = next(b for b in json.loads(a.orbits.read_text()) if b['core'] == a.core)
    orbit = block['orbits'][a.orbit]
    point = next(r for r in json.loads(a.points.read_text())
                 if r['core'] == a.core and r['orbit'] == a.orbit)
    assert point['status'] == 'sat'
    begin = time.monotonic(); cnf, edge, high, zero = build(block['rows'], orbit)
    present = {tuple(e) for e in point['edges']}
    cnf.extend([[v if e in present else -v] for e, v in edge.items()])
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
            result.update(edges=oe, high_low_edges=he, zero_low_edges=ze)
            B, N = matrices(block, orbit, dict(point, low_edges=he))
            for z, l in ze:
                N[z+16, l] = 1
            result.update(B=B.tolist(), N=N.tolist())
    if a.output:
        a.output.write_text(json.dumps(result, indent=2)+'\n')
    print({k: v for k, v in result.items() if k not in
           ('edges', 'high_low_edges', 'zero_low_edges', 'B', 'N')}, flush=True)


if __name__ == '__main__':
    main()
