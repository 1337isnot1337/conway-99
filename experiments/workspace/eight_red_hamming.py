"""Exact finite control for the induced H(3,3) obstruction.

The proof is counting, not enumeration-dependent. This standard-library
checker verifies the small graph and all possible outside-neighborhood
triples used in that proof. No projection is assumed to be linear.
"""

import argparse
from collections import Counter
from itertools import combinations, permutations, product
import json
from pathlib import Path


def check():
    vertices = list(product(range(3), repeat=3))
    distance = [[sum(a != b for a, b in zip(x, y)) for y in vertices]
                for x in vertices]
    adjacent = [{j for j in range(27) if distance[i][j] == 1}
                for i in range(27)]
    assert all(len(neighbors) == 6 for neighbors in adjacent)
    histogram = Counter()
    compatible = [{j for j in range(27) if distance[i][j] == 3}
                  for i in range(27)]
    for i, j in combinations(range(27), 2):
        d = distance[i][j]
        common = len(adjacent[i] & adjacent[j])
        assert common == {1: 1, 2: 2, 3: 0}[d]
        quota = 1 if d == 1 else 2
        assert (quota > common) == (d == 3)
        histogram[d, common] += 1

    triples = [triple for triple in combinations(range(27), 3)
               if all(distance[i][j] == 3 for i, j in combinations(triple, 2))]
    assert len(triples) == 36
    pair_multiplicity = Counter(pair for triple in triples
                                for pair in combinations(triple, 2))
    for i, j in combinations(range(27), 2):
        if distance[i][j] == 3:
            common_compatible = compatible[i] & compatible[j]
            assert len(common_compatible) == 1
            k = next(iter(common_compatible))
            assert vertices[k] == tuple((-a - b) % 3
                                        for a, b in zip(vertices[i], vertices[j]))
            assert pair_multiplicity[i, j] == 1
        else:
            assert pair_multiplicity[i, j] == 0
    assert not any(all(distance[i][j] == 3 for i, j in combinations(four, 2))
                   for four in combinations(range(27), 4))

    # Independent list: order a triple by its first coordinate. Its other
    # coordinates are arbitrary permutations of the three symbols.
    index = {point: i for i, point in enumerate(vertices)}
    permuted = {tuple(sorted(index[x, y[x], z[x]] for x in range(3)))
                for y in permutations(range(3)) for z in permutations(range(3))}
    assert permuted == set(triples)

    outside_count = 99 - 27
    boundary_edges = 27 * (14 - 6)
    assert boundary_edges == 3 * outside_count
    # Every outside neighborhood is a distance-three triple. No triple
    # can occur twice, since the two outside vertices would share three
    # common neighbors. There are only 36 choices for 72 outside vertices.
    assert outside_count > len(triples)
    return {
        'hypothesis': 'an induced H(3,3) in an srg(99,14,1,2)',
        'status': 'excluded by exact counting',
        'hamming_vertices': 27,
        'hamming_degree': 6,
        'pair_distance_and_common_neighbor_counts': [
            {'distance': d, 'common_neighbors': c, 'pairs': count}
            for (d, c), count in sorted(histogram.items())],
        'maximum_outside_neighborhood_size': 3,
        'boundary_edges': boundary_edges,
        'outside_vertices': outside_count,
        'forced_outside_neighborhood_size': 3,
        'allowed_outside_neighborhood_triples': len(triples),
        'maximum_uses_per_triple': 1,
        'distance_three_pairs': len(pair_multiplicity),
        'third_points_per_distance_three_pair': 1,
        'triples': [[vertices[i] for i in triple] for triple in triples],
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = check()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'triples'}), flush=True)
