"""Exact algebra controls for the principal-projector/exterior-Gram identity.

This checks integer-cleared formulas on small symmetric matrices. The
general proof is in projector_exterior_gram_identity.md. No graph domain,
moment tensor, spectral search, or optimizer is loaded.
"""

import argparse
import hashlib
import json
from pathlib import Path
import random


def product(A, B):
    n = len(A)
    return [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)]
            for i in range(n)]


def check(B):
    n, s = len(B), 99 - len(B)
    assert 0 < n < 99
    assert all(B[i][j] == B[j][i] for i in range(n) for j in range(n))
    P = [[27 * (i == j) - 9 * B[i][j] + 1 for j in range(n)] for i in range(n)]
    Q = [[44 * (i == j) + 11 * B[i][j] - 2 for j in range(n)] for i in range(n)]
    B2, P2 = product(B, B), product(P, P)
    G = [[12 * (i == j) - B[i][j] - B2[i][j] + 2 for j in range(n)] for i in range(n)]
    r = [14 - sum(row) for row in B]
    p = [sum(row) for row in P]
    assert all(9 * r[i] == s + p[i] for i in range(n))
    for i in range(n):
        for j in range(n):
            assert 11 * P[i][j] + 9 * Q[i][j] == 693 * (i == j) - 7
            assert 81 * s * G[i][j] - 81 * r[i] * r[j] == (
                63 * s * P[i][j] - s * P2[i][j] - p[i] * p[j])
    return n + 2 * n * n


def controls():
    rng = random.Random(991412)
    matrices = checks = 0
    for n in range(1, 17):
        for case in range(8):
            B = [[0] * n for _ in range(n)]
            for i in range(n):
                for j in range(i, n):
                    value = (0 if i == j else rng.randrange(2)) if case < 4 else rng.randrange(-2, 4)
                    B[i][j] = B[j][i] = value
            checks += check(B)
            matrices += 1
    # Scalar simplification of (I-J/99)(I+J/s)=I, for every permitted order.
    for n in range(1, 99):
        assert 99 - (99 - n) - n == 0
    return {'status': 'PASS: exact integer-cleared identities',
            'symmetric_matrices_checked': matrices, 'orders': list(range(1, 17)),
            'scalar_equalities_checked': checks,
            'rank_one_inverse_orders_checked': 98,
            'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'general_theorem_requires_symmetric_B_and_n_less_than_99': True,
            'degree_bounds_required_for_algebraic_equivalence': False,
            'graph_domain_or_count_point_loaded': False,
            'optimizer_or_spectral_scan_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    result = controls()
    args.output.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))
    print('result_sha256', hashlib.sha256(args.output.read_bytes()).hexdigest())
