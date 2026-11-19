"""Complete matching-orbit coverage for an unrestricted SRG99 root core.

Standard-library enumeration, explicit transports, and an independent
generator-orbit census.  No SAT model is built or solved here.

Local points0..11 stand for near labels2..13.  The fixed mate matching
is i<->i^1.  Every transport maps an input matching TO its canonical
alternating-cycle matching and preserves this fixed mate relation.
"""

import argparse
from collections import Counter, deque
import gzip
import hashlib
from itertools import combinations
import json
from math import factorial
from pathlib import Path
import time


PAIRS = 6
POINTS = 2 * PAIRS


def partitions(total, minimum=1):
    if total == 0:
        yield ()
    for first in range(minimum, total + 1):
        for tail in partitions(total - first, first):
            yield (first,) + tail


def matchings(points=tuple(range(POINTS))):
    """Independent recursive enumeration: match the least remaining point."""
    if not points:
        yield ()
        return
    first = points[0]
    for i in range(1, len(points)):
        second = points[i]
        rest = points[1:i] + points[i + 1:]
        for tail in matchings(rest):
            yield ((first, second),) + tail


def partner_vector(edges):
    partner = [-1] * POINTS
    for a, b in edges:
        assert a != b and partner[a] == partner[b] == -1
        partner[a], partner[b] = b, a
    assert sorted(partner) == list(range(POINTS))
    assert all(partner[partner[i]] == i and partner[i] != i for i in range(POINTS))
    return tuple(partner)


def canonical_matching(partition):
    assert tuple(sorted(partition)) == tuple(partition) and sum(partition) == PAIRS
    edges, offset = [], 0
    for size in partition:
        edges.extend((2 * (offset + j) + 1,
                      2 * (offset + (j + 1) % size)) for j in range(size))
        offset += size
    return partner_vector(edges)


def components(partner):
    remaining, result = set(range(POINTS)), []
    while remaining:
        start = min(remaining)
        component, stack = set(), [start]
        while stack:
            v = stack.pop()
            if v not in component:
                component.add(v)
                stack.extend((v ^ 1, partner[v]))
        remaining -= component
        assert len(component) % 2 == 0
        result.append(tuple(sorted(component)))
    return sorted(result, key=lambda item: (len(item), item[0]))


def transport(partner):
    pieces = components(partner)
    partition = tuple(len(piece) // 2 for piece in pieces)
    image, offset = [-1] * POINTS, 0
    for piece in pieces:
        size = len(piece) // 2
        start = v = min(piece)
        for j in range(size):
            assert image[v] == image[v ^ 1] == -1
            image[v] = 2 * (offset + j)
            image[v ^ 1] = 2 * (offset + j) + 1
            v = partner[v ^ 1]
        assert v == start
        offset += size
    image = tuple(image)
    assert sorted(image) == list(range(POINTS))
    assert all(image[v ^ 1] == (image[v] ^ 1) for v in range(POINTS))
    assert act(partner, image) == canonical_matching(partition)
    return partition, image


def act(partner, image):
    result = [-1] * POINTS
    for v in range(POINTS):
        result[image[v]] = image[partner[v]]
    return tuple(result)


def generators():
    result = []
    for pair in range(PAIRS):
        image = list(range(POINTS))
        image[2 * pair], image[2 * pair + 1] = 2 * pair + 1, 2 * pair
        result.append(tuple(image))
    for pair in range(PAIRS - 1):
        image = list(range(POINTS))
        for end in (0, 1):
            image[2 * pair + end] = 2 * (pair + 1) + end
            image[2 * (pair + 1) + end] = 2 * pair + end
        result.append(tuple(image))
    assert len(set(result)) == 11
    assert all(all(image[v ^ 1] == (image[v] ^ 1) for v in range(POINTS))
               for image in result)
    return result


def generator_orbit(partner):
    found, queue = {partner}, deque([partner])
    actions = generators()
    while queue:
        current = queue.popleft()
        for image in actions:
            following = act(current, image)
            if following not in found:
                found.add(following)
                queue.append(following)
    return found


def formula(partition):
    denominator = 1
    for size, multiplicity in Counter(partition).items():
        denominator *= size ** multiplicity * factorial(multiplicity)
    numerator = 2 ** (PAIRS - len(partition)) * factorial(PAIRS)
    assert numerator % denominator == 0
    return numerator // denominator


def encode(values):
    assert len(values) == POINTS and all(0 <= value < POINTS for value in values)
    return sum(value * POINTS ** i for i, value in enumerate(values))


def decode(code):
    assert type(code) is int and code >= 0
    values = []
    for _ in range(POINTS):
        code, value = divmod(code, POINTS)
        values.append(value)
    assert code == 0
    return tuple(values)


def census():
    types = list(partitions(PAIRS))
    assert len(types) == 11 and types == sorted(types)
    index = {partition: i for i, partition in enumerate(types)}
    seen, counts, records = set(), Counter(), []
    for edges in matchings():
        partner = partner_vector(edges)
        assert partner not in seen
        seen.add(partner)
        partition, image = transport(partner)
        counts[partition] += 1
        records.append([encode(partner), index[partition], encode(image)])
    assert len(seen) == 10395
    assert sum(counts.values()) == 10395
    independent_union = set()
    summaries = []
    for partition in types:
        canonical = canonical_matching(partition)
        orbit = generator_orbit(canonical)
        assert not independent_union & orbit
        independent_union |= orbit
        expected = formula(partition)
        assert len(orbit) == counts[partition] == expected
        summaries.append({'partition': list(partition),
                          'canonical_edges': [[i, canonical[i]] for i in range(POINTS)
                                              if i < canonical[i]],
                          'enumerated_count': counts[partition],
                          'generator_orbit_count': len(orbit), 'formula_count': expected})
    assert independent_union == seen
    return summaries, sorted(records), seen


def run(certificate, write=False):
    started = time.monotonic()
    summaries, records, matchings_seen = census()
    if write:
        data = {'schema': 1, 'local_points': 12, 'fixed_mate': [i ^ 1 for i in range(12)],
                'near_label_for_local_point': [i + 2 for i in range(12)],
                'transport_direction': 'input matching to canonical matching',
                'record_columns': ['base12_partner_code', 'orbit_index', 'base12_transport_code'],
                'summaries': summaries, 'transports': records}
        payload = json.dumps(data, separators=(',', ':'), sort_keys=True).encode() + b'\n'
        certificate.parent.mkdir(parents=True, exist_ok=True)
        certificate.write_bytes(gzip.compress(payload, mtime=0))
    data = json.loads(gzip.decompress(certificate.read_bytes()))
    assert data['schema'] == 1 and data['local_points'] == POINTS
    assert data['fixed_mate'] == [i ^ 1 for i in range(POINTS)]
    assert data['near_label_for_local_point'] == [i + 2 for i in range(POINTS)]
    assert data['transport_direction'] == 'input matching to canonical matching'
    assert data['record_columns'] == ['base12_partner_code', 'orbit_index', 'base12_transport_code']
    assert data['summaries'] == summaries and data['transports'] == records
    checked = set()
    for code, orbit, image_code in data['transports']:
        partner, image = decode(code), decode(image_code)
        assert partner in matchings_seen and partner not in checked
        checked.add(partner)
        assert sorted(image) == list(range(POINTS))
        assert all(image[i ^ 1] == (image[i] ^ 1) for i in range(POINTS))
        assert act(partner, image) == canonical_matching(summaries[orbit]['partition'])
    assert checked == matchings_seen
    result = {'status': 'complete exact coverage PASS', 'perfect_matchings': 10395,
              'matching_orbits': 11, 'explicit_transports_verified': len(checked),
              'independent_generator_orbits_verified': 11, 'summaries': summaries,
              'certificate_sha256': hashlib.sha256(certificate.read_bytes()).hexdigest(),
              'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'seconds': time.monotonic() - started, 'SAT_model_built': False,
              'solver_called': False}
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    run(args.certificate, args.write)
