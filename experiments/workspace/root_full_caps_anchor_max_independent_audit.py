"""Independent small audit of maximum-anchor coverage and its exact clauses.

This imports no rooted-model or matching-coverage construction helper.
It uses standard-library arithmetic and reads the frozen certificate.
No CNF is built and no solver is called.
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations, product
import json
from math import comb, prod
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def odd_factorial(n):
    return prod(range(1, n+1, 2))


def run():
    source = ROOT/'experiments/workspace/root_full_caps_anchor_max.py'
    note = ROOT/'research/root_full_caps_anchor_max.md'
    certificate = ROOT/'experiments/logs/root-full-caps-anchor-max/anchor-max-certificate.json'
    manifest = ROOT/'experiments/logs/root-full-caps/model.json'
    saved = json.loads(certificate.read_text())
    assert digest(source) == '4bece4beff33280f0c19ab4bcbd68c7519895e03dd2e58d21642df55640d3249'
    assert saved['source_hashes']['root_full_caps_anchor_max.py'] == digest(source)
    labels = [x for x in combinations(range(14), 2) if x[0]//2 != x[1]//2]
    position = {x: i for i, x in enumerate(labels)}
    edges = list(combinations(range(84), 2))
    variable = {x: i+1 for i, x in enumerate(edges)}
    supports = []
    for anchor in range(14):
        supports.append([variable[tuple(sorted((position[tuple(sorted((anchor, 2*axis)))],
                                                 position[tuple(sorted((anchor, 2*axis+1)))])))]
                         for axis in range(7) if axis != anchor//2])
    assert supports == saved['near_count_supports']
    assert len(set(sum(supports, []))) == 84
    side_edges = set()
    diagonal_edges = set()
    for first_axis, second_axis in combinations(range(7), 2):
        cell = [position[(2*first_axis+s, 2*second_axis+t)]
                for s, t in product(range(2), repeat=2)]
        for i, j in combinations(range(4), 2):
            target = side_edges if len(set(labels[cell[i]]) & set(labels[cell[j]])) else diagonal_edges
            target.add(variable[tuple(sorted((cell[i], cell[j])))])
    assert side_edges == set(sum(supports, []))
    assert len(diagonal_edges) == 42 and not side_edges & diagonal_edges
    core_rows = [(1 << 15)-2]+[1 | 1 << (1+(a ^ 1)) for a in range(14)]
    record = {'core_rows': core_rows, 'labels': labels,
              'signatures': [(1+a, 1+b) for a, b in labels],
              'edge_variables': [[a, b, variable[a, b]] for a, b in edges]}
    domain_hash = hashlib.sha256(json.dumps(record, sort_keys=True,
                                           separators=(',', ':')).encode()).hexdigest()
    assert domain_hash == saved['domain_sha256'] == json.loads(manifest.read_text())['domain_sha256']
    # Inclusion-exclusion, independent of the recursive matching enumeration.
    matching_counts = {j: comb(6, j)*sum((-1)**i*comb(6-j, i)*odd_factorial(2*(6-j-i)-1)
                                        for i in range(7-j)) for j in range(7)}
    matching_counts = {j: count for j, count in matching_counts.items() if count}
    assert matching_counts == {int(k): v for k, v in saved['matching_histogram'].items()}
    assert sum(matching_counts.values()) == 10395
    generators = []
    for axis in range(7):
        image = list(range(14))
        image[2*axis:2*axis+2] = reversed(image[2*axis:2*axis+2])
        generators.append(image)
    for axis in range(6):
        image = list(range(14))
        for sign in range(2):
            image[2*axis+sign], image[2*(axis+1)+sign] = image[2*(axis+1)+sign], image[2*axis+sign]
        generators.append(image)
    for image in generators:
        lift = [position[tuple(sorted((image[a], image[b])))] for a, b in labels]
        assert len(set(lift)) == 84
        edge_image = [variable[tuple(sorted((lift[a], lift[b])))] for a, b in edges]
        for anchor in range(14):
            assert {edge_image[v-1] for v in supports[anchor]} == set(supports[image[anchor]])
    boolean_cases = 0
    cases = []
    for case in saved['cases']:
        parts = case['partition']
        assert sum(parts) == 6 and parts == sorted(parts)
        bound = parts.count(1)
        clauses = [[-v for v in subset] for row in supports for subset in combinations(row, bound+1)]
        assert clauses == case['clauses']
        assert len(clauses) == case['clause_count'] and bound == case['maximum_near_count']
        assert all(abs(lit) in side_edges for clause in clauses for lit in clause)
        if bound == 0:
            assert len(clauses) == 84 and all(len(clause) == 1 for clause in clauses)
        cases.append({'index': case['index'], 'partition': parts,
                      'bound': bound, 'clauses': len(clauses)})
    for bound in matching_counts:
        for bits in product((0, 1), repeat=6):
            permitted = all(any(not bits[i] for i in subset)
                            for subset in combinations(range(6), bound+1))
            assert permitted == (sum(bits) <= bound)
            boolean_cases += 1
    assert boolean_cases == 384
    return {'status': 'independent read-only mathematical and exact domain audit PASS',
            'scope': 'exhaustive union of maximum-anchor cases, not preservation of each old case',
            'source_sha256': digest(source), 'note_sha256': digest(note),
            'certificate_sha256': digest(certificate), 'base_manifest_sha256': digest(manifest),
            'audit_source_sha256': digest(Path(__file__)), 'domain_sha256': domain_hash,
            'reference_matching_counts_by_inclusion_exclusion': matching_counts,
            'distinct_side_variables': len(side_edges), 'unconstrained_cell_diagonals': len(diagonal_edges),
            'signed_axis_generators_checked': len(generators), 'boolean_assignments_checked': boolean_cases,
            'cases': cases, 'solver_called': False, 'full_cnf_built': False,
            'mathematical_checks': [
                'Every near fiber induces a perfect matching by the adjacent mixed equation.',
                'Reference-matching edges are exactly the size-one alternating components.',
                'Choose a maximizing near anchor, move it to zero, and normalize its matching.',
                'Signed-axis relabeling permutes all fourteen counts without changing their values.',
                'The matching stabilizer fixes the zero count and permutes the remaining supports.',
                'The maximizing convention preserves the union and needs no graph automorphism.',
            ]}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run()
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))
