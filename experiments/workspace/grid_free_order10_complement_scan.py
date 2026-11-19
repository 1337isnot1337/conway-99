"""Bounded exact-gated separation of the 737 Boolean-complement matrices.

All 916 existing scalar child blocks are separately screened at the same
integer point. The 4,478 quota-one cases are recorded as mathematically
implied by child PSD, not as directly scanned or exactly certified.
No new product tensors, dense count reduction or optimizer are used.
"""

import argparse
from collections import Counter
from functools import reduce
import gzip
import json
from math import gcd
from pathlib import Path
import pickle
import resource
import signal
import time

import numpy as np
from threadpoolctl import threadpool_limits

import grid_free_order10_complement_domains as domains
import grid_free_order10_projector_probe as point
import grid_free_order10_r8s1 as forms
from grid_free_order10_r8s1_scan import FullScanner
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ROOT/'experiments/logs/moments-and-counts/order10-complement-domains.json.gz'
DOMAIN_SHA = '67ab98b4e727c6de1a7e79fddec560942963b6c93fdc5901ede8b38dea5f2b30'
DOMAIN_SOURCE_SHA = '4961411ec0f7671abb7e34c5dbd4ec257ac98f9bffcb745a408e979751179ed8'


def inputs():
    assert files.digest(DOMAIN) == DOMAIN_SHA
    assert files.digest(Path(domains.__file__)) == DOMAIN_SOURCE_SHA
    assert files.digest(point.WITNESS) == point.WITNESS_SHA
    assert files.digest(domains.BASE) == domains.BASE_SHA
    assert files.digest(domains.CHILD) == domains.CHILD_SHA
    ledger = domains.read(DOMAIN)
    assert ledger['source_sha256'] == DOMAIN_SOURCE_SHA
    assert ledger['summary']['high_mask_domains'] == 5215
    assert ledger['summary']['quota_one_redundant_masks'] == 4478
    assert ledger['summary']['new_complement_candidates'] == 737
    witness = json.loads(point.WITNESS.read_text())
    counts = witness['induced_counts']
    assert len(counts) == 48965 and all(type(x) is int and x >= 0 for x in counts)
    assert witness['x521_zero'] and len(witness['required_zero_coordinates']) == 59
    return ledger, counts


def metadata(ledger):
    return {
        'source_sha256': files.digest(Path(__file__)),
        'domain_source_sha256': DOMAIN_SOURCE_SHA, 'domain_certificate_sha256': DOMAIN_SHA,
        'base_cache_sha256': domains.BASE_SHA, 'child_cache_sha256': domains.CHILD_SHA,
        'catalogue_sha256': domains.direct.CATALOGUE_SHA,
        'integer_witness_sha256': point.WITNESS_SHA,
        'negative_direction_source_sha256': files.digest(Path(__file__).with_name('grid_free_order10_r8s1_scan.py')),
        'scalar_child_blocks_to_scan': 916, 'complement_blocks_to_scan': 737,
        'complement_root_types': 82, 'distinct_conditional_child_types': 183,
        'complement_quotient_lower_entries': 1903068,
        'quota_one_cases_directly_scanned': 0,
        'quota_one_cases_implied_by_child_PSD': 4478,
        'largest_complement_order_before_zero_row_deletion': 100,
        'maximum_scan_seconds': 120, 'threads': 1,
        'all_domains_retained': True, 'point_dependent_cache_pruning': False,
        'all_count_contractions_use_Python_integers': True,
        'selected_zero_rows_checked_before_deletion': True,
        'independent_supported_product_replay_deferred': True,
        'new_product_tensors_generated': False, 'dense_reduction_loaded': False, 'optimizer_called': False,
    }


def raw_form(tensor, vector, automorphisms):
    result = Counter()
    for i, a in enumerate(vector):
        if not a:
            continue
        for j, b in enumerate(vector[:i+1]):
            if not b:
                continue
            factor = a*b*(1 if i == j else 2)
            row = i*(i+1)//2+j
            for k in range(tensor.indptr[row], tensor.indptr[row+1]):
                index = int(tensor.indices[k])
                result[index] += factor*int(tensor.data[k])*automorphisms[index]
    return result


def accepted_form(counter, counts, quadratic):
    terms = [[index, value] for index, value in sorted(counter.items()) if value]
    divisor = reduce(gcd, (abs(value) for _, value in terms), 0)
    assert divisor > 0
    terms = [[index, value//divisor] for index, value in terms]
    value = sum(coefficient*counts[index] for index, coefficient in terms)
    assert value*divisor == quadratic < 0
    return {'primitive_induced_count_form': terms, 'induced_form_gcd': divisor,
            'primitive_value_at_integer_witness': value,
            'independent_supported_product_replay_complete': False,
            'core_form_reduced': False, 'optimizer_eligible': False}


def run(args, prepared):
    total_started = time.monotonic()
    ledger, counts = inputs()
    assert prepared == metadata(ledger)
    assert files.digest(args.catalogue) == domains.direct.CATALOGUE_SHA
    with args.catalogue.open('rb') as stream:
        data = pickle.load(stream)
    base_list = pickle.loads(domains.BASE.read_bytes())
    child_saved = pickle.loads(gzip.decompress(domains.CHILD.read_bytes()))
    assert child_saved['point_independent'] and child_saved['complete_root_family']
    assert not child_saved['zero_flags_or_roots_removed']
    assert child_saved['construction_source_sha256'] == domains.TRANSPORT_SHA
    assert [root for root, _, _ in child_saved['blocks']] == data[1][8]
    bases = {root: (flags, tensor) for root, flags, tensor in base_list}
    children = {root: (masks, tensor) for root, masks, tensor in child_saved['blocks']}
    cases = [(record, flag) for record in ledger['roots'] for flag in record['flags']
             if flag['classification'] == 'new_complement_candidate']
    assert len(cases) == 737
    needed = {flag['child_root_type'] for _, flag in cases}
    assert len(needed) == 183
    embeddings = [int(a)*c for a, c in zip(data[2], counts)]
    child_matrices, base_matrices = {}, {}
    result = {
        'source_sha256': files.digest(Path(__file__)), 'preparation_sha256': files.digest(args.preparation),
        'preparation': prepared, 'scalar_child_records': [], 'complement_records': [],
        'negative_blocks': [], 'unique_induced_cuts': [], 'unconfirmed_numeric_negatives': [],
        'independent_supported_product_replay_complete': False,
        'scalar_child_PSD_certified': False, 'complement_PSD_certified': False,
        'quota_one_cases_directly_scanned': 0, 'quota_one_cases_implied_by_child_PSD': 4478,
    }
    known, timed_out, error, current = {}, False, None, None
    scan_started = time.monotonic()

    def commit(record, negative, target, matrix=None):
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
        try:
            if negative is not None:
                key = tuple(map(tuple, negative['primitive_induced_count_form']))
                if key not in known:
                    known[key] = len(result['unique_induced_cuts'])
                    result['unique_induced_cuts'].append({
                        'terms': negative['primitive_induced_count_form'],
                        'exact_value_at_witness': negative['primitive_value_at_integer_witness'],
                        'independent_supported_product_replay_complete': False})
                negative['cut_index'] = known[key]
                result['negative_blocks'].append(negative)
            elif record['smallest_numeric_eigenvalue'] is not None and record['smallest_numeric_eigenvalue'] < -1e-8:
                result['unconfirmed_numeric_negatives'].append(record.copy())
            result[target].append(record)
            if matrix is not None and record['root_type'] in needed:
                child_matrices[record['root_type']] = matrix
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)

    def deadline(_signum, _frame):
        raise TimeoutError('bounded scalar-child and complement separation')

    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    try:
        for root, masks, tensor in child_saved['blocks']:
            current = ['scalar_child', root]
            assert masks == [mask for mask, _ in data[3][root] if mask.bit_count() >= 3]
            order = len(masks)+1
            assert tensor.shape == (order*(order+1)//2, 48965)
            matrix = FullScanner.matrix(tensor, order, embeddings)
            vector, quadratic, smallest, zeros = FullScanner.negative(matrix)
            record = {'kind': 'scalar_child', 'root_type': root, 'order': order,
                      'smallest_numeric_eigenvalue': smallest, 'exact_zero_rows': zeros}
            negative = None
            if vector is not None:
                v = np.asarray(vector, dtype=object)
                assert int(v@matrix@v) == quadratic < 0
                form = accepted_form(raw_form(tensor, vector, data[2]), counts, quadratic)
                negative = {**record, 'integer_vector': vector, 'integer_quadratic_value': quadratic, **form}
            commit(record, negative, 'scalar_child_records', matrix)
            current = None
            if len(result['scalar_child_records']) % 128 == 0:
                files.save(args.output, result)
                print(json.dumps({'scalar_children_completed': len(result['scalar_child_records']),
                                  'negative_blocks': len(result['negative_blocks']),
                                  'seconds': time.monotonic()-scan_started}), flush=True)
        assert set(child_matrices) == needed
        for case_index, (record, flag) in enumerate(cases):
            root, selected = record['root_type'], flag['base_position']
            child = flag['child_root_type']
            current = ['complement', root, flag['mask']]
            flags, tensor = bases[root]
            assert [tuple(f) for f in flags] == [tuple(record['root_rows'])]+[
                forms.attach(record['root_rows'], mask) for mask in record['high_masks']]
            order = len(flags)
            assert tensor.shape == (order*(order+1)//2, 6535)
            if root not in base_matrices:
                base_matrices[root] = FullScanner.matrix(tensor, order, embeddings)
            parent = base_matrices[root]
            child_masks, child_tensor = children[child]
            assert child_masks == flag['child_high_masks']
            child_matrix = child_matrices[child]
            lift = flag['sparse_rows']
            assert len(lift) == order and lift[0] == lift[selected] == [0]
            localizer = np.empty((order, order), dtype=object)
            for i in range(order):
                for j in range(i+1):
                    conditional = sum(child_matrix[u,v] for u in lift[i] for v in lift[j])
                    localizer[i,j] = localizer[j,i] = int(parent[i,j])-conditional
            assert all(localizer[selected,j] == 0 for j in range(order))
            keep = [i for i in range(order) if i != selected]
            vector, quadratic, smallest, zeros = FullScanner.negative(localizer[np.ix_(keep,keep)])
            summary = {'kind': 'complement', 'root_type': root, 'selected_mask': flag['mask'],
                       'selected_base_position': selected, 'child_root_type': child,
                       'order': order, 'quotient_order': len(keep),
                       'selected_zero_row_checked_exactly': True,
                       'smallest_numeric_eigenvalue': smallest, 'exact_zero_quotient_rows': zeros}
            negative = None
            if vector is not None:
                full = [0]*order
                for i, value in zip(keep, vector):
                    full[i] = value
                v = np.asarray(full, dtype=object)
                assert int(v@localizer@v) == quadratic < 0
                child_vector = [0]*len(child_matrix)
                for coefficient, row in zip(full, lift):
                    for column in row:
                        child_vector[column] += coefficient
                w = np.asarray(child_vector, dtype=object)
                assert int(v@parent@v-w@child_matrix@w) == quadratic
                combined = raw_form(tensor, full, data[2])
                conditional_form = raw_form(child_tensor, child_vector, data[2])
                for index, coefficient in conditional_form.items():
                    combined[index] -= coefficient
                form = accepted_form(combined, counts, quadratic)
                negative = {**summary, 'integer_parent_vector': full,
                            'integer_child_vector': child_vector,
                            'integer_quadratic_value': quadratic, **form}
            commit(summary, negative, 'complement_records')
            current = None
            if (case_index+1) % 64 == 0:
                files.save(args.output, result)
                print(json.dumps({'complements_completed': len(result['complement_records']),
                                  'negative_blocks': len(result['negative_blocks']),
                                  'unique_exact_induced_forms_pending_replay': len(result['unique_induced_cuts']),
                                  'seconds': time.monotonic()-scan_started}), flush=True)
    except TimeoutError:
        timed_out = True
    except Exception as problem:
        error = repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    child_complete = len(result['scalar_child_records']) == 916
    complement_complete = len(result['complement_records']) == 737
    result.update(
        status='complete scalar-child and complement discovery scan' if child_complete and complement_complete else 'partial scalar-child and complement discovery scan',
        complete_child_scan=child_complete, complete_complement_scan=complement_complete,
        scalar_child_blocks_scanned=len(result['scalar_child_records']),
        complement_blocks_scanned=len(result['complement_records']),
        exact_negative_blocks=len(result['negative_blocks']), unique_induced_cut_count=len(result['unique_induced_cuts']),
        timed_out=timed_out, interrupted_case=current, error=error,
        scan_seconds=time.monotonic()-scan_started, total_seconds=time.monotonic()-total_started,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    )
    files.save(args.output, result)
    print(json.dumps({k: result[k] for k in ('status','complete_child_scan','complete_complement_scan',
        'scalar_child_blocks_scanned','complement_blocks_scanned','exact_negative_blocks',
        'unique_induced_cut_count','timed_out','interrupted_case','error','scan_seconds','total_seconds','peak_rss_kib')},indent=2),flush=True)
    if error:
        raise RuntimeError(error)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--preparation', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=120)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 120
    if args.prepare:
        assert args.preparation is None
        ledger, _ = inputs()
        prepared = metadata(ledger)
        files.save(args.output, prepared)
        print(json.dumps(prepared,indent=2),flush=True)
    else:
        assert args.preparation
        with threadpool_limits(limits=1):
            run(args, json.loads(args.preparation.read_text()))
