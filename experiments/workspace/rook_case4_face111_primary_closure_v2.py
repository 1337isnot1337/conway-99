"""Complete111-zero closure with the proved second-cover equality explicit.

Both new integer covers remain explicit rows. The primary propagation rule
and independent sequential-reason checker are unchanged. New units enter
only through the direct full1214-coordinate integer Gram proof. There is no
optimizer, probing assumption, native presolve premise or new row search.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import complement_rook_35core_case0004_primary_propagation as rules
import rook_case4_complete_lp_recovery as recovery
import rook_case4_four_gram_face_closure as earlier
import rook_case4_face99_parity_face as face

RULE_SHA='3e4b8a5118c0ee8e37aee03d5f265128b53af9ae8ffc169393fe2d731062d8f7'
RECOVERY_SHA='e577327c9cc2471f119c755a49a179b9f94f1004a22de80152a4114787a7eec6'
EARLIER_SHA='ea4bd7b7be0f98bcf81d2335d20ff09e794087a4e2b33feac689105f4c231777'
FACE_SHA='52621284ad3b8344c5b64e99b028a8e5e063f32e91468399ad69ab4ee69e93cc'
FACE_CERT_SHA='717c3e4103dd56bdd260f52b0f50c5a06f4245b834d92194357481d3163e229e'
SECONDS=60


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def save(path,value):
    assert not path.exists()
    path.write_text(json.dumps(value,indent=2)+'\n')


def bindings():
    for module,expected in ((rules,RULE_SHA),(recovery,RECOVERY_SHA),(earlier,EARLIER_SHA),(face,FACE_SHA)):
        assert sha(Path(module.__file__).read_bytes())==expected
    return {'wrapper_sha256':sha(Path(__file__).read_bytes()),
        'unchanged_rule_and_reason_checker_sha256':RULE_SHA,
        'published_input_recovery_sha256':RECOVERY_SHA,
        'unchanged_scope_and_dimension_helper_sha256':EARLIER_SHA,
        'full_coordinate_integer_Gram_proof_sha256':FACE_SHA,
        'full_coordinate_integer_Gram_certificate_sha256':FACE_CERT_SHA}


def load(root,certificate):
    source=bindings()
    assert sha(certificate.read_bytes())==FACE_CERT_SHA
    proof=face.prove(root)
    assert canonical(proof)==canonical(json.loads(certificate.read_bytes()))
    inventory,metadata,raw=recovery.checked_inputs(root)
    unit_columns,registry=recovery.audit_registry(raw,metadata)
    original=rules.rows_from_inventory(inventory)
    assert len(original)==2271
    assert [{k:r[k] for k in ('terms','lower','upper','family')} for r in original]==recovery.original_rows(inventory)
    parity=[rules.row(row['terms'],row['lower'],row['upper'],'integer_parity_cover',i)
            for i,row in enumerate(proof['both_integer_cover_rows'])]
    assert len(parity)==2 and all(len(row['terms'])==42 and row['lower']==1 and row['upper']==42 for row in parity)
    # The direct Gram identity is H2+2*sum(new12)=1. All new12
    # coordinates are proved zero, so H2 has both lower and upper bound1.
    assert proof['original_Gram_right_hand_side']==1
    assert proof['direct_identity_on_prior_face']=='sum_H2(x)+2*sum_new12(x)=1'
    assert parity[1]['terms']==[[a,1] for a in proof['H2_support']]
    assert set(proof['new_zero_columns'])<=set(proof['all_zero_columns'])
    parity[1]['upper']=1
    seed=proof['all_zero_columns']
    assert len(seed)==111 and seed==sorted(set(seed)) and set(unit_columns)<=set(seed)
    assert len(proof['prior_zero_columns'])==99 and len(proof['new_zero_columns'])==12
    axioms=[rules.row([[a,1]],0,0,'proved_integer_Gram_zero',a) for a in seed]
    native=original+parity
    rows=native+axioms
    assert len(native)==2273 and len(rows)==2384
    record={'source_bindings':source,'primary_inventory_sha256':recovery.PRIMARY_SHA,
        'original_native_rows':2271,'added_proved_integer_cover_rows':2,
        'all_original_registered_covers':178533,
        'original_integer_rows_sha256':sha(canonical(original)),
        'native_and_integer_cover_rows_sha256':sha(canonical(native)),
        'complete_raw_registry_sha256':sha(raw),
        'verified_zero_axiom_rows':111,'verified_zero_axiom_columns':seed,
        'prior99_zeros':proof['prior_zero_columns'],'new12_integer_zeros':proof['new_zero_columns'],
        'augmented_integer_rows_sha256':sha(canonical(rows)),
        'total_augmented_native_rows':2384,
        'initial_cover_unit_ids':registry['unit_clause_ids'],
        'initial_cover_unit_columns':unit_columns,
        'distinct_certified_initial_zero_columns':seed,
        'both_integer_cover_rows_retained':True,
        'second_cover_exactly_one_from_direct_Gram_identity':True,
        'integer_cover_ranges':[[1,42],[1,1]],
        'requested_forward_seconds':SECONDS,
        'maximum_assignments':1214,'maximum_records':1215,'maximum_sweeps':1215,
        'new_zero_axioms_are_global_integer_theorems_not_branch_assumptions':True,
        'real_scope':'Any real-saturation labels are relative to the augmented rows and integer-derived premises, not to the old real LP.',
        'optimizer_called':False,'failed_literal_probes':False}
    return record,native,rows,raw,registry['unit_clause_ids'],seed


def prepare(root,certificate,output):
    record,*_=load(root,certificate)
    record.update(status='complete111-zero original-row/cover closure prepared; no production closure',
        controls=earlier.controls(),case4_closure_run=False,case4_excluded=False)
    save(output,record)
    print(json.dumps({'status':record['status'],'output':str(output),'sha256':sha(output.read_bytes())},indent=2))


def checked(preparation,root,certificate):
    saved=json.loads(preparation.read_bytes())
    record,native,rows,raw,units,seed=load(root,certificate)
    for key,value in record.items():assert saved[key]==value,('preparation',key)
    assert not saved['case4_closure_run'] and not saved['case4_excluded']
    return saved,native,rows,raw,units,seed


def run(preparation,root,certificate,output):
    started=time.monotonic()
    prepared,native,rows,raw,units,seed=checked(preparation,root,certificate)
    before=time.monotonic()
    trace=rules.propagate(1214,rows,raw,units,SECONDS)
    forward_seconds=time.monotonic()-before
    before=time.monotonic()
    reason_check=rules.verify_trace(1214,rows,raw,trace)
    scope=earlier.real_scope(rows,raw,trace)
    scope['relative_to_augmented_integer_derived_premises_only']=True
    if trace['complete'] and not reason_check['contradiction']:
        assert set(seed)<=set(a for a,v in enumerate(trace['values']) if v==0)
    dims=earlier.dimensions(native,raw,trace['values']) if trace['complete'] and not reason_check['contradiction'] else None
    if dims is not None:
        dims['both_integer_cover_rows_accounted_for']=True
        dims['original_plus_integer_cover_row_count']=2273
    result={'status':trace['status'],'source_bindings':bindings(),
        'preparation_sha256':sha(preparation.read_bytes()),'trace':trace,
        'exact_reason_replay':reason_check,'relative_real_scope':scope,'dimensions':dims,
        'new_zero_columns_beyond111':[a for a,v in enumerate(trace['values']) if v==0 and a not in set(seed)],
        'new_one_columns':[a for a,v in enumerate(trace['values']) if v==1],
        'forward_seconds':forward_seconds,'replay_and_inventory_seconds':time.monotonic()-before,
        'total_seconds':time.monotonic()-started,
        'optimizer_called':False,'failed_literal_probes':False,
        'case4_exclusion_verified_by_cold_replay':False,'whole_graph_problem_resolved':False}
    save(output,result)
    print(json.dumps({k:v for k,v in result.items() if k!='trace'},indent=2))


def replay(preparation,root,certificate,result_path,output):
    started=time.monotonic()
    prepared,native,rows,raw,units,seed=checked(preparation,root,certificate)
    result=json.loads(result_path.read_bytes())
    assert result['source_bindings']==bindings()
    assert result['preparation_sha256']==sha(preparation.read_bytes())
    trace=result['trace']
    assert len(trace['values'])==1214 and len(trace['records'])<=1215 and trace['sweeps']<=1215
    check=rules.verify_trace(1214,rows,raw,trace)
    assert check==result['exact_reason_replay']
    scope=earlier.real_scope(rows,raw,trace)
    scope['relative_to_augmented_integer_derived_premises_only']=True
    assert scope==result['relative_real_scope']
    if trace['complete'] and not check['contradiction']:
        assert set(seed)<=set(a for a,v in enumerate(trace['values']) if v==0)
    assert result['new_zero_columns_beyond111']==[a for a,v in enumerate(trace['values']) if v==0 and a not in set(seed)]
    assert result['new_one_columns']==[a for a,v in enumerate(trace['values']) if v==1]
    if result['dimensions'] is not None:
        assert trace['complete'] and not check['contradiction']
        dims=earlier.dimensions(native,raw,trace['values'])
        dims['both_integer_cover_rows_accounted_for']=True
        dims['original_plus_integer_cover_row_count']=2273
        assert dims==result['dimensions']
    report={'status':'PASS:111 proved premises, every sequential reason and complete fixed-point scope replayed',
        'source_bindings':bindings(),'preparation_sha256':sha(preparation.read_bytes()),
        'result_sha256':sha(result_path.read_bytes()),'checked':check,
        'relative_real_scope':result['relative_real_scope'],'dimensions':result['dimensions'],
        'new_zero_columns_beyond111':result['new_zero_columns_beyond111'],
        'new_one_columns':result['new_one_columns'],'optimizer_called':False,
        'case4_exclusion_verified':check['contradiction'],'whole_graph_problem_resolved':False,
        'seconds':time.monotonic()-started}
    save(output,report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','run','replay'))
    parser.add_argument('--root',type=Path,default=recovery.ROOT)
    parser.add_argument('--certificate',type=Path,required=True)
    parser.add_argument('--preparation',type=Path)
    parser.add_argument('--result',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    a=parser.parse_args()
    if a.mode=='prepare':prepare(a.root,a.certificate,a.output)
    elif a.mode=='run':
        assert a.preparation is not None
        run(a.preparation,a.root,a.certificate,a.output)
    else:
        assert a.preparation is not None and a.result is not None
        replay(a.preparation,a.root,a.certificate,a.result,a.output)
