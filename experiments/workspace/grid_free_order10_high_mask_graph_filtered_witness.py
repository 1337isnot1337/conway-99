"""Carry the exact decorated-moment witness through the projector filter.

All positive-mass graphs in the old witness survive, so no new optimizer
is called. Representatives are nevertheless selected from retained full
columns. Exact characteristic polynomials certify both principal PSD
conditions on every graph that carries positive mass.
"""

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import resource
import time

from flint import fmpz_mat
import numpy as np

import grid_free_order10_high_mask_graph_query as base


ROOT, LOGS = base.ROOT, base.LOGS
BINDINGS = {
    'query_source': ('experiments/workspace/grid_free_order10_high_mask_graph_query.py',
                     '97490da5a7f39ff1e9d20ac9f5124e8552cfe8c715ac0f6017a2ad6e4fec8eda'),
    'old_witness': ('experiments/logs/moments-and-counts/order10-high-mask-graph-query01.json',
                    '99261d06e9ad1219c0a580abe1715642ed11eff4a425fb030f8d7de05727beb9'),
    'old_replay': ('experiments/logs/moments-and-counts/order10-high-mask-graph-query01-replay.json',
                   'cead67533854a289364128b011f2d201c581d90c4825b69a347922b6b82c72e1'),
    'filter_source': ('experiments/workspace/grid_free_order10_high_mask_graph_projectors.py',
                      '6582189b3d6f541bb46aec5e86123a507e8622e023e1f6f73093ab86cf53660d'),
    'finish_source': ('experiments/workspace/grid_free_order10_high_mask_graph_projectors_finish.py',
                      'ba9b596969fd69a3c6aa753de3ae9bd4a325daad357b4f740e61afeb40ed7b55'),
    'filter': ('experiments/logs/moments-and-counts/order10-high-mask-graph-projectors-complete01.json.gz',
               '9160decc71391fe42ec3f523b773f90708645bb524067122884c6d42e4c9566f'),
    'filter_replay': ('experiments/logs/moments-and-counts/order10-high-mask-graph-projectors-complete01-replay.json',
                      'c4811ece424b8aabb789b36c687ee00d76b70eb010a30bb23740edcf0ca764ed'),
}


def read(name):
    path, expected = BINDINGS[name]
    path = ROOT / path
    assert base.digest(path) == expected
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def psd_characteristic(rows, kind):
    n = len(rows)
    if kind == 0:
        P = [[27 * (i == j) - 9 * ((rows[i] >> j) & 1) + 1 for j in range(n)] for i in range(n)]
    else:
        P = [[44 * (i == j) + 11 * ((rows[i] >> j) & 1) - 2 for j in range(n)] for i in range(n)]
    assert all(P[i][j] == P[j][i] for i in range(n) for j in range(n))
    # charpoly(-P) is det(tI+P), in ascending coefficient order.
    coefficients = list(map(int, fmpz_mat([[-v for v in row] for row in P]).charpoly()))
    assert len(coefficients) == n + 1 and coefficients[-1] == 1
    assert all(value >= 0 for value in coefficients)
    nullity = next(i for i, value in enumerate(coefficients) if value)
    return {'projector': kind, 'order': n, 'det_tI_plus_P_ascending_coefficients': coefficients,
            'rank': n - nullity, 'positive_semidefinite': True}


def build():
    for path, expected in BINDINGS.values():
        assert base.digest(ROOT / path) == expected
    data = base.load_inputs()
    old, old_replay, filtered, cold = (read(name) for name in
                                      ('old_witness', 'old_replay', 'filter', 'filter_replay'))
    assert old['exact_finite_witness'] and old_replay['result_sha256'] == BINDINGS['old_witness'][1]
    assert old_replay['status'].startswith('PASS:')
    assert filtered['complete'] and filtered['checked_full_columns'] == 157711
    assert filtered['unvisited_columns_retained'] == 0
    assert filtered['source_sha256'] == BINDINGS['filter_source'][1]
    assert filtered['continuation_source_sha256'] == BINDINGS['finish_source'][1]
    assert cold['result_sha256'] == BINDINGS['filter'][1] and cold['status'].startswith('PASS:')
    retained = np.asarray(filtered['retained_columns'], dtype=np.uint32)
    assert len(retained) == 135565 and np.all(retained[1:] > retained[:-1])
    rejected = {row['full_column'] for row in filtered['rejection_witnesses']}
    assert len(rejected) == len(filtered['rejection_witnesses']) == 22146
    assert set(map(int, retained)).isdisjoint(rejected)
    assert set(map(int, retained)) | rejected == set(range(157711))
    assert cold['removed_graphs_checked'] == len(rejected) and cold['retained_graphs'] == len(retained)
    inverse = data['arrays']['full_graph_column_to_distinct']
    old_columns, first, new_inverse, multiplicities = np.unique(
        inverse[retained], return_index=True, return_inverse=True, return_counts=True)
    representatives = retained[first]
    assert len(old_columns) == 17922
    assert np.array_equal(old_columns[new_inverse], inverse[retained])
    assert np.array_equal(inverse[representatives], old_columns)
    C = np.ascontiguousarray(data['C'][:, old_columns])
    assert C.shape == (200, 17922) and np.count_nonzero(C) == 757947
    assert np.all(C[0] == 1)
    weights = [Fraction(0)] * len(old_columns)
    transports = []
    for old_column, numerator, denominator in old['exact_primal']['weights']:
        at = int(np.searchsorted(old_columns, old_column))
        assert at < len(old_columns) and int(old_columns[at]) == old_column
        assert weights[at] == 0 and numerator > 0 and denominator > 0
        weights[at] = Fraction(numerator, denominator)
        transports.append({'old_feature_column': old_column, 'filtered_feature_column': at,
                           'retained_full_representative': int(representatives[at])})
    modified = dict(data)
    modified['C'] = C
    modified['arrays'] = dict(data['arrays'], representative_full_graph_columns=representatives)
    proof = base.check_weights(modified, weights)
    retained_set = set(map(int, retained))
    assert all(graph['full_graph_column'] in retained_set for graph in proof['representative_graphs'])
    principal_certificates = []
    rank_counts = [Counter(), Counter()]
    for graph in proof['representative_graphs']:
        projectors = [psd_characteristic(graph['core_plus_high_adjacency_rows'], kind) for kind in (0, 1)]
        for kind, item in enumerate(projectors):
            rank_counts[kind][item['rank']] += 1
        principal_certificates.append({'filtered_feature_column': graph['distinct_column'],
                                       'full_graph_column': graph['full_graph_column'],
                                       'projectors': projectors})
    assert len(principal_certificates) == proof['positive_graph_masses'] == 200
    arrays = {'coefficients': C, 'old_distinct_feature_columns': old_columns,
              'retained_full_graph_columns': retained,
              'retained_full_to_filtered_column': new_inverse.astype(np.uint32),
              'retained_full_representatives': representatives,
              'filtered_column_multiplicities': multiplicities.astype(np.uint32)}
    record = {'status': 'EXACT_FILTERED_DECORATED_MOMENT_WITNESS',
              'source_sha256': base.digest(Path(__file__)),
              'bindings': {name: {'path': path, 'sha256': expected} for name, (path, expected) in BINDINGS.items()},
              'integer_count_point_sha256': base.BINDINGS['point'][1],
              'rows': 200, 'distinct_columns': 17922, 'nonzeros': 757947,
              'retained_full_columns': 135565, 'certified_excluded_full_columns': 22146,
              'complete_original_domain': 157711, 'moment_rhs_unchanged': True,
              'every_representative_chosen_from_retained_full_columns': True,
              'support_transport': transports, 'exact_primal': proof,
              'support_principal_psd_certificates': principal_certificates,
              'support_projector_rank_histograms': [{str(rank): count for rank, count in sorted(c.items())}
                                                   for c in rank_counts],
              'positive_psd_criterion': 'P symmetric and all coefficients of det(tI+P) nonnegative',
              'positive_psd_proof': 'a negative eigenvalue would give a positive root of a monic polynomial with nonnegative coefficients',
              'new_optimizer_calls': 0, 'full_domain_psd_scan_repeated': False,
              'graph_existence_resolved': False,
              'array_sha256': {name: base.array_digest(array) for name, array in arrays.items()}}
    return record, arrays


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--arrays', type=Path)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    record, arrays = build()
    if args.replay:
        saved = json.loads(args.replay.read_text())
        assert all(saved[key] == value for key, value in record.items())
        path = ROOT / saved['arrays']['path']
        assert base.digest(path) == saved['arrays']['sha256']
        with np.load(path, allow_pickle=False) as old:
            assert set(old.files) == set(arrays)
            assert all(np.array_equal(old[key], value) for key, value in arrays.items())
        result = {'status': 'PASS: filtered exact measure, retained-column lift and 400 principal PSD polynomials',
                  'source_sha256': base.digest(Path(__file__)), 'result_sha256': base.digest(args.replay),
                  'optimizer_called': False, 'graph_existence_resolved': False}
    else:
        assert args.arrays and not args.arrays.exists()
        np.savez_compressed(args.arrays, **arrays)
        record['arrays'] = {'path': str(args.arrays.resolve().relative_to(ROOT)),
                            'sha256': base.digest(args.arrays), 'bytes': args.arrays.stat().st_size}
        result = record
    result['seconds'] = time.monotonic() - started
    result['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    base.save(args.output, result)
    print(json.dumps({key: value for key, value in result.items() if key not in
                     ('support_transport', 'exact_primal', 'support_principal_psd_certificates')}, indent=2))
    print('result_sha256', base.digest(args.output))


if __name__ == '__main__':
    main()
