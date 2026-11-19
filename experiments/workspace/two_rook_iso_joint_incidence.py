"""Joint real incidence/edge relaxation of the surviving two-arm rook core.

All 168 candidate signatures remain available. Known core automorphisms
are used only to average a real linear relaxation, not to impose symmetry
on an integer graph. Exact certificate replay uses the standard library.
"""

import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations, permutations, product
import json
from math import gcd
from pathlib import Path
import time

from two_rook_iso_completion import core, gram, rook, allowed_edges


MATCHING = (0, 5, 7, 8, 6, 1, 4, 2, 3)


class DisjointSets:
    def __init__(self, n):
        self.parent = list(range(n))

    def find(self, x):
        while self.parent[x] != x:
            self.parent[x] = self.parent[self.parent[x]]
            x = self.parent[x]
        return x

    def join(self, x, y):
        a, b = self.find(x), self.find(y)
        if a != b:
            self.parent[max(a, b)] = min(a, b)

    def labels(self):
        roots = sorted({self.find(x) for x in range(len(self.parent))})
        ids = {root: i for i, root in enumerate(roots)}
        return [ids[self.find(x)] for x in range(len(self.parent))]


def domain():
    rows = core(3, MATCHING)
    G = gram(rows)
    signatures, need = [], []
    for sites in product(range(9), range(9, 18), range(18, 27)):
        if not all(G[i][j] > 0 for i, j in combinations(sites, 2)):
            continue
        mask = sum(1 << i for i in sites)
        target = [2-(adj & mask).bit_count()-int(i in sites) for i, adj in enumerate(rows)]
        if min(target) < 0:
            continue
        signatures.append(sites)
        need.append(target+[11])
    assert len(signatures) == 168
    return rows, G, signatures, need


def automorphisms(rows, signatures):
    """Explicit partition-preserving automorphisms; no completeness needed."""
    rook_group = sorted({tuple(3*a[y if swap else x]+b[x if swap else y]
                               for x, y in product(range(3), repeat=2))
                         for a, b, swap in product(permutations(range(3)),
                                                   permutations(range(3)), (0, 1))})
    assert len(rook_group) == 72
    centralizer = [p for p in rook_group if all(p[MATCHING[x]] == MATCHING[p[x]] for x in range(9))]
    assert all(MATCHING[MATCHING[x]] == x for x in range(9))
    lookup = {s: i for i, s in enumerate(signatures)}
    point_maps, signature_maps = [], []
    for p, swap in product(centralizer, (False, True)):
        mapping = [9*((3-base) if swap and base else base)+p[x]
                   for base, x in product(range(3), range(9))]
        assert sorted(mapping) == list(range(27))
        assert all(((rows[i] >> j) & 1) == ((rows[mapping[i]] >> mapping[j]) & 1)
                   for i, j in combinations(range(27), 2))
        induced = [lookup[tuple(sorted(mapping[x] for x in s))] for s in signatures]
        assert sorted(induced) == list(range(len(signatures)))
        point_maps.append(mapping)
        signature_maps.append(induced)
    return point_maps, signature_maps


def build(pair_packing=False):
    rows, G, signatures, need = domain()
    edges = allowed_edges(signatures, need)
    points, symmetry = automorphisms(rows, signatures)
    edge_index = {edge: i for i, edge in enumerate(edges)}
    zsets, esets = DisjointSets(len(signatures)), DisjointSets(len(edges))
    for p in symmetry:
        for i, image in enumerate(p):
            zsets.join(i, image)
        for i, (a, b) in enumerate(edges):
            image = tuple(sorted((p[a], p[b])))
            assert image in edge_index
            esets.join(i, edge_index[image])
    zlabels, elabels = zsets.labels(), esets.labels()
    nz, ne = max(zlabels)+1, max(elabels)+1
    variable_count = nz+ne
    eq, le = {}, {}

    def insert(target, terms, rhs):
        key = tuple(sorted((v, c) for v, c in terms.items() if c))
        if key in target:
            assert target[key] == rhs
        else:
            target[key] = rhs

    # All core Gram entries, including the diagonal, and total population.
    for i in range(27):
        for j in range(i, 27):
            terms = Counter(zlabels[s] for s, sites in enumerate(signatures) if i in sites and j in sites)
            insert(eq, terms, G[i][j])
    insert(eq, Counter(zlabels), 72)
    incidence_equations = len(eq)

    incident = [[] for _ in signatures]
    for edge, (a, b) in enumerate(edges):
        variable = nz+elabels[edge]
        incident[a].append((b, variable))
        incident[b].append((a, variable))
        for endpoint in (a, b):
            insert(le, {variable: 1, zlabels[endpoint]: -1}, 0)
    for t, sites in enumerate(signatures):
        for i in range(28):
            terms = Counter(v for s, v in incident[t] if i == 27 or i in signatures[s])
            terms[zlabels[t]] -= need[t][i]
            insert(eq, terms, 0)
    for z in range(nz):
        insert(le, {z: 1}, 1)
    if pair_packing:
        neighbor_variables = [dict(neighbors) for neighbors in incident]
        for i, j in combinations(range(27), 2):
            family = [s for s, sites in enumerate(signatures) if i in sites and j in sites]
            if len(family) < 2:
                continue
            for t in range(len(signatures)):
                variables = [neighbor_variables[t][s] for s in family if s in neighbor_variables[t]]
                if len(variables) < 2:
                    continue
                terms = Counter(variables)
                terms[zlabels[t]] -= 1
                insert(le, terms, 0)

    equalities = [(list(key), value) for key, value in eq.items()]
    inequalities = [(list(key), value) for key, value in le.items()]
    return {'matching': list(MATCHING), 'pair_packing': pair_packing, 'core_rows': rows,
            'signatures': [list(s) for s in signatures],
            'candidate_edges': [list(e) for e in edges],
            'point_automorphisms': points, 'signature_automorphisms': symmetry,
            'signature_orbits': zlabels, 'edge_orbits': elabels,
            'signature_orbit_count': nz, 'edge_orbit_count': ne,
            'variables': variable_count, 'equalities': equalities,
            'incidence_equation_count': incidence_equations,
            'inequalities': inequalities}


def metadata(model):
    return {'pair_packing': model['pair_packing'],
            'signatures': len(model['signatures']), 'candidate_edges': len(model['candidate_edges']),
            'averaging_automorphisms': len(model['point_automorphisms']),
            'signature_orbits': model['signature_orbit_count'],
            'edge_orbits': model['edge_orbit_count'], 'variables': model['variables'],
            'equalities': len(model['equalities']), 'inequalities': len(model['inequalities'])}


def check_point(model, values):
    assert len(values) == model['variables'] and min(values) >= 0
    for terms, rhs in model['equalities']:
        assert sum(c*values[v] for v, c in terms) == rhs
    for terms, rhs in model['inequalities']:
        assert sum(c*values[v] for v, c in terms) <= rhs


def check_ray(model, ray):
    n_eq = len(model['equalities'])
    assert len(ray) == n_eq+len(model['inequalities'])
    assert all(type(x) is int for x in ray)
    coefficients = [0]*model['variables']
    rhs = 0
    for weight, (terms, value) in zip(ray, model['equalities']+model['inequalities']):
        rhs += weight*value
        for variable, coefficient in terms:
            coefficients[variable] += weight*coefficient
    assert min(coefficients) >= 0 and min(ray[n_eq:]) >= 0 and rhs < 0
    return {'dot_rhs': rhs, 'nonzero_entries': sum(x != 0 for x in ray),
            'minimum_variable_coefficient': min(coefficients)}


def integer_rank(matrix):
    """Integer row elimination; row gcds control intermediate growth."""
    rows = [row[:] for row in matrix]
    rank = 0
    for column in range(len(rows[0])):
        pivot = next((i for i in range(rank, len(rows)) if rows[i][column]), None)
        if pivot is None:
            continue
        rows[rank], rows[pivot] = rows[pivot], rows[rank]
        for i in range(rank+1, len(rows)):
            if not rows[i][column]:
                continue
            divisor = gcd(rows[rank][column], rows[i][column])
            scale, multiple = rows[rank][column]//divisor, rows[i][column]//divisor
            rows[i] = [scale*x-multiple*y for x, y in zip(rows[i], rows[rank])]
            divisor = 0
            for value in rows[i]:
                divisor = gcd(divisor, abs(value))
            if divisor > 1:
                rows[i] = [value//divisor for value in rows[i]]
        rank += 1
        if rank == len(rows):
            break
    return rank


def incidence_space():
    rows, G, signatures, need = domain()
    pairs = [(i, j) for i in range(27) for j in range(i, 27) if G[i][j]]
    matrix = [[int(i in s and j in s) for s in signatures] for i, j in pairs]
    rank = integer_rank(matrix)
    augmented_rank = integer_rank([row+[G[i][j]] for row, (i, j) in zip(matrix, pairs)])
    assert rank == augmented_rank == 134
    model = build()
    symmetric = []
    for terms, rhs in model['equalities'][:model['incidence_equation_count']]:
        row = [0]*model['signature_orbit_count']
        for variable, coefficient in terms:
            assert variable < len(row)
            row[variable] = coefficient
        symmetric.append(row)
    symmetric_rank = integer_rank(symmetric)
    return {'status': 'exact linear incidence dimensions', 'signatures': len(signatures),
            'positive_gram_equations': len(pairs), 'rank': rank,
            'augmented_rank': augmented_rank, 'affine_dimension': len(signatures)-rank,
            'averaging_automorphisms': len(model['point_automorphisms']),
            'signature_orbits': model['signature_orbit_count'],
            'symmetric_incidence_rank': symmetric_rank,
            'symmetric_affine_dimension': model['signature_orbit_count']-symmetric_rank}


def sparse(rows, n):
    import numpy as np
    from scipy.sparse import csc_matrix
    ri, ci, values, rhs = [], [], [], []
    for r, (terms, value) in enumerate(rows):
        rhs.append(value)
        for variable, coefficient in terms:
            ri.append(r); ci.append(variable); values.append(coefficient)
    return csc_matrix((np.array(values, dtype=int), (ri, ci)), shape=(len(rows), n)), np.array(rhs, dtype=int)


def exact_basic_point(model, point):
    """Recover a solver-proposed active system, then verify every row exactly."""
    from flint import fmpq_mat
    support = [v for v, value in enumerate(point) if value > 1e-8]
    lookup = {v: i for i, v in enumerate(support)}
    active = model['equalities']+[row for row in model['inequalities']
              if abs(sum(c*point[v] for v, c in row[0])-row[1]) < 1e-8]
    matrix = []
    for terms, rhs in active:
        row = [0]*(len(support)+1)
        row[-1] = rhs
        for variable, coefficient in terms:
            if variable in lookup:
                row[lookup[variable]] = coefficient
        matrix.append(row)
    reduced, rank = fmpq_mat(matrix).rref()
    if rank != len(support):
        return None
    values = [Fraction(0)]*model['variables']
    for i, variable in enumerate(support):
        if any(reduced[i, j] != int(i == j) for j in range(len(support))):
            return None
        values[variable] = Fraction(str(reduced[i, len(support)]))
    try:
        check_point(model, values)
    except AssertionError:
        return None
    return values


def solve(model, seconds):
    import numpy as np
    from scipy import sparse as sp
    from scipy.optimize import linprog
    n = model['variables']
    E, b = sparse(model['equalities'], n)
    L, d = sparse(model['inequalities'], n)
    started = time.monotonic()
    answer = linprog(np.zeros(n), A_eq=E, b_eq=b, A_ub=L, b_ub=d,
                     bounds=(0, None), method='highs', options={'time_limit': seconds})
    result = {'status': 'unresolved', 'metadata': metadata(model),
              'lp_status': int(answer.status), 'solver_message': answer.message,
              'seconds': time.monotonic()-started}
    if answer.success:
        for denominator in (12, 120, 1000, 100000, 10000000):
            values = [Fraction(float(x)).limit_denominator(denominator) for x in answer.x]
            try:
                check_point(model, values)
            except AssertionError:
                continue
            result.update(status='exact rational real relaxation witness',
                          values=[[v.numerator, v.denominator] for v in values])
            return result
        values = exact_basic_point(model, answer.x)
        if values is not None:
            result.update(status='exact rational real relaxation witness',
                          reconstruction='rational active-system elimination',
                          values=[[v.numerator, v.denominator] for v in values])
        else:
            result['status'] = 'numerically feasible; exact witness not recovered'
    elif answer.status == 2:
        from completion_constraints import exact_farkas
        # Convert each <= row to an equality by adding a nonnegative slack.
        A = sp.vstack((E, L), format='csc')
        slacks = sp.vstack((sp.csc_matrix((E.shape[0], L.shape[0])),
                            sp.eye(L.shape[0], dtype=int)), format='csc')
        A = sp.hstack((A, slacks), format='csc')
        ray = exact_farkas(A, np.r_[b, d])
        if ray is not None:
            result.update(status='exact exclusion of all incidence assignments', ray=ray,
                          certificate=check_ray(model, ray))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=30)
    parser.add_argument('--pair-packing', action='store_true')
    parser.add_argument('--space-only', action='store_true')
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    if args.space_only:
        result = incidence_space()
        if args.verify:
            assert result == json.loads(args.verify.read_text())
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps(result), flush=True)
        raise SystemExit
    saved = json.loads(args.verify.read_text()) if args.verify else None
    packing = saved['metadata']['pair_packing'] if saved else args.pair_packing
    model = build(packing)
    print(json.dumps({'built': metadata(model)}), flush=True)
    if args.verify:
        result = saved
        assert result['metadata'] == metadata(model)
        if 'ray' in result:
            assert check_ray(model, result['ray']) == result['certificate']
        else:
            assert result['status'] == 'exact rational real relaxation witness'
            check_point(model, [Fraction(a, b) for a, b in result['values']])
    else:
        result = solve(model, args.seconds)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('ray', 'values')}), flush=True)
