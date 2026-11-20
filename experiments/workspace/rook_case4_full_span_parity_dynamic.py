"""Point-parameterized full-span parity proposals and exact proof conversion.

The complete286-row span and112-zero domain remain immutable. Only the accepted
point, its exact registry prefix, rounding bits, integer weights and bound vary.
"""
import copy
import gzip
import hashlib
import json
import os
from pathlib import Path
import resource
import time

import rook_case4_full_span_parity_separation as formulation
import rook_case4_full_span_parity_query as fixed_query
import rook_case4_parity_cycle_exact as exact
import rook_case4_parity_polytope as parity

ROOT=Path(__file__).resolve().parents[2]
LOG='experiments/logs/grids-and-triangles/'
SOURCES={
 'formulation':('experiments/workspace/rook_case4_full_span_parity_separation.py','893c7b0ba5d849daf29ed6a5668fb937efda854103d99812e84a68df66f27207'),
 'fixed_query':('experiments/workspace/rook_case4_full_span_parity_query.py','3a66af1c2500eebdb36001a004628460f936efc60584d411a2dbdc37d4a928da'),
 'exact':('experiments/workspace/rook_case4_parity_cycle_exact.py','2f10a42f546623cb1840d228101537e6f4f4bc584776407140ae0c36b08c99b7'),
 'parity':('experiments/workspace/rook_case4_parity_polytope.py','048df509b05601f15d6cb4230750b36d221276cce66e625b0cf9c720ecb89062'),
}
INPUTS={
 'span_preparation':(LOG+'rook-case4-full-span-parity-preparation01/preparation.json','0b2de700e4cd088ffb7a52726b0aef4cf8e3d0eeb4ade2d2dfacdf9dc7dbdd90'),
 'span_audit':(LOG+'rook-case4-full-span-parity-independent-audit01.json','d6d7cfef703c8e598cb52b7c3dce67aaf9f7a7b99028e83056fb95f7c31885f5'),
 'lp_preflight':(LOG+'rook-case4-parity-cycle-preflight04.json','d3827408d08dd443093cba2d0c19e250391c142c6e97a4f04f316567c04bf264'),
}
INTEGER_LIMIT=(1 << 62)-1
MAX_SPEC_BYTES=16 << 20
MAX_PROTO_BYTES=16 << 20


def sha(raw):return hashlib.sha256(raw).hexdigest()


def canonical(value):return exact.canonical(value)


def ref(path):
    path=Path(path).resolve()
    return {'path':str(path.relative_to(ROOT)),'sha256':sha(path.read_bytes())}


def checked(reference):
    path=(ROOT/reference['path']).resolve();assert path.is_relative_to(ROOT)
    raw=path.read_bytes();assert sha(raw)==reference['sha256'],reference['path']
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def bound(name):
    path,digest=INPUTS[name];return checked({'path':path,'sha256':digest})


def save(path,value,gz=False):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    raw=canonical(value)
    if gz:raw=gzip.compress(raw,mtime=0)
    temporary=path.with_name(path.name+'.tmp')
    with temporary.open('wb') as stream:
        stream.write(raw);stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)
    return ref(path)


def bindings():
    modules={'formulation':formulation,'fixed_query':fixed_query,'exact':exact,'parity':parity}
    for name,(path,digest) in SOURCES.items():
        assert Path(modules[name].__file__).resolve()==ROOT/path
        assert sha((ROOT/path).read_bytes())==digest
    return json.loads(json.dumps({'dynamic_source_sha256':sha(Path(__file__).read_bytes()),'sources':SOURCES,'inputs':INPUTS}))


def fixed_domain():
    bindings();prepared=bound('span_preparation');audit=bound('span_audit')
    assert prepared['source_sha256']==SOURCES['formulation'][1]
    assert audit['status'].startswith('PASS:') and audit['preparation_sha256']==INPUTS['span_preparation'][1]
    assert audit['specification_sha256']==prepared['specification']['sha256']
    template=checked(prepared['specification'])
    assert len(template['basis_rhs'])==286 and template['span_certificate']['rank']==286
    assert len(template['fixed_zero_columns'])==112 and len(template['kept_original_columns'])==1102
    assert audit['exact_rank']==286 and audit['original_equation_span_representations_checked']==630
    native=checked({'path':prepared['inputs']['native'][0],'sha256':prepared['inputs']['native'][1]})
    return prepared,template,native


def accepted_point(point,registry,accepted_count):
    assert type(accepted_count) is int and 0<=accepted_count<=len(registry)
    candidate,cold=checked(point['candidate']),checked(point['cold'])
    assert cold['status'].startswith('PASS:') and cold['exact_point_replayed']
    assert cold['candidate_sha256']==point['candidate']['sha256']
    prefix=registry[:accepted_count];digest=sha(canonical(prefix))
    assert cold['registry_sha256']==candidate['registry_sha256']==digest
    assert cold['full_face_rows_checked']==candidate['exact_check']['full_face_rows_checked']==167115+accepted_count
    outcome,state=checked(cold['result']),checked(cold['state'])
    assert outcome['state']==cold['state'] and outcome['candidate']==point['candidate']
    assert outcome['exact_point_found'] and not outcome['exact_certificate_found']
    assert outcome['optimizer_calls']==0
    assert state['cuts']==prefix
    flight=bound('lp_preflight')
    assert state['source_bindings']==flight['source_bindings']
    nums=list(map(int,candidate['exact_check']['original1214_selector_numerators']))
    den=int(candidate['common_denominator'])
    assert len(nums)==1214 and den>0 and all(0<=n<=den for n in nums)
    return nums,den


def point_specification(point,registry,accepted_count,deadline):
    """Pure exact transport from one full-model accepted point; no search."""
    assert accepted_count==len(registry), 'separator requires an accepted current-registry point'
    prepared,template,native=fixed_domain()
    nums,den=accepted_point(point,registry,accepted_count)
    assert all(nums[a]==0 for a in template['fixed_zero_columns'])
    assert all(nums[a]>0 for a in template['kept_original_columns'])
    for i,j,q,support in native['primary_inventory']['Gram_rows']:
        exact.tick(deadline);assert sum(nums[a] for a in support)==q*den
    spec=copy.deepcopy(template)
    spec['schema']='conway99.rook.case4.full_span_parity_separation.dynamic.v1'
    spec['inputs']=copy.deepcopy(template['inputs'])
    spec['inputs']['point']=[point['candidate']['path'],point['candidate']['sha256']]
    spec['inputs']['point_cold']=[point['cold']['path'],point['cold']['sha256']]
    spec['point_numerators1214']=list(map(str,nums));spec['denominator']=str(den)
    kept=template['kept_original_columns']
    spec['weights']=[min(nums[a],den-nums[a]) for a in kept]
    spec['penalties']=[abs(den-2*nums[a]) for a in kept]
    spec['nearest_bits']=[int(2*nums[a]>den) for a in kept]
    spec['weighted_upper']=den-1
    spec['weighted_nonzeros']=sum(c!=0 for c in spec['weights']+spec['penalties'])
    spec['worst_weighted_unit_box_activity']=sum(spec['weights'])+sum(spec['penalties'])
    assert max([den,*spec['weights'],*spec['penalties']])<=INTEGER_LIMIT
    assert spec['worst_weighted_unit_box_activity']<=INTEGER_LIMIT
    spec['dynamic_context']={'source_bindings':bindings(),'point':point,
                             'point_key':exact.point_key(nums,den),'registry_sha256':sha(canonical(registry)),
                             'accepted_cut_count':accepted_count,'accepted_extended_rows':167115+accepted_count,
                             'fixed_template_specification':prepared['specification']}
    changed={'schema','inputs','point_numerators1214','denominator','weights','penalties','nearest_bits',
             'weighted_upper','weighted_nonzeros','worst_weighted_unit_box_activity','dynamic_context'}
    assert {k:spec[k] for k in spec if k not in changed}=={k:template[k] for k in template if k not in changed}
    assert len(canonical(spec))<=MAX_SPEC_BYTES
    exact.tick(deadline)
    return spec,native


def transport(spec,directory):
    from ortools.sat import cp_model_pb2
    prepared=bound('span_preparation')
    assert formulation.runtime_binding()==prepared['runtime_binding']
    model=formulation.build_model(spec)
    path=directory/'model.pb';assert model.export_to_file(str(path))
    raw=path.read_bytes();assert len(raw)<=MAX_PROTO_BYTES
    actual=cp_model_pb2.CpModelProto();actual.ParseFromString(raw)
    formulation.literal_proto_check(actual,spec)
    baseline=cp_model_pb2.CpModelProto()
    path0=ROOT/prepared['proto']['path'];raw0=path0.read_bytes()
    assert sha(raw0)==prepared['proto']['sha256'];baseline.ParseFromString(raw0)
    assert list(actual.variables)==list(baseline.variables)
    assert len(actual.constraints)==len(baseline.constraints)==2208
    assert all(actual.constraints[r]==baseline.constraints[r] for r in range(2208) if r not in (1103,2207))
    return model,{'proto':ref(path),'bytes':len(raw),'unchanged_variables':2491,
                  'unchanged_constraints':2206,'only_permitted_changed_rows':[1103,2207],
                  'literal_dynamic_rows_checked':True,'runtime_binding':prepared['runtime_binding']}


def normalize_cut(raw,spec,native,deadline):
    """Canonical nearest vertex for this support, without another span search."""
    nums=list(map(int,spec['point_numerators1214']));den=int(spec['denominator'])
    support=raw['active_original_support'];rhs=raw['parity_rhs']
    certificate=parity.closest_forbidden(support,rhs,nums,den)
    check=parity.check_exact(certificate,nums,den)
    # A strictly violated one-flip witness is already the nearest forbidden
    # vertex: its flipped coordinate must have weight>half the support total.
    assert certificate['forbidden_ones']==raw['forbidden_ones']
    assert check['exact_violation_numerator']==int(raw['exact_deficit_numerator'])>0
    normalized={key:raw[key] for key in ['original_Gram_row_ids','full_original1214_integer_coefficients',
                                        'original_Gram_rhs_sum','removed_proved_zero_odd_columns','parity_rhs']}
    normalized.update(active_original_support_hex=hex(sum(1 << a for a in support)),
                      forbidden_vertex_certificate=certificate,inequality=check['inequality'],
                      exact_violation_numerator=check['exact_violation_numerator'],
                      family='full_original_Gram_parity_span')
    exact.verify_cut(normalized,native['primary_inventory']['Gram_rows'],spec['fixed_zero_columns'],nums,den,deadline)
    return normalized


def separate(state_path,directory,check_state):
    started=time.monotonic();deadline=started+115
    state=check_state(state_path);context=state['full_span_continuation']
    assert context['point_accepted_cut_count']==len(state['cuts'])
    result={'status':'STARTING','state':ref(state_path),'bindings':bindings(),'native_calls':0,
            'native_seconds':0.0,'case4_excluded':False,'native_INFEASIBLE_is_uncertified':True}
    save(directory/'result.json',result)
    try:
        spec,native=point_specification(state['point'],state['cuts'],len(state['cuts']),deadline)
        result['specification']=save(directory/'specification.json.gz',spec,True)
        model,record=transport(spec,directory);result['transport']=record
        solver=fixed_query.configured_solver()
        assert solver.parameters.max_time_in_seconds==60 and solver.parameters.num_search_workers==1
        result.update(status='RUNNING: sole full-span native call',native_calls=1,parameters=str(solver.parameters))
        save(directory/'result.json',result)
        from ortools.sat.python import cp_model
        before=time.monotonic();answer=solver.solve(model)
        result.update(native_seconds=time.monotonic()-before,backend_status=solver.status_name(answer),
                      backend_status_code=int(answer),statistics={'branches':solver.num_branches,
                      'conflicts':solver.num_conflicts,'wall_time':solver.wall_time})
        values=list(solver.response_proto.solution)
        if len(values)==2491 and all(type(v) is int and v in (0,1) for v in values):
            result['native_vector']=save(directory/'native-vector.json',
                {'state':ref(state_path),'specification':result['specification'],'model':record['proto'],
                 'values':values,'accepted':False,'backend_status':result['backend_status']})
            save(directory/'result.json',result)
        response=str(solver.response_proto).encode()+b'\n'
        assert len(response)<=4 << 20
        (directory/'response.txt').write_bytes(response);result['native_response']=ref(directory/'response.txt')
        if answer in (cp_model.OPTIMAL,cp_model.FEASIBLE):
            assert 'native_vector' in result
            cut=formulation.inspect_assignment(spec,values,{'native':native})
            cut.update(state=ref(state_path),source_point=state['point'],native_vector=result['native_vector'])
            result['cut']=save(directory/'cut.json',cut)
            result['status']='OWNER_CHECKED_CUT: separate direct replay required'
        elif answer in (cp_model.INFEASIBLE,cp_model.UNKNOWN):
            result['status']='UNRESOLVED: no exact cut; native status is not a no-cut certificate'
        else:result['status']='ERROR: invalid native model or unexpected status'
    except Exception as error:
        result.update(status='UNRESOLVED: separator error; no retry',error_type=type(error).__name__,reason=str(error))
    finally:
        result['seconds']=time.monotonic()-started
        result['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(directory/'result.json',result)
    return result


def replay(state_path,directory,check_state):
    started=time.monotonic();deadline=started+10
    state=check_state(state_path);result=json.loads((directory/'result.json').read_text())
    assert result['state']==ref(state_path) and result['bindings']==bindings()
    assert result['native_calls']==1 and result['case4_excluded'] is False
    if 'native_response' in result:
        response=result['native_response']
        assert sha((ROOT/response['path']).read_bytes())==response['sha256']
    spec,native=point_specification(state['point'],state['cuts'],len(state['cuts']),deadline)
    assert checked(result['specification'])==json.loads(json.dumps(spec))
    assert result['transport']['runtime_binding']==bound('span_preparation')['runtime_binding']
    proto_ref=result['transport']['proto'];proto_bytes=(ROOT/proto_ref['path']).read_bytes()
    assert sha(proto_bytes)==proto_ref['sha256']
    from ortools.sat import cp_model_pb2
    proto=cp_model_pb2.CpModelProto();proto.ParseFromString(proto_bytes)
    formulation.literal_proto_check(proto,spec)
    vector=None;addition=None;direct=None
    if 'native_vector' in result:
        vector=checked(result['native_vector'])
        assert vector['state']==ref(state_path) and vector['specification']==result['specification']
        assert vector['model']==proto_ref
    if result['status']=='OWNER_CHECKED_CUT: separate direct replay required':
        assert vector is not None and formulation.evaluate_proto(proto,vector['values'])
        raw=checked(result['cut'])
        assert raw['state']==ref(state_path) and raw['source_point']==state['point']
        assert raw['native_vector']==result['native_vector']
        direct=fixed_query.direct_cut_check(spec,vector,raw,native['primary_inventory']['Gram_rows'])
        normalized=normalize_cut(raw,spec,native,deadline)
        key=exact.row_key(normalized['inequality'])
        assert key not in {entry['row_key'] for entry in state['cuts']}
        addition={'certificate':normalized,'row_key':key,'source_point':state['point'],
                  'full_span_native_cut':result['cut'],'full_span_native_vector':result['native_vector']}
    else:assert result['status'].startswith(('UNRESOLVED:','ERROR:'))
    exact.tick(deadline)
    report={'status':'PASS: full-span terminal and direct original-Gram cut replay',
            'state':ref(state_path),'result':ref(directory/'result.json'),'bindings':bindings(),
            'direct_original_arithmetic':direct,'registry_addition':addition,
            'canonical_nearest_vertex_is_chosen_only_within_saved_support':True,
            'native_calls':0,'native_model_rebuilds':0,'span_searches':0,
            'native_INFEASIBLE_is_uncertified':True,'case4_excluded':False,
            'seconds':time.monotonic()-started}
    assert not (directory/'proof.json').exists();save(directory/'proof.json',report)
    return report


def controls():
    # This tests the new coefficient transport, not the frozen Boolean model again.
    cases=0
    for den in (1,2,3,7,(1 << 40)+1):
        for n in sorted(set((0,den//2,den//2+1,den))):
            if n>den:continue
            f=int(2*n>den);w=min(n,den-n);penalty=abs(den-2*n)
            assert w==(den-n if f else n)
            assert w+penalty==(n if f else den-n)
            cases+=1
    assert sum([INTEGER_LIMIT//2]*3)>INTEGER_LIMIT
    transfer=0
    for nums in ([9,2,1],[1,4,1],[5,0,0]):
        for rhs in (0,1):
            nearest=parity.closest_forbidden([0,1,2],rhs,nums,10)
            for flip in (None,0,1,2):
                ones=[a for a,n in enumerate(nums) if bool(2*n>10)^(a==flip)]
                if len(ones)%2==rhs:continue
                cost=sum(10-n if a in ones else n for a,n in enumerate(nums))
                if cost<10:
                    assert nearest['forbidden_ones']==ones and nearest['distance_numerator']==cost
                transfer+=1
    return {'dynamic_weight_and_flip_cases':cases,'overflow_refusal_arithmetic':True,
            'strict_one_flip_to_canonical_certificate_controls':transfer,
            'old13056_controls_repeated':False,'production_points_searched':0,'optimizer_calls':0}
