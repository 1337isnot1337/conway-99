"""Exact spectral certificates for the complete four/five-base censuses.

Floating eigenvectors propose negative integer rays during generation.
Replay uses only integer quadratic forms, explicit isomorphisms, and exact
characteristic polynomials. It does not call an optimizer or eigensolver.
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path

import sympy as sp


ROOT = Path(__file__).resolve().parents[2]


def catalogue(bases):
    return json.loads((ROOT/'experiments/logs/grids-and-triangles'/
                       f'seven-red-interfaces-b{bases}-backtrack.json').read_text())


def catalogue_digest(data):
    payload = {key: data[key] for key in ('allowed_maps', 'edge_order', 'assignments')}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def adjacency(data, labels):
    n, bases = 9*data['bases'], data['bases']
    rows = [0]*n
    for i in range(bases):
        for x, y in combinations(range(9), 2):
            if x//3 == y//3 or x%3 == y%3:
                rows[9*i+x] |= 1 << (9*i+y)
                rows[9*i+y] |= 1 << (9*i+x)
    for j in range(1, bases):
        for x in range(9):
            rows[x] |= 1 << (9*j+x)
            rows[9*j+x] |= 1 << x
    for (i, j), label in zip(data['edge_order'], labels):
        for x, y in enumerate(data['allowed_maps'][label]):
            rows[9*i+x] |= 1 << (9*j+y)
            rows[9*j+y] |= 1 << (9*i+x)
    assert all(row.bit_count() == bases+3 for row in rows)
    assert all((rows[i] & rows[j]).bit_count()+(rows[i] >> j & 1) <= 2
               for i, j in combinations(range(n), 2))
    return rows


def gram(rows):
    return [[12*int(i == j)+2-(rows[i] >> j & 1)-(rows[i] & rows[j]).bit_count()
             for j in range(len(rows))] for i in range(len(rows))]


def quadratic(matrix, vector):
    return sum(vector[i]*matrix[i][j]*vector[j]
               for i in range(len(vector)) for j in range(len(vector)))


def graph(rows):
    import networkx as nx
    result = nx.Graph()
    result.add_nodes_from(range(len(rows)))
    result.add_edges_from((i, j) for i, j in combinations(range(len(rows)), 2)
                          if rows[i] >> j & 1)
    return result


def spectrum(rows):
    x = sp.Symbol('x')
    B = sp.Matrix([[row >> j & 1 for j in range(len(rows))] for row in rows])
    polynomial = B.charpoly(x).as_poly()
    degree = rows[0].bit_count()
    residual = polynomial.exquo(sp.Poly(x-degree, x))
    factors = [(sp.Poly(f, x), int(m)) for f, m in sp.factor_list(residual)[1]]
    for factor, _ in factors:
        if factor.degree() == 1:
            root = -factor.TC()/factor.LC()
            assert -4 <= root <= 3
        else:
            assert factor.eval(-4) != 0 and factor.eval(3) != 0
            assert factor.count_roots(-sp.oo, -4) == 0
            assert factor.count_roots(3, sp.oo) == 0
    return {'constant_eigenvalue': degree,
            'remaining_factors': [{'coefficients': list(map(int, f.all_coeffs())), 'multiplicity': m}
                                  for f, m in factors],
            'gram_constant_eigenvalue': 12+2*len(rows)-degree-degree*degree}


def boundary_rows(bases):
    if bases == 4:
        from four_red_boundary import core
        return core()
    from petersen_red_core_boundary import construct
    B = construct()[3]
    return [sum(1 << j for j, entry in enumerate(row) if entry) for row in B]


def generate():
    import networkx as nx
    import numpy as np
    result = {'scope': 'complete local interface censuses, not graph constructions', 'censuses': []}
    for bases in (4, 5):
        data = catalogue(bases)
        records, positive = [], []
        for case, labels in enumerate(data['assignments']):
            rows = adjacency(data, labels)
            G = gram(rows)
            values, vectors = np.linalg.eigh(np.array(G, dtype=float))
            if values[0] < -1e-7:
                found = None
                for scale in (10, 100, 1000, 10000):
                    vector = list(map(int, np.rint(scale*vectors[:, 0])))
                    value = quadratic(G, vector)
                    if value < 0:
                        found = {'case': case, 'kind': 'negative_gram', 'vector': vector, 'value': value}
                        break
                assert found is not None
                records.append(found)
                continue
            candidate = graph(rows)
            for index, item in enumerate(positive):
                matcher = nx.algorithms.isomorphism.GraphMatcher(candidate, item['graph'])
                if matcher.is_isomorphic():
                    mapping = [int(matcher.mapping[i]) for i in range(len(rows))]
                    break
            else:
                index = len(positive)
                positive.append({'case': case, 'rows': rows, 'graph': candidate, 'spectrum': spectrum(rows)})
                mapping = list(range(len(rows)))
            records.append({'case': case, 'kind': 'surviving_isomorphism', 'representative': index, 'mapping': mapping})
        for item in positive:
            matcher = nx.algorithms.isomorphism.GraphMatcher(item['graph'], graph(boundary_rows(bases)))
            assert matcher.is_isomorphic()
            item['boundary_model_mapping'] = [int(matcher.mapping[i]) for i in range(9*bases)]
        result['censuses'].append({'bases': bases, 'catalogue_digest': catalogue_digest(data),
                                  'cases': records,
                                  'surviving_representatives': [{k: v for k, v in item.items() if k != 'graph'}
                                                               for item in positive]})
    return result


def verify(result):
    summaries = []
    assert [row['bases'] for row in result['censuses']] == [4, 5]
    for census in result['censuses']:
        data = catalogue(census['bases'])
        assert catalogue_digest(data) == census['catalogue_digest']
        assert len(census['cases']) == len(data['assignments'])
        representatives = census['surviving_representatives']
        assert len(representatives) == 1
        for item in representatives:
            rows = adjacency(data, data['assignments'][item['case']])
            assert rows == item['rows'] and spectrum(rows) == item['spectrum']
            assert item['spectrum']['gram_constant_eigenvalue'] > 0
            target = boundary_rows(census['bases'])
            mapping = item['boundary_model_mapping']
            assert sorted(mapping) == list(range(len(rows)))
            assert all((rows[i] >> j & 1) == (target[mapping[i]] >> mapping[j] & 1)
                       for i, j in combinations(range(len(rows)), 2))
        counts = Counter()
        for case, record in enumerate(census['cases']):
            assert case == record['case']
            rows = adjacency(data, data['assignments'][case])
            if record['kind'] == 'negative_gram':
                vector = record['vector']
                assert len(vector) == len(rows) and all(type(v) is int for v in vector)
                value = quadratic(gram(rows), vector)
                assert value == record['value'] < 0
            else:
                assert record['kind'] == 'surviving_isomorphism'
                target = representatives[record['representative']]['rows']
                mapping = record['mapping']
                assert sorted(mapping) == list(range(len(rows)))
                assert all((rows[i] >> j & 1) == (target[mapping[i]] >> mapping[j] & 1)
                           for i, j in combinations(range(len(rows)), 2))
            counts[record['kind']] += 1
        assert counts['surviving_isomorphism'] == 12
        summaries.append({'bases': census['bases'], 'assignments': len(census['cases']),
                          'exact_negative_gram_vectors': counts['negative_gram'],
                          'exact_surviving_isomorphisms': counts['surviving_isomorphism'],
                          'surviving_graph_classes': len(representatives),
                          'surviving_spectrum': representatives[0]['spectrum']})
    return {'censuses': summaries, 'status': 'all exact certificates verified'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate', type=Path)
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.generate:
        result = generate()
        args.generate.write_text(json.dumps(result, indent=2)+'\n')
    else:
        assert args.verify
        result = json.loads(args.verify.read_text())
    summary = verify(result)
    if args.output:
        args.output.write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary), flush=True)
