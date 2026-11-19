"""Exact small projector-Schur census for the complementary-rook core.

Only the standard library is used. The core, 252 signatures, eligible
edges, and 144 relabelings are reconstructed independently. Exact
positive LDL factorizations and scaled inverse identities validate both
core blocks. No solver, floating-point calculation, or large CNF is used.
"""

import argparse
from collections import Counter
from fractions import Fraction
from functools import reduce
import hashlib
from itertools import combinations, permutations, product
import json
from math import gcd, lcm
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ratio(value):
    value = Fraction(value)
    return [value.numerator, value.denominator]


def rook(i, j):
    return i != j and (i//3 == j//3 or i % 3 == j % 3)


def exact_inverse(matrix):
    n = len(matrix)
    work = [[Fraction(x) for x in row]+[Fraction(i == j) for j in range(n)]
            for i, row in enumerate(matrix)]
    for i in range(n):
        pivot = work[i][i]
        assert pivot > 0  # Every leading principal submatrix is positive.
        work[i] = [value/pivot for value in work[i]]
        for j in range(n):
            if i != j and work[j][i]:
                coefficient = work[j][i]
                work[j] = [a-coefficient*b for a, b in zip(work[j], work[i])]
    assert all(work[i][j] == (i == j) for i in range(n) for j in range(n))
    inverse = [row[n:] for row in work]
    scale = lcm(*(value.denominator for row in inverse for value in row))
    scaled = [[int(scale*value) for value in row] for row in inverse]
    assert all(sum(scaled[i][k]*matrix[k][j] for k in range(n)) == scale*(i == j)
               for i in range(n) for j in range(n))
    return scale, scaled


def positive_ldl(matrix):
    n = len(matrix)
    lower = [[Fraction(i == j) for j in range(n)] for i in range(n)]
    diagonal = []
    for i in range(n):
        diagonal.append(Fraction(matrix[i][i])-sum(lower[i][k]**2*diagonal[k] for k in range(i)))
        assert diagonal[i] > 0
        for j in range(i+1, n):
            lower[j][i] = (matrix[j][i]-sum(lower[j][k]*lower[i][k]*diagonal[k]
                                          for k in range(i)))/diagonal[i]
    assert all(sum(lower[i][k]*diagonal[k]*lower[j][k] for k in range(n)) == matrix[i][j]
               for i in range(n) for j in range(n))
    return [ratio(value) for value in diagonal]


def domain():
    rows = [0]*27
    for i, j in combinations(range(27), 2):
        if i//9 == j//9:
            adjacent = rook(i % 9, j % 9) if i//9 < 2 else not rook(i % 9, j % 9)
        else:
            adjacent = i % 9 == j % 9
        if adjacent:
            rows[i] |= 1 << j
            rows[j] |= 1 << i
    assert all(row.bit_count() == 6 for row in rows)
    gram = [[12*(i == j)+2-((rows[i] >> j) & 1)-(rows[i] & rows[j]).bit_count()
             for j in range(27)] for i in range(27)]
    triples = list(product(range(9), repeat=3))
    signatures = [tuple(9*b+p for b, p in enumerate(triple)) for triple in triples]
    signatures = [sites for sites in signatures if all(gram[i][j] > 0 for i, j in combinations(sites, 2))]
    triples = [tuple(i % 9 for i in sites) for sites in signatures]
    assert len(signatures) == 252
    assert triples == [(p, q, t) for p, q, t in product(range(9), repeat=3)
                       if p != q and not rook(p, q) and t not in (p, q)]
    masks = [sum(1 << i for i in sites) for sites in signatures]
    needs = [[2-(rows[i] & mask).bit_count()-int(mask >> i & 1)
              for i in range(27)]+[11] for mask in masks]
    assert min(value for row in needs for value in row) >= 0
    edges = [(a, b) for a, b in combinations(range(252), 2)
             if (masks[a] & masks[b]).bit_count() <= 1
             and all(needs[a][i] >= 1 for i in signatures[b])
             and all(needs[b][i] >= 1 for i in signatures[a])]
    assert len(edges) == 20934
    record = {'core_rows': rows, 'gram': gram, 'signatures': signatures, 'mixed_need': needs,
              'edge_variables': [[a, b, 253+i] for i, (a, b) in enumerate(edges)]}
    domain_hash = hashlib.sha256(json.dumps(record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    return rows, gram, triples, signatures, masks, edges, domain_hash


def actions(rows, triples):
    position = {triple: i for i, triple in enumerate(triples)}
    group = []
    for row, column, transpose, swap in product(permutations(range(3)), permutations(range(3)), (0, 1), (0, 1)):
        point = [3*row[p % 3]+column[p//3] if transpose else 3*row[p//3]+column[p % 3]
                 for p in range(9)]
        core = [9*(1-b if swap and b < 2 else b)+point[p] for b in range(3) for p in range(9)]
        assert sorted(core) == list(range(27))
        assert all(((rows[i] >> j) & 1) == ((rows[core[i]] >> core[j]) & 1)
                   for i in range(27) for j in range(27))
        action = [position[(point[q], point[p], point[t]) if swap else
                           (point[p], point[q], point[t])] for p, q, t in triples]
        assert sorted(action) == list(range(252))
        group.append(action)
    assert len({tuple(action) for action in group}) == 144
    return sorted(group)


def projector(kind, rows, signatures):
    negative = kind == 'minus'
    diagonal_coefficient, adjacency_coefficient, constant = (27, -9, 1) if negative else (44, 11, -2)
    full = [[diagonal_coefficient*(i == j)+adjacency_coefficient*((rows[i] >> j) & 1)+constant
             for j in range(27)] for i in range(27)]
    keep = [i for i in range(27) if not negative or i % 9 != 8]
    matrix = [[full[i][j] for j in keep] for i in keep]
    pivots = positive_ldl(matrix)
    inverse_scale, inverse = exact_inverse(matrix)
    full_vectors = [[adjacency_coefficient*int(i in sites)+constant for i in range(27)] for sites in signatures]
    if negative:
        assert len(keep) == 24
        assert all(sum(full[i][j] for j in range(9*b, 9*b+9)) == 0
                   for i in range(27) for b in range(3))
        assert all(sum(v[9*b:9*b+9]) == 0 for v in full_vectors for b in range(3))
        # Reconstruction F K F^T proves exactly the three stated kernels.
        expansion = [[int(i == j) if i % 9 != 8 else -int(i//9 == j//9) for j in keep]
                     for i in range(27)]
        assert all(sum(expansion[i][a]*matrix[a][b]*expansion[j][b]
                       for a in range(24) for b in range(24)) == full[i][j]
                   for i in range(27) for j in range(27))
        assert all(sum(expansion[i][a]*v[keep[a]] for a in range(24)) == v[i]
                   for v in full_vectors for i in range(27))
    vectors = [[v[i] for i in keep] for v in full_vectors]
    inverse_vectors = [[sum(x*y for x, y in zip(row, v)) for row in inverse] for v in vectors]
    products = [[sum(x*y for x, y in zip(v, w)) for w in inverse_vectors] for v in vectors]
    assert all(products[a][b] == products[b][a] for a in range(252) for b in range(252))
    diag = [(diagonal_coefficient+constant)*inverse_scale-products[a][a] for a in range(252)]
    off = [[[inverse_scale*(constant+adjacency_coefficient*edge)-products[a][b] for b in range(252)]
            for a in range(252)] for edge in (0, 1)]
    common = reduce(gcd, [inverse_scale]+diag+[value for states in off for row in states for value in row])
    scale = inverse_scale//common
    diag = [value//common for value in diag]
    off = [[[value//common for value in row] for row in states] for states in off]
    assert all(value > 0 for value in diag)
    saved = {'core_rank': len(keep), 'retained_core_coordinates': keep, 'positive_ldl_diagonal': pivots,
             'inverse_scale': inverse_scale, 'scaled_inverse': inverse, 'residual_scale': scale,
             'kernel_dimension': 3 if negative else 0,
             'kernel_compatible_signatures_checked': 252,
             'single_vertex_residuals': [[ratio(Fraction(value, scale)), count]
                                       for value, count in sorted(Counter(diag).items())]}
    return {'saved': saved, 'diag': diag, 'off': off, 'scale': scale,
            'keep': keep, 'inverse': inverse, 'inverse_scale': inverse_scale, 'vectors': vectors}


def determinant3(a, b, c, x, y, z):
    return a*b*c+2*x*y*z-a*z*z-b*y*y-c*x*x


def source_type(triple):
    p, q, t = triple
    return 2-int(rook(p, t))-int(rook(q, t))


def three_point_patterns(indices, triples):
    names = ['independent', 'one_edge', 'path', 'triangle']
    answer = []
    for base in range(3):
        points = [triples[a][base] for a in indices]
        fixed = [[i, j] for i, j in combinations(range(3), 2) if rook(points[i], points[j])]
        actual = fixed if base < 2 else [[i, j] for i, j in combinations(range(3), 2)
                                       if not rook(points[i], points[j])]
        answer.append({'base': ['R', 'S', 'T'][base], 'points': points,
                       'fixed_R_edges_by_selected_vertex_index': fixed,
                       'actual_core_edges_by_selected_vertex_index': actual,
                       'fixed_R_pattern': names[len(fixed)], 'actual_core_pattern': names[len(actual)]})
    return answer


def primitive(vector):
    divisor = reduce(gcd, vector)
    assert divisor
    return [value//divisor for value in vector]


def negative_witness(indices, data, rows, signatures):
    diagonal, off, scale = data['diag'], data['off'][1], data['scale']
    matrix = [[diagonal[a] if i == j else off[a][b] for j, b in enumerate(indices)]
              for i, a in enumerate(indices)]
    vector = [1, 1, 1]
    row_sums = [sum(row) for row in matrix]
    if sum(row_sums) == 0:
        i = next(i for i, value in enumerate(row_sums) if value)
        multiple = matrix[i][i]//(2*abs(row_sums[i]))+1
        vector = [multiple]*3
        vector[i] += -1 if row_sums[i] > 0 else 1
    if sum(vector[i]*matrix[i][j]*vector[j] for i in range(3) for j in range(3)) >= 0:
        a, x, y = matrix[0]
        _, b, z = matrix[1]
        minor = a*b-x*x
        assert minor > 0
        vector = [x*z-b*y, x*y-a*z, minor]
    vector = primitive(vector)
    quadratic = sum(vector[i]*matrix[i][j]*vector[j] for i in range(3) for j in range(3))
    assert quadratic < 0
    combined = [sum(vector[i]*data['vectors'][a][j] for i, a in enumerate(indices))
                for j in range(len(data['keep']))]
    core = [-sum(x*y for x, y in zip(row, combined)) for row in data['inverse']]
    full_vector = [0]*30
    for i, value in zip(data['keep'], core):
        full_vector[i] = value
    full_vector[27:] = [data['inverse_scale']*value for value in vector]
    full_vector = primitive(full_vector)
    edges = [(i, j) for i, j in combinations(range(27), 2) if rows[i] >> j & 1]
    edges += [(i, 27+b) for b, a in enumerate(indices) for i in signatures[a]]
    edges += [(27, 28), (27, 29), (28, 29)]
    direct = (27*sum(value*value for value in full_vector)
              -18*sum(full_vector[a]*full_vector[b] for a, b in edges)+sum(full_vector)**2)
    assert direct < 0
    # Also compare to the Schur quadratic after the common rescaling.
    factor = Fraction(full_vector[27], vector[0])
    assert all(full_vector[27+i] == factor*vector[i] for i in range(3))
    assert direct == factor*factor*Fraction(quadratic, scale)
    return {'scaled_residual_matrix': matrix, 'residual_scale': scale,
            'all_ones_residual_quadratic': ratio(Fraction(sum(row_sums), scale)),
            'negative_residual_vector': vector, 'residual_quadratic': ratio(Fraction(quadratic, scale)),
            'full_30_vertex_integer_vector': full_vector, 'full_projector_quadratic': direct}


def census():
    base_path = ROOT/'experiments/logs/grids-and-triangles/two-rook-tip-boundary-joint-3943553752-model.json'
    triangle_path = ROOT/'experiments/logs/grids-and-triangles/complement-rook-triangle-domains.json'
    base = json.loads(base_path.read_text())
    triangle_record = json.loads(triangle_path.read_text())
    rows, gram, triples, signatures, masks, edges, domain_hash = domain()
    assert domain_hash == base['domain_sha256'] == triangle_record['base_domain_sha256']
    group = actions(rows, triples)
    projectors = {kind: projector(kind, rows, signatures) for kind in ('minus', 'plus')}
    edge_set = set(edges)
    edge_variables = {edge: i+253 for i, edge in enumerate(edges)}
    pair_orbits = []
    seen = set()
    pair_summary = Counter()
    pair_minimum = {kind: [None, None] for kind in projectors}
    for a, b in combinations(range(252), 2):
        if (a, b) in seen:
            continue
        members = {tuple(sorted((image[a], image[b]))) for image in group}
        assert not seen.intersection(members)
        seen.update(members)
        shared = [i for i in signatures[a] if i in signatures[b]]
        coexist = all(gram[i][j] >= 2 for i, j in combinations(shared, 2))
        eligible = (a, b) in edge_set
        determinants = {}
        for kind, data in projectors.items():
            values = []
            for edge in (0, 1):
                det = data['diag'][a]*data['diag'][b]-data['off'][edge][a][b]**2
                assert det > 0
                value = Fraction(det, data['scale']**2)
                pair_minimum[kind][edge] = value if pair_minimum[kind][edge] is None else min(value, pair_minimum[kind][edge])
                values.append(ratio(value))
            determinants[kind] = values
        pair_summary[coexist, eligible] += len(members)
        pair_orbits.append({'representative': [a, b], 'size': len(members),
                            'compatible_with_incidence_quotas': coexist,
                            'eligible_edge': eligible, 'determinants_for_edge_0_and_1': determinants})
    assert len(seen) == 31626
    adjacency = [0]*252
    for a, b in edges:
        if not masks[a] & masks[b]:
            adjacency[a] |= 1 << b
            adjacency[b] |= 1 << a
    triangles = []
    domain_digest = hashlib.sha256()
    for a, b in edges:
        if masks[a] & masks[b]:
            continue
        common = adjacency[a] & adjacency[b] & ~((1 << (b+1))-1)
        while common:
            bit = common & -common
            common -= bit
            c = bit.bit_length()-1
            triangles.append((a, b, c))
            domain_digest.update(f'{a},{b},{c}\n'.encode())
    assert len(triangles) == 209952
    assert domain_digest.hexdigest() == triangle_record['allowed_triangle_domain_sha256']
    all_triangles = set(triangles)
    before_sources = Counter(a for triangle in triangles for a in triangle)
    before_edges = Counter(pair for triangle in triangles for pair in combinations(triangle, 2))
    seen = set()
    triangle_orbits = []
    counts = {kind: Counter() for kind in projectors}
    triangle_minimum = {kind: None for kind in projectors}
    forbidden = []
    witnesses = []
    for a, b, c in triangles:
        if (a, b, c) in seen:
            continue
        members = {tuple(sorted((image[a], image[b], image[c]))) for image in group}
        assert members <= all_triangles and not seen.intersection(members)
        seen.update(members)
        determinants = {}
        for kind, data in projectors.items():
            d, o = data['diag'], data['off'][1]
            det = determinant3(d[a], d[b], d[c], o[a][b], o[a][c], o[b][c])
            status = 'positive' if det > 0 else 'negative' if det < 0 else 'zero'
            counts[kind][status] += len(members)
            value = Fraction(det, data['scale']**3)
            triangle_minimum[kind] = value if triangle_minimum[kind] is None else min(value, triangle_minimum[kind])
            determinants[kind] = ratio(value)
            if det < 0:
                assert kind == 'minus'
                forbidden.extend(members)
                witness = negative_witness((a, b, c), data, rows, signatures)
                witnesses.append({'representative': [a, b, c], 'coordinate_triples': [triples[v] for v in (a, b, c)],
                                  'source_types': [source_type(triples[v]) for v in (a, b, c)],
                                  'source_type_multiset': sorted(source_type(triples[v]) for v in (a, b, c)),
                                  'selected_three_point_patterns': three_point_patterns((a, b, c), triples),
                                  'orbit_size': len(members), 'determinant': ratio(value), **witness})
        triangle_orbits.append({'representative': [a, b, c], 'size': len(members), 'determinants': determinants})
    assert seen == all_triangles
    forbidden.sort()
    assert len(forbidden) == len(set(forbidden)) == 1296
    assert len(witnesses) == 9 and all(item['orbit_size'] == 144 for item in witnesses)
    clauses = [[-edge_variables[a, b], -edge_variables[a, c], -edge_variables[b, c]] for a, b, c in forbidden]
    assert len({tuple(clause) for clause in clauses}) == 1296
    removed_sources = Counter(a for triangle in forbidden for a in triangle)
    removed_edges = Counter(pair for triangle in forbidden for pair in combinations(triangle, 2))
    source_support = []
    for kind in range(3):
        members = [a for a, triple in enumerate(triples) if source_type(triple) == kind]
        histogram = Counter((before_sources[a], removed_sources[a], before_sources[a]-removed_sources[a]) for a in members)
        assert len(histogram) == 1
        source_support.append({'type': kind, 'name': ['both_R_near', 'one_R_near', 'both_R_far'][kind],
                               'signatures': len(members), 'representative_index': members[0],
                               'coordinate_triple': triples[members[0]],
                               'triangle_supports': [{'before': before, 'removed': removed, 'after': after, 'signatures': count}
                                                    for (before, removed, after), count in sorted(histogram.items())]})
    assert all(before_sources[a] > removed_sources[a] for a in range(252))
    assert all(before_edges[pair] > removed_edges[pair] for pair in before_edges)
    edge_support = Counter((before, removed_edges[pair], before-removed_edges[pair]) for pair, before in before_edges.items())
    # These local thirty-vertex graphs obey the already visible pair caps.
    for witness in witnesses:
        extended = rows+[0]*3
        for j, index in enumerate(witness['representative']):
            for i in signatures[index]:
                extended[i] |= 1 << (27+j)
                extended[27+j] |= 1 << i
        for i, j in combinations(range(27, 30), 2):
            extended[i] |= 1 << j
            extended[j] |= 1 << i
        assert all((extended[i] & extended[j]).bit_count()+int(extended[i] >> j & 1) <= 2
                   for i, j in combinations(range(30), 2))
    return {'status': 'exact pair and disjoint-triangle projector census PASS',
            'scope': '1296 necessary triangle exclusions; no whole-core or graph-existence conclusion',
            'source_sha256': digest(Path(__file__)), 'base_manifest_sha256': digest(base_path),
            'triangle_domain_certificate_sha256': digest(triangle_path), 'base_domain_sha256': domain_hash,
            'normalizations': {'minus': '27I-9A+J=63E_minus4', 'plus': '44I+11A-2J=77E_3'},
            'projector_core_certificates': {kind: data['saved'] for kind, data in projectors.items()},
            'group_order': 144, 'candidate_signatures': 252, 'eligible_edges': len(edges),
            'pairs_checked': 31626, 'pair_orbits': pair_orbits,
            'pair_class_counts': [{'incidence_compatible': key[0], 'eligible_edge': key[1], 'count': count}
                                  for key, count in sorted(pair_summary.items())],
            'all_pair_edge_states_strictly_positive': True,
            'minimum_pair_determinants_for_edge_0_and_1': {kind: [ratio(value) for value in values]
                                                         for kind, values in pair_minimum.items()},
            'allowed_triangle_domain_sha256': domain_digest.hexdigest(),
            'allowed_disjoint_triangles': len(triangles), 'triangle_orbits': triangle_orbits,
            'triangle_status_counts': {kind: dict(counts[kind]) for kind in projectors},
            'minimum_triangle_determinants': {kind: ratio(value) for kind, value in triangle_minimum.items()},
            'forbidden_triangle_orbits': witnesses, 'forbidden_triangles': forbidden,
            'source_type_definitions': ['both p,t and q,t are R-adjacent', 'exactly one is R-adjacent', 'neither is R-adjacent'],
            'triangle_support_by_source_type': source_support,
            'triangle_support_by_eligible_disjoint_edge': [{'before': before, 'removed': removed, 'after': after, 'edges': count}
                                                          for (before, removed, after), count in sorted(edge_support.items())],
            'any_source_or_eligible_disjoint_edge_loses_all_triangle_support': False,
            'forbidden_triangle_clauses_in_base_variable_order': clauses,
            'forbidden_triangle_list_sha256': hashlib.sha256(''.join(f'{a},{b},{c}\n' for a, b, c in forbidden).encode()).hexdigest(),
            'local_cap_controls': {'representatives': 9, 'pairs_per_representative': 435, 'all_passed': True},
            'all_arithmetic_exact': True, 'solver_called': False, 'large_cnf_built': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = census()
    if args.write:
        args.certificate.write_text(json.dumps(result, indent=2)+'\n')
    else:
        assert json.loads(args.certificate.read_text()) == json.loads(json.dumps(result))
    summary = {key: value for key, value in result.items() if key not in
               ('projector_core_certificates', 'pair_orbits', 'triangle_orbits',
                'forbidden_triangle_orbits', 'forbidden_triangles', 'forbidden_triangle_clauses_in_base_variable_order')}
    summary['pair_orbit_count'] = len(result['pair_orbits'])
    summary['triangle_orbit_count'] = len(result['triangle_orbits'])
    summary['forbidden_triangle_orbit_count'] = len(result['forbidden_triangle_orbits'])
    summary['forbidden_triangles'] = len(result['forbidden_triangles'])
    print(json.dumps(summary, indent=2), flush=True)
