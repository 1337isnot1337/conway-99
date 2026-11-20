"""At most five LP/row-separation rounds for the one frozen case4 core.

All original Gram/capacity rows and30 binary no-goods remain. Two checked
row inequalities seed the loop. Discovery uses floating points; accepted
cuts and any infeasibility certificate have separate integer replay.
No SAT query or wider matching search is exposed.
"""

import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from math import gcd, isfinite, lcm
from pathlib import Path
import time

import complement_rook_35core_case0004_lp as original_lp
import complement_rook_35core_case0004_row_separation as separator


ROOT, LOGS = separator.ROOT, separator.LOGS
BASE_MODEL = LOGS / 'complement-rook-35core-case0004-lp-model.json.gz'
BASE_SHA = '18e7b79a7e83c1c40f0c0c29301703400f26b42401f0b07a2f21783a298119a6'
INITIAL_RESULT = LOGS / 'complement-rook-35core-case0004-row-separation-run01.json'
INITIAL_SHA = 'e758fffa8bbeb80f0fc2edd3bdb9b9fc8b992a27303679df9d9658f0c9aa18f3'
DEPENDENCIES = {
    'complement_rook_35core_case0004_lp.py': 'cba1a71b01cb48e33bfd0a82113b35d3c5b846176dfb244369660d8762320d02',
    'complement_rook_35core_case0004_exterior_rows.py': 'db88ab6af3b151dc233519efb052d1fc20bd40b251e01a61558a3c93ac709977',
    'complement_rook_35core_case0004_row_separation.py': 'a5a7f1a950de22e310484ec17c098eaaf19915b556d71cec67b191c4a1a79339',
}
digest, canonical, portable = separator.digest, separator.canonical, separator.portable


def sha(data):
    return hashlib.sha256(data).hexdigest()


def compact_cut(certificate):
    return {key: certificate[key] for key in ('target_column', 'integer_vector', 'positive_demand', 'positive_terms')}


def verify_cut(row_model, certificate):
    actual = separator.checked_integer_cut(row_model, certificate['target_column'], certificate['integer_vector'])
    assert compact_cut(actual) == certificate
    return actual


def cut_key(cut):
    common = gcd(cut['positive_demand'], *(w for b, w in cut['positive_terms']))
    return (cut['target_column'], cut['positive_demand'] // common,
            tuple((b, w // common) for b, w in cut['positive_terms']))


def load_inputs():
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert digest(BASE_MODEL) == BASE_SHA and digest(INITIAL_RESULT) == INITIAL_SHA
    original = json.loads(gzip.decompress(BASE_MODEL.read_bytes()))
    assert json.loads(canonical(original_lp.inventory())) == original
    row_model = separator.load(True)
    assert original['column_masks35'] == row_model['column_masks35']
    initial = json.loads(INITIAL_RESULT.read_text())
    assert initial['source_sha256'] == DEPENDENCIES['complement_rook_35core_case0004_row_separation.py']
    assert initial['model_sha256'] == separator.MODEL_SHA
    cuts = []
    for row in initial['rows']:
        if 'integer_certificate' in row:
            cut = compact_cut(row['integer_certificate'])
            verify_cut(row_model, cut)
            cuts.append(cut)
    assert [c['target_column'] for c in cuts] == [85, 628]
    return original, row_model, cuts


def all_rows(original, cuts):
    old, equality_count = original_lp.rows(original, True)
    rows = [{'kind': row['kind'], 'label': row['label'], 'terms': [[b, 1] for b in row['support']],
             'rhs': row['rhs']} for row in old]
    for index, cut in enumerate(cuts):
        terms = [[cut['target_column'], cut['positive_demand']]]
        terms.extend([b, -w] for b, w in cut['positive_terms'])
        terms.sort()
        assert len({b for b, w in terms}) == len(terms)
        rows.append({'kind': 'exact exterior-row inequality', 'label': [index, cut['target_column']],
                     'terms': terms, 'rhs': 0})
    return rows, equality_count


def row_inventory(rows, equality_count, n):
    return {'equations': equality_count, 'inequalities': len(rows) - equality_count,
            'standard_form_rows': len(rows), 'standard_form_variables': n + len(rows) - equality_count,
            'standard_form_nonzeros': sum(len(row['terms']) for row in rows) + len(rows) - equality_count,
            'row_inventory_sha256': sha(canonical(rows))}


def verify_farkas(rows, equality_count, n, ray):
    assert len(ray) == len(rows) and all(type(v) is int for v in ray)
    coefficients = [0] * n
    for index, (row, value) in enumerate(zip(rows, ray)):
        if index >= equality_count:
            assert value >= 0  # The coefficient of this row's nonnegative slack.
        for b, coefficient in row['terms']:
            coefficients[b] += value * coefficient
    assert min(coefficients) >= 0
    rhs = sum(value * row['rhs'] for value, row in zip(ray, rows))
    assert rhs < 0
    return {'rhs_dot_product': rhs, 'minimum_primary_coefficient': min(coefficients),
            'all_slack_coefficients_nonnegative': True, 'nonzero_ray_rows': sum(v != 0 for v in ray),
            'orientation': 'E^T ray>=0 and rhs^T ray<0, with all primary and slack variables nonnegative'}


def controls():
    rows = [{'terms': [[0, 1]], 'rhs': 2}, {'terms': [[0, 1]], 'rhs': 1}]
    assert verify_farkas(rows, 1, 1, [-1, 1])['rhs_dot_product'] == -1
    rejected = 0
    for ray in ([1, -1], [1, 1], [-2, 1], [0, 0]):
        try:
            verify_farkas(rows, 1, 1, ray)
        except AssertionError:
            rejected += 1
    assert rejected == 4
    return {'integer_Farkas_positive_control': True, 'invalid_ray_controls_rejected': rejected,
            'optimizer_or_solver_called': False}


def preparation():
    original, row_model, cuts = load_inputs()
    rows, equality_count = all_rows(original, cuts)
    n = original['counts']['primary_columns']
    inventory = row_inventory(rows, equality_count, n)
    assert (n, equality_count, len(rows)) == (1214, 397, 1841)
    return {'status': 'case4 full-LP and complete-positive-row loop prepared; no optimizer called',
            'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': DEPENDENCIES,
            'base_model': portable(BASE_MODEL), 'base_model_sha256': BASE_SHA,
            'row_domain_sha256': separator.MODEL_SHA,
            'initial_result': portable(INITIAL_RESULT), 'initial_result_sha256': INITIAL_SHA,
            'initial_exact_cuts': cuts, 'initial_inventory': inventory,
            'primary_columns': n, 'fixed_prior_binary_no_goods': 30,
            'full_candidate_row_universe': 1214, 'eligible_unordered_edges': 275578,
            'maximum_rounds': 5, 'maximum_requested_total_seconds': 60,
            'maximum_global_LP_seconds': 10, 'maximum_row_LP_seconds': 2, 'threads': 1,
            'proposal_rule': 'values<1e-9 become0; values>1-1e-9 become1; all other values unchanged',
            'row_order': 'every positive sanitized proposal column, in increasing column order',
            'cut_acceptance': 'exact integer products and positive RHS; normalized numerical gap>1e-8',
            'cuts_not_binary_weight_capped': True,
            'infeasibility_gate': 'exact integer Farkas replay against every full current standard-form column',
            'stop_conditions': ['no new checked integer separator on the complete positive support',
                                'global LP infeasible, with exact certificate required for exclusion',
                                'first nonoptimal LP, error, total time budget, or five completed rounds'],
            'controls': controls(), 'SAT_queries': 0,
            'scope': 'Only indexed35-core case4. Numerical points are discovery proposals; '
                     'they are not exact feasible points. Any actual-graph exclusion requires a checked Farkas ray.'}


def ray_candidates(values):
    for scale in (1, 2, 4, 8, 16, 32, 64, 128, 256, 1024, 4096):
        candidate = [round(float(v) * scale) for v in values]
        common = gcd(*(abs(v) for v in candidate))
        if common:
            yield [v // common for v in candidate], {'rounding_scale': scale}
    for limit in (1, 2, 4, 16, 64, 256, 4096, 1000000):
        fractions = [Fraction(float(v)).limit_denominator(limit) for v in values]
        denominator = lcm(*(f.denominator for f in fractions))
        if denominator.bit_length() > 4096:
            continue
        candidate = [int(f * denominator) for f in fractions]
        common = gcd(*(abs(v) for v in candidate))
        if common:
            yield [v // common for v in candidate], {'rational_denominator_limit': limit}


def global_query(original, cuts, seconds):
    import highspy
    import numpy as np
    from scipy import sparse

    assert 0 < seconds <= 10
    rows, equality_count = all_rows(original, cuts)
    n, m = original['counts']['primary_columns'], len(rows)
    rr, cc, vv = [], [], []
    for i, row in enumerate(rows):
        for b, coefficient in row['terms']:
            rr.append(i); cc.append(b); vv.append(coefficient)
        if i >= equality_count:
            rr.append(i); cc.append(n + i - equality_count); vv.append(1)
    matrix = sparse.csc_matrix((np.asarray(vv, dtype=np.int64), (rr, cc)),
                               shape=(m, n + m - equality_count))
    rhs = np.asarray([row['rhs'] for row in rows], dtype=np.int64)
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = matrix.shape[1], m
    lp.col_cost_, lp.col_lower_ = np.zeros(matrix.shape[1]), np.zeros(matrix.shape[1])
    lp.col_upper_ = np.full(matrix.shape[1], highspy.kHighsInf)
    lp.row_lower_, lp.row_upper_ = rhs.astype(float), rhs.astype(float)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = matrix.indptr, matrix.indices, matrix.data.astype(float)
    solver = highspy.Highs()
    for name, value in [('output_flag', False), ('threads', 1), ('presolve', 'on'), ('time_limit', seconds)]:
        assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
    assert solver.passModel(lp) == highspy.HighsStatus.kOk
    start = time.monotonic()
    solver.run()
    status = solver.getModelStatus()
    record = {'numerical_status': str(status), 'requested_seconds': seconds,
              'solve_seconds': time.monotonic() - start, 'exact_cut_count': len(cuts),
              'inventory': row_inventory(rows, equality_count, n),
              'exact_feasibility_claimed': False, 'exact_infeasibility_claimed': False}
    if status == highspy.HighsModelStatus.kOptimal:
        values = list(map(float, solver.getSolution().col_value[:n]))
        assert all(isfinite(v) and -1e-7 <= v <= 1 + 1e-7 for v in values)
        residuals = [sum(w * values[b] for b, w in row['terms']) - row['rhs'] for row in rows]
        record['numerical_point'] = values
        record['maximum_absolute_Gram_residual'] = max(abs(v) for v in residuals[:equality_count])
        record['maximum_capacity_violation'] = max([0.0] + residuals[equality_count:])
        record['status'] = 'numerical LP proposal only; no exact feasibility certificate'
    elif status == highspy.HighsModelStatus.kInfeasible:
        record['status'] = 'numerical infeasibility without an exact ray; no exclusion'
        _, exists, proposed = solver.getDualRay()
        if exists:
            record['numerical_dual_ray'] = list(map(float, proposed))
            for candidate, method in ray_candidates(proposed):
                for sign in (1, -1):
                    ray = [sign * v for v in candidate]
                    try:
                        check = verify_farkas(rows, equality_count, n, ray)
                    except AssertionError:
                        continue
                    record.update(status='exact integer Farkas certificate verified for this current case4 LP',
                                  exact_infeasibility_claimed=True, integer_farkas_ray=ray,
                                  reconstruction_method=method, exact_farkas_check=check)
                    return record
    else:
        record['status'] = 'nonoptimal global LP; stop without exclusion'
    return record


def save(path, value):
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def run(preparation_path, output, seconds, rounds):
    assert not output.exists() and 0 < seconds <= 60 and 1 <= rounds <= 5
    start = time.monotonic()
    expected = json.loads(gzip.decompress(preparation_path.read_bytes()))
    assert json.loads(canonical(preparation())) == expected
    original, row_model, cuts = load_inputs()
    keys = {cut_key(cut) for cut in cuts}
    result = {'status': 'running bounded case4 LP and positive-row separation loop',
              'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': DEPENDENCIES,
              'preparation': portable(preparation_path), 'preparation_sha256': digest(preparation_path),
              'requested_total_seconds': seconds, 'requested_rounds': rounds,
              'case_index': 4, 'exact_cuts': cuts, 'rounds': [], 'SAT_queries': 0,
              'exact_feasibility_claimed': False, 'exact_case4_exclusion_claimed': False,
              'whole_local_set_or_graph_excluded': False}
    def checkpoint():
        result['elapsed_seconds'] = time.monotonic() - start
        save(output, result)
    checkpoint()
    try:
        for round_index in range(rounds):
            remaining = seconds - (time.monotonic() - start)
            if remaining <= 0:
                result['status'] = 'total budget reached before next global LP; unresolved'
                break
            count_before = len(cuts)
            record = {'round_index': round_index, 'LP_cut_prefix_count': count_before,
                      'row_queries': [], 'new_cut_indices': [], 'complete_positive_support_separation': False}
            result['rounds'].append(record)
            checkpoint()
            global_result = global_query(original, cuts, min(10, remaining))
            record['global_LP'] = global_result
            checkpoint()
            if global_result['numerical_status'] != 'HighsModelStatus.kOptimal':
                if global_result['exact_infeasibility_claimed']:
                    result['status'] = 'exact case4 LP contradiction found; independent integer replay required'
                    result['exact_case4_exclusion_claimed'] = True
                else:
                    result['status'] = global_result['status']
                break
            raw = global_result['numerical_point']
            point = [0.0 if v < 1e-9 else 1.0 if v > 1 - 1e-9 else float(v) for v in raw]
            support = [a for a, value in enumerate(point) if value > 0]
            record['positive_sanitized_support'] = support
            record['discarded_tiny_positive_count'] = sum(0 < v < 1e-9 for v in raw)
            record['discarded_tiny_positive_sum'] = sum(v for v in raw if 0 < v < 1e-9)
            discovery_model = dict(row_model, proposal_values=point)
            stopped = False
            for target in support:
                remaining = seconds - (time.monotonic() - start)
                if remaining <= 0:
                    result['status'] = 'total budget during positive support; unvisited rows unresolved'
                    stopped = True
                    break
                row = separator.query(discovery_model, target, min(2, remaining))
                certificate = row.pop('integer_certificate', None)
                if certificate is not None:
                    cut = compact_cut(certificate)
                    verify_cut(row_model, cut)
                    key = cut_key(cut)
                    if key not in keys:
                        row['new_exact_cut_index'] = len(cuts)
                        record['new_cut_indices'].append(len(cuts))
                        cuts.append(cut)
                        keys.add(key)
                    else:
                        row['already_known_exact_cut'] = True
                record['row_queries'].append(row)
                checkpoint()
                if row['numerical_status'] != 'HighsModelStatus.kOptimal':
                    result['status'] = 'nonoptimal row query; unvisited rows unresolved'
                    stopped = True
                    break
            record['complete_positive_support_separation'] = len(record['row_queries']) == len(support)
            record['positive_support_size'] = len(support)
            record['visited_positive_rows'] = len(record['row_queries'])
            checkpoint()
            print(json.dumps({'round': round_index, 'positive_rows': len(support),
                              'visited': len(record['row_queries']), 'new_cuts': len(record['new_cut_indices']),
                              'total_cuts': len(cuts), 'elapsed_seconds': result['elapsed_seconds']}, indent=2), flush=True)
            if stopped:
                break
            if not record['new_cut_indices']:
                result['status'] = 'no new checked integer separator on full positive support; numerical proposal only'
                break
        else:
            result['status'] = 'five-round or requested round cap reached; case4 unresolved'
        result['exact_cut_count'] = len(cuts)
        result['new_exact_cuts'] = len(cuts) - 2
        result['cooperative_budget_overrun_seconds'] = max(0, time.monotonic() - start - seconds)
        checkpoint()
    except Exception as error:
        result.update(status='error; unverified progress not promoted', error_type=type(error).__name__, error_message=str(error))
        checkpoint()
        raise
    print(json.dumps({k: v for k, v in result.items() if k not in ('rounds', 'exact_cuts')}, indent=2), flush=True)


def replay(preparation_path, result_path, output):
    assert not output.exists()
    expected = json.loads(gzip.decompress(preparation_path.read_bytes()))
    assert json.loads(canonical(preparation())) == expected
    original, row_model, initial = load_inputs()
    result = json.loads(result_path.read_text())
    assert result['source_sha256'] == digest(Path(__file__))
    assert result['preparation_sha256'] == digest(preparation_path)
    assert result['exact_cuts'][:2] == initial
    cuts = result['exact_cuts']
    assert len({cut_key(cut) for cut in cuts}) == len(cuts)
    cut_checks = []
    for index, cut in enumerate(cuts):
        verify_cut(row_model, cut)
        cut_checks.append({'index': index, 'target': cut['target_column'],
                           'positive_demand': cut['positive_demand'], 'positive_terms': len(cut['positive_terms'])})
    rays, next_cut = [], 2
    for index, record in enumerate(result['rounds']):
        assert record['round_index'] == index and record['LP_cut_prefix_count'] == next_cut
        if 'global_LP' not in record:
            continue
        lp_result = record['global_LP']
        rows, eq = all_rows(original, cuts[:next_cut])
        assert lp_result['inventory'] == row_inventory(rows, eq, 1214)
        if lp_result['exact_infeasibility_claimed']:
            check = verify_farkas(rows, eq, 1214, lp_result['integer_farkas_ray'])
            assert check == lp_result['exact_farkas_check']
            rays.append({'round': index, 'check': check})
        if 'positive_sanitized_support' not in record:
            continue
        raw = lp_result['numerical_point']
        point = [0.0 if v < 1e-9 else 1.0 if v > 1 - 1e-9 else float(v) for v in raw]
        support = [a for a, v in enumerate(point) if v > 0]
        assert support == record['positive_sanitized_support']
        assert [row['target_column'] for row in record['row_queries']] == support[:len(record['row_queries'])]
        found = []
        for row in record['row_queries']:
            if 'new_exact_cut_index' in row:
                cut_index = row['new_exact_cut_index']
                assert cut_index == next_cut and cuts[cut_index]['target_column'] == row['target_column']
                gap = cuts[cut_index]['positive_demand'] * point[row['target_column']]
                gap -= sum(w * point[b] for b, w in cuts[cut_index]['positive_terms'])
                assert gap == row['numerical_proposal_gap']
                found.append(cut_index)
                next_cut += 1
        assert found == record['new_cut_indices']
        assert record['complete_positive_support_separation'] == (len(record['row_queries']) == len(support))
    assert next_cut == len(cuts)
    assert result['exact_case4_exclusion_claimed'] == bool(rays)
    report = {'status': 'complete base/row-domain and all integer cuts/rays replay PASS',
              'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation_path),
              'result_sha256': digest(result_path), 'checked_cuts': cut_checks,
              'exact_Farkas_certificates': rays, 'exact_case4_exclusion_verified': bool(rays),
              'numerical_statuses_and_proposal_gaps_only_bound': True,
              'exact_feasibility_claimed': False, 'optimizer_or_SAT_called': False,
              'whole_local_set_or_graph_excluded': False}
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prepare_command = commands.add_parser('prepare')
    prepare_command.add_argument('--output', type=Path, required=True)
    run_command = commands.add_parser('run')
    run_command.add_argument('--preparation', type=Path, required=True)
    run_command.add_argument('--output', type=Path, required=True)
    run_command.add_argument('--seconds', type=float, default=60)
    run_command.add_argument('--rounds', type=int, default=5)
    replay_command = commands.add_parser('replay')
    replay_command.add_argument('--preparation', type=Path, required=True)
    replay_command.add_argument('--result', type=Path, required=True)
    replay_command.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        assert not args.output.exists()
        value = preparation()
        args.output.write_bytes(gzip.compress(canonical(value) + b'\n', mtime=0))
        print(json.dumps({k: v for k, v in value.items() if k != 'initial_exact_cuts'}, indent=2))
        print('preparation_sha256', digest(args.output))
    elif args.command == 'run':
        run(args.preparation, args.output, args.seconds, args.rounds)
    else:
        replay(args.preparation, args.result, args.output)
