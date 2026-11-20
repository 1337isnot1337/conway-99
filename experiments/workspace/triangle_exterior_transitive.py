"""Check orbital unions for the 60-vertex exterior of a triangle in an SRG(99,14,1,2)."""
import argparse
from itertools import combinations
from pathlib import Path

import numpy as np


def pair_orbits(generators):
    remaining = set(combinations(range(60), 2))
    while remaining:
        first = remaining.pop()
        stack = [first]
        rows = [0] * 60
        while stack:
            x, y = stack.pop()
            rows[x] |= 1 << y
            rows[y] |= 1 << x
            for g in generators:
                a, b = g[x], g[y]
                pair = (a, b) if a < b else (b, a)
                if pair in remaining:
                    remaining.remove(pair)
                    stack.append(pair)
        assert len({r.bit_count() for r in rows}) == 1
        yield rows


def unions(options, remaining, first=0, chosen=()):
    if remaining == 0:
        yield chosen
        return
    for i in range(first, len(options)):
        degree, rows = options[i]
        if degree <= remaining:
            yield from unions(options, remaining - degree, i + 1, chosen + (rows,))


def local_counts(rows, v):
    triangles_twice = squares = 0
    common_ok = True
    for w, row in enumerate(rows):
        if w == v:
            continue
        adjacent = (rows[v] >> w) & 1
        common = (rows[v] & row).bit_count()
        if common + adjacent > 2:
            common_ok = False
        triangles_twice += adjacent * common
        squares += common * (common - 1) // 2
    return triangles_twice, squares, common_ok


def rank_mod(matrix, prime):
    a = np.array(matrix, dtype=np.int64) % prime
    rank = 0
    for j in range(a.shape[1]):
        pivots = np.flatnonzero(a[rank:, j])
        if not len(pivots):
            continue
        i = rank + pivots[0]
        a[[rank, i]] = a[[i, rank]]
        a[rank, j:] *= pow(int(a[rank, j]), -1, prime)
        a[rank, j:] %= prime
        a[rank+1:, j:] -= a[rank+1:, j, None] * a[rank, j:]
        a[rank+1:, j:] %= prime
        rank += 1
    return rank


def scan_action(block, generators, counts):
    orbits = list(pair_orbits(generators))
    x, y, z = block
    inside, = [rows for rows in orbits if (rows[x] >> y) & 1]
    assert inside[x] == (1 << y | 1 << z) and inside[y] >> z & 1
    options = [(r[0].bit_count(), r) for r in orbits if r is not inside and r[0].bit_count() <= 6]
    counts[0] += 1
    for chosen in unions(options, 6):
        # Distinct pair orbits are disjoint, so the sum is their bitwise union.
        rows = [sum(entries) for entries in zip(inside, *chosen)]
        counts[1] += 1
        check = local_counts(rows, 0)
        triangles_twice, squares, common_ok = check
        if triangles_twice != 2:
            continue
        counts[4] += 1
        if common_ok:
            counts[2] += 1
        exterior = common_ok and squares in (14, 15)
        cospectral = squares == 15
        counts[3] += int(exterior)
        counts[5] += int(cospectral)
        if not (exterior or cospectral):
            continue
        assert all(r.bit_count() == 8 and local_counts(rows, i) == check for i, r in enumerate(rows))
        matrix = np.array([[(row >> j) & 1 for j in range(60)] for row in rows])
        matrix -= 3 * np.eye(60, dtype=int)
        ranks = [rank_mod(matrix, p) for p in (101, 1009)]
        assert all(r > 42 for r in ranks), ranks


def scan(path):
    counts = [0] * 6
    labels = set()
    for line in path.read_text().replace("\\\n", "").splitlines():
        group, action, n, x, y, z, *images = map(int, line.split())
        assert (group, action) not in labels and 1 <= group <= 1117
        labels.add((group, action))
        generators = [images[i:i+60] for i in range(0, len(images), 60)]
        assert len(generators) == n and all(sorted(g) == list(range(60)) for g in generators)
        scan_action((x, y, z), generators, counts)
    assert counts == [912, 66327, 2302, 362, 14778, 314], counts
    print(f"{counts[0]} actions, {counts[1]} orbital unions, {counts[2]} local passes, "
          f"{counts[3]} square-count passes, zero rank passes at either prime.")
    print(f"{counts[4]} unions with one triangle at every vertex, {counts[5]} with fifteen rooted squares, "
          "zero cospectral rank passes at either prime.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("actions", type=Path)
    scan(parser.parse_args().actions)
