"""Integer replay of partial two-grid edge points and necessary lazy clauses."""

import argparse
from collections import Counter
import hashlib
from itertools import combinations, product
import json
from pathlib import Path

from two_rook_iso_completion import core, rook, check_incidence, allowed_edges


def replay(record):
    rows = core()
    signatures = [(i, 9+i) for i in range(9)]
    signatures += [(i, 9+j) for i, j in product(range(9), repeat=2)
                   if i != j and not rook(i, j) for copy in range(2)]
    need = check_incidence(rows, signatures)
    edges = set(allowed_edges(signatures, need))
    assert len(edges) == 3060
    source = Path(__file__).with_name('two_rook_iso_pair_integer.py')
    assert hashlib.sha256(source.read_bytes()).hexdigest() == record['metadata']['source_sha256']
    cuts, seen, defect_counts = [], set(), []
    for point in record['points']:
        adjacency = rows[:]+[0]*81
        for a, sites in enumerate(signatures, 18):
            for b in sites:
                adjacency[a] |= 1 << b
                adjacency[b] |= 1 << a
        selected = [tuple(edge) for edge in point['selected_edges']]
        assert len(selected) == len(set(selected)) == 486
        assert set(selected) <= edges
        for a, b in selected:
            adjacency[18+a] |= 1 << (18+b)
            adjacency[18+b] |= 1 << (18+a)
        assert all(row.bit_count() == 14 for row in adjacency)
        assert all((adjacency[i] & adjacency[j]).bit_count()+((adjacency[i] >> j) & 1) == 2
                   for i in range(18) for j in range(i+1, 99))
        histogram, defects = Counter(), []
        for i, j in combinations(range(99), 2):
            difference = (adjacency[i] & adjacency[j]).bit_count()+((adjacency[i] >> j) & 1)-2
            histogram[difference] += 1
            if difference:
                defects.append([i, j, difference])
        assert [[k, v] for k, v in sorted(histogram.items())] == point['common_neighbor_defect_histogram']
        assert len(defects) == point['defective_pairs']
        assert defects[:30] == point['first_defects']
        assert [[a, b] for a, b in selected if a < 9 and b < 9] == point['tip_edges']
        defect_counts.append(len(defects))
        violations = 0
        for a, b in combinations(range(81), 2):
            i, j = 18+a, 18+b
            overlap = len(set(signatures[a]) & set(signatures[b]))
            if overlap == 2:
                assert not (adjacency[i] & adjacency[j]) >> 18
            units = [('edge', None)] if (adjacency[i] >> j) & 1 else []
            units += [('via', c) for c in range(81)
                      if (adjacency[i] >> (18+c)) & 1 and (adjacency[j] >> (18+c)) & 1]
            if len(units)+overlap <= 2:
                continue
            violations += 1
            witness = units[:3-overlap]
            cut = {'pair': [a, b], 'edge': any(kind == 'edge' for kind, _ in witness),
                   'via': [c for kind, c in witness if kind == 'via']}
            edge_terms = {(a, b)} if cut['edge'] else set()
            for c in cut['via']:
                edge_terms.add(tuple(sorted((a, c))))
                edge_terms.add(tuple(sorted((b, c))))
            assert edge_terms <= edges
            assert int(cut['edge'])+len(cut['via'])+overlap == 3
            key = tuple(sorted(edge_terms))
            if key not in seen:
                seen.add(key)
                cuts.append(cut)
        assert violations == point['outside_cap_violations']
    assert cuts == record['necessary_cuts']
    result = {'status': 'partial binary points and necessary cuts verified; no SRG found',
              'binary_points': len(record['points']), 'defective_pairs': defect_counts,
              'necessary_cuts': len(cuts), 'reported_search_status': record['status']}
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('record', type=Path)
    args = parser.parse_args()
    replay(json.loads(args.record.read_text()))
