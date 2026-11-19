"""Exact high-edge order-nine census and two-isomorphic-rook tip bound.

The catalogue is freshly rebuilt, not loaded from the count cache.
This tool checks the small census and arithmetic controls. The separate
joint-model DRAT certificate is a theorem dependency, not replayed here.
"""

import argparse
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path

from subgraph_counts import build


def rook_rows():
    return [sum(1 << j for j in range(9) if i != j and
                (i//3 == j//3 or i % 3 == j % 3)) for i in range(9)]


def edge_count(rows):
    return sum(row.bit_count() for row in rows)//2


def isomorphism(source, target):
    """Find an explicit permutation, independent of canonical labelling."""
    n = len(source)
    source_degree = [row.bit_count() for row in source]
    target_degree = [row.bit_count() for row in target]
    mapping = [-1]*n

    def extend(used):
        if len(used) == n:
            return mapping[:]
        candidates = []
        for a in range(n):
            if mapping[a] != -1:
                continue
            choices = [b for b in range(n) if b not in used and target_degree[b] == source_degree[a]
                       and all(((source[a] >> c) & 1) == ((target[b] >> mapping[c]) & 1)
                               for c in range(n) if mapping[c] != -1)]
            candidates.append((len(choices), a, choices))
        _, a, choices = min(candidates)
        for b in choices:
            mapping[a] = b
            answer = extend(used | {b})
            if answer is not None:
                return answer
        mapping[a] = -1
        return None

    result = extend(set())
    assert result is not None and sorted(result) == list(range(n))
    assert all(((source[a] >> b) & 1) == ((target[result[a]] >> result[b]) & 1)
               for a, b in combinations(range(n), 2))
    return result


def checks():
    root = rook_rows()
    broken = root[:]
    broken[0] ^= 1 << 1
    broken[1] ^= 1 << 0
    assert edge_count(root) == 18 and edge_count(broken) == 17
    assert all((rows[a] & rows[b]).bit_count()+((rows[a] >> b) & 1) <= 2
               for rows in (root, broken) for a, b in combinations(range(9), 2))
    degrees = [row.bit_count() for row in broken]
    restricted_vector = [4-d for d in degrees]
    assert restricted_vector == [1, 1, 0, 0, 0, 0, 0, 0, 0]
    assert (broken[0] >> 2) & 1 and (broken[1] >> 2) & 1
    norm = 7*(3*9-2*17+9*9//9)
    assert norm == 14
    lower = 7*comb(4, 2)
    upper = 2*comb(7, 2)
    assert lower == upper == 42
    allowed = [(e, t) for e in range(19) if e != 17 for t in range(e//2+1)
               if e != 18 or t == 0]
    maximum = max(4*e+t for e, t in allowed)
    equality = [[e, t] for e, t in allowed if 4*e+t == maximum]
    assert maximum == 72 and equality == [[16, 8], [18, 0]]
    return root, broken, {
        'broken_rook_degrees': degrees, 'restricted_integral_vector': restricted_vector,
        'zero_coordinate_common_neighbor_of_deleted_endpoints': 2,
        'projected_squared_norm': norm, 'large_coordinate_squared_norm_floor': 16,
        'signed_pair_count_lower': lower, 'signed_pair_count_upper': upper,
        'maximum_4e_plus_t': maximum, 'equality_pairs': equality,
    }


def generate(boundary_proof):
    root, broken, control = checks()
    graphs, levels, automorphisms, _ = build(9)
    assert [len(level) for level in levels] == [1, 1, 2, 4, 9, 21, 62, 208, 916, 5311]
    assert len(graphs) == 6535
    high = []
    for index in levels[9]:
        rows = graphs[index]
        edges = edge_count(rows)
        assert edges <= 18
        if edges < 17:
            continue
        target = root if edges == 18 else broken
        high.append({'catalogue_index': index, 'edges': edges, 'adjacency_rows': list(rows),
                     'identified_as': 'rook' if edges == 18 else 'rook minus one edge',
                     'automorphism_order': automorphisms[index],
                     'isomorphism_to_standard_target': isomorphism(rows, target)})
    assert [item['edges'] for item in high] == [17, 18]
    return {'scope': 'fresh order-nine high-edge census and arithmetic controls; no solver run',
            'catalogue_types': len(graphs), 'order_nine_types': len(levels[9]),
            'levels': [len(level) for level in levels],
            'standard_rook_rows': root, 'standard_broken_rook_rows': broken,
            'high_edge_types': high, 'controls': control,
            'checked_boundary_proof_dependency': {
                'logical_name': boundary_proof.name,
                'sha256': hashlib.sha256(boundary_proof.read_bytes()).hexdigest(),
                'scope': 'excludes the18-labelled non-complement boundary orbit; DRAT replay is separate'},
            'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def verify(record, boundary_proof):
    expected = generate(boundary_proof)
    assert record == expected
    # Verify the saved identifications directly, without canonical certificates.
    for item in record['high_edge_types']:
        target = record['standard_rook_rows'] if item['edges'] == 18 else record['standard_broken_rook_rows']
        permutation = item['isomorphism_to_standard_target']
        assert sorted(permutation) == list(range(9))
        assert all(((item['adjacency_rows'][a] >> b) & 1)
                   == ((target[permutation[a]] >> permutation[b]) & 1)
                   for a, b in combinations(range(9), 2))
    return {'status': 'fresh high-edge census, explicit isomorphisms, and arithmetic controls passed',
            'order_nine_types': record['order_nine_types'],
            'seventeen_edge_types': sum(item['edges'] == 17 for item in record['high_edge_types']),
            'eighteen_edge_types': sum(item['edges'] == 18 for item in record['high_edge_types']),
            'maximum_4e_plus_t': 72, 'equality_pairs': record['controls']['equality_pairs'],
            'proof_scope': 'the17-edge norm argument and separately checked18-edge boundary proof are stated in the accompanying note',
            'solver_launched': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--boundary-proof', type=Path, required=True)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        record = generate(args.boundary_proof)
        args.certificate.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(verify(json.loads(args.certificate.read_text()), args.boundary_proof), indent=2))
