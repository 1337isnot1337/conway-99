"""One fixed60-by60 incidence matching across two eighteen-components.

This fixes both component incidence designs and their fiber alignment.
UNSAT can exclude only this fixed pair. SAT supplies an exact39-core
incidence point, whose known caps and visible forbidden motifs are checked.
No edges between the sixty exterior vertices are selected.
"""
import argparse
from collections import Counter
import gc
import gzip
from itertools import combinations, permutations
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

import root_prism_free_f0_coupling as coupling
import root_prism_free_f0_components as components
import root_prism_free_f0_pair_clauses as motifs


ROOT,LOGS = coupling.ROOT,coupling.LOGS
CERTIFICATE = LOGS/'f0-coupling-certificate.json.gz'
CERTIFICATE_SHA = 'bbe73089b6ae19b25ebb43597195ee81682202e3139e627fbc75db427a5c4cc7'
SOURCES = ('root_prism_free_f0_fixed_pair.py','root_prism_free_f0_coupling.py',
           'root_prism_free_f0_components.py','root_prism_free_f0_pair_clauses.py')
digest = coupling.digest


def portable(path):
    return str(path.resolve().relative_to(ROOT))


def load(complete_replay=False):
    assert digest(CERTIFICATE) == CERTIFICATE_SHA
    saved = json.loads(gzip.decompress(CERTIFICATE.read_bytes()))
    assert saved['source_sha256'] == digest(Path(coupling.__file__))
    if complete_replay:
        actual = coupling.result()
        actual['elapsed_seconds_for_information_only'] = saved['elapsed_seconds_for_information_only']
        assert actual == saved
    data = coupling.fixed_problem()
    assert saved['fixed_design'] == data[2]
    assert saved['fixed_both_pairs'] == [list(pair) for pair in data[3]]
    assert saved['joined39_Gram'] == data[-1]
    return data


def assemble(first,second,pairs,cross,first_size,second_size):
    """Complete row/column quotas, cross counts, and overlap>2 conflicts."""
    assert len(first) == len(second)
    assert pairs == sorted(set(pairs))
    pool,cnf = IDPool(start_from=len(pairs)+1),CNF()
    coverage=[]
    def exact(kind,label,literals,quota):
        assert len(literals) == len(set(literals)) and quota >= 0
        if quota > len(literals):
            cnf.append([])
        elif literals:
            cnf.extend(CardEnc.equals(literals,quota,vpool=pool,encoding=EncType.seqcounter).clauses)
        else:
            assert quota == 0
        coverage.append({'kind':kind,'indices':label,'quota':quota,'support':len(literals)})
    for a in range(len(first)):
        exact('first row',[a],[i+1 for i,p in enumerate(pairs) if p[0] == a],1)
    row_end=len(cnf.clauses)
    for b in range(len(second)):
        exact('second column',[b],[i+1 for i,p in enumerate(pairs) if p[1] == b],1)
    column_end=len(cnf.clauses)
    for i in range(first_size):
        for j in range(second_size):
            exact('cross Gram',[i,j],[k+1 for k,(a,b) in enumerate(pairs)
                                     if i in first[a] and j in second[b]],cross[i][j])
    cross_end=len(cnf.clauses)
    masks=[sum(1 << i for i in first[a])+sum(1 << (first_size+j) for j in second[b])
           for a,b in pairs]
    packing=[]
    for a,b in combinations(range(len(pairs)),2):
        if pairs[a][0] == pairs[b][0] or pairs[a][1] == pairs[b][1]:
            continue
        if (masks[a]&masks[b]).bit_count() > 2:
            packing.append([a,b])
            cnf.append([-a-1,-b-1])
    metadata={'primary_variables':len(pairs),'variables':cnf.nv,'clauses':len(cnf.clauses),
              'first_row_cardinality_clauses':row_end,
              'second_column_cardinality_clauses':column_end-row_end,
              'cross_Gram_cardinality_clauses':cross_end-column_end,
              'packing_pair_clauses':len(packing),'constraint_coverage':coverage,
              'packing_pairs_sha256':components.sha(components.canonical(packing)),
              'auxiliary_variables_begin_at':len(pairs)+1}
    return cnf,metadata


def rebuild(complete_replay=False):
    data=load(complete_replay)
    domain,selected,design,pairs,columns,core,gram=data
    cross=[[2-(i//6 == j//6) for j in range(18)] for i in range(18)]
    cnf,metadata=assemble(design,design,pairs,cross,18,18)
    assert len(metadata['constraint_coverage']) == 444
    metadata.update(row_quotas=60,column_quotas=60,cross_Gram_positions=324,
                    fixed_component_representatives=[0,0],second_fiber_alignment=[0,1,2],
                    fixed_design_on_both_sides=True,exterior_edge_variables=0,
                    additional_symmetry_assumptions=0)
    return data,cnf,metadata


def controls():
    rook=lambda a,b:a!=b and (a//3==b//3 or a%3==b%3)
    first_core,second_core,outside=[0,1],[3,4],[2,5,6,7,8]
    first=[[i for i,v in enumerate(first_core) if rook(u,v)] for u in outside]
    second=[[i for i,v in enumerate(second_core) if rook(u,v)] for u in outside]
    cross=[[sum(i in a and j in b for a,b in zip(first,second)) for j in range(2)] for i in range(2)]
    pairs=[(a,b) for a in range(5) for b in range(5)]
    cnf,_=assemble(first,second,pairs,cross,2,2)
    positive=negative=0
    with Solver(name='glucose3',bootstrap_with=cnf.clauses) as solver:
        for image in permutations(range(5)):
            wanted={(a,image[a]) for a in range(5)}
            assumptions=[k+1 if pair in wanted else -k-1 for k,pair in enumerate(pairs)]
            direct=[[sum(i in first[a] and j in second[image[a]] for a in range(5))
                     for j in range(2)] for i in range(2)]
            masks=[sum(1<<i for i in first[a])+sum(1<<(2+j) for j in second[image[a]]) for a in range(5)]
            expected=direct==cross and all((masks[a]&masks[b]).bit_count()<=2 for a,b in combinations(range(5),2))
            assert solver.solve(assumptions=assumptions)==expected
            positive+=expected
            negative+=not expected
        assert not solver.solve(assumptions=[-i-1 for i in range(len(pairs))])
    assert positive>0 and negative>0
    return {'rook9_known_matching_positive_control':True,'all_rook_control_permutations':120,
            'positive_permutations':positive,'negative_permutations':negative,
            'empty_matching_negative_control':True,'main_fixed_pair_solved':False}


def prepare(model_path,cnf_path):
    assert not model_path.exists() and not cnf_path.exists()
    started=time.monotonic()
    control=controls()
    data,cnf,metadata=rebuild(True)
    cnf.to_file(cnf_path)
    model={'status':'fixed-both-design matching model prepared; main model not solved',
           'source_hashes':{name:digest(Path(__file__).with_name(name)) for name in SOURCES},
           'coupling_certificate':portable(CERTIFICATE),'coupling_certificate_sha256':CERTIFICATE_SHA,
           'fixed_incidence_result_sha256':coupling.RESULT_SHA,
           'scope':'one fixed pair of60-triple designs on component0, identity fiber alignment',
           'whole_component_case_fixed_or_excluded':False,
           'paired_domain_sha256':components.sha(components.canonical(data[3])),
           'formula':metadata,'cnf':str(cnf_path.resolve()),'cnf_sha256':digest(cnf_path),
           'controls':control,'exact_fractional_control_scope':'larger fixed-first/all-second-domain model only',
           'visible_motif_conflicts_beyond_core_overlap_not_encoded':True,
           'SAT_scope':'full39-core incidence candidate; no exterior adjacency or full graph',
           'UNSAT_scope':'this fixed incidence pair and fiber alignment only',
           'elapsed_seconds':time.monotonic()-started}
    model_path.write_text(json.dumps(model,indent=2)+'\n')
    print(json.dumps({k:v for k,v in model.items() if k!='formula'},indent=2),flush=True)
    print(json.dumps({k:v for k,v in metadata.items() if k!='constraint_coverage'},indent=2),flush=True)


def visible_motifs(rows):
    triangles=[tuple((a,b,c)) for a in range(len(rows)) for b in range(a+1,len(rows))
               if rows[a]>>b&1 for c in range(b+1,len(rows)) if rows[a]>>c&1 and rows[b]>>c&1]
    prisms=[]
    for a,b in combinations(triangles,2):
        if set(a)&set(b):
            continue
        if all(sum(rows[u]>>v&1 for v in b)==1 for u in a) and all(sum(rows[v]>>u&1 for u in a)==1 for v in b):
            prisms.append(sorted(a+b))
    found=[]
    for u,v in combinations(range(len(rows)),2):
        if not rows[u]>>v&1:
            continue
        left=[a for a in range(len(rows)) if a!=v and rows[u]>>a&1 and not rows[v]>>a&1]
        right=[a for a in range(len(rows)) if a!=u and rows[v]>>a&1 and not rows[u]>>a&1]
        le=[(a,b) for a,b in combinations(left,2) if rows[a]>>b&1]
        re=[(a,b) for a,b in combinations(right,2) if rows[a]>>b&1]
        for l1,l2 in combinations(le,2):
            if set(l1)&set(l2):
                continue
            for r1,r2 in combinations(re,2):
                if set(r1)&set(r2):
                    continue
                sites=[u,v,*l1,*l2,*r1,*r2]
                if motifs.is_F(motifs.induced(rows,sites)):
                    found.append(sites)
    return {'known_triangles':len(triangles),'visible_prism_count':len(prisms),
            'visible_prism_supports':prisms,'visible_F_count':len(found),'visible_F_supports':found,
            'absence_of_future_motifs_not_claimed':True}


def inspect(selected,data):
    domain,indices,design,pairs,columns,core,gram=data
    assert selected==sorted(set(selected)) and len(selected)==60
    chosen=[pairs[i] for i in selected]
    assert sorted(a for a,b in chosen)==sorted(b for a,b in chosen)==list(range(60))
    paired=[columns[i] for i in selected]
    assert len({tuple(h) for h in paired})==60
    assert all(sum(i in h and j in h for h in paired)==gram[i][j] for i in range(39) for j in range(39))
    masks=[sum(1<<i for i in h) for h in paired]
    assert all(mask.bit_count()==6 for mask in masks)
    assert all(sum(1 for i in h if 3<=i<21 and (i-3)//6==f)+
               sum(1 for i in h if 21<=i<39 and (i-21)//6==f)==2
               for h in paired for f in range(3))
    assert all(((core[i]|(1<<i))&mask).bit_count()<=2 for mask in masks for i in range(39))
    assert all((masks[a]&masks[b]).bit_count()<=2 for a,b in combinations(range(60),2))
    packing=Counter(t for h in paired for t in combinations(h,3))
    assert max(packing.values())<=1
    rows=list(core)+[0]*60
    for outside,h in enumerate(paired,39):
        for i in h:
            components.edge(rows,outside,i)
    assert [row.bit_count() for row in rows]==[14]*39+[6]*60
    assert components.caps(rows)
    visible=visible_motifs(rows)
    return {'selected_variables':[i+1 for i in selected],'selected_pair_indices':selected,
            'matching':[[a,b] for a,b in chosen],'six_neighbor_columns':paired,
            'full39_Gram_entries_checked':1521,'outside_pair_caps_checked':1770,
            'known_partial_graph_caps_checked':4851,'core_triple_packing_max':max(packing.values()),
            'partial99_rows':[str(row) for row in rows],'visible_motifs':visible,
            'satisfies_all_checked_visible_PF_restrictions':not(visible['visible_prism_count'] or visible['visible_F_count']),
            'unmodeled_exterior_edges':1770,'full_graph_completion':False}


def checked_model(path,require_cnf=False):
    model=json.loads(path.read_text())
    for name,expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name))==expected
    assert model['coupling_certificate_sha256']==CERTIFICATE_SHA
    if require_cnf:
        assert digest(Path(model['cnf']))==model['cnf_sha256']
    return model


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
    result={'status':'running one fixed incidence matching query','model':portable(model_path),
            'model_sha256':digest(model_path),'source_sha256':digest(Path(__file__)),
            'cnf_sha256':model['cnf_sha256'],'seconds_including_bootstrap':seconds,
            'direct_checker_seconds':checker_seconds,'assumptions':[],
            'whole_component_or_split_case_excluded':False,'full_graph_completion':False}
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
                result['status']='UNKNOWN; this fixed incidence pair remains unresolved'
            elif answer:
                positive={v for v in solver.get_model() if v>0}
                selected=[i for i in range(model['formula']['primary_variables']) if i+1 in positive]
                result['incidence_candidate']=inspect(selected,load())
                result['status']='SAT; exact39-core incidence candidate checked, exterior edges unspecified'
            else:
                proof=solver.get_proof()
                assert proof is not None
                result['terminal_empty_clause_appended']=not proof or proof[-1]!='0'
                if result['terminal_empty_clause_appended']:
                    proof.append('0')
                raw=directory/'raw.drat'
                raw.write_text('\n'.join(proof)+'\n')
                result.update(status='solver UNSAT; direct DRAT pending',raw_proof=portable(raw),
                              raw_proof_sha256=digest(raw),raw_proof_lines=len(proof))
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
    print(json.dumps({k:v for k,v in result.items() if k!='incidence_candidate'},indent=2),flush=True)


def replay(model_path,result_path,checker,checker_seconds,output):
    assert not output.exists()
    model=checked_model(model_path)
    data,cnf,metadata=rebuild(True)
    assert metadata==model['formula']
    assert components.sha(components.canonical(data[3]))==model['paired_domain_sha256']
    with tempfile.TemporaryDirectory(prefix='conway-f0-fixed-pair-replay-') as directory:
        rebuilt=Path(directory)/'rebuilt.cnf'
        cnf.to_file(rebuilt)
        assert digest(rebuilt)==model['cnf_sha256']
    report={'status':'exact fixed-pair domain and full CNF rebuilt','model_sha256':digest(model_path),
            'cnf_sha256':model['cnf_sha256'],'whole_component_or_split_case_excluded':False,
            'full_graph_completion':False}
    if result_path:
        result=json.loads(result_path.read_text())
        assert result['model_sha256']==digest(model_path) and result['cnf_sha256']==model['cnf_sha256']
        assert result['source_sha256']==digest(Path(__file__))
        if result['status'].startswith('SAT;'):
            actual=inspect(result['incidence_candidate']['selected_pair_indices'],data)
            assert actual==result['incidence_candidate']
            report.update(status='cold full formula and exact39-core incidence candidate replay passed',
                          visible_F_motifs=actual['visible_motifs']['visible_F_count'],
                          visible_prisms=actual['visible_motifs']['visible_prism_count'])
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
                          excluded_scope='one fixed pair of60-triple designs and identity fiber alignment only',
                          retained_input_clauses=len(inputs),checker_log=portable(log),
                          checker_log_sha256=digest(log))
        else:
            assert result['status'].startswith('UNKNOWN;')
            report['status']='cold formula and UNKNOWN binding checked; no exclusion'
    output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='command',required=True)
    prep=commands.add_parser('prepare')
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
        prepare(args.model.resolve(),args.cnf.resolve())
    elif args.command=='solve':
        solve(args.model.resolve(),args.directory.resolve(),args.seconds,
              args.drat_trim.resolve(),args.checker_seconds)
    else:
        replay(args.model.resolve(),args.result.resolve() if args.result else None,
               args.drat_trim.resolve(),args.checker_seconds,args.output.resolve())
