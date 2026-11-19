"""Bounded32-row numerical discovery with exact universal integer cuts.

This separates the immutable case4 numerical proposal from independent
exterior-row boxes. No global LP is rerun and no SAT formula is changed.
The proposal remains numerical-only. Every exported inequality is checked
using only integers and the complete frozen row domain.
"""

import argparse
from fractions import Fraction
import gzip
import json
from math import gcd, lcm
from pathlib import Path
import time

import complement_rook_35core_case0004_exterior_rows as prepared


ROOT, LOGS = prepared.ROOT, prepared.LOGS
MODEL = LOGS / 'complement-rook-35core-case0004-exterior-rows.json.gz'
MODEL_SHA = '10377b5494b8d39e3b41f400b39af485c1db44d06232e1c03663a07f530e8628'
PREP_SOURCE_SHA = 'db88ab6af3b151dc233519efb052d1fc20bd40b251e01a61558a3c93ac709977'
digest, canonical, portable = prepared.digest, prepared.canonical, prepared.portable


def load(full_replay=False):
    assert digest(Path(prepared.__file__)) == PREP_SOURCE_SHA
    assert digest(MODEL) == MODEL_SHA
    model = json.loads(gzip.decompress(MODEL.read_bytes()))
    assert model['source_sha256'] == PREP_SOURCE_SHA
    if full_replay:
        assert json.loads(canonical(prepared.prepare_data())) == model
    assert model['exact_proposal_feasibility_claimed'] is False
    assert model['counts']['pilot_targets'] == 32
    return model


def checked_integer_cut(model, target, vector):
    return prepared.verify_potential(model['column_masks35'], model['row_targets36'],
                                     model['eligible_neighbor_column_ids'], target, vector)


def numerical_gap(model, certificate):
    point = model['proposal_values']
    return (certificate['positive_demand'] * point[certificate['target_column']]
            - sum(weight * point[b] for b, weight in certificate['positive_terms']))


def rationalize(model, target, values):
    attempts = []
    for limit in (1, 2, 3, 4, 6, 12, 60, 360, 4096, 1000000):
        fractions = [Fraction(float(v)).limit_denominator(limit) for v in values]
        denominator = lcm(*(x.denominator for x in fractions))
        vector = [int(x * denominator) for x in fractions]
        common = gcd(*(abs(x) for x in vector))
        if common:
            vector = [x // common for x in vector]
        size = max(map(abs, vector))
        record = {'denominator_limit': limit, 'maximum_absolute_integer_coordinate': size}
        attempts.append(record)
        if size == 0 or size > 1000000:
            record['accepted'] = False
            continue
        try:
            certificate = checked_integer_cut(model, target, vector)
        except AssertionError:
            record['accepted'] = False
            continue
        gap = numerical_gap(model, certificate) / size
        record['normalized_numerical_proposal_gap'] = gap
        record['accepted'] = gap > 1e-8
        if record['accepted']:
            return certificate, attempts
    return None, attempts


def query(model, target, seconds):
    import highspy
    import numpy as np
    from scipy import sparse

    assert 0 < seconds <= 2
    masks, targets = model['column_masks35'], model['row_targets36']
    neighbors = model['eligible_neighbor_column_ids'][target]
    point = model['proposal_values']
    # Minimize sum x_b*s_b - x_a*t_a.v subject to W^T v-s<=0.
    # The36 free-sign potential coordinates are bounded by[-1,1].
    nr, nv = len(neighbors), 36 + len(neighbors)
    rr, cc, vv = [], [], []
    for row, b in enumerate(neighbors):
        for i in range(35):
            if masks[b] >> i & 1:
                rr.append(row); cc.append(i); vv.append(1)
        rr.extend((row, row)); cc.extend((35, 36 + row)); vv.extend((1, -1))
    matrix = sparse.csc_matrix((np.asarray(vv, dtype=np.int64), (rr, cc)), shape=(nr, nv))
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = nv, nr
    lp.col_cost_ = np.asarray([-point[target] * t for t in targets[target]] + [point[b] for b in neighbors])
    lp.col_lower_ = np.asarray([-1.0] * 36 + [0.0] * nr)
    lp.col_upper_ = np.asarray([1.0] * 36 + [highspy.kHighsInf] * nr)
    lp.row_lower_ = np.full(nr, -highspy.kHighsInf)
    lp.row_upper_ = np.zeros(nr)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = matrix.indptr, matrix.indices, matrix.data.astype(float)
    solver = highspy.Highs()
    for name, value in [('output_flag', False), ('threads', 1), ('presolve', 'on'), ('time_limit', seconds)]:
        assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
    assert solver.passModel(lp) == highspy.HighsStatus.kOk
    start = time.monotonic()
    solver.run()
    status = solver.getModelStatus()
    record = {'target_column': target, 'numerical_status': str(status), 'requested_seconds': seconds,
              'solve_seconds': time.monotonic() - start, 'threads': 1,
              'dual_matrix_shape': [nr, nv], 'dual_matrix_nonzeros': int(matrix.nnz),
              'exact_global_feasibility_or_infeasibility_claimed': False}
    if status != highspy.HighsModelStatus.kOptimal:
        record['status'] = 'nonoptimal numerical row query; stop pilot without exclusion'
        return record
    proposed = list(map(float, solver.getSolution().col_value[:36]))
    record['numerical_potential'] = proposed
    record['numerical_bounded_dual_score'] = -float(solver.getObjectiveValue())
    certificate, attempts = rationalize(model, target, proposed)
    record['integer_reconstruction_attempts'] = attempts
    if certificate is None:
        record['status'] = 'no exact separating integer potential retained from this query'
    else:
        record['status'] = 'exact universally necessary integer inequality checked; proposal violation numerical-only'
        record['integer_certificate'] = certificate
        record['numerical_proposal_gap'] = numerical_gap(model, certificate)
    return record


def run(output, row_seconds, total_seconds):
    assert not output.exists() and 0 < row_seconds <= 2 and 0 < total_seconds <= 60
    start = time.monotonic()
    model = load(True)
    result = {'status': 'running one capped numerical32-row discovery pilot',
              'source_sha256': digest(Path(__file__)), 'preparation_source_sha256': PREP_SOURCE_SHA,
              'model': portable(MODEL), 'model_sha256': MODEL_SHA, 'case_index': 4,
              'proposal_sha256': model['proposal_sha256'], 'proposal_variant': model['proposal_variant'],
              'target_order': [r['target_column'] for r in model['pilot_plan']],
              'row_seconds': row_seconds, 'total_seconds': total_seconds, 'rows': [],
              'exact_proposal_feasibility_claimed': False, 'full_graph_or_case_exclusion': False,
              'SAT_queries': 0, 'new_global_LP_queries': 0}
    def checkpoint():
        result['elapsed_seconds'] = time.monotonic() - start
        output.write_text(json.dumps(result, indent=2) + '\n')
    checkpoint()
    try:
        for target in result['target_order']:
            remaining = total_seconds - (time.monotonic() - start)
            if remaining <= 0:
                result['status'] = 'bounded pilot stopped at total wall budget; unvisited rows open'
                break
            row = query(model, target, min(row_seconds, remaining))
            result['rows'].append(row)
            checkpoint()
            print(json.dumps({k: v for k, v in row.items() if k not in ('integer_certificate', 'numerical_potential')},
                             indent=2), flush=True)
            if row['numerical_status'] != 'HighsModelStatus.kOptimal':
                result['status'] = 'bounded pilot stopped at first nonoptimal row; unvisited rows open'
                break
        else:
            result['status'] = 'all32 planned row queries completed; exact inequalities only, no completion claim'
        result['visited_rows'] = len(result['rows'])
        result['exact_integer_inequalities'] = sum('integer_certificate' in r for r in result['rows'])
        result['complete32_row_plan'] = len(result['rows']) == 32
        checkpoint()
    except Exception as error:
        result.update(status='error; no unverified inequality promoted', error_type=type(error).__name__,
                      error_message=str(error))
        checkpoint()
        raise
    print(json.dumps({k: v for k, v in result.items() if k != 'rows'}, indent=2), flush=True)


def replay(result_path, output):
    assert not output.exists()
    model = load(True)
    result = json.loads(result_path.read_text())
    assert result['source_sha256'] == digest(Path(__file__))
    assert result['model_sha256'] == MODEL_SHA and result['preparation_source_sha256'] == PREP_SOURCE_SHA
    order = [row['target_column'] for row in model['pilot_plan']]
    assert result['target_order'] == order
    assert [row['target_column'] for row in result['rows']] == order[:len(result['rows'])]
    checked = []
    for row in result['rows']:
        if 'integer_certificate' not in row:
            continue
        old = row['integer_certificate']
        actual = checked_integer_cut(model, row['target_column'], old['integer_vector'])
        assert actual == old
        gap = numerical_gap(model, actual)
        assert gap == row['numerical_proposal_gap']
        checked.append({'target_column': row['target_column'], 'positive_demand': actual['positive_demand'],
                        'positive_terms': len(actual['positive_terms']),
                        'max_abs_integer_coordinate': max(map(abs, actual['integer_vector'])),
                        'numerical_proposal_gap': gap})
    assert len(checked) == result.get('exact_integer_inequalities', len(checked))
    report = {'status': 'complete domain binding and all retained integer row inequalities replay PASS',
              'source_sha256': digest(Path(__file__)), 'model_sha256': MODEL_SHA,
              'result_sha256': digest(result_path), 'checked_inequalities': checked,
              'numerical_statuses_only_bound_not_recomputed': True,
              'optimizer_or_SAT_called': False, 'exact_proposal_feasibility_claimed': False,
              'full_graph_or_case_exclusion': False}
    output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    run_command = commands.add_parser('run')
    run_command.add_argument('--output', type=Path, required=True)
    run_command.add_argument('--row-seconds', type=float, default=2)
    run_command.add_argument('--total-seconds', type=float, default=60)
    replay_command = commands.add_parser('replay')
    replay_command.add_argument('--result', type=Path, required=True)
    replay_command.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'run':
        run(args.output, args.row_seconds, args.total_seconds)
    else:
        replay(args.result, args.output)
