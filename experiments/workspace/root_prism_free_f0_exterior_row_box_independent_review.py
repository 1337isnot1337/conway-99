"""Independent exact check of three row cuts and57 rational row boxes.

No subject builder, optimizer, or solver is imported. The complete480
signature domain, necessary edge domain, integer capacities, explicit
core relabelings and rational witness equations are checked directly.
"""

import argparse
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/root-prism-free'
SOURCE = ROOT / 'experiments/workspace/root_prism_free_f0_exterior_row_box_separation.py'
SOURCE_SHA = '60366da662c74ee8d3ca367dc532c16b652952101fa5725a3248fc5a53a773bd'
FILES = {
    'f0-exterior-row-domains02.json.gz':
        '665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4',
    'f0-exterior-row-box-separation-preparation.json.gz':
        '4ef94dc28a84fea3c236aac46ec7e5f2fa471cb6831014954bb0ba53b3fa43a0',
    'f0-exterior-row-box-separation-run01/result.json':
        '328fddcc22b7ee2bfdd2a5c93189cef12240a56eee5804073a0848e64e7a749f',
    'f0-exterior-row-cut-overlay-run01/result.json':
        '80daa535121c7c6c05b0b3ce90f65085b1e34236d8d53b143fe1e5ec01765bf3',
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def audit():
    assert sha(SOURCE.read_bytes()) == SOURCE_SHA
    saved = {}
    for name, expected in FILES.items():
        raw = (LOGS / name).read_bytes()
        assert sha(raw) == expected
        saved[name] = json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
    domain = saved['f0-exterior-row-domains02.json.gz']
    preparation = saved['f0-exterior-row-box-separation-preparation.json.gz']
    result = saved['f0-exterior-row-box-separation-run01/result.json']
    assert result['source_sha256'] == preparation['source_sha256'] == SOURCE_SHA
    core = domain['component_core_rows']
    A = [[core[3+i] >> (3+j) & 1 for j in range(18)] for i in range(18)]
    gram = [[12 * (i == j) + 2 - (core[3+i] & core[3+j]).bit_count() - A[i][j]
             for j in range(18)] for i in range(18)]
    triples = [list(h) for h in combinations(range(18), 3)
               if max(sum(v // 6 == f for v in h) for f in range(3)) <= 2
               and all(gram[i][j] > 0 for i, j in combinations(h, 2))
               and all(sum((i == j) + A[i][j] for j in h) <= 2 for i in range(18))]
    assert triples == domain['signature_domain'] and len(triples) == 480
    masks = [sum(1 << i for i in h) for h in triples]
    targets = [[2 - sum((i == j) + A[i][j] for j in h) for i in range(18)] for h in triples]
    assert targets == domain['row_targets'] and all(sum(t) == 24 and min(t) >= 0 for t in targets)
    neighbors = [[] for _ in triples]
    for a, b in combinations(range(480), 2):
        if (masks[a] & masks[b]).bit_count() <= 1 and all(targets[a][i] for i in triples[b]) \
                and all(targets[b][i] for i in triples[a]):
            neighbors[a].append(b)
            neighbors[b].append(a)
    assert neighbors == domain['possible_neighbor_signature_ids']
    assert sum(map(len, neighbors)) == 136788
    point = saved['f0-exterior-row-cut-overlay-run01/result.json']
    selected = point['incidence_candidate']['base_incidence_witness']['selected_columns']
    assert selected == sorted(set(selected)) and len(selected) == 60
    assert [[sum(i in triples[a] and j in triples[a] for a in selected) for j in range(18)]
            for i in range(18)] == gram
    assert all(not {a, b} <= set(selected) for a, b in domain['motif_pairs'])
    actions = preparation['verified_core_actions']
    assert len(actions) == 12
    positions = {tuple(h): a for a, h in enumerate(triples)}
    full_moves = []
    for action in actions:
        move = action['component_image']
        assert sorted(move) == list(range(18))
        full = tuple([move[6*i] // 6 for i in range(3)] + [j + 3 for j in move])
        assert sorted(full) == list(range(21))
        assert all((core[i] >> j & 1) == (core[full[i]] >> full[j] & 1) for i in range(21) for j in range(21))
        full_moves.append(full)
        assert action['signature_image'] == [positions[tuple(sorted(move[i] for i in h))] for h in triples]
    group = set(full_moves)
    assert len(group) == 12 and tuple(range(21)) in group
    assert all(tuple(g[h[i]] for i in range(21)) in group for g in group for h in group)
    assert [row['target'] for row in result['rows']] == selected
    obstructions, witnesses, clauses = [], [], set()
    for a, row in zip(selected, result['rows']):
        inside = sorted(set(neighbors[a]) & set(selected))
        if 'exact_obstruction' in row:
            record = row['exact_obstruction']
            vector = record['integer_vector']
            assert len(vector) == 18 and all(type(v) is int for v in vector)
            demand = sum(v * q for v, q in zip(vector, targets[a]))
            positive = [[b, sum(vector[i] for i in triples[b])] for b in neighbors[a]
                        if sum(vector[i] for i in triples[b]) > 0]
            capacity = sum(w for b, w in positive if b in selected)
            assert demand == record['integer_demand'] and capacity == record['selected_positive_capacity']
            assert demand > capacity >= 0 and demand - capacity == record['strict_integer_gap']
            assert positive == record['full_positive_weighted_terms']
            cover = [b for b, w in positive if b not in selected]
            assert record['cover_clause'] == [-a - 1] + [b + 1 for b in cover]
            transports = record['all12_verified_core_transports']
            assert len(transports) == 12
            for j, transport in enumerate(transports):
                assert transport['core_action_index'] == j
                action, move = actions[j]['signature_image'], actions[j]['component_image']
                target = action[a]
                moved = [0] * 18
                for i in range(18):
                    moved[move[i]] = vector[i]
                assert transport['target'] == target and transport['integer_vector'] == moved
                assert sum(v * q for v, q in zip(moved, targets[target])) == demand
                weighted = [[b, sum(moved[i] for i in triples[b])] for b in neighbors[target]
                            if sum(moved[i] for i in triples[b]) > 0]
                assert weighted == transport['positive_weighted_terms']
                moved_cover = sorted(action[b] for b in cover)
                assert transport['cover_clause'] == [-target - 1] + [b + 1 for b in moved_cover]
                remaining = sum(w for b, w in weighted if b not in moved_cover)
                assert remaining == transport['remaining_positive_capacity_if_clause_false'] == capacity < demand
                clauses.add(tuple(transport['cover_clause']))
            obstructions.append({'target': a, 'demand': demand, 'capacity': capacity,
                                 'gap': demand - capacity, 'positive_terms': len(positive),
                                 'base_cover_literals': len(cover) + 1})
        else:
            witness = row['exact_box_witness']
            den, nums = witness['denominator'], witness['numerators']
            assert type(den) is int and den > 0 and len(nums) == len(inside)
            assert witness['neighbor_signature_ids'] == inside
            assert all(type(n) is int and 0 <= n <= den for n in nums)
            assert [sum(n for b, n in zip(inside, nums) if i in triples[b]) for i in range(18)] \
                   == [den * q for q in targets[a]]
            assert sum(nums) == 8 * den
            binary = all(n in (0, den) for n in nums)
            support = [b for b, n in zip(inside, nums) if n]
            packing = binary and all((masks[a] & masks[b]).bit_count() <= 1 for a, b in combinations(support, 2))
            assert binary == witness['binary_neighbor_weights']
            assert packing == witness['binary_neighbor_pair_packing_checked_and_passed']
            witnesses.append({'target': a, 'denominator': den, 'binary': binary, 'packing': packing})
    assert len(obstructions) == 3 and len(witnesses) == 57
    assert [row['target'] for row in obstructions] == [110, 349, 479]
    assert len(clauses) == 36 and [list(c) for c in sorted(clauses)] == result['deduplicated_exact_cover_clauses']
    return {'status': 'independent integer capacities,36 actual core transports and57 exact rational row witnesses PASS',
            'source_sha256': sha(Path(__file__).read_bytes()), 'reviewed_source_sha256': SOURCE_SHA,
            'checked_input_hashes': FILES, 'complete_signatures': 480, 'complete_eligible_edges': 68394,
            'new60_column_design_Gram_entries_checked': 324, 'obstructions': obstructions,
            'core_relabelings_checked': 12, 'transported_cover_clauses_checked': 36,
            'rational_row_witnesses_checked': 57, 'rational_row_witness_metadata': witnesses,
            'cover_necessity': 'If the target is selected and the cover clause is false, every available '
                               'positive-weight signature lies outside the cover and has binary capacity1. '
                               'Their complete total capacity is strictly below the exact row demand.',
            'scope': 'Only necessary incidence restrictions and separate rational row boxes in component0. '
                     'No joint exterior graph, full component exclusion, or actual graph automorphism is assumed.',
            'subject_imported': False, 'optimizer_or_solver_called': False, 'CNF_or_proof_rebuilt': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = audit()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
