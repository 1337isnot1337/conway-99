"""Exact finite bound for a common triangle system in the eight-red case.

A connected three-sheeted K3,3 cover has 18 vertices and 27 edges. A new
projection is a pair of partitions of its two nine-vertex sides into three
triples, each triple having disjoint neighborhoods. Two base projections
cannot share a three-edge fiber: the corresponding base vertices would
have three common U neighbors.

All 6^4 spanning-tree-normalized voltage assignments are enumerated.  For
every connected cover, the maximum family of projections without a common
edge fiber is computed exactly and independently checked by subsets.
Only the connected/common-triangle-system case is addressed by this script.
"""

import argparse
from collections import Counter
from itertools import combinations, permutations, product
import json
from pathlib import Path


def partitions(vertices):
    if not vertices:
        yield ()
        return
    first, *rest = vertices
    for a,b in combinations(rest, 2):
        for tail in partitions([v for v in rest if v not in (a,b)]):
            yield ((first,a,b),)+tail


def cover(signs, perms):
    neighbors = [0]*18
    for i,j in product(range(3), repeat=2):
        p = perms[signs[(i-1)*2+j-1]] if i and j else perms[0]
        for bit in range(3):
            v, w = 3*i+bit, 9+3*j+p[bit]
            neighbors[v] |= 1 << (w-9)
            neighbors[w] |= 1 << v
    assert all(mask.bit_count() == 3 for mask in neighbors)
    return neighbors


def components(neighbors):
    unvisited = set(range(18))
    sizes = []
    while unvisited:
        root = min(unvisited)
        unvisited.remove(root)
        todo, count = [root], 0
        while todo:
            v = todo.pop()
            count += 1
            offset = 9 if v < 9 else 0
            for j in range(9):
                w = offset+j
                if neighbors[v] >> j & 1 and w in unvisited:
                    unvisited.remove(w)
                    todo.append(w)
        sizes.append(count)
    return sorted(sizes)


def max_clique(adjacency):
    best = ()
    def visit(candidates, chosen):
        nonlocal best
        while candidates:
            if len(chosen)+candidates.bit_count() <= len(best):
                return
            bit = candidates & -candidates
            v = bit.bit_length()-1
            candidates -= bit
            visit(candidates & adjacency[v], chosen+(v,))
        if len(chosen) > len(best):
            best = chosen
    visit((1 << len(adjacency))-1, ())
    assert all(adjacency[v] >> w & 1 for v,w in combinations(best, 2))
    # Direct subset audit does not use the branch-and-bound recursion.
    assert not any(all(adjacency[v] >> w & 1 for v,w in combinations(S, 2))
                   for S in combinations(range(len(adjacency)), len(best)+1))
    return best


def run(output=None):
    perms = list(permutations(range(3)))
    parts = list(partitions(list(range(9))))
    assert len(perms) == 6 and len(parts) == 280
    records = []
    component_counts, bound_counts = Counter(), Counter()
    for signs in product(range(6), repeat=4):
        neighbors = cover(signs, perms)
        sizes = components(neighbors)
        component_counts[tuple(sizes)] += 1
        record = {'voltages': list(signs), 'component_sizes': sizes}
        if sizes == [18]:
            valid = []
            for side in (neighbors[:9], neighbors[9:]):
                triples = {T for T in combinations(range(9), 3)
                           if side[T[0]] | side[T[1]] | side[T[2]] == 511}
                valid.append([frozenset(part) for part in parts if all(T in triples for T in part)])
            assert 1 <= len(valid[0]) <= 4 and 1 <= len(valid[1]) <= 4
            available_triples = [sorted(set(T for part in side for T in part)) for side in valid]
            occurrence = [[sum(v in T for T in triples) for v in range(9)]
                          for triples in available_triples]
            fiber_bound, edge_left, edge_right = min(
                (occurrence[0][a]*occurrence[1][b], a, b)
                for a,b in product(range(9), repeat=2) if neighbors[a] >> b & 1)
            assert 1 <= fiber_bound <= 4
            left_triples = [list(T) for T in available_triples[0] if edge_left in T]
            right_triples = [list(T) for T in available_triples[1] if edge_right in T]
            assert neighbors[edge_left] >> edge_right & 1
            assert all(edge_left in T for T in left_triples)
            assert all(edge_right in T for T in right_triples)
            assert len(left_triples)*len(right_triples) == fiber_bound
            labels = list(product(range(len(valid[0])), range(len(valid[1]))))
            adjacency = [0]*len(labels)
            for i,(a,b) in enumerate(labels):
                for j,(c,d) in enumerate(labels):
                    if i != j and (not (valid[0][a] & valid[0][c]) or
                                   not (valid[1][b] & valid[1][d])):
                        adjacency[i] |= 1 << j
            clique = max_clique(adjacency)
            assert len(clique) == fiber_bound
            bound_counts[len(clique)] += 1
            record.update({'left_partitions': len(valid[0]),
                           'right_partitions': len(valid[1]),
                           'compatible_projection_maximum': len(clique),
                           'edge_with_few_fibers': [edge_left,9+edge_right],
                           'maximum_fibers_containing_that_edge': fiber_bound,
                           'left_fibers_at_edge': left_triples,
                           'right_fibers_at_edge': right_triples,
                           'maximum_family': [list(labels[i]) for i in clique]})
        records.append(record)
    assert len(records) == 1296
    assert component_counts == {(18,): 1250, (6,12): 45, (6,6,6): 1}
    assert max(bound_counts) == 4
    result = {'normalized_three_covers': len(records),
              'component_histogram': {','.join(map(str,k)):v for k,v in sorted(component_counts.items())},
              'connected_projection_bound_histogram': dict(sorted(bound_counts.items())),
              'maximum_connected_compatible_projections': max(bound_counts),
              'covers': records}
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output')
    args = parser.parse_args()
    run(args.output)
