"""One sparse real diagnostic for unresolved35-core case4.

The baseline has all original Gram equations, signature/triple capacities,
and0<=x<=1. A separately labelled variant adds the30 previously certified
binary no-good inequalities. These inequalities need not hold for every
point of the original real cone. An infeasibility claim requires an exact
integer Farkas certificate; numerical statuses alone exclude nothing.
"""

import argparse
from collections import Counter
from fractions import Fraction
import gzip
from itertools import combinations
import json
from math import gcd, lcm
from pathlib import Path
import time

import complement_rook_35core_incidence as original


ROOT, LOGS = original.ROOT, original.LOGS
BASE = LOGS/'complement-rook-35core-first-local-sweep01/case0004-model.json'
CENSUS_MANIFEST = LOGS/'complement-rook-35core-first-local-downdates01-artifacts.json'
CENSUS_SHA = '21c3aeddd103d6146699a0f0efc88b80e348c9f066db1402de9d81432994c185'
CERTIFICATE = LOGS/'complement-rook-35core-first-local-downdates01/case0004.json.gz'
digest, canonical, portable = original.digest, original.canonical, original.portable


def inventory():
    data = original.load(4)
    base = original.checked_model(BASE)
    domain, _, case, record, _, gram, supports, groups, triples, masks = data
    assert base['case'] == case and original.domains.sha(canonical(record)) == base['domain_record_sha256']
    equations, seen, coverage = [], {}, []
    positions = [(i, j) for i in range(35) for j in range(i, 35)]
    pair_supports = dict(zip(positions, supports))
    for (i, j), members in zip(positions, supports):
        target = gram[i][j]
        key = tuple(members), target
        if key not in seen:
            seen[key] = len(equations)
            equations.append({'kind': 'Gram equality', 'label': [i, j], 'support': members, 'rhs': target})
        coverage.append([i, j, seen[key]])
    assert coverage == base['formula']['Gram_equation_coverage']
    capacities = []
    multiplicity = []
    for source, members in sorted(groups.items()):
        if len(members) > 1:
            multiplicity.append([source, members])
            capacities.append({'kind': 'original signature capacity', 'label': [source], 'support': members, 'rhs': 1})
    assert multiplicity == base['formula']['original_signature_multiplicity_rows']
    extra_triples, triple_coverage = [], []
    for sites, members in sorted(triples.items()):
        if len(members) <= 1:
            continue
        quota_one = [pair for pair in combinations(sites, 2) if gram[pair[0]][pair[1]] == 1]
        if quota_one:
            pair = min(quota_one)
            assert set(members) <= set(pair_supports[pair])
            triple_coverage.append({'triple': list(sites), 'support': len(members), 'implied_by_Gram_pair': list(pair)})
        else:
            extra_triples.append([list(sites), members])
            capacities.append({'kind': 'additional triple capacity', 'label': list(sites), 'support': members, 'rhs': 1})
            triple_coverage.append({'triple': list(sites), 'support': len(members), 'extra_row_index': len(extra_triples)-1})
    assert extra_triples == base['formula']['additional_triple_rows']
    assert triple_coverage == base['formula']['triple_capacity_coverage']
    capacities.extend({'kind': 'column upper bound', 'label': [i], 'support': [i], 'rhs': 1}
                      for i in range(len(masks)))
    assert digest(CENSUS_MANIFEST) == CENSUS_SHA
    hashes = {item['path']: item['sha256'] for item in json.loads(CENSUS_MANIFEST.read_text())['artifacts']}
    assert digest(CERTIFICATE) == hashes[portable(CERTIFICATE)]
    saved = json.loads(gzip.decompress(CERTIFICATE.read_bytes()))
    assert saved['attachment_columns'] == record['columns'] and saved['Gram'] == gram
    witnesses = []
    cuts = []
    for witness in saved['scan']['additional_binary_exclusion_witnesses']:
        a, b = witness['columns']
        vector = witness['negative_vector']
        value = sum(vector[i]*gram[i][j]*vector[j] for i in range(35) for j in range(35))
        value -= sum(sum(vector[i] for i in range(35) if masks[c] >> i & 1)**2 for c in (a, b))
        assert value == witness['negative_quadratic_value'] < 0
        cuts.append({'kind': 'certified binary no-good', 'label': [a, b], 'support': [a, b], 'rhs': 1})
        witnesses.append({'columns': [a, b], 'negative_vector': vector, 'negative_value': value})
    assert len(cuts) == 30 and len(masks) == 1214
    return {
        'source_sha256': digest(Path(__file__)),
        'original_source_hashes': base['source_hashes'], 'case_index': 4,
        'base_model': portable(BASE), 'base_model_sha256': digest(BASE),
        'domain_record_sha256': base['domain_record_sha256'],
        'original_CNF_sha256': base['cnf_sha256'],
        'columns': record['columns'], 'column_masks35': masks, 'Gram': gram,
        'equalities': equations, 'capacities': capacities, 'optional_binary_cuts': cuts,
        'optional_binary_cut_negative_witnesses': witnesses,
        'all630_Gram_positions': coverage, 'nontrivial_triple_coverage': triple_coverage,
        'counts': {'primary_columns': len(masks), 'Gram_equalities': len(equations),
                   'capacity_rows': len(capacities), 'optional_binary_cuts': len(cuts),
                   'capacity_kinds': dict(Counter(row['kind'] for row in capacities))},
        'baseline_column_lower_bound': 0, 'baseline_column_upper_bound': 1,
        'extra_binary_cuts_not_claimed_valid_for_the_unaugmented_fractional_cone': True,
        'solver_called_during_inventory': False,
    }


def rows(model, with_cuts):
    inequalities = model['capacities']+(model['optional_binary_cuts'] if with_cuts else [])
    return model['equalities']+inequalities, len(model['equalities'])


def verify_ray(model, with_cuts, ray):
    all_rows, eq_count = rows(model, with_cuts)
    assert len(ray) == len(all_rows) and all(type(v) is int for v in ray)
    n = model['counts']['primary_columns']
    coefficients = [0]*n
    for i, (row, value) in enumerate(zip(all_rows, ray)):
        if i >= eq_count:
            assert value >= 0  # The independent nonnegative slack column.
        for c in row['support']:
            coefficients[c] += value
    assert min(coefficients) >= 0
    rhs = sum(value*row['rhs'] for value, row in zip(ray, all_rows))
    assert rhs < 0
    return {'rhs_dot_product': rhs, 'minimum_primary_coefficient': min(coefficients),
            'nonzero_ray_rows': sum(v != 0 for v in ray),
            'nonnegative_slack_coefficients_checked': len(all_rows)-eq_count,
            'exact_orientation': 'E^T y>=0, b^T y<0, with all primal variables including slacks nonnegative'}


def verify_point(model, with_cuts, point):
    assert len(point) == model['counts']['primary_columns'] and all(0 <= x <= 1 for x in point)
    all_rows, eq_count = rows(model, with_cuts)
    for i, row in enumerate(all_rows):
        value = sum(point[c] for c in row['support'])
        assert value == row['rhs'] if i < eq_count else value <= row['rhs']
    return {'all_equalities': eq_count, 'all_capacity_rows': len(all_rows)-eq_count,
            'strictly_fractional_columns': sum(0 < x < 1 for x in point),
            'positive_columns': sum(x > 0 for x in point), 'binary_incidence_claimed': False}


def query(model, with_cuts, seconds):
    import highspy
    import numpy as np
    from scipy import sparse

    assert 0 < seconds <= 10
    all_rows, eq_count = rows(model, with_cuts)
    n, m = model['counts']['primary_columns'], len(all_rows)
    rr, cc = [], []
    for i, row in enumerate(all_rows):
        rr.extend([i]*len(row['support']))
        cc.extend(row['support'])
        if i >= eq_count:
            rr.append(i)
            cc.append(n+i-eq_count)
    matrix = sparse.csc_matrix((np.ones(len(rr), dtype=np.int64), (rr, cc)), shape=(m, n+m-eq_count))
    rhs = np.array([row['rhs'] for row in all_rows], dtype=np.int64)
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = matrix.shape[1], matrix.shape[0]
    lp.col_cost_ = np.zeros(matrix.shape[1])
    lp.col_lower_ = np.zeros(matrix.shape[1])
    lp.col_upper_ = np.full(matrix.shape[1], highspy.kHighsInf)
    lp.row_lower_ = rhs.astype(float)
    lp.row_upper_ = rhs.astype(float)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = matrix.indptr, matrix.indices, matrix.data.astype(float)
    solver = highspy.Highs()
    for option, value in [('output_flag', False), ('threads', 1), ('time_limit', seconds), ('presolve', 'off')]:
        assert solver.setOptionValue(option, value) == highspy.HighsStatus.kOk
    assert solver.passModel(lp) == highspy.HighsStatus.kOk
    started = time.monotonic()
    solver.run()
    status = solver.getModelStatus()
    result = {'variant': 'with30_binary_no_good_rows' if with_cuts else 'unaugmented_real_cone',
              'numerical_status': str(status), 'requested_seconds': seconds,
              'solve_seconds': time.monotonic()-started, 'threads': 1,
              'matrix_shape_including_slacks': list(matrix.shape), 'matrix_nonzeros': matrix.nnz,
              'exact_infeasibility_claimed': False, 'exact_feasibility_claimed': False}
    if status == highspy.HighsModelStatus.kInfeasible:
        _, exists, proposed = solver.getDualRay()
        if exists:
            result['numerical_ray'] = list(map(float, proposed))
            for limit in (1, 2, 4, 16, 64, 256, 4096, 1000000):
                rational = [Fraction(float(v)).limit_denominator(limit) for v in proposed]
                scale = lcm(*(x.denominator for x in rational))
                ray = [int(x*scale) for x in rational]
                common = gcd(*(abs(v) for v in ray))
                if common:
                    ray = [v//common for v in ray]
                for sign in (1, -1):
                    candidate = [sign*v for v in ray]
                    try:
                        check = verify_ray(model, with_cuts, candidate)
                    except AssertionError:
                        continue
                    result.update(status='exact rational Farkas certificate verified', ray=candidate,
                                  exact_check=check, exact_infeasibility_claimed=True)
                    return result
        result['status'] = 'numerical infeasibility only; no exact exclusion'
    elif status == highspy.HighsModelStatus.kOptimal:
        values = list(map(float, solver.getSolution().col_value[:n]))
        result['numerical_point'] = values
        residual = [sum(values[c] for c in row['support'])-row['rhs'] for row in all_rows]
        result['maximum_equality_residual'] = max(map(abs, residual[:eq_count]))
        result['maximum_capacity_violation'] = max([0.0]+residual[eq_count:])
        result['status'] = 'numerically feasible relaxation; rational reconstruction not yet verified'
        for limit in (1, 2, 4, 12, 60, 360, 4096, 1000000):
            point = [Fraction(v).limit_denominator(limit) for v in values]
            try:
                check = verify_point(model, with_cuts, point)
            except AssertionError:
                continue
            result.update(status='exact rational feasible relaxation point verified',
                          point=[[v.numerator, v.denominator] for v in point], exact_check=check,
                          exact_feasibility_claimed=True)
            break
    else:
        result['status'] = 'LP limit or other numerical status; no conclusion'
    return result


def run(model_path, output, seconds):
    assert not output.exists()
    saved = json.loads(gzip.decompress(model_path.read_bytes()))
    assert saved == inventory()
    result = {'status': 'one-case real diagnostic', 'model_sha256': digest(model_path),
              'source_sha256': digest(Path(__file__)), 'case_index': 4, 'variants': [],
              'new_SAT_queries': 0, 'whole_local_set_excluded': False}
    for with_cuts in (False, True):
        result['variants'].append(query(saved, with_cuts, seconds))
        output.write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({k: v for k, v in result['variants'][-1].items() if k not in ('ray', 'numerical_ray', 'point', 'numerical_point')}, indent=2), flush=True)
        if result['variants'][-1]['exact_infeasibility_claimed']:
            break


def replay(model_path, result_path, output):
    assert not output.exists()
    model = json.loads(gzip.decompress(model_path.read_bytes()))
    assert model == inventory()
    result = json.loads(result_path.read_text())
    assert result['source_sha256'] == digest(Path(__file__)) and result['model_sha256'] == digest(model_path)
    reports = []
    for record in result['variants']:
        with_cuts = record['variant'] == 'with30_binary_no_good_rows'
        if record['exact_infeasibility_claimed']:
            report = verify_ray(model, with_cuts, record['ray'])
        elif record['exact_feasibility_claimed']:
            report = verify_point(model, with_cuts, [Fraction(*x) for x in record['point']])
        else:
            report = {'status': 'only numerical output is bound; no exact conclusion'}
        reports.append({'variant': record['variant'], 'check': report})
    answer = {'status': 'inventory and all claimed exact LP certificates replayed',
              'source_sha256': digest(Path(__file__)), 'model_sha256': digest(model_path),
              'result_sha256': digest(result_path), 'variants': reports, 'optimizer_called': False}
    output.write_text(json.dumps(answer, indent=2)+'\n')
    print(json.dumps(answer, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=('prepare', 'run', 'replay'))
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--result', type=Path)
    parser.add_argument('--seconds', type=float, default=8)
    args = parser.parse_args()
    if args.mode == 'prepare':
        assert not args.model.exists()
        model = inventory()
        args.model.write_bytes(gzip.compress(canonical(model)+b'\n', mtime=0))
        print(json.dumps({'model_sha256': digest(args.model), 'counts': model['counts'], 'source_sha256': digest(Path(__file__))}, indent=2))
    elif args.mode == 'run':
        assert args.output
        run(args.model, args.output, args.seconds)
    else:
        assert args.result and args.output
        replay(args.model, args.result, args.output)
