"""Separate H/Z cores by exact Gram cuts and full low-incidence tests.

This is an exploratory search, not an exclusion certificate.  Exact Gram
vectors and UNSAT assumption cores are retained in its output.  A final
UNSAT result requires an independently checked proof before publication
as an incidence-template exclusion.
"""
from __future__ import annotations

import argparse
from itertools import product
import json
from pathlib import Path
from threading import Timer
import time

from pysat.formula import IDPool
from pysat.solvers import Solver

from coupled_shells_low import extend_model
from coupled_shells_incidence import build, verify
from coupled_zero_completion import matrices
from coupled_zero_gram import gram, negative_vector, linear_cut


def weighted_atmost(terms, bound, pool):
    """Encode a signed integer linear upper bound by binary half-adders."""
    positive = []
    for literal, weight in terms:
        if weight < 0:
            literal = -literal; weight = -weight; bound += weight
        if weight:
            positive.append((literal, weight))
    if bound < 0:
        return [[]]
    if bound >= sum(w for _, w in positive):
        return []
    columns = [[] for _ in range(1+sum(w for _, w in positive).bit_length())]
    for literal, weight in positive:
        for bit in range(weight.bit_length()):
            if weight >> bit & 1:
                columns[bit].append(literal)
    cnf = []
    bit = 0
    def xor(a, b, s):
        cnf.extend([[a, b, -s], [-a, -b, -s], [a, -b, s], [-a, b, s]])
    while bit < len(columns):
        while len(columns[bit]) > 1:
            if bit+1 == len(columns):
                columns.append([])
            a, b = columns[bit].pop(), columns[bit].pop()
            s, carry = pool.id(), pool.id()
            if columns[bit]:
                c = columns[bit].pop(); temporary = pool.id()
                xor(a, b, temporary); xor(temporary, c, s)
                cnf.extend([[-a, -b, carry], [-a, -c, carry], [-b, -c, carry],
                            [a, b, -carry], [a, c, -carry], [b, c, -carry]])
            else:
                xor(a, b, s)
                cnf.extend([[-carry, a], [-carry, b], [carry, -a, -b]])
            columns[bit].append(s); columns[bit+1].append(carry)
        bit += 1
    bits = [column[0] if column else None for column in columns]
    for bit, variable in enumerate(bits):
        if variable is None or (bound >> bit & 1):
            continue
        clause = [-variable]
        for j in range(bit+1, len(bits)):
            if bits[j] is None:
                if bound >> j & 1:
                    break  # A higher fixed zero is already below the bound.
            else:
                clause.append(-bits[j] if bound >> j & 1 else bits[j])
        else:
            cnf.append(clause)
    return cnf


def check_encoder():
    cases = [([2, -3, 5], 1), ([-2, -1, 3, 7], 2),
             ([1, 1, 1, 1, 1], 2), ([8, -8, 4, -4], -1)]
    for weights, bound in cases:
        n = len(weights); pool = IDPool(start_from=n+1)
        cnf = weighted_atmost(list(zip(range(1, n+1), weights)), bound, pool)
        with Solver(name='glucose4', bootstrap_with=cnf) as solver:
            for values in product((0, 1), repeat=n):
                assumptions = [i if values[i-1] else -i for i in range(1, n+1)]
                actual = solver.solve(assumptions=assumptions)
                assert actual == (sum(w*x for w, x in zip(weights, values)) <= bound)


def limited(solver, seconds, assumptions=None):
    solver.clear_interrupt(); timer = Timer(seconds, solver.interrupt); timer.start()
    try:
        return solver.solve_limited(assumptions=assumptions or [], expect_interrupt=True)
    finally:
        timer.cancel()


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--orbits', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-orbits.json'))
    p.add_argument('--core', type=int, default=0); p.add_argument('--orbit', type=int, default=1)
    p.add_argument('--seconds', type=float, default=60)
    p.add_argument('--inner-seconds', type=float, default=5)
    p.add_argument('--iterations', type=int, default=100)
    p.add_argument('--output', type=Path)
    p.add_argument('--check-encoder', action='store_true')
    a = p.parse_args()
    check_encoder()
    if a.check_encoder:
        print('PASS: weighted binary-adder inequalities on all assignments of four examples.')
        return
    block = next(b for b in json.loads(a.orbits.read_text()) if b['core'] == a.core)
    orbit = block['orbits'][a.orbit]
    outer_cnf, edge, *_ = extend_model(block['rows'], orbit)
    full_cnf, full_edge, high, zero = build(block['rows'], orbit)
    assert edge == full_edge
    pool = IDPool(start_from=outer_cnf.nv+1)
    history = []; start = time.monotonic()
    outcome = {'core': a.core, 'orbit': a.orbit, 'status': 'iteration_limit', 'history': history}
    with Solver(name='glucose4', bootstrap_with=outer_cnf.clauses) as outer, \
            Solver(name='glucose4', bootstrap_with=full_cnf.clauses) as inner:
        for iteration in range(a.iterations):
            remaining = a.seconds-(time.monotonic()-start)
            if remaining <= 0:
                outcome['status'] = 'time_limit'; break
            status = limited(outer, min(remaining, a.inner_seconds))
            if status is not True:
                outcome['status'] = 'solver_unsat' if status is False else 'outer_unknown'; break
            truth = {v for v in outer.get_model() if v > 0}
            oe = [[i, j] for (i, j), v in edge.items() if v in truth]
            B, _ = matrices(block, orbit, {'edges': oe, 'low_edges': []})
            vector = negative_vector(gram(B))
            if vector is not None:
                cut = linear_cut(B, vector)
                clauses = weighted_atmost([(edge[i, j], c) for i, j, c in cut['coefficients']],
                                           cut['upper_bound'], pool)
                outer.append_formula(clauses)
                record = {'iteration': iteration, 'type': 'exact_gram',
                          'edges': oe, 'vector': vector, 'new_clauses': len(clauses)}
            else:
                assumptions = [v if v in truth else -v for v in edge.values()]
                remaining = a.seconds-(time.monotonic()-start)
                if remaining <= 0:
                    outcome['status'] = 'time_limit'; break
                inner_status = limited(inner, min(remaining, a.inner_seconds), assumptions)
                if inner_status is False:
                    core = inner.get_core(); outer.add_clause([-v for v in core])
                    record = {'iteration': iteration, 'type': 'solver_assumption_core',
                              'core_literals': core, 'edges': oe}
                elif inner_status is None:
                    history.append({'iteration': iteration, 'type': 'inner_unknown', 'edges': oe})
                    outcome['status'] = 'inner_unknown'; break
                else:
                    truth = {v for v in inner.get_model() if v > 0}
                    he = [[i, l] for (i, l), v in high.items() if v in truth]
                    ze = [[i, l] for (i, l), v in zero.items() if v in truth]
                    verify(block['rows'], orbit, oe, he, ze)
                    B, N = matrices(block, orbit, {'edges': oe, 'low_edges': he})
                    for z, l in ze:
                        N[z+16, l] = 1
                    outcome.update(status='sat', edges=oe, high_low_edges=he,
                                   zero_low_edges=ze, B=B.tolist(), N=N.tolist())
                    break
            history.append(record)
            print(iteration, record['type'], len(record.get('core_literals', [])),
                  round(time.monotonic()-start, 3), flush=True)
            if a.output:
                a.output.write_text(json.dumps(outcome, indent=2)+'\n')
    outcome['seconds'] = time.monotonic()-start
    if a.output:
        a.output.write_text(json.dumps(outcome, indent=2)+'\n')
    print({k: v for k, v in outcome.items() if k not in
           ('history', 'edges', 'high_low_edges', 'zero_low_edges', 'B', 'N')}, flush=True)


if __name__ == '__main__':
    main()
