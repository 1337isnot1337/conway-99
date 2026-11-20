"""Add twelve exact exterior-row inequalities to the free480-column model.

The base incidence formula is unchanged. The only suffix is444 guarded
primary clauses. Neither the old60-column witness nor a second component
incidence is fixed. One bounded fresh query is exposed separately from
preparation and cold replay.
"""

import argparse
import gc
import gzip
import json
from pathlib import Path
import resource
import subprocess
import tempfile
from threading import Timer
import time

from pysat.formula import CNF
from pysat.solvers import Solver

import root_prism_free_f0_incidence as base
import root_prism_free_f0_first_design_exterior_row_audit as audit


ROOT = base.ROOT
LOGS = ROOT/'experiments/logs/root-prism-free'
BASE_MODEL = LOGS/'f0-incidence-case00-model.json'
BASE_MODEL_SHA = '16deda266149f5123a1db3833cfebf22d6bdfe4426b1424fcc51ccbfdc38f0a1'
CUT_CERTIFICATE = LOGS/'f0-first-design-exterior-row-certificate.json.gz'
CUT_CERTIFICATE_SHA = '3b5c302f9a9e3bfce6175de7c73cb835cc89f88e63148de15d59085b1da974c0'
OLD_RESULT = LOGS/'f0-incidence-case00-run01/result.json'
OLD_RESULT_SHA = '64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf'
digest,canonical,portable = base.digest,base.canonical,base.portable


def save(path,record):
    path.write_text(json.dumps(record,indent=2)+'\n')


def load_cuts():
    assert digest(CUT_CERTIFICATE) == CUT_CERTIFICATE_SHA
    certificate = json.loads(gzip.decompress(CUT_CERTIFICATE.read_bytes()))
    assert certificate['source_sha256'] == digest(Path(audit.__file__))
    rebuilt = audit.calculate()
    rebuilt['elapsed_seconds_for_information_only'] = certificate['elapsed_seconds_for_information_only']
    assert rebuilt == certificate
    row = certificate['row_certificate']
    clauses = row['all_guarded_clauses']
    assert len(clauses) == 444 and all(len(c) == 56 for c in clauses)
    assert all(1 <= abs(v) <= 480 for c in clauses for v in c)
    assert len({tuple(sorted(c)) for c in clauses}) == 444
    return row['transported_cuts'],clauses,certificate


def check_cuts(selected,cuts,clauses):
    chosen = set(selected)
    outcomes = []
    for cut in cuts:
        target = cut['target_signature']
        left = sum(weight for b,weight in cut['binary_capped_weights'] if b in chosen)
        right = 2*int(target in chosen)
        outcomes.append({'target_signature':target,'left':left,'right':right,'holds':left >= right})
    truth = {i+1 for i in chosen}
    clause_truth = [any(v in truth if v > 0 else -v not in truth for v in clause) for clause in clauses]
    assert all(item['holds'] for item in outcomes) == all(clause_truth)
    return outcomes,clause_truth


def rebuild(complete_replay=False):
    assert digest(BASE_MODEL) == BASE_MODEL_SHA
    old = base.checked_model(BASE_MODEL)
    assert old['case'] == 0 and old['formula']['primary_variables'] == 480
    domain,records,cnf,metadata = base.rebuild(0,complete_replay)
    assert metadata == old['formula']
    assert base.components.sha(canonical(domain)) == old['domain_record_sha256']
    assert base.components.sha(canonical(records)) == old['pair_record_sha256']
    with tempfile.TemporaryDirectory(prefix='conway-f0-rowcut-base-') as directory:
        path = Path(directory)/'base.cnf'
        cnf.to_file(path)
        assert digest(path) == old['cnf_sha256']
    cuts,clauses,certificate = load_cuts()
    assert len(cnf.clauses) == 56550 and cnf.nv == 28308
    prefix = len(cnf.clauses)
    cnf.extend(clauses)
    assert cnf.clauses[prefix:] == clauses and cnf.nv == 28308
    assert len(cnf.clauses) == 56994
    assert digest(OLD_RESULT) == OLD_RESULT_SHA
    original = json.loads(OLD_RESULT.read_text())
    selected = original['incidence_witness']['selected_columns']
    assert base.inspect(selected,domain,records) == original['incidence_witness']
    outcomes,truth = check_cuts(selected,cuts,clauses)
    assert not all(truth)
    return old,domain,records,cnf,cuts,clauses,certificate,{
        'primary_variables':480,'variables':cnf.nv,'clauses':len(cnf.clauses),
        'literal_occurrences':sum(map(len,cnf.clauses)),
        'base_clauses':prefix,'added_guarded_clauses':len(clauses),
        'added_literal_occurrences':sum(map(len,clauses)),
        'new_auxiliary_variables':0,'cut_count':12,
        'old_witness_cut_outcomes':outcomes,
        'old_witness_failed_guarded_clause_count':sum(not value for value in truth),
        'old_witness_rejected':True,'old_witness_or_its_complement_fixed':False,
        'all480_original_selectors_free':True,'exterior_edge_variables':0}


def prepare(model_path,cnf_path):
    assert not model_path.exists() and not cnf_path.exists()
    started = time.monotonic()
    old,domain,records,cnf,cuts,clauses,certificate,formula = rebuild()
    cnf.to_file(cnf_path)
    model = {'status':'free480-column base plus twelve necessary exterior-row cuts prepared; no query',
        'source_sha256':digest(Path(__file__)),'base_model':portable(BASE_MODEL),
        'base_model_sha256':BASE_MODEL_SHA,'base_source_hashes':old['source_hashes'],
        'base_cnf_sha256':old['cnf_sha256'],
        'cut_source_sha256':digest(Path(audit.__file__)),
        'cut_certificate':portable(CUT_CERTIFICATE),'cut_certificate_sha256':CUT_CERTIFICATE_SHA,
        'old_incidence_result_sha256':OLD_RESULT_SHA,
        'formula':formula,'cnf':str(cnf_path),'cnf_sha256':digest(cnf_path),
        'cnf_bytes':cnf_path.stat().st_size,
        'clause_suffix_sha256':base.components.sha(canonical(clauses)),
        'controls':certificate['row_certificate']['controls'],
        'scope':old['scope'],'fixed_incidence_design':False,'graph_symmetry_constraints':False,
        'SAT_scope':'necessary one-component incidence only; exterior edges and second component unspecified',
        'UNSAT_scope':'component0 in the conditional globallyP=F=0 split18+18 case only',
        'solver_called':False,'seconds':time.monotonic()-started}
    save(model_path,model)
    print(json.dumps(model,indent=2),flush=True)


def checked_model(path,require_cnf=False):
    model = json.loads(path.read_text())
    assert model['source_sha256'] == digest(Path(__file__))
    assert digest(BASE_MODEL) == model['base_model_sha256'] == BASE_MODEL_SHA
    for name,value in model['base_source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == value
    assert model['cut_source_sha256'] == digest(Path(audit.__file__))
    assert digest(CUT_CERTIFICATE) == model['cut_certificate_sha256'] == CUT_CERTIFICATE_SHA
    assert model['fixed_incidence_design'] is False and model['graph_symmetry_constraints'] is False
    if require_cnf:
        assert digest(Path(model['cnf'])) == model['cnf_sha256']
    return model


def inspect(selected,domain,records,cuts,clauses):
    original = base.inspect(selected,domain,records)
    outcomes,truth = check_cuts(selected,cuts,clauses)
    assert all(truth) and all(row['holds'] for row in outcomes)
    return {'base_incidence_witness':original,'all12_exterior_row_cut_outcomes':outcomes,
            'all444_guarded_clauses_checked':True,'actual_exterior_rows_found':False,
            'full_graph_completion':False}


def solve(model_path,directory,seconds,checker,checker_seconds):
    assert not directory.exists() and 0 < seconds <= 60 and 0 < checker_seconds <= 60
    directory.mkdir(parents=True)
    model = checked_model(model_path,True)
    result = {'status':'running one fresh free480-column incidence query with twelve row cuts',
        'model':portable(model_path),'model_sha256':digest(model_path),
        'source_sha256':digest(Path(__file__)),'cnf_sha256':model['cnf_sha256'],
        'seconds_including_bootstrap':seconds,'checker_seconds':checker_seconds,
        'assumptions':[],'fixed_incidence_design':False,'all66_components_excluded':False,
        'full_graph_completion':False}
    output = directory/'result.json'
    save(output,result)
    started = time.monotonic()
    try:
        cnf = CNF(from_file=model['cnf'])
        assert (cnf.nv,len(cnf.clauses)) == (model['formula']['variables'],model['formula']['clauses'])
        with Solver(name='glucose4',bootstrap_with=cnf.clauses,with_proof=True) as solver:
            del cnf
            gc.collect()
            result['bootstrap_seconds'] = time.monotonic()-started
            timer = Timer(max(0.001,seconds-result['bootstrap_seconds']),solver.interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
            result['solver_return_seconds'] = time.monotonic()-started
            result['cooperative_budget_overrun_seconds'] = max(0,result['solver_return_seconds']-seconds)
            result['solver_statistics'] = solver.accum_stats()
            if answer is None:
                result['status'] = 'UNKNOWN; no incidence or component exclusion'
            elif answer:
                positive = {v for v in solver.get_model() if v > 0}
                selected = [i for i in range(480) if i+1 in positive]
                cuts,clauses,_ = load_cuts()
                domain,records = base.load(0)
                result['incidence_candidate'] = inspect(selected,domain,records,cuts,clauses)
                result['status'] = 'SAT; exact necessary incidence and twelve row cuts checked, no graph completion'
            else:
                proof = solver.get_proof()
                assert proof is not None
                result['terminal_empty_clause_appended'] = not proof or proof[-1] != '0'
                if result['terminal_empty_clause_appended']:
                    proof.append('0')
                raw = directory/'raw.drat'
                raw.write_text('\n'.join(proof)+'\n')
                result.update(status='solver UNSAT; proof check pending',raw_proof=portable(raw),
                              raw_proof_sha256=digest(raw),raw_proof_lines=len(proof))
        save(output,result)
        if result['status'].startswith('solver UNSAT'):
            retained,proof = directory/'retained.cnf',directory/'retained.drat'
            log = directory/'direct-drat.log'
            try:
                checked = subprocess.run([str(checker),model['cnf'],str(ROOT/result['raw_proof']),
                    '-t',str(checker_seconds),'-w','-c',str(retained),'-l',str(proof)],
                    capture_output=True,text=True,timeout=checker_seconds+5,check=False)
            except subprocess.TimeoutExpired as error:
                log.write_text(str(error)+'\n')
                result['status'] = 'solver UNSAT; proof checker timed out, no certified exclusion'
            else:
                log.write_text(checked.stdout+checked.stderr)
                if checked.returncode != 0 or 's VERIFIED' not in checked.stdout:
                    result['status'] = 'solver UNSAT; proof checker did not verify, no certified exclusion'
                else:
                    inputs = list(base.read_clauses(retained))
                    needed = {tuple(sorted(c)) for c in inputs}
                    for clause in base.read_clauses(Path(model['cnf'])):
                        needed.discard(tuple(sorted(clause)))
                    assert not needed
                    result['retained_certificate'] = {'cnf':portable(retained),'cnf_sha256':digest(retained),
                        'proof':portable(proof),'proof_sha256':digest(proof),'input_clauses':len(inputs),
                        'checker_log':portable(log),'checker_log_sha256':digest(log)}
                    result['status'] = 'UNSAT with direct DRAT; cold complete rebuild and proof replay required'
        result['elapsed_seconds'] = time.monotonic()-started
        result['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(output,result)
    except Exception as error:
        result.update(status='error; no unchecked exclusion promoted',error_type=type(error).__name__,
                      error_message=str(error),elapsed_seconds=time.monotonic()-started)
        save(output,result)
        raise
    print(json.dumps({k:v for k,v in result.items() if k != 'incidence_candidate'},indent=2),flush=True)


def replay(model_path,result_path,output,checker,checker_seconds):
    assert not output.exists() and 0 < checker_seconds <= 60
    model = checked_model(model_path)
    old,domain,records,cnf,cuts,clauses,certificate,formula = rebuild(True)
    assert formula == model['formula']
    assert base.components.sha(canonical(clauses)) == model['clause_suffix_sha256']
    with tempfile.TemporaryDirectory(prefix='conway-f0-rowcut-replay-') as directory:
        path = Path(directory)/'replay.cnf'
        cnf.to_file(path)
        assert digest(path) == model['cnf_sha256']
    report = {'status':'cold complete component domain, base CNF, twelve cuts and exact overlay replay PASS',
        'model_sha256':digest(model_path),'cnf_sha256':model['cnf_sha256'],
        'variables':cnf.nv,'clauses':len(cnf.clauses),'fixed_incidence_design':False,
        'all66_components_excluded':False,'full_graph_completion':False}
    if result_path:
        result = json.loads(result_path.read_text())
        assert result['source_sha256'] == digest(Path(__file__))
        assert result['model_sha256'] == digest(model_path) and result['cnf_sha256'] == model['cnf_sha256']
        if result['status'].startswith('SAT;'):
            selected = result['incidence_candidate']['base_incidence_witness']['selected_columns']
            assert inspect(selected,domain,records,cuts,clauses) == result['incidence_candidate']
            report['status'] = 'cold complete formula and exact necessary incidence candidate replay PASS'
        elif result['status'].startswith('UNSAT with direct DRAT;'):
            certificate = result['retained_certificate']
            retained,proof = ROOT/certificate['cnf'],ROOT/certificate['proof']
            assert digest(retained) == certificate['cnf_sha256'] and digest(proof) == certificate['proof_sha256']
            inputs = list(base.read_clauses(retained))
            assert len(inputs) == certificate['input_clauses']
            needed = {tuple(sorted(c)) for c in inputs}
            needed.difference_update(tuple(sorted(c)) for c in cnf.clauses)
            assert not needed
            log = output.with_suffix('.drat.log')
            try:
                checked = subprocess.run([str(checker),str(retained),str(proof),'-t',str(checker_seconds),'-w'],
                    capture_output=True,text=True,timeout=checker_seconds+5,check=False)
            except subprocess.TimeoutExpired as error:
                log.write_text(str(error)+'\n')
                report['status'] = 'cold formula and retained inclusion PASS; proof replay timed out, no promotion'
            else:
                log.write_text(checked.stdout+checked.stderr)
                assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
                report.update(status='cold complete domain/CNF/cut rebuild, retained inclusion and DRAT PASS',
                    excluded_component=0,retained_input_clauses=len(inputs),
                    checker_log=portable(log),checker_log_sha256=digest(log))
        else:
            assert result['status'].startswith(('UNKNOWN;','solver UNSAT;'))
            report['status'] = 'cold exact formula and unresolved-result binding PASS; no certified exclusion'
    save(output,report)
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--model',type=Path,required=True)
    prep.add_argument('--cnf',type=Path,required=True)
    run = commands.add_parser('solve')
    run.add_argument('--model',type=Path,required=True)
    run.add_argument('--directory',type=Path,required=True)
    run.add_argument('--seconds',type=float,default=60)
    run.add_argument('--checker',type=Path,default=Path('/tmp/conway99-drat-trim/drat-trim'))
    run.add_argument('--checker-seconds',type=int,default=60)
    check = commands.add_parser('replay')
    check.add_argument('--model',type=Path,required=True)
    check.add_argument('--result',type=Path)
    check.add_argument('--output',type=Path,required=True)
    check.add_argument('--checker',type=Path,default=Path('/tmp/conway99-drat-trim/drat-trim'))
    check.add_argument('--checker-seconds',type=int,default=60)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.model.resolve(),args.cnf.resolve())
    elif args.command == 'solve':
        solve(args.model.resolve(),args.directory.resolve(),args.seconds,args.checker.resolve(),args.checker_seconds)
    else:
        replay(args.model.resolve(),args.result.resolve() if args.result else None,
               args.output.resolve(),args.checker.resolve(),args.checker_seconds)
