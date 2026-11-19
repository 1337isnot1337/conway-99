"""The 27-point covers of the rook graph by nine triangles and their exterior types."""
import argparse
from collections import Counter
from itertools import combinations, permutations, product
from pathlib import Path
import subprocess
import tempfile

import numpy as np
import pynauty

PERMS = tuple(permutations(range(3)))
WORDS = np.array([tuple(9*i + 3*cols[i] + signs[i] for i in range(3))
                  for cols in PERMS for signs in product(range(3), repeat=3)])
INCIDENCE = np.zeros((162, 27), dtype=int)
INCIDENCE[np.arange(162)[:, None], WORDS] = 1


def certificate(matrix, core_size=None):
    colors = [] if core_size is None else [set(range(core_size)), set(range(core_size, len(matrix)))]
    graph = pynauty.Graph(len(matrix), adjacency_dict={
        i: np.flatnonzero(row).tolist() for i, row in enumerate(matrix)
    }, vertex_coloring=colors)
    return pynauty.certificate(graph)


def core(labels):
    matrix = np.zeros((27, 27), dtype=int)
    transport = {(i, j): PERMS[labels[2*(i-1)+j-1]] if i and j else PERMS[0]
                 for i, j in product(range(3), repeat=2)}
    for u, v in combinations(range(27), 2):
        i, j, a = u//9, (u//3) % 3, u % 3
        k, l, b = v//9, (v//3) % 3, v % 3
        if ((i == k and (j == l or a == b)) or
                (j == l and transport[i, j][a] == transport[k, l][b])):
            matrix[u, v] = matrix[v, u] = 1
    return matrix


def attachment_sets(words, quota):
    """All binary 3-by-3-by-3 tables for one permutation of the nine cells."""
    choices = [list(combinations(range(3), int(quota[u, v]))) for u, v, _ in words[::3]]
    first = quota[np.ix_(words[::9, 0], words[:3, 2])].copy()
    second = quota[np.ix_(words[::3, 1][:3], words[:3, 2])].copy()

    def visit(k, selected):
        if k == 9:
            if not first.any() and not second.any():
                yield selected
            return
        a, b = divmod(k, 3)
        for subset in choices[k]:
            if any(first[a, c] == 0 or second[b, c] == 0 for c in subset):
                continue
            for c in subset:
                first[a, c] -= 1
                second[b, c] -= 1
            yield from visit(k+1, selected + tuple(3*k+c for c in subset))
            for c in subset:
                first[a, c] += 1
                second[b, c] += 1

    return list(visit(0, ()))


def cases():
    seen = set()
    counts = Counter()
    for labels in product(range(6), repeat=4):
        a = core(labels)
        key = certificate(a)
        if key in seen:
            continue
        seen.add(key)
        quota = 12*np.eye(27, dtype=int) + 2 - a - a @ a
        if np.any(quota < 0):
            continue
        domains = [attachment_sets(WORDS[27*i:27*i+27], quota) for i in range(6)]
        seen_exterior = set()
        for assignment in product(*domains):
            ids = [27*i+j for i, group in enumerate(assignment) for j in group]
            incidence = INCIDENCE[ids]
            assert len(ids) == 72 and np.array_equal(incidence.T @ incidence, quota)
            fixed = np.block([[a, incidence.T], [incidence, np.zeros((72, 72), dtype=int)]])
            exterior_key = certificate(fixed, 27)
            counts['assignments'] += 1
            if exterior_key in seen_exterior:
                continue
            seen_exterior.add(exterior_key)
            yield labels, a, incidence
        if seen_exterior:
            counts['extendible'] += 1
    assert len(seen) == 18 and counts == {'assignments': 484, 'extendible': 5}


def adjacency_formula(a, incidence, all_pairs):
    from pysat.card import CardEnc, EncType
    from pysat.formula import CNF, IDPool

    outside, inside = incidence.shape
    overlap = incidence @ incidence.T
    required = 2 - incidence - incidence @ a
    assert np.min(required) >= 0
    edges = {}
    for x, y in combinations(range(outside), 2):
        if (overlap[x, y] <= 1 and np.all(required[x] >= incidence[y]) and
                np.all(required[y] >= incidence[x])):
            edges[x, y] = len(edges) + 1
    pool = IDPool(start_from=len(edges)+1)
    formula = CNF()

    def at_most(lits, bound):
        if bound < 0:
            formula.append([])
        elif bound >= len(lits):
            return
        elif bound == 0:
            formula.extend([[-x] for x in lits])
        elif bound <= 2 and len(lits) <= 7:
            formula.extend([[-x for x in subset] for subset in combinations(lits, bound+1)])
        else:
            formula.extend(CardEnc.atmost(lits, bound=bound, vpool=pool,
                                          encoding=EncType.seqcounter).clauses)

    for x in range(outside):
        for i in range(inside):
            lits = [edges[tuple(sorted((x, y)))] for y in np.flatnonzero(incidence[:, i])
                    if tuple(sorted((x, y))) in edges]
            bound = int(required[x, i])
            at_most(lits, bound)
            at_most([-v for v in lits], len(lits)-bound)
    for x, y in combinations(range(outside), 2):
        limit = 2 - int(overlap[x, y])
        direct = edges.get((x, y))
        contacts = [direct] if direct else []
        for z in range(outside):
            u = edges.get(tuple(sorted((x, z))))
            v = edges.get(tuple(sorted((y, z))))
            if u is None or v is None:
                continue
            if limit == 0:
                formula.append([-u, -v])
            elif limit == 1 and direct:
                formula.append([-direct, -u, -v])
            if all_pairs and limit:
                common = pool.id()
                formula.append([-u, -v, common])
                contacts.append(common)
        if all_pairs and limit:
            at_most(contacts, limit)
    return formula, edges


def positive_control():
    from pysat.solvers import Solver

    rook = np.array([[int(i != j and (i//3 == j//3 or i%3 == j%3)) for j in range(9)]
                     for i in range(9)])
    for mask in range(1, 511):
        inside = [i for i in range(9) if mask & (1 << i)]
        outside = [i for i in range(9) if i not in inside]
        a, b = rook[np.ix_(inside, inside)], rook[np.ix_(outside, inside)]
        formula, edges = adjacency_formula(a, b, True)
        witness = []
        for i, j in combinations(range(len(outside)), 2):
            lit = edges.get((i, j))
            if rook[outside[i], outside[j]]:
                assert lit is not None
                witness.append(lit)
            elif lit is not None:
                witness.append(-lit)
        with Solver(name='glucose3', bootstrap_with=formula) as solver:
            assert solver.solve(assumptions=witness)
    print('The true exterior graph passed all 510 nontrivial splits of the nine-point rook graph.')


def verify_case(number, labels, a, incidence, args):
    # The final core has six harder cases. Use all outer pair bounds for it.
    formula, _ = adjacency_formula(a, incidence, labels == (3, 4, 4, 3))
    with tempfile.TemporaryDirectory() as directory:
        cnf = Path(directory) / 'instance.cnf'
        proof = Path(directory) / 'proof.drat'
        formula.to_file(str(cnf))
        result = subprocess.run([args.solver, str(cnf), str(proof)],
                                stdout=subprocess.DEVNULL)
        if result.returncode != 20:
            raise RuntimeError(f'case {number}: solver exit {result.returncode}')
        check = subprocess.run([args.checker, str(cnf), str(proof)],
                               stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if check.returncode or b's VERIFIED' not in check.stdout:
            raise RuntimeError(f'case {number}: proof check failed')
    print(f'case {number:02d} {labels} verified', flush=True)


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
    totals = Counter()
    for n, (labels, a, incidence) in enumerate(cases()):
        totals[labels] += 1
        if args.verify and n % count == index:
            verify_case(n, labels, a, incidence, args)
    assert list(totals.values()) == [2, 21, 51, 6, 6]
    print('1296 normalized covers, 18 cores, 484 exterior attachments, 86 cases.')


if __name__ == '__main__':
    main()
