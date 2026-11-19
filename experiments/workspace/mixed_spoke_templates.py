"""Generate prescribed-size mixed supports and the matching domains of their two full axes."""
import argparse
from functools import reduce
from itertools import combinations, permutations, product
from operator import xor

AXES = range(5)
EDGES = tuple((i, j) for i, j in product(AXES, repeat=2) if i != j)
PERMS = list(permutations(range(4)))
CHARS = [[(-1) ** ((a & mask).bit_count()) for a in range(4)] for mask in (1, 2, 3)]


def transport(p, i, j):
    return sum(CHARS[i][a] * CHARS[j][p[a]] for a in range(4)) // 4


ALIGNED = {s: sum(1 << k for k, p in enumerate(PERMS) if transport(p, 0, 0) == s)
           for s in (-1, 1)}
MIXED = {}
for a, b in product((-2, -1, 1, 2), repeat=2):
    matches = [k for k, p in enumerate(PERMS)
               if transport(p, abs(a), 0) == (1 if a > 0 else -1)
               and transport(p, 0, abs(b)) == (1 if b > 0 else -1)]
    assert len(matches) == 1
    MIXED[a, b] = 1 << matches[0]


def symmetries():
    for perm in permutations(AXES):
        yield tuple((perm[i], perm[j]) for i, j in product(AXES, repeat=2))
        yield tuple((perm[j], perm[i]) for i, j in product(AXES, repeat=2))


GROUP = tuple(symmetries())


def image(f, symmetry):
    return tuple(sorted(symmetry[5*i+j] for i, j in f))


def supports(size):
    boundary = {(i, j): (1 << i) | (1 << (5+j)) for i, j in EDGES}
    even = {f for f in combinations(EDGES, size) if not reduce(xor, map(boundary.get, f), 0)}
    while even:
        # Retain the indexing used in the four-cycle proof.
        f = ((0, 2), (0, 3), (1, 2), (1, 3)) if size == 4 else min(even)
        orbit = {image(f, s) for s in GROUP}
        even -= orbit
        yield f


def patterns(mixed):
    rows = []
    for i in AXES:
        aligned = [j for j in AXES if i != j and (i, j) not in mixed]
        rows.append([tuple(1 if j in pos else -int(j in aligned) for j in AXES)
                     for pos in combinations(aligned, len(aligned) // 2)])
    remaining = {sum(p, ()) for p in product(*rows) if all(sum(c) == 0 for c in zip(*p))}
    stabilizer = [s for s in GROUP if image(mixed, s) == mixed]
    while remaining:
        p = min(remaining)
        remaining -= {tuple(sign * p[5*i+j] for i, j in s)
                      for sign in (-1, 1) for s in stabilizer}
        yield p


def signed_types(degree, normalize):
    return [seq for seq in product((-2, -1, 1, 2), repeat=degree)
            if seq.count(1) == seq.count(-1) and seq.count(2) == seq.count(-2)
            and (not seq or not normalize or seq[0] > 0)]


def templates(f, p):
    rows = [[j for a, j in f if a == i] for i in AXES]
    cols = [[i for i, b in f if b == j] for j in AXES]
    left = [signed_types(len(row), True) for row in rows]
    # The switch at index j normalizes a row if active, otherwise a column.
    right = [signed_types(len(col), not rows[j]) for j, col in enumerate(cols)]
    base = [ALIGNED.get(v, 0) for v in p]
    for r in product(*left):
        for c in product(*right):
            domain = base.copy()
            for i, j in f:
                domain[5*i+j] = MIXED[r[i][rows[i].index(j)], c[j][cols[j].index(i)]]
            yield domain


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('size', type=int, nargs='?', default=4, choices=range(4, 21, 2))
    args = parser.parse_args()
    for f in supports(args.size):
        for p in patterns(f):
            for domain in templates(f, p):
                print(*domain)


if __name__ == '__main__':
    main()
