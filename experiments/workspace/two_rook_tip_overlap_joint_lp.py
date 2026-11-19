"""Exact replay for a full joint real relaxation of rook-tip core3679836361.

Every candidate incidence selector is retained.  Averaging over the fixed
core/domain automorphisms is used only for this convex real relaxation.
No fixed 72-column incidence design or graph automorphism is assumed.
"""

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import combinations, permutations, product
import json
from math import gcd, lcm
from pathlib import Path
import time


REPRESENTATIVE = 3679836361


def rook(p, q):
    return p != q and (p // 3 == q // 3 or p % 3 == q % 3)


def matrix_data(domain_path):
    data = json.loads(domain_path.read_text())
    saved = next(case for case in data['cases'] if case['representative'] == REPRESENTATIVE)
    Z = [[0] * 9 for _ in range(9)]
    for bit, (p, q) in enumerate(combinations(range(9), 2)):
        Z[p][q] = Z[q][p] = (REPRESENTATIVE >> bit) & 1
    B = [[0] * 27 for _ in range(27)]
    for i, j in combinations(range(27), 2):
        a, p = divmod(i, 9)
        b, q = divmod(j, 9)
        value = (Z[p][q] if a == 2 else int(rook(p, q))) if a == b else int(p == q)
        B[i][j] = B[j][i] = value
    assert all(sum(row) == 6 for row in B)
    rows = [sum(value << j for j, value in enumerate(row)) for row in B]
    assert rows == saved['core_rows']
    G = [[12 * int(i == j) + 2 - B[i][j]
          - sum(B[i][k] * B[k][j] for k in range(27))
          for j in range(27)] for i in range(27)]
    assert G == saved['core_gram']
    signatures, need = [], []
    for p, q, t in product(range(9), repeat=3):
        signature = (p, 9 + q, 18 + t)
        quota = [2 - sum(B[i][j] + int(i == j) for j in signature)
                 for i in range(27)]
        if all(G[i][j] > 0 for i, j in combinations(signature, 2)) and min(quota) >= 0:
            signatures.append(signature)
            need.append(quota + [11])
    assert [list(s) for s in signatures] == saved['core_signatures']
    assert [row[:-1] for row in need] == saved['mixed_need']
    assert len(signatures) == 188
    margins = [([s for s, signature in enumerate(signatures) if i in signature and j in signature],
                G[i][j]) for i in range(27) for j in range(i, 27)]
    # Independent elementary replay of the propagated binary units.  All
    # these units already follow from Gram margins and 0 <= selector <= 1.
    forced = {}
    changed = True
    while changed:
        changed = False
        for family, quota in margins:
            residual = quota - sum(forced.get(s, 0) for s in family)
            remaining = [s for s in family if s not in forced]
            assert 0 <= residual <= len(remaining)
            if remaining and residual in (0, len(remaining)):
                value = int(residual > 0)
                forced.update((s, value) for s in remaining)
                changed = True
    assert sorted(s for s, value in forced.items() if value) == saved['forced_one_indices']
    assert sorted(s for s, value in forced.items() if not value) == saved['forced_zero_indices']
    edges = [(v, w) for v, w in combinations(range(len(signatures)), 2)
             if len(set(signatures[v]) & set(signatures[w])) <= 1
             and all(need[v][i] > 0 for i in signatures[w])
             and all(need[w][i] > 0 for i in signatures[v])]
    assert len(edges) == 12010
    return B, G, signatures, need, edges, forced


def automorphisms(B, signatures, forced):
    index = {signature: i for i, signature in enumerate(signatures)}
    result = []
    for rows, columns, transpose in product(permutations(range(3)),
                                           permutations(range(3)), (0, 1)):
        g = tuple(3 * rows[p % 3] + columns[p // 3] if transpose else
                  3 * rows[p // 3] + columns[p % 3] for p in range(9))
        for swap in (0, 1):
            core_image = tuple((9 if swap else 0) + g[p] for p in range(9)) + tuple(
                (0 if swap else 9) + g[p] for p in range(9)) + tuple(18 + g[p] for p in range(9))
            if any(B[i][j] != B[core_image[i]][core_image[j]]
                   for i, j in combinations(range(27), 2)):
                continue
            image = tuple(index[tuple(sorted(core_image[i] for i in signature))]
                          for signature in signatures)
            assert all(forced.get(s) == forced.get(image[s]) for s in range(len(signatures)))
            result.append((core_image, image))
    assert len(result) == 8
    image_set = {image for _, image in result}
    assert all(tuple(first[second[s]] for s in range(len(signatures))) in image_set
               for first in image_set for second in image_set)
    return result


def orbit_labels(size, actions):
    parent = list(range(size))

    def find(i):
        while parent[i] != i:
            parent[i] = parent[parent[i]]
            i = parent[i]
        return i

    for image in actions:
        for i, j in enumerate(image):
            parent[find(i)] = find(j)
    names, labels, representatives = {}, [], []
    for i in range(size):
        root = find(i)
        if root not in names:
            names[root] = len(names)
            representatives.append(i)
        labels.append(names[root])
    return labels, representatives


def build(domain_path):
    started = time.monotonic()
    B, G, signatures, need, edges, forced = matrix_data(domain_path)
    actions = automorphisms(B, signatures, forced)
    selection_orbits, selected_representatives = orbit_labels(
        len(signatures), [image for _, image in actions])
    edge_index = {edge: i for i, edge in enumerate(edges)}
    edge_actions = [tuple(edge_index[tuple(sorted((image[v], image[w])))] for v, w in edges)
                    for _, image in actions]
    edge_orbits, edge_representatives = orbit_labels(len(edges), edge_actions)
    offset = len(selected_representatives)
    variables = offset + len(edge_representatives)
    equalities, inequalities = [], []
    eq_seen, le_seen = set(), set()

    def add_row(collection, seen, coefficients, rhs, label, equality=False):
        coefficients = {i: value for i, value in coefficients.items() if value}
        common = abs(rhs)
        for value in coefficients.values():
            common = gcd(common, abs(value))
        if common > 1:
            coefficients = {i: value // common for i, value in coefficients.items()}
            rhs //= common
        if equality and coefficients and coefficients[min(coefficients)] < 0:
            coefficients = {i: -value for i, value in coefficients.items()}
            rhs = -rhs
        key = (tuple(sorted(coefficients.items())), rhs)
        if not coefficients:
            assert rhs == 0 if equality else rhs >= 0
        elif key not in seen:
            seen.add(key)
            collection.append({'terms': [list(item) for item in key[0]], 'rhs': rhs, 'label': label})

    def eq(coefficients, rhs, label):
        add_row(equalities, eq_seen, coefficients, rhs, label, equality=True)

    def le(coefficients, rhs, label):
        add_row(inequalities, le_seen, coefficients, rhs, label)

    for i in range(27):
        for j in range(i, 27):
            coefficients = Counter(selection_orbits[s] for s, signature in enumerate(signatures)
                                   if i in signature and j in signature)
            eq(coefficients, G[i][j], ['gram', i, j])
    eq(Counter(selection_orbits), 72, ['population'])
    for s, value in sorted(forced.items()):
        eq({selection_orbits[s]: 1}, value, ['forced', s])
    for orbit in range(offset):
        le({orbit: 1}, 1, ['selector_upper', orbit])
    incident = [[] for _ in signatures]
    for i, (v, w) in enumerate(edges):
        variable = offset + edge_orbits[i]
        incident[v].append((w, variable))
        incident[w].append((v, variable))
    for edge in edge_representatives:
        v, w = edges[edge]
        variable = offset + edge_orbits[edge]
        le({variable: 1, selection_orbits[v]: -1}, 0, ['activation', v, w, v])
        le({variable: 1, selection_orbits[w]: -1}, 0, ['activation', v, w, w])
    families = [(i, j, set(s for s, signature in enumerate(signatures)
                          if i in signature and j in signature))
                for i, j in combinations(range(27), 2)]
    for v in selected_representatives:
        selected = selection_orbits[v]
        for u in range(28):
            coefficients = Counter(variable for w, variable in incident[v]
                                   if u == 27 or u in signatures[w])
            coefficients[selected] -= need[v][u]
            eq(coefficients, 0, ['mixed' if u < 27 else 'degree', v, u])
        for i, j, family in families:
            literals = [variable for w, variable in incident[v] if w in family]
            if len(literals) < 2:
                continue
            coefficients = Counter(literals)
            coefficients[selected] -= 1
            le(coefficients, 0, ['core_pair_packing', v, i, j])
    model = {'variables': variables, 'equalities': equalities, 'inequalities': inequalities}
    encoded = json.dumps(model, sort_keys=True, separators=(',', ':')).encode()
    metadata = {'representative': REPRESENTATIVE, 'signature_variables_before_averaging': 188,
                'edge_variables_before_averaging': 12010, 'core_domain_automorphisms': len(actions),
                'selector_orbits': offset, 'edge_orbits': len(edge_representatives),
                'equalities': len(equalities), 'inequalities': len(inequalities),
                'equality_types': dict(Counter(row['label'][0] for row in equalities)),
                'inequality_types': dict(Counter(row['label'][0] for row in inequalities)),
                'forced_ones': sum(forced.values()), 'forced_zeros': len(forced) - sum(forced.values()),
                'model_sha256': hashlib.sha256(encoded).hexdigest(),
                'domain_sha256': hashlib.sha256(domain_path.read_bytes()).hexdigest(),
                'fixed_incidence_designs': 0}
    return model, metadata, time.monotonic() - started


def verify_ray(model, ray):
    rows = model['equalities'] + model['inequalities']
    assert len(ray) == len(rows) and all(type(value) is int for value in ray)
    assert all(value >= 0 for value in ray[len(model['equalities']):])
    coefficients = [0] * model['variables']
    rhs = 0
    for value, row in zip(ray, rows):
        rhs += value * row['rhs']
        for variable, coefficient in row['terms']:
            coefficients[variable] += value * coefficient
    assert min(coefficients) >= 0 and rhs < 0
    return {'right_side': rhs, 'minimum_coefficient': min(coefficients),
            'nonzero_weights': sum(value != 0 for value in ray),
            'maximum_weight': max(map(abs, ray))}


def verify_point(model, point):
    assert len(point) == model['variables'] and min(point) >= 0
    for row in model['equalities']:
        assert sum(coefficient * point[variable] for variable, coefficient in row['terms']) == row['rhs']
    for row in model['inequalities']:
        assert sum(coefficient * point[variable] for variable, coefficient in row['terms']) <= row['rhs']
    return {'status': 'exact real joint relaxation feasible',
            'fractional_variables': sum(value.denominator > 1 for value in point),
            'maximum_denominator': max(value.denominator for value in point)}


def solve(model, seconds):
    import highspy
    import numpy as np
    from scipy import sparse
    rows = model['equalities'] + model['inequalities']
    eq_count = len(model['equalities'])
    variable_count = model['variables']
    rr, cc, values = [], [], []
    for i, row in enumerate(rows):
        for variable, value in row['terms']:
            rr.append(i); cc.append(variable); values.append(value)
        if i >= eq_count:
            rr.append(i); cc.append(variable_count + i - eq_count); values.append(1)
    E = sparse.csc_matrix((np.array(values, dtype=np.int64), (rr, cc)),
                          shape=(len(rows), variable_count + len(model['inequalities'])))
    rhs = np.array([row['rhs'] for row in rows], dtype=np.int64)
    h = highspy.Highs()
    h.setOptionValue('output_flag', False)
    h.setOptionValue('threads', 1)
    h.setOptionValue('time_limit', seconds)
    h.setOptionValue('presolve', 'off')
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = E.shape[1], E.shape[0]
    lp.col_cost_ = np.zeros(E.shape[1])
    lp.col_lower_ = np.zeros(E.shape[1])
    lp.col_upper_ = np.full(E.shape[1], highspy.kHighsInf)
    lp.row_lower_ = rhs.astype(float)
    lp.row_upper_ = rhs.astype(float)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = E.indptr
    lp.a_matrix_.index_ = E.indices
    lp.a_matrix_.value_ = E.data.astype(float)
    h.passModel(lp)
    started = time.monotonic()
    h.run()
    status = h.getModelStatus()
    result = {'numerical_status': str(status), 'seconds': time.monotonic() - started,
              'requested_seconds': seconds, 'threads': 1}
    if status == highspy.HighsModelStatus.kInfeasible:
        _, exists, proposed = h.getDualRay()
        if exists:
            for denominator in (1, 2, 4, 16, 64, 256, 4096, 100000):
                rational = [Fraction(float(value)).limit_denominator(denominator) for value in proposed]
                multiple = lcm(*(value.denominator for value in rational))
                ray = [int(value * multiple) for value in rational]
                common = 0
                for value in ray:
                    common = gcd(common, abs(value))
                if common:
                    ray = [value // common for value in ray]
                for sign in (1, -1):
                    candidate = [sign * value for value in ray]
                    try:
                        check = verify_ray(model, candidate)
                    except AssertionError:
                        continue
                    return {**result, 'status': 'exact full joint linear exclusion',
                            'ray': candidate, 'check': check}
    elif status == highspy.HighsModelStatus.kOptimal:
        values = h.getSolution().col_value[:variable_count]
        for denominator in (1, 2, 4, 12, 60, 360, 4096, 100000):
            point = [Fraction(float(value)).limit_denominator(denominator) for value in values]
            try:
                check = verify_point(model, point)
            except AssertionError:
                continue
            return {**result, **check, 'point': [[value.numerator, value.denominator] for value in point]}
    return {**result, 'status': 'no exact exclusion or feasible point certified'}


def run(domains, certificate, write=False, seconds=30):
    model, metadata, build_seconds = build(domains)
    print(json.dumps({'built': metadata, 'build_seconds': build_seconds}), flush=True)
    if write:
        result = solve(model, seconds)
        data = {'metadata': metadata, 'result': result}
        certificate.parent.mkdir(parents=True, exist_ok=True)
        certificate.write_text(json.dumps(data, indent=2) + '\n')
    data = json.loads(certificate.read_text())
    assert data['metadata'] == metadata
    result = data['result']
    if 'ray' in result:
        assert verify_ray(model, result['ray']) == result['check']
    elif 'point' in result:
        check = verify_point(model, [Fraction(p, q) for p, q in result['point']])
        assert all(result[key] == value for key, value in check.items())
    print(json.dumps({key: value for key, value in result.items() if key not in ('ray', 'point')}, indent=2),
          flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--domains', type=Path, required=True)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--seconds', type=float, default=30)
    args = parser.parse_args()
    run(args.domains, args.certificate, args.write, args.seconds)
