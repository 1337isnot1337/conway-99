"""Build the 48-point corner graphs with a transitive action on each ten-point fiber."""
from itertools import combinations, product

import numpy as np
import pynauty


def bare_core():
    core = np.zeros((48, 48), dtype=np.int16)
    for i in range(4):
        j = (i+1) % 4
        for x, y in ((i, j), (i, 4+i), (j, 4+i)):
            core[x, y] = core[y, x] = 1
        core[i, 8+10*i:18+10*i] = core[8+10*i:18+10*i, i] = 1
    for i in (4, 5):
        core[i, i+2] = core[i+2, i] = 1
    return core


def block(core, i, j, relation):
    left = slice(8+10*i, 18+10*i)
    right = slice(8+10*j, 18+10*j)
    core[left, right] = relation
    core[right, left] = relation.T


def marked_core(matchings, twist):
    core = bare_core()
    for i, matching in enumerate(matchings):
        block(core, i, i, matching)
    for i in range(3):
        block(core, i, i+1, np.eye(10, dtype=np.int16))
    block(core, 3, 0, twist)
    return core


def pair_orbits(generators):
    remaining = set(product(range(10), repeat=2))
    while remaining:
        stack = [remaining.pop()]
        relation = np.zeros((10, 10), dtype=np.int16)
        while stack:
            x, y = stack.pop()
            relation[x, y] = 1
            for g in generators:
                pair = g[x], g[y]
                if pair in remaining:
                    remaining.remove(pair)
                    stack.append(pair)
        assert len(set(relation.sum(axis=1))) == 1
        yield relation


def nonregular(group_file, totals):
    numbers = []
    for line in group_file.read_text().splitlines():
        number, size, count, *images = map(int, line.split())
        numbers.append(number)
        generators = np.reshape(images, (count, 10))
        assert all(sorted(g) == list(range(10)) for g in generators)
        if size == 10:
            assert number in (1, 2)
            continue
        orbitals = list(pair_orbits(generators))
        maps = [r for r in orbitals if r[0].sum() == 1]
        involutions = [r for r in maps if r.trace() == 0 and np.array_equal(r, r.T)]
        if not involutions:
            continue
        two = ([r for r in orbitals if r[0].sum() == 2] +
               [r+s for r, s in combinations(maps, 2)])
        for inner in product(involutions, repeat=4):
            for twist, a, b in product(maps, two, two):
                totals[0] += 1
                core = marked_core(inner, twist)
                block(core, 0, 2, a)
                block(core, 1, 3, b)
                if np.max(np.triu(core @ core + core, 1)) <= 2:
                    totals[1] += 1
                    yield core
    assert numbers == list(range(1, 46))


def regular(dihedral, totals):
    if dihedral:
        def mul(x, y):
            return 5*((x//5) ^ (y//5)) + (x%5 + (y if x < 5 else -y)) % 5

        def scale(x, k):
            return 5*(x//5) + (k*x) % 5

        inner = tuple(range(5, 10))
        units = (1, 2, 3, 4)
    else:
        def mul(x, y):
            return (x+y) % 10

        def scale(x, k):
            return k*x % 10

        inner = (5,)
        units = (1, 3, 7, 9)
    maps = []
    for y in range(10):
        r = np.zeros((10, 10), dtype=np.int16)
        r[np.arange(10), [mul(x, y) for x in range(10)]] = 1
        maps.append(r)
    pairs = list(combinations(range(10), 2))
    ordered = list(product(range(45), repeat=2))
    relabelings = {}
    for k in units:
        indices = [pairs.index(tuple(sorted((scale(x, k), scale(y, k))))) for x, y in pairs]
        relabelings[k] = np.array([45*indices[a]+indices[b] for a, b in ordered])
    ix = np.arange(len(ordered))
    shifts = np.arange(48, dtype=np.uint64)
    powers = np.uint64(1) << shifts
    masks = []
    for v in (0, 1):
        rels = []
        for x, y in pairs:
            r = np.zeros((48, 48), dtype=np.uint64)
            block(r, v, v+2, maps[x]+maps[y])
            rels.append(r @ powers)
        masks.append(np.array(rels))
    for header in product(inner, inner, inner, range(10)):
        relatives = {k: tuple(scale(x, k) for x in header) for k in units}
        if header != min(relatives.values()):
            continue
        permitted = np.ones(len(ordered), dtype=bool)
        for k, other in relatives.items():
            if other == header:
                permitted &= ix <= relabelings[k]
        choices = ix[permitted]
        totals[0] += len(choices)
        core = marked_core([maps[g] for g in (5, *header[:3])], maps[header[3]])
        rows = (core.astype(np.uint64) @ powers) | masks[0][choices//45] | masks[1][choices%45]
        ok = np.ones(len(rows), dtype=bool)
        for point in (*range(8), 8, 18, 28, 38):
            origin = rows[:, point, None]
            counts = np.bitwise_count(origin & rows) + ((origin >> shifts) & 1)
            counts[:, point] = 0
            ok &= counts.max(axis=1) <= 2
        totals[1] += int(ok.sum())
        for row in rows[ok]:
            yield ((row[:, None] >> shifts) & 1).astype(np.int16)


def canonical(core):
    colors = [set(range(4)), set(range(4, 8)), set(range(8, 48))]
    adj = {i: list(np.flatnonzero(row)) for i, row in enumerate(core)}
    return pynauty.certificate(pynauty.Graph(48, adjacency_dict=adj, vertex_coloring=colors))
