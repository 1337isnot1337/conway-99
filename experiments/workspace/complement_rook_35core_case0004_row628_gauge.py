"""Exact11-coordinate presentation of the frozen target628 row cut."""

import argparse
import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/grids-and-triangles'
MODEL = LOGS / 'complement-rook-35core-case0004-exterior-rows.json.gz'
RESULT = LOGS / 'complement-rook-35core-case0004-row-separation-run01.json'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def calculate():
    assert sha(MODEL) == '10377b5494b8d39e3b41f400b39af485c1db44d06232e1c03663a07f530e8628'
    assert sha(RESULT) == 'e758fffa8bbeb80f0fc2edd3bdb9b9fc8b992a27303679df9d9658f0c9aa18f3'
    model = json.loads(gzip.decompress(MODEL.read_bytes()))
    result = json.loads(RESULT.read_text())
    cut = next(row['integer_certificate'] for row in result['rows'] if row['target_column'] == 628)
    old = cut['integer_vector']
    q = model['row_targets36'][628]
    masks = model['column_masks35']
    neighbors = model['eligible_neighbor_column_ids'][628]
    assert all((mask & 511).bit_count() == 1 for mask in masks)
    assert sum(q[:9]) == q[-1]
    new = [old[i] - int(i < 9) for i in range(35)] + [old[-1] + 1]
    zeros = [i for i in range(35) if q[i] == 0]
    assert all(not (masks[b] >> i & 1) for b in neighbors for i in zeros)
    for i in zeros:
        new[i] = 0
    expected = [(6,-2),(7,1),(9,-1),(12,-2),(13,2),(14,-1),
                (17,-2),(19,1),(20,2),(27,2),(32,1)]
    assert [(i, v) for i, v in enumerate(new) if v] == expected
    assert new[-1] == 0
    assert sum(v * t for v, t in zip(new, q)) == cut['positive_demand'] == 2
    products = [[b, new[-1] + sum(new[i] for i in range(35) if masks[b] >> i & 1)] for b in neighbors]
    assert products == cut['all_eligible_neighbor_products']
    positive = [[b, value] for b, value in products if value > 0]
    assert positive == cut['positive_terms'] and len(positive) == 96
    return {'status': 'exact equivalent11-coordinate target628 potential replay PASS',
            'source_sha256': sha(Path(__file__)), 'model_sha256': sha(MODEL), 'result_sha256': sha(RESULT),
            'target': 628, 'old_potential': old, 'new_potential': new,
            'nonzero_core_coordinates': expected, 'degree_coordinate': 0,
            'zero_quota_coordinates': zeros, 'right_hand_side': 2,
            'eligible_neighbors_checked': len(neighbors), 'positive_coefficients_unchanged': len(positive),
            'identity': 'Subtract1 from all nine R potentials and add1 to the degree potential; '
                        'then zero positions whose quota is0. All eligible columns and the row target '
                        'annihilate these changes.',
            'new_cut_claimed': False, 'optimizer_or_solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    value = calculate()
    args.output.write_text(json.dumps(value, indent=2) + '\n')
    print(json.dumps(value, indent=2))
