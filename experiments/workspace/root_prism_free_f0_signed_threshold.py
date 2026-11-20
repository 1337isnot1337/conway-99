"""Encode an unconditional signed selector inequality with the frozen DAG.

For sum(c_i*z_i)<=0, negative coefficients use z_i and positive
coefficients use not z_i in a positive-weight threshold. Literal
substitution in the already checked DAG is exact. One fresh guard is
forced true; no original primary selector is fixed.
"""

import argparse
import hashlib
from itertools import product
import json
from pathlib import Path

import root_prism_free_f0_weighted_threshold as unsigned


UNSIGNED_SHA = 'a0c4b38d7787c8e6565ab122e0fdf41655ea40a9f0f218c0f860cd59d3f05144'


def signed_atmost_zero(terms, top, maximum_states=250000):
    assert hashlib.sha256(Path(unsigned.__file__).read_bytes()).hexdigest() == UNSIGNED_SHA
    assert type(top) is int and top >= 0
    assert all(type(v) is int and 0 < v <= top and type(c) is int and c != 0 for v, c in terms)
    assert len({v for v, _ in terms}) == len(terms)
    ordered = sorted(terms)
    demand = sum(c for _, c in ordered if c > 0)
    if demand == 0:
        return [], top, {'signed_terms': [[v, c] for v, c in ordered], 'tautology': True,
                         'initial_top': top, 'final_top': top, 'auxiliary_variables': 0,
                         'clauses': 0, 'literal_occurrences': 0}
    guard = top+1
    weights = [(v, abs(c)) for v, c in ordered]
    signs = {v: -1 if c > 0 else 1 for v, c in ordered}
    clauses, final_top, metadata = unsigned.guarded_threshold(guard, weights, demand, guard, maximum_states)
    mapped = [[literal*signs.get(abs(literal), 1) for literal in clause] for clause in clauses]
    result = [[guard]]+mapped
    assert all(abs(literal) <= final_top for clause in result for literal in clause)
    return result, final_top, {
        'signed_terms': [[v, c] for v, c in ordered], 'tautology': False,
        'positive_weighted_literals': [[v if c < 0 else -v, abs(c)] for v, c in ordered],
        'positive_literal_threshold': demand, 'fresh_true_guard': guard,
        'initial_top': top, 'final_top': final_top, 'auxiliary_variables': final_top-top,
        'clauses': len(result), 'literal_occurrences': sum(map(len, result)),
        'underlying_unsigned_DAG': metadata,
        'primary_assignment_restriction': 'original signed sum is at most zero',
        'no_original_selector_fixed': True}


def controls():
    from pysat.solvers import Solver
    formulas = assignments = 0
    samples = [()]
    for n in range(1, 5):
        samples.extend(product((-2, -1, 0, 1, 2), repeat=n))
    samples.extend([(7, -13, 4, -2), (100, -3, -2), (-6, 9, -12), (2, 1, 1, 1, 3, -8)])
    for coefficients in samples:
        n = len(coefficients)
        terms = [(i+1, c) for i, c in enumerate(coefficients) if c]
        clauses, top, metadata = signed_atmost_zero(terms, n+3)
        assert top == metadata['final_top']
        with Solver(name='minisat22', bootstrap_with=clauses) as solver:
            for values in product((0, 1), repeat=n):
                assumptions = [i+1 if value else -(i+1) for i, value in enumerate(values)]
                expected = sum(c*x for c, x in zip(coefficients, values)) <= 0
                assert solver.solve(assumptions=assumptions) == expected
                assignments += 1
        formulas += 1
    try:
        signed_atmost_zero([(1, 1), (2, 1), (3, -1), (4, -1)], 4, maximum_states=1)
    except RuntimeError:
        pass
    else:
        raise AssertionError('state guard did not refuse the formula')
    return {'status': 'signed literal substitution into the frozen threshold DAG controls PASS',
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'unsigned_encoder_sha256': UNSIGNED_SHA, 'formulas': formulas,
        'complete_primary_assignments': assignments, 'both_signs_and_zero_coefficients_checked': True,
        'fresh_true_guard_and_no_primary_fixing_checked': True,
        'resource_refusal_checked': True, 'tiny_boolean_solver_only': True,
        'incidence_or_LP_query_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = controls()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
