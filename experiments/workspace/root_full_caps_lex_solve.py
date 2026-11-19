"""Separate proof-enabled pilot for rooted lex cases 0 and 10.

The frozen base and analysis sources are not changed. Building requires
the original eleven-case batch to have ended with both pilot cases open.
The pilot uses the same Glucose4 configuration and budget convention as
that batch; its planned budget is 60 seconds for each case.
"""

import argparse
from datetime import datetime, timezone
import gc
import json
from pathlib import Path
import subprocess
import sys
from threading import Timer
import time

from pysat.formula import CNF
from pysat.solvers import Solver

import root_full_caps as base
import root_full_caps_lex as lex


ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ['root_full_caps_lex_solve.py', 'root_full_caps_lex_certificate.py']


def portable(path):
    path = path.resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def completed_original(path):
    state = json.loads(path.read_text())
    assert state['status'] == 'bounded batch completed; open cases remain'
    assert len(state['cases']) == 11
    assert [case['index'] for case in state['cases']] == list(range(11))
    assert all(case['status'] in ('UNKNOWN; case remains open', 'UNSAT; direct proof verified')
               for case in state['cases'])
    assert all(state['cases'][i]['status'] == 'UNKNOWN; case remains open' for i in (0, 10))
    return state


def build(analysis_path, index, original_batch, cnf_path, model_path):
    assert index in (0, 10)
    state = completed_original(original_batch)
    assert not cnf_path.exists() and not model_path.exists(), 'Use new pilot paths.'
    model = lex.build(analysis_path, index, cnf_path, model_path)
    analysis = json.loads(analysis_path.read_text())
    assert state['manifest_sha256'] == analysis['base_manifest_sha256']
    assert model['case']['base_cnf_sha256'] == json.loads(
        (ROOT/state['manifest']).read_text())['cases'][index]['cnf_sha256']
    model.update(original_batch=portable(original_batch),
                 original_batch_sha256=base.digest(original_batch),
                 run_support_source_hashes={name: base.digest(Path(__file__).with_name(name))
                                           for name in SUPPORT})
    base.save(model_path, model)
    print(json.dumps({'status': model['status'], 'case': index,
                      'variables': model['case']['total_variables'],
                      'clauses': model['case']['total_clauses'],
                      'cnf_sha256': model['cnf_sha256'],
                      'model_sha256': base.digest(model_path)}), flush=True)
    return model


def check_bindings(model_path, check_cnf=True):
    model = json.loads(model_path.read_text())
    analysis_path = ROOT/model['analysis']
    assert base.digest(analysis_path) == model['analysis_sha256']
    analysis = json.loads(analysis_path.read_text())
    assert analysis['source_hashes'] == model['source_hashes']
    for hashes in (model['run_support_source_hashes'], analysis['source_hashes'],
                   analysis['base_source_hashes']):
        for name, expected in hashes.items():
            assert base.digest(Path(__file__).with_name(name)) == expected
    assert base.digest(ROOT/analysis['coverage']) == analysis['coverage_sha256']
    assert base.digest(ROOT/analysis['base_manifest']) == analysis['base_manifest_sha256']
    original_path = ROOT/model['original_batch']
    assert base.digest(original_path) == model['original_batch_sha256']
    completed_original(original_path)
    case = model['case']
    assert case == analysis['cases'][case['index']] and case['index'] in (0, 10)
    if check_cnf:
        assert base.digest(Path(model['cnf'])) == model['cnf_sha256']
    return model, analysis


def solve(model_path, seconds, proof_path, output):
    assert seconds > 0
    model, _ = check_bindings(model_path)
    case = model['case']
    result = {'status': 'running', 'case_index': case['index'], 'partition': case['partition'],
              'model': portable(model_path), 'model_sha256': base.digest(model_path),
              'cnf_path': model['cnf'], 'cnf_sha256': model['cnf_sha256'],
              'solver': 'glucose4', 'proof_enabled': True,
              'requested_wall_budget_seconds': seconds,
              'budget_includes_cnf_parse_and_solver_bootstrap': True,
              'full_outside_caps': True, 'lex_generators': case['generator_count'],
              'graph_automorphism_assumptions': 0, 'lazy_cuts': 0,
              'completed_witness': None}
    base.save(output, result)
    print(json.dumps({'start': result}), flush=True)
    started = time.monotonic()
    cnf = CNF(from_file=model['cnf'])
    assert (cnf.nv, len(cnf.clauses)) == (case['total_variables'], case['total_clauses'])
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
        del cnf
        gc.collect()
        remaining = seconds-(time.monotonic()-started)
        print(json.dumps({'solver_ready_seconds': time.monotonic()-started,
                          'remaining_seconds': max(0, remaining)}), flush=True)
        if remaining > 0:
            timer = Timer(remaining, solver.interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
        else:
            answer = None
        result['solve_return_seconds'] = time.monotonic()-started
        result['solver_statistics'] = solver.accum_stats()
        if answer is None:
            result['status'] = 'unknown at wall budget; this normalization case remains open'
        elif answer is False:
            proof = solver.get_proof()
            assert proof is not None
            proof_path.parent.mkdir(parents=True, exist_ok=True)
            with proof_path.open('w') as stream:
                for line in proof:
                    stream.write(line+'\n')
            result.update(status='solver UNSAT; saved proof requires independent verification',
                          proof_path=str(proof_path), proof_sha256=base.digest(proof_path),
                          proof_lines=len(proof))
        else:
            rows, labels, signatures, _, _, variables, _ = lex.primary_domain(14)
            point = base.inspect({v for v in solver.get_model() if v > 0},
                                 14, rows, labels, signatures, variables)
            result.update(status='exact99-vertex SRG candidate; independent validation required',
                          completed_witness=point)
    result['total_seconds'] = time.monotonic()-started
    base.save(output, result)
    print(json.dumps({key: value for key, value in result.items()
                      if key != 'completed_witness'}), flush=True)
    return result


def batch(model_paths, seconds, logs, proofs, checker):
    models = [check_bindings(path)[0] for path in model_paths]
    assert [model['case']['index'] for model in models] == [0, 10]
    assert 0 < seconds <= 60 and checker.is_file()
    assert len({model['analysis_sha256'] for model in models}) == 1
    logs.mkdir(parents=True, exist_ok=True)
    proofs.mkdir(parents=True, exist_ok=True)
    state_path = logs/'batch.json'
    assert not state_path.exists(), 'Use a fresh pilot output directory.'
    state = {'status': 'running sequential two-case lex pilot',
             'requested_seconds_per_case': seconds, 'hard_execution_limit_per_case': seconds+60,
             'started_utc': datetime.now(timezone.utc).isoformat(),
             'cases': [{'index': model['case']['index'], 'partition': model['case']['partition'],
                        'status': 'not started', 'model': portable(path),
                        'model_sha256': base.digest(path)}
                       for path, model in zip(model_paths, models)]}
    base.save(state_path, state)
    started = time.monotonic()
    for model_path, model, entry in zip(model_paths, models, state['cases']):
        index, case = entry['index'], model['case']
        stem = f'case-{index:02d}'
        result_path, log_path = logs/f'{stem}-result.json', logs/f'{stem}.log'
        raw = Path(model['cnf']).with_name(stem+'-raw.drat')
        entry.update(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
                     result=portable(result_path), log=portable(log_path))
        base.save(state_path, state)
        print(json.dumps({'case_start': entry}), flush=True)
        command = [sys.executable, str(Path(__file__).resolve()), 'solve', str(model_path.resolve()),
                   '--seconds', str(seconds), '--proof', str(raw), '--output', str(result_path)]
        try:
            with log_path.open('w') as stream:
                completed = subprocess.run(command, cwd=ROOT, stdout=stream,
                                           stderr=subprocess.STDOUT, timeout=seconds+60, check=False)
        except subprocess.TimeoutExpired:
            entry['status'] = 'execution limit reached without a terminal solver record'
            state['status'] = 'stopped on execution timeout; remaining pilot not run'
            break
        if completed.returncode != 0:
            entry.update(status='solver process failed', returncode=completed.returncode)
            state['status'] = 'stopped on execution failure; remaining pilot not run'
            break
        result = json.loads(result_path.read_text())
        assert result['model_sha256'] == entry['model_sha256']
        assert result['case_index'] == index and result['cnf_sha256'] == model['cnf_sha256']
        entry.update(result_sha256=base.digest(result_path), solver_status=result['status'],
                     seconds=result['total_seconds'], statistics=result['solver_statistics'])
        if result['completed_witness'] is not None:
            assert result['completed_witness']['all_pair_equations_exact']
            entry['status'] = 'complete99-vertex candidate; independent validation required'
            state['status'] = 'stopped at complete candidate'
            break
        if result['status'].startswith('unknown'):
            entry['status'] = 'UNKNOWN; case remains open'
        elif result['status'].startswith('solver UNSAT'):
            assert base.digest(raw) == result['proof_sha256']
            retained, trimmed = proofs/f'{stem}-core.cnf', proofs/f'{stem}-proof.drat'
            checker_log = logs/f'{stem}-drat.log'
            try:
                with checker_log.open('w') as stream:
                    checked = subprocess.run([str(checker), model['cnf'], str(raw),
                                              '-c', str(retained), '-l', str(trimmed), '-t', '60', '-w'],
                                             cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                             timeout=60, check=False)
            except subprocess.TimeoutExpired:
                entry['status'] = 'solver UNSAT; proof verification timed out'
                state['status'] = 'stopped at unverified proof; remaining pilot not run'
                break
            if checked.returncode != 0 or 's VERIFIED' not in checker_log.read_text():
                entry.update(status='solver UNSAT; proof verification did not pass',
                             checker_returncode=checked.returncode)
                state['status'] = 'stopped at unverified proof; remaining pilot not run'
                break
            with retained.open() as stream:
                header = next(line.split() for line in stream if line.startswith('p cnf '))
            certificate = {'scope': 'one exhaustive rooted case with an orbit-preserving lex overlay',
                           'model': portable(model_path), 'model_sha256': base.digest(model_path),
                           'case_index': index, 'partition': case['partition'],
                           'full_cnf_sha256': model['cnf_sha256'],
                           'core_file': portable(retained), 'core_sha256': base.digest(retained),
                           'proof_file': portable(trimmed), 'proof_sha256': base.digest(trimmed),
                           'retained_clauses': int(header[3]), 'lazy_cuts': 0,
                           'graph_automorphism_assumptions': 0,
                           'wrapper_source_sha256': base.digest(Path(__file__).with_name(SUPPORT[1])),
                           'direct_checker_log': portable(checker_log)}
            certificate_path = proofs/f'{stem}-certificate.json'
            base.save(certificate_path, certificate)
            entry.update(status='UNSAT; direct proof verified', certificate=portable(certificate_path),
                         certificate_sha256=base.digest(certificate_path), retained_clauses=int(header[3]))
        else:
            raise AssertionError(result['status'])
        base.save(state_path, state)
        print(json.dumps({'case_finished': entry}), flush=True)
    else:
        state['status'] = 'bounded two-case pilot completed; other rooted cases not tested here'
    state.update(elapsed_seconds=time.monotonic()-started,
                 finished_utc=datetime.now(timezone.utc).isoformat())
    base.save(state_path, state)
    print(json.dumps({'pilot_status': state['status'], 'elapsed_seconds': state['elapsed_seconds'],
                      'case_statuses': [entry['status'] for entry in state['cases']]}), flush=True)
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prepare = sub.add_parser('build')
    prepare.add_argument('analysis', type=Path)
    prepare.add_argument('--case', type=int, choices=(0, 10), required=True)
    prepare.add_argument('--original-batch', type=Path, required=True)
    prepare.add_argument('--cnf', type=Path, required=True)
    prepare.add_argument('--output', type=Path, required=True)
    single = sub.add_parser('solve')
    single.add_argument('model', type=Path)
    single.add_argument('--seconds', type=float, default=60)
    single.add_argument('--proof', type=Path, required=True)
    single.add_argument('--output', type=Path, required=True)
    sequence = sub.add_parser('batch')
    sequence.add_argument('models', type=Path, nargs=2)
    sequence.add_argument('--seconds', type=float, default=60)
    sequence.add_argument('--logs', type=Path, required=True)
    sequence.add_argument('--proofs', type=Path, required=True)
    sequence.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'build':
        build(args.analysis, args.case, args.original_batch, args.cnf, args.output)
    elif args.command == 'solve':
        solve(args.model, args.seconds, args.proof, args.output)
    else:
        batch(args.models, args.seconds, args.logs.resolve(), args.proofs.resolve(), args.drat_trim.resolve())
