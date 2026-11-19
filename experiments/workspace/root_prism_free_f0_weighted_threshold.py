"""Exact guarded positive-weight threshold CNF with no optional PB package.

The encoding uses only forward implications from a suffix predicate to
its branch selected by a primary Boolean. Its auxiliary variables are
existential: a valid weighted sum extends by the true suffix predicates,
and a forced root predicate follows the actual branches to a true leaf.
"""

import argparse
import hashlib
from itertools import product
import json
from math import gcd
from pathlib import Path


def normalize(terms, demand):
    assert type(demand) is int and demand > 0
    assert all(type(v) is int and v > 0 and type(w) is int and w > 0 for v, w in terms)
    assert len({v for v, _ in terms}) == len(terms)
    capped = [(v, min(w, demand)) for v, w in terms]
    divisor = gcd(*(w for _, w in capped)) if capped else 1
    normalized = sorted(((v, w // divisor) for v, w in capped), key=lambda row: (-row[1], row[0]))
    return normalized, (demand + divisor - 1) // divisor, divisor


def same(a, b):
    # A positive primary variable numbered1 must not compare equal to True.
    return type(a) is type(b) and a == b


def guarded_threshold(target, terms, demand, top, maximum_states=250000):
    """Return clauses, new maximum ID, and deterministic encoding metadata.

    ``terms`` contains distinct positive variable IDs and positive weights.
    Every supplied ID, including target, is at most ``top``. A resource
    bound raises before any returned formula can be used; it is not an
    additional mathematical constraint.
    """
    assert type(target) is int and target > 0 and type(top) is int and top >= target
    assert all(v <= top and v != target for v, _ in terms)
    assert type(maximum_states) is int and maximum_states > 0
    weighted, threshold, divisor = normalize(terms, demand)
    original_top = top
    suffix = [0] * (len(weighted) + 1)
    for i in range(len(weighted) - 1, -1, -1):
        suffix[i] = suffix[i + 1] + weighted[i][1]
    clauses = []

    def append(values):
        if any(value is True for value in values):
            return
        clause = [value for value in values if value is not False]
        assert all(type(value) is int and value for value in clause)
        assert len(set(clause)) == len(clause)
        assert not any(-value in clause for value in clause)
        clauses.append(clause)

    cache = {}
    stack = [(0, threshold, False)]
    branch_states = 0
    while stack:
        i, remaining, ready = stack.pop()
        key = (i, remaining)
        if key in cache:
            continue
        if remaining <= 0:
            cache[key] = True
            continue
        if remaining > suffix[i]:
            cache[key] = False
            continue
        assert i < len(weighted)
        variable, weight = weighted[i]
        low, high = (i + 1, remaining), (i + 1, remaining - weight)
        if not ready:
            stack.append((i, remaining, True))
            if high not in cache:
                stack.append((*high, False))
            if low not in cache:
                stack.append((*low, False))
            continue
        lo, hi = cache[low], cache[high]
        branch_states += 1
        if branch_states > maximum_states:
            raise RuntimeError('weighted threshold state budget exceeded; no formula returned')
        if same(lo, hi):
            node = lo
        elif lo is False and hi is True:
            node = variable
        else:
            top += 1
            node = top
            # If node is forced, choose the true branch of this primary bit.
            append([-node, variable, lo])
            append([-node, -variable, hi])
        cache[key] = node
    root = cache[(0, threshold)]
    append([-target, root])
    assert all(abs(value) <= top for clause in clauses for value in clause)
    metadata = {
        'target': target, 'original_demand': demand, 'original_positive_terms': len(terms),
        'capped_weight_gcd': divisor, 'normalized_demand': threshold,
        'normalized_terms': [[v, w] for v, w in weighted],
        'initial_top': original_top, 'final_top': top,
        'auxiliary_variables': top - original_top, 'branch_states': branch_states,
        'clauses': len(clauses), 'literal_occurrences': sum(map(len, clauses)),
        'root_predicate': root, 'forward_only_branch_encoding': True,
        'primary_assignment_restriction': 'target implies original weighted sum at least original demand'}
    return clauses, top, metadata


def controls():
    # These tiny solvers verify only the generic encoding. They do not query
    # any Conway incidence formula or row domain.
    from pysat.solvers import Solver
    cases = assignments = maximum_aux = 0
    weight_cases = [()]
    for size in range(1, 5):
        weight_cases.extend(product(range(1, 4), repeat=size))
    weight_cases.extend([(1, 1, 1, 1, 1), (7, 2, 13, 4, 9), (100, 3, 2), (6, 9, 12)])
    for weights in weight_cases:
        n = len(weights)
        for demand in range(1, sum(weights) + 2):
            terms = [(i + 1, w) for i, w in enumerate(weights)]
            target, old_top = n + 1, n + 4
            clauses, top, record = guarded_threshold(target, terms, demand, old_top)
            maximum_aux = max(maximum_aux, top - old_top)
            assert record['auxiliary_variables'] == top - old_top
            assert all(abs(v) <= n + 1 or old_top < abs(v) <= top for c in clauses for v in c)
            with Solver(name='minisat22', bootstrap_with=clauses) as solver:
                for values in product((0, 1), repeat=n):
                    primary = [i + 1 if value else -(i + 1) for i, value in enumerate(values)]
                    expected_threshold = sum(w * value for w, value in zip(weights, values)) >= demand
                    normalized, new_demand, _ = normalize(terms, demand)
                    assert (sum(w * values[v - 1] for v, w in normalized) >= new_demand) == expected_threshold
                    for target_value in (0, 1):
                        answer = solver.solve(assumptions=primary + [target if target_value else -target])
                        assert answer == (not target_value or expected_threshold)
                        assignments += 1
            cases += 1
    # State exhaustion must refuse to return a formula, never add a unit.
    try:
        guarded_threshold(5, [(1, 1), (2, 1), (3, 1), (4, 1)], 2, 5, maximum_states=1)
    except RuntimeError:
        pass
    else:
        raise AssertionError('resource guard did not fail')
    return {'status': 'exact guarded weighted-threshold existential controls PASS',
        'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'weight_vectors': len(weight_cases), 'threshold_formulas': cases,
        'complete_primary_and_guard_assignments': assignments,
        'largest_auxiliary_count_in_controls': maximum_aux,
        'capping_and_gcd_threshold_equivalence_checked': True,
        'forward_only_auxiliary_existential_equivalence_checked': True,
        'resource_guard_refuses_formula': True,
        'tiny_boolean_solvers_only': True, 'incidence_query_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = controls()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)
