"""Exact induced products for the frozen r4s3 and r2s4 flag domains.

All flags and product variables count labelled embeddings. Free-label
stabilizers are checked but never divided out. Preparation builds only
the two tiny r2s4 blocks and small cold controls, not the full r4s3 cache.
"""

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import combinations, permutations, product
import json
from math import factorial
from pathlib import Path
import pickle
import resource
import time

import numpy as np
import pynauty
from scipy import sparse
from threadpoolctl import threadpool_limits

import grid_free_order10_higher_flags_domains as domains
import grid_free_order10_r6s2_independent_audit as oracle
import grid_free_order10_r8s1 as transports
import grid_free_order10_scaled as files
from subgraph_counts import nauty


DOMAIN_SOURCE_SHA = 'a2fb1b18940423cdd6d36bce91bac54cbe3eecc8622c2418642b8a9559c8c6f0'
TRANSPORT_SOURCE_SHA = '77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469'
ORACLE_SOURCE_SHA = '46bbbf5521383fc14925644e1dcb82ebeca99094b5726b8f23e3d774aa6f643f'


@lru_cache(None)
def overlap_maps(left_masks, right_masks):
    """Every partial injection matching root masks, with no orbit quotient."""
    answer = []

    def visit(j, used, image):
        if j == len(right_masks):
            answer.append(tuple(image))
            return
        image.append(None)
        visit(j+1, used, image)
        image.pop()
        for i, mask in enumerate(left_masks):
            if i not in used and mask == right_masks[j]:
                image.append(i)
                visit(j+1, used | {i}, image)
                image.pop()

    visit(0, set(), [])
    histogram = Counter(sum(value is not None for value in mapping) for mapping in answer)
    expected = domains.mask_overlap_counts(left_masks, right_masks)
    assert [histogram[q] for q in range(len(expected))] == list(expected)
    assert sum(histogram.values()) == len(answer) == len(set(answer))
    return tuple(answer)


def shared_compatible(r, left, right, mapping):
    shared = [(j, i) for j, i in enumerate(mapping) if i is not None]
    return all(((left['rows'][r+i] >> (r+k)) & 1) ==
               ((right['rows'][r+j] >> (r+ell)) & 1)
               for (j, i), (ell, k) in combinations(shared, 2))


class Builder:
    def __init__(self, data, prepared):
        self.data = data
        self.graphs, self.levels, self.aut, self.children = data
        self.engine = transports.Builder(data)
        self.records = {record['root_type']: record for family in prepared['families']
                        for record in family['records']}
        assert set(self.records) == set(self.levels[2]) | set(self.levels[4])
        self.product_entries = 0
        self.accepted_by_overlap = Counter()
        self.raw_transport_prefixes = 0
        self.normalized_transport_prefixes = 0

    @lru_cache(maxsize=150000)
    def checked_transport(self, graph, target):
        return tuple(self.engine.transport(graph, target))

    @lru_cache(maxsize=125000)
    def prefix_transport(self, graph, target, r):
        """Relabel only to share transport caches; never quotient products."""
        groups = domains.mask_groups(graph, r)
        possibilities = 1
        for group in groups:
            possibilities *= factorial(len(group))
        if possibilities > 16:
            self.raw_transport_prefixes += 1
            return self.checked_transport(graph, target)
        best, order = None, None
        for parts in product(*(permutations(group) for group in groups)):
            candidate_order = tuple(range(r))+tuple(i for part in parts for i in part)
            candidate = domains.relabel(graph, candidate_order)
            if best is None or candidate < best:
                best, order = candidate, candidate_order
        normal_to_target = self.checked_transport(best, target)
        actual_to_target = [0]*len(graph)
        for new, old in enumerate(order):
            actual_to_target[old] = normal_to_target[new]
        representative = self.graphs[target]
        assert sorted(actual_to_target) == list(range(len(graph)))
        assert all(transports.transported_mask(graph[i], actual_to_target) == representative[actual_to_target[i]]
                   for i in range(len(graph)))
        self.normalized_transport_prefixes += 1
        return tuple(actual_to_target)

    @lru_cache(None)
    def flags(self, root):
        r = len(self.graphs[root])
        answer = []
        record = self.records[root]
        assert list(self.graphs[root]) == record['root_rows']
        for item in record['flag_domain']:
            rows, masks = tuple(item['rows']), tuple(item['root_masks'])
            assert len(rows) == r+item['size'] and len(masks) == item['size']
            assert tuple(row & ((1 << r)-1) for row in rows[r:]) == masks
            assert domains.caps(rows) and all(row.bit_count() >= 3 for row in rows[r:])
            flag = {'size': item['size'], 'rows': rows, 'masks': masks, 'type': item['type'],
                    'stabilizer': item['root_fixing_free_stabilizer'],
                    'transport': self.prefix_transport(rows, item['type'], r)}
            full = [mapping for mapping in overlap_maps(masks, masks)
                    if all(i is not None for i in mapping) and shared_compatible(r, flag, flag, mapping)]
            assert len(full) == flag['stabilizer']
            answer.append(flag)
        assert len(answer) == record['flags']
        assert len({flag['rows'] for flag in answer}) == len(answer)
        return tuple(answer)

    def product_form(self, root, left, right, return_overlap_counts=False):
        r = len(self.graphs[root])
        a, b = left['size'], right['size']
        answer, by_overlap = Counter(), Counter()
        for mapping in overlap_maps(left['masks'], right['masks']):
            if not shared_compatible(r, left, right, mapping):
                continue
            assigned = {j: r+i for j, i in enumerate(mapping) if i is not None}
            shared_left = set(assigned.values())
            unknown_left = [i for i in range(r, r+a) if i not in shared_left]
            fresh = [j for j, i in enumerate(mapping) if i is None]
            q = len(assigned)

            def extend(position, graph, current_type, transport, locations):
                if position == len(fresh):
                    answer[current_type] += 1
                    by_overlap[q] += 1
                    return
                j = fresh[position]
                prescribed = right['masks'][j]
                for other, location in locations.items():
                    if right['rows'][r+j] >> (r+other) & 1:
                        prescribed |= 1 << location
                slots = self.engine.child_map(current_type)
                for bits in range(1 << len(unknown_left)):
                    mask = prescribed
                    for bit, location in enumerate(unknown_left):
                        if bits >> bit & 1:
                            mask |= 1 << location
                    translated = transports.transported_mask(mask, transport)
                    target = slots.get(translated)
                    if target is None:
                        continue
                    if position+1 == len(fresh):
                        answer[target] += 1
                        by_overlap[q] += 1
                    else:
                        extended = transports.attach(graph, mask)
                        new_locations = dict(locations)
                        new_locations[j] = len(graph)
                        new_transport = self.prefix_transport(extended, target, r)
                        extend(position+1, extended, target, new_transport, new_locations)

            extend(0, left['rows'], left['type'], left['transport'], assigned)
        bound = domains.upper_choices(a, b, domains.mask_overlap_counts(left['masks'], right['masks']))
        assert sum(answer.values()) <= bound
        self.product_entries += 1
        self.accepted_by_overlap.update(by_overlap)
        if return_overlap_counts:
            return answer, by_overlap
        return answer

    def block(self, root):
        flags = self.flags(root)
        rr, cc, vv = [], [], []
        for i, left in enumerate(flags):
            for j, right in enumerate(flags[:i+1]):
                terms = self.product_form(root, left, right)
                for index, value in sorted(terms.items()):
                    assert value > 0
                    rr.append(i*(i+1)//2+j)
                    cc.append(index)
                    vv.append(value)
        tensor = sparse.csr_matrix((np.array(vv, dtype=np.int64), (rr, cc)),
                                   shape=(len(flags)*(len(flags)+1)//2, len(self.graphs)), dtype=np.int64)
        return flags, tensor


def tensor_row(tensor, i, j):
    a, b = max(i, j), min(i, j)
    row = a*(a+1)//2+b
    return {int(tensor.indices[k]): int(tensor.data[k])
            for k in range(tensor.indptr[row], tensor.indptr[row+1])}


def sample_positions(flags):
    selected = {0}
    for size in (1, 2, 3, 4):
        choices = [i for i, flag in enumerate(flags) if flag['size'] == size]
        if choices:
            selected.update((choices[0], choices[-1]))
    for condition in (lambda f: f['size'] and min(mask.bit_count() for mask in f['masks']) == 1,
                      lambda f: f['stabilizer'] > 1,
                      lambda f: f['size'] == 3 and sum((row >> (len(f['rows'])-3)).bit_count()
                                                      for row in f['rows'][-3:]) == 6):
        choices = [i for i, flag in enumerate(flags) if condition(flag)]
        if choices:
            selected.add(choices[0])
    return sorted(selected)


def rook_controls(builder, ids, roots):
    host = tuple(sum(1 << j for j in range(9) if i != j and
                     (i//3 == j//3 or i % 3 == j % 3)) for i in range(9))
    induced = [0]*len(builder.graphs)
    for n in range(10):
        for subset in combinations(range(9), n):
            rows = domains.relabel(host, subset)
            induced[ids[oracle.canonical(rows)]] += 1
    embeddings = [value*aut for value, aut in zip(induced, builder.aut)]
    reports = []
    for root in roots:
        r = len(builder.graphs[root])
        flags, tensor = builder.block(root)
        direct = np.zeros((len(flags), len(flags)), dtype=object)
        root_embeddings, largest = 0, 0
        for image in permutations(range(9), r):
            if domains.relabel(host, image) != tuple(builder.graphs[root]):
                continue
            root_embeddings += 1
            classes = defaultdict(list)
            for vertex in set(range(9))-set(image):
                mask = sum(((host[vertex] >> image[j]) & 1) << j for j in range(r))
                classes[mask].append(vertex)
            vector = []
            for flag in flags:
                value = 0
                for free in product(*(classes[mask] for mask in flag['masks'])):
                    if len(set(free)) != len(free):
                        continue
                    if all(((host[free[a]] >> free[b]) & 1) == ((flag['rows'][r+a] >> (r+b)) & 1)
                           for a in range(flag['size']) for b in range(a)):
                        value += 1
                assert value % flag['stabilizer'] == 0
                vector.append(value)
            largest = max(largest, max(vector))
            v = np.array(vector, dtype=object)
            direct += np.outer(v, v)
        assert root_embeddings > 0
        matrix = np.empty_like(direct)
        for i in range(len(flags)):
            for j in range(i+1):
                value = sum(coefficient*embeddings[index] for index, coefficient in tensor_row(tensor,i,j).items())
                matrix[i,j] = matrix[j,i] = value
        assert np.array_equal(matrix, direct)
        reports.append({'root_type': root, 'flags': len(flags), 'root_embeddings': root_embeddings,
                        'maximum_labelled_flag_value': largest, 'first_moments': [int(v) for v in matrix[0]],
                        'second_moments': [int(matrix[i,i]) for i in range(len(flags))],
                        'all_matrix_entries_match_direct_host_counts': True})
    return reports


def prepare(domain_path, output):
    started = time.monotonic()
    assert files.digest(Path(domains.__file__)) == DOMAIN_SOURCE_SHA
    assert files.digest(Path(transports.__file__)) == TRANSPORT_SOURCE_SHA
    assert files.digest(Path(oracle.__file__)) == ORACLE_SOURCE_SHA
    prepared = json.loads(domain_path.read_text())
    assert prepared['source_sha256'] == DOMAIN_SOURCE_SHA
    catalogue = Path(prepared['catalogue_path'])
    assert files.digest(catalogue) == prepared['catalogue_sha256'] == domains.CATALOGUE_SHA
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    builder = Builder(data, prepared)
    ids = {oracle.canonical(tuple(rows)): i for i, rows in enumerate(data[0])}
    entries, ten_terms, full_overlap_checks = 0, 0, 0
    tiny_blocks = []
    for root in sorted(builder.records):
        flags = builder.flags(root)
        r = len(data[0][root])
        for flag in flags:
            full = [mapping for mapping in overlap_maps(flag['masks'], flag['masks'])
                    if all(i is not None for i in mapping) and shared_compatible(r, flag, flag, mapping)]
            assert len(full) == flag['stabilizer']
            full_overlap_checks += 1
        positions = list(range(len(flags))) if r == 2 else sample_positions(flags)
        symbolic = []
        for i, left_index in enumerate(positions):
            for right_index in positions[:i+1]:
                left, right = flags[left_index], flags[right_index]
                expected, by_q = oracle.direct_product(r, left['rows'], right['rows'], ids)
                forward, forward_q = builder.product_form(root,left,right,True)
                backward, backward_q = builder.product_form(root,right,left,True)
                assert expected == forward == backward
                assert by_q == forward_q == backward_q
                if left_index == right_index:
                    assert by_q[left['size']] == left['stabilizer']
                if right_index == 0:
                    assert expected == {left['type']: 1}
                entries += 1
                ten_terms += any(len(data[0][index]) == 10 for index in expected)
                if r == 2:
                    symbolic.append({'flag_indices': [left_index,right_index],
                                     'labelled_embedding_terms': [[k,v] for k,v in sorted(expected.items())],
                                     'accepted_completions_by_overlap': dict(sorted(by_q.items()))})
        if r == 2:
            tiny_blocks.append({'root_type': root, 'flag_rows': [list(flag['rows']) for flag in flags],
                                'stabilizers': [flag['stabilizer'] for flag in flags], 'entries': symbolic})
    # These are small direct-host controls: two blocks of orders4/3 and
    # the order15 four-cycle-root block, not the complete r4s3 generation.
    host_checks = rook_controls(builder, ids, (2,3,16))
    prism = tuple(sum(1 << j for j in range(6) if i != j and
                      (i//3 == j//3 or abs(i-j) == 3)) for i in range(6))
    assert ids[oracle.canonical(prism)] == 99
    projection = []
    for root in data[1][2]:
        flags = builder.flags(root)
        retained, zero = [], []
        for i, flag in enumerate(flags):
            if flag['type'] == 99:
                zero.append(i)
            else:
                retained.append(i)
                if flag['size']:
                    assert root == 2 and flag['type'] in (95,98)
                    completed = list(flag['rows'])
                    completed[0] |= 2
                    completed[1] |= 1
                    assert ids[oracle.canonical(tuple(completed))] == 99
        projection.append({'root_type': root, 'retained_flag_indices': retained,
                           'prism_flag_indices': zero, 'retained_order': len(retained)})
    assert [record['retained_order'] for record in projection] == [3,1]
    result = {'status': 'higher-flag products prepared; cold literal controls PASS',
              'source_sha256': files.digest(Path(__file__)), 'domain_source_sha256': DOMAIN_SOURCE_SHA,
              'domain_path': str(domain_path), 'domain_sha256': files.digest(domain_path),
              'catalogue_path': str(catalogue), 'catalogue_sha256': domains.CATALOGUE_SHA,
              'transport_source_sha256': TRANSPORT_SOURCE_SHA, 'independent_oracle_sha256': ORACLE_SOURCE_SHA,
              'full_overlap_stabilizer_checks': full_overlap_checks,
              'cold_independent_lower_entries': entries,
              'cold_entries_with_order_ten_terms': ten_terms,
              'both_product_orders_checked': True, 'all_overlap_multiplicities_retained': True,
              'stabilizer_divisor_used': False, 'small_r2s4_symbolic_blocks': tiny_blocks,
              'direct_rook_host_controls': host_checks, 'prism_zero_projection': projection,
              'full_r4s3_root_count': 9, 'full_r4s3_flags': 883, 'full_r4s3_lower_entries': 90240,
              'full_r4s3_cache_generated': False, 'full_r2s4_lower_entries': 16,
              'count_point_used': False, 'dense_reduction_loaded': False, 'optimizer_called': False,
              'transport_checks': builder.engine.transports_checked,
              'normalized_prefixes': builder.normalized_transport_prefixes,
              'raw_prefixes_used_only_for_transport_caching': builder.raw_transport_prefixes,
              'seconds': time.monotonic()-started,
              'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    files.save(output,result)
    print(json.dumps({key:value for key,value in result.items() if key != 'small_r2s4_symbolic_blocks'},indent=2),flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--domains',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        prepare(args.domains,args.output)
