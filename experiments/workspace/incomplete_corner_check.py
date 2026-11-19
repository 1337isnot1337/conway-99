"""Exact spectrum, determinant, and point-attachment tests for the marked corner fibers."""
import argparse
from collections import Counter
from functools import lru_cache
from itertools import combinations, product
from math import isqrt
from pathlib import Path

import numpy as np
from flint import fmpq_mat, fmpz_mat, fmpz_poly

from incomplete_corner_actions import canonical, nonregular, regular


def integer_array(matrix):
    entries = [[int(x) for x in row] for row in matrix.tolist()]
    # Every scalar sum below uses at most 49 entries, each with coefficient one.
    small = all(abs(x) < 2**52 for row in entries for x in row)
    return np.array(entries, dtype=np.int64 if small else object)


class Projection:
    def __init__(self, core, diagonal, adjacency, constant):
        n = len(core)
        matrix = diagonal*np.eye(n, dtype=int) + adjacency*core + constant
        gram = fmpz_mat(matrix.tolist())
        reduced, _, self.rank = gram.rref()
        pivots = [next(j for j in range(n) if reduced[i, j]) for i in range(self.rank)]
        basis = fmpz_mat(matrix[np.ix_(pivots, pivots)].tolist())
        self.determinant = int(basis.det())
        assert self.determinant > 0
        inverse, denominator = fmpq_mat(basis).inv().numer_denom()
        self.denominator = int(denominator)
        features = np.vstack((np.full(n, constant), adjacency*np.eye(n, dtype=int)))
        coordinates = fmpz_mat(features[:, pivots].tolist())
        projected = coordinates * inverse
        self.inner = integer_array(projected * coordinates.transpose())
        remainder = projected * fmpz_mat(matrix[pivots].tolist()) - denominator * fmpz_mat(features.tolist())
        self.remainder = integer_array(remainder)
        self.remainder = self.remainder[:, np.any(self.remainder != 0, axis=0)]
        self.norm = (diagonal+constant)*self.denominator

    def filter(self, words, limit=None):
        marks = np.column_stack((np.zeros(len(words), dtype=int), 1+words))
        if self.remainder.shape[1]:
            ok = np.all(self.remainder[marks].sum(axis=1) == 0, axis=1)
            words, marks = words[ok], marks[ok]
        residual = self.norm - self.inner[marks[:, :, None], marks[:, None, :]].sum(axis=(1, 2))
        ok = residual == 0 if self.rank == limit else residual >= 0
        words, residual = words[ok], residual[ok]
        if limit is None or self.rank+1 != limit:
            return words, None
        lengths = []
        keep = []
        for i, r in enumerate(residual):
            determinant, remainder = divmod(self.determinant*int(r), self.denominator)
            assert remainder == 0
            length = isqrt(determinant)
            if length*length == determinant:
                lengths.append(length)
                keep.append(i)
        return words[keep], lengths


@lru_cache(None)
def point_marks(tips, normalized=False):
    need = [2-sum(i == j-4 or i == (j-3) % 4 for j in tips) for i in range(4)]
    choices = [combinations(range(8+10*i, 18+10*i), v) for i, v in enumerate(need)]
    if normalized:
        assert need[0] == 1
        choices[0] = [(8,)]
    return np.array([(*tips, *(x for group in plan for x in group)) for plan in product(*choices)],
                    dtype=np.int16)


def eligible(core, tips, minus, plus, normalized=False):
    words = point_marks(tips, normalized)
    cap = 2-core-core@core
    ok = np.ones(len(words), dtype=bool)
    for i, j in combinations(range(words.shape[1]), 2):
        ok &= cap[words[:, i], words[:, j]] > 0
    words = words[ok]
    border = (core+np.eye(len(core), dtype=np.int16))[words].sum(axis=1)
    words = words[np.max(border, axis=1) <= 2]
    words, _ = plus.filter(words)
    return minus.filter(words, limit=44)


def signed_relations(options, core, projection):
    assert projection.rank == 43
    incidence = []
    lengths = []
    groups = []
    for words, unsigned in options:
        group = []
        for word, length in zip(words, unsigned):
            for signed in ([length, -length] if length else [0]):
                row = np.zeros(len(core), dtype=np.int16)
                row[word] = 1
                group.append(len(incidence))
                incidence.append(row)
                lengths.append(signed)
        groups.append(group)
    b = np.array(incidence)
    features = np.column_stack((np.ones(len(b), dtype=np.int16), b))
    projected = (features @ projection.inner @ features.T).astype(object)
    scale, remainder = divmod(projection.determinant, projection.denominator)
    assert not remainder
    signed = np.array(lengths, dtype=object)
    numerators = projected*scale + signed[:, None]*signed[None, :]
    overlap = b @ b.T
    blocked = (b @ ((2-b-b@core) == 0).T) > 0
    edge = (numerators == -8*projection.determinant) & (overlap <= 1) & ~blocked & ~blocked.T
    nonedge = (numerators == projection.determinant) & (overlap <= 2)

    return groups, edge, nonedge


def compatible_six(options, core, projection):
    groups, edge, nonedge = signed_relations(options, core, projection)

    def extend(chosen, edge_count, remaining):
        if not remaining:
            return edge_count == 1
        for v in remaining[0]:
            total = edge_count + sum(bool(edge[v, u]) for u in chosen)
            if total > 1:
                continue
            permitted = nonedge[v] if total == 1 else nonedge[v] | edge[v]
            options = [[u for u in group if permitted[u]] for group in remaining[1:]]
            if all(options) and extend(chosen+[v], total, options):
                return True
        return False

    return extend([], 0, groups)


def complete_grid_test(core):
    with_center = np.zeros((49, 49), dtype=np.int16)
    with_center[:48, :48] = core
    with_center[48, 4:8] = with_center[4:8, 48] = 1
    minus = Projection(with_center, 27, -9, 1)
    plus = Projection(with_center, 44, 11, -2)
    # The single mark in fiber zero may be transported to its first point.
    normalized, _ = eligible(with_center, (4,), minus, plus, normalized=True)
    if not len(normalized):
        return 'no exterior point'
    # Its mate can mark any member of that fiber, so restore all choices.
    options = eligible(with_center, (4,), minus, plus)
    _, edge, _ = signed_relations([options], with_center, minus)
    assert not np.any(edge)
    return 'no exterior mate'


def control():
    # The actual 3-by-3 rook graph has a four-dimensional negative eigenspace.
    rook = np.array([[i != j and (i//3 == j//3 or i%3 == j%3) for j in range(9)]
                     for i in range(9)], dtype=np.int16)
    gram = 3*np.eye(9, dtype=int) - 3*rook + 1
    marked = [0, 1, 3]
    rest = [i for i in range(9) if i not in marked]
    p = Projection(rook[np.ix_(marked, marked)], 3, -3, 1)
    assert p.rank == 3
    features, lengths = [], []
    for v in rest:
        words = np.array([np.flatnonzero(rook[v, marked])], dtype=int)
        allowed, unsigned = p.filter(words, limit=4)
        assert len(allowed) == 1
        features.append([1, *rook[v, marked]])
        lengths.append(unsigned[0])
    f = np.array(features)
    known = (f @ p.inner @ f.T).astype(object) * (p.determinant//p.denominator)
    actual = gram[np.ix_(rest, rest)] * p.determinant - known
    assert any(lengths) and np.any(actual < 0)
    assert all(int(actual[i, j])**2 == (lengths[i]*lengths[j])**2
               for i in range(len(rest)) for j in range(len(rest)))


def verify(group_file):
    seen = set()
    stages = Counter()
    x = fmpz_poly([0, 1])
    counts = []
    complete = Counter()
    for name, iterator in [('cyclic', lambda totals: regular(False, totals)),
                           ('dihedral', lambda totals: regular(True, totals)),
                           ('other', lambda totals: nonregular(group_file, totals))]:
        totals = [0, 0]
        for core in iterator(totals):
            key = canonical(core)
            if key in seen:
                continue
            seen.add(key)
            char = fmpz_mat(core[8:, 8:].tolist()).charpoly()
            modes, rem = divmod(char, (x-5)*(x-1)*(x+1)**2)
            assert not rem
            if min(modes(x+3)) < 0 or min(modes(-4-x)) < 0:
                continue
            stages['spectral'] += 1
            minus = Projection(core, 27, -9, 1)
            d = -int(char(3))
            square = d >= 0 and isqrt(d)**2 == d
            assert minus.rank <= 44
            assert square == (minus.rank < 44 or isqrt(minus.determinant)**2 == minus.determinant)
            if not square:
                continue
            stages['core determinant'] += 1
            complete[complete_grid_test(core)] += 1
            plus = Projection(core, 44, 11, -2)
            options = []
            for tips in combinations(range(4, 8), 2):
                words, lengths = eligible(core, tips, minus, plus)
                if not len(words):
                    break
                options.append((words, lengths))
            if len(options) == 6:
                stages['individual attachments'] += 1
                assert not compatible_six(options, core, minus)
        counts.append(totals)
        print(name, 'normalized and locally admissible:', *totals, flush=True)
    assert counts == [[5076, 1208], [632826, 48038], [230, 64]]
    assert len(seen) == 6593 and stages == {'spectral': 341, 'core determinant': 148, 'individual attachments': 2}, stages
    assert complete == {'no exterior point': 139, 'no exterior mate': 9}, complete
    print(f'{len(seen)} marked cores, {dict(stages)}, zero six-point attachments.')
    print('Complete-grid attachment checks:', dict(complete))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('groups', type=Path)
    args = parser.parse_args()
    control()
    verify(args.groups)
