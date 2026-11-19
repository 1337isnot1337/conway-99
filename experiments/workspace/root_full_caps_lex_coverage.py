"""Exact stabilizers of the eleven normalized rooted matchings.

The permutations here relabel coordinates. They are not required to be
automorphisms of a completed graph. This module uses the standard library
only and explicitly checks all 46,080 elements of C2 wr S6.
"""

import argparse
from collections import Counter, deque
import hashlib
from itertools import permutations, product
import json
from math import factorial, prod
from pathlib import Path

from root_full_caps_coverage import canonical_matching, partitions


def compact_hash(value):
    return hashlib.sha256(json.dumps(value, separators=(',', ':')).encode()).hexdigest()


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def signed_axis_group(axes):
    """Yield all mate-preserving permutations of 2*axes local endpoints."""
    for order in permutations(range(axes)):
        for signs in product(range(2), repeat=axes):
            yield tuple(2*order[a]+(s ^ signs[a])
                        for a in range(axes) for s in range(2))


def moved_matching(matching, image):
    return tuple(sorted(tuple(sorted((image[a], image[b]))) for a, b in matching))


def component_generators(parts):
    """Colored-cycle dihedral generators and equal-component interchanges."""
    points = 2*sum(parts)
    identity = tuple(range(points))
    result, blocks = [], []
    offset = 0
    for index, size in enumerate(parts):
        blocks.append((offset, size))
        if size > 1:
            image = list(identity)
            for j, s in product(range(size), range(2)):
                image[2*(offset+j)+s] = 2*(offset+(j+1) % size)+s
            result.append({'kind': 'rotation', 'component': index, 'image': image})
        image = list(identity)
        for j, s in product(range(size), range(2)):
            image[2*(offset+j)+s] = 2*(offset+(-j) % size)+(s ^ 1)
        result.append({'kind': 'reflection', 'component': index, 'image': image})
        offset += size
    for size in sorted(set(parts)):
        equal = [i for i, part in enumerate(parts) if part == size]
        for first, second in zip(equal, equal[1:]):
            a, b = blocks[first][0], blocks[second][0]
            image = list(identity)
            for j, s in product(range(size), range(2)):
                image[2*(a+j)+s] = 2*(b+j)+s
                image[2*(b+j)+s] = 2*(a+j)+s
            result.append({'kind': 'component interchange',
                           'components': [first, second], 'image': image})
    images = [tuple(g['image']) for g in result]
    assert len(images) == len(set(images)) and identity not in images
    assert all(sorted(image) == list(identity) for image in images)
    assert all(image[i ^ 1] == (image[i] ^ 1)
               for image in images for i in range(points))
    matching = canonical_matching(parts)
    assert all(moved_matching(matching, image) == matching for image in images)
    return result


def generated_group(generators, points):
    identity = tuple(range(points))
    reached, queue = {identity}, deque([identity])
    while queue:
        current = queue.popleft()
        for image in generators:
            composed = tuple(image[current[i]] for i in range(points))
            if composed not in reached:
                reached.add(composed)
                queue.append(composed)
    return reached


def generate(axes=6):
    assert axes >= 1
    parts = list(partitions(axes))
    matchings = [canonical_matching(part) for part in parts]
    stabilizers = [set() for _ in parts]
    ambient = set()
    for image in signed_axis_group(axes):
        assert image not in ambient
        ambient.add(image)
        assert sorted(image) == list(range(2*axes))
        assert all(image[i ^ 1] == (image[i] ^ 1) for i in range(2*axes))
        for matching, stabilizer in zip(matchings, stabilizers):
            if moved_matching(matching, image) == matching:
                stabilizer.add(image)
    ambient_order = 2**axes*factorial(axes)
    assert len(ambient) == ambient_order
    records = []
    for index, (part, matching, stabilizer) in enumerate(zip(parts, matchings, stabilizers)):
        generators = component_generators(part)
        closure = generated_group([tuple(g['image']) for g in generators], 2*axes)
        # This comparison proves that the generators produce the entire
        # stabilizer, not merely an arbitrary subgroup.
        assert closure == stabilizer
        multiplicities = Counter(part)
        order_formula = prod((2*size)**count*factorial(count)
                             for size, count in multiplicities.items())
        assert len(stabilizer) == order_formula
        assert ambient_order % order_formula == 0
        records.append({'index': index, 'partition': list(part),
                        'canonical_matching': [list(edge) for edge in matching],
                        'stabilizer_order': len(stabilizer),
                        'matching_orbit_size': ambient_order//len(stabilizer),
                        'stabilizer_sha256': compact_hash(sorted(stabilizer)),
                        'generator_count': len(generators), 'generators': generators,
                        'generated_closure_equals_explicit_stabilizer': True})
    assert sum(case['matching_orbit_size'] for case in records) == prod(range(1, 2*axes, 2))
    if axes == 6:
        assert ambient_order == 46080 and len(records) == 11
        assert [case['stabilizer_order'] for case in records] == [
            46080, 1536, 288, 256, 64, 48, 20, 384, 32, 72, 12]
    directory = Path(__file__).resolve().parent
    return {'scope': 'complete normalized-matching stabilizers; coordinate relabelings only',
            'axes': axes, 'local_endpoints': 2*axes,
            'ambient_group_order': ambient_order,
            'ambient_group_sha256': compact_hash(sorted(ambient)),
            'stabilizer_cases': len(records),
            'source_hashes': {name: file_hash(directory/name) for name in
                              ['root_full_caps_coverage.py', 'root_full_caps_lex_coverage.py']},
            'cases': records}


def replay(path):
    saved = json.loads(path.read_text())
    actual = generate(saved['axes'])
    assert saved == actual
    return actual


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--axes', type=int, default=6)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        result = generate(args.axes)
        args.certificate.write_text(json.dumps(result, indent=2)+'\n')
    else:
        result = replay(args.certificate)
    print(json.dumps({'status': 'exact pass', 'ambient_group_order': result['ambient_group_order'],
                      'cases': [{key: case[key] for key in
                                 ['index', 'partition', 'stabilizer_order',
                                  'matching_orbit_size', 'generator_count']}
                                for case in result['cases']]}), flush=True)
