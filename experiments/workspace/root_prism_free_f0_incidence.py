"""Exact binary Gram model for one eighteen-component on the P=F=0 face.

All distinct admissible triples are free selectors. The only constraints
are all171 Gram positions and the explicitly certified two-column
prism/F conflicts. No exterior edges or graph symmetries are imposed.
"""
import argparse
from collections import Counter
import gc
import gzip
from itertools import combinations
import json
from pathlib import Path
import resource
import subprocess
import tempfile
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

import root_prism_free_f0_components as components
import root_prism_free_f0_pair_clauses as motifs


ROOT = Path(__file__).resolve().parents[2]
PAIR_CERTIFICATE = ROOT/'experiments/logs/root-prism-free/f0-pair-clauses.json.gz'
PAIR_SHA = '47e9d8f518fab10aee604f33df1f22c97b0d201a1af4180e4307553e4857672f'
SOURCES = ('root_prism_free_f0_incidence.py','root_prism_free_f0_components.py',
           'root_prism_free_f0_pair_clauses.py')
digest,canonical = motifs.digest,components.canonical


def portable(path):
    return str(path.resolve().relative_to(ROOT))


def load(case, complete_replay=False):
    assert 0 <= case < 66
    if complete_replay:
        components.replay(motifs.DOMAIN)
    catalogue = motifs.load()
    assert digest(PAIR_CERTIFICATE) == PAIR_SHA
    certificate = json.loads(gzip.decompress(PAIR_CERTIFICATE.read_bytes()))
    assert certificate == motifs.result()
    domain = catalogue['representatives'][case]['domain']
    assert components.component_domain(domain['core_rows']) == domain
    record = certificate['representatives'][case]
    assert record['representative'] == case
    return domain,record


def assemble(gram, signatures, conflicts):
    size = len(gram)
    pool,cnf = IDPool(start_from=len(signatures)+1),CNF()
    coverage,distinct = [],{}
    for i in range(size):
        for j in range(i,size):
            members = [s+1 for s,h in enumerate(signatures) if i in h and j in h]
            quota = gram[i][j]
            assert quota >= 0
            key = tuple(members),quota
            if key not in distinct:
                distinct[key] = len(distinct)
                if quota > len(members):
                    cnf.append([])
                elif members:
                    cnf.extend(CardEnc.equals(members,quota,vpool=pool,
                                              encoding=EncType.seqcounter).clauses)
                else:
                    assert quota == 0
            coverage.append([i,j,quota,len(members),distinct[key]])
    gram_clauses = len(cnf.clauses)
    assert conflicts == sorted(set(tuple(pair) for pair in conflicts))
    for a,b in conflicts:
        assert 0 <= a < b < len(signatures)
        cnf.append([-a-1,-b-1])
    metadata = {'primary_variables':len(signatures),'variables':cnf.nv,
                'clauses':len(cnf.clauses),'Gram_cardinality_clauses':gram_clauses,
                'distinct_Gram_equations_including_empty_zero':len(distinct),
                'Gram_position_coverage':coverage,'motif_conflict_clauses':len(conflicts),
                'auxiliary_variables_begin_at':len(signatures)+1}
    return cnf,metadata


def rebuild(case, complete_replay=False):
    domain,records = load(case,complete_replay)
    f_pairs = {tuple(r['columns']) for r in records['F_conflicts']}
    p_pairs = {tuple(r['columns']) for r in records['prism_conflicts']}
    conflicts = sorted(f_pairs | p_pairs)
    cnf,metadata = assemble(domain['Gram'],domain['signature_domain'],conflicts)
    metadata.update(F_conflicts=len(f_pairs),prism_conflicts=len(p_pairs),
                    conflicts_in_both_families=len(f_pairs&p_pairs),
                    F_conflict_family_counts=records['F_family_counts'],
                    primary_domain_sha256=domain['signature_domain_sha256'],
                    all66_domain_coverage_available=True,
                    additional_orbit_or_incidence_equalities=0,
                    exterior_edge_variables=0)
    return domain,records,cnf,metadata


def controls():
    truth_assignments = 0
    for n in range(7):
        for k in range(n+1):
            gram = [[k]]
            signatures = [[0] for _ in range(n)]
            cnf,_ = assemble(gram,signatures,[])
            with Solver(name='glucose3',bootstrap_with=cnf.clauses) as solver:
                for mask in range(1 << n):
                    assumptions = [i+1 if mask >> i & 1 else -i-1 for i in range(n)]
                    assert solver.solve(assumptions=assumptions) == (mask.bit_count()==k)
                    truth_assignments += 1
    with Solver(name='glucose3',bootstrap_with=[[-1,-2]]) as solver:
        for a in (0,1):
            for b in (0,1):
                assert solver.solve(assumptions=[1 if a else -1,2 if b else -2]) == (not(a and b))
                truth_assignments += 1
    selected_core,outside = [0,1,3,4,8],[2,5,6,7]
    rook = lambda a,b: a!=b and (a//3==b//3 or a%3==b%3)
    rows = [sum(1 << j for j,v in enumerate(selected_core) if rook(u,v)) for u in selected_core]
    gram = [[2*(i==j)+2-(rows[i]&rows[j]).bit_count()-(rows[i]>>j&1)
             for j in range(5)] for i in range(5)]
    signatures = [[i for i in range(5) if mask>>i&1] for mask in range(1,32)
                  if all(not(mask>>i&1 and mask>>j&1) or gram[i][j]>0
                         for i in range(5) for j in range(5))
                  and all(((rows[i]|(1<<i))&mask).bit_count()<=2 for i in range(5))]
    actual = [[i for i,v in enumerate(selected_core) if rook(u,v)] for u in outside]
    assert len({tuple(h) for h in actual}) == 4 and all(h in signatures for h in actual)
    chosen = {signatures.index(h) for h in actual}
    cnf,_ = assemble(gram,signatures,[])
    assumptions = [i+1 if i in chosen else -i-1 for i in range(len(signatures))]
    with Solver(name='glucose3',bootstrap_with=cnf.clauses) as solver:
        assert solver.solve(assumptions=assumptions)
        assumptions[min(chosen)] *= -1
        assert not solver.solve(assumptions=assumptions)
    return {'elementary_truth_assignments':truth_assignments,
            'rook9_known_incidence_positive_control':True,
            'rook9_deleted_column_negative_control':True,
            'main_component_model_solved':False}


def prepare(case, model_path, cnf_path):
    assert not model_path.exists() and not cnf_path.exists()
    started = time.monotonic()
    control = controls()
    domain,records,cnf,metadata = rebuild(case,True)
    cnf.to_file(cnf_path)
    model = {'status':'one necessary component incidence model prepared; main model not solved',
             'source_hashes':{name:digest(Path(__file__).with_name(name)) for name in SOURCES},
             'domain_certificate':portable(motifs.DOMAIN),'domain_certificate_sha256':motifs.DOMAIN_SHA,
             'pair_certificate':portable(PAIR_CERTIFICATE),'pair_certificate_sha256':PAIR_SHA,
             'case':case,'complete_component_cover_size':66,
             'scope':'globally prism-free SRG(99,14,1,2), x521=0, split18+18 triangle shell, one indexed component',
             'domain_record_sha256':components.sha(canonical(domain)),
             'pair_record_sha256':components.sha(canonical(records)),
             'formula':metadata,'cnf':str(cnf_path.resolve()),'cnf_sha256':digest(cnf_path),
             'controls':control,'complete_cover_and_motif_replay_passed':True,
             'population60_and_profile24_36_are_derived':True,
             'graph_automorphism_assumptions':0,'fixed_incidence_witness':False,
             'SAT_scope':'exact necessary one-component incidence witness, no graph completion',
             'UNSAT_scope':'this component representative and its verified relabelings only',
             'elapsed_seconds':time.monotonic()-started}
    model_path.write_text(json.dumps(model,indent=2)+'\n')
    print(json.dumps({k:v for k,v in model.items() if k!='formula'},indent=2),flush=True)
    print(json.dumps({k:v for k,v in metadata.items() if k!='Gram_position_coverage'},indent=2),flush=True)


def checked_model(path, require_cnf=False):
    model=json.loads(path.read_text())
    for name,expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name))==expected
    assert model['domain_certificate_sha256']==motifs.DOMAIN_SHA
    assert model['pair_certificate_sha256']==PAIR_SHA
    if require_cnf:
        assert digest(Path(model['cnf']))==model['cnf_sha256']
    return model


def inspect(selected,domain,records):
    assert selected==sorted(set(selected)) and len(selected)==60
    signatures=domain['signature_domain']
    assert all(0<=i<len(signatures) for i in selected)
    columns=[signatures[i] for i in selected]
    assert len({tuple(h) for h in columns})==60
    gram=domain['Gram']
    assert all(sum(i in h and j in h for h in columns)==gram[i][j]
               for i in range(18) for j in range(i,18))
    profiles=Counter(tuple(sum(v//6==f for v in h) for f in range(3)) for h in columns)
    assert profiles[(1,1,1)]==24 and sum(v for p,v in profiles.items() if p!=(1,1,1))==36
    for f in range(3):
        assert [sum(v for p,v in profiles.items() if p[f]==k) for k in range(3)]==[12,36,12]
    chosen=set(selected)
    for kind in ('F_conflicts','prism_conflicts'):
        assert all(not set(record['columns'])<=chosen for record in records[kind])
    return {'selected_columns':selected,'selected_triples':columns,
            'unique_triples':60,'Gram_positions_checked':171,
            'profile_counts':[[list(p),n] for p,n in sorted(profiles.items())],
            'F_conflicts_checked':len(records['F_conflicts']),
            'prism_conflicts_checked':len(records['prism_conflicts']),
            'second_component_and_exterior_edges_unspecified':True,
            'full_graph_completion':False}


def read_clauses(path):
    with path.open() as stream:
        for line in stream:
            if not line or line[0] in 'cp':
                continue
            values=list(map(int,line.split()))
            assert values and values[-1]==0
            yield values[:-1]


def solve(model_path,directory,seconds,checker,checker_seconds):
    assert not directory.exists() and 0<seconds<=60 and 0<checker_seconds<=60
    directory.mkdir(parents=True)
    model=checked_model(model_path,True)
    result={'status':'running one component incidence query','model':portable(model_path),
            'model_sha256':digest(model_path),'source_sha256':digest(Path(__file__)),
            'case':model['case'],'cnf_sha256':model['cnf_sha256'],
            'seconds_including_bootstrap':seconds,'direct_checker_seconds':checker_seconds,
            'assumptions':[],'all66_components_excluded':False,'full_graph_completion':False}
    output=directory/'result.json'
    def save():
        result['peak_process_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        output.write_text(json.dumps(result,indent=2)+'\n')
    started=time.monotonic()
    save()
    try:
        cnf=CNF(from_file=model['cnf'])
        assert (cnf.nv,len(cnf.clauses))==(model['formula']['variables'],model['formula']['clauses'])
        with Solver(name='glucose4',bootstrap_with=cnf.clauses,with_proof=True) as solver:
            del cnf
            gc.collect()
            result['bootstrap_seconds']=time.monotonic()-started
            timer=Timer(max(0.001,seconds-result['bootstrap_seconds']),solver.interrupt)
            timer.start()
            try:
                answer=solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
            result['solver_return_seconds']=time.monotonic()-started
            result['solver_statistics']=solver.accum_stats()
            if answer is None:
                result['status']='UNKNOWN; component incidence unresolved'
            elif answer:
                positive={v for v in solver.get_model() if v>0}
                selected=[i for i in range(model['formula']['primary_variables']) if i+1 in positive]
                result['incidence_witness']=inspect(selected,*load(model['case']))
                result['status']='SAT; exact necessary one-component incidence witness checked'
            else:
                proof=solver.get_proof()
                assert proof is not None
                result['terminal_empty_clause_appended']=not proof or proof[-1]!='0'
                if result['terminal_empty_clause_appended']:
                    proof.append('0')
                raw=directory/'raw.drat'
                raw.write_text('\n'.join(proof)+'\n')
                result.update(status='solver UNSAT; direct DRAT pending',
                              raw_proof=portable(raw),raw_proof_sha256=digest(raw),
                              raw_proof_lines=len(proof))
        save()
        if result['status'].startswith('solver UNSAT'):
            retained,trimmed,log=directory/'retained.cnf',directory/'retained.drat',directory/'direct-drat.log'
            checked=subprocess.run([str(checker),model['cnf'],str(ROOT/result['raw_proof']),
                                    '-t',str(checker_seconds),'-w','-c',str(retained),'-l',str(trimmed)],
                                   capture_output=True,text=True,timeout=checker_seconds+5,check=False)
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode==0 and 's VERIFIED' in checked.stdout
            inputs=list(read_clauses(retained))
            needed={tuple(sorted(c)) for c in inputs}
            for clause in read_clauses(Path(model['cnf'])):
                needed.discard(tuple(sorted(clause)))
            assert not needed
            result['retained_certificate']={'cnf':portable(retained),'cnf_sha256':digest(retained),
                'proof':portable(trimmed),'proof_sha256':digest(trimmed),'input_clauses':len(inputs),
                'checker_log':portable(log),'checker_log_sha256':digest(log)}
            result['status']='UNSAT with direct DRAT; cold full rebuild and proof replay required'
        result['elapsed_seconds']=time.monotonic()-started
        save()
    except Exception as error:
        result.update(status='error; no unchecked exclusion promoted',error_type=type(error).__name__,
                      error_message=str(error),elapsed_seconds=time.monotonic()-started)
        save()
        raise
    print(json.dumps({k:v for k,v in result.items() if k!='incidence_witness'},indent=2),flush=True)


def replay(model_path,result_path,checker,checker_seconds,output):
    assert not output.exists()
    model=checked_model(model_path)
    domain,records,cnf,metadata=rebuild(model['case'],True)
    assert metadata==model['formula']
    assert components.sha(canonical(domain))==model['domain_record_sha256']
    assert components.sha(canonical(records))==model['pair_record_sha256']
    with tempfile.TemporaryDirectory(prefix='conway-f0-component-replay-') as directory:
        rebuilt=Path(directory)/'rebuilt.cnf'
        cnf.to_file(rebuilt)
        assert digest(rebuilt)==model['cnf_sha256']
    report={'status':'complete domain/motif coverage and exact full CNF rebuilt',
            'model_sha256':digest(model_path),'cnf_sha256':model['cnf_sha256'],
            'case':model['case'],'all66_components_excluded':False,'full_graph_completion':False}
    if result_path:
        result=json.loads(result_path.read_text())
        assert result['model_sha256']==digest(model_path) and result['cnf_sha256']==model['cnf_sha256']
        assert result['source_sha256']==digest(Path(__file__))
        if result['status'].startswith('SAT;'):
            actual=inspect(result['incidence_witness']['selected_columns'],domain,records)
            assert actual==result['incidence_witness']
            report['status']='cold full formula and exact incidence witness replay passed'
        elif result['status'].startswith('UNSAT with direct DRAT;'):
            certificate=result['retained_certificate']
            retained,proof=ROOT/certificate['cnf'],ROOT/certificate['proof']
            assert digest(retained)==certificate['cnf_sha256'] and digest(proof)==certificate['proof_sha256']
            inputs=list(read_clauses(retained))
            assert len(inputs)==certificate['input_clauses']
            needed={tuple(sorted(c)) for c in inputs}
            needed.difference_update(tuple(sorted(c)) for c in cnf.clauses)
            assert not needed
            checked=subprocess.run([str(checker),str(retained),str(proof),'-t',str(checker_seconds),'-w'],
                                   capture_output=True,text=True,timeout=checker_seconds+5,check=False)
            log=output.with_suffix('.drat.log')
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode==0 and 's VERIFIED' in checked.stdout
            report.update(status='cold complete-domain/CNF rebuild, retained inclusion and DRAT replay passed',
                          excluded_component=model['case'],retained_input_clauses=len(inputs),
                          checker_log=portable(log),checker_log_sha256=digest(log))
        else:
            assert result['status'].startswith('UNKNOWN;')
            report['status']='cold formula and UNKNOWN binding checked; no exclusion'
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    prep=commands.add_parser('prepare')
    prep.add_argument('--case',type=int,default=0)
    prep.add_argument('--model',type=Path,required=True)
    prep.add_argument('--cnf',type=Path,required=True)
    run=commands.add_parser('solve')
    run.add_argument('--model',type=Path,required=True)
    run.add_argument('--directory',type=Path,required=True)
    run.add_argument('--seconds',type=float,default=60)
    run.add_argument('--drat-trim',type=Path,required=True)
    run.add_argument('--checker-seconds',type=int,default=30)
    check=commands.add_parser('replay')
    check.add_argument('--model',type=Path,required=True)
    check.add_argument('--result',type=Path)
    check.add_argument('--output',type=Path,required=True)
    check.add_argument('--drat-trim',type=Path,default=Path('/tmp/conway99-drat-trim/drat-trim'))
    check.add_argument('--checker-seconds',type=int,default=30)
    args=parser.parse_args()
    if args.command=='prepare':
        prepare(args.case,args.model.resolve(),args.cnf.resolve())
    elif args.command=='solve':
        solve(args.model.resolve(),args.directory.resolve(),args.seconds,
              args.drat_trim.resolve(),args.checker_seconds)
    else:
        replay(args.model.resolve(),args.result.resolve() if args.result else None,
               args.drat_trim.resolve(),args.checker_seconds,args.output.resolve())
