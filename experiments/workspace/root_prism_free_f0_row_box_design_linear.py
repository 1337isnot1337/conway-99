"""One symmetric shared-edge LP for the saved60-triple row-box design.

All1220 edges have bounds0..1 and satisfy the1080 mixed and60 degree
equations. Upper bounds are represented by explicit nonnegative slacks,
so an infeasibility ray has a simple complete integer verifier. A
numerical feasible point is accepted only after exact rational replay.
No outside pair-cap inequality or binary graph claim enters this LP.
"""

import argparse
from fractions import Fraction
import hashlib
import json
from math import gcd, isfinite, lcm
from pathlib import Path
import time

import root_prism_free_f0_row_box_design_exterior as exterior


ROOT, LOGS = exterior.ROOT, exterior.LOGS
digest, canonical, portable = exterior.digest, exterior.canonical, exterior.portable


def save(path, record):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(record, indent=2)+'\n')
    temporary.replace(path)


def verify_point(rows, n, values):
    assert len(values) == n and all(isinstance(value, Fraction) and 0 <= value <= 1 for value in values)
    assert all(sum(values[b] for b in row['support']) == row['rhs'] for row in rows)
    return {'equations_checked': len(rows), 'exact_lower_and_upper_bounds_checked': n,
            'nonzero_edges': sum(value > 0 for value in values),
            'fractional_edges': sum(value.denominator != 1 for value in values),
            'sum_edge_weights': [sum(values).numerator, sum(values).denominator]}


def verify_ray(rows, n, ray):
    m = len(rows)
    assert len(ray) == m+n and all(type(value) is int for value in ray)
    upper = ray[m:]
    assert all(value >= 0 for value in upper)
    coefficients = list(upper)
    for row, weight in zip(rows, ray[:m]):
        for b in row['support']:
            coefficients[b] += weight
    assert min(coefficients) >= 0
    rhs = sum(row['rhs']*weight for row, weight in zip(rows, ray[:m]))+sum(upper)
    assert rhs < 0
    return {'rhs_dot_product': rhs, 'minimum_primary_coefficient': min(coefficients),
            'minimum_upper_slack_coefficient': min(upper),
            'nonzero_row_multipliers': sum(value != 0 for value in ray),
            'maximum_absolute_multiplier': max(map(abs, ray)),
            'orientation': 'E^T ray>=0 and rhs^T ray<0 for every nonnegative primary and upper slack'}


def controls():
    toy = [{'support': [0], 'rhs': 2}]
    assert verify_ray(toy, 1, [-1, 1])['rhs_dot_product'] == -1
    rejected = 0
    for vector in ([1, -1], [1, 1], [-2, 1], [0, 0]):
        try:
            verify_ray(toy, 1, vector)
        except AssertionError:
            rejected += 1
    assert rejected == 4
    assert verify_point([{'support': [0, 1], 'rhs': 1}], 2,
                        [Fraction(1, 3), Fraction(2, 3)])['fractional_edges'] == 2
    return {'positive_integer_Farkas_control': True, 'invalid_rays_rejected': rejected,
            'exact_fractional_capacity_control': True, 'optimizer_or_solver_called': False}


def load(model_path):
    model = exterior.checked_model(model_path)
    data = exterior.inputs()
    assert json.loads(canonical(data)) == model['data']
    rows = exterior.linear_rows(data)
    assert rows == model['linear_rows']
    assert hashlib.sha256(canonical(rows)).hexdigest() == model['LP_inventory']['rows_sha256']
    n, m = len(data['edge_domain']), len(rows)
    assert (n, m) == (1220, 1140)
    return model, data, rows


def preparation(model_path):
    model, _, rows = load(model_path)
    return {'status': 'one symmetric1220-edge LP prepared; no query',
        'source_sha256': digest(Path(__file__)), 'exterior_source_sha256': digest(Path(exterior.__file__)),
        'model': portable(model_path), 'model_sha256': digest(model_path),
        'candidate_sha256': exterior.CANDIDATE_SHA, 'LP_inventory': model['LP_inventory'],
        'maximum_total_seconds': 60, 'maximum_optimizer_calls': 1,
        'solver': 'HiGHS simplex', 'threads': 1, 'objective': 'zero feasibility objective',
        'standard_form': 'original1140 equations; x_e+s_e=1 for all1220 edges; every variable nonnegative',
        'point_acceptance': 'all1220 rational bounds and1140 exact equations',
        'ray_acceptance': 'all2440 exact coefficient signs and strictly negative RHS',
        'pair_caps_in_LP': False, 'binary_or_graph_feasibility_claimed': False,
        'scope': 'one saved first incidence, second component and alignment/incidence free',
        'controls': controls(), 'optimizer_or_SAT_called': False}


def primitive(vector):
    divisor = gcd(*(abs(value) for value in vector))
    return None if not divisor else [value//divisor for value in vector]


def ray_candidates(values):
    seen = set()
    for scale in (1, 2, 3, 4, 6, 12, 24, 60, 120, 720, 4096):
        candidate = primitive([round(scale*float(value)) for value in values])
        if candidate is not None and tuple(candidate) not in seen:
            seen.add(tuple(candidate))
            yield candidate, {'rounding_scale': scale}
    for bound in (1, 2, 3, 4, 6, 12, 24, 60, 120, 1000, 1000000):
        values_q = [Fraction(float(value)).limit_denominator(bound) for value in values]
        denominator = lcm(*(value.denominator for value in values_q))
        if denominator.bit_length() > 4096:
            continue
        candidate = primitive([int(value*denominator) for value in values_q])
        if candidate is not None and tuple(candidate) not in seen:
            seen.add(tuple(candidate))
            yield candidate, {'rational_denominator_bound': bound}


def fixed_capacity_potentials(rows, data, ray):
    # Eliminate the degree multipliers by using sum(q_a)=24 and |h_b|=3.
    # Multiplying by3 avoids denominators and preserves all exact gaps.
    potentials = [[0]*18 for _ in range(60)]
    for row, coefficient in zip(rows, ray[:len(rows)]):
        v = row['vertex']
        if row['kind'] == 'degree':
            for i in range(18):
                potentials[v][i] -= coefficient
        else:
            potentials[v][row['core_vertex']] -= 3*coefficient
    demand = sum(sum(x*q for x, q in zip(vector, target))
                 for vector, target in zip(potentials, data['targets']))
    edge_weights = [sum(potentials[a][i] for i in data['design'][b])
                   +sum(potentials[b][i] for i in data['design'][a]) for a, b in data['edge_domain']]
    positive_capacity = sum(max(weight, 0) for weight in edge_weights)
    assert demand > positive_capacity >= 0
    assert demand == -3*sum(row['rhs']*value for row, value in zip(rows, ray[:len(rows)]))
    assert all(weight <= 3*upper for weight, upper in zip(edge_weights, ray[len(rows):]))
    return {'integer_potentials60_by18': potentials, 'total_weighted_demand': demand,
            'complete_internal_positive_edge_capacity': positive_capacity,
            'strict_gap': demand-positive_capacity,
            'universal_selector_cut_not_assembled_here': True}


def run(preparation_path, output, seconds):
    assert not output.exists() and 0 < seconds <= 60
    started = time.monotonic()
    prepared = exterior.load_json(preparation_path)
    model_path = ROOT/prepared['model']
    assert preparation(model_path) == prepared
    model, data, rows = load(model_path)
    n, m = 1220, len(rows)
    record = {'status': 'running one bounded shared-edge LP; no exact result yet',
        'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation_path),
        'model_sha256': digest(model_path), 'candidate_sha256': exterior.CANDIDATE_SHA,
        'requested_total_seconds': seconds, 'optimizer_calls': 0,
        'exact_linear_feasibility': False, 'exact_fixed_design_infeasibility': False,
        'binary_or_full_graph_constructed': False, 'whole_component_excluded': False}
    save(output, record)
    try:
        import highspy
        import numpy as np
        from scipy import sparse
        rr, cc = [], []
        for i, row in enumerate(rows):
            for b in row['support']:
                rr.append(i); cc.append(b)
        for b in range(n):
            rr.extend([m+b, m+b]); cc.extend([b, n+b])
        matrix = sparse.csc_matrix((np.ones(len(rr)), (rr, cc)), shape=(m+n, 2*n))
        rhs = np.array([row['rhs'] for row in rows]+[1]*n, dtype=float)
        assert matrix.nnz == model['LP_inventory']['explicit_upper_slack_standard_form_nonzeros']
        lp = highspy.HighsLp()
        lp.num_col_, lp.num_row_ = 2*n, m+n
        lp.col_cost_, lp.col_lower_ = np.zeros(2*n), np.zeros(2*n)
        lp.col_upper_ = np.full(2*n, highspy.kHighsInf)
        lp.row_lower_, lp.row_upper_ = rhs, rhs
        lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
        lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = matrix.indptr, matrix.indices, matrix.data
        solver = highspy.Highs()
        remaining = seconds-(time.monotonic()-started)
        if remaining <= 0:
            record['status'] = 'UNKNOWN: preparation exhausted total budget; optimizer not called'
        else:
            for name, value in [('output_flag', False), ('threads', 1), ('solver', 'simplex'),
                                ('presolve', 'on'), ('time_limit', remaining)]:
                assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
            assert solver.passModel(lp) == highspy.HighsStatus.kOk
            record['requested_optimizer_seconds'] = remaining
            record['optimizer_calls'] = 1
            save(output, record)
            solver.run()
            status = solver.getModelStatus()
            record['numerical_status'] = str(status)
            record['optimizer_return_seconds'] = time.monotonic()-started
            if status == highspy.HighsModelStatus.kOptimal:
                values = list(map(float, solver.getSolution().col_value[:n]))
                assert all(isfinite(value) for value in values)
                record['numerical_primary_hex'] = [value.hex() for value in values]
                exact = [Fraction(value).limit_denominator(1000000) for value in values]
                try:
                    checked = verify_point(rows, n, exact)
                except AssertionError:
                    record['status'] = 'numerical feasible proposal; exact rational reconstruction failed, unresolved'
                else:
                    record.update(status='exact rational symmetric mixed/degree point verified; pair caps and integrality untested',
                                  rational_primary=[[value.numerator, value.denominator] for value in exact],
                                  exact_point_check=checked, exact_linear_feasibility=True)
            elif status == highspy.HighsModelStatus.kInfeasible:
                record['status'] = 'numerical infeasible without an exact ray; no exclusion'
                _, exists, numerical = solver.getDualRay()
                if exists:
                    numerical = list(map(float, numerical))
                    assert len(numerical) == m+n and all(isfinite(value) for value in numerical)
                    record['numerical_ray_hex'] = [value.hex() for value in numerical]
                    accepted = False
                    for vector, method in ray_candidates(numerical):
                        for sign in (1, -1):
                            ray = [sign*value for value in vector]
                            try:
                                checked = verify_ray(rows, n, ray)
                            except AssertionError:
                                continue
                            record.update(status='exact integer symmetric-row Farkas contradiction; fixed first design only',
                                integer_ray=ray, exact_ray_check=checked, ray_reconstruction=method,
                                fixed_capacity_potentials=fixed_capacity_potentials(rows, data, ray),
                                exact_fixed_design_infeasibility=True)
                            accepted = True
                            break
                        if accepted:
                            break
            else:
                record['status'] = 'UNKNOWN: nonoptimal bounded LP status; no exact conclusion'
    except Exception as error:
        record.update(status='ERROR: shared-edge LP stopped; no unchecked conclusion',
                      error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        record['elapsed_seconds'] = time.monotonic()-started
        record['cooperative_budget_overrun_seconds'] = max(0, record['elapsed_seconds']-seconds)
        save(output, record)
    print(json.dumps({k: v for k, v in record.items() if k not in
        ('numerical_primary_hex', 'rational_primary', 'numerical_ray_hex', 'integer_ray', 'fixed_capacity_potentials')}, indent=2), flush=True)


def replay(preparation_path, result_path, output):
    assert not output.exists()
    prepared = exterior.load_json(preparation_path)
    model_path = ROOT/prepared['model']
    assert preparation(model_path) == prepared
    _, data, rows = load(model_path)
    result = exterior.load_json(result_path)
    assert result['source_sha256'] == digest(Path(__file__))
    assert result['preparation_sha256'] == digest(preparation_path)
    assert result['model_sha256'] == digest(model_path)
    assert result['optimizer_calls'] in (0, 1)
    assert not (result['exact_linear_feasibility'] and result['exact_fixed_design_infeasibility'])
    point, ray = None, None
    if result['exact_linear_feasibility']:
        values = [Fraction(n, d) for n, d in result['rational_primary']]
        point = verify_point(rows, 1220, values)
        assert point == result['exact_point_check']
    if result['exact_fixed_design_infeasibility']:
        ray = verify_ray(rows, 1220, result['integer_ray'])
        assert ray == result['exact_ray_check']
        assert fixed_capacity_potentials(rows, data, result['integer_ray']) == result['fixed_capacity_potentials']
    report = {'status': 'complete shared-edge row domain and exact LP certificate replay PASS',
        'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation_path),
        'result_sha256': digest(result_path), 'model_sha256': digest(model_path),
        'exact_linear_feasibility': point is not None,
        'exact_fixed_design_infeasibility': ray is not None,
        'point_check': point, 'ray_check': ray,
        'optimizer_or_solver_called': False, 'whole_component_excluded': False,
        'binary_or_full_graph_constructed': False}
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--model', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    execute = commands.add_parser('run')
    execute.add_argument('--preparation', type=Path, required=True)
    execute.add_argument('--output', type=Path, required=True)
    execute.add_argument('--seconds', type=float, default=60)
    check = commands.add_parser('replay')
    check.add_argument('--preparation', type=Path, required=True)
    check.add_argument('--result', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        assert not args.output.exists()
        report = preparation(args.model.resolve())
        save(args.output, report)
        print(json.dumps(report, indent=2), flush=True)
    elif args.command == 'run':
        run(args.preparation.resolve(), args.output.resolve(), args.seconds)
    else:
        replay(args.preparation.resolve(), args.result.resolve(), args.output.resolve())
