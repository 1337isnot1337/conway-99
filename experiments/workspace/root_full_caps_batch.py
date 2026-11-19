"""Sequential bounded eleven-case rooted search with durable status.

The model must be constructed and independently reviewed before this
command is launched. Every UNSAT return is checked against its exact
input formula; a timeout never counts as an excluded case.
"""

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import subprocess
import sys
import time

from root_full_caps import digest, save


ROOT = Path(__file__).resolve().parents[2]


def portable(path):
    path = path.resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def run(manifest_path, seconds, logs, proofs, checker):
    manifest_path = manifest_path.resolve()
    logs, proofs, checker = logs.resolve(), proofs.resolve(), checker.resolve()
    assert seconds > 0 and checker.is_file()
    model = json.loads(manifest_path.read_text())
    assert model['metadata']['degree'] == 14 and len(model['cases']) == 11
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    logs.mkdir(parents=True, exist_ok=True)
    proofs.mkdir(parents=True, exist_ok=True)
    state_path = logs/'batch.json'
    assert not state_path.exists(), 'Preserve the previous batch; use a fresh output directory.'
    manifest_hash = digest(manifest_path)
    state = {'status': 'running sequential batch', 'manifest': portable(manifest_path),
             'manifest_sha256': manifest_hash, 'requested_seconds_per_case': seconds,
             'hard_execution_limit_per_case': seconds+60,
             'proof_checker_limit_seconds': 60,
             'started_utc': datetime.now(timezone.utc).isoformat(),
             'cases': [{'index': case['index'], 'partition': case['partition'],
                        'status': 'not started'} for case in model['cases']]}
    save(state_path, state)
    started = time.monotonic()
    helper = Path(__file__).with_name('root_full_caps.py').resolve()
    for case, entry in zip(model['cases'], state['cases']):
        index = case['index']
        assert entry['index'] == index
        stem = f'case-{index:02d}'
        result_path, log_path = logs/f'{stem}-result.json', logs/f'{stem}.log'
        raw = Path(case['cnf_path']).with_name(f'{stem}-raw.drat')
        entry.update(status='running', started_utc=datetime.now(timezone.utc).isoformat(),
                     result=portable(result_path), log=portable(log_path))
        save(state_path, state)
        print(json.dumps({'case_start': entry}), flush=True)
        command = [sys.executable, str(helper), 'solve', str(manifest_path),
                   '--case', str(index), '--seconds', str(seconds), '--proof', str(raw),
                   '--output', str(result_path)]
        try:
            with log_path.open('w') as stream:
                completed = subprocess.run(command, cwd=ROOT, stdout=stream,
                                           stderr=subprocess.STDOUT, timeout=seconds+60,
                                           check=False)
        except subprocess.TimeoutExpired:
            entry['status'] = 'execution limit reached without a terminal solver record'
            state['status'] = 'stopped on execution timeout; remaining cases not run'
            save(state_path, state)
            break
        if completed.returncode != 0:
            entry.update(status='solver process failed', returncode=completed.returncode)
            state['status'] = 'stopped on execution failure; remaining cases not run'
            save(state_path, state)
            break
        result = json.loads(result_path.read_text())
        assert result['manifest_sha256'] == manifest_hash
        assert result['case_index'] == index and result['cnf_sha256'] == case['cnf_sha256']
        entry.update(result_sha256=digest(result_path), solver_status=result['status'],
                     seconds=result['total_seconds'], statistics=result['solver_statistics'])
        if result['completed_witness'] is not None:
            assert result['completed_witness']['all_pair_equations_exact']
            entry['status'] = 'complete99-vertex candidate; independent validation required'
            state['status'] = 'stopped at complete candidate'
            save(state_path, state)
            print(json.dumps({'case_finished': entry}), flush=True)
            break
        if result['status'].startswith('unknown'):
            entry['status'] = 'UNKNOWN; case remains open'
        elif result['status'].startswith('solver UNSAT'):
            assert digest(raw) == result['proof_sha256']
            retained = proofs/f'root-full-caps-{stem}-core.cnf'
            trimmed = proofs/f'root-full-caps-{stem}-proof.drat'
            checked_log = logs/f'{stem}-drat.log'
            checking = time.monotonic()
            try:
                with checked_log.open('w') as stream:
                    checked = subprocess.run([str(checker), case['cnf_path'], str(raw),
                                              '-c', str(retained), '-l', str(trimmed),
                                              '-t', '60', '-w'], cwd=ROOT, stdout=stream,
                                             stderr=subprocess.STDOUT, timeout=60, check=False)
            except subprocess.TimeoutExpired:
                entry['status'] = 'solver UNSAT; proof verification timed out'
                state['status'] = 'stopped at unverified proof; remaining cases not run'
                save(state_path, state)
                break
            checker_output = checked_log.read_text()
            if checked.returncode != 0 or 's VERIFIED' not in checker_output:
                entry.update(status='solver UNSAT; proof verification did not pass',
                             checker_returncode=checked.returncode)
                state['status'] = 'stopped at unverified proof; remaining cases not run'
                save(state_path, state)
                break
            with retained.open() as stream:
                header = next(line.split() for line in stream if line.startswith('p cnf '))
            certificate = {'scope': 'one exhaustive rooted anchor normalization case',
                           'model_manifest': portable(manifest_path),
                           'model_manifest_sha256': manifest_hash,
                           'case_index': index, 'partition': case['partition'],
                           'full_cnf_sha256': case['cnf_sha256'],
                           'core_file': portable(retained), 'core_sha256': digest(retained),
                           'proof_file': portable(trimmed), 'proof_sha256': digest(trimmed),
                           'retained_clauses': int(header[3]),
                           'wrapper_source_sha256': digest(Path(__file__).with_name('root_full_caps_certificate.py')),
                           'lazy_cuts': 0, 'orbit_equalities': 0,
                           'direct_checker_log': portable(checked_log)}
            certificate_path = proofs/f'root-full-caps-{stem}-certificate.json'
            save(certificate_path, certificate)
            entry.update(status='UNSAT; direct proof verified',
                         proof_checker_seconds=time.monotonic()-checking,
                         certificate=portable(certificate_path),
                         certificate_sha256=digest(certificate_path),
                         retained_clauses=int(header[3]))
        else:
            raise AssertionError(result['status'])
        save(state_path, state)
        print(json.dumps({'case_finished': entry}), flush=True)
    else:
        excluded = sum(entry['status'] == 'UNSAT; direct proof verified' for entry in state['cases'])
        state['status'] = ('all eleven cases have direct verified proofs; independent full replay required'
                           if excluded == 11 else 'bounded batch completed; open cases remain')
    state['elapsed_seconds'] = time.monotonic()-started
    state['finished_utc'] = datetime.now(timezone.utc).isoformat()
    save(state_path, state)
    print(json.dumps({'batch_status': state['status'], 'elapsed_seconds': state['elapsed_seconds'],
                      'case_statuses': [entry['status'] for entry in state['cases']]}), flush=True)
    return state


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--seconds', type=float, default=180)
    parser.add_argument('--logs', type=Path, required=True)
    parser.add_argument('--proofs', type=Path, required=True)
    parser.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    run(args.manifest, args.seconds, args.logs, args.proofs, args.drat_trim)
