"""Point-independent scope census for five-root triple-clique absence.

This builds only mask/clique domains, formal Boolean expansions, root
actions and conservative work estimates. It constructs no conditional
lift, product tensor, count matrix or numerical separator.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from math import comb,prod
from pathlib import Path
import pickle
import resource
import signal
import time

import grid_free_order10_complement_cliques as cliques
import grid_free_order10_complement_clique_orbits as groups
import grid_free_order10_complement_visible_domains as visible


CATALOGUE=Path('/tmp/conway99-order10-catalogue.pickle')
CATALOGUE_SHA='1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'
BINDINGS={
    'grid_free_order10_complement_cliques.py':'765f0ca7ca7ffcb16e6c518d80c70ffca99ba2c0c46d682077f1027ae47fe912',
    'grid_free_order10_complement_clique_orbits.py':'5569a81838301fa54dc2401b98592a91fb302b7ed7a3110983a6f475a1107130',
    'grid_free_order10_complement_visible_domains.py':'d89248dce73849059afa12cf1c731f31dcafa8a0769ccde3b25574c67ec4c54a',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def attach(rows,mask):
    n=len(rows)
    return tuple(row|(((mask >> i)&1) << n) for i,row in enumerate(rows))+(mask,)


def caps(rows):
    return all((rows[i]&rows[j]).bit_count()+((rows[i] >> j)&1)<=2
               for i in range(len(rows)) for j in range(i))


def conditional_choice_bound(selected,allowed_edges):
    return prod(len(allowed_edges[tuple(sorted(pair))]) for pair in combinations(selected,2))


def independent(selected,positions,adjacency):
    return all(not (adjacency[positions[a]] >> positions[b]&1) for a,b in combinations(selected,2))


def expansion(clique_masks,positions,adjacency):
    polynomial={():1}
    for clique in clique_masks:
        expanded=Counter(polynomial)
        for old,coefficient in polynomial.items():
            for mask in clique:
                merged=tuple(sorted(set(old)|{mask}))
                if independent(merged,positions,adjacency):
                    expanded[merged]-=coefficient
        polynomial={key:value for key,value in expanded.items() if value}
    union=sorted(set().union(*map(set,clique_masks)))
    memberships={mask:sum(1 << i for i,C in enumerate(clique_masks) if mask in C) for mask in union}
    assert all(memberships.values())
    for a,b in combinations(union,2):
        if independent((a,b),positions,adjacency):
            assert memberships[a]&memberships[b]==0
    expected={():1}
    for size in (1,2,3):
        for selected in combinations(union,size):
            if independent(selected,positions,adjacency):
                expected[selected]=(-1)**size
    assert polynomial==expected
    # Disjoint nonempty membership subsets of a three-set imply size <=3.
    cancellations=[]
    for chosen in union:
        projected=Counter()
        matching=[]
        for selected,coefficient in polynomial.items():
            merged=tuple(sorted(set(selected)|{chosen}))
            if independent(merged,positions,adjacency):
                projected[merged]+=coefficient
            if chosen in selected:
                smaller=tuple(mask for mask in selected if mask!=chosen)
                assert polynomial[smaller]==-coefficient
                matching.append([list(smaller),list(selected)])
        assert not any(projected.values())
        cancellations.append({'union_mask':chosen,'opposite_sign_subset_pairs':matching})
    return union,memberships,polynomial,cancellations


def root_scope(root,data):
    rows=tuple(data[0][root])
    assert len(rows)==5 and caps(rows)
    allowed=[mask for mask in range(32) if caps(attach(rows,mask))]
    assert allowed==[mask for mask,_ in data[3][root]]
    high=[mask for mask in allowed if mask.bit_count()>=3]
    n=len(high)+1
    positions={mask:i for i,mask in enumerate(high)}
    residuals=[[i,j,2-((rows[i] >> j)&1)-(rows[i]&rows[j]).bit_count()]
               for i,j in combinations(range(5),2)]
    q1=[(1 << i)|(1 << j) for i,j,q in residuals if q==1]
    adjacency=[0]*len(high)
    allowed_edges={}
    for a,b in combinations(high,2):
        overlap=a&b
        forbidden=overlap.bit_count()>=3 or any(overlap&pair==pair for pair in q1)
        edge_choices=[e for e in (0,1) if caps(attach(attach(rows,a),b|(e << 5)))]
        assert forbidden==(not edge_choices)
        if forbidden:
            adjacency[positions[a]]|=1 << positions[b]
            adjacency[positions[b]]|=1 << positions[a]
        else:
            assert edge_choices[0]==0
            allowed_edges[a,b]=edge_choices
    codes=cliques.bron_kerbosch(adjacency)
    alternate,order,intermediate=visible.incremental_cliques(adjacency,high)
    assert codes==alternate
    records=[]
    counts=Counter(root_types=1,high_masks=len(high),literal_high_mask_pairs_checked=comb(len(high),2))
    for code in sorted(codes):
        cliques.maximal(code,(1 << len(high))-1,adjacency)
        masks=[high[i] for i in cliques.members(code)]
        common=31
        for mask in masks:
            common &= mask
        witness=next(([i,j,1] for i,j,q in residuals if q==1 and common >> i&1 and common >> j&1),None)
        kind='constant_only' if not masks else 'quota_one_redundant' if witness else 'remaining'
        record={'masks':masks,'classification':kind}
        if kind=='quota_one_redundant':
            pair=(1 << witness[0])|(1 << witness[1])
            record['quota_one_pair']=witness
            record['positive_sum_other_masks']=[mask for mask in allowed if mask&pair==pair and mask not in masks]
            assert pair in record['positive_sum_other_masks']
        records.append(record)
        counts[kind+'_maximal_cliques']+=1
    remaining=[i for i,C in enumerate(records) if C['classification']=='remaining']
    candidates=[]
    for triple in combinations(remaining,3):
        Cs=[records[i]['masks'] for i in triple]
        union,memberships,polynomial,cancellations=expansion(Cs,positions,adjacency)
        subsets=sorted((S for S in polynomial if S),key=lambda S:(len(S),S))
        degree_counts={str(size):sum(len(S)==size for S in subsets) for size in (1,2,3)}
        q=n-len(union)
        assert q>=1
        candidates.append({'clique_indices':list(triple),'union_masks':union,
            'union_base_positions':[positions[mask]+1 for mask in union],
            'clique_membership_bits':[[mask,memberships[mask]] for mask in union],
            'nonconstant_squarefree_terms':[{'masks':list(S),'coefficient':polynomial[S],
                'internal_edge_choice_upper_bound':conditional_choice_bound(S,allowed_edges)} for S in subsets],
            'term_counts_by_degree':degree_counts,
            'formal_idempotent_product_equals_compatible_subset_sum':True,
            'compatible_subsets_have_size_at_most_three':True,
            'formal_union_row_cancellations':cancellations,
            'quotient_order':q,'quotient_lower_entries':q*(q+1)//2})
        counts['formal_factor_products_compared']+=1
        counts['formal_union_rows_checked']+=len(union)
    counts['all_distinct_maximal_clique_triples']=comb(len(records),3)
    counts['candidate_triples']=len(candidates)
    counts['quota_one_redundant_triples']=counts['all_distinct_maximal_clique_triples']-len(candidates)
    counts['candidate_roots']=int(bool(candidates))
    group,permutations=groups.all_automorphisms(rows)
    counts['degree_preserving_permutations_checked']=permutations
    counts['root_automorphisms_enumerated']=len(group)
    clique_index={tuple(C['masks']):i for i,C in enumerate(records)}
    triple_index={tuple(case['clique_indices']):i for i,case in enumerate(candidates)}
    actions=[]
    for move in sorted(group):
        assert groups.automorphism(rows,move)
        images={mask:groups.move_mask(mask,move) for mask in high}
        assert sorted(images.values())==high
        p=[positions[images[mask]] for mask in high]
        assert all(sum(1 << p[j] for j in cliques.members(row))==adjacency[p[i]] for i,row in enumerate(adjacency))
        cmap=[]
        for C in records:
            image=clique_index[tuple(sorted(images[mask] for mask in C['masks']))]
            assert records[image]['classification']==C['classification']
            cmap.append(image)
        actions.append({'vertex_map':list(move),'clique_image':cmap})
    pending=set(range(len(candidates)))
    orbits=[]
    needed=set()
    while pending:
        representative=min(pending)
        case=candidates[representative]
        found={}
        for action in actions:
            image_triple=tuple(sorted(action['clique_image'][i] for i in case['clique_indices']))
            image=triple_index[image_triple]
            if image in found:
                continue
            move=action['vertex_map']
            transformed={tuple(sorted(groups.move_mask(m,move) for m in term['masks'])):term['coefficient']
                         for term in case['nonconstant_squarefree_terms']}
            actual={tuple(term['masks']):term['coefficient'] for term in candidates[image]['nonconstant_squarefree_terms']}
            assert transformed==actual
            found[image]={'candidate_index':image,'representative_to_member_vertex_map':move}
        assert set(found)<=pending
        pending-=set(found)
        orbits.append({'representative_candidate_index':representative,'orbit_size':len(found),
            'quotient_order':case['quotient_order'],'quotient_lower_entries':case['quotient_lower_entries'],
            'members':[found[i] for i in sorted(found)]})
        for term in case['nonconstant_squarefree_terms']:
            needed.add(tuple(term['masks']))
        counts['representative_quotient_lower_entries']+=case['quotient_lower_entries']
        counts['representative_full_matrix_additions_subtractions']+=len(case['nonconstant_squarefree_terms'])*n*n
        counts['representative_union_rows']+=len(case['union_masks'])
    assert sum(orbit['orbit_size'] for orbit in orbits)==len(candidates)
    counts['candidate_orbits']=len(orbits)
    registry=[]
    all_child_cells=0
    largest_child_order=1
    for selected in sorted(needed,key=lambda S:(len(S),S)):
        size=len(selected)
        edge_bound=conditional_choice_bound(selected,allowed_edges)
        child_root_order=5+size
        child_order_bound=1+sum(comb(child_root_order,k) for k in range(3,child_root_order+1))
        registry.append({'selected_masks':list(selected),'selected_count':size,
            'internal_edge_choice_upper_bound':edge_bound,'child_root_order':child_root_order,
            'child_scalar_order_upper_bound':child_order_bound})
        counts[f'needed_conditional_subsets_size_{size}']+=1
        counts[f'conditional_edge_cases_upper_bound_size_{size}']+=edge_bound
        counts['sparse_lower_lift_products_upper_bound']+=edge_bound*(n*(n+1)//2)*(4**size)
        all_child_cells+=edge_bound*child_order_bound*child_order_bound
        largest_child_order=max(largest_child_order,child_order_bound)
    streamed_cells=(len(needed)+2)*n*n+largest_child_order*largest_child_order
    return {'root_type':root,'root_rows':list(rows),'allowed_masks':allowed,'high_masks':high,'base_order':n,
        'visible_incompatibility_adjacency':adjacency,
        'compatible_pair_edge_choices':[{'masks':list(pair),'allowed_edges':edges} for pair,edges in sorted(allowed_edges.items())],
        'bron_kerbosch_equals_incremental':True,'incremental_vertex_order':order,'incremental_counts':intermediate,
        'maximal_cliques':records,'candidate_triples':candidates,'root_actions':actions,'triple_orbits':orbits,
        'needed_conditional_subset_scope':registry,
        'conditional_matrices_plus_one_streamed_child_cells_upper_bound':streamed_cells,
        'uncanonicalized_all_child_matrix_cells_upper_bound':all_child_cells,
        'counts':dict(sorted(counts.items()))}


def run(args):
    started=time.monotonic()
    assert digest(CATALOGUE)==CATALOGUE_SHA
    for name,sha in BINDINGS.items():
        assert digest(Path(__file__).with_name(name))==sha
    data=pickle.loads(CATALOGUE.read_bytes())
    result={'source_sha256':digest(Path(__file__)),'dependency_source_hashes':BINDINGS,
        'catalogue_sha256':CATALOGUE_SHA,'roots':[],
        'point_independent':True,'no_root_or_flag_pruning_by_point':True,
        'formal_Boolean_identities_only':True,'cached_tensor_coefficient_identities_checked':False,
        'conditional_lifts_constructed':False,'product_tensor_cache_loaded':False,
        'count_point_loaded':False,'point_scanned':False,'dense_reduction_loaded':False,'optimizer_called':False}
    total=Counter()
    current,error,timed_out=None,None,False
    def deadline(_signum,_frame):
        raise TimeoutError('bounded five-root triple-clique scope census')
    previous=signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        for root in data[1][5]:
            current=root
            record=root_scope(root,data)
            blocked=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM})
            try:
                result['roots'].append(record)
                total.update(record['counts'])
                current=None
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK,blocked)
    except TimeoutError:
        timed_out=True
    except Exception as problem:
        error=repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    complete=[r['root_type'] for r in result['roots']]==data[1][5] and not error and not timed_out
    result.update(status='complete five-root triple-clique scope census' if complete else 'UNKNOWN: incomplete triple-clique scope census',
        complete_root_family=complete,timed_out=timed_out,error=error,unfinished_root=current,summary=dict(sorted(total.items())),
        largest_representative_quotient_order=max((o['quotient_order'] for r in result['roots'] for o in r['triple_orbits']),default=0),
        largest_streamed_matrix_cell_bound=max((r['conditional_matrices_plus_one_streamed_child_cells_upper_bound'] for r in result['roots']),default=0),
        largest_uncanonicalized_all_child_cell_bound=max((r['uncanonicalized_all_child_matrix_cells_upper_bound'] for r in result['roots']),default=0))
    if args.replay:
        assert complete
        old=json.loads(gzip.decompress(args.replay.read_bytes()))
        old.pop('seconds')
        old.pop('max_rss_kib')
        assert old==groups.normalise(result)
        result={'status':'PASS: complete five-root triple-clique scope replay',
            'source_sha256':digest(Path(__file__)),'certificate_sha256':digest(args.replay),'summary':dict(sorted(total.items()))}
    result['seconds']=time.monotonic()-started
    result['max_rss_kib']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    raw=json.dumps(result,indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(raw,compresslevel=9,mtime=0) if args.output.suffix=='.gz' else raw)
    print(json.dumps({key:value for key,value in result.items() if key!='roots'},indent=2),flush=True)
    print('output_sha256',digest(args.output),flush=True)
    return 1 if error else 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',type=Path)
    parser.add_argument('--seconds',type=int,default=60)
    args=parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 60
    raise SystemExit(run(args))
