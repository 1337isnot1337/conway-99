"""Bounded transportation continuation from99 independently certified zeros.

This is a new one-stage closure on the proven current face. The unseeded
two-stage source/results remain unchanged. All cut and terminal-flow algebra
is reused from the frozen helper; every external zero has an exact proof.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import time

import rook_case4_transportation_faces as original
import rook_case4_transportation_seed as seeds

ROOT=Path(__file__).resolve().parents[2]
ORIGINAL_SHA='c791b50870e68933a18af5ff0e59d3f9dff34088774a323299da326953d00206'
SEED_SOURCE_SHA='9eedacb4b62db8ad7058e291d04f83141fca306971ed278a58548ead4cd1e8a1'
SEED_CERT='experiments/logs/grids-and-triangles/rook-case4-transportation-seed-certificate.json'
SEED_CERT_SHA='64d8e375280bc067097913de2dd6e2995c19de2a4807f63cecdcd80b811a85cf'
ORIGINAL_PREP='experiments/logs/grids-and-triangles/rook-case4-transportation-faces-preparation01'
ORIGINAL_PREP_SHA='ccebde239de30b464f3f0d968ea4ff665cd75d92960005b38ac0ce3ddc467fd2'
MODEL_RAW_SHA='5d43970be8436fc51bef7a6eedec74e886b8e81f46f795d0ea3bd0b43d28ae91'
MODE='Gram_triple_and_unit_box'
LIMITS={'forward_seconds':60,'replay_seconds':60,'initial_certified_zeros':99,
        'maximum_new_zero_columns':1115,'maximum_new_events_including_contradiction':1116,
        'maximum_flow_calls':1116*105,'maximum_augmentations_per_flow':14}
flow=original.flow
digest,canonical,save=original.digest,original.canonical,original.save


def bindings():
    assert digest(Path(original.__file__).read_bytes())==ORIGINAL_SHA
    assert digest(Path(seeds.__file__).read_bytes())==SEED_SOURCE_SHA
    return {'source_sha256':digest(Path(__file__).read_bytes()),
        'original_transportation_source_sha256':ORIGINAL_SHA,
        'pure_flow_source_sha256':original.bindings()['exact_flow_source_sha256'],
        'seed_source_sha256':SEED_SOURCE_SHA,'seed_certificate_sha256':SEED_CERT_SHA,
        'original_preparation_sha256':ORIGINAL_PREP_SHA,'model_raw_sha256':MODEL_RAW_SHA}


def checked_inputs(root):
    source=bindings()
    old_directory=root/ORIGINAL_PREP
    assert digest((old_directory/'preparation.json').read_bytes())==ORIGINAL_PREP_SHA
    prepared,model=original.load_prepared(root,old_directory)
    assert prepared['model_raw_sha256']==MODEL_RAW_SHA
    raw=(root/SEED_CERT).read_bytes()
    assert digest(raw)==SEED_CERT_SHA
    seed=seeds.prove(root)
    assert canonical(seed)==canonical(json.loads(raw))
    assert len(seed['seed_zero_columns'])==99
    return source,model,seed


def seed_state(seed):
    zeros=set(seed['seed_zero_columns'])
    reasons={int(a):reason for a,reason in seed['seed_reasons'].items()}
    assert set(reasons)==zeros and len(zeros)==99
    return zeros,reasons


def definition(model,seed):
    zeros,_=seed_state(seed)
    inventory=[]
    for d in model['domains']:
        cells,capacities=original.projected_state(d,zeros,MODE)
        inventory.append({'projection_id':d['id'],'core_vertex':d['core_vertex'],
            'grid_pair':d['grid_pair'],'margin_total':d['total'],
            'active_supported_cells':len(cells),
            'active_column_occurrences':sum(map(len,cells.values())),
            'zero_capacity_cells':sum(k==0 for k in capacities.values())})
    assert [d['projection_id']for d in inventory]==list(range(105))
    return {'source_bindings':bindings(),'mode':MODE,'full_original_columns':1214,
        'initial_zero_columns':sorted(zeros),'initial_remaining_columns':1115,
        'all35_vertices_and3_grid_pairs_retained':True,'projections':inventory,
        'limits':LIMITS,'feasible_projection_lifting_claimed':False,
        'Gram_only_stage_repeated':False,'optimizer_called':False}


def prepare(root,directory):
    assert not directory.exists()
    started=time.monotonic()
    source,model,seed=checked_inputs(root)
    specification=definition(model,seed)
    directory.mkdir(parents=True)
    report={'status':'prepared exact continuation from99 verified zeros; no case4 flow run',
        'source_bindings':source,'definition':specification,
        'definition_sha256':digest(canonical(specification)),
        'all_external_zero_proofs_replayed':True,
        'literal_empty_cover_unit_proofs':14,'short_Gram_triple_zeros':88,
        'seed_overlap':[352,354,957],'seed_union':99,
        'active_supported_cells':sum(d['active_supported_cells']for d in specification['projections']),
        'active_column_occurrences':sum(d['active_column_occurrences']for d in specification['projections']),
        'flow_run':False,'optimizer_called':False,'seconds':time.monotonic()-started}
    save(directory/'preparation.json',report)
    print(json.dumps({k:v for k,v in report.items()if k!='definition'},indent=2),flush=True)


def load(root,directory):
    prepared=json.loads((directory/'preparation.json').read_text())
    source,model,seed=checked_inputs(root)
    assert prepared['source_bindings']==source
    specification=definition(model,seed)
    assert prepared['definition']==specification
    assert prepared['definition_sha256']==digest(canonical(specification))
    assert prepared['flow_run']is False and prepared['optimizer_called']is False
    return prepared,model,seed


def run(root,directory,output):
    assert not output.exists()
    started=time.monotonic();deadline=started+LIMITS['forward_seconds']
    prepared,model,seed=load(root,directory)
    zeros,reasons=seed_state(seed)
    initial=set(zeros)
    result={'status':'running exact seeded transportation closure','source_bindings':bindings(),
        'preparation_sha256':digest((directory/'preparation.json').read_bytes()),
        'definition_sha256':prepared['definition_sha256'],'limits':LIMITS,'mode':MODE,
        'initial_zero_columns':sorted(initial),'events':[],'zero_columns':sorted(zeros),
        'new_zero_columns':[],'flow_calls':0,'sweeps':0,'terminal_flows':[],
        'complete_fixed_point':False,'contradiction':False,'optimizer_called':False,
        'joint_incidence_feasibility_claimed':False,'cold_replay_required':True}
    save(output,result)
    try:
        for sweep in range(LIMITS['maximum_new_zero_columns']+1):
            flow.tick(deadline)
            before=len(zeros);terminal=[]
            for domain in model['domains']:
                flow.tick(deadline)
                active,capacities=original.projected_state(domain,zeros,MODE)
                solved=flow.transport(domain['row_margins'],domain['column_margins'],capacities,deadline)
                result['flow_calls']+=1
                assert result['flow_calls']<=LIMITS['maximum_flow_calls']
                assert solved['augmentations']<=LIMITS['maximum_augmentations_per_flow']
                cuts=(flow.zero_cuts(domain['row_margins'],domain['column_margins'],capacities,solved['flow'])[0]
                      if solved['feasible']else[solved['infeasible_cut']])
                for cut in cuts:
                    flow.tick(deadline)
                    cells=([cut['cell']]if cut['kind']=='zero_capacity'else cut['incoming_cells'])
                    candidates={a for key in cells for a in active[tuple(key)]}-zeros
                    if cut['rhs']==0 and not candidates:continue
                    event=original.cut_proof(model,domain,MODE,cut,zeros,reasons)
                    index=len(result['events'])
                    result['events'].append(event)
                    assert len(result['events'])<=LIMITS['maximum_new_events_including_contradiction']
                    if event['contradiction']:
                        result['contradiction']=True
                        break
                    for a in event['new_zero_columns']:
                        assert a not in zeros
                        zeros.add(a);reasons[a]={'new_event':index}
                result['zero_columns']=sorted(zeros)
                result['new_zero_columns']=sorted(zeros-initial)
                if cuts:save(output,result)
                if result['contradiction']:break
                terminal.append(original.flow_record(domain['id'],solved))
            result['sweeps']=sweep+1
            if result['contradiction']:break
            if len(zeros)==before:
                result['complete_fixed_point']=True
                result['terminal_flows']=terminal
                break
        assert result['contradiction']or result['complete_fixed_point']
        result['status']=('exact seeded projected contradiction; cold replay required'if result['contradiction']else
            'complete seeded projected zero-face closure; cold replay required')
    except TimeoutError as error:
        result['status']='PARTIAL: bounded seeded closure; checked event prefixes retained'
        result['limit_message']=str(error)
    finally:
        result['zero_columns']=sorted(zeros)
        result['new_zero_columns']=sorted(zeros-initial)
        result['seconds']=time.monotonic()-started
        save(output,result)
    print(json.dumps({k:v for k,v in result.items()if k not in('events','terminal_flows')},indent=2),flush=True)


def replay(root,directory,result_path,output):
    assert not output.exists()
    started=time.monotonic();deadline=started+LIMITS['replay_seconds']
    prepared,model,seed=load(root,directory)
    result=json.loads(result_path.read_text())
    assert result['source_bindings']==bindings()and result['limits']==LIMITS and result['mode']==MODE
    assert result['preparation_sha256']==digest((directory/'preparation.json').read_bytes())
    assert result['definition_sha256']==prepared['definition_sha256']
    assert result['optimizer_called']is False and result['joint_incidence_feasibility_claimed']is False
    assert type(result['flow_calls'])is int and 0<=result['flow_calls']<=LIMITS['maximum_flow_calls']
    assert type(result['sweeps'])is int and 0<=result['sweeps']<=LIMITS['maximum_new_zero_columns']+1
    zeros,reasons=seed_state(seed);initial=set(zeros)
    assert result['initial_zero_columns']==sorted(initial)
    events=result['events']
    assert len(events)<=LIMITS['maximum_new_events_including_contradiction']
    for index,event in enumerate(events):
        flow.tick(deadline)
        pid=event['projection_id']
        assert type(pid)is int and 0<=pid<105 and event['mode']==MODE
        checked=original.cut_proof(model,model['domains'][pid],MODE,event['cut'],zeros,reasons)
        assert checked==event
        if event['contradiction']:assert index==len(events)-1
        else:
            assert event['new_zero_columns']
            for a in event['new_zero_columns']:
                assert a not in zeros
                zeros.add(a);reasons[a]={'new_event':index}
    assert result['contradiction']==bool(events and events[-1]['contradiction'])
    assert result['zero_columns']==sorted(zeros)and result['new_zero_columns']==sorted(zeros-initial)
    assert len(zeros-initial)<=LIMITS['maximum_new_zero_columns']
    terminal=[]
    if result['complete_fixed_point']:
        assert result['sweeps']>=1 and not result['contradiction']
        assert [r['projection_id']for r in result['terminal_flows']]==list(range(105))
        for record in result['terminal_flows']:
            flow.tick(deadline)
            terminal.append(original.verify_flow_record(model['domains'][record['projection_id']],zeros,MODE,record))
    else:assert not result['terminal_flows']
    report={'status':'PASS: external seed, full signed cuts, induction and claimed projected fixed point replayed',
        'source_bindings':bindings(),'preparation_sha256':result['preparation_sha256'],
        'result_sha256':digest(result_path.read_bytes()),'initial_certified_zeros':99,
        'new_zero_columns':sorted(zeros-initial),'zero_columns':sorted(zeros),
        'new_events_checked':len(events),'complete_fixed_point':result['complete_fixed_point'],
        'terminal_projection_checks':terminal,'contradiction':result['contradiction'],
        'case4_exclusion_verified':result['contradiction'],'whole_graph_problem_resolved':False,
        'max_flow_repeated_by_replay':False,'optimizer_called':False,'seconds':time.monotonic()-started}
    save(output,report)
    print(json.dumps({k:v for k,v in report.items()if k!='terminal_projection_checks'},indent=2),flush=True)


def main():
    p=argparse.ArgumentParser(description=__doc__)
    commands=p.add_subparsers(dest='command',required=True)
    for name in ('prepare','preflight','run','replay'):
        c=commands.add_parser(name)
        c.add_argument('--root',type=Path,default=ROOT)
        c.add_argument('--directory',type=Path,required=True)
        if name!='prepare':c.add_argument('--output',type=Path,required=True)
        if name=='replay':c.add_argument('--result',type=Path,required=True)
    a=p.parse_args()
    if a.command=='prepare':prepare(a.root,a.directory)
    elif a.command=='run':run(a.root,a.directory,a.output)
    elif a.command=='replay':replay(a.root,a.directory,a.result,a.output)
    else:
        assert not a.output.exists()
        start=time.monotonic()
        prepared,model,seed=load(a.root,a.directory)
        report={'status':'PASS: full105 projected domains and all99 seed proofs cold-rebuilt; no flow run',
            'source_bindings':bindings(),'preparation_sha256':digest((a.directory/'preparation.json').read_bytes()),
            'definition_sha256':prepared['definition_sha256'],'seed_zero_columns':seed['seed_zero_columns'],
            'flow_run':False,'optimizer_called':False,'seconds':time.monotonic()-start}
        save(a.output,report)
        print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':
    main()
