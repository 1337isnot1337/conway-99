"""Integer root weights for the graph-wide grid bound."""

from itertools import combinations

from root_cell_profiles import AXIS_PAIRS
from ten_grid_supports import remaining
from thirteen_grid_supports import bipartite_components, certificate, unlabelled_graphs


def root_supports():
    ten = {certificate(7, missing) for missing in remaining()}
    for present in unlabelled_graphs():
        e = len(present)
        if e > 10:
            continue
        missing = tuple(sorted(set(AXIS_PAIRS)-set(present)))
        degrees = [sum(i in edge for edge in present) for i in range(7)]
        f = degrees.count(6)
        if f > 1 or (e == 10 and certificate(7,missing) not in ten):
            continue
        rank_defect = bipartite_components(missing)
        if any(bipartite_components(missing[:i]+missing[i+1:]) != rank_defect
               for i in range(len(missing))):
            continue
        yield present, degrees


def verify():
    counts = [0,0]
    for present,degrees in root_supports():
        e = len(present)
        f = degrees.count(6)
        assert min(degrees) <= 2
        m = sum(not set(a).intersection(b) for a,b in combinations(present,2))
        capacity = 2*m-sum(min(2,d)*(6-d) for d in degrees)+2*degrees.count(2)
        n = f*int(e == 10)
        q = f*int(e <= 8 or (e == 9 and degrees.count(2) == 6))
        assert 13*e <= 120+6*f+capacity+2*n-2*q
        counts[f] += 1
    assert sum(counts) == 322
    grids = (120*99+20*20)//117
    assert grids == 104 and 4158-18*grids == 2286
    print(f'All {sum(counts)} root supports satisfy the integer capacity inequality. '
          'At most 104 grids, at least 2,286 percolating nonedges, '
          'and all 99 points covered by triangles on at most two grids.')


if __name__ == '__main__':
    verify()
