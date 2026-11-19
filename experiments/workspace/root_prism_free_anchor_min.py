"""Small component encoding for a separate minimum-anchor normalization.

All10,395 matchings are enumerated directly. Equivalence is asserted on
the6,040 that avoid reference mates. No complete graph CNF is built or
solved, and the earlier global-prism-free pilot is unchanged.
"""

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path

import root_full_caps_lex as lex
import root_prism_free_structure as structure


ROOT = Path(__file__).resolve().parents[2]
TYPES = ((2, 2, 2), (2, 4), (3, 3), (6,))


def matchings(sites):
    if not sites:
        yield ()
        return
    a = sites[0]
    for b in sites[1:]:
        remaining = tuple(c for c in sites[1:] if c != b)
        for rest in matchings(remaining):
            yield tuple(sorted(((a, b),) + rest))


def cycle_type(matching):
    adjacent = {}
    for a, b in matching:
        adjacent.setdefault(a, set()).update((b, a ^ 1))
        adjacent.setdefault(b, set()).update((a, b ^ 1))
    remaining, parts = set(adjacent), []
    while remaining:
        stack = [min(remaining)]
        seen = set(stack)
        while stack:
            a = stack.pop()
            for b in adjacent[a]:
                if b not in seen:
                    seen.add(b)
                    stack.append(b)
        remaining -= seen
        assert len(seen) % 2 == 0
        parts.append(len(seen) // 2)
    return tuple(sorted(parts))


def component_patterns(length):
    output = []
    for axes in combinations(range(6), length):
        sites = tuple(a for axis in axes for a in (2 * axis, 2 * axis + 1))
        output.extend(matching for matching in matchings(sites) if cycle_type(matching) == (length,))
    assert len(output) == (30 if length == 2 else 160)
    assert len(output) == len(set(output))
    return sorted(output)


def pattern_sets(census):
    two = component_patterns(2)
    three = component_patterns(3)
    full = sorted(matching for matching in census if cycle_type(matching) == (2, 2, 2))
    double = []
    for first, second in combinations(two, 2):
        if not {v for edge in first for v in edge} & {v for edge in second for v in edge}:
            double.append(tuple(sorted(first + second)))
    assert len(full) == 120
    assert len(double) == len(set(double)) == 180
    return {'case24_full': full, 'case24_components': sorted(double),
            'case33_components': two, 'case6_components': sorted(two + three)}


def violates(matching, patterns):
    present = set(matching)
    return any(set(pattern) <= present for pattern in patterns)


def unit_propagation(clauses, units):
    values = {}
    pending = list(units)
    while True:
        while pending:
            literal = pending.pop()
            variable, value = abs(literal), literal > 0
            if variable in values and values[variable] != value:
                return True, values
            values[variable] = value
        found = []
        for clause in clauses:
            if any(abs(lit) in values and values[abs(lit)] == (lit > 0) for lit in clause):
                continue
            unassigned = [lit for lit in clause if abs(lit) not in values]
            if not unassigned:
                return True, values
            if len(unassigned) == 1:
                found.append(unassigned[0])
        if not found:
            return False, values
        pending = found


def propagation_control(patterns, census):
    edges = [edge for edge in combinations(range(12), 2) if edge[0] ^ 1 != edge[1]]
    variables = {edge: i + 1 for i, edge in enumerate(edges)}
    base = []
    for a in range(12):
        incident = [v for edge, v in variables.items() if a in edge]
        assert len(incident) == 10
        base.append(incident)
        base.extend([[-u, -v] for u, v in combinations(incident, 2)])
    assert len(base) == 552
    fixed = ((0, 3), (1, 2), (4, 7), (5, 6))
    units = [variables[edge] for edge in fixed]
    full = [[-variables[edge] for edge in pattern] for pattern in patterns['case24_full']]
    short = [[-variables[edge] for edge in pattern] for pattern in patterns['case24_components']]
    full_conflict, full_values = unit_propagation(base + full, units)
    short_conflict, _ = unit_propagation(base + short, units)
    assert not full_conflict and short_conflict
    completions = [matching for matching in census
                   if all(a ^ 1 != b for a, b in matching) and set(fixed) <= set(matching)]
    assert len(completions) == 2
    assert all(violates(matching, patterns['case24_full']) for matching in completions)
    return {'status': 'strict unit-propagation improvement in the explicit local matching CNF',
            'local_matching_variables': 60, 'local_matching_clauses': len(base),
            'four_positive_edges': fixed, 'remaining_perfect_matchings': len(completions),
            'full_six_edge_clauses_detect_conflict_by_unit_propagation': full_conflict,
            'four_edge_component_clauses_detect_conflict_by_unit_propagation': short_conflict,
            'unassigned_variables_after_full_clause_propagation': 60 - len(full_values),
            'scope': 'local pairwise exactly-one encoding only; no full-SRG runtime comparison'}


def global_clauses(patterns):
    labels, variables = structure.labels_and_variables()
    position = {pair: i for i, pair in enumerate(labels)}
    clauses = []
    for anchor in range(1, 14):
        other = [a for a in range(14) if a // 2 != anchor // 2]
        assert all(other[i ^ 1] == (other[i] ^ 1) for i in range(12))
        for pattern in patterns:
            selected = []
            for b, c in pattern:
                u = position[tuple(sorted((anchor, other[b])))]
                v = position[tuple(sorted((anchor, other[c])))]
                selected.append(-variables[tuple(sorted((u, v)))])
            clauses.append(sorted(selected))
    assert len(clauses) == len({tuple(clause) for clause in clauses}) == 13 * len(patterns)
    return clauses


def generate(analysis_path):
    census = list(matchings(tuple(range(12))))
    assert len(census) == len(set(census)) == 10395
    histogram = Counter(cycle_type(matching) for matching in census)
    assert dict(histogram) == {(1, 1, 1, 1, 1, 1): 1, (1, 1, 1, 1, 2): 30,
                              (1, 1, 1, 3): 160, (1, 1, 2, 2): 180,
                              (1, 1, 4): 720, (1, 2, 3): 960,
                              (1, 5): 2304, (2, 2, 2): 120,
                              (2, 4): 1440, (3, 3): 640, (6,): 3840}
    patterns = pattern_sets(census)
    valid = [matching for matching in census if all(a ^ 1 != b for a, b in matching)]
    assert len(valid) == 6040
    counts = Counter()
    for matching in valid:
        kind = cycle_type(matching)
        assert kind in TYPES
        assert violates(matching, patterns['case24_full']) == (kind == TYPES[0])
        assert violates(matching, patterns['case24_components']) == (kind == TYPES[0])
        assert violates(matching, patterns['case33_components']) == (kind in TYPES[:2])
        assert violates(matching, patterns['case6_components']) == (kind in TYPES[:3])
        for name, forbidden in patterns.items():
            counts[name] += not violates(matching, forbidden)
    assert dict(counts) == {'case24_full': 5920, 'case24_components': 5920,
                           'case33_components': 4480, 'case6_components': 3840}
    # The two case24 encodings are not equivalent without the no-mates
    # hypothesis: two2-components can leave two reference matching edges.
    outside_difference = [matching for matching in census
                          if violates(matching, patterns['case24_full']) !=
                             violates(matching, patterns['case24_components'])]
    assert len(outside_difference) == 180
    assert all(cycle_type(matching) == (1, 1, 2, 2) for matching in outside_difference)
    analysis = json.loads(analysis_path.read_text())
    records = {}
    for name, local in patterns.items():
        index = 8 if name.startswith('case24') else 9 if name.startswith('case33') else 10
        case = analysis['cases'][index]
        clauses = global_clauses(local)
        original = {tuple(clause) for clause in clauses}
        for generator in case['generators']:
            image = lex.lift(tuple(case['partition']), generator['image'])['edge_image']
            moved = {tuple(sorted(-image[-lit - 1] for lit in clause)) for clause in clauses}
            assert moved == original
        # All existing matching-complete partial controls of the named
        # type also satisfy these normalized near-matching conditions.
        matching_control = structure.cyclic_partial_matchings(TYPES[index - 7])
        for anchor in range(1, 14):
            sites = sorted(matching_control[anchor])
            inverse = {a: i for i, a in enumerate(sites)}
            control = tuple(sorted((min(inverse[a], inverse[b]), max(inverse[a], inverse[b]))
                                   for a, b in matching_control[anchor].items() if a < b))
            assert not violates(control, local)
        records[name] = {'case_index': index, 'clauses_per_other_anchor': len(local),
                         'literal_occurrences_per_other_anchor': sum(map(len, local)),
                         'other_anchors': 13, 'global_clauses': len(clauses),
                         'clause_length_histogram': sorted(Counter(map(len, clauses)).items()),
                         'local_patterns': local, 'global_clause_set_sha256': structure.sha(structure.canonical(clauses)),
                         'surviving_no_mate_matchings': counts[name],
                         'stabilizer_generators_checked': case['generator_count'],
                         'matching_complete_partial_control': 'PASS'}
    return {'status': 'exact minimum-partition component equivalence PASS; no formula changed',
            'source_sha256': structure.sha(Path(__file__).read_bytes()),
            'structure_source_sha256': structure.sha(Path(structure.__file__).read_bytes()),
            'lex_analysis': str(analysis_path.relative_to(ROOT)),
            'lex_analysis_sha256': structure.sha(analysis_path.read_bytes()),
            'matching_count': len(census), 'no_mate_matching_count': len(valid),
            'matching_type_histogram': [[list(kind), count] for kind, count in sorted(histogram.items())],
            'variants': records, 'case24_equivalence_requires_no_reference_mates': True,
            'case24_outside_scope_counterexamples': len(outside_difference),
            'propagation_control': propagation_control(patterns, census),
            'scope': 'new minimum-anchor four-case union, not each earlier case separately',
            'current_pilot_changed': False, 'full_CNF_built': False, 'solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lex-analysis', type=Path, required=True)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    record = json.loads(json.dumps(generate(args.lex_analysis.resolve())))
    if args.replay:
        assert json.loads(args.certificate.read_text()) == record
    else:
        args.certificate.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({key: value for key, value in record.items() if key != 'variants'}, indent=2))
    print(json.dumps({'variant_counts': {name: {key: value for key, value in item.items() if key != 'local_patterns'}
                                        for name, item in record['variants'].items()}}, indent=2))
