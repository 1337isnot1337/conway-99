"""Exact grid-free witness for the available order-nine count/PSD model.

The certificate contains integer core counts and integer triangular
congruences for all 584 cached moment matrices. The verifier uses only
integer arithmetic for its sign decisions. Floating-point Cholesky is
used only when generating a congruence, never when replaying one.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
from math import comb
from pathlib import Path
import pickle
import time

import numpy as np
from scipy.linalg import solve_triangular
from threadpoolctl import threadpool_limits

from flag_moments import BASE, cache9
from subgraph_counts import build, identities


INTEGER_POINT = [
    1, 326, 367, 735, 163, 326, 10277, 14097, 1141, 82, 408, 82, 82,
    82, 326, 16005, 82, 16130, 326, 163, 326, 4076, 163, 1386, 1631,
    652, 82, 408, 489, 82, 82, 82, 163, 7569, 2243, 23542, 21800,
    489, 489, 18649, 978, 978, 4837, 82, 1006, 571, 326, 326, 82,
    82, 163, 163, 82, 82, 82, 82, 0, 0,
]


def count_checks(pack, point):
    graphs, levels, aut, cores, scale, inj, induced = pack
    x = np.array(point, dtype=object)
    assert len(x) == len(cores)+1 and x[0] == 1
    assert all(isinstance(v, int) and v >= 0 for v in point)
    raw = induced@x
    assert all(value >= 0 and value % scale == 0 for value in raw)
    counts = raw//scale
    embeddings = inj@x
    assert all(value >= 0 and value % a == 0 for value, a in zip(embeddings, aut))
    assert all(sum(counts[i] for i in level) == comb(99, n) for n, level in enumerate(levels))
    zero_types = [i for i, graph in enumerate(graphs)
                  if len(graph) == 9 and sum(row.bit_count() for row in graph) >= 34]
    assert len(zero_types) == 2 and all(counts[i] == 0 for i in zero_types)
    assert all(embeddings[i] == 0 for i in zero_types)
    # Rebuild the extension catalogue and replay the original equations,
    # independently of the reduced inequalities defining the point.
    data = build(9)
    assert data[0] == graphs and data[1] == levels and data[2] == aut
    equation_count = 0
    for equation in identities(data, 99, 14):
        assert sum(value*(counts[j-1] if j else 1) for j, value in equation.items()) == 0
        equation_count += 1
    assert equation_count == 23189
    return {'catalogue_types': len(graphs), 'core_coordinates': len(cores),
            'original_equations_checked': equation_count,
            'nonnegative_integral_induced_counts': len(counts),
            'zero_rook_and_broken_rook_types': zero_types,
            'grid_count': 0, 'broken_rook_count': 0}, embeddings, counts


def blocks_and_matrices(pack, point):
    graphs, levels, aut, cores, scale, inj, induced = pack
    x = np.array(point, dtype=object)
    for prefix, forms in (
        ('', inj),
        ('induced-', (induced//scale)*np.array(aut, dtype=object)[:, None]),
    ):
        assert not np.any(induced % scale)
        embeddings_object = forms@x
        assert all(0 <= value < 2**63 for value in embeddings_object)
        embeddings = np.asarray(embeddings_object, dtype=np.int64)
        for path in sorted(BASE.glob(prefix+'moments-?-?-512.pickle')):
            with path.open('rb') as stream:
                blocks = pickle.load(stream)
            for root, flags, T in blocks:
                n = len(flags)
                assert T.nnz and T.data.dtype.kind == 'i' and min(T.data) > 0
                # Compute the overflow bound without fixed-width summation.
                largest_row_sum = max(sum(int(value) for value in T.data[a:b])
                                      for a, b in zip(T.indptr[:-1], T.indptr[1:]))
                bound = int(max(embeddings[T.indices]))*largest_row_sum
                if bound < 2**63:
                    values = T@embeddings
                else:
                    values = np.array([
                        sum(int(T.data[k])*int(embeddings[T.indices[k]])
                            for k in range(T.indptr[row], T.indptr[row+1]))
                        for row in range(T.shape[0])], dtype=object)
                assert all(0 <= value < 2**63 for value in values)
                lower = np.tril_indices(n)
                M = np.empty((n, n), dtype=np.int64)
                M[lower] = values
                M[(lower[1], lower[0])] = values
                yield path.name, root, M


def matrix_hash(M):
    return hashlib.sha256(np.asarray(M, dtype='<i8').tobytes()).hexdigest()


def exact_congruence_check(M, upper):
    n = len(M)
    assert len(upper) == n*(n+1)//2
    assert all(type(value) is int for value in upper)
    Q = np.zeros((n, n), dtype=object)
    Q[np.triu_indices(n)] = upper
    assert all(Q[i, i] != 0 for i in range(n))
    transformed = Q.T@M.astype(object)@Q
    minimum = min(int(transformed[i, i])-sum(abs(int(transformed[i, j]))
                                           for j in range(n) if j != i)
                  for i in range(n))
    return minimum


def make_congruence(M):
    n = len(M)
    d = np.sqrt(np.asarray(np.diag(M), dtype=float))
    assert np.all(d > 0)
    normalized = M/d[:, None]/d[None, :]
    L = np.linalg.cholesky(normalized)
    inverse_factor = solve_triangular(L.T, np.eye(n), lower=False)/d[:, None]
    inverse_factor /= np.max(abs(inverse_factor))
    for power in (20, 28, 36, 44):
        upper = np.rint((2**power)*inverse_factor)[np.triu_indices(n)].astype(np.int64).tolist()
        Q_diagonal_positions = [i*n-i*(i-1)//2 for i in range(n)]
        if any(upper[i] == 0 for i in Q_diagonal_positions):
            continue
        minimum = exact_congruence_check(M, upper)
        if minimum > 0:
            return {'scale_power': power, 'upper_triangular_congruence': upper,
                    'minimum_integer_dominance_margin': minimum}
    raise ArithmeticError('No positive integer dominance certificate found')


def generate():
    pack = cache9()
    checks, _, _ = count_checks(pack, INTEGER_POINT)
    result = {'format': 1, 'scope': 'finite order-nine count and cached flag-PSD relaxation',
              'core_point_with_constant': INTEGER_POINT, 'count_checks': checks,
              'blocks': []}
    for name, root, M in blocks_and_matrices(pack, INTEGER_POINT):
        record = {'cache_file': name, 'root_type': root, 'order': len(M),
                  'integer_matrix_sha256': matrix_hash(M), **make_congruence(M)}
        result['blocks'].append(record)
        if len(result['blocks']) % 50 == 0:
            print(json.dumps({'exact_positive_definite_blocks': len(result['blocks'])}), flush=True)
    assert len(result['blocks']) == 584
    result['exact_positive_definite_blocks'] = 584
    result['ordinary_blocks'] = sum(not b['cache_file'].startswith('induced-') for b in result['blocks'])
    result['induced_blocks'] = 584-result['ordinary_blocks']
    assert result['ordinary_blocks'] == result['induced_blocks'] == 292
    return result


def replay(result):
    assert result['format'] == 1
    pack = cache9()
    point = result['core_point_with_constant']
    checks, _, _ = count_checks(pack, point)
    assert checks == result['count_checks']
    matrices = list(blocks_and_matrices(pack, point))
    assert len(matrices) == len(result['blocks']) == 584
    for record, (name, root, M) in zip(result['blocks'], matrices):
        assert record['cache_file'] == name and record['root_type'] == root and record['order'] == len(M)
        assert record['integer_matrix_sha256'] == matrix_hash(M)
        minimum = exact_congruence_check(M, record['upper_triangular_congruence'])
        assert minimum == record['minimum_integer_dominance_margin'] and minimum > 0
    assert result['exact_positive_definite_blocks'] == 584


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    assert bool(args.write) != bool(args.verify)
    start = time.monotonic()
    with threadpool_limits(limits=1):
        if args.write:
            result = generate()
            args.write.write_bytes(gzip.compress(json.dumps(result, separators=(',', ':')).encode(), mtime=0))
        else:
            result = json.loads(gzip.decompress(args.verify.read_bytes()))
            replay(result)
    print(json.dumps({'grid_count': result['count_checks']['grid_count'],
                      'broken_rook_count': result['count_checks']['broken_rook_count'],
                      'original_equations_checked': result['count_checks']['original_equations_checked'],
                      'exact_positive_definite_blocks': result['exact_positive_definite_blocks'],
                      'certificate_replayed': bool(args.verify), 'seconds': time.monotonic()-start}), flush=True)
