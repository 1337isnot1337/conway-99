"""Separate proof-enabled batch for maximum-anchor cases 7 through 10.

The new normalization covers the eleven-case union. It does not preserve
each original case individually. These four cases have maximum near count
zero and force all 84 cell-side edges absent. The frozen root and lex
sources, models, and completed runs are not changed.
"""

import argparse
from datetime import datetime, timezone
import gc
import json
from pathlib import Path
import shutil
import subprocess
import sys
from threading import Timer
import time

from pysat.formula import CNF
from pysat.solvers import Solver

import root_full_caps as base
import root_full_caps_anchor_max as maximum
import root_full_caps_lex as lex


ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ['root_full_caps_anchor_max_solve.py', 'root_full_caps_anchor_max_certificate.py']


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
    assert all(state['cases'][i]['status'] == 'UNKNOWN; case remains open' for i in range(7, 11))
    return state


def completed_lex(path):
    state = json.loads(path.read_text())
    assert state['status'] == 'bounded two-case pilot completed; other rooted cases not tested here'
    assert [case['index'] for case in state['cases']] == [0, 10]
    assert all(case['status'] == 'UNKNOWN; case remains open' for case in state['cases'])
    return state


def maximum_certificate(path, full_replay=False):
    record = json.loads(path.read_text())
    for name, expected in record['source_hashes'].items():
        assert base.digest(Path(__file__).with_name(name)) == expected
    if full_replay:
        assert json.loads(json.dumps(maximum.generate())) == record
    assert record['scope'] == 'new maximum-anchor eleven-case union; not each original case separately'
    assert record['solver_called'] is False and record['full_cnf_built'] is False
    return record


def build(analysis_path, maximum_path, index, original_batch, lex_batch, cnf_path, model_path):
    assert index in range(7, 11)
    state = completed_original(original_batch)
    completed_lex(lex_batch)
    certificate = maximum_certificate(maximum_path, full_replay=True)
    assert not cnf_path.exists() and not model_path.exists(), 'Use new maximum-anchor paths.'
    temporary_model = cnf_path.with_suffix('.lex-only.json')
    assert not temporary_model.exists()
    model = lex.build(analysis_path, index, cnf_path, temporary_model)
    analysis = json.loads(analysis_path.read_text())
    assert state['manifest_sha256'] == analysis['base_manifest_sha256']
    assert certificate['base_manifest_sha256'] == analysis['base_manifest_sha256']
    assert certificate['domain_sha256'] == analysis['domain_sha256']
    assert model['case']['base_cnf_sha256'] == json.loads(
        (ROOT/state['manifest']).read_text())['cases'][index]['cnf_sha256']
    case, maximum_case = model['case'], certificate['cases'][index]
    assert maximum_case['partition'] == case['partition']
    assert maximum_case['maximum_near_count'] == 0
    extra = maximum_case['clauses']
    assert len(extra) == 84 and all(len(clause) == 1 and clause[0] < 0 for clause in extra)
    side_variables = {-clause[0] for clause in extra}
    assert len(side_variables) == 84
    for generator in case['generators']:
        image = lex.lift(tuple(case['partition']), generator['image'])['edge_image']
        assert {image[v-1] for v in side_variables} == side_variables
    lex_hash = model['cnf_sha256']
    pending = cnf_path.with_name(cnf_path.name+'.pending')
    assert not pending.exists()
    with cnf_path.open('rb') as incoming, pending.open('wb') as outgoing:
        assert incoming.readline() == f'p cnf {case["total_variables"]} {case["total_clauses"]}\n'.encode()
        outgoing.write(f'p cnf {case["total_variables"]} {case["total_clauses"]+84}\n'.encode())
        shutil.copyfileobj(incoming, outgoing)
        for clause in extra:
            outgoing.write(f'{clause[0]} 0\n'.encode())
    pending.replace(cnf_path)
    model.update(original_batch=portable(original_batch),
                 original_batch_sha256=base.digest(original_batch),
                 lex_pilot_batch=portable(lex_batch), lex_pilot_batch_sha256=base.digest(lex_batch),
                 maximum_anchor_certificate=portable(maximum_path),
                 maximum_anchor_certificate_sha256=base.digest(maximum_path),
                 scope='new maximum-anchor normalization case; not the entire old same-index case',
                 status='maximum-anchor case CNF built; no solve',
                 maximum_near_count=0, maximum_anchor_clauses=84,
                 variables=case['total_variables'], clauses=case['total_clauses']+84,
                 lex_cnf_sha256=lex_hash, cnf_sha256=base.digest(cnf_path),
                 run_support_source_hashes={name: base.digest(Path(__file__).with_name(name))
                                           for name in SUPPORT})
    base.save(model_path, model)
    print(json.dumps({'status': model['status'], 'case': index,
                      'variables': model['variables'], 'clauses': model['clauses'],
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
    lex_path = ROOT/model['lex_pilot_batch']
    assert base.digest(lex_path) == model['lex_pilot_batch_sha256']
    completed_lex(lex_path)
    maximum_path = ROOT/model['maximum_anchor_certificate']
    assert base.digest(maximum_path) == model['maximum_anchor_certificate_sha256']
    certificate = maximum_certificate(maximum_path)
    assert certificate['base_manifest_sha256'] == analysis['base_manifest_sha256']
    assert certificate['domain_sha256'] == analysis['domain_sha256']
    case = model['case']
    assert case == analysis['cases'][case['index']] and case['index'] in range(7, 11)
    maximum_case = certificate['cases'][case['index']]
    assert maximum_case['partition'] == case['partition']
    assert maximum_case['maximum_near_count'] == model['maximum_near_count'] == 0
    assert maximum_case['clause_count'] == model['maximum_anchor_clauses'] == 84
    assert model['variables'] == case['total_variables']
    assert model['clauses'] == case['total_clauses']+84
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
              'normalization': 'maximum near-anchor count; new case in an exhaustive union',
              'excludes_old_same_index_case': False,
              'requested_wall_budget_seconds': seconds,
              'budget_includes_cnf_parse_and_solver_bootstrap': True,
              'full_outside_caps': True, 'lex_generators': case['generator_count'],
              'graph_automorphism_assumptions': 0, 'lazy_cuts': 0,
              'completed_witness': None}
    base.save(output, result)
    print(json.dumps({'start': result}), flush=True)
    started = time.monotonic()
    cnf = CNF(from_file=model['cnf'])
    assert (cnf.nv, len(cnf.clauses)) == (model['variables'], model['clauses'])
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
            result['status'] = 'unknown at wall budget; this maximum-anchor case remains open'
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
    assert [model['case']['index'] for model in models] == [7, 8, 9, 10]
    assert 0 < seconds <= 60 and checker.is_file()
    assert len({model['analysis_sha256'] for model in models}) == 1
    assert len({model['maximum_anchor_certificate_sha256'] for model in models}) == 1
    logs.mkdir(parents=True, exist_ok=True)
    proofs.mkdir(parents=True, exist_ok=True)
    state_path = logs/'batch.json'
    assert not state_path.exists(), 'Use a fresh maximum-anchor output directory.'
    state = {'status': 'running four maximum-anchor cases sequentially',
             'scope': 'new maximum-anchor cases 7 through 10; not old same-index exclusions',
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
            state['status'] = 'stopped on execution timeout; remaining maximum-anchor cases not run'
            break
        if completed.returncode != 0:
            entry.update(status='solver process failed', returncode=completed.returncode)
            state['status'] = 'stopped on execution failure; remaining maximum-anchor cases not run'
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
            entry['status'] = 'UNKNOWN; maximum-anchor case remains open'
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
                state['status'] = 'stopped at unverified proof; remaining maximum-anchor cases not run'
                break
            if checked.returncode != 0 or 's VERIFIED' not in checker_log.read_text():
                entry.update(status='solver UNSAT; proof verification did not pass',
                             checker_returncode=checked.returncode)
                state['status'] = 'stopped at unverified proof; remaining maximum-anchor cases not run'
                break
            with retained.open() as stream:
                header = next(line.split() for line in stream if line.startswith('p cnf '))
            certificate = {'scope': 'one new maximum-anchor case in an exhaustive eleven-case union',
                           'excludes_old_same_index_case': False,
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
        state['status'] = 'bounded maximum-anchor batch completed; maximum-anchor cases 0 through 6 not tested here'
    state.update(elapsed_seconds=time.monotonic()-started,
                 finished_utc=datetime.now(timezone.utc).isoformat())
    base.save(state_path, state)
    print(json.dumps({'batch_status': state['status'], 'elapsed_seconds': state['elapsed_seconds'],
                      'case_statuses': [entry['status'] for entry in state['cases']]}), flush=True)
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prepare = sub.add_parser('build')
    prepare.add_argument('analysis', type=Path)
    prepare.add_argument('--case', type=int, choices=range(7, 11), required=True)
    prepare.add_argument('--maximum-certificate', type=Path, required=True)
    prepare.add_argument('--original-batch', type=Path, required=True)
    prepare.add_argument('--lex-pilot-batch', type=Path, required=True)
    prepare.add_argument('--cnf', type=Path, required=True)
    prepare.add_argument('--output', type=Path, required=True)
    single = sub.add_parser('solve')
    single.add_argument('model', type=Path)
    single.add_argument('--seconds', type=float, default=60)
    single.add_argument('--proof', type=Path, required=True)
    single.add_argument('--output', type=Path, required=True)
    sequence = sub.add_parser('batch')
    sequence.add_argument('models', type=Path, nargs=4)
    sequence.add_argument('--seconds', type=float, default=60)
    sequence.add_argument('--logs', type=Path, required=True)
    sequence.add_argument('--proofs', type=Path, required=True)
    sequence.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'build':
        build(args.analysis, args.maximum_certificate, args.case, args.original_batch,
              args.lex_pilot_batch, args.cnf, args.output)
    elif args.command == 'solve':
        solve(args.model, args.seconds, args.proof, args.output)
    else:
        batch(args.models, args.seconds, args.logs.resolve(), args.proofs.resolve(), args.drat_trim.resolve())
