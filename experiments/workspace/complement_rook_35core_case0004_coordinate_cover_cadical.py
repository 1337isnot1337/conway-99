"""Prepare one CaDiCaL query of the unchanged case4 coordinate-cover CNF.

CaDiCaL's installed Python wrapper has no interrupt API. A parent process
therefore owns a hard wall deadline, including child imports and loading.
On timeout it persists UNKNOWN, kills and reaps the child, and uses no
partial proof. Tiny SAT/UNSAT and checked DRAT controls select300 or195.
"""

import argparse
import hashlib
import importlib.metadata
import inspect
from itertools import product
import json
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

import pysat.solvers as solver_api
import pysolvers

import complement_rook_35core_case0004_coordinate_cover_query as previous


ROOT, LOGS = previous.ROOT, previous.LOGS
PREVIOUS_PREPARATION = LOGS / 'complement-rook-35core-case0004-coordinate-cover-query-preparation.json'
PREVIOUS_PREPARATION_SHA = 'da135f734508b5116df69e27b132948672dc738e3e07594cd1c5bbc26ad3a42f'
PREVIOUS_SOURCE_SHA = 'eb352386f55c5a1fd6ddb9c692ad934d8eef87904c00e86122172dc1ebc1f9d8'
BACKENDS = [('cadical300', 'Cadical300'), ('cadical195', 'Cadical195')]
LIMITS = {'production_child_wall_seconds_including_imports_bootstrap_solve': 180,
          'tiny_control_child_wall_seconds': 10, 'tiny_DRAT_seconds': 10,
          'direct_DRAT_seconds': 60, 'cold_DRAT_seconds': 60,
          'production_queries': 1, 'automatic_retries': 0}
digest, portable, save, normalized = previous.digest, previous.portable, previous.save, previous.normalized


def source_hashes():
    result = previous.source_hashes()
    result[Path(__file__).name] = digest(Path(__file__))
    return dict(sorted(result.items()))


def runtime_binding(backend):
    class_name = dict(BACKENDS)[backend]
    cls = getattr(solver_api, class_name)
    wrapper, native = Path(solver_api.__file__), Path(pysolvers.__file__)
    return {'backend_name': backend, 'backend_class': class_name,
            'python_sat_version': importlib.metadata.version('python-sat'),
            'python_executable': sys.executable, 'python_version': sys.version,
            'python_wrapper': {'path': str(wrapper), 'sha256': digest(wrapper)},
            'native_extension': {'path': str(native), 'sha256': digest(native)},
            'native_factory_symbol': backend+'_new',
            'native_factory_present': hasattr(pysolvers, backend+'_new'),
            'backend_method_source_sha256': {name: hashlib.sha256(inspect.getsource(getattr(cls, name)).encode()).hexdigest()
                for name in ('new', 'add_clause', 'solve', 'get_model', 'get_proof', 'interrupt')}}


def checked_base(require_cnf=False):
    assert digest(Path(previous.__file__)) == PREVIOUS_SOURCE_SHA
    assert digest(PREVIOUS_PREPARATION) == PREVIOUS_PREPARATION_SHA
    _, model = previous.checked_preparation(PREVIOUS_PREPARATION, require_cnf)
    assert model['cnf_sha256'] == previous.CNF_SHA
    return model


def owned_child(command, log_path, seconds, on_timeout):
    """Persist timeout status before SIGKILL; always reap our child."""
    started = time.monotonic()
    with log_path.open('wb') as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        timed_out = False
        killed = False
        try:
            try:
                returncode = process.wait(timeout=max(0.001, seconds-(time.monotonic()-started)))
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    on_timeout(process.pid, time.monotonic()-started)
                finally:
                    try:
                        process.kill()
                        killed = True
                    except ProcessLookupError:
                        pass
                    returncode = process.wait(timeout=5)
        except BaseException:
            # An I/O error or interruption must not leave our solver child
            # running after its parent exits.
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            raise
        assert process.poll() is not None
    return {'pid': process.pid, 'returncode': returncode, 'timed_out': timed_out,
            'UNKNOWN_persisted_before_kill': timed_out,
            'SIGKILL_sent_at_deadline': killed, 'child_reaped': True,
            'requested_wall_seconds': seconds, 'elapsed_seconds': time.monotonic()-started,
            'log': portable(log_path), 'log_sha256': digest(log_path)}


def watchdog_control(directory):
    directory.mkdir(parents=True)
    record = directory/'timeout.json'

    def persist(pid, elapsed):
        save(record, {'status': 'UNKNOWN: deliberate watchdog control timeout',
                      'pid': pid, 'elapsed_before_kill': elapsed,
                      'no_partial_child_result_used': True})

    process = owned_child([sys.executable, '-c', 'import time; time.sleep(5)'],
                          directory/'child.log', 0.1, persist)
    assert process['timed_out'] and process['child_reaped'] and record.exists()
    assert json.loads(record.read_text())['status'].startswith('UNKNOWN:')
    result = {'status': 'PASS: parent persisted UNKNOWN then killed and reaped owned child',
              'process': process, 'persisted_UNKNOWN_sha256': digest(record),
              'solver_or_optimizer_called': False}
    save(directory/'result.json', result)
    return result


def tiny_formulas(directory):
    # Each of the eight clauses forbids exactly one assignment on3 variables.
    clauses = [[-i if assignment >> (i-1) & 1 else i for i in range(1, 4)]
               for assignment in range(8)]
    paths = {}
    for name, selected in [('sat', clauses[:-1]), ('unsat', clauses)]:
        path = directory/(name+'.cnf')
        path.write_text(f'p cnf 3 {len(selected)}\n'+''.join(' '.join(map(str, clause))+' 0\n' for clause in selected))
        paths[name] = path
    return clauses, paths


def control_child(backend, directory):
    assert backend in dict(BACKENDS) and directory.exists()
    runtime = runtime_binding(backend)
    assert runtime['native_factory_present']
    started = time.monotonic()
    output = {'status': 'running tiny backend controls', 'backend': backend,
              'runtime': runtime, 'source_hashes': source_hashes(), 'solver_calls': 0}
    for name, count, expected in [('sat', 7, True), ('unsat', 8, False)]:
        path = directory/(name+'.cnf')
        with solver_api.Solver(name=backend, with_proof=True) as solver:
            assert type(solver.solver).__name__ == runtime['backend_class']
            for clause in previous.read_full_clauses(path, 3, count):
                solver.add_clause(clause)
            answer = solver.solve()
            output['solver_calls'] += 1
            assert answer is expected
            row = {'answer': answer, 'CNF_sha256': digest(path), 'statistics': solver.accum_stats()}
            if answer:
                assignment = solver.get_model()
                positive = {value for value in assignment if value > 0}
                assert all(any((v in positive) if v > 0 else (-v not in positive) for v in clause)
                           for clause in previous.read_full_clauses(path, 3, count))
                row['model'] = assignment
            else:
                proof = solver.get_proof()
                assert proof is not None
                row['terminal_empty_clause_appended'] = not proof or proof[-1] != '0'
                if row['terminal_empty_clause_appended']:
                    proof.append('0')
                raw = directory/'tiny.drat'
                raw.write_text('\n'.join(proof)+'\n')
                row.update(proof_sha256=digest(raw), proof_lines=len(proof))
            output[name] = row
    output.update(status='tiny SAT/UNSAT answers and SAT model checked; direct DRAT pending',
                  elapsed_seconds=time.monotonic()-started)
    save(directory/'child-result.json', output)


def prepare(output, directory, checker):
    assert not output.exists() and not directory.exists()
    directory.mkdir(parents=True)
    model = checked_base(True)
    watch = watchdog_control(directory/'watchdog')
    attempts, selected = [], None
    progress = directory/'preparation-progress.json'
    for backend, class_name in BACKENDS:
        subdir = directory/backend
        subdir.mkdir()
        clauses, paths = tiny_formulas(subdir)
        row = {'backend': backend, 'class_name': class_name, 'passed': False,
               'runtime': runtime_binding(backend)}

        def persist(pid, elapsed):
            save(subdir/'timeout.json', {'status': 'UNKNOWN: tiny control exceeded its wall limit',
                                        'pid': pid, 'elapsed_before_kill': elapsed})

        try:
            process = owned_child([sys.executable, str(Path(__file__).resolve()), 'control-child',
                                   '--backend', backend, '--directory', str(subdir)],
                                  subdir/'child.log', LIMITS['tiny_control_child_wall_seconds'], persist)
            row['process'] = process
            assert not process['timed_out'] and process['returncode'] == 0
            child_path = subdir/'child-result.json'
            child = json.loads(child_path.read_text())
            assert child['runtime'] == row['runtime'] and child['source_hashes'] == source_hashes()
            assert child['backend'] == backend and child['solver_calls'] == 2
            assert child['sat']['answer'] is True and child['unsat']['answer'] is False
            positive = {value for value in child['sat']['model'] if value > 0}
            assert all(any((v in positive) if v > 0 else (-v not in positive) for v in clause) for clause in clauses[:-1])
            # Independent truth-table check binds the intended SAT/UNSAT tasks.
            satisfying = [bits for bits in range(8) if all(any(bool(bits >> (abs(v)-1) & 1) == (v > 0)
                           for v in clause) for clause in clauses[:-1])]
            assert satisfying == [7]
            assert not any(all(any(bool(bits >> (abs(v)-1) & 1) == (v > 0) for v in clause)
                               for clause in clauses) for bits in range(8))
            assert child['sat']['CNF_sha256'] == digest(paths['sat'])
            assert child['unsat']['CNF_sha256'] == digest(paths['unsat'])
            raw = subdir/'tiny.drat'
            assert digest(raw) == child['unsat']['proof_sha256']
            checked = subprocess.run([str(checker), str(paths['unsat']), str(raw),
                                      '-t', str(LIMITS['tiny_DRAT_seconds']), '-w'],
                                     capture_output=True, text=True, timeout=LIMITS['tiny_DRAT_seconds']+5, check=False)
            log = subdir/'direct-drat.log'
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            row.update(passed=True, child_result=portable(child_path), child_result_sha256=digest(child_path),
                       proof=portable(raw), proof_sha256=digest(raw),
                       direct_DRAT_log=portable(log), direct_DRAT_log_sha256=digest(log),
                       checker_executable_sha256=digest(checker), all8_truth_assignments_checked=True)
            selected = backend
        except Exception as error:
            row.update(error_type=type(error).__name__, error_message=str(error),
                       no_failed_or_partial_proof_used=True)
        attempts.append(row)
        save(progress, {'status': 'backend controls only; no production query', 'attempts': attempts})
        if selected is not None:
            break
    complete = selected is not None
    record = {'status': 'CaDiCaL production wrapper prepared; no production query' if complete
                       else 'no backend passed tiny proof controls; production unavailable',
              'complete': complete, 'source_hashes': source_hashes(), 'limits': LIMITS,
              'previous_preparation': portable(PREVIOUS_PREPARATION),
              'previous_preparation_sha256': PREVIOUS_PREPARATION_SHA,
              'overlay_model_sha256': previous.MODEL_SHA, 'cnf_sha256': previous.CNF_SHA,
              'formula': model['formula'], 'backend': selected,
              'runtime': next((row['runtime'] for row in attempts if row['backend'] == selected), None),
              'control_directory': portable(directory), 'backend_attempts': attempts,
              'watchdog_control': watch, 'production_solver_calls': 0,
              'assumptions': [], 'CNF_changes': 0, 'symmetry_constraints_added': 0,
              'timeout_policy': 'Persist UNKNOWN before SIGKILL; reap child; never use a partial proof.',
              'scope': 'Identical indexed35-core case4 coordinate-cover formula; a different backend only.'}
    save(output, record)
    print(json.dumps(record, indent=2), flush=True)
    assert complete


def checked_preparation(path, require_runtime=False, require_cnf=False):
    record = json.loads(path.read_text())
    assert record['complete'] and record['source_hashes'] == source_hashes() and record['limits'] == LIMITS
    assert record['previous_preparation_sha256'] == PREVIOUS_PREPARATION_SHA
    assert record['cnf_sha256'] == previous.CNF_SHA and record['overlay_model_sha256'] == previous.MODEL_SHA
    assert record['backend'] in dict(BACKENDS) and record['production_solver_calls'] == 0
    assert record['assumptions'] == [] and record['CNF_changes'] == record['symmetry_constraints_added'] == 0
    model = checked_base(require_cnf)
    assert record['formula'] == model['formula']
    accepted = [item for item in record['backend_attempts'] if item['passed']]
    assert len(accepted) == 1 and accepted[0]['backend'] == record['backend']
    for field, hash_field in [('child_result', 'child_result_sha256'), ('proof', 'proof_sha256'),
                             ('direct_DRAT_log', 'direct_DRAT_log_sha256')]:
        assert digest(ROOT/accepted[0][field]) == accepted[0][hash_field]
    assert accepted[0]['runtime'] == record['runtime']
    if require_runtime:
        assert runtime_binding(record['backend']) == record['runtime']
    return record, model


def solve_child(preparation, directory):
    prep, model = checked_preparation(preparation, True, True)
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic()
    row = {'status': 'child solving unchanged frozen CNF', 'source_hashes': source_hashes(),
           'preparation_sha256': digest(preparation), 'cnf_sha256': previous.CNF_SHA,
           'backend': prep['backend'], 'runtime': prep['runtime'], 'assumptions': []}
    with solver_api.Solver(name=prep['backend'], with_proof=True) as solver:
        assert type(solver.solver).__name__ == prep['runtime']['backend_class']
        count = 0
        for clause in previous.read_full_clauses(Path(model['cnf']), 134852, 439604):
            solver.add_clause(clause)
            count += 1
        assert count == 439604
        row.update(bootstrap_clauses_added=count, bootstrap_seconds=time.monotonic()-started)
        answer = solver.solve()
        row.update(solve_return_internal_seconds=time.monotonic()-started,
                   solver_statistics=solver.accum_stats())
        if answer:
            positive = {value for value in solver.get_model() if value > 0}
            row.update(status='SAT; parent exact witness inspection pending',
                       selected_columns=[a for a in range(1214) if a+1 in positive])
        else:
            assert answer is False
            proof = solver.get_proof()
            assert proof is not None
            row['terminal_empty_clause_appended'] = not proof or proof[-1] != '0'
            if row['terminal_empty_clause_appended']:
                proof.append('0')
            raw = directory/'raw.drat'
            raw.write_text('\n'.join(proof)+'\n')
            row.update(status='UNSAT; parent direct DRAT pending', raw_proof=portable(raw),
                       raw_proof_sha256=digest(raw), raw_proof_lines=len(proof))
    row.update(child_internal_seconds=time.monotonic()-started,
               peak_child_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(directory/'result.json', row)


def solve(preparation, directory, seconds, checker, checker_seconds):
    assert 0 < seconds <= LIMITS['production_child_wall_seconds_including_imports_bootstrap_solve']
    assert 0 < checker_seconds <= LIMITS['direct_DRAT_seconds'] and not directory.exists()
    prep, model = checked_preparation(preparation, True, True)
    directory.mkdir(parents=True)
    path = directory/'result.json'
    started = time.monotonic()
    result = {'status': 'parent running one bounded CaDiCaL child', 'source_hashes': source_hashes(),
        'preparation_sha256': digest(preparation), 'model_sha256': previous.MODEL_SHA,
        'cnf_sha256': previous.CNF_SHA, 'backend': prep['backend'], 'runtime': prep['runtime'],
        'requested_child_wall_seconds': seconds, 'requested_direct_checker_seconds': checker_seconds,
        'case_index': 4, 'assumptions': [], 'CNF_changes': 0, 'automatic_retries': 0,
        'whole_local_set_excluded': False, 'full_graph_found': False}

    def persist_timeout(pid, elapsed):
        result.update(status='UNKNOWN; hard child wall deadline reached', child_pid=pid,
                      elapsed_at_timeout=elapsed, partial_child_proof_used=False)
        save(path, result)

    save(path, result)
    try:
        process = owned_child([sys.executable, str(Path(__file__).resolve()), 'solve-child',
                               '--preparation', str(preparation), '--directory', str(directory/'child')],
                              directory/'child.log', seconds, persist_timeout)
        result['child_process'] = process
        if process['timed_out']:
            assert process['child_reaped'] and result['status'].startswith('UNKNOWN;')
            child_path = directory/'child/result.json'
            result['unaccepted_child_result_present'] = child_path.exists()
            if child_path.exists():
                result['unaccepted_child_result_sha256'] = digest(child_path)
        else:
            assert process['returncode'] == 0
            child_path = directory/'child/result.json'
            child = json.loads(child_path.read_text())
            assert child['source_hashes'] == source_hashes() and child['preparation_sha256'] == digest(preparation)
            assert child['cnf_sha256'] == previous.CNF_SHA and child['backend'] == prep['backend']
            assert child['runtime'] == prep['runtime'] and child['assumptions'] == []
            assert child['bootstrap_clauses_added'] == 439604
            result.update(child_result=portable(child_path), child_result_sha256=digest(child_path))
            if child['status'].startswith('SAT;'):
                result['partial_witness'] = previous.inspect_selected(child['selected_columns'])
                result['status'] = 'SAT; exact partial incidence and every original/coordinate cut checked'
            else:
                assert child['status'].startswith('UNSAT;')
                raw = ROOT/child['raw_proof']
                assert digest(raw) == child['raw_proof_sha256']
                result.update(status='solver UNSAT; direct DRAT pending',
                              raw_proof=portable(raw), raw_proof_sha256=digest(raw))
                save(path, result)
                retained, proof, log = directory/'retained.cnf', directory/'retained.drat', directory/'direct-drat.log'
                checked = subprocess.run([str(checker), model['cnf'], str(raw), '-t', str(checker_seconds),
                                          '-w', '-c', str(retained), '-l', str(proof)],
                                         capture_output=True, text=True, timeout=checker_seconds+5, check=False)
                log.write_text(checked.stdout+checked.stderr)
                assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
                inclusion = previous.retained_inclusion(Path(model['cnf']), retained, model['formula'])
                result['retained_certificate'] = {'cnf': portable(retained), 'cnf_sha256': digest(retained),
                    'proof': portable(proof), 'proof_sha256': digest(proof), 'input_inclusion': inclusion,
                    'checker_log': portable(log), 'checker_log_sha256': digest(log),
                    'checker_executable_sha256': digest(checker)}
                result['status'] = 'UNSAT with direct DRAT; separate cold complete-model/input/proof replay required'
        result.update(elapsed_seconds=time.monotonic()-started,
                      peak_parent_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(path, result)
    except Exception as error:
        result.update(status='error; no unchecked exclusion promoted', error_type=type(error).__name__,
                      error_message=str(error), elapsed_seconds=time.monotonic()-started)
        save(path, result)
        raise
    print(json.dumps({key: value for key, value in result.items() if key != 'partial_witness'}, indent=2), flush=True)


def replay(preparation, result_path, output, checker, checker_seconds):
    assert not output.exists() and 0 < checker_seconds <= LIMITS['cold_DRAT_seconds']
    prep, model = checked_preparation(preparation)
    result = json.loads(result_path.read_text())
    assert result['source_hashes'] == source_hashes() and result['preparation_sha256'] == digest(preparation)
    assert result['model_sha256'] == previous.MODEL_SHA and result['cnf_sha256'] == previous.CNF_SHA
    assert result['backend'] == prep['backend'] and result['runtime'] == prep['runtime']
    assert result['assumptions'] == [] and result['CNF_changes'] == 0
    report = {'status': 'cold complete formula replay pending', 'source_hashes': source_hashes(),
              'preparation_sha256': digest(preparation), 'result_sha256': digest(result_path),
              'backend': prep['backend'], 'bound_runtime': prep['runtime'], 'case_index': 4,
              'cnf_sha256': previous.CNF_SHA, 'whole_local_set_excluded': False,
              'complete_graph': False, 'solver_query_called': False}
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='conway-case4-cadical-cold-') as directory:
        full_path = Path(directory)/'full.cnf'
        base, ledger, formula = previous.overlay.build(full_path)
        assert normalized(formula) == model['formula'] and normalized(ledger) == model['cover_ledger_check']
        assert digest(full_path) == previous.CNF_SHA
        if result['status'].startswith('SAT;'):
            actual = previous.inspect_selected(result['partial_witness']['incidence']['selected_columns'])
            assert normalized(actual) == result['partial_witness']
            report['status'] = 'PASS: cold full formula and exact partial incidence/cut witness'
        elif result['status'].startswith('UNSAT with direct DRAT;'):
            item = result['retained_certificate']
            retained, proof = ROOT/item['cnf'], ROOT/item['proof']
            assert digest(retained) == item['cnf_sha256'] and digest(proof) == item['proof_sha256']
            inclusion = previous.retained_inclusion(full_path, retained, formula)
            assert normalized(inclusion) == item['input_inclusion']
            checked = subprocess.run([str(checker), str(retained), str(proof), '-t', str(checker_seconds), '-w'],
                                     capture_output=True, text=True, timeout=checker_seconds+5, check=False)
            log = output.with_suffix('.drat.log')
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            report.update(status='PASS: cold full formula, retained-input inclusion and DRAT',
                          excluded_indexed_core=4, input_inclusion=inclusion,
                          checker_log=portable(log), checker_log_sha256=digest(log))
        else:
            assert result['status'].startswith('UNKNOWN;')
            assert result['child_process']['timed_out'] and result['child_process']['child_reaped']
            assert result['partial_child_proof_used'] is False
            report['status'] = 'PASS: cold full formula and hard-timeout UNKNOWN binding; no exclusion'
    report.update(elapsed_seconds=time.monotonic()-started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--output', type=Path, required=True)
    prep.add_argument('--controls-directory', type=Path, required=True)
    prep.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    control = commands.add_parser('control-child')
    control.add_argument('--backend', choices=dict(BACKENDS), required=True)
    control.add_argument('--directory', type=Path, required=True)
    child = commands.add_parser('solve-child')
    child.add_argument('--preparation', type=Path, required=True)
    child.add_argument('--directory', type=Path, required=True)
    run = commands.add_parser('solve')
    run.add_argument('--preparation', type=Path, required=True)
    run.add_argument('--directory', type=Path, required=True)
    run.add_argument('--seconds', type=float, default=180)
    run.add_argument('--checker-seconds', type=int, default=60)
    run.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    check = commands.add_parser('replay')
    check.add_argument('--preparation', type=Path, required=True)
    check.add_argument('--result', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    check.add_argument('--checker-seconds', type=int, default=60)
    check.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output.resolve(), args.controls_directory.resolve(), args.drat_trim.resolve())
    elif args.command == 'control-child':
        control_child(args.backend, args.directory.resolve())
    elif args.command == 'solve-child':
        solve_child(args.preparation.resolve(), args.directory.resolve())
    elif args.command == 'solve':
        solve(args.preparation.resolve(), args.directory.resolve(), args.seconds,
              args.drat_trim.resolve(), args.checker_seconds)
    else:
        replay(args.preparation.resolve(), args.result.resolve(), args.output.resolve(),
               args.drat_trim.resolve(), args.checker_seconds)
