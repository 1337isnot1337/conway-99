"""Exclude a ten-grid support by four independent defect columns."""

from itertools import product

import numpy as np

from root_cell_profiles import AXIS_PAIRS, RootCells, sum_possible

MISSING = ((0, 3), (0, 4), (0, 6), (1, 4), (1, 5), (1, 6),
           (2, 5), (2, 6), (3, 6), (4, 6), (5, 6))
PIVOTS = (2, 7, 8, 10)
TRANSFORM = np.array([
    [ 0,-1, 1, 1, 0,-1, 0, 0, 0, 0, 0],
    [ 0, 0, 0, 0, 1,-1,-1, 1, 0, 0, 0],
    [-1, 1, 0, 0, 0, 0, 0, 0, 1,-1, 0],
    [ 0, 0, 0, 1,-1, 0, 0, 0, 0,-1, 1],
])


def cell_sum_matrices(by_sum, missing, pivots, transform):
    domains = [by_sum[AXIS_PAIRS.index(e)] for e in missing]
    for rows in product(*(domains[k] for k in pivots)):
        pivot = np.array(rows)
        if not np.array_equal(pivot[:, pivots], pivot[:, pivots].T):
            continue
        matrix = transform.T @ pivot
        if all(tuple(row) in domain for row, domain in zip(matrix, domains)):
            yield matrix


def viable(cells, i, population, groups):
    for k in PIVOTS:
        options = []
        for j, domain in enumerate(groups):
            if not any(cells.degrees[list(population), j]):
                continue
            sums = set()
            for other in (domain if i != j else (population,)):
                sums.update(cells.contributions(i, j, population, other, (k,)))
            if not sums:
                return False
            options.append(sums)
        if not sum_possible(options, tuple(-4*cells.z[list(population), k])):
            return False
    return True


def verify():
    cells = RootCells(MISSING)
    assert np.array_equal(cells.z[:, PIVOTS] @ TRANSFORM, cells.z)
    by_sum = []
    for i in range(len(AXIS_PAIRS)):
        group = {}
        for p in cells.cell_populations(i):
            row = tuple(cells.z[list(p)].sum(axis=0))
            group.setdefault(row, []).append(p)
        by_sum.append(group)

    count = 0
    for matrix in cell_sum_matrices(by_sum, MISSING, PIVOTS, TRANSFORM):
        count += 1
        groups = []
        for e, rows in zip(AXIS_PAIRS, by_sum):
            target = tuple(matrix[MISSING.index(e)]) if e in MISSING else (0,)*len(MISSING)
            groups.append(rows[target])
        for i in sorted(range(len(groups)), key=lambda j: len(groups[j])):
            groups[i] = [p for p in groups[i] if viable(cells, i, p, groups)]
            if not groups[i]:
                break
        else:
            raise AssertionError(matrix)
    assert count == 9
    print('Ten-grid degree pattern 0,3,3,3,3,4,4: nine cell-sum matrices, '
          'all excluded by the four-site eigenvector equations.')


if __name__ == '__main__':
    verify()
