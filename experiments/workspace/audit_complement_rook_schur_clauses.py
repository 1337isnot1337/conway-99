"""Verify the exported Schur triangle clauses from direct integer witnesses.

No Schur-census helper, inverse, or eigenvalue calculation is imported.
The nine explicit30-vertex quadratic witnesses and their144 relabelings
suffice to certify every exported forbidden triangle clause.
"""

import argparse
import hashlib
from itertools import combinations, permutations, product
import json
from pathlib import Path


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rook(a, b):
    return a != b and (a//3 == b//3 or a % 3 == b % 3)


def audit(path):
    saved = json.loads(path.read_text())
    core = [[0]*27 for _ in range(27)]
    for i, j in combinations(range(27), 2):
        bi, pi = divmod(i, 9)
        bj, pj = divmod(j, 9)
        adjacent = (rook(pi, pj) if bi < 2 else not rook(pi, pj)) if bi == bj else pi == pj
        core[i][j] = core[j][i] = int(adjacent)
    rows = [sum(bit << j for j, bit in enumerate(row)) for row in core]
    gram = [[12*(i == j)+2-core[i][j]-sum(core[i][k]*core[k][j] for k in range(27))
             for j in range(27)] for i in range(27)]
    triples = [(p, q, t) for p, q, t in product(range(9), repeat=3)
               if p != q and not rook(p, q) and t not in (p, q)]
    assert len(triples) == 252
    position = {s: i for i, s in enumerate(triples)}
    signatures = [[p, 9+q, 18+t] for p, q, t in triples]
    needs = [[2-int(i in sites)-sum(core[i][j] for j in sites) for i in range(27)]+[11]
             for sites in signatures]
    edges = [(a, b) for a, b in combinations(range(252), 2)
             if len(set(signatures[a]) & set(signatures[b])) <= 1
             and all(needs[a][i] > 0 for i in signatures[b])
             and all(needs[b][i] > 0 for i in signatures[a])]
    assert len(edges) == 20934
    variables = {edge: i+253 for i, edge in enumerate(edges)}
    domain = {'core_rows': rows, 'gram': gram, 'signatures': signatures, 'mixed_need': needs,
              'edge_variables': [[a, b, variables[a, b]] for a, b in edges]}
    domain_sha = hashlib.sha256(json.dumps(domain, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert domain_sha == saved['base_domain_sha256']
    actions = []
    for rp, cp, transpose, swap in product(permutations(range(3)), permutations(range(3)), (0, 1), (0, 1)):
        point = []
        for p in range(9):
            r, c = divmod(p, 3)
            if transpose:
                r, c = c, r
            point.append(3*rp[r]+cp[c])
        core_image = [9*(1-b if swap and b < 2 else b)+point[p]
                      for b in range(3) for p in range(9)]
        assert sorted(core_image) == list(range(27))
        assert all(core[i][j] == core[core_image[i]][core_image[j]]
                   for i, j in combinations(range(27), 2))
        image = [position[(point[q], point[p], point[t]) if swap else (point[p], point[q], point[t])]
                 for p, q, t in triples]
        assert all(sorted(core_image[i] for i in signatures[s]) == signatures[image[s]]
                   for s in range(252))
        actions.append(image)
    assert len({tuple(p) for p in actions}) == 144
    forbidden = set()
    checks = []
    for witness in saved['forbidden_triangle_orbits']:
        indices = witness['representative']
        assert witness['coordinate_triples'] == [list(triples[i]) for i in indices]
        adjacency = [row+[0]*3 for row in core]+[[0]*30 for _ in range(3)]
        for t, index in enumerate(indices, 27):
            for i in signatures[index]:
                adjacency[t][i] = adjacency[i][t] = 1
        for i, j in combinations(range(27, 30), 2):
            adjacency[i][j] = adjacency[j][i] = 1
        vector = witness['full_30_vertex_integer_vector']
        assert len(vector) == 30 and all(type(v) is int for v in vector)
        value = sum(vector[i]*(27*(i == j)-9*adjacency[i][j]+1)*vector[j]
                    for i in range(30) for j in range(30))
        assert value == witness['full_projector_quadratic'] < 0
        assert all(sum(adjacency[i][k]*adjacency[j][k] for k in range(30))+adjacency[i][j] <= 2
                   for i, j in combinations(range(30), 2))
        orbit = {tuple(sorted(image[i] for i in indices)) for image in actions}
        assert len(orbit) == witness['orbit_size'] == 144
        assert not orbit & forbidden
        assert all(tuple(pair) in variables for member in orbit for pair in combinations(member, 2))
        forbidden.update(orbit)
        checks.append({'representative': indices, 'integer_quadratic': value, 'orbit_size': len(orbit)})
    assert len(checks) == 9 and len(forbidden) == 1296
    assert [list(t) for t in sorted(forbidden)] == saved['forbidden_triangles']
    clauses = [[-variables[a, b], -variables[a, c], -variables[b, c]] for a, b, c in sorted(forbidden)]
    assert clauses == saved['forbidden_triangle_clauses_in_base_variable_order']
    return {'status': 'independent integer-witness and clause-orbit audit PASS',
            'source_sha256': digest(Path(__file__)), 'certificate_sha256': digest(path),
            'base_domain_sha256': domain_sha, 'representatives': checks,
            'verified_negative_integer_witnesses': 9, 'verified_three_literal_clauses': 1296,
            'solver_called': False, 'Schur_inverse_used': False,
            'scope': 'Validity of the1296 exported clauses; no whole-core exclusion.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = audit(args.certificate)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
