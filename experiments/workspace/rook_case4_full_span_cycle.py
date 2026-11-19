"""Bounded append-only LP / exact-point / full-span parity continuation.

Preparation is separate. Imported numerical and exact LP kernels are unchanged.
No source-file, old result, proof, row or variable domain is mutated.
"""
import argparse
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import rook_case4_parity_cycle_v4 as previous
import rook_case4_full_span_parity_dynamic as separator

ROOT,LOG=previous.ROOT,previous.LOGS
exact=previous.exact
save,read,ref,checked=previous.save,previous.read_record,previous.record_ref,previous.checked_ref
sha,canonical=exact.sha,exact.canonical
SOURCES={
 'previous':('experiments/workspace/rook_case4_parity_cycle_v4.py','345e091ef71dde96b3423773d5315b8733c275f0af142ab0f88ac03570ca263e'),
 'separator':('experiments/workspace/rook_case4_full_span_parity_dynamic.py','ce200386980da082fef8370956f7a546b12e1c9e8979288b5d48a0843a924dd8'),
}
INPUTS={
 'prior_terminal':(LOG+'rook-case4-parity-discovery-cycle-run02/result.json','fd0737a2c47664b52cf8cd48024a10e6936b3110f3cd2c8344b4081ff424adea'),
 'prior_bindings':(LOG+'rook-case4-parity-discovery-cycle-run02-bindings.json','164f8c09048b9c9502d45cff407b0a78102b87aa9524bcc46e0d92b3b28590ca'),
 'new_cut':(LOG+'rook-case4-full-span-parity-query-run01/cut.json','f9080c52f570d3a9eabf461eabd6ef4dde6ac2fc2454ecc75367fe658d9e3fd7'),
 'new_cut_cold':(LOG+'rook-case4-full-span-parity-query-run01-cold.json','28cc396064b7e6ae5e7ad0ac401de0929aa3ea25b20d88483a1020abc79d620c'),
 'new_cut_terminal':(LOG+'rook-case4-full-span-parity-query-run01/result.json','2e1db8a9aba8fd991bdfeaa050e9d4099a6c83cc8a78842fcc8c4567a573f395'),
 'native_preflight':(LOG+'rook-case4-parity-cycle-preflight04.json','d3827408d08dd443093cba2d0c19e250391c142c6e97a4f04f316567c04bf264'),
 'containment':(LOG+'rook-case4-full-span-cover-containment01.json','983e6c1d30c71476c817fdf0935a81e7f0286b590bc90ce633ab52c6386b8117'),
}
LIMITS={
 'LP_rounds':4,'separations':4,'seed_cuts':4,'initial_point_accepted_cuts':3,
 'cuts_per_separation':1,'maximum_cuts':8,
 'numerical_seconds':180,'exact_seconds':60,'exact_cold_seconds':60,
 'cumulative_native_LP_seconds':120,'native_LP_calls_per_round':30,'maximum_native_LP_calls':120,
 'native_separation_seconds':60,'separation_hard_seconds':120,'separation_cold_seconds':10,
 'maximum_declared_child_seconds':1720,'whole_cycle_hard_seconds':1860,
 'maximum_dynamic_exact_dimension':512,'maximum_exact_output_bits':4096,
 'threads':1,'automatic_retries':0,'maximum_separator_artifact_bytes':64 << 20,
}
REUSED=['numeric_stage','numeric_records','finite_bound','inspect_point','exact_stage',
        'replay_numeric','exact_cold','load_matrix']


def bindings():
    for name,(path,digest) in SOURCES.items():
        assert sha((ROOT/path).read_bytes())==digest,name
    assert Path(previous.__file__).resolve()==ROOT/SOURCES['previous'][0]
    assert Path(separator.__file__).resolve()==ROOT/SOURCES['separator'][0]
    for name in REUSED:
        assert Path(getattr(previous,name).__code__.co_filename).resolve()==Path(previous.__file__).resolve()
    return json.loads(json.dumps({'controller_sha256':sha(Path(__file__).read_bytes()),
        'sources':SOURCES,'inputs':INPUTS,'reused_LP_bindings':previous.source_bindings(),
        'separator_bindings':separator.bindings(),'unchanged_LP_functions':REUSED}))


def input_ref(name):
    path,digest=INPUTS[name];return {'path':path,'sha256':digest}


def bound(name):return checked(input_ref(name))


def seed():
    prior=bound('prior_terminal');audit=bound('prior_bindings')
    assert audit['status'].startswith('PASS:') and audit['result']==input_ref('prior_terminal')
    assert audit['registered_cuts']==audit['latest_point_accepted_cut_count']==3
    assert prior['registered_cut_count']==prior['latest_exact_point_accepted_cut_count']==3
    registry=list(prior['registry']);assert len(registry)==3
    point=prior['latest_exact_point']
    spec,native=separator.point_specification(point,registry,3,time.monotonic()+60)
    cut,cold,terminal=bound('new_cut'),bound('new_cut_cold'),bound('new_cut_terminal')
    assert cold['status'].startswith('PASS:') and cold['result_sha256']==INPUTS['new_cut_terminal'][1]
    assert cold['cut_arithmetic']['support_size']==42 and cold['cut_arithmetic']['forbidden_ones']==0
    child=checked({'path':str(Path(INPUTS['new_cut_terminal'][0]).parent/'child-result.json'),
                   'sha256':terminal['child_result_sha256']})
    assert child['cut_sha256']==INPUTS['new_cut'][1]
    assert cut['source_point_sha256']==point['candidate']['sha256']
    assert cut['status']=='EXACT_VIOLATED_PARITY_CUT' and cut['case4_excluded'] is False
    normalized=separator.normalize_cut(cut,spec,native,time.monotonic()+10)
    entry={'certificate':normalized,'row_key':exact.row_key(normalized['inequality']),
           'source_point':point,'full_span_seed_cut':input_ref('new_cut'),
           'full_span_seed_cold':input_ref('new_cut_cold')}
    assert entry['row_key'] not in {x['row_key'] for x in registry}
    registry.append(entry)
    containment=bound('containment')
    assert containment['status'].startswith('COMPLETE:')
    assert containment['inputs']['cut']==list(INPUTS['new_cut'])
    assert not containment['upper_at_most_two_witnesses']
    cold_point=checked(point['cold']);state=checked(cold_point['state'])
    numeric=checked(state['numerical_result'])
    assert numeric['registry_sha256']==sha(canonical(registry[:3])) and numeric['complete']
    carried=numeric['carried_covers_after']
    assert carried==sorted(set(carried)) and all(previous.NATIVE_ROWS<=r<previous.COVER_END for r in carried)
    return registry,point,carried,state['numerical_result'],spec


def definition():
    registry,point,carried,numeric_ref,spec=seed()
    old=bound('native_preflight');assert old['status'].startswith('PASS:') and old['optimizer_calls']==0
    assert old['source_bindings']==previous.source_bindings()
    assert previous.PREFIX_ROWS==167115 and previous.PREFIX_NNZ==10769496
    assert previous.SELECTORS==1102 and previous.VARIABLES==1103
    assert previous.LIMITS['cumulative_native_seconds']==LIMITS['cumulative_native_LP_seconds']
    assert previous.LIMITS['native_calls_per_round']==LIMITS['native_LP_calls_per_round']
    assert previous.LIMITS['numerical_phase_seconds']==LIMITS['numerical_seconds']
    assert previous.LIMITS['exact_seconds']==previous.LIMITS['exact_cold_seconds']==60
    assert previous.LIMITS['maximum_dynamic_exact_dimension']==512
    assert LIMITS['maximum_declared_child_seconds']==4*(180+60+60+120+10)
    return {'bindings':bindings(),'limits':LIMITS,'immutable_extended_prefix_rows':previous.PREFIX_ROWS,
            'immutable_prefix_nonzeros':previous.PREFIX_NNZ,'variables':previous.VARIABLES,
            'positive_selector_domain':previous.SELECTORS,'initial_rows':167119,
            'initial_nonzeros':previous.PREFIX_NNZ+sum(len(e['certificate']['inequality']['terms']) for e in registry),
            'maximum_rows':167123,'maximum_nonzeros':previous.PREFIX_NNZ+1102*8,
            'seed_registry_sha256':sha(canonical(registry)),'initial_point':point,
            'initial_point_accepted_cuts':3,'initial_carried_covers':carried,
            'carried_covers_source':numeric_ref,'native_preflight':input_ref('native_preflight'),
            'maximum_declared_native_seconds':120+4*60,
            'whole_span_INFEASIBLE_is_uncertified':True,
            'point_prefix_may_precede_a_later_proved_rejecting_cut':True,
            'only_original_coordinate_Gram_parity_cuts_appended':True,
            'complete_old_rows_and_original_coordinate_checks_retained':True,
            'basis_aliases_and_fixed_values_are_proposals_only':True}


def prepare(output):
    assert not output.exists();started=time.monotonic();value=definition()
    registry,point,carried,numeric_ref,spec=seed()
    frozen,template,native=separator.fixed_domain()
    for name in ['weights','penalties','nearest_bits','denominator','point_numerators1214','weighted_upper']:
        assert spec[name]==template[name],('known-point transport',name)
    report={'status':'PREPARED: four-round bounded full-span parity/LP continuation; no query',
            'definition':value,'definition_sha256':sha(canonical(value)),
            'seed_registry':registry,'controls':separator.controls(),
            'known_point_dynamic_spec_matches_frozen_weighted_coefficients':True,
            'no_case_span_elimination_no_old_family_scan_no_optimizer':True,
            'seconds':time.monotonic()-started}
    save(output,report);return report


def checked_preparation(path):
    prep=read(path);value=definition()
    assert prep['definition']==value and prep['definition_sha256']==sha(canonical(value))
    assert prep['seed_registry']==seed()[0] and prep['status'].startswith('PREPARED:')
    return prep


def preflight(preparation,output):
    assert not output.exists();started=time.monotonic();deadline=started+60
    prep=checked_preparation(preparation);data=previous.domain(deadline)
    old,arrays,pool=previous.load_matrix(data,prep['seed_registry'],deadline)
    assert len(arrays['row_lower'])==prep['definition']['initial_rows']==167119
    assert len(arrays['coefficients'])==prep['definition']['initial_nonzeros']==10769728
    runtime=old.runtime_binding();assert runtime==bound('native_preflight')['runtime_binding']
    appended=[]
    for i,entry in enumerate(prep['seed_registry']):
        r=167115+i;terms=exact.row_terms(arrays,r)
        original=[[int(arrays['original_column_ids'][j]),c] for j,c in terms]
        assert original==entry['certificate']['inequality']['terms']
        assert int(arrays['row_upper'][r])==entry['certificate']['inequality']['upper']
        appended.append({'row':r,'terms':original,'lower':int(arrays['row_lower'][r]),'upper':int(arrays['row_upper'][r])})
    exact.tick(deadline)
    report={'status':'PASS: cached167115-row prefix plus four exact seed cuts',
            'preparation':ref(preparation),'bindings':bindings(),
            'definition_sha256':prep['definition_sha256'],'matrix_binding':exact.matrix_binding(arrays),
            'rows':167119,'nonzeros':10769728,'appended_rows':appended,
            'runtime_binding':runtime,'optimizer_calls':0,'native_model_transports':0,
            'original_cover_supports_reconstructed':False,'seconds':time.monotonic()-started}
    save(output,report);return report


def checked_flight(preparation,preflight_path):
    prep=checked_preparation(preparation);flight=read(preflight_path)
    assert flight['preparation']==ref(preparation) and flight['bindings']==bindings()
    assert flight['definition_sha256']==prep['definition_sha256'] and flight['status'].startswith('PASS:')
    assert flight['optimizer_calls']==0 and flight['native_model_transports']==0
    return prep,flight


def check_envelope(path):
    state=read(path);context=state['full_span_continuation']
    assert context['bindings']==bindings() and context['limits']==LIMITS
    prep,flight=checked(context['preparation']),checked(context['preflight'])
    assert prep['definition']['bindings']==bindings() and prep['definition']['limits']==LIMITS
    assert prep['definition_sha256']==sha(canonical(prep['definition']))
    assert flight['preparation']==context['preparation'] and flight['bindings']==bindings()
    assert flight['definition_sha256']==prep['definition_sha256'] and flight['status'].startswith('PASS:')
    assert state['source_bindings']==previous.source_bindings() and state['limits']==previous.LIMITS
    assert state['native_preflight']==input_ref('native_preflight')
    assert 4<=len(state['cuts'])<=8 and state['cuts'][:4]==prep['seed_registry']
    count=context['point_accepted_cut_count']
    assert 3<=count<=len(state['cuts'])
    separator.accepted_point(state['point'],state['cuts'],count)
    for entry in state['cuts'][4:]:
        proof=checked(entry['full_span_proof_record'])
        assert proof['status']=='PASS: full-span terminal and direct original-Gram cut replay'
        assert proof['bindings']==separator.bindings()
        assert proof['registry_addition']=={k:v for k,v in entry.items() if k!='full_span_proof_record'}
    return state


def state_payload(point,registry,native_seconds,carried,preparation,preflight_path,accepted_count):
    state=previous.state_payload(point,registry,native_seconds,carried,0)
    state['native_preflight']=input_ref('native_preflight')
    state['full_span_continuation']={'bindings':bindings(),'limits':LIMITS,
        'preparation':ref(preparation),'preflight':ref(preflight_path),'point_accepted_cut_count':accepted_count}
    return state


def owned(mode,state_path,directory,seconds):
    directory.mkdir(parents=True,exist_ok=True);label=mode.removeprefix('_');started=time.monotonic()
    with (directory/(label+'.stdout.log')).open('xb') as out,(directory/(label+'.stderr.log')).open('xb') as err:
        try:
            process=subprocess.run([sys.executable,str(Path(__file__).resolve()),mode,'--state',str(state_path.resolve()),
                                    '--directory',str(directory.resolve())],stdout=out,stderr=err,timeout=seconds,check=False)
            result={'exit_code':process.returncode,'hard_timeout':False}
        except subprocess.TimeoutExpired:result={'exit_code':None,'hard_timeout':True}
    result.update(mode=mode,state=ref(state_path),hard_seconds=seconds,seconds=time.monotonic()-started,
                  artifacts=previous.stage_files(directory))
    return result


def stage_ok(record):return not record['hard_timeout'] and record['exit_code']==0


def controller(preparation,preflight_path,directory):
    started=time.monotonic();deadline=started+LIMITS['whole_cycle_hard_seconds']-5
    prep,flight=checked_flight(preparation,preflight_path)
    registry=list(prep['seed_registry']);point=prep['definition']['initial_point'];accepted_count=3
    nums,den=previous.point_data(point);key=exact.point_key(nums,den);seen={key}
    carried=list(prep['definition']['initial_carried_covers'])
    result={'status':'RUNNING','bindings':bindings(),'limits':LIMITS,'preparation':ref(preparation),
            'preflight':ref(preflight_path),'registry':registry,'stages':[],'LP_rounds':0,'separations':0,
            'native_LP_calls':0,'native_LP_seconds':0.0,'native_separation_calls':0,'native_separation_seconds':0.0,
            'point_history':[{'point':point,'point_key':key,'accepted_cut_count':3,'accepted_extended_rows':167118}],
            'latest_exact_point':point,'latest_exact_point_accepted_cut_count':3,
            'latest_exact_point_accepted_extended_rows':167118,'later_cuts_not_satisfied_by_latest_point':1,
            'case4_exclusion_verified':False,'exact_zero_face_found':False,'whole_graph_problem_resolved':False,
            'parity_span_exhaustion_certified':False}
    target=directory/'result.json';save(target,result)
    try:
        for round_id in range(4):
            exact.tick(deadline)
            if result['native_LP_seconds']>=120:
                result['status']='UNRESOLVED: cumulative native LP budget reached';break
            state=state_payload(point,registry,result['native_LP_seconds'],carried,preparation,preflight_path,accepted_count)
            state_path=directory/f'state-numeric-{round_id:02d}.json';save(state_path,state)
            numeric_dir=directory/f'numeric-{round_id:02d}'
            record=owned('_numeric',state_path,numeric_dir,180)
            result['stages'].append(record);result['LP_rounds']+=1
            numerical=read(numeric_dir/'result.json') if (numeric_dir/'result.json').exists() else None
            if numerical is not None:
                result['native_LP_calls']+=numerical['native_calls'];result['native_LP_seconds']+=numerical['native_seconds']
            save(target,result)
            assert result['native_LP_calls']<=120
            if not stage_ok(record) or numerical is None or not numerical['complete'] or not numerical['iterations']:
                result['status']='UNRESOLVED: numerical stage incomplete; no retry';break
            exact_state=dict(state,numerical_result=ref(numeric_dir/'result.json'))
            exact_path=directory/f'state-exact-{round_id:02d}.json';save(exact_path,exact_state)
            exact_dir=directory/f'exact-{round_id:02d}'
            record=owned('_exact',exact_path,exact_dir,60);result['stages'].append(record);save(target,result)
            if not stage_ok(record) or not (exact_dir/'result.json').exists():
                result['status']='UNRESOLVED: exact reconstruction incomplete';break
            outcome=read(exact_dir/'result.json')
            record=owned('_exact_cold',exact_path,exact_dir,60);result['stages'].append(record);save(target,result)
            if not stage_ok(record) or not (exact_dir/'cold.json').exists():
                result['status']='UNRESOLVED: exact cold replay incomplete';break
            cold=read(exact_dir/'cold.json')
            assert cold['status'].startswith('PASS:') and cold['result']==ref(exact_dir/'result.json')
            if outcome['exact_certificate_found']:
                assert cold['exact_certificate_replayed']
                result['exact_certificate']=outcome['certificate'];result['exact_certificate_cold']=ref(exact_dir/'cold.json')
                result['case4_exclusion_verified']=cold['kind']=='exact_infeasibility'
                result['exact_zero_face_found']=cold['kind']=='exact_zero_face'
                result['status']='EXACT: case4 relaxation infeasible' if result['case4_exclusion_verified'] else 'EXACT: new zero face; domain unchanged'
                break
            if not outcome['exact_point_found'] or not cold['exact_point_replayed']:
                result['status']='UNRESOLVED: exact basis proposal failed full acceptance';break
            point={'candidate':outcome['candidate'],'cold':ref(exact_dir/'cold.json')}
            accepted_count=len(registry);nums,den=separator.accepted_point(point,registry,accepted_count)
            key=exact.point_key(nums,den)
            result.update(latest_exact_point=point,latest_exact_point_accepted_cut_count=accepted_count,
                          latest_exact_point_accepted_extended_rows=167115+accepted_count,
                          later_cuts_not_satisfied_by_latest_point=0)
            if key in seen:
                result['status']='UNRESOLVED: repeated accepted point; separator not repeated';break
            seen.add(key);result['point_history'].append({'point':point,'point_key':key,'accepted_cut_count':accepted_count,
                                                         'accepted_extended_rows':167115+accepted_count})
            carried=numerical['carried_covers_after'];save(target,result)
            separation_state=state_payload(point,registry,result['native_LP_seconds'],carried,preparation,preflight_path,accepted_count)
            separation_path=directory/f'state-separation-{round_id:02d}.json';save(separation_path,separation_state)
            separation_dir=directory/f'separation-{round_id:02d}'
            record=owned('_separate',separation_path,separation_dir,120)
            result['stages'].append(record);result['separations']+=1
            proposal=read(separation_dir/'result.json') if (separation_dir/'result.json').exists() else None
            if proposal is not None:
                result['native_separation_calls']+=proposal['native_calls']
                result['native_separation_seconds']+=proposal['native_seconds']
            save(target,result)
            assert result['native_separation_calls']<=4
            if not stage_ok(record) or proposal is None or proposal['native_calls']!=1:
                result['status']='UNRESOLVED: separator incomplete or resource-refused; no retry';break
            if sum(p.stat().st_size for p in separation_dir.iterdir() if p.is_file())>LIMITS['maximum_separator_artifact_bytes']:
                result['status']='UNRESOLVED: separator artifact limit; proposal retained';break
            record=owned('_separation_cold',separation_path,separation_dir,10)
            result['stages'].append(record);save(target,result)
            if not stage_ok(record) or not (separation_dir/'proof.json').exists():
                result['status']='UNRESOLVED: separate cut proof unfinished';break
            proof=read(separation_dir/'proof.json')
            assert proof['status']=='PASS: full-span terminal and direct original-Gram cut replay'
            assert proof['state']==ref(separation_path)
            if proof['registry_addition'] is None:
                result['status']='UNRESOLVED: no exact cut from bounded full-span call';break
            entry=dict(proof['registry_addition'],full_span_proof_record=ref(separation_dir/'proof.json'))
            assert entry['row_key'] not in {old['row_key'] for old in registry}
            registry.append(entry);assert len(registry)<=8
            result['registry']=registry;result['later_cuts_not_satisfied_by_latest_point']=len(registry)-accepted_count
            save(target,result)
            if round_id==3:
                result['status']='UNRESOLVED: round cap; last checked rejecting cut retained';break
        else:result['status']='UNRESOLVED: declared cycle completed'
    except Exception as error:
        result.update(status='UNRESOLVED: controller error; completed records retained',
                      error_type=type(error).__name__,reason=str(error))
    finally:
        result['seconds']=time.monotonic()-started
        result['source_and_state_artifacts']=[ref(p) for p in sorted(directory.glob('state-*.json'))]
        result['registered_cut_count']=len(registry);result['registered_extended_rows']=167115+len(registry)
        save(target,result)
    return result


def run(preparation,preflight_path,directory):
    assert not directory.exists();directory.mkdir(parents=True);started=time.monotonic()
    with (directory/'controller.stdout.log').open('xb') as out,(directory/'controller.stderr.log').open('xb') as err:
        process=subprocess.Popen([sys.executable,str(Path(__file__).resolve()),'_controller',
            '--preparation',str(preparation.resolve()),'--preflight',str(preflight_path.resolve()),
            '--directory',str(directory.resolve())],stdout=out,stderr=err,start_new_session=True)
        timeout=False
        try:code=process.wait(timeout=LIMITS['whole_cycle_hard_seconds'])
        except subprocess.TimeoutExpired:
            timeout=True;os.killpg(process.pid,signal.SIGKILL);code=process.wait()
        except BaseException:
            if process.poll() is None:os.killpg(process.pid,signal.SIGKILL)
            process.wait();raise
    report={'status':'UNKNOWN: whole-cycle guard' if timeout else 'UNKNOWN: controller error' if code else 'owned full-span cycle terminated',
            'bindings':bindings(),'preparation':ref(preparation),'preflight':ref(preflight_path),
            'hard_timeout':timeout,'exit_code':code,'automatic_retries':0,
            'hard_seconds':LIMITS['whole_cycle_hard_seconds'],'seconds':time.monotonic()-started}
    if (directory/'result.json').exists():report['result']=ref(directory/'result.json')
    save(directory/'supervisor.json',report);return report


def verify(preparation,preflight_path,directory,output):
    """Bind saved proof/point chronology; no repeated optimizer or arithmetic scan."""
    assert not output.exists();started=time.monotonic();checked_flight(preparation,preflight_path)
    supervisor=read(directory/'supervisor.json')
    assert supervisor['bindings']==bindings() and supervisor['preparation']==ref(preparation)
    assert supervisor['preflight']==ref(preflight_path) and supervisor['hard_seconds']==1860
    if 'result' not in supervisor:
        report={'status':'PASS: supervisor binding; no complete controller result',
                'bindings':bindings(),'supervisor':ref(directory/'supervisor.json'),'no_mathematical_outcome_claimed':True}
        save(output,report);return report
    result=checked(supervisor['result']);registry=result['registry']
    assert result['bindings']==bindings() and result['limits']==LIMITS
    assert registry[:4]==seed()[0] and 4<=len(registry)<=8
    assert result['LP_rounds']<=4 and result['separations']<=4 and result['native_LP_calls']<=120
    assert result['native_separation_calls']<=4
    hard={'_numeric':180,'_exact':60,'_exact_cold':60,'_separate':120,'_separation_cold':10}
    modes=[stage['mode'] for stage in result['stages']]
    assert modes.count('_numeric')==result['LP_rounds'] and modes.count('_separate')==result['separations']
    files=0
    for stage in result['stages']:
        state=check_envelope(ROOT/stage['state']['path'])
        assert ref(ROOT/stage['state']['path'])==stage['state']
        assert state['cuts']==registry[:len(state['cuts'])] and stage['hard_seconds']==hard[stage['mode']]
        for artifact in stage['artifacts']:
            assert sha((ROOT/artifact['path']).read_bytes())==artifact['sha256'];files+=1
    for entry in registry[4:]:
        proof=checked(entry['full_span_proof_record'])
        assert proof['bindings']==separator.bindings() and proof['registry_addition']=={k:v for k,v in entry.items() if k!='full_span_proof_record'}
        assert proof['status']=='PASS: full-span terminal and direct original-Gram cut replay'
    for state_ref in result.get('source_and_state_artifacts',[]):checked(state_ref)
    seen=set();assert len(result['point_history'])<=5
    for item in result['point_history']:
        count=item['accepted_cut_count'];nums,den=separator.accepted_point(item['point'],registry,count)
        key=exact.point_key(nums,den)
        assert key==item['point_key'] and key not in seen;seen.add(key)
        assert item['accepted_extended_rows']==167115+count
    count=result['latest_exact_point_accepted_cut_count']
    separator.accepted_point(result['latest_exact_point'],registry,count)
    if result['case4_exclusion_verified'] or result['exact_zero_face_found']:
        cold=checked(result['exact_certificate_cold']);assert cold['exact_certificate_replayed']
        assert result['case4_exclusion_verified']==(cold['kind']=='exact_infeasibility')
        assert result['exact_zero_face_found']==(cold['kind']=='exact_zero_face')
    report={'status':'PASS: full-span cycle bindings and exact point-prefix ancestry',
            'bindings':bindings(),'supervisor':ref(directory/'supervisor.json'),'result':supervisor['result'],
            'stage_artifacts_bound':files,'registered_cuts':len(registry),'latest_point_accepted_cut_count':count,
            'later_registered_cuts':len(registry)-count,'optimizer_or_span_search_or_exact_solve_repeated':False,
            'parity_span_exhaustion_certified':False,'seconds':time.monotonic()-started}
    save(output,report);return report


def main():
    if not __debug__:raise RuntimeError('assertions are required')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','preflight','run','verify','_controller','_numeric','_exact','_exact_cold','_separate','_separation_cold'))
    for name in ('preparation','preflight','state','directory','output'):parser.add_argument('--'+name,type=Path)
    args=parser.parse_args()
    if args.mode=='prepare':result=prepare(args.output)
    elif args.mode=='preflight':result=preflight(args.preparation,args.output)
    elif args.mode=='run':result=run(args.preparation,args.preflight,args.directory)
    elif args.mode=='verify':result=verify(args.preparation,args.preflight,args.directory,args.output)
    elif args.mode=='_controller':result=controller(args.preparation,args.preflight,args.directory)
    elif args.mode=='_separate':result=separator.separate(args.state,args.directory,check_envelope)
    elif args.mode=='_separation_cold':result=separator.replay(args.state,args.directory,check_envelope)
    else:
        check_envelope(args.state)
        result=getattr(previous,{'_numeric':'numeric_stage','_exact':'exact_stage','_exact_cold':'exact_cold'}[args.mode])(args.state,args.directory)
    print(json.dumps({'status':result['status'],'seconds':result.get('seconds')}),flush=True)


if __name__=='__main__':main()
