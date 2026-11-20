"""One bounded exact case4 primary closure and optimizer-free trace replay.

The separate prepare command performs no closure. All accepted assignment
reasons come from the immutable integer rows and complete cover registry.
Native presolve messages and failed-literal probes are never premises.
"""

import argparse
import json
from pathlib import Path
import resource
import time

import complement_rook_35core_case0004_primary_propagation as rules


ROOT, LOGS = rules.ROOT, rules.LOGS
digest, save = rules.digest, rules.save
RULE_SOURCE_SHA = '3e4b8a5118c0ee8e37aee03d5f265128b53af9ae8ffc169393fe2d731062d8f7'
INVENTORY = LOGS/'complement-rook-35core-case0004-primary-propagation-preparation.json'
INVENTORY_SHA = '7e242554f2fea7d9d0da8543c8760534ff461e21ae5689208352551c8e4df2d2'
CONTROLS = LOGS/'complement-rook-35core-case0004-primary-propagation-controls03.json'
SECONDS = 60


def inputs():
    assert digest(Path(rules.__file__)) == RULE_SOURCE_SHA and digest(INVENTORY) == INVENTORY_SHA
    record = json.loads(INVENTORY.read_text())
    assert record['source_sha256'] == RULE_SOURCE_SHA and record['complete']
    assert digest(CONTROLS) == record['controls_sha256']
    control = json.loads(CONTROLS.read_text())
    assert control['source_sha256'] == RULE_SOURCE_SHA and control['status'].startswith('PASS:')
    assert not control['case4_closure_run'] and not control['solver_or_optimizer_called']
    assert record['maximum_new_primary_assignments'] == 1214
    assert record['maximum_records_including_final_contradiction'] == 1215
    assert record['maximum_complete_monotone_sweeps'] == 1215
    return record


def prepare(output):
    assert not output.exists()
    inventory = inputs()
    report = {'status': 'one bounded exact case4 closure prepared; not run', 'complete': True,
        'source_sha256': digest(Path(__file__)), 'rule_source_sha256': RULE_SOURCE_SHA,
        'inventory_preparation_sha256': INVENTORY_SHA, 'controls_sha256': digest(CONTROLS),
        'requested_closure_seconds': SECONDS, 'variables': 1214,
        'base_integer_rows': 2271, 'complete_registered_covers': 178533,
        'initial_unit_clause_ids': inventory['initial_unit_clause_ids'],
        'initial_absent_columns': inventory['initial_absent_columns'],
        'bounds': {'maximum_assignments': 1214, 'maximum_trace_records': 1215,
                   'maximum_sweeps': 1215},
        'every_assignment_checked_by_integer_reason_replay': True,
        'complete_fixed_point_checked_against_every_original_row_and_cover': True,
        'partial_trace_has_no_fixed_point_completeness_claim': True,
        'time_limit_is_cooperative_not_an_OS_timeout': True,
        'failed_literal_probing_run': False, 'solver_or_optimizer_called': False,
        'case4_closure_run': False}
    save(output, report)
    print(json.dumps(report, indent=2))
    print('preparation_sha256', digest(output))


def checked_preparation(path):
    inventory = inputs()
    record = json.loads(path.read_text())
    assert record['complete'] and record['source_sha256'] == digest(Path(__file__))
    assert record['rule_source_sha256'] == RULE_SOURCE_SHA
    assert record['inventory_preparation_sha256'] == INVENTORY_SHA
    assert record['controls_sha256'] == digest(CONTROLS)
    assert record['requested_closure_seconds'] == SECONDS and not record['case4_closure_run']
    assert not record['solver_or_optimizer_called'] and not record['failed_literal_probing_run']
    return record, inventory


def summary(trace, initial_absent):
    zero = [a for a, value in enumerate(trace['values']) if value == 0]
    one = [a for a, value in enumerate(trace['values']) if value == 1]
    assert set(initial_absent) <= set(zero)
    new_zero = sorted(set(zero)-set(initial_absent))
    return {'proved_absent_columns': zero, 'proved_selected_columns': one,
            'new_absent_columns_beyond14_initial_units': new_zero,
            'new_selected_columns': one, 'new_assignments': len(new_zero)+len(one),
            'trace_records': len(trace['records']), 'sweeps': trace['sweeps'],
            'complete_under_these_rules': trace['complete'],
            'contradiction': trace['status'] == 'exact contradiction'}


def run(preparation, output):
    assert not output.exists()
    prepared, inventory = checked_preparation(preparation)
    started = time.monotonic()
    rows, raw, units, bindings = rules.load_inventory()
    assert bindings == inventory['bindings']
    assert units == inventory['initial_unit_clause_ids']
    reconstruction_seconds = time.monotonic()-started
    at = time.monotonic()
    trace = rules.propagate(rules.N, rows, raw, units, SECONDS)
    closure_seconds = time.monotonic()-at
    at = time.monotonic()
    check = rules.verify_trace(rules.N, rows, raw, trace)
    check_seconds = time.monotonic()-at
    report = {'status': trace['status'], 'source_sha256': digest(Path(__file__)),
        'rule_source_sha256': RULE_SOURCE_SHA, 'preparation_sha256': digest(preparation),
        'inventory_preparation_sha256': INVENTORY_SHA, 'bindings': bindings,
        'initial_unit_clause_ids': units, 'trace': trace, 'exact_reason_replay': check,
        'summary': summary(trace, inventory['initial_absent_columns']),
        'inventory_reconstruction_seconds': reconstruction_seconds,
        'requested_closure_seconds': SECONDS, 'closure_seconds': closure_seconds,
        'reason_and_fixed_point_check_seconds': check_seconds,
        'total_seconds': time.monotonic()-started,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        'native_presolve_messages_used_as_premises': False,
        'failed_literal_probing_run': False, 'solver_or_optimizer_called': False,
        'case4_exclusion_promoted': False, 'full_graph_completion_found': False}
    save(output, report)
    print(json.dumps({k: v for k, v in report.items() if k not in ('trace', 'bindings')}, indent=2))
    print('result_sha256', digest(output))


def replay(preparation, result_path, output):
    assert not output.exists()
    prepared, inventory = checked_preparation(preparation)
    result = json.loads(result_path.read_text())
    assert result['source_sha256'] == digest(Path(__file__))
    assert result['rule_source_sha256'] == RULE_SOURCE_SHA
    assert result['preparation_sha256'] == digest(preparation)
    assert result['inventory_preparation_sha256'] == INVENTORY_SHA
    assert not result['native_presolve_messages_used_as_premises']
    assert not result['failed_literal_probing_run'] and not result['solver_or_optimizer_called']
    rows, raw, units, bindings = rules.load_inventory()
    assert bindings == inventory['bindings'] == result['bindings']
    assert units == result['initial_unit_clause_ids'] == inventory['initial_unit_clause_ids']
    trace = result['trace']
    assert result['status'] == trace['status']
    assert len(trace['values']) == 1214 and len(trace['records']) <= 1215
    assert trace['sweeps'] <= 1215
    assert [r['origin'] for r in trace['records'][:14]] == [
        {'family': 'cover', 'id': identifier} for identifier in units]
    check = rules.verify_trace(rules.N, rows, raw, trace)
    assert check == result['exact_reason_replay']
    assert summary(trace, inventory['initial_absent_columns']) == result['summary']
    report = {'status': 'PASS: every original-input reason and complete closure scope replayed',
        'source_sha256': digest(Path(__file__)), 'rule_source_sha256': RULE_SOURCE_SHA,
        'preparation_sha256': digest(preparation), 'result_sha256': digest(result_path),
        'summary': result['summary'], 'reason_check': check,
        'closure_discovery_repeated': False, 'solver_or_optimizer_called': False,
        'case4_exclusion_promoted': False, 'full_graph_completion_found': False}
    save(output, report)
    print(json.dumps(report, indent=2))
    print('replay_sha256', digest(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--output', type=Path, required=True)
    run_parser = commands.add_parser('run')
    run_parser.add_argument('--preparation', type=Path, required=True)
    run_parser.add_argument('--output', type=Path, required=True)
    check = commands.add_parser('replay')
    check.add_argument('--preparation', type=Path, required=True)
    check.add_argument('--result', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output.resolve())
    elif args.command == 'run':
        run(args.preparation.resolve(), args.output.resolve())
    else:
        replay(args.preparation.resolve(), args.result.resolve(), args.output.resolve())
