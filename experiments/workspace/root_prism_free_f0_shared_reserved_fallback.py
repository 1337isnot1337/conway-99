"""Reserve time for one exact bounded shared-potential fallback.

After setup, with at least20 seconds remaining, make at most one old
feasibility call with min(10,remaining/4) seconds.  Otherwise use the
bounded separator directly.  An unresolved first call is followed by
one bounded call using the actual remainder.  There are no retries.
Only exact points or strict integer gaps establish mathematical results.
"""

import argparse
import json
from pathlib import Path
import time

import root_prism_free_f0_shared_bounded_fallback as frozen


ROOT, LOGS = frozen.ROOT, frozen.LOGS
canonical, digest, save = frozen.canonical, frozen.digest, frozen.save
domain, inventory, lift = frozen.domain, frozen.inventory, frozen.lift
DEPENDENCIES = {
    'root_prism_free_f0_shared_bounded_fallback.py': '46ff20ca4269b71b80c2fd7e3ba2fec4f369b7dca3d4e08272a935cdfde72f1a'}
SCHEDULE = {'original_if_remaining_at_least': 20,
            'original_maximum_seconds': 10, 'original_fraction_denominator': 4,
            'otherwise_bounded_only': True, 'original_after_bounded': False}


def check_sources():
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    frozen.check_sources()


def plan(remaining):
    assert type(remaining) in (int, float) and remaining <= 60
    if remaining <= 0:
        return {'first_phase': None, 'original_seconds': 0}
    if remaining < SCHEDULE['original_if_remaining_at_least']:
        return {'first_phase': 'bounded', 'original_seconds': 0}
    return {'first_phase': 'original', 'original_seconds': min(10, remaining/4)}


def accept_original(report, first):
    report['status'] = first['status']
    if first['exact_linear_feasibility']:
        report.update(exact_linear_feasibility=True, exact_point_check=first['exact_point_check'])
    elif first['exact_fixed_design_infeasibility']:
        report.update(exact_fixed_design_infeasibility=True,
                      fixed_capacity_potentials=first['fixed_capacity_potentials'])
    else:
        assert frozen.fallback_needed(first)


def accept_bounded(report, second):
    report['status'] = second['status']
    if second['exact_separator']:
        report.update(exact_fixed_design_infeasibility=True,
            fixed_capacity_potentials={
                'integer_potentials60_by18': second['certificate']['integer_potentials60_by18'],
                'strict_integer_support_gap': second['certificate']['check']},
            exact_support_gap=second['certificate']['check']['integer_support_gap'])


def query(selected, triples, targets, neighbors, output, candidate_sha, seconds):
    assert not output.exists() and 0 < seconds <= 60
    started = time.monotonic()
    check_sources()
    data, rows = domain(selected, triples, targets, neighbors)
    _, model_hash = frozen.exact_model(data, rows)
    report = {'status': 'RUNNING: reserved shared-feasibility/bounded sequence',
        'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': DEPENDENCIES,
        'selected_signature_ids': selected, 'candidate_sha256': candidate_sha,
        'inventory': inventory(data, rows), 'bounded_model_sha256': model_hash,
        'requested_seconds': seconds, 'schedule': SCHEDULE, 'optimizer_calls': 0,
        'original_feasibility_calls': 0, 'bounded_potential_calls': 0,
        'exact_linear_feasibility': False, 'exact_fixed_design_infeasibility': False,
        'full_graph_constructed': False, 'old_feasibility_call_never_retried': True,
        'both_phases_share_one_budget': True}
    save(output, report)
    try:
        remaining = seconds-(time.monotonic()-started)
        chosen = plan(remaining)
        report.update(remaining_seconds_after_setup=remaining, initial_phase_plan=chosen)
        if chosen['first_phase'] is None:
            report['status'] = 'UNKNOWN: shared setup exhausted budget'
        else:
            if chosen['first_phase'] == 'original':
                first_path = output.with_name(output.stem+'-feasibility.json')
                first = frozen.original.query(selected, triples, targets, neighbors, first_path,
                                              candidate_sha, chosen['original_seconds'])
                frozen.original.replay(first, selected, triples, targets, neighbors)
                frozen.record_phase(report, 'original_feasibility', first_path, first)
                report['original_feasibility_calls'] = first['optimizer_calls']
                report['optimizer_calls'] = first['optimizer_calls']
                accept_original(report, first)
                save(output, report)
            if not (report['exact_linear_feasibility'] or report['exact_fixed_design_infeasibility']):
                remaining = seconds-(time.monotonic()-started)
                report['remaining_seconds_before_bounded'] = remaining
                if remaining > 0:
                    second_path = output.with_name(output.stem+'-bounded.json')
                    second = frozen.bounded_query(data, rows, second_path, remaining)
                    frozen.replay_bounded(second, data, rows)
                    frozen.record_phase(report, 'bounded_potential', second_path, second)
                    report['bounded_potential_calls'] = second['optimizer_calls']
                    report['optimizer_calls'] += second['optimizer_calls']
                    accept_bounded(report, second)
                else:
                    report['status'] = 'UNKNOWN: no exact shared certificate before shared budget'
    except Exception as error:
        report.update(status='ERROR: reserved shared sequence stopped',
                      error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic()-started
        report['cooperative_budget_overrun_seconds'] = max(0, report['elapsed_seconds']-seconds)
        save(output, report)
    return report


def replay(report, selected, triples, targets, neighbors):
    check_sources()
    assert report['source_sha256'] == digest(Path(__file__)) and report['dependency_source_hashes'] == DEPENDENCIES
    assert report['selected_signature_ids'] == selected and report['schedule'] == SCHEDULE
    assert not report['status'].startswith(('RUNNING:', 'ERROR:'))
    assert 0 < report['requested_seconds'] <= 60
    assert report['old_feasibility_call_never_retried'] and report['both_phases_share_one_budget']
    remaining = report['remaining_seconds_after_setup']
    assert remaining <= report['requested_seconds']
    chosen = plan(remaining)
    assert chosen == report['initial_phase_plan']
    data, rows = domain(selected, triples, targets, neighbors)
    assert report['inventory'] == inventory(data, rows)
    assert report['bounded_model_sha256'] == frozen.exact_model(data, rows)[1]
    first_calls = second_calls = 0
    point = obstruction = False
    potentials = None
    assert ('original_feasibility' in report) == (chosen['first_phase'] == 'original')
    if 'original_feasibility' in report:
        first = frozen.replay_phase(report, 'original_feasibility')
        assert first['candidate_sha256'] == report['candidate_sha256']
        assert first['requested_seconds'] == chosen['original_seconds']
        frozen.original.replay(first, selected, triples, targets, neighbors)
        first_calls = first['optimizer_calls']
        point, obstruction = first['exact_linear_feasibility'], first['exact_fixed_design_infeasibility']
        if point:
            assert report['exact_point_check'] == first['exact_point_check']
        if obstruction:
            potentials = first['fixed_capacity_potentials']
    if 'bounded_potential' in report:
        assert chosen['first_phase'] in ('original', 'bounded') and not (point or obstruction)
        if 'original_feasibility' in report:
            assert frozen.fallback_needed(first)
        second = frozen.replay_phase(report, 'bounded_potential')
        assert 0 < second['requested_seconds_including_setup'] == report['remaining_seconds_before_bounded'] <= remaining
        frozen.replay_bounded(second, data, rows)
        second_calls = second['optimizer_calls']
        obstruction = second['exact_separator']
        if obstruction:
            potentials = {'integer_potentials60_by18': second['certificate']['integer_potentials60_by18'],
                          'strict_integer_support_gap': second['certificate']['check']}
            assert report['exact_support_gap'] == second['certificate']['check']['integer_support_gap'] > 0
    elif chosen['first_phase'] is not None and not (point or obstruction):
        assert report['remaining_seconds_before_bounded'] <= 0
    assert report['exact_linear_feasibility'] == point and report['exact_fixed_design_infeasibility'] == obstruction
    assert not (point and obstruction)
    if obstruction:
        assert report['fixed_capacity_potentials'] == potentials
        assert frozen.bounded.exact_gap(data, potentials['integer_potentials60_by18'])['integer_support_gap'] > 0
    assert (report['original_feasibility_calls'], report['bounded_potential_calls'], report['optimizer_calls']) == (
        first_calls, second_calls, first_calls+second_calls)
    assert first_calls in (0, 1) and second_calls in (0, 1)


def controls():
    check_sources()
    cases = [0, -1, 0.001, 1, 3.5, 19.999, 20, 20.001, 39.999, 40, 40.001, 59.999, 60]
    for remaining in cases:
        p = plan(remaining)
        if remaining <= 0:
            assert p == {'first_phase': None, 'original_seconds': 0}
        elif remaining < 20:
            assert p == {'first_phase': 'bounded', 'original_seconds': 0}
        else:
            assert p['first_phase'] == 'original' and 0 < p['original_seconds'] <= 10
            assert p['original_seconds'] <= remaining/4
    fields = {'exact_linear_feasibility': False, 'exact_fixed_design_infeasibility': False}
    point = {'status': 'exact box control', 'exact_linear_feasibility': True,
             'exact_fixed_design_infeasibility': False, 'exact_point_check': {'valid': True}}
    r = dict(fields); accept_original(r, point)
    assert r['exact_linear_feasibility'] and not r['exact_fixed_design_infeasibility']
    unknown = {'status': 'UNKNOWN: numerical outcome', 'exact_linear_feasibility': False,
               'exact_fixed_design_infeasibility': False}
    r = dict(fields); accept_original(r, unknown)
    assert not any(r[k] for k in fields)
    r = dict(fields); accept_bounded(r, {'status': 'UNKNOWN: no strict integer gap', 'exact_separator': False})
    assert not any(r[k] for k in fields)
    return {'status': 'reserved shared schedule and exact-only acceptance controls PASS',
        'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': DEPENDENCIES,
        'schedule': SCHEDULE, 'boundary_schedule_cases': len(cases), 'exact_status_cases': 3,
        'bounded_model_and_integer_reconstruction_unchanged': True,
        'same_input_timing_comparison_claimed': False, 'optimizer_or_solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = controls(); save(args.output, report)
    print(json.dumps(report, indent=2), flush=True)
