"""Test integer identities for induced subgraph counts in an srg(v,k,1,2)."""
import argparse
from collections import Counter
from itertools import combinations
from math import comb, gcd
from functools import reduce

import pynauty


def members(mask):
    while mask:
        bit = mask & -mask
        yield bit.bit_length() - 1
        mask ^= bit


def nauty(rows):
    return pynauty.Graph(len(rows), adjacency_dict={
        i: list(members(mask)) for i, mask in enumerate(rows)
    })


def extensions(rows):
    n = len(rows)
    # If a pair already has its full quota of common neighbors, the new
    # vertex cannot be adjacent to both.
    forbidden = []
    for i, j in combinations(range(n), 2):
        quota = 2 - ((rows[i] >> j) & 1)
        if (rows[i] & rows[j]).bit_count() == quota:
            forbidden.append((1 << i) | (1 << j))
    for mask in range(1 << n):
        if any((mask & pair) == pair for pair in forbidden):
            continue
        if any((row & mask).bit_count() > 2 - ((mask >> i) & 1)
               for i, row in enumerate(rows)):
            continue
        yield mask, tuple(row | (((mask >> i) & 1) << n)
                          for i, row in enumerate(rows)) + (mask,)


def build(order):
    graphs = [()]
    levels = [[0]]
    automorphisms = [1]
    children = []
    for n in range(order):
        index = {}
        start = len(graphs)
        for parent in levels[-1]:
            slots = []
            for mask, extension in extensions(graphs[parent]):
                graph = nauty(extension)
                cert = pynauty.certificate(graph)
                child = index.get(cert)
                if child is None:
                    child = len(graphs)
                    index[cert] = child
                    graphs.append(extension)
                    _, mantissa, exponent, _, _ = pynauty.autgrp(graph)
                    automorphisms.append(round(mantissa * 10**exponent))
                slots.append((mask, child))
            children.append(slots)
        levels.append(list(range(start, len(graphs))))
        print('catalog order', n + 1, 'types', len(index), flush=True)
    return graphs, levels, automorphisms, children


def identities(data, v, k):
    graphs, levels, aut, children = data
    # Column zero is a separate constant. Index i represents c_i via i+1.
    for n, level in enumerate(levels):
        yield {0: -comb(v, n), **{i+1: 1 for i in level}}
    for parent, slots in enumerate(children):
        rows = graphs[parent]
        n = len(rows)
        marked = [(0, v-n)]
        marked.extend((1 << i, k - row.bit_count())
                      for i, row in enumerate(rows))
        for i, j in combinations(range(n), 2):
            missing = 2 - ((rows[i] >> j) & 1) - (rows[i] & rows[j]).bit_count()
            marked.append(((1 << i) | (1 << j), missing))
        distinct = set()
        for mark, residual in marked:
            counts = Counter(child for mask, child in slots if mask & mark == mark)
            eq = {child + 1: aut[child] * count for child, count in counts.items()}
            if residual:
                eq[parent + 1] = -aut[parent] * residual
            if eq:
                divisor = reduce(gcd, eq.values())
                eq = {i: value // divisor for i, value in eq.items()}
                key = tuple(sorted(eq.items()))
                if key not in distinct:
                    distinct.add(key)
                    yield eq


def parity(equations):
    pivots = {}
    for index, row in enumerate(equations):
        bits = sum(1 << col for col, num in row.items() if num & 1)
        while bits > 1:
            pivot = bits.bit_length() - 1
            if pivot not in pivots:
                pivots[pivot] = bits
                break
            bits ^= pivots[pivot]
        if bits == 1:
            return index + 1, len(pivots), 'inconsistent'
    return index + 1, len(pivots), 'consistent'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('order', type=int)
    parser.add_argument('--parameters', nargs=2, type=int, action='append')
    args = parser.parse_args()
    data = build(args.order)
    for v, k in args.parameters or [(9, 4), (243, 22), (99, 14)]:
        print('v k', v, k, 'equations/rank/parity', parity(identities(data, v, k)), flush=True)


if __name__ == '__main__':
    main()
