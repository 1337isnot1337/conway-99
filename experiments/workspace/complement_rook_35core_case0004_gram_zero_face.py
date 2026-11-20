"""A three-row nonnegative Gram certificate forcing 46 case4 columns zero.

The complete frozen attachment domain is an input. This verifier imports no
model builder, propagator, solver, optimizer or linear-algebra package.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/grids-and-triangles'
INPUTS = {
    'domain': ('experiments/logs/grids-and-triangles/complement-rook-35core-case0004-exterior-rows.json.gz',
               '10377b5494b8d39e3b41f400b39af485c1db44d06232e1c03663a07f530e8628'),
    'native_model': ('experiments/logs/grids-and-triangles/complement-rook-35core-case0004-native-cpsat-model.json',
                     'a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476'),
}
OLD_ABSENT = [352, 353, 354, 355, 439, 552, 553, 645, 869, 873, 957, 1080, 1081, 1167]
ROW_COMBINATION = [[3, 27, 1], [4, 27, 1], [17, 27, -1]]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def derive():
    loaded = {}
    for key, (name, expected) in INPUTS.items():
        path = ROOT / name
        assert digest(path) == expected
        raw = path.read_bytes()
        loaded[key] = json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)
    domain = loaded['domain']
    B = domain['core_adjacency_rows']
    masks = domain['column_masks35']
    assert len(B) == 35 and len(masks) == 1214 and len(set(masks)) == 1214
    assert all(type(x) is int and 0 <= x < 1 << 35 for x in B + masks)
    assert all(not (B[i] >> i & 1) for i in range(35))
    assert all((B[i] >> j & 1) == (B[j] >> i & 1) for i in range(35) for j in range(35))
    rows = loaded['native_model']['primary_inventory']['Gram_rows']
    row_index = {tuple(row[:2]): k for k, row in enumerate(rows)}
    assert len(rows) == len(row_index) == 630
    coefficients = [0] * len(masks)
    rhs = 0
    used_rows = []
    for i, j, multiplier in ROW_COMBINATION:
        assert i < j and multiplier in (-1, 1)
        quota = 2 - (B[i] >> j & 1) - (B[i] & B[j]).bit_count()
        support = [a for a, h in enumerate(masks) if (h >> i & 1) and (h >> j & 1)]
        index = row_index[(i, j)]
        assert rows[index] == [i, j, quota, support]
        for a in support:
            coefficients[a] += multiplier
        rhs += multiplier * quota
        used_rows.append({'core_pair': [i, j], 'multiplier': multiplier,
                         'quota': quota, 'native_Gram_row_index': index, 'support': support})
    assert rhs == 0 and min(coefficients) >= 0
    forced = [a for a, coefficient in enumerate(coefficients) if coefficient > 0]
    assert len(forced) == 46 and coefficients[359] == 1
    assert set(coefficients) == {0, 1}
    assert set(used_rows[2]['support']) <= set(used_rows[0]['support']) | set(used_rows[1]['support'])
    assert not (set(used_rows[0]['support']) & set(used_rows[1]['support']))
    new = sorted(set(forced) - set(OLD_ABSENT))
    assert len(new) == 44
    return {
        'status': 'PASS: exact nonnegative three-row Gram zero face',
        'source_sha256': digest(Path(__file__)),
        'inputs': {key: {'path': name, 'sha256': expected} for key, (name, expected) in INPUTS.items()},
        'case_index': 4, 'core_vertices': 35, 'complete_column_count': 1214,
        'row_combination': used_rows, 'combined_rhs': rhs,
        'combined_coefficients': coefficients,
        'coefficient_sha256': hashlib.sha256(canonical(coefficients)).hexdigest(),
        'forced_absent_columns': forced,
        'forced_column_masks': [[a, masks[a]] for a in forced],
        'new_columns_beyond_previous14': new,
        'previous14_used_as_proof_premises': False,
        'integrality_or_Boolean_bounds_used': False,
        'other_Gram_rows_or_capacity_cuts_used': False,
        'necessity': 'The exact Gram equations imply c dot x = 0. Every c is nonnegative and every x is nonnegative. Thus x_a = 0 for every positive c_a.',
        'full_attachment_domain_census_repeated': False,
        'solver_or_optimizer_called': False,
        'entire_case_excluded': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', type=Path)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    assert (args.write is None) != (args.replay is None)
    certificate = derive()
    if args.write:
        assert not args.write.exists()
        args.write.write_text(json.dumps(certificate, indent=2) + '\n')
        path = args.write
    else:
        path = args.replay
        assert certificate == json.loads(path.read_text())
    print(json.dumps({'status': certificate['status'], 'certificate_sha256': digest(path),
        'forced_absent_columns': certificate['forced_absent_columns'],
        'new_columns_beyond_previous14': certificate['new_columns_beyond_previous14'],
        'complete_columns_checked': certificate['complete_column_count']}, indent=2), flush=True)


if __name__ == '__main__':
    main()
