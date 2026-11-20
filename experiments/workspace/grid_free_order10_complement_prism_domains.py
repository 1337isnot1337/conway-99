"""Bounded prism-free clique/orbit preparation and exact zero supports.

All original high-mask domains are retained. Two complete clique
enumerations agree. New conditional zero rows are recorded as exact
labelled-count tensor terms supported on the proved prism-zero types;
they are not claimed to vanish as unrestricted tensor identities.
"""

import argparse
from collections import Counter, deque
from functools import reduce
import gzip
import json
from operator import and_
from pathlib import Path
import pickle
import resource
import signal
import time

import grid_free_order10_complement_cliques as clique_tools
import grid_free_order10_complement_clique_orbits as groups
import grid_free_order10_complement_domains as domains
import grid_free_order10_complement_visible_domains as visible_tools
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
SCOUT = LOGS/'order10-complement-prism-scout.json.gz'
SCOUT_SHA = '7547298a08a3ed7d735367e9b81a22c9e193f54da995c3cabd6032139cf70851'
P4 = LOGS/'order10-complement-prism-p4.json.gz'
P4_SHA = '6c68411eb538dcbf2b51eab39f62b1fdecfbb569a0c312e7ebe0283c6498cab1'
VISIBLE = LOGS/'order10-complement-visible-domains.json.gz'
VISIBLE_SHA = 'b273c84d939cefbe61cfbb2ed77721fd81c9f9c61a203d9fdbe17e674e453d10'
CLOSURE = LOGS/'prism-zero-order10-zero-closure.json'
CLOSURE_SHA = 'cde1bd353eb39fe8aa713080a5acfb6ae78f3dd13244d9255c9217541060919c'
OLD_LIFTS = LOGS/'order10-complement-clique-lifts.json.gz'
OLD_LIFTS_SHA = 'c92a8ad205545a75f67cdffc43011db21f687f14722109a03f2b34f6490c5c28'
SOURCE_BINDINGS = {
    'grid_free_order10_complement_cliques.py':'765f0ca7ca7ffcb16e6c518d80c70ffca99ba2c0c46d682077f1027ae47fe912',
    'grid_free_order10_complement_clique_orbits.py':'5569a81838301fa54dc2401b98592a91fb302b7ed7a3110983a6f475a1107130',
    'grid_free_order10_complement_domains.py':'4961411ec0f7671abb7e34c5dbd4ec257ac98f9bffcb745a408e979751179ed8',
    'grid_free_order10_complement_visible_domains.py':'d89248dce73849059afa12cf1c731f31dcafa8a0769ccde3b25574c67ec4c54a',
    'grid_free_order10_r8s1.py':'77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469',
}


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes())


def supported_terms(counter,zero_types):
    terms = [[int(i),int(c)] for i,c in sorted(counter.items()) if c]
    assert all(c>0 and i in zero_types for i,c in terms)
    return terms


def prepare_root(record,visible,data,lift_builder,bases,children,zero_types):
    root,rows,high = record['root_type'],record['root_rows'],record['high_masks']
    assert visible['root_type']==root and visible['root_rows']==rows and visible['high_masks']==high
    assert high==[mask for mask,_ in data[3][root] if mask.bit_count()>=3]
    n=len(high)+1
    adjacency=record['prism_free_pair_incompatibility_adjacency']
    first=clique_tools.bron_kerbosch(adjacency)
    second,addition_order,intermediate_sizes=visible_tools.incremental_cliques(adjacency,high)
    assert first==second
    codes=sorted(first)
    for code in codes:
        clique_tools.maximal(code,(1 << len(high))-1,adjacency)
    counts=Counter()
    residuals=[(i,j,2-((rows[i] >> j)&1)-(rows[i]&rows[j]).bit_count())
               for i in range(7) for j in range(i)]
    allowed=[mask for mask,_ in data[3][root]]
    cases=[]
    for code in codes:
        selected=[high[i] for i in clique_tools.members(code)]
        common=reduce(and_,selected,127)
        witness=next(([i,j,1] for i,j,q in residuals if q==1 and common >> i & 1 and common >> j & 1),None)
        classification=('constant_only_base' if not selected else
                        'quota_one_redundant' if witness else 'remaining_clique_complement')
        if not selected:
            assert not high
        case={'masks':selected,'base_positions':[i+1 for i in clique_tools.members(code)],
              'common_mask':common,'classification':classification,'quotient_order':n-len(selected)}
        case['quotient_lower_entries']=case['quotient_order']*(case['quotient_order']+1)//2
        if witness:
            pair=(1 << witness[0])|(1 << witness[1])
            case['residual_pair_witness']=witness
            case['other_allowed_masks_in_positive_sum']=[mask for mask in allowed if mask & pair==pair and mask not in set(selected)]
        cases.append(case)
        counts[classification]+=1
        counts['all_clique_selected_row_instances']+=len(selected)
    positions={mask:i for i,mask in enumerate(high)}
    previous_covers=[]
    for previous in visible['maximal_cliques']:
        code=sum(1 << positions[mask] for mask in previous['masks'])
        previous_covers.append(next(i for i,new in enumerate(codes) if code & ~new==0))
    counts['old_visible_cliques_covered']=len(previous_covers)
    index={tuple(case['masks']):i for i,case in enumerate(cases)}
    triples=[]
    for previous in visible['triple_groups_with_pair_residuals_two']:
        code=sum(1 << positions[mask] for mask in previous['all_allowed_superset_masks'])
        covering=next(i for i,new in enumerate(codes) if code & ~new==0)
        triples.append({'triple_mask':previous['triple_mask'],
            'all_allowed_superset_masks':previous['all_allowed_superset_masks'],
            'covering_maximal_clique_index':covering,
            'is_still_maximal':code in first})
    counts['retained_triple_groups_with_saved_cover']=len(triples)
    counts['triple_groups_still_maximal']=sum(t['is_still_maximal'] for t in triples)
    group,permutations_checked=groups.all_automorphisms(rows)
    generators=[tuple(g) for g in visible['generators']]
    assert groups.closure(generators,7)==group and len(group)==visible['automorphism_order']
    actions=[]
    absent=set(record['absent_high_masks'])
    for generator in generators:
        assert groups.automorphism(rows,generator)
        moved={mask:groups.move_mask(mask,generator) for mask in high}
        assert sorted(moved.values())==high and {moved[mask] for mask in absent}==absent
        action_on_masks=[positions[moved[mask]] for mask in high]
        for i,row in enumerate(adjacency):
            assert sum(1 << action_on_masks[j] for j in clique_tools.members(row))==adjacency[action_on_masks[i]]
        action=[]
        for case in cases:
            image=index[tuple(sorted(moved[mask] for mask in case['masks']))]
            assert cases[image]['classification']==case['classification']
            action.append(image)
        assert sorted(action)==list(range(len(cases)))
        actions.append(action)
    counts['root_automorphisms_enumerated']=len(group)
    counts['degree_preserving_vertex_permutations_checked']=permutations_checked
    counts['generators_verified']=len(generators)
    remaining={i for i,c in enumerate(cases) if c['classification']=='remaining_clique_complement'}
    unvisited,orbits,needed=set(remaining),[],set()
    while unvisited:
        representative=min(unvisited)
        maps={representative:tuple(range(7))}
        pending=deque([representative])
        while pending:
            old=pending.popleft()
            for generator,action in zip(generators,actions):
                image=action[old]
                assert image in remaining
                if image not in maps:
                    maps[image]=groups.compose(generator,maps[old])
                    pending.append(image)
        assert set(maps)<=unvisited
        unvisited-=set(maps)
        for image,mapping in maps.items():
            assert groups.automorphism(rows,mapping)
            assert sorted(groups.move_mask(mask,mapping) for mask in cases[representative]['masks'])==cases[image]['masks']
        case=cases[representative]
        q,size=case['quotient_order'],len(case['masks'])
        needed.update(case['masks'])
        counts['remaining_clique_orbits']+=1
        counts['covered_remaining_cliques']+=len(maps)
        counts['representative_quotient_lower_entries']+=q*(q+1)//2
        counts['representative_full_matrix_subtractions']+=size*n*n
        counts['representative_quotient_lower_subtractions']+=size*q*(q+1)//2
        orbits.append({'representative_clique_index':representative,'representative_masks':case['masks'],
            'quotient_order':q,'quotient_lower_entries':q*(q+1)//2,'orbit_size':len(maps),
            'members':[{'clique_index':i,'representative_to_member_vertex_map':list(maps[i])} for i in sorted(maps)]})
    assert counts['covered_remaining_cliques']==len(remaining)
    lifts={mask:{'mask':mask,'base_position':i+1,**lift_builder.build(root,mask,high)} for i,mask in enumerate(high)}
    for old in visible['conditional_lifts']:
        assert lifts[old['mask']]==old
        counts['previous_representative_lifts_reconstructed_exactly']+=1
    zero_rows=[]
    support=set()
    old_adjacency=visible['visible_incompatibility_adjacency']
    for i,a in enumerate(high):
        lift=lifts[a]
        assert lift['sparse_rows'][0]==lift['sparse_rows'][i+1]==[0]
        child_tensor=children[lift['child_root_type']][1]
        for j in clique_tools.members(adjacency[i]):
            if old_adjacency[i] >> j & 1:
                assert lift['sparse_rows'][j+1]==[]
                counts['old_visible_directed_rows_rechecked_empty']+=1
                continue
            selected_row=lift['sparse_rows'][j+1]
            assert selected_row
            entries=[]
            for k,sparse in enumerate(lift['sparse_rows']):
                counter=Counter()
                for u in selected_row:
                    for v in sparse:
                        counter.update(domains.entry(child_tensor,u,v))
                terms=supported_terms(counter,zero_types)
                if terms:
                    entries.append([k,terms])
                    support.update(t for t,_ in terms)
                    counts['new_conditional_zero_support_nonempty_entries']+=1
                    counts['new_conditional_zero_support_tensor_terms']+=len(terms)
                counts['new_conditional_row_entries_checked']+=1
            assert entries and entries[0][0]==0
            zero_rows.append({'selected_mask':a,'vanishing_old_flag_mask':high[j],
                'child_root_type':lift['child_root_type'],'nonempty_child_columns':selected_row,
                'nonzero_parent_row_entries_as_labelled_count_forms':entries,
                'zero_entry_count':n-len(entries)})
            counts['new_conditional_rows_supported_on_prism_zeros']+=1
    parent_zero_rows=[]
    parent_positions=range(n) if record['root_contains_prism'] else [positions[mask]+1 for mask in sorted(absent)]
    for i in parent_positions:
        entries=[]
        for j in range(n):
            terms=supported_terms(domains.entry(bases[root][1],i,j) if high else {root:1},zero_types)
            if terms:
                entries.append([j,terms])
                support.update(t for t,_ in terms)
                counts['absent_parent_row_tensor_terms']+=len(terms)
            counts['absent_parent_row_entries_checked']+=1
        parent_zero_rows.append({'parent_row':i,'nonzero_entries_as_labelled_count_forms':entries})
    counts['absent_parent_rows_checked']=len(parent_zero_rows)
    counts['all_high_mask_lifts_reconstructed']=len(high)
    retained=[lifts[mask] for mask in sorted(needed)]
    child_orders={lift['child_root_type']:lift['child_base_order'] for lift in retained}
    for lift in retained:
        lengths=[len(row) for row in lift['sparse_rows']]
        counts['representative_conditional_lower_products_upper_bound']+=(sum(lengths)**2+sum(v*v for v in lengths))//2
    counts['representative_conditional_lifts']=len(retained)
    return {'root_type':root,'root_rows':rows,'high_masks':high,'base_order':n,
        'root_contains_prism':record['root_contains_prism'],'absent_high_masks':record['absent_high_masks'],
        'prism_free_pair_incompatibility_adjacency':adjacency,
        'bron_kerbosch_equals_incremental_enumeration':True,
        'incremental_vertex_order':addition_order,'incremental_maximal_clique_counts':intermediate_sizes,
        'maximal_cliques':cases,'old_visible_clique_superset_indices':previous_covers,
        'triple_groups_with_pair_residuals_two':triples,
        'generators':[list(g) for g in generators],'automorphism_order':len(group),
        'full_group_and_domain_actions_checked':True,'orbits':orbits,'conditional_lifts':retained,
        'new_conditional_rows_vanishing_only_after_prism_zero_substitution':zero_rows,
        'absent_parent_rows_vanishing_after_prism_zero_substitution':parent_zero_rows,
        'zero_support_type_indices':sorted(support),
        'all_selected_clique_rows_zero_after_prism_zero_substitution':True,
        'unrestricted_selected_row_zero_identity_claim':False,
        'conditional_matrix_object_cells':len(needed)*n*n,
        'child_matrix_object_cells':sum(order*order for order in child_orders.values()),
        'two_working_matrix_object_cells':2*n*n,'counts':dict(sorted(counts.items()))}


def run(args):
    started=time.monotonic()
    for name,sha in SOURCE_BINDINGS.items():
        assert files.digest(Path(__file__).with_name(name))==sha
    for path,sha in ((SCOUT,SCOUT_SHA),(P4,P4_SHA),(VISIBLE,VISIBLE_SHA),(CLOSURE,CLOSURE_SHA),(OLD_LIFTS,OLD_LIFTS_SHA),
                     (domains.BASE,domains.BASE_SHA),(domains.CHILD,domains.CHILD_SHA)):
        assert files.digest(path)==sha
    assert files.digest(args.catalogue)==domains.direct.CATALOGUE_SHA
    scout,p4,visible,closure,old_lifts=read(SCOUT),read(P4),read(VISIBLE),read(CLOSURE),read(OLD_LIFTS)
    assert scout['complete_root_family'] and visible['complete_root_family']
    assert p4['summary']['genuine_prism_pair_edges_classified_by_p4']==1155
    assert old_lifts['summary']['checked_high_mask_lifts']==5215
    assert closure['all_induced_prism_forms_vanish_after_prism_core_zeros']
    zero_types=set(closure['prism_containing_induced_types'])
    assert len(zero_types)==1443
    with args.catalogue.open('rb') as stream:
        data=pickle.load(stream)
    bases={root:(flags,tensor) for root,flags,tensor in pickle.loads(domains.BASE.read_bytes())}
    child_saved=pickle.loads(gzip.decompress(domains.CHILD.read_bytes()))
    assert child_saved['point_independent'] and child_saved['complete_root_family']
    assert not child_saved['zero_flags_or_roots_removed']
    assert child_saved['construction_source_sha256']==domains.TRANSPORT_SHA
    children={root:(masks,tensor) for root,masks,tensor in child_saved['blocks']}
    assert sorted(children)==data[1][8]
    for child,(masks,tensor) in children.items():
        assert masks==[mask for mask,_ in data[3][child] if mask.bit_count()>=3]
        n=len(masks)+1
        assert tensor.shape==(n*(n+1)//2,48965)
    for root,(flags,tensor) in bases.items():
        high=[mask for mask,_ in data[3][root] if mask.bit_count()>=3]
        assert [tuple(flag) for flag in flags]==[tuple(data[0][root])]+[domains.transport.attach(data[0][root],mask) for mask in high]
        n=len(flags)
        assert tensor.shape==(n*(n+1)//2,6535)
    lift_builder=domains.Lifts(data,children)
    old_by_root={root['root_type']:root for root in visible['roots']}
    result={'source_sha256':files.digest(Path(__file__)),'source_bindings':SOURCE_BINDINGS,
        'prism_pair_scout_sha256':SCOUT_SHA,'independent_p4_replay_sha256':P4_SHA,
        'visible_domain_sha256':VISIBLE_SHA,'prism_zero_closure_sha256':CLOSURE_SHA,
        'old_all_high_mask_coefficientwise_lifts_sha256':OLD_LIFTS_SHA,
        'catalogue_sha256':domains.direct.CATALOGUE_SHA,
        'base_cache_sha256':domains.BASE_SHA,'child_cache_sha256':domains.CHILD_SHA,
        'assumption':'The ambient graph is prism-free (ordinary core coordinate x1=0).',
        'all_prism_containing_types_forced_zero':sorted(zero_types),
        'saved_tensor_terms_are_labelled_induced_embedding_coefficients':True,
        'new_selected_row_identities_hold_modulo_prism_zero_support':True,
        'unrestricted_selected_row_zero_identity_claim':False,
        'all_original_high_mask_domains_retained':True,'roots':[],
        'count_point_loaded':False,'point_scanned':False,'new_product_tensors_generated':False,
        'dense_reduction_loaded':False,'optimizer_called':False}
    totals=Counter()
    support=set()
    peak_cells,peak_root=0,None
    timed_out,error,current=False,None,None
    def deadline(_signum,_frame):
        raise TimeoutError('bounded prism-free clique and zero-support preparation')
    previous=signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        for record in scout['roots']:
            current=record['root_type']
            saved=prepare_root(record,old_by_root[current],data,lift_builder,bases,children,zero_types)
            old_mask=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM})
            try:
                result['roots'].append(saved)
                totals.update(saved['counts'])
                support.update(saved['zero_support_type_indices'])
                cells=saved['conditional_matrix_object_cells']+saved['child_matrix_object_cells']+saved['two_working_matrix_object_cells']
                if cells>peak_cells:
                    peak_cells,peak_root=cells,current
                current=None
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK,old_mask)
    except TimeoutError:
        timed_out=True
    except Exception as problem:
        error=repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    complete=len(result['roots'])==208
    if complete:
        assert totals['all_high_mask_lifts_reconstructed']==5215
        assert totals['previous_representative_lifts_reconstructed_exactly']==1575
        assert totals['new_conditional_rows_supported_on_prism_zeros']==3208
        assert totals['old_visible_directed_rows_rechecked_empty']==65752
        assert totals['old_visible_cliques_covered']==5379
        assert totals['retained_triple_groups_with_saved_cover']==530
        assert totals['remaining_clique_complement']==totals['covered_remaining_cliques']
    result.update(status='complete prism-free clique/orbit and tensor zero-support preparation' if complete else 'UNKNOWN: incomplete prism-free clique preparation',
        complete_root_family=complete,timed_out=timed_out,error=error,unfinished_root_type=current,
        root_types_completed=len(result['roots']),summary=dict(sorted(totals.items())),
        surviving_zero_support_type_indices=sorted(support),
        largest_representative_quotient_order=max((o['quotient_order'] for r in result['roots'] for o in r['orbits']),default=0),
        per_root_cache_sizing={'largest_joint_matrix_object_cells':peak_cells,'largest_joint_cache_root_type':peak_root,
            'illustrative_64_bytes_per_object_cell':64*peak_cells,
            'illustrative_bytes_are_not_a_runtime_RSS_guarantee':True})
    if args.replay:
        assert complete and not timed_out and error is None
        old=read(args.replay)
        old.pop('seconds')
        old.pop('max_rss_kib')
        assert old==groups.normalise(result)
        result={'status':'PASS: complete prism-free clique/orbit and raw zero-support replay',
            'source_sha256':files.digest(Path(__file__)),'certificate_sha256':files.digest(args.replay),
            'summary':dict(sorted(totals.items())),'zero_support_type_count':len(support)}
    result['seconds']=time.monotonic()-started
    result['max_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    content=json.dumps(result,indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(content,compresslevel=9,mtime=0) if args.output.suffix=='.gz' else content)
    print(json.dumps({key:value for key,value in result.items() if key not in ('roots','all_prism_containing_types_forced_zero','surviving_zero_support_type_indices')},indent=2),flush=True)
    print('output_sha256',files.digest(args.output),flush=True)
    return 1 if error else 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',type=Path)
    parser.add_argument('--seconds',type=int,default=30)
    args=parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 30
    raise SystemExit(run(args))
