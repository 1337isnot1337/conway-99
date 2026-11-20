"""Exact 18-component reduction on the globally prism-free x521=0 face.

Generation uses nauty only to merge isomorphic 21-vertex descriptions.
Replay verifies every saved transport directly, using the standard library.
No incidence optimizer or exterior-edge solver is called.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[2]


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def sha(value):
    return hashlib.sha256(value).hexdigest()


def edge(rows, a, b):
    assert a != b
    rows[a] |= 1 << b
    rows[b] |= 1 << a


def matchings(sites):
    if not sites:
        yield ()
        return
    a = sites[0]
    for b in sites[1:]:
        rest = tuple(v for v in sites if v not in (a, b))
        for tail in matchings(rest):
            partner = {a: b, b: a}
            for x, y in tail:
                partner[x] = y
                partner[y] = x
            yield ((a, b),) + tail


def partner(edges, size):
    result = [-1] * size
    for a, b in edges:
        assert result[a] == result[b] == -1
        result[a], result[b] = b, a
    assert all(v >= 0 for v in result)
    return result


def component_sizes(rows):
    unseen, sizes = set(range(len(rows))), []
    while unseen:
        stack, seen = [min(unseen)], set()
        while stack:
            a = stack.pop()
            if a in seen:
                continue
            seen.add(a)
            stack.extend(b for b in range(len(rows)) if rows[a] >> b & 1 and b not in seen)
        unseen -= seen
        sizes.append(len(seen))
    return sorted(sizes)


def core(first, second, third, q):
    n = len(first)
    assert all(len(v) == n for v in (second, third, q))
    rows = [0] * (3 + 3*n)
    for a, b in combinations(range(3), 2):
        edge(rows, a, b)
    for fiber, matching in enumerate((first, second, third)):
        for a in range(n):
            edge(rows, fiber, 3+n*fiber+a)
            edge(rows, 3+n*fiber+a, 3+n*fiber+matching[a])
    for a in range(n):
        edge(rows, 3+a, 3+n+a)
        edge(rows, 3+a, 3+2*n+a)
        edge(rows, 3+n+a, 3+2*n+q[a])
    return rows


def caps(rows):
    return all((rows[a] & rows[b]).bit_count() + (rows[a] >> b & 1) <= 2
               for a, b in combinations(range(len(rows)), 2))


def alternating(first, second):
    rows = [0] * len(first)
    for matching in (first, second):
        for a, b in enumerate(matching):
            edge(rows, a, b)
    return [size//2 for size in component_sizes(rows)]


def transported(matching, q):
    inverse = [q.index(i) for i in range(len(q))]
    return [inverse[matching[q[i]]] for i in range(len(q))]


def prism_count(rows):
    triangles = [t for t in combinations(range(len(rows)), 3)
                 if all(rows[a] >> b & 1 for a, b in combinations(t, 2))]
    return sum(not(set(first) & set(second))
               and all(sum(rows[a] >> b & 1 for b in second) == 1 for a in first)
               and all(sum(rows[b] >> a & 1 for a in first) == 1 for b in second)
               for first, second in combinations(triangles, 2))


def input_domain():
    first = [i ^ 1 for i in range(6)]
    matching_pool = [partner(edges, 6) for edges in matchings(tuple(range(6)))]
    no_mate = sorted(m for m in matching_pool if all(m[i] != first[i] for i in range(6)))
    derangements = [list(q) for q in permutations(range(6)) if all(q[i] != i for i in range(6))]
    assert len(matching_pool) == 15 and len(no_mate) == 8 and len(derangements) == 265
    assert all(alternating(first, m) == [3] for m in no_mate)
    return first, no_mate, derangements


def valid_inputs(first, no_mate, derangements):
    for p_index, second in enumerate(no_mate):
        for r_index, third in enumerate(no_mate):
            for q_index, q in enumerate(derangements):
                pulled = transported(third, q)
                if any(second[i] == pulled[i] for i in range(6)):
                    continue
                rows = core(first, second, third, q)
                assert alternating(second, pulled) == [3]
                assert caps(rows)
                assert component_sizes([row >> 3 for row in rows[3:]]) == [18]
                yield (p_index, r_index, q_index), rows


def permute(rows, order):
    assert sorted(order) == list(range(len(rows)))
    return tuple(sum(((rows[order[i]] >> order[j]) & 1) << j for j in range(len(rows)))
                 for i in range(len(rows)))


def component_domain(rows):
    assert len(rows) == 21 and [row.bit_count() for row in rows] == [8]*3+[4]*18
    shell = [row >> 3 for row in rows[3:]]
    gram = [[12*int(i == j)+2-(rows[3+i] & rows[3+j]).bit_count()
             -((rows[3+i] >> (3+j)) & 1) for j in range(18)] for i in range(18)]
    assert all(gram[i][i] == 10 for i in range(18))
    assert all(value >= 0 for row in gram for value in row)
    assert [sum(gram[i][j] for j in range(18)) for i in range(18)] == [30]*18
    signatures, pair_only, profiles = [], 0, Counter()
    for triple in combinations(range(18), 3):
        profile = tuple(sum(v//6 == fiber for v in triple) for fiber in range(3))
        if max(profile) > 2:
            continue
        if any(gram[i][j] == 0 for i, j in combinations(triple, 2)):
            continue
        pair_only += 1
        mask = sum(1 << v for v in triple)
        if any(((shell[i] | (1 << i)) & mask).bit_count() > 2 for i in range(18)):
            continue
        signatures.append(list(triple))
        profiles[profile] += 1
    availability = [[sum(i in triple and j in triple for triple in signatures)
                     for j in range(18)] for i in range(18)]
    deficient = [[i, j, availability[i][j], gram[i][j]]
                 for i in range(18) for j in range(i, 18) if availability[i][j] < gram[i][j]]
    profile_counts = [[list(profile), count] for profile, count in sorted(profiles.items())]
    return {'core_rows': rows, 'shell_rows': shell, 'Gram': gram,
            'signature_domain': signatures, 'signature_domain_sha256': sha(canonical(signatures)),
            'pair_support_triples_before_mixed_filter': pair_only,
            'admissible_triples': len(signatures), 'profile_availability': profile_counts,
            'Gram_row_availability': availability, 'deficient_Gram_rows': deficient,
            'population_deficiency': len(signatures) < 60,
            'necessary_population': 60, 'necessary_profile111': 24,
            'necessary_profile210_total': 36, 'optimizer_called': False}


def controls():
    first = [i ^ 1 for i in range(12)]
    shifted = partner([(2*i+1, (2*i+2) % 12) for i in range(6)], 12)
    q = [(i+1) % 12 for i in range(12)]
    rows = core(first, shifted, shifted, q)
    edge_types = [alternating(first, shifted), alternating(first, shifted),
                  alternating(shifted, transported(shifted, q))]
    assert edge_types == [[6], [6], [6]]
    assert caps(rows) and prism_count(rows) == 0
    assert component_sizes([row >> 3 for row in rows[3:]]) == [36]
    # Fibers are the only shell neighbors of central vertices. Shell degree4
    # in the39-core prevents a shell vertex being a degree5 center of F.
    assert [row.bit_count() for row in rows] == [14]*3+[4]*36
    return {'connected36_local_control': {'core_rows': [str(v) for v in rows],
             'central_edge_partitions': edge_types, 'visible_cap_check': True,
             'internal_prisms': 0, 'internal_F_motifs': 0,
             'complete99_vertex_graph': False},
            'split_profile_counts': {'total_columns': 60, 'per_fiber_counts_0_1_2': [12,36,12],
                                     'profile111': 24, 'profile210': 36,
                                     'six210_counts': ['a','12-a','12-a','a','a','12-a'],
                                     'a_integer_range': [0,12]}}


def generate(path):
    import pynauty
    started = time.monotonic()
    first, no_mate, derangements = input_domain()
    keys, representatives, transports = {}, [], []
    for description, rows in valid_inputs(first, no_mate, derangements):
        graph = pynauty.Graph(21, directed=False,
            adjacency_dict={i: [j for j in range(21) if rows[i] >> j & 1] for i in range(21)})
        order = pynauty.canon_label(graph)
        key = permute(rows, order)
        if key not in keys:
            keys[key] = len(representatives)
            representatives.append({'description': list(description), 'canonical_order': order,
                                    'domain': component_domain(rows), 'members': 0})
        index = keys[key]
        representative = representatives[index]
        representative['members'] += 1
        image = [0]*21
        for v, w in zip(representative['canonical_order'], order):
            image[v] = w
        assert permute(rows, image) == tuple(representative['domain']['core_rows'])
        transports.append([*description, index, image])
    result = {'status': 'complete normalized18-component domain census; no optimizer called',
              'source_sha256': sha(Path(__file__).read_bytes()),
              'scope': 'globally prism-free SRG(99,14,1,2) with x521=0 and a split18+18 triangle shell',
              'raw_normalized_shells': 8*8*265, 'retained_shells': len(transports),
              'isomorphism_representatives': len(representatives),
              'representatives': representatives, 'transports': transports, 'controls': controls(),
              'full_graph_completion_claimed': False, 'optimizer_called': False}
    raw = canonical(result)+b'\n'
    assert not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(gzip.compress(raw, mtime=0))
    summary = {key: result[key] for key in ('status','raw_normalized_shells','retained_shells',
                                          'isomorphism_representatives','scope')}
    summary.update(elapsed_seconds=time.monotonic()-started,
                   domain_sizes=[r['domain']['admissible_triples'] for r in representatives],
                   elementary_exclusions=[i for i,r in enumerate(representatives)
                       if r['domain']['deficient_Gram_rows'] or r['domain']['population_deficiency']],
                   compressed_sha256=sha(path.read_bytes()), decompressed_sha256=sha(raw))
    print(json.dumps(summary, indent=2), flush=True)


def replay(path):
    started = time.monotonic()
    result = json.loads(gzip.decompress(path.read_bytes()))
    assert result['source_sha256'] == sha(Path(__file__).read_bytes())
    first, no_mate, derangements = input_domain()
    representatives = result['representatives']
    counts = Counter()
    expected = list(valid_inputs(first, no_mate, derangements))
    assert len(expected) == len(result['transports']) == result['retained_shells']
    for (description, rows), record in zip(expected, result['transports']):
        p, r, q, index, image = record
        assert description == (p,r,q)
        assert permute(rows, image) == tuple(representatives[index]['domain']['core_rows'])
        counts[index] += 1
    for i, representative in enumerate(representatives):
        p, r, q = representative['description']
        rows = core(first, no_mate[p], no_mate[r], derangements[q])
        assert representative['domain'] == component_domain(rows)
        assert representative['members'] == counts[i]
        assert prism_count(rows) == 0
    assert result['controls'] == controls()
    print(json.dumps({'status': 'PASS: complete raw coverage, explicit isomorphisms, triple domains and controls',
                      'retained_shells': len(expected), 'representatives': len(representatives),
                      'standard_library_only': True, 'optimizer_called': False,
                      'elapsed_seconds': time.monotonic()-started}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', required=True, type=Path)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    (replay if args.replay else generate)(args.certificate.resolve())
