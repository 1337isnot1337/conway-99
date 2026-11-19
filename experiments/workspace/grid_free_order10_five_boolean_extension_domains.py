"""Prepare complete five-Boolean marginal extensions from degree-four moments.

This file reads the small catalogue and the frozen four-Boolean domain ledger.
It does not load a count point, product tensor, or reduced-count matrix.  The
only numerical arrays below are explicit synthetic Boolean controls.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path
import pickle
import resource
import signal
import struct
import time

import numpy as np

import grid_free_order10_four_boolean_domains as old


ROOT = old.ROOT
LOGS = ROOT/'experiments/logs/moments-and-counts'
DOMAIN = LOGS/'order10-four-boolean-domains.json.gz'
DOMAIN_SHA = '5fd508dba5bcda5aeb8231ab39dd6b68df5c55ffffebb98b7344e874155bef35'
DOMAIN_SOURCE_SHA = '52ab6687063ca4e16930013cbb159658337e8f8ce007f3d82c1d39d3c9a042d6'
SCAN_SOURCE = ROOT/'experiments/workspace/grid_free_order10_four_boolean_scan.py'
SCAN_SOURCE_SHA = '5a97b204d8830af614f22c6e72f6ca4c120ec5c6a31320b4b8841c7e0ce19286'
ODD = tuple(s for s in range(32) if s.bit_count() % 2)
EVEN = tuple(s for s in range(32) if not s.bit_count() % 2)
LIMIT = (1 << 63)-1
BATCH_SIZE = 50000


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def direct_single(rows, mask):
    """Visible pair caps after appending one vertex, without attaching rows."""
    assert len(rows) == 6 and 0 <= mask < 64
    for i in range(6):
        if (rows[i]&mask).bit_count()+((mask >> i)&1) > 2:
            return False
        for j in range(i):
            if ((rows[i]&rows[j]).bit_count()+((rows[i] >> j)&1)
                    +((mask >> i)&1)*((mask >> j)&1)) > 2:
                return False
    return True


def direct_pair(rows, a, b, edge):
    """Visible pair caps after appending two specified mask classes."""
    assert len(rows) == 6 and 0 <= a < b < 64 and edge in (0, 1)
    if (a&b).bit_count()+edge > 2:
        return False
    for i in range(6):
        ai, bi = (a >> i)&1, (b >> i)&1
        if (rows[i]&a).bit_count()+edge*bi+ai > 2:
            return False
        if (rows[i]&b).bit_count()+edge*ai+bi > 2:
            return False
        for j in range(i):
            if ((rows[i]&rows[j]).bit_count()+((rows[i] >> j)&1)
                    +ai*((a >> j)&1)+bi*((b >> j)&1)) > 2:
                return False
    return True


def colex_rank(indices):
    return sum(comb(i, j+1) for j, i in enumerate(indices))


def colex_table(h):
    assert 0 <= h <= 42
    return np.asarray([[comb(i, k) for k in range(5)] for i in range(h)], dtype=np.int64).reshape(h, 5)


def batch_proper_moments(dense, indices, table):
    """Gather the 31 known moments; the degree-five slot is exactly zero."""
    assert indices.dtype == np.dtype('int64') and indices.ndim == 2 and indices.shape[1] == 5
    h = len(table)
    assert table.shape == (h, 5) and table.dtype == np.dtype('int64')
    assert np.all((indices >= 0)&(indices < h)) and np.all(indices[:, 1:] > indices[:, :-1])
    assert len(dense) == 5
    for degree in range(5):
        assert dense[degree].dtype == np.dtype('int64')
        assert dense[degree].shape == (comb(h, degree),)
    answer = np.zeros((len(indices), 32), dtype=np.int64)
    answer[:, 0] = dense[0][0]
    for pattern in range(1, 31):
        positions = [i for i in range(5) if pattern >> i & 1]
        ranks = np.zeros(len(indices), dtype=np.int64)
        for j, position in enumerate(positions):
            ranks += table[indices[:, position], j+1]
        answer[:, pattern] = dense[len(positions)][ranks]
    return answer


def interval_batch(proper):
    """Exact int64 transform after a Python-integer bound covers every step."""
    assert proper.dtype == np.dtype('int64') and proper.ndim == 2 and proper.shape[1] == 32
    assert np.all(proper >= 0) and np.all(proper[:, 31] == 0)
    maximum = int(proper.max(initial=0))
    # Any intermediate is a signed sum of at most 32 original entries.
    # A sum across all 32 atom columns has absolute partial sums <=1024*M.
    assert 1024*maximum <= LIMIT
    atoms = proper.copy()
    for bit in range(5):
        for pattern in range(32):
            if not (pattern >> bit & 1):
                atoms[:, pattern] -= atoms[:, pattern | (1 << bit)]
    assert np.all(atoms.sum(axis=1) == proper[:, 0])
    lower = (-atoms[:, ODD]).max(axis=1)
    upper = atoms[:, EVEN].min(axis=1)
    assert np.all(lower >= 0)  # The all-present atom is exactly x.
    return atoms, lower, upper


def atom_polynomial(state):
    """Squarefree monomial coefficients of the exact-assignment indicator."""
    assert 0 <= state < 32
    return {mask: (-1)**(mask.bit_count()-state.bit_count())
            for mask in range(32) if mask & state == state}


def conflict_polynomial(odd, even):
    assert odd in ODD and even in EVEN
    coefficients = Counter(atom_polynomial(odd))
    coefficients.update(atom_polynomial(even))
    coefficients = {mask: c for mask, c in sorted(coefficients.items()) if c}
    assert 31 not in coefficients and all(mask.bit_count() <= 4 for mask in coefficients)
    assert all(c in (-1, 1) for c in coefficients.values()) and len(coefficients) <= 31
    return coefficients


def moments_from_masses(masses):
    assert len(masses) == 32 and all(type(v) is int for v in masses)
    return [sum(masses[state] for state in range(32) if state & mask == mask)
            for mask in range(32)]


def literal_constants(moments):
    assert len(moments) == 32
    return [sum(coefficient*moments[mask] for mask, coefficient in atom_polynomial(state).items()
                if mask != 31) for state in range(32)]


def four_marginal_atoms(masses):
    answer = []
    for omitted in range(5):
        kept = [i for i in range(5) if i != omitted]
        answer.append([sum(masses[state] for state in range(32)
                           if all(((state >> at)&1) == ((pattern >> j)&1)
                                  for j, at in enumerate(kept)))
                       for pattern in range(16)])
    return answer


def controls():
    templates, distances = [], Counter()
    literal_checks = 0
    for odd in ODD:
        for even in EVEN:
            coefficients = conflict_polynomial(odd, even)
            distance = (odd ^ even).bit_count()
            distances[distance] += 1
            for state in range(32):
                value = sum(c for mask, c in coefficients.items() if state & mask == mask)
                assert value == int(state == odd)+int(state == even)
                literal_checks += 1
            if distance == 1:
                free = (odd ^ even).bit_length()-1
                assert all(not (mask >> free & 1) for mask in coefficients)
            templates.append({'odd_state': odd, 'even_state': even,
                              'hamming_distance': distance,
                              'monomial_coefficients': [[mask, c] for mask, c in coefficients.items()]})
    assert dict(distances) == {1: 80, 3: 160, 5: 16}
    assert max(len(record['monomial_coefficients']) for record in templates) == 31

    distributions = [('zero', [0]*32)]
    for state in range(32):
        for weight in (1, 3):
            masses = [0]*32; masses[state] = weight
            distributions.append((f'pure-{state}-{weight}', masses))
    for a, b in combinations(range(32), 2):
        masses = [0]*32; masses[a] = 1; masses[b] = 2
        distributions.append((f'two-atom-{a}-{b}', masses))
    distributions.append(('uniform', [1]*32))
    for weight in (1, 3):
        for parity in (0, 1):
            distributions.append((f'parity-{parity}-{weight}',
                                  [weight*int(state.bit_count() % 2 == parity) for state in range(32)]))
    distributions.append(('nonuniform', [(state*state+7*state+11) % 13 for state in range(32)]))
    proper = []
    for _, masses in distributions:
        moments = moments_from_masses(masses)
        proper.append(moments[:31]+[0])
    atoms, lower, upper = interval_batch(np.asarray(proper, dtype=np.int64))
    stream = hashlib.sha256()
    examples = []
    for i, (name, masses) in enumerate(distributions):
        moments = moments_from_masses(masses)
        literal = literal_constants(moments)
        assert [int(x) for x in atoms[i]] == literal
        x = moments[31]
        assert int(lower[i]) <= x <= int(upper[i])
        reconstructed = [literal[s]+(1 if s in ODD else -1)*x for s in range(32)]
        assert reconstructed == masses
        for endpoint in sorted(set((int(lower[i]), int(upper[i])))):
            endpoint_masses = [literal[s]+(1 if s in ODD else -1)*endpoint for s in range(32)]
            assert min(endpoint_masses) >= 0
            assert moments_from_masses(endpoint_masses)[:31] == moments[:31]
        stream.update(old.canonical({'name': name, 'masses': masses, 'moments': moments,
                                     'lower': int(lower[i]), 'upper': int(upper[i])}))
        if name.startswith('parity') or name in ('zero', 'uniform', 'nonuniform'):
            examples.append({'name': name, 'masses': masses, 'moments_through_degree_four': moments[:31],
                             'actual_fifth_moment': x, 'interval': [int(lower[i]), int(upper[i])]})
        if name.startswith('parity'):
            weight = int(name.rsplit('-', 1)[1])
            assert (int(lower[i]), int(upper[i])) == (0, weight)
    assert len(distributions) == 567

    strict_controls = []
    for negative_state in (7, 31):
        masses = [1]*32; masses[0] = masses[negative_state] = -1
        moments = moments_from_masses(masses)
        proper = np.asarray([moments[:31]+[0]], dtype=np.int64)
        constants, L, U = interval_batch(proper)
        marginals = four_marginal_atoms(masses)
        assert len(marginals) == 5 and all(len(row) == 16 for row in marginals)
        assert min(v for row in marginals for v in row) == 0
        assert max(v for row in marginals for v in row) == 2
        assert int(L[0])-int(U[0]) == 2
        odd = ODD[int(np.argmax(-constants[0, ODD]))]
        even = EVEN[int(np.argmin(constants[0, EVEN]))]
        coefficients = conflict_polynomial(odd, even)
        value = sum(c*moments[mask] for mask, c in coefficients.items())
        assert value == int(U[0])-int(L[0]) == -2
        strict_controls.append({'negative_signed_atoms': [0, negative_state],
            'signed_masses': masses, 'moments_through_degree_four': moments[:31],
            'four_marginal_atoms': marginals, 'interval': [int(L[0]), int(U[0])],
            'odd_state': odd, 'even_state': even, 'hamming_distance': (odd ^ even).bit_count(),
            'conflicting_polynomial': [[mask, c] for mask, c in coefficients.items()],
            'exact_negative_value': value,
            'scope': 'synthetic Boolean moments, not graph counts'})

    gather_checks = 0
    for h in range(5, 9):
        table = colex_table(h)
        dense = [np.asarray([1000*k+17*i+5 for i in range(comb(h, k))], dtype=np.int64)
                 for k in range(5)]
        subsets = list(combinations(range(h), 5))
        gathered = batch_proper_moments(dense, np.asarray(subsets, dtype=np.int64), table)
        constants, L, U = interval_batch(gathered)
        for at, subset in enumerate(subsets):
            expected = []
            for pattern in range(31):
                indices = tuple(subset[i] for i in range(5) if pattern >> i & 1)
                expected.append(int(dense[len(indices)][colex_rank(indices)]))
            expected.append(0)
            assert gathered[at].tolist() == expected
            literal = literal_constants(expected)
            assert constants[at].tolist() == literal
            assert int(L[at]) == max(-literal[s] for s in ODD)
            assert int(U[at]) == min(literal[s] for s in EVEN)
            gather_checks += 1
    assert gather_checks == 84
    return {'opposite_parity_pair_templates': templates,
        'pair_templates_by_hamming_distance': {str(k): v for k, v in sorted(distances.items())},
        'literal_polynomial_evaluations': literal_checks,
        'maximum_nonzero_monomials_per_cut': 31, 'maximum_absolute_monomial_coefficient': 1,
        'positive_distribution_controls': len(distributions),
        'positive_distribution_control_sha256': stream.hexdigest(),
        'selected_positive_controls': examples,
        'strictly_stronger_than_four_atoms_controls': strict_controls,
        'synthetic_colex_gather_and_transform_controls': gather_checks,
        'real_interval_has_integer_endpoints_for_integer_known_moments': True}


def root_inventory(record, catalogue):
    root, rows = int(record['root_type']), tuple(record['root_rows'])
    assert rows == tuple(catalogue[0][root]) and len(rows) == 6
    assert all(row >> 6 == 0 and not (row >> i & 1) for i, row in enumerate(rows))
    assert all(((rows[i] >> j)&1) == ((rows[j] >> i)&1) for i in range(6) for j in range(6))
    high = [m for m in range(64) if m.bit_count() >= 3 and direct_single(rows, m)]
    assert high == record['high_masks']
    assert all(direct_single(rows, m) == old.caps(old.attach(rows, m)) for m in range(64))
    singles = dict(record['single_flag_positions'])
    assert sorted(singles) == high and len(singles) == len(record['single_flag_positions'])
    assert len(set(singles.values())) == len(high)
    assert all(0 < p < record['cached_flag_count'] for p in singles.values())
    pairs = {}
    for item in record['pair_flag_positions']:
        a, b = item['masks']
        assert a < b and a in singles and b in singles and (a, b) not in pairs
        allowed = [e for e in (0, 1) if direct_pair(rows, a, b, e)]
        assert allowed == [e for e in (0, 1)
                           if old.caps(old.attach(old.attach(rows, a), b | (e << 6)))]
        assert allowed == item['allowed_edges'] and len(allowed) == len(item['flag_positions'])
        assert all(0 < p < record['cached_flag_count'] for p in item['flag_positions'])
        pairs[a, b] = item['flag_positions']
    assert sorted(pairs) == list(combinations(high, 2))
    h = len(high)
    stream, dense_stream = hashlib.sha256(), hashlib.sha256()
    refs = 0
    degree_counts = {}
    for degree in range(5):
        expected = comb(h, degree)
        seen = bytearray(expected)
        visited = 0
        for indices in combinations(range(h), degree):
            masks = tuple(high[i] for i in indices)
            row_refs = old.monomial_rows(masks, singles, pairs)
            assert len(row_refs) <= 4
            assert all(0 <= r < record['cached_tensor_lower_rows'] for r in row_refs)
            stream.update(struct.pack('<qq', degree, len(row_refs)))
            stream.update(struct.pack('<'+'q'*degree, *masks))
            stream.update(struct.pack('<'+'q'*len(row_refs), *row_refs))
            rank = colex_rank(indices)
            assert 0 <= rank < expected and not seen[rank]
            seen[rank] = 1
            dense_stream.update(struct.pack('<qq', degree, rank)+bytes(masks))
            refs += len(row_refs)
            visited += 1
        assert visited == expected and all(seen)
        degree_counts[str(degree)] = expected
    assert degree_counts == record['squarefree_monomials_by_degree']
    assert stream.hexdigest() == record['monomial_product_row_reference_sha256']
    assert refs == record['monomial_product_row_references']
    count = comb(h, 5)
    subset_stream = hashlib.sha256(struct.pack('<qq', root, count))
    buffer = bytearray()
    visited, first, last = 0, None, None
    for subset in combinations(high, 5):
        if first is None:
            first = list(subset)
        last = list(subset)
        buffer.extend(subset)
        if len(buffer) >= 250000:
            subset_stream.update(buffer); buffer.clear()
        visited += 1
    subset_stream.update(buffer)
    assert visited == count
    return {'root_type': root, 'root_rows': list(rows), 'high_masks': high,
        'five_subsets': count, 'first_five_subset': first, 'last_five_subset': last,
        'complete_five_subset_stream_sha256': subset_stream.hexdigest(),
        'squarefree_monomials_by_degree': degree_counts,
        'colex_dense_index_stream_sha256': dense_stream.hexdigest(),
        'monomial_product_row_reference_sha256': stream.hexdigest(),
        'monomial_product_row_references': refs,
        'inherited_sparse_coefficient_reads': record['monomial_sparse_coefficient_reads'],
        'dense_moment_entries': sum(degree_counts.values()),
        'maximum_dense_array_entries': max(degree_counts.values()),
        'batch_count_at_50000': (count+BATCH_SIZE-1)//BATCH_SIZE,
        'zero_point_or_domain_pruning': False}


def preparation():
    assert old.digest(Path(old.__file__)) == DOMAIN_SOURCE_SHA
    assert old.digest(DOMAIN) == DOMAIN_SHA and old.digest(SCAN_SOURCE) == SCAN_SOURCE_SHA
    assert old.digest(old.INDEX) == old.INDEX_SHA
    assert old.digest(old.CATALOGUE) == old.CATALOGUE_SHA
    ledger, index = read(DOMAIN), read(old.INDEX)
    assert ledger['source_sha256'] == DOMAIN_SOURCE_SHA
    assert ledger['cache_index_sha256'] == old.INDEX_SHA
    assert ledger['catalogue_sha256'] == old.CATALOGUE_SHA
    assert ledger['family_source_sha256'] == old.FAMILY_SHA
    assert ledger['all_allowed_high_masks_retained'] and not ledger['point_or_zero_pruning']
    assert index['point_independent_tensors'] and not index['root_or_flag_zero_pruning']
    assert index['covers_full62_family'] and index['cached_root_count'] == 62
    assert ledger['cache_parts'] == index['cache_parts']
    catalogue = pickle.loads(old.CATALOGUE.read_bytes())
    records = [root_inventory(r, catalogue) for r in ledger['roots']]
    assert [r['root_type'] for r in records] == list(catalogue[1][6]) == list(range(38, 100))
    totals = {key: sum(r[key] for r in records) for key in
              ('five_subsets', 'dense_moment_entries', 'monomial_product_row_references',
               'inherited_sparse_coefficient_reads', 'batch_count_at_50000')}
    totals['high_masks'] = sum(len(r['high_masks']) for r in records)
    totals['roots_with_five_subsets'] = sum(r['five_subsets'] > 0 for r in records)
    totals['roots_without_five_subsets'] = sum(r['five_subsets'] == 0 for r in records)
    totals['maximum_high_masks'] = max(len(r['high_masks']) for r in records)
    totals['maximum_root_dense_moment_entries'] = max(r['dense_moment_entries'] for r in records)
    totals['maximum_root_five_subsets'] = max(r['five_subsets'] for r in records)
    totals['monomials_by_degree'] = {str(k): sum(r['squarefree_monomials_by_degree'][str(k)]
                                               for r in records) for k in range(5)}
    assert totals['five_subsets'] == 4543737 and totals['high_masks'] == 829
    assert totals['monomials_by_degree'] == ledger['summary']['monomials_by_degree']
    assert totals['monomial_product_row_references'] == 327655
    assert totals['inherited_sparse_coefficient_reads'] == 229779
    n = totals['five_subsets']
    workload = {'affine_atom_constants': 32*n, 'proper_moment_lookups': 31*n,
        'mobius_subtractions': 80*n, 'implicit_opposite_parity_atom_pairs': 256*n,
        'already_four_atom_pairs_hamming_1': 80*n,
        'new_pairs_hamming_3': 160*n, 'new_pairs_hamming_5': 16*n,
        'new_pairs_hamming_3_or_5': 176*n,
        'cached_product_rows_available': ledger['summary']['cached_tensor_lower_rows'],
        'sparse_product_coefficient_reads_for_selected_monomials': 229779,
        'sparse_product_read_count_source': 'inherited frozen four-Boolean tensor ledger; tensors not reloaded',
        'batch_size': BATCH_SIZE, 'batch_proper_moments_int64_bytes': BATCH_SIZE*32*8,
        'batch_affine_constants_int64_bytes': BATCH_SIZE*32*8,
        'batch_input_indices_int64_bytes': BATCH_SIZE*5*8,
        'maximum_root_dense_moment_int64_bytes': totals['maximum_root_dense_moment_entries']*8,
        'numpy_temporary_and_python_tuple_memory_not_included_in_array_bounds': True,
        'full_cache_loading_memory_not_included_in_array_bounds': True,
        'no_array_of_all_implicit_pair_constraints_is_needed': True}
    arithmetic = {'integer_type_for_saved_forms': 'unbounded Python integers',
        'integer_type_for_array_batch': 'signed int64 after exact bounds',
        'tensor_contraction_requirement': 'same positive-data, used-column, coefficient-row-sum guards as frozen four-Boolean scan',
        'maximum_product_entry_symbol': 'A', 'maximum_proper_moment_symbol': 'M',
        'proper_moment_bound': 'M <= 4*A',
        'maximum_transform_intermediate_absolute_value': '32*M <= 128*A',
        'maximum_interval_gap_absolute_value': '64*M <= 256*A',
        'maximum_atom_row_sum_partial_absolute_value': '1024*M <= 4096*A',
        'required_batch_guard': '1024*M <= 2^63-1, checked as Python integers before subtraction',
        'failed_bound_behavior': 'stop with incomplete status; never use approximate arithmetic',
        'zero_root_policy': 'do not skip; every five-subset interval is still checked',
        'colex_rank_bound': '0 <= rank < C(h,k), h <= 42, k <= 4',
        'integer_interval_endpoints_imply_integer_fifth_moment': True}
    return {'status': 'complete five-Boolean extension domain and synthetic controls prepared',
        'source_sha256': old.digest(Path(__file__)), 'domain_source_sha256': DOMAIN_SOURCE_SHA,
        'domain_certificate_sha256': DOMAIN_SHA, 'contraction_reference_source_sha256': SCAN_SOURCE_SHA,
        'catalogue_sha256': old.CATALOGUE_SHA, 'cache_index_sha256': old.INDEX_SHA,
        'family_source_sha256': old.FAMILY_SHA, 'cache_parts': ledger['cache_parts'],
        'root_count': 62, 'roots': records, 'summary': totals, 'workload': workload,
        'arithmetic': arithmetic, 'controls': controls(),
        'odd_present_cardinality_is_lower_bound': True,
        'even_present_cardinality_is_upper_bound': True,
        'full_degree_five_coefficient_cancelled_before_cache_conversion': True,
        'all_allowed_high_masks_retained': True, 'root_or_flag_pruning': False,
        'all_five_subsets_explicitly_enumerated': True,
        'no_joint_distribution_across_different_five_subsets_claimed': True,
        'count_point_loaded': False, 'product_tensors_loaded': False,
        'new_product_tensors_generated': False, 'reduced_matrix_loaded': False,
        'optimizer_or_eigensystem_called': False, 'point_scan_performed': False,
        'future_negative_form_requires_fresh_literal_product_replay': True,
        'graph_existence_resolved': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 60
    started = time.monotonic()
    def deadline(_signum, _frame):
        raise TimeoutError('bounded five-Boolean extension domain preparation')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    try:
        result = preparation()
        if args.replay:
            assert read(args.replay) == result
            result = {'status': 'cold complete five-Boolean extension domain replay PASS',
                'source_sha256': old.digest(Path(__file__)), 'certificate_sha256': old.digest(args.replay),
                'summary': result['summary'], 'workload': result['workload'],
                'count_point_loaded': False, 'product_tensors_loaded': False,
                'point_scan_performed': False}
        raw = json.dumps(result, indent=2).encode()+b'\n'
        args.output.write_bytes(gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw)
        print(json.dumps({k: v for k, v in result.items() if k not in ('roots', 'controls')}, indent=2), flush=True)
        print('output_sha256', old.digest(args.output), flush=True)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        print('elapsed_seconds', time.monotonic()-started,
              'peak_rss_kib', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, flush=True)


if __name__ == '__main__':
    main()
