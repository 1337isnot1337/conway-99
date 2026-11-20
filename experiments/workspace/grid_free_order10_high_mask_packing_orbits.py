"""Exact S6 quotient of the complete empty-root packing moment model.

This is a relabelling action on the six specified root positions. It makes
no automorphism assumption about a hypothetical host graph. All original
columns and rows remain recorded by explicit generator maps and orbit IDs.
"""

import argparse
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations, permutations
import json
from math import comb, factorial
from pathlib import Path
import resource
import signal
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
FEATURES = LOGS/'order10-high-mask-packing-features02.json'
FEATURES_SHA = 'd4df7b082b71cc25b2f2b4710c034e43a75bafeaa4d4cf4e913422bf3787fe0f'
FEATURE_SOURCE = ROOT/'experiments/workspace/grid_free_order10_high_mask_packing_features_v2.py'
FEATURE_SOURCE_SHA = '8e0ceb67d345456058ae2adac42326214f9386914bfb08b8df90f223a7c9cb04'
DOMAIN = LOGS/'order10-high-mask-packing-domains02.json.gz'
DOMAIN_SHA = '27c27163aa7429d75df5d430072ece5dd045df2d54caa8a6d57a28db45db0a71'
POINT_SHA = '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df'
INT64_MAX = (1 << 63)-1


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def array_digest(array):
    return hashlib.sha256(array.tobytes(order='C')).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def move_root_mask(mask, permutation):
    return sum(((mask >> i)&1) << permutation[i] for i in range(len(permutation)))


def move_class_code(code, permutation):
    return sum(((code >> i)&1) << permutation[i] for i in range(len(permutation)))


def generator_class_maps(high):
    index = {mask: i for i, mask in enumerate(high)}
    root_maps, class_maps = [], []
    for adjacent in range(5):
        root_map = list(range(6))
        root_map[adjacent], root_map[adjacent+1] = root_map[adjacent+1], root_map[adjacent]
        mapping = [index[move_root_mask(mask, root_map)] for mask in high]
        assert sorted(mapping) == list(range(42))
        assert all(mapping[mapping[i]] == i for i in range(42))
        root_maps.append(root_map)
        class_maps.append(mapping)
    return root_maps, np.asarray(class_maps, dtype=np.int32)


def move_array(codes, class_map):
    # Seven six-bit tables implement the permutation of 42 coordinates.
    tables = np.zeros((7, 64), dtype='<u8')
    for chunk in range(7):
        for word in range(64):
            tables[chunk, word] = sum(((word >> i)&1) << int(class_map[6*chunk+i])
                                      for i in range(6))
    answer = np.zeros(len(codes), dtype='<u8')
    for chunk in range(7):
        answer |= tables[chunk, (codes >> np.uint64(6*chunk)) & np.uint64(63)]
    return answer


def orbit_partition(generator_maps):
    n = generator_maps.shape[1]
    labels = np.full(n, -1, dtype=np.int32)
    predecessor = np.full(n, -1, dtype=np.int32)
    step = np.full(n, -1, dtype=np.int8)
    depth = np.zeros(n, dtype=np.int8)
    representatives, sizes = [], []
    for start in range(n):
        if labels[start] >= 0:
            continue
        orbit = len(representatives)
        representatives.append(start)
        queue = [start]
        labels[start] = orbit
        front = 0
        while front < len(queue):
            vertex = queue[front]
            front += 1
            for g in range(len(generator_maps)):
                other = int(generator_maps[g, vertex])
                if labels[other] < 0:
                    labels[other] = orbit
                    predecessor[other] = vertex
                    step[other] = g
                    depth[other] = int(depth[vertex])+1
                    queue.append(other)
                else:
                    assert labels[other] == orbit
        sizes.append(len(queue))
    representatives = np.asarray(representatives, dtype=np.int32)
    sizes = np.asarray(sizes, dtype=np.int32)
    assert len(labels) == int(sizes.sum(dtype=np.int64))
    assert np.all(labels >= 0) and np.all(720 % sizes == 0)
    assert int(depth.max(initial=0)) <= 15
    assert np.array_equal(labels[representatives], np.arange(len(representatives)))
    for g in range(len(generator_maps)):
        assert np.array_equal(labels[generator_maps[g]], labels)
    for vertex in range(n):
        if predecessor[vertex] < 0:
            assert representatives[labels[vertex]] == vertex and depth[vertex] == 0 and step[vertex] == -1
        else:
            parent = int(predecessor[vertex])
            assert generator_maps[int(step[vertex]), parent] == vertex
            assert labels[parent] == labels[vertex]
            assert int(depth[parent])+1 == depth[vertex]
    return {'labels': labels, 'representatives': representatives, 'sizes': sizes,
            'predecessor': predecessor, 'generator_step': step, 'depth': depth}


def literal_controls():
    reports = []
    transports, lifted_moments = 0, 0
    for n in (2, 3, 4):
        high = [h for h in range(1 << n) if h.bit_count() >= 3]
        index = {mask: i for i, mask in enumerate(high)}
        pair_sites = list(combinations(range(n), 2))
        atoms = []
        for code in range(1 << len(high)):
            selected = [mask for i, mask in enumerate(high) if code >> i & 1]
            if any(sum(int(mask >> i & 1 and mask >> j & 1) for mask in selected) > 2
                   for i, j in pair_sites):
                continue
            if any((a&b).bit_count() > 2 for a, b in combinations(selected, 2)):
                continue
            atoms.append(code)
        monomials = [code for code in range(1 << len(high)) if code.bit_count() <= 4]
        maps = [[index[move_root_mask(mask, p)] for mask in high]
                for p in permutations(range(n))]
        def explicit_orbits(values):
            remaining = set(values)
            answer = []
            while remaining:
                representative = min(remaining)
                orbit = {move_class_code(representative, p) for p in maps}
                assert orbit <= remaining
                answer.append(sorted(orbit))
                remaining -= orbit
            return answer
        atom_orbits, row_orbits = explicit_orbits(atoms), explicit_orbits(monomials)
        base_mass = {code: (code*code+3*code+1) % 7+1 for code in atoms}
        symmetric_mass = {}
        for code in atoms:
            images = [move_class_code(code, p) for p in maps]
            assert all(image in base_mass for image in images)
            symmetric_mass[code] = sum(base_mass[image] for image in images)
            transports += len(images)
        moments = {t: sum(mass for s, mass in symmetric_mass.items() if s&t == t)
                   for t in monomials}
        weights = [sum(symmetric_mass[s] for s in orbit) for orbit in atom_orbits]
        for orbit in atom_orbits:
            assert len({symmetric_mass[s] for s in orbit}) == 1
        for row_orbit in row_orbits:
            assert len({moments[t] for t in row_orbit}) == 1
            coefficients = [sum(t & atom_orbit[0] == t for t in row_orbit)
                            for atom_orbit in atom_orbits]
            rhs = sum(moments[t] for t in row_orbit)
            assert sum(c*w for c, w in zip(coefficients, weights)) == rhs
            for t in row_orbit:
                lifted = sum(Fraction(w*sum(s&t == t for s in orbit), len(orbit))
                             for w, orbit in zip(weights, atom_orbits))
                assert lifted == moments[t]
                lifted_moments += 1
            for c, atom_orbit in zip(coefficients, atom_orbits):
                d = sum(s & row_orbit[0] == row_orbit[0] for s in atom_orbit)
                assert len(atom_orbit)*c == len(row_orbit)*d
        reports.append({'root_size': n, 'high_classes': len(high), 'atoms': len(atoms),
            'row_monomials': len(monomials), 'root_permutations': factorial(n),
            'atom_orbits': len(atom_orbits), 'row_orbits': len(row_orbits),
            'uniform_lift_recovers_every_individual_moment': True})
    return {'cases': reports, 'literal_root_transports_checked': transports,
            'individual_lifted_moments_checked': lifted_moments,
            'quotient_rhs_uses_sum_of_row_orbit_moments': True,
            'quotient_weights_are_total_atom_orbit_mass': True}


def inputs():
    assert digest(FEATURES) == FEATURES_SHA
    assert digest(FEATURE_SOURCE) == FEATURE_SOURCE_SHA
    assert digest(DOMAIN) == DOMAIN_SHA
    prepared = read(FEATURES)
    assert prepared['complete'] and prepared['source_sha256'] == FEATURE_SOURCE_SHA
    assert prepared['integer_count_point_sha256'] == POINT_SHA
    assert not prepared['optimizer_called']
    packed = read(DOMAIN)
    assert packed['complete'] and packed['universal_census_complete']
    arrays = {}
    for key in ('matrix', 'moments', 'filters'):
        item = prepared['artifacts'][key]
        path = ROOT/item['path']
        assert digest(path) == item['sha256']
        with np.load(path, allow_pickle=False) as saved:
            arrays[key] = {name: saved[name] for name in saved.files}
    matrix, moment_data, filters = (arrays[key] for key in ('matrix', 'moments', 'filters'))
    for name, expected in prepared['matrix_array_sha256'].items():
        assert array_digest(matrix[name]) == expected
    assert array_digest(moment_data['moments']) == prepared['moment_array_sha256']
    assert np.array_equal(matrix['monomial_masks'], moment_data['monomial_masks'])
    assert list(matrix['shape']) == [124314, 132062]
    assert matrix['indices'].dtype == matrix['indptr'].dtype == np.dtype('int32')
    assert moment_data['moments'].dtype == np.dtype('int64')
    assert matrix['atom_codes'].dtype == matrix['monomial_masks'].dtype == np.dtype('<u8')
    assert int(matrix['indptr'][-1]) == len(matrix['indices']) == 5804664
    assert np.array_equal(filters['active_columns'], filters['visible_columns'])
    assert len(filters['active_columns']) == 90776
    assert len(filters['positive_rows']) == 17903
    assert not len(filters['unsupported_positive_rows'])
    assert not len(filters['visible_zero_removed_columns'])
    assert np.array_equal(filters['positive_rows'], np.flatnonzero(moment_data['moments'] > 0))
    high = prepared['high_masks']
    assert high == [h for h in range(64) if h.bit_count() >= 3]
    root = next(record for record in packed['roots'] if record['root_type'] == 38)
    assert root['root_rows'] == [0]*6 and root['pair_quotas'] == [2]*15
    assert np.array_equal(filters['visible_columns'], root['visible_pair_cap_atom_ids'])
    return prepared, matrix, moment_data['moments'], filters, high


def prepare(result, output_arrays, checkpoint):
    result['controls'] = literal_controls()
    prepared, matrix, moments, filters, high = inputs()
    atoms = matrix['atom_codes']
    rows = matrix['monomial_masks']
    visible_ids = filters['visible_columns']
    visible_atoms = atoms[visible_ids]
    root_maps, class_maps = generator_class_maps(high)
    row_sort = np.argsort(rows)
    sorted_rows = rows[row_sort]
    row_generators, atom_generators = [], []
    closure_tests = 0
    for g in range(5):
        moved = move_array(atoms, class_maps[g])
        at = np.searchsorted(atoms, moved)
        assert np.all(at < len(atoms)) and np.array_equal(atoms[at], moved)
        closure_tests += len(atoms)
        moved = move_array(visible_atoms, class_maps[g])
        at = np.searchsorted(visible_atoms, moved)
        assert np.all(at < len(visible_atoms)) and np.array_equal(visible_atoms[at], moved)
        atom_generators.append(at.astype(np.int32))
        closure_tests += len(visible_atoms)
        moved = move_array(rows, class_maps[g])
        at = np.searchsorted(sorted_rows, moved)
        assert np.all(at < len(rows)) and np.array_equal(sorted_rows[at], moved)
        row_map = row_sort[at].astype(np.int32)
        assert np.array_equal(moments[row_map], moments)
        row_generators.append(row_map)
        closure_tests += len(rows)
    row_generators = np.asarray(row_generators, dtype=np.int32)
    atom_generators = np.asarray(atom_generators, dtype=np.int32)
    for g in range(5):
        assert np.array_equal(row_generators[g, row_generators[g]], np.arange(len(rows)))
        assert np.array_equal(atom_generators[g, atom_generators[g]], np.arange(len(visible_atoms)))
    result.update(root_generators=root_maps, class_generators=class_maps.tolist(),
                  exact_generator_domain_closure_checks=closure_tests,
                  exact_moment_constancy_checks=5*len(rows))
    checkpoint('all five generators preserve both atom domains, all monomials and exact moments')
    row_orbits = orbit_partition(row_generators)
    atom_orbits = orbit_partition(atom_generators)
    nr, na = len(row_orbits['representatives']), len(atom_orbits['representatives'])
    coefficients = np.zeros((nr, na), dtype=np.int64)
    for orbit, local in enumerate(atom_orbits['representatives']):
        global_column = int(visible_ids[int(local)])
        lo, hi = (int(matrix['indptr'][global_column+i]) for i in (0, 1))
        coefficients[:, orbit] = np.bincount(
            row_orbits['labels'][matrix['indices'][lo:hi]], minlength=nr)
    rhs_python = [0]*nr
    for orbit, value in zip(row_orbits['labels'], moments):
        rhs_python[int(orbit)] += int(value)
    rhs_bound = int(moments.max())*int(row_orbits['sizes'].max())
    assert rhs_bound <= INT64_MAX
    rhs = np.asarray(rhs_python, dtype=np.int64)
    for orbit, representative in enumerate(row_orbits['representatives']):
        assert rhs_python[orbit] == int(row_orbits['sizes'][orbit])*int(moments[representative])
    constant_orbit = int(row_orbits['labels'][0])
    assert row_orbits['sizes'][constant_orbit] == 1
    assert np.all(coefficients[constant_orbit] == 1)
    assert rhs[constant_orbit] == moments[0] > 0
    assert int(coefficients.max()) <= 386
    active_rows = np.flatnonzero(rhs > 0).astype(np.int32)
    assert np.array_equal(active_rows, np.flatnonzero(np.any(coefficients != 0, axis=1)))
    assert sum(int(row_orbits['sizes'][r]) for r in active_rows) == 17903
    checkpoint('complete deterministic orbit partitions and integer quotient constructed')
    # Independently count incidences at a fixed monomial, using the literal
    # bit-subset condition on every structurally allowed atom.
    dual_counts = np.zeros((nr, na), dtype=np.int64)
    for orbit, representative in enumerate(row_orbits['representatives']):
        mask = rows[representative]
        contains = (visible_atoms & mask) == mask
        dual_counts[orbit] = np.bincount(atom_orbits['labels'][contains], minlength=na)
    product_bound = 720*max(int(coefficients.max()), int(dual_counts.max()))
    assert product_bound <= INT64_MAX
    assert np.array_equal(coefficients*atom_orbits['sizes'][None, :],
                          dual_counts*row_orbits['sizes'][:, None])
    assert int(dual_counts.max()) <= 720
    arrays = {'root_generators': np.asarray(root_maps, dtype=np.int8),
        'class_generators': class_maps, 'row_generators': row_generators,
        'atom_generators': atom_generators, 'visible_global_atom_ids': visible_ids,
        'visible_atom_codes': visible_atoms, 'row_monomial_codes': rows,
        'quotient_coefficients': coefficients, 'quotient_rhs': rhs,
        'literal_fixed_monomial_incidence_counts': dual_counts,
        'active_quotient_rows': active_rows,
        'constant_quotient_row': np.asarray([constant_orbit], dtype=np.int32)}
    for prefix, orbit_data in (('row', row_orbits), ('atom', atom_orbits)):
        arrays.update({prefix+'_'+key: value for key, value in orbit_data.items()})
    np.savez_compressed(output_arrays, **arrays)
    result.update(complete=True, status='complete exact S6 packing-moment quotient; no optimizer',
        row_orbits=nr, active_row_orbits=len(active_rows), atom_orbits=na,
        full_quotient_shape=[nr, na], active_quotient_shape=[len(active_rows), na],
        full_quotient_nnz=int(np.count_nonzero(coefficients)),
        active_quotient_nnz=int(np.count_nonzero(coefficients[active_rows])),
        row_orbit_size_histogram={str(size): int(np.count_nonzero(row_orbits['sizes'] == size))
                                 for size in sorted(set(map(int, row_orbits['sizes'])))},
        atom_orbit_size_histogram={str(size): int(np.count_nonzero(atom_orbits['sizes'] == size))
                                  for size in sorted(set(map(int, atom_orbits['sizes'])))},
        covered_full_rows=len(rows), covered_supported_rows=17903,
        covered_visible_atoms=len(visible_atoms), covered_baseline_atoms=len(atoms),
        literal_lift_identity_entry_checks=nr*na,
        literal_lift_identity='atom_orbit_size * C[R,O] = row_orbit_size * D[R,O]',
        rhs_construction='sum of the individual moments over each complete monomial orbit',
        quotient_variable='total nonnegative mass of one atom orbit',
        uniform_lift='assign quotient mass divided by atom-orbit size to every atom in that orbit',
        coefficient_and_lift_product_bound=product_bound,
        rhs_integer_bound=rhs_bound, maximum_coefficient=int(coefficients.max()),
        root_labelled_embedding_mass=int(moments[0]),
        maximum_row_transport_length=int(row_orbits['depth'].max()),
        maximum_atom_transport_length=int(atom_orbits['depth'].max()),
        arrays={'path': str(output_arrays.relative_to(ROOT)), 'sha256': digest(output_arrays),
                'bytes': output_arrays.stat().st_size},
        array_sha256={name: array_digest(array) for name, array in arrays.items()},
        feature_artifact_bindings=prepared['artifacts'])
    checkpoint('full literal incidence lift identity verified and quotient arrays saved')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--arrays', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    args.output, args.arrays = args.output.resolve(), args.arrays.resolve()
    assert 0 < args.seconds <= 60
    progress = args.output.with_suffix('.progress.json')
    assert not any(path.exists() for path in (args.output, args.arrays, progress))
    started = time.monotonic()
    result = {'status': 'running exact root-relabeling orbit preparation', 'complete': False,
        'source_sha256': digest(Path(__file__)), 'feature_preparation_sha256': FEATURES_SHA,
        'feature_source_sha256': FEATURE_SOURCE_SHA, 'packing_domain_sha256': DOMAIN_SHA,
        'integer_count_point_sha256': POINT_SHA, 'requested_seconds': args.seconds,
        'optimizer_called': False, 'new_product_tensor_or_reduction_loaded': False,
        'host_graph_automorphism_assumed': False, 'graph_existence_resolved': False}
    def checkpoint(stage):
        result.update(stage=stage, seconds=time.monotonic()-started,
                      peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        progress.write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({'stage': stage, 'seconds': result['seconds'],
                          'peak_rss_kib': result['peak_rss_kib']}), flush=True)
    def deadline(_signum, _frame):
        raise TimeoutError('bounded packing-moment orbit preparation')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    error, timed_out = None, False
    try:
        prepare(result, args.arrays, checkpoint)
    except TimeoutError:
        timed_out = True
        result.update(status='UNKNOWN: incomplete orbit preparation', complete=False)
    except Exception as problem:
        error = repr(problem)
        result.update(status='ERROR: orbit preparation failed', complete=False, error=error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    result.update(seconds=time.monotonic()-started, timed_out=timed_out,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in
                     ('controls', 'root_generators', 'class_generators', 'array_sha256')}, indent=2), flush=True)
    print('output_sha256', digest(args.output), flush=True)
    raise SystemExit(int(error is not None))


if __name__ == '__main__':
    main()
