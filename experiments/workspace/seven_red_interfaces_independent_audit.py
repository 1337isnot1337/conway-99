"""Independent checks of the all-red rook-interface encoding.

The audit generates rook automorphisms by exhaustive permutations of nine
points.  It checks all four-base label assignments against direct integer
adjacency matrices and the production CNF.  A separate weaker CNF uses
only forbidden label triples and root common-neighbor counts, written as
plain clauses without auxiliary variables or cardinality encoders.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
from itertools import combinations, permutations, product
import json
from pathlib import Path
import time

from pysat.solvers import Solver


def independent_data():
    rook = tuple(tuple(int(x != y and (x // 3 == y // 3 or x % 3 == y % 3))
                       for y in range(9)) for x in range(9))
    edges = tuple((x, y) for x in range(9) for y in range(x) if rook[x][y])
    automorphisms = []
    for p in permutations(range(9)):
        if all(rook[p[x]][p[y]] for x, y in edges):
            automorphisms.append(p)
    assert len(automorphisms) == 72
    labels = tuple(p for p in automorphisms if all(not rook[x][p[x]] for x in range(9)))
    assert len(labels) == 11
    inv = tuple(tuple(p.index(x) for x in range(9)) for p in labels)
    allowed = set(labels)
    good = set()
    for a, b, c in product(range(11), repeat=3):
        # Route i -> j -> k -> i, represented directly point by point.
        result = tuple(inv[c][labels[b][labels[a][x]]] for x in range(9))
        if result in allowed:
            good.add((a, b, c))
    assert len(good) == 581
    return rook, labels, inv, good


def direct_adjacency(bases, labels, selected, rook):
    n = 9 * bases
    rows = [0] * n
    for i in range(bases):
        for x in range(9):
            for y in range(9):
                if rook[x][y]:
                    rows[9*i+x] |= 1 << (9*i+y)
    for i, j in combinations(range(bases), 2):
        p = tuple(range(9)) if i == 0 else labels[selected[i, j]]
        for x, y in enumerate(p):
            u, v = 9*i+x, 9*j+y
            rows[u] |= 1 << v
            rows[v] |= 1 << u
    return rows


def direct_valid(rows):
    return all((rows[x] & rows[y]).bit_count() + ((rows[x] >> y) & 1) <= 2
               for x in range(len(rows)) for y in range(x))


def weaker_clauses(bases, rook, labels, inverses, good):
    edges = list(combinations(range(1, bases), 2))
    variable = {(i, j, a): 1 + 11*k + a for k, (i, j) in enumerate(edges) for a in range(11)}
    clauses = []
    for i, j in edges:
        choices = [variable[i, j, a] for a in range(11)]
        clauses.append(choices)
        clauses.extend([-x, -y] for x, y in combinations(choices, 2))
    for i, j, k in combinations(range(1, bases), 3):
        for a, b, c in product(range(11), repeat=3):
            if (a, b, c) not in good:
                clauses.append([-variable[i, j, a], -variable[j, k, b], -variable[i, k, c]])
    # Pair (root,x),(i,z): two internal paths if x~z, plus one path
    # through each j with pi_{i,j}(z)=x.  The pair itself is adjacent iff x=z.
    for i in range(1, bases):
        for x, z in product(range(9), repeat=2):
            bound = 2 - int(x == z) - 2*rook[x][z]
            terms = []
            for j in range(1, bases):
                if i == j:
                    continue
                lo, hi = sorted((i, j))
                maps = labels if i < j else inverses
                terms.extend(variable[lo, hi, a] for a in range(11) if maps[a][z] == x)
            clauses.extend([-v for v in subset] for subset in combinations(terms, bound+1))
    return clauses, variable


def four_base_control(rook, labels):
    source = Path(__file__).with_name('seven_red_interfaces.py')
    spec = importlib.util.spec_from_file_location('production_interfaces', source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    production_labels = module.data()[1]
    assert labels == tuple(production_labels)
    cnf, variables, _ = module.build(None, bases=4, require_both=False)
    count = 0
    examples = []
    edges = list(combinations(range(1, 4), 2))
    with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
        for choice in product(range(11), repeat=3):
            selected = dict(zip(edges, choice))
            expected = direct_valid(direct_adjacency(4, labels, selected, rook))
            actual = solver.solve(assumptions=[variables[edge][a] for edge, a in selected.items()])
            assert actual == expected, (choice, expected, actual)
            count += expected
            if expected and len(examples) < 3:
                examples.append(list(choice))
    return {'assignments_checked': 11**3, 'valid_assignments': count, 'examples': examples,
            'production_source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
            'production_cnf_matches_direct_adjacency': True}


def direct_cut(rows, selected, variables):
    """Return one necessary clause per violated graph pair, with no gates."""
    cuts = []
    n = len(rows)
    for u in range(n):
        for v in range(u):
            common = rows[u] & rows[v]
            adjacent = (rows[u] >> v) & 1
            if common.bit_count() + adjacent <= 2:
                continue
            edges = [(u, v)] if adjacent else []
            count = adjacent
            while count < 3:
                bit = common & -common
                w = bit.bit_length() - 1
                common ^= bit
                edges.extend(((u, w), (v, w)))
                count += 1
            conditions = set()
            for a, b in edges:
                i, j = sorted((a // 9, b // 9))
                if i != j and i != 0:
                    conditions.add(variables[i, j, selected[i, j]])
            assert conditions
            cuts.append([-x for x in sorted(conditions)])
    return cuts


def lazy_full_model(b, rook, labels, inverses, good, seconds):
    clauses, variables = weaker_clauses(b, rook, labels, inverses, good)
    t = time.monotonic()
    rounds = 0
    count = 0
    record = {'bases': b, 'independent_encoding': 'direct graph witness clauses',
              'solver': 'cadical195'}
    with Solver(name='cadical195', bootstrap_with=clauses) as solver:
        while True:
            if time.monotonic()-t > seconds:
                record['status'] = 'unknown'
                break
            answer = solver.solve()
            if not answer:
                record['status'] = 'solver_unsat'
                break
            positive = set(v for v in solver.get_model() if v > 0)
            selected = {(i, j): a for (i, j, a), v in variables.items() if v in positive}
            rows = direct_adjacency(b, labels, selected, rook)
            cuts = direct_cut(rows, selected, variables)
            rounds += 1
            if not cuts:
                assert direct_valid(rows)
                record['status'] = 'partial_interface_witness'
                record['labels'] = [[i, j, a] for (i, j), a in selected.items()]
                break
            for cut in cuts:
                solver.add_clause(cut)
            count += len(cuts)
    record.update(rounds=rounds, direct_cap_cuts=count, seconds=time.monotonic()-t)
    return record


def run(bases, audit_four=True, lazy=False, seconds=60):
    start = time.monotonic()
    rook, labels, inverses, good = independent_data()
    result = {'rook_automorphisms': 72, 'allowed_labels': 11,
              'allowed_triangle_label_triples': len(good)}
    if audit_four:
        result['four_base_control'] = four_base_control(rook, labels)
        print(json.dumps(result['four_base_control']), flush=True)
    result['weak_models'] = []
    for b in bases:
        clauses, variables = weaker_clauses(b, rook, labels, inverses, good)
        t = time.monotonic()
        with Solver(name='glucose4', bootstrap_with=clauses) as solver:
            answer = solver.solve()
            record = {'bases': b, 'variables': len(variables), 'clauses': len(clauses),
                      'satisfiable': answer, 'solve_seconds': time.monotonic()-t}
            if answer:
                positive = set(v for v in solver.get_model() if v > 0)
                selected = {(i, j): a for (i, j, a), v in variables.items() if v in positive}
                record['labels'] = [[i, j, a] for (i, j), a in selected.items()]
                record['satisfies_all_pair_caps'] = direct_valid(direct_adjacency(b, labels, selected, rook))
            result['weak_models'].append(record)
            print(json.dumps(record), flush=True)
    if lazy:
        result['independent_full_models'] = []
        for b in bases:
            record = lazy_full_model(b, rook, labels, inverses, good, seconds)
            result['independent_full_models'].append(record)
            print(json.dumps(record), flush=True)
    result['seconds'] = time.monotonic()-start
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--bases', nargs='+', type=int, default=[5, 6, 7])
    parser.add_argument('--skip-four-control', action='store_true')
    parser.add_argument('--lazy-full-model', action='store_true')
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run(args.bases, not args.skip_four_control, args.lazy_full_model, args.seconds)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2)+'\n')
