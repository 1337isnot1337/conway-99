"""Direct integer audit of the terminal60-column point and60 row boxes."""

import argparse
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/root-prism-free'
INPUTS = {
    'f0-exterior-row-domains02.json.gz': '665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4',
    'f0-incidence-row-loop-run01/iteration00/candidate.json': '9e38e41273ad247021854236a56a4e9dd0cdc74b7156867904b7d19fe2d64e46',
    'f0-incidence-row-loop-run01/iteration00/rows.json': 'dfaee7888eccfa0f673212e054e9824f4aac9256e745a282574ef758b7e79519',
}


def audit():
    loaded = {}
    for name, expected in INPUTS.items():
        raw = (LOGS / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == expected
        loaded[name] = json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
    domain = loaded['f0-exterior-row-domains02.json.gz']
    candidate = loaded['f0-incidence-row-loop-run01/iteration00/candidate.json']
    rows = loaded['f0-incidence-row-loop-run01/iteration00/rows.json']
    core = domain['component_core_rows']
    A = [[core[i+3] >> (j+3) & 1 for j in range(18)] for i in range(18)]
    G = [[12 * (i == j) + 2 - A[i][j] - (core[i+3] & core[j+3]).bit_count()
          for j in range(18)] for i in range(18)]
    triples = [list(h) for h in combinations(range(18), 3)
               if max(sum(i // 6 == f for i in h) for f in range(3)) <= 2
               and all(G[i][j] > 0 for i, j in combinations(h, 2))
               and all(sum((i == j) + A[i][j] for j in h) <= 2 for i in range(18))]
    assert triples == domain['signature_domain'] and len(triples) == 480
    targets = [[2 - sum((i == j) + A[i][j] for j in h) for i in range(18)] for h in triples]
    assert targets == domain['row_targets']
    masks = [sum(1 << i for i in h) for h in triples]
    selected = candidate['selected_signature_ids']
    assert selected == sorted(set(selected)) and len(selected) == 60
    assert [[sum(i in triples[a] and j in triples[a] for a in selected) for j in range(18)]
            for i in range(18)] == G
    assert all(not {a, b} <= set(selected) for a, b in domain['motif_pairs'])
    assert rows['selected_signature_ids'] == selected and [r['target'] for r in rows['rows']] == selected
    denominators, binary_count, packing_count = [], 0, 0
    for a, row in zip(selected, rows['rows']):
        assert row['status'] == 'EXACT RATIONAL BOX ROW WITNESS'
        assert 'exact_obstruction' not in row
        eligible = [b for b in range(480) if b != a and (masks[a] & masks[b]).bit_count() <= 1
                    and all(targets[a][i] for i in triples[b]) and all(targets[b][i] for i in triples[a])]
        assert eligible == domain['possible_neighbor_signature_ids'][a]
        inside = sorted(set(eligible) & set(selected))
        witness = row['exact_box_witness']
        den, nums = witness['denominator'], witness['numerators']
        assert type(den) is int and den > 0 and len(nums) == len(inside)
        assert witness['neighbor_signature_ids'] == inside
        assert all(type(n) is int and 0 <= n <= den for n in nums)
        assert [sum(n for b, n in zip(inside, nums) if i in triples[b]) for i in range(18)] == [den*q for q in targets[a]]
        assert sum(nums) == 8 * den
        binary = all(n in (0, den) for n in nums)
        support = [b for b, n in zip(inside, nums) if n]
        packing = binary and all((masks[b] & masks[c]).bit_count() <= 1 for b, c in combinations(support, 2))
        assert witness['binary_neighbor_weights'] == binary
        assert witness['binary_neighbor_pair_packing_checked_and_passed'] == packing
        denominators.append(den); binary_count += binary; packing_count += packing
    assert len(denominators) == 60
    return {'status': 'independent exact terminal incidence and all60 rational row boxes PASS',
            'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'input_hashes': INPUTS, 'complete_signature_domain': 480, 'selected_columns': 60,
            'Gram_entries_checked': 324, 'motif_pairs_checked': len(domain['motif_pairs']),
            'complete_selected_target_neighbor_domains_checked': 60, 'exact_box_witnesses_checked': 60,
            'mixed_equations_checked': 1080, 'degree_sums_checked': 60,
            'maximum_witness_denominator': max(denominators), 'binary_boxes': binary_count,
            'binary_boxes_passing_pair_packing': packing_count,
            'single_row_box_potential_family_has_no_separator_for_this_selection': True,
            'shared_edges_or_complete_graph_verified': False, 'weighted_CNF_or_proof_replayed': False,
            'optimizer_or_solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = audit()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2))
