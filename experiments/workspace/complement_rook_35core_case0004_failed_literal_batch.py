"""One bounded exact positive-assumption batch; no numerical solver.

Preparation is separate. Each negative conclusion requires an exact
contradiction trace under the original rows/covers, earlier proved units,
and one explicit positive assumption. Noncontradictory branch assignments
are never carried into the next probe.
"""

import argparse
import gzip
import json
from pathlib import Path
import resource
import time

import complement_rook_35core_case0004_failed_literal_preparation as scope


rules = scope.rules
ROOT, LOGS = scope.ROOT, scope.LOGS
digest, canonical = scope.digest, scope.canonical
SCOPE_SHA = '65808c886e17f00d9e98955fdb2bca70c5fae464e351f404e7d898829204236f'
SCOPE_PREP = LOGS/'complement-rook-35core-case0004-failed-literal-preparation.json'
SCOPE_PREP_SHA = '38023613faa4de991eb1d4cef375cb6ea1661b7be6b6379f25ab920ddad5cc0e'
CONTROL = LOGS/'complement-rook-35core-case0004-failed-literal-controls.json'


def portable(path):
    return str(path.resolve().relative_to(ROOT))


def save(path, value):
    temporary = path.with_name(path.name+'.writing')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def save_step(path, value):
    raw = canonical(value)+b'\n'
    temporary = path.with_name(path.name+'.writing')
    temporary.write_bytes(gzip.compress(raw, mtime=0))
    temporary.replace(path)
    return {'path': portable(path), 'sha256': digest(path),
            'decompressed_sha256': rules.sha(raw)}


def inputs():
    assert digest(Path(scope.__file__)) == SCOPE_SHA
    assert digest(Path(rules.__file__)) == scope.RULE_SHA
    assert digest(SCOPE_PREP) == SCOPE_PREP_SHA
    prepared = json.loads(SCOPE_PREP.read_text())
    assert prepared['complete'] and prepared['source_sha256'] == SCOPE_SHA
    assert prepared['rule_source_sha256'] == scope.RULE_SHA
    assert prepared['limits'] == scope.LIMITS and prepared['case4_probes_run'] == 0
    assert digest(CONTROL) == prepared['controls_sha256']
    assert prepared['candidate_count'] == 1200
    assert len(prepared['priority_order']) == len(set(prepared['priority_order'])) == 1200
    assert prepared['planned_first32_columns'] == prepared['priority_order'][:32]
    assert prepared['automorphism_census']['core35_group_order'] == 1
    assert prepared['automorphism_census']['column_orbit_count'] == 1214
    return prepared


def prepare(output):
    assert not output.exists()
    data = inputs()
    old = json.loads(scope.CLOSURE.read_text())
    assert digest(scope.CLOSURE) == scope.CLOSURE_SHA
    report = {'status': 'one bounded exact failed-literal batch prepared; not run', 'complete': True,
        'source_sha256': digest(Path(__file__)), 'scope_source_sha256': SCOPE_SHA,
        'rule_source_sha256': scope.RULE_SHA, 'scope_preparation_sha256': SCOPE_PREP_SHA,
        'limits': scope.LIMITS, 'candidate_count': 1200,
        'planned_columns': data['planned_first32_columns'],
        'complete_core35_group_order': 1, 'graph_automorphism_pruning_applied': False,
        'single_sweep_baseline_seconds': old['closure_seconds'],
        'baseline_reason_replay_seconds': old['reason_and_fixed_point_check_seconds'],
        '32_forward_plus_replay_baselines_seconds_not_a_guarantee':
            32*(old['closure_seconds']+old['reason_and_fixed_point_check_seconds']),
        'batch_budget_includes_reconstruction_discovery_replay_and_checkpointing': True,
        'budget_is_cooperative': True, 'durable_checkpoint_after_every_probe': True,
        'learned_unit_requires_checked_contradiction': True,
        'new_positive_assumptions_per_probe': 1,
        'unproved_conditional_assignments_reused': False,
        'native_presolve_messages_used': False,
        'complete1200_probe_coverage_claimed': False,
        'production_probes': 0, 'solver_or_optimizer_called': False}
    save(output, report)
    print(json.dumps(report, indent=2))
    print('preparation_sha256', digest(output))


def checked_preparation(path):
    scoped = inputs()
    prepared = json.loads(path.read_text())
    assert prepared['complete'] and prepared['source_sha256'] == digest(Path(__file__))
    assert prepared['scope_source_sha256'] == SCOPE_SHA
    assert prepared['rule_source_sha256'] == scope.RULE_SHA
    assert prepared['scope_preparation_sha256'] == SCOPE_PREP_SHA
    assert prepared['limits'] == scope.LIMITS
    assert prepared['planned_columns'] == scoped['planned_first32_columns']
    assert prepared['production_probes'] == 0 and not prepared['solver_or_optimizer_called']
    return prepared, scoped


def run(preparation, directory):
    assert not directory.exists()
    prepared, scoped = checked_preparation(preparation)
    directory.mkdir(parents=True)
    started = time.monotonic()
    result = {'status': 'running one exact failed-literal batch',
        'source_sha256': digest(Path(__file__)), 'scope_source_sha256': SCOPE_SHA,
        'rule_source_sha256': scope.RULE_SHA, 'preparation_sha256': digest(preparation),
        'scope_preparation_sha256': SCOPE_PREP_SHA, 'limits': scope.LIMITS,
        'candidate_count': 1200, 'planned_columns': prepared['planned_columns'],
        'steps': [], 'proved_absent_columns_beyond14': [],
        'all1200_candidates_covered': False, 'planned32_prefix_complete': False,
        'failed_literal_probing_run': True, 'solver_or_optimizer_called': False,
        'case4_exclusion_promoted': False, 'full_graph_completion_found': False}
    path = directory/'result.json'
    save(path, result)
    rows, raw, units, bindings = rules.load_inventory()
    assert bindings == scoped['input_bindings']
    result['input_bindings'] = bindings
    prior = []
    try:
        for index, assumed in enumerate(prepared['planned_columns']):
            remaining = scope.LIMITS['requested_batch_seconds']-(time.monotonic()-started)
            if remaining <= 0:
                result['status'] = 'partial coverage: requested batch budget reached'
                break
            assert assumed not in scoped['initial_absent_columns'] and assumed not in prior
            seconds = min(scope.LIMITS['seconds_per_probe'], remaining)
            extended = scope.augmented_rows(rows, prior, assumed)
            at = time.monotonic()
            trace = rules.propagate(1214, extended, raw, units, seconds)
            discovery_seconds = time.monotonic()-at
            at = time.monotonic()
            checked = scope.check_probe(1214, rows, raw, units, prior, assumed, trace)
            replay_seconds = time.monotonic()-at
            record = {'index': index, 'assumed_column': assumed,
                'prior_proved_absent_columns': list(prior), 'requested_probe_seconds': seconds,
                'trace': trace, 'exact_check': checked,
                'discovery_seconds': discovery_seconds, 'reason_replay_seconds': replay_seconds,
                'conditional_fixed_zero_count': trace['values'].count(0),
                'conditional_fixed_one_count': trace['values'].count(1),
                'conditional_values_are_not_global_units': True}
            if checked['newly_proved_absent'] is not None:
                assert trace['status'] == 'exact contradiction' and trace['complete']
                prior = sorted(prior+[assumed])
            step = save_step(directory/f'probe{index:02d}-column{assumed:04d}.json.gz', record)
            step.update(index=index, assumed_column=assumed,
                        status=trace['status'], learned_unit=checked['newly_proved_absent'])
            result['steps'].append(step)
            result['proved_absent_columns_beyond14'] = list(prior)
            result['elapsed_seconds'] = time.monotonic()-started
            result['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            save(path, result)
            print(json.dumps({'probe': index, 'column': assumed, 'status': trace['status'],
                              'new_unit': checked['newly_proved_absent'],
                              'elapsed_seconds': result['elapsed_seconds']}), flush=True)
            if not trace['complete']:
                result['status'] = 'partial coverage: stopped at first incomplete propagation trace'
                break
        else:
            result['status'] = 'complete planned32 prefix; remaining1168 candidates unprobed'
            result['planned32_prefix_complete'] = True
    except Exception as error:
        result.update(status='ERROR: exact failed-literal batch stopped',
                      error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        result.update(elapsed_seconds=time.monotonic()-started,
                      cooperative_budget_overrun_seconds=max(0, time.monotonic()-started-scope.LIMITS['requested_batch_seconds']),
                      peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(path, result)
    print(json.dumps({k: v for k, v in result.items() if k not in ('steps', 'input_bindings')}, indent=2), flush=True)


def replay(preparation, result_path, output):
    assert not output.exists()
    prepared, scoped = checked_preparation(preparation)
    result = json.loads(result_path.read_text())
    assert result['source_sha256'] == digest(Path(__file__))
    assert result['scope_source_sha256'] == SCOPE_SHA and result['rule_source_sha256'] == scope.RULE_SHA
    assert result['preparation_sha256'] == digest(preparation)
    assert result['scope_preparation_sha256'] == SCOPE_PREP_SHA
    assert result['limits'] == scope.LIMITS and result['planned_columns'] == prepared['planned_columns']
    assert not result['status'].startswith(('running', 'ERROR:'))
    assert not result['solver_or_optimizer_called'] and not result['all1200_candidates_covered']
    rows, raw, units, bindings = rules.load_inventory()
    assert bindings == result['input_bindings'] == scoped['input_bindings']
    prior, partial_seen = [], False
    for index, step in enumerate(result['steps']):
        assert index < 32 and not partial_seen
        path = ROOT/step['path']
        assert digest(path) == step['sha256']
        payload = gzip.decompress(path.read_bytes())
        assert rules.sha(payload) == step['decompressed_sha256']
        record = json.loads(payload)
        assumed = prepared['planned_columns'][index]
        assert record['index'] == step['index'] == index
        assert record['assumed_column'] == step['assumed_column'] == assumed
        assert record['prior_proved_absent_columns'] == prior
        assert assumed not in scoped['initial_absent_columns'] and assumed not in prior
        assert 0 < record['requested_probe_seconds'] <= scope.LIMITS['seconds_per_probe']
        trace = record['trace']
        assert [r['origin'] for r in trace['records'][:14]] == [
            {'family': 'cover', 'id': identifier} for identifier in units]
        checked = scope.check_probe(1214, rows, raw, units, prior, assumed, trace)
        assert checked == record['exact_check']
        assert step['status'] == trace['status'] and step['learned_unit'] == checked['newly_proved_absent']
        assert record['conditional_values_are_not_global_units']
        assert record['conditional_fixed_zero_count'] == trace['values'].count(0)
        assert record['conditional_fixed_one_count'] == trace['values'].count(1)
        if checked['newly_proved_absent'] is not None:
            assert trace['complete'] and trace['status'] == 'exact contradiction'
            prior = sorted(prior+[assumed])
        partial_seen = not trace['complete']
    assert prior == result['proved_absent_columns_beyond14']
    assert result['planned32_prefix_complete'] == (len(result['steps']) == 32 and not partial_seen)
    if partial_seen:
        assert result['status'] == 'partial coverage: stopped at first incomplete propagation trace'
    elif result['planned32_prefix_complete']:
        assert result['status'] == 'complete planned32 prefix; remaining1168 candidates unprobed'
    else:
        assert result['status'] == 'partial coverage: requested batch budget reached'
    report = {'status': 'PASS: every conditional trace and inductive failed-literal unit replayed',
        'source_sha256': digest(Path(__file__)), 'rule_source_sha256': scope.RULE_SHA,
        'preparation_sha256': digest(preparation), 'result_sha256': digest(result_path),
        'probes_checked': len(result['steps']), 'new_proved_absent_columns': prior,
        'planned32_prefix_complete': result['planned32_prefix_complete'],
        'all1200_candidates_covered': False, 'discovery_probes_repeated': False,
        'solver_or_optimizer_called': False, 'case4_exclusion_promoted': False,
        'full_graph_completion_found': False}
    save(output, report)
    print(json.dumps(report, indent=2))
    print('replay_sha256', digest(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('prepare'); p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('run'); p.add_argument('--preparation', type=Path, required=True)
    p.add_argument('--directory', type=Path, required=True)
    p = commands.add_parser('replay'); p.add_argument('--preparation', type=Path, required=True)
    p.add_argument('--result', type=Path, required=True); p.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output.resolve())
    elif args.command == 'run':
        run(args.preparation.resolve(), args.directory.resolve())
    else:
        replay(args.preparation.resolve(), args.result.resolve(), args.output.resolve())
