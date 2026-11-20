"""Exact small audits for the complementary-rook matching-edge tips.

Replay uses only the Python standard library.  Optional certificate generation
uses the existing numerical Farkas-ray proposal helper; every accepted ray is
then checked by integer arithmetic here.  No graph automorphism is assumed.
"""

import argparse
from collections import Counter
from fractions import Fraction
from itertools import combinations, permutations, product
import json
from pathlib import Path


P0 = (0, 5, 7, 8, 6, 1, 4, 2, 3)


def rook(p, q):
    return p != q and (p // 3 == q // 3 or p % 3 == q % 3)


def far(p, q):
    return p != q and not rook(p, q)


def add(p, q):
    return 3 * ((p // 3 + q // 3) % 3) + (p % 3 + q % 3) % 3


def subtract(p, q):
    return 3 * ((p // 3 - q // 3) % 3) + (p % 3 - q % 3) % 3


def core():
    B = [[0] * 27 for _ in range(27)]
    for i, j in combinations(range(27), 2):
        a, p = divmod(i, 9)
        b, q = divmod(j, 9)
        edge = (far(p, q) if a == 2 else rook(p, q)) if a == b else p == q
        B[i][j] = B[j][i] = int(edge)
    assert all(sum(row) == 6 for row in B)
    return B


def quota(B):
    return [[12 * (i == j) + 2 - B[i][j]
             - sum(B[i][k] * B[k][j] for k in range(27))
             for j in range(27)] for i in range(27)]


def sites(signature):
    p, q, t = signature
    return (p, 9 + q, 18 + t)


def candidate_signatures():
    B, G = core(), quota(core())
    candidates = []
    for signature in product(range(9), repeat=3):
        h = sites(signature)
        if all(G[i][j] > 0 for i, j in combinations(h, 2)) and all(
            sum(B[i][j] + (i == j) for j in h) <= 2 for i in range(27)
        ):
            candidates.append(signature)
    assert candidates == [(p, q, t) for p, q, t in product(range(9), repeat=3)
                          if far(p, q) and t not in (p, q)]
    assert len(candidates) == 252
    return candidates


def check_incidence(design):
    assert len(design) == len(set(design)) == 72
    assert set(design) <= set(candidate_signatures())
    G = quota(core())
    actual = [[0] * 27 for _ in range(27)]
    for signature in design:
        for i in sites(signature):
            for j in sites(signature):
                actual[i][j] += 1
    assert actual == G
    return True


def explicit_design():
    design = tuple(sorted((p, add(t, P0[subtract(p, t)]), t)
                          for t in range(9) for p in range(9) if p != t))
    assert Counter(subtract(P0[p], p) for p in range(9)) == {
        0: 1, 4: 2, 5: 2, 7: 2, 8: 2}
    assert all(P0[P0[p]] == p for p in range(9))
    check_incidence(design)
    return design


def rref(matrix):
    M = [[Fraction(x) for x in row] for row in matrix]
    row, pivots = 0, []
    for column in range(len(M[0]) - 1):
        pivot = next((i for i in range(row, len(M)) if M[i][column]), None)
        if pivot is None:
            continue
        M[row], M[pivot] = M[pivot], M[row]
        scale = M[row][column]
        M[row] = [x / scale for x in M[row]]
        for i in range(len(M)):
            if i != row and M[i][column]:
                scale = M[i][column]
                M[i] = [x - scale * y for x, y in zip(M[i], M[row])]
        pivots.append(column)
        row += 1
    assert all(any(line[:-1]) or line[-1] == 0 for line in M)
    return M, pivots


def a0_designs():
    """All designs with neither near/near nor far/far triples.

    For each tip, each direction N -> F and F -> N has exactly two
    perfect matchings.  The remaining RS margins are 36 linear equations
    in the resulting 18 Boolean choices.  Exact row reduction leaves six
    free Boolean coordinates, so all 64 possibilities are inspected.
    """
    far_pairs = [(p, q) for p, q in product(range(9), repeat=2) if far(p, q)]
    position = {pair: i for i, pair in enumerate(far_pairs)}
    choices, base = [], [0] * 36
    E = [[0] * 18 for _ in range(36)]
    for t in range(9):
        near = [p for p in range(9) if rook(p, t)]
        distant = [p for p in range(9) if far(p, t)]
        for left, right in ((near, distant), (distant, near)):
            options = [tuple(zip(left, image)) for image in permutations(right)
                       if all(far(p, q) for p, q in zip(left, image))]
            assert len(options) == 2
            column = len(choices)
            choices.append((t, options))
            for pair in options[0]:
                base[position[pair]] += 1
                E[position[pair]][column] -= 1
            for pair in options[1]:
                E[position[pair]][column] += 1
    rhs = [2 - x for x in base]
    reduced, pivots = rref([row + [b] for row, b in zip(E, rhs)])
    free = sorted(set(range(18)) - set(pivots))
    assert len(pivots) == 12 and len(free) == 6
    result = {}
    for bits in product((0, 1), repeat=len(free)):
        values = [Fraction(0)] * 18
        for column, bit in zip(free, bits):
            values[column] = Fraction(bit)
        for row, pivot in enumerate(pivots):
            values[pivot] = reduced[row][-1] - sum(
                reduced[row][column] * values[column] for column in free)
        if any(value not in (0, 1) for value in values):
            continue
        values = tuple(map(int, values))
        assert all(sum(a * x for a, x in zip(row, values)) == b
                   for row, b in zip(E, rhs))
        design = tuple(sorted((p, q, t) for (t, options), value in zip(choices, values)
                              for p, q in options[value]))
        check_incidence(design)
        result[design] = values
    assert len(result) == 16
    return result


def group():
    actions = []
    for rows, columns, transpose in product(permutations(range(3)),
                                           permutations(range(3)), (0, 1)):
        g = tuple(3 * rows[p % 3] + columns[p // 3] if transpose else
                  3 * rows[p // 3] + columns[p % 3] for p in range(9))
        assert all(rook(p, q) == rook(g[p], g[q])
                   for p, q in combinations(range(9), 2))
        for swap in (0, 1):
            actions.append((g, swap))
    assert len(set(actions)) == 144
    return actions


def transform(design, action):
    g, swap = action
    return tuple(sorted((g[q], g[p], g[t]) if swap else (g[p], g[q], g[t])
                        for p, q, t in design))


def design_orbits(designs):
    remaining, result = set(designs), []
    actions = group()
    while remaining:
        representative = min(remaining)
        orbit = {transform(representative, action) for action in actions}
        assert orbit <= set(designs)
        remaining -= orbit
        result.append((representative, len(orbit)))
    assert sorted(size for _, size in result) == [2, 2, 12]
    return result


def tip_cycle_types(design):
    result = []
    for t in range(9):
        image = {p: q for p, q, tip in design if tip == t}
        image[t] = t
        assert sorted(image.values()) == list(range(9))
        remaining, lengths = set(range(9)), []
        while remaining:
            start = min(remaining)
            cycle, v = [], start
            while v not in cycle:
                cycle.append(v)
                v = image[v]
            assert v == start
            remaining -= set(cycle)
            lengths.append(len(cycle))
        result.append(sorted(lengths))
    return result


def quotient(design):
    """Average a necessary real edge system over incidence automorphisms.

    Averaging is valid for the linear relaxation; it does not restrict a
    hypothetical binary completion to have any symmetry.
    """
    B = core()
    h = [sites(signature) for signature in design]
    index = {signature: i for i, signature in enumerate(design)}
    need = [[2 - sum(B[u][v] + (u == v) for v in signature)
             for u in range(27)] for signature in h]
    edges = [(v, w) for v, w in combinations(range(72), 2)
             if len(set(h[v]) & set(h[w])) <= 1
             and all(need[v][u] > 0 for u in h[w])
             and all(need[w][u] > 0 for u in h[v])]
    edge_index = {edge: i for i, edge in enumerate(edges)}
    actions = []
    for g, swap in group():
        if transform(design, (g, swap)) != design:
            continue
        image = tuple(index[(g[q], g[p], g[t]) if swap else (g[p], g[q], g[t])]
                      for p, q, t in design)
        core_image = tuple((9 if swap else 0) + g[p] for p in range(9)) + tuple(
            (0 if swap else 9) + g[p] for p in range(9)) + tuple(18 + g[p] for p in range(9))
        assert all(B[i][j] == B[core_image[i]][core_image[j]]
                   for i, j in combinations(range(27), 2))
        assert all(tuple(sorted(core_image[u] for u in h[v])) == h[image[v]]
                   for v in range(72))
        actions.append(image)
    parent = list(range(len(edges)))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for image in actions:
        for i, (v, w) in enumerate(edges):
            j = edge_index[tuple(sorted((image[v], image[w])))]
            parent[find(i)] = find(j)
    names, edge_orbits = {}, []
    for i in range(len(edges)):
        root = find(i)
        if root not in names:
            names[root] = len(names)
        edge_orbits.append(names[root])
    vertices, representatives = set(range(72)), []
    while vertices:
        v = min(vertices)
        representatives.append(v)
        vertices -= {image[v] for image in actions}
    rows = [(v, u) for v in representatives for u in range(27)]
    row_index = {row: i for i, row in enumerate(rows)}
    E = [[0] * len(names) for _ in rows]
    for i, (v, w) in enumerate(edges):
        for first, second in ((v, w), (w, v)):
            if first in representatives:
                for u in h[second]:
                    E[row_index[first, u]][edge_orbits[i]] += 1
    rhs = [need[v][u] for v, u in rows]
    duplicate = {}
    for v, (p, q, _) in enumerate(design):
        duplicate.setdefault((p, q), []).append(v)
    assert all(len(pair) == 2 for pair in duplicate.values())
    packing, descriptions, seen = [], [], set()
    for v in representatives:
        for (p, q), pair in sorted(duplicate.items()):
            row = [0] * len(names)
            for w in pair:
                edge = tuple(sorted((v, w)))
                if edge in edge_index:
                    row[edge_orbits[edge_index[edge]]] += 1
            if sum(row) <= 1 or tuple(row) in seen:
                continue
            seen.add(tuple(row))
            packing.append(row)
            descriptions.append([v, p, q])
    # Both vertices of a duplicate pair already have two common core
    # neighbors, so no exterior vertex can meet both.  Nonnegative slack
    # converts each necessary sum <= 1 into an equality.
    E = [row + [0] * len(packing) for row in E]
    for i, row in enumerate(packing):
        E.append(row + [int(j == i) for j in range(len(packing))])
        rhs.append(1)
    return E, rhs, {'eligible_edges': len(edges), 'automorphisms': len(actions),
                    'vertex_orbits': len(representatives), 'edge_orbits': len(names),
                    'rows': [list(row) for row in rows],
                    'duplicate_packing_rows': descriptions}


def verify_ray(E, rhs, ray, bounded=False):
    m, n = len(E), len(E[0])
    assert len(ray) == m + n * bool(bounded)
    assert all(type(value) is int for value in ray)
    right = sum(ray[i] * rhs[i] for i in range(m))
    if bounded:
        assert all(value >= 0 for value in ray[m:])
        right += sum(ray[m:])
    coefficients = [sum(ray[i] * E[i][j] for i in range(m))
                    + (ray[m + j] if bounded else 0) for j in range(n)]
    assert min(coefficients) >= 0 and right < 0
    return {'right_side': right, 'minimum_coefficient': min(coefficients),
            'nonzero_weights': sum(value != 0 for value in ray)}


def propose_ray(E, rhs):
    import numpy as np
    from scipy import sparse as sparse
    from scipy.optimize import linprog
    from completion_constraints import exact_farkas
    M = sparse.csc_matrix(np.array(E, dtype=np.int64))
    b = np.array(rhs, dtype=np.int64)
    ray = exact_farkas(M, b)
    if ray is not None:
        verify_ray(E, rhs, ray)
        return {'ray': ray, 'bounded': False}
    n = M.shape[1]
    M = sparse.bmat([[M, None], [sparse.eye(n), sparse.eye(n)]], format='csc')
    b = np.r_[b, np.ones(n, dtype=np.int64)]
    ray = exact_farkas(M, b)
    if ray is not None:
        verify_ray(E, rhs, ray, bounded=True)
        return {'ray': ray, 'bounded': True}
    # A rationally checked real point records the exact scope of a surviving
    # relaxation.  It is not a binary edge completion.
    point = linprog(np.zeros(len(E[0])), A_eq=np.array(E, dtype=np.int64),
                    b_eq=np.array(rhs, dtype=np.int64), bounds=(0, 1),
                    method='highs', options={'time_limit': 10})
    if point.success:
        for denominator in (1, 2, 4, 12, 60, 360, 10000):
            values = [Fraction(float(x)).limit_denominator(denominator)
                      for x in point.x]
            if all(0 <= value <= 1 for value in values) and all(
                    sum(a * value for a, value in zip(row, values)) == b
                    for row, b in zip(E, rhs)):
                return {'status': 'exact real edge relaxation feasible',
                        'rational_point': [[x.numerator, x.denominator] for x in values]}
    return {'status': 'no exact linear exclusion obtained'}


def run(path, write=False):
    explicit = explicit_design()
    designs = a0_designs()
    assert explicit in designs
    orbits = design_orbits(designs)
    if write:
        data = {'candidate_signatures': len(candidate_signatures()),
                'explicit_design': [list(s) for s in explicit],
                'a0_linear_rank': 12, 'a0_free_binary_coordinates': 6,
                'a0_design_count': len(designs), 'cases': []}
        for design, orbit_size in orbits:
            E, rhs, metadata = quotient(design)
            record = {'signatures': [list(s) for s in design],
                      'orbit_size': orbit_size, 'quotient': metadata,
                      'tip_cycle_types': tip_cycle_types(design),
                      **propose_ray(E, rhs)}
            data['cases'].append(record)
            print(json.dumps({'orbit_size': orbit_size, 'quotient': {
                key: value for key, value in metadata.items()
                if key not in ('rows', 'duplicate_packing_rows')},
                'duplicate_packing_rows': len(metadata['duplicate_packing_rows']),
                'exact_ray_found': 'ray' in record}), flush=True)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, indent=2) + '\n')
    data = json.loads(path.read_text())
    assert data['candidate_signatures'] == 252
    assert data['explicit_design'] == [list(s) for s in explicit]
    assert data['a0_linear_rank'] == 12 and data['a0_free_binary_coordinates'] == 6
    assert data['a0_design_count'] == len(designs)
    assert len(data['cases']) == len(orbits)
    checks = []
    for record, (design, orbit_size) in zip(data['cases'], orbits):
        assert record['signatures'] == [list(s) for s in design]
        assert record['orbit_size'] == orbit_size
        assert record['tip_cycle_types'] == tip_cycle_types(design)
        E, rhs, metadata = quotient(design)
        assert metadata == record['quotient']
        if 'ray' in record:
            check = verify_ray(E, rhs, record['ray'], record['bounded'])
        elif 'rational_point' in record:
            point = [Fraction(p, q) for p, q in record['rational_point']]
            assert len(point) == len(E[0])
            assert all(0 <= value <= 1 for value in point)
            assert all(sum(a * value for a, value in zip(row, point)) == b
                       for row, b in zip(E, rhs))
            check = {'status': record['status'],
                     'fractional_edge_orbits': sum(value.denominator > 1
                                                  for value in point[:metadata['edge_orbits']])}
        else:
            check = {'status': record['status']}
        checks.append({'orbit_size': orbit_size, **check})
    report = {'candidate_signatures': 252, 'positive_incidence_columns': 72,
              'a0_designs': 16, 'a0_orbits': 3, 'checks': checks,
              'exactly_excluded_a0_designs': sum(record['orbit_size'] for record
                                                in data['cases'] if 'ray' in record),
              'a0_fully_excluded': all('ray' in record for record in data['cases']),
              'whole_complementary_rook_case_excluded': False}
    print(json.dumps(report, indent=2), flush=True)
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    run(args.certificate, args.write)
