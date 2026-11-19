"""Exact PSD scan of the saved Hall-strengthened two-grid transcript.

The certificate embeds every audited tip graph and all matrix witnesses.
An optional raw or gzipped source transcript verifies the uncompressed hash.
No search for graph completions is performed here.
"""

import argparse
from collections import Counter
from fractions import Fraction
from functools import reduce
import gzip
import hashlib
from itertools import combinations, product
import json
from math import gcd
from pathlib import Path

import two_rook_tip_psd_audit as psd


def payload(path):
    data = path.read_bytes()
    return gzip.decompress(data) if data[:2] == b'\x1f\x8b' else data


def cap_witnesses(edges):
    neighbors = [set() for _ in range(9)]
    for a, b in edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    answer = []
    for a, b in combinations(range(9), 2):
        common = sorted(neighbors[a] & neighbors[b])
        adjacent = b in neighbors[a]
        if len(common)+int(adjacent) > 2:
            answer.append({'pair': [a, b], 'adjacent': adjacent,
                           'common_tip_neighbors': common,
                           'cap_value': len(common)+int(adjacent)})
    return answer


def short_negative(matrix, fallback):
    # This bounded vector simplification is not a graph search.
    for size in range(1, 10):
        for support in combinations(range(9), size):
            for tail in product((-1, 1), repeat=size-1):
                signs = (1, *tail)
                value = 4*size+2*sum(matrix[a][b]*signs[i]*signs[j]
                                    for i, a in enumerate(support)
                                    for j, b in enumerate(support) if i < j)
                if value < 0:
                    vector = [0]*9
                    for a, sign in zip(support, signs):
                        vector[a] = sign
                    assert psd.quadratic(matrix, vector) == value
                    return vector
    scale = max(map(abs, fallback))
    for bound in range(1, 101):
        vector = [round(Fraction(bound*x, scale)) for x in fallback]
        if psd.quadratic(matrix, vector) < 0:
            return psd.primitive(vector)
    return fallback


def normalized_cut(vector):
    cut = psd.edge_cut(vector)
    divisor = reduce(gcd, (abs(c) for _, _, c in cut['terms']))
    assert divisor > 0
    terms = [[a, b, c//divisor] for a, b, c in cut['terms']]
    rhs = cut['rhs']//divisor
    # Signed integer coefficients can be encoded with positive weights on
    # literals: replace a negative coefficient on z by its weight on not z.
    literal_terms = [[a, b, c > 0, abs(c)] for a, b, c in terms]
    literal_rhs = rhs+sum(-c for _, _, c in terms if c < 0)
    return {'signed_terms': terms, 'rhs': rhs, 'divisor': divisor,
            'raw_rhs': cut['rhs'],
            'positive_weight_literals': literal_terms,
            'positive_weight_rhs': literal_rhs}


def generate(input_path):
    data = payload(input_path)
    source = json.loads(data)
    points = []
    for index, point in enumerate(source['points']):
        edges = point['tip_edges']
        matrix = psd.tip_matrix(edges)
        certificate = psd.congruence(matrix)
        row = {'point_index': index, 'tip_edges': edges,
               'matrix_certificate': certificate,
               'tip_cap_violations': cap_witnesses(edges)}
        if certificate['status'] == 'not PSD':
            vector = short_negative(matrix, certificate['negative_vector'])
            value = psd.quadratic(matrix, vector)
            assert value < 0
            row.update(short_negative_vector=vector, quadratic_value=value,
                       necessary_edge_cut=normalized_cut(vector))
        points.append(row)
    return {'source_logical_name': input_path.name.removesuffix('.gz'),
            'source_uncompressed_sha256': hashlib.sha256(data).hexdigest(),
            'source_status': source['status'],
            'frozen_psd_helper_sha256': hashlib.sha256(Path(psd.__file__).read_bytes()).hexdigest(),
            'points': points}


def verify(record, input_path=None):
    assert record['frozen_psd_helper_sha256'] == hashlib.sha256(Path(psd.__file__).read_bytes()).hexdigest()
    if input_path is not None:
        data = payload(input_path)
        assert hashlib.sha256(data).hexdigest() == record['source_uncompressed_sha256']
        source = json.loads(data)
        assert source['status'] == record['source_status']
        assert [p['tip_edges'] for p in source['points']] == [p['tip_edges'] for p in record['points']]
    summary = []
    singular = []
    for index, point in enumerate(record['points']):
        assert point['point_index'] == index
        edges = point['tip_edges']
        matrix = psd.tip_matrix(edges)
        certificate = point['matrix_certificate']
        psd.verify_congruence(matrix, certificate)
        caps = cap_witnesses(edges)
        assert point['tip_cap_violations'] == caps
        if certificate['status'] == 'not PSD':
            vector = point['short_negative_vector']
            assert all(type(x) is int for x in vector)
            value = psd.quadratic(matrix, vector)
            assert value == point['quadratic_value'] < 0
            cut = normalized_cut(vector)
            assert point['necessary_edge_cut'] == cut
            edge_set = {tuple(edge) for edge in edges}
            lhs = sum(c for a, b, c in cut['signed_terms'] if (a, b) in edge_set)
            literal_lhs = sum(weight for a, b, positive, weight in cut['positive_weight_literals']
                              if ((a, b) in edge_set) == positive)
            assert lhs > cut['rhs'] and literal_lhs > cut['positive_weight_rhs']
            summary.append({'point_index': index, 'negative_vector': vector,
                            'quadratic_value': value, 'cut_lhs': lhs, 'cut_rhs': cut['rhs'],
                            'tip_cap_violations': len(caps),
                            'already_excluded_by_complete_tip_caps': bool(caps)})
        elif certificate['rank'] < 9:
            singular.append(index)
    ranks = Counter(p['matrix_certificate'].get('rank') for p in record['points']
                    if p['matrix_certificate']['status'] == 'PSD')
    cap_compatible_overlaps = Counter(sum(psd.rook(a, b) for a, b in p['tip_edges'])
                                     for p in record['points'] if not p['tip_cap_violations'])
    for point in record['points']:
        edges = {tuple(edge) for edge in point['tip_edges']}
        if any(psd.rook(a, b) for a, b in edges):
            continue
        gram = [[0]*9 for _ in range(9)]
        for a, b in combinations(range(9), 2):
            if psd.rook(a, b):
                continue
            sign = 1-2*int((a, b) in edges)
            gram[a][a] += 1
            gram[b][b] += 1
            gram[a][b] += sign
            gram[b][a] += sign
        assert gram == psd.tip_matrix(point['tip_edges'])
    return {'status': 'exact Hall-run tip PSD replay passed',
            'source_status': record['source_status'],
            'points': len(record['points']),
            'distinct_tip_graphs': len({tuple(tuple(e) for e in p['tip_edges']) for p in record['points']}),
            'PSD_ranks': dict(sorted(ranks.items())), 'singular_point_indices': singular,
            'cap_compatible_tip_graph_points': sum(not p['tip_cap_violations'] for p in record['points']),
            'cap_compatible_rook_edge_overlap_distribution': dict(sorted(cap_compatible_overlaps.items())),
            'PSD_failures': summary,
            'PSD_failures_passing_complete_tip_caps': sum(not p['tip_cap_violations'] for p in record['points']
                                                         if p['matrix_certificate']['status'] == 'not PSD')}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        assert args.input
        record = generate(args.input)
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(verify(json.loads(args.certificate.read_text()), args.input), indent=2))
