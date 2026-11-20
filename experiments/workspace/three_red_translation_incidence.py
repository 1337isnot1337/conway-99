"""Exact incidence obstruction for three rook bases with translation holonomy.

There are 108 mixed-admissible outside signatures. A weighted sum of
their pair-incidence equations gives the exact contradiction 0 = 54.
Separately, pair quotas force 81 distinct signatures, but only 72 exterior
vertices exist. The replay uses only Python's standard library.
"""

import argparse
from collections import Counter
from itertools import combinations, product
import json
from pathlib import Path


TRANSLATION = (4, 5, 3, 7, 8, 6, 1, 2, 0)


def rook(x, y):
    return x != y and (x//3 == y//3 or x % 3 == y % 3)


def core():
    """Build the 27-vertex core, without importing any other builder."""
    assert TRANSLATION == tuple(3*((x+1) % 3)+(y+1) % 3
                                for x, y in product(range(3), repeat=2))
    rows = [0]*27
    for base in range(3):
        for x, y in combinations(range(9), 2):
            if rook(x, y):
                i, j = 9*base+x, 9*base+y
                rows[i] |= 1 << j
                rows[j] |= 1 << i
    for a, b in combinations(range(3), 2):
        mapping = TRANSLATION if (a, b) == (1, 2) else tuple(range(9))
        for x, y in enumerate(mapping):
            i, j = 9*a+x, 9*b+y
            rows[i] |= 1 << j
            rows[j] |= 1 << i
    assert all(row.bit_count() == 6 for row in rows)
    assert all(((rows[i] >> j) & 1) == ((rows[j] >> i) & 1)
               for i, j in combinations(range(27), 2))
    assert all((rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1) <= 2
               for i, j in combinations(range(27), 2))
    return rows


def data():
    rows = core()
    gram = [[12*int(i == j)+2-((rows[i] >> j) & 1)
             -(rows[i] & rows[j]).bit_count() for j in range(27)]
            for i in range(27)]
    assert all(gram[i][i] == 8 and sum(gram[i]) == 24 for i in range(27))
    pair_signatures = []
    signatures = []
    for sites in product(range(9), range(9, 18), range(18, 27)):
        if not all(gram[i][j] > 0 for i, j in combinations(sites, 2)):
            continue
        pair_signatures.append(sites)
        mask = sum(1 << i for i in sites)
        if all((row & mask).bit_count()+((mask >> i) & 1) <= 2
               for i, row in enumerate(rows)):
            signatures.append(sites)
    return rows, gram, pair_signatures, signatures


def audit():
    rows, gram, pair_signatures, signatures = data()
    assert len(pair_signatures) == 135 and len(signatures) == 108
    # Direct integer-matrix mixed caps, separate from the bit-mask listing.
    check = []
    for sites in pair_signatures:
        if all(sum(int(i in sites) if i == j else (rows[i] >> j) & 1
                   for j in sites) <= 2 for i in range(27)):
            check.append(sites)
    assert check == signatures
    assert all(sum(i in sites for sites in signatures) == 12 for i in range(27))

    equations = []
    for i in range(27):
        for j in range(i, 27):
            available = [a for a, sites in enumerate(signatures) if i in sites and j in sites]
            assert bool(available) == bool(gram[i][j])
            if gram[i][j]:
                equations.append({'pair': [i, j], 'quota': gram[i][j], 'signatures': available})
    assert len(equations) == 162
    availability = Counter((e['quota'], len(e['signatures'])) for e in equations)
    assert availability == {(1, 1): 27, (1, 4): 27, (2, 2): 54,
                            (2, 3): 27, (8, 12): 27}

    # This certificate needs neither nonnegativity nor integrality.
    # Sum equations in four classes, then take the indicated combination.
    classes = ((1, 1), (1, 4), (2, 2), (2, 3))
    weights = (-8, -2, 1, 4)
    grouped = [[e for e in equations if (e['quota'], len(e['signatures'])) == key]
               for key in classes]
    right_sides = [sum(e['quota'] for e in group) for group in grouped]
    assert right_sides == [27, 27, 108, 54]
    patterns = [tuple(sum(a in e['signatures'] for e in group) for group in grouped)
                for a in range(len(signatures))]
    pattern_counts = Counter(patterns)
    assert pattern_counts == {(1, 0, 0, 2): 27, (0, 1, 2, 0): 54,
                              (0, 2, 0, 1): 27}
    column_coefficients = [sum(w*x for w, x in zip(weights, pattern)) for pattern in patterns]
    right_side = sum(w*x for w, x in zip(weights, right_sides))
    assert column_coefficients == [0]*108 and right_side == 54

    # A size-three signature cannot repeat: two outside vertices with
    # that signature would have at least three common neighbors.
    # Hence quota == available forces every available signature to occur.
    forcing = [e for e in equations if e['pair'][0] != e['pair'][1]
               and e['quota'] == len(e['signatures'])]
    forced = sorted({a for e in forcing for a in e['signatures']})
    occurrences = [sum(i in signatures[a] for a in forced) for i in range(27)]
    assert len(forcing) == 81 and len(forced) == 81 and occurrences == [9]*27
    assert len(forced) > 99-len(rows)
    assert all(n > 14-rows[i].bit_count() for i, n in enumerate(occurrences))

    local = []
    for a in forced:
        if 0 in signatures[a]:
            witness = next(e for e in forcing if a in e['signatures'])
            local.append({'signature': a, 'forcing_pair': witness['pair']})
    assert len(local) == 9
    return {
        'status': 'excluded by exact linear incidence identity 0 = 54',
        'core_vertices': 27, 'core_degree': 6,
        'translation': list(TRANSLATION),
        'core_adjacency_rows': rows, 'gram_matrix': gram,
        'all_one_per_base_signatures': 729,
        'pair_quota_signature_count': len(pair_signatures),
        'mixed_quota_signature_count': len(signatures),
        'signatures': [list(sites) for sites in signatures],
        'incidence_equations': equations,
        'quota_availability_counts': [[quota, available, count]
                                     for (quota, available), count in sorted(availability.items())],
        'aggregate_equation_types': [list(key) for key in classes],
        'aggregate_equation_right_sides': right_sides,
        'signature_pattern_counts': [[list(pattern), count]
                                    for pattern, count in sorted(pattern_counts.items())],
        'linear_certificate_weights': list(weights),
        'linear_certificate_column_coefficients': column_coefficients,
        'linear_certificate_right_side': right_side,
        'maximum_multiplicity_per_signature': 1,
        'forcing_equations': forcing,
        'forced_signatures': forced,
        'forced_signature_count': len(forced),
        'outside_vertices_required': 72,
        'forced_occurrences_per_core_vertex': occurrences,
        'outside_degree_required_per_core_vertex': 8,
        'local_vertex_zero_forcing_certificate': local,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    result = audit()
    if args.verify:
        assert json.loads(args.verify.read_text()) == result
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    hidden = {'core_adjacency_rows', 'gram_matrix', 'signatures',
              'incidence_equations', 'forcing_equations', 'forced_signatures',
              'forced_occurrences_per_core_vertex', 'local_vertex_zero_forcing_certificate',
              'linear_certificate_column_coefficients'}
    print(json.dumps({k: v for k, v in result.items() if k not in hidden}), flush=True)
