"""Bounded four-root product, normalization and resource controls.

All masks and all four projector blocks are constructed for each selected
root. Pointwise kernels are verified before pivot deletion. Numerical
eigenvectors propose directions; accepted directions and induced-count
forms use Python integers, with a separate literal-entry reconstruction.
This driver cannot run the complete 916-root family.
"""

import argparse
from collections import Counter
from functools import reduce
import gzip
from itertools import combinations, permutations
import json
from math import gcd
from pathlib import Path
import pickle
import random
import resource
import signal
import time

import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits

import grid_free_order10_projector_domains as domains
import grid_free_order10_projector_literal as literal
import grid_free_order10_r8s1 as forms
from grid_free_order10_r8s1_scan import FullScanner
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ROOT/'experiments/logs/moments-and-counts/order10-eight-root-projector-domains.json'
DOMAIN_SHA = 'b1a35b1d8dbabf870331fc591e6d332ed503a447b2cdc81f83c6b5d5c8bcbf1f'
DOMAIN_SOURCE_SHA = '3c5973dd74b3daadff09dc7ec967a7ab156afe06b6140d5520d0093dabc455c0'
WITNESS = ROOT/'experiments/logs/moments-and-counts/prism-zero-order10-all-flags-x521-face-loop01-round0-rounded-counts.json'
WITNESS_SHA = '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'
CONTROL_ROOTS = (1223, 1200, 308, 610)


def inputs():
    assert files.digest(DOMAIN) == DOMAIN_SHA
    assert files.digest(Path(domains.__file__)) == DOMAIN_SOURCE_SHA
    assert files.digest(WITNESS) == WITNESS_SHA
    certificate = json.loads(DOMAIN.read_text())
    witness = json.loads(WITNESS.read_text())
    assert witness['x521_zero'] and len(witness['required_zero_coordinates']) == 59
    counts = witness['induced_counts']
    assert len(counts) == 48965 and all(type(x) is int and x >= 0 for x in counts)
    records = {item['root_type']: item for item in certificate['roots']}
    return records, counts


def metadata(records, counts):
    sizes = [records[root]['classes'] for root in CONTROL_ROOTS]
    return {
        'source_sha256': files.digest(Path(__file__)),
        'literal_oracle_source_sha256': files.digest(Path(literal.__file__)),
        'domain_source_sha256': DOMAIN_SOURCE_SHA, 'domain_certificate_sha256': DOMAIN_SHA,
        'transport_and_form_source_sha256': files.digest(Path(forms.__file__)),
        'negative_direction_source_sha256': files.digest(Path(__file__).with_name('grid_free_order10_r8s1_scan.py')),
        'catalogue_sha256': domains.CATALOGUE_SHA, 'witness_sha256': WITNESS_SHA,
        'selected_roots': [{'root_type': root, 'classes': records[root]['classes'],
                            'unlabelled_root_count_at_target': counts[root]}
                           for root in CONTROL_ROOTS],
        'blocks': 4*len(CONTROL_ROOTS),
        'lower_entries': sum(m*(m+1)+(m+8)*(m+9) for m in sizes),
        'spectral_coefficient_placements_upper_bound': sum(2*(36+9*m+m*(m+1)) for m in sizes),
        'schur_coefficient_placements_upper_bound': sum(2*(m+m*(m+1)) for m in sizes),
        'maximum_seconds': 60, 'complete_root_family': False,
        'all_selected_root_domains_retained': True, 'point_dependent_cache_pruning': False,
        'dense_reduction_loaded': False, 'optimizer_called': False,
    }


class Builder:
    def __init__(self, data):
        self.data = data
        self.transport = forms.Builder(data)

    def products(self, record):
        root, masks = record['root_type'], record['masks']
        rows = self.data[0][root]
        one = self.transport.child_map(root)
        assert sorted(one) == masks
        pairs = []
        for i, mask in enumerate(masks):
            child = one[mask]
            mapping = self.transport.transport(forms.attach(rows, mask), child)
            next_children = self.transport.child_map(child)
            edge_bit = 1 << mapping[8]
            for j, other in enumerate(masks[:i+1]):
                translated = forms.transported_mask(other, mapping)
                absent = next_children.get(translated, -1)
                present = next_children.get(translated | edge_bit, -1)
                if i == j and mask.bit_count() >= 3:
                    assert absent == present == -1
                pairs.append((i, j, child if i == j else -1, absent, present))
        return one, pairs

    def blocks(self, record):
        root, masks = record['root_type'], record['masks']
        rows = self.data[0][root]
        one, pairs = self.products(record)
        blocks = []
        for projection in record['projectors']:
            sign = projection['projector']
            diagonal, edge, constant = projection['parameters']
            numerator = projection['inverse_numerator']
            denominator, divisor = projection['inverse_denominator'], projection['schur_common_divisor']
            crosses = [[constant+edge*((mask >> k) & 1) for k in range(8)] for mask in masks]
            first = [[sum(c[k]*numerator[k][j] for k in range(8)) for j in range(8)] for c in crosses]
            for family in ('spectral', 'schur'):
                offset = 8 if family == 'spectral' else 0
                order = offset+len(masks)
                triplets = []

                def append(i, j, terms):
                    accumulated = Counter()
                    for index, coefficient in terms:
                        if index >= 0:
                            accumulated[index] += int(coefficient)
                    for index, coefficient in accumulated.items():
                        if coefficient:
                            assert abs(coefficient) < 1 << 63
                            triplets.append((i*(i+1)//2+j, index, coefficient))

                if offset:
                    for i in range(8):
                        for j in range(i+1):
                            append(i, j, [(root, diagonal*(i == j)+edge*((rows[i] >> j) & 1)+constant)])
                    for i, mask in enumerate(masks, 8):
                        for j in range(8):
                            append(i, j, [(one[mask], constant+edge*((mask >> j) & 1))])
                for i, j, coincident, absent, present in pairs:
                    multiplier, subtraction = 1, 0
                    if family == 'schur':
                        product = sum(first[i][k]*crosses[j][k] for k in range(8))
                        assert product % divisor == 0 and denominator % divisor == 0
                        multiplier, subtraction = denominator//divisor, product//divisor
                    append(offset+i, offset+j, [
                        (coincident, multiplier*(diagonal+constant)-subtraction),
                        (absent, multiplier*constant-subtraction),
                        (present, multiplier*(constant+edge)-subtraction)])
                indices, types, coefficients = zip(*triplets) if triplets else ([], [], [])
                tensor = sparse.csr_matrix((np.asarray(coefficients, dtype=np.int64), (indices, types)),
                    shape=(order*(order+1)//2, len(self.data[0])), dtype=np.int64)
                assert tensor.nnz == len(triplets)
                blocks.append({'root_type': root, 'masks': masks, 'family': family,
                               'projector': sign, 'order': order, 'tensor': tensor})
        return blocks


def tensor_entry(tensor, i, j):
    row = i*(i+1)//2+j
    return {int(tensor.indices[k]): int(tensor.data[k])
            for k in range(tensor.indptr[row], tensor.indptr[row+1])}


def cold_control(block, record, oracle):
    n = block['order']
    if n <= 30:
        selected = {(i, j) for i in range(n) for j in range(i+1)}
    else:
        rng = random.Random(100000*block['root_type']+100*(block['family'] == 'schur')
                            +(block['projector'] == 'plus'))
        selected = {(i, i) for i in range(n)}
        selected.update((max(i, j), min(i, j))
                        for i, j in ((rng.randrange(n), rng.randrange(n)) for _ in range(256)))
        if block['family'] == 'spectral':
            selected.update((i, j) for i in range(8) for j in range(i+1))
    for i, j in sorted(selected):
        direct = oracle.entry(record, block['family'], block['projector'], i, j)
        assert tensor_entry(block['tensor'], i, j) == direct
    return len(selected)


def kernel(block, record):
    offset = 8 if block['family'] == 'spectral' else 0
    K = np.zeros((block['order'], 9), dtype=object)
    if offset:
        shift = 4 if block['projector'] == 'minus' else -3
        for i, row in enumerate(record['root_rows']):
            K[i, 0] = 1
            for j in range(8):
                K[i, j+1] = ((row >> j) & 1)+shift*(i == j)
    for i, mask in enumerate(record['masks'], offset):
        K[i, 0] = 1
        for j in range(8):
            K[i, j+1] = (mask >> j) & 1
    pivots = [offset+record['masks'].index(mask) for mask in [0]+[1 << i for i in range(8)]]
    assert domains.determinant(K[pivots].tolist()) == 1
    return K, pivots


def fresh_cut(block, record, vector, oracle, automorphisms, counts):
    terms, entries = Counter(), 0
    for i, a in enumerate(vector):
        if not a:
            continue
        for j, b in enumerate(vector[:i+1]):
            if not b:
                continue
            weight = a*b*(1 if i == j else 2)
            direct = oracle.entry(record, block['family'], block['projector'], i, j)
            assert direct == tensor_entry(block['tensor'], i, j)
            for index, coefficient in direct.items():
                terms[index] += weight*coefficient*automorphisms[index]
            entries += 1
    terms = [[index, value] for index, value in sorted(terms.items()) if value]
    divisor = reduce(gcd, (abs(value) for _, value in terms), 0)
    assert divisor > 0
    terms = [[index, value//divisor] for index, value in terms]
    value = sum(coefficient*counts[index] for index, coefficient in terms)
    assert value < 0
    return terms, divisor, value, entries


def rook_control(builder, record, blocks, oracle):
    host = tuple(sum(1 << j for j in range(9) if i != j and
                     (i//3 == j//3 or i % 3 == j % 3)) for i in range(9))
    root_rows = tuple(record['root_rows'])
    assert oracle.ids[literal.canonical(forms.induced_rows(host, tuple(range(8))))] == record['root_type']
    counts = [0]*48965
    for subset in combinations(range(9), 8):
        counts[oracle.ids[literal.canonical(forms.induced_rows(host, subset))]] += 1
    counts[oracle.ids[literal.canonical(host)]] = 1
    embeddings = [int(a)*c for a, c in zip(builder.data[2], counts)]
    autos = [order for order in permutations(range(8)) if forms.induced_rows(root_rows, order) == root_rows]
    assert len(autos) == builder.data[2][record['root_type']] == 8
    root_images = set()
    for subset in combinations(range(9), 8):
        mapping = builder.transport.transport(forms.induced_rows(host, subset), record['root_type'])
        inverse = [mapping.index(i) for i in range(8)]
        for automorphism in autos:
            image = tuple(subset[inverse[automorphism[i]]] for i in range(8))
            assert forms.induced_rows(host, image) == root_rows
            root_images.add(image)
    assert len(root_images) == 72
    results = []
    for block in blocks:
        direct = np.zeros((block['order'], block['order']), dtype=object)
        projection = next(p for p in record['projectors'] if p['projector'] == block['projector'])
        diagonal, edge, constant = projection['parameters']
        for image in root_images:
            outside = next(v for v in range(9) if v not in image)
            mask = sum(((host[outside] >> image[i]) & 1) << i for i in range(8))
            position = record['masks'].index(mask)
            if block['family'] == 'spectral':
                labels = list(image)+[outside]
                locations = list(range(8))+[8+position]
                for a, i in enumerate(locations):
                    for b, j in enumerate(locations):
                        direct[i, j] += diagonal*(labels[a] == labels[b])+edge*((host[labels[a]] >> labels[b]) & 1)+constant
            else:
                cross = [constant+edge*((host[outside] >> image[i]) & 1) for i in range(8)]
                numerator = projection['inverse_numerator']
                h, divisor = projection['inverse_denominator'], projection['schur_common_divisor']
                product = sum(cross[i]*numerator[i][j]*cross[j] for i in range(8) for j in range(8))
                assert product % divisor == 0
                direct[position, position] += (h//divisor)*(diagonal+constant)-product//divisor
        actual = FullScanner.matrix(block['tensor'], block['order'], embeddings)
        assert np.array_equal(actual, direct)
        results.append({'family': block['family'], 'projector': block['projector'],
                        'order': block['order'], 'root_embeddings': 72,
                        'direct_full_matrix_equality': True})
    return results


def run(args, preparation):
    started = time.monotonic()
    records, counts = inputs()
    assert preparation == metadata(records, counts)
    assert files.digest(args.catalogue) == domains.CATALOGUE_SHA
    with args.catalogue.open('rb') as stream:
        data = pickle.load(stream)
    builder = Builder(data)
    embeddings = [int(a)*c for a, c in zip(data[2], counts)]
    result = {'preparation': preparation, 'preparation_sha256': files.digest(args.preparation),
              'roots_constructed': [], 'blocks_scanned': [], 'negative_blocks': [],
              'unique_induced_cuts': [], 'cold_literal_entries_checked': 0,
              'direct_nine_rook_controls': [], 'numerical_no_separator_is_not_a_PSD_certificate': True}
    cache, known, timed_out = [], {}, False

    def deadline(_signum, _frame):
        raise TimeoutError('bounded four-root projector controls')

    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    try:
        oracle = literal.Oracle(data)
        for root in CONTROL_ROOTS:
            root_started = time.monotonic()
            record = records[root]
            blocks = builder.blocks(record)
            build_seconds = time.monotonic()-root_started
            cache.extend(blocks)
            root_record = {'root_type': root, 'classes': record['classes'],
                           'construction_seconds': build_seconds,
                           'lower_entries': sum(b['tensor'].shape[0] for b in blocks),
                           'nonzero_tensor_coefficients': sum(b['tensor'].nnz for b in blocks),
                           'csr_bytes': sum(b['tensor'].data.nbytes+b['tensor'].indices.nbytes+b['tensor'].indptr.nbytes for b in blocks)}
            result['roots_constructed'].append(root_record)
            for block in blocks:
                result['cold_literal_entries_checked'] += cold_control(block, record, oracle)
            if root == 1223:
                result['direct_nine_rook_controls'] = rook_control(builder, record, blocks, oracle)
            for block in blocks:
                scan_started = time.monotonic()
                matrix = FullScanner.matrix(block['tensor'], block['order'], embeddings)
                K, pivots = kernel(block, record)
                assert not any(int(x) for x in (matrix@K).flat)
                keep = [i for i in range(block['order']) if i not in set(pivots)]
                vector, quadratic, smallest, zero = FullScanner.negative(matrix[np.ix_(keep, keep)])
                scan_record = {'root_type': root, 'family': block['family'], 'projector': block['projector'],
                               'order': block['order'], 'quotient_order': len(keep),
                               'all_nine_kernels_checked_exactly': True,
                               'smallest_numeric_eigenvalue': smallest, 'exact_zero_quotient_rows': zero}
                result['blocks_scanned'].append(scan_record)
                if vector is not None:
                    full = [0]*block['order']
                    for i, value in zip(keep, vector):
                        full[i] = value
                    v = np.asarray(full, dtype=object)
                    assert int(v@matrix@v) == quadratic < 0
                    terms, divisor = forms.induced_form(block['tensor'], full, data[2])
                    value = sum(coefficient*counts[index] for index, coefficient in terms)
                    assert value*divisor == quadratic < 0
                    saved = {**scan_record, 'integer_vector': full, 'integer_quadratic_value': quadratic,
                             'primitive_induced_count_form': terms, 'induced_form_gcd': divisor,
                             'primitive_value_at_integer_witness': value,
                             'independent_literal_replay_complete': False}
                    result['negative_blocks'].append(saved)
                    direct_terms, direct_divisor, direct_value, entries = fresh_cut(block, record, full, oracle, data[2], counts)
                    assert (terms, divisor, value) == (direct_terms, direct_divisor, direct_value)
                    saved.update(independent_literal_replay_complete=True, supported_literal_entries_rebuilt=entries)
                    key = tuple(map(tuple, terms))
                    if key not in known:
                        known[key] = len(result['unique_induced_cuts'])
                        result['unique_induced_cuts'].append({'terms': terms, 'exact_value_at_witness': value})
                    saved['cut_index'] = known[key]
                scan_record['seconds'] = time.monotonic()-scan_started
            root_record['total_control_and_scan_seconds'] = time.monotonic()-root_started
            print(json.dumps(root_record), flush=True)
            files.save(args.output, result)
    except TimeoutError:
        timed_out = True
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    cache_record = {'format': 1, 'point_independent': True, 'complete_root_family': False,
                    'all_masks_retained_for_constructed_roots': True,
                    'zero_flags_or_roots_removed': False, 'construction_source_sha256': files.digest(Path(__file__)),
                    'domain_certificate_sha256': DOMAIN_SHA, 'catalogue_sha256': domains.CATALOGUE_SHA,
                    'selected_roots': list(CONTROL_ROOTS), 'constructed_roots': [r['root_type'] for r in result['roots_constructed']],
                    'blocks': cache}
    args.cache.write_bytes(gzip.compress(pickle.dumps(cache_record, protocol=5), compresslevel=9, mtime=0))
    result.update(status='completed four-root controls' if not timed_out and len(result['blocks_scanned']) == 16 else 'partial four-root controls',
                  timed_out=timed_out, complete_selected_roots=len(result['roots_constructed']) == 4,
                  complete_selected_block_scan=not timed_out and len(result['blocks_scanned']) == 16,
                  full_916_root_family_scanned=False, cache_sha256=files.digest(args.cache),
                  cache_bytes=args.cache.stat().st_size, seconds=time.monotonic()-started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                  unconfirmed_numeric_negatives=[r for r in result['blocks_scanned']
                      if r['smallest_numeric_eigenvalue'] is not None and r['smallest_numeric_eigenvalue'] < -1e-8
                      and not any((b['root_type'],b['family'],b['projector']) == (r['root_type'],r['family'],r['projector'])
                                  for b in result['negative_blocks'])])
    files.save(args.output, result)
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ('preparation','blocks_scanned','negative_blocks','unique_induced_cuts')}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--preparation', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 60
    if args.prepare:
        assert args.preparation is None and args.cache is None
        records, counts = inputs()
        result = metadata(records, counts)
        files.save(args.output, result)
        print(json.dumps(result, indent=2), flush=True)
    else:
        assert args.preparation and args.cache and not args.cache.exists()
        preparation = json.loads(args.preparation.read_text())
        with threadpool_limits(limits=1):
            run(args, preparation)
