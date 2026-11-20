"""Literal projector-entry oracle, independent of child DAGs and transports."""

from collections import Counter
from functools import lru_cache

import pynauty


def canonical(rows):
    graph = pynauty.Graph(len(rows), adjacency_dict={
        i: [j for j in range(len(rows)) if row >> j & 1]
        for i, row in enumerate(rows)})
    return len(rows), pynauty.certificate(graph)


def valid(rows):
    for i in range(len(rows)):
        for j in range(i):
            common = sum(bool(rows[i] >> k & 1) and bool(rows[j] >> k & 1)
                         for k in range(len(rows)))
            if common > 2-((rows[i] >> j) & 1):
                return False
    return True


def extend(root, masks, mutual_edge=0):
    r, s = len(root), len(masks)
    rows = list(root)+[0]*s
    for k, mask in enumerate(masks, r):
        for i in range(r):
            if mask >> i & 1:
                rows[k] |= 1 << i
                rows[i] |= 1 << k
    if s == 2 and mutual_edge:
        rows[r] |= 1 << (r+1)
        rows[r+1] |= 1 << r
    return tuple(rows)


class Oracle:
    def __init__(self, data):
        self.ids = {canonical(tuple(rows)): i for i, rows in enumerate(data[0])
                    if 8 <= len(rows) <= 10}
        self.roots = data[0]

    @lru_cache(maxsize=100000)
    def type_id(self, rows):
        if not valid(rows):
            return None
        return self.ids[canonical(rows)]

    def entry(self, root_record, family, sign, i, j):
        """Map labelled induced embedding types to exact integer coefficients."""
        root = root_record['root_type']
        rows, masks = root_record['root_rows'], root_record['masks']
        r = len(rows)
        assert i >= j and family in ('spectral', 'schur') and sign in ('minus', 'plus')
        diagonal, edge, constant = (27, -9, 1) if sign == 'minus' else (44, 11, -2)
        if family == 'spectral' and i < r:
            return {root: diagonal*(i == j)+edge*((rows[i] >> j) & 1)+constant}
        if family == 'spectral' and j < r:
            mask = masks[i-r]
            return {self.type_id(extend(rows, [mask])): constant+edge*((mask >> j) & 1)}
        a, b = (i-r, j-r) if family == 'spectral' else (i, j)
        left, right = masks[a], masks[b]
        multiplier, subtraction = 1, 0
        if family == 'schur':
            record = next(p for p in root_record['projectors'] if p['projector'] == sign)
            h, numerator = record['inverse_denominator'], record['inverse_numerator']
            divisor = record['schur_common_divisor']
            x = [constant+edge*((left >> k) & 1) for k in range(r)]
            y = [constant+edge*((right >> k) & 1) for k in range(r)]
            product = sum(x[k]*numerator[k][l]*y[l] for k in range(r) for l in range(r))
            assert h % divisor == 0 and product % divisor == 0
            multiplier, subtraction = h//divisor, product//divisor
        terms = Counter()
        if a == b:
            terms[self.type_id(extend(rows, [left]))] += multiplier*(diagonal+constant)-subtraction
        for mutual_edge in (0, 1):
            index = self.type_id(extend(rows, [left, right], mutual_edge))
            if index is not None:
                terms[index] += multiplier*(constant+edge*mutual_edge)-subtraction
        return {index: value for index, value in terms.items() if value}
