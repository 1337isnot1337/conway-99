"""Bounded continuation for the20 remaining first-local35-core matchings.

Every formula preserves its frozen original clause body and appends only
its previously certified Gram conflicts. There is one fresh proof-enabled
query per requested case, no retries. Stop at the first checked SAT
incidence witness, uncertified proof, or error. UNKNOWN remains open and
the next requested case may run. Every completed case is saved durably.
No wider local-set sweep or full exterior completion is attempted here.
"""

import argparse
import gc
import gzip
import json
from pathlib import Path
import subprocess
import tempfile
import time

import complement_rook_35core_incidence as original
import complement_rook_35core_downdate_census as census


ROOT, LOGS = original.ROOT, original.LOGS
MANIFEST = LOGS/'complement-rook-35core-first-local-downdates01-artifacts.json'
MANIFEST_SHA = '21c3aeddd103d6146699a0f0efc88b80e348c9f066db1402de9d81432994c185'
TERMINAL = LOGS/'complement-rook-35core-first-local-downdates01/terminal.json'
PRIOR_TERMINAL = LOGS/'complement-rook-35core-cases09-10-terminal-artifacts.json'
PRIOR_TERMINAL_SHA = '72b8229ac724c43d43b50ef027c787400f84ed716194da5fd28ff462be3aa6a8'
PRIOR_EXCLUDED = [0, 1, 2, 3, 8, 9, 10, 21]
EXPECTED = {4: 30, 5: 92, 6: 27, 7: 86, 11: 22, 12: 57, 13: 21, 14: 65,
            15: 8, 16: 28, 17: 10, 18: 26, 19: 6, 20: 7, 22: 8, 23: 10,
            24: 10, 25: 11, 26: 5, 27: 5}
CASES = list(EXPECTED)
assert CASES == sorted(set(range(28))-set(PRIOR_EXCLUDED))
SOURCES = ('complement_rook_35core_downdate_continuation.py',
           'complement_rook_35core_downdate_continuation_audit.py', *original.SOURCES, *census.SOURCES)
digest, portable, canonical = original.digest, original.portable, original.canonical


def inputs(case_index):
    assert case_index in EXPECTED and digest(MANIFEST) == MANIFEST_SHA
    assert digest(PRIOR_TERMINAL) == PRIOR_TERMINAL_SHA
    prior = json.loads(PRIOR_TERMINAL.read_text())
    assert prior['excluded_first_local_matchings'] == PRIOR_EXCLUDED
    assert prior['unresolved_first_local_matchings'] == CASES
    manifest = json.loads(MANIFEST.read_text())
    hashes = {item['path']: item['sha256'] for item in manifest['artifacts']}
    assert digest(TERMINAL) == hashes[portable(TERMINAL)]
    terminal = json.loads(TERMINAL.read_text())
    assert terminal['complete'] and terminal['completed_cases'] == census.CASES
    for name, expected in terminal['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    item = next(record for record in terminal['case_records'] if record['case_index'] == case_index)
    cert_path, fragment = ROOT/item['certificate'], ROOT/item['binary_fragment']
    assert digest(cert_path) == item['certificate_sha256'] and digest(fragment) == item['binary_fragment_sha256']
    raw = gzip.decompress(cert_path.read_bytes())
    assert original.domains.sha(raw) == item['decompressed_certificate_sha256']
    saved = json.loads(raw)
    actual = census.build(case_index, census.context(), saved=saved)
    assert canonical(actual)+b'\n' == raw and census.clauses(actual) == fragment.read_bytes()
    base_path = ROOT/saved['original_model']
    assert digest(base_path) == saved['original_model_sha256']
    base = original.checked_model(base_path)
    assert base['case'] == saved['case']
    for key in ('domain_record_sha256', 'column_domain_sha256', 'Gram_sha256'):
        assert base[key] == saved[key]
    assert base['cnf_sha256'] == saved['original_cnf_sha256']
    clauses = list(original.read_clauses(fragment))
    assert len(clauses) == len({tuple(c) for c in clauses}) == EXPECTED[case_index]
    assert all(len(c) == 2 and all(-len(saved['attachment_columns']) <= v < 0 for v in c) for c in clauses)
    return base_path, base, cert_path, fragment, saved, clauses


def append_bytes(raw, base, clauses):
    first, body = raw.split(b'\n', 1)
    n, count = base['formula']['variables'], base['formula']['clauses']
    assert first == f'p cnf {n} {count}'.encode()
    assert body.endswith(b'\n') and body.count(b'\n') == count
    tail = ''.join(' '.join(map(str, c))+' 0\n' for c in clauses).encode()
    return f'p cnf {n} {count+len(clauses)}\n'.encode()+body+tail


def rebuild(case_index):
    base_path, base, cert_path, fragment, certificate, clauses = inputs(case_index)
    data, cnf, metadata = original.rebuild(case_index)
    assert metadata == base['formula']
    assert data[3]['columns'] == certificate['attachment_columns'] and data[5] == certificate['Gram']
    with tempfile.TemporaryDirectory(prefix=f'conway35-case{case_index}-base-') as directory:
        path = Path(directory)/'base.cnf'
        cnf.to_file(path)
        raw = path.read_bytes()
    assert original.domains.sha(raw) == base['cnf_sha256']
    return base_path, base, cert_path, fragment, data, cnf, clauses, append_bytes(raw, base, clauses)


def prepare(case_index, model_path, cnf_path):
    assert not model_path.exists() and not cnf_path.exists()
    started = time.monotonic()
    base_path, base, cert_path, fragment, data, cnf, clauses, raw = rebuild(case_index)
    assert digest(Path(base['cnf'])) == base['cnf_sha256']
    assert raw == append_bytes(Path(base['cnf']).read_bytes(), base, clauses)
    cnf_path.write_bytes(raw)
    model = {'status': 'fresh original formula plus certified pair clauses prepared; not solved',
             'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in SOURCES},
             'prefix_certificate_sha256': original.PREFIX_SHA,
             'prior_terminal_manifest': portable(PRIOR_TERMINAL),
             'prior_terminal_manifest_sha256': PRIOR_TERMINAL_SHA,
             'complete_remaining_case_list': CASES,
             'census_artifact_manifest': portable(MANIFEST), 'census_artifact_manifest_sha256': MANIFEST_SHA,
             'base_model': portable(base_path), 'base_model_sha256': digest(base_path),
             'base_cnf_sha256': base['cnf_sha256'],
             'certificate': portable(cert_path), 'certificate_sha256': digest(cert_path),
             'binary_fragment': portable(fragment), 'binary_fragment_sha256': digest(fragment),
             'case': base['case'], 'domain_record_sha256': base['domain_record_sha256'],
             'column_domain_sha256': base['column_domain_sha256'], 'Gram_sha256': base['Gram_sha256'],
             'cnf': str(cnf_path.resolve()), 'cnf_sha256': digest(cnf_path),
             'formula': {'primary_columns': len(data[3]['columns']), 'variables': cnf.nv,
                         'original_clauses': len(cnf.clauses), 'additional_binary_clauses': len(clauses),
                         'clauses': len(cnf.clauses)+len(clauses)},
             'controls': {'cold_original_CNF_hash_matched': True, 'all_exact_certificate_tests_replayed': True,
                          'every_added_clause_has_direct_integer_negative_vector': True,
                          'original_body_unchanged': True, 'new_variables': 0},
             'solver_implementation': 'unmodified complement_rook_35core_incidence.solve',
             'maximum_query_seconds_including_bootstrap': 60,
             'scope': 'one indexed35-core only; no fixed incidence or graph symmetry',
             'preparation_seconds': time.monotonic()-started}
    model_path.write_text(json.dumps(model, indent=2)+'\n')
    print(json.dumps(model, indent=2), flush=True)
    return model


def checked(model_path, require_cnf=False):
    model = original.checked_model(model_path, require_cnf)
    assert model['case']['index'] in EXPECTED
    assert model['complete_remaining_case_list'] == CASES
    assert model['prior_terminal_manifest_sha256'] == PRIOR_TERMINAL_SHA == digest(PRIOR_TERMINAL)
    assert model['census_artifact_manifest_sha256'] == MANIFEST_SHA == digest(MANIFEST)
    for key in ('base_model', 'certificate', 'binary_fragment'):
        assert digest(ROOT/model[key]) == model[key+'_sha256']
    assert model['formula']['additional_binary_clauses'] == EXPECTED[model['case']['index']]
    return model


def witness_overlay_check(model, witness):
    selected = set(witness['selected_columns'])
    clauses = list(original.read_clauses(ROOT/model['binary_fragment']))
    assert all(not all(-value-1 in selected for value in clause) for clause in clauses)
    return {'status': 'all certified binary overlay clauses satisfied by the exact original incidence witness',
            'case_index': model['case']['index'], 'binary_clauses_checked': len(clauses), 'full_graph': False}


def solve(model_path, directory, seconds, checker, checker_seconds):
    assert 0 < seconds <= 60 and 0 < checker_seconds <= 60
    model = checked(model_path, True)
    result = original.solve(model_path, directory, seconds, checker, checker_seconds)
    if result['status'].startswith('SAT;'):
        report = witness_overlay_check(model, result['incidence_witness'])
        (directory/'overlay-witness-check.json').write_text(json.dumps(report, indent=2)+'\n')
    return result


def replay(model_path, result_path, output, checker, checker_seconds):
    assert not output.exists() and 0 < checker_seconds <= 60
    model = checked(model_path)
    index = model['case']['index']
    base_path, base, cert_path, fragment, data, cnf, clauses, raw = rebuild(index)
    assert original.domains.sha(raw) == model['cnf_sha256']
    assert model['formula'] == {'primary_columns': len(data[3]['columns']), 'variables': cnf.nv,
                                'original_clauses': len(cnf.clauses), 'additional_binary_clauses': len(clauses),
                                'clauses': len(cnf.clauses)+len(clauses)}
    report = {'status': 'cold original and overlay rebuild, exact cut certificates replayed',
              'model_sha256': digest(model_path), 'base_cnf_sha256': base['cnf_sha256'],
              'cnf_sha256': model['cnf_sha256'], 'case_index': index,
              'whole_local_set_excluded': False, 'full_graph': False}
    if result_path:
        result = json.loads(result_path.read_text())
        assert result['model_sha256'] == digest(model_path) and result['cnf_sha256'] == model['cnf_sha256']
        assert result['source_sha256'] == digest(Path(original.__file__)) and result['case_index'] == index
        if result['status'].startswith('SAT;'):
            actual = original.inspect(result['incidence_witness']['selected_columns'], data)
            assert json.loads(json.dumps(actual)) == result['incidence_witness']
            report['overlay_witness_check'] = witness_overlay_check(model, actual)
            report['status'] = 'cold formula and exact partial incidence witness replay passed'
        elif result['status'].startswith('UNSAT with direct DRAT;'):
            record = result['retained_certificate']
            retained, proof = ROOT/record['cnf'], ROOT/record['proof']
            assert digest(retained) == record['cnf_sha256'] and digest(proof) == record['proof_sha256']
            inputs = list(original.read_clauses(retained))
            assert len(inputs) == record['input_clauses']
            outside_original = {tuple(sorted(c)) for c in inputs}
            outside_original.difference_update(tuple(sorted(c)) for c in cnf.clauses)
            assert outside_original <= {tuple(sorted(c)) for c in clauses}
            checked_proof = subprocess.run([str(checker), str(retained), str(proof), '-t', str(checker_seconds), '-w'],
                                            capture_output=True, text=True, timeout=checker_seconds+5, check=False)
            log = output.with_suffix('.drat.log')
            log.write_text(checked_proof.stdout+checked_proof.stderr)
            assert checked_proof.returncode == 0 and 's VERIFIED' in checked_proof.stdout
            report.update(status='cold original/overlay rebuild, direct cut certificates, retained inclusion and DRAT passed',
                          retained_input_clauses=len(inputs),
                          retained_distinct_inputs_outside_original_formula=len(outside_original),
                          original_only_proof_binding_verified=not outside_original,
                          excluded_indexed_core=index, checker_log=portable(log), checker_log_sha256=digest(log))
        else:
            assert result['status'].startswith('UNKNOWN;')
            report['status'] = 'cold overlay and UNKNOWN binding replay passed; no exclusion'
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
    return report


def source_hashes():
    return {name: digest(Path(__file__).with_name(name)) for name in SOURCES}


def prepare_all(directory, cnf_directory, seconds):
    """Prepare only the20 enumerated formulas, with an audit after each one."""
    import complement_rook_35core_downdate_continuation_audit as audit

    assert not directory.exists() and not cnf_directory.exists() and 0 < seconds <= 120
    directory.mkdir(parents=True)
    cnf_directory.mkdir(parents=True)
    started = time.monotonic()
    progress = {'status': 'preparing finite20-case continuation; no solver',
                'complete': False, 'requested_cases': CASES,
                'prior_excluded_cases': PRIOR_EXCLUDED,
                'prior_terminal_manifest_sha256': PRIOR_TERMINAL_SHA,
                'source_hashes': source_hashes(), 'prepared_cases': [], 'case_records': [],
                'unprepared_cases': CASES[:], 'wall_budget_seconds': seconds,
                'solver_called': False, 'non_author_source_gate_required_before_queries': True}

    def save():
        progress['elapsed_seconds'] = time.monotonic()-started
        census.atomic_json(directory/'progress.json', progress)

    save()
    try:
        for index in CASES:
            if time.monotonic()-started >= seconds:
                progress['status'] = 'preparation wall budget reached; unprepared cases remain open'
                break
            model_path = directory/f'case{index:04d}-model.json'
            cnf_path = cnf_directory/f'case{index:04d}.cnf'
            model = prepare(index, model_path, cnf_path)
            report = audit.audit(index, model_path, digest(model_path))
            audit_path = directory/f'case{index:04d}-author-direct-audit.json'
            census.atomic_json(audit_path, report)
            item = {'case_index': index, 'model': portable(model_path),
                    'model_sha256': digest(model_path), 'cnf_sha256': model['cnf_sha256'],
                    'cnf_bytes': cnf_path.stat().st_size, 'formula': model['formula'],
                    'author_direct_audit': portable(audit_path),
                    'author_direct_audit_sha256': digest(audit_path)}
            progress['prepared_cases'].append(index)
            progress['case_records'].append(item)
            progress['unprepared_cases'] = [i for i in CASES if i not in progress['prepared_cases']]
            save()
            print(json.dumps({'prepared_case': item}), flush=True)
            gc.collect()
        else:
            progress.update(status='all20 exact overlays prepared and author-audited; no solver', complete=True)
    except Exception as error:
        progress.update(status='preparation stopped on error; no unchecked case promoted',
                        error_type=type(error).__name__, error_message=str(error))
        save()
        census.atomic_json(directory/'terminal.json', progress)
        raise
    save()
    census.atomic_json(directory/'terminal.json', progress)
    print(json.dumps({key: value for key, value in progress.items() if key != 'case_records'}, indent=2), flush=True)


def run_all(preparation, directory, seconds, checker, checker_seconds):
    """One query per prepared case. A SAT point or failed proof stops the batch."""
    assert not directory.exists() and 0 < seconds <= 60 and 0 < checker_seconds <= 60
    prepared_path = preparation/'terminal.json'
    prepared = json.loads(prepared_path.read_text())
    assert prepared['complete'] and prepared['requested_cases'] == prepared['prepared_cases'] == CASES
    assert prepared['prior_excluded_cases'] == PRIOR_EXCLUDED
    assert prepared['prior_terminal_manifest_sha256'] == PRIOR_TERMINAL_SHA == digest(PRIOR_TERMINAL)
    assert prepared['source_hashes'] == source_hashes() and not prepared['unprepared_cases']
    assert [item['case_index'] for item in prepared['case_records']] == CASES
    directory.mkdir(parents=True)
    started = time.monotonic()
    progress = {'status': 'running one fresh bounded query per remaining matching',
                'preparation_terminal': portable(prepared_path),
                'preparation_terminal_sha256': digest(prepared_path),
                'source_hashes': source_hashes(), 'requested_cases': CASES,
                'prior_excluded_cases': PRIOR_EXCLUDED, 'started_cases': [], 'completed_cases': [],
                'certified_unsat_cases': [], 'unknown_cases': [], 'sat_incidence_case': None,
                'unstarted_cases': CASES[:], 'case_records': [],
                'solver_seconds_including_bootstrap_per_case': seconds,
                'direct_checker_seconds_per_unsat_case': checker_seconds,
                'cold_checker_seconds_per_unsat_case': checker_seconds,
                'maximum_queries': len(CASES), 'retries': 0,
                'complete_requested_queries': False, 'all_requested_cases_certified_unsat': False,
                'whole_complementary_core_excluded': False, 'full_graph_found': False}

    def save():
        progress['elapsed_seconds'] = time.monotonic()-started
        census.atomic_json(directory/'progress.json', progress)

    save()
    try:
        for item in prepared['case_records']:
            index = item['case_index']
            model_path, audit_path = ROOT/item['model'], ROOT/item['author_direct_audit']
            assert digest(model_path) == item['model_sha256']
            assert digest(audit_path) == item['author_direct_audit_sha256']
            audit = json.loads(audit_path.read_text())
            assert audit['case_index'] == index and audit['model_sha256'] == item['model_sha256']
            assert audit['status'].startswith('PASS:')
            model = checked(model_path, True)
            assert model['case']['index'] == index and model['formula'] == item['formula']
            assert model['cnf_sha256'] == item['cnf_sha256']
            case_directory = directory/f'case{index:04d}'
            assert index not in progress['started_cases'] and not case_directory.exists()
            progress['started_cases'].append(index)
            progress['unstarted_cases'] = [i for i in CASES if i not in progress['started_cases']]
            progress['active_case'] = index
            save()
            result = solve(model_path, case_directory, seconds, checker, checker_seconds)
            result_path = case_directory/'result.json'
            terminal = {'case_index': index, 'model_sha256': digest(model_path),
                        'result': portable(result_path), 'result_sha256': digest(result_path),
                        'observed_solver_seconds_including_bootstrap': result['solve_return_seconds']}
            if result['status'].startswith('UNSAT with direct DRAT;'):
                replay_path = case_directory/'cold-replay.json'
                checked_proof = replay(model_path, result_path, replay_path, checker, checker_seconds)
                assert checked_proof['excluded_indexed_core'] == index
                terminal.update(status='certified UNSAT: direct and cold proof checks passed',
                                cold_replay=portable(replay_path), cold_replay_sha256=digest(replay_path),
                                retained_nonoriginal_Gram_inputs=checked_proof['retained_distinct_inputs_outside_original_formula'],
                                original_only_proof_binding_verified=checked_proof['original_only_proof_binding_verified'])
                progress['certified_unsat_cases'].append(index)
            elif result['status'].startswith('SAT;'):
                replay_path = case_directory/'cold-replay.json'
                checked_point = replay(model_path, result_path, replay_path, checker, checker_seconds)
                assert checked_point['status'] == 'cold formula and exact partial incidence witness replay passed'
                terminal.update(status='SAT incidence only: original exact inspector and cold replay passed',
                                cold_replay=portable(replay_path), cold_replay_sha256=digest(replay_path),
                                a=result['incidence_witness']['a'], full_graph=False)
                progress['sat_incidence_case'] = index
                progress['status'] = 'stopped at the first checked partial incidence witness'
            else:
                assert result['status'].startswith('UNKNOWN;')
                terminal['status'] = 'UNKNOWN; indexed core remains open'
                progress['unknown_cases'].append(index)
            progress['case_records'].append(terminal)
            progress['completed_cases'].append(index)
            progress.pop('active_case')
            save()
            print(json.dumps({'completed_case': terminal}), flush=True)
            gc.collect()
            if progress['sat_incidence_case'] is not None:
                break
        else:
            progress['complete_requested_queries'] = True
            progress['all_requested_cases_certified_unsat'] = progress['certified_unsat_cases'] == CASES
            progress['status'] = ('all20 requested cases have checked UNSAT proofs' if progress['all_requested_cases_certified_unsat']
                                  else 'all20 bounded queries completed; every UNKNOWN remains open')
    except Exception as error:
        progress.update(status='stopped on an error or uncertified proof; no unchecked exclusion promoted',
                        error_type=type(error).__name__, error_message=str(error))
        save()
        census.atomic_json(directory/'terminal.json', progress)
        raise
    save()
    census.atomic_json(directory/'terminal.json', progress)
    print(json.dumps({key: value for key, value in progress.items() if key != 'case_records'}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--case', type=int, choices=sorted(EXPECTED), required=True)
    prep.add_argument('--model', type=Path, required=True)
    prep.add_argument('--cnf', type=Path, required=True)
    prep_all = commands.add_parser('prepare-all')
    prep_all.add_argument('--directory', type=Path, required=True)
    prep_all.add_argument('--cnf-directory', type=Path, required=True)
    prep_all.add_argument('--seconds', type=float, default=120)
    run = commands.add_parser('solve')
    run.add_argument('--model', type=Path, required=True)
    run.add_argument('--directory', type=Path, required=True)
    run.add_argument('--seconds', type=float, default=60)
    run.add_argument('--checker-seconds', type=int, default=60)
    run.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    check = commands.add_parser('replay')
    check.add_argument('--model', type=Path, required=True)
    check.add_argument('--result', type=Path)
    check.add_argument('--output', type=Path, required=True)
    check.add_argument('--checker-seconds', type=int, default=60)
    check.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    batch = commands.add_parser('run-all')
    batch.add_argument('--preparation', type=Path, required=True)
    batch.add_argument('--directory', type=Path, required=True)
    batch.add_argument('--seconds', type=float, default=60)
    batch.add_argument('--checker-seconds', type=int, default=60)
    batch.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.case, args.model.resolve(), args.cnf.resolve())
    elif args.command == 'prepare-all':
        prepare_all(args.directory.resolve(), args.cnf_directory.resolve(), args.seconds)
    elif args.command == 'solve':
        solve(args.model.resolve(), args.directory.resolve(), args.seconds, args.drat_trim.resolve(), args.checker_seconds)
    elif args.command == 'run-all':
        run_all(args.preparation.resolve(), args.directory.resolve(), args.seconds,
                args.drat_trim.resolve(), args.checker_seconds)
    else:
        replay(args.model.resolve(), args.result.resolve() if args.result else None,
               args.output.resolve(), args.drat_trim.resolve(), args.checker_seconds)
