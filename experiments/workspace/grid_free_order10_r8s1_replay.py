"""Replay new order-ten moment cuts by direct graph identification.

This verifier does not use the producer's label-transport builder. It
constructs each one/two-extension graph explicitly, checks its pair caps,
identifies its catalogue type, and checks the saved integer quadratic form.
No eigensystem or optimizer is called.
"""

import argparse
from collections import Counter
from functools import reduce
import gzip
import json
from math import gcd
from pathlib import Path
import pickle
import signal
import time

import numpy as np
import pynauty
from scipy import sparse
from threadpoolctl import threadpool_limits

import grid_free_order10_scaled as counts
from grid_free_core9_certificate import matrix_hash
from subgraph_counts import nauty


GENERATOR_SHA = '77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469'


def extend(root, masks, edge=0):
    r = len(root)
    rows = list(root)+list(masks)
    for j, mask in enumerate(masks, r):
        for i in range(r):
            if mask >> i & 1:
                rows[i] |= 1 << j
    if len(masks) == 2 and edge:
        rows[r] |= 1 << (r+1)
        rows[r+1] |= 1 << r
    return tuple(rows)


def pair_caps(rows):
    return all((rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1) <= 2
               for i in range(len(rows)) for j in range(i))


def replay(certificate, output):
    started = time.monotonic()
    saved = json.loads(certificate.read_text())
    assert saved['source_sha256'] == GENERATOR_SHA
    generator = Path(__file__).with_name('grid_free_order10_r8s1.py')
    assert counts.digest(generator) == GENERATOR_SHA
    paths = {name: Path(saved[name+'_path']) for name in ('catalogue', 'reduced_cache', 'witness', 'generated_cache')}
    for name, path in paths.items():
        assert counts.digest(path) == saved[name+'_sha256']
    with paths['catalogue'].open('rb') as stream:
        data = pickle.load(stream)
    graphs, _, aut, _ = data
    ids = {(len(rows), pynauty.certificate(nauty(rows))): i for i, rows in enumerate(graphs)}
    assert len(ids) == len(graphs) == 48965
    witness = json.loads(paths['witness'].read_text())
    induced_counts, point = witness['induced_counts'], witness['rounded_core_values']
    embeddings = [a*c for a, c in zip(aut, induced_counts)]
    cache = pickle.loads(gzip.decompress(paths['generated_cache'].read_bytes()))
    assert cache['witness_sha256'] == saved['witness_sha256']
    assert cache['catalogue_sha256'] == saved['catalogue_sha256']
    cached_blocks = {root: (masks, tensor) for root, masks, tensor in cache['blocks']}
    assert len(cached_blocks) == len(cache['blocks'])
    fresh_data, cores, scale, raw = counts.load_reduced(paths['reduced_cache'])
    assert fresh_data[0] == graphs and fresh_data[2] == aut and len(cores) == 549
    report = []
    used_cuts = set()

    def identify(rows):
        if not pair_caps(rows):
            return None
        return ids[len(rows), pynauty.certificate(nauty(rows))]

    for block in saved['negative_blocks']:
        root, masks = block['root_type'], block['flag_masks']
        rows = graphs[root]
        assert len(rows) == 8 and len(masks)+1 == block['retained_flags']
        assert len(set(masks)) == len(masks) and all(mask.bit_count() >= 3 for mask in masks)
        terms_by_entry = [[root]]
        rr, cc = [0], [root]
        for i, left in enumerate(masks, 1):
            child = identify(extend(rows, [left]))
            assert child is not None
            assert identify(extend(rows, [left, left], 0)) is None
            assert identify(extend(rows, [left, left], 1)) is None
            for j in range(i+1):
                if j == 0 or j == i:
                    terms = [child]
                else:
                    terms = [index for edge in (0, 1)
                             if (index := identify(extend(rows, [left, masks[j-1]], edge))) is not None]
                terms_by_entry.append(terms)
                rr.extend([i*(i+1)//2+j]*len(terms))
                cc.extend(terms)
        n = len(masks)+1
        tensor = sparse.csr_matrix((np.ones(len(rr), dtype=np.int64), (rr, cc)),
                                   shape=(n*(n+1)//2, len(graphs)), dtype=np.int64)
        cached_masks, cached_tensor = cached_blocks[root]
        assert cached_masks == masks and (tensor != cached_tensor).nnz == 0
        matrix = np.zeros((n, n), dtype=object)
        position = 0
        for i in range(n):
            for j in range(i+1):
                value = sum(embeddings[index] for index in terms_by_entry[position])
                matrix[i, j] = matrix[j, i] = value
                position += 1
        assert all(-(1 << 63) <= v < (1 << 63) for v in matrix.flat)
        assert matrix_hash(matrix.astype(np.int64)) == block['integer_matrix_sha256']
        vector = block['integer_vector']
        assert len(vector) == n and all(type(v) is int for v in vector)
        v = np.array(vector, dtype=object)
        quadratic = int(v@matrix@v)
        assert quadratic == block['integer_quadratic_value'] < 0
        weights = Counter()
        position = 0
        for i in range(n):
            for j in range(i+1):
                coefficient = vector[i]*vector[j]*(1 if i == j else 2)
                for index in terms_by_entry[position]:
                    weights[index] += coefficient*aut[index]
                position += 1
        entries = [[index, value] for index, value in sorted(weights.items()) if value]
        divisor = reduce(gcd, [abs(value) for _, value in entries], 0)
        assert divisor == block['induced_form_gcd'] > 0
        entries = [[index, value//divisor] for index, value in entries]
        assert entries == block['primitive_induced_count_form']
        induced_value = sum(value*induced_counts[index] for index, value in entries)
        assert induced_value == block['primitive_induced_value'] and induced_value*divisor == quadratic
        core = [0]*550
        for index, weight in entries:
            for j in np.flatnonzero(raw[index]):
                core[int(j)] += weight*int(raw[index, j])
        assert all(value % scale == 0 for value in core)
        core = [value//scale for value in core]
        common = reduce(gcd, [abs(value) for value in core], 0)
        assert common == block['core_form_gcd'] > 0
        core = [value//common for value in core]
        cut_index = block['core_cut_index']
        cut = saved['unique_core_cuts'][cut_index]
        assert core == cut['coefficients']
        value = sum(a*x for a, x in zip(core, point))
        assert value == cut['exact_value_at_witness'] < 0
        assert value*common == induced_value
        assert cut['new_coordinate_support'] == [j for j in range(58, 550) if core[j]]
        used_cuts.add(cut_index)
        report.append({'root_type': root, 'flags': n, 'integer_quadratic_value': quadratic,
                       'primitive_core_cut_value': value,
                       'new_coordinate_support_size': len(cut['new_coordinate_support'])})
    assert len(report) == saved['exact_negative_blocks'] == 11
    assert used_cuts == set(range(saved['unique_core_cut_count'])) == set(range(11))
    result = {'status': 'direct graph reconstruction and exact eleven-cut replay PASS',
              'source_sha256': counts.digest(Path(__file__)),
              'generator_source_sha256': GENERATOR_SHA,
              'certificate_sha256': counts.digest(certificate), 'blocks': report,
              'exact_negative_blocks': 11, 'unique_core_cuts': 11,
              'label_transport_builder_used': False,
              'numerical_eigensystems_recomputed': False, 'optimizer_called': False,
              'seconds': time.monotonic()-started}
    counts.save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    signal.alarm(120)
    with threadpool_limits(limits=1):
        replay(args.certificate, args.output)
    signal.alarm(0)
