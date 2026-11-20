"""One bounded exact-gated scan of 1,225 prism-free clique representatives.

The frozen root transports cover 4,584 remaining cliques and all 530
residual-two triple groups. Direct representatives and congruent cases
are reported separately. Count contractions use Python integers; all
designated zero rows are checked before deletion. Conditional matrices
and child matrices are cached only for the current root.
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

import grid_free_order10_complement_domains as domains
import grid_free_order10_complement_scan as exact
import grid_free_order10_projector_probe as point
import grid_free_order10_r8s1 as forms
from grid_free_order10_r8s1_scan import FullScanner
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
PRISM = LOGS/'order10-complement-prism-domains.json.gz'
PRISM_SHA = '80270c7e4373324981eeab06733c9b3b83e419929eb4b824d48e6e4134461393'
CLOSURE = LOGS/'prism-zero-order10-zero-closure.json'
CLOSURE_SHA = 'cde1bd353eb39fe8aa713080a5acfb6ae78f3dd13244d9255c9217541060919c'
REPLAY = LOGS/'order10-complement-prism-domains-replay.json'
REPLAY_SHA = '9048fab61da410e7cc5b3a260ff39b3145548334e8327e76efb2e56880aa3330'
CHILD_SCAN = LOGS/'order10-complement-scan01.json'
CHILD_SCAN_SHA = '72bbe6bf45832ef2cd6a76f3ac25227c1f334c32f1cb358401b544b740df563c'
EXACT_HELPER_SHA = '806aea35eedde9f09eda5c5b0b5113b62e0c37e218a46c6ad727ea6950ca74a7'


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix=='.gz' else path.read_bytes())


def inputs():
    for path,sha in ((PRISM,PRISM_SHA),(CLOSURE,CLOSURE_SHA),(REPLAY,REPLAY_SHA),
                     (CHILD_SCAN,CHILD_SCAN_SHA),
                     (point.WITNESS,point.WITNESS_SHA),(Path(exact.__file__),EXACT_HELPER_SHA),
                     (domains.BASE,domains.BASE_SHA),(domains.CHILD,domains.CHILD_SHA)):
        assert files.digest(path) == sha
    prism,closure,replay = read(PRISM),read(CLOSURE),read(REPLAY)
    assert prism['complete_root_family'] and prism['root_types_completed'] == 208
    assert not prism['timed_out'] and prism['error'] is None
    assert prism['summary']['remaining_clique_orbits'] == 1225
    assert prism['summary']['covered_remaining_cliques'] == 4584
    assert prism['summary']['new_conditional_rows_supported_on_prism_zeros'] == 3208
    assert prism['new_selected_row_identities_hold_modulo_prism_zero_support']
    assert not prism['unrestricted_selected_row_zero_identity_claim']
    assert all(root['all_selected_clique_rows_zero_after_prism_zero_substitution'] for root in prism['roots'])
    assert replay['certificate_sha256'] == PRISM_SHA
    assert replay['status'] == 'PASS: complete prism-free clique/orbit and raw zero-support replay'
    assert closure['all_induced_prism_forms_vanish_after_prism_core_zeros']
    zeros = closure['prism_containing_induced_types']
    assert len(zeros) == 1443 and sorted(zeros) == prism['all_prism_containing_types_forced_zero']
    assert all(root['maximal_cliques'][group['covering_maximal_clique_index']]['classification']=='remaining_clique_complement'
               for root in prism['roots'] for group in root['triple_groups_with_pair_residuals_two'])
    child_scan = read(CHILD_SCAN)
    assert child_scan['complete_child_scan'] and len(child_scan['scalar_child_records']) == 916
    assert not child_scan['negative_blocks'] and not child_scan['unconfirmed_numeric_negatives']
    assert not child_scan['scalar_child_PSD_certified']
    witness = read(point.WITNESS)
    counts = witness['induced_counts']
    assert len(counts) == 48965 and all(type(value) is int and value >= 0 for value in counts)
    assert witness['x521_zero'] and len(witness['required_zero_coordinates']) == 59
    assert witness['rounded_core_values'][1] == 0
    assert all(counts[graph] == 0 for graph in zeros)
    return prism,counts


def metadata():
    prism,_ = inputs()
    return {'source_sha256':files.digest(Path(__file__)),
        'prism_domain_lifts_and_orbits_sha256':PRISM_SHA,
        'proved_prism_zero_closure_sha256':CLOSURE_SHA,'cold_zero_support_replay_sha256':REPLAY_SHA,
        'catalogue_sha256':domains.direct.CATALOGUE_SHA,
        'base_cache_sha256':domains.BASE_SHA,'child_cache_sha256':domains.CHILD_SHA,
        'exact_form_helper_sha256':EXACT_HELPER_SHA,
        'negative_direction_source_sha256':files.digest(Path(__file__).with_name('grid_free_order10_r8s1_scan.py')),
        'integer_witness_sha256':point.WITNESS_SHA,
        'earlier_scalar_child_scan_sha256':CHILD_SCAN_SHA,
        'direct_representatives_to_scan':1225,'remaining_cliques_covered_by_congruence':4584,
        'triple_groups_covered_by_congruence':530,
        'quota_one_redundant_cliques_directly_scanned':0,
        'quota_one_redundant_cliques_implied_by_child_PSD_and_count_identities':1378,
        'representative_quotient_lower_entries':1417349,
        'largest_representative_quotient_order':84,
        'conditional_lifts_for_representatives':2103,
        'full_matrix_subtractions':53444911,
        'maximum_scan_seconds':60,'threads':1,
        'per_root_cache_sizing':prism['per_root_cache_sizing'],
        'assumption':'Global prism-freeness (ordinary core coordinate x1=0).',
        'all_1443_required_prism_type_counts_checked_exactly_zero':True,
        'triple_cover_multiplicities_retained':True,
        'new_zero_rows_are_not_unrestricted_identities':True,
        'conditional_and_child_count_matrices_released_after_each_root':True,
        'all_count_contractions_use_Python_integers':True,
        'all_selected_zero_rows_checked_before_deletion':True,
        'all_count_points_and_domains_preserved':True,
        'independent_supported_product_replay_deferred':True,
        'new_product_tensors_generated':False,'dense_reduction_loaded':False,'optimizer_called':False}


def run(args,prepared):
    total_started = time.monotonic()
    assert prepared == metadata()
    prism,counts = inputs()
    assert files.digest(args.catalogue) == domains.direct.CATALOGUE_SHA
    with args.catalogue.open('rb') as stream:
        data = pickle.load(stream)
    bases = {root:(flags,tensor) for root,flags,tensor in pickle.loads(domains.BASE.read_bytes())}
    child_saved = pickle.loads(gzip.decompress(domains.CHILD.read_bytes()))
    assert child_saved['point_independent'] and child_saved['complete_root_family']
    assert not child_saved['zero_flags_or_roots_removed']
    assert child_saved['construction_source_sha256'] == domains.TRANSPORT_SHA
    children = {root:(masks,tensor) for root,masks,tensor in child_saved['blocks']}
    assert sorted(children) == data[1][8]
    embeddings = [int(a)*count for a,count in zip(data[2],counts)]
    result = {'source_sha256':files.digest(Path(__file__)),
        'preparation_sha256':files.digest(args.preparation),'preparation':prepared,
        'representative_records':[],'negative_blocks':[],'unique_induced_cuts':[],
        'unconfirmed_numeric_negatives':[],
        'direct_representatives_completed':0,'cliques_covered_by_root_congruence':0,
        'triple_groups_covered_by_root_congruence':0,
        'independent_supported_product_replay_complete':False,
        'PSD_feasibility_certified':False,'scalar_child_PSD_certified':False,
        'scalar_child_screening_reused_from_frozen_same_integer_point':True,
        'quota_one_redundant_cliques_directly_scanned':0}
    result['scope_assumption'] = 'Global prism-freeness (ordinary core coordinate x1=0).'
    result['required_prism_type_counts_checked_exactly_zero'] = 1443
    known = {}
    timed_out,error,current = False,None,None
    scan_started = time.monotonic()

    def commit(record,negative,covered_triples):
        previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM})
        try:
            if negative is not None:
                key = tuple(map(tuple,negative['primitive_induced_count_form']))
                if key not in known:
                    known[key] = len(result['unique_induced_cuts'])
                    result['unique_induced_cuts'].append({
                        'terms':negative['primitive_induced_count_form'],
                        'exact_value_at_witness':negative['primitive_value_at_integer_witness'],
                        'necessary_only_on_prism_free_face':True,
                        'independent_supported_product_replay_complete':False})
                negative['cut_index'] = known[key]
                result['negative_blocks'].append(negative)
            elif record['smallest_numeric_eigenvalue'] is not None and record['smallest_numeric_eigenvalue'] < -1e-8:
                result['unconfirmed_numeric_negatives'].append(record.copy())
            result['representative_records'].append(record)
            result['direct_representatives_completed'] += 1
            result['cliques_covered_by_root_congruence'] += record['orbit_size']
            result['triple_groups_covered_by_root_congruence'] += covered_triples
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK,previous_mask)

    def deadline(_signum,_frame):
        raise TimeoutError('bounded 1225-representative prism-free clique scan')

    previous = signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        for orbit_root in prism['roots']:
            if not orbit_root['orbits']:
                continue
            root = orbit_root['root_type']
            current = ['root_cache',root]
            domain = orbit_root
            high,n = domain['high_masks'],domain['base_order']
            flags,tensor = bases[root]
            assert [tuple(f) for f in flags] == [tuple(domain['root_rows'])]+[
                forms.attach(domain['root_rows'],mask) for mask in high]
            assert tensor.shape == (n*(n+1)//2,6535)
            parent = FullScanner.matrix(tensor,n,embeddings)
            absent_positions = list(range(n)) if domain['root_contains_prism'] else [high.index(mask)+1 for mask in domain['absent_high_masks']]
            assert all(parent[i,j] == 0 for i in absent_positions for j in range(n))
            lifts = {item['mask']:item for item in orbit_root['conditional_lifts']}
            needed = sorted(lifts)
            assert needed == sorted({mask for orbit in orbit_root['orbits'] for mask in orbit['representative_masks']})
            child_types = {lifts[mask]['child_root_type'] for mask in needed}
            child_matrices = {}
            for child in child_types:
                masks,T = children[child]
                assert masks == [mask for mask,_ in data[3][child] if mask.bit_count() >= 3]
                order = len(masks)+1
                assert T.shape == (order*(order+1)//2,48965)
                child_matrices[child] = FullScanner.matrix(T,order,embeddings)
            conditional = {}
            for mask in needed:
                lift = lifts[mask]
                child_matrix = child_matrices[lift['child_root_type']]
                sparse = lift['sparse_rows']
                assert len(sparse) == n and sparse[0] == sparse[lift['base_position']] == [0]
                matrix = np.empty((n,n),dtype=object)
                for i in range(n):
                    for j in range(i+1):
                        value = sum(child_matrix[u,v] for u in sparse[i] for v in sparse[j])
                        matrix[i,j] = matrix[j,i] = int(value)
                conditional[mask] = matrix
            triple_cliques = Counter(g['covering_maximal_clique_index'] for g in domain['triple_groups_with_pair_residuals_two'])
            for orbit in orbit_root['orbits']:
                index = orbit['representative_clique_index']
                case = domain['maximal_cliques'][index]
                masks,selected = case['masks'],case['base_positions']
                assert masks == orbit['representative_masks']
                assert selected == [high.index(mask)+1 for mask in masks]
                current = ['clique_representative',root,index]
                localizer = parent.copy()
                for mask in masks:
                    localizer -= conditional[mask]
                assert all(localizer[i,j] == 0 for i in selected for j in range(n))
                keep = [i for i in range(n) if i not in set(selected)]
                assert len(keep) == orbit['quotient_order']
                vector,quadratic,smallest,zeros = FullScanner.negative(localizer[np.ix_(keep,keep)])
                record = {'root_type':root,'representative_clique_index':index,
                    'selected_masks':masks,'selected_base_positions':selected,
                    'orbit_size':orbit['orbit_size'],'base_order':n,'quotient_order':len(keep),
                    'all_selected_rows_checked_exactly_zero':True,
                    'selected_row_zeros_use_the_proved_prism_zero_substitution':True,
                    'smallest_numeric_eigenvalue':smallest,'exact_zero_quotient_rows':zeros}
                negative = None
                if vector is not None:
                    full = [0]*n
                    for i,value in zip(keep,vector):
                        full[i] = value
                    v = np.asarray(full,dtype=object)
                    assert int(v@localizer@v) == quadratic < 0
                    combined = exact.raw_form(tensor,full,data[2])
                    child_vectors = []
                    identity_value = int(v@parent@v)
                    for mask in masks:
                        lift = lifts[mask]
                        child = lift['child_root_type']
                        w = [0]*lift['child_base_order']
                        for coefficient,sparse in zip(full,lift['sparse_rows']):
                            for column in sparse:
                                w[column] += coefficient
                        W = np.asarray(w,dtype=object)
                        identity_value -= int(W@child_matrices[child]@W)
                        subtraction = exact.raw_form(children[child][1],w,data[2])
                        for graph,coefficient in subtraction.items():
                            combined[graph] -= coefficient
                        child_vectors.append({'selected_mask':mask,'child_root_type':child,
                                              'integer_child_vector':w})
                    assert identity_value == quadratic
                    form = exact.accepted_form(combined,counts,quadratic)
                    negative = {**record,'integer_parent_vector':full,
                        'conditional_child_vectors':child_vectors,
                        'integer_quadratic_value':quadratic,
                        'necessary_only_on_prism_free_face':True,**form}
                covered_triples = sum(triple_cliques[member['clique_index']] for member in orbit['members'])
                commit(record,negative,covered_triples)
                current = None
            child_matrices.clear()
            conditional.clear()
            files.save(args.output,result)
            print(json.dumps({'root_completed':root,'direct_representatives_completed':result['direct_representatives_completed'],
                'cliques_covered_by_root_congruence':result['cliques_covered_by_root_congruence'],
                'negative_blocks':len(result['negative_blocks']),'seconds':time.monotonic()-scan_started}),flush=True)
    except TimeoutError:
        timed_out = True
    except Exception as problem:
        error = repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    complete = result['direct_representatives_completed'] == 1225
    if complete:
        assert result['cliques_covered_by_root_congruence'] == 4584
        assert result['triple_groups_covered_by_root_congruence'] == 530
    result.update(status='complete prism-free clique representative discovery scan' if complete else 'partial prism-free clique representative discovery scan',
        complete_representative_scan=complete,complete_congruence_coverage=complete,
        timed_out=timed_out,error=error,unfinished_case=current,
        scan_seconds=time.monotonic()-scan_started,total_seconds=time.monotonic()-total_started,
        max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    files.save(args.output,result)
    print(json.dumps({key:value for key,value in result.items() if key not in (
        'representative_records','negative_blocks','unique_induced_cuts','preparation')},indent=2),flush=True)
    print('negative_blocks',len(result['negative_blocks']),'unique_exact_forms',len(result['unique_induced_cuts']),flush=True)
    print('output_sha256',files.digest(args.output),flush=True)
    return 1 if error else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--preparation',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--seconds',type=int,default=60)
    args = parser.parse_args()
    assert 0 < args.seconds <= 60
    if args.prepare:
        assert not args.preparation.exists()
        prepared = metadata()
        files.save(args.preparation,prepared)
        print(json.dumps(prepared,indent=2),flush=True)
    else:
        assert args.output is not None and not args.output.exists()
        with threadpool_limits(limits=1):
            raise SystemExit(run(args,read(args.preparation)))
