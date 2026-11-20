"""Exact finite-box checks for the separate case4 max-min LP.

No optimizer is imported. Integers from hashed sparse arrays are converted
to arbitrary-precision Python integers before multiplication. All variables,
including t, have bounds0<=z<=1. The last variable is the objective t.
"""

from fractions import Fraction
from math import gcd, isfinite, lcm
import time


def budget(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError('bounded exact finite-box check')


def check_bound(arrays, variables, sparse_multipliers, gamma, seconds=60):
    assert type(gamma) is int and gamma >= 0 and 0 < seconds <= 60
    started = time.monotonic()
    deadline = started+seconds
    lower, upper = arrays['row_lower'], arrays['row_upper']
    pointer, index, data = arrays['row_pointers'], arrays['column_indices'], arrays['coefficients']
    assert len(pointer) == len(lower)+1 and len(upper) == len(lower)
    assert sparse_multipliers == sorted(sparse_multipliers)
    assert len({i for i, v in sparse_multipliers}) == len(sparse_multipliers)
    assert all(type(i) is type(v) is int and 0 <= i < len(lower) and v != 0 for i, v in sparse_multipliers)
    coefficients = [0]*variables
    endpoint, visited = 0, 0
    for row, multiplier in sparse_multipliers:
        budget(deadline)
        lo, hi = int(lower[row]), int(upper[row])
        assert lo <= hi
        endpoint += multiplier*(hi if multiplier >= 0 else lo)
        for p in range(int(pointer[row]), int(pointer[row+1])):
            column = int(index[p])
            assert 0 <= column < variables
            coefficients[column] += multiplier*int(data[p])
            visited += 1
            if visited % 8192 == 0:
                budget(deadline)
    residual = [-value for value in coefficients]
    residual[-1] += gamma
    bound = endpoint+sum(max(value, 0) for value in residual)
    budget(deadline)
    return {
        'gamma': str(gamma),
        'row_endpoint_sum': str(endpoint),
        'column_coefficients': list(map(str, coefficients)),
        'objective_residual': list(map(str, residual)),
        'objective_upper_bound_numerator': str(bound),
        'inequality': 'gamma*t <= B with B=row_endpoint_sum+sum(max(objective_residual,0))',
        'row_multiplier_count': len(sparse_multipliers),
        'sparse_matrix_entries_visited': visited,
        'physical_variable_bounds_checked': variables,
        'proof': 'sum of nonnegative ranged-row endpoint slacks and0<=z<=1 variable-bound slacks',
        'check_seconds': time.monotonic()-started}


def face_implications(check, sparse_multipliers, base_rows, original_column_ids):
    gamma = int(check['gamma'])
    bound = int(check['objective_upper_bound_numerator'])
    assert gamma > 0 and bound == 0
    n = len(original_column_ids)
    residual = list(map(int, check['objective_residual']))
    assert len(residual) == n+1
    zero_reasons, one_reasons = {}, {}
    def add(destination, column, reason):
        destination.setdefault(int(original_column_ids[column]), []).append(reason)
    for row, value in sparse_multipliers:
        if base_rows <= row < base_rows+n:
            column = row-base_rows
            add(zero_reasons if value < 0 else one_reasons, column,
                {'kind': 'extension_row_multiplier', 'row': row, 'value': str(value)})
    for column in range(n):
        if residual[column]:
            add(zero_reasons if residual[column] < 0 else one_reasons, column,
                {'kind': 'variable_bound_residual', 'value': str(residual[column])})
    if residual[-1] <= 0:
        assert zero_reasons  # gamma=-sum(lambda_extension)+r_t>0.
    return {'zero_columns': sorted(zero_reasons), 'one_columns': sorted(one_reasons),
        'zero_reasons': zero_reasons, 'one_reasons': one_reasons,
        'conflicting_columns': sorted(set(zero_reasons)&set(one_reasons)),
        'positive_t_residual_contradicts_original_feasibility': residual[-1] > 0,
        'derivation': 'insert any original feasible x at t=0; each nonnegative slack in B-gamma*t=0 must vanish'}


def check_point(arrays, variables, numerators, denominator, seconds=60):
    assert type(denominator) is int and denominator > 0 and 0 < seconds <= 60
    assert len(numerators) == variables and all(type(v) is int and 0 <= v <= denominator for v in numerators)
    started = time.monotonic()
    deadline = started+seconds
    pointer, index, data = arrays['row_pointers'], arrays['column_indices'], arrays['coefficients']
    lower, upper = arrays['row_lower'], arrays['row_upper']
    visited = 0
    for row in range(len(lower)):
        if row % 128 == 0:
            budget(deadline)
        value = 0
        for p in range(int(pointer[row]), int(pointer[row+1])):
            value += int(data[p])*numerators[int(index[p])]
            visited += 1
        assert int(lower[row])*denominator <= value <= int(upper[row])*denominator, ('violated exact row', row)
    budget(deadline)
    return {'status': 'all finite-box rational primal coordinates and ranged rows checked exactly',
        'variables_checked': variables, 'rows_checked': len(lower), 'nonzeros_checked': visited,
        'positive_original_selectors': sum(value > 0 for value in numerators[:-1]),
        't_numerator': str(numerators[-1]), 'common_denominator': str(denominator),
        'strictly_positive_t': numerators[-1] > 0,
        'rules_out_any_remaining_identically_zero_selector': numerators[-1] > 0,
        'binary_incidence_or_graph_claimed': False,
        'check_seconds': time.monotonic()-started}


def integer_candidates(values, with_objective, deadline):
    """Discovery only; every yielded candidate still needs check_bound."""
    assert all(isfinite(float(v)) for v in values)
    support = [(i, float(v)) for i, v in enumerate(values) if v != 0]
    if not support:
        return
    maximum = max(abs(v) for i, v in support)
    normalized = support if with_objective else [(i, v/maximum) for i, v in support]
    seen = set()
    methods = [('scale', s) for s in (1, 2, 4, 8, 16, 64, 256, 4096, 65536, 1000000)]
    methods += [('fraction', d) for d in (1, 2, 4, 16, 64, 256, 4096, 1000000)]
    for method, parameter in methods:
        budget(deadline)
        if method == 'scale':
            entries = [[i, round(value*parameter)] for i, value in normalized]
            entries = [[i, v] for i, v in entries if v]
            gamma = parameter if with_objective else 0
        else:
            fractions, scale = [], 1
            refused = False
            for k, (i, value) in enumerate(normalized):
                if k % 128 == 0:
                    budget(deadline)
                f = Fraction(value).limit_denominator(parameter)
                if f:
                    scale = lcm(scale, f.denominator)
                    if scale.bit_length() > 4096:
                        refused = True
                        break
                    fractions.append((i, f))
            if refused:
                continue
            entries = [[i, int(f*scale)] for i, f in fractions]
            gamma = scale if with_objective else 0
        common = gcd(gamma, *(abs(v) for i, v in entries))
        if not common:
            continue
        gamma //= common
        entries = [[i, v//common] for i, v in entries]
        for sign in (-1, 1):
            candidate = [[i, sign*v] for i, v in entries]
            key = (gamma, tuple((i, v) for i, v in candidate))
            if key in seen:
                continue
            seen.add(key)
            yield candidate, gamma, {'method': method, 'parameter': parameter, 'orientation': sign}


def point_candidates(values, deadline):
    assert all(isfinite(float(v)) for v in values)
    sanitized = [0.0 if abs(float(v)) < 1e-12 else
                 1.0 if abs(float(v)-1) < 1e-12 else float(v) for v in values]
    seen = set()
    for limit in (1, 2, 4, 16, 64, 256, 4096, 1000000, 1000000000):
        budget(deadline)
        fractions, denominator = [], 1
        refused = False
        for value in sanitized:
            fraction = Fraction(value).limit_denominator(limit)
            denominator = lcm(denominator, fraction.denominator)
            if denominator.bit_length() > 4096:
                refused = True
                break
            fractions.append(fraction)
        if refused:
            continue
        numerators = [int(value*denominator) for value in fractions]
        common = gcd(denominator, *(abs(value) for value in numerators))
        numerators = [value//common for value in numerators]
        denominator //= common
        key = (denominator, tuple(numerators))
        if key not in seen:
            seen.add(key)
            yield numerators, denominator, {'denominator_limit': limit,
                'proposal_sanitization': 'values within1e-12 of0 or1 replaced by that endpoint; no feasibility inferred'}


def toy_arrays(rows, lower, upper):
    data, index, pointer = [], [], [0]
    for row in rows:
        for column, value in enumerate(row):
            if value:
                data.append(value)
                index.append(column)
        pointer.append(len(data))
    return {'coefficients': data, 'column_indices': index, 'row_pointers': pointer,
            'row_lower': lower, 'row_upper': upper}


def controls():
    C = [[1, 1, 0], [1, 0, -1], [0, 1, -1]]
    half = toy_arrays(C, [1, 0, 0], [1, 1, 1])
    bound = check_bound(half, 3, [[0, 1], [1, -1], [2, -1]], 2, 1)
    assert bound['objective_upper_bound_numerator'] == '1'
    assert check_point(half, 3, [1, 1, 1], 2, 1)['strictly_positive_t']
    zero = toy_arrays(C, [0, 0, 0], [0, 1, 1])
    bound = check_bound(zero, 3, [[0, 1], [1, -1], [2, -1]], 2, 1)
    assert bound['objective_upper_bound_numerator'] == '0'
    assert face_implications(bound, [[0, 1], [1, -1], [2, -1]], 1, [10, 20])['zero_columns'] == [10, 20]
    impossible = toy_arrays([[1, 1, 0]], [3], [3])
    bound = check_bound(impossible, 3, [[0, -1]], 0, 1)
    assert bound['objective_upper_bound_numerator'] == '-1'
    rejected = 0
    for point, denominator in (([0, 0, 0], 1), ([3, 0, 0], 2), ([2, 0, 2], 2)):
        try:
            check_point(half, 3, point, denominator, 1)
        except AssertionError:
            rejected += 1
    assert rejected == 3
    return {'sharp_maxmin_half_control': True, 'exact_zero_face_control': True,
        'finite_upper_bound_Farkas_control': True,
        'invalid_rational_points_rejected': rejected, 'optimizer_called': False}
