"""One bounded parity-separation proposal, followed by exact cut acceptance.

The original graph/incidence problem is never declared infeasible here.
"""
import argparse
import ast
import gzip
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import resource
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parents[2]
LOG = 'experiments/logs/grids-and-triangles/'
SUBJECT = 'experiments/workspace/rook_case4_full_span_parity_separation.py'
SUBJECT_SHA = '893c7b0ba5d849daf29ed6a5668fb937efda854103d99812e84a68df66f27207'
MODEL_PREP = LOG+'rook-case4-full-span-parity-preparation01/preparation.json'
MODEL_PREP_SHA = '0b2de700e4cd088ffb7a52726b0aef4cf8e3d0eeb4ade2d2dfacdf9dc7dbdd90'
AUDIT_SOURCE = 'experiments/workspace/rook_case4_full_span_parity_independent_audit.py'
AUDIT_SOURCE_SHA = '9ce4502d0b1d20e27c071cf5c50226bd13a98313b7fb8c1217fea1f8af644944'
AUDIT = LOG+'rook-case4-full-span-parity-independent-audit01.json'
AUDIT_SHA = 'd6d7cfef703c8e598cb52b7c3dce67aaf9f7a7b99028e83056fb95f7c31885f5'
WATCHDOG = 'experiments/workspace/complement_rook_35core_case0004_coordinate_cover_cadical.py'
WATCHDOG_SHA = '1921f71964795d819e0369c9679dc1526df97c29bb1920a932c7ca449ba3de25'
LIMITS = {'native_seconds':60,'owned_child_seconds':120,'workers':1,
          'native_calls':1,'retries':0,'cold_seconds':60,'maximum_response_bytes':4 << 20}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def portable(path):
    return str(Path(path).resolve().relative_to(ROOT))


def save(path,value):
    path=Path(path); path.parent.mkdir(parents=True,exist_ok=True)
    temporary=path.with_name(path.name+'.tmp')
    with temporary.open('w') as stream:
        json.dump(value,stream,sort_keys=True,indent=2,allow_nan=False)
        stream.write('\n');stream.flush();os.fsync(stream.fileno())
    os.replace(temporary,path)


def bound_json(path,expected):
    assert digest(ROOT/path)==expected,path
    raw=(ROOT/path).read_bytes()
    return json.loads(gzip.decompress(raw) if path.endswith('.gz') else raw)


def load_subject():
    path=ROOT/SUBJECT;assert digest(path)==SUBJECT_SHA
    spec=importlib.util.spec_from_file_location('frozen_full_span_parity',path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    return module


def bindings():
    frozen=bound_json(MODEL_PREP,MODEL_PREP_SHA)
    audit=bound_json(AUDIT,AUDIT_SHA)
    assert digest(ROOT/AUDIT_SOURCE)==AUDIT_SOURCE_SHA
    assert audit['audit_source_sha256']==AUDIT_SOURCE_SHA
    assert audit['subject_source_sha256']==frozen['source_sha256']==SUBJECT_SHA
    assert audit['preparation_sha256']==MODEL_PREP_SHA and audit['status'].startswith('PASS:')
    assert audit['proto_sha256']==frozen['proto']['sha256']
    assert audit['specification_sha256']==frozen['specification']['sha256']
    spec=bound_json(frozen['specification']['path'],frozen['specification']['sha256'])
    assert digest(ROOT/frozen['proto']['path'])==frozen['proto']['sha256']
    for name,(path,expected) in frozen['inputs'].items(): assert digest(ROOT/path)==expected,name
    for item in frozen['runtime_binding']['files'].values(): assert digest(item['path'])==item['sha256']
    assert frozen['production_optimizer_calls']==0 and spec['case4_exclusion_claimed'] is False
    return frozen,spec


def owned_child(command, log_path, seconds, on_timeout):
    """Persist timeout status before SIGKILL; always reap our child."""
    started = time.monotonic()
    with log_path.open('wb') as log:
        process = subprocess.Popen(command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT)
        timed_out = False
        killed = False
        try:
            try:
                returncode = process.wait(timeout=max(0.001, seconds-(time.monotonic()-started)))
            except subprocess.TimeoutExpired:
                timed_out = True
                try:
                    on_timeout(process.pid, time.monotonic()-started)
                finally:
                    try:
                        process.kill()
                        killed = True
                    except ProcessLookupError:
                        pass
                    returncode = process.wait(timeout=5)
        except BaseException:
            # An I/O error or interruption must not leave our solver child
            # running after its parent exits.
            if process.poll() is None:
                process.kill()
            process.wait(timeout=5)
            raise
        assert process.poll() is not None
    return {'pid': process.pid, 'returncode': returncode, 'timed_out': timed_out,
            'UNKNOWN_persisted_before_kill': timed_out,
            'SIGKILL_sent_at_deadline': killed, 'child_reaped': True,
            'requested_wall_seconds': seconds, 'elapsed_seconds': time.monotonic()-started,
            'log': portable(log_path), 'log_sha256': digest(log_path)}


def watchdog_reuse():
    assert digest(ROOT/WATCHDOG)==WATCHDOG_SHA
    def function(path):
        tree=ast.parse(Path(path).read_text())
        return next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name=='owned_child')
    old,new=function(ROOT/WATCHDOG),function(Path(__file__))
    assert ast.dump(old,include_attributes=False)==ast.dump(new,include_attributes=False)
    return {'source':WATCHDOG,'source_sha256':WATCHDOG_SHA,'complete_function_AST_identical':True,
            'watchdog_controls_repeated':False}


def native_model(subject,spec,frozen):
    # The small model is transported from its frozen exact specification.
    # No original-domain reconstruction, rank calculation or controls are repeated.
    model=subject.build_model(spec)
    with tempfile.TemporaryDirectory(prefix='rook_full_span_native_') as directory:
        path=Path(directory)/'model.pb';assert model.export_to_file(str(path))
        assert digest(path)==frozen['proto']['sha256']
        assert path.stat().st_size==frozen['proto']['bytes']
    return model


def configured_solver():
    from ortools.sat.python import cp_model
    solver=cp_model.CpSolver()
    solver.parameters.max_time_in_seconds=LIMITS['native_seconds']
    solver.parameters.num_search_workers=LIMITS['workers']
    solver.parameters.log_search_progress=True
    return solver


def prepare(output):
    assert not output.exists();started=time.monotonic()
    frozen,spec=bindings();subject=load_subject()
    assert subject.runtime_binding()==frozen['runtime_binding']
    native_model(subject,spec,frozen)
    solver=configured_solver()
    result={'status':'PREPARED: one full-span parity query; zero production solver calls',
            'driver_source_sha256':digest(Path(__file__)),'subject_source_sha256':SUBJECT_SHA,
            'model_preparation_sha256':MODEL_PREP_SHA,'independent_audit_sha256':AUDIT_SHA,
            'proto_sha256':frozen['proto']['sha256'],'specification_sha256':frozen['specification']['sha256'],
            'limits':LIMITS,'parameters':str(solver.parameters),'runtime_binding':frozen['runtime_binding'],
            'watchdog_reuse':watchdog_reuse(),'native_proto_transport_sha256_matches':True,
            'variables':2491,'constraints':2208,'one_complete_vector_persisted_before_replay':True,
            'objective_hint_assumptions_added':False,'native_calls':0,'controls_repeated':False,
            'INFEASIBLE_is_unresolved':True,'case4_excluded':False,'seconds':time.monotonic()-started}
    save(output,result);return result


def checked_preparation(path):
    record=json.loads(path.read_text())
    assert record['status'].startswith('PREPARED:') and record['native_calls']==0
    assert record['driver_source_sha256']==digest(Path(__file__))
    assert record['subject_source_sha256']==SUBJECT_SHA and record['limits']==LIMITS
    assert record['model_preparation_sha256']==MODEL_PREP_SHA and record['independent_audit_sha256']==AUDIT_SHA
    frozen,spec=bindings()
    assert record['proto_sha256']==frozen['proto']['sha256']
    assert record['specification_sha256']==frozen['specification']['sha256']
    assert record['runtime_binding']==frozen['runtime_binding']
    assert record['watchdog_reuse']==watchdog_reuse()
    return record,frozen,spec


def child(preparation,directory):
    started=time.monotonic()
    record,frozen,spec=checked_preparation(preparation);subject=load_subject()
    result={'status':'STARTING','driver_source_sha256':digest(Path(__file__)),
            'query_preparation_sha256':digest(preparation),'proto_sha256':frozen['proto']['sha256'],
            'native_calls':0,'case4_excluded':False,'native_INFEASIBLE_certificate_accepted':False}
    def checkpoint():
        result['elapsed_seconds']=time.monotonic()-started
        result['peak_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(directory/'child-result.json',result)
    try:
        assert subject.runtime_binding()==record['runtime_binding']
        model=native_model(subject,spec,frozen);solver=configured_solver()
        assert str(solver.parameters)==record['parameters']
        result.update(status='RUNNING: sole native call',native_calls=1,parameters=str(solver.parameters))
        checkpoint();solve_start=time.monotonic()
        from ortools.sat.python import cp_model
        answer=solver.solve(model)
        result.update(native_seconds=time.monotonic()-solve_start,backend_status_code=int(answer),
                      backend_status=solver.status_name(answer),
                      statistics={'conflicts':solver.num_conflicts,'branches':solver.num_branches,
                                  'wall_time':solver.wall_time,'user_time':solver.user_time})
        values=list(solver.response_proto.solution)
        if len(values)==2491 and all(type(v) is int and v in (0,1) for v in values):
            vector={'schema':'conway99.rook.full_span_parity.native_vector.v1',
                    'query_preparation_sha256':digest(preparation),'proto_sha256':frozen['proto']['sha256'],
                    'point_sha256':frozen['inputs']['point'][1],'backend_status':result['backend_status'],
                    'values':values,'accepted':False}
            save(directory/'native-vector.json',vector)
            result['native_vector_sha256']=digest(directory/'native-vector.json')
            checkpoint()  # The complete proposal is durable before mathematical replay.
        response=str(solver.response_proto).encode()+b'\n'
        assert len(response)<=LIMITS['maximum_response_bytes']
        (directory/'response.txt').write_bytes(response)
        result['response_sha256']=digest(directory/'response.txt')
        if answer in (cp_model.OPTIMAL,cp_model.FEASIBLE):
            assert 'native_vector_sha256' in result
            cut=subject.inspect_assignment(spec,values,subject.inputs())
            cut.update(query_preparation_sha256=digest(preparation),
                       source_point_sha256=frozen['inputs']['point'][1],
                       native_vector_sha256=result['native_vector_sha256'])
            save(directory/'cut.json',cut)
            result.update(status='EXACT_VIOLATED_PARITY_CUT: owner replay passed',cut_sha256=digest(directory/'cut.json'))
        elif answer==cp_model.INFEASIBLE:
            result['status']='UNRESOLVED: native INFEASIBLE without an accepted proof'
        elif answer==cp_model.UNKNOWN:
            result['status']='UNRESOLVED: bounded native search returned UNKNOWN'
        else:
            result['status']='ERROR: MODEL_INVALID or unexpected native status'
        checkpoint()
    except Exception as error:
        result.update(status='ERROR: no accepted cut or exclusion',error=repr(error))
        checkpoint();raise


def run(preparation,directory):
    assert not directory.exists()
    record,frozen,spec=checked_preparation(preparation)
    directory.mkdir(parents=True);started=time.monotonic()
    result={'status':'RUNNING: one owned child','driver_source_sha256':digest(Path(__file__)),
            'query_preparation_sha256':digest(preparation),'model_preparation_sha256':MODEL_PREP_SHA,
            'proto_sha256':frozen['proto']['sha256'],'limits':LIMITS,'production_children':1,
            'retries':0,'case4_excluded':False,'native_INFEASIBLE_certificate_accepted':False}
    save(directory/'result.json',result)
    def timeout(pid,elapsed):
        result.update(status='UNRESOLVED: owned child hard timeout',timeout_pid=pid,
                      timeout_seconds=elapsed,no_partial_child_result_used=True)
        save(directory/'result.json',result)
    process=owned_child([sys.executable,str(Path(__file__).resolve()),'_child','--preparation',str(preparation),
                         '--directory',str(directory)],directory/'child.log',LIMITS['owned_child_seconds'],timeout)
    result['owned_process']=process
    child_path=directory/'child-result.json'
    if not process['timed_out']:
        if process['returncode']==0 and child_path.exists():
            terminal=json.loads(child_path.read_text())
            assert terminal['query_preparation_sha256']==digest(preparation)
            assert terminal['driver_source_sha256']==result['driver_source_sha256']
            assert terminal['proto_sha256']==frozen['proto']['sha256'] and terminal['native_calls']==1
            assert terminal['case4_excluded'] is False
            result['status']=terminal['status'];result['child_result_sha256']=digest(child_path)
        else:result['status']='UNRESOLVED: child error or missing terminal'
    result['saved_artifacts']=[{'path':portable(p),'bytes':p.stat().st_size,'sha256':digest(p)}
                               for p in sorted(directory.iterdir()) if p.is_file() and p.name!='result.json']
    result['elapsed_seconds']=time.monotonic()-started
    save(directory/'result.json',result);return result


def direct_cut_check(spec,vector,cut,gram):
    """Independent integer cut derivation; no call to the subject inspector."""
    values=vector['values'];assert len(values)==2491 and all(type(v) is int and v in (0,1) for v in values)
    choice,h,z,beta=values[:286],values[286:1388],values[1388:2490],values[2490]
    witness=0
    for i,bit in enumerate(choice):
        if bit:witness^=int(spec['basis_original_Gram_witness_hex'][i],16)
    ids=[i for i in range(630) if witness>>i&1]
    coefficients=[0]*1214;rhs=0
    for r in ids:
        rhs+=gram[r][2]
        for a in gram[r][3]:coefficients[a]+=1
    zeros=set(spec['fixed_zero_columns']);kept=spec['kept_original_columns']
    assert [coefficients[a]%2 for a in kept]==h and rhs%2==beta
    assert sum(z)<=1 and all(zj<=hj for zj,hj in zip(z,h))
    den=int(spec['denominator']);nums=list(map(int,spec['point_numerators1214']))
    assert all(nums[a]==0 for a in zeros)
    assert sum(c*n for c,n in zip(coefficients,nums))==rhs*den
    support=[a for a in kept if coefficients[a]%2]
    forbidden=[a for a,hj,zj in zip(kept,h,z) if hj and (int(2*nums[a]>den)^zj)]
    assert support and len(forbidden)%2!=beta
    one=set(forbidden);terms=[[a,1 if a in one else -1] for a in support]
    upper=len(one)-1;deficit=sum(c*nums[a] for a,c in terms)-upper*den
    distance=sum(den-nums[a] if a in one else nums[a] for a in support)
    assert deficit==den-distance>0
    assert cut['original_Gram_row_ids']==ids and cut['full_original1214_integer_coefficients']==coefficients
    assert cut['original_Gram_rhs_sum']==rhs and cut['parity_rhs']==beta
    assert cut['active_original_support']==support and cut['forbidden_ones']==forbidden
    assert cut['removed_proved_zero_odd_columns']==sorted(a for a in zeros if coefficients[a]%2)
    assert cut['inequality']=={'terms':terms,'upper':upper}
    assert int(cut['exact_deficit_numerator'])==deficit and int(cut['point_denominator'])==den
    return {'original_Gram_rows':len(ids),'full_integer_coefficients_checked':1214,
            'support_size':len(support),'forbidden_ones':len(forbidden),
            'deficit_numerator':str(deficit),'denominator':str(den)}


def replay(preparation,directory,output):
    assert not output.exists();started=time.monotonic()
    record,frozen,spec=checked_preparation(preparation)
    result=json.loads((directory/'result.json').read_text())
    assert result['driver_source_sha256']==digest(Path(__file__)) and result['limits']==LIMITS
    assert result['query_preparation_sha256']==digest(preparation) and result['model_preparation_sha256']==MODEL_PREP_SHA
    assert result['proto_sha256']==frozen['proto']['sha256'] and result['production_children']==1 and result['retries']==0
    assert result['case4_excluded'] is False and result['native_INFEASIBLE_certificate_accepted'] is False
    process=result['owned_process'];assert process['child_reaped'] and process['requested_wall_seconds']==120
    assert digest(ROOT/process['log'])==process['log_sha256']
    for entry in result['saved_artifacts']:
        path=ROOT/entry['path'];assert path.stat().st_size==entry['bytes'] and digest(path)==entry['sha256']
    arithmetic=None
    if process['timed_out']:
        assert result['status'].startswith('UNRESOLVED:') and result['no_partial_child_result_used']
        assert process['UNKNOWN_persisted_before_kill']
    elif 'child_result_sha256' in result:
        assert process['returncode']==0 and digest(directory/'child-result.json')==result['child_result_sha256']
        terminal=json.loads((directory/'child-result.json').read_text())
        assert terminal['status']==result['status'] and terminal['native_calls']==1 and terminal['parameters']==record['parameters']
        assert terminal['query_preparation_sha256']==digest(preparation)
        if terminal['status'].startswith('EXACT_VIOLATED_PARITY_CUT:'):
            vector=bound_json(portable(directory/'native-vector.json'),terminal['native_vector_sha256'])
            cut=bound_json(portable(directory/'cut.json'),terminal['cut_sha256'])
            assert vector['query_preparation_sha256']==cut['query_preparation_sha256']==digest(preparation)
            assert vector['proto_sha256']==frozen['proto']['sha256']
            assert vector['point_sha256']==cut['source_point_sha256']==frozen['inputs']['point'][1]
            assert cut['native_vector_sha256']==terminal['native_vector_sha256']
            subject=load_subject()
            from ortools.sat import cp_model_pb2
            proto=cp_model_pb2.CpModelProto();proto.ParseFromString((ROOT/frozen['proto']['path']).read_bytes())
            assert subject.evaluate_proto(proto,vector['values'])
            native=bound_json(*frozen['inputs']['native'])
            arithmetic=direct_cut_check(spec,vector,cut,native['primary_inventory']['Gram_rows'])
    else:assert result['status'].startswith('UNRESOLVED:')
    assert time.monotonic()-started<LIMITS['cold_seconds']
    report={'status':'PASS: bounded outcome bindings and direct original-Gram cut replay',
            'driver_source_sha256':digest(Path(__file__)),'query_preparation_sha256':digest(preparation),
            'result_sha256':digest(directory/'result.json'),'terminal_status':result['status'],
            'cut_arithmetic':arithmetic,'optimizer_calls':0,'native_model_rebuilds':0,
            'case4_excluded':False,'native_INFEASIBLE_certificate_accepted':False,'seconds':time.monotonic()-started}
    save(output,report);return report


def main():
    if not __debug__:raise RuntimeError('assertions are required')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','run','_child','replay'))
    parser.add_argument('--preparation',type=Path);parser.add_argument('--directory',type=Path)
    parser.add_argument('--output',type=Path);args=parser.parse_args()
    if args.mode=='prepare':result=prepare(args.output.resolve())
    elif args.mode=='run':result=run(args.preparation.resolve(),args.directory.resolve())
    elif args.mode=='_child':child(args.preparation.resolve(),args.directory.resolve());return
    else:result=replay(args.preparation.resolve(),args.directory.resolve(),args.output.resolve())
    print(json.dumps({'status':result['status'],'seconds':result.get('seconds',result.get('elapsed_seconds'))}),flush=True)


if __name__=='__main__':main()
