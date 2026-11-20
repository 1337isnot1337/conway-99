"""Bounded query and exact replay of the 73 by 249 packing quotient.

Preparation runs only tiny known controls. A production primal query and
the optional bounded-dual query are separate invocations. Numerical status
alone never certifies feasibility or exclusion.
"""

import argparse
from fractions import Fraction
import hashlib
import json
from math import gcd, isfinite
from pathlib import Path
import resource
import signal
from threading import Timer
import time

import highspy
import numpy as np

import finite_boolean_moment_certificates as certificates


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
ORBITS = LOGS/'order10-high-mask-packing-orbits01.json'
ORBITS_SHA = 'a6ca65e8edeb1d4545e89c28833bf7526c693ce6066ec5b6f15a47d31853c61d'
ORBIT_SOURCE = ROOT/'experiments/workspace/grid_free_order10_high_mask_packing_orbits.py'
ORBIT_SOURCE_SHA = '59af3f038c1f2795d03d11a80eaee363832f748bcc9863245b8237c71d8d73cd'
HELPER_SHA = 'cdc37c56d4e379fc3774a832d942fb4cfb2eb787746bfdd3f9071880e791ee1e'
POINT_SHA = '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'
ROUNDING_SCALES = (1, 10, 100, 1000, 10000, 1000000, 100000000)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def array_digest(array):
    return hashlib.sha256(array.tobytes(order='C')).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def finite_data(value):
    number = float(value)
    return number if isfinite(number) else str(number)


def load_inputs():
    assert digest(ORBITS) == ORBITS_SHA and digest(ORBIT_SOURCE) == ORBIT_SOURCE_SHA
    assert digest(Path(certificates.__file__)) == HELPER_SHA
    record = json.loads(ORBITS.read_text())
    assert record['complete'] and record['integer_count_point_sha256'] == POINT_SHA
    assert record['active_quotient_shape'] == [73, 249]
    assert not record['host_graph_automorphism_assumed']
    path = ROOT/record['arrays']['path']
    assert digest(path) == record['arrays']['sha256']
    with np.load(path, allow_pickle=False) as saved:
        arrays = {name: saved[name] for name in saved.files}
    assert set(arrays) == set(record['array_sha256'])
    for name, array in arrays.items():
        assert array_digest(array) == record['array_sha256'][name]
    active = arrays['active_quotient_rows']
    C = arrays['quotient_coefficients'][active]
    b = arrays['quotient_rhs'][active]
    g = record['root_labelled_embedding_mass']
    constant = int(np.flatnonzero(active == arrays['constant_quotient_row'][0])[0])
    assert C.shape == (73, 249) and C.dtype == b.dtype == np.dtype('int64')
    assert np.all(C >= 0) and np.all(b > 0) and np.all(C[constant] == 1)
    assert int(b[constant]) == g == 72926995680
    moment_item = record['feature_artifact_bindings']['moments']
    moment_path = ROOT/moment_item['path']
    assert digest(moment_path) == moment_item['sha256']
    with np.load(moment_path, allow_pickle=False) as saved:
        moments = saved['moments']
        masks = saved['monomial_masks']
    assert np.array_equal(masks, arrays['row_monomial_codes'])
    assert len(moments) == len(arrays['row_labels']) == 124314
    assert np.all(moments == moments[arrays['row_representatives']][arrays['row_labels']])
    return record, arrays, C, b, g, constant, moments


def normalized_rhs(b, g):
    return np.asarray([float(Fraction(int(value), g)) for value in b], dtype=np.float64)


def model_metadata(record, arrays, C, b, g, constant):
    numerical_rhs = normalized_rhs(b, g)
    data = {'C': C.tolist(), 'integer_rhs': b.tolist(), 'root_mass': g,
            'normalized_rhs_float_hex': [float(v).hex() for v in numerical_rhs],
            'active_row_orbits': arrays['active_quotient_rows'].tolist(),
            'constant_row': constant, 'column_lower': 0, 'column_upper': 'unbounded'}
    return {'source_sha256': digest(Path(__file__)), 'orbit_result_sha256': ORBITS_SHA,
        'orbit_source_sha256': ORBIT_SOURCE_SHA, 'orbit_arrays_sha256': record['arrays']['sha256'],
        'integer_count_point_sha256': POINT_SHA, 'certificate_helper_sha256': HELPER_SHA,
        'exact_and_numerical_model_sha256': hashlib.sha256(canonical(data)).hexdigest(),
        'rows': 73, 'columns': 249, 'nonzeros': int(np.count_nonzero(C)),
        'constant_row': constant, 'root_mass': g,
        'primal': {'objective': 'zero', 'equations': 'C w = b/g',
                   'bounds': 'w >= 0, no finite upper bounds', 'sum_w': 1},
        'optional_dual': {'objective': 'minimize lambda dot (b/g)',
                          'constraints': 'C transpose lambda >= 0',
                          'bounds': '-1 <= lambda <= 1',
                          'requires': 'a saved numerical-infeasible primal result with no exact separator',
                          'automatic_fallback': False},
        'maximum_solver_seconds_per_invocation': 30, 'maximum_exact_stage_seconds': 60,
        'threads': 1, 'solver': 'simplex', 'parallel': 'off', 'presolve': 'on',
        'highs_version': highspy.Highs().version(),
        'normalized_rhs_float_hex': data['normalized_rhs_float_hex'],
        'rounding_scales': list(ROUNDING_SCALES),
        'fresh_literal_product_lift_required_before_any_cut_use': True,
        'optimizer_eligible_separators_from_this_driver': False,
        'graph_existence_resolved': False}


def run_lp(A, cost, lower, upper, row_lower, row_upper, seconds, request_ray=False):
    h = highspy.Highs()
    for name, value in (('output_flag', False), ('threads', 1), ('parallel', 'off'),
                        ('solver', 'simplex'), ('presolve', 'on'),
                        ('random_seed', 0), ('time_limit', float(seconds))):
        assert h.setOptionValue(name, value) == highspy.HighsStatus.kOk
    A = np.asarray(A, dtype=np.float64)
    m, n = A.shape
    starts, indices, values = [0], [], []
    for j in range(n):
        nonzero = np.flatnonzero(A[:, j])
        indices.extend(map(int, nonzero))
        values.extend(float(A[i, j]) for i in nonzero)
        starts.append(len(indices))
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = n, m
    lp.col_cost_ = np.asarray(cost, dtype=np.float64)
    lp.col_lower_ = np.asarray(lower, dtype=np.float64)
    lp.col_upper_ = np.asarray(upper, dtype=np.float64)
    lp.row_lower_ = np.asarray(row_lower, dtype=np.float64)
    lp.row_upper_ = np.asarray(row_upper, dtype=np.float64)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = np.asarray(starts, dtype=np.int32)
    lp.a_matrix_.index_ = np.asarray(indices, dtype=np.int32)
    lp.a_matrix_.value_ = np.asarray(values, dtype=np.float64)
    assert h.passModel(lp) == highspy.HighsStatus.kOk
    h.HandleUserInterrupt = True
    started = time.monotonic()
    timer = Timer(seconds, h.cancelSolve)
    timer.daemon = True
    timer.start()
    ray, ray_status = None, None
    try:
        run_status = h.run()
        status = h.getModelStatus()
        if request_ray and status == highspy.HighsModelStatus.kInfeasible:
            remaining = seconds-(time.monotonic()-started)
            if remaining > 0:
                assert h.setOptionValue('time_limit', float(remaining)) == highspy.HighsStatus.kOk
                ray_call, exists, candidate = h.getDualRay()
                ray_status = str(ray_call)
                if exists and len(candidate) == m and np.all(np.isfinite(candidate)):
                    ray = [float(v) for v in candidate]
    finally:
        timer.cancel()
        timer.join()
    solution, basis, info = h.getSolution(), h.getBasis(), h.getInfo()
    return {'model_status': str(status), 'run_status': str(run_status),
        'optimal': status == highspy.HighsModelStatus.kOptimal,
        'numerically_infeasible': status == highspy.HighsModelStatus.kInfeasible,
        'solver_and_ray_seconds': time.monotonic()-started,
        'requested_solver_seconds': seconds, 'threads': 1,
        'col_values': [finite_data(v) for v in solution.col_value],
        'row_values': [finite_data(v) for v in solution.row_value],
        'row_duals': [finite_data(v) for v in solution.row_dual],
        'col_duals': [finite_data(v) for v in solution.col_dual],
        'solution_value_valid': bool(solution.value_valid),
        'basis_valid': bool(basis.valid),
        'basic_columns': [i for i, state in enumerate(basis.col_status)
                          if state == highspy.HighsBasisStatus.kBasic],
        'column_basis_status': [str(state) for state in basis.col_status],
        'row_basis_status': [str(state) for state in basis.row_status],
        'objective': finite_data(info.objective_function_value),
        'simplex_iterations': int(info.simplex_iteration_count),
        'dual_ray_request_status': ray_status, 'dual_ray': ray,
        'backend_run_calls': 1}


def exact_support(C, b, support):
    """Solve the proposed independent support by exact rational elimination."""
    support = sorted(set(map(int, support)))
    m, total = C.shape
    assert all(0 <= j < total for j in support)
    n = len(support)
    if not n or n > m:
        return {'status': 'no exact witness from this support', 'reason': 'empty or too large',
                'support': support}, None
    rows = [[Fraction(int(C[i, j])) for j in support]+[Fraction(int(b[i]))] for i in range(m)]
    pivot = 0
    for column in range(n):
        at = next((i for i in range(pivot, m) if rows[i][column]), None)
        if at is None:
            return {'status': 'no exact witness from this support', 'reason': 'dependent columns',
                    'support': support, 'rank_found': pivot}, None
        rows[pivot], rows[at] = rows[at], rows[pivot]
        divisor = rows[pivot][column]
        for j in range(column, n+1):
            rows[pivot][j] /= divisor
        for i in range(pivot+1, m):
            factor = rows[i][column]
            if factor:
                for j in range(column, n+1):
                    rows[i][j] -= factor*rows[pivot][j]
        pivot += 1
    if any(any(row[:n]) or row[n] for row in rows[pivot:]):
        return {'status': 'no exact witness from this support', 'reason': 'inconsistent exact equations',
                'support': support}, None
    values = [Fraction(0)]*n
    for i in range(n-1, -1, -1):
        values[i] = rows[i][n]-sum(rows[i][j]*values[j] for j in range(i+1, n))
    for i in range(m):
        assert sum(int(C[i, j])*value for j, value in zip(support, values)) == int(b[i])
    if any(value < 0 for value in values):
        return {'status': 'no nonnegative exact witness from this support', 'reason': 'negative exact mass',
                'support': support, 'negative_values': [[j, value.numerator, value.denominator]
                    for j, value in zip(support, values) if value < 0]}, None
    weights = [Fraction(0)]*total
    for j, value in zip(support, values):
        weights[j] = value
    return {'status': 'exact nonnegative rational support solution',
            'solved_support': support, 'exact_rank': n,
            'all_equation_rows_checked': m}, weights


def check_weights(C, b, g, arrays, moments, weights):
    assert len(weights) == C.shape[1] and all(type(v) is Fraction and v >= 0 for v in weights)
    assert sum(weights) == g
    for i in range(C.shape[0]):
        assert sum(int(C[i, j])*weights[j] for j in range(C.shape[1])) == int(b[i])
    support = [j for j, value in enumerate(weights) if value]
    D, orbit_sizes = arrays['literal_fixed_monomial_incidence_counts'], arrays['atom_sizes']
    lifted = []
    for row in range(len(arrays['row_representatives'])):
        value = sum(weights[j]*int(D[row, j])/int(orbit_sizes[j]) for j in support)
        assert value == int(moments[arrays['row_representatives'][row]])
        lifted.append(value)
    assert all(lifted[int(orbit)] == int(value) for orbit, value in zip(arrays['row_labels'], moments))
    payload = [[j, weights[j].numerator, weights[j].denominator] for j in support]
    return {'status': 'EXACT_FINITE_MOMENT_WITNESS', 'weights': payload,
        'weight_units': 'total labelled embedding mass per atom orbit',
        'normalized_weight': 'listed rational divided by root mass',
        'positive_orbit_weights': len(payload), 'nonnegative': True,
        'all_73_quotient_rows_checked': True, 'total_mass': g,
        'all_500_row_orbit_lifts_checked': True,
        'all_124314_individual_moments_match_the_uniform_lift': True,
        'full_visible_atom_domain': 90776,
        'maximum_numerator_bits': max((v.numerator.bit_length() for v in weights), default=0),
        'maximum_denominator_bits': max((v.denominator.bit_length() for v in weights), default=0),
        'weights_sha256': hashlib.sha256(canonical(payload)).hexdigest(),
        'host_graph_constructed': False}


def rank_control(arrays, C):
    active = arrays['active_quotient_rows']
    atoms = arrays['visible_atom_codes']
    representatives = arrays['row_representatives'][active]
    monomials = arrays['row_monomial_codes'][representatives]
    at = np.searchsorted(atoms, monomials)
    assert np.all(at < len(atoms)) and np.array_equal(atoms[at], monomials)
    columns = arrays['atom_labels'][at]
    assert len(set(map(int, columns))) == 73
    degrees = np.asarray([int(mask).bit_count() for mask in monomials])
    block = C[:, columns]
    assert np.all(np.diag(block) == 1)
    for i in range(73):
        for j in range(73):
            if degrees[i] > degrees[j] or (degrees[i] == degrees[j] and i != j):
                assert block[i, j] == 0
    return {'exact_row_rank': 73, 'unimodular_triangular_columns': columns.tolist(),
            'reason': 'one atom orbit for each supported degree-at-most-four monomial orbit'}


def controls():
    C = np.asarray([[1, 1], [0, 1]], dtype=np.int64)
    b = np.asarray([3, 1], dtype=np.int64)
    exact, weights = exact_support(C, b, [0, 1])
    assert weights == [Fraction(2), Fraction(1)]
    assert exact_support(C, np.asarray([1, 2]), [0, 1])[1] is None
    assert exact_support(np.asarray([[1], [0]]), np.asarray([1, 1]), [0])[1] is None
    assert exact_support(np.asarray([[1, 1], [2, 2]]), np.asarray([1, 2]), [0, 1])[1] is None
    rhs = normalized_rhs(b, 3)
    positive = run_lp(C, [0, 0], [0, 0], [highspy.kHighsInf]*2, rhs, rhs, 2)
    assert positive['optimal']
    _, values = exact_support(C, b, positive['basic_columns'])
    assert values == [Fraction(2), Fraction(1)]
    negative_rhs = np.asarray([1.0, 2.0])
    negative = run_lp(C, [0, 0], [0, 0], [highspy.kHighsInf]*2,
                      negative_rhs, negative_rhs, 2, request_ray=True)
    assert negative['numerically_infeasible']
    dual = run_lp(C.T, negative_rhs, [-1]*2, [1]*2, [0]*2,
                  [highspy.kHighsInf]*2, 2)
    assert dual['optimal'] and float(dual['objective']) < 0
    helper = certificates.constant_shift([(0, 1), (1, -1)], {0: 1, 1: 2}, [0, 1], 1)
    assert helper['status'] == 'EXACT_SEPARATOR' and helper['exact_value_at_supplied_moments'] == -1
    certificates.replay(helper, {0: 1, 1: 2}, [0, 1])
    return {'exact_support_controls': 4, 'tiny_backend_calls': 3,
        'tiny_seconds_per_backend_call': 2, 'tiny_primal_status': positive['model_status'],
        'tiny_infeasible_status': negative['model_status'], 'tiny_dual_status': dual['model_status'],
        'tiny_exact_separator_value': -1, 'production_query_calls': 0}


def integer_candidate(C, b, g, floating):
    if len(floating) != len(b) or not all(type(v) in (int, float) and isfinite(v) for v in floating):
        return {'status': 'no finite multiplier'}, None
    maximum = max(map(abs, floating), default=0)
    if not maximum:
        return {'status': 'zero multiplier'}, None
    attempts, best = [], None
    for orientation in (1, -1):
        for scale in ROUNDING_SCALES:
            integers = [int(round(orientation*v/maximum*scale)) for v in floating]
            common = gcd(*(abs(v) for v in integers))
            if common > 1:
                integers = [v//common for v in integers]
            values = [sum(int(C[i, j])*integers[i] for i in range(len(b))) for j in range(C.shape[1])]
            minimum = min(values)
            objective = sum(int(v)*c for v, c in zip(b, integers))-minimum*g
            attempts.append({'orientation': orientation, 'scale': scale,
                'minimum_on_orbit_representatives': minimum, 'shifted_integer_moment_value': objective})
            if objective < 0 and best is None:
                best = integers
    return {'status': 'integer multiplier proposed' if best else 'no negative exact proposal from saved scales',
            'attempts': attempts}, best


def full_domain_separator(C, b, g, arrays, moments, floating):
    proposals, integers = integer_candidate(C, b, g, floating)
    if integers is None:
        return {'proposal': proposals, 'exact_separator': False}
    row_coefficients = {int(row): coefficient for row, coefficient in
                        zip(arrays['active_quotient_rows'], integers) if coefficient}
    terms = [(int(mask), row_coefficients[int(orbit)]) for mask, orbit in
             zip(arrays['row_monomial_codes'], arrays['row_labels'])
             if int(orbit) in row_coefficients]
    moment_dict = {int(mask): int(value) for mask, value in zip(arrays['row_monomial_codes'], moments)}
    atoms = list(map(int, arrays['visible_atom_codes']))
    proof = certificates.constant_shift(terms, moment_dict, atoms, (1 << 42)-1)
    assert proof['status'] == 'EXACT_SEPARATOR'
    replay = certificates.replay(proof, moment_dict, atoms)
    return {'proposal': proposals, 'integer_quotient_multipliers': integers,
        'exact_separator': True, 'full_domain_certificate': proof, 'full_domain_replay': replay,
        'literal_graph_product_lift_complete': False, 'eligible_for_count_optimizer': False,
        'scope': 'bound integer moment point excluded from this finite packing moment model'}


def run(preparation, phase, output, prior):
    record, arrays, C, b, g, constant, moments = load_inputs()
    prepared = json.loads(preparation.read_text())
    assert prepared['model'] == model_metadata(record, arrays, C, b, g, constant)
    result = {'status': 'starting one bounded quotient query', 'phase': phase,
        'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation),
        'model_sha256': prepared['model']['exact_and_numerical_model_sha256'],
        'integer_count_point_sha256': POINT_SHA, 'exact_finite_witness': False,
        'exact_separator': False, 'literal_graph_product_lift_complete': False,
        'eligible_for_count_optimizer': False, 'graph_existence_resolved': False}
    if phase == 'dual':
        assert prior is not None
        previous = json.loads(prior.read_text())
        assert previous['phase'] == 'primal'
        assert previous['preparation_sha256'] == digest(preparation)
        assert previous['numeric']['numerically_infeasible'] and not previous['exact_separator']
        result['prior_primal'] = {'path': str(prior.resolve().relative_to(ROOT)), 'sha256': digest(prior)}
    started = time.monotonic()
    save(output, result)
    rhs = normalized_rhs(b, g)
    if phase == 'primal':
        numeric = run_lp(C, np.zeros(249), np.zeros(249), np.full(249, highspy.kHighsInf),
                         rhs, rhs, 30, request_ray=True)
    else:
        numeric = run_lp(C.T, rhs, np.full(73, -1), np.ones(73), np.zeros(249),
                         np.full(249, highspy.kHighsInf), 30)
    result.update(numeric=numeric, status='numerical query saved; exact stage pending')
    save(output, result)
    print(json.dumps({'phase': phase, 'numeric_status': numeric['model_status'],
                      'solver_seconds': numeric['solver_and_ray_seconds']}), flush=True)
    def deadline(_signum, _frame):
        raise TimeoutError('bounded exact quotient outcome stage')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, 60)
    try:
        if phase == 'primal' and numeric['optimal']:
            supports = [numeric['basic_columns']]
            if all(type(v) in (int, float) for v in numeric['col_values']):
                supports.append([j for j, value in enumerate(numeric['col_values']) if value > 0])
            seen, attempts = set(), []
            for support in supports:
                key = tuple(sorted(set(support)))
                if key in seen:
                    continue
                seen.add(key)
                attempt, weights = exact_support(C, b, support)
                attempts.append(attempt)
                if weights is not None:
                    proof = check_weights(C, b, g, arrays, moments, weights)
                    result.update(exact_finite_witness=True, exact_primal=proof,
                                  status='EXACT_FINITE_MOMENT_WITNESS')
                    break
            result['exact_support_attempts'] = attempts
            if not result['exact_finite_witness']:
                result['status'] = 'numerical optimum saved; no exact primal witness reconstructed'
        elif phase == 'primal' and numeric['numerically_infeasible'] and numeric['dual_ray'] is not None:
            result['separation'] = full_domain_separator(C, b, g, arrays, moments, numeric['dual_ray'])
            result['exact_separator'] = result['separation']['exact_separator']
            result['status'] = ('EXACT_FINITE_MOMENT_SEPARATOR_PENDING_LITERAL_LIFT' if result['exact_separator']
                                else 'numerically infeasible; no exact separator reconstructed')
        elif phase == 'dual' and numeric['optimal']:
            result['separation'] = full_domain_separator(C, b, g, arrays, moments, numeric['col_values'])
            result['exact_separator'] = result['separation']['exact_separator']
            result['status'] = ('EXACT_FINITE_MOMENT_SEPARATOR_PENDING_LITERAL_LIFT' if result['exact_separator']
                                else 'bounded dual saved; no exact separator reconstructed')
        else:
            result['status'] = 'UNKNOWN: no certified finite-model outcome'
    except TimeoutError:
        result.update(status='UNKNOWN: exact outcome stage timed out', exact_stage_timed_out=True,
                      exact_finite_witness=False, exact_separator=False)
    except Exception as problem:
        result.update(status='ERROR: exact outcome stage failed', exact_stage_error=repr(problem),
                      exact_finite_witness=False, exact_separator=False)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    result.update(total_seconds=time.monotonic()-started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in
                     ('numeric', 'exact_primal', 'separation', 'exact_support_attempts')}, indent=2), flush=True)
    print('output_sha256', digest(output), flush=True)
    return int('exact_stage_error' in result)


def replay(preparation, saved_result, output):
    record, arrays, C, b, g, constant, moments = load_inputs()
    prepared, result = (json.loads(p.read_text()) for p in (preparation, saved_result))
    assert prepared['model'] == model_metadata(record, arrays, C, b, g, constant)
    assert result['source_sha256'] == digest(Path(__file__))
    assert result['preparation_sha256'] == digest(preparation)
    assert result['model_sha256'] == prepared['model']['exact_and_numerical_model_sha256']
    if result['exact_finite_witness']:
        weights = [Fraction(0)]*249
        seen = set()
        for j, numerator, denominator in result['exact_primal']['weights']:
            assert j not in seen and 0 <= j < 249 and type(numerator) is type(denominator) is int
            assert numerator > 0 and denominator > 0
            seen.add(j)
            weights[j] = Fraction(numerator, denominator)
        proof = check_weights(C, b, g, arrays, moments, weights)
        assert proof == result['exact_primal']
        status = 'PASS: exact rational finite moment witness and full uniform lift'
    elif result['exact_separator']:
        proof = result['separation']['full_domain_certificate']
        integers = result['separation']['integer_quotient_multipliers']
        coefficients = {int(row): coefficient for row, coefficient in
                        zip(arrays['active_quotient_rows'], integers) if coefficient}
        terms = [(int(mask), coefficients[int(orbit)]) for mask, orbit in
                 zip(arrays['row_monomial_codes'], arrays['row_labels']) if int(orbit) in coefficients]
        assert certificates.polynomial(terms, (1 << 42)-1) == dict(proof['raw_integer_polynomial'])
        moment_dict = {int(mask): int(value) for mask, value in zip(arrays['row_monomial_codes'], moments)}
        certificates.replay(proof, moment_dict, list(map(int, arrays['visible_atom_codes'])))
        status = 'PASS: full-domain exact polynomial separator; literal graph lift remains pending'
    else:
        status = 'bindings checked; no exact finite-model conclusion to replay'
    answer = {'status': status, 'source_sha256': digest(Path(__file__)),
        'result_sha256': digest(saved_result), 'preparation_sha256': digest(preparation),
        'optimizer_called': False, 'graph_existence_resolved': False}
    save(output, answer)
    print(json.dumps(answer, indent=2), flush=True)
    print('output_sha256', digest(output), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--phase', choices=('primal', 'dual'))
    parser.add_argument('--prior-primal', type=Path)
    parser.add_argument('--replay', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.prepare:
        assert not args.preparation.exists() and not args.phase and not args.replay
        record, arrays, C, b, g, constant, _ = load_inputs()
        prepared = {'model': model_metadata(record, arrays, C, b, g, constant),
                    'full_rank_control': rank_control(arrays, C), 'controls': controls(),
                    'production_query_called': False}
        save(args.preparation, prepared)
        print(json.dumps(prepared, indent=2), flush=True)
        print('preparation_sha256', digest(args.preparation), flush=True)
    else:
        assert args.output and not args.output.exists()
        if args.replay:
            assert not args.phase
            replay(args.preparation, args.replay, args.output)
        else:
            assert args.phase
            raise SystemExit(run(args.preparation, args.phase, args.output, args.prior_primal))


if __name__ == '__main__':
    main()
