"""Independent replay of the surviving four-cover graphs and colorings.

This does not repeat the 24^4-cover census.  It checks explicit edge-set
isomorphisms for its 2736 survivors, enumerates side partitions by an
anchored recursion, and verifies the saved compatibility-graph colorings.
No original projection-builder helper is imported.
"""
from __future__ import annotations

import argparse
from collections import Counter
from itertools import combinations, permutations, product
import json
from pathlib import Path
import time

import networkx as nx


def cover(voltages):
    perms = tuple(permutations(range(4)))
    neighbors = [set() for _ in range(24)]
    for u in range(12):
        row, sheet = divmod(u, 4)
        for column in range(3):
            permutation = (perms[voltages[2*(row-1)+column-1]]
                           if row and column else (0, 1, 2, 3))
            v = 12+4*column+permutation[sheet]
            neighbors[u].add(v); neighbors[v].add(u)
    assert all(len(n) == 3 for n in neighbors)
    seen = {0}
    while True:
        more = seen | {w for v in seen for w in neighbors[v]}
        if more == seen:
            break
        seen = more
    assert len(seen) == 24
    return neighbors


def graph(neighbors):
    g = nx.Graph(); g.add_nodes_from(range(24))
    g.add_edges_from((i, j) for i in range(12) for j in sorted(neighbors[i]))
    return g


def side_partitions(neighbors, vertices):
    opposite = set(range(24))-set(vertices)
    def recurse(remaining):
        if not remaining:
            yield ()
            return
        smallest = min(remaining)
        for extra in combinations(sorted(set(remaining)-{smallest}), 3):
            block = (smallest,)+extra
            if set.union(*(neighbors[v] for v in block)) != opposite:
                continue
            for rest in recurse(set(remaining)-set(block)):
                yield (block,)+rest
    answer = sorted(recurse(set(vertices)))
    assert len(answer) == len(set(answer))
    return answer


def projection_data(neighbors):
    edges = [(i, j) for i in range(12) for j in sorted(neighbors[i])]
    index = {e: i for i, e in enumerate(edges)}
    left = side_partitions(neighbors, range(12))
    right = side_partitions(neighbors, range(12, 24))
    all_fibers = []
    for L, R in product(left, right):
        fibers = []
        for a, b in product(L, R):
            matching = [(u, v) for u in a for v in b if v in neighbors[u]]
            assert len(matching) == 4
            assert {u for u, v in matching} == set(a)
            assert {v for u, v in matching} == set(b)
            fibers.append(sum(1 << index[e] for e in matching))
        assert sum(f.bit_count() for f in fibers) == 36
        assert len(set(fibers)) == 9
        all_fibers.append(fibers)
    compatible = [0]*len(all_fibers)
    for i, j in combinations(range(len(all_fibers)), 2):
        if max((a & b).bit_count() for a in all_fibers[i] for b in all_fibers[j]) <= 2:
            compatible[i] |= 1 << j; compatible[j] |= 1 << i
    distinct = set(f for fibers in all_fibers for f in fibers)
    bound = min(sum(bool(f >> e & 1) for f in distinct) for e in range(36))
    return left, right, compatible, bound


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--source', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/seven-red-four-cover-scout.json'))
    p.add_argument('--classes', type=Path, default=Path(
        'experiments/logs/grids-and-triangles/seven-red-four-cover-orbits.json'))
    p.add_argument('--colorings', type=Path, default=Path(
        'experiments/workspace/seven-red-four-cover-colorings.json'))
    p.add_argument('--output', type=Path)
    a = p.parse_args(); started = time.monotonic()
    source = json.loads(a.source.read_text()); classes = json.loads(a.classes.read_text())
    colorings = json.loads(a.colorings.read_text())
    assert source['complete'] is True and source['normalized_covers'] == 24**4
    assert sum(r['count'] for r in source['component_histogram']) == 24**4
    assert sum(r['count'] for r in source['connected_fiber_bound_histogram']) == 326010
    assert len(source['survivors']) == 2736
    voltages = [tuple(r['voltages']) for r in source['survivors']]
    assert len(set(voltages)) == 2736
    assert all(len(v) == 4 and all(0 <= x < 24 for x in v) for v in voltages)
    assert sum(r['count'] for r in source['connected_fiber_bound_histogram']
               if r['bound'] >= 7) == 2736
    targets = {}
    summaries = []
    assert len(classes['classes']) == len(colorings['classes']) == 3
    for row, certificate in zip(classes['classes'], colorings['classes']):
        representative = row['representative']
        assert representative['voltages'] == certificate['voltages']
        neighbors = cover(representative['voltages'])
        assert [sorted(n) for n in neighbors] == row['adjacency']
        left, right, compatibility, bound = projection_data(neighbors)
        assert len(left) == len(right) == 8 and len(compatibility) == 64
        assert bound == representative['fiber_bound']
        assert compatibility == certificate['compatibility_rows']
        colors = certificate['colors']
        assert len(colors) == 64 and all(type(c) is int and c >= 0 for c in colors)
        assert len(set(colors)) == certificate['color_count'] <= 4
        for i, j in combinations(range(64), 2):
            if compatibility[i] >> j & 1:
                assert colors[i] != colors[j]
        targets[bound] = graph(neighbors)
        summaries.append({'fiber_bound': bound, 'left_partitions': 8, 'right_partitions': 8,
                          'projection_count': 64, 'color_count': len(set(colors)),
                          'compatibility_edges': sum(r.bit_count() for r in compatibility)//2,
                          'expected_assignments': row['count']})
    checked = Counter()
    for row in source['survivors']:
        bound = row['fiber_bound']; target = targets[bound]
        candidate = graph(cover(row['voltages']))
        matcher = nx.algorithms.isomorphism.GraphMatcher(candidate, target)
        assert matcher.is_isomorphic()
        mapping = matcher.mapping
        assert set(mapping) == set(range(24)) and set(mapping.values()) == set(range(24))
        image = {tuple(sorted((mapping[u], mapping[v]))) for u, v in candidate.edges}
        assert image == {tuple(sorted(e)) for e in target.edges}
        checked[bound] += 1
    for r in summaries:
        assert checked[r['fiber_bound']] == r['expected_assignments']
        r['verified_assignment_isomorphisms'] = checked[r['fiber_bound']]
    result = {'scope': 'independent survivor quotient and coloring replay; no repeat of full census',
              'assignment_isomorphisms': sum(checked.values()), 'classes': summaries,
              'conclusion': 'the connected four-cover survivors admit no seven pairwise-compatible projections',
              'seconds': time.monotonic()-started}
    if a.output:
        a.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
