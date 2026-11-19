"""Incidence tables at the three vertices of a full triangle."""

from itertools import combinations, permutations

import numpy as np
from ortools.sat.python import cp_model

PAIRS = tuple(combinations(range(6), 2))
PERMS = tuple(permutations(range(6)))
TRIPLES = tuple(row for row in permutations(range(15), 3)
                if len({x for j in row for x in PAIRS[j]}) == 6)


def graph(edges):
    return sum(1 << PAIRS.index(tuple(sorted(e))) for e in edges)


def relabel(mask, perm):
    return graph((perm[a], perm[b]) for j,(a,b) in enumerate(PAIRS) if mask >> j & 1)


SHAPES = (graph(((0,1),(1,2),(2,3),(0,3))), graph(((0,1),(1,2),(0,2),(2,3))))
SPLITS = [[(1 << b) | (1 << c) for a,b,c in TRIPLES if a == e and b < c] for e in range(15)]


def has_splits(graphs):
    for i, selected in enumerate(graphs):
        others = graphs[(i+1)%3] | graphs[(i+2)%3]
        if any(selected >> e & 1 and all(m & others for m in SPLITS[e]) for e in range(15)):
            return False
    return True


def candidates():
    masks = {relabel(shape,p) for shape in SHAPES for p in PERMS}
    images = {m: np.array([relabel(m,p) for p in PERMS]) for m in masks}
    seen = set()
    for first in SHAPES:
        stab = np.flatnonzero(images[first] == first)
        second_choices = masks.copy()
        while second_choices:
            second = min(second_choices)
            second_choices.difference_update(images[second][stab])
            both = stab[images[second][stab] == second]
            third_choices = masks.copy()
            while third_choices:
                third = min(third_choices)
                third_choices.difference_update(images[third][both])
                selected = (first, second, third)
                if has_splits(selected):
                    moved = np.stack([images[g] for g in selected], axis=1)
                    seen.add(min(map(tuple, np.sort(moved, axis=1).tolist())))
    return sorted(seen)


def table_count(graphs):
    rows = [r for r in TRIPLES if sum((g >> e) & 1 for g,e in zip(graphs,r)) <= 1]
    model = cp_model.CpModel()
    variables = [model.new_int_var(0,4,'') for _ in rows]
    for j in range(3):
        for e in range(15):
            model.add(sum(x for r,x in zip(rows,variables) if r[j] == e) == 4)
            if graphs[j] >> e & 1:
                for h in range(6):
                    if h not in PAIRS[e]:
                        model.add(sum(x for r,x in zip(rows,variables)
                                      if r[j] == e and h in PAIRS[r[(j+1)%3]]) == 2)
    for j,k in combinations(range(3),2):
        for a,b in permutations(range(6),2):
            model.add(sum(x for r,x in zip(rows,variables)
                          if a in PAIRS[r[j]] and b in PAIRS[r[k]]) == 8)

    class Count(cp_model.CpSolverSolutionCallback):
        total = 0
        def on_solution_callback(self):
            self.total += 1

    count = Count()
    solver = cp_model.CpSolver()
    solver.parameters.enumerate_all_solutions = True
    solver.parameters.num_workers = 1
    status = solver.solve(model,count)
    assert status in (cp_model.INFEASIBLE, cp_model.OPTIMAL)
    return count.total


def verify():
    supports = candidates()
    assert len(supports) == 116
    survivors = [(gs,n) for gs in supports if (n := table_count(gs))]
    assert len(survivors) == 17 and sum(n for _,n in survivors) == 1899
    assert min((a & b & c).bit_count() for (a,b,c),_ in survivors) == 2
    print('Three ten-grid roots on a full triangle: 116 triples after the split test, '
          '17 triples admitting 1,899 incidence tables; each has at least two common pairs.')


if __name__ == '__main__':
    verify()
