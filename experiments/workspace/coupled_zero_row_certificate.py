"""Exact Farkas certificate for one fixed zero-to-low neighborhood row.

All low/core incidence is fixed by the referenced saved partial witness.
This rejects that point, not every point in the incidence class.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from scipy import sparse as sp

from coupled_zero_completion import matrices


def row_system(B, N, z):
    M = np.vstack((N[:24], np.ones((1, 64), dtype=int)))
    rhs = np.r_[2-B[:24, z]-(B@B)[:24, z], 14-B[z].sum()]
    return M, rhs


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--orbits', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-orbits.json'))
    p.add_argument('--points', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-low-all.json'))
    p.add_argument('--output', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-zero-row-certificate.json'))
    p.add_argument('--core', type=int, default=0)
    p.add_argument('--orbit', type=int, default=1)
    p.add_argument('--zero', type=int, default=0)
    p.add_argument('--verify', action='store_true')
    a = p.parse_args()
    blocks = {b['core']: b for b in json.loads(a.orbits.read_text())}
    points = {(r['core'], r['orbit']): r for r in json.loads(a.points.read_text())
              if r['status'] == 'sat'}
    record = (json.loads(a.output.read_text()) if a.verify else
              {'core': a.core, 'orbit': a.orbit, 'zero': a.zero})
    block = blocks[record['core']]
    B, N = matrices(block, block['orbits'][record['orbit']],
                    points[record['core'], record['orbit']])
    M, rhs = row_system(B, N, record['zero']+24)
    if not a.verify:
        from completion_constraints import exact_farkas
        ray = exact_farkas(sp.csc_matrix(M), rhs)
        assert ray is not None, 'No exact nonnegative-incidence certificate found'
        record.update(ray=ray, rhs=[int(x) for x in rhs])
        a.output.write_text(json.dumps(record, indent=2)+'\n')
    ray = record['ray']
    assert len(ray) == len(rhs) == 25
    assert record['rhs'] == [int(x) for x in rhs]
    columns = [sum(ray[i]*int(M[i, l]) for i in range(25)) for l in range(64)]
    value = sum(ray[i]*int(rhs[i]) for i in range(25))
    assert min(columns) >= 0 and value < 0
    print('PASS: row certificate for core', record['core'], 'orbit', record['orbit'],
          'zero vertex', record['zero'])
    print('Dual column minimum:', min(columns), '; right-hand side:', value)
    print('Thus a nonnegative neighborhood row would imply 0 <=', value)
    print('Scope: this fixed H/Z and H/L point only, not its incidence template.')


if __name__ == '__main__':
    main()
