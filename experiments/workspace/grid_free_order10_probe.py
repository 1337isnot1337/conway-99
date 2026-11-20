"""Bounded order-ten extension probes for the exact zero-grid count witness.

The input cache is generated locally by subgraph_counts.build(10) and
core_counts.reduce_counts(data,99,14). Numerical statuses are not proofs.
Any integer candidate is checked against every original count equation.
"""

import argparse
from functools import reduce
from math import comb, gcd
import hashlib
import json
from pathlib import Path
import pickle
import time

import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits

from flag_moments import cache9
from grid_free_core9_certificate import INTEGER_POINT
from subgraph_counts import identities


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify_integer(data, cores, scale, induced, point, fixed_old):
    assert len(point) == len(cores)+1 and point[0] == 1
    assert all(type(value) is int and value >= 0 for value in point)
    if fixed_old:
        assert point[:58] == INTEGER_POINT
    raw = induced@np.array(point, dtype=object)
    negatives = [i for i, value in enumerate(raw) if value < 0]
    remainders = [i for i, value in enumerate(raw) if value % scale]
    if negatives or remainders:
        return {'status': 'integer rounding failed exact induced-count checks',
                'negative_rows': len(negatives), 'nonintegral_rows': len(remainders),
                'first_negative': negatives[:8], 'first_nonintegral': remainders[:8]}
    counts = [int(value//scale) for value in raw]
    assert all(sum(counts[i] for i in level) == comb(99, n)
               for n, level in enumerate(data[1]))
    checked = 0
    for equation in identities(data, 99, 14):
        assert sum(coefficient*(counts[i-1] if i else 1)
                   for i, coefficient in equation.items()) == 0
        checked += 1
    assert checked == 180445
    zero_types = [i for i, graph in enumerate(data[0])
                  if len(graph) == 9 and sum(row.bit_count() for row in graph) >= 34]
    assert len(zero_types) == 2 and all(counts[i] == 0 for i in zero_types)
    return {'status': 'exact integral order-ten count witness verified',
            'scope': 'original extension equations and nonnegative integer counts; not a graph',
            'original_equations_checked': checked, 'nonnegative_integral_counts': len(counts),
            'fixed_order_nine_point': fixed_old, 'core_values': point, 'induced_counts': counts}


def rows_for(induced, fixed):
    """Substitute fixed coordinates and preserve every exact integer row."""
    free = [i for i in range(1, induced.shape[1]) if i not in fixed]
    all_rows = []
    for index, row in enumerate(induced):
        constant = sum(int(row[i])*value for i, value in fixed.items())
        coefficients = [(i, int(row[i])) for i in free if row[i]]
        common = reduce(gcd, [abs(constant)]+[abs(v) for _, v in coefficients])
        if common > 1:
            constant //= common
            coefficients = [(i, value//common) for i, value in coefficients]
        all_rows.append((index, constant, coefficients))
    forced_zero = set()
    while True:
        fresh = set()
        for index, constant, coefficients in all_rows:
            remaining = [(i, value) for i, value in coefficients if i not in forced_zero]
            if not remaining and constant < 0:
                return free, [], forced_zero, {'type': 'negative constant after exact substitution',
                                               'catalogue_type': index, 'constant': constant}
            if constant == 0 and remaining and all(value <= 0 for _, value in remaining):
                fresh.update(i for i, _ in remaining)
        fresh -= forced_zero
        if not fresh:
            break
        forced_zero.update(fresh)
    active = [i for i in free if i not in forced_zero]
    position = {i: j for j, i in enumerate(active)}
    unique = {}
    for index, constant, coefficients in all_rows:
        remaining = tuple((position[i], value) for i, value in coefficients if i not in forced_zero)
        if constant >= 0 and all(value >= 0 for _, value in remaining):
            continue
        key = (constant, remaining)
        unique.setdefault(key, index)
    rows = [(index, constant, coefficients) for (constant, coefficients), index in unique.items()]
    return active, rows, forced_zero, None


def probe(data, cores, scale, induced, fixed_old, seconds):
    fixed = dict(enumerate(INTEGER_POINT)) if fixed_old else {0: 1, 56: 0, 57: 0}
    started = time.monotonic()
    active, rows, forced, contradiction = rows_for(induced, fixed)
    record = {'fixed_order_nine_point': fixed_old, 'active_core_coordinates': active,
              'forced_zero_coordinates': sorted(forced), 'integer_rows': len(rows),
              'exact_preprocessing_seconds': time.monotonic()-started}
    if contradiction:
        return {**record, 'status': 'exact necessary count inequality rejects the fixed substitution',
                'contradiction': contradiction}
    rr, cc, vv, rhs = [], [], [], []
    for i, (_, constant, coefficients) in enumerate(rows):
        norm = sum(abs(value) for _, value in coefficients)
        assert norm > 0
        for j, value in coefficients:
            rr.append(i); cc.append(j); vv.append(-value/norm)
        rr.append(i); cc.append(len(active)); vv.append(1)
        rhs.append(constant/norm)
    matrix = sparse.csc_matrix((vv, (rr, cc)), shape=(len(rows), len(active)+1))
    goal = np.zeros(len(active)+1)
    goal[-1] = -1
    solving = time.monotonic()
    solution = linprog(goal, A_ub=matrix, b_ub=np.array(rhs),
                       bounds=[(0, None)]*len(active)+[(None, None)], method='highs',
                       options={'time_limit': seconds})
    record.update(numerical_status=int(solution.status), numerical_message=solution.message,
                  requested_solver_seconds=seconds, solver_seconds=time.monotonic()-solving)
    if not solution.success:
        return {**record, 'status': 'numerical solver did not provide a certified conclusion'}
    record['numerical_normalized_margin'] = float(solution.x[-1])
    record['numerical_core_values'] = [float(value) for value in solution.x[:-1]]
    point = [0]*(len(cores)+1)
    for i, value in fixed.items():
        point[i] = value
    for i, value in zip(active, solution.x[:-1]):
        point[i] = int(round(float(value)))
    exact = verify_integer(data, cores, scale, induced, point, fixed_old)
    record['rounded_point_check'] = exact
    record['status'] = exact['status'] if 'induced_counts' in exact else 'numerical candidate only; no exact witness or exclusion'
    return record


def run(cache, output, seconds):
    with cache.open('rb') as stream:
        data, cores, scale, inj, induced = pickle.load(stream)
    old_graphs, old_levels, old_aut, old_cores, old_scale, old_inj, old_induced = cache9()
    assert len(data[0]) == 48965 and len(cores) == 549
    assert data[0][:len(old_graphs)] == old_graphs
    assert data[2][:len(old_graphs)] == old_aut and cores[:57] == old_cores
    assert scale == 3628800 and induced.shape == (48965, 550)
    assert np.array_equal(inj[:len(old_graphs), :58], old_inj)
    assert not np.any(inj[:len(old_graphs), 58:])
    assert np.array_equal(induced[:len(old_graphs), :58]//10, old_induced)
    assert not np.any(induced[:len(old_graphs), :58] % 10)
    assert not np.any(induced[:len(old_graphs), 58:])
    zero_core_types = [cores[i-1] for i in (56, 57)]
    assert all(len(data[0][i]) == 9 and sum(row.bit_count() for row in data[0][i]) >= 34
               for i in zero_core_types)
    source_names = ['grid_free_order10_probe.py', 'core_counts.py', 'subgraph_counts.py',
                    'grid_free_core9_certificate.py']
    result = {'scope': 'order-ten count relaxation; no new order-ten moment blocks',
              'catalogue_types': len(data[0]), 'order_ten_types': len(data[1][10]),
              'core_coordinates': len(cores), 'new_core_coordinates': len(cores)-57,
              'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in source_names},
              'cases': []}
    for fixed_old in (True, False):
        record = probe(data, cores, scale, induced, fixed_old, seconds)
        result['cases'].append(record)
        output.write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({key: value for key, value in record.items()
                          if key not in ('numerical_core_values', 'rounded_point_check',
                                         'active_core_coordinates', 'forced_zero_coordinates')}), flush=True)
        if record.get('rounded_point_check', {}).get('induced_counts') is not None:
            # A fixed-prefix witness already establishes feasibility of
            # the unrestricted-prefix zero-grid count relaxation as well.
            if fixed_old:
                break
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reduced-cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=30)
    args = parser.parse_args()
    assert 0 < args.seconds <= 60
    with threadpool_limits(limits=1):
        run(args.reduced_cache, args.output, args.seconds)
