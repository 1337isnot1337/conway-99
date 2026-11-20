"""Near-minimal covers of the 99 vertices by triangles on at most two grids."""

from collections import Counter
from itertools import combinations

from ortools.sat.python import cp_model

from full_triangle_global_bound import root_supports
from root_cell_profiles import AXIS_PAIRS

ORDINARY = (0,3,3,3,3,3,3)
SPECIAL = (1,2,4,6)


def low(degrees):
    return sum(d <= 2 for d in degrees)


def degree_profiles():
    profiles = set()
    ordinary_count = 0
    for present,degrees in root_supports():
        missing = set(AXIS_PAIRS)-set(present)
        if any(sum(not set(e).intersection(f) for f in missing) < 5 for e in present):
            continue
        profile = tuple(sorted(degrees))
        if low(profile) == 1:
            assert profile == ORDINARY
            ordinary_count += 1
        profiles.add(profile)
    assert ordinary_count == 2
    return profiles


def populations(profiles, excess, size):
    options = sorted(d for d in profiles if 1 < low(d) <= 2+excess-size
                     and 2*sum(x in SPECIAL for x in d) < size)

    def extend(start,chosen,left):
        slots = size-len(chosen)
        if not slots:
            if left or sum(sum(d)//2-9 for d in chosen) % 9:
                return
            for z in SPECIAL:
                occurrences = sum(d.count(z) for d in chosen)
                if occurrences % 3 or (occurrences and sum(z in d for d in chosen) < 3):
                    return
            yield tuple(chosen)
            return
        for j in range(start,len(options)):
            d = options[j]
            if left-(low(d)-1) >= slots-1:
                yield from extend(j,chosen+[d],left-(low(d)-1))

    yield from extend(0,[],excess)


def core_possible(degrees):
    size = len(degrees)
    points = range(size)
    edges = list(combinations(points,2))
    triples = list(combinations(points,3))
    h = [9-sum(d)//2 for d in degrees]
    k = sum(h)//9
    model = cp_model.CpModel()
    edge = {e:model.new_bool_var('') for e in edges}
    lines = {(z,t):model.new_bool_var('') for z in SPECIAL for t in triples
             if all(z in degrees[i] for i in t)}
    for z in SPECIAL:
        for i in points:
            model.add(sum(v for (d,t),v in lines.items() if d == z and i in t)
                      == degrees[i].count(z))
    for i,j in edges:
        model.add(sum(v for (_,t),v in lines.items() if i in t and j in t) <= edge[i,j])
    for i in points:
        model.add(sum(edge[min(i,j),max(i,j)]*h[j] for j in points if j != i) == 3*h[i]+k)

    for i,j in edges:
        common = []
        for u in points:
            if u in (i,j):
                continue
            a,b = edge[min(u,i),max(u,i)],edge[min(u,j),max(u,j)]
            v = model.new_bool_var('')
            model.add(v <= a)
            model.add(v <= b)
            model.add(v >= a+b-1)
            common.append(v)
        model.add(sum(common)+edge[i,j] <= 2)
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 1
    status = solver.solve(model)
    assert status in (cp_model.OPTIMAL,cp_model.INFEASIBLE)
    return status == cp_model.OPTIMAL


def verify():
    profiles = degree_profiles()
    for excess,expected in ((3,0),(6,3),(9,134)):
        tested = 0
        survivors = []
        for size in range(1,excess+1):
            for ds in populations(profiles,excess,size):
                tested += 1
                if core_possible(ds):
                    survivors.append(ds)
        assert tested == expected, (excess,tested)
        if excess < 9:
            assert not survivors
        else:
            a,b,c = (0,0,3,3,3,3,4),(0,1,3,3,3,3,3),(0,2,3,3,3,3,4)
            expected_pop = [Counter({a:9-j,b:j}) for j in (0,3,6,9)]+[Counter({c:9})]
            assert len(survivors) == 5 and all(Counter(ds) in expected_pop for ds in survivors)
        print(f'{33+excess//3} low triangles: {tested} root populations, '
              f'{len(survivors)} admitting an exceptional core.')


if __name__ == '__main__':
    verify()
