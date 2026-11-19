"""Fresh proof and cold replay for a terminal lazy free480 UNSAT.

The loop's incremental answer is not a certificate. This driver rebuilds
the final necessary formula from exact potentials and clause bounds, reruns one
fresh proof-enabled query, and checks DRAT. A separate cold command
rebuilds it again, verifies retained-input inclusion, and rechecks DRAT.
"""

import argparse
import gc
import json
from pathlib import Path
import resource
import subprocess
import tempfile
from threading import Timer
import time

from pysat.solvers import Solver

import root_prism_free_f0_lazy_row_loop as loop


ROOT = loop.ROOT
digest, portable, save = loop.digest, loop.portable, loop.save


def inputs_subset(cnf, retained):
    clauses = list(loop.BASE.read_clauses(retained))
    needed = {tuple(sorted(clause)) for clause in clauses}
    for clause in cnf.clauses:
        needed.discard(tuple(sorted(clause)))
    assert not needed
    return len(clauses)


def checker_call(checker, cnf, proof, seconds, log, retained=None, trimmed=None):
    command = [str(checker), str(cnf), str(proof), '-t', str(seconds), '-w']
    if retained is not None:
        assert trimmed is not None
        command += ['-c', str(retained), '-l', str(trimmed)]
    started = time.monotonic()
    try:
        completed = subprocess.run(command, capture_output=True, text=True,
                                   timeout=seconds+5, check=False)
    except subprocess.TimeoutExpired as error:
        log.write_text(str(error)+'\n')
        return {'verified': False, 'timeout': True, 'seconds': time.monotonic()-started}
    log.write_text(completed.stdout+completed.stderr)
    return {'verified': completed.returncode == 0 and 's VERIFIED' in completed.stdout,
            'timeout': False, 'returncode': completed.returncode,
            'seconds': time.monotonic()-started}


def prove(preparation, result_path, directory, seconds, checker, checker_seconds):
    assert not directory.exists() and 0 < seconds <= 60 and 0 < checker_seconds <= 60
    result = loop.load_json(result_path)
    assert result['status'].startswith('UNSAT_UNCERTIFIED:')
    directory.mkdir(parents=True)
    output = directory/'certificate.json'
    report = {'status': 'fresh final-formula proof preparation running; no exclusion',
        'source_sha256': digest(Path(__file__)), 'loop_source_sha256': digest(Path(loop.__file__)),
        'preparation': portable(preparation), 'preparation_sha256': digest(preparation),
        'loop_result': portable(result_path), 'loop_result_sha256': digest(result_path),
        'fresh_query_seconds_including_bootstrap': seconds, 'checker_seconds': checker_seconds,
        'checker_sha256': digest(checker), 'assumptions': [],
        'whole_component_excluded': False, 'full_graph_completion': False}
    save(output, report)
    total_started = time.monotonic()
    try:
        cnf, registry, _, rebuilt = loop.reconstruct(preparation, result_path)
        save(directory/'cold-formula-replay.json', rebuilt)
        formula_path = directory/'fresh.cnf'
        cnf.to_file(formula_path)
        assert digest(formula_path) == result['final_cnf_sha256']
        report.update(final_cnf_sha256=digest(formula_path), variables=cnf.nv,
                      clauses=len(cnf.clauses), weighted_cuts=len(registry),
                      prequery_reconstruction_seconds=time.monotonic()-total_started)
        query_started = time.monotonic()
        with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
            gc.collect()
            report['bootstrap_seconds'] = time.monotonic()-query_started
            remaining = seconds-report['bootstrap_seconds']
            if remaining <= 0:
                answer = None
            else:
                timer = Timer(remaining, solver.interrupt)
                timer.start()
                try:
                    answer = solver.solve_limited(expect_interrupt=True)
                finally:
                    timer.cancel()
            report['solver_return_seconds'] = time.monotonic()-query_started
            report['cooperative_query_overrun_seconds'] = max(0, report['solver_return_seconds']-seconds)
            report['solver_statistics'] = solver.accum_stats()
            if answer is None:
                report['status'] = 'UNKNOWN in fresh proof query; no certified exclusion'
            elif answer:
                report['status'] = 'ERROR: fresh final formula SAT after incremental UNSAT; no exclusion'
                report['primary_positive_variables'] = [v for v in solver.get_model() if 0 < v <= 480]
            else:
                proof = solver.get_proof()
                assert proof is not None
                report['terminal_empty_clause_appended'] = not proof or proof[-1] != '0'
                if report['terminal_empty_clause_appended']:
                    proof.append('0')
                raw = directory/'raw.drat'
                raw.write_text('\n'.join(proof)+'\n')
                report.update(status='fresh solver UNSAT; direct proof check pending',
                              raw_proof=portable(raw), raw_proof_sha256=digest(raw), raw_proof_lines=len(proof))
        save(output, report)
        if report['status'].startswith('fresh solver UNSAT;'):
            retained, trimmed, log = directory/'retained.cnf', directory/'retained.drat', directory/'direct-drat.log'
            outcome = checker_call(checker, formula_path, ROOT/report['raw_proof'],
                                   checker_seconds, log, retained, trimmed)
            report['direct_checker'] = outcome
            report['direct_checker_log'] = portable(log)
            report['direct_checker_log_sha256'] = digest(log)
            if outcome['verified']:
                count = inputs_subset(cnf, retained)
                report.update(status='fresh UNSAT and direct DRAT PASS; independent cold proof replay required',
                    retained_cnf=portable(retained), retained_cnf_sha256=digest(retained),
                    retained_proof=portable(trimmed), retained_proof_sha256=digest(trimmed),
                    retained_input_clauses=count)
            else:
                report['status'] = 'fresh solver UNSAT without verified proof; no certified exclusion'
    except Exception as error:
        report.update(status='ERROR during proof construction or check; no exclusion',
                      error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic()-total_started
        report['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(output, report)
    print(json.dumps(report, indent=2), flush=True)


def replay(preparation, result_path, certificate_path, output, checker, seconds):
    assert not output.exists() and 0 < seconds <= 60
    certificate = loop.load_json(certificate_path)
    assert certificate['status'].startswith('fresh UNSAT and direct DRAT PASS;')
    assert certificate['source_sha256'] == digest(Path(__file__))
    assert certificate['loop_source_sha256'] == digest(Path(loop.__file__))
    assert certificate['preparation_sha256'] == digest(preparation)
    assert certificate['loop_result_sha256'] == digest(result_path)
    assert certificate['checker_sha256'] == digest(checker)
    cnf, registry, _, formula_report = loop.reconstruct(preparation, result_path)
    retained, proof = ROOT/certificate['retained_cnf'], ROOT/certificate['retained_proof']
    assert digest(retained) == certificate['retained_cnf_sha256']
    assert digest(proof) == certificate['retained_proof_sha256']
    with tempfile.TemporaryDirectory(prefix='conway-f0-row-loop-proof-') as directory:
        file = Path(directory)/'full.cnf'
        cnf.to_file(file)
        assert digest(file) == certificate['final_cnf_sha256']
    count = inputs_subset(cnf, retained)
    assert count == certificate['retained_input_clauses']
    log = output.with_name(output.stem+'-drat.log')
    outcome = checker_call(checker, retained, proof, seconds, log)
    report = {'status': 'cold full formula and retained input replay; proof unverified',
        'source_sha256': digest(Path(__file__)), 'certificate_sha256': digest(certificate_path),
        'formula_replay': formula_report, 'final_cnf_sha256': certificate['final_cnf_sha256'],
        'retained_input_clauses': count, 'proof_checker': outcome,
        'proof_checker_log_sha256': digest(log), 'full_weighted_cut_count': len(registry),
        'conditional_component0_excluded': False, 'all_components_excluded': False,
        'full_graph_completion': False}
    if outcome['verified']:
        report['status'] = 'cold full free480 formula, exact cuts and clause bounds, retained inclusion and DRAT replay PASS'
        report['conditional_component0_excluded'] = True
        report['scope'] = 'Only component0 in the globallyP=F=0 split18+18 case; every first incidence remains free'
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)
    if not outcome['verified']:
        raise RuntimeError('cold DRAT did not verify; no certified exclusion')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    execute = commands.add_parser('prove')
    execute.add_argument('--preparation', type=Path, required=True)
    execute.add_argument('--result', type=Path, required=True)
    execute.add_argument('--directory', type=Path, required=True)
    execute.add_argument('--seconds', type=float, default=60)
    execute.add_argument('--checker', type=Path, required=True)
    execute.add_argument('--checker-seconds', type=int, default=60)
    check = commands.add_parser('replay')
    check.add_argument('--preparation', type=Path, required=True)
    check.add_argument('--result', type=Path, required=True)
    check.add_argument('--certificate', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    check.add_argument('--checker', type=Path, required=True)
    check.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    if args.command == 'prove':
        prove(args.preparation.resolve(), args.result.resolve(), args.directory.resolve(),
              args.seconds, args.checker.resolve(), args.checker_seconds)
    else:
        replay(args.preparation.resolve(), args.result.resolve(), args.certificate.resolve(),
               args.output.resolve(), args.checker.resolve(), args.seconds)
