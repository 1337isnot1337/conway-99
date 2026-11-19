"""Direct matrix replay of the independent interface backtracking results.

The eleven maps are derived explicitly, without importing the SAT model.
All saved five-base points are checked.  The four-base census is small
enough to reproduce by testing every one of its 11^3 full assignments.
"""
from __future__ import annotations

import argparse
from itertools import combinations, permutations, product
import json
from pathlib import Path

import numpy as np


def allowed_maps():
    points = list(product(range(3), repeat=2))
    maps = {tuple(range(9))}
    for a, b in product((1, 2), repeat=2):
        maps.add(tuple(3*((x+a) % 3)+(y+b) % 3 for x, y in points))
    for sigma in permutations(range(3)):
        inverse = tuple(sigma.index(x) for x in range(3))
        maps.add(tuple(3*sigma[y]+inverse[x] for x, y in points))
    assert len(maps) == 11
    return sorted(maps)


def adjacency(bases, maps, edges, labels):
    n = 9*bases
    A = np.zeros((n, n), dtype=np.int16)
    for i in range(bases):
        for x, y in combinations(range(9), 2):
            if x//3 == y//3 or x % 3 == y % 3:
                A[9*i+x, 9*i+y] = A[9*i+y, 9*i+x] = 1
    for j in range(1, bases):
        for x in range(9):
            A[x, 9*j+x] = A[9*j+x, x] = 1
    for (i, j), label in zip(edges, labels):
        for x, y in enumerate(maps[label]):
            A[9*i+x, 9*j+y] = A[9*j+y, 9*i+x] = 1
    assert np.array_equal(A, A.T)
    assert np.all(A.sum(axis=1) == bases+3)
    return A


def valid(A):
    return int(np.triu(A@A+A, 1).max()) <= 2


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--five', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/seven-red-interfaces-b5-backtrack.json'))
    p.add_argument('--six', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/seven-red-interfaces-b6-backtrack.json'))
    p.add_argument('--four-output', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/seven-red-interfaces-b4-backtrack.json'))
    p.add_argument('--output', type=Path)
    a = p.parse_args(); five = json.loads(a.five.read_text()); six = json.loads(a.six.read_text())
    maps = allowed_maps()
    assert [list(m) for m in maps] == five['allowed_maps']
    assert five['complete'] and five['status'] == 'complete_local_census'
    assert len(five['assignments']) == five['assignment_count'] == 564
    assert len({tuple(row) for row in five['assignments']}) == 564
    expected_edges = [[i, j] for j in range(2, 5) for i in range(1, j)]
    assert five['edge_order'] == expected_edges
    for labels in five['assignments']:
        assert len(labels) == 6 and all(0 <= x < 11 for x in labels)
        assert valid(adjacency(5, maps, expected_edges, labels))
    for depth in range(6):
        assert five['attempts_by_depth'][depth] == 11*five['visits_by_depth'][depth]
        assert (five['attempts_by_depth'][depth]-five['rejected_by_depth'][depth]
                == five['visits_by_depth'][depth+1])
    assert six['complete'] and six['status'] == 'exhaustive_no_local_assignment'
    assert six['five_base_seeds'] == six['seeds_completed'] == 564
    assert not six['witnesses'] and six['visits_by_depth'][10] == 0
    for depth in range(6, 10):
        assert six['attempts_by_depth'][depth] == 11*six['visits_by_depth'][depth]
        assert (six['attempts_by_depth'][depth]-six['rejected_by_depth'][depth]
                == six['visits_by_depth'][depth+1])
    four_edges = [[1, 2], [1, 3], [2, 3]]
    four = [list(labels) for labels in product(range(11), repeat=3)
            if valid(adjacency(4, maps, four_edges, labels))]
    assert len(four) == five['visits_by_depth'][3] == 136
    four_data = {'bases': 4, 'complete': True, 'status': 'complete_local_census',
                 'allowed_maps': [list(m) for m in maps], 'edge_order': four_edges,
                 'assignments': four, 'assignment_count': len(four),
                 'full_assignments_checked': 11**3}
    a.four_output.write_text(json.dumps(four_data, indent=2)+'\n')
    result = {'explicitly_derived_maps': 11, 'four_base_assignments': 136,
              'five_base_witnesses_verified': 564, 'six_base_terminal_count': 0,
              'six_base_extension_attempts': sum(six['attempts_by_depth']),
              'scope': 'matrix witness replay and four-base exhaustive control; six-base completeness uses the independent C++ backtracker'}
    if a.output:
        a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
