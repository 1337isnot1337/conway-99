"""Exact three-variable inequalities for binary one-vertex induced flags.

This scans the full r=8,s=1 tensor cache at a saved integer count point.
For each flag triple it checks the four quadratic polynomials which are
nonnegative on {0,1}^3. It exports one most-negative instance per kind
and root, then reconstructs each used product by direct graph lookup.
No reduced matrix, numerical eigensystem, or optimizer is loaded.
"""

import argparse
from collections import Counter
from functools import reduce
import gzip
import hashlib
from itertools import product
import json
from math import comb, gcd
from pathlib import Path
import pickle
import time

import numpy as np
import pynauty
from threadpoolctl import threadpool_limits

from subgraph_counts import nauty


CACHE_SHA = 'aecf7411230f718c8c3879c38ad39dcdb041ed07c58a799f8b044ebd0ab5028d'
CATALOGUE_SHA = '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def products(kind, i, j, k):
    if kind == 0:
        return [(0, 0, 1), (0, i, -1), (0, j, -1), (0, k, -1),
                (i, j, 1), (i, k, 1), (j, k, 1)]
    a, b, c = ((i, j, k), (j, i, k), (k, i, j))[kind-1]
    return [(0, a, 1), (a, b, -1), (a, c, -1), (b, c, 1)]


def controls():
    table = []
    for values in product((0, 1), repeat=3):
        x = (1,)+values
        scores = [sum(coef*x[a]*x[b] for a, b, coef in products(kind, 1, 2, 3))
                  for kind in range(4)]
        assert all(value >= 0 for value in scores)
        q = sum(values)-1
        assert scores[0] == q*(q-1)//2
        for kind in range(1, 4):
            a = kind-1
            q = sum(values)-2*values[a]
            assert scores[kind] == q*(q-1)//2
        table.append({'binary_values': list(values), 'polynomial_values': scores})
    return table


def extended(root, masks, cross_edge=0):
    n = len(root)
    rows = list(root)+list(masks)
    for j, mask in enumerate(masks, n):
        for i in range(n):
            if mask >> i & 1:
                rows[i] |= 1 << j
    if len(masks) == 2 and cross_edge:
        rows[n] |= 1 << (n+1)
        rows[n+1] |= 1 << n
    return tuple(rows)


def admissible(rows):
    return all((rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1) <= 2
               for i in range(len(rows)) for j in range(i))


def row_index(i, j):
    i, j = max(i, j), min(i, j)
    return i*(i+1)//2+j


def scan(catalogue, cache_path, witness_path, output):
    started = time.monotonic()
    assert digest(catalogue) == CATALOGUE_SHA and digest(cache_path) == CACHE_SHA
    data = pickle.loads(catalogue.read_bytes())
    graphs, levels, aut, children = data
    assert len(graphs) == 48965 and len(levels[8]) == 916
    cache = pickle.loads(gzip.decompress(cache_path.read_bytes()))
    assert cache['point_independent'] and cache['complete_root_family']
    assert not cache['zero_flags_or_roots_removed']
    assert [root for root, _, _ in cache['blocks']] == levels[8]
    witness = json.loads(witness_path.read_text())
    counts = witness['induced_counts']
    assert len(counts) == len(graphs) and all(type(v) is int for v in counts)
    embeddings = [a*c for a, c in zip(aut, counts)]
    maximum = max(map(abs, embeddings))
    # Each matrix entry sums at most two embeddings. Each tested
    # polynomial has at most seven signed entries.
    assert 14*maximum < 1 << 63
    embeddings_array = np.array(embeddings, dtype=np.int64)
    candidates, block_stats = [], []
    tested = violations = 0
    for root, masks, tensor in cache['blocks']:
        assert masks == [mask for mask, _ in children[root] if mask.bit_count() >= 3]
        assert tensor.data.dtype.kind == 'i' and np.all(tensor.data > 0)
        assert max(np.asarray(tensor.sum(axis=1)).ravel(), default=0) <= 2
        n = len(masks)+1
        assert tensor.shape == (n*(n+1)//2, len(graphs))
        lower = np.tril_indices(n)
        matrix = np.empty((n, n), dtype=np.int64)
        values = tensor @ embeddings_array
        matrix[lower] = values
        matrix[(lower[1], lower[0])] = values
        assert matrix[0, 0] == embeddings[root]
        assert np.array_equal(matrix[0], matrix.diagonal())
        best = [(0, None) for _ in range(4)]
        bad = [0]*4
        for i in range(1, n-2):
            for j in range(i+1, n-1):
                ks = slice(j+1, n)
                pi, pj, pk = matrix[0, i], matrix[0, j], matrix[0, ks]
                pij, pik, pjk = matrix[i, j], matrix[i, ks], matrix[j, ks]
                scores = (matrix[0, 0]-pi-pj-pk+pij+pik+pjk,
                          pi-pij-pik+pjk, pj-pij-pjk+pik, pk-pik-pjk+pij)
                for kind, array in enumerate(scores):
                    bad[kind] += int(np.count_nonzero(array < 0))
                    index = int(np.argmin(array))
                    value = int(array[index])
                    if value < best[kind][0]:
                        best[kind] = value, (i, j, j+1+index)
        local_tests = 4*comb(len(masks), 3)
        tested += local_tests
        violations += sum(bad)
        block_stats.append({'root_type': root, 'binary_flags': len(masks),
                            'inequalities_checked': local_tests,
                            'negative_inequalities_by_kind': bad})
        for kind, (value, triple) in enumerate(best):
            if triple is None:
                continue
            i, j, k = triple
            coefficients = Counter()
            for a, b, weight in products(kind, i, j, k):
                at = row_index(a, b)
                for t in range(tensor.indptr[at], tensor.indptr[at+1]):
                    index = int(tensor.indices[t])
                    coefficients[index] += weight*int(tensor.data[t])*aut[index]
            terms = [[index, coefficient] for index, coefficient in sorted(coefficients.items()) if coefficient]
            divisor = reduce(gcd, (abs(c) for _, c in terms), 0)
            assert divisor > 0
            terms = [[index, coefficient//divisor] for index, coefficient in terms]
            evaluated = sum(c*counts[index] for index, c in terms)
            assert evaluated*divisor == value < 0
            candidates.append({'root_type': root, 'kind': kind,
                               'three_flag_masks': [masks[t-1] for t in triple],
                               'full_block_indices': list(triple),
                               'raw_integer_value': value, 'positive_gcd': divisor,
                               'primitive_induced_count_form': terms,
                               'primitive_integer_value': evaluated})
    # This graph lookup is independent of the cache's label transports.
    lookup = {(len(rows), pynauty.certificate(nauty(rows))): i for i, rows in enumerate(graphs)}
    assert len(lookup) == len(graphs)
    for record in candidates:
        rows = graphs[record['root_type']]
        masks = record['three_flag_masks']
        for mask in masks:
            assert mask.bit_count() >= 3
            assert all(not admissible(extended(rows, [mask, mask], edge)) for edge in (0, 1))
        direct = Counter()
        for i, j, coefficient in products(record['kind'], 1, 2, 3):
            i, j = min(i, j), max(i, j)
            if i == j == 0:
                terms = [record['root_type']]
            elif i == 0 or i == j:
                graph = extended(rows, [masks[j-1]])
                assert admissible(graph)
                terms = [lookup[len(graph), pynauty.certificate(nauty(graph))]]
            else:
                terms = []
                for edge in (0, 1):
                    graph = extended(rows, [masks[i-1], masks[j-1]], edge)
                    if admissible(graph):
                        terms.append(lookup[len(graph), pynauty.certificate(nauty(graph))])
            for index in terms:
                direct[index] += coefficient*aut[index]
        direct_terms = [[index, value] for index, value in sorted(direct.items()) if value]
        divisor = reduce(gcd, (abs(value) for _, value in direct_terms), 0)
        assert divisor == record['positive_gcd']
        assert [[index, value//divisor] for index, value in direct_terms] == record['primitive_induced_count_form']
    result = {'status': 'complete exact binary-flag triangle scan',
              'source_sha256': digest(Path(__file__)), 'catalogue_sha256': CATALOGUE_SHA,
              'full_cache_sha256': CACHE_SHA, 'witness_path': str(witness_path),
              'witness_sha256': digest(witness_path), 'binary_truth_table': controls(),
              'root_blocks': len(block_stats), 'inequalities_checked': tested,
              'negative_inequalities': violations, 'exported_negative_instances': len(candidates),
              'blocks_with_a_negative': sum(any(r['negative_inequalities_by_kind']) for r in block_stats),
              'unique_primitive_induced_cuts': len({tuple(map(tuple, c['primitive_induced_count_form'])) for c in candidates}),
              'direct_graph_reconstruction_passed': True, 'block_statistics': block_stats,
              'cuts': candidates, 'optimizer_called': False, 'reduced_matrix_loaded': False,
              'PSD_test_used': False, 'count_point_is_graph': False,
              'seconds': time.monotonic()-started}
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('cuts', 'block_statistics', 'binary_truth_table')}, indent=2))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('catalogue', 'cache', 'witness', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        scan(args.catalogue, args.cache, args.witness, args.output)
