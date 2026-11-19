"""One bounded query of the complete decorated high-graph moment table.

The numerical primal has 200 equations and 18,427 nonnegative masses.
Exact acceptance checks rational masses, or a finite-table inequality on
all 157,711 saved graph decorations. No numerical status is a proof.
Preparation runs tiny controls only; no automatic second optimizer call.
"""

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import combinations, permutations, product
import json
from math import comb, gcd, isfinite, lcm
from pathlib import Path
import resource
import signal
import time

import highspy
import numpy as np

import grid_free_order10_high_mask_packing_query as helper


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/moments-and-counts'
BINDINGS = {
    'features': ('experiments/logs/moments-and-counts/order10-high-mask-graph-features.json',
                 'fc5c2876dfdbfe6b9237a0ebfa610742fda9e3127bd00d6b0676e6e2ee576596'),
    'feature_source': ('experiments/workspace/grid_free_order10_high_mask_graph_features.py',
                       'e5f8ae3388375c9cb84a2689917acdaf3973d0c2c2553c01647b5807c36ad934'),
    'patterns': ('experiments/logs/moments-and-counts/order10-high-mask-graph-patterns.json',
                 '86248876874c7b3ded078aec9e189de6f9728302137bb857ffe1500ad519400b'),
    'pattern_source': ('experiments/workspace/grid_free_order10_high_mask_graph_patterns.py',
                       '9e5714d7570536c347159072456aae2b6bf2d6e90c71a0ae2e58a018f69ca829'),
    'domain': ('experiments/logs/moments-and-counts/order10-high-mask-graph-domain.json',
               '39fb9f237327616f83917a15644c36a2f397d5c938720b4dff9278d4262d94f8'),
    'domain_source': ('experiments/workspace/grid_free_order10_high_mask_graph_domain.py',
                      '3ffaf63a411157d0800ce99b24440f0f738ee83e66ff56697eb6077889f3acf5'),
    'moments': ('experiments/logs/moments-and-counts/order10-high-mask-graph-moments01.json',
                '43bde72fa777410a73732d418530a6a853a39740a1b7bcfc591d78977ad4cc3d'),
    'moment_source': ('experiments/workspace/grid_free_order10_high_mask_graph_moments.py',
                      'e5a3cd963baa17aa755e04cae36fb33725cd7b03e40df4ca00b4014d81c899f7'),
    'moment_replay': ('experiments/logs/moments-and-counts/order10-high-mask-graph-moments01-replay.json',
                      '002e643769789b4505288dd815ccf65436d2cc1135aa349b8276e6dbf5658d96'),
    'presence_orbits': ('experiments/logs/moments-and-counts/order10-high-mask-packing-orbits01.json',
                        'a6ca65e8edeb1d4545e89c28833bf7526c693ce6066ec5b6f15a47d31853c61d'),
    'point': ('experiments/logs/moments-and-counts/prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json',
              '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'),
    'query_helper': ('experiments/workspace/grid_free_order10_high_mask_packing_query.py',
                     '8aa977d91ed3bd5407974e9e704fe7d48eb07f798795ccd2b614c40ba2717e57'),
}
ROUNDING_SCALES = (1, 10, 100, 1000, 10000, 1000000, 100000000)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False) + '\n')


def array_digest(value):
    return hashlib.sha256(value.tobytes(order='C')).hexdigest()


def arrays_for(record):
    path = ROOT / record['arrays']['path']
    assert digest(path) == record['arrays']['sha256']
    with np.load(path, allow_pickle=False) as saved:
        arrays = {name: saved[name] for name in saved.files}
    assert set(arrays) == set(record['array_sha256'])
    assert all(array_digest(array) == record['array_sha256'][name]
               for name, array in arrays.items())
    return arrays


def load_inputs():
    for name, (path, expected) in BINDINGS.items():
        assert digest(ROOT / path) == expected, name
    records = {name: json.loads((ROOT / BINDINGS[name][0]).read_text())
               for name in ('features', 'patterns', 'domain', 'moments', 'presence_orbits', 'point')}
    features, patterns, domain, moments, old, point = (records[name] for name in
        ('features', 'patterns', 'domain', 'moments', 'presence_orbits', 'point'))
    assert all(record['complete'] for record in (features, patterns, domain, moments, old))
    assert features['source_sha256'] == BINDINGS['feature_source'][1]
    assert features['patterns_sha256'] == moments['pattern_sha256'] == BINDINGS['patterns'][1]
    assert moments['integer_count_point_sha256'] == BINDINGS['point'][1]
    arrays, domain_arrays, old_arrays = (arrays_for(record) for record in (features, domain, old))
    C = arrays['coefficients']
    b = np.asarray(moments['quotient_rhs'], dtype=np.int64)
    assert C.shape == (200, 18427) and C.dtype == np.dtype('uint16')
    assert b.shape == (200,) and np.all(b > 0)
    assert np.all(C[0] == 1) and int(b[0]) == 72926995680
    assert all(type(value) is int and value >= 0 for value in point['induced_counts'])
    assert len(point['induced_counts']) == 48965
    assert [row['row'] for row in patterns['rows']] == list(range(200))
    for i, (pattern, row) in enumerate(zip(patterns['rows'], moments['rows'])):
        assert all(row[key] == value for key, value in pattern.items())
        orbit = row['root_label_orbit_size']
        assert 720 % orbit == 0
        assert int(arrays['root_label_orbit_sizes'][i]) == orbit
        count = point['induced_counts'][row['catalogue_type']]
        assert row['saved_induced_count'] == count
        assert row['fixed_pattern_moment'] == row['catalogue_automorphism_order'] * count
        assert row['quotient_row_rhs'] == int(b[i]) == orbit * row['fixed_pattern_moment']
        assert sum(coefficient * point['induced_counts'][at]
                   for at, coefficient in row['direct_induced_count_form']) == int(b[i])
    assert sum(map(int, arrays['root_label_orbit_sizes'])) == 73263
    inverse = arrays['full_graph_column_to_distinct']
    representatives = arrays['representative_full_graph_columns']
    assert inverse.shape == (157711,) and representatives.shape == (18427,)
    assert int(inverse.max()) < 18427 and int(representatives.max()) < 157711
    assert np.array_equal(inverse[representatives], np.arange(18427))
    assert np.array_equal(np.bincount(inverse, minlength=18427), arrays['feature_column_multiplicities'])
    assert domain_arrays['graph_codes'].shape == (157711,)
    assert np.array_equal(domain_arrays['atom_offsets'],
        np.asarray([row['offset_start'] for row in domain['records']] + [157711]))
    result = dict(records, arrays=arrays, domain_arrays=domain_arrays, old_arrays=old_arrays,
                  C=C, b=b, g=int(b[0]))
    result['feature_checks'] = feature_checks(result)
    return result


def feature_checks(data):
    """Replay saved-array coverage, rank, degree sums and old-row aggregation."""
    C, arrays, old = data['C'], data['arrays'], data['old_arrays']
    inverse = arrays['full_graph_column_to_distinct']
    multiplicities = arrays['feature_column_multiplicities']
    full_hash = hashlib.sha256()
    for row in C:
        full_hash.update(row[inverse].tobytes(order='C'))
    assert full_hash.hexdigest() == data['features']['full_matrix_sha256']
    nnz = int(np.count_nonzero(C))
    full_nnz = sum(int(count) * int(multiplicity) for count, multiplicity in
                   zip(np.count_nonzero(C, axis=0), multiplicities))
    assert nnz == 782041 and full_nnz == 7291472 and int(C.max()) == 60
    degrees = arrays['row_free_vertices']
    populations = C[degrees == 1].sum(axis=0, dtype=np.uint64)
    assert int(populations.max()) == 10
    for degree in range(5):
        wanted = np.asarray([comb(int(k), degree) if k >= degree else 0 for k in populations])
        assert np.array_equal(C[degrees == degree].sum(axis=0, dtype=np.uint64), wanted)
    offsets = data['domain_arrays']['atom_offsets']
    full_atoms = np.repeat(np.arange(249), np.diff(offsets))
    for aggregation in data['moments']['aggregations']:
        rows = aggregation['decorated_rows']
        old_row = aggregation['old_presence_row_orbit']
        assert all(int(arrays['row_old_presence_equations'][row]) == old_row for row in rows)
        actual = C[rows].sum(axis=0, dtype=np.uint64)
        assert np.array_equal(actual[inverse], old['quotient_coefficients'][old_row, full_atoms])
        assert sum(int(data['b'][row]) for row in rows) == int(old['quotient_rhs'][old_row])
    minor = C[:, arrays['unimodular_minor_columns']]
    assert minor.shape == (200, 200) and np.all(np.diag(minor) == 1)
    for i in range(200):
        for j in range(200):
            if degrees[i] > degrees[j] or (degrees[i] == degrees[j] and i != j):
                assert minor[i, j] == 0
    maximum_sum = int(C.sum(axis=0, dtype=np.uint64).max())
    assert maximum_sum == sum(comb(10, k) for k in range(5)) == 386
    return {'full_column_map_checks': 157711, 'full_matrix_sha256_replayed': full_hash.hexdigest(),
            'full_matrix_nonzeros': full_nnz, 'distinct_matrix_nonzeros': nnz,
            'presence_rows_checked_on_every_full_column': 73,
            'degree_partitions_checked_on_every_distinct_column': 5,
            'exact_row_rank_from_unimodular_minor': 200, 'maximum_column_sum': maximum_sum,
            'fresh_graph_enumeration_or_product_tensor': False}


def metadata(data):
    rhs = helper.normalized_rhs(data['b'], data['g'])
    model = {'coefficient_sha256': array_digest(data['C']), 'integer_rhs': data['b'].tolist(),
             'root_mass': data['g'], 'normalized_rhs_float_hex': [float(v).hex() for v in rhs],
             'constant_row': 0, 'column_lower': 0, 'column_upper': 'unbounded', 'objective': 0}
    return {'source_sha256': digest(Path(__file__)),
            'bindings': {name: {'path': path, 'sha256': expected}
                         for name, (path, expected) in BINDINGS.items()},
            'exact_and_numerical_model_sha256': hashlib.sha256(canonical(model)).hexdigest(),
            'features_array_sha256': data['features']['arrays']['sha256'],
            'domain_array_sha256': data['domain']['arrays']['sha256'],
            'rows': 200, 'distinct_columns': 18427, 'full_graph_decorations': 157711,
            'nonzeros': 782041, 'root_mass': data['g'], 'constant_row': 0,
            'primal': {'objective': 'zero', 'equations': 'C w = b/g',
                       'bounds': 'w >= 0, no finite upper bounds', 'sum_w': 1},
            'normalized_rhs_float_hex': model['normalized_rhs_float_hex'],
            'maximum_solver_and_ray_seconds': 30, 'maximum_exact_stage_seconds': 60,
            'threads': 1, 'solver': 'simplex', 'parallel': 'off', 'presolve': 'on',
            'highs_version': highspy.Highs().version(), 'production_backend_calls_per_run': 1,
            'automatic_dual_optimizer_or_retry': False, 'rounding_scales': list(ROUNDING_SCALES),
            'numerical_status_alone_is_a_certificate': False,
            'host_graph_symmetry_assumed': False, 'graph_existence_resolved': False}


def literal_graph(data, distinct_column):
    full = int(data['arrays']['representative_full_graph_columns'][distinct_column])
    arrays = data['domain_arrays']
    atom = int(np.searchsorted(arrays['atom_offsets'], full, side='right') - 1)
    item = data['domain']['records'][atom]
    masks = list(map(int, item['selected_high_masks']))
    code = int(arrays['graph_codes'][full])
    rows = [0] * (6 + len(masks))
    for j, mask in enumerate(masks):
        for i in range(6):
            if mask >> i & 1:
                rows[i] |= 1 << (6 + j)
                rows[6 + j] |= 1 << i
    edges = []
    for bit, (a, b) in enumerate(arrays['edge_tables'][atom, :item['eligible_edge_count']]):
        a, b = int(a), int(b)
        if code >> bit & 1:
            rows[6 + a] |= 1 << (6 + b)
            rows[6 + b] |= 1 << (6 + a)
            edges.append([a, b])
    assert all(row.bit_count() <= 14 for row in rows)
    assert all((rows[a] & rows[b]).bit_count() + ((rows[a] >> b) & 1) <= 2
               for a, b in combinations(range(len(rows)), 2))
    return {'distinct_column': distinct_column, 'full_graph_column': full, 'atom_orbit': atom,
            'high_masks': masks, 'eligible_edge_code': code, 'high_edges': edges,
            'core_plus_high_adjacency_rows': rows}


def check_weights(data, weights):
    C, b, g = data['C'], data['b'], data['g']
    assert len(weights) == C.shape[1] and all(type(w) is Fraction and w >= 0 for w in weights)
    support = [j for j, w in enumerate(weights) if w]
    assert sum(weights) == g
    for i, row in enumerate(data['moments']['rows']):
        value = sum(int(C[i, j]) * weights[j] for j in support)
        assert value == int(b[i])
        assert value / row['root_label_orbit_size'] == row['fixed_pattern_moment']
    payload = [[j, weights[j].numerator, weights[j].denominator] for j in support]
    graphs = [literal_graph(data, j) for j in support]
    return {'status': 'EXACT_FINITE_DECORATED_MOMENT_WITNESS', 'weights': payload,
            'weight_units': 'total labelled-root embedding mass assigned to a representative graph',
            'normalized_distribution': 'divide each listed mass by the root mass',
            'individual_root_relabeling_mass': 'listed mass divided by 720',
            'positive_graph_masses': len(payload), 'total_mass': g,
            'all_200_equations_checked': True,
            'all_73263_individual_pattern_moments_follow_from_uniform_root_label_lift': True,
            'lift_justification': 'each row-orbit indicator averages to its coefficient divided by that orbit size',
            'common_weight_denominator': lcm(*(weights[j].denominator for j in support)),
            'maximum_numerator_bits': max(weights[j].numerator.bit_length() for j in support),
            'maximum_denominator_bits': max(weights[j].denominator.bit_length() for j in support),
            'weights_sha256': hashlib.sha256(canonical(payload)).hexdigest(),
            'representative_graphs': graphs,
            'integer_embedding_measure_or_host_graph_constructed': False}


def exact_column_values(C, multipliers):
    assert len(multipliers) == C.shape[0] and all(type(v) is int for v in multipliers)
    assert np.issubdtype(C.dtype, np.integer) and np.all(C >= 0)
    bound = int(C.sum(axis=0, dtype=np.uint64).max()) * max(map(abs, multipliers), default=0)
    if bound <= np.iinfo(np.int64).max:
        values = C.astype(np.int64).T @ np.asarray(multipliers, dtype=np.int64)
        return list(map(int, values)), {'method': 'guarded int64', 'absolute_sum_bound': bound}
    active = [(i, v) for i, v in enumerate(multipliers) if v]
    values = [sum(int(C[i, j]) * v for i, v in active) for j in range(C.shape[1])]
    return values, {'method': 'Python integers', 'absolute_sum_bound': bound}


def table_certificate(C, b, inverse, multipliers):
    """Shift a finite-table polynomial by its exact full-domain minimum."""
    assert np.all(C[0] == 1) and int(b[0]) > 0
    raw_values, arithmetic = exact_column_values(C, multipliers)
    minimum = min(raw_values)
    corrected = list(multipliers)
    corrected[0] -= minimum
    common = gcd(*(abs(v) for v in corrected)) or 1
    corrected = [v // common for v in corrected]
    values, final_arithmetic = exact_column_values(C, corrected)
    assert values == [(v - minimum) // common for v in raw_values]
    assert min(values) >= 0
    assert set(map(int, inverse)) == set(range(C.shape[1]))
    full_values = [values[int(j)] for j in inverse]
    assert min(full_values) >= 0
    objective = sum(int(value) * coefficient for value, coefficient in zip(b, corrected))
    return {'status': 'EXACT_FINITE_TABLE_SEPARATOR' if objective < 0 else 'NO_SEPARATOR',
            'raw_integer_multipliers': multipliers, 'raw_arithmetic': arithmetic,
            'raw_minimum': minimum, 'constant_row_subtraction': minimum,
            'positive_gcd_division': common, 'integer_multipliers': corrected,
            'final_arithmetic': final_arithmetic, 'exact_moment_value': objective,
            'distinct_columns_checked': C.shape[1], 'full_columns_checked': len(inverse),
            'minimum_final_column_value': min(full_values), 'maximum_final_column_value': max(full_values),
            'distinct_column_values_sha256': hashlib.sha256(canonical(values)).hexdigest(),
            'full_column_values_sha256': hashlib.sha256(canonical(full_values)).hexdigest()}


def ray_separator(data, floating):
    if len(floating) != 200 or not all(type(v) in (int, float) and isfinite(v) for v in floating):
        return {'exact_separator': False, 'reason': 'no finite ray'}
    maximum = max(map(abs, floating), default=0)
    if maximum == 0:
        return {'exact_separator': False, 'reason': 'zero ray'}
    attempts = []
    for orientation in (1, -1):
        for scale in ROUNDING_SCALES:
            integers = [int(round(orientation * value / maximum * scale)) for value in floating]
            values, arithmetic = exact_column_values(data['C'], integers)
            minimum = min(values)
            objective = sum(int(b) * a for b, a in zip(data['b'], integers)) - minimum * data['g']
            attempts.append({'orientation': orientation, 'scale': scale, 'minimum': minimum,
                             'corrected_exact_value': objective, 'arithmetic': arithmetic})
            if objective >= 0:
                continue
            proof = table_certificate(data['C'], data['b'],
                                      data['arrays']['full_graph_column_to_distinct'], integers)
            assert proof['status'] == 'EXACT_FINITE_TABLE_SEPARATOR'
            induced = Counter()
            for coefficient, row in zip(proof['integer_multipliers'], data['moments']['rows']):
                for at, value in row['direct_induced_count_form']:
                    induced[at] += coefficient * value
            induced = {at: int(value) for at, value in induced.items() if value}
            divisor = gcd(*(abs(v) for v in induced.values()))
            primitive = [[at, value // divisor] for at, value in sorted(induced.items())]
            exact_value = sum(coefficient * data['point']['induced_counts'][at] for at, coefficient in primitive)
            assert exact_value * divisor == proof['exact_moment_value'] < 0
            return {'exact_separator': True, 'rounding_attempts': attempts, 'certificate': proof,
                    'direct_induced_count_form': primitive, 'induced_form_gcd_division': divisor,
                    'primitive_exact_induced_value': exact_value,
                    'direct_literal_moment_lift_sha256': BINDINGS['moment_replay'][1],
                    'eligible_for_count_optimizer': False,
                    'scope': 'the supplied integer point fails the complete finite decorated-graph moment table'}
    return {'exact_separator': False, 'rounding_attempts': attempts}


def averaging_controls():
    controls = []
    for masks, edges in (([7, 56], {(0, 1)}), ([7, 11, 21], {(1, 2)})):
        def key(vertices, permutation):
            moved = [sum(1 << permutation[i] for i in range(6) if masks[v] >> i & 1) for v in vertices]
            order = sorted(range(len(vertices)), key=lambda i: moved[i])
            ordered_vertices = [vertices[i] for i in order]
            return (tuple(sorted(moved)), sum(1 << bit for bit, (a, b) in enumerate(combinations(ordered_vertices, 2))
                                             if tuple(sorted((a, b))) in edges))
        observed = Counter()
        orbits = {}
        coefficient = Counter()
        for k in range(len(masks) + 1):
            for vertices in combinations(range(len(masks)), k):
                orbit = frozenset(key(vertices, p) for p in permutations(range(6)))
                identifier = min(orbit)
                assert identifier not in orbits or orbits[identifier] == orbit
                orbits[identifier] = orbit
                coefficient[identifier] += 1
                observed.update(key(vertices, p) for p in permutations(range(6)))
        for identifier, orbit in orbits.items():
            assert all(Fraction(observed[member], 720) == Fraction(coefficient[identifier], len(orbit))
                       for member in orbit)
        controls.append({'high_masks': masks, 'free_edges': sorted(edges), 'root_permutations': 720,
                         'pattern_orbits': len(orbits), 'labelled_pattern_keys': len(observed)})
    return controls


def controls():
    C = np.asarray([[1, 1, 1], [0, 1, 1]], dtype=np.uint16)
    b = np.asarray([3, 1], dtype=np.int64)
    _, weights = helper.exact_support(C, b, [0, 1])
    assert weights == [Fraction(2), Fraction(1), Fraction(0)]
    assert helper.exact_support(C, np.asarray([1, 2]), [0, 1])[1] is None
    assert helper.exact_support(np.asarray([[1], [0]]), np.asarray([1, 1]), [0])[1] is None
    assert helper.exact_support(C, b, [1, 2])[1] is None
    inverse = np.asarray([0, 1, 2, 1], dtype=np.uint32)
    proof = table_certificate(C, np.asarray([1, 2]), inverse, [0, -1])
    assert proof['status'] == 'EXACT_FINITE_TABLE_SEPARATOR' and proof['exact_moment_value'] == -1
    huge = table_certificate(C, np.asarray([1, 2]), inverse, [0, -(2 ** 201 + 1)])
    assert huge['raw_arithmetic']['method'] == 'Python integers'
    assert huge['integer_multipliers'] == [1, -1] and huge['exact_moment_value'] == -1
    for coefficients in product(range(-2, 3), repeat=2):
        assert table_certificate(C, b, inverse, list(coefficients))['status'] == 'NO_SEPARATOR'
    rhs = helper.normalized_rhs(b, 3)
    positive = helper.run_lp(C, [0] * 3, [0] * 3, [highspy.kHighsInf] * 3, rhs, rhs, 2)
    assert positive['optimal']
    assert helper.exact_support(C, b, positive['basic_columns'])[1] is not None
    negative = helper.run_lp(C, [0] * 3, [0] * 3, [highspy.kHighsInf] * 3,
                             [1, 2], [1, 2], 2, request_ray=True)
    assert negative['numerically_infeasible']
    return {'exact_support_controls': 4, 'finite_table_separator_controls': 2,
            'positive_distribution_nonseparation_controls': 25, 'maximum_raw_coefficient_bits': 202,
            'literal_root_averaging_controls': averaging_controls(), 'tiny_backend_calls': 2,
            'tiny_backend_seconds_each': 2, 'tiny_primal_status': positive['model_status'],
            'tiny_infeasible_status': negative['model_status'], 'production_query_calls': 0}


def run(preparation, output):
    data = load_inputs()
    prepared = json.loads(preparation.read_text())
    assert prepared['model'] == metadata(data)
    result = {'status': 'starting one bounded decorated-graph query',
              'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation),
              'model_sha256': prepared['model']['exact_and_numerical_model_sha256'],
              'integer_count_point_sha256': BINDINGS['point'][1],
              'exact_finite_witness': False, 'exact_separator': False,
              'eligible_for_count_optimizer': False, 'graph_existence_resolved': False}
    started = time.monotonic()
    save(output, result)
    rhs = helper.normalized_rhs(data['b'], data['g'])
    try:
        numeric = helper.run_lp(data['C'], np.zeros(18427), np.zeros(18427),
                                np.full(18427, highspy.kHighsInf), rhs, rhs, 30, request_ray=True)
    except Exception as error:
        result.update(status='ERROR: numerical invocation failed', error=repr(error),
                      total_seconds=time.monotonic() - started)
        save(output, result)
        raise
    result.update(numeric=numeric, status='numerical outcome saved; exact stage pending')
    save(output, result)
    print(json.dumps({'numeric_status': numeric['model_status'],
                      'solver_seconds': numeric['solver_and_ray_seconds']}), flush=True)
    def deadline(_signum, _frame):
        raise TimeoutError('bounded exact decorated-graph outcome stage')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 60)
    try:
        if numeric['optimal']:
            supports = [numeric['basic_columns']]
            if all(type(v) in (int, float) for v in numeric['col_values']):
                supports.append([j for j, value in enumerate(numeric['col_values']) if value > 0])
            seen, attempts = set(), []
            for support in supports:
                key = tuple(sorted(set(support)))
                if key in seen:
                    continue
                seen.add(key)
                attempt, weights = helper.exact_support(data['C'], data['b'], support)
                attempts.append(attempt)
                result['exact_support_attempts'] = attempts
                if weights is not None:
                    proof = check_weights(data, weights)
                    result.update(exact_finite_witness=True, exact_primal=proof,
                                  status='EXACT_FINITE_DECORATED_MOMENT_WITNESS')
                    break
            if not result['exact_finite_witness']:
                result['status'] = 'numerical optimum saved; no exact rational witness reconstructed'
        elif numeric['numerically_infeasible'] and numeric['dual_ray'] is not None:
            result['separation'] = ray_separator(data, numeric['dual_ray'])
            result['exact_separator'] = result['separation']['exact_separator']
            result['status'] = ('EXACT_FINITE_DECORATED_MOMENT_SEPARATOR' if result['exact_separator']
                                else 'numerically infeasible; no exact separator reconstructed')
        else:
            result['status'] = 'UNKNOWN: no certified finite-model outcome'
    except TimeoutError:
        result.update(status='UNKNOWN: exact outcome stage timed out', exact_stage_timed_out=True,
                      exact_finite_witness=False, exact_separator=False)
    except Exception as error:
        result.update(status='ERROR: exact outcome stage failed', exact_stage_error=repr(error),
                      exact_finite_witness=False, exact_separator=False)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    result.update(total_seconds=time.monotonic() - started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in
                     ('numeric', 'exact_primal', 'separation', 'exact_support_attempts')}, indent=2), flush=True)
    print('result_sha256', digest(output), flush=True)
    return int('exact_stage_error' in result)


def replay(preparation, result_path, output):
    data = load_inputs()
    prepared, result = (json.loads(path.read_text()) for path in (preparation, result_path))
    assert prepared['model'] == metadata(data)
    assert result['source_sha256'] == digest(Path(__file__))
    assert result['preparation_sha256'] == digest(preparation)
    assert result['model_sha256'] == prepared['model']['exact_and_numerical_model_sha256']
    if result['exact_finite_witness']:
        weights = [Fraction(0)] * 18427
        seen = set()
        for j, numerator, denominator in result['exact_primal']['weights']:
            assert type(j) is type(numerator) is type(denominator) is int
            assert 0 <= j < 18427 and j not in seen and numerator > 0 and denominator > 0
            seen.add(j)
            weights[j] = Fraction(numerator, denominator)
        assert check_weights(data, weights) == result['exact_primal']
        status = 'PASS: exact rational decorated-graph measure and uniform root-label lift'
    elif result['exact_separator']:
        separation = result['separation']
        proof = table_certificate(data['C'], data['b'], data['arrays']['full_graph_column_to_distinct'],
                                  separation['certificate']['raw_integer_multipliers'])
        assert proof == separation['certificate'] and proof['status'] == 'EXACT_FINITE_TABLE_SEPARATOR'
        induced = Counter()
        for coefficient, row in zip(proof['integer_multipliers'], data['moments']['rows']):
            for at, value in row['direct_induced_count_form']:
                induced[at] += coefficient * value
        induced = {at: int(value) for at, value in induced.items() if value}
        divisor = gcd(*(abs(v) for v in induced.values()))
        primitive = [[at, value // divisor] for at, value in sorted(induced.items())]
        assert primitive == separation['direct_induced_count_form']
        assert divisor == separation['induced_form_gcd_division']
        assert sum(value * data['point']['induced_counts'][at] for at, value in primitive) == separation['primitive_exact_induced_value'] < 0
        status = 'PASS: exact full-column inequality and direct induced-count form'
    else:
        status = 'bindings checked; no exact finite-model conclusion to replay'
    report = {'status': status, 'source_sha256': digest(Path(__file__)),
              'result_sha256': digest(result_path), 'preparation_sha256': digest(preparation),
              'optimizer_called': False, 'graph_existence_resolved': False}
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)
    print('output_sha256', digest(output), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--run', action='store_true')
    parser.add_argument('--replay', type=Path)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    assert sum((args.prepare, args.run, args.replay is not None)) == 1
    if args.prepare:
        assert not args.preparation.exists()
        started = time.monotonic()
        data = load_inputs()
        prepared = {'model': metadata(data), 'feature_checks': data['feature_checks'],
                    'controls': controls(), 'production_query_called': False,
                    'seconds': time.monotonic() - started,
                    'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        save(args.preparation, prepared)
        print(json.dumps(prepared, indent=2), flush=True)
        print('preparation_sha256', digest(args.preparation), flush=True)
    else:
        assert args.output and not args.output.exists()
        if args.run:
            raise SystemExit(run(args.preparation, args.output))
        replay(args.preparation, args.replay, args.output)


if __name__ == '__main__':
    main()
