"""Check the three square profiles forced by the last eleven-grid support."""

from collections import Counter
from itertools import product

from eleven_grid_supports import LAST
from root_cell_profiles import RootCells


def verify():
    model = RootCells(LAST)
    assert (model.z[:, LAST.index((0, 4))] == model.z[:, LAST.index((5, 6))]).all()
    for a in (1, 2):
        assert (model.z[:, LAST.index((a, 5))] == -model.z[:, LAST.index((a, 6))]).all()

    # Square sites are ++, +-, -+, --. Opposite sites differ in both bits.
    options = []
    for b in product(range(5), repeat=4):
        if sum(b) != 4:
            continue
        negatives = tuple(2-b[i]+b[i^3] for i in range(4))
        if min(negatives) < 0 or any(b[i] >= 2 and negatives[i] for i in range(4)):
            continue
        z = tuple(1-n for n in b)
        options.append((sum(t*t for t in z), sum(x*y for x,y in zip(b,negatives)),
                        z[0]+z[1], z[0]+z[2]))

    counts = Counter()
    for first, second, third in product(options, repeat=3):
        if first[0]+second[0]+third[0] != 12:
            continue
        counts['norm'] += 1
        if first[1]+second[1]+third[1] > 8:
            continue
        counts['contacts'] += 1
        # The three ordered cells are (1,2), (1,3), (2,3).
        if first[2]+second[2] or first[3]+third[2] or second[3]+third[3]:
            continue
        counts['survivors'] += 1
    assert not counts['survivors']
    print(f'{len(options)} oriented square profiles, {counts["norm"]} norm-compatible triples, '
          f'{counts["contacts"]} meeting the contact bound, none satisfying the three axis sums.')


if __name__ == '__main__':
    verify()
