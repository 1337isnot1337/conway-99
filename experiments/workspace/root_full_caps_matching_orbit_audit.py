"""Independent closed-form audit of rooted matching normalization.

No perfect-matching census, group-orbit BFS, or completion solver is used.
The orbit formula is checked against canonical representatives and total
matching counts. A separate64-case local-cell control checks the scope
of the broken-rook implications.
"""

import argparse
from collections import Counter
from itertools import combinations
import json
from math import factorial, prod
from pathlib import Path


def partitions(total, least=1):
    if not total:
        yield ()
    for part in range(least, total+1):
        for tail in partitions(total-part, part):
            yield (part, *tail)


def representative(parts):
    matching = []
    offset = 0
    for size in parts:
        for i in range(size):
            matching.append(tuple(sorted((2*(offset+i)+1, 2*(offset+(i+1) % size)))))
        offset += size
    assert sorted(x for edge in matching for x in edge) == list(range(2*sum(parts)))
    return sorted(matching)


def component_type(matching):
    n = len(matching)
    adjacency = [{i ^ 1} for i in range(2*n)]
    for a, b in matching:
        adjacency[a].add(b)
        adjacency[b].add(a)
    remaining = set(range(2*n))
    sizes = []
    while remaining:
        component = {min(remaining)}
        queue = list(component)
        for vertex in queue:
            for neighbor in adjacency[vertex]:
                if neighbor not in component:
                    component.add(neighbor)
                    queue.append(neighbor)
        assert len(component) % 2 == 0
        sizes.append(len(component)//2)
        remaining -= component
    return tuple(sorted(sizes))


def orbit_table(n):
    group_order = 2**n*factorial(n)
    table = []
    for parts in partitions(n):
        multiplicities = Counter(parts)
        numerator = 2**(n-len(parts))*factorial(n)
        denominator = prod(length**count*factorial(count) for length, count in multiplicities.items())
        assert numerator % denominator == 0
        size = numerator//denominator
        assert group_order % size == 0
        matching = representative(parts)
        assert component_type(matching) == parts
        table.append({'partition': list(parts), 'orbit_size': size,
                      'stabilizer_order': group_order//size,
                      'matching_on_neighbor_labels': [[a+2, b+2] for a, b in matching]})
    assert sum(row['orbit_size'] for row in table) == prod(range(1, 2*n, 2))
    return table


def local_cell_control():
    base = [(0, i) for i in range(1, 5)]+[(1, 2), (3, 4)]
    for i in range(2):
        for j in range(2):
            point = 5+2*i+j
            base.extend([(1+i, point), (3+j, point)])
    sides = [(5, 6), (7, 8), (5, 7), (6, 8)]
    diagonals = [(5, 8), (6, 7)]
    compatible = []
    for mask in range(64):
        adjacency = [0]*9
        for a, b in base+[edge for i, edge in enumerate(sides+diagonals) if mask >> i & 1]:
            adjacency[a] |= 1 << b
            adjacency[b] |= 1 << a
        valid = all((adjacency[a] & adjacency[b]).bit_count()+((adjacency[a] >> b) & 1) <= 2
                    for a, b in combinations(range(9), 2))
        if not valid:
            continue
        side_count = (mask & 15).bit_count()
        if side_count:
            assert mask >> 4 == 0
        compatible.append(mask)
        if side_count == 4:
            assert all(row.bit_count() == 4 for row in adjacency)
            assert all((adjacency[a] & adjacency[b]).bit_count()+((adjacency[a] >> b) & 1) == 2
                       for a, b in combinations(range(9), 2))
    assert len(compatible) == 19
    three_sides = [mask for mask in compatible if (mask & 15).bit_count() == 3]
    assert len(three_sides) == 4 and all(mask < 16 for mask in three_sides)
    assert all(mask in compatible for mask in (0, 16, 32, 48))
    return {'far_edge_assignments': 64, 'cap_compatible_assignments': 19,
            'cap_compatible_masks': compatible,
            'broken_rook_three_side_masks': three_sides,
            'diagonals_with_no_sides_not_excluded': [0, 16, 32, 48],
            'rook_positive_control_mask': 15,
            'four_implications_per_cell': 4, 'two_axis_cells_at_valency14': 21,
            'total_broken_rook_implications': 84}


def generate():
    smaller = {str(n): sum(row['orbit_size'] for row in orbit_table(n)) for n in range(1, 6)}
    table = orbit_table(6)
    assert len(table) == 11
    return {'scope': 'closed-form matching orbit coverage and conditional broken-rook cell control',
            'fixed_mates': [[2*i+2, 2*i+3] for i in range(6)],
            'group_order': 46080, 'perfect_matchings': 10395, 'orbits': table,
            'smaller_axis_count_controls': smaller, 'local_cell_control': local_cell_control(),
            'completion_solver_launched': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    expected = generate()
    if args.write:
        args.certificate.write_text(json.dumps(expected, indent=2)+'\n')
    assert json.loads(args.certificate.read_text()) == expected
    print(json.dumps({'status': 'closed orbit formula and local-cell controls passed',
                      'perfect_matchings': 10395,
                      'orbit_sizes': [row['orbit_size'] for row in expected['orbits']],
                      'local_cell_control': expected['local_cell_control']}, indent=2))
