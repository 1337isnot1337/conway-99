"""Exact local incidence and projector census at the core point R0.

Enumerates all864 possible eight-signature sets and all eligible perfect
matchings on representatives of the118 stabilizer orbits. Every resulting
35-point core passes visible caps and both principal-projector tests.
No exterior completion, SAT query, or full-incidence existence is claimed.
"""

import argparse
from collections import Counter
from fractions import Fraction
import hashlib
from itertools import combinations
import json
from pathlib import Path

import complement_rook_projector_schur as projectors


PROJECTOR_SHA = '8c88eb59b331cac3a087b9f49b579013c5ab0d3ac6ec0d44401e22a3edf0d567'
DEFAULT = Path(__file__).resolve().parents[1]/'logs/grids-and-triangles/complement-rook-local-star-census.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def local_patterns(triples):
    lookup = {tuple(triple): s for s, triple in enumerate(triples)}
    qs = sorted({q for p, q, t in triples if p == 0})
    assert qs == [4, 5, 7, 8]
    answer = []

    def visit(position, remaining, selected):
        if position == len(qs):
            assert not remaining
            answer.append(tuple(sorted(selected)))
            return
        q = qs[position]
        for pair in combinations([t for t in remaining if t != q], 2):
            visit(position+1, tuple(t for t in remaining if t not in pair),
                  selected+tuple(lookup[0, q, t] for t in pair))

    visit(0, tuple(range(1, 9)), ())
    assert len(answer) == len(set(answer)) == 864
    for selected in answer:
        assert Counter(triples[s][1] for s in selected) == Counter({q: 2 for q in qs})
        assert sorted(triples[s][2] for s in selected) == list(range(1, 9))
    return sorted(answer)


def perfect_matchings(selected, edges, remaining=tuple(range(8))):
    if not remaining:
        yield ()
        return
    a = remaining[0]
    for b in remaining[1:]:
        if tuple(sorted((selected[a], selected[b]))) in edges:
            rest = tuple(i for i in remaining if i not in (a, b))
            for tail in perfect_matchings(selected, edges, rest):
                yield ((a, b),)+tail


def extended_core(rows, signatures, selected, matching):
    result = list(rows)+[0]*8
    for i, source in enumerate(selected, 27):
        for point in signatures[source]:
            result[i] |= 1 << point
            result[point] |= 1 << i
    for a, b in matching:
        result[27+a] |= 1 << (27+b)
        result[27+b] |= 1 << (27+a)
    assert result[0].bit_count() == 14
    assert all((result[i] & result[j]).bit_count()+((result[i] >> j) & 1) <= 2
               for i, j in combinations(range(35), 2))
    return result


def census():
    assert digest(Path(projectors.__file__)) == PROJECTOR_SHA
    rows, gram, triples, signatures, _, eligible, domain_sha = projectors.domain()
    eligible = set(eligible)
    family = {s for s, sites in enumerate(signatures) if 0 in sites}
    assert len(family) == 28 and gram[0][0] == 8
    core_neighbors = [i for i in range(27) if rows[0] >> i & 1]
    assert len(core_neighbors) == 6
    assert all(sum(rows[i] >> j & 1 for j in core_neighbors) == 1 for i in core_neighbors)
    assert all(not (set(signatures[s]) & set(core_neighbors)) for s in family)
    patterns = local_patterns(triples)
    group = projectors.actions(rows, triples)
    stabilizer = [g for g in group if {g[s] for s in family} == family]
    assert len(stabilizer) == 8
    for action in stabilizer:
        assert {tuple(sorted((action[a], action[b]))) for a, b in eligible} == eligible
    remaining = set(patterns)
    orbit_records = []
    pattern_records = []
    while remaining:
        selected = min(remaining)
        orbit = sorted({tuple(sorted(g[s] for s in selected)) for g in stabilizer})
        assert set(orbit) <= remaining
        matches = list(perfect_matchings(selected, eligible))
        assert matches
        orbit_records.append({'selected_signatures': list(selected),
                              'orbit_size': len(orbit), 'eligible_perfect_matchings': len(matches)})
        for member in orbit:
            assert len(list(perfect_matchings(member, eligible))) == len(matches)
            pattern_records.append({'selected_signatures': list(member),
                                    'orbit_index': len(orbit_records)-1,
                                    'eligible_perfect_matchings': len(matches)})
        remaining -= set(orbit)
    assert len(orbit_records) == 118 and len(pattern_records) == 864
    pattern_records.sort(key=lambda r: r['selected_signatures'])
    forms = {kind: projectors.projector(kind, rows, signatures) for kind in ('minus', 'plus')}
    certificates_hash = hashlib.sha256()
    smallest_pivot = {kind: None for kind in forms}
    matched_cores = 0
    for record in orbit_records:
        selected = record['selected_signatures']
        for matching in perfect_matchings(selected, eligible):
            extended_core(rows, signatures, selected, matching)
            matched_cores += 1
            present = set(matching)
            for kind, form in forms.items():
                matrix = [[form['diag'][a] if i == j else
                           form['off'][int(tuple(sorted((i, j))) in present)][a][b]
                           for j, b in enumerate(selected)] for i, a in enumerate(selected)]
                assert all(sum(row) == 0 for row in matrix)
                quotient = [row[:7] for row in matrix[:7]]
                pivots = projectors.positive_ldl(quotient)
                # The helper checks L*diag(pivots)*L^T=quotient exactly.
                # S*1=0 then gives S=E*quotient*E^T for E=[I;-1^T].
                for numerator, denominator in pivots:
                    value = Fraction(numerator, denominator)
                    assert value > 0
                    if smallest_pivot[kind] is None or value < smallest_pivot[kind]:
                        smallest_pivot[kind] = value
                certificates_hash.update(canonical([selected, matching, kind, matrix, pivots]))
    assert matched_cores == 2521
    return {'status': 'complete local R0 incidence and exact projector census PASS',
            'source_sha256': digest(Path(__file__)), 'projector_source_sha256': PROJECTOR_SHA,
            'base_domain_sha256': domain_sha, 'core_point': 0, 'core_point_label': 'R0',
            'candidate_signatures': sorted(family), 'local_signature_sets': len(patterns),
            'inclusion_exclusion_terms': [2520, -2520, 1080, -240, 24],
            'stabilizer_order': len(stabilizer), 'local_set_orbits': len(orbit_records),
            'orbit_size_histogram': dict(sorted(Counter(r['orbit_size'] for r in orbit_records).items())),
            'local_matching_count_histogram': dict(sorted(Counter(r['eligible_perfect_matchings'] for r in pattern_records).items())),
            'matching_choices_on_representatives': matched_cores,
            'matching_choices_over_all_labelled_local_sets': sum(r['eligible_perfect_matchings'] for r in pattern_records),
            'visible_caps_passed_on_all_representative_cores': True,
            'exact_projector_checks': 2*matched_cores,
            'projector_residual_kernel': 'all-ones vector on the eight added vertices',
            'projector_residual_ranks': {'minus': 7, 'plus': 7},
            'smallest_exact_LDL_pivots': {kind: [v.numerator, v.denominator] for kind, v in smallest_pivot.items()},
            'all_matrix_and_LDL_records_sha256': certificates_hash.hexdigest(),
            'orbit_records': orbit_records, 'pattern_records': pattern_records,
            'local_patterns_excluded': 0, 'local_matchings_excluded': 0,
            'full_incidence_extension_claimed': False, 'graph_constructed': False,
            'optimizer_called': False, 'numerical_eigensystems_used': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, default=DEFAULT)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = json.loads(json.dumps(census()))
    if args.write:
        args.certificate.write_text(json.dumps(result, indent=2)+'\n')
    else:
        assert result == json.loads(args.certificate.read_text())
    print(json.dumps({k: v for k, v in result.items() if k not in ('orbit_records', 'pattern_records', 'candidate_signatures')}, indent=2))
