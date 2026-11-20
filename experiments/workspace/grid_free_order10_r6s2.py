"""Exact domains and product rules for induced six-root, two-outside flags.

Outside vertices have degree at least three in their whole flag, including
their mutual edge. They need not have three root neighbors. Two-outside
flags can therefore take the value two. Products include every consistent
overlap and every unspecified cross edge; no binary diagonal shortcut is
used. This module's preparation builds only domains and small R9 controls.
"""

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import combinations, permutations, product
import json
from pathlib import Path
import pickle
import resource
import time

import numpy as np
import pynauty
from scipy import sparse
from threadpoolctl import threadpool_limits

import flag_moments
import grid_free_order10_r8s1 as transport_tools
import grid_free_order10_scaled as counts
from grid_free_core9_certificate import matrix_hash
from subgraph_counts import nauty


CATALOGUE_SHA = '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'
WITNESS_SHA = '3f75ad72024829c91995f3b22d50f89cd709af6b6d9d3b0806c5ee05f3097326'
TRANSPORT_SOURCE_SHA = '77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469'


def caps(rows):
    return all((rows[a] & rows[b]).bit_count()+((rows[a] >> b) & 1) <= 2
               for a in range(len(rows)) for b in range(a))


def relabel(rows, order):
    return tuple(sum(((rows[a] >> b) & 1) << j for j, b in enumerate(order)) for a in order)


@lru_cache(None)
def overlaps(left_size, right_size):
    """right-position -> left-position or None, with every injection once."""
    answer = []
    for count in range(min(left_size, right_size)+1):
        for shared in combinations(range(right_size), count):
            for images in permutations(range(left_size), count):
                mapping = dict(zip(shared, images))
                answer.append(tuple(mapping.get(j) for j in range(right_size)))
    return tuple(answer)


class Builder:
    def __init__(self, data):
        self.data = data
        self.graphs, self.levels, self.aut, self.children = data
        self.transport_engine = transport_tools.Builder(data)
        self.entries_built = 0
        self.overlap_cases_used = Counter()

    @lru_cache(maxsize=150000)
    def _normalized_transport(self, rows, target):
        return tuple(self.transport_engine.transport(rows, target))

    def prefix_transport(self, rows, target, root_size):
        """Share transports across permutations of at most three free sites."""
        assert len(rows)-root_size <= 3
        root_mask = (1 << root_size)-1
        groups = defaultdict(list)
        for i in range(root_size, len(rows)):
            groups[rows[i] & root_mask].append(i)
        choices = [tuple(permutations(groups[key])) for key in sorted(groups)]
        best = None
        best_order = None
        for parts in product(*choices):
            order = tuple(range(root_size))+tuple(i for part in parts for i in part)
            current = relabel(rows, order)
            if best is None or current < best:
                best, best_order = current, order
        assert best is not None
        normal_to_target = self._normalized_transport(best, target)
        result = [None]*len(rows)
        for normal, original in enumerate(best_order):
            result[original] = normal_to_target[normal]
        assert sorted(result) == list(range(len(rows)))
        return tuple(result)

    @lru_cache(None)
    def flags(self, root):
        rows = self.graphs[root]
        r = len(rows)
        one = self.transport_engine.child_map(root)
        flags = [{'size': 0, 'masks': (), 'edge': 0, 'rows': tuple(rows),
                  'type': root, 'transport': tuple(range(r))}]
        for mask, target in sorted(one.items()):
            if mask.bit_count() >= 3:
                graph = transport_tools.attach(rows, mask)
                flags.append({'size': 1, 'masks': (mask,), 'edge': 0, 'rows': graph,
                              'type': target, 'transport': self.prefix_transport(graph, target, r)})
        for left, first_type in sorted(one.items()):
            if left.bit_count() < 2:
                continue
            first = transport_tools.attach(rows, left)
            mapping = self.prefix_transport(first, first_type, r)
            next_slots = self.transport_engine.child_map(first_type)
            for right in range(left+1, 1 << r):
                for edge in (0, 1):
                    if min(left.bit_count(), right.bit_count())+edge < 3:
                        continue
                    mask = right | (edge << r)
                    translated = transport_tools.transported_mask(mask, mapping)
                    target = next_slots.get(translated)
                    if target is None:
                        continue
                    graph = transport_tools.attach(first, mask)
                    assert caps(graph)
                    flags.append({'size': 2, 'masks': (left, right), 'edge': edge, 'rows': graph,
                                  'type': target, 'transport': self.prefix_transport(graph, target, r)})
        assert len({flag['rows'] for flag in flags}) == len(flags)
        assert all(all(row.bit_count() >= 3 for row in flag['rows'][r:]) for flag in flags)
        return tuple(flags)

    def product_form(self, root, left, right, with_overlap_counts=False):
        """Nonnegative integer coefficients in labelled induced embeddings."""
        r = len(self.graphs[root])
        s, t = left['size'], right['size']
        answer = Counter()
        by_overlap = Counter()
        for mapping in overlaps(s, t):
            q = sum(value is not None for value in mapping)
            if any(right['masks'][j] != left['masks'][i]
                   for j, i in enumerate(mapping) if i is not None):
                continue
            if q == 2 and right['edge'] != left['edge']:
                continue
            assigned = {j: r+i for j, i in enumerate(mapping) if i is not None}
            shared_left = set(assigned.values())
            unknown_left = [i for i in range(r, r+s) if i not in shared_left]
            fresh = [j for j, i in enumerate(mapping) if i is None]

            def extend(position, rows, current_type, transport, locations):
                if position == len(fresh):
                    answer[current_type] += 1
                    by_overlap[q] += 1
                    return
                j = fresh[position]
                prescribed = right['masks'][j]
                if right['edge']:
                    for other, location in locations.items():
                        assert other != j
                        prescribed |= 1 << location
                slots = self.transport_engine.child_map(current_type)
                for bits in range(1 << len(unknown_left)):
                    mask = prescribed
                    for i, location in enumerate(unknown_left):
                        if bits >> i & 1:
                            mask |= 1 << location
                    translated = transport_tools.transported_mask(mask, transport)
                    target = slots.get(translated)
                    if target is None:
                        continue
                    if position+1 == len(fresh):
                        answer[target] += 1
                        by_overlap[q] += 1
                    else:
                        graph = transport_tools.attach(rows, mask)
                        new_transport = self.prefix_transport(graph, target, r)
                        new_locations = dict(locations)
                        new_locations[j] = len(rows)
                        extend(position+1, graph, target, new_transport, new_locations)

            extend(0, left['rows'], left['type'], left['transport'], assigned)
        self.entries_built += 1
        self.overlap_cases_used.update(by_overlap)
        if with_overlap_counts:
            return answer, by_overlap
        return answer

    def block(self, root):
        flags = self.flags(root)
        rr, cc, vv = [], [], []
        for i, left in enumerate(flags):
            for j, right in enumerate(flags[:i+1]):
                form = self.product_form(root, left, right)
                row = i*(i+1)//2+j
                for index, coefficient in sorted(form.items()):
                    assert coefficient > 0
                    rr.append(row)
                    cc.append(index)
                    vv.append(coefficient)
        tensor = sparse.csr_matrix((np.array(vv, dtype=np.int64), (rr, cc)),
                                   shape=(len(flags)*(len(flags)+1)//2, len(self.graphs)), dtype=np.int64)
        return flags, tensor


def exact_matrix(tensor, order, embeddings):
    values = [sum(int(tensor.data[k])*embeddings[int(tensor.indices[k])]
                  for k in range(tensor.indptr[i], tensor.indptr[i+1]))
              for i in range(tensor.shape[0])]
    matrix = np.empty((order, order), dtype=object)
    lower = np.tril_indices(order)
    matrix[lower] = values
    matrix[(lower[1], lower[0])] = values
    return matrix


def rook_controls(builder):
    host = tuple(sum(1 << j for j in range(9) if i != j and
                     (i//3 == j//3 or i % 3 == j % 3)) for i in range(9))
    ids = {(len(rows), pynauty.certificate(nauty(rows))): i
           for i, rows in enumerate(builder.graphs) if len(rows) <= 9}
    induced = [0]*len(builder.graphs)
    for n in range(10):
        for subset in combinations(range(9), n):
            rows = relabel(host, subset)
            induced[ids[n, pynauty.certificate(nauty(rows))]] += 1
    embeddings = [a*c for a, c in zip(builder.aut, induced)]
    controls = []
    for subset in ((0, 4, 8), (0, 1, 5), (0, 1, 2, 3, 4, 5)):
        root_rows = relabel(host, subset)
        root = ids[len(subset), pynauty.certificate(nauty(root_rows))]
        rows = builder.graphs[root]
        r = len(rows)
        flags, tensor = builder.block(root)
        matrix = exact_matrix(tensor, len(flags), embeddings)
        direct = np.zeros((len(flags), len(flags)), dtype=object)
        seen_embeddings = 0
        maximum_flag_value = 0
        nonbinary_diagonal_examples = []
        for image in permutations(range(9), r):
            if any(((rows[i] >> j) & 1) != ((host[image[i]] >> image[j]) & 1)
                   for i in range(r) for j in range(i)):
                continue
            classes = defaultdict(list)
            for vertex in set(range(9))-set(image):
                mask = sum(((host[vertex] >> image[j]) & 1) << j for j in range(r))
                classes[mask].append(vertex)
            vector = [1]
            for flag in flags[1:]:
                if flag['size'] == 1:
                    value = len(classes[flag['masks'][0]])
                    assert value <= 1
                else:
                    a, b = flag['masks']
                    value = sum(((host[x] >> y) & 1) == flag['edge']
                                for x in classes[a] for y in classes[b])
                    assert value <= 2
                    if min(a.bit_count(), b.bit_count()) >= 3:
                        assert value <= 1
                vector.append(value)
                maximum_flag_value = max(maximum_flag_value, value)
            v = np.array(vector, dtype=object)
            direct += np.outer(v, v)
            seen_embeddings += 1
        assert np.array_equal(matrix, direct)
        assert seen_embeddings == embeddings[root]
        for index in range(1, len(flags)):
            if matrix[index, index] > matrix[0, index]:
                assert flags[index]['size'] == 2
                form, by_overlap = builder.product_form(root, flags[index], flags[index], True)
                nonbinary_diagonal_examples.append({'flag_index': index, 'masks': list(flags[index]['masks']),
                    'edge': flags[index]['edge'], 'first_moment': int(matrix[0, index]),
                    'second_moment': int(matrix[index, index]),
                    'labelled_embedding_form': sorted(form.items()),
                    'admissible_completion_counts_by_overlap': dict(by_overlap)})
        controls.append({'host_subset_for_root': list(subset), 'root_type': root, 'root_order': r,
                         'flag_count': len(flags), 'root_embeddings': seen_embeddings,
                         'maximum_flag_value': maximum_flag_value,
                         'nonbinary_diagonal_examples': nonbinary_diagonal_examples,
                         'exact_matrix_sha256': matrix_hash(matrix), 'passed': True})
    assert controls[0]['maximum_flag_value'] == 2
    assert controls[0]['nonbinary_diagonal_examples']
    assert controls[-1]['root_order'] == 6
    return {'status': 'direct R9 overlap-product controls PASS', 'cases': controls}


def prepare(catalogue, witness, output, limit=512):
    assert limit == 512
    started = time.monotonic()
    assert counts.digest(catalogue) == CATALOGUE_SHA
    assert counts.digest(witness) == WITNESS_SHA
    assert counts.digest(Path(transport_tools.__file__)) == TRANSPORT_SOURCE_SHA
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    assert len(data[0]) == 48965 and len(data[1][6]) == 62
    point = json.loads(witness.read_text())
    assert point['negative_induced_rows'] == point['nonintegral_induced_rows'] == 0
    assert point['original_equations_checked'] == 180445
    builder = Builder(data)
    records = []
    for root in data[1][6]:
        flags = builder.flags(root)
        old_flags = flag_moments.flags(data[0][root], 2)
        assert {flag['rows'] for flag in flags} == set(old_flags)
        assert len(flags) == len(old_flags)
        strict = sum(flag['size'] == 0 or min(mask.bit_count() for mask in flag['masks']) >= 3
                     for flag in flags)
        selected = 1 < len(flags) <= limit
        record = {'root_type': root, 'root_rows': list(data[0][root]),
                  'root_count_at_witness': point['induced_counts'][root],
                  'flags': len(flags), 'single_outside_flags': sum(f['size'] == 1 for f in flags),
                  'two_outside_flags': sum(f['size'] == 2 for f in flags),
                  'both_root_degree_at_least_three_subfamily_flags': strict,
                  'two_flags_using_a_root_degree_two_vertex': sum(f['size'] == 2 and
                       min(mask.bit_count() for mask in f['masks']) == 2 for f in flags),
                  'two_flags_with_both_root_degrees_two': sum(f['size'] == 2 and
                       all(mask.bit_count() == 2 for mask in f['masks']) for f in flags),
                  'lower_entries': len(flags)*(len(flags)+1)//2,
                  'selected_by_fixed_size_limit': selected,
                  'domain_agrees_with_existing_full_degree_rule': True}
        records.append(record)
    selected = [record for record in records if record['selected_by_fixed_size_limit']]
    control = rook_controls(builder)
    overlap_control = {f'{s},{t}': [sum(sum(v is not None for v in row) == q for row in overlaps(s,t))
                                    for q in range(min(s,t)+1)]
                       for s in range(3) for t in range(3)}
    assert overlap_control['2,2'] == [1, 4, 2]
    result = {'status': 'r6s2 exact domains and small controls prepared; no large blocks generated',
              'source_sha256': counts.digest(Path(__file__)),
              'catalogue_path': str(catalogue), 'catalogue_sha256': CATALOGUE_SHA,
              'witness_path': str(witness), 'witness_sha256': WITNESS_SHA,
              'transport_source_sha256': TRANSPORT_SOURCE_SHA,
              'existing_flag_source_sha256': counts.digest(Path(flag_moments.__file__)),
              'root_order': 6, 'maximum_free_vertices_per_flag': 2, 'maximum_product_order': 10,
              'flag_rule': 'each free vertex has degree at least3 inside its whole flag, including the mutual edge',
              'free_labels_quotiented': 'one representative under permutations of only the free labels',
              'variables_count_labelled_embeddings': True, 'binary_diagonal_shortcut_used': False,
              'all_62_root_domains': records, 'root_count': len(records),
              'nontrivial_root_blocks': sum(record['flags'] > 1 for record in records),
              'maximum_full_flag_count': max(record['flags'] for record in records),
              'full_family_lower_entries': sum(record['lower_entries'] for record in records),
              'strict_root_degree_subfamily_maximum': max(record['both_root_degree_at_least_three_subfamily_flags']
                                                        for record in records),
              'fixed_size_limit': limit, 'selected_root_types': [record['root_type'] for record in selected],
              'selected_blocks': len(selected), 'selected_lower_entries': sum(record['lower_entries'] for record in selected),
              'selected_maximum_flags': max(record['flags'] for record in selected),
              'selected_zero_count_roots': [record['root_type'] for record in selected if not record['root_count_at_witness']],
              'point_dependent_flag_or_root_pruning': False,
              'oversize_root_types': [record['root_type'] for record in records if record['flags'] > limit],
              'overlap_injection_counts': overlap_control, 'direct_rook_controls': control,
              'small_control_moment_entries_built': builder.entries_built,
              'verified_transports': builder.transport_engine.transports_checked,
              'optimizer_called': False, 'dense_reduction_loaded': False,
              'large_family_generation_or_scan_started': False,
              'seconds': time.monotonic()-started,
              'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    counts.save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key != 'all_62_root_domains'}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, required=True)
    parser.add_argument('--witness', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    with threadpool_limits(limits=1):
        args = parser.parse_args()
        prepare(args.catalogue, args.witness, args.output)
