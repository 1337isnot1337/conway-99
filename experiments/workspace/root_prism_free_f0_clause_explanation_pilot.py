"""Optimizer-free clause explanations of twelve proved shared-row cuts.

Every original inequality remains in the certificate. This preparation
measures weaker clause consequences; it changes no SAT formula or run.
The optional population premise is derived from the original Gram rows.
"""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

import integer_cut_clause_explanations as explain


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
INPUTS = {
    'f0-carry-row-loop-run01-shared-ray-repair.json.gz': '96e945d1211147e2ad13ed3468f51d72bd3ef87319ca33153eda6248e0b5c7c5',
    'f0-carry-row-loop-run01-shared-ray-repair-independent-audit.json': 'e67e932377d757928b12b0d4e4612afceff2141e92c827e919bd0f59ce4b5df1',
    'f0-exterior-row-domains02.json.gz': '665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4',
    'f0-incidence-case00-model.json': '16deda266149f5123a1db3833cfebf22d6bdfe4426b1424fcc51ccbfdc38f0a1',
}
EXPLAIN_SHA = 'f57d51b8be3fefd7a5d1035c52cc5758c719adb6a79d16a0909f1a54fdaa59f3'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def calculate():
    assert digest(Path(explain.__file__)) == EXPLAIN_SHA
    for name, sha in INPUTS.items():
        assert digest(LOGS/name) == sha
    repair = read(LOGS/'f0-carry-row-loop-run01-shared-ray-repair.json.gz')
    domain = read(LOGS/'f0-exterior-row-domains02.json.gz')
    model = read(LOGS/'f0-incidence-case00-model.json')
    assert repair['fixed_candidate_excluded'] and not repair['whole_component_excluded']
    lift = repair['universal_selector_lift']
    selected = lift['selected_signature_ids_for_allocation_only']
    assert selected == sorted(set(selected)) and len(selected) == 60
    core, triples = domain['component_core_rows'], domain['signature_domain']
    assert len(core) == 21 and len(triples) == 480
    assert all(len(h) == len(set(h)) == 3 and all(0 <= i < 18 for i in h) for h in triples)
    gram = [[12*int(i == j)+2-(core[i+3] & core[j+3]).bit_count()
             -((core[i+3] >> (j+3)) & 1) for j in range(18)] for i in range(18)]
    assert [gram[i][i] for i in range(18)] == [10]*18
    assert model['case'] == 0 and model['formula']['primary_variables'] == 480
    coverage = model['formula']['Gram_position_coverage']
    assert [(i, j) for i, j, *_ in coverage] == [(i, j) for i in range(18) for j in range(i, 18)]
    for i, j, quota, member_count, _ in coverage:
        assert quota == gram[i][j]
        assert member_count == sum(i in h and j in h for h in triples)
    assert [[sum(i in triples[a] and j in triples[a] for a in selected)
             for j in range(18)] for i in range(18)] == gram
    population = sum(gram[i][i] for i in range(18))//3
    assert population == 60

    identity = tuple(range(21))
    group, queue = {identity}, [identity]
    while queue:
        old = queue.pop()
        for generator in domain['core_generators']:
            image = tuple(generator[old[i]] for i in range(21))
            assert sorted(image) == list(range(21)) and set(image[:3]) == {0, 1, 2}
            assert all(((core[i] >> j) & 1) == ((core[image[i]] >> image[j]) & 1)
                       for i in range(21) for j in range(21))
            if image not in group:
                group.add(image)
                queue.append(image)
    assert len(group) == 12
    positions = {tuple(h): i for i, h in enumerate(triples)}
    records = []
    universe = tuple(range(1, 481))
    transports = lift['transported_cuts']
    assert len(transports) == 12
    for index, image in enumerate(sorted(group)):
        action = [positions[tuple(sorted(image[i+3]-3 for i in h))] for h in triples]
        assert sorted(action) == list(range(480))
        chosen = {action[a]+1 for a in selected}
        assignment = {i: i in chosen for i in universe}
        cut = transports[index]
        assert cut['core_action_index'] == index
        terms = [(a+1, c) for a, c in cut['signed_coefficients']]
        assert len(terms) == 480 and len({i for i, _ in terms}) == 480
        assert all(type(c) is int and c != 0 for _, c in terms)
        assert sum(c for i, c in terms if i in chosen) == cut['transported_selection_gap'] == 26
        plain = explain.independent_explanation(terms, 0, assignment)
        card = explain.cardinality_explanation(terms, 0, assignment, universe, population)
        for record in (plain, card):
            assert all(assignment[abs(lit)] == (lit < 0) for lit in record['clause'])
        # Separate direct recomputation from the published literal lists.
        a = dict(terms)
        fixed = {abs(lit): int(lit < 0) for lit in plain['clause']}
        lower = sum(a[i]*fixed[i] if i in fixed else min(0, a[i]) for i in universe)
        assert lower == plain['minimum_if_clause_is_false'] > 0
        fixed = {abs(lit): int(lit < 0) for lit in card['clause']}
        remaining = population-sum(fixed.values())
        free_coefficients = sorted(a[i] for i in universe if i not in fixed)
        lower = sum(a[i]*v for i, v in fixed.items())+sum(free_coefficients[:remaining])
        assert lower == card['minimum_if_clause_is_false'] > 0
        assert len(card['clause']) <= 60 and all(lit < 0 for lit in card['clause'])
        records.append({'core_action_index': index,
                        'proved_signed_cut_sha256': hashlib.sha256(canonical(cut)).hexdigest(),
                        'transported_selected_columns': sorted(i-1 for i in chosen),
                        'independent_explanation': plain,
                        'cardinality_explanation': card})
    counts = Counter()
    for record in records:
        counts['independent_literal_occurrences'] += len(record['independent_explanation']['clause'])
        counts['cardinality_literal_occurrences'] += len(record['cardinality_explanation']['clause'])
    return {'status': 'PASS: twelve proved signed cuts give exact independent and population clause explanations',
            'source_sha256': digest(Path(__file__)), 'helper_sha256': EXPLAIN_SHA,
            'frozen_inputs': INPUTS, 'records': records, 'summary': dict(counts),
            'population_premise': {'value': 60, 'Gram_diagonal_equations': 18,
                'each_diagonal_margin': 10, 'each_selector_multiplicity_in_diagonal_sum': 3,
                'derivation': 'Sum the eighteen exact diagonal Gram equations: 3*sum(z)=180.',
                'complete_original_Gram_position_coverage_checked': True,
                'original_incidence_model_sha256': INPUTS['f0-incidence-case00-model.json']},
            'new_auxiliary_variables': 0, 'candidate_falsifies_every_corresponding_clause': True,
            'inequalities_are_not_replaced_in_any_existing_formula': True,
            'clauses_are_weaker_consequences_not_complete_PB_encodings': True,
            'optimizer_or_solver_called': False, 'component_excluded': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    result = calculate()
    if args.replay:
        assert canonical(result) == canonical(read(args.replay))
        result = {'status': 'PASS: cold twelve-cut clause and population-premise replay',
                  'source_sha256': digest(Path(__file__)), 'certificate_sha256': digest(args.replay),
                  'summary': result['summary'], 'optimizer_or_solver_called': False}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'records'}, indent=2))
    print('seconds', time.monotonic()-started)
    print('output_sha256', digest(args.output))
