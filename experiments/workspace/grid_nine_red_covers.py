"""Exact audit of the two-sheeted K3,3 covers in the nine-red-grid reduction.

No graph, numerical, or SAT package is used.  A spanning-tree gauge fixes
five of the nine edge signs, leaving sixteen covers.  Every free involution
preserving the two bipartition classes is one of 15*15 pairings.

The general complement-neighborhood argument proves the bound without this
enumeration.  This script is an independent finite control of that lemma.
"""

import argparse
from collections import Counter
from itertools import product
import json
from pathlib import Path


def matchings(vertices):
    if not vertices:
        yield ()
        return
    first, *rest = vertices
    for i, partner in enumerate(rest):
        for pairs in matchings(rest[:i]+rest[i+1:]):
            yield ((first, partner),)+pairs


def cover(mask):
    neighbors = [set() for _ in range(12)]
    for i,j in product(range(3), repeat=2):
        sign = ((mask >> ((i-1)*2+j-1)) & 1) if i and j else 0
        for bit in range(2):
            v, w = 2*i+bit, 2*(3+j)+(bit ^ sign)
            neighbors[v].add(w)
            neighbors[w].add(v)
    assert all(len(row) == 3 for row in neighbors)
    return neighbors


def connected(neighbors):
    reached, todo = {0}, [0]
    while todo:
        for w in neighbors[todo.pop()]:
            if w not in reached:
                reached.add(w)
                todo.append(w)
    return len(reached) == len(neighbors)


def pairing_permutations(vertices):
    answer = []
    for pairs in matchings(list(vertices)):
        p = list(range(12))
        for v,w in pairs:
            p[v], p[w] = w, v
        answer.append(p)
    assert len(answer) == 15
    return answer


def run(output=None):
    left = pairing_permutations(range(6))
    right = pairing_permutations(range(6,12))
    rows = []
    for mask in range(16):
        neighbors = cover(mask)
        is_connected = connected(neighbors)
        decks = []
        for a,b in product(left,right):
            p = a[:6]+b[6:]
            if any({p[w] for w in neighbors[v]} != neighbors[p[v]] for v in range(12)):
                continue
            if any(len({min(w,p[w]) for w in neighbors[v]}) != 3 for v in range(12)):
                continue
            assert all(p[v] != v and p[p[v]] == v for v in range(12))
            # The two rows over every quotient vertex have complementary
            # neighborhoods, not merely disjoint neighborhoods.
            for v in range(12):
                opposite = set(range(6,12)) if v < 6 else set(range(6))
                assert neighbors[p[v]] == opposite-neighbors[v]
            decks.append(p)
        assert decks
        counts = []
        multiplicities = []
        for vertices, permutations in [(range(6),left),(range(6,12),right)]:
            classes = Counter(tuple(sorted(neighbors[v])) for v in vertices)
            multiplicities.append(sorted(classes.values()))
            opposite = set(range(6,12)) if vertices.start == 0 else set(range(6))
            count = sum(all(neighbors[p[v]] == opposite-neighbors[v] for v in vertices)
                        for p in permutations)
            counts.append(count)
            if is_connected:
                assert max(classes.values()) <= 2
                assert count <= 2
        if is_connected:
            assert len(decks) <= counts[0]*counts[1] <= 4
        rows.append({'mask': mask, 'connected': is_connected,
                     'neighborhood_class_multiplicities': multiplicities,
                     'complement_pairings_per_part': counts,
                     'deck_involutions': decks, 'deck_count': len(decks)})
    assert sum(row['connected'] for row in rows) == 15
    histogram = Counter(row['deck_count'] for row in rows if row['connected'])
    result = {'normalized_covers': 16, 'connected_covers': 15,
              'connected_deck_count_histogram': dict(sorted(histogram.items())),
              'maximum_connected_decks': max(histogram),
              'maximum_base_projections_at_multiplicity_two': 2*max(histogram),
              'covers': rows}
    if output:
        Path(output).parent.mkdir(parents=True, exist_ok=True)
        Path(output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output')
    args = parser.parse_args()
    run(args.output)
