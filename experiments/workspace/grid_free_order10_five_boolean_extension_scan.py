"""Exact five-Boolean extension intervals at the frozen 48-cut count point.

Preparation performs bindings and synthetic controls only.  The separately
requested scan has a 60-second wall timer, one thread, complete domains, and
bounded exact negative certificates.  No optimizer or new product is used.
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations, islice
import json
from math import comb, gcd
from pathlib import Path
import pickle
import resource
import signal
import struct
import time

import numpy as np
from scipy.sparse import csr_matrix
from threadpoolctl import threadpool_info, threadpool_limits

import grid_free_order10_five_boolean_extension_domains as extension
import grid_free_order10_four_boolean_scan as contraction


old = extension.old
ROOT, LOGS = extension.ROOT, extension.LOGS
DOMAIN = LOGS/'order10-five-boolean-extension-domains.json.gz'
DOMAIN_SHA = 'd53285b4629cfe4f34d361a7caadd96c35d9825b48b71ab7fff518fd1dcab3a1'
SOURCE_SHA = 'b71adc6a56216e2fb211ab30f94711e65c667435cfbd59e49943329383253c9f'
POINT = LOGS/'prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json'
POINT_SHA = '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'
MAX_FIRST = 7
MAX_SAVED_FORMS = 64


def inputs():
    assert old.digest(Path(extension.__file__)) == SOURCE_SHA
    assert old.digest(Path(contraction.__file__)) == extension.SCAN_SOURCE_SHA
    assert old.digest(Path(old.__file__)) == extension.DOMAIN_SOURCE_SHA
    assert old.digest(DOMAIN) == DOMAIN_SHA and old.digest(extension.DOMAIN) == extension.DOMAIN_SHA
    assert old.digest(POINT) == POINT_SHA and old.digest(old.CATALOGUE) == old.CATALOGUE_SHA
    assert old.digest(old.INDEX) == old.INDEX_SHA
    ledger, prior, point = extension.read(DOMAIN), extension.read(extension.DOMAIN), extension.read(POINT)
    assert ledger['source_sha256'] == SOURCE_SHA and ledger['domain_certificate_sha256'] == extension.DOMAIN_SHA
    assert ledger['all_allowed_high_masks_retained'] and not ledger['root_or_flag_pruning']
    assert ledger['all_five_subsets_explicitly_enumerated'] and ledger['root_count'] == 62
    assert ledger['cache_parts'] == prior['cache_parts'] == extension.read(old.INDEX)['cache_parts']
    assert [r['root_type'] for r in ledger['roots']] == [r['root_type'] for r in prior['roots']] == list(range(38, 100))
    assert ledger['summary']['five_subsets'] == 4543737
    for item in ledger['cache_parts']:
        assert old.digest(ROOT/item['path']) == item['sha256']
    counts = point['induced_counts']
    assert len(counts) == 48965 and all(type(c) is int and c >= 0 for c in counts)
    assert point['exact_count_and_held_cut_witness'] and point['required_zeros_hold']
    assert point['x521_zero'] and len(point['required_zero_coordinates']) == 59
    assert 1 in point['required_zero_coordinates'] and 521 in point['required_zero_coordinates']
    core = point['rounded_core_values']
    assert len(core) == 550 and all(type(c) is int for c in core)
    assert all(core[i] == 0 for i in point['required_zero_coordinates'])
    assert len(point['exact_held_cut_values']) == 48 and min(point['exact_held_cut_values']) >= 0
    return ledger, prior, point


def negative_certificate(record, proposed, tensor, automorphisms, counts):
    """Reconstruct all known moments and the chosen cut with Python integers."""
    masks = tuple(proposed['selected_high_masks'])
    assert len(masks) == 5 and list(masks) == sorted(set(masks))
    assert set(masks).issubset(record['high_masks'])
    singles = dict(record['single_flag_positions'])
    pairs = {tuple(item['masks']): item['flag_positions'] for item in record['pair_flag_positions']}
    moments, known = [], []
    for pattern in range(31):
        subset = tuple(masks[i] for i in range(5) if pattern >> i & 1)
        refs = old.monomial_rows(subset, singles, pairs)
        assert len(refs) <= 4
        value = sum(int(tensor.data[k])*int(automorphisms[int(tensor.indices[k])])*counts[int(tensor.indices[k])]
                    for row in refs for k in range(int(tensor.indptr[row]), int(tensor.indptr[row+1])))
        assert value >= 0
        moments.append(value)
        known.append({'pattern': pattern, 'high_masks': list(subset),
                      'cached_product_rows': refs, 'exact_labelled_moment': value})
    moments.append(0)
    constants = extension.literal_constants(moments)
    L = max(-constants[s] for s in extension.ODD)
    U = min(constants[s] for s in extension.EVEN)
    odd = next(s for s in extension.ODD if -constants[s] == L)
    even = next(s for s in extension.EVEN if constants[s] == U)
    assert L > U and (L, U, odd, even) == (proposed['lower'], proposed['upper'],
                                         proposed['odd_state'], proposed['even_state'])
    coefficients = extension.conflict_polynomial(odd, even)
    signed, labelled = [], Counter()
    for pattern, coefficient in coefficients.items():
        entry = known[pattern]
        signed.append({**entry, 'coefficient': coefficient})
        for row in entry['cached_product_rows']:
            for at in range(int(tensor.indptr[row]), int(tensor.indptr[row+1])):
                labelled[int(tensor.indices[at])] += coefficient*int(tensor.data[at])
    labelled = {i: c for i, c in sorted(labelled.items()) if c}
    induced = {i: c*int(automorphisms[i]) for i, c in labelled.items()}
    value = sum(c*counts[i] for i, c in induced.items())
    assert value == U-L == sum(c*moments[p] for p, c in coefficients.items()) < 0
    divisor = gcd(*(abs(c) for c in induced.values()))
    assert divisor > 0 and value % divisor == 0
    primitive = [[i, c//divisor] for i, c in induced.items()]
    return {'root_type': record['root_type'], 'selected_high_masks': list(masks),
        'lower': L, 'upper': U, 'exact_interval_width': U-L,
        'odd_state': odd, 'even_state': even, 'hamming_distance': (odd ^ even).bit_count(),
        'all_32_exact_affine_constants': constants,
        'all_31_known_proper_moments': known, 'signed_proper_monomials': signed,
        'degree_five_coefficient': 0, 'maximum_monomial_degree': max(p.bit_count() for p in coefficients),
        'labelled_induced_embedding_form': [[i, c] for i, c in labelled.items()],
        'primitive_induced_count_form': primitive, 'coefficient_gcd': divisor,
        'exact_labelled_value': value, 'primitive_value_at_integer_witness': value//divisor,
        'normalized_form_sha256': hashlib.sha256(old.canonical(primitive)).hexdigest(),
        'supported_cached_rows': sorted({r for term in signed for r in term['cached_product_rows']}),
        'known_moments_and_interval_recomputed_with_python_integers': True,
        'independent_literal_replay_complete': False, 'optimizer_eligible': False}


def proposed_example(masks, constants, lower, upper):
    odd = extension.ODD[int(np.argmax(-constants[list(extension.ODD)]))]
    even = extension.EVEN[int(np.argmin(constants[list(extension.EVEN)]))]
    return {'selected_high_masks': list(masks), 'lower': int(lower), 'upper': int(upper),
            'odd_state': odd, 'even_state': even}


def sample_union(first, worst):
    result = list(first)
    if worst is not None and not any(item['selected_high_masks'] == worst['selected_high_masks'] for item in result):
        result.append(worst)
    assert len(result) <= MAX_FIRST+1
    return result


def controls():
    """Small synthetic caches test exact extraction, not graph feasibility."""
    high = [7, 11, 13, 14, 19]
    singles = {mask: i+1 for i, mask in enumerate(high)}
    pairs = {pair: [i+6] for i, pair in enumerate(combinations(high, 2))}
    record = {'root_type': -1, 'high_masks': high, 'single_flag_positions': list(singles.items()),
              'pair_flag_positions': [{'masks': list(pair), 'flag_positions': positions}
                                      for pair, positions in pairs.items()]}
    rows, columns, data = [], [], []
    used = set()
    for pattern in range(31):
        subset = tuple(high[i] for i in range(5) if pattern >> i & 1)
        refs = old.monomial_rows(subset, singles, pairs)
        assert len(refs) == 1 and refs[0] not in used
        used.add(refs[0]); rows.append(refs[0]); columns.append(pattern); data.append(1)
    tensor = csr_matrix((np.asarray(data, dtype=np.int64), (rows, columns)), shape=(136, 31))
    cases = []
    for state in (7, 31):
        masses = [1]*32; masses[0] = masses[state] = -1
        counts = extension.moments_from_masses(masses)[:31]
        assert min(counts) >= 0
        for aut in (1, 2, 17):
            proper = np.asarray([[aut*c for c in counts]+[0]], dtype=np.int64)
            constants, lower, upper = extension.interval_batch(proper)
            proposal = proposed_example(high, constants[0], lower[0], upper[0])
            saved = negative_certificate(record, proposal, tensor, [aut]*31, counts)
            assert saved['exact_labelled_value'] == -2*aut
            assert saved['coefficient_gcd'] == aut and saved['primitive_value_at_integer_witness'] == -2
            cases.append({'negative_signed_atoms': [0, state], 'synthetic_automorphism_multiplier': aut,
                          'interval': [saved['lower'], saved['upper']],
                          'raw_value': saved['exact_labelled_value'],
                          'primitive_value': saved['primitive_value_at_integer_witness'],
                          'normalized_form_sha256': saved['normalized_form_sha256']})
    first = [{'selected_high_masks': [i]} for i in range(MAX_FIRST)]
    assert sample_union(first, first[2]) == first
    assert len(sample_union(first, {'selected_high_masks': [99]})) == MAX_FIRST+1
    assert sample_union([], None) == []
    return {'synthetic_cache_extraction_controls': cases,
            'normalization_divisors_checked': [1, 2, 17],
            'first_and_worst_sampling_controls': 3,
            'synthetic_cache_is_not_a_graph_product_certificate': True}


def metadata(ledger, point):
    return {'status': 'prepared exact five-Boolean extension scan; no current-point contraction',
        'source_sha256': old.digest(Path(__file__)), 'extension_source_sha256': SOURCE_SHA,
        'extension_domain_sha256': DOMAIN_SHA, 'four_boolean_domain_sha256': extension.DOMAIN_SHA,
        'contraction_source_sha256': extension.SCAN_SOURCE_SHA,
        'integer_count_point_sha256': POINT_SHA, 'catalogue_sha256': old.CATALOGUE_SHA,
        'cache_index_sha256': old.INDEX_SHA, 'cache_parts': ledger['cache_parts'],
        'family_source_sha256': old.FAMILY_SHA, 'root_count': 62,
        'expected_summary': ledger['summary'], 'workload': ledger['workload'],
        'arithmetic': ledger['arithmetic'], 'required_zero_coordinates': point['required_zero_coordinates'],
        'held_cut_count': len(point['exact_held_cut_values']),
        'maximum_wall_seconds': 60, 'thread_limit': 1, 'batch_size': extension.BATCH_SIZE,
        'negative_sampling': {'first_per_root': MAX_FIRST, 'worst_per_root': 1,
                              'maximum_distinct_normalized_forms_saved': MAX_SAVED_FORMS,
                              'all_sampled_examples_reconstructed_before_saved_form_cap': True},
        'no_point_zero_pruning': True, 'roots_without_five_subsets_retained': True,
        'partial_completed_batch_counts_preserved': True,
        'negative_forms_require_fresh_literal_product_replay': True,
        'current_count_point_read_for_binding_only': True, 'current_point_scan_performed': False,
        'new_product_tensors_generated': False, 'reduced_matrix_loaded': False,
        'optimizer_or_eigensystem_called': False, 'controls': controls()}


def dense_moments(record, extension_record, tensor, embeddings):
    high = record['high_masks']
    singles = dict(record['single_flag_positions'])
    pairs = {tuple(item['masks']): item['flag_positions'] for item in record['pair_flag_positions']}
    values, bounds = contraction.cached_values(tensor, embeddings)
    A = bounds['maximum_cached_product_value']
    dense, stream = [], hashlib.sha256()
    maximum, references = 0, 0
    for degree in range(5):
        array = np.empty(comb(len(high), degree), dtype=np.int64)
        visited = 0
        for indices in combinations(range(len(high)), degree):
            subset = tuple(high[i] for i in indices)
            refs = old.monomial_rows(subset, singles, pairs)
            stream.update(struct.pack('<qq', degree, len(refs)))
            stream.update(struct.pack('<'+'q'*degree, *subset))
            stream.update(struct.pack('<'+'q'*len(refs), *refs))
            value = sum(int(values[row]) for row in refs)
            assert 0 <= value <= 4*A <= extension.LIMIT
            array[extension.colex_rank(indices)] = value
            maximum = max(maximum, value); references += len(refs); visited += 1
        assert visited == extension_record['squarefree_monomials_by_degree'][str(degree)]
        dense.append(array)
    assert stream.hexdigest() == record['monomial_product_row_reference_sha256'] == extension_record['monomial_product_row_reference_sha256']
    assert references == extension_record['monomial_product_row_references']
    assert 1024*maximum <= extension.LIMIT
    bounds.update(maximum_proper_moment=maximum,
                  safe_five_atom_transform_and_row_sum_bound=1024*maximum)
    return dense, bounds


def publish_progress(progress, updates):
    blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
    try:
        progress.update(updates)
    finally:
        signal.pthread_sigmask(signal.SIG_SETMASK, blocked)


def scan_root(record, extension_record, flags, tensor, embeddings, automorphisms, counts, result, saved_by_hash):
    high = record['high_masks']
    progress = {'root_type': record['root_type'], 'high_mask_count': len(high),
        'expected_five_subsets': extension_record['five_subsets'], 'five_subsets_tested': 0,
        'infeasible_intervals': 0, 'tight_intervals': 0, 'positive_width_intervals': 0,
        'completed_batches': 0, 'minimum_interval_width': None, 'maximum_interval_width': None,
        'first_or_worst_pending_examples': [], 'sampled_examples_exactly_reconstructed': 0,
        'sampled_example_hamming_distances': [], 'saved_negative_form_indices': [],
        'duplicate_normalized_examples': 0, 'examples_omitted_by_global_saved_form_cap': 0,
        'complete_root': False, 'count_zero_pruning_used': False}
    result['root_records'].append(progress)
    assert high == extension_record['high_masks']
    assert len(flags) == record['cached_flag_count']
    assert [flag['masks'][0] for flag in flags if flag['size'] == 1] == high
    assert tensor.shape == (record['cached_tensor_lower_rows'], len(counts))
    dense, bounds = dense_moments(record, extension_record, tensor, embeddings)
    progress['arithmetic_bounds'] = bounds
    table = extension.colex_table(len(high))
    iterator = iter(combinations(range(len(high)), 5))
    stream = hashlib.sha256(struct.pack('<qq', record['root_type'], extension_record['five_subsets']))
    first, worst = [], None
    high_array = np.asarray(high, dtype=np.uint8)
    while True:
        tuples = list(islice(iterator, extension.BATCH_SIZE))
        if not tuples:
            break
        indices = np.asarray(tuples, dtype=np.int64)
        proper = extension.batch_proper_moments(dense, indices, table)
        constants, L, U = extension.interval_batch(proper)
        widths = U-L
        bad = np.flatnonzero(widths < 0)
        bad_count = int(len(bad)); tight_count = int(np.count_nonzero(widths == 0))
        positive_count = int(np.count_nonzero(widths > 0))
        assert bad_count+tight_count+positive_count == len(tuples)
        if bad_count:
            for index in bad[:MAX_FIRST-len(first)]:
                i = int(index)
                masks = [high[j] for j in tuples[i]]
                first.append(proposed_example(masks, constants[i], L[i], U[i]))
            i = int(np.argmin(widths))
            candidate = proposed_example([high[j] for j in tuples[i]], constants[i], L[i], U[i])
            if worst is None or candidate['upper']-candidate['lower'] < worst['upper']-worst['lower']:
                worst = candidate
        least, greatest = int(widths.min()), int(widths.max())
        current_min, current_max = progress['minimum_interval_width'], progress['maximum_interval_width']
        # bytes(uint8 high-mask rows) is the same stream as the frozen
        # explicit lexicographic five-subset enumeration.
        stream.update(high_array[indices].tobytes(order='C'))
        publish_progress(progress, {
            'five_subsets_tested': progress['five_subsets_tested']+len(tuples),
            'infeasible_intervals': progress['infeasible_intervals']+bad_count,
            'tight_intervals': progress['tight_intervals']+tight_count,
            'positive_width_intervals': progress['positive_width_intervals']+positive_count,
            'completed_batches': progress['completed_batches']+1,
            'minimum_interval_width': least if current_min is None else min(current_min, least),
            'maximum_interval_width': greatest if current_max is None else max(current_max, greatest),
            'first_or_worst_pending_examples': sample_union(first, worst),
            'last_completed_five_subset': [high[j] for j in tuples[-1]],
            'completed_subset_prefix_sha256': stream.hexdigest()})
    assert progress['five_subsets_tested'] == extension_record['five_subsets']
    assert progress['completed_batches'] == extension_record['batch_count_at_50000']
    assert stream.hexdigest() == extension_record['complete_five_subset_stream_sha256']
    progress['complete_five_subset_stream_sha256'] = stream.hexdigest()
    pending = sample_union(first, worst)
    for proposal in pending:
        certificate = negative_certificate(record, proposal, tensor, automorphisms, counts)
        key = certificate['normalized_form_sha256']
        blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
        try:
            progress['sampled_examples_exactly_reconstructed'] += 1
            progress['sampled_example_hamming_distances'].append(certificate['hamming_distance'])
            if key in saved_by_hash:
                index = saved_by_hash[key]
                assert result['negative_certificates'][index]['primitive_induced_count_form'] == certificate['primitive_induced_count_form']
                progress['duplicate_normalized_examples'] += 1
                progress['saved_negative_form_indices'].append(index)
            elif len(result['negative_certificates']) < MAX_SAVED_FORMS:
                index = len(result['negative_certificates'])
                saved_by_hash[key] = index
                result['negative_certificates'].append(certificate)
                progress['saved_negative_form_indices'].append(index)
            else:
                progress['examples_omitted_by_global_saved_form_cap'] += 1
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
    publish_progress(progress, {'first_or_worst_pending_examples': [], 'complete_root': True})


def run(prepared, output, seconds):
    assert 0 < seconds <= 60
    started = time.monotonic()
    result = {'source_sha256': old.digest(Path(__file__)), 'preparation': prepared,
        'integer_count_point_sha256': POINT_SHA, 'requested_wall_seconds': seconds,
        'root_records': [], 'negative_certificates': [], 'complete_extension_scan': False,
        'new_product_tensors_generated': False, 'reduced_matrix_loaded': False,
        'optimizer_or_eigensystem_called': False, 'graph_existence_resolved': False,
        'joint_distribution_across_all_masks_certified': False, 'PSD_feasibility_certified': False}
    current, error, timed_out = None, None, False
    expected_roots = list(range(38, 100))
    def deadline(_signum, _frame):
        raise TimeoutError('bounded exact five-Boolean extension scan')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        with threadpool_limits(limits=1):
            assert all(info['num_threads'] <= 1 for info in threadpool_info())
            ledger, prior, point = inputs()
            assert prepared == metadata(ledger, point)
            catalogue = pickle.loads(old.CATALOGUE.read_bytes())
            assert list(catalogue[1][6]) == expected_roots
            counts = point['induced_counts']
            automorphisms = [int(a) for a in catalogue[2]]
            assert len(automorphisms) == len(counts) and min(automorphisms) > 0
            embeddings = [a*c for a, c in zip(automorphisms, counts)]
            extension_by_root = {r['root_type']: r for r in ledger['roots']}
            by_root = {r['root_type']: r for r in prior['roots']}
            saved_by_hash = {}
            for _, blocks in old.cache_parts():
                for root, flags, tensor in blocks:
                    current = int(root)
                    scan_root(by_root[current], extension_by_root[current], flags, tensor,
                              embeddings, automorphisms, counts, result, saved_by_hash)
                    current = None
    except TimeoutError:
        timed_out = True
    except Exception as problem:
        error = repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    result['root_records'].sort(key=lambda record: record['root_type'])
    complete = (not error and not timed_out
                and [r['root_type'] for r in result['root_records']] == expected_roots
                and all(r['complete_root'] for r in result['root_records']))
    summary = {key: sum(r[key] for r in result['root_records']) for key in
               ('five_subsets_tested', 'infeasible_intervals', 'tight_intervals',
                'positive_width_intervals', 'completed_batches', 'sampled_examples_exactly_reconstructed',
                'duplicate_normalized_examples', 'examples_omitted_by_global_saved_form_cap')}
    assert summary['five_subsets_tested'] == sum(summary[key] for key in
            ('infeasible_intervals', 'tight_intervals', 'positive_width_intervals'))
    if complete:
        assert summary['five_subsets_tested'] == 4543737 and summary['completed_batches'] == 132
    result.update(status='complete exact five-Boolean extension scan' if complete else 'UNKNOWN: incomplete five-Boolean extension scan',
        complete_extension_scan=bool(complete), summary=summary,
        saved_distinct_negative_forms=len(result['negative_certificates']),
        all_five_variable_extensions_exist=(not bool(summary['infeasible_intervals'])) if complete else None,
        error=error, timed_out=timed_out, unfinished_root=current,
        completed_root_count=sum(r['complete_root'] for r in result['root_records']),
        scan_seconds=time.monotonic()-started, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in
                     ('preparation', 'root_records', 'negative_certificates')}, indent=2), flush=True)
    print('output_sha256', old.digest(output), flush=True)
    return int(error is not None)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--prepare', action='store_true')
    mode.add_argument('--replay-preparation', action='store_true')
    mode.add_argument('--run', action='store_true')
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    assert 0 < args.seconds <= 60
    if args.prepare or args.replay_preparation:
        started = time.monotonic()
        ledger, _, point = inputs()
        prepared = metadata(ledger, point)
        if args.prepare:
            assert not args.preparation.exists()
            args.preparation.write_text(json.dumps(prepared, indent=2)+'\n')
            destination = args.preparation
            result = prepared
        else:
            assert args.output and not args.output.exists()
            assert extension.read(args.preparation) == prepared
            result = {'status': 'cold five-Boolean extension scan preparation replay PASS',
                'source_sha256': old.digest(Path(__file__)), 'preparation_sha256': old.digest(args.preparation),
                'integer_count_point_sha256': POINT_SHA, 'expected_summary': prepared['expected_summary'],
                'controls': prepared['controls'], 'current_point_scan_performed': False}
            args.output.write_text(json.dumps(result, indent=2)+'\n')
            destination = args.output
        print(json.dumps(result, indent=2), flush=True)
        print('output_sha256', old.digest(destination), 'elapsed_seconds', time.monotonic()-started,
              'peak_rss_kib', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, flush=True)
    else:
        assert args.output and not args.output.exists()
        raise SystemExit(run(extension.read(args.preparation), args.output, args.seconds))


if __name__ == '__main__':
    main()
