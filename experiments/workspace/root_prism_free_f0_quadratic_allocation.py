"""Exact Boolean shared-potential allocation pilot; no optimizer or solver.

The fixed component has480 possible triples and68394 eligible edges.
For any integer mixed-row potentials, actual completions satisfy
Q(z)=sum(w_ab^+ z_a z_b)-sum(d_a z_a)>=0.  A positive edge weight
may be allocated to either endpoint to produce a necessary signed
linear selector inequality.  At a Boolean candidate, allocating to an
absent endpoint whenever possible attains exactly -Q(candidate).

This file recovers all24 published potential families, verifies all12
core transports and all288 previous fixed allocations, and checks the
pointwise allocation on saved incidences.  It does not change a formula,
choose an incidence, or run an optimizer.  All arithmetic is unbounded
Python integer arithmetic (Fractions only in artificial controls).
"""

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations, product
import json
from math import gcd
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
INPUTS = {
    'f0-exterior-row-domains02.json.gz': '665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4',
    'f0-lazy-registry.json.gz': 'b8e008d3c89122ae8a7b96c1c7c68d506e3a6345cc2a0ccd334f4f79597d0dc1',
    'f0-symmetric-selector-cut-certificate.json.gz': '3aea5e48c4a35eb7e023708231f3dbf585634c25de25484f364276041260f846',
    'f0-carry-row-loop-run01-shared-ray-repair.json.gz': '96e945d1211147e2ad13ed3468f51d72bd3ef87319ca33153eda6248e0b5c7c5',
    'f0-symmetric-row-loop-run01/result.json': '03c7cfa9cfde1a23df0e3b3b2ffe6e1650801eaf5daf9e79a0403f45574fd20b',
    'f0-deficit-row-loop-run01/result.json': '13b47be2d896887c3b23c435499bc6b4ba75c541469a3de229cebeb98b14a8fe',
    'f0-lazy-row-loop-run01/result.json': '93037f2b7c0055aabc115ae3a269547f0ad17c7da904b78ab4b76ce9e6b42468',
    'f0-lazy-continuation-run01/result.json': '3bb89930202266409acfce6ca52949b5c370928216ce64e9123e22daf5f9e593',
    'f0-bounded-shared-separator-run01-universal-cuts.json': '9029303e60cbf1249db03a5b9be0da44f2fb2b0c086760067f28887ee286e45f',
    'f0-bounded-lazy-continuation-run01/result.json': '88c4858aa36aaf3af15f4b53ce41be5c1fee3d8f2c237a49e2df026f1228bd86',
    'f0-terminal-bounded-query-run01-universal-cuts.json': '2dcb71399b53da20f21cc2dc1f4cd40a3db92d2d28e0ee8844e70aba3ba68c82'}


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_hash(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def checked(path, expected):
    assert digest(path) == expected, str(path)
    return read(path)


def child(record, key):
    path = ROOT/record[key]
    assert path.resolve().is_relative_to(LOGS.resolve())
    return checked(path, record[key+'_sha256'])


def normalized(terms):
    assert terms == sorted(terms) and len({a for a, _ in terms}) == len(terms)
    assert all(type(a) is int and 0 <= a < 480 and type(c) is int and c for a, c in terms)
    divisor = gcd(*(abs(c) for _, c in terms))
    assert divisor > 0
    return [[a, c//divisor] for a, c in terms], divisor


def domain(saved, expected_actions):
    """Reconstruct full triple/edge domain and actual core relabelings."""
    core = saved['component_core_rows']
    assert len(core) == 21 and all(type(row) is int and 0 <= row < 1 << 21 for row in core)
    assert all(not (core[i] >> i & 1) for i in range(21))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    adjacency = [(row >> 3)&((1 << 18)-1) for row in core[3:]]
    gram = [[12*int(i == j)+2-(core[3+i]&core[3+j]).bit_count()-(core[3+i] >> (3+j) & 1)
             for j in range(18)] for i in range(18)]
    triples = []
    for h in combinations(range(18), 3):
        if max(sum(i//6 == f for i in h) for f in range(3)) > 2:
            continue
        if any(gram[i][j] == 0 for i, j in combinations(h, 2)):
            continue
        if any(sum(int(i == j or adjacency[i] >> j & 1) for j in h) > 2 for i in range(18)):
            continue
        triples.append(list(h))
    assert triples == saved['signature_domain'] and len(triples) == 480
    targets = [[2-int(i in h)-sum(adjacency[i] >> j & 1 for j in h) for i in range(18)] for h in triples]
    assert targets == saved['row_targets'] and all(min(q) >= 0 and sum(q) == 24 for q in targets)
    masks = [sum(1 << i for i in h) for h in triples]
    edges, neighbors = [], [[] for _ in triples]
    for a, b in combinations(range(480), 2):
        if (masks[a]&masks[b]).bit_count() > 1:
            continue
        if any(targets[a][i] == 0 for i in triples[b]) or any(targets[b][i] == 0 for i in triples[a]):
            continue
        edges.append([a, b]); neighbors[a].append(b); neighbors[b].append(a)
    assert len(edges) == 68394 and neighbors == saved['possible_neighbor_signature_ids']
    identity = tuple(range(21))
    group, frontier = {identity}, [identity]
    while frontier:
        old = frontier.pop()
        for generator in saved['core_generators']:
            image = tuple(generator[old[i]] for i in range(21))
            assert sorted(image) == list(range(21)) and set(image[:3]) == set(range(3))
            assert all((core[i] >> j & 1) == (core[image[i]] >> image[j] & 1)
                       for i in range(21) for j in range(21))
            if image not in group:
                group.add(image); frontier.append(image)
    assert len(group) == 12
    positions, edge_set = {tuple(h): a for a, h in enumerate(triples)}, {tuple(e) for e in edges}
    actions = []
    for image in sorted(group):
        move = [image[i+3]-3 for i in range(18)]
        action = [positions[tuple(sorted(move[i] for i in h))] for h in triples]
        assert sorted(action) == list(range(480))
        assert {tuple(sorted((action[a], action[b]))) for a, b in edges} == edge_set
        assert all(targets[action[a]][move[i]] == targets[a][i] for a in range(480) for i in range(18))
        actions.append({'component_image': move, 'signature_image': action})
    assert actions == expected_actions
    return triples, targets, gram, edges, actions


def quantities(triples, targets, edges, potentials):
    n, width = len(triples), len(targets[0])
    assert len(targets) == len(potentials) == n
    assert all(len(v) == width and all(type(x) is int for x in v) for v in potentials)
    demand = [sum(x*y for x, y in zip(v, q)) for v, q in zip(potentials, targets)]
    positive = []
    for a, b in edges:
        w = sum(potentials[a][i] for i in triples[b])+sum(potentials[b][i] for i in triples[a])
        if w > 0:
            positive.append([a, b, w])
    return demand, positive


def best_allocation(demand, positive, selected):
    """Exact necessary linear cut; equality with -Q is Boolean-specific."""
    selected = set(selected)
    assert all(type(a) is int and 0 <= a < len(demand) for a in selected)
    coefficients, endpoints = list(demand), []
    for a, b, weight in positive:
        assert type(weight) is int and weight > 0 and 0 <= a < b < len(demand)
        endpoint = a if a not in selected else b if b not in selected else a
        coefficients[endpoint] -= weight
        endpoints.append(endpoint)
    gap = sum(demand[a] for a in selected)-sum(w for a, b, w in positive if a in selected and b in selected)
    assert sum(coefficients[a] for a in selected) == gap
    return coefficients, endpoints, gap


def moved_terms(terms, action):
    return sorted([action[a], c] for a, c in terms)


def saved_terms(transport):
    if 'signed_coefficients' in transport:
        return transport['signed_coefficients']
    return sorted(transport['positive_terms']+[[a, -w] for a, w in transport['negative_side_positive_weights']])


def inspect_selection(selected, triples, gram, motifs):
    assert selected == sorted(set(selected)) and len(selected) == 60
    assert all(type(a) is int and 0 <= a < len(triples) for a in selected)
    selected_set = set(selected)
    assert all(not (a in selected_set and b in selected_set) for a, b in motifs)
    assert [[sum(i in triples[a] and j in triples[a] for a in selected) for j in range(18)]
            for i in range(18)] == gram


def family_record(index, lifted, origin, triples, targets, gram, edges, actions, motifs):
    support = lifted.get('selected_signature_ids_for_allocation_only',
                         lifted.get('selected_signature_ids_for_potential_support_and_allocation_only'))
    inspect_selection(support, triples, gram, motifs)
    sparse = lifted['nonzero_target_potentials']
    assert sparse == sorted(sparse) and len({a for a, _ in sparse}) == len(sparse)
    potentials = [[0]*18 for _ in range(480)]
    for a, vector in sparse:
        assert a in support and len(vector) == 18 and any(vector) and all(type(x) is int for x in vector)
        potentials[a] = list(vector)
    demand, positive = quantities(triples, targets, edges, potentials)
    coefficients, endpoints, gap = best_allocation(demand, positive, support)
    terms, divisor = normalized([[a, c] for a, c in enumerate(coefficients) if c])
    assert gap == lifted['raw_gap'] > 0 and divisor == lifted['coefficient_gcd']
    assert gap//divisor == lifted.get('normalized_gap', lifted.get('normalized_saved_gap'))
    if 'positive_edge_count' in lifted:
        assert len(positive) == lifted['positive_edge_count'] and len(edges) == lifted['complete_global_edges']
        assert object_hash(edges) == lifted['global_edge_sha256']
        support_set = set(support)
        records = [{'edge': [a, b], 'weight': w, 'allocated_endpoint': endpoint,
                    'kind': 'internal' if a in support_set and b in support_set else 'boundary'}
                   for (a, b, w), endpoint in zip(positive, endpoints)]
        assert object_hash(records) == lifted['positive_edge_allocation_sha256']
        assert dict(Counter(r['kind'] for r in records)) == lifted['positive_edge_type_counts']
    transports = []
    for action_index, action in enumerate(actions):
        image = action['signature_image']
        transport = lifted['transported_cuts'][action_index]
        assert transport['core_action_index'] == action_index
        expected = moved_terms(terms, image)
        assert expected == saved_terms(transport)
        moved_d = sorted([image[a], value] for a, value in enumerate(demand) if value)
        moved_p = sorted([min(image[a], image[b]), max(image[a], image[b]), w] for a, b, w in positive)
        transports.append({'core_action_index': action_index,
            'quadratic_predicate_sha256': object_hash([moved_d, moved_p]),
            'existing_linear_predicate_sha256': object_hash(expected),
            'known_generation_selection_raw_gap': gap})
    return {'family_index': index, 'origin': origin,
        'selected_generation_signature_ids': support, 'nonzero_target_potentials': sparse,
        'target_demands': demand, 'positive_edges': positive,
        'base_quadratic_predicate_sha256': object_hash([[[a, d] for a, d in enumerate(demand) if d], positive]),
        'old_allocation_raw_coefficients': coefficients, 'old_allocation_coefficient_gcd': divisor,
        'generation_raw_gap': gap, 'generation_normalized_gap': gap//divisor,
        'transports': transports}, [saved_terms(t) for t in lifted['transported_cuts']]


def controls():
    extrema, dominance = 0, 0
    small_edges = [[0, 1], [0, 2], [1, 2]]
    for weights in product(range(3), repeat=3):
        positive = [[a, b, w] for (a, b), w in zip(small_edges, weights) if w]
        demand = [3, -2, 1]
        for bits in product((0, 1), repeat=3):
            selected = {a for a, value in enumerate(bits) if value}
            coefficients, _, gap = best_allocation(demand, positive, selected)
            values = []
            for choices in product((0, 1), repeat=len(positive)):
                c = list(demand)
                for (a, b, w), side in zip(positive, choices):
                    c[(a, b)[side]] -= w
                value = sum(c[a] for a in selected)
                assert value <= gap
                values.append(value); dominance += 1
            assert max(values) == gap == sum(coefficients[a] for a in selected)
            extrema += 1
    # Forty edges of K10 minus a matching, plus four inactive vertices.
    triples = [list(h) for h in list(combinations(range(18), 3))[:14]]
    actual_edges = {(a, b) for a, b in combinations(range(10), 2) if a//2 != b//2}
    assert len(actual_edges) == 40
    targets = [[sum(i in triples[b] for b in range(10) if tuple(sorted((a, b))) in actual_edges)
                for i in range(18)] if a < 10 else [8*int(i in triples[a]) for i in range(18)]
               for a in range(14)]
    assert all(sum(q) == 24 for q in targets)
    edges = list(combinations(range(14), 2))
    feasible_checks = 0
    for seed in range(48):
        potentials = [[((seed+3)*(a+5)*(i+7)+a*i)%13-6 for i in range(18)] for a in range(14)]
        demand, positive = quantities(triples, targets, edges, potentials)
        signed_edge_sum = sum(sum(potentials[a][i] for i in triples[b])+sum(potentials[b][i] for i in triples[a])
                              for a, b in actual_edges)
        assert sum(demand[:10]) == signed_edge_sum
        coefficients, _, gap = best_allocation(demand, positive, set(range(10)))
        assert gap <= 0 and sum(coefficients[:10]) <= 0
        feasible_checks += 1
    # A genuine fractional edge box: every K10 edge has value8/9,
    # while the activation selectors remain Boolean.
    triples = [[0, 1, 2] for _ in range(10)]
    targets = [[8, 8, 8] for _ in range(10)]
    edges = list(combinations(range(10), 2))
    for seed in range(24):
        potentials = [[(seed+3*a+5*i)%11-5 for i in range(3)] for a in range(10)]
        demand, positive = quantities(triples, targets, edges, potentials)
        signed = sum(Fraction(8, 9)*(sum(potentials[a])+sum(potentials[b])) for a, b in edges)
        assert signed == sum(demand)
        _, _, gap = best_allocation(demand, positive, set(range(10)))
        assert gap <= 0
        feasible_checks += 1
    # Equality with the product is intentionally not asserted for
    # fractional selectors: min(1/2,1/2)=1/2 exceeds their product1/4.
    assert min(Fraction(1, 2), Fraction(1, 2)) != Fraction(1, 2)**2
    return {'endpoint_extrema_checks': extrema, 'individual_allocation_dominance_checks': dominance,
        'feasible_artificial_activated_boxes': feasible_checks, 'all_boxes_have_degree8_and_weight3_columns': True,
        'fractional_edge_box_checks': 24, 'fractional_selector_product_equality_explicitly_rejected': True,
        'optimizer_or_solver_called': False}


def prepare():
    loaded = {name: checked(LOGS/name, expected) for name, expected in INPUTS.items()}
    raw, registry = loaded['f0-exterior-row-domains02.json.gz'], loaded['f0-lazy-registry.json.gz']
    triples, targets, gram, edges, actions = domain(raw, registry['verified_core_actions'])
    origins, lifted_records = [], []
    def add(lifted, origin):
        lifted_records.append(lifted); origins.append(origin)
    def add_steps(name, indices):
        result = loaded[name]
        assert [s['iteration'] for s in result['iterations']] == list(range(len(result['iterations'])))
        assert [s['iteration'] for s in result['iterations'] if 'symmetric_lift' in s] == indices
        for index in indices:
            step = result['iterations'][index]
            lifted = child(step, 'symmetric_lift')
            candidate = child(step, 'candidate')
            assert candidate['selected_signature_ids'] == lifted['selected_signature_ids_for_allocation_only']
            add(lifted, {'kind': 'saved complete universal lift', 'result': str((LOGS/name).relative_to(ROOT)),
                'result_sha256': INPUTS[name], 'iteration': index,
                'lift': step['symmetric_lift'], 'lift_sha256': step['symmetric_lift_sha256'],
                'candidate': step['candidate'], 'candidate_sha256': step['candidate_sha256']})
    name = 'f0-symmetric-selector-cut-certificate.json.gz'
    add(loaded[name], {'kind': 'first exact universal certificate', 'path': str((LOGS/name).relative_to(ROOT)),
                       'sha256': INPUTS[name]})
    add_steps('f0-symmetric-row-loop-run01/result.json', [4])
    name = 'f0-carry-row-loop-run01-shared-ray-repair.json.gz'
    add(loaded[name]['universal_selector_lift'], {'kind': 'separate exact-deficit repair',
        'path': str((LOGS/name).relative_to(ROOT)), 'sha256': INPUTS[name], 'json_key': 'universal_selector_lift'})
    add_steps('f0-deficit-row-loop-run01/result.json', [9, 10, 11])
    add_steps('f0-lazy-row-loop-run01/result.json', [7, 9, 12])
    add_steps('f0-lazy-continuation-run01/result.json', [9, 10, 12, 13, 15])
    name = 'f0-bounded-shared-separator-run01-universal-cuts.json'
    add(loaded[name], {'kind': 'separate exact bounded support gap33', 'path': str((LOGS/name).relative_to(ROOT)),
                       'sha256': INPUTS[name]})
    add_steps('f0-bounded-lazy-continuation-run01/result.json', [10, 11, 36, 37, 38, 41, 42, 45])
    name = 'f0-terminal-bounded-query-run01-universal-cuts.json'
    add(loaded[name], {'kind': 'separate exact bounded support gap64', 'path': str((LOGS/name).relative_to(ROOT)),
                       'sha256': INPUTS[name]})
    assert len(origins) == len(lifted_records) == 24
    families, recovered_terms = [], []
    for index, (lifted, origin) in enumerate(zip(lifted_records, origins)):
        record, terms = family_record(index, lifted, origin, triples, targets, gram, edges, actions, raw['motif_pairs'])
        families.append(record); recovered_terms.extend(terms)
    parent = loaded['f0-bounded-lazy-continuation-run01/result.json']
    old_signed, old_rows = child(parent, 'symmetric-registry'), child(parent, 'individual-registry')
    assert len(old_signed) == 276 and len(old_rows) == 2640
    for old, terms in zip(old_signed, recovered_terms):
        assert old['signed_coefficients'] == terms and old['predicate_sha256'] == object_hash(terms)
    assert len(recovered_terms) == 288
    assert len({object_hash(t) for t in recovered_terms}) == 288
    candidates = {}
    def add_candidate(selected, origin):
        inspect_selection(selected, triples, gram, raw['motif_pairs'])
        key = tuple(selected)
        if key not in candidates:
            candidates[key] = {'selected_signature_ids': selected, 'origins': []}
        candidates[key]['origins'].append(origin)
    for seed in registry['seed_candidates']:
        for origin in seed['origins']:
            add_candidate(seed['selected_signature_ids'], origin)
    for name in ('f0-lazy-row-loop-run01/result.json', 'f0-lazy-continuation-run01/result.json',
                 'f0-bounded-lazy-continuation-run01/result.json'):
        for step in loaded[name]['iterations']:
            if 'candidate' in step:
                selected = child(step, 'candidate')['selected_signature_ids']
                add_candidate(selected, {'path': step['candidate'], 'sha256': step['candidate_sha256'],
                    'result': str((LOGS/name).relative_to(ROOT)), 'result_sha256': INPUTS[name], 'iteration': step['iteration']})
    return {'status': 'complete24-family quadratic allocation preparation PASS; no new query',
        'source_sha256': digest(Path(__file__)), 'input_hashes': INPUTS,
        'component_core_rows': raw['component_core_rows'], 'signature_domain': triples, 'row_targets': targets,
        'complete_global_edges': len(edges), 'global_edge_sha256': object_hash(edges),
        'verified_core_actions': actions, 'potential_families': families, 'base_family_count': 24,
        'transported_family_count': 288,
        'distinct_transported_quadratic_predicates': len({t['quadratic_predicate_sha256'] for f in families for t in f['transports']}),
        'all276_parent_signed_allocations_reproduced': True, 'all12_gap64_allocations_reproduced': True,
        'parent_individual_registry_sha256': parent['individual-registry_sha256'],
        'parent_signed_registry_sha256': parent['symmetric-registry_sha256'],
        'parent_explanation_registry_sha256': parent['explanation-registry_sha256'],
        'retained_existing_inequalities': 2928, 'retained_existing_explanation_count': 5340,
        'parent_final_cnf_sha256': parent['final_cnf_sha256'],
        'saved_candidates': list(candidates.values()), 'saved_candidate_count': len(candidates),
        'controls': controls(), 'all480_selectors_free': True,
        'second_component_or_alignment_fixed': False, 'original_UNKNOWNS_unchanged': True,
        'original_registry_or_formula_modified': False, 'optimizer_or_solver_called': False}


def scan(prepared):
    """Check every transported potential on every saved Boolean incidence."""
    families, actions = prepared['potential_families'], prepared['verified_core_actions']
    inverses = []
    for action in actions:
        inverse = [0]*480
        for a, b in enumerate(action['signature_image']):
            inverse[b] = a
        inverses.append(inverse)
    lookup = [{(a, b): w for a, b, w in f['positive_edges']} for f in families]
    rows, cuts, seen = [], [], set()
    scalar_checks = strict_improvements = new_family_violations = old_violations = quadratic_violations = 0
    newly_detected_candidates = 0
    for candidate_index, candidate in enumerate(prepared['saved_candidates']):
        selected = candidate['selected_signature_ids']
        moved = [sorted(inverse[a] for a in selected) for inverse in inverses]
        gaps, old_values, new_ids = [], [], []
        best = None
        for family_index, family in enumerate(families):
            demand, old_coefficients = family['target_demands'], family['old_allocation_raw_coefficients']
            weight = lookup[family_index]
            for action_index, source_selected in enumerate(moved):
                raw_gap = sum(demand[a] for a in source_selected)-sum(weight.get((a, b), 0) for a, b in combinations(source_selected, 2))
                old_value = sum(old_coefficients[a] for a in source_selected)
                assert old_value <= raw_gap
                predicate_id = 12*family_index+action_index
                gaps.append(raw_gap); old_values.append(old_value); scalar_checks += 1
                strict_improvements += old_value < raw_gap
                old_violations += old_value > 0
                quadratic_violations += raw_gap > 0
                if raw_gap > 0 and old_value <= 0:
                    new_family_violations += 1; new_ids.append(predicate_id)
                    # A deterministic new witness is exported for each saved
                    # incidence with any previously unviolated family.
                    if best is None or raw_gap > best[0]:
                        best = (raw_gap, family_index, action_index, source_selected)
        if max(gaps) > 0 and max(old_values) <= 0:
            newly_detected_candidates += 1
        record = {'candidate_index': candidate_index, 'selection_sha256': object_hash(selected),
                  'negative_Q_values': gaps, 'old_allocation_raw_values': old_values,
                  'negative_Q_predicates': [i for i, value in enumerate(gaps) if value > 0],
                  'newly_violated_family_predicates': new_ids}
        if best is not None:
            _, family_index, action_index, source_selected = best
            family = families[family_index]
            coefficients, endpoints, gap = best_allocation(family['target_demands'], family['positive_edges'], source_selected)
            terms, divisor = normalized([[a, c] for a, c in enumerate(coefficients) if c])
            terms = moved_terms(terms, actions[action_index]['signature_image'])
            assert gap > 0 and sum(c for a, c in terms if a in set(selected)) == gap//divisor
            predicate = object_hash(terms)
            if predicate not in seen:
                cuts.append({'candidate_index': candidate_index, 'family_index': family_index,
                    'core_action_index': action_index, 'selected_signature_ids': selected,
                    'base_candidate_signature_ids': source_selected,
                    'positive_edge_endpoint_choices_sha256': object_hash(endpoints),
                    'raw_gap': gap, 'coefficient_gcd': divisor, 'normalized_gap': gap//divisor,
                    'signed_coefficients': terms, 'predicate_sha256': predicate,
                    'validity': 'every positive weight allocated to one endpoint; no fixed-selection premise'})
                seen.add(predicate)
            record['exported_predicate_sha256'] = predicate
        rows.append(record)
    return {'status': 'complete saved-candidate quadratic allocation scan PASS; no new query',
        'source_sha256': digest(Path(__file__)), 'preparation_content_sha256': object_hash(prepared),
        'candidate_count': len(rows), 'transported_family_count': 288, 'exact_scalar_comparisons': scalar_checks,
        'strict_pointwise_improvements': strict_improvements,
        'old_fixed_allocation_violations': old_violations, 'quadratic_violations': quadratic_violations,
        'new_family_violations': new_family_violations,
        'candidates_detected_only_by_quadratic_family_union': newly_detected_candidates,
        'per_candidate': rows, 'new_endpoint_allocation_cuts': cuts,
        'exported_cut_policy': 'at most one maximal-raw-gap new-family witness per saved incidence, then exact deduplication',
        'no_global_linear_domination_claim': True, 'Boolean_selectors_required_for_pointwise_equality': True,
        'prior_2916_plus_gap64_inequalities_retained': True, 'original_registry_or_formula_modified': False,
        'optimizer_or_solver_called': False, 'whole_component_excluded': False}


def save_new(path, value):
    assert not path.exists(), str(path)
    raw = canonical(value)+b'\n'
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['controls', 'prepare', 'replay', 'scan', 'replay-scan'])
    parser.add_argument('--preparation', type=Path)
    parser.add_argument('--result', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    started = time.perf_counter()
    assert not args.output.exists()
    if args.mode == 'controls':
        summary = controls()
        summary['source_sha256'] = digest(Path(__file__))
    else:
        assert args.preparation is not None
        prepared = prepare()
        if args.mode == 'prepare':
            save_new(args.preparation, prepared)
        else:
            assert prepared == read(args.preparation)
        summary = {'status': prepared['status'], 'preparation_sha256': digest(args.preparation),
            'families': 24, 'transports': 288, 'saved_candidates': prepared['saved_candidate_count'],
            'distinct_quadratic_predicates': prepared['distinct_transported_quadratic_predicates'],
            'complete_positive_edges_across_base_families': sum(len(f['positive_edges']) for f in prepared['potential_families']),
            'controls': prepared['controls']}
        if args.mode in ('scan', 'replay-scan'):
            assert args.result is not None
            result = scan(prepared)
            if args.mode == 'scan':
                save_new(args.result, result)
            else:
                assert result == read(args.result)
            summary.update({k: v for k, v in result.items() if k not in ('per_candidate', 'new_endpoint_allocation_cuts')})
            summary['new_endpoint_allocation_cuts'] = len(result['new_endpoint_allocation_cuts'])
            summary['result_sha256'] = digest(args.result)
    summary['elapsed_seconds'] = time.perf_counter()-started
    save_new(args.output, summary)
    print(json.dumps(summary, indent=2), flush=True)
