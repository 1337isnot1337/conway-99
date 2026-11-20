"""Maximum near-anchor count: an exhaustive new eleven-case convention.

This does not preserve each original case individually. It preserves the
union by first choosing a near anchor of maximum mate-coincident matching
count, then normalizing that anchor's matching. No full CNF is built and
no solver is called. The standard-library controls check the count domain,
relabelings, clauses, and the direct nine-vertex rook graph.
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations, product
import json
from math import comb
from pathlib import Path

from root_full_caps_coverage import all_matchings, canonical_matching, canonical_transport, partitions


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def domain(degree):
    assert degree in (4, 14)
    labels = [pair for pair in combinations(range(degree), 2) if pair[0] ^ 1 != pair[1]]
    index = {pair: i for i, pair in enumerate(labels)}
    edges = list(combinations(range(len(labels)), 2))
    variables = {edge: i+1 for i, edge in enumerate(edges)}
    supports = []
    for anchor in range(degree):
        support = []
        for axis in range(degree//2):
            if axis == anchor//2:
                continue
            first = index[tuple(sorted((anchor, 2*axis)))]
            second = index[tuple(sorted((anchor, 2*axis+1)))]
            support.append(variables[tuple(sorted((first, second)))])
        supports.append(support)
    assert all(len(row) == (degree-2)//2 for row in supports)
    assert len(set(sum(supports, []))) == degree*(degree-2)//2
    return labels, index, edges, variables, supports


def matching(positive, anchor, degree):
    labels, _, edges, variables, _ = domain(degree)
    result = []
    for a, b in edges:
        if variables[a, b] in positive and anchor in labels[a] and anchor in labels[b]:
            first, = set(labels[a])-{anchor}
            second, = set(labels[b])-{anchor}
            result.append(tuple(sorted((first, second))))
    expected = [v for v in range(degree) if v//2 != anchor//2]
    assert sorted(v for edge in result for v in edge) == expected
    return tuple(sorted(result))


def edge_permutation(near_image, degree):
    labels, index, edges, variables, _ = domain(degree)
    assert sorted(near_image) == list(range(degree))
    assert all(near_image[i ^ 1] == (near_image[i] ^ 1) for i in range(degree))
    outside = [index[tuple(sorted((near_image[a], near_image[b])))] for a, b in labels]
    result = [variables[tuple(sorted((outside[a], outside[b])))] for a, b in edges]
    assert sorted(result) == list(range(1, len(edges)+1))
    return result


def normalize(positive, degree, chosen=None):
    _, _, _, _, supports = domain(degree)
    counts = [sum(v in positive for v in row) for row in supports]
    for anchor in range(degree):
        assert counts[anchor] == sum(a ^ 1 == b for a, b in matching(positive, anchor, degree))
    if chosen is None:
        chosen = min(a for a in range(degree) if counts[a] == max(counts))
    assert counts[chosen] == max(counts)
    axis_order = list(range(degree//2))
    axis_order[0], axis_order[chosen//2] = axis_order[chosen//2], axis_order[0]
    move = [2*axis_order[a]+(s ^ int(a == chosen//2 and chosen % 2))
            for a in range(degree//2) for s in range(2)]
    assert move[chosen] == 0 and move[chosen ^ 1] == 1
    local = tuple(sorted(tuple(sorted((move[a]-2, move[b]-2)))
                         for a, b in matching(positive, chosen, degree)))
    parts, canonical_to_local = canonical_transport(local, (degree-2)//2)
    inverse = [0]*(degree-2)
    for old, new in enumerate(canonical_to_local):
        inverse[new] = old
    gauge = [0, 1]+[2+i for i in inverse]
    near_image = [gauge[move[a]] for a in range(degree)]
    edge_image = edge_permutation(near_image, degree)
    normalized = {edge_image[v-1] for v in positive}
    actual = tuple(sorted((a-2, b-2) for a, b in matching(normalized, 0, degree)))
    assert actual == canonical_matching(parts)
    updated = [sum(v in normalized for v in row) for row in supports]
    assert updated[0] == max(updated) == parts.count(1)
    assert all(updated[near_image[a]] == counts[a] for a in range(degree))
    return parts, normalized, near_image


def clauses(parts, degree=14):
    _, _, _, _, supports = domain(degree)
    bound = parts.count(1)
    return [[-v for v in subset] for row in supports for subset in combinations(row, bound+1)]


def partial_controls():
    degree = 14
    _, index, _, variables, _ = domain(degree)
    count = 0
    for chosen in range(degree):
        for parts in partitions(6):
            positive = set()
            for anchor in range(degree):
                other = [a for a in range(degree) if a//2 != anchor//2]
                row_parts = parts if anchor == chosen else (6,)
                for a, b in canonical_matching(row_parts):
                    first = index[tuple(sorted((anchor, other[a])))]
                    second = index[tuple(sorted((anchor, other[b])))]
                    positive.add(variables[tuple(sorted((first, second)))])
            # These controls have all fourteen required fiber matchings,
            # but are not claimed to satisfy the remaining SRG equations.
            assert len(positive) == 84
            normalized_parts, normalized, _ = normalize(positive, degree, chosen)
            assert normalized_parts == parts
            assert all(any(-v not in normalized for v in clause) for clause in clauses(parts))
            count += 1
    assert count == 154
    return count


def rook_control():
    labels, _, edges, variables, _ = domain(4)
    near = [(0, 1), (0, 2), (1, 0), (2, 0)]
    coords = [(0, 0)]+near+[(near[b][0], near[a][1]) for a, b in labels]
    grid = [[int(i != j and (a[0] == b[0] or a[1] == b[1]))
             for j, b in enumerate(coords)] for i, a in enumerate(coords)]
    positive = {variables[a, b] for a, b in edges if grid[5+a][5+b]}
    for chosen in range(4):
        parts, normalized, _ = normalize(positive, 4, chosen)
        assert parts == (1,)
        rows = [0]*9
        def join(a, b):
            rows[a] |= 1 << b
            rows[b] |= 1 << a
        for a in range(4):
            join(0, 1+a)
            join(1+a, 1+(a ^ 1))
        for i, signature in enumerate(labels):
            for a in signature:
                join(5+i, 1+a)
        for a, b in edges:
            if variables[a, b] in normalized:
                join(5+a, 5+b)
        assert all(row.bit_count() == 4 and not row >> i & 1 for i, row in enumerate(rows))
        assert all((rows[a] & rows[b]).bit_count()+int(rows[a] >> b & 1) == 2
                   for a, b in combinations(range(9), 2))
    return {'status': 'exact pass', 'anchor_choices': 4, 'pair_equations_per_choice': 36}


def generate():
    labels, _, edges, variables, supports = domain(14)
    rows = [sum(1 << (1+a) for a in range(14))]+[1 | 1 << (1+(a ^ 1)) for a in range(14)]
    domain_record = {'core_rows': rows, 'labels': labels,
                     'signatures': [(1+a, 1+b) for a, b in labels],
                     'edge_variables': [[a, b, v] for (a, b), v in variables.items()]}
    domain_hash = hashlib.sha256(json.dumps(domain_record, sort_keys=True,
                                          separators=(',', ':')).encode()).hexdigest()
    root = Path(__file__).resolve().parents[2]
    manifest_path = root/'experiments/logs/root-full-caps/model.json'
    manifest = json.loads(manifest_path.read_text())
    assert domain_hash == manifest['domain_sha256']
    histogram = Counter()
    for original in all_matchings(tuple(range(12))):
        parts, _ = canonical_transport(original, 6)
        same = sum(a ^ 1 == b for a, b in original)
        assert same == parts.count(1)
        histogram[same] += 1
    assert histogram == {0: 6040, 1: 3264, 2: 900, 3: 160, 4: 30, 6: 1}
    assert sum(histogram.values()) == 10395
    # Axis flips and adjacent axis interchanges generate the full signed
    # near-label group. Independently check their count-support action.
    generators = []
    for axis in range(7):
        image = list(range(14))
        image[2*axis], image[2*axis+1] = image[2*axis+1], image[2*axis]
        generators.append(image)
    for axis in range(6):
        image = list(range(14))
        for s in range(2):
            image[2*axis+s], image[2*(axis+1)+s] = image[2*(axis+1)+s], image[2*axis+s]
        generators.append(image)
    for image in generators:
        lifted = edge_permutation(image, 14)
        assert all({lifted[v-1] for v in supports[a]} == set(supports[image[a]]) for a in range(14))
    controls = 0
    for bound in (0, 1, 2, 3, 4, 6):
        forbidden = list(combinations(range(6), bound+1))
        for values in product((0, 1), repeat=6):
            actual = all(any(not values[i] for i in subset) for subset in forbidden)
            assert actual == (sum(values) <= bound)
            controls += 1
    assert controls == 384
    cases = []
    for index, parts in enumerate(partitions(6)):
        extra = clauses(parts)
        assert len(extra) == 14*(comb(6, parts.count(1)+1) if parts.count(1) < 6 else 0)
        if parts.count(1) == 0:
            assert sorted(-clause[0] for clause in extra) == sorted(sum(supports, []))
        cases.append({'index': index, 'partition': list(parts), 'maximum_near_count': parts.count(1),
                      'clauses': extra, 'clause_count': len(extra), 'added_variables': 0})
    return {'status': 'exact derivation/domain controls pass; no full CNF or solver',
            'scope': 'new maximum-anchor eleven-case union; not each original case separately',
            'base_manifest_sha256': digest(manifest_path), 'domain_sha256': domain_hash,
            'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in
                              ['root_full_caps_anchor_max.py', 'root_full_caps_coverage.py']},
            'matching_histogram': dict(sorted(histogram.items())), 'matchings_checked': 10395,
            'near_count_supports': supports, 'distinct_side_variables': 84,
            'signed_near_generators_checked': len(generators),
            'direct_atmost_assignments_checked': controls,
            'matching_domain_relabeling_controls': partial_controls(),
            'rook_positive_control': rook_control(), 'cases': cases,
            'graph_automorphism_assumptions': 0, 'full_cnf_built': False, 'solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = generate()
    if args.write:
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps(result, indent=2)+'\n')
    else:
        assert json.loads(args.certificate.read_text()) == json.loads(json.dumps(result))
    print(json.dumps({**{k: v for k, v in result.items() if k not in ('near_count_supports', 'cases')},
                      'cases': [{k: v for k, v in case.items() if k != 'clauses'}
                                for case in result['cases']]}), flush=True)
