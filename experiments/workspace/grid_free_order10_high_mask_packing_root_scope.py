"""Complete packing-orbit scope for the other 61 six-vertex roots.

Only actual automorphisms of each specified root are used. A supported
monomial of degree at most four is itself an atom of size at most four,
because the complete structural packing domain is downward closed.
No count point, tensor, optimizer, or outside-edge graph is used.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, permutations
import json
from math import comb
from pathlib import Path
import pickle
import resource
import signal
import time

import numpy as np

import grid_free_order10_high_mask_packing_orbits as bit_actions


ROOT = bit_actions.ROOT
LOGS = ROOT/'experiments/logs/moments-and-counts'
DOMAIN = LOGS/'order10-high-mask-packing-domains02.json.gz'
DOMAIN_SHA = '27c27163aa7429d75df5d430072ece5dd045df2d54caa8a6d57a28db45db0a71'
DOMAIN_SOURCE = ROOT/'experiments/workspace/grid_free_order10_high_mask_packing_domains.py'
DOMAIN_SOURCE_SHA = '0887869f50f0684f99bc000fd804f5400cfe59c2a5e322633d1d9b00fdf36637'
BIT_ACTION_SOURCE_SHA = '59af3f038c1f2795d03d11a80eaee363832f748bcc9863245b8237c71d8d73cd'
CATALOGUE = Path('/tmp/conway99-order10-catalogue.pickle')
CATALOGUE_SHA = '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'
IDENTITY = tuple(range(6))
ALL_PERMUTATIONS = tuple(permutations(range(6)))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_digest(array):
    return hashlib.sha256(array.tobytes(order='C')).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def is_automorphism(rows, permutation):
    return all(((rows[i] >> j)&1) == ((rows[permutation[i]] >> permutation[j])&1)
               for i in range(6) for j in range(i))


def generated_group(generators):
    group, seen, depths = [IDENTITY], {IDENTITY}, [0]
    front = 0
    while front < len(group):
        permutation = group[front]
        for generator in generators:
            product = tuple(generator[permutation[i]] for i in range(6))
            if product not in seen:
                seen.add(product)
                group.append(product)
                depths.append(depths[front]+1)
        front += 1
    assert len(group) <= 720
    return group, max(depths)


def automorphism_group(rows, expected_order):
    complete = [permutation for permutation in ALL_PERMUTATIONS
                if is_automorphism(rows, permutation)]
    assert len(complete) == expected_order and complete[0] == IDENTITY
    generators, closure = [], [IDENTITY]
    seen = set(closure)
    diameter = 0
    for permutation in complete:
        if permutation not in seen:
            generators.append(permutation)
            closure, diameter = generated_group(generators)
            seen = set(closure)
    assert set(complete) == seen
    assert all(is_automorphism(rows, generator) for generator in generators)
    return complete, generators, diameter


def orbits(generator_maps, order, group_diameter):
    n = generator_maps.shape[1]
    labels = np.full(n, -1, dtype=np.int32)
    predecessor = np.full(n, -1, dtype=np.int32)
    step = np.full(n, -1, dtype=np.int8)
    depth = np.zeros(n, dtype=np.int16)
    representatives, sizes = [], []
    for first in range(n):
        if labels[first] >= 0:
            continue
        label = len(representatives)
        representatives.append(first)
        labels[first] = label
        queue, at = [first], 0
        while at < len(queue):
            vertex = queue[at]
            at += 1
            for g in range(len(generator_maps)):
                other = int(generator_maps[g, vertex])
                if labels[other] < 0:
                    labels[other] = label
                    predecessor[other] = vertex
                    step[other] = g
                    depth[other] = int(depth[vertex])+1
                    queue.append(other)
                else:
                    assert labels[other] == label
        sizes.append(len(queue))
    representatives = np.asarray(representatives, dtype=np.int32)
    sizes = np.asarray(sizes, dtype=np.int32)
    assert int(sizes.sum(dtype=np.int64)) == n
    assert np.all(labels >= 0) and np.all(order % sizes == 0)
    assert int(depth.max(initial=0)) <= group_diameter <= 719
    for g in range(len(generator_maps)):
        assert np.array_equal(labels[generator_maps[g]], labels)
    for vertex in range(n):
        if predecessor[vertex] < 0:
            assert representatives[labels[vertex]] == vertex and depth[vertex] == 0
        else:
            parent = int(predecessor[vertex])
            assert generator_maps[int(step[vertex]), parent] == vertex
            assert labels[parent] == labels[vertex] and depth[parent]+1 == depth[vertex]
    return {'labels': labels, 'representatives': representatives, 'sizes': sizes,
            'predecessor': predecessor, 'generator_step': step, 'depth': depth}


def monomials(code):
    bits = []
    while code:
        bit = code & -code
        bits.append(bit)
        code -= bit
    for degree in range(5):
        for chosen in combinations(bits, degree):
            yield sum(chosen)


def root_scope(record, all_atoms, universal_high, expected_order):
    root, rows = record['root_type'], record['root_rows']
    complete_group, generators, diameter = automorphism_group(rows, expected_order)
    index = {mask: i for i, mask in enumerate(universal_high)}
    allowed = set(record['global_class_indices'])
    global_ids = np.asarray(record['visible_pair_cap_atom_ids'], dtype=np.int32)
    atoms = all_atoms[global_ids]
    assert len(atoms) == record['visible_pair_cap_atom_count'] and atoms[0] == 0
    assert np.all(atoms[1:] > atoms[:-1])
    lookup = {int(code): i for i, code in enumerate(atoms)}
    downward_checks = 0
    for code in map(int, atoms):
        remaining = code
        while remaining:
            bit = remaining & -remaining
            assert code ^ bit in lookup
            remaining -= bit
            downward_checks += 1
    class_maps, generator_maps = [], []
    for generator in generators:
        mapping = [index[bit_actions.move_root_mask(mask, generator)] for mask in universal_high]
        assert sorted(mapping) == list(range(42))
        assert {mapping[i] for i in allowed} == allowed
        moved = bit_actions.move_array(atoms, mapping)
        at = np.searchsorted(atoms, moved)
        assert np.all(at < len(atoms)) and np.array_equal(atoms[at], moved)
        class_maps.append(mapping)
        generator_maps.append(at.astype(np.int32))
    generator_maps = np.asarray(generator_maps, dtype=np.int32).reshape(len(generators), len(atoms))
    partition = orbits(generator_maps, len(complete_group), diameter)
    representative_codes = atoms[partition['representatives']]
    populations = np.asarray([int(code).bit_count() for code in atoms], dtype=np.int8)
    representative_populations = populations[partition['representatives']]
    assert np.array_equal(populations, representative_populations[partition['labels']])
    small_orbits = np.flatnonzero(representative_populations <= 4).astype(np.int32)
    small_rows = np.flatnonzero(populations <= 4).astype(np.int32)
    row_of_orbit = {int(orbit): row for row, orbit in enumerate(small_orbits)}
    C = np.zeros((len(small_orbits), len(representative_codes)), dtype=np.int64)
    for column, code in enumerate(map(int, representative_codes)):
        count = 0
        for subset in monomials(code):
            local = lookup[subset]
            row = row_of_orbit[int(partition['labels'][local])]
            C[row, column] += 1
            count += 1
        assert count == sum(comb(code.bit_count(), d) for d in range(5))
    assert int(C.max(initial=0)) <= 386
    row_sizes = partition['sizes'][small_orbits]
    products = C*partition['sizes'][None, :]
    assert np.all(products % row_sizes[:, None] == 0)
    # This complete minor is triangular by population, with identity
    # diagonal blocks. It proves full row rank without a floating SVD.
    minor = C[:, small_orbits]
    row_degrees = representative_populations[small_orbits]
    assert np.all(np.diag(minor) == 1)
    forced_zero = (row_degrees[:, None] > row_degrees[None, :])
    forced_zero |= ((row_degrees[:, None] == row_degrees[None, :]) &
                    ~np.eye(len(small_orbits), dtype=bool))
    assert np.all(minor[forced_zero] == 0)
    raw_counts = [comb(len(allowed), d) for d in range(5)]
    supported_counts = [int(np.count_nonzero(populations == d)) for d in range(5)]
    assert sum(supported_counts) == len(small_rows)
    assert sum(int(row_sizes[i]) for i in range(len(row_sizes))) == len(small_rows)
    result = {'root_type': root, 'root_rows': rows, 'high_masks': record['high_masks'],
        'allowed_global_class_indices': sorted(allowed), 'automorphism_order': len(complete_group),
        'complete_root_automorphisms': [list(p) for p in complete_group],
        'root_generators': [list(p) for p in generators], 'generator_group_diameter': diameter,
        'generator_count': len(generators), 'literal_root_permutations_checked': 720,
        'visible_atoms': len(atoms), 'pair_quota_baseline_atoms': record['pair_quota_atom_count'],
        'raw_monomials_by_degree': raw_counts, 'raw_monomials': sum(raw_counts),
        'supported_monomials_by_degree': supported_counts, 'supported_monomials': len(small_rows),
        'atom_orbits': len(representative_codes), 'supported_monomial_orbits': len(small_orbits),
        'quotient_shape': list(C.shape), 'quotient_nnz': int(np.count_nonzero(C)),
        'maximum_coefficient': int(C.max(initial=0)), 'exact_row_rank': len(small_orbits),
        'downward_closure_checks': downward_checks,
        'literal_domain_generator_checks': len(atoms)*len(generators),
        'orbit_size_histogram': {str(size): int(np.count_nonzero(partition['sizes'] == size))
                                for size in sorted(set(map(int, partition['sizes'])))},
        'atom_orbits_by_population': {str(k): int(np.count_nonzero(representative_populations == k))
                                     for k in range(11)},
        'all_lift_incidence_ratios_integral': True,
        'literal_fixed_monomial_lift_counts_checked': False,
        'point_moments_loaded_or_checked': False, 'complete': True}
    arrays = {'global_atom_ids': global_ids, 'atom_codes': atoms,
        'class_generators': np.asarray(class_maps, dtype=np.int32).reshape(len(generators), 42),
        'generator_maps': generator_maps, 'small_atom_ids': small_rows,
        'supported_row_orbits': small_orbits, 'quotient_coefficients': C,
        'populations': populations, **partition}
    return result, arrays


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--arrays', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    args.output, args.arrays = args.output.resolve(), args.arrays.resolve()
    progress = args.output.with_suffix('.progress.json')
    assert 0 < args.seconds <= 60
    assert not any(p.exists() for p in (args.output, args.arrays, progress))
    started = time.monotonic()
    result = {'status': 'running complete other-root packing scope', 'complete': False,
        'source_sha256': digest(Path(__file__)), 'packing_domain_sha256': DOMAIN_SHA,
        'packing_domain_source_sha256': DOMAIN_SOURCE_SHA,
        'bit_action_source_sha256': BIT_ACTION_SOURCE_SHA, 'catalogue_sha256': CATALOGUE_SHA,
        'requested_seconds': args.seconds, 'roots': [],
        'count_point_loaded': False, 'product_tensor_loaded': False,
        'optimizer_called': False, 'outside_graph_enumerated': False,
        'host_graph_automorphism_assumed': False, 'graph_existence_resolved': False}
    saved_arrays = {}
    def checkpoint():
        result.update(completed_roots=len(result['roots']), seconds=time.monotonic()-started,
                      peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        progress.write_text(json.dumps(result, indent=2)+'\n')
        last = result['roots'][-1]
        print(json.dumps({'root': last['root_type'], 'aut_order': last['automorphism_order'],
                          'shape': last['quotient_shape'], 'nnz': last['quotient_nnz'],
                          'seconds': result['seconds']}), flush=True)
    def deadline(_signum, _frame):
        raise TimeoutError('bounded complete other-root packing scope')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    timed_out, error = False, None
    try:
        assert digest(DOMAIN) == DOMAIN_SHA and digest(DOMAIN_SOURCE) == DOMAIN_SOURCE_SHA
        assert digest(Path(bit_actions.__file__)) == BIT_ACTION_SOURCE_SHA
        assert digest(CATALOGUE) == CATALOGUE_SHA
        domain = read(DOMAIN)
        assert domain['complete'] and domain['completed_root_domains'] == 62
        atom_path = ROOT/domain['atoms']['path']
        assert digest(atom_path) == domain['atoms']['sha256']
        all_atoms = np.fromfile(atom_path, dtype='<u8')
        assert len(all_atoms) == 132062 and all_atoms[0] == 0
        assert np.all(all_atoms[1:] > all_atoms[:-1])
        catalogue = pickle.loads(CATALOGUE.read_bytes())
        records = [r for r in domain['roots'] if r['root_type'] != 38]
        assert [r['root_type'] for r in records] == list(range(39, 100))
        for record in records:
            root = record['root_type']
            assert list(catalogue[0][root]) == record['root_rows']
            current, arrays = root_scope(record, all_atoms, domain['universal_high_masks'],
                                         int(catalogue[2][root]))
            blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
            try:
                result['roots'].append(current)
                saved_arrays.update({f'r{root}_{name}': array for name, array in arrays.items()})
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
            checkpoint()
        assert [r['root_type'] for r in result['roots']] == list(range(39, 100))
        result.update(complete=True, status='complete packing-moment orbit scope for all other 61 roots')
    except TimeoutError:
        timed_out = True
        result.update(complete=False, status='UNKNOWN: incomplete other-root packing scope')
    except Exception as problem:
        error = repr(problem)
        result.update(complete=False, status='ERROR: other-root scope failed', error=error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    np.savez_compressed(args.arrays, **saved_arrays)
    result.update(arrays={'path': str(args.arrays.relative_to(ROOT)), 'sha256': digest(args.arrays),
                          'bytes': args.arrays.stat().st_size},
                  array_sha256={name: array_digest(array) for name, array in saved_arrays.items()},
                  completed_roots=len(result['roots']), timed_out=timed_out,
                  seconds=time.monotonic()-started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if result['complete']:
        result['summary'] = {key: sum(r[key] for r in result['roots']) for key in
            ('visible_atoms', 'raw_monomials', 'supported_monomials', 'atom_orbits',
             'supported_monomial_orbits', 'quotient_nnz', 'downward_closure_checks',
             'literal_domain_generator_checks', 'literal_root_permutations_checked')}
        result['summary']['largest_quotient_rows'] = max(r['quotient_shape'][0] for r in result['roots'])
        result['summary']['largest_quotient_columns'] = max(r['quotient_shape'][1] for r in result['roots'])
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in
                     ('roots', 'array_sha256')}, indent=2), flush=True)
    print('output_sha256', digest(args.output), flush=True)
    raise SystemExit(int(error is not None))


if __name__ == '__main__':
    main()
