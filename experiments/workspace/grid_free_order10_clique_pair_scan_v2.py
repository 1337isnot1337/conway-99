"""Padded-cache correction for the 347 six-root clique-pair scan.

The v1 attempt stopped before its first matrix contraction. This version
accepts the frozen order-nine column padding and verifies order-eight support.

The complete frozen domain has 3,283 pairs. All count contractions use
Python integers. Every union row is checked before deletion. Numerical
directions are retained only after exact quadratic and induced-form checks.
Any accepted cut still needs a separate literal supported-product replay.
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

import grid_free_order10_clique_pair_domains as domains
import grid_free_order10_complement_scan as exact
from grid_free_order10_r8s1_scan import FullScanner
import grid_free_order10_scaled as files


ROOT=Path(__file__).resolve().parents[2]
LOGS=ROOT/'experiments/logs/moments-and-counts'
DOMAIN=LOGS/'order10-clique-pair-domains.json.gz'
DOMAIN_SHA='1812d7faa0dc865d21d970e7bff97e903693277804b341272145abc365bfcb51'
DOMAIN_SOURCE_SHA='0cde57ec1213c49b66f85c5a27a638883f7d0851bf9cb265632e3d82240de33c'
DOMAIN_REPLAY=LOGS/'order10-clique-pair-domains-replay.json'
DOMAIN_REPLAY_SHA='51d2de8b4d2a2991fe346a38f35223bbc1a8be6e1d8961a928eaff4f9d1a92c4'
WITNESS=LOGS/'prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json'
WITNESS_SHA='0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'
EXACT_SHA='806aea35eedde9f09eda5c5b0b5113b62e0c37e218a46c6ad727ea6950ca74a7'
NEGATIVE_SHA='71f06ef752adff6d49f88136b9e82f054f6485a2b2867c2cd4ef9f7ef7f82887'


def read(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix=='.gz' else raw)


def inputs():
    generic=domains.generic
    for path,sha in ((DOMAIN,DOMAIN_SHA),(Path(domains.__file__),DOMAIN_SOURCE_SHA),
        (DOMAIN_REPLAY,DOMAIN_REPLAY_SHA),
        (Path(exact.__file__),EXACT_SHA),
        (Path(__file__).with_name('grid_free_order10_r8s1_scan.py'),NEGATIVE_SHA),
        (WITNESS,WITNESS_SHA),(generic.BASE,generic.BASE_SHA),
        (generic.seven.BASE,generic.seven.BASE_SHA),(generic.seven.CHILD,generic.seven.CHILD_SHA)):
        assert files.digest(path)==sha
    for name,sha in domains.SOURCE_BINDINGS.items():
        assert files.digest(Path(__file__).with_name(name))==sha
    ledger=read(DOMAIN)
    assert ledger['source_sha256']==DOMAIN_SOURCE_SHA
    assert ledger['complete_preparation'] and ledger['complete_root_family']
    assert not ledger['timed_out'] and ledger['error'] is None
    assert ledger['all_union_rows_are_unrestricted_coefficient_identities']
    assert not ledger['point_dependent_pruning'] and not ledger['count_point_loaded']
    summary=ledger['summary']
    assert summary['root_types']==62 and summary['candidate_roots']==18
    assert summary['candidate_clique_pairs']==3283 and summary['candidate_pair_orbits']==347
    assert len(ledger['roots'])==62 and len({root['root_type'] for root in ledger['roots']})==62
    assert len(ledger['literal_controls'])==6
    replay=read(DOMAIN_REPLAY)
    assert replay['status'].startswith('PASS:')
    assert replay['source_sha256']==DOMAIN_SOURCE_SHA and replay['certificate_sha256']==DOMAIN_SHA
    assert replay['summary']==summary
    witness=read(WITNESS)
    counts=witness['induced_counts']
    cores=witness['rounded_core_values']
    assert len(counts)==48965 and all(type(value) is int and value>=0 for value in counts)
    assert len(cores)==550 and all(type(value) is int for value in cores)
    assert witness['x521_zero'] and len(witness['required_zero_coordinates'])==59
    assert cores[0]==1 and cores[1]==cores[521]==0
    assert all(cores[i]==0 for i in witness['required_zero_coordinates'])
    return ledger,counts


def metadata(ledger):
    generic=domains.generic
    summary=ledger['summary']
    representatives=[(root,orbit) for root in ledger['roots'] for orbit in root['pair_orbits']]
    assert len(representatives)==347
    assert sum(orbit['orbit_size'] for _,orbit in representatives)==3283
    selected=sum(len(root['candidate_clique_pairs'][orbit['representative_pair_index']]['union_masks'])
                 for root,orbit in representatives)
    return {'source_sha256':files.digest(Path(__file__)),
        'domain_source_sha256':DOMAIN_SOURCE_SHA,'domain_certificate_sha256':DOMAIN_SHA,
        'cold_domain_replay_sha256':DOMAIN_REPLAY_SHA,
        'generic_double_lift_source_sha256':domains.SOURCE_BINDINGS['grid_free_order10_double_complement_domains.py'],
        'catalogue_sha256':generic.direct.CATALOGUE_SHA,
        'six_root_cache_sha256':generic.BASE_SHA,
        'seven_root_cache_sha256':generic.seven.BASE_SHA,
        'eight_root_cache_sha256':generic.seven.CHILD_SHA,
        'exact_form_helper_sha256':EXACT_SHA,'negative_direction_helper_sha256':NEGATIVE_SHA,
        'integer_witness_sha256':WITNESS_SHA,
        'root_domains_retained':62,'root_types_with_direct_representatives':18,
        'direct_representatives_to_scan':347,'candidate_pairs_covered_by_congruence':3283,
        'quota_one_redundant_pairs_directly_scanned':0,
        'quota_one_redundant_pairs':1405,
        'quota_one_redundancy_requires_child_clique_localizers_and_count_identities':True,
        'quota_one_redundancy_is_not_a_point_PSD_certificate':True,
        'representative_union_rows_to_check':selected,
        'representative_quotient_lower_entries':summary['representative_quotient_lower_entries'],
        'largest_representative_quotient_order':ledger['largest_representative_quotient_order'],
        'representative_single_registry_entries':summary['representative_single_registry_size'],
        'representative_double_registry_entries':summary['representative_double_registry_size'],
        'full_matrix_additions_and_subtractions':summary['representative_full_matrix_additions_and_subtractions'],
        'sparse_lower_lift_products_upper_bound':summary['representative_sparse_lower_products_upper_bound'],
        'per_root_cache_sizing':ledger['per_root_cache_sizing'],
        'six_root_cache_column_count':6535,'six_root_nonzero_support_limit':1224,
        'previous_zero_coverage_attempt_sha256':'d54eacc3094fc2a5284f993479562b27d81c3560844a2027c77e429fca60dade',
        'maximum_scan_seconds':60,'threads':1,
        'all_count_contractions_use_Python_integers':True,
        'all_union_rows_checked_exactly_before_deletion':True,
        'conditional_matrices_cached_per_root':True,
        'no_root_or_flag_removed_from_domain_by_point_value':True,
        'additional_zero_rows_removed_only_after_exact_entry_checks':True,
        'independent_supported_product_replay_deferred':True,
        'new_product_tensors_generated':False,'dense_reduction_loaded':False,'optimizer_called':False}


def lifted_matrix(lift,child,n):
    sparse=lift['sparse_rows']
    assert len(sparse)==n and sparse[0]==[0]
    matrix=np.empty((n,n),dtype=object)
    for i in range(n):
        for j in range(i+1):
            value=sum(child[u,v] for u in sparse[i] for v in sparse[j])
            matrix[i,j]=matrix[j,i]=int(value)
    return matrix


def signed_lifts(root,case):
    for i in case['single_registry_ids']:
        yield -1,'single',i,root['single_lift_registry'][i]['lift']
    for i in case['compatible_cross_double_registry_ids']:
        for lift in root['double_lift_registry'][i]['conditional_lifts']:
            yield 1,'double',i,lift


def constant_form(root,vector,automorphisms):
    assert len(vector)==1
    return Counter({root:vector[0]*vector[0]*automorphisms[root]})


def negative_form(root,case,full,quadratic,parent,bases,children,child_matrix,automorphisms,counts):
    n=root['base_order']
    assert len(full)==n and all(type(value) is int for value in full)
    V=np.asarray(full,dtype=object)
    combined=exact.raw_form(bases[root['root_type']][1],full,automorphisms)
    identity_value=int(V@parent@V)
    child_vectors=[]
    for sign,kind,index,lift in signed_lifts(root,case):
        w=[0]*lift['child_base_order']
        for coefficient,row in zip(full,lift['sparse_rows']):
            for j in row:
                w[j]+=coefficient
        W=np.asarray(w,dtype=object)
        identity_value+=sign*int(W@child_matrix(lift)@W)
        level=len(lift['selected_masks'])
        child=lift['child_root_type']
        blocks=children[level]
        form=(exact.raw_form(blocks[child][1],w,automorphisms) if child in blocks
              else constant_form(child,w,automorphisms))
        for graph,coefficient in form.items():
            combined[graph]+=sign*coefficient
        child_vectors.append({'sign':sign,'registry_kind':kind,'registry_id':index,
            'selected_masks':lift['selected_masks'],'mutual_edge':lift['mutual_edge'],
            'child_root_type':child,'integer_child_vector':w})
    assert identity_value==quadratic<0
    accepted=exact.accepted_form(combined,counts,quadratic)
    return {'integer_parent_vector':full,'conditional_child_vectors':child_vectors,
            'integer_quadratic_value':quadratic,**accepted}


def run(args,prepared):
    total_started=time.monotonic()
    ledger,counts=inputs()
    assert prepared==metadata(ledger)
    generic=domains.generic
    assert files.digest(args.catalogue)==generic.direct.CATALOGUE_SHA
    data=pickle.loads(args.catalogue.read_bytes())
    assert [root['root_type'] for root in ledger['roots']]==data[1][6]
    bases={root:(flags,tensor) for root,flags,tensor in pickle.loads(generic.BASE.read_bytes())}
    seven={root:([flag[-1] for flag in flags[1:]],tensor)
           for root,flags,tensor in pickle.loads(generic.seven.BASE.read_bytes())}
    saved8=pickle.loads(gzip.decompress(generic.seven.CHILD.read_bytes()))
    assert saved8['point_independent'] and saved8['complete_root_family']
    assert not saved8['zero_flags_or_roots_removed']
    assert saved8['construction_source_sha256']==generic.seven.TRANSPORT_SHA
    eight={root:(masks,tensor) for root,masks,tensor in saved8['blocks']}
    assert len(bases)==55 and len(seven)==203 and sorted(eight)==data[1][8]
    children={1:seven,2:eight}
    automorphisms=[int(value) for value in data[2]]
    embeddings=[a*count for a,count in zip(automorphisms,counts)]
    assert all(type(value) is int for value in embeddings)
    result={'source_sha256':files.digest(Path(__file__)),
        'preparation_sha256':files.digest(args.preparation),'preparation':prepared,
        'representative_records':[],'negative_blocks':[],'unique_induced_cuts':[],
        'unconfirmed_numeric_negatives':[],
        'direct_representatives_completed':0,'pairs_covered_by_root_congruence':0,
        'union_rows_checked_exactly_zero':0,'completed_candidate_roots':0,
        'quota_one_redundant_pairs_directly_scanned':0,
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
                    result['unique_induced_cuts'].append({
                        'terms':negative['primitive_induced_count_form'],
                        'exact_value_at_witness':negative['primitive_value_at_integer_witness'],
                        'independent_supported_product_replay_complete':False,
                        'core_form_reduced':False,'optimizer_eligible':False})
                negative['cut_index']=known[key]
                result['negative_blocks'].append(negative)
            elif record['smallest_numeric_eigenvalue'] is not None and record['smallest_numeric_eigenvalue'] < -1e-8:
                result['unconfirmed_numeric_negatives'].append(record.copy())
            result['representative_records'].append(record)
            result['direct_representatives_completed']+=1
            result['pairs_covered_by_root_congruence']+=record['orbit_size']
            result['union_rows_checked_exactly_zero']+=len(record['union_base_positions'])
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK,blocked)

    def deadline(_signum,_frame):
        raise TimeoutError('bounded 347-representative six-root clique-pair scan')

    previous=signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        for root in ledger['roots']:
            if not root['pair_orbits']:
                continue
            rid,n=root['root_type'],root['base_order']
            current=['root_cache',rid]
            high=root['high_masks']
            flags,tensor=bases[rid]
            assert [tuple(flag) for flag in flags]==[tuple(root['root_rows'])]+[
                generic.transport.attach(root['root_rows'],mask) for mask in high]
            # The frozen six-root cache is padded through order nine.
            assert tensor.shape==(n*(n+1)//2,6535)
            assert max((int(i) for i in tensor.indices),default=-1)<sum(len(level) for level in data[1][:9])
            parent=FullScanner.matrix(tensor,n,embeddings)
            child_matrices,singles,doubles={},{},{}

            def child_matrix(lift):
                level=len(lift['selected_masks'])
                child=lift['child_root_type']
                key=level,child
                if key not in child_matrices:
                    expected=[mask for mask,_ in data[3][child] if mask.bit_count()>=3]
                    assert expected==lift['child_high_masks']
                    assert lift['child_base_order']==len(expected)+1
                    blocks=children[level]
                    if child in blocks:
                        masks,T=blocks[child]
                        assert masks==expected
                        order=len(masks)+1
                        limit=6+level+2
                        assert T.shape==(order*(order+1)//2,sum(len(part) for part in data[1][:limit+1]))
                        child_matrices[key]=FullScanner.matrix(T,order,embeddings)
                    else:
                        assert level==1 and not expected
                        child_matrices[key]=np.asarray([[embeddings[child]]],dtype=object)
                return child_matrices[key]

            expected_singles=set()
            expected_doubles=set()
            for orbit in root['pair_orbits']:
                case=root['candidate_clique_pairs'][orbit['representative_pair_index']]
                expected_singles.update(case['single_registry_ids'])
                expected_doubles.update(case['compatible_cross_double_registry_ids'])
            assert sorted(expected_singles)==root['representative_single_registry_ids']
            assert sorted(expected_doubles)==root['representative_double_registry_ids']
            for i in sorted(expected_singles):
                lift=root['single_lift_registry'][i]['lift']
                assert lift['selected_masks']==[root['single_lift_registry'][i]['mask']]
                singles[i]=lifted_matrix(lift,child_matrix(lift),n)
            for i in sorted(expected_doubles):
                entry=root['double_lift_registry'][i]
                matrix=np.zeros((n,n),dtype=object)
                for lift in entry['conditional_lifts']:
                    assert lift['selected_masks']==entry['masks']
                    matrix+=lifted_matrix(lift,child_matrix(lift),n)
                doubles[i]=matrix

            for orbit in root['pair_orbits']:
                index=orbit['representative_pair_index']
                case=root['candidate_clique_pairs'][index]
                current=['clique_pair_representative',rid,index]
                C=root['maximal_cliques'][case['left_clique_index']]['masks']
                D=root['maximal_cliques'][case['right_clique_index']]['masks']
                selected=case['union_base_positions']
                assert case['union_masks']==sorted(set(C)|set(D))
                assert selected==[high.index(mask)+1 for mask in case['union_masks']]
                assert [root['single_lift_registry'][i]['mask'] for i in case['single_registry_ids']]==case['union_masks']
                localizer=parent.copy()
                for i in case['single_registry_ids']:
                    localizer-=singles[i]
                for i in case['compatible_cross_double_registry_ids']:
                    localizer+=doubles[i]
                assert all(localizer[i,j]==0 for i in selected for j in range(n))
                assert np.array_equal(localizer,localizer.T)
                keep=[i for i in range(n) if i not in set(selected)]
                assert len(keep)==case['quotient_order']==orbit['quotient_order']
                vector,quadratic,smallest,zeros=FullScanner.negative(localizer[np.ix_(keep,keep)])
                record={'root_type':rid,'representative_pair_index':index,
                    'left_clique_index':case['left_clique_index'],'right_clique_index':case['right_clique_index'],
                    'left_clique_masks':C,'right_clique_masks':D,
                    'union_masks':case['union_masks'],'union_base_positions':selected,
                    'single_registry_ids':case['single_registry_ids'],
                    'compatible_cross_double_registry_ids':case['compatible_cross_double_registry_ids'],
                    'orbit_size':orbit['orbit_size'],'base_order':n,'quotient_order':len(keep),
                    'all_union_rows_checked_exactly_zero':True,
                    'smallest_numeric_eigenvalue':smallest,'exact_zero_quotient_rows':zeros}
                negative=None
                if vector is not None:
                    full=[0]*n
                    for i,value in zip(keep,vector):
                        full[i]=int(value)
                    V=np.asarray(full,dtype=object)
                    assert int(V@localizer@V)==quadratic<0
                    form=negative_form(root,case,full,quadratic,parent,bases,children,
                                       child_matrix,automorphisms,counts)
                    negative={**record,**form}
                commit(record,negative)
                current=None
            child_matrices.clear()
            singles.clear()
            doubles.clear()
            result['completed_candidate_roots']+=1
            files.save(args.output,result)
            print(json.dumps({'root_completed':rid,'representatives':result['direct_representatives_completed'],
                'pairs_covered_by_congruence':result['pairs_covered_by_root_congruence'],
                'negative_blocks':len(result['negative_blocks']),'seconds':time.monotonic()-scan_started}),flush=True)
    except TimeoutError:
        timed_out=True
    except Exception as problem:
        error=repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    complete=result['direct_representatives_completed']==347
    if complete:
        assert result['pairs_covered_by_root_congruence']==3283
        assert result['union_rows_checked_exactly_zero']==prepared['representative_union_rows_to_check']
    result.update(status='complete six-root clique-pair representative discovery scan' if complete else 'partial six-root clique-pair representative discovery scan',
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
        ledger,_=inputs()
        prepared=metadata(ledger)
        files.save(args.preparation,prepared)
        print(json.dumps(prepared,indent=2),flush=True)
    else:
        assert args.output is not None and not args.output.exists()
        with threadpool_limits(limits=1):
            raise SystemExit(run(args,read(args.preparation)))
