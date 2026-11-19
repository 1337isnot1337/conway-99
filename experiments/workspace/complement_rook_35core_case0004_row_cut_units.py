"""Two-coordinate exact proofs of the two already encoded case4 units.

This standard-library check rebuilds every target and the complete
eligible neighbor lists for columns1080/1081. It proves the same two
absent-column conclusions as cuts34/35, without changing those cuts.
"""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/grids-and-triangles'
DOMAIN = LOGS / 'complement-rook-35core-case0004-exterior-rows.json.gz'
DOMAIN_SHA = '10377b5494b8d39e3b41f400b39af485c1db44d06232e1c03663a07f530e8628'
CUTS = LOGS / 'complement-rook-35core-case0004-row-loop-run01.json'
CUTS_SHA = '9b0713b668e2c0ae47139007cdf6ad8961be2fb0e9caf2b42e0193a5528ecaa6'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calculate():
    assert digest(DOMAIN) == DOMAIN_SHA and digest(CUTS) == CUTS_SHA
    model = json.loads(gzip.decompress(DOMAIN.read_bytes()))
    cuts = json.loads(CUTS.read_text())['exact_cuts']
    core, masks = model['core_adjacency_rows'], model['column_masks35']
    assert len(core) == 35 and len(masks) == 1214
    targets = [[2-int(mask >> i & 1)-(core[i] & mask).bit_count() for i in range(35)]
               + [14-mask.bit_count()] for mask in masks]
    assert targets == model['row_targets36']
    zeros = [sum(1 << i for i, quota in enumerate(row[:35]) if quota == 0)
             for row in targets]
    certificates = []
    for index, a in ((34, 1080), (35, 1081)):
        old = cuts[index]
        assert old['target_column'] == a and not old['positive_terms']
        eligible = [b for b in range(1214) if b != a
                    and (masks[a] & masks[b]).bit_count() <= 1
                    and not masks[b] & zeros[a] and not masks[a] & zeros[b]]
        assert eligible == model['eligible_neighbor_column_ids'][a]
        products = [int(masks[b] >> 3 & 1)-int(masks[b] >> 10 & 1) for b in eligible]
        assert products and max(products) <= 0
        assert targets[a][3] == 2 and targets[a][10] == 1
        v = old['integer_vector']
        assert len(v) == 36 and all(type(value) is int for value in v)
        assert sum(x*y for x, y in zip(v, targets[a])) == old['positive_demand'] == 2
        assert max(v[-1]+sum(v[i] for i in range(35) if masks[b] >> i & 1)
                   for b in eligible) <= 0
        left = [b for b in eligible if masks[b] >> 3 & 1]
        right = [b for b in eligible if masks[b] >> 10 & 1]
        assert set(left) <= set(right)
        certificates.append({
            'old_cut_index': index, 'zero_based_column': a,
            'DIMACS_forbidding_unit': [-a-1],
            'old_signature_and_attachment': model['columns'][a],
            'core_neighbors': [i for i in range(35) if masks[a] >> i & 1],
            'new_sparse_integer_potential': [[3, 1], [10, -1]],
            'degree_coordinate': 0, 'positive_demand': 1,
            'all1214_candidate_neighbors_tested': True,
            'eligible_neighbor_count': len(eligible),
            'R3_neighbor_column_support': left, 'S1_neighbor_column_support': right,
            'support_inclusion_checked': True,
            'R3_demand': 2, 'S1_demand': 1,
            'complete_neighbor_product_histogram': dict(sorted(Counter(products).items())),
            'old_frozen_integer_certificate_also_rechecked': True,
        })
    return {
        'status': 'PASS: both existing absent-column units have exact two-coordinate proofs',
        'source_sha256': digest(Path(__file__)), 'row_domain_sha256': DOMAIN_SHA,
        'original60_cut_result_sha256': CUTS_SHA,
        'all_reconstructed_targets': len(targets), 'certificates': certificates,
        'mathematical_reason': 'Every eligible exterior neighbor meeting R3 also meets S1, but the chosen source would require two R3 neighbors and only one S1 neighbor.',
        'new_selector_exclusions_beyond_the_frozen60_cuts': 0,
        'case4_or_local_set_excluded': False, 'optimizer_or_solver_called': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = calculate()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)
