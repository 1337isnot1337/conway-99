"""Rebuild the ordinary 59-point core and compute the negative Gram rank modulo 1009."""
from itertools import combinations, permutations
import sys
import numpy as np

PERMS = list(permutations(range(4)))


def core(interface):
    labels = [()] + [(a,) for a in range(14)]
    labels += [(a, b) for a, b in combinations(range(14), 2) if a//2 != b//2 and b >= 10]
    matrix = np.zeros((59, 59), dtype=int)

    def connect(i, j):
        matrix[i, j] = matrix[j, i] = 1

    for i, j in combinations(range(59), 2):
        a, b = labels[i], labels[j]
        if not a:
            adjacent = len(b) == 1
        elif len(b) == 1:
            adjacent = (a[0] ^ 1) == b[0]
        elif len(a) == 1:
            adjacent = a[0] in b
        else:
            adjacent = (a[0]//2, a[1]//2) == (b[0]//2, b[1]//2) and len(set(a) & set(b)) == 1
        if adjacent:
            connect(i, j)
    for i in range(5):
        for j in range(5):
            if i == j:
                assert interface[5*i+j] == -1
                continue
            for t, u in enumerate(PERMS[interface[5*i+j]]):
                x = labels.index((2*i+t//2, 10+t%2))
                y = labels.index((2*j+u//2, 12+u%2))
                connect(x, y)
    return matrix


def rank_mod(matrix, prime):
    work = matrix.copy() % prime
    pivot = 0
    for j in range(work.shape[1]):
        nonzero = np.flatnonzero(work[pivot:, j])
        if not len(nonzero):
            continue
        i = pivot + nonzero[0]
        work[[pivot, i]] = work[[i, pivot]]
        row = work[pivot] * pow(int(work[pivot, j]), -1, prime) % prime
        work[pivot+1:] = (work[pivot+1:] - work[pivot+1:, j:j+1]*row) % prime
        pivot += 1
    return pivot


if __name__ == '__main__':
    from collections import Counter
    counts = Counter()
    for line in sys.stdin:
        tokens = line.split()
        if tokens[:1] != ['survivor']:
            continue
        neg_rank, _, *interface = map(int, tokens[1:])
        assert len(interface) == 25
        matrix = core(interface)
        rank = rank_mod(27*np.eye(59, dtype=int)-9*matrix+1, 1009)
        assert rank <= 31 + neg_rank
        counts[rank] += 1
    print('Ordinary 59-point ranks modulo 1009:', dict(sorted(counts.items())))
