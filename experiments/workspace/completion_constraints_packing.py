"""Exact integer exterior-incidence packing for a fixed induced core.

This is a necessary-condition search, not a graph-completion assertion.
The incomplete-grid mode uses only integer filters on candidate signatures.
"""
from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path
from threading import Timer
import time

import numpy as np
from pysat.solvers import Solver

from broken_grid import canonical_cases, single_signatures


def signatures(B):
    """All signatures in the proved incomplete-grid reduction, without PSD filters."""
    n = len(B)
    result = []
    for S in single_signatures(B):
        row = B[list(S)].sum(axis=0)
        row[list(S)] += 1
        if np.max(row) <= 2:
            result.append(tuple(S))
    assert len(result) == len(set(result))
    return result


def packing(B, domains, k=14, v=99, seconds=30, solver_name='mc'):
    n = len(B)
    quota = (k - 2) * np.eye(n, dtype=int) + 2 - B - B @ B
    copies = []
    by_pair = defaultdict(list)
    by_triple = defaultdict(list)
    chains = []
    for index, S in enumerate(domains):
        if len(S) >= 3:
            limit = 1
        elif len(S) == 2:
            limit = int(quota[S[0], S[1]])
        elif len(S) == 1:
            limit = int(quota[S[0], S[0]])
        else:
            limit = v - n
        previous = None
        for _ in range(limit):
            copies.append(index)
            lit = len(copies)
            if previous is not None:
                chains.append([-lit, previous])
            previous = lit
            for a, i in enumerate(S):
                for j in S[a:]:
                    by_pair[min(i, j), max(i, j)].append(lit)
            for triple in combinations(sorted(S), 3):
                by_triple[triple].append(lit)
    start = time.monotonic()
    if solver_name == 'cp-sat':
        return packing_cp(B, domains, copies, by_pair, by_triple, chains, quota, k, v, seconds)
    with Solver(name=solver_name) as solver:
        solver.append_formula(chains)

        def atmost(lits, bound):
            if bound < 0:
                solver.add_clause([])
            elif bound < len(lits):
                solver.add_atmost(lits, bound)

        def exactly(lits, target):
            atmost(lits, target)
            atmost([-x for x in lits], len(lits) - target)

        for i in range(n):
            for j in range(i, n):
                exactly(by_pair[i, j], int(quota[i, j]))
        exactly(list(range(1, len(copies) + 1)), v - n)
        for lits in by_triple.values():
            atmost(lits, 1)
        if n == 27 and k == 14:
            groups = defaultdict(list)
            for lit, index in enumerate(copies, 1):
                groups[sum(8 <= x < 14 for x in domains[index])].append(lit)
            assert max(groups) <= 2
            two = sum(int(quota[i, j]) for i, j in combinations(range(8, 14), 2))
            one = sum(int(quota[i, i]) for i in range(8, 14)) - 2 * two
            for count, target in ((2, two), (1, one), (0, v - n - one - two)):
                exactly(groups[count], target)
        timer = Timer(seconds, solver.interrupt)
        timer.start()
        try:
            result = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
        elapsed = time.monotonic() - start
        output = {
            'core_vertices': n, 'signatures': len(domains), 'variables': len(copies),
            'triple_constraints': len(by_triple), 'seconds': round(elapsed, 3),
            'status': 'unknown' if result is None else ('integer incidence feasible' if result else 'solver reported unsat'),
            'solver': solver_name, 'solver_statistics': solver.accum_stats(),
        }
        if result:
            on = {x for x in solver.get_model() if x > 0}
            count = Counter(copies[x - 1] for x in on if x <= len(copies))
            N = np.zeros((n, v - n), dtype=int)
            col = 0
            for i, multiplicity in count.items():
                for _ in range(multiplicity):
                    N[list(domains[i]), col] = 1
                    col += 1
            assert col == v - n
            assert np.array_equal(N @ N.T, quota)
            common = N.T @ N
            np.fill_diagonal(common, 0)
            assert np.max(common) <= 2
            output['witness'] = {str(i): int(x) for i, x in count.items()}
        return output


def packing_cp(B, domains, copies, by_pair, by_triple, chains, quota, k, v, seconds):
    from ortools.sat.python import cp_model
    n = len(B)
    model = cp_model.CpModel()
    xs = [model.new_bool_var('s' + str(i)) for i in range(len(copies))]
    for clause in chains:
        model.add_bool_or([xs[x - 1] if x > 0 else xs[-x - 1].Not() for x in clause])
    for i in range(n):
        for j in range(i, n):
            model.add(sum(xs[x - 1] for x in by_pair[i, j]) == int(quota[i, j]))
    model.add(sum(xs) == v - n)
    for lits in by_triple.values():
        model.add_at_most_one(xs[x - 1] for x in lits)
    if n == 27 and k == 14:
        groups = defaultdict(list)
        for lit, index in enumerate(copies):
            groups[sum(8 <= x < 14 for x in domains[index])].append(xs[lit])
        assert max(groups) <= 2
        two = sum(int(quota[i, j]) for i, j in combinations(range(8, 14), 2))
        one = sum(int(quota[i, i]) for i in range(8, 14)) - 2 * two
        for count, target in ((2, two), (1, one), (0, v - n - one - two)):
            model.add(sum(groups[count]) == target)
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_workers = 1
    start = time.monotonic()
    result = solver.solve(model)
    output = {
        'core_vertices': n, 'signatures': len(domains), 'variables': len(copies),
        'triple_constraints': len(by_triple), 'seconds': round(time.monotonic() - start, 3),
        'status': 'unknown', 'solver': 'cp-sat', 'solver_status': solver.status_name(result),
        'branches': solver.num_branches, 'conflicts': solver.num_conflicts,
    }
    if result == cp_model.INFEASIBLE:
        output['status'] = 'solver reported unsat'
    elif result in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        output['status'] = 'integer incidence feasible'
        count = Counter(copies[i] for i, x in enumerate(xs) if solver.value(x))
        N = np.zeros((n, v - n), dtype=int)
        col = 0
        for i, multiplicity in count.items():
            for _ in range(multiplicity):
                N[list(domains[i]), col] = 1
                col += 1
        assert col == v - n
        assert np.array_equal(N @ N.T, quota)
        common = N.T @ N
        np.fill_diagonal(common, 0)
        assert np.max(common) <= 2
        output['witness'] = {str(i): int(x) for i, x in count.items()}
    return output


def control():
    from triangle_ball import golay
    G = golay()[0].astype(int)
    U = [0, 1, 3, 9, 27, 81]
    R = sorted(set(range(len(G))) - set(U))
    B = G[np.ix_(U, U)]
    domains = sorted({tuple(int(i) for i in np.flatnonzero(G[x, U])) for x in R})
    result = packing(B, domains, 22, 243, 10)
    assert result['status'] == 'integer incidence feasible'
    result.pop('witness')
    print(json.dumps({'positive_control': 'Golay', **result}), flush=True)


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--control', action='store_true')
    p.add_argument('--case', type=int)
    p.add_argument('--seconds', type=float, default=30)
    p.add_argument('--solver', choices=['mc', 'cp-sat'], default='mc')
    p.add_argument('--out', type=Path)
    args = p.parse_args()
    if args.control:
        control()
    else:
        output = []
        for case, (edge, counts, B) in enumerate(canonical_cases()):
            if args.case is not None and case != args.case:
                continue
            S = signatures(B)
            print(json.dumps({'case': case, 'candidate_signatures': len(S), 'size_counts': dict(Counter(map(len, S)))}), flush=True)
            result = packing(B, S, seconds=args.seconds, solver_name=args.solver)
            result['case'] = case
            output.append(result)
            print(json.dumps({k: v for k, v in result.items() if k != 'witness'}), flush=True)
        if args.out:
            args.out.write_text(json.dumps(output, indent=2) + '\n')
