"""Complete six-root pairs of clique-absence conditions.

For distinct maximal cliques C,D, the localizer is M minus singles in
their union plus compatible doubles across their two differences.
Per-root lift registries and exact primitive row identities certify
every union row by a saved cancellation bijection. No point is loaded.
"""

import argparse
from collections import Counter
import gzip
from itertools import combinations
import json
from pathlib import Path
import pickle
import resource
import signal
import time

import grid_free_order10_double_complement_domains as generic
import grid_free_order10_complement_cliques as cliques
import grid_free_order10_complement_clique_orbits as groups
import grid_free_order10_complement_visible_domains as visible


ROOT=Path(__file__).resolve().parents[2]
SOURCE_BINDINGS={
    'grid_free_order10_double_complement_domains.py':'1283b15c44f408e0baf2cb1f9abd1c59b4ebee8717ca099c39e52b55c56ea935',
    'grid_free_order10_complement_cliques.py':'765f0ca7ca7ffcb16e6c518d80c70ffca99ba2c0c46d682077f1027ae47fe912',
    'grid_free_order10_complement_clique_orbits.py':'5569a81838301fa54dc2401b98592a91fb302b7ed7a3110983a6f475a1107130',
    'grid_free_order10_complement_visible_domains.py':'d89248dce73849059afa12cf1c731f31dcafa8a0769ccde3b25574c67ec4c54a',
    'grid_free_order10_complement_domains.py':'4961411ec0f7671abb7e34c5dbd4ec257ac98f9bffcb745a408e979751179ed8',
    'grid_free_order10_r8s1.py':'77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469',
}


def terms(counter):
    return [[int(i),int(c)] for i,c in sorted(counter.items()) if c]


def visible_graph(rows,high):
    q1=[(1 << i)|(1 << j) for i,j in combinations(range(6),2)
        if 2-((rows[i] >> j)&1)-(rows[i]&rows[j]).bit_count()==1]
    adjacency=[0]*len(high)
    edge_choices={}
    for i,a in enumerate(high):
        for j,b in enumerate(high[:i]):
            shared=a&b
            forbidden=shared.bit_count()>=3 or any(shared & pair==pair for pair in q1)
            allowed=[edge for edge in (0,1) if generic.literal.valid(generic.literal.extend(rows,[a,b],edge))]
            assert forbidden==(not allowed)
            if allowed:
                assert allowed[0]==0
                edge_choices[tuple(sorted((a,b)))]=allowed
            else:
                adjacency[i]|=1 << j
                adjacency[j]|=1 << i
    return adjacency,edge_choices


def lower_product_bound(lift):
    lengths=[len(row) for row in lift['sparse_rows']]
    return (sum(lengths)**2+sum(v*v for v in lengths))//2


def prepare_root(root,data,lifts,bases,seven_blocks,eight_blocks):
    rows=tuple(data[0][root])
    allowed=generic.direct.masks_for(rows)
    assert allowed==[mask for mask,_ in data[3][root]]
    high=[mask for mask in allowed if mask.bit_count()>=3]
    n=len(high)+1
    if high:
        assert [tuple(flag) for flag in bases[root][0]]==[rows]+[generic.transport.attach(rows,mask) for mask in high]
    else:
        assert root not in bases
    positions={mask:i for i,mask in enumerate(high)}
    adjacency,edge_choices=visible_graph(rows,high)
    enumerated=cliques.bron_kerbosch(adjacency)
    incremental,addition_order,intermediate_sizes=visible.incremental_cliques(adjacency,high)
    assert enumerated==incremental
    codes=sorted(enumerated)
    for code in codes:
        cliques.maximal(code,(1 << len(high))-1,adjacency)
    residuals=[[i,j,2-((rows[i] >> j)&1)-(rows[i]&rows[j]).bit_count()] for i,j in combinations(range(6),2)]
    clique_records=[]
    counts=Counter(root_types=1,high_masks=len(high),high_mask_pairs_checked=len(high)*(len(high)-1)//2)
    for code in codes:
        masks=[high[i] for i in cliques.members(code)]
        common=63
        for mask in masks:
            common &= mask
        witness=next(([i,j,1] for i,j,q in residuals if q==1 and common >> i & 1 and common >> j & 1),None)
        classification=('constant_only_base' if not masks else 'quota_one_redundant' if witness else 'remaining_clique')
        record={'masks':masks,'base_positions':[positions[mask]+1 for mask in masks],
                'classification':classification,'common_mask':common}
        if witness:
            pair=(1 << witness[0])|(1 << witness[1])
            record['residual_pair_witness']=witness
            record['positive_sum_other_masks']=[mask for mask in allowed if mask & pair==pair and mask not in set(masks)]
            assert pair in record['positive_sum_other_masks']
        clique_records.append(record)
        counts[classification]+=1
    remaining=[i for i,record in enumerate(clique_records) if record['classification']=='remaining_clique']
    pair_specs=[]
    needed_singles,needed_doubles=set(),set()
    for left,right in combinations(remaining,2):
        C,D=set(clique_records[left]['masks']),set(clique_records[right]['masks'])
        assert not C<=D and not D<=C
        A,B,I=C-D,D-C,C&D
        union=sorted(C|D)
        cross=sorted({tuple(sorted((a,b))) for a in A for b in B
                      if not (adjacency[positions[a]] >> positions[b] & 1)})
        assert len(cross)==sum(not (adjacency[positions[a]] >> positions[b] & 1) for a in A for b in B)
        pair_specs.append({'left_clique_index':left,'right_clique_index':right,
            'union_masks':union,'left_only_masks':sorted(A),'right_only_masks':sorted(B),
            'intersection_masks':sorted(I),'cross_pair_keys':cross,
            'quotient_order':n-len(union),
            'quotient_lower_entries':(n-len(union))*(n-len(union)+1)//2})
        needed_singles.update(union)
        needed_doubles.update(cross)
    counts['all_unordered_maximal_clique_pairs']=len(clique_records)*(len(clique_records)-1)//2
    counts['quota_one_redundant_clique_pairs']=counts['all_unordered_maximal_clique_pairs']-len(pair_specs)
    counts['candidate_clique_pairs']=len(pair_specs)
    counts['candidate_roots']=int(bool(pair_specs))
    single_records=[]
    single_ids={mask:i for i,mask in enumerate(sorted(needed_singles))}
    singles={}
    for mask in sorted(needed_singles):
        lift=lifts.conditional(root,high,[mask])
        assert lift is not None
        singles[mask]=lift
        i=positions[mask]+1
        forms=[]
        for j in range(n):
            parent=generic.entry(bases,root,i,j)
            child=generic.lifted_entry(seven_blocks,lift,i,j)
            assert Counter(parent)==Counter(child)
            forms.append(terms(parent))
            counts['single_self_row_coefficient_comparisons']+=1
        empty=[]
        for u in cliques.members(adjacency[positions[mask]]):
            assert lift['sparse_rows'][u+1]==[]
            empty.append(high[u])
            counts['single_incompatible_rows_checked_empty']+=1
        single_records.append({'mask':mask,'lift':lift,
            'self_selected_row_labelled_count_forms':forms,
            'incompatible_old_masks_checked_empty':empty})
    double_records=[]
    double_ids={pair:i for i,pair in enumerate(sorted(needed_doubles))}
    for a,b in sorted(needed_doubles):
        children=[lifts.conditional(root,high,[a,b],edge) for edge in (0,1)]
        children=[child for child in children if child is not None]
        assert children and [child['mutual_edge'] for child in children]==edge_choices[(a,b)]
        selected_identity_rows=[]
        for chosen,partner in ((a,b),(b,a)):
            i=positions[chosen]+1
            forms=[]
            for j in range(n):
                double=Counter()
                for child in children:
                    double.update(generic.lifted_entry(eight_blocks,child,i,j))
                single=Counter(generic.lifted_entry(seven_blocks,singles[partner],i,j))
                assert double==single
                forms.append(terms(single))
                counts['double_selected_row_coefficient_comparisons']+=1
            selected_identity_rows.append({'selected_mask':chosen,'partner_mask':partner,
                         'common_labelled_count_row_forms':forms})
        incompatible=adjacency[positions[a]]|adjacency[positions[b]]
        empty=[]
        for u in cliques.members(incompatible):
            assert high[u] not in (a,b)
            assert all(child['sparse_rows'][u+1]==[] for child in children)
            empty.append(high[u])
            counts['double_incompatible_rows_checked_empty']+=len(children)
        double_records.append({'masks':[a,b],'conditional_lifts':children,
            'selected_row_partner_identities':selected_identity_rows,'incompatible_old_masks_checked_empty':empty})
    candidate_records=[]
    for spec in pair_specs:
        cross=spec.pop('cross_pair_keys')
        cross_ids=[double_ids[key] for key in cross]
        union=spec['union_masks']
        cancellations=[]
        for chosen in union:
            i=positions[chosen]
            partners=sorted(mask for mask in union if mask!=chosen and not (adjacency[i] >> positions[mask] & 1))
            surviving=[key for key in cross if chosen in key]
            assert sorted(key[1] if key[0]==chosen else key[0] for key in surviving)==partners
            for key in cross:
                if chosen in key:
                    continue
                assert adjacency[i] >> positions[key[0]] & 1 or adjacency[i] >> positions[key[1]] & 1
                assert all(child['sparse_rows'][i+1]==[] for child in double_records[double_ids[key]]['conditional_lifts'])
            for mask in union:
                if mask!=chosen and mask not in partners:
                    assert singles[mask]['sparse_rows'][i+1]==[]
            if chosen in spec['intersection_masks']:
                assert not partners and not surviving
            cancellations.append({'union_mask':chosen,'self_single_registry_id':single_ids[chosen],
                'compatible_single_partner_masks':partners,
                'partner_single_registry_ids':[single_ids[mask] for mask in partners],
                'cancelling_double_registry_ids':[double_ids[tuple(sorted((chosen,mask)))] for mask in partners]})
            counts['union_rows_certified_by_exact_primitive_cancellation']+=1
            counts['union_row_entries_certified_by_exact_primitive_cancellation']+=n
        candidate_records.append({**spec,
            'union_base_positions':[positions[mask]+1 for mask in union],
            'single_registry_ids':[single_ids[mask] for mask in union],
            'compatible_cross_double_registry_ids':cross_ids,
            'union_row_cancellation_bijections':cancellations,
            'all_union_rows_vanish_as_unrestricted_coefficient_identities':True})
    actions=generic.root_actions(rows,high) if candidate_records else []
    clique_index={tuple(record['masks']):i for i,record in enumerate(clique_records)}
    pair_index={(record['left_clique_index'],record['right_clique_index']):i for i,record in enumerate(candidate_records)}
    action_maps=[]
    for action in actions:
        mapping=action['vertex_image']
        images={mask:generic.transport.transported_mask(mask,mapping) for mask in high}
        perm=[positions[images[mask]] for mask in high]
        for i,row in enumerate(adjacency):
            assert sum(1 << perm[j] for j in cliques.members(row))==adjacency[perm[i]]
        clique_map=[]
        for case in clique_records:
            image=clique_index[tuple(sorted(images[mask] for mask in case['masks']))]
            assert clique_records[image]['classification']==case['classification']
            clique_map.append(image)
        action_maps.append((mapping,clique_map))
    pending=set(range(len(candidate_records)))
    orbits=[]
    representative_singles,representative_doubles=set(),set()
    while pending:
        representative=min(pending)
        case=candidate_records[representative]
        members={}
        for mapping,action in action_maps:
            pair=tuple(sorted((action[case['left_clique_index']],action[case['right_clique_index']])))
            image=pair_index[pair]
            if image not in members:
                members[image]={'pair_index':image,'representative_to_member_vertex_map':mapping,
                    'clique_sides_swapped':action[case['left_clique_index']]>action[case['right_clique_index']]}
        assert set(members)<=pending
        pending-=set(members)
        for image,record in members.items():
            moved=sorted(generic.transport.transported_mask(mask,record['representative_to_member_vertex_map']) for mask in case['union_masks'])
            assert moved==candidate_records[image]['union_masks']
        orbits.append({'representative_pair_index':representative,'orbit_size':len(members),
            'quotient_order':case['quotient_order'],'quotient_lower_entries':case['quotient_lower_entries'],
            'members':[members[i] for i in sorted(members)]})
        representative_singles.update(case['single_registry_ids'])
        representative_doubles.update(case['compatible_cross_double_registry_ids'])
        operations=len(case['single_registry_ids'])+len(case['compatible_cross_double_registry_ids'])
        counts['representative_quotient_lower_entries']+=case['quotient_lower_entries']
        counts['representative_full_matrix_additions_and_subtractions']+=operations*n*n
        counts['representative_quotient_lower_additions_and_subtractions']+=operations*case['quotient_lower_entries']
    assert sum(orbit['orbit_size'] for orbit in orbits)==len(candidate_records)
    counts['candidate_pair_orbits']=len(orbits)
    counts['root_automorphisms_checked_for_candidate_roots']=len(actions)
    counts['single_lift_registry_size']=len(single_records)
    counts['double_lift_registry_size']=len(double_records)
    counts['representative_single_registry_size']=len(representative_singles)
    counts['representative_double_registry_size']=len(representative_doubles)
    child_orders={}
    for i in representative_singles:
        lift=single_records[i]['lift']
        child_orders[lift['child_root_type']]=lift['child_base_order']
        counts['representative_sparse_lower_products_upper_bound']+=lower_product_bound(lift)
    for i in representative_doubles:
        for lift in double_records[i]['conditional_lifts']:
            child_orders[lift['child_root_type']]=lift['child_base_order']
            counts['representative_sparse_lower_products_upper_bound']+=lower_product_bound(lift)
    conditional_cells=(len(representative_singles)+len(representative_doubles))*n*n
    child_cells=sum(order*order for order in child_orders.values())
    return {'root_type':root,'root_rows':list(rows),'allowed_masks':allowed,'high_masks':high,'base_order':n,
        'visible_incompatibility_adjacency':adjacency,'both_literal_edge_choices_checked_for_every_high_mask_pair':True,
        'bron_kerbosch_equals_incremental_enumeration':True,'incremental_vertex_order':addition_order,
        'incremental_maximal_clique_counts':intermediate_sizes,'maximal_cliques':clique_records,
        'single_lift_registry':single_records,'double_lift_registry':double_records,
        'candidate_clique_pairs':candidate_records,'root_automorphisms':actions,'pair_orbits':orbits,
        'representative_single_registry_ids':sorted(representative_singles),
        'representative_double_registry_ids':sorted(representative_doubles),
        'conditional_matrix_object_cells':conditional_cells,'child_matrix_object_cells':child_cells,
        'two_working_matrix_object_cells':2*n*n,'counts':dict(sorted(counts.items()))}


def literal_control(root_record,lifts,free_masks,edge):
    root,rows,high=root_record['root_type'],root_record['root_rows'],root_record['high_masks']
    assert rows==[0]*6
    C={mask for mask in high if mask & 7==7}
    D={mask for mask in high if mask & 56==56}
    assert any(set(case['masks'])==C for case in root_record['maximal_cliques'])
    assert any(set(case['masks'])==D for case in root_record['maximal_cliques'])
    host=generic.literal.extend(rows,free_masks,edge)
    assert generic.literal.valid(host)
    actual=Counter(free_masks)
    X=[1]+[actual[mask] for mask in high]
    assert all(value in (0,1) for value in X)
    zC=sum(actual[mask] for mask in C)
    zD=sum(actual[mask] for mask in D)
    assert zC in (0,1) and zD in (0,1)
    def contribution(selected):
        if not all(actual[mask] for mask in selected):
            return [[0]*len(X) for _ in X]
        chosen=[6+free_masks.index(mask) for mask in selected]
        cross=((host[chosen[0]] >> chosen[1])&1) if len(chosen)==2 else None
        lift=lifts.conditional(root,high,selected,cross)
        assert lift is not None
        root_vertices=list(range(6))+chosen
        positions={mask:i+1 for i,mask in enumerate(lift['child_high_masks'])}
        Y=[1]+[0]*len(positions)
        for vertex in range(6,len(host)):
            if vertex in chosen:
                continue
            mask=sum(((host[vertex] >> old)&1) << i for i,old in enumerate(root_vertices))
            moved=generic.transport.transported_mask(mask,lift['actual_to_child_map'])
            if moved in positions:
                Y[positions[moved]]+=1
        image=[sum(Y[k] for k in row) for row in lift['sparse_rows']]
        assert image==X
        return [[a*b for b in image] for a in image]
    matrix=[[a*b for b in X] for a in X]
    for mask in C|D:
        sub=contribution([mask])
        matrix=[[matrix[i][j]-sub[i][j] for j in range(len(X))] for i in range(len(X))]
    positions={mask:i for i,mask in enumerate(high)}
    for a in C-D:
        for b in D-C:
            if root_record['visible_incompatibility_adjacency'][positions[a]] >> positions[b] & 1:
                continue
            add=contribution(sorted((a,b)))
            matrix=[[matrix[i][j]+add[i][j] for j in range(len(X))] for i in range(len(X))]
    factor=(1-zC)*(1-zD)
    assert matrix==[[factor*a*b for b in X] for a in X]
    return {'root_type':root,'host_rows':list(host),'left_clique':sorted(C),'right_clique':sorted(D),
        'outside_masks':free_masks,'outside_edge':edge,'left_clique_sum':zC,'right_clique_sum':zD,
        'absence_product':factor,'intersection_flag_present':bool(set(free_masks)&C&D),
        'full_literal_lift_and_union_formula_checked':True,
        'scope':'Cap-compatible small host, not an SRG(99,14,1,2) assertion.'}


def run(args):
    started=time.monotonic()
    for name,sha in SOURCE_BINDINGS.items():
        assert generic.files.digest(Path(__file__).with_name(name))==sha
    for path,sha in ((args.catalogue,generic.direct.CATALOGUE_SHA),(generic.BASE,generic.BASE_SHA),
                     (generic.seven.BASE,generic.seven.BASE_SHA),(generic.seven.CHILD,generic.seven.CHILD_SHA)):
        assert generic.files.digest(path)==sha
    data=pickle.loads(args.catalogue.read_bytes())
    bases={r:(f,t) for r,f,t in pickle.loads(generic.BASE.read_bytes())}
    seven_blocks={r:([flag[-1] for flag in flags[1:]],t) for r,flags,t in pickle.loads(generic.seven.BASE.read_bytes())}
    saved8=pickle.loads(gzip.decompress(generic.seven.CHILD.read_bytes()))
    assert saved8['point_independent'] and saved8['complete_root_family'] and not saved8['zero_flags_or_roots_removed']
    eight_blocks={r:(m,t) for r,m,t in saved8['blocks']}
    assert len(bases)==55 and len(seven_blocks)==203 and len(eight_blocks)==916
    lifts=generic.Lifts(data,seven_blocks,eight_blocks)
    result={'source_sha256':generic.files.digest(Path(__file__)),'source_bindings':SOURCE_BINDINGS,
        'catalogue_sha256':generic.direct.CATALOGUE_SHA,'six_root_cache_sha256':generic.BASE_SHA,
        'seven_root_cache_sha256':generic.seven.BASE_SHA,'eight_root_cache_sha256':generic.seven.CHILD_SHA,
        'roots':[],'literal_controls':[],
        'all_union_rows_are_unrestricted_coefficient_identities':True,
        'proof_method':'Exact primitive coefficient comparisons plus a saved cancellation bijection for every union row.',
        'normalization':'Labelled induced embeddings; distinct selected masks specify the selected vertices without an automorphism or factorial divisor.',
        'quota_one_redundancy_uses_complete_child_clique_localizers_and_SRG_count_identities':True,
        'point_dependent_pruning':False,'count_point_loaded':False,'point_scanned':False,
        'new_product_tensors_generated':False,'dense_reduction_loaded':False,'optimizer_called':False}
    totals=Counter()
    peak_cells,peak_root=0,None
    timed_out,error,current=False,None,None
    def deadline(_signum,_frame):
        raise TimeoutError('bounded six-root clique-pair preparation')
    previous=signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        for root in data[1][6]:
            current=['root',root]
            record=prepare_root(root,data,lifts,bases,seven_blocks,eight_blocks)
            oldmask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM})
            try:
                result['roots'].append(record)
                totals.update(record['counts'])
                cells=record['conditional_matrix_object_cells']+record['child_matrix_object_cells']+record['two_working_matrix_object_cells']
                if cells>peak_cells:
                    peak_cells,peak_root=cells,root
                current=None
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK,oldmask)
        current=['literal_controls']
        for masks,edge in (([11],0),([7,11],0),([56,11],0),([7,56,11],0),([63],0),([7,56],1)):
            result['literal_controls'].append(literal_control(result['roots'][0],lifts,masks,edge))
        current=None
    except TimeoutError:
        timed_out=True
    except Exception as problem:
        error=repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    complete=len(result['roots'])==62 and len(result['literal_controls'])==6
    if complete:
        assert totals['root_types']==62 and totals['high_masks']==829
        assert totals['high_mask_pairs_checked']==9118
        assert totals['candidate_clique_pairs']==3283 and totals['candidate_roots']==18
        assert sum(totals[k] for k in ('constant_only_base','quota_one_redundant','remaining_clique'))==541
        assert any(control['intersection_flag_present'] for control in result['literal_controls'])
    result.update(status='complete six-root clique-pair domain and coefficient preparation' if complete else 'UNKNOWN: incomplete six-root clique-pair preparation',
        complete_preparation=complete,complete_root_family=len(result['roots'])==62,
        timed_out=timed_out,error=error,unfinished_case=current,summary=dict(sorted(totals.items())),
        largest_representative_quotient_order=max((o['quotient_order'] for r in result['roots'] for o in r['pair_orbits']),default=0),
        per_root_cache_sizing={'largest_joint_matrix_object_cells':peak_cells,'largest_joint_cache_root_type':peak_root,
            'illustrative_64_bytes_per_object_cell':64*peak_cells,'illustrative_bytes_are_not_a_runtime_RSS_guarantee':True})
    if args.replay:
        assert complete and not timed_out and error is None
        old=json.loads(gzip.decompress(args.replay.read_bytes()))
        old.pop('seconds')
        old.pop('max_rss_kib')
        assert old==groups.normalise(result)
        result={'status':'PASS: complete clique-pair domains, registries, coefficient primitives and cancellation maps replayed',
            'source_sha256':generic.files.digest(Path(__file__)),'certificate_sha256':generic.files.digest(args.replay),
            'summary':dict(sorted(totals.items()))}
    result['seconds']=time.monotonic()-started
    result['max_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    content=json.dumps(result,indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(content,compresslevel=9,mtime=0) if args.output.suffix=='.gz' else content)
    print(json.dumps({key:value for key,value in result.items() if key not in ('roots','literal_controls')},indent=2),flush=True)
    print('output_sha256',generic.files.digest(args.output),flush=True)
    return 1 if error else 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',type=Path)
    parser.add_argument('--seconds',type=int,default=60)
    args=parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 60
    raise SystemExit(run(args))
