"""Bounded exact-point discovery scan of 23 five-root triple-clique matrices.

Preparation reads the frozen domain, lift, replay and point certificates.
The separate scan contracts existing tensors with Python integers. A
negative direction is accepted only after exact quadratic and induced-form
checks. Fresh literal reconstruction remains a separate gate.
"""

import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import pickle
import resource
import signal
import time

import numpy as np
from threadpoolctl import threadpool_limits

import grid_free_order10_triple_clique_lifts as lifts
import grid_free_order10_complement_scan as exact
from grid_free_order10_r8s1_scan import FullScanner
import grid_free_order10_scaled as files


ROOT=Path(__file__).resolve().parents[2]
LOGS=ROOT/'experiments/logs/moments-and-counts'
LIFTS=LOGS/'order10-triple-clique-lifts.json.gz'
LIFTS_SHA='a6f5315d82c74fb3432fb357f247ef11c1aabbdae85df3ca22f0d86ed74db8b8'
LIFTS_SOURCE_SHA='d70999d19f1a49284a211edcbeb7d68e03025935523fed78c7a798ad6060ea66'
LIFTS_REPLAY=LOGS/'order10-triple-clique-lifts-replay.json'
LIFTS_REPLAY_SHA='6f9a25dd7c5e8825ace995bf324240674dbd79f10bec745c502619a0b44f3133'
WITNESS=LOGS/'prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json'
WITNESS_SHA='0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'
EXACT_SHA='806aea35eedde9f09eda5c5b0b5113b62e0c37e218a46c6ad727ea6950ca74a7'
NEGATIVE_SHA='71f06ef752adff6d49f88136b9e82f054f6485a2b2867c2cd4ef9f7ef7f82887'


def read(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def inputs():
    old=lifts.old
    for path,sha in ((LIFTS,LIFTS_SHA),(Path(lifts.__file__),LIFTS_SOURCE_SHA),
        (LIFTS_REPLAY,LIFTS_REPLAY_SHA),(lifts.SCOPE,lifts.SCOPE_SHA),
        (Path(lifts.scope.__file__),lifts.SCOPE_SOURCE_SHA),
        (Path(old.__file__),lifts.GENERIC_SHA),
        (Path(lifts.transport.__file__),lifts.TRANSPORT_SHA),
        (lifts.PARENT,lifts.PARENT_SHA),(old.BASE,old.BASE_SHA),
        (old.seven.BASE,old.seven.BASE_SHA),(old.seven.CHILD,old.seven.CHILD_SHA),
        (Path(exact.__file__),EXACT_SHA),
        (Path(__file__).with_name('grid_free_order10_r8s1_scan.py'),NEGATIVE_SHA),
        (WITNESS,WITNESS_SHA)):
        assert files.digest(path)==sha
    ledger=read(LIFTS)
    scope=read(lifts.SCOPE)
    replay=read(LIFTS_REPLAY)
    assert ledger['source_sha256']==LIFTS_SOURCE_SHA
    assert ledger['complete_preparation'] and ledger['error'] is None and not ledger['timed_out']
    assert ledger['scope_certificate_sha256']==lifts.SCOPE_SHA
    assert not ledger['count_point_loaded'] and not ledger['point_scanned']
    assert scope['complete_root_family'] and scope['error'] is None and not scope['timed_out']
    assert replay['status'].startswith('PASS:')
    assert replay['source_sha256']==LIFTS_SOURCE_SHA and replay['certificate_sha256']==LIFTS_SHA
    assert replay['summary']==ledger['summary']
    assert len(ledger['roots'])==len(scope['roots'])==21
    for root,domain in zip(ledger['roots'],scope['roots']):
        assert root['root_type']==domain['root_type']
        assert root['high_masks']==domain['high_masks']
        assert root['base_order']==domain['base_order']
        extraction=root['parent_principal_extraction']
        rows=extraction['labelled_count_coefficient_rows']
        assert lifts.hashlib.sha256(lifts.canonical(rows)).hexdigest()==extraction['principal_coefficient_rows_sha256']
        assert len(rows)==root['base_order']*(root['base_order']+1)//2
        assert extraction['nonzero_tensor_support_exclusive_limit']==308
        assert all(0<=index<308 and type(c) is int and c>0 for row in rows for index,c in row)
        assert len(root['representatives'])==len(domain['triple_orbits'])
        for case,orbit in zip(root['representatives'],domain['triple_orbits']):
            assert case['representative_candidate_index']==orbit['representative_candidate_index']
            assert case['orbit_size']==orbit['orbit_size']
            original=domain['candidate_triples'][case['representative_candidate_index']]
            for key in ('clique_indices','union_masks','union_base_positions','quotient_order','quotient_lower_entries'):
                assert case[key]==original[key]
            actual=[]
            for index,coefficient in case['signed_conditional_registry_entries']:
                item=root['conditional_subset_registry'][index]
                assert coefficient==(-1)**item['subset_size']
                actual.append({'masks':item['selected_masks'],'coefficient':coefficient})
            assert actual==original['nonconstant_squarefree_terms']
    witness=read(WITNESS)
    counts=witness['induced_counts']
    cores=witness['rounded_core_values']
    assert len(counts)==48965 and all(type(c) is int and c>=0 for c in counts)
    assert len(cores)==550 and all(type(c) is int for c in cores)
    assert witness['x521_zero'] and len(witness['required_zero_coordinates'])==59
    assert cores[0]==1 and cores[1]==cores[521]==0
    assert all(cores[i]==0 for i in witness['required_zero_coordinates'])
    return ledger,scope,counts


def metadata(ledger,scope):
    summary=ledger['summary']
    cases=[case for root in ledger['roots'] for case in root['representatives']]
    assert len(cases)==23 and sum(case['orbit_size'] for case in cases)==236
    assert sum(len(case['union_base_positions']) for case in cases)==171
    assert sum(case['quotient_lower_entries'] for case in cases)==958
    return {'source_sha256':files.digest(Path(__file__)),
        'lift_source_sha256':LIFTS_SOURCE_SHA,'lift_certificate_sha256':LIFTS_SHA,
        'lift_cold_replay_sha256':LIFTS_REPLAY_SHA,
        'scope_source_sha256':lifts.SCOPE_SOURCE_SHA,'scope_certificate_sha256':lifts.SCOPE_SHA,
        'parent_cache_sha256':lifts.PARENT_SHA,'parent_true_support_order':7,
        'parent_padded_tensor_columns':6535,'parent_nonzero_support_exclusive_limit':308,
        'six_root_cache_sha256':lifts.old.BASE_SHA,
        'seven_root_cache_sha256':lifts.old.seven.BASE_SHA,
        'eight_root_cache_sha256':lifts.old.seven.CHILD_SHA,
        'catalogue_sha256':lifts.scope.CATALOGUE_SHA,
        'exact_form_helper_sha256':EXACT_SHA,'negative_direction_helper_sha256':NEGATIVE_SHA,
        'integer_witness_sha256':WITNESS_SHA,
        'root_domains_retained':21,'root_types_with_direct_representatives':5,
        'direct_representatives_to_scan':23,'candidate_triples_covered_by_congruence':236,
        'quota_one_redundant_triples_directly_scanned':0,
        'quota_one_redundant_triples':scope['summary']['quota_one_redundant_triples'],
        'quota_one_redundancy_requires_child_localizers_and_count_identities':True,
        'quota_one_redundancy_is_not_a_point_PSD_certificate':True,
        'representative_union_rows_to_check':171,'representative_quotient_lower_entries':958,
        'largest_representative_quotient_order':max(case['quotient_order'] for case in cases),
        'conditional_registry_entries_by_selected_size':[summary[f'conditional_registry_subsets_size_{k}'] for k in (1,2,3)],
        'admissible_children_by_selected_size':[summary[f'admissible_children_for_subset_size_{k}'] for k in (1,2,3)],
        'collectively_impossible_selected_triples':summary['collectively_impossible_selected_triples'],
        'sparse_lower_lift_products_upper_bound':summary['sparse_lower_lift_products_upper_bound'],
        'largest_per_root_matrix_cells':ledger['largest_per_root_matrix_cells'],
        'maximum_scan_seconds':60,'threads':1,
        'all_count_contractions_use_Python_integers':True,
        'all_union_rows_checked_exactly_before_deletion':True,
        'conditional_matrices_cached_per_root':True,
        'no_root_or_flag_removed_from_domain_by_point_value':True,
        'additional_zero_rows_removed_only_after_exact_entry_checks':True,
        'independent_supported_product_replay_deferred':True,
        'new_product_tensors_generated':False,'dense_reduction_loaded':False,'optimizer_called':False}


def parent_matrix(root,embeddings):
    n=root['base_order']
    rows=root['parent_principal_extraction']['labelled_count_coefficient_rows']
    matrix=np.empty((n,n),dtype=object)
    for i in range(n):
        for j in range(i+1):
            value=sum(coefficient*embeddings[index] for index,coefficient in rows[lifts.lower(i,j)])
            assert type(value) is int
            matrix[i,j]=matrix[j,i]=value
    return matrix


def lifted_matrix(lift,child,n):
    sparse=lift['sparse_rows']
    assert len(sparse)==n and sparse[0]==[0]
    matrix=np.empty((n,n),dtype=object)
    for i in range(n):
        for j in range(i+1):
            value=sum(int(child[u,v]) for u in sparse[i] for v in sparse[j])
            matrix[i,j]=matrix[j,i]=value
    return matrix


def parent_form(root,vector,automorphisms):
    result=Counter()
    rows=root['parent_principal_extraction']['labelled_count_coefficient_rows']
    for i in range(len(vector)):
        for j in range(i+1):
            weight=vector[i]*vector[j]*(1 if i==j else 2)
            for index,coefficient in rows[lifts.lower(i,j)]:
                result[index]+=weight*coefficient*automorphisms[index]
    return result


def negative_form(root,case,full,quadratic,parent,children,child_matrix,automorphisms,counts):
    V=np.asarray(full,dtype=object)
    combined=parent_form(root,full,automorphisms)
    identity_value=int(V@parent@V)
    child_vectors=[]
    for index,coefficient in case['signed_conditional_registry_entries']:
        item=root['conditional_subset_registry'][index]
        for lift in item['admissible_conditional_lifts']:
            w=[0]*lift['child_scalar_order']
            for value,row in zip(full,lift['sparse_rows']):
                for j in row:
                    w[j]+=value
            W=np.asarray(w,dtype=object)
            identity_value+=coefficient*int(W@child_matrix(lift)@W)
            child=lift['child_root_type']
            blocks=children[lift['child_root_order']]
            if child in blocks:
                form=exact.raw_form(blocks[child][1],w,automorphisms)
            else:
                assert len(w)==1
                form={child:w[0]*w[0]*automorphisms[child]}
            for graph,c in form.items():
                combined[graph]+=coefficient*c
            child_vectors.append({'sign':coefficient,'registry_id':index,
                'selected_masks':lift['selected_masks'],'internal_edge_word':lift['internal_edge_word'],
                'child_root_type':child,'integer_child_vector':w})
    assert identity_value==quadratic<0
    accepted=exact.accepted_form(combined,counts,quadratic)
    return {'integer_parent_vector':full,'conditional_child_vectors':child_vectors,
        'integer_quadratic_value':quadratic,**accepted}


def run(args,prepared):
    total_started=time.monotonic()
    ledger,scope,counts=inputs()
    assert prepared==metadata(ledger,scope)
    assert files.digest(args.catalogue)==lifts.scope.CATALOGUE_SHA
    data=pickle.loads(args.catalogue.read_bytes())
    assert [root['root_type'] for root in ledger['roots']]==data[1][5]
    six={root:([flag[-1] for flag in flags[1:]],T) for root,flags,T in pickle.loads(lifts.old.BASE.read_bytes())}
    seven={root:([flag[-1] for flag in flags[1:]],T) for root,flags,T in pickle.loads(lifts.old.seven.BASE.read_bytes())}
    saved8=pickle.loads(gzip.decompress(lifts.old.seven.CHILD.read_bytes()))
    assert saved8['point_independent'] and saved8['complete_root_family']
    assert not saved8['zero_flags_or_roots_removed']
    eight={root:(masks,T) for root,masks,T in saved8['blocks']}
    assert len(six)==55 and len(seven)==203 and sorted(eight)==data[1][8]
    children={6:six,7:seven,8:eight}
    automorphisms=[int(value) for value in data[2]]
    embeddings=[a*c for a,c in zip(automorphisms,counts)]
    assert all(type(value) is int for value in embeddings)
    result={'source_sha256':files.digest(Path(__file__)),
        'preparation_sha256':files.digest(args.preparation),'preparation':prepared,
        'representative_records':[],'negative_blocks':[],'unique_induced_cuts':[],
        'unconfirmed_numeric_negatives':[],
        'direct_representatives_completed':0,'triples_covered_by_root_congruence':0,
        'union_rows_checked_exactly_zero':0,'completed_candidate_roots':0,
        'PSD_feasibility_certified':False,'independent_supported_product_replay_complete':False,
        'new_product_tensors_generated':False,'dense_reduction_loaded':False,'optimizer_called':False}
    known={}
    timed_out,error,current=False,None,None
    scan_started=time.monotonic()

    def commit(record,negative):
        blocked=signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM})
        try:
            if negative is not None:
                key=tuple(map(tuple,negative['primitive_induced_count_form']))
                if key not in known:
                    known[key]=len(result['unique_induced_cuts'])
                    result['unique_induced_cuts'].append({'terms':negative['primitive_induced_count_form'],
                        'exact_value_at_witness':negative['primitive_value_at_integer_witness'],
                        'independent_supported_product_replay_complete':False,
                        'core_form_reduced':False,'optimizer_eligible':False})
                negative['cut_index']=known[key]
                result['negative_blocks'].append(negative)
            elif record['smallest_numeric_eigenvalue'] is not None and record['smallest_numeric_eigenvalue'] < -1e-8:
                result['unconfirmed_numeric_negatives'].append(record.copy())
            result['representative_records'].append(record)
            result['direct_representatives_completed']+=1
            result['triples_covered_by_root_congruence']+=record['orbit_size']
            result['union_rows_checked_exactly_zero']+=len(record['union_base_positions'])
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK,blocked)

    def deadline(_signum,_frame):
        raise TimeoutError('bounded 23-representative five-root triple-clique scan')

    previous=signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        for root in ledger['roots']:
            if not root['representatives']:
                continue
            rid,n=root['root_type'],root['base_order']
            current=['root_cache',rid]
            parent=parent_matrix(root,embeddings)
            child_matrices,conditional={},{}

            def child_matrix(lift):
                child,size=lift['child_root_type'],lift['child_root_order']
                key=size,child
                if key not in child_matrices:
                    expected=[mask for mask,_ in data[3][child] if mask.bit_count()>=3]
                    assert expected==lift['child_high_masks']
                    assert lift['child_scalar_order']==len(expected)+1
                    blocks=children[size]
                    if child in blocks:
                        masks,T=blocks[child]
                        assert masks==expected
                        order=len(masks)+1
                        columns=48965 if size==8 else 6535
                        assert T.shape==(order*(order+1)//2,columns)
                        assert max((int(i) for i in T.indices),default=-1)<sum(map(len,data[1][:size+3]))
                        child_matrices[key]=FullScanner.matrix(T,order,embeddings)
                    else:
                        assert size in (6,7) and not expected
                        child_matrices[key]=np.asarray([[embeddings[child]]],dtype=object)
                return child_matrices[key]

            for index,item in enumerate(root['conditional_subset_registry']):
                matrix=np.zeros((n,n),dtype=object)
                assert item['zero_conditional_contribution']==(not item['admissible_conditional_lifts'])
                for lift in item['admissible_conditional_lifts']:
                    assert lift['selected_masks']==item['selected_masks']
                    matrix+=lifted_matrix(lift,child_matrix(lift),n)
                conditional[index]=matrix
            for case in root['representatives']:
                index=case['representative_candidate_index']
                current=['triple_clique_representative',rid,index]
                selected=case['union_base_positions']
                assert selected==[root['high_masks'].index(mask)+1 for mask in case['union_masks']]
                localizer=parent.copy()
                for registry_id,coefficient in case['signed_conditional_registry_entries']:
                    localizer+=coefficient*conditional[registry_id]
                assert all(localizer[i,j]==0 for i in selected for j in range(n))
                assert np.array_equal(localizer,localizer.T)
                keep=[i for i in range(n) if i not in set(selected)]
                assert len(keep)==case['quotient_order']
                vector,quadratic,smallest,zeros=FullScanner.negative(localizer[np.ix_(keep,keep)])
                record={'root_type':rid,'representative_candidate_index':index,
                    'clique_indices':case['clique_indices'],'union_masks':case['union_masks'],
                    'union_base_positions':selected,'orbit_size':case['orbit_size'],
                    'signed_conditional_registry_entries':case['signed_conditional_registry_entries'],
                    'base_order':n,'quotient_order':len(keep),
                    'all_union_rows_checked_exactly_zero':True,
                    'smallest_numeric_eigenvalue':smallest,'exact_zero_quotient_rows':zeros}
                negative=None
                if vector is not None:
                    full=[0]*n
                    for i,value in zip(keep,vector):
                        full[i]=int(value)
                    V=np.asarray(full,dtype=object)
                    assert int(V@localizer@V)==quadratic<0
                    form=negative_form(root,case,full,quadratic,parent,children,child_matrix,automorphisms,counts)
                    negative={**record,**form}
                commit(record,negative)
                current=None
            result['completed_candidate_roots']+=1
            child_matrices.clear()
            conditional.clear()
            files.save(args.output,result)
            print(json.dumps({'root_completed':rid,'representatives':result['direct_representatives_completed'],
                'triples_covered_by_congruence':result['triples_covered_by_root_congruence'],
                'negative_blocks':len(result['negative_blocks']),'seconds':time.monotonic()-scan_started}),flush=True)
    except TimeoutError:
        timed_out=True
    except Exception as problem:
        error=repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    complete=result['direct_representatives_completed']==23 and not error and not timed_out
    if complete:
        assert result['triples_covered_by_root_congruence']==236
        assert result['union_rows_checked_exactly_zero']==171
        assert result['completed_candidate_roots']==5
    result.update(status='complete five-root triple-clique discovery scan' if complete else 'partial five-root triple-clique discovery scan',
        complete_representative_scan=complete,complete_candidate_congruence_coverage=complete,
        timed_out=timed_out,error=error,unfinished_case=current,
        scan_seconds=time.monotonic()-scan_started,total_seconds=time.monotonic()-total_started,
        max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    files.save(args.output,result)
    print(json.dumps({key:value for key,value in result.items() if key not in
        ('preparation','representative_records','negative_blocks','unique_induced_cuts')},indent=2),flush=True)
    print('negative_blocks',len(result['negative_blocks']),'unique_exact_forms',len(result['unique_induced_cuts']),flush=True)
    print('output_sha256',files.digest(args.output),flush=True)
    return 1 if error else 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--preparation',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--seconds',type=int,default=60)
    args=parser.parse_args()
    assert 0 < args.seconds <= 60
    if args.prepare:
        assert not args.preparation.exists()
        ledger,scope,_=inputs()
        prepared=metadata(ledger,scope)
        files.save(args.preparation,prepared)
        print(json.dumps(prepared,indent=2),flush=True)
    else:
        assert args.output is not None and not args.output.exists()
        with threadpool_limits(limits=1):
            raise SystemExit(run(args,read(args.preparation)))
