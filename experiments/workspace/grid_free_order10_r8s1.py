"""Bounded induced order-ten moment separation with eight labelled root sites.

Each nonconstant flag has one outside vertex adjacent to at least three
root sites. Such a flag is binary, by the two-common-neighbor bound.
Products use the two possible cross edges and existing catalogue children.
No optimizer or dense matrix of reduced moment forms is constructed.
"""

import argparse
from collections import Counter
from functools import lru_cache, reduce
import gzip
import hashlib
from itertools import combinations, permutations
import json
from math import gcd
from pathlib import Path
import pickle
import resource
import signal
import time

import numpy as np
import pynauty
from scipy import sparse
from threadpoolctl import threadpool_limits

import grid_free_order10_scaled as counts
from grid_free_core9_certificate import matrix_hash
from subgraph_counts import nauty


WITNESS_SHA = '62faca107e3f5a7f560c009133e2da563aa16619382b7778f7ff53aa1cd75db7'


def induced_rows(host, subset):
    return tuple(sum(((host[a] >> b) & 1) << j for j, b in enumerate(subset)) for a in subset)


def attach(rows, mask):
    n = len(rows)
    return tuple(row | (((mask >> i) & 1) << n) for i, row in enumerate(rows))+(mask,)


def transported_mask(mask, mapping):
    result = 0
    while mask:
        bit = mask & -mask
        mask ^= bit
        result |= 1 << mapping[bit.bit_length()-1]
    return result


class Builder:
    def __init__(self, data):
        self.graphs, self.levels, self.aut, self.children = data
        self.transports_checked = 0

    @lru_cache(None)
    def child_map(self, root):
        slots = dict(self.children[root])
        assert len(slots) == len(self.children[root])
        return slots

    @lru_cache(None)
    def canonical_order(self, root):
        return tuple(pynauty.canon_label(nauty(self.graphs[root])))

    def transport(self, graph, target):
        representative = self.graphs[target]
        n = len(graph)
        if tuple(graph) == tuple(representative):
            mapping = list(range(n))
        else:
            p = list(pynauty.canon_label(nauty(graph)))
            q = self.canonical_order(target)
            mapping = [0]*n
            for a, b in zip(p, q):
                mapping[a] = b
            if not all(transported_mask(graph[i], mapping) == representative[mapping[i]] for i in range(n)):
                inverse = [0]*n
                for i, value in enumerate(q):
                    inverse[value] = i
                mapping = [inverse[p[i]] for i in range(n)]
        assert sorted(mapping) == list(range(n))
        assert all(transported_mask(graph[i], mapping) == representative[mapping[i]] for i in range(n))
        self.transports_checked += 1
        return mapping

    def block(self, root, induced_counts, remove_zero_flags=True, specified_masks=None):
        rows = self.graphs[root]
        r = len(rows)
        all_masks = [mask for mask, child in self.children[root] if mask.bit_count() >= 3]
        one = self.child_map(root)
        zero_masks = [mask for mask in all_masks if induced_counts[one[mask]] == 0]
        if remove_zero_flags:
            for mask in zero_masks:
                assert all(induced_counts[child] == 0 for _, child in self.children[one[mask]])
        masks = [mask for mask in all_masks if not remove_zero_flags or mask not in set(zero_masks)]
        if specified_masks is not None:
            assert masks == specified_masks
        n = len(masks)+1
        row_index, type_index = [0], [root]
        for i, mask in enumerate(masks, 1):
            child = one[mask]
            first = i*(i+1)//2
            row_index.extend((first, first+i))
            type_index.extend((child, child))
            graph = attach(rows, mask)
            mapping = self.transport(graph, child)
            next_children = self.child_map(child)
            own = transported_mask(mask, mapping)
            edge = 1 << mapping[r]
            # Two distinct outside vertices with this mask would share at
            # least three root neighbors. Only the coincident term survives.
            assert own not in next_children and (own | edge) not in next_children
            for j, other in enumerate(masks[:i-1], 1):
                translated = transported_mask(other, mapping)
                for cross_edge in (0, edge):
                    target = next_children.get(translated | cross_edge)
                    if target is not None:
                        row_index.append(first+j)
                        type_index.append(target)
        tensor = sparse.csr_matrix((np.ones(len(row_index), dtype=np.int64),
                                    (row_index, type_index)),
                                   shape=(n*(n+1)//2, len(self.graphs)), dtype=np.int64)
        assert max(np.diff(tensor.indptr), default=0) <= 2
        return masks, tensor, {'full_flags': len(all_masks)+1, 'retained_flags': n,
                               'exact_zero_flag_masks': zero_masks if remove_zero_flags else []}


def exact_matrix(tensor, n, embeddings):
    bound = 2*max(abs(int(value)) for value in embeddings)
    assert bound < (1 << 63)
    values = tensor@np.array(embeddings, dtype=np.int64)
    matrix = np.zeros((n, n), dtype=np.int64)
    lower = np.tril_indices(n)
    matrix[lower] = values
    matrix[(lower[1], lower[0])] = values
    return matrix, bound


def rook_controls(builder):
    host = tuple(sum(1 << j for j in range(9) if i != j and
                     (i//3 == j//3 or i % 3 == j % 3)) for i in range(9))
    assert all((host[i] & host[j]).bit_count()+((host[i] >> j) & 1) == 2
               for i, j in combinations(range(9), 2))
    ids = {(len(graph), pynauty.certificate(nauty(graph))): i
           for i, graph in enumerate(builder.graphs) if len(graph) <= 9}
    values = [0]*len(builder.graphs)
    for n in range(10):
        for subset in combinations(range(9), n):
            graph = induced_rows(host, subset)
            values[ids[n, pynauty.certificate(nauty(graph))]] += 1
    embeddings = [a*c for a, c in zip(builder.aut, values)]
    reports = []
    for omitted in ((0, 1), (0, 4)):
        chosen = tuple(i for i in range(9) if i not in omitted)
        graph = induced_rows(host, chosen)
        root = ids[7, pynauty.certificate(nauty(graph))]
        rows = builder.graphs[root]
        masks, tensor, metadata = builder.block(root, values, remove_zero_flags=False)
        matrix, _ = exact_matrix(tensor, len(masks)+1, embeddings)
        direct = np.zeros_like(matrix)
        location = {mask: i+1 for i, mask in enumerate(masks)}
        matches = 0
        for image in permutations(range(9), 7):
            if any(((rows[i] >> j) & 1) != ((host[image[i]] >> image[j]) & 1)
                   for i in range(7) for j in range(i)):
                continue
            vector = [1]+[0]*len(masks)
            for vertex in set(range(9))-set(image):
                mask = sum(((host[vertex] >> image[j]) & 1) << j for j in range(7))
                if mask in location:
                    vector[location[mask]] += 1
            assert all(value in (0, 1) for value in vector)
            v = np.array(vector, dtype=np.int64)
            direct += np.outer(v, v)
            matches += 1
        assert np.array_equal(matrix, direct)
        reports.append({'omitted_pair': list(omitted), 'root_type': root,
                        'root_embeddings': matches, 'flags': len(masks)+1,
                        'exact_matrix_sha256': matrix_hash(matrix), 'passed': True})
    return {'status': 'direct R9 rooted-product controls passed', 'cases': reports}, values


def negative_direction(matrix):
    scales = np.sqrt(np.asarray(np.diag(matrix), dtype=float))
    assert np.all(scales > 0)
    normalized = matrix/scales[:, None]/scales[None, :]
    eigenvalues, eigenvectors = np.linalg.eigh(normalized)
    smallest = float(eigenvalues[0])
    if smallest >= -1e-8:
        return None, smallest
    direction = eigenvectors[:, 0]/scales
    direction /= max(abs(direction))
    for power in (8, 12, 20, 28, 36):
        vector = [int(round(value*(2**power))) for value in direction]
        divisor = reduce(gcd, [abs(v) for v in vector], 0)
        if not divisor:
            continue
        vector = [v//divisor for v in vector]
        v = np.array(vector, dtype=object)
        value = int(v@matrix.astype(object)@v)
        if value < 0:
            return {'integer_vector': vector, 'integer_quadratic_value': value}, smallest
    return None, smallest


def induced_form(tensor, vector, aut):
    weights = Counter()
    row = 0
    for i in range(len(vector)):
        for j in range(i+1):
            coefficient = vector[i]*vector[j]*(1 if i == j else 2)
            if coefficient:
                for k in range(tensor.indptr[row], tensor.indptr[row+1]):
                    index = int(tensor.indices[k])
                    weights[index] += coefficient*int(tensor.data[k])*aut[index]
            row += 1
    terms = [[index, value] for index, value in sorted(weights.items()) if value]
    divisor = reduce(gcd, [abs(value) for _, value in terms], 0)
    assert divisor > 0
    return [[index, value//divisor] for index, value in terms], divisor


def reduced_form(terms, raw, scale):
    indices = [index for index, value in terms]
    weights = np.array([value for index, value in terms], dtype=object)
    coefficient = weights@raw[indices].astype(object)
    assert not np.any(coefficient % scale)
    coefficient = [int(value)//scale for value in coefficient]
    divisor = reduce(gcd, [abs(value) for value in coefficient], 0)
    assert divisor > 0
    return [value//divisor for value in coefficient], divisor


def write_cache(path, blocks, witness_sha, catalogue_sha):
    record = {'format': 1, 'root_order': 8, 'outside_flag_size': 1, 'induced': True,
              'zero_flag_rows_removed_at_witness': True, 'witness_sha256': witness_sha,
              'catalogue_sha256': catalogue_sha, 'blocks': blocks}
    temporary = path.with_name(path.name+'.pending')
    temporary.write_bytes(gzip.compress(pickle.dumps(record, protocol=5), mtime=0))
    temporary.replace(path)


def generate(catalogue, reduced, witness, output, block_cache, seconds):
    started = time.monotonic()
    assert counts.digest(witness) == WITNESS_SHA
    saved = json.loads(witness.read_text())
    point, induced_counts = saved['rounded_core_values'], saved['induced_counts']
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    assert [len(level) for level in data[1]] == [1, 1, 2, 4, 9, 21, 62, 208, 916, 5311, 42430]
    assert len(induced_counts) == len(data[0]) == 48965
    assert all(type(value) is int and value >= 0 for value in induced_counts)
    embeddings = [a*c for a, c in zip(data[2], induced_counts)]
    builder = Builder(data)
    controls, rook_counts = rook_controls(builder)
    result = {'source_sha256': counts.digest(Path(__file__)),
              'catalogue_path': str(catalogue), 'catalogue_sha256': counts.digest(catalogue),
              'reduced_cache_path': str(reduced), 'reduced_cache_sha256': counts.digest(reduced),
              'witness_path': str(witness), 'witness_sha256': WITNESS_SHA,
              'root_order': 8, 'outside_flag_size': 1, 'induced': True,
              'maximum_generation_seconds': seconds, 'optimizer_called': False,
              'direct_rook_controls': controls, 'root_count': 916,
              'zero_roots_skipped': [], 'blocks': [], 'negative_blocks': [],
              'unique_core_cuts': [], 'unconfirmed_numeric_negatives': [],
              'PSD_feasibility_certified': False}
    raw = None
    generated_blocks = []
    known = {}

    def deadline(_signum, _frame):
        raise TimeoutError('bounded order-ten moment separation limit')

    old_handler = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, seconds-(time.monotonic()-started)))
    timed_out = False
    try:
        for root in data[1][8]:
            if induced_counts[root] == 0:
                assert all(induced_counts[child] == 0 for _, child in data[3][root])
                result['zero_roots_skipped'].append(root)
                continue
            masks, tensor, metadata = builder.block(root, induced_counts)
            matrix, bound = exact_matrix(tensor, len(masks)+1, embeddings)
            generated_blocks.append((root, masks, tensor))
            negative, smallest = negative_direction(matrix)
            record = {'root_type': root, 'flag_masks': masks, **metadata,
                      'lower_entries': int(tensor.shape[0]), 'tensor_nonzeros': int(tensor.nnz),
                      'integer_matrix_sha256': matrix_hash(matrix),
                      'sparse_product_absolute_bound': bound,
                      'smallest_normalized_numeric_eigenvalue': smallest}
            if negative:
                terms, form_gcd = induced_form(tensor, negative['integer_vector'], data[2])
                value = sum(coefficient*induced_counts[index] for index, coefficient in terms)
                assert value*form_gcd == negative['integer_quadratic_value'] < 0
                control = sum(coefficient*rook_counts[index] for index, coefficient in terms)
                assert control >= 0
                if raw is None:
                    fresh_data, cores, scale, raw = counts.load_reduced(reduced)
                    assert fresh_data[0] == data[0] and fresh_data[2] == data[2]
                    assert len(cores) == 549
                core, core_gcd = reduced_form(terms, raw, scale)
                core_value = sum(a*x for a, x in zip(core, point))
                assert core_value*core_gcd == value < 0
                key = tuple(core)
                if key not in known:
                    known[key] = len(result['unique_core_cuts'])
                    result['unique_core_cuts'].append({'coefficients': core,
                        'exact_value_at_witness': core_value,
                        'new_coordinate_support': [j for j in range(58, 550) if core[j]]})
                result['negative_blocks'].append({**record, **negative,
                    'primitive_induced_count_form': terms, 'induced_form_gcd': form_gcd,
                    'primitive_induced_value': value, 'direct_rook_control_value': control,
                    'core_form_gcd': core_gcd, 'core_cut_index': known[key]})
            elif smallest < -1e-8:
                result['unconfirmed_numeric_negatives'].append(record)
            result['blocks'].append(record)
            if len(result['blocks']) % 64 == 0:
                counts.save(output, result)
                print(json.dumps({'positive_roots_scanned': len(result['blocks']),
                    'exact_negative_blocks': len(result['negative_blocks']),
                    'unique_core_cuts': len(result['unique_core_cuts'])}), flush=True)
    except TimeoutError:
        timed_out = True
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
    write_cache(block_cache, generated_blocks, WITNESS_SHA, result['catalogue_sha256'])
    result.update(status='exact order-ten moment violations found' if result['negative_blocks'] else
                         'no exact violation in scanned blocks; PSD not certified',
                  timed_out=timed_out, completed_root_scan=(len(result['blocks'])+len(result['zero_roots_skipped']) == 916),
                  positive_roots_scanned=len(result['blocks']), exact_negative_blocks=len(result['negative_blocks']),
                  unique_core_cut_count=len(result['unique_core_cuts']),
                  explicit_transports_checked=builder.transports_checked,
                  generated_cache_path=str(block_cache), generated_cache_sha256=counts.digest(block_cache),
                  generated_cache_bytes=block_cache.stat().st_size,
                  lower_entries=sum(row['lower_entries'] for row in result['blocks']),
                  tensor_nonzeros=sum(row['tensor_nonzeros'] for row in result['blocks']),
                  seconds=time.monotonic()-started,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    counts.save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key not in
                     ('blocks', 'negative_blocks', 'unique_core_cuts', 'zero_roots_skipped',
                      'unconfirmed_numeric_negatives')}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, required=True)
    parser.add_argument('--reduced', type=Path, required=True)
    parser.add_argument('--witness', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--block-cache', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=180)
    args = parser.parse_args()
    assert 0 < args.seconds <= 180
    with threadpool_limits(limits=1):
        generate(args.catalogue, args.reduced, args.witness, args.output, args.block_cache, args.seconds)
