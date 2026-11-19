"""Normalize the six grids from two partners sharing both witness centers."""
import argparse
from itertools import combinations, permutations, product

import numpy as np
import pynauty

# Relative to the common tip b=0, the first axis index selects S1/S2 or P/Q.
PARTNERS = np.array([[1, 2], [3, 4]])
CENTERS = np.array([[5, 6], [7, 8]])
# Axes P/Q, S1/S2, sign on P/Q, sign on S1/S2.
FAR = np.arange(9, 25).reshape(2, 2, 2, 2)
ORDERINGS = tuple(permutations(range(4)))


def grids_at_tip():
    for side, partner in product(range(2), repeat=2):
        grid = np.zeros((3, 3), dtype=int)
        grid[0, 1:] = PARTNERS[partner]
        grid[1:, 0] = CENTERS[side]
        grid[1:, 1:] = FAR[side, partner]
        yield grid


def bases():
    fixed = np.zeros((28, 28), dtype=int)
    for grid in grids_at_tip():
        for line in [*grid, *grid.T]:
            for x, y in combinations(line, 2):
                fixed[x, y] = fixed[y, x] = 1
    # The tip a of T sees p,q. Its two partners in T see opposite signs of S1,S2.
    for t, neighbors in enumerate(((5, 7), (1, 3), (2, 4)), start=25):
        fixed[t, list(neighbors)] = fixed[list(neighbors), t] = 1
    for x, y in combinations(range(25, 28), 2):
        fixed[x, y] = fixed[y, x] = 1

    colors = [{0}, set(range(1, 5)), set(range(5, 9)), set(range(9, 25)), {25}, {26, 27}]
    seen = set()
    for first, second in product(ORDERINGS, repeat=2):
        a = fixed.copy()
        for i, order in enumerate((first, second)):
            left = FAR[0, i].ravel()
            right = FAR[1, 1-i].ravel()[list(order)]
            a[left, right] = a[right, left] = 1
        graph = pynauty.Graph(28, adjacency_dict={
            i: np.flatnonzero(row).tolist() for i, row in enumerate(a)
        }, vertex_coloring=colors)
        key = pynauty.certificate(graph)
        if key not in seen:
            seen.add(key)
            yield a
    assert len(seen) == 117


def attachments(side):
    # The T-grid rows are (a,x,y), (center,r,s), and (t,u,v).
    # Store only the contacts of r,s,t,u,v to the initial 28 points.
    contact = np.zeros((5, 28), dtype=int)
    contact[[0, 1, 2], CENTERS[side, 0]] = 1
    contact[range(5), [26, 27, 25, 26, 27]] = 1
    for reversals in product((False, True), repeat=2):
        same = contact.copy()
        for partner, reverse in enumerate(reversals):
            pair = FAR[side, partner, 1]
            same[[3, 4], pair[::-1] if reverse else pair] = 1
        for shared in range(5):
            rest = [i for i in range(5) if i != shared]
            opposite = same.copy()
            opposite[shared, CENTERS[1-side, 1]] = 1
            for first in ORDERINGS:
                marked = opposite.copy()
                marked[rest, FAR[1-side, 0].ravel()[list(first)]] = 1
                for second in ORDERINGS:
                    result = marked.copy()
                    result[rest, FAR[1-side, 1].ravel()[list(second)]] = 1
                    yield result


def mask(points):
    return sum(1 << int(v) for v in points)


def emit():
    covers = [list(grid.flat) for grid in grids_at_tip()]
    for side in range(2):
        covers.append([25, 26, 27, CENTERS[side, 0], *range(28+5*side, 33+5*side)])
    print(*(mask(c) for c in covers))
    inner = ((1, 3), (0, 4), (3, 4), (0, 2, 4), (1, 2, 3))
    print(*(mask(v) for v in inner))
    for side in range(2):
        # Packing the five rows as little-endian integers keeps this replay stream small.
        total = 0
        for a in attachments(side):
            print(*(a @ (1 << np.arange(28))))
            total += 1
        assert total == 11520
    for a in bases():
        print(*(a @ (1 << np.arange(28))))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--emit', action='store_true')
    if parser.parse_args().emit:
        emit()
    else:
        assert sum(1 for _ in bases()) == 117
        print('576 base interfaces give 117 marked cores. Each side has 4 × 5 × 24² attachments.')
