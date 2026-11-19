"""Independently lift the complementary-rook real point to all labeled rows.

No optimizer or construction helper from the audited model is imported.
The 27-core, complete signature/edge domains, group orbits, and every
unaveraged constraint are reconstructed with integer arithmetic.
"""

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import combinations, permutations, product
import json
from math import lcm
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rook(p, q):
    return p != q and (p//3 == q//3 or p % 3 == q % 3)


def audit(certificate_path, output):
    certificate = json.loads(certificate_path.read_text())
    metadata = certificate['metadata']
    for name, expected in certificate['source_hashes'].items():
        assert sha(Path(__file__).with_name(name)) == expected
    B = [[0]*27 for _ in range(27)]
    for i, j in combinations(range(27), 2):
        a, p = divmod(i, 9)
        b, q = divmod(j, 9)
        value = int(p == q) if a != b else int(
            (p != q and not rook(p, q)) if a == 2 else rook(p, q))
        B[i][j] = B[j][i] = value
    assert all(sum(row) == 6 for row in B)
    G = [[12*int(i == j)+2-B[i][j]-sum(B[i][k]*B[k][j] for k in range(27))
          for j in range(27)] for i in range(27)]
    triples, signatures, needs = [], [], []
    for p, q, t in product(range(9), repeat=3):
        sites = (p, 9+q, 18+t)
        need = [2-sum(B[i][j]+int(i == j) for j in sites) for i in range(27)]
        if min(need) >= 0 and all(G[i][j] > 0 for i, j in combinations(sites, 2)):
            triples.append((p, q, t))
            signatures.append(sites)
            needs.append(need)
    assert len(signatures) == 252
    edges = [(v, w) for v, w in combinations(range(252), 2)
             if len(set(signatures[v]) & set(signatures[w])) <= 1
             and all(needs[v][i] > 0 for i in signatures[w])
             and all(needs[w][i] > 0 for i in signatures[v])]
    assert len(edges) == 20934
    signature_index = {triple: i for i, triple in enumerate(triples)}
    actions = set()
    for rp, cp, transposed, swapped in product(permutations(range(3)),
                                               permutations(range(3)), (0, 1), (0, 1)):
        points = [3*rp[p % 3]+cp[p//3] if transposed else
                  3*rp[p//3]+cp[p % 3] for p in range(9)]
        core = [9*(1-a if swapped and a < 2 else a)+points[p]
                for a in range(3) for p in range(9)]
        assert all(B[i][j] == B[core[i]][core[j]] and G[i][j] == G[core[i]][core[j]]
                   for i in range(27) for j in range(27))
        action = tuple(signature_index[(points[q], points[p], points[t]) if swapped else
                                       (points[p], points[q], points[t])]
                       for p, q, t in triples)
        assert sorted(action) == list(range(252))
        actions.add(action)
    assert len(actions) == 144
    # Orbit representatives are the least domain index, independently of
    # union-find choices or the order in which the group was generated.
    selector_min = [min(g[s] for g in actions) for s in range(252)]
    selector_reps = sorted(set(selector_min))
    selector_names = {r: i for i, r in enumerate(selector_reps)}
    selector_orbits = [selector_names[r] for r in selector_min]
    selector_sizes = [selector_orbits.count(i) for i in range(len(selector_reps))]
    assert selector_sizes == [72, 144, 36] == metadata['selector_orbit_sizes']
    assert [list(triples[s]) for s in selector_reps] == metadata['selector_representative_triples']
    edge_index = {edge: i for i, edge in enumerate(edges)}
    edge_min = list(range(len(edges)))
    for g in actions:
        image = [edge_index[tuple(sorted((g[v], g[w])))] for v, w in edges]
        assert sorted(image) == list(range(len(edges)))
        edge_min = [min(old, new) for old, new in zip(edge_min, image)]
    edge_reps = sorted(set(edge_min))
    edge_names = {r: i for i, r in enumerate(edge_reps)}
    edge_orbits = [edge_names[r] for r in edge_min]
    assert len(edge_reps) == 179 == metadata['edge_orbits']
    point = [Fraction(p, q) for p, q in certificate['result']['point']]
    assert len(point) == 182 and min(point) >= 0
    scale = lcm(*(value.denominator for value in point))
    values = [int(scale*value) for value in point]
    selectors = [values[selector_orbits[s]] for s in range(252)]
    chosen_edges = [values[3+edge_orbits[e]] for e in range(len(edges))]
    assert max(selectors) <= scale and sum(selectors) == 72*scale
    gram = [[0]*27 for _ in range(27)]
    for s, sites in enumerate(signatures):
        for i in sites:
            for j in sites:
                gram[i][j] += selectors[s]
    assert all(gram[i][j] == scale*G[i][j] for i in range(27) for j in range(27))
    mixed = [[0]*27 for _ in range(252)]
    degree = [0]*252
    packing = [Counter() for _ in range(252)]
    for (v, w), value in zip(edges, chosen_edges):
        assert value <= selectors[v] and value <= selectors[w]
        for a, b in ((v, w), (w, v)):
            degree[a] += value
            for i in signatures[b]:
                mixed[a][i] += value
            for pair in combinations(signatures[b], 2):
                packing[a][pair] += value
    assert all(degree[v] == 11*selectors[v] for v in range(252))
    assert all(mixed[v][i] == needs[v][i]*selectors[v]
               for v in range(252) for i in range(27))
    assert all(packing[v][i, j] <= selectors[v]
               for v in range(252) for i, j in combinations(range(27), 2))
    counted = [s for s, (p, q, t) in enumerate(triples) if rook(p, t) and rook(q, t)]
    assert len(counted) == 72 and {selector_orbits[s] for s in counted} == {0}
    objective = sum(selectors[s] for s in counted)
    assert objective == 36*scale
    # Full Gram margins force 4 first-grid-near and 4 second-grid-near
    # selections at each tip. With 8 total, near-near equals far-far and
    # hence contributes at most 4. This proves the upper bound 36 directly.
    for t in range(9):
        families = Counter()
        for s, (p, q, tip) in enumerate(triples):
            if tip == t:
                families[int(rook(p, t)), int(rook(q, t))] += selectors[s]
        assert sum(families.values()) == 8*scale
        assert families[1, 1] == families[0, 0]
        assert families[1, 0]+families[1, 1] == 4*scale
        assert families[0, 1]+families[1, 1] == 4*scale
    result = {
        'status': 'independent full labeled real-constraint and group audit PASS',
        'source_sha256': sha(Path(__file__)),
        'audited_source_hashes': certificate['source_hashes'],
        'certificate_path': str(certificate_path), 'certificate_sha256': sha(certificate_path),
        'complete_signatures': 252, 'complete_eligible_edges': 20934,
        'group_order': 144, 'selector_orbit_sizes': selector_sizes, 'edge_orbits': 179,
        'lifted_population': 72, 'gram_entries_checked': 729,
        'activation_inequalities_checked': 41868, 'mixed_equations_checked': 6804,
        'degree_equations_checked': 252, 'core_pair_packing_inequalities_checked': 88452,
        'exact_point_scale': scale, 'point_objective': 36, 'analytic_upper_bound': 36,
        'averaging_argument': 'the full real system and objective are invariant under144 core relabelings; averaging any graph point preserves every equality and inequality',
        'scope': 'the stated real relaxation has optimum36; this is not a binary graph or incidence completion',
    }
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.certificate, args.output)
