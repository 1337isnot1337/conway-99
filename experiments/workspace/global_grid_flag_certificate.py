"""Exact certificate for 29*g - 4*b <= 3465.

Here g counts all induced rook grids and b counts all-red grids. This
standard-library verifier checks every one of the 2^21 labeled seven-axis
graphs, using only necessary local support restrictions, and every one of
the 1596 unordered grid-line profiles. It does not run an optimizer or
depend on a graph-isomorphism catalogue.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations, combinations_with_replacement
import json
from pathlib import Path
import time


SCALE = 180
POINT_WEIGHT = 3696
CROSSING_WEIGHT = 62
PAIR_KEYS = tuple(combinations_with_replacement(range(1, 7), 2))


def pair_weight(key):
    return -487 if key == (2, 2) else -332 if key == (6, 6) else -456


def cover_weight(key):
    if key == (2, 2):
        return 0
    if key == (6, 6):
        return 44
    return 160 if 6 in key else 31


def edge_count_between(adjacency, a, b, equal):
    count = 0
    while a:
        bit = a & -a
        count += (adjacency[bit.bit_length()-1] & b).bit_count()
        a ^= bit
    return count // 2 if equal else count


def verify_root_columns():
    """Check a necessary superset of the frozen model's local root types."""
    edges = tuple(combinations(range(7), 2))
    adjacency = [0]*7
    degrees = [0]*7
    degree_masks = [127]+[0]*6
    degree_counts = [7]+[0]*6
    edge_count = 0
    adjacent_edge_pairs = 0
    filters = Counter()
    slack_counts = Counter()
    zero_examples = []
    covers_by_edge_count = {
        e: tuple((a, b, cover_weight((a, b))) for a, b in PAIR_KEYS
                 if a+b == e+1 and cover_weight((a, b)))
        for e in range(12)
    }
    for step in range(1 << 21):
        if step:
            # Consecutive binary-reflected Gray words differ at the index
            # of the least significant nonzero bit of step.
            k = (step & -step).bit_length()-1
            u, v = edges[k]
            old_u, old_v = degrees[u], degrees[v]
            adding = not (adjacency[u] >> v) & 1
            delta = 1 if adding else -1
            adjacent_edge_pairs += old_u+old_v if adding else -old_u-old_v+2
            edge_count += delta
            adjacency[u] ^= 1 << v
            adjacency[v] ^= 1 << u
            for point, old in ((u, old_u), (v, old_v)):
                new = old+delta
                degree_masks[old] ^= 1 << point
                degree_masks[new] ^= 1 << point
                degree_counts[old] -= 1
                degree_counts[new] += 1
                degrees[point] = new
        if edge_count > 15:
            filters['more_than_fifteen_edges'] += 1
            continue
        # Degree five in D means a support vertex of degree one in its
        # complement. The unique incident support vector would be zero.
        if degree_counts[5]:
            filters['degree_five_vertex'] += 1
            continue
        # These degree sequences uniquely describe K_r join
        # (K_(5-r) disjoint-union 2K1), r=1,2. The shared edge of the
        # complementary book is forced to have zero support vector.
        book_one = degree_counts[6] == 1 and degree_counts[4] == 4 and degree_counts[1] == 2
        book_two = degree_counts[6] == 2 and degree_counts[4] == 3 and degree_counts[2] == 2
        if book_one or book_two:
            filters['forbidden_book_complement'] += 1
            continue
        disjoint = edge_count*(edge_count-1)//2-adjacent_edge_pairs
        pair_22 = edge_count_between(adjacency, degree_masks[2], degree_masks[2], True)
        pair_66 = degree_counts[6]*(degree_counts[6]-1)//2
        cover_cost = 0
        if edge_count <= 11:
            for a, b, weight in covers_by_edge_count[edge_count]:
                cover_cost += weight*edge_count_between(adjacency, degree_masks[a], degree_masks[b], a == b)
        slack = (POINT_WEIGHT-456*edge_count-31*pair_22+124*pair_66
                 +CROSSING_WEIGHT*disjoint-cover_cost)
        assert slack >= 0, (step ^ (step >> 1), degrees, slack)
        filters['checked_root_columns'] += 1
        slack_counts[slack] += 1
        if slack == 0 and len(zero_examples) < 12:
            zero_examples.append(step ^ (step >> 1))
    assert sum(filters.values()) == 1 << 21
    return {'all_labeled_axis_graphs': 1 << 21,
            'filters': dict(sorted(filters.items())),
            'minimum_scaled_slack': min(slack_counts),
            'zero_slack_labeled_columns': slack_counts[0],
            'scaled_slack_histogram': [[slack, count] for slack, count in sorted(slack_counts.items())],
            'first_zero_slack_graph_masks': zero_examples}


def verify_grid_columns():
    triples = tuple(combinations_with_replacement(range(1, 7), 3))
    slacks = Counter()
    red_cases = {}
    checked = 0
    for rows, columns in combinations_with_replacement(triples, 2):
        pair_counts = Counter()
        cover_counts = Counter()
        red_rows = rows.count(6)
        red_columns = columns.count(6)
        for i, j in product_indices():
            key = tuple(sorted((rows[i], columns[j])))
            pair_counts[key] += 1
            if red_rows-int(rows[i] == 6) > 0 and red_columns-int(columns[j] == 6) > 0:
                cover_counts[key] += 1
        is_all_red = rows == columns == (6, 6, 6)
        target = SCALE*(29-4*int(is_all_red))
        column = (18*CROSSING_WEIGHT
                  -sum(pair_weight(key)*count for key, count in pair_counts.items())
                  +sum(cover_weight(key)*count for key, count in cover_counts.items()))
        slack = column-target
        assert slack >= 0, (rows, columns, slack)
        # Independent closed formula for the grid-side verification.
        red_case = tuple(sorted((red_rows, red_columns)))
        if red_case[0] == 0:
            expected = 31*pair_counts[2, 2]
        else:
            expected = {(1, 1): 0, (1, 2): 454, (1, 3): 588,
                        (2, 2): 351, (2, 3): 0, (3, 3): 0}[red_case]
        assert slack == expected
        red_cases.setdefault(red_case, Counter())[slack] += 1
        slacks[slack] += 1
        checked += 1
    assert checked == 1596
    return {'grid_line_profiles': checked, 'minimum_scaled_slack': min(slacks),
            'zero_slack_columns': slacks[0],
            'scaled_slack_histogram': [[slack, count] for slack, count in sorted(slacks.items())],
            'red_row_column_cases': [
                {'red_counts': list(key), 'scaled_slacks': [[s, n] for s, n in sorted(values.items())]}
                for key, values in sorted(red_cases.items())]}


def product_indices():
    return ((i, j) for i in range(3) for j in range(3))


def verify():
    roots = verify_root_columns()
    grids = verify_grid_columns()
    right_hand_side = POINT_WEIGHT*99+CROSSING_WEIGHT*4158
    assert right_hand_side == SCALE*3465
    assert all(cover_weight(key) >= 0 for key in PAIR_KEYS)
    return {'inequality': '29*g - 4*b <= 3465', 'scale': SCALE,
            'point_equality_weight': POINT_WEIGHT,
            'crossing_inequality_weight': CROSSING_WEIGHT,
            'degree_pair_equality_weights': [{'degrees': list(key), 'weight': pair_weight(key)} for key in PAIR_KEYS],
            'cover_inequality_weights': [{'degrees': list(key), 'weight': cover_weight(key)} for key in PAIR_KEYS],
            'triangle_population_equality_weights': [0]*7,
            'all_red_cap_row_used': False,
            'scaled_right_hand_side': right_hand_side,
            'root_column_check': roots, 'grid_column_check': grids,
            'integer_consequence_for_b_at_most_three': (3465+4*3)//29}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--write', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    start = time.monotonic()
    result = verify()
    if args.verify:
        assert json.loads(args.verify.read_text()) == result
    if args.write:
        args.write.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'inequality': result['inequality'],
                      'all_red_cap_row_used': False,
                      'labeled_root_graphs': result['root_column_check']['all_labeled_axis_graphs'],
                      'root_filters': result['root_column_check']['filters'],
                      'grid_profiles': result['grid_column_check']['grid_line_profiles'],
                      'minimum_scaled_root_slack': result['root_column_check']['minimum_scaled_slack'],
                      'minimum_scaled_grid_slack': result['grid_column_check']['minimum_scaled_slack'],
                      'scaled_rhs': result['scaled_right_hand_side'],
                      'replayed_saved_certificate': bool(args.verify),
                      'seconds': time.monotonic()-start}), flush=True)
