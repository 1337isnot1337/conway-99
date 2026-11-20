"""Complete at-most-four high-mask Boolean marginals from frozen r6s2 rows.

Only point-independent domains and cached product-row references are built.
No count point, eigensystem, optimizer or new product tensor is used here.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, product
import json
from math import comb
from pathlib import Path
import pickle
import resource
import signal
import struct
import time


ROOT = Path(__file__).resolve().parents[2]
INDEX = ROOT/'experiments/logs/moments-and-counts/order10-r6s2-full-cache.json'
INDEX_SHA = '8f8d0b3e2e509fb617962f744e6df7ca56d401bc67a2916f16ab124dafb486d0'
CATALOGUE = Path('/tmp/conway99-order10-catalogue.pickle')
CATALOGUE_SHA = '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'
FAMILY_SHA = '3772c728ec764dbec0142865696bb747c06e47b29495964af867103618b75a6d'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def attach(rows, mask):
    n = len(rows)
    return tuple(row | (((mask >> i)&1) << n) for i, row in enumerate(rows))+(mask,)


def caps(rows):
    return all((rows[a]&rows[b]).bit_count()+((rows[a] >> b)&1) <= 2
               for a in range(len(rows)) for b in range(a))


def lower(i, j):
    i, j = max(i, j), min(i, j)
    return i*(i+1)//2+j


def cache_parts():
    assert digest(INDEX) == INDEX_SHA
    index = json.loads(INDEX.read_text())
    assert index['point_independent_tensors'] and not index['root_or_flag_zero_pruning']
    assert index['covers_full62_family'] and index['cached_root_count'] == 62
    assert index['family_source_sha256'] == FAMILY_SHA
    seen = set()
    for item in index['cache_parts']:
        path = ROOT/item['path']
        assert digest(path) == item['sha256']
        saved = pickle.loads(gzip.decompress(path.read_bytes()))
        assert saved['point_independent_tensors'] and not saved['root_or_flag_zero_pruning']
        assert saved['family_source_sha256'] == FAMILY_SHA
        assert saved['catalogue_sha256'] == CATALOGUE_SHA
        roots = [int(root) for root, _, _ in saved['blocks']]
        assert sorted(roots) == sorted(item['root_types']) and not seen.intersection(roots)
        seen.update(roots)
        yield item, saved['blocks']
    assert sorted(seen) == index['all_cached_root_types'] == list(range(38, 100))


def monomial_rows(subset, singles, pairs):
    """Rows for a squarefree monomial; all masks are distinct and high."""
    if not subset:
        return [0]
    if len(subset) == 1:
        return [lower(singles[subset[0]], 0)]
    left = pairs[tuple(subset[:2])]
    if len(subset) == 2:
        return [lower(i, 0) for i in left]
    if len(subset) == 3:
        return [lower(i, singles[subset[2]]) for i in left]
    assert len(subset) == 4
    return [lower(i, j) for i in left for j in pairs[tuple(subset[2:])]]


def root_domain(root, flags, tensor, catalogue):
    rows = tuple(catalogue[0][root])
    assert len(rows) == 6 and flags[0]['size'] == 0 and tuple(flags[0]['rows']) == rows
    high = [mask for mask in range(64) if mask.bit_count() >= 3 and caps(attach(rows, mask))]
    singles = {int(flag['masks'][0]): i for i, flag in enumerate(flags) if flag['size'] == 1}
    assert sorted(singles) == high and len(singles) == sum(flag['size'] == 1 for flag in flags)
    pair_flags = {}
    for i, flag in enumerate(flags):
        assert flag['size'] in (0, 1, 2)
        if flag['size'] == 2:
            a, b = flag['masks']
            assert a < b and min(a.bit_count(), b.bit_count())+flag['edge'] >= 3
            assert tuple(flag['rows']) == attach(attach(rows, a), b | (flag['edge'] << 6))
            assert caps(flag['rows'])
            key = (a, b, flag['edge'])
            assert key not in pair_flags
            pair_flags[key] = i
    pairs, pair_records = {}, []
    for a, b in combinations(high, 2):
        allowed = [edge for edge in (0, 1) if caps(attach(attach(rows, a), b | (edge << 6)))]
        assert allowed == [edge for edge in (0, 1) if (a, b, edge) in pair_flags]
        pairs[a, b] = [pair_flags[a, b, edge] for edge in allowed]
        pair_records.append({'masks': [a, b], 'allowed_edges': allowed, 'flag_positions': pairs[a, b]})
    assert tensor.shape == (len(flags)*(len(flags)+1)//2, 48965)
    stream = hashlib.sha256()
    counts, refs, term_reads = {}, 0, 0
    for size in range(5):
        counts[str(size)] = comb(len(high), size) if len(high) >= size else 0
        visited = 0
        for subset in combinations(high, size):
            references = monomial_rows(subset, singles, pairs)
            assert all(0 <= row < tensor.shape[0] for row in references)
            stream.update(struct.pack('<qq', size, len(references)))
            stream.update(struct.pack('<'+'q'*size, *subset))
            stream.update(struct.pack('<'+'q'*len(references), *references))
            refs += len(references)
            term_reads += sum(int(tensor.indptr[row+1])-int(tensor.indptr[row]) for row in references)
            visited += 1
        assert visited == counts[str(size)]
    size = min(4, len(high))
    groups = comb(len(high), size)
    return {'root_type': root, 'root_rows': list(rows), 'cached_flag_count': len(flags),
        'cached_tensor_lower_rows': tensor.shape[0], 'high_masks': high,
        'single_flag_positions': [[mask, singles[mask]] for mask in high],
        'pair_flag_positions': pair_records, 'squarefree_monomials_by_degree': counts,
        'monomial_product_row_reference_sha256': stream.hexdigest(),
        'monomial_product_row_references': refs, 'monomial_sparse_coefficient_reads': term_reads,
        'tested_marginal_order': size, 'tested_marginals': groups,
        'tested_atom_inequalities': groups*(1 << size),
        'all_lower_order_marginals_are_sums_of_tested_atoms': True,
        'nonbinary_two_free_flags_preserved_in_cache': True}


def controls():
    assignment_count = 0
    for n in range(5):
        for bits in product((0, 1), repeat=n):
            moments = [int(all(bits[i] for i in range(n) if subset >> i & 1)) for subset in range(1 << n)]
            atoms = list(moments)
            for bit in range(n):
                for subset in range(1 << n):
                    if not (subset >> bit & 1):
                        atoms[subset] -= atoms[subset | (1 << bit)]
            state = sum(value << i for i, value in enumerate(bits))
            assert atoms == [int(i == state) for i in range(1 << n)]
            assert sum(atoms) == moments[0]
            assignment_count += 1
    literal_cases = []
    root = (0,)*6
    for masks, edge_word in (([], 0), ([7], 0), ([7, 56], 0), ([7, 56], 1),
                             ([7, 25, 42, 52], 0)):
        rows = root
        at = 0
        for i, mask in enumerate(masks):
            joined = mask
            for j in range(i):
                joined |= ((edge_word >> at)&1) << (6+j)
                at += 1
            rows = attach(rows, joined)
        assert caps(rows)
        actual = Counter(row & 63 for row in rows[6:])
        assert all(actual[mask] <= 1 for mask in range(64) if mask.bit_count() >= 3)
        for a, b in combinations(range(7, 64), 2):
            if min(a.bit_count(), b.bit_count()) < 3:
                continue
            edge_counts = [0, 0]
            for u in range(6, len(rows)):
                for v in range(6, len(rows)):
                    if u != v and rows[u] & 63 == a and rows[v] & 63 == b:
                        edge_counts[(rows[u] >> v)&1] += 1
            assert sum(edge_counts) == actual[a]*actual[b]
        literal_cases.append({'host_rows': list(rows), 'selected_high_masks': masks,
                              'sum_of_edge_and_nonedge_pair_flags_equals_class_product': True})
    return {'boolean_assignments_checked': assignment_count, 'literal_hosts': literal_cases,
            'normalization': 'labelled root embeddings; distinct mask classes fix free labels'}


def prepare():
    assert digest(CATALOGUE) == CATALOGUE_SHA
    catalogue = pickle.loads(CATALOGUE.read_bytes())
    records, bindings = [], []
    for item, blocks in cache_parts():
        bindings.append(item)
        for root, flags, tensor in blocks:
            records.append(root_domain(int(root), flags, tensor, catalogue))
    records.sort(key=lambda record: record['root_type'])
    assert [record['root_type'] for record in records] == list(catalogue[1][6])
    totals = {key: sum(record[key] for record in records) for key in
              ('cached_flag_count', 'cached_tensor_lower_rows', 'tested_marginals',
               'tested_atom_inequalities', 'monomial_product_row_references', 'monomial_sparse_coefficient_reads')}
    totals['high_masks'] = sum(len(record['high_masks']) for record in records)
    totals['monomials_by_degree'] = {str(k): sum(record['squarefree_monomials_by_degree'][str(k)] for record in records) for k in range(5)}
    assert totals['high_masks'] == 829 and totals['monomials_by_degree']['4'] == 679045
    assert totals['cached_flag_count'] == 14348 and totals['cached_tensor_lower_rows'] == 3913479
    return {'status': 'complete point-independent at-most-four Boolean marginal coverage',
        'source_sha256': digest(Path(__file__)), 'cache_index_sha256': INDEX_SHA,
        'catalogue_sha256': CATALOGUE_SHA, 'family_source_sha256': FAMILY_SHA,
        'cache_parts': bindings, 'roots': records, 'summary': totals, 'controls': controls(),
        'root_count': 62, 'all_allowed_high_masks_retained': True,
        'point_or_zero_pruning': False, 'count_point_loaded': False,
        'new_product_tensors_generated': False, 'optimizer_or_eigensystem_called': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 60
    started = time.monotonic()
    def deadline(_signum, _frame):
        raise TimeoutError('bounded four-Boolean domain preparation')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    try:
        result = prepare()
        if args.replay:
            old = json.loads(gzip.decompress(args.replay.read_bytes()))
            assert old == result
            result = {'status': 'cold complete four-Boolean domain replay PASS',
                      'source_sha256': digest(Path(__file__)),
                      'certificate_sha256': digest(args.replay), 'summary': result['summary']}
        raw = json.dumps(result, indent=2).encode()+b'\n'
        args.output.write_bytes(gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw)
        print(json.dumps({k: v for k, v in result.items() if k not in ('roots', 'controls')}, indent=2), flush=True)
        print('output_sha256', digest(args.output), flush=True)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        print('elapsed_seconds', time.monotonic()-started, 'peak_rss_kib', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss, flush=True)


if __name__ == '__main__':
    main()
