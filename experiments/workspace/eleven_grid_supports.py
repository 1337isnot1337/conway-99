"""Classify the single remaining support for eleven grids through a vertex."""

from collections import Counter

from root_cell_profiles import AXIS_PAIRS, FOUR_GRAPHS, RootCells
from sparse_grid_cones import SHAPES
from thirteen_grid_supports import bipartite_components, certificate, unlabelled_graphs


LAST = ((0, 4), (0, 5), (0, 6), (1, 5), (1, 6),
        (2, 5), (2, 6), (4, 5), (4, 6), (5, 6))


def passive_shape(missing, e):
    axes = sorted(set(range(7))-set(e))
    return certificate(5, [(axes.index(a), axes.index(b)) for a, b in missing
                           if a in axes and b in axes])


def impossible_degree_cell(missing):
    model = RootCells(missing)
    allowed_degrees = [set(map(len,g)) for g in FOUR_GRAPHS if sum(map(len,g)) <= 4]
    for i, cell in enumerate(AXIS_PAIRS):
        if cell in missing:
            degrees = {int(model.degrees[t,i]) for t in model.bins[i]}
            if not any(values <= degrees for values in allowed_degrees):
                return True
    return False


def incidence_possible(missing, present):
    if any(sum(not set(e) & set(f) for f in missing) < 4 for e in present):
        return False
    if len({v for e in missing for v in e}) < 6:
        return False
    parts = bipartite_components(missing)
    return all(bipartite_components(missing[:i]+missing[i+1:]) == parts
               for i in range(len(missing)))


def verify():
    forbidden = {certificate(5, SHAPES[key][0]) for key in ('paw', 'fork', 'path')}
    count = Counter()
    survivors = []
    for edges in unlabelled_graphs():
        if len(edges) != 10:
            continue
        count['graphs'] += 1
        missing = tuple(sorted(edges))
        present = set(AXIS_PAIRS)-set(missing)
        if not incidence_possible(missing, present):
            continue
        count['supports'] += 1
        if impossible_degree_cell(missing):
            count['empty cell'] += 1
            continue
        if any(passive_shape(missing, e) in forbidden for e in present):
            count['four missing obstruction'] += 1
            continue
        survivors.append(certificate(7, missing))
    assert survivors == [certificate(7, LAST)]
    assert count['supports'] == 20 and count['empty cell'] == 5 and count['four missing obstruction'] == 14
    print(f'{count["graphs"]} ten-edge graphs, 20 incidence supports, five empty cells, '
          'fourteen excluded opposite a grid, one support left.')


if __name__ == '__main__':
    verify()
