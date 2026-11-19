"""Independent small-domain review of the incidence-master interface.

No solver is instantiated, and no large CNF is parsed or regenerated.
The dense core construction and Gram-completeness checks are independent
of the incidence helper. Protocol and proof-wrapper review is documented
separately in the accompanying note.
"""

import argparse
import hashlib
from itertools import combinations, product
import json
from pathlib import Path

import complement_rook_incidence_master as master


ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def review(manifest_path):
    bound, base, cnf, rows, gram, triples, signatures, edges = master.check_model(
        manifest_path, require_base_cnf=False)

    def near(a, b):
        return a != b and (a // 3 == b // 3 or a % 3 == b % 3)

    dense = [[0] * 27 for _ in range(27)]
    for i, j in combinations(range(27), 2):
        same_class = i // 9 == j // 9
        if same_class:
            bit = near(i % 9, j % 9)
            if i // 9 == 2:
                bit = not bit
        else:
            bit = i % 9 == j % 9
        dense[i][j] = dense[j][i] = int(bit)
    exact_gram = [[12 * int(i == j) + 2 - dense[i][j]
                   - sum(dense[i][k] * dense[k][j] for k in range(27))
                   for j in range(27)] for i in range(27)]
    assert exact_gram == gram
    assert rows == [sum(bit << j for j, bit in enumerate(row)) for row in dense]
    assert all(sum(row) == 6 for row in dense)

    rebuilt = []
    for p, q, t in product(range(9), repeat=3):
        sites = (p, 9 + q, 18 + t)
        if all(exact_gram[i][j] > 0 for i, j in combinations(sites, 2)):
            rebuilt.append(sites)
    assert rebuilt == signatures and len(rebuilt) == 252
    assert triples == [(a, b - 9, c - 18) for a, b, c in rebuilt]
    membership = [[int(i in sites) for sites in rebuilt] for i in range(27)]
    equations = {}
    for i, j in combinations(range(27), 2):
        coefficients = [a * b for a, b in zip(membership[i], membership[j])]
        if exact_gram[i][j]:
            assert i // 9 != j // 9
            equations[i, j] = (coefficients, exact_gram[i][j])
        else:
            assert not any(coefficients)
    assert len(equations) == 180
    histogram = {}
    for (i, j), (_, quota) in equations.items():
        key = (i // 9, j // 9, quota)
        histogram[key] = histogram.get(key, 0) + 1
    assert histogram == {(0, 1, 2): 36, (0, 2, 1): 72, (1, 2, 1): 72}

    # Summing one complete cross-class margin gives each diagonal row.
    # Every column has exactly one point in the chosen other class.
    for i in range(27):
        other = 1 if i // 9 == 0 else 0
        summed = [0] * 252
        rhs = 0
        for j in range(9 * other, 9 * other + 9):
            record = equations.get(tuple(sorted((i, j))))
            if record is not None:
                coefficients, quota = record
                summed = [a + b for a, b in zip(summed, coefficients)]
                rhs += quota
        assert summed == membership[i]
        assert rhs == exact_gram[i][i] == 8
    assert [sum(membership[i][s] for i in range(9)) for s in range(252)] == [1] * 252
    assert sum(exact_gram[i][i] for i in range(9)) == 72

    _, _, _, _, _, actual = master.incidence.domain()
    actual_equations = sorted((tuple(members), quota) for members, quota in actual)
    expected_equations = sorted((tuple(s for s, value in enumerate(coefficients) if value), quota)
                                for coefficients, quota in equations.values())
    assert actual_equations == expected_equations

    selected = master.incidence.zero_control()['selected_signatures']
    assumptions = master.full_assumptions(selected)
    chosen = set(selected)
    assert assumptions == [s + 1 if s in chosen else -s - 1 for s in range(252)]
    # Check all 16 sign patterns of four-literal cores without a solver.
    # A negated core clause is false exactly at its prohibited conjunction.
    signed_checks = 0
    for signs in product((-1, 1), repeat=4):
        units = [sign * (i + 1) for i, sign in enumerate(signs)]
        cut = [-literal for literal in units]
        for assignment in product((False, True), repeat=4):
            conjunction = all(assignment[abs(lit) - 1] == (lit > 0) for lit in units)
            clause = any(assignment[abs(lit) - 1] == (lit > 0) for lit in cut)
            assert clause == (not conjunction)
            signed_checks += 1

    return {
        'status': 'independent dense domain and master completeness review PASS',
        'review_source_sha256': digest(Path(__file__)),
        'manifest': str(manifest_path.relative_to(ROOT)),
        'manifest_sha256': digest(manifest_path),
        'reviewed_source_hashes': bound['source_hashes'],
        'core_order': 27, 'candidate_triples_examined': 729,
        'admissible_signatures': len(rebuilt), 'full_gram_entries_checked': 729,
        'margin_equations': len(equations),
        'margin_histogram': [[*key, count] for key, count in sorted(histogram.items())],
        'diagonal_margins_derived': 27, 'implied_population': 72,
        'master_variables': cnf.nv, 'master_clauses': len(cnf.clauses),
        'master_cnf_sha256': bound['master_cnf_sha256'],
        'oracle_variables': base['variables'], 'oracle_clauses': base['clauses'],
        'oracle_edge_variables': len(edges),
        'full_signed_assumptions_checked': len(assumptions),
        'signed_cut_truth_table_cases': signed_checks,
        'solver_called': False, 'large_CNF_parsed_or_rebuilt': False,
        'new_graph_or_exclusion_claimed': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = review(args.manifest.resolve())
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
