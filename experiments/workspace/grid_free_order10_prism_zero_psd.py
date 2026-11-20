"""Exact cached PSD certificates for the repaired prism-zero count prefix.

Only exact zero rows and an explicitly checked kernel span are removed.
Each remaining principal quotient is certified by an integer congruence
with strict positive diagonal dominance. Generation is time-bounded and
never interprets a numerical eigensystem as a PSD certificate.
"""

import argparse
from functools import reduce
import gzip
import hashlib
import json
from math import gcd
from pathlib import Path
import pickle
import resource
import signal
import time

import numpy as np
import sympy as sp
from threadpoolctl import threadpool_limits

from grid_free_core9_certificate import exact_congruence_check, make_congruence, matrix_hash
from grid_free_projector_probe import matrix_from_block
import grid_free_order10_moments as caches
from subgraph_counts import extensions


WITNESS_SHA = '62faca107e3f5a7f560c009133e2da563aa16619382b7778f7ff53aa1cd75db7'


def write_certificate(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.pending')
    temporary.write_bytes(gzip.compress(json.dumps(record, separators=(',', ':')).encode(), mtime=0))
    temporary.replace(path)


def matrices(witness_path):
    assert caches.digest(witness_path) == WITNESS_SHA
    witness = json.loads(witness_path.read_text())
    point = witness['rounded_core_values'][:58]
    assert len(point) == 58 and point[0] == 1 and point[1] == point[56] == point[57] == 0
    assert all(type(v) is int and v >= 0 for v in point)
    path = caches.BASE/'moments-order9.pickle'
    with path.open('rb') as stream:
        graphs, _, aut, cores, scale, inj, induced = pickle.load(stream)
    assert len(graphs) == 6535 and len(cores) == 57
    assert not np.any(induced % scale)
    x = np.array(point, dtype=object)
    old_counts = (induced//scale)@x
    assert [int(v) for v in old_counts] == witness['induced_counts'][:6535]
    embeddings = {'ordinary': inj@x,
                  'induced': old_counts*np.array(aut, dtype=object)}
    for values in embeddings.values():
        assert all(0 <= value < 2**63 for value in values)
    for path, kind in caches.cache_files():
        raw = path.read_bytes()
        blocks = pickle.loads(raw)
        for index, (root, flags, tensor) in enumerate(blocks):
            matrix, bound = matrix_from_block(tensor, len(flags), embeddings[kind])
            assert all(-(2**63) <= value < 2**63 for value in matrix.flat)
            matrix = np.asarray(matrix, dtype=np.int64)
            metadata = {'cache_file': path.name,
                        'cache_sha256': hashlib.sha256(raw).hexdigest(),
                        'block_index': index, 'root_type': int(root), 'order': len(flags),
                        'integer_matrix_sha256': matrix_hash(matrix),
                        'sparse_product_absolute_bound': int(bound)}
            yield metadata, matrix, graphs[int(root)]


def obvious_negative(matrix):
    n = len(matrix)
    for i in range(n):
        diagonal = int(matrix[i, i])
        if diagonal < 0:
            vector = [0]*n
            vector[i] = 1
            return vector, diagonal
        if diagonal == 0:
            for j in range(n):
                value = int(matrix[i, j])
                if value:
                    vector = [0]*n
                    vector[i] = max(1, int(matrix[j, j])//(2*abs(value))+1)
                    vector[j] = -1 if value > 0 else 1
                    v = np.array(vector, dtype=object)
                    quadratic = int(v@matrix.astype(object)@v)
                    assert quadratic < 0
                    return vector, quadratic
    return None


def quotient(metadata, matrix, rows):
    zero = [i for i in range(len(matrix)) if matrix[i, i] == 0]
    assert all(not np.any(matrix[i]) for i in zero)
    active = [i for i in range(len(matrix)) if i not in set(zero)]
    record = {'exact_zero_rows': zero, 'active_order': len(active),
              'kernel_rank': 0, 'kernel_columns': [], 'kernel_pivot_rows': [],
              'kernel_pivot_determinant': 1}
    kernel_names = ('induced-spectral-7.pickle', 'induced-schur-7.pickle')
    if active and metadata['cache_file'] in kernel_names:
        assert len(rows) == 7
        masks = [mask for mask, _ in extensions(rows)]
        start = 7 if metadata['cache_file'] == kernel_names[0] else 0
        assert len(matrix) == start+len(masks)
        shift = 4 if metadata['block_index'] % 2 == 0 else -3
        kernel = [[1]+[((rows[i] >> j) & 1)+shift*(i == j)
                       for j in range(7)] for i in range(start)]
        kernel += [[1]+[(mask >> j) & 1 for j in range(7)] for mask in masks]
        kernel = np.array(kernel, dtype=object)
        assert not np.any(matrix.astype(object)@kernel)
        restricted = sp.Matrix(kernel[active].tolist())
        columns = list(restricted.rref()[1])
        rank = len(columns)
        if rank:
            basis = restricted[:, columns]
            pivots = list(basis.T.rref()[1])
            assert len(pivots) == rank
            determinant = int(basis[pivots, :].det())
            assert determinant != 0
            removed = [active[i] for i in pivots]
            record.update(kernel_rank=rank, kernel_columns=columns,
                          kernel_pivot_rows=removed,
                          kernel_pivot_determinant=determinant)
            active = [i for i in active if i not in set(removed)]
    reduced = matrix[np.ix_(active, active)]
    record.update(quotient_indices=active, quotient_order=len(active),
                  quotient_matrix_sha256=matrix_hash(reduced))
    return record, reduced


def negative_proposal(matrix):
    if not len(matrix):
        return None, None
    diagonal = np.array([float(matrix[i, i]) for i in range(len(matrix))])
    scales = np.sqrt(np.maximum(1, np.abs(diagonal)))
    normalized = np.asarray(matrix, dtype=float)/scales[:, None]/scales[None, :]
    values, vectors = np.linalg.eigh(normalized)
    direction = vectors[:, 0]/scales
    direction /= max(abs(direction))
    for power in (8, 12, 20, 28, 36):
        vector = [int(round(v*(2**power))) for v in direction]
        divisor = reduce(gcd, [abs(v) for v in vector], 0)
        if not divisor:
            continue
        vector = [v//divisor for v in vector]
        x = np.array(vector, dtype=object)
        value = int(x@matrix.astype(object)@x)
        if value < 0:
            return {'integer_vector': vector, 'quadratic_value': value}, float(values[0])
    return None, float(values[0])


def generate(witness, certificate, summary_path, seconds):
    started = time.monotonic()
    result = {'format': 1, 'scope': 'the specified1416 cached order-nine PSD blocks',
              'source_sha256': caches.digest(Path(__file__)),
              'witness_path': str(witness), 'witness_sha256': caches.digest(witness),
              'integer_prefix': json.loads(witness.read_text())['rounded_core_values'][:58],
              'order_nine_cache_sha256': caches.digest(caches.BASE/'moments-order9.pickle'),
              'helper_source_hashes': {name: caches.digest(caches.BASE/name) for name in
                  ('grid_free_core9_certificate.py', 'grid_free_projector_probe.py',
                   'grid_free_order10_moments.py', 'subgraph_counts.py')},
              'maximum_generation_seconds': seconds, 'optimizer_called': False,
              'blocks': [], 'unresolved_blocks': [], 'negative_blocks': []}

    def deadline(_signum, _frame):
        raise TimeoutError('bounded exact PSD generation time limit')

    old_handler = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    timed_out = False
    try:
        for metadata, matrix, rows in matrices(witness):
            negative = obvious_negative(matrix)
            if negative:
                vector, value = negative
                result['negative_blocks'].append({**metadata, 'integer_vector': vector,
                                                  'quadratic_value': value})
                break
            reduced_metadata, reduced = quotient(metadata, matrix, rows)
            try:
                proof = make_congruence(reduced) if len(reduced) else {
                    'scale_power': 0, 'upper_triangular_congruence': [],
                    'minimum_integer_dominance_margin': 0}
            except (np.linalg.LinAlgError, ArithmeticError) as error:
                negative, smallest = negative_proposal(reduced)
                if negative:
                    full = [0]*len(matrix)
                    for i, value in zip(reduced_metadata['quotient_indices'], negative['integer_vector']):
                        full[i] = value
                    v = np.array(full, dtype=object)
                    value = int(v@matrix.astype(object)@v)
                    assert value == negative['quadratic_value'] < 0
                    result['negative_blocks'].append({**metadata, 'integer_vector': full,
                                                      'quadratic_value': value})
                    break
                result['unresolved_blocks'].append({**metadata, **reduced_metadata,
                    'reason': str(error), 'smallest_numeric_quotient_eigenvalue': smallest})
            else:
                result['blocks'].append({**metadata, **reduced_metadata, **proof})
            examined = len(result['blocks'])+len(result['unresolved_blocks'])
            if examined % 64 == 0:
                write_certificate(certificate, result)
                print(json.dumps({'examined': examined, 'exact_PSD_blocks': len(result['blocks']),
                                  'unresolved': len(result['unresolved_blocks'])}), flush=True)
    except TimeoutError:
        timed_out = True
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
    examined = len(result['blocks'])+len(result['unresolved_blocks'])+len(result['negative_blocks'])
    complete = not timed_out and examined == 1416 and not result['unresolved_blocks'] and not result['negative_blocks']
    result.update(status='all1416 cached blocks certified PSD' if complete else
                         'exact negative block found' if result['negative_blocks'] else
                         'partial exact certification; unresolved',
                  exact_PSD_blocks=len(result['blocks']), examined_blocks=examined,
                  all_cached_blocks_PSD_certified=complete, timed_out=timed_out,
                  seconds=time.monotonic()-started,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    write_certificate(certificate, result)
    summary = {key: value for key, value in result.items() if key not in
               ('blocks', 'unresolved_blocks', 'negative_blocks', 'integer_prefix')}
    summary.update(certificate_path=str(certificate), certificate_sha256=caches.digest(certificate),
                   unresolved_blocks=result['unresolved_blocks'], negative_blocks=result['negative_blocks'])
    caches.save(summary_path, summary)
    print(json.dumps(summary, indent=2), flush=True)
    return result


def replay(certificate):
    result = json.loads(gzip.decompress(certificate.read_bytes()))
    assert result['source_sha256'] == caches.digest(Path(__file__))
    witness = Path(result['witness_path'])
    assert result['witness_sha256'] == caches.digest(witness) == WITNESS_SHA
    assert result['integer_prefix'] == json.loads(witness.read_text())['rounded_core_values'][:58]
    assert result['order_nine_cache_sha256'] == caches.digest(caches.BASE/'moments-order9.pickle')
    for name, digest in result['helper_source_hashes'].items():
        assert caches.digest(caches.BASE/name) == digest
    records = {(row['cache_file'], row['block_index']): row for row in result['blocks']}
    assert len(records) == len(result['blocks'])
    checked = 0
    for metadata, matrix, rows in matrices(witness):
        key = metadata['cache_file'], metadata['block_index']
        if key not in records:
            continue
        saved = records[key]
        assert all(saved[k] == value for k, value in metadata.items())
        assert obvious_negative(matrix) is None
        reduced_metadata, reduced = quotient(metadata, matrix, rows)
        assert all(saved[k] == value for k, value in reduced_metadata.items())
        if len(reduced):
            margin = exact_congruence_check(reduced, saved['upper_triangular_congruence'])
            assert margin == saved['minimum_integer_dominance_margin'] > 0
        else:
            assert saved['upper_triangular_congruence'] == []
            assert saved['minimum_integer_dominance_margin'] == 0
        checked += 1
    assert checked == len(records)
    if result['all_cached_blocks_PSD_certified']:
        assert checked == 1416 and not result['unresolved_blocks'] and not result['negative_blocks']
    answer = {'status': 'exact PSD certificate replay passed', 'exact_PSD_blocks': checked,
              'all1416_cached_blocks_certified': result['all_cached_blocks_PSD_certified'],
              'optimizer_called': False, 'numerical_eigensystems_recomputed': False}
    print(json.dumps(answer, indent=2), flush=True)
    return answer


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    generate_parser = sub.add_parser('generate')
    generate_parser.add_argument('--witness', type=Path, required=True)
    generate_parser.add_argument('--certificate', type=Path, required=True)
    generate_parser.add_argument('--summary', type=Path, required=True)
    generate_parser.add_argument('--seconds', type=float, default=240)
    replay_parser = sub.add_parser('replay')
    replay_parser.add_argument('--certificate', type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'generate':
            assert 0 < args.seconds <= 300
            generate(args.witness, args.certificate, args.summary, args.seconds)
        else:
            replay(args.certificate)
