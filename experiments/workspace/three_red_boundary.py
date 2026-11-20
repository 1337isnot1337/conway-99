"""Independent exact boundary census for three rook-isomorphic bases.

The three cores are built from adjacency matrices, independently of the
interface SAT models and the translation bit-mask incidence checker.
All arithmetic is integral and only the standard library is required.
"""

from collections import Counter
from itertools import combinations, permutations, product
import argparse
import json
from pathlib import Path


IDENTITY = tuple(range(9))
REFLECTION = (0, 3, 6, 1, 4, 7, 2, 5, 8)
TRANSLATION = (4, 5, 3, 7, 8, 6, 1, 2, 0)
REPRESENTATIVES = {
    'identity': IDENTITY,
    'reflection': REFLECTION,
    'translation': TRANSLATION,
}


def rook(i, j):
    return i != j and (i // 3 == j // 3 or i % 3 == j % 3)


def automorphisms():
    maps = set()
    for row, col in product(permutations(range(3)), repeat=2):
        maps.add(tuple(3 * row[x] + col[y]
                       for x, y in product(range(3), repeat=2)))
        maps.add(tuple(3 * row[y] + col[x]
                       for x, y in product(range(3), repeat=2)))
    assert len(maps) == 72
    for mapping in maps:
        assert sorted(mapping) == list(range(9))
        assert all(rook(i, j) == rook(mapping[i], mapping[j])
                   for i, j in combinations(range(9), 2))
    return sorted(maps)


def classify_maps():
    autos = automorphisms()
    allowed = [p for p in autos if all(not rook(x, p[x]) for x in range(9))]
    assert len(allowed) == 11
    classes = []
    for label, p in enumerate(allowed):
        matches = []
        for name, representative in REPRESENTATIVES.items():
            conjugators = [q for q in autos
                           if all(q[p[x]] == representative[q[x]] for x in range(9))]
            if conjugators:
                matches.append((name, conjugators[0]))
        assert len(matches) == 1
        name, q = matches[0]
        classes.append({'label': label, 'map': list(p), 'class': name,
                        'conjugator': list(q)})
    assert Counter(row['class'] for row in classes) == {
        'identity': 1, 'reflection': 6, 'translation': 4}
    return classes


def adjacency(mapping):
    """Construct three bases with both root interfaces equal to identity."""
    matrix = [[0] * 27 for _ in range(27)]
    for base in range(3):
        for i, j in combinations(range(9), 2):
            if rook(i, j):
                matrix[9 * base + i][9 * base + j] = 1
                matrix[9 * base + j][9 * base + i] = 1
    for a, b in combinations(range(3), 2):
        interface = mapping if (a, b) == (1, 2) else IDENTITY
        for x, y in enumerate(interface):
            matrix[9 * a + x][9 * b + y] = 1
            matrix[9 * b + y][9 * a + x] = 1
    assert all(sum(row) == 6 for row in matrix)
    assert all(matrix[i][j] == matrix[j][i] for i in range(27) for j in range(27))
    return matrix


def enumerate_case(name, mapping):
    matrix = adjacency(mapping)
    square = [[sum(matrix[i][k] * matrix[k][j] for k in range(27))
               for j in range(27)] for i in range(27)]
    gram = [[12 * int(i == j) + 2 - matrix[i][j] - square[i][j]
             for j in range(27)] for i in range(27)]
    assert all(gram[i][i] == 8 and sum(gram[i]) == 24 for i in range(27))
    assert min(min(row) for row in gram) >= 0
    pairs = []
    mixed = []
    for x, y, z in product(range(9), repeat=3):
        sites = (x, 9 + y, 18 + z)
        if any(gram[i][j] == 0 for i, j in combinations(sites, 2)):
            continue
        pairs.append(sites)
        if all(sum(matrix[u][v] for v in sites) + int(u in sites) <= 2
               for u in range(27)):
            mixed.append(sites)
    return {
        'name': name,
        'map': list(mapping),
        'core_adjacency_matrix': matrix,
        'gram_matrix': gram,
        'signatures_checked': 729,
        'pair_quota_signatures': [list(s) for s in pairs],
        'mixed_quota_signatures': [list(s) for s in mixed],
        'pair_quota_signature_count': len(pairs),
        'mixed_quota_signature_count': len(mixed),
        'pair_occurrences_per_vertex': [sum(i in s for s in pairs) for i in range(27)],
        'mixed_occurrences_per_vertex': [sum(i in s for s in mixed) for i in range(27)],
    }


def translation_audit(case):
    """Check forcing and an exact linear contradiction from the independent list."""
    signatures = case['mixed_quota_signatures']
    gram = case['gram_matrix']
    groups = ((1, 1), (1, 4), (2, 2), (2, 3))
    equations = [[] for _ in groups]
    forced = set()
    forcing_rows = 0
    for i, j in combinations(range(27), 2):
        containing = [index for index, s in enumerate(signatures) if i in s and j in s]
        quota = gram[i][j]
        if not quota:
            assert not containing
            continue
        key = (quota, len(containing))
        assert key in groups
        equations[groups.index(key)].append((i, j, containing))
        if quota == len(containing):
            forced.update(containing)
            forcing_rows += 1
    assert [len(group) for group in equations] == [27, 27, 54, 27]
    assert forcing_rows == 81 and len(forced) == 81
    forced_degrees = [sum(i in signatures[index] for index in forced) for i in range(27)]
    assert forced_degrees == [9] * 27
    rhs = [groups[k][0] * len(equations[k]) for k in range(4)]
    patterns = []
    for index in range(len(signatures)):
        patterns.append(tuple(sum(index in row[2] for row in group) for group in equations))
    assert Counter(patterns) == {(1, 0, 0, 2): 27,
                                 (0, 1, 2, 0): 54,
                                 (0, 2, 0, 1): 27}
    weights = (-8, -2, 1, 4)
    assert all(sum(w * n for w, n in zip(weights, pattern)) == 0 for pattern in patterns)
    assert sum(w * n for w, n in zip(weights, rhs)) == 54
    return {
        'forcing_row_count': forcing_rows,
        'forced_signature_count': len(forced),
        'forced_occurrences_per_vertex': forced_degrees,
        'pair_equation_groups': [list(group) for group in groups],
        'group_equation_counts': [len(group) for group in equations],
        'group_rhs': rhs,
        'column_patterns': [{'pattern': list(pattern), 'count': count}
                            for pattern, count in sorted(Counter(patterns).items())],
        'equality_certificate_weights': list(weights),
        'weighted_rhs': 54,
        'weighted_column_coefficients': [0] * len(signatures),
    }


def audit():
    classification = classify_maps()
    cases = {name: enumerate_case(name, mapping)
             for name, mapping in REPRESENTATIVES.items()}
    assert [(cases[name]['pair_quota_signature_count'],
             cases[name]['mixed_quota_signature_count']) for name in REPRESENTATIVES] == [
                 (36, 36), (102, 84), (135, 108)]
    assert cases['identity']['mixed_occurrences_per_vertex'] == [4] * 27
    reflection = cases['reflection']
    through_zero = [s for s in reflection['pair_quota_signatures'] if 0 in s]
    assert through_zero == [[0, 13, 26], [0, 14, 23], [0, 14, 25],
                            [0, 16, 23], [0, 16, 25], [0, 17, 22]]
    assert all(s in reflection['mixed_quota_signatures'] for s in through_zero)
    assert Counter(reflection['mixed_occurrences_per_vertex']) == {6: 9, 11: 18}
    assert cases['translation']['mixed_occurrences_per_vertex'] == [12] * 27
    cases['translation']['independent_incidence_audit'] = translation_audit(cases['translation'])
    return {
        'status': 'all three interface classes excluded',
        'arithmetic': 'exact integers; standard library only',
        'rook_automorphisms': 72,
        'allowed_maps': classification,
        'core_vertices': 27,
        'core_degree': 6,
        'outside_vertices_required': 72,
        'outside_neighbors_per_core_vertex_required': 8,
        'maximum_signature_multiplicity': 1,
        'cases': cases,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    parser.add_argument('--translation-certificate', type=Path,
                        help='independently compare the separate translation checker output')
    args = parser.parse_args()
    result = audit()
    if args.verify:
        assert json.loads(args.verify.read_text()) == result
    if args.translation_certificate:
        certificate = json.loads(args.translation_certificate.read_text())
        case = result['cases']['translation']
        assert certificate['translation'] == case['map']
        assert certificate['signatures'] == case['mixed_quota_signatures']
        assert certificate['gram_matrix'] == case['gram_matrix']
        assert certificate['forced_signature_count'] == 81
        assert certificate['forced_occurrences_per_core_vertex'] == [9] * 27
        assert certificate['core_adjacency_rows'] == [
            sum(bit << j for j, bit in enumerate(row)) for row in case['core_adjacency_matrix']]
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2) + '\n')
    brief = {key: value for key, value in result.items() if key not in ('cases', 'allowed_maps')}
    brief['allowed_map_class_counts'] = dict(Counter(row['class'] for row in result['allowed_maps']))
    brief['cases'] = {name: {key: case[key] for key in (
        'pair_quota_signature_count', 'mixed_quota_signature_count',
        'mixed_occurrences_per_vertex')} for name, case in result['cases'].items()}
    brief['translation_equality_certificate'] = result['cases']['translation']['independent_incidence_audit']
    print(json.dumps(brief), flush=True)
