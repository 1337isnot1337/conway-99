"""Case4 exact transportation-face preparation, closure and proof replay.

Every projection uses literal Gram margins at one core vertex and two of the
three complete nine-point grids. A column containing the vertex maps to one
cell. The first stage uses Gram equations only. The second adds literal triple
capacities, singleton unit boxes and repeated-site Gram bounds. Feasible
projected flows are never claimed to lift to joint attachment incidences.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import time

import rook_transportation_faces as flow

ROOT=Path(__file__).resolve().parents[2]
FLOW_SHA='9990f33f1c21a233668dbcc8de8a35bd5f3468de8c1225942f23a38bbac67741'
NATIVE='experiments/logs/grids-and-triangles/complement-rook-35core-case0004-native-cpsat-model.json'
NATIVE_SHA='a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476'
PRIMARY_SHA='5a6af30f47826df629a3795ceea0a0a91b853cf8149860355ce1bd17ac0094b2'
N,PROJECTIONS=1214,105
MODES=['Gram_only','Gram_triple_and_unit_box']
LIMITS={'forward_seconds':60,'replay_seconds':60,'maximum_zero_events':1214,
        'maximum_records_including_contradiction':1215,
        'maximum_flow_calls':(1214+2)*105,'maximum_augmentations_per_flow':14}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def save(path,value):
    temporary=path.with_name(path.name+'.partial')
    temporary.write_text(json.dumps(value,indent=2)+'\n')
    temporary.replace(path)


def bindings():
    assert digest(Path(flow.__file__).read_bytes())==FLOW_SHA
    return {'wrapper_sha256':digest(Path(__file__).read_bytes()),
            'exact_flow_source_sha256':FLOW_SHA,'native_input_sha256':NATIVE_SHA,
            'primary_inventory_sha256':PRIMARY_SHA}


def build(root):
    source=bindings()
    raw=(root/NATIVE).read_bytes()
    assert digest(raw)==NATIVE_SHA
    native=json.loads(raw)
    inventory=native['primary_inventory']
    assert native['complete'] and digest(canonical(inventory))==PRIMARY_SHA
    assert inventory['primary_variables']==N
    assert inventory['case']['index']==inventory['case']['matching_index']==4
    grams=inventory['Gram_rows']
    assert [(i,j)for i,j,q,s in grams]==[(i,j)for i in range(35)for j in range(i,35)]
    masks=[0]*N
    gram_index={}
    G=[[0]*35 for _ in range(35)]
    for index,(i,j,quota,support)in enumerate(grams):
        assert type(quota)is int and quota>=0 and support==sorted(set(support))
        gram_index[i,j]=index
        G[i][j]=G[j][i]=quota
        if i==j:
            for a in support:masks[a]|=1<<i
    for i,j,q,s in grams:
        assert s==[a for a,h in enumerate(masks)if h>>i&1 and h>>j&1]
    assert all(0<=G[i][i]<=14 for i in range(35))
    groups=[list(range(9*g,9*g+9))for g in range(3)]
    labels=[]
    for h in masks:
        sites=[]
        for group in groups:
            present=[j for j in group if h>>j&1]
            assert len(present)==1
            sites.append(present[0]%9)
        labels.append(sites)
    triples=[]
    triple_index={}
    for index,entry in enumerate(inventory['triple_rows']):
        sites=entry['triple']
        assert sites==sorted(set(sites)) and len(sites)==3
        members=[a for a,h in enumerate(masks)if all(h>>i&1 for i in sites)]
        assert members==entry['members'] and len(members)>1
        triple_index[tuple(sites)]=index
        triples.append([sites,members])
    assert len(triples)==1365 and len(triple_index)==1365
    domains=[]
    counts=Counter()
    for vertex in range(35):
        for left,right in ((0,1),(0,2),(1,2)):
            row_sites,column_sites=groups[left],groups[right]
            r=[G[vertex][j]for j in row_sites]
            c=[G[vertex][j]for j in column_sites]
            assert sum(r)==sum(c)==G[vertex][vertex]
            cells={}
            for a,h in enumerate(masks):
                if h>>vertex&1:
                    cells.setdefault((labels[a][left],labels[a][right]),[]).append(a)
            packed=[]
            for (u,v),members in sorted(cells.items()):
                sites=sorted(set((vertex,row_sites[u],column_sites[v])))
                assert len(sites)in(2,3)
                if len(sites)==2:
                    index=gram_index[tuple(sites)]
                    assert grams[index][3]==members
                    bound={'kind':'Gram','index':index,'upper':grams[index][2]}
                elif len(members)==1:
                    bound={'kind':'unit_box','index':members[0],'upper':1}
                else:
                    index=triple_index[tuple(sites)]
                    assert triples[index][1]==members
                    bound={'kind':'triple','index':index,'upper':1}
                counts['cells_with_'+bound['kind']+'_capacity']+=1
                packed.append({'row':u,'column':v,'members':members,'capacity_proof':bound})
            union=[a for cell in packed for a in cell['members']]
            expected=grams[gram_index[vertex,vertex]][3]
            assert len(union)==len(set(union)) and sorted(union)==expected
            row_ids=[gram_index[min(vertex,j),max(vertex,j)]for j in row_sites]
            column_ids=[gram_index[min(vertex,j),max(vertex,j)]for j in column_sites]
            for u,index in enumerate(row_ids):
                assert sorted(a for cell in packed if cell['row']==u for a in cell['members'])==grams[index][3]
            for v,index in enumerate(column_ids):
                assert sorted(a for cell in packed if cell['column']==v for a in cell['members'])==grams[index][3]
            domains.append({'id':len(domains),'core_vertex':vertex,'grid_pair':[left,right],
                'row_sites':row_sites,'column_sites':column_sites,
                'row_margins':r,'column_margins':c,'total':sum(r),
                'row_Gram_ids':row_ids,'column_Gram_ids':column_ids,'cells':packed})
            counts['projected_column_occurrences']+=len(union)
            counts['full_supported_cells']+=len(packed)
            counts['zero_total_projections']+=sum(r)==0
    assert len(domains)==PROJECTIONS
    return {'schema':'conway99.case4.transportation.faces.v1','source_bindings':source,
        'native_input_path':NATIVE,'case_index':4,'full_columns':N,
        'core_vertices':35,'complete_grid_groups':groups,
        'every_column_meets_each_grid_once':True,'column_masks':masks,
        'Gram_rows':grams,'triple_rows':triples,'domains':domains,
        'domain_counts':dict(counts),'stages':MODES,'initial_zero_premises':[],
        'Gram_stage_uses_no_upper_boxes_or_triple_capacities':True,
        'capacitated_stage_uses_only_literal_Gram_triple_and_unit_box_bounds':True,
        'projection_lifting_claimed':False,'limits':LIMITS}


def projected_state(domain,zeros,mode):
    assert mode in MODES
    cells={}
    capacities={}
    for cell in domain['cells']:
        active=[a for a in cell['members']if a not in zeros]
        if not active:continue
        key=(cell['row'],cell['column'])
        cells[key]=active
        capacities[key]=(domain['total']+1 if mode=='Gram_only'else cell['capacity_proof']['upper'])
    return cells,capacities


def row_data(model,kind,index):
    if kind=='Gram':
        i,j,q,s=model['Gram_rows'][index]
        return s,q
    if kind=='triple':
        sites,members=model['triple_rows'][index]
        return members,1
    assert kind=='unit_box'and 0<=index<N
    return [index],1


def cut_proof(model,domain,mode,cut,zeros,reasons):
    """Rebuild a signed original-row combination; no flow is trusted here."""
    full={(cell['row'],cell['column']):cell for cell in domain['cells']}
    combination=Counter()
    if cut['kind']=='zero_capacity':
        assert mode=='Gram_triple_and_unit_box'
        keys=[tuple(cut['cell'])]
        assert full[keys[0]]['capacity_proof']['upper']==0
        P,Q=[],[]
    else:
        assert cut['kind']=='transport_cut'
        P,Q=cut['rows'],cut['columns']
        assert P==sorted(set(P))and Q==sorted(set(Q))
        assert all(0<=u<9 for u in P+Q)
        for u in P:combination['Gram',domain['row_Gram_ids'][u]]-=1
        for v in Q:combination['Gram',domain['column_Gram_ids'][v]]+=1
        keys=[tuple(k)for k in cut['capacity_cells']]
        assert keys==sorted(set(keys))
        assert all(u in P and v not in Q for u,v in keys)
        if mode=='Gram_only':
            # A feasible flow has total M, so no edge of capacity M+1 is
            # saturated. An infeasible min-cut has capacity < M as well.
            assert not keys
    for key in keys:
        assert key in full
        bound=full[key]['capacity_proof']
        combination[bound['kind'],bound['index']]+=1
    combination={key:v for key,v in combination.items()if v}
    coefficients=[0]*N
    rhs=0
    terms=[]
    for (kind,index),weight in sorted(combination.items()):
        assert kind=='Gram'or weight>0
        support,quota=row_data(model,kind,index)
        rhs+=weight*quota
        for a in support:coefficients[a]+=weight
        terms.append({'kind':kind,'index':index,'coefficient':weight,'rhs':quota})
    assert rhs==cut['rhs'] and rhs<=0
    assert set(coefficients)<={-1,0,1}
    negative=[a for a,c in enumerate(coefficients)if c<0]
    assert set(negative)<=zeros
    assert all(a in reasons for a in negative)
    positive=[a for a,c in enumerate(coefficients)if c>0]
    newly_zero=[a for a in positive if a not in zeros]
    assert rhs<0 or newly_zero
    return {'mode':mode,'projection_id':domain['id'],'cut':cut,
        'original_row_combination':terms,'combined_rhs_upper_bound':rhs,
        'all1214_coefficients_sha256':digest(canonical(coefficients)),
        'positive_coefficient_columns':positive,
        'negative_coefficient_prior_zero_premises':[[a,reasons[a]]for a in negative],
        'new_zero_columns':newly_zero,'contradiction':rhs<0,
        'nonnegative_on_every_remaining_original_column':True}


def flow_record(identifier,result):
    return {'projection_id':identifier,
        'positive_cell_flows':[[u,v,f]for (u,v),f in sorted(result['flow'].items())if f],
        'augmentations':result['augmentations']}


def verify_flow_record(domain,zeros,mode,record):
    assert record['projection_id']==domain['id']
    assert type(record['augmentations'])is int and 0<=record['augmentations']<=domain['total']
    _,capacities=projected_state(domain,zeros,mode)
    entries=record['positive_cell_flows']
    assert entries==sorted(entries)and len({(u,v)for u,v,f in entries})==len(entries)
    values={key:0 for key in capacities}
    for u,v,f in entries:
        assert (u,v)in capacities and type(f)is int and 0<f<=capacities[u,v]
        values[u,v]=f
    cuts,forced=flow.zero_cuts(domain['row_margins'],domain['column_margins'],capacities,values)
    assert not cuts and not forced
    return {'projection_id':domain['id'],'supported_cells':len(capacities),
            'positive_flow_cells':len(entries),'all_active_cells_can_be_positive_in_some_projected_flow':True}


def verify(model,result,deadline):
    assert result['source_bindings']==bindings()and result['limits']==LIMITS
    assert result['initial_zero_premises']==[]
    assert type(result['flow_calls'])is int and 0<=result['flow_calls']<=LIMITS['maximum_flow_calls']
    assert result['LP_or_SAT_optimizer_called']is False
    assert result['joint_incidence_feasibility_claimed']is False
    events=result['events']
    assert len(events)<=LIMITS['maximum_records_including_contradiction']
    zeros,reasons=set(),{}
    stage_index=0
    for index,event in enumerate(events):
        flow.tick(deadline)
        mode=event['mode']
        assert mode in MODES and MODES.index(mode)>=stage_index
        stage_index=MODES.index(mode)
        assert type(event['projection_id'])is int and 0<=event['projection_id']<PROJECTIONS
        domain=model['domains'][event['projection_id']]
        checked=cut_proof(model,domain,mode,event['cut'],zeros,reasons)
        assert checked==event,('event',index)
        if event['contradiction']:
            assert index==len(events)-1
        else:
            assert event['new_zero_columns']
            for a in event['new_zero_columns']:
                assert a not in zeros
                zeros.add(a)
                reasons[a]=index
    assert sorted(zeros)==result['zero_columns']
    assert len(zeros)<=N
    assert result['contradiction']==bool(events and events[-1]['contradiction'])
    final_checks=[]
    stages=result['stages']
    assert len(stages)<=len(MODES)and [s['mode']for s in stages]==MODES[:len(stages)]
    cursor=0
    stage_zeros=set()
    for stage_number,stage in enumerate(stages):
        flow.tick(deadline)
        assert stage['event_start']==cursor
        assert stage['initial_zero_columns']==sorted(stage_zeros)
        if stage_number:assert stages[stage_number-1]['complete_fixed_point']
        boundary=stage['event_end']
        assert type(boundary)is int and cursor<=boundary<=len(events)
        assert type(stage['sweeps'])is int and 0<=stage['sweeps']<=N+1
        assert all(e['mode']==stage['mode']for e in events[cursor:boundary])
        stage_zeros.update(a for e in events[cursor:boundary]if not e['contradiction']for a in e['new_zero_columns'])
        assert sorted(stage_zeros)==stage['zero_columns']
        if stage['complete_fixed_point']:
            assert stage['sweeps']>=1
            assert not any(e['contradiction']for e in events[:boundary])
            assert [r['projection_id']for r in stage['terminal_flows']]==list(range(PROJECTIONS))
            for record in stage['terminal_flows']:
                flow.tick(deadline)
                final_checks.append(dict(mode=stage['mode'],**verify_flow_record(
                    model['domains'][record['projection_id']],stage_zeros,stage['mode'],record)))
        else:
            assert stage_number==len(stages)-1 and not stage['terminal_flows']
        cursor=boundary
    assert cursor==len(events)
    assert result['complete']==(not result['contradiction']and len(stages)==len(MODES)
        and all(s['complete_fixed_point']for s in stages))
    return {'status':'PASS: all signed cuts, prior-zero induction and claimed projected fixed points replayed',
        'events_checked':len(events),'zero_columns':sorted(zeros),
        'contradiction':result['contradiction'],'complete':result['complete'],
        'terminal_projection_flow_checks':final_checks,
        'max_flow_repeated_by_replay':False,'LP_or_SAT_optimizer_called':False,
        'joint_incidence_feasibility_claimed':False}


def prepare(root,directory):
    started=time.monotonic()
    assert not directory.exists()
    model=build(root)
    controls=flow.controls()
    raw=canonical(model)
    compressed=gzip.compress(raw,mtime=0)
    directory.mkdir(parents=True)
    (directory/'model.json.gz').write_bytes(compressed)
    report={'status':'complete point-independent transportation-face preparation; no case4 flow run',
        'source_bindings':bindings(),'model_raw_sha256':digest(raw),
        'model_gzip_sha256':digest(compressed),'model_bytes':len(raw),
        'projections':PROJECTIONS,'full_columns':N,'core_vertices':35,
        'grid_pairs':[[0,1],[0,2],[1,2]],'domain_counts':model['domain_counts'],
        'every_literal_column_meets_each_grid_once':True,
        'all630_Gram_rows_and1365_triple_supports_reconstructed':True,
        'controls':controls,'limits':LIMITS,'initial_zero_premises':[],
        'stages':MODES,'case4_flow_run':False,'LP_or_SAT_optimizer_called':False,
        'case4_excluded':False,'seconds':time.monotonic()-started}
    save(directory/'preparation.json',report)
    print(json.dumps(report,indent=2),flush=True)


def load_prepared(root,directory):
    report=json.loads((directory/'preparation.json').read_text())
    assert report['source_bindings']==bindings()and report['limits']==LIMITS
    compressed=(directory/'model.json.gz').read_bytes()
    assert digest(compressed)==report['model_gzip_sha256']
    raw=gzip.decompress(compressed)
    assert digest(raw)==report['model_raw_sha256']
    model=json.loads(raw)
    assert canonical(build(root))==raw
    return report,model


def run(root,preparation,output):
    assert not output.exists()
    started=time.monotonic()
    deadline=started+LIMITS['forward_seconds']
    prepared,model=load_prepared(root,preparation)
    result={'status':'running exact transportation faces','source_bindings':bindings(),
        'preparation_sha256':digest((preparation/'preparation.json').read_bytes()),
        'model_raw_sha256':prepared['model_raw_sha256'],'limits':LIMITS,
        'initial_zero_premises':[],'events':[],'stages':[],'zero_columns':[],
        'flow_calls':0,'complete':False,'contradiction':False,
        'LP_or_SAT_optimizer_called':False,'case4_exclusion_requires_cold_replay':True,
        'joint_incidence_feasibility_claimed':False}
    zeros,reasons=set(),{}
    save(output,result)
    try:
        for mode in MODES:
            stage={'mode':mode,'event_start':len(result['events']),
                'event_end':len(result['events']),'initial_zero_columns':sorted(zeros),
                'zero_columns':sorted(zeros),'complete_fixed_point':False,
                'sweeps':0,'terminal_flows':[]}
            result['stages'].append(stage)
            for sweep in range(N+1):
                flow.tick(deadline)
                before=len(zeros)
                terminal=[]
                for domain in model['domains']:
                    flow.tick(deadline)
                    active,capacities=projected_state(domain,zeros,mode)
                    solved=flow.transport(domain['row_margins'],domain['column_margins'],capacities,deadline)
                    result['flow_calls']+=1
                    assert result['flow_calls']<=LIMITS['maximum_flow_calls']
                    assert solved['augmentations']<=LIMITS['maximum_augmentations_per_flow']
                    if solved['feasible']:
                        cuts,_=flow.zero_cuts(domain['row_margins'],domain['column_margins'],capacities,solved['flow'])
                    else:
                        cuts=[solved['infeasible_cut']]
                    for cut in cuts:
                        flow.tick(deadline)
                        # Several residual cuts can overlap. Skip an already
                        # proved incoming family; every retained cut has a
                        # fresh positive coefficient or a strict contradiction.
                        cells=([cut['cell']]if cut['kind']=='zero_capacity'else cut['incoming_cells'])
                        candidates={a for key in cells for a in active[tuple(key)]}-zeros
                        if cut['rhs']==0 and not candidates:continue
                        event=cut_proof(model,domain,mode,cut,zeros,reasons)
                        index=len(result['events'])
                        result['events'].append(event)
                        assert len(result['events'])<=LIMITS['maximum_records_including_contradiction']
                        if event['contradiction']:
                            result['contradiction']=True
                            break
                        for a in event['new_zero_columns']:
                            assert a not in zeros
                            zeros.add(a)
                            reasons[a]=index
                    stage['event_end']=len(result['events'])
                    stage['zero_columns']=result['zero_columns']=sorted(zeros)
                    if cuts:save(output,result)
                    if result['contradiction']:break
                    terminal.append(flow_record(domain['id'],solved))
                stage['sweeps']=sweep+1
                if result['contradiction']:break
                if len(zeros)==before:
                    stage['complete_fixed_point']=True
                    stage['terminal_flows']=terminal
                    break
            assert result['contradiction']or stage['complete_fixed_point']
            save(output,result)
            if result['contradiction']:break
        result['complete']=not result['contradiction']and all(s['complete_fixed_point']for s in result['stages'])
        result['status']=('exact projected contradiction found; cold replay required'if result['contradiction']else
            'both exact projected zero-face closures complete; cold replay required')
    except TimeoutError as error:
        result['status']='PARTIAL: exact forward budget; completed cut proofs retained'
        result['limit_message']=str(error)
    finally:
        if result['stages']:
            result['stages'][-1]['event_end']=len(result['events'])
            result['stages'][-1]['zero_columns']=sorted(zeros)
        result['zero_columns']=sorted(zeros)
        result['seconds']=time.monotonic()-started
        save(output,result)
    print(json.dumps({k:v for k,v in result.items()if k not in('events','stages')},indent=2),flush=True)


def replay(root,preparation,result_path,output):
    assert not output.exists()
    started=time.monotonic()
    deadline=started+LIMITS['replay_seconds']
    prepared,model=load_prepared(root,preparation)
    result=json.loads(result_path.read_text())
    assert result['preparation_sha256']==digest((preparation/'preparation.json').read_bytes())
    assert result['model_raw_sha256']==prepared['model_raw_sha256']
    report=verify(model,result,deadline)
    report.update(source_bindings=bindings(),result_sha256=digest(result_path.read_bytes()),
                  model_raw_sha256=prepared['model_raw_sha256'],seconds=time.monotonic()-started,
                  case4_exclusion_verified=report['contradiction'],whole_graph_problem_resolved=False)
    save(output,report)
    print(json.dumps({k:v for k,v in report.items()if k!='terminal_projection_flow_checks'},indent=2),flush=True)


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    commands=parser.add_subparsers(dest='mode',required=True)
    for mode in ('prepare','preflight','run','replay'):
        c=commands.add_parser(mode)
        c.add_argument('--root',type=Path,default=ROOT)
        c.add_argument('--directory',type=Path,required=True)
        if mode!='prepare':c.add_argument('--output',type=Path,required=True)
        if mode=='replay':c.add_argument('--result',type=Path,required=True)
    args=parser.parse_args()
    if args.mode=='prepare':prepare(args.root,args.directory)
    elif args.mode=='run':run(args.root,args.directory,args.output)
    elif args.mode=='replay':replay(args.root,args.directory,args.result,args.output)
    else:
        assert not args.output.exists()
        started=time.monotonic()
        prepared,model=load_prepared(args.root,args.directory)
        report={'status':'PASS: all literal domains, capacities and source/model bindings rebuilt',
            'source_bindings':bindings(),'model_raw_sha256':prepared['model_raw_sha256'],
            'projections':PROJECTIONS,'domain_counts':model['domain_counts'],
            'case4_flow_run':False,'LP_or_SAT_optimizer_called':False,
            'seconds':time.monotonic()-started}
        save(args.output,report)
        print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
