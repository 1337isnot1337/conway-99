"""Independent arithmetic/provenance audit; no subject import or CNF build."""

import ast
from collections import Counter
import gzip
import hashlib
import json
from math import gcd
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT/'experiments/workspace'
LOGS = ROOT/'experiments/logs/root-prism-free'
SOURCE = WORK/'root_prism_free_f0_lazy_registry.py'
CERTIFICATE = LOGS/'f0-lazy-registry.json.gz'
DOMAIN = LOGS/'f0-exterior-row-domains02.json.gz'
BASE = LOGS/'f0-incidence-case00-model.json'
BINDINGS = {
    SOURCE: '9a9a2c40241dc3899b9692568a2ee4127d17d5a4b8c33972dfd9b59a57e43478',
    CERTIFICATE: 'b8e008d3c89122ae8a7b96c1c7c68d506e3a6345cc2a0ccd334f4f79597d0dc1',
    DOMAIN: '665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4',
    BASE: '16deda266149f5123a1db3833cfebf22d6bdfe4426b1424fcc51ccbfdc38f0a1'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def predicate(target, demand, weights):
    capped = [[a+1, min(w, demand)] for a, w in weights]
    divisor = gcd(*(w for _, w in capped)) if capped else 1
    normalized = [[a, w//divisor] for a, w in capped]
    return {'target': target+1, 'demand': (demand+divisor-1)//divisor, 'terms': normalized}


def audit():
    started = time.monotonic()
    for path, expected in BINDINGS.items():
        assert digest(path) == expected
    saved, domain, model = read(CERTIFICATE), read(DOMAIN), read(BASE)
    assert saved['source_sha256'] == BINDINGS[SOURCE]
    tree = ast.parse(SOURCE.read_text())
    constants = {node.targets[0].id: ast.literal_eval(node.value) for node in tree.body
                 if isinstance(node, ast.Assign) and len(node.targets) == 1
                 and isinstance(node.targets[0], ast.Name) and node.targets[0].id in ('SOURCES', 'INPUTS')}
    assert constants['SOURCES'] == saved['dependency_source_hashes']
    assert constants['INPUTS'] == saved['input_hashes']
    for name, expected in constants['SOURCES'].items():
        assert digest(WORK/name) == expected
    for name, expected in constants['INPUTS'].items():
        assert digest(LOGS/name) == expected
    rows, signed = saved['individual_cuts'], saved['symmetric_cuts']
    assert len(rows) == 660 and len(signed) == 72
    triples, targets, neighbors = (domain[k] for k in
        ('signature_domain', 'row_targets', 'possible_neighbor_signature_ids'))
    assert len(triples) == len(targets) == len(neighbors) == 480
    assert all(len(set(h)) == 3 for h in triples)
    assert all(a not in neighbors[a] and neighbors[a] == sorted(set(neighbors[a])) for a in range(480))
    assert all(a in neighbors[b] for a in range(480) for b in neighbors[a])
    assert sum(map(len, neighbors))//2 == saved['complete_global_edges'] == 68394
    for cut in rows:
        a, vector = cut['target'], cut['integer_vector']
        assert len(vector) == 18 and all(type(v) is int for v in vector)
        demand = sum(v*q for v, q in zip(vector, targets[a]))
        weights = [[b, sum(vector[i] for i in triples[b])] for b in neighbors[a]]
        weights = [[b, w] for b, w in weights if w > 0]
        assert demand == cut['demand'] > 0 and weights == cut['weights']
        assert hashlib.sha256(canonical(predicate(a, demand, weights))).hexdigest() == cut['normalized_predicate_sha256']
    assert len({c['normalized_predicate_sha256'] for c in rows}) == 660
    for cut in signed:
        terms = cut['signed_coefficients']
        assert terms == sorted(terms) and len({a for a, _ in terms}) == len(terms)
        assert all(type(a) is int and 0 <= a < 480 and type(c) is int and c for a, c in terms)
        assert gcd(*(abs(c) for _, c in terms)) == 1
        assert hashlib.sha256(canonical(terms)).hexdigest() == cut['predicate_sha256']
    assert len({c['predicate_sha256'] for c in signed}) == 72

    parent = read(LOGS/'f0-deficit-row-loop-run01/result.json')
    row_path, signed_path = ROOT/parent['individual-registry'], ROOT/parent['symmetric-registry']
    assert digest(row_path) == parent['individual-registry_sha256']
    assert digest(signed_path) == parent['symmetric-registry_sha256']
    assert rows[:647] == read(row_path) and signed == read(signed_path)
    final = parent['iterations'][-1]
    final_path = ROOT/final['individual_rows']
    assert digest(final_path) == final['individual_rows_sha256']
    final_rows = read(final_path)
    reconstructed, keys = list(rows[:647]), {c['normalized_predicate_sha256'] for c in rows[:647]}
    for row in final_rows['rows']:
        if 'exact_obstruction' not in row:
            continue
        for transport in row['exact_obstruction']['all12_verified_core_transports']:
            a, vector = transport['target'], transport['integer_vector']
            demand = sum(v*q for v, q in zip(vector, targets[a]))
            weights = [[b, sum(vector[i] for i in triples[b])] for b in neighbors[a]]
            weights = [[b, w] for b, w in weights if w > 0]
            assert demand == transport['integer_demand'] and weights == transport['positive_weighted_terms']
            key = hashlib.sha256(canonical(predicate(a, demand, weights))).hexdigest()
            cut = {'target': a, 'integer_vector': vector, 'demand': demand, 'weights': weights,
                   'normalized_predicate_sha256': key,
                   'origin': {'kind': 'loop exact row obstruction', 'iteration': final['iteration'],
                              'source_target': row['target'], 'core_action_index': transport['core_action_index']}}
            if key not in keys:
                reconstructed.append(cut); keys.add(key)
    assert reconstructed == rows and saved['previously_unencoded_individual_indices'] == list(range(647, 660))
    assert hashlib.sha256(canonical([rows, signed])).hexdigest() == saved['raw_registry_sha256']

    core = domain['component_core_rows']
    assert len(core) == 21
    gram = [[12*int(i == j)+2-(core[i+3]&core[j+3]).bit_count()-((core[i+3] >> (j+3))&1)
             for j in range(18)] for i in range(18)]
    coverage = model['formula']['Gram_position_coverage']
    assert [(i, j) for i, j, *_ in coverage] == [(i, j) for i in range(18) for j in range(i, 18)]
    for i, j, quota, members, _ in coverage:
        assert quota == gram[i][j] and members == sum(i in h and j in h for h in triples)
    assert [gram[i][i] for i in range(18)] == [10]*18
    assert saved['population_premise']['population'] == 60
    assert saved['population_premise']['universe'] == list(range(1, 481))
    assert sum(gram[i][i] for i in range(18)) == 3*60

    action_records = saved['verified_core_actions']
    assert len(action_records) == 12
    for action in action_records:
        move, image = action['component_image'], action['signature_image']
        assert sorted(move) == list(range(18)) and sorted(image) == list(range(480))
        center_image = {}
        for i in range(18):
            old_center, new_center = core[i+3]&7, core[move[i]+3]&7
            assert old_center.bit_count() == new_center.bit_count() == 1
            a, b = old_center.bit_length()-1, new_center.bit_length()-1
            assert center_image.get(a, b) == b
            center_image[a] = b
        assert sorted(center_image) == sorted(center_image.values()) == [0, 1, 2]
        full = [center_image[i] for i in range(3)]+[i+3 for i in move]
        assert all(sum(1 << full[j] for j in range(21) if core[i] >> j & 1) == core[full[i]] for i in range(21))
        for a, h in enumerate(triples):
            assert sorted(move[i] for i in h) == triples[image[a]]
            assert all(targets[image[a]][move[i]] == targets[a][i] for i in range(18))
            assert sorted(image[b] for b in neighbors[a]) == neighbors[image[a]]

    old_cut_path = LOGS/'f0-first-design-exterior-row-certificate.json.gz'
    assert digest(old_cut_path) == '3b5c302f9a9e3bfce6175de7c73cb835cc89f88e63148de15d59085b1da974c0'
    old_clauses = read(old_cut_path)['row_certificate']['all_guarded_clauses']
    assert len(old_clauses) == 444
    failures = []
    for candidate in saved['seed_candidates']:
        selected = candidate['selected_signature_ids']
        assert selected == sorted(set(selected)) and len(selected) == 60
        chosen = set(selected)
        assert all(sum(i in triples[a] and j in triples[a] for a in chosen) == gram[i][j]
                   for i in range(18) for j in range(i, 18))
        assert all(any((v-1 in chosen) if v > 0 else (-v-1 not in chosen) for v in clause) for clause in old_clauses)
        values = [cut['demand']*int(cut['target'] in chosen)-sum(w for b, w in cut['weights'] if b in chosen)
                  for cut in rows]
        values += [sum(c for a, c in cut['signed_coefficients'] if a in chosen) for cut in signed]
        assert max(values) > 0
        assert hashlib.sha256(canonical(values)).hexdigest() == candidate['complete_registry_value_sha256']
        assert sum(v > 0 for v in values) == candidate['violated_proved_inequalities']
        failures.append(sum(v > 0 for v in values))
    assert len(failures) == 30

    report = {'status': 'PASS: independent lazy-registry source, arithmetic and provenance audit',
        'audit_source_sha256': digest(Path(__file__)), 'subject_source_sha256': BINDINGS[SOURCE],
        'certificate_sha256': BINDINGS[CERTIFICATE], 'domain_sha256': BINDINGS[DOMAIN],
        'individual_potentials_and_predicates_recomputed': 660,
        'prior_individual_prefix_recovered': 647, 'unencoded_final_transports_recovered': 13,
        'signed_predicates_and_parent_registry_checked': 72,
        'shared_proof_families_source_reviewed': 6, 'all_shared_ray_arithmetic_repeated': False,
        'original_Gram_positions_checked': 171, 'population_derived': 60,
        'complete_universe_size': 480, 'actual_core_signature_target_and_neighbor_actions_checked': 12,
        'seed_Gram_and_444_old_clause_checks': 30, 'complete732_cut_seed_evaluations_checked': 30,
        'seed_violation_counts': failures,
        'source_review': [
            'The helper reconstructs only the original direct-cut base, then validates mathematical cuts directly.',
            'All 13 final row transports omitted by the bounded parent encoding are recovered without assuming its candidate.',
            'All six shared families replay exact fixed rays and recompute the universal full-domain lift and all 12 transports.',
            'The fixed selections choose potential support and allocation; they are not hypotheses of the resulting cuts.',
            'All 480 selectors remain free; the 30 old incidences are controls and no alternative component is fixed.',
            'The population premise follows from the original Gram diagonal equations, rather than observed seed sizes.'],
        'subject_modules_imported': False, 'subject_calculate_or_replay_called': False,
        'CNF_rebuilt': False, 'solver_or_optimizer_called': False, 'DRAT_checked': False,
        'whole_component_excluded': False, 'seconds': time.monotonic()-started}
    output = LOGS/'f0-lazy-registry-independent-audit.json'
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2)); print('output_sha256', digest(output))


if __name__ == '__main__':
    audit()
