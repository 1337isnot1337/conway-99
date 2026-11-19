"""Exact universal selector cut from the fixed shared-edge Farkas ray.

This standard-library verifier reconstructs all480 signatures and68394
eligible edges, independently checks the fixed symmetric LP ray, and
extends its nine supported row potentials by zero. Every positive edge
weight is allocated to one of its endpoint selectors. The saved design
chooses that allocation only; it is not assumed in the resulting cut.
"""

import argparse
from collections import Counter
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
    'f0-incidence-row-loop-run01/iteration00/candidate.json': '9e38e41273ad247021854236a56a4e9dd0cdc74b7156867904b7d19fe2d64e46',
    'f0-row-box-design-exterior-model.json.gz': '1a75d60173991252b55892a911a5470e4e5074992916ead7ffc8d9df0c298b79',
    'f0-row-box-design-linear-run01.json': '96486063f18150392852eeddd55e7e023b4987e0b2233d3fd133c88168de29f9',
    'f0-row-box-design-linear-run01-replay.json': 'b73b97d938ec9cbc5754d09361eccd7967f68da063d199eb183c2462953ad393'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def global_domain(saved):
    core = saved['component_core_rows']
    assert len(core) == 21 and all(not (core[i] >> i & 1) for i in range(21))
    assert all((core[i] >> j & 1) == (core[j] >> i & 1) for i in range(21) for j in range(21))
    adjacency = [(row >> 3)&((1 << 18)-1) for row in core[3:]]
    gram = [[12*int(i == j)+2-(core[3+i]&core[3+j]).bit_count()-(core[3+i] >> (3+j) & 1)
             for j in range(18)] for i in range(18)]
    signatures = []
    for h in combinations(range(18), 3):
        if max(sum(i//6 == f for i in h) for f in range(3)) > 2:
            continue
        if any(gram[i][j] == 0 for i, j in combinations(h, 2)):
            continue
        if any(sum(int(i == j or adjacency[i] >> j & 1) for j in h) > 2 for i in range(18)):
            continue
        signatures.append(list(h))
    assert signatures == saved['signature_domain'] and len(signatures) == 480
    targets = [[2-int(i in h)-sum(adjacency[i] >> j & 1 for j in h) for i in range(18)] for h in signatures]
    assert targets == saved['row_targets']
    masks = [sum(1 << i for i in h) for h in signatures]
    edges, neighbors = [], [[] for _ in range(480)]
    for a, b in combinations(range(480), 2):
        if (masks[a]&masks[b]).bit_count() > 1:
            continue
        if any(targets[a][i] == 0 for i in signatures[b]) or any(targets[b][i] == 0 for i in signatures[a]):
            continue
        edges.append([a, b])
        neighbors[a].append(b); neighbors[b].append(a)
    assert len(edges) == 68394 and neighbors == saved['possible_neighbor_signature_ids']
    return core, signatures, targets, gram, edges


def allocate(signatures, targets, edges, potentials, support, inverse_order=None):
    n = len(signatures)
    assert len(targets) == len(potentials) == n
    assert all(not any(potentials[a]) for a in range(n) if a not in support)
    order = list(range(n)) if inverse_order is None else inverse_order
    assert sorted(order) == list(range(n))
    delta = [sum(x*y for x, y in zip(v, q)) for v, q in zip(potentials, targets)]
    coefficients, positive = list(delta), []
    for a, b in edges:
        weight = sum(potentials[a][i] for i in signatures[b])+sum(potentials[b][i] for i in signatures[a])
        if weight <= 0:
            continue
        assert a in support or b in support
        if a in support and b in support:
            endpoint = min((a, b), key=lambda x: order[x])
            kind = 'internal'
        else:
            endpoint = b if a in support else a
            kind = 'boundary'
        assert endpoint in (a, b)
        coefficients[endpoint] -= weight
        positive.append({'edge': [a, b], 'weight': weight, 'allocated_endpoint': endpoint, 'kind': kind})
    return delta, coefficients, positive


def controls():
    checked = 0
    for edge_set in ([[0, 1], [1, 2]], [[0, 1], [0, 2], [1, 2]]):
        signatures, targets = [[0]]*3, [[1]]*3
        for support_bits in product((0, 1), repeat=3):
            support = {i for i, value in enumerate(support_bits) if value}
            for vector in product((-1, 0, 1), repeat=3):
                if any(vector[i] for i in range(3) if i not in support):
                    continue
                _, coefficients, _ = allocate(signatures, targets, edge_set,
                                               [[value] for value in vector], support)
                for z in product((0, 1), repeat=3):
                    for y in product((0, 1), repeat=len(edge_set)):
                        if any(value > min(z[a], z[b]) for (a, b), value in zip(edge_set, y)):
                            continue
                        degrees = [sum(value for edge, value in zip(edge_set, y) if a in edge) for a in range(3)]
                        if degrees != list(z):
                            continue
                        assert sum(c*value for c, value in zip(coefficients, z)) <= 0
                        checked += 1
    _, c, positive = allocate([[0]]*3, [[1]]*3, [[0, 1], [1, 2]], [[1], [-1], [1]], {0, 1, 2})
    assert c == [1, -1, 1] and not positive and sum(c) == 1
    return {'exhaustive_small_activated_edge_assignments_checked': checked,
            'three_vertex_path_separate_rows_but_shared_contradiction': True,
            'path_selector_cut': [1, -1, 1], 'optimizer_or_solver_called': False}


def calculate():
    loaded = {}
    for name, expected in INPUTS.items():
        path = LOGS/name
        assert digest(path) == expected
        loaded[name] = read(path)
    saved = loaded['f0-exterior-row-domains02.json.gz']
    core, signatures, targets, gram, global_edges = global_domain(saved)
    candidate = loaded['f0-incidence-row-loop-run01/iteration00/candidate.json']
    selected = candidate['selected_signature_ids']
    support = set(selected)
    assert selected == sorted(support) and len(selected) == 60
    assert [[sum(i in signatures[a] and j in signatures[a] for a in selected) for j in range(18)] for i in range(18)] == gram
    fixed = loaded['f0-row-box-design-exterior-model.json.gz']
    assert fixed['data']['design_source_indices'] == selected
    fixed_edges = [[u, v] for u in range(60) for v in range(u)
                   if selected[v] in saved['possible_neighbor_signature_ids'][selected[u]]]
    assert fixed_edges == fixed['data']['edge_domain'] and len(fixed_edges) == 1220
    incident = [[] for _ in range(60)]
    for e, (a, b) in enumerate(fixed_edges):
        incident[a].append((b, e)); incident[b].append((a, e))
    rows = []
    for a in range(60):
        rows.append({'kind': 'degree', 'vertex': a, 'support': sorted(e for _, e in incident[a]), 'rhs': 8})
        for i in range(18):
            rows.append({'kind': 'mixed', 'vertex': a, 'core_vertex': i,
                         'support': sorted(e for b, e in incident[a] if i in signatures[selected[b]]),
                         'rhs': targets[selected[a]][i]})
    assert rows == fixed['linear_rows'] and len(rows) == 1140
    result = loaded['f0-row-box-design-linear-run01.json']
    assert result['exact_fixed_design_infeasibility'] and not result['exact_linear_feasibility']
    assert loaded['f0-row-box-design-linear-run01-replay.json']['exact_fixed_design_infeasibility']
    ray = result['integer_ray']
    assert len(ray) == 2360 and all(type(value) is int for value in ray)
    upper = ray[1140:]
    assert min(upper) >= 0
    columns = list(upper)
    for row, value in zip(rows, ray[:1140]):
        for e in row['support']:
            columns[e] += value
    rhs = sum(row['rhs']*value for row, value in zip(rows, ray[:1140]))+sum(upper)
    assert min(columns) >= 0 and rhs == -2
    potentials = [[0]*18 for _ in range(480)]
    for row, value in zip(rows, ray[:1140]):
        a = selected[row['vertex']]
        if row['kind'] == 'degree':
            for i in range(18):
                potentials[a][i] -= value
        else:
            potentials[a][row['core_vertex']] -= 3*value
    assert [potentials[a] for a in selected] == result['fixed_capacity_potentials']['integer_potentials60_by18']
    delta, coefficients, positive = allocate(signatures, targets, global_edges, potentials, support)
    demand = sum(delta[a] for a in selected)
    internal = sum(edge['weight'] for edge in positive if edge['kind'] == 'internal')
    assert (demand, internal, demand-internal) == (15, 9, 6)
    assert sum(coefficients[a] for a in selected) == 6
    divisor = gcd(*(abs(value) for value in coefficients))
    assert divisor == 3
    normalized = [value//divisor for value in coefficients]
    assert sum(value > 0 for value in normalized) == 5 and sum(value < 0 for value in normalized) == 163
    identity = tuple(range(21))
    group, frontier = {identity}, [identity]
    while frontier:
        old = frontier.pop()
        for generator in saved['core_generators']:
            image = tuple(generator[old[i]] for i in range(21))
            assert sorted(image) == list(range(21)) and set(image[:3]) == set(range(3))
            assert all((core[i] >> j & 1) == (core[image[i]] >> image[j] & 1) for i in range(21) for j in range(21))
            if image not in group:
                group.add(image); frontier.append(image)
    assert len(group) == 12
    positions = {tuple(h): a for a, h in enumerate(signatures)}
    edge_set = {tuple(edge) for edge in global_edges}
    transports = []
    for index, image in enumerate(sorted(group)):
        move = [image[i+3]-3 for i in range(18)]
        action = [positions[tuple(sorted(move[i] for i in h))] for h in signatures]
        inverse = [0]*480
        for a, b in enumerate(action):
            inverse[b] = a
        assert sorted(action) == list(range(480))
        assert {tuple(sorted((action[a], action[b]))) for a, b in global_edges} == edge_set
        assert all(targets[action[a]][move[i]] == targets[a][i] for a in range(480) for i in range(18))
        moved = [[0]*18 for _ in range(480)]
        for a in range(480):
            for i, value in enumerate(potentials[a]):
                moved[action[a]][move[i]] = value
        moved_support = {action[a] for a in selected}
        moved_delta, moved_coefficients, moved_positive = allocate(signatures, targets, global_edges,
                                                                  moved, moved_support, inverse)
        assert all(moved_coefficients[action[a]] == coefficients[a] for a in range(480))
        assert all(moved_delta[action[a]] == delta[a] for a in range(480))
        transported_edges = sorted((min(action[e['edge'][0]], action[e['edge'][1]]),
                                    max(action[e['edge'][0]], action[e['edge'][1]]),
                                    e['weight'], action[e['allocated_endpoint']]) for e in positive)
        assert transported_edges == sorted((*e['edge'], e['weight'], e['allocated_endpoint']) for e in moved_positive)
        c = [value//divisor for value in moved_coefficients]
        assert sum(c[a] for a in moved_support) == 2
        transports.append({'core_action_index': index, 'component_image': move, 'signature_image': action,
            'positive_terms': [[a, value] for a, value in enumerate(c) if value > 0],
            'negative_side_positive_weights': [[a, -value] for a, value in enumerate(c) if value < 0],
            'transported_saved_selection_value': 2, 'original_saved_selection_value': sum(c[a] for a in selected),
            'normalized_coefficients_sha256': hashlib.sha256(canonical(c)).hexdigest(),
            'complete_global_edge_allocation_recomputed': True})
    assert len({record['normalized_coefficients_sha256'] for record in transports}) == 12
    return {'status': 'complete global shared-row selector inequality and twelve transports exactly verified',
        'source_sha256': digest(Path(__file__)), 'input_hashes': INPUTS,
        'scope': 'all480 free first-incidence selectors for component0 in globallyP=F=0 split18+18',
        'saved_selection_is_not_a_hypothesis_of_the_cut': True,
        'complete_signatures': 480, 'complete_eligible_undirected_edges': 68394,
        'signature_domain_sha256': hashlib.sha256(canonical(signatures)).hexdigest(),
        'edge_domain_sha256': hashlib.sha256(canonical(global_edges)).hexdigest(),
        'fixed_LP_ray_check': {'equations': 1140, 'upper_slacks': 1220, 'all_coefficients_checked': 2440,
                               'rhs_dot_product': rhs, 'nonzero_multipliers': sum(value != 0 for value in ray)},
        'selected_signature_ids_for_potential_support_and_allocation_only': selected,
        'nonzero_target_potentials': [[a, vector] for a, vector in enumerate(potentials) if any(vector)],
        'nonzero_target_demands': [[a, value] for a, value in enumerate(delta) if value],
        'positive_edge_allocation': positive, 'positive_edge_type_counts': dict(Counter(e['kind'] for e in positive)),
        'saved_total_demand': demand, 'saved_internal_positive_capacity': internal, 'raw_gap': demand-internal,
        'coefficient_gcd': divisor, 'normalized_saved_gap': 2,
        'positive_terms': [[a, value] for a, value in enumerate(normalized) if value > 0],
        'negative_side_positive_weights': [[a, -value] for a, value in enumerate(normalized) if value < 0],
        'normalized_coefficient_histogram': {str(value): count for value, count in sorted(Counter(normalized).items())},
        'transported_cuts': transports, 'controls': controls(),
        'SAT_formula_mutated': False, 'optimizer_or_solver_called': False,
        'whole_component_excluded': False, 'full_graph_constructed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=['generate', 'replay'])
    parser.add_argument('--certificate', type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    result = calculate()
    if args.command == 'generate':
        assert not args.certificate.exists()
        args.certificate.write_bytes(gzip.compress(canonical(result)+b'\n', mtime=0))
    else:
        assert canonical(read(args.certificate)) == canonical(result)
    print(json.dumps({'status': result['status'], 'source_sha256': result['source_sha256'],
        'certificate_sha256': digest(args.certificate), 'complete_edges': result['complete_eligible_undirected_edges'],
        'supported_targets': len(result['nonzero_target_potentials']),
        'positive_terms': result['positive_terms'], 'negative_terms': len(result['negative_side_positive_weights']),
        'saved_gap': result['normalized_saved_gap'], 'transported_cuts': len(result['transported_cuts']),
        'controls': result['controls'], 'seconds': time.monotonic()-started}, indent=2), flush=True)
