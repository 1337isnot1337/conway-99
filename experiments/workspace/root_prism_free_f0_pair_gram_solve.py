"""One bounded proof-enabled query for the full unfixed component0 pair.

The180-second discovery budget includes streamed bootstrap. Both proof
stages have separate hard120-second limits. A proof-check timeout retains
an explicitly uncertified status. No continuation or second query occurs.
"""

import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import tempfile
from threading import Timer
import time

from pysat.solvers import Solver

import root_prism_free_f0_pair_gram_build as build


ROOT = build.ROOT
MODEL_SHA = 'a87cac772964ec5af7415f327f0a2f52713ac9ca87767c1ae7b3ac0db2fa0728'
CNF_SHA = '31a59090b935889b97515d20f5d03cdb02f5fc9b33a321ea30ded8b20c16b4b8'
digest, portable = build.digest, build.portable


def text_output(value):
    return value.decode(errors='replace') if isinstance(value,bytes) else value or ''


def read_clauses(path):
    with path.open() as stream:
        for line in stream:
            if not line.strip() or line[0] in 'cp':
                continue
            values = list(map(int,line.split()))
            assert values and values[-1] == 0 and all(values[:-1])
            yield values[:-1]


def checked_model(path):
    assert digest(path) == MODEL_SHA
    model = build.checked_model(path)
    assert model['cnf_sha256'] == CNF_SHA
    assert model['formula']['variables'] == 1478076
    assert model['formula']['clauses'] == 3173640
    return model


def bootstrap(solver, model, deadline):
    expected = model['formula']
    hasher = hashlib.sha256()
    count = 0
    with Path(model['cnf']).open('rb') as stream:
        header = stream.readline()
        assert header == f"p cnf {expected['variables']} {expected['clauses']}\n".encode()
        hasher.update(header)
        for line in stream:
            hasher.update(line)
            values = list(map(int,line.split()))
            assert values and values[-1] == 0 and all(values[:-1])
            solver.add_clause(values[:-1])
            count += 1
            if count % 1024 == 0 and time.monotonic() >= deadline:
                return {'complete':False,'clauses_loaded':count,'budget_expired_during_bootstrap':True}
    assert count == expected['clauses']
    assert hasher.hexdigest() == model['cnf_sha256']
    return {'complete':True,'clauses_loaded':count,'cnf_sha256':hasher.hexdigest(),
            'budget_expired_during_bootstrap':False}


def direct_check(model, raw, directory, checker, seconds):
    retained, proof, log = directory/'retained.cnf', directory/'retained.drat', directory/'direct-drat.log'
    command = [str(checker),model['cnf'],str(raw),'-t',str(seconds),'-w',
               '-c',str(retained),'-l',str(proof)]
    started = time.monotonic()
    try:
        checked = subprocess.run(command,capture_output=True,text=True,timeout=seconds,check=False)
    except subprocess.TimeoutExpired as error:
        log.write_text(text_output(error.stdout)+text_output(error.stderr)+'\nHARD WALL TIMEOUT\n')
        return {'status':'direct proof check timed out; no certified exclusion',
                'verified':False,'hard_seconds':seconds,'elapsed_seconds':time.monotonic()-started,
                'checker_log':portable(log),'checker_log_sha256':digest(log)}
    log.write_text(checked.stdout+checked.stderr)
    passed = checked.returncode == 0 and 's VERIFIED' in checked.stdout
    result = {'status':'direct DRAT passed' if passed else 'direct proof check failed or timed out; no certified exclusion',
              'verified':passed,'checker_returncode':checked.returncode,'hard_seconds':seconds,
              'elapsed_seconds':time.monotonic()-started,
              'checker_log':portable(log),'checker_log_sha256':digest(log)}
    if passed:
        count = sum(1 for _ in read_clauses(retained))
        result.update(cnf=portable(retained),cnf_sha256=digest(retained),
                      proof=portable(proof),proof_sha256=digest(proof),input_clauses=count)
    return result


def cold_worker(model_path, result_path, checker, seconds, output):
    """Called in a separate process with a parent-enforced hard deadline."""
    started = time.monotonic()
    assert not output.exists()
    model = checked_model(model_path)
    result = json.loads(result_path.read_text())
    assert result['source_sha256'] == digest(Path(__file__))
    assert result['model_sha256'] == MODEL_SHA and result['cnf_sha256'] == CNF_SHA
    direct = result['direct_certificate']
    assert direct['verified'] is True
    retained, proof = ROOT/direct['cnf'], ROOT/direct['proof']
    assert digest(retained) == direct['cnf_sha256'] and digest(proof) == direct['proof_sha256']
    data,specs,clauses,saved = build.load_specification()
    with tempfile.TemporaryDirectory(prefix='conway-f0-pair-gram-proof-') as directory:
        rebuilt = Path(directory)/'rebuilt.cnf'
        actual = build.stream_cnf(rebuilt,specs,clauses,saved['formula'])
        assert actual == model['formula'] and actual['cnf_sha256'] == CNF_SHA
        needed = set()
        retained_count = 0
        for clause in read_clauses(retained):
            needed.add(tuple(sorted(clause)))
            retained_count += 1
        assert retained_count == direct['input_clauses']
        for clause in read_clauses(rebuilt):
            needed.discard(tuple(sorted(clause)))
            if not needed:
                break
        assert not needed
    remaining = seconds-(time.monotonic()-started)
    assert remaining > 0
    log = output.with_suffix('.drat.log')
    try:
        checked = subprocess.run([str(checker),str(retained),str(proof),'-t',str(max(1,int(remaining))),'-w'],
                                 capture_output=True,text=True,timeout=remaining,check=False)
    except subprocess.TimeoutExpired as error:
        log.write_text(text_output(error.stdout)+text_output(error.stderr)+'\nCOLD CHECK TIMEOUT\n')
        raise
    log.write_text(checked.stdout+checked.stderr)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
    report = {'status':'cold complete domain/CNF rebuild, retained inclusion and DRAT passed',
              'source_sha256':digest(Path(__file__)),'model_sha256':MODEL_SHA,'cnf_sha256':CNF_SHA,
              'retained_input_clauses':retained_count,'retained_inputs_checked_against_rebuilt_formula':True,
              'checker_log':portable(log),'checker_log_sha256':digest(log),
              'elapsed_seconds':time.monotonic()-started,
              'excluded_scope':'complete component0 pair with identity fiber alignment under the conditional P=F=0 split-shell reduction',
              'other_components_or_alignments_excluded':False,'full_graph_completion':False}
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


def cold_check(model_path, result_path, directory, checker, seconds):
    output, log = directory/'cold-replay.json', directory/'cold-replay.log'
    assert not output.exists() and not log.exists()
    command = [sys.executable,str(Path(__file__).resolve()),'cold-worker',
               '--model',str(model_path),'--result',str(result_path),
               '--drat-trim',str(checker),'--seconds',str(seconds),'--output',str(output)]
    started = time.monotonic()
    process = subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,
                               text=True,start_new_session=True)
    try:
        stdout, stderr = process.communicate(timeout=seconds)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid,signal.SIGKILL)
        stdout, stderr = process.communicate()
        log.write_text(stdout+stderr+'\nHARD COLD REPLAY TIMEOUT\n')
        return {'status':'cold proof replay timed out; no complete exclusion promoted','verified':False,
                'hard_seconds':seconds,'elapsed_seconds':time.monotonic()-started,
                'log':portable(log),'log_sha256':digest(log)}
    log.write_text(stdout+stderr)
    verified = False
    if process.returncode == 0 and output.exists():
        report = json.loads(output.read_text())
        verified = (report['status'] == 'cold complete domain/CNF rebuild, retained inclusion and DRAT passed'
                    and report['cnf_sha256'] == CNF_SHA and report['model_sha256'] == MODEL_SHA
                    and report['source_sha256'] == digest(Path(__file__)))
    value = {'status':'cold proof replay passed' if verified else 'cold proof replay failed; no complete exclusion promoted',
             'verified':verified,'returncode':process.returncode,'hard_seconds':seconds,
             'elapsed_seconds':time.monotonic()-started,'log':portable(log),'log_sha256':digest(log)}
    if output.exists():
        value.update(report=portable(output),report_sha256=digest(output))
    return value


def solve(model_path, directory, seconds, checker, proof_seconds):
    assert not directory.exists() and 0 < seconds <= 180 and 0 < proof_seconds <= 120
    directory.mkdir(parents=True)
    started = time.monotonic()
    deadline = started+seconds
    model = checked_model(model_path)
    assert digest(Path(model['cnf'])) == CNF_SHA
    output = directory/'result.json'
    result = {'status':'running one complete unfixed component0-pair query',
              'source_sha256':digest(Path(__file__)),'build_source_sha256':digest(Path(build.__file__)),
              'model':portable(model_path),'model_sha256':MODEL_SHA,'cnf_sha256':CNF_SHA,
              'query_seconds_including_bootstrap':seconds,'proof_stage_hard_seconds_each':proof_seconds,
              'solver':'glucose4','proof_enabled':True,'assumptions':[],
              'fixed_incidence_designs':False,'graph_symmetry_constraints':False,
              'full_graph_completion':False,'complete_component_pair_excluded':False}
    def save():
        result['elapsed_seconds']=time.monotonic()-started
        result['peak_process_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        output.write_text(json.dumps(result,indent=2)+'\n')
    save()
    interrupted = []
    try:
        with Solver(name='glucose4',with_proof=True) as solver:
            def interrupt():
                interrupted.append(time.monotonic()-started)
                solver.interrupt()
            timer = Timer(max(0.001,deadline-time.monotonic()),interrupt)
            timer.start()
            try:
                result['bootstrap'] = bootstrap(solver,model,deadline)
                result['bootstrap_seconds'] = time.monotonic()-started
                save()
                if result['bootstrap']['complete'] and time.monotonic() < deadline:
                    answer = solver.solve_limited(expect_interrupt=True)
                else:
                    answer = None
            finally:
                timer.cancel()
            result['solver_return_seconds'] = time.monotonic()-started
            result['cooperative_overrun_seconds'] = max(0.0,result['solver_return_seconds']-seconds)
            result['interrupt_callback_elapsed_seconds'] = interrupted
            result['solver_statistics'] = solver.accum_stats()
            if answer is None:
                result['status'] = 'UNKNOWN; complete component0 pair remains unresolved'
            elif answer:
                initial = model['formula']['initial_primary_and_derived_variables']
                true_primary = sorted(v for v in solver.get_model() if 1 <= v <= initial)
                data,specs,direct,saved = build.load_specification()
                point = build.inspect(true_primary,data,specs,direct,saved)
                result['incidence_candidate'] = point
                result['status'] = 'SAT; full primary incidence checked, exterior adjacency unspecified'
                result['additional_visible_PF_defects'] = {
                    'prisms':point['visible_motifs']['visible_prism_count'],
                    'F':point['visible_motifs']['visible_F_count']}
            else:
                proof = solver.get_proof()
                assert proof is not None
                result['terminal_empty_clause_appended'] = not proof or proof[-1] != '0'
                if result['terminal_empty_clause_appended']:
                    proof.append('0')
                raw = directory/'raw.drat'
                with raw.open('w') as stream:
                    for line in proof:
                        stream.write(line+'\n')
                result.update(status='solver UNSAT; proof stages pending, no exclusion yet',
                              raw_proof=portable(raw),raw_proof_sha256=digest(raw),raw_proof_lines=len(proof))
                del proof
        gc.collect()
        save()
        if result['status'].startswith('solver UNSAT;'):
            print('Solver UNSAT; direct DRAT phase starting.',flush=True)
            result['direct_certificate'] = direct_check(model,ROOT/result['raw_proof'],directory,checker,proof_seconds)
            if not result['direct_certificate']['verified']:
                result['status'] = 'solver UNSAT; direct proof unverified, no exclusion'
                save()
            else:
                result['status'] = 'UNSAT with direct DRAT; cold replay pending'
                save()
                print('Direct DRAT passed; cold full-formula proof replay starting.',flush=True)
                result['cold_certificate'] = cold_check(model_path,output,directory,checker,proof_seconds)
                if result['cold_certificate']['verified']:
                    result['status'] = 'UNSAT with direct DRAT and cold complete-formula proof replay'
                    result['complete_component_pair_excluded'] = True
                    result['excluded_scope'] = 'component0 paired with component0, identity fiber alignment, under the conditional globally P=F=0 split-shell reduction'
                else:
                    result['status'] = 'UNSAT with direct DRAT; cold proof replay unverified, no complete exclusion promoted'
                save()
        save()
    except Exception as error:
        result.update(status='error; no unchecked result promoted',error_type=type(error).__name__,
                      error_message=str(error),complete_component_pair_excluded=False)
        save()
        raise
    print(json.dumps({key:value for key,value in result.items() if key != 'incidence_candidate'},indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    run = commands.add_parser('solve')
    run.add_argument('--model',type=Path,required=True)
    run.add_argument('--directory',type=Path,required=True)
    run.add_argument('--seconds',type=float,default=180)
    run.add_argument('--drat-trim',type=Path,required=True)
    run.add_argument('--proof-seconds',type=int,default=120)
    cold = commands.add_parser('cold-worker')
    cold.add_argument('--model',type=Path,required=True)
    cold.add_argument('--result',type=Path,required=True)
    cold.add_argument('--drat-trim',type=Path,required=True)
    cold.add_argument('--seconds',type=float,required=True)
    cold.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.command == 'solve':
        solve(args.model.resolve(),args.directory.resolve(),args.seconds,args.drat_trim.resolve(),args.proof_seconds)
    else:
        assert 0 < args.seconds <= 120
        cold_worker(args.model.resolve(),args.result.resolve(),args.drat_trim.resolve(),args.seconds,args.output.resolve())
