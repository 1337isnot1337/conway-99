"""Exact clause consequences of Boolean integer inequalities.

The input inequality is sum(a_i*z_i) <= rhs. A clause is accepted only
when its falsifying partial assignment makes that inequality impossible.
An optional exact-cardinality premise is explicit. No solver is used.
"""

import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from pathlib import Path


def coefficients(terms):
    result = Counter()
    for variable, value in terms:
        assert type(variable) is int and variable > 0
        assert type(value) is int
        result[variable] += value
    return {i: value for i, value in sorted(result.items()) if value}


def lower_bound(terms, fixed, universe=None, cardinality=None):
    """Compute the exact independent or cardinality-constrained minimum."""
    a = coefficients(terms)
    assert all(type(i) is int and i > 0 and type(v) is bool
               for i, v in fixed.items())
    if cardinality is None:
        assert universe is None and set(fixed) <= set(a)
        value = sum(c * fixed[i] if i in fixed else min(0, c)
                    for i, c in a.items())
        return {'minimum': value, 'cardinality_infeasible': False}
    universe = tuple(universe)
    assert len(universe) == len(set(universe))
    assert all(type(i) is int and i > 0 for i in universe)
    assert set(a) | set(fixed) <= set(universe)
    assert type(cardinality) is int and 0 <= cardinality <= len(universe)
    residual = cardinality - sum(fixed.values())
    free = [i for i in universe if i not in fixed]
    if residual < 0 or residual > len(free):
        return {'minimum': None, 'cardinality_infeasible': True,
                'residual_cardinality': residual, 'free_variables': len(free)}
    ordered = sorted((a.get(i, 0), i) for i in free)
    value = sum(a.get(i, 0) * v for i, v in fixed.items())
    value += sum(c for c, _ in ordered[:residual])
    return {'minimum': value, 'cardinality_infeasible': False,
            'residual_cardinality': residual, 'free_variables': len(free)}


def verify_clause(terms, rhs, clause, universe=None, cardinality=None):
    """Check the implication from the literal falsifying assignment."""
    assert type(rhs) is int
    assert all(type(lit) is int and lit != 0 for lit in clause)
    assert len({abs(lit) for lit in clause}) == len(clause)
    fixed = {abs(lit): lit < 0 for lit in clause}
    result = lower_bound(terms, fixed, universe, cardinality)
    assert result['cardinality_infeasible'] or result['minimum'] > rhs
    return result


def independent_explanation(terms, rhs, assignment):
    """Minimum-cardinality explanation using independent Boolean bounds."""
    a = coefficients(terms)
    assert type(rhs) is int and set(a) <= set(assignment)
    assert all(type(assignment[i]) is bool for i in a)
    value = sum(c * assignment[i] for i, c in a.items())
    assert value > rhs
    baseline = sum(min(0, c) for c in a.values())
    helpful = sorted(((-abs(c), i) for i, c in a.items()
                      if assignment[i] == (c > 0)))
    fixed, minimum = {}, baseline
    for negative_weight, i in helpful:
        if minimum > rhs:
            break
        fixed[i] = assignment[i]
        minimum -= negative_weight
    assert minimum > rhs
    clause = [-i if fixed[i] else i for i in sorted(fixed)]
    checked = verify_clause(list(a.items()), rhs, clause)
    assert checked['minimum'] == minimum
    # The k-1 largest helpful gains cannot cross the strict threshold.
    k = len(clause)
    previous = baseline + sum(-w for w, _ in helpful[:max(0, k-1)])
    assert k == 0 or previous <= rhs
    return {'clause': clause, 'minimum_if_clause_is_false': minimum,
            'strict_integer_margin': minimum-rhs,
            'violating_assignment_value': value,
            'independent_baseline': baseline,
            'minimum_explanation_literal_count': k,
            'largest_k_minus_one_gains_bound': previous,
            'cardinality_premise': None}


def cardinality_explanation(terms, rhs, assignment, universe, cardinality):
    """Greedily shorten a clause on selected variables, using sum(z)=K."""
    a = coefficients(terms)
    universe = tuple(universe)
    assert set(assignment) == set(universe)
    assert all(type(v) is bool for v in assignment.values())
    assert sum(assignment.values()) == cardinality
    value = sum(c * assignment[i] for i, c in a.items())
    assert value > rhs
    fixed = {i: True for i in universe if assignment[i]}
    initial = lower_bound(list(a.items()), fixed, universe, cardinality)
    assert not initial['cardinality_infeasible'] and initial['minimum'] == value
    deletions = []
    for i in sorted(fixed, key=lambda j: (abs(a.get(j, 0)), j)):
        trial = {j: v for j, v in fixed.items() if j != i}
        bound = lower_bound(list(a.items()), trial, universe, cardinality)
        assert not bound['cardinality_infeasible']
        accepted = bound['minimum'] > rhs
        deletions.append({'variable': i, 'minimum_without_variable': bound['minimum'],
                          'removed': accepted})
        if accepted:
            fixed = trial
    clause = [-i for i in sorted(fixed)]
    checked = verify_clause(list(a.items()), rhs, clause, universe, cardinality)
    assert not checked['cardinality_infeasible']
    # Later removals only weaken a bound, so one deletion pass suffices.
    for i in fixed:
        weaker = {j: v for j, v in fixed.items() if j != i}
        assert lower_bound(list(a.items()), weaker, universe, cardinality)['minimum'] <= rhs
    return {'clause': clause,
            'minimum_if_clause_is_false': checked['minimum'],
            'strict_integer_margin': checked['minimum']-rhs,
            'violating_assignment_value': value,
            'cardinality_premise': cardinality,
            'full_universe': list(universe),
            'initial_selected_variables': sum(assignment.values()),
            'deletion_checks': deletions,
            'inclusion_minimal_in_selected_variables': True,
            'minimum_cardinality_claimed': False}


def controls():
    independent, constrained, semantic = 0, 0, 0
    universe = (1, 2, 3)
    points = [dict(zip(universe, values)) for values in product((False, True), repeat=3)]
    for values in product(range(-2, 3), repeat=3):
        terms = list(zip(universe, values))
        evaluated = [sum(c * point[i] for i, c in terms) for point in points]
        for rhs in range(-7, 8):
            for point, value in zip(points, evaluated):
                if value <= rhs:
                    continue
                plain = independent_explanation(terms, rhs, point)
                k = sum(point.values())
                card = cardinality_explanation(terms, rhs, point, universe, k)
                independent += 1
                constrained += 1
                for candidate, observed in zip(points, evaluated):
                    for record, applicable in ((plain, True), (card, sum(candidate.values()) == k)):
                        false_clause = all(candidate[abs(lit)] == (lit < 0) for lit in record['clause'])
                        if applicable and observed <= rhs:
                            assert not false_clause
                        semantic += 1
    huge = 1 << 200
    terms = [(1, huge), (1, 7), (2, -huge), (2, -9), (3, 0)]
    point = {1: True, 2: False, 3: False}
    a = coefficients(terms)
    assert a == {1: huge+7, 2: -huge-9}
    independent_explanation(terms, 0, point)
    cardinality_explanation(terms, 0, point, universe, 1)
    # Missing zero coefficients still contribute selectable free variables.
    bound = lower_bound([(1, 5)], {}, universe, 1)
    assert bound['minimum'] == 0
    rejected = 0
    for clause in ([1], [-2], [-1, 2]):
        try:
            verify_clause([(1, 1), (2, -1)], 0, clause)
        except AssertionError:
            rejected += 1
    assert rejected == 2
    return {'status': 'PASS: exact independent/cardinality clause controls',
            'independent_explanations': independent,
            'cardinality_explanations': constrained,
            'explicit_boolean_semantic_checks': semantic,
            'arbitrary_precision_and_repeated_coefficients_checked': True,
            'zero_coefficient_universe_control': True,
            'invalid_clauses_rejected': rejected,
            'optimizer_or_solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controls', action='store_true', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = controls()
    result['source_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
