"""Exclude a central grid together with grids on all ten disjoint axis pairs."""

from collections import Counter
from itertools import combinations, permutations, product

import numpy as np
from flint import fmpz_mat


PAIRS = tuple(combinations(range(5), 2))
NEIGHBORS = [tuple(i for i, other in enumerate(PAIRS) if not set(pair) & set(other))
             for pair in PAIRS]
PERMS = tuple(permutations(range(4)))
OPPOSITES = ((1, 0, 3, 2), (2, 3, 0, 1), (3, 2, 1, 0))
INVERSE = [PERMS.index(tuple(p.index(i) for i in range(4))) for p in PERMS]
CHARACTERS = np.array([[1 if i in (0, p[0]) else -1 for i in range(4)] for p in OPPOSITES])


def local_states():
    states = []
    for color, opposite in enumerate(OPPOSITES):
        target = [sorted((x, OPPOSITES[0][x], opposite[x])) for x in range(4)]
        possible = [i for i, p in enumerate(PERMS) if all(p[x] in target[x] for x in range(4))]
        for triple in product(possible, repeat=3):
            if all(sorted(PERMS[i][x] for i in triple) == target[x] for x in range(4)):
                states.append((color,) + triple)
    return states


def assignments():
    states = local_states()
    assert Counter(s[0] for s in states) == {0: 9, 1: 24, 2: 24}
    tables = {(j, p): sum(1 << i for i, row in enumerate(states) if row[j] == p)
              for j in range(1, 4) for p in range(24)}

    def extend(assigned, domains):
        if len(assigned) == 10:
            yield tuple(states[assigned[i]] for i in range(10))
            return
        i = min((i for i in range(10) if i not in assigned), key=lambda i: domains[i].bit_count())
        choices = domains[i]
        while choices:
            bit = choices & -choices
            choices ^= bit
            selected = bit.bit_length()-1
            new = domains.copy()
            for j, p in zip(NEIGHBORS[i], states[selected][1:]):
                if j not in assigned:
                    new[j] &= tables[1+NEIGHBORS[j].index(i), INVERSE[p]]
                    if not new[j]:
                        break
            else:
                yield from extend(assigned | {i: selected}, new)

    yield from extend({}, [(1 << len(states))-1]*10)


def transformations(pairs=PAIRS, neighbors=NEIGHBORS):
    for axes in permutations(range(5)):
        order = [pairs.index(tuple(sorted(axes[a] for a in pair))) for pair in pairs]
        slots = [tuple(neighbors[i].index(order.index(j)) for j in neighbors[k])
                 for i, k in enumerate(order)]
        for q in PERMS:
            conjugate = [tuple(q[p[q.index(i)]] for i in range(4)) for p in PERMS]
            colors = [OPPOSITES.index(conjugate[PERMS.index(p)]) for p in OPPOSITES]
            if colors[0] == 0:
                yield order, slots, [PERMS.index(p) for p in conjugate], colors


def representatives(all_cases):
    actions = list(transformations())
    while all_cases:
        case = min(all_cases)
        for order, slots, perm, colors in actions:
            image = [None]*10
            for i, row in enumerate(case):
                image[order[i]] = (colors[row[0]],) + tuple(perm[row[1+j]] for j in slots[i])
            all_cases.discard(tuple(image))
        yield case


def adjacency(case):
    matrix = np.zeros((44, 44), dtype=int)
    for i, row in enumerate(case + ((0,),)):
        for x, opposite in enumerate(OPPOSITES[row[0]]):
            for y in set(range(4)) - {x, opposite}:
                matrix[4*i+x, 4*i+y] = 1
        if i == 10:
            continue
        for x in range(4):
            matrix[4*i+x, 40+x] = matrix[40+x, 4*i+x] = 1
        for j, p in zip(NEIGHBORS[i], row[1:]):
            for x, y in enumerate(PERMS[p]):
                matrix[4*i+x, 4*j+y] = 1
    assert np.array_equal(matrix, matrix.T)
    return matrix


def gram_possible(matrix):
    if np.any(matrix < 0):
        return False
    # For a real symmetric matrix, det(xI + M) has nonnegative coefficients
    # exactly when M has no negative eigenvalue.
    return all(c >= 0 for c in fmpz_mat((-matrix).tolist()).charpoly().coeffs())


def permitted_characters(case, quota, axis):
    cells = [i for i, pair in enumerate(PAIRS) if axis in pair]
    possible = set()
    for colors in product(*[set(range(3))-{case[i][0]} for i in cells]):
        for tail in product((-1, 1), repeat=3):
            # The two names of this near axis are interchangeable.
            values = np.array((1,)+tail)[:, None]*CHARACTERS[list(colors)]
            if np.any(values.sum(axis=0)):
                continue
            near = np.zeros((44, 2), dtype=int)
            for i, signs in zip(cells, values):
                for x, sign in enumerate(signs):
                    near[4*i+x, int(sign < 0)] = 1
            if gram_possible(quota-near@near.T):
                possible.add(colors)
                break
    return cells, possible


def obstruction(case):
    matrix = adjacency(case)
    quota = 12*np.eye(44, dtype=int)+2-matrix-matrix@matrix
    if not gram_possible(quota):
        return 'far Gram'
    # Four aligned spokes through one axis are already excluded by parity.
    if any(all(case[i][0] == 0 for i, pair in enumerate(PAIRS) if a in pair) for a in range(5)):
        return 'aligned spokes'
    allowed = [permitted_characters(case, quota, a) for a in range(5)]
    options = [tuple(permutations(set(range(3))-{row[0]})) for row in case]
    for endpoint_colors in product(*options):
        if all(tuple(endpoint_colors[i][PAIRS[i].index(a)] for i in cells) in possible
               for a, (cells, possible) in enumerate(allowed)):
            raise AssertionError('a full near labeling survived')
    return 'axis labels'


def verify():
    cases = set(assignments())
    assert len(cases) == 14160
    counts = Counter(obstruction(case) for case in representatives(cases))
    assert counts == {'far Gram': 49, 'aligned spokes': 9, 'axis labels': 6}
    print('Central grid with ten disjoint grids: 14160 assignments, 64 classes, no extension.')
    print(dict(counts))


if __name__ == '__main__':
    verify()
