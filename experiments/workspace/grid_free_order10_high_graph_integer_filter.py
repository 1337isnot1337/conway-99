"""Exact shifted integer-incidence filter of every saved high-graph core.

For v=-1 on the six roots and +1 on the high vertices, each exterior
incidence column has integer z=v.h. Hence sum (z-l)(z-l-1)/2 is nonnegative.
Preparation checks formulas and existing feature normalization only.
Every scan removal receives a direct full-core integer certificate.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path
import resource
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/moments-and-counts'
MAX_SECONDS = 60
BINDINGS = {
    'domain': ('order10-high-mask-graph-domain.json', '39fb9f237327616f83917a15644c36a2f397d5c938720b4dff9278d4262d94f8'),
    'features': ('order10-high-mask-graph-features.json', 'fc5c2876dfdbfe6b9237a0ebfa610742fda9e3127bd00d6b0676e6e2ee576596'),
    'patterns': ('order10-high-mask-graph-patterns.json', '86248876874c7b3ded078aec9e189de6f9728302137bb857ffe1500ad519400b'),
    'moments': ('order10-high-mask-graph-moments01.json', '43bde72fa777410a73732d418530a6a853a39740a1b7bcfc591d78977ad4cc3d'),
    'point': ('prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json', '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'),
    'projector_filter': ('order10-high-mask-graph-projectors-complete01.json.gz', '9160decc71391fe42ec3f523b773f90708645bb524067122884c6d42e4c9566f'),
    'old_witness': ('order10-high-mask-graph-query01.json', '99261d06e9ad1219c0a580abe1715642ed11eff4a425fb030f8d7de05727beb9'),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def save(path, value):
    assert not path.exists()
    raw = json.dumps(value, indent=2).encode() + b'\n'
    path.write_bytes(gzip.compress(raw, mtime=0) if path.suffix == '.gz' else raw)


def load_arrays(record):
    path = ROOT / record['arrays']['path']
    assert digest(path) == record['arrays']['sha256']
    with np.load(path, allow_pickle=False) as saved:
        arrays = {name: saved[name] for name in saved.files}
    assert set(arrays) == set(record['array_sha256'])
    assert all(hashlib.sha256(value.tobytes(order='C')).hexdigest() == record['array_sha256'][name]
               for name, value in arrays.items())
    return arrays


def load_inputs():
    records = {}
    for key, (name, expected) in BINDINGS.items():
        path = LOGS / name
        assert digest(path) == expected
        records[key] = read(path)
    arrays = load_arrays(records['domain'])
    features = load_arrays(records['features'])
    assert len(arrays['graph_codes']) == 157711 and features['coefficients'].shape == (200, 18427)
    assert records['projector_filter']['complete']
    assert records['moments']['integer_count_point_sha256'] == BINDINGS['point'][1]
    return records, arrays, features


def feature_coefficients(patterns, shift):
    assert shift in (-1, 0)
    coefficients = []
    for row in patterns['rows']:
        k, masks, code = row['free_vertices'], row['high_masks'], row['canonical_free_graph_code']
        degrees = [0] * k
        for bit, (a, b) in enumerate(row['free_pair_order']):
            if code >> bit & 1:
                degrees[a] += 1
                degrees[b] += 1
        if k == 0:
            value = 114
        elif k == 1:
            value = -12 - comb(masks[0].bit_count(), 2)
        elif k == 2:
            value = 2 - (masks[0] & masks[1]).bit_count()
            value += code * (masks[0].bit_count() + masks[1].bit_count() - 1)
        elif k == 3:
            value = -sum(comb(d, 2) for d in degrees)
        else:
            assert k == 4
            value = 0
        if shift == -1:
            # P_{-1}=P_0+sum z; sum z=14(k-6)-2e(H).
            value += -84 if k == 0 else (14 if k == 1 else (-2 * code if k == 2 else 0))
        coefficients.append(value)
    assert len(coefficients) == 200
    return coefficients


def graph_data(record, arrays, full):
    atom = int(np.searchsorted(arrays['atom_offsets'], full, side='right') - 1)
    item = record['records'][atom]
    masks = list(map(int, item['selected_high_masks']))
    code = int(arrays['graph_codes'][full])
    edges = [(int(a), int(b)) for bit, (a, b) in enumerate(arrays['edge_tables'][atom, :item['eligible_edge_count']])
             if code >> bit & 1]
    return atom, masks, edges


def closed_values(masks, edges):
    k = len(masks)
    d = [mask.bit_count() for mask in masks]
    a = [sum((mask >> i) & 1 for mask in masks) for i in range(6)]
    h = [0] * k
    for i, j in edges:
        h[i] += 1
        h[j] += 1
    e = len(edges)
    p0 = (114 - 13 * k + k * k - sum(comb(value, 2) for value in d)
          - sum(comb(value, 2) for value in a) + sum(x * y for x, y in zip(d, h))
          - e - sum(comb(value, 2) for value in h))
    first, population = 14 * (k - 6) - 2 * e, 93 - k
    shift = first // population
    assert shift in (-1, 0)
    optimum = p0 - shift * first + shift * (shift + 1) * population // 2
    assert optimum == min(p0, p0 + first)
    return {'high_count': k, 'high_edges': e, 'first_moment': first,
            'outside_population': population, 'shift': shift,
            'unshifted_half_value': p0, 'minus_one_half_value': p0 + first,
            'optimal_shifted_half_value': optimum}


def literal_certificate(masks, edges, summary):
    n = 6 + len(masks)
    B = [0] * n
    for j, mask in enumerate(masks):
        for i in range(6):
            if mask >> i & 1:
                B[i] |= 1 << (6 + j)
                B[6 + j] |= 1 << i
    for i, j in edges:
        B[6 + i] |= 1 << (6 + j)
        B[6 + j] |= 1 << (6 + i)
    v = [-1] * 6 + [1] * len(masks)
    Bv = [sum(v[j] for j in range(n) if row >> j & 1) for row in B]
    first = sum(v[i] * (14 - B[i].bit_count()) for i in range(n))
    second = 12 * n - sum(v[i] * Bv[i] for i in range(n)) - sum(value * value for value in Bv) + 2 * sum(v) ** 2
    shift, population = summary['shift'], 99 - n
    value = second - (2 * shift + 1) * first + shift * (shift + 1) * population
    assert first == summary['first_moment'] and population == summary['outside_population']
    assert second - first == 2 * summary['unshifted_half_value']
    assert value == 2 * summary['optimal_shifted_half_value']
    return {'core_adjacency_rows': B, 'integer_core_vector': v,
            'outside_population': population, 'integer_shift': shift,
            'first_moment': first, 'second_moment': second,
            'twice_shifted_polynomial_sum': value}


def aggregate(records, coefficients):
    rhs = records['moments']['quotient_rhs']
    value = sum(coefficient * int(moment) for coefficient, moment in zip(coefficients, rhs))
    induced = Counter()
    for coefficient, row in zip(coefficients, records['moments']['rows']):
        for at, term in row['direct_induced_count_form']:
            induced[at] += coefficient * term
    terms = [[at, int(term)] for at, term in sorted(induced.items()) if term]
    direct = sum(coefficient * records['point']['induced_counts'][at] for at, coefficient in terms)
    assert direct == value
    return {'feature_coefficients': coefficients,
            'nonzero_feature_coefficients': sum(value != 0 for value in coefficients),
            'exact_feature_moment_value': value, 'direct_induced_count_form': terms,
            'exact_direct_induced_value': direct}


def prepare(output):
    started = time.monotonic()
    records, arrays, features = load_inputs()
    coefficients = {shift: feature_coefficients(records['patterns'], shift) for shift in (0, -1)}
    aggregates = {str(shift): aggregate(records, coefficients[shift]) for shift in (0, -1)}
    assert aggregates['0']['exact_feature_moment_value'] == 4371578740080
    controls = set(map(int, arrays['atom_offsets'][:-1])) | {157710, 47724}
    controls.update(graph['full_graph_column'] for graph in records['old_witness']['exact_primal']['representative_graphs'])
    shifts = Counter()
    for full in sorted(controls):
        _, masks, edges = graph_data(records['domain'], arrays, full)
        summary = closed_values(masks, edges)
        literal = literal_certificate(masks, edges, summary)
        column = int(features['full_graph_column_to_distinct'][full])
        for shift, name in ((0, 'unshifted_half_value'), (-1, 'minus_one_half_value')):
            contraction = sum(int(features['coefficients'][i, column]) * coefficients[shift][i] for i in range(200))
            assert contraction == summary[name]
        p0, first, population = summary['unshifted_half_value'], summary['first_moment'], summary['outside_population']
        assert summary['optimal_shifted_half_value'] == min(
            p0 - shift * first + shift * (shift + 1) * population // 2 for shift in range(-20, 21))
        shifts[summary['shift']] += 1
    column_sum = int(features['coefficients'].sum(axis=0, dtype=np.uint64).max())
    maximum_coefficient = max(abs(value) for values in coefficients.values() for value in values)
    bound = column_sum * maximum_coefficient
    assert bound <= np.iinfo(np.int64).max
    result = {'status': 'complete-domain integer-incidence filter prepared; no full filter run',
              'source_sha256': digest(Path(__file__)),
              'bindings': {key: {'name': name, 'sha256': expected} for key, (name, expected) in BINDINGS.items()},
              'full_graph_columns': 157711, 'maximum_core_order': 16,
              'coefficient_aggregates': aggregates,
              'literal_full_core_feature_controls': len(controls),
              'control_full_columns': sorted(controls), 'control_shift_counts': dict(sorted(shifts.items())),
              'maximum_feature_column_sum': column_sum, 'maximum_feature_coefficient': maximum_coefficient,
              'int64_feature_contraction_absolute_bound': bound,
              'all_other_certificate_arithmetic': 'Python integers',
              'optimal_shift': 'floor(first_moment/outside_population)',
              'possible_optimal_shifts': [-1, 0], 'maximum_scan_seconds': MAX_SECONDS,
              'unvisited_columns_retained_on_timeout': True,
              'every_removal_requires_direct_full_core_integer_certificate': True,
              'optimizer_called': False, 'full_domain_scan_called': False,
              'seconds': time.monotonic() - started,
              'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key not in
                     ('coefficient_aggregates', 'control_full_columns')}, indent=2))
    print('preparation_sha256', digest(output))


def scan(preparation, output):
    prepared = read(preparation)
    assert prepared['source_sha256'] == digest(Path(__file__)) and prepared['maximum_scan_seconds'] == MAX_SECONDS
    records, arrays, features = load_inputs()
    vectors = {}
    C = features['coefficients'].astype(np.int64)
    assert int(C.sum(axis=0).max()) * max(abs(value) for item in prepared['coefficient_aggregates'].values()
                                        for value in item['feature_coefficients']) == prepared['int64_feature_contraction_absolute_bound']
    for shift in (0, -1):
        coefficients = feature_coefficients(records['patterns'], shift)
        assert aggregate(records, coefficients) == prepared['coefficient_aggregates'][str(shift)]
        vectors[shift] = np.asarray(coefficients, dtype=np.int64) @ C
    started = time.monotonic()
    rejects, checked, shift_counts = [], 0, Counter()
    for full in range(157711):
        if time.monotonic() - started >= MAX_SECONDS:
            break
        atom, masks, edges = graph_data(records['domain'], arrays, full)
        summary = closed_values(masks, edges)
        column = int(features['full_graph_column_to_distinct'][full])
        assert int(vectors[0][column]) == summary['unshifted_half_value']
        assert int(vectors[-1][column]) == summary['minus_one_half_value']
        shift_counts[summary['shift']] += 1
        if summary['optimal_shifted_half_value'] < 0:
            proof = literal_certificate(masks, edges, summary)
            assert proof['twice_shifted_polynomial_sum'] < 0
            rejects.append({'full_graph_column': full, 'presence_atom_orbit': atom,
                            'old_distinct_feature_column': column,
                            'closed_values': summary, 'certificate': proof})
        checked += 1
        if checked % 16384 == 0:
            print(json.dumps({'checked': checked, 'removed': len(rejects), 'seconds': time.monotonic() - started}), flush=True)
    removed = {item['full_graph_column'] for item in rejects}
    kept = [full for full in range(157711) if full not in removed]
    projector_kept = set(records['projector_filter']['retained_columns'])
    combined = [full for full in kept if full in projector_kept]
    old_support = [graph['full_graph_column'] for graph in records['old_witness']['exact_primal']['representative_graphs']]
    result = {'status': 'complete exact shifted integer-incidence filter' if checked == 157711 else
              'partial exact integer-incidence filter; unvisited columns retained',
              'complete': checked == 157711, 'source_sha256': digest(Path(__file__)),
              'preparation_sha256': digest(preparation), 'domain_sha256': BINDINGS['domain'][1],
              'projector_filter_sha256': BINDINGS['projector_filter'][1],
              'checked_full_columns': checked, 'rejected_full_columns': len(rejects),
              'retained_full_columns': len(kept), 'unvisited_columns_retained': 157711 - checked,
              'retained_columns': kept, 'rejection_certificates': rejects,
              'optimal_shift_histogram': {str(key): value for key, value in sorted(shift_counts.items())},
              'combined_with_projectors_retained_columns': combined,
              'combined_with_projectors_retained_count': len(combined),
              'new_removals_after_projectors': len(projector_kept & removed),
              'old_positive_support_columns_removed': [full for full in old_support if full in removed],
              'all_checked_columns_match_existing_200_feature_contractions': True,
              'optimizer_called': False, 'graph_existence_resolved': False,
              'seconds': time.monotonic() - started,
              'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key not in
                     ('retained_columns', 'rejection_certificates', 'combined_with_projectors_retained_columns')}, indent=2))
    print('result_sha256', digest(output), flush=True)


def replay(preparation, result_path, output):
    prepared, result = read(preparation), read(result_path)
    assert prepared['source_sha256'] == result['source_sha256'] == digest(Path(__file__))
    assert result['preparation_sha256'] == digest(preparation)
    records, arrays, features = load_inputs()
    for shift in (0, -1):
        assert aggregate(records, feature_coefficients(records['patterns'], shift)) == prepared['coefficient_aggregates'][str(shift)]
    removed = set()
    for item in result['rejection_certificates']:
        full = item['full_graph_column']
        assert type(full) is int and 0 <= full < result['checked_full_columns'] and full not in removed
        atom, masks, edges = graph_data(records['domain'], arrays, full)
        assert atom == item['presence_atom_orbit']
        assert int(features['full_graph_column_to_distinct'][full]) == item['old_distinct_feature_column']
        summary = closed_values(masks, edges)
        assert summary == item['closed_values']
        proof = literal_certificate(masks, edges, summary)
        assert proof == item['certificate'] and proof['twice_shifted_polynomial_sum'] < 0
        removed.add(full)
    kept = [full for full in range(157711) if full not in removed]
    assert kept == result['retained_columns'] and len(removed) == result['rejected_full_columns']
    assert set(range(result['checked_full_columns'], 157711)) <= set(kept)
    combined = sorted(set(kept) & set(records['projector_filter']['retained_columns']))
    assert combined == result['combined_with_projectors_retained_columns']
    report = {'status': 'PASS: every removed full core has a direct exact integer-incidence obstruction',
              'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation),
              'result_sha256': digest(result_path), 'removed_full_columns_checked': len(removed),
              'combined_retained_full_columns': len(combined),
              'unvisited_columns_retained': result['unvisited_columns_retained'],
              'positive_classification_repeated': False, 'optimizer_called': False}
    save(output, report)
    print(json.dumps(report, indent=2))
    print('replay_sha256', digest(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'scan', 'replay'))
    parser.add_argument('--preparation', type=Path)
    parser.add_argument('--result', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output)
    elif args.command == 'scan':
        scan(args.preparation, args.output)
    else:
        replay(args.preparation, args.result, args.output)
