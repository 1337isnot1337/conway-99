"""Exact small controls for the unrestricted triangle39-core identities.

This file does not enumerate triangle cores or solve a completion problem.
All arithmetic in the default audit is integral or Fraction arithmetic.
The companion note proves the identities for arbitrary three matchings and
one permutation; these controls test the formulae and their indexing.
"""

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path


def zeros(n, m=None):
    return [[0] * (n if m is None else m) for _ in range(n)]


def eye(n):
    return [[int(i == j) for j in range(n)] for i in range(n)]


def ones(n, m=None):
    return [[1] * (n if m is None else m) for _ in range(n)]


def linear(*terms):
    return [[sum(a * M[i][j] for a, M in terms)
             for j in range(len(terms[0][1][0]))]
            for i in range(len(terms[0][1]))]


def transpose(M):
    return [list(row) for row in zip(*M)]


def product(A, B):
    BT = transpose(B)
    return [[sum(x * y for x, y in zip(row, col)) for col in BT]
            for row in A]


def exact_rank(M):
    rows = [[Fraction(x) for x in row] for row in M]
    r = 0
    for j in range(len(rows[0])):
        pivot = next((i for i in range(r, len(rows)) if rows[i][j]), None)
        if pivot is None:
            continue
        rows[r], rows[pivot] = rows[pivot], rows[r]
        a = rows[r][j]
        rows[r] = [x / a for x in rows[r]]
        for i in range(r + 1, len(rows)):
            if rows[i][j]:
                a = rows[i][j]
                rows[i] = [x - a * y for x, y in zip(rows[i], rows[r])]
        r += 1
        if r == len(rows):
            break
    return r


def build(matchings, q):
    assert len(matchings) == 3
    assert sorted(q) == list(range(12))
    for m in matchings:
        assert sorted(m) == list(range(12))
        assert all(m[i] != i and m[m[i]] == i for i in range(12))
    D = zeros(36)
    B = zeros(39)

    def edge(A, i, j):
        assert i != j
        A[i][j] = A[j][i] = 1

    for a, b in combinations(range(3), 2):
        edge(B, a, b)
    for a in range(3):
        for i in range(12):
            edge(D, 12 * a + i, 12 * a + matchings[a][i])
            edge(B, a, 3 + 12 * a + i)
    for i in range(12):
        edge(D, i, 12 + i)
        edge(D, i, 24 + i)
        edge(D, 12 + i, 24 + q[i])
    for i in range(36):
        for j in range(36):
            B[3 + i][3 + j] = D[i][j]
    E = [[int(i // 12 == a) for a in range(3)] for i in range(36)]
    return B, D, E


def components(D):
    unseen = set(range(len(D)))
    answer = []
    while unseen:
        start = min(unseen)
        unseen.remove(start)
        comp = [start]
        for u in comp:
            for v in sorted(unseen.copy()):
                if D[u][v]:
                    unseen.remove(v)
                    comp.append(v)
        answer.append(sorted(comp))
    return answer


def audit_case(name, matchings, q, expected):
    B, D, E = build(matchings, q)
    D2 = product(D, D)
    B2 = product(B, B)
    EE = product(E, transpose(E))
    I, J = eye(36), ones(36)
    assert all(sum(row) == 3 for row in D)
    assert product(D, E) == product(E, ones(3))

    comps = components(D)
    component_m = []
    for comp in comps:
        profile = [sum(v // 12 == a for v in comp) for a in range(3)]
        assert len(set(profile)) == 1 and profile[0] % 2 == 0
        component_m.append(profile[0])

    false_twins = [(i, j) for i, j in combinations(range(36), 2)
                   if D[i] == D[j]]
    cap_violations = [(i, j) for i, j in combinations(range(39), 2)
                      if B2[i][j] + B[i][j] > 2]
    assert cap_violations == [(i + 3, j + 3) for i, j in false_twins]

    G = linear((12, eye(39)), (2, ones(39)), (-1, B), (-1, B2))
    GD = linear((12, I), (2, J), (-1, D), (-1, D2), (-1, EE))
    assert all(not any(row) for row in G[:3])
    assert [row[3:] for row in G[3:]] == GD
    for a in range(3):
        block = [[GD[12 * a + i][12 * a + j] for j in range(12)]
                 for i in range(12)]
        assert block == [[9 * int(i == j) + 1 - int(matchings[a][i] == j)
                          for j in range(12)] for i in range(12)]

    kernel = [[int(i == a) for i in range(39)] for a in range(3)]
    for a in (0, 1):
        kernel.append([0] * 3 + [int(i // 12 == a) - int(i // 12 == 2)
                                for i in range(36)])
    for comp, m in zip(comps[:-1], component_m[:-1]):
        C = set(comp)
        kernel.append([0] * 3 + [12 * int(i in C) - m for i in range(36)])
    assert product(G, transpose(kernel)) == zeros(39, len(kernel))
    assert exact_rank(kernel) == len(comps) + 4
    assert exact_rank(G) == 35 - len(comps)

    # These integer equations verify the exact congruences in the note.
    Fminus9 = linear((27, I), (-9, D), (1, J))
    Wminus9 = linear((-9, E), (1, ones(36, 3)))
    Yminus18 = product(E, linear((-6, eye(3)), (1, ones(3))))
    Tminus9 = linear((36, eye(3)), (-8, ones(3)))
    assert product(Fminus9, Yminus18) == linear((18, Wminus9))
    assert product(transpose(Wminus9), Yminus18) == linear((18, Tminus9))
    Fplus11 = linear((44, I), (11, D), (-2, J))
    Wplus11 = linear((11, E), (-2, ones(36, 3)))
    Yplus4 = product(E, linear((1, eye(3)), (1, ones(3))))
    Tplus11 = linear((33, eye(3)), (9, ones(3)))
    assert product(Fplus11, Yplus4) == linear((4, Wplus11))
    assert product(transpose(Wplus11), Yplus4) == linear((4, Tplus11))
    minus_full9 = linear((27, eye(39)), (-9, B), (1, ones(39)))
    plus_full11 = linear((44, eye(39)), (11, B), (-2, ones(39)))
    assert exact_rank(minus_full9) == 37 - len(comps)
    assert exact_rank(plus_full11) == 36

    f = sum(q[i] == i for i in range(12))
    triangles = sum(D[i][j] * D[i][k] * D[j][k]
                    for i, j, k in combinations(range(36), 3))
    assert triangles == f
    # Every cross edge contributes its residual outside common-neighbor quota.
    cross_residual_sum = sum(1 - D2[i][j]
                             for i, j in combinations(range(36), 2)
                             if i // 12 != j // 12 and D[i][j])
    assert cross_residual_sum == 36 - 3 * f

    # The pair catalogue profiles use no outside incidence assignment.
    pair_profiles = []
    for comp, m in zip(comps, component_m):
        C = set(comp)
        r = m // 2
        expected_counts = [2 * (r - 5) * (r - 6), 4 * r * (6 - r),
                           2 * r * (r - 1)]
        for a in range(3):
            count = Counter(sum(12 * a + v in C for v in pair)
                            for pair in combinations(range(12), 2)
                            if matchings[a][pair[0]] != pair[1])
            assert [count[j] for j in range(3)] == expected_counts
        pair_profiles.append(expected_counts)

    if not false_twins:
        for comp, m in zip(comps, component_m):
            if m != 2:
                continue
            indices = [0, 1, 2] + [3 + i for i in comp]
            rook = [[B[i][j] for j in indices] for i in indices]
            assert all(sum(row) == 4 for row in rook)
            assert linear((1, product(rook, rook)), (1, rook)) == linear(
                (2, eye(9)), (2, ones(9)))

    result = {
        "name": name,
        "matchings": matchings,
        "q": q,
        "component_m": component_m,
        "false_twin_pairs": len(false_twins),
        "core_cap_violations": len(cap_violations),
        "shell_triangles": f,
        "incidence_gram_rank": 35 - len(comps),
        "negative_projector_rank": 37 - len(comps),
        "positive_projector_rank": 36,
        "outside_signature_edge_sum_if_completable": 36 - 3 * f,
        "component_pair_profiles_0_1_2": pair_profiles,
    }
    for key, value in expected.items():
        assert result[key] == value, (key, result[key], value)
    return result


def audit():
    mate = [i ^ 1 for i in range(12)]
    cases = [
        ("six_prisms", list(range(12)),
         {"component_m": [2] * 6, "false_twin_pairs": 0,
          "shell_triangles": 12}),
        ("six_K33_negative_control", mate,
         {"component_m": [2] * 6, "false_twin_pairs": 36,
          "shell_triangles": 0}),
        ("connected_shift2", [(i + 2) % 12 for i in range(12)],
         {"component_m": [12], "false_twin_pairs": 0,
          "shell_triangles": 0}),
    ]
    return {
        "schema": "triangle-root-constraints-exact-controls-v1",
        "source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "status": "PASS",
        "arithmetic": "standard-library integers and Fraction",
        "cases": [audit_case(name, [mate] * 3, q, expected)
                  for name, q, expected in cases],
        "scope": "Three formula/indexing controls, not a census or completion test.",
        "solver_called": False,
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--replay", type=Path)
    args = parser.parse_args()
    result = audit()
    if args.replay:
        assert result == json.loads(args.replay.read_text())
        print("Exact triangle39-core controls and saved report: PASS")
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + "\n")
    if not args.output and not args.replay:
        print(json.dumps(result, indent=2))
