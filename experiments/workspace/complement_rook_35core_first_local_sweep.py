"""Sweep the other27 matchings of the first local eight-signature set.

Every solve reuses the frozen incidence runner with10s including
bootstrap. Direct and cold DRAT stages each have separate60s bounds.
UNKNOWN cases remain open; no wider local-set sweep is authorized here.
"""

import argparse
from contextlib import redirect_stdout
import gc
import gzip
import json
from pathlib import Path
import time

import complement_rook_35core_incidence as incidence


ROOT, LOGS = incidence.ROOT, incidence.LOGS
ZERO = LOGS/'complement-rook-35core-incidence-case0000-pilot01-cold-replay.json'
CONTROL = LOGS/'complement-rook-35core-first-local-Gram-control01/cold-replay.json'
digest, portable = incidence.digest, incidence.portable


def prepare(directory):
    assert not directory.exists()
    zero, control = json.loads(ZERO.read_text()), json.loads(CONTROL.read_text())
    assert zero['status'] == 'cold domain/full-CNF rebuild, retained inclusion, and DRAT replay passed'
    assert zero['excluded_indexed_core'] == 0
    assert control['status'] == 'SAT incidence witness and full conditional Gram CNF cold replay passed'
    assert control['a'] == 10 and not control['complete_graph']
    data = incidence.load(0)
    first = data[2]
    cases = [case for case in data[1]['cases'] if case['local_set_orbit'] == first['local_set_orbit']]
    assert [case['index'] for case in cases] == list(range(28))
    assert all(case['selected_signatures'] == first['selected_signatures'] for case in cases)
    assert len({tuple(map(tuple, case['matching'])) for case in cases}) == 28
    assert control['unit_selectors'] == [s+1 for s in first['selected_signatures']]
    prefix = json.loads((incidence.PREFIX/'certificate.json').read_text())
    raw = gzip.decompress((ROOT/prefix['archive']).read_bytes())
    records = {item['index']: item for item in map(json.loads, raw.splitlines())}
    assert set(range(28)) <= set(records)
    coverage = [{'case': case, 'column_domain_sha256': records[case['index']]['column_domain_sha256'],
                 'Gram_sha256': records[case['index']]['Gram_sha256'],
                 'columns': records[case['index']]['admitted_columns'],
                 'previously_verified_UNSAT': case['index'] == 0} for case in cases]
    directory.mkdir(parents=True)
    manifest = {'status': 'remaining27 matching cases prepared; no new query run',
                'source_sha256': digest(Path(__file__)),
                'runner_source_sha256': digest(Path(incidence.__file__)),
                'prefix_certificate_sha256': incidence.PREFIX_SHA,
                'full_index_sha256': digest(incidence.PREFIX/'all-core-index.json'),
                'case_zero_replay': portable(ZERO), 'case_zero_replay_sha256': digest(ZERO),
                'Gram_only_SAT_control_replay': portable(CONTROL),
                'Gram_only_SAT_control_replay_sha256': digest(CONTROL),
                'complete_global_index_cases': 2521, 'all28_matching_cases': coverage,
                'new_case_indices': list(range(1, 28)),
                'solver_seconds_including_bootstrap_per_case': 10,
                'direct_DRAT_seconds_per_UNSAT_case': 60, 'cold_DRAT_seconds_per_UNSAT_case': 60,
                'assumptions': [], 'UNKNOWN_cases_remain_open': True,
                'wider_local_set_sweep': False, 'full_graph_claim_from_SAT': False}
    path = directory/'manifest.json'
    path.write_text(json.dumps(manifest, indent=2)+'\n')
    progress = {'status': 'prepared; no new query run', 'manifest_sha256': digest(path),
                'active_case': None, 'completed_cases': [], 'all27_new_cases_processed': False,
                'first_local_set_excluded': False, 'whole_complementary_core_excluded': False}
    (directory/'progress.json').write_text(json.dumps(progress, indent=2)+'\n')
    print(json.dumps({'manifest': portable(path), 'manifest_sha256': digest(path),
                      'source_sha256': manifest['source_sha256'], 'new_cases': list(range(1, 28))}, indent=2), flush=True)
    return manifest


def run(directory, maximum_cases, checker):
    assert 0 < maximum_cases <= 27
    manifest_path, progress_path = directory/'manifest.json', directory/'progress.json'
    manifest = json.loads(manifest_path.read_text())
    assert manifest['source_sha256'] == digest(Path(__file__))
    assert manifest['runner_source_sha256'] == digest(Path(incidence.__file__))
    assert digest(ZERO) == manifest['case_zero_replay_sha256']
    assert digest(CONTROL) == manifest['Gram_only_SAT_control_replay_sha256']
    progress = json.loads(progress_path.read_text())
    assert progress['manifest_sha256'] == digest(manifest_path) and progress['active_case'] is None
    completed = progress['completed_cases']
    assert [item['case_index'] for item in completed] == list(range(1, len(completed)+1))
    requested = manifest['new_case_indices'][len(completed):len(completed)+maximum_cases]
    assert requested
    started = time.monotonic()

    def save():
        progress_path.write_text(json.dumps(progress, indent=2)+'\n')

    for case_index in requested:
        progress.update(status='bounded first-local-set sweep running', active_case=case_index)
        save()
        before = time.monotonic()
        stem = f'case{case_index:04d}'
        model_path, replay_path = directory/(stem+'-model.json'), directory/(stem+'-cold-replay.json')
        result_directory, log = directory/stem, directory/(stem+'-stages.log')
        cnf_path = Path('/tmp')/f'conway-complement-rook-35core-first-local-{stem}.cnf'
        try:
            gc.collect()
            assert not log.exists()
            with log.open('w') as stream, redirect_stdout(stream):
                model = incidence.prepare(case_index, model_path, cnf_path)
                expected = manifest['all28_matching_cases'][case_index]
                assert model['case'] == expected['case']
                assert model['column_domain_sha256'] == expected['column_domain_sha256']
                assert model['Gram_sha256'] == expected['Gram_sha256']
                assert model['formula']['primary_columns'] == expected['columns']
                result = incidence.solve(model_path, result_directory, 10, checker, 60)
                replay = incidence.replay(model_path, result_directory/'result.json', checker, 60, replay_path)
            if result['status'].startswith('UNSAT with direct DRAT;'):
                assert replay['status'] == 'cold domain/full-CNF rebuild, retained inclusion, and DRAT replay passed'
                assert replay['excluded_indexed_core'] == case_index
                outcome = 'verified UNSAT'
            elif result['status'].startswith('SAT;'):
                assert replay['status'] == 'cold formula rebuild and exact binary incidence witness replay passed'
                outcome = 'SAT incidence witness; full completion open'
            else:
                assert result['status'].startswith('UNKNOWN;')
                assert replay['status'] == 'cold formula rebuild and UNKNOWN binding checked; no exclusion'
                outcome = 'UNKNOWN; case remains open'
            item = {'case_index': case_index, 'outcome': outcome,
                    'model': portable(model_path), 'model_sha256': digest(model_path),
                    'result': portable(result_directory/'result.json'),
                    'result_sha256': digest(result_directory/'result.json'),
                    'replay': portable(replay_path), 'replay_sha256': digest(replay_path),
                    'stages_log': portable(log), 'stages_log_sha256': digest(log),
                    'columns': model['formula']['primary_columns'], 'variables': model['formula']['variables'],
                    'clauses': model['formula']['clauses'], 'solver_return_seconds': result['solve_return_seconds'],
                    'case_total_seconds_including_build_and_replay': time.monotonic()-before}
            if 'retained_certificate' in result:
                item['retained_input_clauses'] = result['retained_certificate']['input_clauses']
            if 'incidence_witness' in result:
                item['a'] = result['incidence_witness']['a']
            completed.append(item)
            progress['active_case'] = None
            save()
            print(json.dumps(item), flush=True)
        except Exception as error:
            progress.update(status='error; sweep stopped without promoting the active case',
                            error_type=type(error).__name__, error_message=str(error))
            save()
            raise
    all_done = [item['case_index'] for item in completed] == manifest['new_case_indices']
    all_unsat = all_done and all(item['outcome'] == 'verified UNSAT' for item in completed)
    progress.update(status='all authorized first-local-set matching queries finished' if all_done else
                    'bounded sweep segment finished; remaining matching cases not yet queried',
                    all27_new_cases_processed=all_done, first_local_set_excluded=all_unsat,
                    verified_cases_including_previous_zero=[0]+[item['case_index'] for item in completed
                                                               if item['outcome'] == 'verified UNSAT'],
                    open_processed_cases=[item['case_index'] for item in completed if item['outcome'] != 'verified UNSAT'],
                    last_segment_seconds=time.monotonic()-started)
    save()
    print(json.dumps({key: value for key, value in progress.items() if key != 'completed_cases'}, indent=2), flush=True)
    return progress


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('prepare', 'run'))
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--maximum-cases', type=int, default=8)
    parser.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.directory.resolve())
    else:
        run(args.directory.resolve(), args.maximum_cases, args.drat_trim.resolve())
