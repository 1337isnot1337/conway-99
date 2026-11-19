"""Exact scalar-theta witnesses after forbidding norm-14 and norm-16 shells.

These are solutions of the existing finite coefficient relaxation, not lattice
or graph constructions.  Verification substitutes rational coefficients into
all inequalities without asking a solver.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import json
from pathlib import Path

from level_seven_exact import constraints, expr
import z3


def replay(record):
    rows = constraints(record['rank'], record['order'], {7: 0, 8: 0}, True)
    values = [Fraction(s) for s in record['coefficients']]
    assert len(values) == 15
    for name, (a, rhs) in rows.items():
        assert sum(x * y for x, y in zip(a, values)) >= rhs, (record['rank'], name)
    return len(rows)


def construct(rank, order, timeout_ms):
    rows = constraints(rank, order, {7: 0, 8: 0}, True)
    variables = z3.Reals(' '.join(f'coefficient{j}' for j in range(15)))
    solver = z3.SolverFor('QF_LRA')
    solver.set(timeout=timeout_ms)
    for a, rhs in rows.values():
        solver.add(expr(a, variables) >= z3.RealVal(str(rhs)))
    status = solver.check()
    if status != z3.sat:
        raise RuntimeError(f'rank {rank}: {status}; no witness produced')
    model = solver.model()
    record = {'rank': rank, 'order': order, 'limits': {'7': 0, '8': 0},
              'sparse': True,
              'coefficients': [str(model.eval(v, model_completion=True).as_fraction())
                               for v in variables]}
    replay(record)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--order', type=int, default=18)
    parser.add_argument('--timeout-ms', type=int, default=30000)
    args = parser.parse_args()
    if args.verify:
        data = json.loads(args.verify.read_text())
    else:
        data = []
        for rank in range(34, 43, 2):
            data.append(construct(rank, args.order, args.timeout_ms))
            print(f'rank {rank}: exact finite coefficient witness constructed', flush=True)
    for record in data:
        count = replay(record)
        print(f"rank {record['rank']}: {count} rational inequalities verified; norm14=norm16=0", flush=True)
    if args.output:
        args.output.write_text(json.dumps(data, indent=2) + '\n')


if __name__ == '__main__':
    main()
