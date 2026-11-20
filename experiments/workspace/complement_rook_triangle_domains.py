"""Exact cheap domain and clause census for shared exterior triangles.

No large CNF is built and no solver is called. The prospective encoding
defines each allowed triangle as the conjunction of its three global
edges and enforces one triangle per selected core-disjoint edge.
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations, product
import json
from pathlib import Path

from pysat.card import CardEnc, EncType

import complement_rook_a_incidence as incidence
from two_rook_iso_completion import allowed_edges


ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def conjunction_control():
    # The octahedral graph has8 triangles and an edge partition into4 of
    # them. Implications T=>edges plus one selected T per edge admit that
    # partition, although every actual edge lies in two graph triangles.
    parts = ((0, 1), (2, 3), (4, 5))
    triangles = list(product(*parts))
    edges = {tuple(sorted(edge)) for triangle in triangles for edge in combinations(triangle, 2)}
    chosen = [triangle for triangle in triangles if sum(v % 2 for v in triangle) % 2 == 0]
    assert len(edges) == 12 and len(triangles) == 8 and len(chosen) == 4
    assert all(sum(set(edge) <= set(triangle) for triangle in triangles) == 2 for edge in edges)
    assert all(sum(set(edge) <= set(triangle) for triangle in chosen) == 1 for edge in edges)
    assert any(triangle not in chosen for triangle in triangles)
    return {'status': 'exact octahedral counterexample to omitted reverse implication',
            'vertices': 6, 'edges': 12, 'actual_triangles': 8,
            'selected_edge_partition_triangles': 4, 'reverse_implication_is_required': True}


def census(output):
    base_path = ROOT/'experiments/logs/grids-and-triangles/two-rook-tip-boundary-joint-3943553752-model.json'
    base = json.loads(base_path.read_text())
    rows, G, triples, signatures, _, _ = incidence.domain()
    needs = [[2-sum(((rows[i] >> j) & 1)+int(i == j) for j in sites)
              for i in range(27)]+[11] for sites in signatures]
    edges = allowed_edges(signatures, needs)
    assert len(signatures) == 252 and len(edges) == 20934
    domain = {'core_rows': rows, 'gram': G, 'signatures': signatures, 'mixed_need': needs,
              'edge_variables': [[v, w, 253+i] for i, (v, w) in enumerate(edges)]}
    domain_sha = hashlib.sha256(json.dumps(domain, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert domain_sha == base['domain_sha256']
    masks = [sum(1 << i for i in sites) for sites in signatures]
    adjacency = [0]*252
    edge_index = [[-1]*252 for _ in range(252)]
    overlaps = [[0]*252 for _ in range(252)]
    zero_edges = []
    for ei, (v, w) in enumerate(edges):
        adjacency[v] |= 1 << w
        adjacency[w] |= 1 << v
        edge_index[v][w] = edge_index[w][v] = ei
        shared = masks[v] & masks[w]
        assert shared.bit_count() <= 1
        overlaps[v][w] = overlaps[w][v] = shared
        if not shared:
            zero_edges.append(ei)
    degree = [0]*len(edges)
    triangle_count = 0
    allowed = forbidden = direct_redundant = 0
    shared_count_histogram = Counter()
    direct_histogram = Counter()
    allowed_hash = hashlib.sha256()
    forbidden_hash = hashlib.sha256()
    examples = {}
    for v, w in edges:
        common = adjacency[v] & adjacency[w]
        common &= ~((1 << (w+1))-1)
        while common:
            bit = common & -common
            common -= bit
            u = bit.bit_length()-1
            triangle_count += 1
            shared = (overlaps[v][w], overlaps[v][u], overlaps[w][u])
            count = sum(bool(mask) for mask in shared)
            shared_count_histogram[count] += 1
            if count == 0:
                allowed += 1
                allowed_hash.update(f'{v},{w},{u}\n'.encode())
                for a, b in ((v, w), (v, u), (w, u)):
                    degree[edge_index[a][b]] += 1
                continue
            forbidden += 1
            forbidden_hash.update(f'{v},{w},{u}\n'.encode())
            witnesses = []
            for mask, third in zip(shared, (u, w, v)):
                if mask:
                    core_point = mask.bit_length()-1
                    assert needs[third][core_point] in (1, 2)
                    if needs[third][core_point] == 1:
                        witnesses.append([third, core_point])
            direct_histogram[bool(witnesses)] += 1
            if witnesses:
                direct_redundant += 1
                examples.setdefault('direct_mixed_redundancy', {
                    'signature_indices': [v, w, u], 'coordinate_triples': [triples[s] for s in (v, w, u)],
                    'mixed_row_witnesses': witnesses})
            else:
                examples.setdefault('no_direct_two_edge_mixed_obstruction', {
                    'signature_indices': [v, w, u], 'coordinate_triples': [triples[s] for s in (v, w, u)]})
    assert allowed == 209952
    assert triangle_count == allowed+forbidden
    assert sum(degree) == 3*allowed
    assert len(zero_edges) == 14652 and len(edges)-len(zero_edges) == 6282
    degrees = Counter(degree[ei] for ei in zero_edges)
    zero_edge_set = set(zero_edges)
    assert all(degree[ei] == 0 for ei, edge in enumerate(edges) if ei not in zero_edge_set)
    atmost_clauses = atmost_auxiliaries = 0
    controls = []
    for n, multiplicity in sorted(degrees.items()):
        expected_aux = 0 if n <= 2 else n-1
        expected_clauses = 0 if n <= 1 else 1 if n == 2 else 3*n-4
        if n:
            encoded = CardEnc.atmost(list(range(1, n+1)), 1, encoding=EncType.seqcounter)
            actual_aux = max(0, encoded.nv-n)
            assert actual_aux == expected_aux and len(encoded.clauses) == expected_clauses
        atmost_auxiliaries += multiplicity*expected_aux
        atmost_clauses += multiplicity*expected_clauses
        controls.append({'input_length': n, 'occurrences': multiplicity,
                         'auxiliaries': expected_aux, 'clauses': expected_clauses})
    addition = {'triangle_variables': allowed, 'triangle_conjunction_clauses': 4*allowed,
                'zero_overlap_edge_atleast_clauses': len(zero_edges),
                'zero_overlap_edge_atmost_clauses': atmost_clauses,
                'zero_overlap_edge_atmost_auxiliaries': atmost_auxiliaries,
                'all_forbidden_triangle_clauses': forbidden,
                'forbidden_triangles_already_excluded_by_one_mixed_row': direct_redundant,
                'forbidden_triangles_without_that_direct_redundancy': forbidden-direct_redundant}
    common_clauses = 4*allowed+len(zero_edges)+atmost_clauses
    result = {
        'status': 'exact triangle domain and prospective clause census; no solver or large CNF',
        'source_sha256': digest(Path(__file__)), 'base_manifest_sha256': digest(base_path),
        'base_domain_sha256': domain_sha, 'candidate_signatures': 252,
        'eligible_edges': len(edges), 'overlap_zero_edges': len(zero_edges),
        'overlap_one_edges': len(edges)-len(zero_edges),
        'all_eligible_graph_triangles': triangle_count, 'allowed_disjoint_triangles': allowed,
        'forbidden_overlap_triangles': forbidden,
        'triangles_by_number_of_overlap_one_edges': [[k, v] for k, v in sorted(shared_count_histogram.items())],
        'allowed_triangle_domain_sha256': allowed_hash.hexdigest(),
        'forbidden_triangle_domain_sha256': forbidden_hash.hexdigest(),
        'triangle_counts_per_zero_overlap_edge': [[n, count] for n, count in sorted(degrees.items())],
        'addition': addition,
        'prospective_full_model_variables': base['variables']+allowed+atmost_auxiliaries,
        'prospective_full_model_clauses_all_forbidden': base['clauses']+common_clauses+forbidden,
        'prospective_full_model_clauses_omit_direct_redundancies': base['clauses']+common_clauses+forbidden-direct_redundant,
        'split_case_additional_units': 2, 'small_counter_size_controls': controls,
        'conjunction_control': conjunction_control(), 'examples': examples,
        'scope': 'necessary adjacent-exterior-pair equations; nonadjacent exterior common-neighbor caps remain absent',
    }
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    census(args.output)
