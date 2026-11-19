"""Complete small-domain preparation for induced r4s3 and r2s4 moments.

This enumerates flags and free-label stabilizers, not moment tensors.
Variables retain labelled extension counts. No free stabilizer is divided
out of a variable or a product. The independent direct domains are checked
against flag_moments.flags for every root.
"""

import argparse
from collections import Counter, defaultdict
from functools import lru_cache
from itertools import combinations, combinations_with_replacement, permutations, product
import json
from math import comb, factorial
from pathlib import Path
import pickle
import resource
import time

import pynauty

import flag_moments
import grid_free_order10_scaled as files
from subgraph_counts import nauty


CATALOGUE_SHA = '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'


def caps(rows):
    return all((rows[a] & rows[b]).bit_count()+((rows[a] >> b) & 1) <= 2
               for a in range(len(rows)) for b in range(a))


def relabel(rows, order):
    return tuple(sum(((rows[a] >> b) & 1) << j for j, b in enumerate(order)) for a in order)


def attach(root, masks, code):
    r, s = len(root), len(masks)
    rows = list(root)+list(masks)
    for i, mask in enumerate(masks, r):
        for j in range(r):
            if mask >> j & 1:
                rows[j] |= 1 << i
    for bit, (a, b) in enumerate(combinations(range(r, r+s), 2)):
        if code >> bit & 1:
            rows[a] |= 1 << b
            rows[b] |= 1 << a
    return tuple(rows)


def mask_groups(rows, r):
    groups = defaultdict(list)
    for i in range(r, len(rows)):
        groups[rows[i] & ((1 << r)-1)].append(i)
    return [groups[key] for key in sorted(groups)]


def normal(rows, r):
    groups = mask_groups(rows, r)
    images = (tuple(range(r))+tuple(i for part in parts for i in part)
              for parts in product(*(permutations(group) for group in groups)))
    return min(relabel(rows, order) for order in images)


def free_stabilizer(rows, r):
    answer = []
    for parts in product(*(permutations(group) for group in mask_groups(rows, r))):
        free = tuple(i for part in parts for i in part)
        if relabel(rows, tuple(range(r))+free) == rows:
            answer.append(tuple(i-r for i in free))
    return tuple(answer)


def direct_domain(root, maximum):
    """Sorted masks plus all edges, then quotient only equal-mask labels."""
    r = len(root)
    by_size = []
    sorted_mask_graph_counts = []
    for s in range(maximum+1):
        seen = Counter()
        minimum_root_degree = max(0, 4-s)
        masks_available = [mask for mask in range(1 << r)
                           if mask.bit_count() >= minimum_root_degree]
        if s == 0:
            seen[tuple(root)] = 1
        else:
            for masks in combinations_with_replacement(masks_available, s):
                for code in range(1 << comb(s, 2)):
                    rows = attach(root, masks, code)
                    if any(row.bit_count() < 3 for row in rows[r:]) or not caps(rows):
                        continue
                    seen[normal(rows, r)] += 1
        by_size.append(seen)
        sorted_mask_graph_counts.append(sum(seen.values()))
    return by_size, sorted_mask_graph_counts


def unrestricted_overlap_counts(a, b):
    return [comb(b, q)*factorial(a)//factorial(a-q) for q in range(min(a, b)+1)]


@lru_cache(None)
def mask_overlap_counts(left, right):
    """Counts of partial injections respecting root masks, by overlap size."""
    a, b = Counter(left), Counter(right)
    polynomial = [1]
    for mask in sorted(set(a) & set(b)):
        factor = [comb(a[mask], q)*comb(b[mask], q)*factorial(q)
                  for q in range(min(a[mask], b[mask])+1)]
        updated = [0]*(len(polynomial)+len(factor)-1)
        for i, x in enumerate(polynomial):
            for j, y in enumerate(factor):
                updated[i+j] += x*y
        polynomial = updated
    return tuple(polynomial)


def upper_choices(a, b, overlap_counts):
    return sum(count*(1 << ((a-q)*(b-q))) for q, count in enumerate(overlap_counts))


def complexity(flags, r, maximum):
    profiles = Counter(tuple(row & ((1 << r)-1) for row in rows[r:]) for rows in flags)
    by_size = Counter(len(rows)-r for rows in flags)
    unrestricted, matched = 0, 0
    for a in range(maximum+1):
        for b in range(a+1):
            pairs = by_size[a]*by_size[b] if a != b else by_size[a]*(by_size[a]+1)//2
            unrestricted += pairs*upper_choices(a, b, unrestricted_overlap_counts(a, b))
    profiles = sorted(profiles.items())
    for i, (left, left_count) in enumerate(profiles):
        for right, right_count in profiles[:i+1]:
            pairs = left_count*right_count if left != right else left_count*(left_count+1)//2
            matched += pairs*upper_choices(len(left), len(right), mask_overlap_counts(left, right))
    return {'lower_entries': len(flags)*(len(flags)+1)//2,
            'unrestricted_overlap_completion_upper_bound': unrestricted,
            'root_mask_matched_completion_upper_bound': matched,
            'mask_profiles': len(profiles),
            'bounds_ignore_shared_edge_consistency_and_local_caps': True}


def rook_control(root_rows, flag):
    """Literal host counts demonstrate labelled, not subset, normalization."""
    r, s = len(root_rows), len(flag)-len(root_rows)
    host = tuple(sum(1 << j for j in range(9) if i != j and
                     (i//3 == j//3 or i % 3 == j % 3)) for i in range(9))
    labelled, subsets, root_embeddings, largest = 0, 0, 0, 0
    stab = len(free_stabilizer(flag, r))
    root_counts = Counter()
    for root_image in permutations(range(9), r):
        if relabel(host, root_image) != tuple(root_rows):
            continue
        root_embeddings += 1
        available = sorted(set(range(9))-set(root_image))
        count = 0
        seen = set()
        for free_image in permutations(available, s):
            if relabel(host, root_image+free_image) == flag:
                count += 1
                seen.add(tuple(sorted(free_image)))
        assert count == stab*len(seen)
        labelled += count
        subsets += len(seen)
        largest = max(largest, count)
        root_counts[count] += 1
    assert root_embeddings > 0
    if labelled == 0:
        return None
    return {'root_rows': list(root_rows), 'flag_rows': list(flag), 'free_stabilizer': stab,
            'root_embeddings': root_embeddings, 'labelled_extension_total': labelled,
            'unlabelled_free_subset_total': subsets, 'maximum_labelled_flag_value': largest,
            'labelled_count_histogram': dict(sorted(root_counts.items())),
            'labelled_equals_stabilizer_times_subsets': True}


def prepare(catalogue, output):
    started = time.monotonic()
    assert files.digest(catalogue) == CATALOGUE_SHA
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    graphs, levels, aut, _ = data
    ids = {(len(rows), pynauty.certificate(nauty(rows))): i
           for i, rows in enumerate(graphs) if len(rows) <= 7}
    families, controls = [], []
    for r, maximum in ((4, 3), (2, 4)):
        records, family_by_size, stabilizers = [], Counter(), Counter()
        duplicate_masks = []
        first_rook_control = None
        for root in levels[r]:
            root_started = time.monotonic()
            root_rows = tuple(graphs[root])
            direct, sorted_counts = direct_domain(root_rows, maximum)
            flags = sorted({rows for layer in direct for rows in layer}, key=lambda rows: (len(rows), rows))
            reference = flag_moments.flags(root_rows, maximum)
            reference_normal = [normal(tuple(rows), r) for rows in reference]
            assert len(reference_normal) == len(set(reference_normal))
            assert set(flags) == set(reference_normal)
            by_size, root_stabilizers, flag_records = Counter(), Counter(), []
            for rows in flags:
                s = len(rows)-r
                masks = tuple(row & ((1 << r)-1) for row in rows[r:])
                assert masks == tuple(sorted(masks))
                group = free_stabilizer(rows, r)
                size = len(group)
                assert size > 0 and factorial(s) % size == 0
                mask_permutations = 1
                for count in Counter(masks).values():
                    mask_permutations *= factorial(count)
                assert direct[s][rows]*size == mask_permutations
                by_size[s] += 1
                root_stabilizers[size] += 1
                flag_type = ids[len(rows), pynauty.certificate(nauty(rows))]
                record = {'size': s, 'rows': list(rows), 'root_masks': list(masks),
                          'type': flag_type, 'root_fixing_free_stabilizer': size,
                          'free_label_orbit_size': factorial(s)//size,
                          'free_stabilizer_permutations': [list(p) for p in group]}
                flag_records.append(record)
                if len(set(masks)) != len(masks):
                    duplicate_masks.append({'root_type': root, **record})
                if r == 4:
                    assert len(set(masks)) == len(masks) and size == 1
                if size > 1 and first_rook_control is None:
                    first_rook_control = rook_control(root_rows, rows)
            family_by_size.update(by_size)
            stabilizers.update(root_stabilizers)
            record = {'root_type': root, 'root_rows': list(root_rows), 'flags': len(flags),
                      'flags_by_free_size': [by_size[s] for s in range(maximum+1)],
                      'labelled_patterns_by_free_size': [sum(factorial(s)//len(free_stabilizer(rows,r))
                                                           for rows in direct[s]) for s in range(maximum+1)],
                      'sorted_mask_graphs_before_equal_mask_quotient': sorted_counts,
                      'free_stabilizer_histogram': dict(sorted(root_stabilizers.items())),
                      'all_root_masks_distinct': all(len(set(f['root_masks'])) == len(f['root_masks']) for f in flag_records),
                      'reference_domain_equal': True, 'complexity': complexity(flags, r, maximum),
                      'flag_domain': flag_records, 'seconds': time.monotonic()-root_started}
            records.append(record)
            print(json.dumps({key: record[key] for key in ('root_type','flags','flags_by_free_size',
                  'free_stabilizer_histogram','all_root_masks_distinct','complexity','seconds')}), flush=True)
        if first_rook_control is not None:
            controls.append(first_rook_control)
        maximum_product = unrestricted_overlap_counts(maximum, maximum)
        families.append({'root_size': r, 'maximum_free_size': maximum, 'root_count': len(records),
                         'total_flags': sum(record['flags'] for record in records),
                         'flags_by_free_size': [family_by_size[s] for s in range(maximum+1)],
                         'maximum_block_order': max(record['flags'] for record in records),
                         'total_lower_entries': sum(record['complexity']['lower_entries'] for record in records),
                         'free_stabilizer_histogram': dict(sorted(stabilizers.items())),
                         'flags_with_repeated_root_masks': len(duplicate_masks),
                         'repeated_mask_examples': duplicate_masks[:12],
                         'maximum_size_overlap_counts_by_q': maximum_product,
                         'maximum_size_unrestricted_completion_bound': upper_choices(maximum, maximum, maximum_product),
                         'unrestricted_completion_bound_all_entries': sum(record['complexity']['unrestricted_overlap_completion_upper_bound'] for record in records),
                         'root_mask_matched_completion_bound_all_entries': sum(record['complexity']['root_mask_matched_completion_upper_bound'] for record in records),
                         'records': records})
    assert controls and all(control['free_stabilizer'] > 1 for control in controls)
    result = {'status': 'complete higher-flag domain preparation; no moment tensors generated',
              'source_sha256': files.digest(Path(__file__)), 'catalogue_path': str(catalogue),
              'catalogue_sha256': CATALOGUE_SHA,
              'reference_source_sha256': files.digest(Path(flag_moments.__file__)),
              'normalization': 'one labelled graph pattern per free-permutation orbit; its variable counts every labelled extension, with no stabilizer divisor',
              'families': families, 'nontrivial_stabilizer_rook_controls': controls,
              'count_point_used': False, 'dense_reduction_loaded': False,
              'moment_tensors_generated': False, 'optimizer_called': False,
              'seconds': time.monotonic()-started,
              'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    files.save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key != 'families'}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.catalogue, args.output)
