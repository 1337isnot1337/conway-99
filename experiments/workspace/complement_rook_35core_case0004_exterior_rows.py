"""Exact exterior-row domains for35-core case4; preparation only.

The old numerical incidence point chooses up to32 rows for a future LP
discovery pilot. It is never an exact incidence certificate. No optimizer,
SAT query, graph completion, or whole-case exclusion is performed here.
"""

import argparse
from collections import Counter
import gzip
from itertools import combinations, product
import json
import math
from pathlib import Path
import time

import complement_rook_35core_incidence as original


ROOT, LOGS = original.ROOT, original.LOGS
BASE_MODEL = LOGS / 'complement-rook-35core-first-local-sweep01/case0004-model.json'
BASE_SHA = '43fc0c40a724f4c287df770fce58abc45835ee7534f2b7e5cd06d3baf380cfde'
PROPOSAL = LOGS / 'complement-rook-35core-case0004-lp-result.json'
PROPOSAL_SHA = '716c47ea322a2ede86974dc22354a538cee0ca1b639b757e4be61926a17408c2'
LP_MODEL = LOGS / 'complement-rook-35core-case0004-lp-model.json.gz'
LP_MODEL_SHA = '18e7b79a7e83c1c40f0c0c29301703400f26b42401f0b07a2f21783a298119a6'
VARIANT = 'with30_binary_no_good_rows'
digest, canonical, portable = original.digest, original.canonical, original.portable


def row_domains(core, masks, degree):
    n = len(core)
    assert all(0 <= row < 1 << n for row in core)
    assert all(not (row >> i & 1) for i, row in enumerate(core))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(n) for j in range(n))
    assert len(set(masks)) == len(masks)
    targets = [[2 - (mask >> i & 1) - (core[i] & mask).bit_count() for i in range(n)]
               + [degree - mask.bit_count()] for mask in masks]
    assert all(min(t) >= 0 for t in targets)
    zero = [sum(1 << i for i in range(n) if t[i] == 0) for t in targets]
    neighbors = [[] for _ in masks]
    for a, b in combinations(range(len(masks)), 2):
        if (masks[a] & masks[b]).bit_count() > 1:
            continue
        if masks[b] & zero[a] or masks[a] & zero[b]:
            continue
        neighbors[a].append(b)
        neighbors[b].append(a)
    assert all(row == sorted(set(row)) and a not in row for a, row in enumerate(neighbors))
    return targets, neighbors


def verify_potential(masks, targets, neighbors, target, vector):
    """Exact universally necessary inequality, independent of any LP point."""
    n = len(targets[target]) - 1
    assert len(vector) == n + 1 and all(type(v) is int for v in vector)
    demand = sum(a * b for a, b in zip(vector, targets[target]))
    assert demand > 0
    positive = []
    products = []
    for b in neighbors[target]:
        value = vector[-1] + sum(vector[i] for i in range(n) if masks[b] >> i & 1)
        products.append([b, value])
        if value > 0:
            positive.append([b, value])
    return {'target_column': target, 'integer_vector': vector, 'positive_demand': demand,
            'positive_terms': positive, 'all_eligible_neighbor_products': products,
            'inequality': 'sum positive(v dot (h_b,1))*x_b >= positive_demand*x_target',
            'valid_for_actual_completions': True, 'numeric_proposal_used_in_verification': False}


def controls():
    # A genuine SRG(9,4,1,2) supplies an exact mixed-row positive control.
    adjacent = lambda a, b: a != b and (a // 3 == b // 3 or a % 3 == b % 3)
    core_sites, exterior = [0, 1, 3, 4, 8], [2, 5, 6, 7]
    core = [sum(1 << j for j, b in enumerate(core_sites) if adjacent(a, b)) for a in core_sites]
    masks = [sum(1 << j for j, b in enumerate(core_sites) if adjacent(a, b)) for a in exterior]
    targets, neighbors = row_domains(core, masks, 4)
    actual = [[b for b in range(4) if adjacent(exterior[a], exterior[b])] for a in range(4)]
    checked = 0
    for a in range(4):
        assert set(actual[a]) <= set(neighbors[a])
        value = [sum(masks[b] >> i & 1 for b in actual[a]) for i in range(5)] + [len(actual[a])]
        assert value == targets[a]
        for vector in product((-1, 0, 1), repeat=6):
            if sum(v * t for v, t in zip(vector, targets[a])) > 0:
                certificate = verify_potential(masks, targets, neighbors, a, list(vector))
                assert sum(w for b, w in certificate['positive_terms']) >= certificate['positive_demand']
                checked += 1
    # Independent elementary activation proof with both signs and absent source.
    assignments = 0
    for coefficients in product((-2, -1, 0, 1, 2), repeat=3):
        for selected in product((0, 1), repeat=3):
            for used in product((0, 1), repeat=3):
                if any(y > x for x, y in zip(selected, used)):
                    continue
                value = sum(c * y for c, y in zip(coefficients, used))
                upper = sum(max(c, 0) * x for c, x in zip(coefficients, selected))
                assert value <= upper
                assignments += 1
    return {'rook9_exact_exterior_rows': 4, 'rook9_all_six_coordinates_checked': True,
            'rook9_integer_positive_potentials_checked': checked,
            'signed_product_activation_controls': assignments,
            'solver_or_optimizer_called': False}


def prepare_data():
    assert digest(BASE_MODEL) == BASE_SHA
    assert digest(PROPOSAL) == PROPOSAL_SHA and digest(LP_MODEL) == LP_MODEL_SHA
    base = original.checked_model(BASE_MODEL)
    data = original.load(4)
    _, index, case, record, core, gram, _, _, _, masks = data
    assert original.domains.sha(canonical(record)) == base['domain_record_sha256']
    assert len(masks) == 1214 and len(core) == 35
    assert gram == [[12 * (i == j) + 2 - (core[i] & core[j]).bit_count() - (core[i] >> j & 1)
                    for j in range(35)] for i in range(35)]
    targets, neighbors = row_domains(core, masks, 14)
    point_file = json.loads(PROPOSAL.read_text())
    lp_model = json.loads(gzip.decompress(LP_MODEL.read_bytes()))
    assert point_file['model_sha256'] == LP_MODEL_SHA and point_file['case_index'] == 4
    assert lp_model['column_masks35'] == masks and lp_model['columns'] == record['columns']
    chosen = [v for v in point_file['variants'] if v['variant'] == VARIANT]
    assert len(chosen) == 1
    raw_point = chosen[0]['numerical_point']
    assert len(raw_point) == len(masks) and all(math.isfinite(v) and -1e-8 <= v <= 1 + 1e-8 for v in raw_point)
    assert chosen[0]['exact_feasibility_claimed'] is False
    point = [0.0 if v < 1e-9 else 1.0 if v > 1 - 1e-9 else float(v) for v in raw_point]
    selected_targets = sorted((a for a, x in enumerate(point) if x > 0), key=lambda a: (-point[a], a))[:32]
    assert len(selected_targets) == 32
    plan = []
    for a in selected_targets:
        plan.append({'target_column': a, 'original_signature_and_attachment': record['columns'][a],
                     'proposal_value': point[a], 'core_neighbors': masks[a].bit_count(),
                     'exterior_degree': targets[a][-1], 'row_coordinates': 36,
                     'possible_neighbor_columns': len(neighbors[a]),
                     'matrix_nonzeros': sum(masks[b].bit_count() + 1 for b in neighbors[a]),
                     'neighbors_with_positive_proposal_capacity': sum(point[b] > 0 for b in neighbors[a])})
    return {
        'status': 'exact complete case4 exterior-row domains and bounded discovery plan prepared; no query',
        'source_sha256': digest(Path(__file__)), 'original_source_hashes': base['source_hashes'],
        'base_model': portable(BASE_MODEL), 'base_model_sha256': BASE_SHA,
        'original_CNF_sha256': base['cnf_sha256'], 'case_index': 4, 'indexed_case': case,
        'complete_core_index_cases': len(index['cases']), 'domain_record_sha256': base['domain_record_sha256'],
        'columns': record['columns'], 'column_masks35': masks, 'core_adjacency_rows': core, 'Gram': gram,
        'row_targets36': targets, 'eligible_neighbor_column_ids': neighbors,
        'counts': {'columns': len(masks), 'candidate_unordered_pairs': len(masks) * (len(masks) - 1) // 2,
                   'eligible_unordered_edges': sum(map(len, neighbors)) // 2,
                   'directed_neighbor_entries': sum(map(len, neighbors)),
                   'neighbor_count_min': min(map(len, neighbors)), 'neighbor_count_max': max(map(len, neighbors)),
                   'column_weight_histogram': dict(sorted(Counter(mask.bit_count() for mask in masks).items())),
                   'exterior_degree_histogram': dict(sorted(Counter(t[-1] for t in targets).items())),
                   'pilot_targets': len(plan), 'proposal_positive_columns': sum(x > 0 for x in point),
                   'pilot_total_neighbor_variables': sum(row['possible_neighbor_columns'] for row in plan),
                   'pilot_total_matrix_nonzeros': sum(row['matrix_nonzeros'] for row in plan)},
        'proposal_file': portable(PROPOSAL), 'proposal_sha256': PROPOSAL_SHA,
        'proposal_model_sha256': LP_MODEL_SHA, 'proposal_variant': VARIANT,
        'proposal_value_rule': 'v<1e-9 becomes0; v>1-1e-9 becomes1; otherwise preserve the saved double',
        'proposal_ranking_rule': 'decreasing sanitized proposal value, then increasing zero-based column id',
        'proposal_values': point, 'exact_proposal_feasibility_claimed': False,
        'pilot_plan': plan,
        'planned_row_LP': {'matrix_columns': '(h_b,1) for every eligible b',
                           'equality_target': '(2*1-h_a-B*h_a,14-|h_a|)*proposal[a]',
                           'neighbor_lower_bound': 0, 'neighbor_upper_bound': 'proposal[b]',
                           'full_incidence_fixed': False, 'graph_symmetry_constraints': False},
        'universal_inequality': 'sum_b max(v dot (h_b,1),0)*x_b >= (v dot target_a)*x_a',
        'scope': 'Necessary actual-graph exterior-row inequalities for one indexed35-core. '
                 'They are not claimed consequences of the old Gram-only real cone.',
        'controls': controls(), 'optimizer_called': False, 'SAT_solver_called': False,
        'whole_case_or_local_set_excluded': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    started = time.monotonic()
    result = prepare_data()
    normalized = json.loads(canonical(result))
    if args.replay:
        assert json.loads(gzip.decompress(args.model.read_bytes())) == normalized
    else:
        assert not args.model.exists()
        args.model.write_bytes(gzip.compress(canonical(result) + b'\n', mtime=0))
    print(json.dumps({'status': result['status'], 'source_sha256': result['source_sha256'],
                      'model_sha256': digest(args.model), 'model_bytes': args.model.stat().st_size,
                      'counts': result['counts'], 'controls': result['controls'],
                      'pilot_plan': result['pilot_plan'], 'elapsed_seconds': time.monotonic() - started}, indent=2))
