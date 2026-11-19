"""Exact nine-tip PSD audit for two rook grids with an isomorphic matching.

The verifier uses only rational/integer arithmetic and the standard library.
The generic congruence routine also returns integer negative vectors, which
give necessary linear inequalities on tip edges for later search models.
"""

import argparse
from fractions import Fraction as F
from functools import reduce
import hashlib
from itertools import combinations
import json
from math import gcd, lcm
from pathlib import Path


def rook(a, b):
    return a != b and (a//3 == b//3 or a % 3 == b % 3)


def eye(n):
    return [[F(i == j) for j in range(n)] for i in range(n)]


def transpose(a):
    return [list(row) for row in zip(*a)]


def multiply(a, b):
    return [[sum(x*y for x, y in zip(row, column)) for column in zip(*b)]
            for row in a]


def quadratic(matrix, vector):
    return sum(vector[i]*matrix[i][j]*vector[j]
               for i in range(len(vector)) for j in range(len(vector)))


def primitive(vector):
    denominator = lcm(*(F(x).denominator for x in vector))
    integers = [int(x*denominator) for x in vector]
    divisor = reduce(gcd, integers)
    assert divisor
    integers = [x//divisor for x in integers]
    if next(x for x in integers if x) < 0:
        integers = [-x for x in integers]
    return integers


def determinant(matrix):
    a = [[F(x) for x in row] for row in matrix]
    value = F(1)
    for i in range(len(a)):
        pivot = next((j for j in range(i, len(a)) if a[j][i]), None)
        if pivot is None:
            return F(0)
        if pivot != i:
            a[i], a[pivot] = a[pivot], a[i]
            value = -value
        value *= a[i][i]
        for j in range(i+1, len(a)):
            ratio = a[j][i]/a[i][i]
            for k in range(i+1, len(a)):
                a[j][k] -= ratio*a[i][k]
            a[j][i] = F(0)
    return value


def rational_matrix(a):
    return [[[F(x).numerator, F(x).denominator] for x in row] for row in a]


def read_matrix(a):
    return [[F(*x) for x in row] for row in a]


def congruence(matrix):
    """Return an exact PSD congruence, or an integer negative vector."""
    n = len(matrix)
    a = [[F(x) for x in row] for row in matrix]
    transform = eye(n)
    for k in range(n):
        negative = next((i for i in range(k, n) if a[i][i] < 0), None)
        if negative is not None:
            vector = primitive([row[negative] for row in transform])
            assert quadratic(matrix, vector) < 0
            return {'status': 'not PSD', 'negative_vector': vector,
                    'quadratic_value': int(quadratic(matrix, vector))}
        positive = next((i for i in range(k, n) if a[i][i] > 0), None)
        if positive is None:
            off_diagonal = next(((i, j) for i in range(k, n)
                                 for j in range(i+1, n) if a[i][j]), None)
            if off_diagonal is None:
                break
            i, j = off_diagonal
            sign = 1 if a[i][j] > 0 else -1
            vector = primitive([row[i]-sign*row[j] for row in transform])
            assert quadratic(matrix, vector) < 0
            return {'status': 'not PSD', 'negative_vector': vector,
                    'quadratic_value': int(quadratic(matrix, vector))}
        if positive != k:
            a[positive], a[k] = a[k], a[positive]
            for row in a:
                row[positive], row[k] = row[k], row[positive]
            for row in transform:
                row[positive], row[k] = row[k], row[positive]
        pivot = a[k][k]
        ratios = {j: a[k][j]/pivot for j in range(k+1, n)}
        for j in range(k+1, n):
            for i in range(n):
                transform[i][j] -= ratios[j]*transform[i][k]
        for i in range(k+1, n):
            for j in range(k+1, n):
                a[i][j] -= ratios[i]*ratios[j]*pivot
        for j in range(k+1, n):
            a[k][j] = a[j][k] = F(0)
    assert all(a[i][j] == 0 for i in range(n) for j in range(n) if i != j)
    assert all(a[i][i] >= 0 for i in range(n))
    assert multiply(transpose(transform), multiply(matrix, transform)) == a
    assert determinant(transform)
    diagonal = [a[i][i] for i in range(n)]
    return {'status': 'PSD', 'rank': sum(x > 0 for x in diagonal),
            'transform': rational_matrix(transform),
            'diagonal': [[x.numerator, x.denominator] for x in diagonal],
            'integer_kernel_basis': [primitive([row[j] for row in transform])
                                     for j in range(n) if not diagonal[j]]}


def tip_matrix(tip_edges):
    edges = {tuple(edge) for edge in tip_edges}
    assert len(edges) == len(tip_edges)
    assert all(0 <= a < b < 9 for a, b in edges)
    return [[3*int(i == j)-int(rook(i, j))+1
             -2*int(tuple(sorted((i, j))) in edges) for j in range(9)]
            for i in range(9)]


def edge_cut(vector):
    """The inequality is sum(coefficient * edge) <= rhs."""
    assert len(vector) == 9 and all(type(x) is int for x in vector)
    rhs = 3*sum(x*x for x in vector)+sum(vector)**2
    rhs -= 2*sum(vector[i]*vector[j] for i, j in combinations(range(9), 2)
                 if rook(i, j))
    terms = [[i, j, 4*vector[i]*vector[j]] for i, j in combinations(range(9), 2)
             if vector[i]*vector[j]]
    return {'terms': terms, 'rhs': rhs}


def verify_congruence(matrix, certificate):
    if certificate['status'] == 'not PSD':
        vector = certificate['negative_vector']
        assert all(type(x) is int for x in vector)
        assert quadratic(matrix, vector) == certificate['quadratic_value'] < 0
        return
    assert certificate['status'] == 'PSD'
    transform = read_matrix(certificate['transform'])
    n = len(matrix)
    assert len(transform) == n and all(len(row) == n for row in transform)
    assert determinant(transform)
    diagonal = [F(*x) for x in certificate['diagonal']]
    assert len(diagonal) == n and min(diagonal) >= 0
    expected = [[diagonal[i] if i == j else F(0) for j in range(n)]
                for i in range(n)]
    assert multiply(transpose(transform), multiply(matrix, transform)) == expected
    assert certificate['rank'] == sum(x > 0 for x in diagonal)
    kernels = certificate['integer_kernel_basis']
    assert kernels == [primitive([row[j] for row in transform])
                       for j in range(n) if not diagonal[j]]
    assert all(all(sum(matrix[i][j]*v[j] for j in range(n)) == 0 for i in range(n))
               for v in kernels)


def fixed_controls():
    """Check the Schur formula and a second spectral-projector formula."""
    r = [[F(rook(i, j)) for j in range(9)] for i in range(9)]
    e1 = [[(r[i][j]+2*F(i == j)-F(2, 3))/3 for j in range(9)]
          for i in range(9)]
    em = [[(F(i == j)-r[i][j]+F(1, 3))/3 for j in range(9)]
          for i in range(9)]
    for projector in (e1, em):
        assert multiply(projector, projector) == projector
        assert all(sum(row) == 0 for row in projector)
    assert multiply(e1, em) == [[0]*9 for _ in range(9)]
    block = [[27*F(i == j)+1-9*(r[i % 9][j % 9] if i//9 == j//9
                               else F(i % 9 == j % 9)) for j in range(18)]
             for i in range(18)]
    coupling = [[1-9*F(i % 9 == j) for j in range(9)] for i in range(18)]
    lift = [[e1[i % 9][j]+em[i % 9][j]/4 for j in range(9)] for i in range(18)]
    assert multiply(block, lift) == [[-x for x in row] for row in coupling]
    correction = multiply(transpose(coupling), lift)
    expected = [[-18*e1[i][j]-F(9, 2)*em[i][j] for j in range(9)] for i in range(9)]
    assert correction == expected
    empty = tip_matrix([])
    assert [[27*F(i == j)+1+correction[i][j] for j in range(9)] for i in range(9)] == [
        [F(9, 2)*x for x in row] for row in empty]
    assert [[3*F(i == j)+F(1, 9)-2*e1[i][j]-em[i][j]/2
             for j in range(9)] for i in range(9)] == [[F(x, 2) for x in row] for row in empty]
    core_certificate = congruence(block)
    verify_congruence(block, core_certificate)
    assert core_certificate['status'] == 'PSD' and core_certificate['rank'] == 16
    for edges, rank in (([], 9), ([list(e) for e in combinations(range(9), 2) if rook(*e)], 4)):
        certificate = congruence(tip_matrix(edges))
        verify_congruence(tip_matrix(edges), certificate)
        assert certificate['status'] == 'PSD' and certificate['rank'] == rank
    complete = [list(e) for e in combinations(range(9), 2)]
    negative = congruence(tip_matrix(complete))
    verify_congruence(tip_matrix(complete), negative)
    assert negative['status'] == 'not PSD'
    cut = edge_cut(negative['negative_vector'])
    assert sum(coefficient for _, _, coefficient in cut['terms']) > cut['rhs']
    return e1, em, {'core_gram_rank': 16, 'schur_identity': 'exact pass',
                    'spectral_projector_identity': 'exact pass',
                    'empty_tip_graph_rank': 9, 'rook_tip_graph_rank': 4,
                    'complete_tip_graph_negative_control': negative}


def make_record(input_path):
    e1, em, controls = fixed_controls()
    source = json.loads(input_path.read_text())
    points = []
    for index, point in enumerate(source['points']):
        edges = point['tip_edges']
        certificate = congruence(tip_matrix(edges))
        verify_congruence(tip_matrix(edges), certificate)
        row = {'point_index': index, 'tip_edges': edges, 'certificate': certificate}
        if certificate['status'] == 'not PSD':
            row['necessary_edge_cut'] = edge_cut(certificate['negative_vector'])
        points.append(row)
    return {'source_path': str(input_path),
            'source_sha256': hashlib.sha256(input_path.read_bytes()).hexdigest(),
            'matrix': '3I - R + J - 2Z', 'fixed_controls': controls, 'points': points}


def verify(record, input_path=None):
    e1, em, controls = fixed_controls()
    assert record['matrix'] == '3I - R + J - 2Z'
    assert record['fixed_controls'] == controls
    if input_path:
        assert hashlib.sha256(input_path.read_bytes()).hexdigest() == record['source_sha256']
        source = json.loads(input_path.read_text())
        assert [point['tip_edges'] for point in source['points']] == [point['tip_edges'] for point in record['points']]
    summary = []
    for point in record['points']:
        certificate = point['certificate']
        verify_congruence(tip_matrix(point['tip_edges']), certificate)
        if certificate['status'] == 'not PSD':
            assert point['necessary_edge_cut'] == edge_cut(certificate['negative_vector'])
        summary.append({'point_index': point['point_index'], 'status': certificate['status'],
                        'rank': certificate.get('rank'),
                        'integer_kernel_basis': certificate.get('integer_kernel_basis', [])})
    # The rank-eight saved point gives an independent integrality control.
    first = record['points'][0]['certificate']
    expected = [0, 1, 0, 1, 0, 1, 0, 1, 0]
    assert first['status'] == 'PSD' and first['rank'] == 8
    assert first['integer_kernel_basis'] == [expected]
    u = [sum((e1[i][j]+em[i][j]/4)*expected[j] for j in range(9)) for i in range(9)]
    assert u == [F(x, 18) for x in (-5, 4, -5, 4, 4, 4, -5, 4, -5)]
    assert F(sum(expected), 9)-u[0]-u[4] == F(1, 2)
    assert all([i, j] in record['points'][0]['tip_edges'] for i, j in combinations((1, 3, 5, 7), 2))
    return {'status': 'exact Schur and PSD certificate replay passed', 'points': summary,
            'negative_tip_vectors_from_saved_points': sum(p['status'] == 'not PSD' for p in summary),
            'first_point_kernel_extension_rhs_at_signature_0_4': [1, 2],
            'first_point_integrality_obstruction_already_contains_tip_K4': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--input', type=Path)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        assert args.input
        record = make_record(args.input)
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(verify(json.loads(args.certificate.read_text()), args.input), indent=2))
