"""Exclude the Fano-plane pairing of far orbits at a one-fixed-point involution."""
from collections import Counter
from functools import lru_cache
from itertools import combinations, permutations, product
from math import gcd

import numpy as np
from flint import fmpz_mat


LINES = sorted({tuple(sorted((a, b, a ^ b))) for a, b in combinations(range(1, 8), 2)})
SQUARES = [(t, p) for t, line in enumerate(LINES) for p in line]
M = np.array([[int(k in LINES[t]) + int(k == p) for t, p in SQUARES] for k in range(1, 8)])
DELTA = np.array([[int(k == min(set(LINES[t])-{p})) - int(k == max(set(LINES[t])-{p}))
                   for t, p in SQUARES] for k in range(1, 8)])


def interface(mask):
    signs = np.zeros((7, 21), dtype=int)
    for p in range(1, 8):
        lines = [t for t in range(7) if p in LINES[t]]
        for j, t in enumerate(lines):
            sign = -1 if j and mask >> (2*(p-1)+j-1) & 1 else 1
            q, r = sorted(set(LINES[t])-{p})
            signs[p-1, SQUARES.index((t, q))] = sign
            signs[p-1, SQUARES.index((t, r))] = -sign
    numerator = 4+4*np.eye(21, dtype=int)-M.T@M-signs.T@signs
    assert not np.any(numerator % 2)
    n = numerator//2
    assert np.all((n >= 0) & (n <= 2)) and not np.any(n.diagonal())
    assert np.all(n.sum(axis=1) == 20)
    return n


def fano_permutations():
    for a, b, c in permutations(range(1, 8), 3):
        if a ^ b == c:
            continue
        g = {i: (a if i & 1 else 0) ^ (b if i & 2 else 0) ^ (c if i & 4 else 0)
             for i in range(1, 8)}
        lines = [LINES.index(tuple(sorted(g[i] for i in line))) for line in LINES]
        yield [SQUARES.index((lines[t], g[p])) for t, p in SQUARES]


def representatives():
    permutations_ = list(fano_permutations())
    assert len(permutations_) == 168
    seen = set()
    for mask in range(1 << 14):
        n = interface(mask)
        if n.tobytes() in seen:
            continue
        seen.update(n[np.ix_(p, p)].tobytes() for p in permutations_)
        yield n


def required_gram(n):
    cross = 16-8*M-M@n
    lower = 24*np.eye(21, dtype=int)+32-2*M.T@M-10*n-n@n
    return np.block([[DELTA@DELTA.T, cross], [cross.T, lower]])


@lru_cache(None)
def half_words():
    return np.array([(*x, *y) for x in product((-1, 1), repeat=6)
                     for y in product((-2, 0, 2), repeat=2)])


def column_options(n, gram):
    null, dimension = fmpz_mat(gram.tolist()).nullspace()
    kernel = np.array([[int(null[i, j]) for j in range(dimension)] for i in range(28)],
                      dtype=object)
    for j in range(dimension):
        kernel[:, j] //= gcd(*kernel[:, j].tolist())
    modular = (kernel % 1009).astype(np.int64)
    words = half_words()
    options = []
    for s in range(21):
        single = np.flatnonzero(n[s] == 1)
        double = np.flatnonzero(n[s] == 2)
        assert len(single) == 12 and len(double) == 4
        left = 7+np.r_[single[:6], double[:2]]
        right = 7+np.r_[single[6:], double[2:]]
        left_keys = (words @ modular[left]) % 1009
        right_keys = (-DELTA[:, s]@modular[:7]-words@modular[right]) % 1009
        lookup = {}
        for i, row in enumerate(left_keys):
            lookup.setdefault(row.tobytes(), []).append(i)
        choices = []
        for j, row in enumerate(right_keys):
            for i in lookup.get(row.tobytes(), []):
                y = np.zeros(28, dtype=int)
                y[:7] = DELTA[:, s]
                y[left], y[right] = words[i], words[j]
                if not np.any(y @ kernel):
                    choices.append(y)
        options.append(choices)
    return options


def can_sum(pools, target):
    while pools:
        lows = np.array([p.min(axis=0) for p in pools])
        highs = np.array([p.max(axis=0) for p in pools])
        need = target-highs.sum(axis=0)
        room = target-lows.sum(axis=0)
        if np.any(need > 0) or np.any(room < 0):
            return False
        reduced = [p[np.all((p >= need+highs[k]) & (p <= room+lows[k]), axis=1)]
                   for k, p in enumerate(pools)]
        if any(not len(p) for p in reduced):
            return False
        if all(len(p) == len(q) for p, q in zip(pools, reduced)):
            break
        pools = reduced
    if not pools:
        return not np.any(target)
    k = min(range(len(pools)), key=lambda j: len(pools[j]))
    rest = pools[:k]+pools[k+1:]
    return any(can_sum(rest, target-row) for row in pools[k])


def verify():
    i, j = np.triu_indices(28)
    counts = Counter()
    for n in representatives():
        gram = required_gram(n)
        options = column_options(n, gram)
        assert all(options)
        counts[int(fmpz_mat(gram.tolist()).rank())] += 1
        pools = [np.array([v[i]*v[j] for v in choices]) for choices in options]
        assert not can_sum(pools, gram[i, j])
    assert counts == {12: 2, 13: 102}, counts
    print('Fano square interfaces: 16384 sign choices, 104 classes, zero Gram completions.')


if __name__ == '__main__':
    verify()
