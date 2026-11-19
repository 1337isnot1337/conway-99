"""Exact negative-vector checks for additional root projector blocks.

Numerical eigenvectors propose integer vectors. Only exact negative
quadratic forms are accepted. Passing this probe is not a PSD certificate.
"""

import argparse
import hashlib
import json
from pathlib import Path
import pickle

import numpy as np
from threadpoolctl import threadpool_limits

from flag_moments import BASE, cache9
from grid_free_core9_certificate import INTEGER_POINT


def matrix_from_block(T, order, embeddings):
    assert T.data.dtype.kind == 'i'
    row_bound = max(sum(abs(int(v)) for v in T.data[a:b])
                    for a, b in zip(T.indptr[:-1], T.indptr[1:]))
    bound = max(abs(int(v)) for v in embeddings)*row_bound
    if bound < 2**63:
        values = T@np.asarray(embeddings, dtype=np.int64)
    else:
        values = np.array([
            sum(int(T.data[k])*int(embeddings[T.indices[k]])
                for k in range(T.indptr[i], T.indptr[i+1]))
            for i in range(T.shape[0])], dtype=object)
    matrix = np.zeros((order, order), dtype=object)
    lower = np.tril_indices(order)
    matrix[lower] = [int(v) for v in values]
    matrix[(lower[1], lower[0])] = matrix[lower]
    return matrix, bound


def probe(output):
    _, _, aut, _, scale, _, induced = cache9()
    assert not np.any(induced % scale)
    embeddings = ((induced//scale)*np.array(aut, dtype=object)[:, None])@np.array(INTEGER_POINT, dtype=object)
    result = {'scope': 'additional cached root projector blocks at a fixed count point',
              'integer_point': INTEGER_POINT, 'caches': [], 'negative_blocks': []}
    with threadpool_limits(limits=1):
        for name in ('induced-spectral-7.pickle', 'induced-schur-7.pickle'):
            path = BASE/name
            blocks = pickle.loads(path.read_bytes())
            cache = {'file': name, 'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                     'blocks': len(blocks), 'largest_order': 0, 'negative_blocks': 0,
                     'smallest_normalized_numeric_eigenvalue': 1.0}
            for index, (root, flags, T) in enumerate(blocks):
                matrix, bound = matrix_from_block(T, len(flags), embeddings)
                order = len(matrix)
                cache['largest_order'] = max(cache['largest_order'], order)
                diagonal = np.array([float(matrix[i, i]) for i in range(order)])
                scales = np.sqrt(np.maximum(1, np.abs(diagonal)))
                normalized = np.asarray(matrix, dtype=float)/scales[:, None]/scales[None, :]
                values, vectors = np.linalg.eigh(normalized)
                smallest = float(values[0])
                cache['smallest_normalized_numeric_eigenvalue'] = min(cache['smallest_normalized_numeric_eigenvalue'], smallest)
                if smallest >= -1e-8:
                    continue
                direction = vectors[:, 0]/scales
                direction /= max(abs(direction))
                for power in (12, 20, 28, 36):
                    vector = [int(round(float(v)*(2**power))) for v in direction]
                    x = np.array(vector, dtype=object)
                    value = int(x@matrix@x)
                    if value < 0:
                        result['negative_blocks'].append({'cache_file': name, 'block_index': index,
                            'root_type': int(root), 'order': order, 'integer_vector': vector,
                            'quadratic_value': value, 'sparse_product_bound': bound,
                            'normalized_numeric_eigenvalue': smallest})
                        cache['negative_blocks'] += 1
                        break
                else:
                    raise ArithmeticError('A numerical violation has no exact certificate')
            result['caches'].append(cache)
            print(json.dumps(cache), flush=True)
    result['status'] = 'exact violations found' if result['negative_blocks'] else 'no violation found; PSD not certified'
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'exact_negative_blocks': len(result['negative_blocks'])}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    probe(parser.parse_args().output)
