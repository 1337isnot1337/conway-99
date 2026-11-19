"""Enumerate marked diagonal halves and count complete-grid cut obstructions."""
import argparse
import subprocess
from collections import Counter

import numpy as np
import pynauty

from parallel_triangle_cores import matchings, partitions


def marked_graph(adjacency, colors):
    rows = {i: np.flatnonzero(row).tolist() for i, row in enumerate(adjacency)}
    return pynauty.Graph(len(adjacency), adjacency_dict=rows, vertex_coloring=colors)


def colored_halves(parts):
    factor = np.zeros((20, 20), dtype=np.uint8)
    first = 0
    for size in parts:
        for i in range(size):
            for j in (i, (i+1) % size):
                a, b = first+i, 10+first+j
                factor[a, b] = factor[b, a] = 1
        first += size
    layers = [set(range(10)), set(range(10, 20))]
    generators = pynauty.autgrp(marked_graph(factor, layers))[0]
    pairs = matchings(tuple(range(10)))
    index = {matching: i for i, matching in enumerate(pairs)}
    square = factor @ factor

    def matching_map(permutation, offset):
        relabel = [v-offset for v in permutation[offset:offset+10]]
        return [index[tuple(sorted(tuple(sorted((relabel[a], relabel[b]))) for a, b in m))]
                for m in pairs]

    actions = [(matching_map(g, 0), matching_map(g, 10)) for g in generators]
    allowed = [[i for i, m in enumerate(pairs) if all(not square[o+a, o+b] for a, b in m)]
               for o in (0, 10)]
    remaining = {(a, b) for a in allowed[0] for b in allowed[1]}
    while remaining:
        a, b = remaining.pop()
        stack = [(a, b)]
        while stack:
            i, j = stack.pop()
            for left, right in actions:
                pair = (left[i], right[j])
                if pair in remaining:
                    remaining.remove(pair)
                    stack.append(pair)
        half = factor.copy()
        for offset, m in ((0, pairs[a]), (10, pairs[b])):
            for i, j in m:
                half[offset+i, offset+j] = half[offset+j, offset+i] = 1
        yield half


def unordered_key(half):
    augmented = np.zeros((22, 22), dtype=np.uint8)
    augmented[:20, :20] = half
    for i in range(20):
        j = 20+i//10
        augmented[i, j] = augmented[j, i] = 1
    return pynauty.certificate(marked_graph(augmented, [set(range(20)), {20, 21}]))


def connected(half):
    found = {0}
    stack = [0]
    while stack:
        for j in np.flatnonzero(half[stack.pop()]):
            if j not in found:
                found.add(j)
                stack.append(j)
    return len(found) == len(half)


def verify(checker):
    seen = set()
    graphs = []
    tally = Counter()
    for parts in partitions(10, lower=3):
        for half in colored_halves(parts):
            tally['ordered'] += 1
            key = unordered_key(half)
            if key in seen:
                continue
            seen.add(key)
            if connected(half):
                graphs.append(half)
    result = subprocess.run([checker], input=np.asarray(graphs).tobytes(),
                            stdout=subprocess.PIPE, check=True)
    rejected = small_cuts = 0
    for line in result.stdout.decode().splitlines():
        idx, mask, difference = map(int, line.split())
        # Replay every witness by direct matrix multiplication.
        h = graphs[idx].astype(int)
        z = np.array([(mask >> i) & 1 for i in range(20)])
        if difference == 0:
            assert z @ h @ (1-z) == 2 and z.sum() == 10
            small_cuts += 1
            continue
        a, b = z[:10].sum(), z[10:].sum()
        residual = z @ (12*np.eye(20, dtype=int)+2-h-h@h) @ z-a*a-b*b
        totals = (a+b, a+b, a+2*b, a+2*b, 2*a+b, 2*a+b, 2*a+2*b)
        def minimum(s):
            q, r = divmod(s, 10)
            return 10*q*q + r*(2*q+1)
        assert residual-sum(map(minimum, totals)) == difference < 0
        rejected += 1
    counts = tally['ordered'], len(seen), len(graphs), rejected, small_cuts
    assert counts == (7511, 3985, 3978, 41, 3), counts
    print('Ordered, unordered, connected, cut-excluded, remaining with a cut of size two:', *counts)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('checker')
    verify(parser.parse_args().checker)
