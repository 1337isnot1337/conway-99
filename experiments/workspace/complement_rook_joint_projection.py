"""An exact convex projection for the complementary-rook incidence parameter.

All 252 signatures and all eligible edges enter before averaging.  Only
the real linear relaxation is averaged over core relabelings.  This is
not a symmetry assumption on a binary graph or on its incidence design.
"""

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from math import gcd
from pathlib import Path
import time

import complement_rook_a_incidence as incidence
from complement_rook_a_incidence_census import actions
from two_rook_tip_overlap_joint_lp import orbit_labels, verify_point


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build():
    rows, gram, triples, signatures, counted, margins = incidence.domain()
    group = actions()
    size = len(signatures)
    signature_sets = [set(s) for s in signatures]
    needs = [[2-int(i in s)-sum((rows[i] >> j) & 1 for j in s)
              for i in range(27)]+[11] for s in signatures]
    assert all(min(need) >= 0 and sum(need[:-1]) == 33 for need in needs)
    edges = [(v, w) for v, w in combinations(range(size), 2)
             if len(signature_sets[v] & signature_sets[w]) <= 1
             and all(needs[v][i] > 0 for i in signatures[w])
             and all(needs[w][i] > 0 for i in signatures[v])]
    assert size == 252 and len(edges) == 20934 and len(group) == 144
    selections, representatives = orbit_labels(size, group)
    edge_index = {edge: i for i, edge in enumerate(edges)}
    edge_actions = [[edge_index[tuple(sorted((action[v], action[w])))] for v, w in edges]
                    for action in group]
    edge_orbits, edge_representatives = orbit_labels(len(edges), edge_actions)
    offset = len(representatives)
    variables = offset+len(edge_representatives)
    equalities, inequalities = [], []
    seen_eq, seen_le = set(), set()

    def add(coefficients, rhs, label, equality):
        coefficients = {i: int(value) for i, value in coefficients.items() if value}
        common = abs(rhs)
        for value in coefficients.values():
            common = gcd(common, abs(value))
        if common > 1:
            coefficients = {i: value//common for i, value in coefficients.items()}
            rhs //= common
        if equality and coefficients and coefficients[min(coefficients)] < 0:
            coefficients = {i: -value for i, value in coefficients.items()}
            rhs = -rhs
        key = (tuple(sorted(coefficients.items())), rhs)
        if not coefficients:
            assert rhs == 0 if equality else rhs >= 0
            return
        seen = seen_eq if equality else seen_le
        collection = equalities if equality else inequalities
        if key not in seen:
            seen.add(key)
            collection.append({'terms': [list(pair) for pair in key[0]],
                               'rhs': rhs, 'label': label})

    for i in range(27):
        for j in range(i, 27):
            coefficients = Counter(selections[s] for s, sites in enumerate(signatures)
                                   if i in sites and j in sites)
            add(coefficients, gram[i][j], ['gram', i, j], True)
    add(Counter(selections), 72, ['population'], True)
    for s in range(offset):
        add({s: 1}, 1, ['selector_upper', s], False)
    incident = [[] for _ in signatures]
    for index, (v, w) in enumerate(edges):
        variable = offset+edge_orbits[index]
        incident[v].append((w, variable))
        incident[w].append((v, variable))
    for index in edge_representatives:
        v, w = edges[index]
        variable = offset+edge_orbits[index]
        for endpoint in (v, w):
            add(Counter({variable: 1, selections[endpoint]: -1}), 0,
                ['activation', v, w, endpoint], False)
    pair_families = [(i, j, {s for s, sites in enumerate(signatures) if i in sites and j in sites})
                     for i, j in combinations(range(27), 2)]
    for v in representatives:
        for i in range(28):
            coefficients = Counter(variable for w, variable in incident[v]
                                   if i == 27 or i in signatures[w])
            coefficients[selections[v]] -= needs[v][i]
            add(coefficients, 0, ['degree' if i == 27 else 'mixed', v, i], True)
        for i, j, family in pair_families:
            variables_in_family = [variable for w, variable in incident[v] if w in family]
            if len(variables_in_family) < 2:
                continue
            coefficients = Counter(variables_in_family)
            coefficients[selections[v]] -= 1
            add(coefficients, 0, ['core_pair_packing', v, i, j], False)
    objective = sorted(Counter(selections[s] for s in counted).items())
    model = {'variables': variables, 'equalities': equalities,
             'inequalities': inequalities, 'objective': [list(pair) for pair in objective]}
    metadata = {'scope': 'necessary real incidence, mixed-edge, and core-pair-packing relaxation',
                'candidate_signatures': size, 'eligible_edges': len(edges), 'group_order': len(group),
                'selector_orbits': offset, 'edge_orbits': len(edge_representatives),
                'variables': variables, 'equalities': len(equalities),
                'inequalities': len(inequalities),
                'selector_representative_triples': [triples[s] for s in representatives],
                'selector_orbit_sizes': [selections.count(i) for i in range(offset)],
                'equality_types': dict(Counter(row['label'][0] for row in equalities)),
                'inequality_types': dict(Counter(row['label'][0] for row in inequalities)),
                'model_sha256': hashlib.sha256(json.dumps(model, sort_keys=True,
                                                        separators=(',', ':')).encode()).hexdigest()}
    return model, metadata


def objective_value(model, point):
    return sum(value*point[i] for i, value in model['objective'])


def verify_upper(model, weights):
    rows = model['equalities']+model['inequalities']
    assert len(weights) == len(rows)
    assert min(weights[len(model['equalities']):]) >= 0
    coefficients = [Fraction(0)]*model['variables']
    rhs = Fraction(0)
    for weight, row in zip(weights, rows):
        rhs += weight*row['rhs']
        for variable, coefficient in row['terms']:
            coefficients[variable] += weight*coefficient
    for variable, value in model['objective']:
        coefficients[variable] -= value
    assert min(coefficients) >= 0
    return rhs


def encode(values):
    return [[value.numerator, value.denominator] for value in values]


def solve(model, seconds):
    import highspy
    import numpy as np
    from scipy import sparse
    rows = model['equalities']+model['inequalities']
    rr, cc, values = [], [], []
    for i, row in enumerate(rows):
        for variable, value in row['terms']:
            rr.append(i); cc.append(variable); values.append(value)
    matrix = sparse.csc_matrix((values, (rr, cc)), shape=(len(rows), model['variables']))
    rhs = np.array([row['rhs'] for row in rows], dtype=float)
    cost = np.zeros(model['variables'])
    for i, value in model['objective']:
        cost[i] = -value
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = model['variables'], len(rows)
    lp.col_cost_, lp.col_lower_ = cost, np.zeros(model['variables'])
    lp.col_upper_ = np.full(model['variables'], highspy.kHighsInf)
    lower = rhs.copy()
    lower[len(model['equalities']):] = -highspy.kHighsInf
    lp.row_lower_ = lower
    lp.row_upper_ = rhs
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_ = matrix.indptr
    lp.a_matrix_.index_ = matrix.indices
    lp.a_matrix_.value_ = matrix.data.astype(float)
    solver = highspy.Highs()
    solver.setOptionValue('output_flag', False)
    solver.setOptionValue('threads', 1)
    solver.setOptionValue('time_limit', seconds)
    solver.passModel(lp)
    started = time.monotonic()
    solver.run()
    status = solver.getModelStatus()
    result = {'status': 'no exact bound or point certified', 'numerical_status': str(status),
              'seconds': time.monotonic()-started, 'requested_seconds': seconds}
    if status != highspy.HighsModelStatus.kOptimal:
        return result
    solution = solver.getSolution()
    for denominator in (1, 2, 6, 12, 48, 360, 4096, 1000000):
        if 'point' not in result:
            point = [Fraction(float(v)).limit_denominator(denominator) for v in solution.col_value]
            try:
                check = verify_point(model, point)
            except AssertionError:
                pass
            else:
                result.update(point=encode(point), point_check=check,
                              point_a=encode([objective_value(model, point)])[0])
        if 'upper_weights' not in result:
            weights = [Fraction(float(-v)).limit_denominator(denominator) for v in solution.row_dual]
            try:
                bound = verify_upper(model, weights)
            except AssertionError:
                pass
            else:
                result.update(upper_weights=encode(weights), upper_bound=encode([bound])[0])
    if 'point' in result and 'upper_weights' in result:
        assert result['point_a'] == result['upper_bound']
        result['status'] = 'exact optimum of the stated real relaxation certified'
    return result


def run(path, write, seconds):
    model, metadata = build()
    sources = {name: digest(Path(__file__).with_name(name)) for name in
               ('complement_rook_joint_projection.py', 'complement_rook_a_incidence.py',
                'complement_rook_a_incidence_census.py', 'two_rook_tip_overlap_joint_lp.py')}
    print(json.dumps({'metadata': metadata}), flush=True)
    if write:
        result = solve(model, seconds)
        path.write_text(json.dumps({'metadata': metadata, 'source_hashes': sources,
                                   'result': result}, indent=2)+'\n')
    saved = json.loads(path.read_text())
    assert saved['metadata'] == json.loads(json.dumps(metadata))
    assert saved['source_hashes'] == sources
    result = saved['result']
    if 'point' in result:
        point = [Fraction(p, q) for p, q in result['point']]
        assert verify_point(model, point) == result['point_check']
        assert encode([objective_value(model, point)])[0] == result['point_a']
    if 'upper_weights' in result:
        weights = [Fraction(p, q) for p, q in result['upper_weights']]
        assert encode([verify_upper(model, weights)])[0] == result['upper_bound']
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('point', 'upper_weights')}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    parser.add_argument('--seconds', type=float, default=10)
    args = parser.parse_args()
    assert 0 < args.seconds <= 30
    run(args.certificate, args.write, args.seconds)
