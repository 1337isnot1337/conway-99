"""Classify the ten-grid supports passing the signed cone and cell degree tests."""

from collections import Counter

from eleven_grid_supports import impossible_degree_cell, incidence_possible, passive_shape
from root_cell_profiles import AXIS_PAIRS
from sparse_grid_cones import SHAPES
from thirteen_grid_supports import certificate, unlabelled_graphs


def remaining():
    forbidden = {certificate(5, shape[0]) for shape in SHAPES.values()}
    sizes = Counter()
    supports = []
    for edges in unlabelled_graphs():
        if len(edges) != 11:
            continue
        sizes['missing graphs'] += 1
        missing = tuple(sorted(edges))
        present = set(AXIS_PAIRS)-set(missing)
        if not incidence_possible(missing,present):
            continue
        sizes['incidence'] += 1
        if any(passive_shape(missing,e) in forbidden for e in present):
            continue
        sizes['cones'] += 1
        if not impossible_degree_cell(missing):
            supports.append(missing)
    assert sizes == {'missing graphs': 148, 'incidence': 56, 'cones': 9}
    return supports


if __name__ == '__main__':
    supports = remaining()
    degrees = sorted(tuple(sorted(6-sum(v in e for e in f) for v in range(7))) for f in supports)
    assert degrees == [(0,2,2,4,4,4,4), (0,2,3,3,4,4,4), (0,3,3,3,3,4,4),
                       (1,1,2,3,3,4,6), (1,1,3,3,3,3,6), (2,2,2,2,4,4,4)]
    print('Ten grids: 148 missing graphs, 56 incidence supports, nine after the cone test, '
          'and six after testing the four-point cells.')
    for f in supports:
        print(' '.join(f'{a}{b}' for a,b in AXIS_PAIRS if (a,b) not in f))
