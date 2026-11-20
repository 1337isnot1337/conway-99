"""Exact PSD certificates for the 832 cached order-nine projector blocks.

Eight explicit kernel vectors are removed by a unimodular pivot minor.
Integer congruences certify the remaining principal blocks as positive
definite. Floating point is used only to propose congruences in --write.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import pickle
import time

import numpy as np
from threadpoolctl import threadpool_limits

from flag_moments import BASE, cache9
from grid_free_core9_certificate import (
    INTEGER_POINT, exact_congruence_check, make_congruence, matrix_hash,
)
from grid_free_projector_probe import matrix_from_block
from subgraph_counts import extensions


def quotient_blocks():
    graphs, _, aut, _, scale, _, induced = cache9()
    assert not np.any(induced % scale)
    point = np.array(INTEGER_POINT, dtype=object)
    embeddings = ((induced//scale)*np.array(aut, dtype=object)[:, None])@point
    for kind in ('spectral', 'schur'):
        path = BASE/f'induced-{kind}-7.pickle'
        raw = path.read_bytes()
        blocks = pickle.loads(raw)
        assert len(blocks) == 416
        for index, (root, flags, tensor) in enumerate(blocks):
            rows = graphs[root]
            assert len(rows) == 7
            masks = [mask for mask, _ in extensions(rows)]
            start = 7 if kind == 'spectral' else 0
            assert len(flags) == start+len(masks)
            # The block order is negative projector, then positive projector.
            shift = 4 if index % 2 == 0 else -3
            kernel = [[1]+[((rows[i] >> j) & 1)+shift*(i == j)
                           for j in range(7)] for i in range(start)]
            kernel += [[1]+[(mask >> j) & 1 for j in range(7)] for mask in masks]
            kernel = np.array(kernel, dtype=object)
            matrix, product_bound = matrix_from_block(tensor, len(flags), embeddings)
            assert not np.any(matrix@kernel)
            pivots = [start+masks.index(0)]+[start+masks.index(1 << j) for j in range(7)]
            expected = np.eye(8, dtype=object)
            expected[:, 0] = 1
            assert np.array_equal(kernel[pivots], expected)
            # This pivot matrix has determinant one, so the kernel has rank8.
            keep = [i for i in range(len(flags)) if i not in pivots]
            reduced = matrix[np.ix_(keep, keep)]
            assert all(-(2**63) <= value < 2**63 for value in reduced.flat)
            reduced = np.array(reduced, dtype=np.int64)
            yield {
                'cache_file': path.name, 'cache_sha256': hashlib.sha256(raw).hexdigest(),
                'block_index': index, 'root_type': int(root), 'projector': 'negative' if index % 2 == 0 else 'positive',
                'order': len(flags), 'kernel_dimension': 8, 'pivot_rows': pivots,
                'reduced_order': len(keep), 'integer_matrix_sha256': matrix_hash(reduced),
                'sparse_product_bound': product_bound,
            }, reduced


def generate():
    records = []
    for metadata, reduced in quotient_blocks():
        certificate = make_congruence(reduced) if len(reduced) else {
            'scale_power': 0, 'upper_triangular_congruence': [],
            'minimum_integer_dominance_margin': 0,
        }
        records.append({**metadata, **certificate})
        if len(records) % 64 == 0:
            print(json.dumps({'certified_blocks': len(records)}), flush=True)
    assert len(records) == 832
    return {'scope': '832 cached order-nine root spectral and Schur blocks',
            'integer_point': INTEGER_POINT, 'blocks': records}


def verify(record):
    assert record['integer_point'] == INTEGER_POINT
    fresh = quotient_blocks()
    count, largest, largest_reduced = 0, 0, 0
    for saved, (metadata, reduced) in zip(record['blocks'], fresh, strict=True):
        assert all(saved[key] == value for key, value in metadata.items())
        if len(reduced):
            margin = exact_congruence_check(reduced, saved['upper_triangular_congruence'])
            assert margin == saved['minimum_integer_dominance_margin'] > 0
        else:
            assert saved['upper_triangular_congruence'] == []
            assert saved['minimum_integer_dominance_margin'] == 0
        count += 1
        largest = max(largest, saved['order'])
        largest_reduced = max(largest_reduced, saved['reduced_order'])
    assert count == 832
    return {'status': 'exact projector kernel and positive quotient replay passed',
            'blocks': count, 'largest_order': largest,
            'largest_reduced_order': largest_reduced, 'kernel_dimension_each': 8,
            'grid_count': 0, 'scope': record['scope']}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    started = time.monotonic()
    with threadpool_limits(limits=1):
        if args.write:
            record = generate()
            args.certificate.parent.mkdir(parents=True, exist_ok=True)
            args.certificate.write_bytes(gzip.compress((json.dumps(record, separators=(',', ':'))+'\n').encode(), mtime=0))
        record = json.loads(gzip.decompress(args.certificate.read_bytes()))
        result = verify(record)
    print(json.dumps({**result, 'seconds': time.monotonic()-started}), flush=True)
