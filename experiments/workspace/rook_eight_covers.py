"""Eight triangles on a rook board with its bottom-right cell removed."""
import argparse
from collections import Counter
from itertools import combinations, product

import numpy as np

from rook_nine_covers import (INCIDENCE, PERMS, WORDS, adjacency_formula,
                              attachment_sets, certificate, check_proof, core)


def cases():
    seen = set()
    counts = Counter()
    for labels in product(range(6), repeat=4):
        completed = core(labels)
        a, corner = completed[:24, :24], completed[24:, :24]
        marked = np.block([[a, corner.T], [corner, np.zeros((3, 3), dtype=int)]])
        key = certificate(marked, 24)
        if key in seen:
            continue
        seen.add(key)
        quota = 12*np.eye(24, dtype=int) + 2 - a - a @ a
        remaining = quota - corner.T @ corner
        if np.min(remaining) < 0:
            continue
        domains = []
        for i, perm in enumerate(PERMS):
            words = WORDS[27*i:27*i+27]
            if perm[2] == 2:
                # Only two positions remain. Distinct points can have the same pair.
                rows = []
                for u, v, _ in words[::3]:
                    row = np.zeros(24, dtype=int)
                    row[[u, v]] = 1
                    rows.extend([row]*remaining[u, v])
                domains.append([np.array(rows, dtype=int).reshape(-1, 24)])
            else:
                domains.append([INCIDENCE[27*i + np.array(selected, dtype=int), :24]
                                for selected in attachment_sets(words, remaining)])
        seen_attachments = set()
        for groups in product(*domains):
            b = np.vstack([corner, *groups])
            assert b.shape == (75, 24) and np.array_equal(b.T @ b, quota)
            counts['assignments'] += 1
            marked = np.block([[a, b.T], [b, np.zeros((75, 75), dtype=int)]])
            key = certificate(marked, 24)
            if key not in seen_attachments:
                seen_attachments.add(key)
                yield a, b
        if seen_attachments:
            counts['extendible'] += 1
    assert len(seen) == 59 and counts == {'assignments': 649, 'extendible': 21}


PRISM = tuple((i, j) for i, j in combinations(range(6), 2) if i//2 == j//2 or i%2 == j%2)
PRISM_ADJ = np.zeros((6, 6), dtype=int)
for i, j in PRISM:
    PRISM_ADJ[i, j] = PRISM_ADJ[j, i] = 1


def pages(a, b, triangle):
    fibers = [np.flatnonzero(b[:, j]).tolist() for j in triangle]
    # Every other core point outside this prospective grid sees exactly one point in it.
    target = np.ones(len(a), dtype=int)
    target[np.any(a[:, triangle], axis=1)] = 0
    target[triangle] = 2
    pairs = [[(pair, b[list(pair)].sum(axis=0)) for pair in combinations(fiber, 2)]
             for fiber in fibers]
    last = {}
    for pair, incidence in pairs[2]:
        last.setdefault(tuple(incidence), []).append(pair)
    for (first, u), (second, v) in product(*pairs[:2]):
        for third in last.get(tuple(target-u-v), []):
            for middle, end in product((second, second[::-1]), (third, third[::-1])):
                vertices = first + middle + end
                rows = b[list(vertices)]
                marked = np.block([[a, rows.T], [rows, PRISM_ADJ]])
                if np.all(marked @ marked + marked <= 12*np.eye(len(marked), dtype=int)+2):
                    yield vertices


def require_pages(formula, edges, a, b, triangle):
    pool = formula.nv
    fiber = set(np.flatnonzero(b[:, triangle].sum(axis=1)))
    choices = {x: [] for x in fiber}
    for vertices in pages(a, b, triangle):
        links = [tuple(sorted((vertices[i], vertices[j]))) for i, j in PRISM]
        if any(pair not in edges for pair in links):
            continue
        pool += 1
        for x in vertices:
            choices[x].append(pool)
        for pair in links:
            formula.append([-pool, edges[pair]])
        for x in range(len(b)):
            if x not in fiber:
                contacts = [edges[pair] for y in vertices
                            if (pair := tuple(sorted((x, y)))) in edges]
                formula.append([-pool, *contacts])
    for alternatives in choices.values():
        formula.append(alternatives)


def positive_control():
    from pysat.solvers import Solver

    rook = np.array([[int(i != j and (i//3 == j//3 or i%3 == j%3)) for i in range(9)]
                     for j in range(9)])
    for triangle in [list(range(3*i, 3*i+3)) for i in range(3)] + [list(range(i, 9, 3)) for i in range(3)]:
        others = [j for j in range(9) if j not in triangle]
        a, b = rook[np.ix_(triangle, triangle)], rook[np.ix_(others, triangle)]
        formula, edges = adjacency_formula(a, b, False)
        require_pages(formula, edges, a, b, list(range(3)))
        witness = [v if rook[others[x], others[y]] else -v for (x, y), v in edges.items()]
        with Solver(name='glucose3', bootstrap_with=formula) as solver:
            assert solver.solve(assumptions=witness)
    print('The six marked lines in the nine-point rook graph pass the page constraints.')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--verify', action='store_true')
    p.add_argument('--control', action='store_true')
    p.add_argument('--solver', default='cadical')
    p.add_argument('--checker', default='drat-trim')
    p.add_argument('--shard', type=int, nargs=2, metavar=('INDEX', 'COUNT'), default=(0, 1))
    args = p.parse_args()
    if args.control:
        positive_control()
        return
    index, count = args.shard
    assert 0 <= index < count
    total = 0
    for n, (a, b) in enumerate(cases()):
        total += 1
        if args.verify and n % count == index:
            formula, edges = adjacency_formula(a, b, False)
            for cell in (0, 1, 3, 4):
                require_pages(formula, edges, a, b, list(range(3*cell, 3*cell+3)))
            check_proof(n, formula, args)
            print(f'case {n:03d} verified', flush=True)
    assert total == 268
    print('59 marked cores, 21 with candidate attachments, 649 assignments, 268 cases.')


if __name__ == '__main__':
    main()
