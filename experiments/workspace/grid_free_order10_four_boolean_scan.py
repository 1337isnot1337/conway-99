"""Exact four-variable Boolean-atom screen using frozen cached products.

Every tested atom is a product of present high-mask indicators and absent
high-mask indicators. Nonnegative integer counts do not by themselves
guarantee these inclusion-exclusion expressions are nonnegative.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from math import gcd
from pathlib import Path
import pickle
import resource
import signal
import time

import numpy as np

import grid_free_order10_four_boolean_domains as domains


ROOT = domains.ROOT
LOGS = ROOT/'experiments/logs/moments-and-counts'
DOMAIN = LOGS/'order10-four-boolean-domains.json.gz'
DOMAIN_SHA = '5fd508dba5bcda5aeb8231ab39dd6b68df5c55ffffebb98b7344e874155bef35'
POINT = LOGS/'prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json'
POINT_SHA = '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'
INT64_MAX = (1 << 63)-1


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def inputs():
    assert domains.digest(DOMAIN) == DOMAIN_SHA
    ledger = read(DOMAIN)
    assert ledger['source_sha256'] == domains.digest(Path(domains.__file__))
    assert ledger['cache_index_sha256'] == domains.INDEX_SHA
    assert ledger['all_allowed_high_masks_retained'] and not ledger['point_or_zero_pruning']
    assert ledger['root_count'] == 62
    assert domains.digest(POINT) == POINT_SHA
    point = read(POINT)
    counts = point['induced_counts']
    assert len(counts) == 48965 and all(type(value) is int and value >= 0 for value in counts)
    assert point['x521_zero'] and len(point['required_zero_coordinates']) == 59
    assert all(point['rounded_core_values'][i] == 0 for i in point['required_zero_coordinates'])
    assert domains.digest(domains.CATALOGUE) == domains.CATALOGUE_SHA
    catalogue = pickle.loads(domains.CATALOGUE.read_bytes())
    assert len(catalogue[0]) == len(counts)
    return ledger, counts, catalogue


def metadata(ledger):
    return {'source_sha256': domains.digest(Path(__file__)),
        'domain_source_sha256': domains.digest(Path(domains.__file__)),
        'domain_certificate_sha256': DOMAIN_SHA, 'integer_count_point_sha256': POINT_SHA,
        'catalogue_sha256': domains.CATALOGUE_SHA, 'cache_parts': ledger['cache_parts'],
        'root_count': 62, 'summary': ledger['summary'],
        'arithmetic': 'int64 only after Python-integer bounds prove every contraction and transform safe',
        'fallback_on_failed_integer_bound': 'stop with error; no approximate arithmetic',
        'marginals': 'all four-subsets, or the complete smaller high-mask set when its size is below four',
        'maximum_seconds': 60, 'maximum_saved_negative_atoms_per_root': 4,
        'negative_cut_requires_independent_literal_replay': True,
        'optimizer_or_eigensystem_called': False, 'new_product_tensors_generated': False}


def cached_values(tensor, embeddings):
    assert tensor.dtype == np.dtype('int64')
    assert not tensor.data.size or np.all(tensor.data > 0)
    coefficient_total_bound = int(tensor.nnz)*int(tensor.data.max(initial=0))
    assert coefficient_total_bound <= INT64_MAX
    maximum_row_sum = int(np.asarray(tensor.sum(axis=1)).max(initial=0))
    used_columns = np.unique(tensor.indices)
    maximum_embedding = max((embeddings[int(i)] for i in used_columns), default=0)
    bound = maximum_embedding*maximum_row_sum
    assert bound <= INT64_MAX and maximum_embedding <= INT64_MAX
    # Zero-filled unused tensor columns change no product or flag. This
    # also avoids an unnecessary int64 conversion of unrelated counts.
    contracted = np.zeros(tensor.shape[1], dtype=np.int64)
    contracted[used_columns] = [embeddings[int(i)] for i in used_columns]
    values = np.asarray(tensor @ contracted).reshape(-1)
    assert np.all(values >= 0)
    actual = int(values.max(initial=0))
    # A monomial sums at most four product entries. An atom uses at most
    # sixteen monomials. This stronger bound also protects atom row sums.
    assert 1024*actual <= INT64_MAX
    return values, {'maximum_coefficient_row_sum': maximum_row_sum,
                    'maximum_labelled_embedding': maximum_embedding,
                    'safe_contraction_bound': bound,
                    'maximum_cached_product_value': actual,
                    'safe_transform_and_row_sum_bound': 1024*actual}


def atom_form(masks, pattern, singles, pairs, tensor, automorphisms, counts, expected):
    required = tuple(mask for i, mask in enumerate(masks) if pattern >> i & 1)
    absent = tuple(mask for i, mask in enumerate(masks) if not (pattern >> i & 1))
    labelled = Counter()
    monomials = []
    for size in range(len(absent)+1):
        sign = (-1)**size
        for extra in combinations(absent, size):
            subset = tuple(sorted(required+extra))
            references = domains.monomial_rows(subset, singles, pairs)
            monomials.append({'masks': list(subset), 'sign': sign, 'cached_product_rows': references})
            for row in references:
                for k in range(tensor.indptr[row], tensor.indptr[row+1]):
                    labelled[int(tensor.indices[k])] += sign*int(tensor.data[k])
    labelled = {i: value for i, value in sorted(labelled.items()) if value}
    induced = {i: value*automorphisms[i] for i, value in labelled.items()}
    value = sum(coefficient*counts[i] for i, coefficient in induced.items())
    assert value == expected < 0
    divisor = gcd(*(abs(coefficient) for coefficient in induced.values()))
    assert divisor > 0 and value % divisor == 0
    primitive = [[i, coefficient//divisor] for i, coefficient in induced.items()]
    return {'selected_high_masks': list(masks), 'present_pattern': pattern,
        'required_present_masks': list(required), 'required_absent_masks': list(absent),
        'signed_squarefree_monomials': monomials,
        'labelled_induced_embedding_form': [[i, coefficient] for i, coefficient in labelled.items()],
        'primitive_induced_count_form': primitive, 'coefficient_gcd': divisor,
        'exact_labelled_value': value, 'primitive_value_at_integer_witness': value//divisor,
        'independent_literal_replay_complete': False, 'optimizer_eligible': False}


def root_scan(record, flags, tensor, embeddings, automorphisms, counts):
    high = record['high_masks']
    singles = dict(record['single_flag_positions'])
    pairs = {tuple(item['masks']): item['flag_positions'] for item in record['pair_flag_positions']}
    assert len(flags) == record['cached_flag_count']
    assert [flag['masks'][0] for flag in flags if flag['size'] == 1] == high
    values, bounds = cached_values(tensor, embeddings)
    moments = {}
    stream = hashlib.sha256()
    import struct
    for size in range(5):
        for subset in combinations(high, size):
            references = domains.monomial_rows(subset, singles, pairs)
            stream.update(struct.pack('<qq', size, len(references)))
            stream.update(struct.pack('<'+'q'*size, *subset))
            stream.update(struct.pack('<'+'q'*len(references), *references))
            moments[subset] = sum(int(values[row]) for row in references)
    assert stream.hexdigest() == record['monomial_product_row_reference_sha256']
    n = record['tested_marginal_order']
    marginals = list(combinations(high, n))
    assert len(marginals) == record['tested_marginals']
    atoms = np.empty((len(marginals), 1 << n), dtype=np.int64)
    for pattern in range(1 << n):
        positions = [i for i in range(n) if pattern >> i & 1]
        atoms[:, pattern] = [moments[tuple(masks[i] for i in positions)] for masks in marginals]
    for bit in range(n):
        for pattern in range(1 << n):
            if not (pattern >> bit & 1):
                atoms[:, pattern] -= atoms[:, pattern | (1 << bit)]
    assert np.all(atoms.sum(axis=1) == moments[()])
    negative_count = int(np.count_nonzero(atoms < 0))
    sampled = []
    if negative_count:
        first = [int(i) for i in np.flatnonzero(atoms < 0)[:3]]
        candidates = sorted(set(first+[int(atoms.argmin())]))
        for flat in candidates:
            marginal, pattern = divmod(flat, 1 << n)
            cut = atom_form(marginals[marginal], pattern, singles, pairs, tensor,
                            automorphisms, counts, int(atoms[marginal, pattern]))
            sampled.append({'root_type': record['root_type'], **cut})
    return {'root_type': record['root_type'], 'high_masks': len(high),
        'marginal_order': n, 'marginals_tested': len(marginals),
        'atoms_tested': int(atoms.size), 'negative_atoms': negative_count,
        'zero_atoms': int(np.count_nonzero(atoms == 0)),
        'minimum_atom': int(atoms.min()), 'maximum_atom': int(atoms.max()),
        'negative_atoms_by_present_cardinality': {str(k): sum(int(np.count_nonzero(atoms[:, p] < 0))
            for p in range(1 << n) if p.bit_count() == k) for k in range(n+1)},
        'arithmetic_bounds': bounds, 'all_atom_sums_equal_root_embedding_count': True}, sampled


def run(prepared, output, seconds):
    started = time.monotonic()
    ledger, counts, catalogue = inputs()
    assert prepared == metadata(ledger)
    by_root = {record['root_type']: record for record in ledger['roots']}
    automorphisms = [int(value) for value in catalogue[2]]
    embeddings = [a*c for a, c in zip(automorphisms, counts)]
    result = {'status': 'initializing exact Boolean marginal scan',
        'source_sha256': domains.digest(Path(__file__)), 'preparation': prepared,
        'root_records': [], 'negative_atom_certificates': [],
        'requested_seconds': seconds, 'optimizer_or_eigensystem_called': False,
        'complete_atom_scan': False, 'graph_existence_resolved': False}
    current, error, timed_out = None, None, False
    def deadline(_signum, _frame):
        raise TimeoutError('bounded exact Boolean marginal scan')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    scan_started = time.monotonic()
    try:
        for _, blocks in domains.cache_parts():
            for root, flags, tensor in blocks:
                current = int(root)
                record, negatives = root_scan(by_root[current], flags, tensor, embeddings, automorphisms, counts)
                blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
                try:
                    result['root_records'].append(record)
                    result['negative_atom_certificates'].extend(negatives)
                    current = None
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
    except TimeoutError:
        timed_out = True
    except Exception as problem:
        error = repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    result['root_records'].sort(key=lambda record: record['root_type'])
    total = {key: sum(record[key] for record in result['root_records']) for key in
             ('marginals_tested', 'atoms_tested', 'negative_atoms', 'zero_atoms')}
    complete = [record['root_type'] for record in result['root_records']] == list(range(38, 100)) and not error and not timed_out
    if complete:
        assert total['marginals_tested'] == ledger['summary']['tested_marginals']
        assert total['atoms_tested'] == ledger['summary']['tested_atom_inequalities']
    result.update(status='complete exact at-most-four Boolean atom scan' if complete else 'UNKNOWN: incomplete Boolean atom scan',
        complete_atom_scan=bool(complete), summary=total, timed_out=timed_out, error=error,
        unfinished_root=current, scan_seconds=time.monotonic()-scan_started,
        total_seconds=time.monotonic()-started, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in
                     ('preparation', 'root_records', 'negative_atom_certificates')}, indent=2), flush=True)
    print('output_sha256', domains.digest(output), flush=True)
    return int(error is not None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    assert 0 < args.seconds <= 60
    if args.prepare:
        assert not args.preparation.exists()
        ledger, _, _ = inputs()
        prepared = metadata(ledger)
        args.preparation.write_text(json.dumps(prepared, indent=2)+'\n')
        print(json.dumps(prepared, indent=2))
    else:
        assert args.output and not args.output.exists()
        raise SystemExit(run(read(args.preparation), args.output, args.seconds))
