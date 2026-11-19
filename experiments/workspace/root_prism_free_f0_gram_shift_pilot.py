"""Exact Gram-equality shifts of one proved shared-row inequality.

Integer coordinate descent is a coefficient heuristic, not a solver.
Every proposed output is checked coefficientwise against the original
inequality plus an explicit integer sum of original Gram equalities.
No existing formula is changed.
"""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import root_prism_free_f0_clause_explanation_pilot as pilot
import integer_cut_clause_explanations as explanations
import root_prism_free_f0_carry_threshold as carry


ROOT, LOGS = pilot.ROOT, pilot.LOGS
PILOT_SHA = 'b6f701949f31a09892d8b2211e9fc64d1fb7d1fa9a2ed6775185542980c350c4'
CARRY_SHA = '942efb35d35429d88d7cc9c3bc14aa7a116972186f60abeebe50db89214ec75f'
PASSES = 20


def objective(values):
    return (sum(abs(v) for v in values),
            sum(abs(v).bit_count() for v in values),
            max(map(abs, values), default=0))


def encode_size(values, rhs):
    terms = [(-(i+1) if c > 0 else i+1, abs(c))
             for i, c in enumerate(values) if c]
    demand = sum(c for c in values if c > 0)-rhs
    clauses, _, metadata = carry.literal_threshold(terms, demand, 480)
    result = {key: metadata[key] for key in
              ('auxiliary_variables', 'clauses', 'literal_occurrences',
               'normalized_demand', 'normalized_weight_sum', 'weight_gcd',
               'gate_definition_sha256')}
    assert result['clauses'] == len(clauses)
    return result


def calculate():
    assert pilot.digest(Path(pilot.__file__)) == PILOT_SHA
    assert pilot.digest(Path(carry.__file__)) == CARRY_SHA
    pilot.calculate()
    domain = pilot.read(LOGS/'f0-exterior-row-domains02.json.gz')
    model = pilot.read(LOGS/'f0-incidence-case00-model.json')
    repair = pilot.read(LOGS/'f0-carry-row-loop-run01-shared-ray-repair.json.gz')
    lift = repair['universal_selector_lift']
    selected = set(lift['selected_signature_ids_for_allocation_only'])
    triples = domain['signature_domain']
    original = [0]*480
    for a, c in lift['transported_cuts'][0]['signed_coefficients']:
        original[a] = c
    assert sum(original[a] for a in selected) == 26
    equations, seen = [], set()
    for i, j, quota, count, _ in model['formula']['Gram_position_coverage']:
        members = [a for a, h in enumerate(triples) if i in h and j in h]
        assert len(members) == count
        assert sum(a in selected for a in members) == quota
        if not members:
            assert quota == 0
            continue
        key = tuple(members), quota
        if key not in seen:
            seen.add(key)
            equations.append({'position': [i, j], 'quota': quota, 'members': members})
    current, rhs = list(original), 0
    multipliers = [0]*len(equations)
    records = []
    for iteration in range(PASSES):
        changed = 0
        for index, row in enumerate(equations):
            values = sorted(current[a] for a in row['members'])
            steps = sorted({-values[(len(values)-1)//2], -values[len(values)//2]})
            best, best_step, best_values = objective(current), 0, current
            for step in steps:
                candidate = list(current)
                for a in row['members']:
                    candidate[a] += step
                score = objective(candidate)
                if score < best:
                    best, best_step, best_values = score, step, candidate
            if best_step:
                before = objective(current)
                current = best_values
                rhs += best_step*row['quota']
                multipliers[index] += best_step
                records.append({'pass': iteration, 'equation': index, 'step': best_step,
                                'before': list(before), 'after': list(best)})
                changed += 1
        if not changed:
            break
    rebuilt, rebuilt_rhs = list(original), 0
    for row, multiplier in zip(equations, multipliers):
        for a in row['members']:
            rebuilt[a] += multiplier
        rebuilt_rhs += row['quota']*multiplier
    assert (rebuilt, rebuilt_rhs) == (current, rhs)
    assert sum(current[a] for a in selected)-rhs == 26

    core = domain['component_core_rows']
    identity = tuple(range(21))
    group, queue = {identity}, [identity]
    while queue:
        old = queue.pop()
        for generator in domain['core_generators']:
            image = tuple(generator[old[i]] for i in range(21))
            if image not in group:
                group.add(image)
                queue.append(image)
    assert len(group) == 12 and sorted(group)[0] == identity
    position = {tuple(h): a for a, h in enumerate(triples)}
    universe = tuple(range(1, 481))
    transports = []
    for index, image in enumerate(sorted(group)):
        move = [image[i+3]-3 for i in range(18)]
        action = [position[tuple(sorted(move[i] for i in h))] for h in triples]
        assert sorted(action) == list(range(480))
        moved_original = dict(lift['transported_cuts'][index]['signed_coefficients'])
        assert all(moved_original[action[a]] == original[a] for a in range(480))
        coefficients = [moved_original.get(a, 0) for a in range(480)]
        moved_equations = []
        for row, multiplier in zip(equations, multipliers):
            i, j = sorted(move[v] for v in row['position'])
            members = [a for a, h in enumerate(triples) if i in h and j in h]
            assert members == sorted(action[a] for a in row['members'])
            if multiplier:
                moved_equations.append([i, j, multiplier, row['quota']])
                for a in members:
                    coefficients[a] += multiplier
        assert all(coefficients[action[a]] == current[a] for a in range(480))
        assert sum(multiplier*quota for _, _, multiplier, quota in moved_equations) == rhs
        chosen = {action[a]+1 for a in selected}
        assignment = {i: i in chosen for i in universe}
        terms = [(a+1, c) for a, c in enumerate(coefficients) if c]
        plain = explanations.independent_explanation(terms, rhs, assignment)
        card = explanations.cardinality_explanation(terms, rhs, assignment, universe, 60)
        transports.append({'core_action_index': index, 'signed_coefficients': terms,
            'rhs': rhs, 'nonzero_Gram_equation_multipliers': moved_equations,
            'selected_primary_variables': sorted(chosen),
            'independent_explanation': plain, 'population_explanation': card})
    return {'status': 'PASS: exact Gram-equality coefficient shift and all twelve transports',
            'source_sha256': pilot.digest(Path(__file__)), 'pilot_source_sha256': PILOT_SHA,
            'carry_source_sha256': CARRY_SHA, 'frozen_inputs': pilot.INPUTS,
            'maximum_passes': PASSES, 'last_pass_index': iteration,
            'coordinate_descent_stopped_at_a_fixed_point': changed == 0,
            'heuristic_objective': ['coefficient_L1_norm', 'coefficient_weight_bit_count', 'largest_absolute_coefficient'],
            'coordinate_changes': records, 'original_objective': list(objective(original)),
            'shifted_objective': list(objective(current)),
            'distinct_nonempty_Gram_equalities': len(equations),
            'nonzero_Gram_multipliers': sum(bool(v) for v in multipliers),
            'original_encoding': encode_size(original, 0),
            'shifted_encoding': encode_size(current, rhs),
            'transported_explanations': transports,
            'exact_violation_margin_preserved': 26,
            'point_is_not_a_hypothesis_of_the_shifted_inequality': True,
            'all_original_Gram_equalities_are_existing_model_premises': True,
            'existing_formula_changed': False, 'optimizer_or_solver_called': False,
            'component_excluded': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    result = calculate()
    if args.replay:
        assert pilot.canonical(result) == pilot.canonical(pilot.read(args.replay))
        result = {'status': 'PASS: cold exact Gram shifts and clause explanation replay',
                  'source_sha256': pilot.digest(Path(__file__)),
                  'certificate_sha256': pilot.digest(args.replay),
                  'optimizer_or_solver_called': False}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in
                     ('coordinate_changes', 'transported_explanations')}, indent=2))
    print('seconds', time.monotonic()-started)
    print('output_sha256', pilot.digest(args.output))
