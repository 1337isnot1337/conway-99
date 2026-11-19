"""Exact coverage of anchor matchings by alternating-cycle partitions.

Only standard-library code is used. Each of the 10,395 labelled perfect
matchings receives an explicitly checked signed-axis transport from one
of the eleven canonical representatives. No graph symmetry is assumed.
"""

import argparse
from collections import Counter
import hashlib
import json
from math import prod
from pathlib import Path


def partitions(total, minimum=1):
    if total == 0:
        yield ()
        return
    for first in range(minimum, total+1):
        for tail in partitions(total-first, first):
            yield (first,)+tail


def canonical_matching(parts):
    edges, offset = [], 0
    for size in parts:
        for j in range(size):
            first = 2*(offset+j)+1
            second = 2*(offset+(j+1) % size)
            edges.append(tuple(sorted((first, second))))
        offset += size
    assert sorted(v for edge in edges for v in edge) == list(range(2*offset))
    return tuple(sorted(edges))


def all_matchings(points):
    if not points:
        yield ()
        return
    first = points[0]
    for position in range(1, len(points)):
        second = points[position]
        remaining = points[1:position]+points[position+1:]
        for tail in all_matchings(remaining):
            yield ((first, second),)+tail


def canonical_transport(matching, axes):
    partners = {}
    for first, second in matching:
        assert first != second and first not in partners and second not in partners
        partners[first], partners[second] = second, first
    assert set(partners) == set(range(2*axes))
    remaining = set(partners)
    components = []
    while remaining:
        start = current = min(remaining)
        component = []
        while current in remaining:
            assert current ^ 1 in remaining
            component.extend((current, current ^ 1))
            remaining.remove(current)
            remaining.remove(current ^ 1)
            current = partners[current ^ 1]
        assert current == start
        components.append(tuple(component))
    components.sort(key=lambda component: (len(component), component))
    parts = tuple(len(component)//2 for component in components)
    image = sum(components, ())
    assert sorted(image) == list(range(2*axes))
    assert all(image[i ^ 1] == (image[i] ^ 1) for i in range(2*axes))
    moved = tuple(sorted(tuple(sorted((image[a], image[b])))
                         for a, b in canonical_matching(parts)))
    assert moved == tuple(sorted(tuple(sorted(edge)) for edge in matching))
    return parts, image


def generate(axes=6):
    expected_parts = list(partitions(axes))
    counts = Counter()
    domain = hashlib.sha256()
    count = 0
    for matching in all_matchings(tuple(range(2*axes))):
        assert tuple(sorted(matching)) == matching
        parts, image = canonical_transport(matching, axes)
        assert parts in expected_parts
        counts[parts] += 1
        domain.update((json.dumps(matching, separators=(',', ':'))+'\n').encode())
        count += 1
    assert count == prod(range(1, 2*axes, 2))
    assert set(counts) == set(expected_parts)
    if axes == 6:
        assert count == 10395 and len(expected_parts) == 11
    return {'scope': 'all perfect matchings, with explicit signed-axis transports checked',
            'axes': axes, 'points': 2*axes, 'matching_count': count,
            'partitions': len(expected_parts), 'matching_domain_sha256': domain.hexdigest(),
            'cases': [{'index': i, 'partition': list(parts),
                       'canonical_matching': [list(edge) for edge in canonical_matching(parts)],
                       'labelled_matchings': counts[parts]}
                      for i, parts in enumerate(expected_parts)]}


def replay(path):
    record = json.loads(path.read_text())
    assert record == generate(record['axes'])
    print(json.dumps(record), flush=True)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps(generate(), indent=2)+'\n')
    replay(args.certificate)
