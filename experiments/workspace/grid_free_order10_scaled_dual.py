"""One bounded highspy dual-ray extraction, followed by exact box Farkas checks.

No infeasibility claim is made unless a nonnegative integer combination
of exact induced-count inequalities has a negative maximum over the
proved ordinary-core-count box.
"""

import argparse
from functools import reduce
import hashlib
import json
from math import gcd
from pathlib import Path
from threading import Timer
import time

import highspy
import numpy as np
from threadpoolctl import threadpool_limits

import grid_free_order10_scaled as model


FINDER_SHA = '12409f5ea1932d549cb69d9ca83e8cd4bd53d173b1a6ef136f9cdee6c095fc16'


def primitive_rows(coefficients, record, fixed, upper, ray):
    active = record['active_core_coordinates']
    answer = []
    for slot, value in enumerate(ray):
        if value == 0:
            continue
        index = record['retained_catalogue_types'][slot]
        row = coefficients[index]
        constant = sum(int(row[i])*x for i, x in fixed.items())
        terms = [int(row[j]) for j in active]
        divisor = reduce(gcd, [abs(constant)]+[abs(a) for a in terms])
        assert divisor > 0
        scaling = max([abs(constant)]+[abs(a)*upper[j] for j, a in zip(active, terms)])
        assert scaling > 0
        answer.append({'catalogue_type': index, 'ray': float(value),
                       'divisor': divisor, 'constant': constant//divisor,
                       'coefficients': [a//divisor for a in terms],
                       'weight_scale': divisor/scaling})
    return answer


def aggregate(rows, weights, active, upper):
    constant = 0
    coefficients = [0]*len(active)
    for row, weight in zip(rows, weights):
        assert type(weight) is int and weight >= 0
        if not weight:
            continue
        constant += weight*row['constant']
        for j, value in enumerate(row['coefficients']):
            coefficients[j] += weight*value
    maximum = constant+sum(max(a, 0)*upper[j] for j, a in zip(active, coefficients))
    return {'constant': constant,
            'coefficients': [[j, a] for j, a in zip(active, coefficients) if a],
            'upper_bound_terms': [[j, a, upper[j]] for j, a in zip(active, coefficients) if a > 0],
            'lower_bound_terms': [[j, -a] for j, a in zip(active, coefficients) if a < 0],
            'maximum_over_exact_box': maximum}


def reconstruct(coefficients, record, fixed, upper, ray):
    rows = primitive_rows(coefficients, record, fixed, upper, ray)
    attempts = []
    for sign in (-1, 1):
        values = [max(0.0, sign*r['ray'])*r['weight_scale'] for r in rows]
        top = max(values, default=0.0)
        if not top:
            continue
        for denominator in (1000, 1000000, 1000000000, 1000000000000, 1000000000000000):
            weights = [int(round(value/top*denominator)) for value in values]
            common = reduce(gcd, weights, 0)
            if common > 1:
                weights = [w//common for w in weights]
            exact = aggregate(rows, weights, record['active_core_coordinates'], upper)
            attempts.append({'sign': sign, 'rounding_denominator': denominator,
                             'nonzero_weights': sum(w > 0 for w in weights),
                             'maximum_over_exact_box': exact['maximum_over_exact_box']})
            if exact['maximum_over_exact_box'] < 0:
                return {'status': 'exact fixed-substitution box Farkas contradiction',
                        'row_multipliers': [{'catalogue_type': row['catalogue_type'],
                                             'primitive_divisor': row['divisor'],
                                             'multiplier': weight}
                                            for row, weight in zip(rows, weights) if weight],
                        'aggregate': exact,
                        'reconstruction_attempts': attempts}
    return {'status': 'numerical ray retained; no exact contradiction reconstructed',
            'reconstruction_attempts': attempts}


def check_exact(coefficients, record, fixed, upper, certificate):
    active = record['active_core_coordinates']
    rows, weights = [], []
    allowed = set(record['retained_catalogue_types'])
    seen = set()
    for item in certificate['row_multipliers']:
        index, divisor, weight = item['catalogue_type'], item['primitive_divisor'], item['multiplier']
        assert index in allowed and index not in seen
        assert type(weight) is int and weight > 0
        seen.add(index)
        original = coefficients[index]
        constant = sum(int(original[i])*x for i, x in fixed.items())
        terms = [int(original[j]) for j in active]
        assert divisor == reduce(gcd, [abs(constant)]+[abs(a) for a in terms]) and divisor > 0
        rows.append({'constant': constant//divisor, 'coefficients': [a//divisor for a in terms]})
        weights.append(weight)
    exact = aggregate(rows, weights, active, upper)
    assert exact == certificate['aggregate']
    assert exact['maximum_over_exact_box'] < 0
    return {'status': 'integer-only Farkas replay PASS',
            'induced_inequalities_used': len(rows),
            'upper_bounds_used': len(exact['upper_bound_terms']),
            'lower_bounds_used': len(exact['lower_bound_terms']),
            'negative_constant': exact['maximum_over_exact_box']}


def load_case(cache, preparation, case):
    assert model.digest(Path(model.__file__)) == FINDER_SHA
    saved = json.loads(preparation.read_text())
    assert saved['source_sha256'] == FINDER_SHA
    assert model.digest(cache) == saved['reduced_cache_sha256']
    data, cores, scale, coefficients = model.load_reduced(cache)
    bounds = model.bounds_for(data, cores)
    assert bounds == saved['upper_bounds']
    record, numeric = model.make_model(coefficients, bounds, case == 0)
    assert record == saved['cases'][case]
    assert numeric is not None and not record['forced_zero_coordinates']
    return saved, coefficients, record, numeric


def run(cache, preparation, case, seconds, output):
    saved, coefficients, record, numeric = load_case(cache, preparation, case)
    matrix, rhs, fixed, upper = numeric
    matrix = matrix.tocsc()
    h = highspy.Highs()
    h.setOptionValue('output_flag', False)
    h.setOptionValue('threads', 1)
    h.setOptionValue('time_limit', seconds)
    h.setOptionValue('presolve', 'on')
    h.HandleUserInterrupt = True
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = matrix.shape[1], matrix.shape[0]
    lp.col_cost_ = np.zeros(matrix.shape[1])
    lp.col_lower_ = np.zeros(matrix.shape[1])
    lp.col_upper_ = np.ones(matrix.shape[1])
    lp.row_lower_ = np.full(matrix.shape[0], -highspy.kHighsInf)
    lp.row_upper_ = rhs
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = matrix.indptr
    lp.a_matrix_.index_ = matrix.indices
    lp.a_matrix_.value_ = matrix.data
    assert h.passModel(lp) == highspy.HighsStatus.kOk
    result = {'status': 'running one bounded dual extraction',
              'source_sha256': model.digest(Path(__file__)), 'finder_sha256': FINDER_SHA,
              'preparation_sha256': model.digest(preparation),
              'reduced_cache_sha256': saved['reduced_cache_sha256'],
              'case_index': case, 'fixed_order_nine_point': case == 0,
              'requested_seconds_including_ray_request': seconds,
              'threads': 1, 'numerical_rows': matrix.shape[0], 'numerical_columns': matrix.shape[1],
              'numerical_nonzeros': int(matrix.nnz),
              'exact_exclusion': False}
    model.save(output, result)
    started = time.monotonic()
    timer = Timer(seconds, h.cancelSolve)
    timer.start()
    ray_exists, ray = False, None
    try:
        h.run()
        result['numerical_status'] = str(h.getModelStatus())
        result['initial_solve_seconds'] = time.monotonic()-started
        if h.getModelStatus() == highspy.HighsModelStatus.kInfeasible and time.monotonic()-started < seconds:
            status, ray_exists, ray = h.getDualRay()
            result['ray_request_status'] = str(status)
    finally:
        timer.cancel()
    result['solver_and_ray_seconds'] = time.monotonic()-started
    result['ray_exists'] = bool(ray_exists)
    if ray_exists:
        assert len(ray) == matrix.shape[0] and np.all(np.isfinite(ray))
        result['numerical_ray'] = [[i, record['retained_catalogue_types'][i], float(v)]
                                   for i, v in enumerate(ray) if v]
        result['status'] = 'numerical ray saved; exact reconstruction pending'
        model.save(output, result)
        candidate = reconstruct(coefficients, record, fixed, upper, ray)
        result['exact_reconstruction'] = candidate
        if 'row_multipliers' in candidate:
            result['exact_replay'] = check_exact(coefficients, record, fixed, upper, candidate)
            result['status'] = candidate['status']
            result['exact_exclusion'] = True
        else:
            result['status'] = candidate['status']
    else:
        result['status'] = 'no numerical ray returned; no exact exclusion'
    model.save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('numerical_ray', 'exact_reconstruction')}, indent=2), flush=True)
    return result


def replay(cache, preparation, certificate):
    result = json.loads(certificate.read_text())
    assert result['source_sha256'] == model.digest(Path(__file__))
    assert result['finder_sha256'] == FINDER_SHA
    assert result['preparation_sha256'] == model.digest(preparation)
    assert result['exact_exclusion']
    _, coefficients, record, numeric = load_case(cache, preparation, result['case_index'])
    _, _, fixed, upper = numeric
    checked = check_exact(coefficients, record, fixed, upper, result['exact_reconstruction'])
    assert checked == result['exact_replay']
    print(json.dumps(checked, indent=2), flush=True)
    return checked


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    extract = sub.add_parser('run')
    extract.add_argument('--cache', type=Path, required=True)
    extract.add_argument('--preparation', type=Path, required=True)
    extract.add_argument('--case', type=int, choices=(0, 1), required=True)
    extract.add_argument('--seconds', type=float, default=30)
    extract.add_argument('--output', type=Path, required=True)
    check = sub.add_parser('replay')
    check.add_argument('--cache', type=Path, required=True)
    check.add_argument('--preparation', type=Path, required=True)
    check.add_argument('--certificate', type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'run':
            assert 0 < args.seconds <= 30
            run(args.cache, args.preparation, args.case, args.seconds, args.output)
        else:
            replay(args.cache, args.preparation, args.certificate)
