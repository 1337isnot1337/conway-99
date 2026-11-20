"""Two bounded pure-feasibility probes with exact ordinary-count upper bounds.

The original order-ten probe and its outcomes are unchanged. This source
does not regenerate the large reduction. A floating-point answer is only
a proposal; exact counts and all original equations gate acceptance.
"""

import argparse
import gc
import hashlib
from itertools import combinations, permutations
import json
from math import comb
from pathlib import Path
import pickle
import resource
import time
import warnings

import numpy as np
from scipy import sparse
from scipy.optimize import linprog
from threadpoolctl import threadpool_limits

from grid_free_core9_certificate import INTEGER_POINT
from subgraph_counts import identities


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.pending')
    temporary.write_text(json.dumps(record, indent=2)+'\n')
    temporary.replace(path)


def embedding_bound(rows, vertices=99, degree=14):
    """Minimum sequential labelled-embedding upper bound over all orders.

    For a new vertex with zero/one earlier required neighbors, use v/k.
    With at least two, an adjacent earlier-neighbor pair gives bound1;
    otherwise use bound2. A pattern nonedge need not be a host nonedge.
    """
    n = len(rows)
    size = 1 << n
    has_edge = [False]*size
    for mask in range(1, size):
        bit = mask & -mask
        v = bit.bit_length()-1
        rest = mask ^ bit
        has_edge[mask] = has_edge[rest] or bool(rows[v] & rest)
    dp, last = [None]*size, [None]*size
    dp[0] = 1
    for mask in range(size):
        remaining = (size-1) ^ mask
        while remaining:
            bit = remaining & -remaining
            remaining ^= bit
            v = bit.bit_length()-1
            earlier = rows[v] & mask
            count = earlier.bit_count()
            factor = vertices if count == 0 else degree if count == 1 else 1 if has_edge[earlier] else 2
            candidate = dp[mask]*factor
            target = mask | bit
            if dp[target] is None or candidate < dp[target]:
                dp[target], last[target] = candidate, v
    order = []
    mask = size-1
    while mask:
        v = last[mask]
        order.append(v)
        mask ^= 1 << v
    order.reverse()
    factors, mask, bound = [], 0, 1
    for v in order:
        earlier = rows[v] & mask
        count = earlier.bit_count()
        factor = vertices if count == 0 else degree if count == 1 else 1 if has_edge[earlier] else 2
        factors.append(factor)
        bound *= factor
        mask |= 1 << v
    assert bound == dp[-1]
    return bound, order, factors


def bound_control():
    """Direct ordinary-copy counts of every labelled graph on at most4 sites in R9."""
    rook = [[int(i != j and (i//3 == j//3 or i % 3 == j % 3)) for j in range(9)]
            for i in range(9)]
    assert all(sum(row) == 4 for row in rook)
    assert all(sum(rook[i][k]*rook[j][k] for k in range(9))+rook[i][j] == 2
               for i, j in combinations(range(9), 2))
    checked = 0
    for n in range(5):
        pairs = list(combinations(range(n), 2))
        for bits in range(1 << len(pairs)):
            edges = [pair for k, pair in enumerate(pairs) if bits >> k & 1]
            rows = [0]*n
            for a, b in edges:
                rows[a] |= 1 << b
                rows[b] |= 1 << a
            aut = sum(all(bool(rows[i] >> j & 1) == bool(rows[p[i]] >> p[j] & 1)
                          for i, j in pairs) for p in permutations(range(n)))
            embeddings = sum(all(rook[p[a]][p[b]] for a, b in edges)
                             for p in permutations(range(9), n))
            bound, _, _ = embedding_bound(rows, 9, 4)
            assert embeddings % aut == 0 and embeddings <= bound
            assert embeddings//aut <= bound//aut
            checked += 1
    assert checked == 76
    return {'status': 'exact ordinary-count bounds pass on R9',
            'labelled_patterns': checked, 'maximum_pattern_order': 4}


def load_reduced(path):
    with path.open('rb') as stream:
        data, cores, scale, inj, induced = pickle.load(stream)
    old_path = Path(__file__).with_name('moments-order9.pickle')
    with old_path.open('rb') as stream:
        old_graphs, old_levels, old_aut, old_cores, old_scale, old_inj, old_induced = pickle.load(stream)
    assert len(data[0]) == 48965 and len(data[1][10]) == 42430
    assert len(cores) == 549 and cores[:57] == old_cores
    assert data[0][:len(old_graphs)] == old_graphs
    assert data[1][:len(old_levels)] == old_levels
    assert data[2][:len(old_aut)] == old_aut
    assert scale == 10*old_scale == 3628800 and induced.shape == (48965, 550)
    assert np.array_equal(inj[:len(old_graphs), :58], old_inj)
    assert not np.any(inj[:len(old_graphs), 58:])
    assert not np.any(induced[:len(old_graphs), 58:])
    assert not np.any(induced[:len(old_graphs), :58] % 10)
    assert np.array_equal(induced[:len(old_graphs), :58]//10, old_induced)
    assert all(len(data[0][cores[j-1]]) == 9
               and sum(row.bit_count() for row in data[0][cores[j-1]]) >= 34
               for j in (56, 57))
    # Conversion is guarded before fixed-width storage. All evaluations
    # involving count values are still performed with Python integers.
    lo, hi = int(induced.min()), int(induced.max())
    assert -(1 << 63) <= lo <= hi < (1 << 63)
    del inj, old_inj, old_induced
    gc.collect()
    coefficients = induced.astype(np.int64)
    del induced
    gc.collect()
    return data, cores, scale, coefficients


def bounds_for(data, cores):
    records = []
    for coordinate, graph_index in enumerate(cores, 1):
        rows, aut = data[0][graph_index], data[2][graph_index]
        labelled, order, factors = embedding_bound(rows)
        records.append({'coordinate': coordinate, 'catalogue_type': graph_index,
                        'rows': list(rows), 'automorphisms': aut,
                        'minimum_labelled_embedding_bound': labelled,
                        'ordinary_count_upper_bound': labelled//aut,
                        'minimizing_vertex_order': order, 'factors': factors})
    return records


def make_model(coefficients, bound_records, fixed_old):
    upper = [1]+[r['ordinary_count_upper_bound'] for r in bound_records]
    fixed = dict(enumerate(INTEGER_POINT)) if fixed_old else {0: 1, 56: 0, 57: 0}
    for i, value in fixed.items():
        if not 0 <= value <= upper[i]:
            return {'contradiction': {'kind': 'fixed coordinate violates exact bound',
                                     'coordinate': i, 'value': value, 'upper_bound': upper[i]}}, None
    active = [i for i in range(1, 550) if i not in fixed and upper[i] > 0]
    forced = [i for i in range(1, 550) if i not in fixed and upper[i] == 0]
    constants = [sum(int(row[i])*value for i, value in fixed.items()) for row in coefficients]
    A = coefficients[:, active]
    while True:
        positive = np.any(A > 0, axis=1)
        negative = np.any(A < 0, axis=1)
        for r in np.flatnonzero(~positive & ~negative):
            if constants[int(r)] < 0:
                return {'contradiction': {'kind': 'negative constant after exact substitution',
                                         'catalogue_type': int(r), 'constant': constants[int(r)]}}, None
        trigger = np.array([c == 0 for c in constants]) & ~positive & negative
        fresh = np.any(A[trigger] < 0, axis=0) if np.any(trigger) else np.zeros(len(active), dtype=bool)
        if not np.any(fresh):
            break
        forced.extend(i for i, take in zip(active, fresh) if take)
        active = [i for i, take in zip(active, fresh) if not take]
        A = A[:, ~fresh]
    kept = [i for i, c in enumerate(constants) if c < 0 or negative[i]]
    A = A[kept]
    constants = [constants[i] for i in kept]
    scaled = sparse.csr_matrix(A, dtype=np.float64)
    del A
    variable_scales = np.array([upper[i] for i in active], dtype=float)
    scaled.data *= variable_scales[scaled.indices]
    assert np.all(np.diff(scaled.indptr) > 0)
    row_scales = np.maximum(np.maximum.reduceat(np.abs(scaled.data), scaled.indptr[:-1]),
                            np.array([abs(c) for c in constants], dtype=float))
    assert np.all(row_scales > 0) and np.all(np.isfinite(row_scales))
    scaled.data /= np.repeat(row_scales, np.diff(scaled.indptr))
    rhs = np.array(constants, dtype=float)/row_scales
    scaled.data *= -1
    assert np.all(np.isfinite(scaled.data)) and np.all(np.isfinite(rhs))
    record = {
        'fixed_order_nine_point': fixed_old,
        'active_core_coordinates': active,
        'forced_zero_coordinates': sorted(forced),
        'retained_induced_rows': len(kept),
        'retained_catalogue_types': kept,
        'numerical_nonzeros': int(scaled.nnz),
        'variable_upper_bounds': [upper[i] for i in active],
        'maximum_exact_constant_bits': max((abs(c).bit_length() for c in constants), default=0),
        'minimum_nonzero_normalized_coefficient': float(np.min(np.abs(scaled.data))),
        'normalized_coefficients_below_1e_9': int(np.sum(np.abs(scaled.data) < 1e-9)),
        'objective': 'zero; pure feasibility; no common slack variable',
        'numerical_variable_bounds': [0, 1],
        'row_scaling': 'maximum absolute scaled variable coefficient or substituted constant',
    }
    return record, (scaled, rhs, fixed, upper)


def prepare(cache, output):
    started = time.monotonic()
    data, cores, scale, coefficients = load_reduced(cache)
    bounds = bounds_for(data, cores)
    cases = []
    for fixed in (True, False):
        record, model = make_model(coefficients, bounds, fixed)
        cases.append(record)
        del model
        gc.collect()
    result = {'status': 'exact bounds and scaled feasibility models prepared; not solved',
              'source_sha256': digest(Path(__file__)),
              'reduced_cache_sha256': digest(cache),
              'catalogue_types': len(data[0]), 'core_coordinates': len(cores), 'scale': scale,
              'coefficient_shape': list(coefficients.shape),
              'coefficient_nonzeros': int(np.count_nonzero(coefficients)),
              'maximum_absolute_coefficient': max(abs(int(coefficients.min())), abs(int(coefficients.max()))),
              'bound_method': 'complete subsetDP over all vertex orders, then floor division by automorphism order',
              'upper_bounds': bounds, 'bound_positive_control': bound_control(),
              'cases': cases, 'preparation_seconds': time.monotonic()-started,
              'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('upper_bounds', 'cases')}, indent=2), flush=True)
    for case in cases:
        print(json.dumps({k: v for k, v in case.items() if k not in
                          ('active_core_coordinates', 'forced_zero_coordinates', 'retained_catalogue_types', 'variable_upper_bounds')}, indent=2), flush=True)
    return result


def exact_candidate(data, scale, coefficients, point, upper, fixed_old):
    assert len(point) == 550 and all(type(v) is int for v in point)
    assert point[0] == 1 and all(0 <= x <= b for x, b in zip(point, upper))
    assert point[56] == point[57] == 0
    if fixed_old:
        assert point[:58] == INTEGER_POINT
    raw = [sum(int(row[j])*point[int(j)] for j in np.flatnonzero(row)) for row in coefficients]
    negative = [i for i, value in enumerate(raw) if value < 0]
    remainder = [i for i, value in enumerate(raw) if value % scale]
    result = {'rounded_core_values': point, 'negative_induced_rows': len(negative),
              'nonintegral_induced_rows': len(remainder),
              'first_negative_rows': [[i, raw[i]] for i in negative[:8]],
              'first_nonintegral_rows': [[i, raw[i] % scale] for i in remainder[:8]]}
    if negative or remainder:
        result['status'] = 'rounded point fails exact induced-count checks; real proposal retained'
        return result
    counts = [value//scale for value in raw]
    bad_totals = [(n, sum(counts[i] for i in level), comb(99, n)) for n, level in enumerate(data[1])
                  if sum(counts[i] for i in level) != comb(99, n)]
    violations, checked = [], 0
    for equation in identities(data, 99, 14):
        residual = sum(coefficient*(counts[i-1] if i else 1) for i, coefficient in equation.items())
        if residual and len(violations) < 8:
            violations.append({'equation': sorted(equation.items()), 'residual': residual})
        checked += 1
    assert checked == 180445
    zero_types = [i for i, graph in enumerate(data[0]) if len(graph) == 9
                  and sum(row.bit_count() for row in graph) >= 34]
    assert len(zero_types) == 2
    bad_zeros = [(i, counts[i]) for i in zero_types if counts[i]]
    result.update(original_equations_checked=checked, first_original_equation_violations=violations,
                  bad_level_totals=bad_totals, bad_zero_types=bad_zeros)
    if violations or bad_totals or bad_zeros:
        result['status'] = 'rounded integer counts fail exact extension conditions; real proposal retained'
        return result
    result.update(status='exact integral order-ten count witness verified',
                  induced_counts=counts, fixed_order_nine_point=fixed_old,
                  scope='count equations and exact ordinary-count bounds; not a graph')
    return result


def run(cache, preparation, case_index, seconds, output):
    saved = json.loads(preparation.read_text())
    assert digest(Path(__file__)) == saved['source_sha256']
    assert digest(cache) == saved['reduced_cache_sha256']
    data, cores, scale, coefficients = load_reduced(cache)
    bounds = bounds_for(data, cores)
    assert bounds == saved['upper_bounds']
    record, model = make_model(coefficients, bounds, case_index == 0)
    assert record == saved['cases'][case_index]
    result = {'status': 'running', 'source_sha256': saved['source_sha256'],
              'preparation_sha256': digest(preparation), 'case_index': case_index,
              'fixed_order_nine_point': case_index == 0, 'requested_solver_seconds': seconds,
              'single_thread_requested': True, 'objective': 'pure feasibility',
              'exact_count_witness': False, 'model': record}
    save(output, result)
    if model is None:
        result['status'] = 'exact fixed substitution rejected by a necessary bound or count inequality'
        save(output, result)
        return result
    matrix, rhs, fixed, upper = model
    started = time.monotonic()
    with warnings.catch_warnings(record=True) as caught:
        solution = linprog(np.zeros(matrix.shape[1]), A_ub=matrix, b_ub=rhs,
                           bounds=(0, 1), method='highs',
                           options={'time_limit': seconds, 'threads': 1, 'presolve': True})
    result.update(solver_seconds=time.monotonic()-started,
                  numerical_status=int(solution.status), numerical_message=solution.message,
                  numerical_warnings=[str(w.message) for w in caught])
    if solution.x is not None:
        active = record['active_core_coordinates']
        scaled = [float(v) for v in solution.x]
        values = [float(v)*upper[i] for i, v in zip(active, scaled)]
        result['real_proposal'] = {'active_coordinates': active,
                                   'scaled_values': scaled, 'ordinary_core_values': values,
                                   'exact_real_feasibility_certified': False}
    if not solution.success:
        result['status'] = 'numerical solver gave no certified conclusion'
    else:
        point = [0]*550
        for i, value in fixed.items():
            point[i] = value
        for i, value in zip(record['active_core_coordinates'], result['real_proposal']['ordinary_core_values']):
            point[i] = min(upper[i], max(0, int(round(value))))
        save(output, result)
        exact = exact_candidate(data, scale, coefficients, point, upper, case_index == 0)
        result['rounded_point_check'] = exact
        result['exact_count_witness'] = 'induced_counts' in exact
        result['status'] = exact['status']
    result['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('model', 'real_proposal', 'rounded_point_check')}, indent=2), flush=True)
    if 'rounded_point_check' in result:
        print(json.dumps({k: v for k, v in result['rounded_point_check'].items()
                          if k not in ('rounded_core_values', 'induced_counts')}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--cache', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    solve = sub.add_parser('run')
    solve.add_argument('--cache', type=Path, required=True)
    solve.add_argument('--preparation', type=Path, required=True)
    solve.add_argument('--case', type=int, choices=(0, 1), required=True)
    solve.add_argument('--seconds', type=float, default=30)
    solve.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'prepare':
            prepare(args.cache, args.output)
        else:
            assert 0 < args.seconds <= 30
            run(args.cache, args.preparation, args.case, args.seconds, args.output)
