"""Separate bounded proof-enabled pilot for global-prism-free root cases.

This runner does not change any earlier formula or outcome. The four
cases cover the globally prism-free hypothesis only. SAT is validated
as a full ordinary99-vertex graph, even if a prism exists elsewhere.
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
import root_prism_free_overlay as overlay
import root_prism_free_structure as structure


ROOT = overlay.ROOT


def solve(model_path, seconds, proof_path, output):
    assert 0 < seconds <= 180
    model, _, _, _, _ = overlay.check_bindings(model_path, check_cnf=True)
    result = {'status': 'running', 'scope': overlay.SCOPE,
              'case_index': model['case_index'], 'partition': model['partition'],
              'model': overlay.portable(model_path), 'model_sha256': base.digest(model_path),
              'cnf_path': model['cnf'], 'cnf_sha256': model['cnf_sha256'],
              'solver': 'glucose4', 'proof_enabled': True,
              'requested_wall_budget_seconds': seconds,
              'budget_includes_cnf_parse_and_solver_bootstrap': True,
              'complete_outside_caps': True, 'global_prism_clauses': 34440,
              'minimum_partition_normalization_added': False,
              'graph_automorphism_assumptions': 0, 'lazy_cuts': 0,
              'excludes_whole_old_same_index_case': False,
              'completed_witness': None}
    base.save(output, result)
    started = time.monotonic()
    cnf = CNF(from_file=model['cnf'])
    assert (cnf.nv, len(cnf.clauses)) == (model['variables'], model['clauses'])
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
        del cnf
        gc.collect()
        remaining = seconds - (time.monotonic() - started)
        print(json.dumps({'case_index': model['case_index'],
                          'bootstrap_seconds': time.monotonic() - started,
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
        result['solve_return_seconds'] = time.monotonic() - started
        result['solver_statistics'] = solver.accum_stats()
        if answer is None:
            result['status'] = 'UNKNOWN; globally prism-free case remains open'
        elif answer is False:
            proof = solver.get_proof()
            assert proof and proof[-1] == '0'
            proof_path.parent.mkdir(parents=True, exist_ok=True)
            proof_path.write_text('\n'.join(proof) + '\n')
            result.update(status='solver UNSAT; saved proof requires independent verification',
                          proof_path=str(proof_path), proof_sha256=base.digest(proof_path),
                          proof_lines=len(proof))
        else:
            rows, labels, signatures, _, _, variables, _ = lex.primary_domain(14)
            point = base.inspect({v for v in solver.get_model() if v > 0},
                                 14, rows, labels, signatures, variables)
            adjacency = [sum(1 << j for j in neighbors) for neighbors in point['adjacency_lists']]
            triangles, prisms = structure.triangle_prisms(adjacency)
            assert len(triangles) == 231
            point['actual_induced_prisms'] = len(prisms)
            point['actual_global_prism_freeness'] = not prisms
            result.update(status='exact99-vertex SRG candidate; independent validation required',
                          completed_witness=point)
    result['total_seconds'] = time.monotonic() - started
    base.save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key != 'completed_witness'}), flush=True)
    return result


def batch(model_paths, seconds, logs, proofs, checker):
    assert 0 < seconds <= 180 and checker.is_file()
    models = [overlay.check_bindings(path, check_cnf=True)[0] for path in model_paths]
    assert [model['case_index'] for model in models] == [7, 8, 9, 10]
    assert len({model['structure_certificate_sha256'] for model in models}) == 1
    logs.mkdir(parents=True, exist_ok=True)
    proofs.mkdir(parents=True, exist_ok=True)
    state_path = logs/'batch.json'
    assert not state_path.exists(), 'Use a fresh pilot directory.'
    state = {'status': 'running four global-prism-free cases sequentially',
             'scope': overlay.SCOPE, 'requested_seconds_per_case': seconds,
             'hard_execution_limit_per_case': seconds + 60,
             'started_utc': datetime.now(timezone.utc).isoformat(),
             'cases': [{'index': model['case_index'], 'partition': model['partition'],
                        'status': 'not started', 'model': overlay.portable(path),
                        'model_sha256': base.digest(path)}
                       for path, model in zip(model_paths, models)]}
    base.save(state_path, state)
    started = time.monotonic()
    try:
        for model_path, model, entry in zip(model_paths, models, state['cases']):
            index = model['case_index']
            stem = f'case-{index:02d}'
            result_path, log_path = logs/f'{stem}-result.json', logs/f'{stem}.log'
            raw = Path(model['cnf']).with_name(stem + '-raw.drat')
            entry.update(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
                         result=overlay.portable(result_path), log=overlay.portable(log_path))
            base.save(state_path, state)
            print(json.dumps({'case_start': entry}), flush=True)
            command = [sys.executable, str(Path(__file__).resolve()), 'solve', str(model_path.resolve()),
                       '--seconds', str(seconds), '--proof', str(raw), '--output', str(result_path)]
            try:
                with log_path.open('w') as stream:
                    completed = subprocess.run(command, cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                               timeout=seconds + 60, check=False)
            except subprocess.TimeoutExpired:
                entry['status'] = 'execution limit without a terminal solver record'
                state['status'] = 'stopped on execution timeout; remaining cases not run'
                break
            if completed.returncode:
                entry.update(status='solver process failed', returncode=completed.returncode)
                state['status'] = 'stopped on execution failure; remaining cases not run'
                break
            result = json.loads(result_path.read_text())
            assert result['scope'] == overlay.SCOPE
            assert result['model_sha256'] == entry['model_sha256']
            assert result['case_index'] == index and result['cnf_sha256'] == model['cnf_sha256']
            entry.update(result_sha256=base.digest(result_path), solver_status=result['status'],
                         seconds=result['total_seconds'], statistics=result['solver_statistics'])
            if result['completed_witness'] is not None:
                assert result['completed_witness']['all_pair_equations_exact']
                entry['status'] = 'complete99-vertex candidate; independent validation required'
                state['status'] = 'stopped at complete candidate'
                break
            if result['status'].startswith('UNKNOWN'):
                entry['status'] = result['status']
            elif result['status'].startswith('solver UNSAT'):
                assert base.digest(raw) == result['proof_sha256']
                retained, trimmed = proofs/f'{stem}-core.cnf', proofs/f'{stem}-proof.drat'
                checker_log = logs/f'{stem}-drat.log'
                try:
                    with checker_log.open('w') as stream:
                        checked = subprocess.run([str(checker), model['cnf'], str(raw),
                                                  '-c', str(retained), '-l', str(trimmed), '-t', '60', '-w'],
                                                 cwd=ROOT, stdout=stream, stderr=subprocess.STDOUT,
                                                 timeout=65, check=False)
                except subprocess.TimeoutExpired:
                    entry['status'] = 'solver UNSAT; proof verification timed out'
                    state['status'] = 'stopped at unverified proof; remaining cases not run'
                    break
                if checked.returncode or 's VERIFIED' not in checker_log.read_text():
                    entry.update(status='solver UNSAT; proof verification did not pass',
                                 checker_returncode=checked.returncode)
                    state['status'] = 'stopped at unverified proof; remaining cases not run'
                    break
                with retained.open() as stream:
                    header = next(line.split() for line in stream if line.startswith('p cnf '))
                certificate = {'scope': overlay.SCOPE, 'excludes_whole_old_same_index_case': False,
                               'model': overlay.portable(model_path), 'model_sha256': base.digest(model_path),
                               'case_index': index, 'partition': model['partition'],
                               'full_cnf_sha256': model['cnf_sha256'],
                               'core_file': overlay.portable(retained), 'core_sha256': base.digest(retained),
                               'proof_file': overlay.portable(trimmed), 'proof_sha256': base.digest(trimmed),
                               'retained_clauses': int(header[3]), 'lazy_cuts': 0,
                               'graph_automorphism_assumptions': 0,
                               'wrapper_source_sha256': base.digest(Path(__file__).with_name('root_prism_free_certificate.py')),
                               'direct_checker_log': overlay.portable(checker_log),
                               'full_rebuild_replay_pending': True}
                certificate_path = proofs/f'{stem}-certificate.json'
                base.save(certificate_path, certificate)
                entry.update(status='UNSAT; direct proof verified', certificate=overlay.portable(certificate_path),
                             certificate_sha256=base.digest(certificate_path), retained_clauses=int(header[3]))
            else:
                raise AssertionError(result['status'])
            base.save(state_path, state)
            print(json.dumps({'case_finished': entry}), flush=True)
        else:
            state['status'] = 'bounded global-prism-free four-case pilot completed'
    except Exception as error:
        state.update(status='error; pilot stopped', error_type=type(error).__name__, error_message=str(error))
        base.save(state_path, state)
        raise
    state.update(elapsed_seconds=time.monotonic() - started,
                 finished_utc=datetime.now(timezone.utc).isoformat())
    base.save(state_path, state)
    print(json.dumps({'batch_status': state['status'], 'elapsed_seconds': state['elapsed_seconds'],
                      'case_statuses': [entry['status'] for entry in state['cases']]}), flush=True)
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    single = sub.add_parser('solve')
    single.add_argument('model', type=Path)
    single.add_argument('--seconds', type=float, required=True)
    single.add_argument('--proof', type=Path, required=True)
    single.add_argument('--output', type=Path, required=True)
    sequence = sub.add_parser('batch')
    sequence.add_argument('models', type=Path, nargs=4)
    sequence.add_argument('--seconds', type=float, required=True)
    sequence.add_argument('--logs', type=Path, required=True)
    sequence.add_argument('--proofs', type=Path, required=True)
    sequence.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'solve':
        solve(args.model, args.seconds, args.proof, args.output)
    else:
        batch(args.models, args.seconds, args.logs.resolve(), args.proofs.resolve(), args.drat_trim.resolve())
