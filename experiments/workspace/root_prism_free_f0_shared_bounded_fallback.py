"""One shared-feasibility call, then a distinct bounded-potential fallback.

Both phases share one at-most-sixty-second budget. The old feasibility
call is never retried. Only an exact rational box or a strict integer
support gap can establish a result. Replay calls no optimizer.
"""

import argparse
from collections import Counter
import hashlib
import json
from math import isfinite
from pathlib import Path
import time

import root_prism_free_f0_shared_deficit_separator as original
import root_prism_free_f0_bounded_shared_separator as bounded


ROOT = original.allocation.ROOT
LOGS = original.allocation.LOGS
canonical, digest, save = original.canonical, original.digest, original.save
domain, inventory, lift = original.domain, original.inventory, original.lift
DEPENDENCIES = {
    'root_prism_free_f0_shared_deficit_separator.py': '6bc6944ed00713d384251ab54e54684e6f5ea29300f9ff243df5282f522375bf',
    'root_prism_free_f0_bounded_shared_separator.py': 'bbdf21247d98cff416f68492415a3db6ec5f98f47d1ebb9367acac1604192798'}
CONTROL_INPUTS = {
    'f0-bounded-shared-separator-preparation.json.gz': 'ddce4b389df860780c0f99ba291b2e881ea99da8e73ec3283260c10854794df7',
    'f0-bounded-shared-separator-run01.json': 'fdcf7105748e809f792b4241ecfa8e950ad916b9c229154b2ca6c509e9f7fb6e',
    'f0-bounded-shared-separator-run01-cold-replay.json': '19e2183e0f6eb285075bbcb4e6165717f22ad1eb3922c9fa8f5c9a33bc98e5c6',
    'f0-bounded-shared-separator-run01-universal-cuts.json': '9029303e60cbf1249db03a5b9be0da44f2fb2b0c086760067f28887ee286e45f'}


def check_sources():
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    original.check_sources()


def portable(path):
    return str(path.resolve().relative_to(ROOT))


def exact_model(data, rows):
    assert len(data['design']) == 60
    assert all(len(h) == len(set(h)) == 3 for h in data['design'])
    assert all(len(q) == 18 and sum(q) == 24 and all(type(x) is int and x >= 0 for x in q)
               for q in data['targets'])
    for a in range(60):
        degree, mixed = rows[19*a], rows[19*a+1:19*a+19]
        assert degree['kind'] == 'degree' and degree['rhs'] == 8
        assert Counter(e for row in mixed for e in row['support']) == Counter({e: 3 for e in degree['support']})
        assert sum(row['rhs'] for row in mixed) == 24
    lp = bounded.model(data)
    assert lp['variables'] == 1080+len(data['edge_domain'])
    assert len(lp['rows']) == len(data['edge_domain'])
    model_hash = hashlib.sha256(canonical({'data': data, 'bounded_potential_LP': lp})).hexdigest()
    return lp, model_hash


def fallback_needed(record):
    assert not record['status'].startswith(('RUNNING:', 'ERROR:'))
    assert not (record['exact_linear_feasibility'] and record['exact_fixed_design_infeasibility'])
    return not (record['exact_linear_feasibility'] or record['exact_fixed_design_infeasibility'])


def bounded_query(data, rows, output, seconds):
    assert not output.exists() and 0 < seconds <= 60
    started = time.monotonic()
    lp, model_hash = exact_model(data, rows)
    report = {'status': 'RUNNING: distinct bounded-potential fallback',
        'source_sha256': digest(Path(__file__)), 'model_sha256': model_hash,
        'requested_seconds_including_setup': seconds, 'optimizer_calls': 0,
        'exact_separator': False, 'exact_shared_box_feasibility': False,
        'original_feasibility_query_repeated': False}
    save(output, report)
    try:
        import highspy
        import numpy as np
        from scipy import sparse
        rr, cc, values = [], [], []
        for i, row in enumerate(lp['rows']):
            for j, coefficient in row:
                rr.append(i); cc.append(j); values.append(coefficient)
        matrix = sparse.csc_matrix((np.asarray(values, dtype=float), (rr, cc)),
                                  shape=(len(lp['rows']), lp['variables']))
        assert matrix.nnz == lp['nonzeros']
        problem = highspy.HighsLp()
        problem.num_col_, problem.num_row_ = lp['variables'], len(lp['rows'])
        problem.col_cost_ = np.asarray(lp['cost'], dtype=float)
        problem.col_lower_, problem.col_upper_ = np.asarray(lp['column_lower'], dtype=float), np.asarray(lp['column_upper'], dtype=float)
        problem.row_lower_ = np.full(len(lp['rows']), -highspy.kHighsInf)
        problem.row_upper_ = np.zeros(len(lp['rows']))
        problem.a_matrix_.format_ = highspy.MatrixFormat.kColwise
        problem.a_matrix_.start_, problem.a_matrix_.index_, problem.a_matrix_.value_ = matrix.indptr, matrix.indices, matrix.data
        remaining = seconds-(time.monotonic()-started)
        if remaining <= 0:
            report['status'] = 'UNKNOWN: bounded-potential setup exhausted budget'
        else:
            solver = highspy.Highs()
            for name, value in [('output_flag', False), ('threads', 1), ('solver', 'simplex'),
                                ('presolve', 'on'), ('time_limit', remaining)]:
                assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
            assert solver.passModel(problem) == highspy.HighsStatus.kOk
            report.update(optimizer_calls=1, requested_optimizer_seconds=remaining)
            save(output, report)
            solver.run()
            report['numerical_status'] = str(solver.getModelStatus())
            report['optimizer_return_seconds'] = time.monotonic()-started
            solution = solver.getSolution()
            numeric = list(map(float, solution.col_value))
            report['returned_solution_length'] = len(numeric)
            report['returned_solution_value_valid'] = bool(getattr(solution, 'value_valid', False))
            report['returned_all_columns_hex'] = [x.hex() for x in numeric]
            report['numerical_potential_hex'] = [x.hex() for x in numeric[:1080]]
            save(output, report)
            if len(numeric) != lp['variables'] or not all(isfinite(x) for x in numeric[:1080]):
                report['status'] = 'UNKNOWN: no complete finite bounded-potential proposal'
            else:
                report['numerical_cost_hex'] = sum(c*x for c, x in zip(lp['cost'], numeric)).hex()
                trials, accepted = bounded.proposals(data, numeric[:1080])
                report['exact_integer_trials'] = trials
                if accepted is None:
                    report['status'] = 'UNKNOWN: bounded potential has no strict exact support gap'
                else:
                    report.update(status='EXACT INTEGER BOUNDED SHARED SUPPORT SEPARATOR',
                        exact_separator=True, certificate=accepted, validity_independent_of_optimizer_status=True)
    except Exception as error:
        report.update(status='ERROR: bounded-potential fallback stopped',
                      error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic()-started
        report['cooperative_budget_overrun_seconds'] = max(0, report['elapsed_seconds']-seconds)
        save(output, report)
    return report


def replay_bounded(report, data, rows):
    assert report['source_sha256'] == digest(Path(__file__))
    assert not report['status'].startswith(('RUNNING:', 'ERROR:'))
    assert 0 < report['requested_seconds_including_setup'] <= 60
    assert report['optimizer_calls'] in (0, 1)
    assert not report['exact_shared_box_feasibility'] and not report['original_feasibility_query_repeated']
    lp, model_hash = exact_model(data, rows)
    assert report['model_sha256'] == model_hash
    if 'returned_all_columns_hex' in report:
        numeric = [float.fromhex(x) for x in report['returned_all_columns_hex']]
        assert len(numeric) == report['returned_solution_length']
        assert report['returned_all_columns_hex'][:1080] == report['numerical_potential_hex']
    if 'exact_integer_trials' in report:
        assert len(numeric) == lp['variables']
        trials, accepted = bounded.proposals(data, numeric[:1080])
        assert trials == report['exact_integer_trials']
        assert bool(accepted) == report['exact_separator']
        if accepted is not None:
            assert accepted == report['certificate'] and accepted['check']['integer_support_gap'] > 0
            assert report['status'] == 'EXACT INTEGER BOUNDED SHARED SUPPORT SEPARATOR'
    else:
        assert not report['exact_separator']


def record_phase(report, key, path, phase):
    report[key] = phase
    report[key+'_path'] = portable(path)
    report[key+'_sha256'] = digest(path)


def query(selected, triples, targets, neighbors, output, candidate_sha, seconds):
    assert not output.exists() and 0 < seconds <= 60
    started = time.monotonic()
    check_sources()
    data, rows = domain(selected, triples, targets, neighbors)
    _, model_hash = exact_model(data, rows)
    report = {'status': 'RUNNING: shared box with bounded-potential fallback',
        'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': DEPENDENCIES,
        'selected_signature_ids': selected, 'candidate_sha256': candidate_sha,
        'inventory': inventory(data, rows), 'bounded_model_sha256': model_hash,
        'requested_seconds': seconds, 'optimizer_calls': 0,
        'original_feasibility_calls': 0, 'bounded_potential_calls': 0,
        'exact_linear_feasibility': False, 'exact_fixed_design_infeasibility': False,
        'full_graph_constructed': False, 'old_feasibility_call_never_retried': True,
        'both_phases_share_one_budget': True}
    save(output, report)
    try:
        remaining = seconds-(time.monotonic()-started)
        if remaining <= 0:
            report['status'] = 'UNKNOWN: shared setup exhausted budget'
        else:
            first_path = output.with_name(output.stem+'-feasibility.json')
            first = original.query(selected, triples, targets, neighbors, first_path, candidate_sha, remaining)
            original.replay(first, selected, triples, targets, neighbors)
            record_phase(report, 'original_feasibility', first_path, first)
            report['original_feasibility_calls'] = first['optimizer_calls']
            report['optimizer_calls'] = first['optimizer_calls']
            if first['exact_linear_feasibility']:
                report.update(status=first['status'], exact_linear_feasibility=True,
                              exact_point_check=first['exact_point_check'])
            elif first['exact_fixed_design_infeasibility']:
                report.update(status=first['status'], exact_fixed_design_infeasibility=True,
                    fixed_capacity_potentials=first['fixed_capacity_potentials'])
            else:
                assert fallback_needed(first)
                report['status'] = first['status']
                remaining = seconds-(time.monotonic()-started)
                report['remaining_seconds_after_original_replay'] = remaining
                save(output, report)
                if remaining > 0:
                    second_path = output.with_name(output.stem+'-bounded.json')
                    second = bounded_query(data, rows, second_path, remaining)
                    replay_bounded(second, data, rows)
                    record_phase(report, 'bounded_potential', second_path, second)
                    report['bounded_potential_calls'] = second['optimizer_calls']
                    report['optimizer_calls'] += second['optimizer_calls']
                    report['status'] = second['status']
                    if second['exact_separator']:
                        report.update(exact_fixed_design_infeasibility=True,
                            fixed_capacity_potentials={
                                'integer_potentials60_by18': second['certificate']['integer_potentials60_by18'],
                                'strict_integer_support_gap': second['certificate']['check']},
                            exact_support_gap=second['certificate']['check']['integer_support_gap'])
                else:
                    report['status'] = 'UNKNOWN: no exact shared certificate before shared budget'
    except Exception as error:
        report.update(status='ERROR: shared fallback sequence stopped',
                      error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic()-started
        report['cooperative_budget_overrun_seconds'] = max(0, report['elapsed_seconds']-seconds)
        save(output, report)
    return report


def replay_phase(report, key):
    path = ROOT/report[key+'_path']
    assert digest(path) == report[key+'_sha256']
    assert bounded.read(path) == report[key]
    return report[key]


def replay(report, selected, triples, targets, neighbors):
    check_sources()
    assert report['source_sha256'] == digest(Path(__file__)) and report['dependency_source_hashes'] == DEPENDENCIES
    assert report['selected_signature_ids'] == selected
    assert not report['status'].startswith(('RUNNING:', 'ERROR:'))
    assert 0 < report['requested_seconds'] <= 60
    assert report['old_feasibility_call_never_retried'] and report['both_phases_share_one_budget']
    data, rows = domain(selected, triples, targets, neighbors)
    assert report['inventory'] == inventory(data, rows)
    assert report['bounded_model_sha256'] == exact_model(data, rows)[1]
    first_calls = second_calls = 0
    point = obstruction = False
    potentials = None
    if 'original_feasibility' in report:
        first = replay_phase(report, 'original_feasibility')
        assert first['candidate_sha256'] == report['candidate_sha256']
        assert 0 < first['requested_seconds'] <= report['requested_seconds']
        original.replay(first, selected, triples, targets, neighbors)
        first_calls = first['optimizer_calls']
        point, obstruction = first['exact_linear_feasibility'], first['exact_fixed_design_infeasibility']
        if point:
            assert report['exact_point_check'] == first['exact_point_check']
        if obstruction:
            potentials = first['fixed_capacity_potentials']
    if 'bounded_potential' in report:
        assert 'original_feasibility' in report and fallback_needed(first)
        second = replay_phase(report, 'bounded_potential')
        assert 0 < second['requested_seconds_including_setup'] == report['remaining_seconds_after_original_replay'] <= report['requested_seconds']
        replay_bounded(second, data, rows)
        second_calls = second['optimizer_calls']
        obstruction = second['exact_separator']
        if obstruction:
            potentials = {'integer_potentials60_by18': second['certificate']['integer_potentials60_by18'],
                          'strict_integer_support_gap': second['certificate']['check']}
            assert report['exact_support_gap'] == second['certificate']['check']['integer_support_gap'] > 0
    assert report['exact_linear_feasibility'] == point
    assert report['exact_fixed_design_infeasibility'] == obstruction
    assert not (point and obstruction)
    if obstruction:
        assert report['fixed_capacity_potentials'] == potentials
        assert bounded.exact_gap(data, potentials['integer_potentials60_by18'])['integer_support_gap'] > 0
    assert (report['original_feasibility_calls'], report['bounded_potential_calls'], report['optimizer_calls']) == (
        first_calls, second_calls, first_calls+second_calls)
    assert first_calls in (0, 1) and second_calls in (0, 1)


def controls():
    check_sources()
    for name, expected in CONTROL_INPUTS.items():
        assert digest(LOGS/name) == expected
    prep = LOGS/'f0-bounded-shared-separator-preparation.json.gz'
    result = LOGS/'f0-bounded-shared-separator-run01.json'
    cold, lifted = bounded.reconstruct(prep, result)
    assert cold['exact_support_gap'] == 33 and lifted == bounded.read(LOGS/'f0-bounded-shared-separator-run01-universal-cuts.json')
    saved = bounded.read(prep)
    data = saved['specification']['data']
    triples, targets, neighbors, _, _, _ = bounded.box.load()
    rebuilt, rows = domain(data['selected_signature_ids'], triples, targets, neighbors)
    assert rebuilt == data and exact_model(data, rows)[1] == saved['model']['model_sha256']
    status_controls = 0
    for point, obstruction in ((False, False), (True, False), (False, True)):
        record = {'status': 'terminal exact-control status', 'exact_linear_feasibility': point,
                  'exact_fixed_design_infeasibility': obstruction}
        assert fallback_needed(record) == (not point and not obstruction)
        status_controls += 1
    for status in ('RUNNING: control', 'ERROR: control'):
        try:
            fallback_needed({'status': status, 'exact_linear_feasibility': False,
                             'exact_fixed_design_infeasibility': False})
        except AssertionError:
            status_controls += 1
        else:
            raise AssertionError('nonterminal/error status admitted')
    return {'status': 'PASS: generic model, exact gap33, all12 lifts and fallback status controls',
        'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': DEPENDENCIES,
        'control_input_hashes': CONTROL_INPUTS, 'model_sha256': saved['model']['model_sha256'],
        'exact_gap': 33, 'transport_count': 12, 'fallback_status_controls': status_controls,
        'known_separator_and24_feasible_box_controls_replayed': True,
        'no_query_or_retry': True, 'optimizer_or_solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controls', type=Path, required=True)
    args = parser.parse_args()
    assert not args.controls.exists()
    report = controls()
    save(args.controls, report)
    print(json.dumps(report, indent=2), flush=True)
