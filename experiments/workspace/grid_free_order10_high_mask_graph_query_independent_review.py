"""Independent saved-support arithmetic for the decorated six-root moment query.

This imports neither query implementation nor an optimizer. The finite feature
table is a hash-bound input; its full census is not repeated here.
"""

import argparse
from fractions import Fraction
import hashlib
import json
from math import comb, lcm
from pathlib import Path

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/moments-and-counts'
BINDINGS = {
    'source': ('experiments/workspace/grid_free_order10_high_mask_graph_query.py',
               '97490da5a7f39ff1e9d20ac9f5124e8552cfe8c715ac0f6017a2ad6e4fec8eda'),
    'preparation': ('experiments/logs/moments-and-counts/order10-high-mask-graph-query-preparation.json',
                    '2b2929dcdab9a36acc08b6f5882a681ea1805eafc01393081a67257da3e9e01c'),
    'result': ('experiments/logs/moments-and-counts/order10-high-mask-graph-query01.json',
               '99261d06e9ad1219c0a580abe1715642ed11eff4a425fb030f8d7de05727beb9'),
    'features': ('experiments/logs/moments-and-counts/order10-high-mask-graph-features.json',
                 'fc5c2876dfdbfe6b9237a0ebfa610742fda9e3127bd00d6b0676e6e2ee576596'),
    'domain': ('experiments/logs/moments-and-counts/order10-high-mask-graph-domain.json',
               '39fb9f237327616f83917a15644c36a2f397d5c938720b4dff9278d4262d94f8'),
    'moments': ('experiments/logs/moments-and-counts/order10-high-mask-graph-moments01.json',
                '43bde72fa777410a73732d418530a6a853a39740a1b7bcfc591d78977ad4cc3d'),
    'point': ('experiments/logs/moments-and-counts/prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json',
              '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def arrays(record):
    path = ROOT / record['arrays']['path']
    assert digest(path) == record['arrays']['sha256']
    with np.load(path, allow_pickle=False) as saved:
        values = {name: saved[name] for name in saved.files}
    assert set(values) == set(record['array_sha256'])
    for name, value in values.items():
        assert hashlib.sha256(value.tobytes(order='C')).hexdigest() == record['array_sha256'][name]
    return values


def review():
    for path, expected in BINDINGS.values():
        assert digest(ROOT / path) == expected, path
    records = {name: json.loads((ROOT / path).read_text())
               for name, (path, _) in BINDINGS.items() if name != 'source'}
    result, prepared = records['result'], records['preparation']
    assert result['source_sha256'] == BINDINGS['source'][1]
    assert result['preparation_sha256'] == BINDINGS['preparation'][1]
    assert result['model_sha256'] == prepared['model']['exact_and_numerical_model_sha256']
    assert result['exact_finite_witness'] and not result['exact_separator']
    assert not result['graph_existence_resolved']
    features = arrays(records['features'])
    domain = arrays(records['domain'])
    C = features['coefficients']
    assert C.shape == (200, 18427) and C.dtype == np.dtype('uint16')
    proof = result['exact_primal']
    payload = proof['weights']
    assert len(payload) == 200 and len({j for j, _, _ in payload}) == 200
    assert all(type(j) is type(n) is type(d) is int and 0 <= j < C.shape[1] and n > 0 and d > 0
               for j, n, d in payload)
    fractions = [Fraction(n, d) for _, n, d in payload]
    denominator = lcm(*(f.denominator for f in fractions))
    assert denominator == proof['common_weight_denominator'] == 1841072799597249500967
    scaled = [f.numerator * (denominator // f.denominator) for f in fractions]
    support = [j for j, _, _ in payload]
    moments = records['moments']
    g = 72926995680
    assert sum(scaled) == g * denominator == proof['total_mass'] * denominator
    orbit_sum = 0
    for i, row in enumerate(moments['rows']):
        total = sum(int(C[i, j]) * weight for j, weight in zip(support, scaled))
        orbit = row['root_label_orbit_size']
        count = records['point']['induced_counts'][row['catalogue_type']]
        fixed = row['catalogue_automorphism_order'] * count
        assert 720 % orbit == 0 and orbit > 0
        assert row['saved_induced_count'] == count
        assert row['fixed_pattern_moment'] == fixed
        assert total == denominator * orbit * fixed
        assert total == denominator * row['quotient_row_rhs']
        assert total == denominator * moments['quotient_rhs'][i]
        assert sum(coefficient * records['point']['induced_counts'][at]
                   for at, coefficient in row['direct_induced_count_form']) == orbit * fixed
        orbit_sum += orbit
    assert orbit_sum == 73263
    assert len(moments['aggregations']) == 73
    for aggregation in moments['aggregations']:
        rows = aggregation['decorated_rows']
        assert sum(moments['quotient_rhs'][i] for i in rows) == aggregation['old_presence_rhs']

    pair_checks, degree_sums = 0, 0
    for column, saved_graph in zip(support, proof['representative_graphs']):
        full = int(features['representative_full_graph_columns'][column])
        assert int(features['full_graph_column_to_distinct'][full]) == column
        atom = int(np.searchsorted(domain['atom_offsets'], full, side='right') - 1)
        item = records['domain']['records'][atom]
        masks = item['selected_high_masks']
        assert len(set(masks)) == len(masks) and all(3 <= int(m).bit_count() <= 6 for m in masks)
        code = int(domain['graph_codes'][full])
        n = 6 + len(masks)
        matrix = [[0] * n for _ in range(n)]
        for v, mask in enumerate(masks, 6):
            for i in range(6):
                matrix[v][i] = matrix[i][v] = (mask >> i) & 1
        edges = []
        for bit in range(item['eligible_edge_count']):
            if (code >> bit) & 1:
                a, b = map(int, domain['edge_tables'][atom, bit])
                edges.append([a, b])
                matrix[6+a][6+b] = matrix[6+b][6+a] = 1
        assert all(sum(row) <= 14 for row in matrix)
        for i in range(n):
            for j in range(i):
                assert sum(matrix[i][k] * matrix[j][k] for k in range(n)) + matrix[i][j] <= 2
                pair_checks += 1
        expected_rows = [sum(value << j for j, value in enumerate(row)) for row in matrix]
        assert saved_graph == {'distinct_column': column, 'full_graph_column': full,
            'atom_orbit': atom, 'high_masks': masks, 'eligible_edge_code': code,
            'high_edges': edges, 'core_plus_high_adjacency_rows': expected_rows}
        for k in range(5):
            assert sum(int(C[i, column]) for i in range(200)
                       if int(features['row_free_vertices'][i]) == k) == comb(len(masks), k)
            degree_sums += 1
    return {
        'status': 'PASS: independent exact saved-support arithmetic and source review',
        'audit_source_sha256': digest(Path(__file__)),
        'bindings': {key: {'path': path, 'sha256': sha} for key, (path, sha) in BINDINGS.items()},
        'feature_array_sha256': records['features']['arrays']['sha256'],
        'domain_array_sha256': records['domain']['arrays']['sha256'],
        'positive_rational_masses': len(payload), 'common_denominator': denominator,
        'exact_matrix_products_checked': 200 * len(payload),
        'exact_equations_checked': 200, 'direct_induced_forms_checked': 200,
        'ordinary_presence_aggregations_checked': 73,
        'literal_support_graphs_checked': len(payload), 'literal_core_pair_caps_checked': pair_checks,
        'support_degree_partition_checks': degree_sums,
        'individual_pattern_moments_from_uniform_S6_lift': orbit_sum,
        'uniform_lift_reason': 'A root-pattern orbit has size o. Averaging a representative graph over all 720 root relabelings gives each orbit member coefficient C/o. The checked row sum is o times its required fixed-pattern moment.',
        'source_review': [
            'All finite feature and domain arrays and every dependency are hash-bound.',
            'Normalized numerical mass is converted back to labelled-root mass for exact acceptance.',
            'Sparse rational support is checked on every one of the 200 integer rows.',
            'The optional separator corrects the constant row by the exact finite-table minimum; integer overflow is guarded.',
            'Numerical statuses alone are never accepted as a witness or separator.',
            'The claim is a rational finite moment measure, not a host graph or integer embedding measure.'
        ],
        'subject_imported': False, 'optimizer_or_solver_called': False,
        'full_domain_census_or_feature_reconstruction_repeated': False,
        'subject_controls_or_query_repeated': False, 'graph_existence_resolved': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = review()
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)
    print('report_sha256', digest(args.output), flush=True)


if __name__ == '__main__':
    main()
