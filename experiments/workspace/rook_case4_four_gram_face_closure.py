"""Exact full-registry propagation from the new case4 Gram face.

The frozen primary rule and independent reason checker are reused unchanged.
The only added premise rows are the70 nonnegative-real Gram zeros checked by
rook_case4_four_gram_face.py. The14 old cover units give81 distinct initial
zeros. Every further Boolean implication is flagged if it needs integrality.
No optimizer, probing assumption or numerical presolve result is used.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import complement_rook_35core_case0004_primary_propagation as rules
import rook_case4_complete_lp_recovery as recovery
import rook_case4_four_gram_face as face

RULE_SHA = '3e4b8a5118c0ee8e37aee03d5f265128b53af9ae8ffc169393fe2d731062d8f7'
RECOVERY_SHA = 'e577327c9cc2471f119c755a49a179b9f94f1004a22de80152a4114787a7eec6'
FACE_SHA = '658a4665f156ec892824c4ea5896ee05bb0346fab62f9c3461deb10d2ccf0e46'
FACE_CERT_SHA = 'c28347a46c0c9a0973e16487886d7b166f5bd008b7af2351ad4d7b4f0459cc50'
SECONDS = 60


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def save(path,value):
    assert not path.exists()
    with path.open('x') as f:
        json.dump(value,f,indent=2)
        f.write('\n')


def bindings():
    assert sha(Path(rules.__file__).read_bytes()) == RULE_SHA
    assert sha(Path(recovery.__file__).read_bytes()) == RECOVERY_SHA
    assert sha(Path(face.__file__).read_bytes()) == FACE_SHA
    return {'wrapper_sha256':sha(Path(__file__).read_bytes()),
            'unchanged_rule_and_checker_sha256':RULE_SHA,
            'published_input_recovery_sha256':RECOVERY_SHA,
            'four_Gram_proof_source_sha256':FACE_SHA,
            'four_Gram_certificate_sha256':FACE_CERT_SHA}


def load(root,certificate):
    source = bindings()
    assert sha(certificate.read_bytes()) == FACE_CERT_SHA
    proof = face.build(root/recovery.INPUTS['native_model']['path'])
    assert canonical(proof) == canonical(json.loads(certificate.read_text()))
    inventory, metadata, raw = recovery.checked_inputs(root)
    units, registry = recovery.audit_registry(raw,metadata)
    rows = rules.rows_from_inventory(inventory)
    old = recovery.original_rows(inventory)
    assert all({k:r[k] for k in ('terms','lower','upper','family')} == s for r,s in zip(rows,old))
    assert len(rows) == 2271
    zeros = proof['Gram_only_zero_columns_after_both_relations']
    assert len(zeros) == 70
    unit_ids = registry['unit_clause_ids']
    seed = sorted(set(zeros)|set(units))
    assert len(seed) == 81
    axioms = [rules.row([[a,1]],0,0,'verified_Gram_face',a) for a in zeros]
    record = {'source_bindings':source,
        'primary_inventory_sha256':recovery.PRIMARY_SHA,
        'original_native_rows':2271, 'all_original_registered_covers':178533,
        'original_integer_rows_sha256':sha(canonical(rows)),
        'complete_raw_registry_sha256':sha(raw),
        'verified_Gram_zero_axiom_rows':70,
        'verified_Gram_zero_axiom_columns':zeros,
        'augmented_integer_rows_sha256':sha(canonical(rows+axioms)),
        'initial_cover_unit_ids':unit_ids,
        'initial_cover_unit_columns':units,
        'distinct_certified_initial_zero_columns':seed,
        'requested_forward_seconds':SECONDS,
        'maximum_assignments':1214,'maximum_records':1215,'maximum_sweeps':1215,
        'new_zero_axioms_are_full_domain_theorems_not_assumptions':True,
        'optimizer_called':False,'failed_literal_probes':False}
    return record, rows, rows+axioms, raw, unit_ids, seed


def reason_row(rows,raw,origin):
    if origin['family']=='base_row':
        return rows[origin['id']]
    assert origin['family']=='cover'
    a,bits=rules.cover(raw,origin['id'])
    return rules.row([[a,-1]]+[[b,1] for b in rules.members(bits)],0,bits.bit_count(),'cover',origin['id'])


def real_scope(rows,raw,trace):
    """Separate saturation in the real box from Boolean endpoint exclusion."""
    values=[-1]*len(trace['values'])
    requiring_integrality=[]
    for index,event in enumerate(trace['records']):
        r=reason_row(rows,raw,event['origin'])
        minimum,maximum=rules.bounds(r['terms'],values)
        if event['kind']=='contradiction':
            assert minimum>r['upper'] or maximum<r['lower']
            break
        a,value=event['variable'],event['value']
        coefficient=dict(r['terms'])[a]
        assert coefficient and values[a]==-1
        if value==0:
            real=(coefficient>0 and minimum==r['upper']) or (coefficient<0 and maximum==r['lower'])
        else:
            real=(coefficient>0 and maximum==r['lower']) or (coefficient<0 and minimum==r['upper'])
        if not real:
            requiring_integrality.append({'record':index,'variable':a,'value':value,
                'origin':event['origin'],'coefficient':coefficient,
                'row_minimum':minimum,'row_maximum':maximum,
                'lower':r['lower'],'upper':r['upper']})
        values[a]=value
    assert values==trace['values']
    return {'every_step_is_valid_for_real_unit_box_points':not requiring_integrality,
        'steps_using_Boolean_endpoint_exclusion':requiring_integrality,
        'all_steps_remain_valid_for_binary_incidence':True,
        'rule':'Real endpoint fixing is credited only when the lower or upper row bound equals the exact box extremum.'}


def dimensions(original_rows,raw,values):
    """Exact face substitution and box-tautology inventory; no LP assembly."""
    families=Counter()
    nnz=0
    for r in original_rows:
        fixed=sum(c*values[a] for a,c in r['terms'] if values[a]!=-1)
        free=[(a,c) for a,c in r['terms'] if values[a]==-1]
        lower,upper=r['lower']-fixed,r['upper']-fixed
        low=sum(min(0,c) for a,c in free)
        high=sum(max(0,c) for a,c in free)
        assert lower<=high and upper>=low
        if lower<=low and high<=upper:
            families['tautological_'+r['family']]+=1
        else:
            families['retained_'+r['family']]+=1
            nnz+=len(free)
    native_rows=sum(v for k,v in families.items() if k.startswith('retained_'))
    native_nnz=nnz
    ones=sum(1<<a for a,v in enumerate(values) if v==1)
    active=sum(1<<a for a,v in enumerate(values) if v==-1)
    retained_cover=omitted_cover=0
    for i in range(178533):
        a,bits=rules.cover(raw,i)
        if values[a]==0 or bits&ones:
            omitted_cover+=1
            continue
        support=bits&active
        assert support
        retained_cover+=1
        nnz+=support.bit_count()+(values[a]==-1)
    families['retained_cover']=retained_cover
    families['tautological_cover']=omitted_cover
    assert retained_cover+omitted_cover==178533
    return {'remaining_variables':sum(v==-1 for v in values),
        'fixed_zero_columns':[a for a,v in enumerate(values) if v==0],
        'fixed_one_columns':[a for a,v in enumerate(values) if v==1],
        'remaining_native_rows':native_rows,'remaining_native_nonzeros':native_nnz,
        'remaining_cover_rows':retained_cover,'remaining_total_rows':native_rows+retained_cover,
        'remaining_nonzeros':nnz,'complete_original_row_inventory':dict(families),
        'all2271_native_rows_and178533_covers_accounted_for':True,
        'new_numeric_model_assembled':False}


def controls():
    # No branch or solver is used. These test the newly reported real/Boolean scope.
    zero=rules.row([[1,1]],0,0,'control_zero',0)
    saturated=rules.row([[0,-1],[1,1]],0,1,'control_real',1)
    real=rules.propagate(2,[zero,saturated],b'',[],1)
    assert rules.verify_trace(2,[zero,saturated],b'',real)['complete_fixed_point_rechecked']
    assert real['values']==[0,0]
    assert real_scope([zero,saturated],b'',real)['every_step_is_valid_for_real_unit_box_points']
    weighted=rules.row([[0,-2],[1,1]],0,1,'control_boolean',0)
    binary=rules.propagate(2,[weighted],b'',[],1)
    assert rules.verify_trace(2,[weighted],b'',binary)['complete_fixed_point_rechecked']
    assert binary['values']==[0,-1]
    assert len(real_scope([weighted],b'',binary)['steps_using_Boolean_endpoint_exclusion'])==1
    # x0=1/2,x1=1 is a real feasible point of the last row, proving the distinction.
    assert -2*1+1*2==0
    impossible=rules.propagate(1,[rules.row([[0,1]],0,0,'zero',0),
                                  rules.row([[0,1]],1,1,'one',1)],b'',[],1)
    assert rules.verify_trace(1,[rules.row([[0,1]],0,0,'zero',0),
                                rules.row([[0,1]],1,1,'one',1)],b'',impossible)['contradiction']
    return {'real_saturation_trace':True,'genuinely_Boolean_endpoint_trace_distinguished':True,
            'contradiction_trace':True,'optimizer_called':False}


def prepare(root,certificate,output):
    record,*_=load(root,certificate)
    record.update(status='complete full-row/cover propagation prepared; closure not run',
                  controls=controls(),case4_closure_run=False,case4_excluded=False)
    save(output,record)
    print(json.dumps({'status':record['status'],'output':str(output),'sha256':sha(output.read_bytes())},indent=2))


def inputs(preparation,root,certificate):
    saved=json.loads(preparation.read_text())
    record,original,rows,raw,units,seed=load(root,certificate)
    for k,v in record.items():
        assert saved[k]==v,('preparation',k)
    assert saved['case4_closure_run'] is False and saved['case4_excluded'] is False
    return saved,original,rows,raw,units,seed


def run(preparation,root,certificate,output):
    started=time.monotonic()
    prepared,original,rows,raw,units,seed=inputs(preparation,root,certificate)
    t=time.monotonic()
    trace=rules.propagate(1214,rows,raw,units,SECONDS)
    discovery_seconds=time.monotonic()-t
    t=time.monotonic()
    reason_check=rules.verify_trace(1214,rows,raw,trace)
    scope=real_scope(rows,raw,trace)
    if trace['complete'] and not reason_check['contradiction']:
        assert set(seed)<=set(a for a,v in enumerate(trace['values']) if v==0)
    dims=dimensions(original,raw,trace['values']) if trace['complete'] and not reason_check['contradiction'] else None
    result={'status':trace['status'],'source_bindings':bindings(),
        'preparation_sha256':sha(preparation.read_bytes()),'trace':trace,
        'exact_reason_replay':reason_check,'real_scope':scope,'dimensions':dims,
        'new_zero_columns_beyond81':[a for a,v in enumerate(trace['values']) if v==0 and a not in set(seed)],
        'new_one_columns':[a for a,v in enumerate(trace['values']) if v==1],
        'forward_seconds':discovery_seconds,'replay_and_inventory_seconds':time.monotonic()-t,
        'total_seconds':time.monotonic()-started,
        'optimizer_called':False,'failed_literal_probes':False,
        'case4_exclusion_verified_by_cold_replay':False,'whole_graph_problem_resolved':False}
    save(output,result)
    print(json.dumps({k:v for k,v in result.items() if k!='trace'},indent=2))


def replay(preparation,root,certificate,result_path,output):
    prepared,original,rows,raw,units,seed=inputs(preparation,root,certificate)
    result=json.loads(result_path.read_text())
    assert result['source_bindings']==bindings()
    assert result['preparation_sha256']==sha(preparation.read_bytes())
    trace=result['trace']
    assert len(trace['values'])==1214 and len(trace['records'])<=1215 and trace['sweeps']<=1215
    checked=rules.verify_trace(1214,rows,raw,trace)
    assert checked==result['exact_reason_replay']
    assert real_scope(rows,raw,trace)==result['real_scope']
    if trace['complete'] and not checked['contradiction']:
        assert set(seed)<=set(a for a,v in enumerate(trace['values']) if v==0)
    assert result['new_zero_columns_beyond81']==[a for a,v in enumerate(trace['values']) if v==0 and a not in set(seed)]
    assert result['new_one_columns']==[a for a,v in enumerate(trace['values']) if v==1]
    if result['dimensions'] is not None:
        assert trace['complete'] and not checked['contradiction']
        assert dimensions(original,raw,trace['values'])==result['dimensions']
    report={'status':'PASS: Gram premises, every sequential reason and complete fixed-point scope replayed',
        'source_bindings':bindings(),'preparation_sha256':sha(preparation.read_bytes()),
        'result_sha256':sha(result_path.read_bytes()),'checked':checked,
        'real_scope':result['real_scope'],'dimensions':result['dimensions'],
        'new_zero_columns_beyond81':result['new_zero_columns_beyond81'],
        'new_one_columns':result['new_one_columns'],
        'optimizer_called':False,'case4_exclusion_verified':checked['contradiction'],
        'whole_graph_problem_resolved':False}
    save(output,report)
    print(json.dumps(report,indent=2))


def main():
    p=argparse.ArgumentParser(description=__doc__)
    sub=p.add_subparsers(dest='mode',required=True)
    for mode in ('prepare','run','replay'):
        s=sub.add_parser(mode)
        s.add_argument('--root',type=Path,default=recovery.ROOT)
        s.add_argument('--certificate',type=Path,required=True)
        s.add_argument('--output',type=Path,required=True)
        if mode!='prepare':s.add_argument('--preparation',type=Path,required=True)
        if mode=='replay':s.add_argument('--result',type=Path,required=True)
    a=p.parse_args()
    if a.mode=='prepare':prepare(a.root,a.certificate,a.output)
    elif a.mode=='run':run(a.preparation,a.root,a.certificate,a.output)
    else:replay(a.preparation,a.root,a.certificate,a.result,a.output)


if __name__=='__main__':
    main()
