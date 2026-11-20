"""Bounded exact-gated scan of84 six-root double-complement orbits.

All count contractions use Python integers. A negative direction is
retained only after its integer quadratic value and complete induced
count form agree exactly. A no-separator result does not certify PSD.
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

import grid_free_order10_double_complement_domains as domains
import grid_free_order10_complement_scan as exact
import grid_free_order10_projector_probe as point
from grid_free_order10_r8s1_scan import FullScanner
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ROOT/'experiments/logs/moments-and-counts/order10-double-complement-domains.json.gz'
DOMAIN_SHA = '166c66d9b990f5806ee5fcd729eb90a6e073a98a890a348f12450908f5235eac'
DOMAIN_SOURCE_SHA = '1283b15c44f408e0baf2cb1f9abd1c59b4ebee8717ca099c39e52b55c56ea935'
EXACT_SHA = '806aea35eedde9f09eda5c5b0b5113b62e0c37e218a46c6ad727ea6950ca74a7'


def inputs():
    for path, expected in ((DOMAIN,DOMAIN_SHA),(Path(domains.__file__),DOMAIN_SOURCE_SHA),
                           (domains.BASE,domains.BASE_SHA),(domains.seven.BASE,domains.seven.BASE_SHA),
                           (domains.seven.CHILD,domains.seven.CHILD_SHA),
                           (Path(exact.__file__),EXACT_SHA),(point.WITNESS,point.WITNESS_SHA)):
        assert files.digest(path) == expected
    ledger = json.loads(gzip.decompress(DOMAIN.read_bytes()))
    assert ledger['source_sha256'] == DOMAIN_SOURCE_SHA
    assert ledger['summary']['candidate_pair_orbits'] == 84
    assert ledger['summary']['candidate_pairs'] == 1112
    witness = json.loads(point.WITNESS.read_text())
    counts = witness['induced_counts']
    assert len(counts) == 48965 and all(type(c) is int and c >= 0 for c in counts)
    return ledger, counts


def metadata():
    ledger, _ = inputs()
    single_needed, double_needed, operations, peak = 0, 0, 0, 0
    for root in ledger['roots']:
        pairs = {tuple(p['masks']): p for p in root['candidate_pairs']}
        reps = [pairs[tuple(orbit['representative'])] for orbit in root['pair_orbits']]
        needed = {m for pair in reps for m in pair['masks']}
        singles = [s for s in root['single_conditional_lifts'] if s['mask'] in needed]
        doubles = [s for pair in reps for s in pair['double_conditional_lifts']]
        single_needed += len(singles)
        double_needed += len(doubles)
        child_orders = {(len(s['selected_masks']),s['child_root_type']):s['child_base_order'] for s in singles+doubles}
        n = root['base_order']
        cells = sum(order*order for order in child_orders.values())+(len(singles)+4)*n*n
        peak = max(peak,cells)
        for lift in singles+doubles:
            lengths = [len(row) for row in lift['sparse_rows']]
            operations += (sum(lengths)**2+sum(k*k for k in lengths))//2
    return {'source_sha256':files.digest(Path(__file__)), 'domain_sha256':DOMAIN_SHA,
            'domain_source_sha256':DOMAIN_SOURCE_SHA,'six_root_cache_sha256':domains.BASE_SHA,
            'seven_root_cache_sha256':domains.seven.BASE_SHA,'eight_root_cache_sha256':domains.seven.CHILD_SHA,
            'exact_form_helper_sha256':EXACT_SHA,
            'negative_direction_helper_sha256':files.digest(Path(__file__).with_name('grid_free_order10_r8s1_scan.py')),
            'integer_witness_sha256':point.WITNESS_SHA,'catalogue_sha256':domains.direct.CATALOGUE_SHA,
            'representatives':84,'pairs_covered_by_congruence':1112,'root_types_with_candidates':16,
            'representative_lower_entries':48703,'maximum_quotient_order':41,
            'single_lifts_needed':single_needed,'double_lifts_needed':double_needed,
            'sparse_lower_contraction_terms_upper_bound':operations,'peak_per_root_object_cells':peak,
            'maximum_seconds':30,'threads':1,'all_count_contractions_use_Python_integers':True,
            'all_selected_rows_checked_before_deletion':True,'redundant_pairs_directly_scanned':0,
            'optimizer_called':False,'new_product_tensors_generated':False,'dense_reduction_loaded':False}


def constant_form(root, vector, aut):
    assert len(vector) == 1
    return Counter({root:int(vector[0])*int(vector[0])*int(aut[root])})


def run(args, prepared):
    total_started = time.monotonic()
    assert prepared == metadata()
    ledger, counts = inputs()
    assert files.digest(args.catalogue) == domains.direct.CATALOGUE_SHA
    data = pickle.loads(args.catalogue.read_bytes())
    bases = {r:(f,t) for r,f,t in pickle.loads(domains.BASE.read_bytes())}
    seven = {r:([f[-1] for f in flags[1:]],t) for r,flags,t in pickle.loads(domains.seven.BASE.read_bytes())}
    saved8 = pickle.loads(gzip.decompress(domains.seven.CHILD.read_bytes()))
    eight = {r:(m,t) for r,m,t in saved8['blocks']}
    embeddings = [int(a)*c for a,c in zip(data[2],counts)]
    report = {'source_sha256':files.digest(Path(__file__)), 'preparation_sha256':files.digest(args.preparation),
              'preparation':prepared,'representative_records':[],'negative_blocks':[],
              'unique_induced_cuts':[],'unconfirmed_numeric_negatives':[],
              'direct_representatives_completed':0,'pairs_covered_by_congruence':0,
              'PSD_feasibility_certified':False,'independent_supported_product_replay_complete':False}
    known, current, timed_out, error = {}, None, False, None
    started = time.monotonic()

    def deadline(_signum,_frame):
        raise TimeoutError('bounded84-representative double-complement scan')

    previous = signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        for root in ledger['roots']:
            if not root['pair_orbits']:
                continue
            rid, n = root['root_type'], root['base_order']
            current = ['root_cache',rid]
            parent = FullScanner.matrix(bases[rid][1],n,embeddings)
            child_matrices, conditionals = {}, {}

            def child_matrix(lift):
                level = len(lift['selected_masks'])
                child = lift['child_root_type']
                key = level,child
                if key not in child_matrices:
                    blocks = seven if level == 1 else eight
                    if child in blocks:
                        masks,tensor = blocks[child]
                        assert masks == lift['child_high_masks']
                        child_matrices[key] = FullScanner.matrix(tensor,len(masks)+1,embeddings)
                    else:
                        assert not lift['child_high_masks']
                        child_matrices[key] = np.asarray([[embeddings[child]]],dtype=object)
                return child_matrices[key]

            def conditional(lift):
                child = child_matrix(lift)
                rows = lift['sparse_rows']
                matrix = np.empty((n,n),dtype=object)
                for i in range(n):
                    for j in range(i+1):
                        matrix[i,j] = matrix[j,i] = int(sum(child[u,v] for u in rows[i] for v in rows[j]))
                return matrix

            singles = {s['mask']:s for s in root['single_conditional_lifts']}
            pairs = {tuple(p['masks']):p for p in root['candidate_pairs']}
            for orbit in root['pair_orbits']:
                pair = pairs[tuple(orbit['representative'])]
                a,b = pair['masks']
                current = ['representative',rid,a,b]
                for mask in (a,b):
                    if mask not in conditionals:
                        conditionals[mask] = conditional(singles[mask])
                localizer = parent-conditionals[a]-conditionals[b]
                for lift in pair['double_conditional_lifts']:
                    localizer += conditional(lift)
                selected = pair['selected_base_positions']
                assert all(localizer[i,j] == 0 for i in selected for j in range(n))
                keep = [i for i in range(n) if i not in selected]
                assert len(keep) == pair['quotient_order']
                vector,quadratic,smallest,zeros = FullScanner.negative(localizer[np.ix_(keep,keep)])
                record = {'root_type':rid,'selected_masks':[a,b],'selected_base_positions':selected,
                          'orbit_size':orbit['size'],'quotient_order':len(keep),
                          'both_selected_rows_checked_exactly_zero':True,
                          'smallest_numeric_eigenvalue':smallest,'exact_zero_quotient_rows':zeros}
                negative = None
                if vector is not None:
                    full = [0]*n
                    for i,value in zip(keep,vector):
                        full[i] = value
                    V = np.asarray(full,dtype=object)
                    assert int(V@localizer@V) == quadratic < 0
                    combined = exact.raw_form(bases[rid][1],full,data[2])
                    identity_value = int(V@parent@V)
                    child_vectors = []
                    signed_lifts = [(-1,singles[a]),(-1,singles[b])]+[(1,s) for s in pair['double_conditional_lifts']]
                    for sign,lift in signed_lifts:
                        w = [0]*lift['child_base_order']
                        for coefficient,row in zip(full,lift['sparse_rows']):
                            for j in row:
                                w[j] += coefficient
                        W = np.asarray(w,dtype=object)
                        identity_value += sign*int(W@child_matrix(lift)@W)
                        blocks = seven if len(lift['selected_masks']) == 1 else eight
                        child = lift['child_root_type']
                        form = exact.raw_form(blocks[child][1],w,data[2]) if child in blocks else constant_form(child,w,data[2])
                        for graph,coefficient in form.items():
                            combined[graph] += sign*coefficient
                        child_vectors.append({'sign':sign,'child_root_type':child,'selected_masks':lift['selected_masks'],
                                              'mutual_edge':lift['mutual_edge'],'integer_vector':w})
                    assert identity_value == quadratic
                    form = exact.accepted_form(combined,counts,quadratic)
                    negative = {**record,'integer_parent_vector':full,'conditional_child_vectors':child_vectors,
                                'integer_quadratic_value':quadratic,**form}
                blocked = signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM})
                try:
                    if negative is not None:
                        key = tuple(map(tuple,negative['primitive_induced_count_form']))
                        if key not in known:
                            known[key] = len(report['unique_induced_cuts'])
                            report['unique_induced_cuts'].append({'terms':negative['primitive_induced_count_form'],
                                'exact_value_at_witness':negative['primitive_value_at_integer_witness'],
                                'independent_supported_product_replay_complete':False})
                        negative['cut_index'] = known[key]
                        report['negative_blocks'].append(negative)
                    elif smallest is not None and smallest < -1e-8:
                        report['unconfirmed_numeric_negatives'].append(record.copy())
                    report['representative_records'].append(record)
                    report['direct_representatives_completed'] += 1
                    report['pairs_covered_by_congruence'] += orbit['size']
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK,blocked)
                current = None
            child_matrices.clear()
            conditionals.clear()
            files.save(args.output,report)
            print(json.dumps({'root_completed':rid,'representatives':report['direct_representatives_completed'],
                              'negative_blocks':len(report['negative_blocks']),'seconds':time.monotonic()-started}),flush=True)
    except TimeoutError:
        timed_out = True
    except Exception as problem:
        error = repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    complete = report['direct_representatives_completed'] == 84
    if complete:
        assert report['pairs_covered_by_congruence'] == 1112
    report.update(status='complete double-complement representative scan' if complete else 'partial double-complement scan',
                  complete_representative_scan=complete,timed_out=timed_out,error=error,unfinished_case=current,
                  scan_seconds=time.monotonic()-started,total_seconds=time.monotonic()-total_started,
                  max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    files.save(args.output,report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('representative_records','negative_blocks','unique_induced_cuts','preparation')},indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--preparation',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seconds',type=int,default=30)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 30
    if args.prepare:
        assert args.preparation is None
        result = metadata()
        files.save(args.output,result)
        print(json.dumps(result,indent=2),flush=True)
    else:
        assert args.preparation is not None
        with threadpool_limits(limits=1):
            run(args,json.loads(args.preparation.read_text()))
