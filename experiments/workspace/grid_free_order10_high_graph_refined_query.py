"""One exact-checked moment query after both complete core filters.

The 200 equations are unchanged. All 135,534 surviving full graph columns
map to 17,920 feature columns. Excluded columns have explicit certificates;
representatives are selected only from surviving full columns.
"""

import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import resource
import signal
import time

from flint import fmpz_mat
import highspy
import numpy as np

import grid_free_order10_high_mask_graph_query as base
import grid_free_order10_high_mask_graph_projectors as projectors
import grid_free_order10_high_graph_integer_filter as integer_filter


ROOT, LOGS = base.ROOT, base.LOGS
BINDINGS = {
    'base_query_source': ('experiments/workspace/grid_free_order10_high_mask_graph_query.py',
                          '97490da5a7f39ff1e9d20ac9f5124e8552cfe8c715ac0f6017a2ad6e4fec8eda'),
    'base_query_preparation': ('experiments/logs/moments-and-counts/order10-high-mask-graph-query-preparation.json',
                               '2b2929dcdab9a36acc08b6f5882a681ea1805eafc01393081a67257da3e9e01c'),
    'projector_source': ('experiments/workspace/grid_free_order10_high_mask_graph_projectors.py',
                         '6582189b3d6f541bb46aec5e86123a507e8622e023e1f6f73093ab86cf53660d'),
    'integer_source': ('experiments/workspace/grid_free_order10_high_graph_integer_filter.py',
                       '29b7778bcb0838bc6e2062e530798d85ef3057ed7801e9e49b23498dd07115a1'),
    'projectors': ('experiments/logs/moments-and-counts/order10-high-mask-graph-projectors-complete01.json.gz',
                   '9160decc71391fe42ec3f523b773f90708645bb524067122884c6d42e4c9566f'),
    'projector_replay': ('experiments/logs/moments-and-counts/order10-high-mask-graph-projectors-complete01-replay.json',
                         'c4811ece424b8aabb789b36c687ee00d76b70eb010a30bb23740edcf0ca764ed'),
    'integer_filter': ('experiments/logs/moments-and-counts/order10-high-graph-integer-filter-scan01.json.gz',
                       'fc3de0d243afe6ad6130afc8be1c8d19d27cedec310a7f472c3307d579952157'),
    'integer_replay': ('experiments/logs/moments-and-counts/order10-high-graph-integer-filter-scan01-replay.json',
                       '80d773d2592b74070c5e703417f0b2388e8090e7031264578798f807a1d2fbca'),
}


def read(name):
    path, expected = BINDINGS[name]
    path = ROOT / path
    assert base.digest(path) == expected
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def load_inputs():
    for path, expected in BINDINGS.values():
        assert base.digest(ROOT / path) == expected
    data = base.load_inputs()
    psd, ints, psd_cold, int_cold = (read(name) for name in
                                    ('projectors', 'integer_filter', 'projector_replay', 'integer_replay'))
    assert psd['complete'] and ints['complete']
    assert psd['checked_full_columns'] == ints['checked_full_columns'] == 157711
    assert psd_cold['result_sha256'] == BINDINGS['projectors'][1]
    assert int_cold['result_sha256'] == BINDINGS['integer_filter'][1]
    assert psd_cold['status'].startswith('PASS:') and int_cold['status'].startswith('PASS:')
    removed_psd = {item['full_column'] for item in psd['rejection_witnesses']}
    removed_integer = {item['full_graph_column'] for item in ints['rejection_certificates']}
    assert len(removed_psd) == 22146 and len(removed_integer) == 31
    assert removed_psd.isdisjoint(removed_integer)
    removed = removed_psd | removed_integer
    retained = np.asarray([full for full in range(157711) if full not in removed], dtype=np.uint32)
    assert retained.tolist() == ints['combined_with_projectors_retained_columns']
    assert set(map(int, retained)) == set(psd['retained_columns']) & set(ints['retained_columns'])
    assert len(retained) == 135534
    original_arrays = data['arrays']
    original_inverse = original_arrays['full_graph_column_to_distinct']
    columns, first, inverse, multiplicities = np.unique(
        original_inverse[retained], return_index=True, return_inverse=True, return_counts=True)
    representatives = retained[first]
    C = np.ascontiguousarray(data['C'][:, columns])
    assert C.shape == (200, 17920) and np.count_nonzero(C) == 757898
    assert np.array_equal(columns[inverse], original_inverse[retained])
    assert np.array_equal(original_inverse[representatives], columns)
    assert np.all(C[0] == 1)
    old_minor = original_arrays['unimodular_minor_columns']
    minor_columns = np.searchsorted(columns, old_minor)
    assert np.array_equal(columns[minor_columns], old_minor)
    minor = C[:, minor_columns]
    degree = original_arrays['row_free_vertices']
    assert np.all(np.diag(minor) == 1)
    for i in range(200):
        for j in range(200):
            if degree[i] > degree[j] or (degree[i] == degree[j] and i != j):
                assert minor[i, j] == 0
    data['C'] = C
    data['arrays'] = dict(original_arrays,
                         full_graph_column_to_distinct=inverse.astype(np.uint32),
                         representative_full_graph_columns=representatives)
    data['filters'] = {'projectors': psd, 'integer': ints}
    data['retained'] = retained
    data['old_feature_columns'] = columns
    data['removed'] = removed
    data['filtered_arrays'] = {'coefficients': C, 'old_feature_columns': columns,
        'retained_full_graph_columns': retained,
        'retained_full_to_distinct_column': inverse.astype(np.uint32),
        'retained_full_representatives': representatives,
        'feature_multiplicities': multiplicities.astype(np.uint32),
        'unimodular_minor_columns': minor_columns.astype(np.uint32)}
    return data


def verify_exclusions(data):
    """Recheck every exclusion directly, without a positive-domain scan."""
    removed = set()
    for item in data['filters']['projectors']['rejection_witnesses']:
        full, kind = item['full_column'], item['projector']
        assert full not in removed and 0 <= full < 157711 and kind in (0, 1)
        atom, masks, edges, rows = projectors.graph(data['domain'], data['domain_arrays'], full)
        assert atom == item['atom_orbit']
        z = item['integer_schur_vector']
        assert len(z) == len(masks) and all(type(value) is int for value in z)
        v = projectors.full_vector(masks, z, kind)
        value = projectors.quadratic(projectors.principal(rows, kind), v)
        assert value == item['full_quadratic'] == (891 if kind == 0 else 704) * item['schur_quadratic'] < 0
        removed.add(full)
    psd_count = len(removed)
    for item in data['filters']['integer']['rejection_certificates']:
        full = item['full_graph_column']
        assert full not in removed and 0 <= full < 157711
        atom, masks, edges = integer_filter.graph_data(data['domain'], data['domain_arrays'], full)
        assert atom == item['presence_atom_orbit']
        summary = integer_filter.closed_values(masks, edges)
        assert summary == item['closed_values']
        proof = integer_filter.literal_certificate(masks, edges, summary)
        assert proof == item['certificate'] and proof['twice_shifted_polynomial_sum'] < 0
        removed.add(full)
    assert removed == data['removed'] and len(removed) == 22177
    assert removed.isdisjoint(set(map(int, data['retained'])))
    assert removed | set(map(int, data['retained'])) == set(range(157711))
    return {'status': 'PASS: every deleted original column has a direct exact certificate',
            'projector_negative_vectors_checked': psd_count,
            'integer_incidence_vectors_checked': len(removed) - psd_count,
            'all_original_columns_accounted_for': 157711,
            'positive_domain_classification_repeated': False}


def metadata(data):
    rhs = base.helper.normalized_rhs(data['b'], data['g'])
    exact = {'coefficient_sha256': base.array_digest(data['C']), 'integer_rhs': data['b'].tolist(),
             'root_mass': data['g'], 'normalized_rhs_float_hex': [float(value).hex() for value in rhs],
             'retained_full_ids_sha256': base.array_digest(data['retained']),
             'representatives_sha256': base.array_digest(data['arrays']['representative_full_graph_columns']),
             'bounds': 'nonnegative, no finite upper bounds', 'objective': 0}
    return {'source_sha256': base.digest(Path(__file__)),
            'bindings': {name: {'path': path, 'sha256': expected} for name, (path, expected) in BINDINGS.items()},
            'exact_and_numerical_model_sha256': hashlib.sha256(base.canonical(exact)).hexdigest(),
            'integer_count_point_sha256': base.BINDINGS['point'][1],
            'rows': 200, 'columns': 17920, 'nonzeros': 757898,
            'retained_full_columns': 135534, 'certified_removed_full_columns': 22177,
            'exact_row_rank': 200, 'root_mass': data['g'],
            'primal': {'equations': 'C w=b/g', 'bounds': 'w>=0, no finite upper bounds',
                       'objective': 'zero', 'sum_w': 1},
            'normalized_rhs_float_hex': exact['normalized_rhs_float_hex'],
            'maximum_solver_and_ray_seconds': 30, 'maximum_exact_stage_seconds': 60,
            'threads': 1, 'solver': 'simplex', 'parallel': 'off', 'presolve': 'on',
            'highs_version': highspy.Highs().version(),
            'automatic_second_optimizer_or_retry': False,
            'unchanged_tiny_controls_bound_by_original_query_preparation': True,
            'graph_existence_resolved': False}


def check_primal(data, weights):
    proof = base.check_weights(data, weights)
    retained = set(map(int, data['retained']))
    positive_checks = []
    for graph in proof['representative_graphs']:
        full = graph['full_graph_column']
        assert full in retained
        graph['old_distinct_feature_column'] = int(data['old_feature_columns'][graph['distinct_column']])
        _, masks, edges, rows = projectors.graph(data['domain'], data['domain_arrays'], full)
        assert rows == graph['core_plus_high_adjacency_rows']
        polynomials = []
        for kind in (0, 1):
            P = projectors.principal(rows, kind)
            coefficients = list(map(int, fmpz_mat([[-value for value in row] for row in P]).charpoly()))
            assert len(coefficients) == len(rows) + 1 and coefficients[-1] == 1
            assert all(value >= 0 for value in coefficients)
            polynomials.append(coefficients)
        summary = integer_filter.closed_values(masks, edges)
        assert summary['optimal_shifted_half_value'] >= 0
        direct = integer_filter.literal_certificate(masks, edges, summary)
        assert direct['twice_shifted_polynomial_sum'] >= 0
        positive_checks.append({'full_graph_column': full,
                                'det_tI_plus_projector_coefficients': polynomials,
                                'integer_incidence_certificate': direct})
    proof['support_filter_checks'] = positive_checks
    proof['exact_measure_supported_only_on_surviving_full_columns'] = True
    return proof


def run(preparation, output):
    data = load_inputs()
    prepared = json.loads(preparation.read_text())
    assert prepared['model'] == metadata(data)
    result = {'status': 'starting one refined decorated-moment query',
              'source_sha256': base.digest(Path(__file__)), 'preparation_sha256': base.digest(preparation),
              'model_sha256': prepared['model']['exact_and_numerical_model_sha256'],
              'exact_finite_witness': False, 'exact_separator': False,
              'eligible_for_count_optimizer': False, 'graph_existence_resolved': False}
    started = time.monotonic()
    base.save(output, result)
    rhs = base.helper.normalized_rhs(data['b'], data['g'])
    numeric = base.helper.run_lp(data['C'], np.zeros(17920), np.zeros(17920),
                                 np.full(17920, highspy.kHighsInf), rhs, rhs, 30, request_ray=True)
    result.update(numeric=numeric, status='numerical outcome saved; exact stage pending')
    base.save(output, result)
    print(json.dumps({'numeric_status': numeric['model_status'],
                      'solver_seconds': numeric['solver_and_ray_seconds']}), flush=True)
    def deadline(_signum, _frame):
        raise TimeoutError('bounded exact refined-moment outcome stage')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 60)
    try:
        if numeric['optimal']:
            supports = [numeric['basic_columns']]
            if all(type(value) in (int, float) for value in numeric['col_values']):
                supports.append([j for j, value in enumerate(numeric['col_values']) if value > 0])
            seen, attempts = set(), []
            for support in supports:
                key = tuple(sorted(set(support)))
                if key in seen:
                    continue
                seen.add(key)
                attempt, weights = base.helper.exact_support(data['C'], data['b'], support)
                attempts.append(attempt)
                result['exact_support_attempts'] = attempts
                if weights is not None:
                    proof = check_primal(data, weights)
                    result.update(status='EXACT_REFINED_DECORATED_MOMENT_WITNESS',
                                  exact_finite_witness=True, exact_primal=proof)
                    break
            if not result['exact_finite_witness']:
                result['status'] = 'numerical optimum saved; no exact rational witness reconstructed'
        elif numeric['numerically_infeasible'] and numeric['dual_ray'] is not None:
            separation = base.ray_separator(data, numeric['dual_ray'])
            result['separation'] = separation
            if separation['exact_separator']:
                result['exclusion_replay'] = verify_exclusions(data)
                result.update(status='EXACT_REFINED_DECORATED_MOMENT_SEPARATOR', exact_separator=True)
            else:
                result['status'] = 'numerically infeasible; no exact separator reconstructed'
        else:
            result['status'] = 'UNKNOWN: no exact refined-moment outcome'
    except TimeoutError:
        result.update(status='UNKNOWN: exact stage timed out', exact_stage_timed_out=True,
                      exact_finite_witness=False, exact_separator=False)
    except Exception as error:
        result.update(status='ERROR: exact stage failed', exact_stage_error=repr(error),
                      exact_finite_witness=False, exact_separator=False)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    result.update(total_seconds=time.monotonic() - started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    base.save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key not in
                     ('numeric', 'exact_primal', 'separation', 'exact_support_attempts')}, indent=2), flush=True)
    print('result_sha256', base.digest(output), flush=True)
    return int('exact_stage_error' in result)


def replay(preparation, result_path, output):
    data = load_inputs()
    prepared, result = (json.loads(path.read_text()) for path in (preparation, result_path))
    assert prepared['model'] == metadata(data)
    assert result['source_sha256'] == base.digest(Path(__file__))
    assert result['preparation_sha256'] == base.digest(preparation)
    assert result['model_sha256'] == prepared['model']['exact_and_numerical_model_sha256']
    if result['exact_finite_witness']:
        weights = [Fraction(0)] * 17920
        seen = set()
        for j, numerator, denominator in result['exact_primal']['weights']:
            assert type(j) is type(numerator) is type(denominator) is int
            assert 0 <= j < 17920 and j not in seen and numerator > 0 and denominator > 0
            seen.add(j)
            weights[j] = Fraction(numerator, denominator)
        assert check_primal(data, weights) == result['exact_primal']
        status = 'PASS: exact refined-domain measure, literal graph lift and support filter certificates'
        exclusions = prepared['exclusion_replay']
    elif result['exact_separator']:
        proof = result['separation']['certificate']
        rebuilt = base.table_certificate(data['C'], data['b'],
                                          data['arrays']['full_graph_column_to_distinct'],
                                          proof['raw_integer_multipliers'])
        assert rebuilt == proof and proof['status'] == 'EXACT_FINITE_TABLE_SEPARATOR'
        induced = {}
        for coefficient, row in zip(proof['integer_multipliers'], data['moments']['rows']):
            for at, value in row['direct_induced_count_form']:
                induced[at] = induced.get(at, 0) + coefficient * value
        induced = {at: value for at, value in induced.items() if value}
        divisor = base.gcd(*(abs(value) for value in induced.values()))
        primitive = [[at, value // divisor] for at, value in sorted(induced.items())]
        assert primitive == result['separation']['direct_induced_count_form']
        assert divisor == result['separation']['induced_form_gcd_division']
        assert sum(value * data['point']['induced_counts'][at] for at, value in primitive) == result['separation']['primitive_exact_induced_value'] < 0
        exclusions = verify_exclusions(data)
        assert exclusions == result['exclusion_replay']
        status = 'PASS: exact retained-column separator, induced form and all complete exclusions'
    else:
        exclusions = None
        status = 'bindings checked; no exact refined-moment conclusion to replay'
    report = {'status': status, 'source_sha256': base.digest(Path(__file__)),
              'result_sha256': base.digest(result_path), 'preparation_sha256': base.digest(preparation),
              'exclusion_verification': exclusions, 'optimizer_called': False,
              'graph_existence_resolved': False}
    base.save(output, report)
    print(json.dumps(report, indent=2), flush=True)
    print('replay_sha256', base.digest(output), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--replay', type=Path)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--arrays', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    assert sum((args.prepare, args.run, args.replay is not None)) == 1
    if args.prepare:
        assert args.arrays and not args.preparation.exists() and not args.arrays.exists()
        started = time.monotonic()
        data = load_inputs()
        exclusions = verify_exclusions(data)
        np.savez_compressed(args.arrays, **data['filtered_arrays'])
        prepared = {'model': metadata(data), 'exclusion_replay': exclusions,
                    'arrays': {'path': str(args.arrays.resolve().relative_to(ROOT)),
                               'sha256': base.digest(args.arrays), 'bytes': args.arrays.stat().st_size},
                    'array_sha256': {name: base.array_digest(array) for name, array in data['filtered_arrays'].items()},
                    'unchanged_tiny_controls': read('base_query_preparation')['controls'],
                    'new_optimizer_calls': 0, 'seconds': time.monotonic() - started,
                    'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        base.save(args.preparation, prepared)
        print(json.dumps(prepared, indent=2), flush=True)
        print('preparation_sha256', base.digest(args.preparation), flush=True)
    else:
        assert args.output and not args.output.exists()
        if args.run:
            raise SystemExit(run(args.preparation, args.output))
        replay(args.preparation, args.replay, args.output)
