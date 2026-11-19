"""Independent integer audit of the frozen Gram-shift pilot.

Read data directly; do not import or execute the pilot or its ancestors.
Reconstruct the Gram rows and replay the explicit shifts. Verify every
coefficient, RHS, transport and clause bound. Only the already audited
pure carry primitive is reused for two standalone encoding-size replays.
No solver, optimizer, or ancestor incidence CNF is rebuilt.
"""

import argparse
import gzip
import hashlib
import json
from math import gcd
from pathlib import Path
import time

import root_prism_free_f0_carry_threshold as carry


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
SUBJECT = ROOT/'experiments/workspace/root_prism_free_f0_gram_shift_pilot.py'
SUBJECT_SHA = 'bfae134830c0fe3a6e8f2296bc26c35724046aedef71d677e48e9cecc9d7bb93'
RESULT = LOGS/'f0-gram-shift-pilot.json'
RESULT_SHA = '580442e8c3404a15685270fd139d565ae1924ac37edd8cad0d8975cfb23554ba'
CARRY_SHA = '942efb35d35429d88d7cc9c3bc14aa7a116972186f60abeebe50db89214ec75f'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def objective(values):
    return [sum(abs(c) for c in values), sum(abs(c).bit_count() for c in values), max(map(abs, values), default=0)]


def bound(values, rhs, record, selected, population):
    clause = record['clause']
    assert all(type(lit) is int and 1 <= abs(lit) <= 480 for lit in clause)
    assert len({abs(lit) for lit in clause}) == len(clause)
    fixed = {abs(lit)-1: int(lit < 0) for lit in clause}
    assert all((a in selected) == bool(value) for a, value in fixed.items())
    fixed_sum = sum(values[a]*value for a, value in fixed.items())
    if population is None:
        lower = fixed_sum+sum(min(0, values[a]) for a in range(480) if a not in fixed)
        helpful = sorted((abs(c) for a, c in enumerate(values) if c and ((a in selected) == (c > 0))), reverse=True)
        baseline = sum(min(0, c) for c in values)
        k = len(clause)
        assert all(values[a] and bool(value) == (values[a] > 0) for a, value in fixed.items())
        assert record['minimum_explanation_literal_count'] == k
        assert k == 0 or baseline+sum(helpful[:k-1]) <= rhs
        assert record['largest_k_minus_one_gains_bound'] == baseline+sum(helpful[:max(0, k-1)])
        assert record['independent_baseline'] == baseline and record['cardinality_premise'] is None
    else:
        assert population == 60 and record['cardinality_premise'] == 60
        assert record['full_universe'] == list(range(1, 481)) and record['initial_selected_variables'] == 60
        assert all(lit < 0 for lit in clause)
        free = sorted(values[a] for a in range(480) if a not in fixed)
        slots = 60-sum(fixed.values())
        assert 0 <= slots <= len(free)
        lower = fixed_sum+sum(free[:slots])
        for a in fixed:
            weaker = {b: value for b, value in fixed.items() if b != a}
            slots = 60-sum(weaker.values())
            reduced = sum(values[b]*value for b, value in weaker.items())
            reduced += sum(sorted(values[b] for b in range(480) if b not in weaker)[:slots])
            assert reduced <= rhs
        assert record['inclusion_minimal_in_selected_variables'] and not record['minimum_cardinality_claimed']
    assert lower == record['minimum_if_clause_is_false'] > rhs
    assert lower-rhs == record['strict_integer_margin']
    assert record['violating_assignment_value'] == sum(values[a] for a in selected) == rhs+26
    return {'literal_count': len(clause), 'minimum_when_false': lower,
            'rhs': rhs, 'strict_margin': lower-rhs, 'population': population}


def encoding(values, rhs, expected):
    terms = [(-(a+1) if c > 0 else a+1, abs(c)) for a, c in enumerate(values) if c]
    demand = sum(c for c in values if c > 0)-rhs
    assert demand > 0
    # Check the literal substitution as a symbolic affine identity.
    constant = sum(weight for lit, weight in terms if lit < 0)
    linear = [0]*480
    for lit, weight in terms:
        linear[abs(lit)-1] += weight if lit > 0 else -weight
    assert linear == [-c for c in values] and constant-demand == rhs
    clauses, top, metadata = carry.literal_threshold(terms, demand, 480)
    actual = {key: metadata[key] for key in expected}
    assert actual == expected
    assert len(clauses) == expected['clauses']
    assert sum(map(len, clauses)) == expected['literal_occurrences']
    assert top-480 == expected['auxiliary_variables']
    assert all(1 <= abs(lit) <= top for clause in clauses for lit in clause)
    divisor = gcd(*(weight for _, weight in terms))
    assert divisor == expected['weight_gcd']
    return {'symbolic_literal_substitution_checked': True, 'standalone_initial_top': 480,
            'full_pure_carry_encoding_metadata_replayed': actual,
            'no_original_model_CNF_appended_or_rebuilt': True}


def audit():
    assert digest(SUBJECT) == SUBJECT_SHA and digest(RESULT) == RESULT_SHA
    assert digest(Path(carry.__file__)) == CARRY_SHA
    result = read(RESULT)
    assert result['source_sha256'] == SUBJECT_SHA and result['carry_source_sha256'] == CARRY_SHA
    for name, expected in result['frozen_inputs'].items():
        assert digest(LOGS/name) == expected
    domain = read(LOGS/'f0-exterior-row-domains02.json.gz')
    model = read(LOGS/'f0-incidence-case00-model.json')
    repair = read(LOGS/'f0-carry-row-loop-run01-shared-ray-repair.json.gz')
    core, triples = domain['component_core_rows'], domain['signature_domain']
    assert len(core) == 21 and len(triples) == 480
    assert all(len(h) == len(set(h)) == 3 and h == sorted(h) and all(0 <= i < 18 for i in h) for h in triples)
    masks = [sum(1 << i for i in h) for h in triples]
    lift = repair['universal_selector_lift']
    selected = set(lift['selected_signature_ids_for_allocation_only'])
    assert len(selected) == 60
    gram = [[12*int(i == j)+2-(core[i+3] & core[j+3]).bit_count()
             -int(core[i+3] >> (j+3) & 1) for j in range(18)] for i in range(18)]
    assert [gram[i][i] for i in range(18)] == [10]*18
    assert [[sum(bool(masks[a] >> i & 1) and bool(masks[a] >> j & 1) for a in selected)
             for j in range(18)] for i in range(18)] == gram
    coverage = model['formula']['Gram_position_coverage']
    assert [(i, j) for i, j, *_ in coverage] == [(i, j) for i in range(18) for j in range(i, 18)]
    equations, seen = [], set()
    for i, j, quota, count, _ in coverage:
        members = [a for a, mask in enumerate(masks) if mask >> i & 1 and mask >> j & 1]
        assert quota == gram[i][j] and len(members) == count
        assert sum(a in selected for a in members) == quota
        if not members:
            assert quota == 0
            continue
        key = tuple(members), quota
        if key not in seen:
            seen.add(key)
            equations.append((i, j, quota, members))
    assert len(equations) == result['distinct_nonempty_Gram_equalities'] == 150
    original = [0]*480
    for a, coefficient in lift['transported_cuts'][0]['signed_coefficients']:
        original[a] = coefficient
    assert sum(original[a] for a in selected) == 26
    current, rhs = list(original), 0
    multipliers = [0]*150
    previous_pass = -1
    for step in result['coordinate_changes']:
        assert previous_pass <= step['pass'] < result['maximum_passes']
        previous_pass = step['pass']
        index, change = step['equation'], step['step']
        assert type(change) is int and change != 0 and 0 <= index < 150
        assert objective(current) == step['before']
        i, j, quota, members = equations[index]
        values = sorted(current[a] for a in members)
        assert change in {-values[(len(values)-1)//2], -values[len(values)//2]}
        for a in members:
            current[a] += change
        rhs += change*quota
        multipliers[index] += change
        assert objective(current) == step['after'] < step['before']
    direct = [original[a]+sum(multiplier for (_, _, _, members), multiplier in zip(equations, multipliers)
                              if a in members) for a in range(480)]
    direct_rhs = sum(quota*multiplier for (_, _, quota, _), multiplier in zip(equations, multipliers))
    assert direct == current and direct_rhs == rhs
    assert sum(bool(value) for value in multipliers) == result['nonzero_Gram_multipliers'] == 148
    assert objective(original) == result['original_objective'] and objective(current) == result['shifted_objective']
    assert sum(current[a] for a in selected)-rhs == 26
    # Generate the group by closure of composed images, independently of
    # the pilot's stack order, and check each full core adjacency matrix.
    group = {tuple(range(21))}
    while True:
        enlarged = group | {tuple(g[image[i]] for i in range(21)) for image in group for g in domain['core_generators']}
        if enlarged == group:
            break
        group = enlarged
    assert len(group) == 12
    positions = {tuple(h): a for a, h in enumerate(triples)}
    transport_reports = []
    assert len(result['transported_explanations']) == len(lift['transported_cuts']) == 12
    for index, image in enumerate(sorted(group)):
        assert sorted(image) == list(range(21)) and set(image[:3]) == {0, 1, 2}
        assert all(bool(core[i] >> j & 1) == bool(core[image[i]] >> image[j] & 1)
                   for i in range(21) for j in range(21))
        move = [image[i+3]-3 for i in range(18)]
        action = [positions[tuple(sorted(move[i] for i in h))] for h in triples]
        assert sorted(action) == list(range(480))
        entry = result['transported_explanations'][index]
        assert entry['core_action_index'] == index and entry['rhs'] == rhs
        shifted = [0]*480
        for variable, coefficient in entry['signed_coefficients']:
            assert 1 <= variable <= 480 and coefficient != 0
            assert shifted[variable-1] == 0
            shifted[variable-1] = coefficient
        transported_original = [0]*480
        for a, coefficient in lift['transported_cuts'][index]['signed_coefficients']:
            transported_original[a] = coefficient
        assert all(transported_original[action[a]] == original[a] and shifted[action[a]] == current[a]
                   for a in range(480))
        row_certificate = []
        reconstructed = list(transported_original)
        reconstructed_rhs = 0
        for (i, j, quota, members), multiplier in zip(equations, multipliers):
            left, right = sorted((move[i], move[j]))
            assert gram[left][right] == quota
            moved_members = [a for a, mask in enumerate(masks) if mask >> left & 1 and mask >> right & 1]
            assert moved_members == sorted(action[a] for a in members)
            if multiplier:
                row_certificate.append([left, right, multiplier, quota])
                for a in moved_members:
                    reconstructed[a] += multiplier
                reconstructed_rhs += multiplier*quota
        assert row_certificate == entry['nonzero_Gram_equation_multipliers']
        assert reconstructed == shifted and reconstructed_rhs == rhs
        moved_selected = {action[a] for a in selected}
        assert entry['selected_primary_variables'] == sorted(a+1 for a in moved_selected)
        assert sum(shifted[a] for a in moved_selected)-rhs == 26
        transport_reports.append({'core_action_index': index, 'full480_coefficient_identity_checked': True,
            'Gram_shift_rows_checked': len(row_certificate), 'rhs': rhs, 'preserved_gap': 26,
            'independent_clause': bound(shifted, rhs, entry['independent_explanation'], moved_selected, None),
            'population_clause': bound(shifted, rhs, entry['population_explanation'], moved_selected, 60)})
    return {'status': 'PASS: independent exact Gram-shift, transport, clause-bound and standalone carry audit',
        'audit_source_sha256': digest(Path(__file__)), 'subject_source_sha256': SUBJECT_SHA,
        'subject_result_sha256': RESULT_SHA, 'frozen_input_hashes': result['frozen_inputs'],
        'carry_source_sha256': CARRY_SHA,
        'original_Gram_positions_checked': 171, 'selected_full_Gram_entries_checked': 324,
        'distinct_Gram_equalities': 150, 'recorded_integer_coordinate_changes_replayed': len(result['coordinate_changes']),
        'nonzero_integer_multipliers': 148, 'full_coefficient_identity_entries': 480,
        'rhs': rhs, 'selected_point_gap_preserved': 26,
        'original_objective': objective(original), 'shifted_objective': objective(current),
        'all12_transport_checks': transport_reports,
        'original_standalone_encoding': encoding(original, 0, result['original_encoding']),
        'shifted_standalone_encoding': encoding(current, rhs, result['shifted_encoding']),
        'equivalence_scope': 'Exactly equivalent on the existing full Gram equalities; the saved selected point is a diagnostic, not a hypothesis.',
        'subject_or_ancestor_generator_imported': False,
        'ancestor_incidence_CNF_rebuilt': False, 'existing_formula_changed': False,
        'solver_or_optimizer_called': False,
        'global_or_coordinatewise_heuristic_optimality_claimed_by_this_audit': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    report = audit()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
    print(json.dumps({'elapsed_seconds': time.monotonic()-started,
                      'output_sha256': digest(args.output)}), flush=True)
