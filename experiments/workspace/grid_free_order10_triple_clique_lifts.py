"""Exact conditional lifts for all23 five-root triple-clique representatives.

The parent is a principal submatrix of the frozen r5s2 tensor. Selected
subsets use complete scalar caches rooted at6/7/8 vertices. Every internal
edge pattern is classified, and all171 representative union rows are
checked on full labelled-count coefficient supports. No point is loaded.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import pickle
import resource
import signal
import time

import grid_free_order10_triple_clique_scope as scope
import grid_free_order10_double_complement_domains as old
import grid_free_order10_r8s1 as transport


ROOT=Path(__file__).resolve().parents[2]
LOGS=ROOT/'experiments/logs/moments-and-counts'
SCOPE=LOGS/'order10-triple-clique-scope.json.gz'
SCOPE_SHA='7e1c352fcdfccfc2879b4cb451590173fe0d8e56d3a66db5cb28e3cb75f7573e'
SCOPE_SOURCE_SHA='a751481867973862cd2bbbe8d0d4dab164dbbe8df733df172402ee4491fa6fec'
PARENT=ROOT/'experiments/workspace/induced-moments-5-2-512.pickle'
PARENT_SHA='f35f9d2c709d869924fac026ffb036e310f0967b933b36578ec0e1a53463feac'
GENERIC_SHA='1283b15c44f408e0baf2cb1f9abd1c59b4ebee8717ca099c39e52b55c56ea935'
TRANSPORT_SHA='77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def terms(counter):
    return [[int(i),int(c)] for i,c in sorted(counter.items()) if c]


def add_scaled(target,source,coefficient):
    for i,c in source.items():
        target[i]+=coefficient*c


def lower(i,j):
    i,j=max(i,j),min(i,j)
    return i*(i+1)//2+j


def tensor_entry(tensor,row):
    return {int(tensor.indices[k]):int(tensor.data[k])
            for k in range(tensor.indptr[row],tensor.indptr[row+1])}


def principal(record,flags,tensor,data):
    root,high=record['root_type'],record['high_masks']
    rows=tuple(data[0][root])
    assert tuple(flags[0])==rows and len(rows)==5
    positions=[0]+[i for i,flag in enumerate(flags) if len(flag)==6]
    assert [tuple(flags[i]) for i in positions]==[rows]+[transport.attach(rows,mask) for mask in high]
    n=len(positions)
    assert n==record['base_order'] and tensor.shape==(len(flags)*(len(flags)+1)//2,6535)
    selected_rows=[lower(positions[i],positions[j]) for i in range(n) for j in range(i+1)]
    entries=[tensor_entry(tensor,row) for row in selected_rows]
    assert entries[0]=={root:1}
    support={i for entry in entries for i in entry}
    limit=sum(map(len,data[1][:8]))
    assert limit==308 and all(0<=i<limit and len(data[0][i])<=7 for i in support)
    assert all(c>0 for entry in entries for c in entry.values())
    for i in range(1,n):
        assert entries[lower(i,i)]==entries[lower(i,0)]
    coefficient_rows=[terms(entry) for entry in entries]
    return {'root_type':root,'source_flag_count':len(flags),'source_tensor_columns':6535,
        'parent_order':n,'principal_flag_positions':positions,'source_lower_product_rows':selected_rows,
        'labelled_count_coefficient_rows':coefficient_rows,
        'principal_coefficient_rows_sha256':hashlib.sha256(canonical(coefficient_rows)).hexdigest(),
        'nonzero_tensor_support_exclusive_limit':limit,
        'maximum_nonzero_catalogue_type':max(support),'maximum_nonzero_graph_order':max(len(data[0][i]) for i in support),
        'all_binary_diagonal_identities_checked_coefficientwise':True},entries


def actual_extension(rows,selected,edge_word):
    pairs=list(combinations(range(len(selected)),2))
    edges={pair:(edge_word >> i)&1 for i,pair in enumerate(pairs)}
    actual=tuple(rows)
    for j,mask in enumerate(selected):
        extension=mask|sum(edges[i,j] << (5+i) for i in range(j))
        actual=transport.attach(actual,extension)
    violations=[[i,j,(actual[i]&actual[j]).bit_count()+((actual[i] >> j)&1)]
                for i,j in combinations(range(len(actual)),2)
                if (actual[i]&actual[j]).bit_count()+((actual[i] >> j)&1)>2]
    return actual,edges,violations


class LiftBuilder:
    def __init__(self,data,children):
        self.data=data
        self.children=children
        self.builder=transport.Builder(data)

    def build(self,root,high,selected,edge_word):
        selected=tuple(selected)
        assert 1<=len(selected)<=3 and list(selected)==sorted(set(selected))
        assert all(mask in high for mask in selected)
        actual,edges,violations=actual_extension(self.data[0][root],selected,edge_word)
        if violations:
            return None,violations[0]
        current=root
        prefix=tuple(self.data[0][root])
        mapping=list(range(5))
        for j,mask in enumerate(selected):
            actual_mask=mask|sum(edges[i,j] << (5+i) for i in range(j))
            moved=transport.transported_mask(actual_mask,mapping)
            child=self.builder.child_map(current).get(moved)
            assert child is not None
            prefix=transport.attach(prefix,actual_mask)
            mapping=self.builder.transport(prefix,child)
            current=child
        assert prefix==actual
        assert sorted(mapping)==list(range(len(actual)))
        assert all(transport.transported_mask(row,mapping)==self.data[0][current][mapping[i]] for i,row in enumerate(actual))
        child_high=[mask for mask,_ in self.data[3][current] if mask.bit_count()>=3]
        family=self.children[len(actual)]
        if current in family:
            assert family[current][0]==child_high
        else:
            assert not child_high and len(actual) in (6,7)
        positions={mask:i+1 for i,mask in enumerate(child_high)}
        sparse=[[0]]
        for mask in high:
            choices=[]
            for edges_to_selected in range(1 << len(selected)):
                moved=transport.transported_mask(mask|(edges_to_selected << 5),mapping)
                if moved in positions:
                    choices.append(positions[moved])
            if mask in selected:
                assert not choices
                choices=[0]
            assert len(choices)==len(set(choices))
            sparse.append(choices)
        lift={'selected_masks':list(selected),'internal_edge_word':edge_word,
            'internal_edge_pairs':[list(pair) for pair in combinations(range(len(selected)),2)],
            'actual_child_rows':list(actual),'actual_to_child_map':mapping,
            'child_root_type':current,'child_root_order':len(actual),
            'child_high_masks':child_high,'child_scalar_order':len(child_high)+1,'sparse_rows':sparse}
        return lift,None


def cached_entry(children,lift,i,j):
    blocks=children[lift['child_root_order']]
    root=lift['child_root_type']
    if root not in blocks:
        assert i==j==0 and not lift['child_high_masks']
        return {root:1}
    return tensor_entry(blocks[root][1],lower(i,j))


def lifted_entry(children,lift,i,j):
    result=Counter()
    for a in lift['sparse_rows'][i]:
        for b in lift['sparse_rows'][j]:
            result.update(cached_entry(children,lift,a,b))
    return result


def literal_controls(lift,high):
    actual=tuple(lift['actual_child_rows'])
    mapping=lift['actual_to_child_map']
    selected=lift['selected_masks']
    inverse=[0]*len(mapping)
    for i,j in enumerate(mapping):
        inverse[j]=i
    cases=[None]+lift['child_high_masks']
    for chosen in cases:
        if chosen is None:
            host=actual
            Y=[1]+[0]*len(lift['child_high_masks'])
        else:
            actual_mask=transport.transported_mask(chosen,inverse)
            host=transport.attach(actual,actual_mask)
            assert scope.caps(host)
            Y=[1]+[int(mask==chosen) for mask in lift['child_high_masks']]
        counts=Counter(row&31 for row in host[5:])
        X=[1]+[counts[mask] for mask in high]
        assert all(x in (0,1) for x in X)
        image=[sum(Y[j] for j in sparse) for sparse in lift['sparse_rows']]
        assert image==X and all(counts[mask]==1 for mask in selected)
    return len(cases)


def prepare_root(record,data,parents,children,builder):
    root,high,n=record['root_type'],record['high_masks'],record['base_order']
    extraction,parent=principal(record,*parents[root],data)
    counts=Counter(root_types=1,parent_principal_entries=len(parent),high_masks=len(high))
    needed=record['needed_conditional_subset_scope']
    registry=[]
    by_subset={}
    child_types={}
    for spec in needed:
        selected=spec['selected_masks']
        count=len(selected)
        possibilities=1 << (count*(count-1)//2)
        lifts=[]
        failures=[]
        for edge_word in range(possibilities):
            lift,violation=builder.build(root,high,selected,edge_word)
            counts['all_internal_edge_patterns_classified']+=1
            if lift is None:
                failures.append({'internal_edge_word':edge_word,'first_visible_cap_violation':violation})
                counts['inadmissible_internal_edge_patterns']+=1
            else:
                controls=literal_controls(lift,high)
                lift['literal_selected_root_and_one_extra_vertex_controls']=controls
                counts['literal_lift_controls']+=controls
                counts['admissible_internal_edge_patterns']+=1
                counts[f'admissible_children_for_subset_size_{count}']+=1
                child_types[lift['child_root_type']]=lift['child_scalar_order']
                lengths=[len(sparse) for sparse in lift['sparse_rows']]
                counts['sparse_lower_lift_products_upper_bound']+=(sum(lengths)**2+sum(v*v for v in lengths))//2
                lifts.append(lift)
        assert len(lifts)+len(failures)==possibilities
        assert len(lifts)<=spec['internal_edge_choice_upper_bound']
        if count<=2:
            assert lifts
        else:
            counts['collectively_impossible_selected_triples']+=not bool(lifts)
        entry={'selected_masks':selected,'subset_size':count,'all_internal_edge_patterns':possibilities,
            'admissible_conditional_lifts':lifts,'inadmissible_patterns':failures,
            'zero_conditional_contribution':not bool(lifts)}
        by_subset[tuple(selected)]=len(registry)
        registry.append(entry)
        counts[f'conditional_registry_subsets_size_{count}']+=1
    representatives=[]
    for orbit in record['triple_orbits']:
        case=record['candidate_triples'][orbit['representative_candidate_index']]
        signed=[]
        for term in case['nonconstant_squarefree_terms']:
            key=tuple(term['masks'])
            assert key in by_subset
            signed.append([by_subset[key],term['coefficient']])
        row_checks=[]
        for i in case['union_base_positions']:
            occurrences=0
            for j in range(n):
                combined=Counter(parent[lower(i,j)])
                occurrences+=len(combined)
                for index,coefficient in signed:
                    for lift in registry[index]['admissible_conditional_lifts']:
                        value=lifted_entry(children,lift,i,j)
                        occurrences+=len(value)
                        add_scaled(combined,value,coefficient)
                assert not any(combined.values())
                counts['union_row_entries_checked_coefficientwise']+=1
            counts['union_rows_checked_coefficientwise']+=1
            counts['signed_coefficient_occurrences_replayed']+=occurrences
            row_checks.append({'base_position':i,'mask':high[i-1],'entries_checked':n,
                'signed_coefficient_occurrences':occurrences,'all_entries_identically_zero':True})
        representatives.append({'representative_candidate_index':orbit['representative_candidate_index'],
            'orbit_size':orbit['orbit_size'],'clique_indices':case['clique_indices'],
            'union_masks':case['union_masks'],'union_base_positions':case['union_base_positions'],
            'quotient_order':case['quotient_order'],'quotient_lower_entries':case['quotient_lower_entries'],
            'signed_conditional_registry_entries':signed,'coefficientwise_union_row_checks':row_checks})
        counts['direct_representatives_prepared']+=1
        counts['candidate_triples_covered_by_root_actions']+=orbit['orbit_size']
    assert len(registry)==len(needed)
    cells=(len(registry)+2)*n*n+sum(order*order for order in child_types.values())
    return {'root_type':root,'high_masks':high,'base_order':n,'parent_principal_extraction':extraction,
        'conditional_subset_registry':registry,'representatives':representatives,
        'all_scope_domains_retained_by_certificate_reference':True,
        'actual_conditional_and_child_and_two_working_matrix_cells':cells,
        'distinct_conditional_child_types':[[child,order] for child,order in sorted(child_types.items())],
        'counts':dict(sorted(counts.items()))}


def run(args):
    started=time.monotonic()
    for path,sha in ((SCOPE,SCOPE_SHA),(Path(scope.__file__),SCOPE_SOURCE_SHA),
        (PARENT,PARENT_SHA),(Path(old.__file__),GENERIC_SHA),(Path(transport.__file__),TRANSPORT_SHA),
        (scope.CATALOGUE,scope.CATALOGUE_SHA),(old.BASE,old.BASE_SHA),
        (old.seven.BASE,old.seven.BASE_SHA),(old.seven.CHILD,old.seven.CHILD_SHA)):
        assert digest(path)==sha
    ledger=json.loads(gzip.decompress(SCOPE.read_bytes()))
    assert ledger['complete_root_family'] and ledger['error'] is None and not ledger['timed_out']
    assert ledger['summary']['candidate_orbits']==23 and ledger['summary']['candidate_triples']==236
    data=pickle.loads(scope.CATALOGUE.read_bytes())
    parents={root:(flags,tensor) for root,flags,tensor in pickle.loads(PARENT.read_bytes())}
    six={root:([flag[-1] for flag in flags[1:]],tensor) for root,flags,tensor in pickle.loads(old.BASE.read_bytes())}
    seven={root:([flag[-1] for flag in flags[1:]],tensor) for root,flags,tensor in pickle.loads(old.seven.BASE.read_bytes())}
    cache8=pickle.loads(gzip.decompress(old.seven.CHILD.read_bytes()))
    assert cache8['point_independent'] and cache8['complete_root_family'] and not cache8['zero_flags_or_roots_removed']
    eight={root:(masks,tensor) for root,masks,tensor in cache8['blocks']}
    assert sorted(parents)==data[1][5] and len(six)==55 and len(seven)==203 and sorted(eight)==data[1][8]
    children={6:six,7:seven,8:eight}
    for size,blocks in children.items():
        for root,(masks,tensor) in blocks.items():
            assert len(data[0][root])==size
            assert masks==[mask for mask,_ in data[3][root] if mask.bit_count()>=3]
            n=len(masks)+1
            columns=48965 if size==8 else 6535
            assert tensor.shape==(n*(n+1)//2,columns)
            assert all(int(c)>0 for c in tensor.data)
            assert max((int(i) for i in tensor.indices),default=-1)<sum(map(len,data[1][:size+3]))
    builder=LiftBuilder(data,children)
    result={'source_sha256':digest(Path(__file__)),'scope_certificate_sha256':SCOPE_SHA,
        'scope_source_sha256':SCOPE_SOURCE_SHA,'parent_r5s2_cache_sha256':PARENT_SHA,
        'six_root_cache_sha256':old.BASE_SHA,'seven_root_cache_sha256':old.seven.BASE_SHA,
        'eight_root_cache_sha256':old.seven.CHILD_SHA,'catalogue_sha256':scope.CATALOGUE_SHA,
        'transport_source_sha256':TRANSPORT_SHA,'roots':[],
        'normalization':'Labelled induced embeddings; selected distinct high masks fix free labels with no factorial or automorphism divisor.',
        'parent_extraction_is_principal_submatrix_only':True,
        'all_internal_edge_patterns_retained_or_rejected_by_explicit_visible_cap':True,
        'zero_selected_triples_retained_in_registry':True,
        'count_point_loaded':False,'point_scanned':False,'new_product_tensors_generated':False,
        'dense_reduction_loaded':False,'optimizer_called':False}
    total=Counter()
    current,error,timed_out=None,None,False
    def deadline(_sig,_frame):
        raise TimeoutError('bounded triple-clique conditional lift preparation')
    previous=signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        for record in ledger['roots']:
            current=record['root_type']
            prepared=prepare_root(record,data,parents,children,builder)
            blocked=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM})
            try:
                result['roots'].append(prepared)
                total.update(prepared['counts'])
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
    if complete:
        assert total['direct_representatives_prepared']==23
        assert total['candidate_triples_covered_by_root_actions']==236
        assert total['union_rows_checked_coefficientwise']==171
    result.update(status='complete exact triple-clique conditional lifts and union-row identities' if complete else 'UNKNOWN: incomplete triple-clique lift preparation',
        complete_preparation=complete,timed_out=timed_out,error=error,unfinished_root=current,summary=dict(sorted(total.items())),
        largest_per_root_matrix_cells=max((r['actual_conditional_and_child_and_two_working_matrix_cells'] for r in result['roots']),default=0))
    if args.replay:
        assert complete
        old_result=json.loads(gzip.decompress(args.replay.read_bytes()))
        old_result.pop('seconds'); old_result.pop('max_rss_kib')
        assert old_result==json.loads(json.dumps(result))
        result={'status':'PASS: triple-clique parent extraction, every edge pattern, lifts and exact row identities replayed',
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
