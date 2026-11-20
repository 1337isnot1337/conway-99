"""Exact local consequences and partial controls for global prism-freeness.

This standard-library program runs no solver. It emits the 34,440
four-edge clauses on the existing rooted primary order, checks four
matching-complete partial configurations, and checks a countercontrol
separating a prism-free root from a globally prism-free graph.
"""

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations, permutations, product
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
PARTITIONS = ((2, 2, 2), (2, 4), (3, 3), (6,))


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def labels_and_variables():
    labels = [pair for pair in combinations(range(14), 2) if pair[0] ^ 1 != pair[1]]
    variables = {pair: i + 1 for i, pair in enumerate(combinations(range(84), 2))}
    assert len(labels) == 84 and len(variables) == 3486
    return labels, variables


def edge(rows, a, b):
    assert a != b
    rows[a] |= 1 << b
    rows[b] |= 1 << a


def triangle_prisms(rows):
    triangles = [tuple(t) for t in combinations(range(len(rows)), 3)
                 if all((rows[a] >> b) & 1 for a, b in combinations(t, 2))]
    prisms = []
    for first, second in combinations(triangles, 2):
        if set(first) & set(second):
            continue
        if (all(sum((rows[a] >> b) & 1 for b in second) == 1 for a in first)
                and all(sum((rows[b] >> a) & 1 for a in first) == 1 for b in second)):
            prisms.append(tuple(sorted(first + second)))
    assert len(prisms) == len(set(prisms))
    return triangles, prisms


def cap_violations(rows):
    return [(a, b) for a, b in combinations(range(len(rows)), 2)
            if (rows[a] & rows[b]).bit_count() + ((rows[a] >> b) & 1) > 2]


def matching_edges(matching):
    return {tuple(sorted((a, b))) for a, b in matching.items()}


def transported(matching, permutation):
    inverse = {value: key for key, value in permutation.items()}
    return {a: inverse[matching[permutation[a]]] for a in permutation}


def component_sizes(rows):
    remaining, sizes = set(range(len(rows))), []
    while remaining:
        stack = [min(remaining)]
        seen = set(stack)
        while stack:
            a = stack.pop()
            for b in range(len(rows)):
                if rows[a] >> b & 1 and b not in seen:
                    seen.add(b)
                    stack.append(b)
        remaining -= seen
        sizes.append(len(seen))
    return sorted(sizes)


def alternating_type(first, second):
    sites = sorted(first)
    index = {a: i for i, a in enumerate(sites)}
    rows = [0] * len(sites)
    for matching in (first, second):
        assert all(matching[matching[a]] == a and matching[a] != a for a in sites)
        for a, b in matching.items():
            edge(rows, index[a], index[b])
    return [size // 2 for size in component_sizes(rows)]


def triangle_core(first, second, third, permutation):
    sites = sorted(first)
    index = {a: i for i, a in enumerate(sites)}
    size = len(sites)
    rows = [0] * (3 + 3 * size)
    for a, b in combinations(range(3), 2):
        edge(rows, a, b)
    for fiber, matching in enumerate((first, second, third)):
        for a in sites:
            edge(rows, fiber, 3 + size * fiber + index[a])
            edge(rows, 3 + size * fiber + index[a], 3 + size * fiber + index[matching[a]])
    for a in sites:
        edge(rows, 3 + index[a], 3 + size + index[a])
        edge(rows, 3 + index[a], 3 + 2 * size + index[a])
        edge(rows, 3 + size + index[a], 3 + 2 * size + index[permutation[a]])
    return rows


def small_characterization_control():
    matchings = ({0: 1, 1: 0, 2: 3, 3: 2},
                 {0: 2, 2: 0, 1: 3, 3: 1},
                 {0: 3, 3: 0, 1: 2, 2: 1})
    first = matchings[0]
    count = prism_free = 0
    for second, third, values in product(matchings, matchings, permutations(range(4))):
        permutation = dict(enumerate(values))
        condition = (all(permutation[a] != a for a in range(4))
                     and not (matching_edges(first) & matching_edges(second))
                     and not (matching_edges(first) & matching_edges(third))
                     and not (matching_edges(second) & matching_edges(transported(third, permutation))))
        rows = triangle_core(first, second, third, permutation)
        _, prisms = triangle_prisms(rows)
        assert condition == (not prisms)
        if condition:
            assert not cap_violations(rows)
            prism_free += 1
        count += 1
    assert count == 216
    return {'complete_small_configurations': count, 'prism_free_configurations': prism_free,
            'characterization_and_cap_implication': 'PASS'}


def near_axis_clauses(labels, variables):
    position = {pair: i for i, pair in enumerate(labels)}

    def vertex(a, b):
        return position[tuple(sorted((a, b)))]

    def literal(a, b):
        return -variables[tuple(sorted((a, b)))]

    clauses, counts = [], []
    for axis in range(7):
        a, opposite = 2 * axis, 2 * axis + 1
        sites = [b for b in range(14) if b // 2 != axis]
        pairs = [pair for pair in combinations(sites, 2) if pair[0] ^ 1 != pair[1]]
        before = len(clauses)
        assert len(pairs) == 60
        for b, c in pairs:
            choices = [(d, e) for d, e in pairs if not {b, c} & {d, e}]
            assert len(choices) == 41
            for d, e in choices:
                for x, y in ((d, e), (e, d)):
                    u, v = vertex(a, b), vertex(a, c)
                    w, z = vertex(opposite, x), vertex(opposite, y)
                    clause = sorted((literal(u, v), literal(w, z), literal(u, w), literal(v, z)))
                    assert len(set(clause)) == 4 and all(-3486 <= value < 0 for value in clause)
                    clauses.append(clause)
        counts.append(len(clauses) - before)
    assert counts == [4920] * 7
    assert len(clauses) == len({tuple(clause) for clause in clauses}) == 34440
    return clauses, counts


def cyclic_partial_matchings(parts, countercontrol=False):
    matchings = {}
    for axis in range(7):
        first, second, offset = {}, {}, 1
        for length in parts:
            block = list(range(offset, offset + length))
            offset += length
            for i, b in enumerate(block):
                c = block[(i + 1) % length]
                x, y = 2 * ((axis + b) % 7) + 1, 2 * ((axis + c) % 7)
                first[x] = y
                first[y] = x
            if length == 2:
                b, c = block
                for sign in range(2):
                    x, y = 2 * ((axis + b) % 7) + sign, 2 * ((axis + c) % 7) + sign
                    second[x] = y
                    second[y] = x
            else:
                for i, b in enumerate(block):
                    c = block[(i + 1) % length]
                    x, y = 2 * ((axis + b) % 7) + 1, 2 * ((axis + c) % 7)
                    second[x] = y
                    second[y] = x
        if countercontrol:
            second = {a ^ 1: b ^ 1 for a, b in first.items()}
        matchings[2 * axis] = first
        matchings[2 * axis + 1] = second
    return matchings


def partial_control(parts, clauses, labels, variables, countercontrol=False):
    position = {pair: i for i, pair in enumerate(labels)}
    matchings = cyclic_partial_matchings(parts, countercontrol)
    outside = [0] * 84
    transition = [0] * 84
    for a, matching in matchings.items():
        reference = {b: b ^ 1 for b in matching}
        assert alternating_type(reference, matching) == list(parts)
        for b, c in matching.items():
            u, v = (position[tuple(sorted((a, z)))] for z in (b, c))
            edge(outside, u, v)
            edge(transition, u, v)
    for i, (a, b) in enumerate(labels):
        edge(outside, i, position[tuple(sorted((a ^ 1, b ^ 1)))])
    assert all(row.bit_count() == 3 for row in outside)
    assert all(row.bit_count() == 2 for row in transition)

    rows = [0] * 99
    for a in range(14):
        edge(rows, 0, 1 + a)
        edge(rows, 1 + a, 1 + (a ^ 1))
    for i, pair in enumerate(labels):
        for a in pair:
            edge(rows, 15 + i, 1 + a)
        for j in range(84):
            if outside[i] >> j & 1:
                edge(rows, 15 + i, 15 + j)
    assert not cap_violations(rows)
    triangles, prisms = triangle_prisms(rows)
    assert len(triangles) == 91
    assert not any(0 in prism for prism in prisms)
    assert len(prisms) == (42 if countercontrol else 0)
    positive = {variable for (i, j), variable in variables.items() if outside[i] >> j & 1}
    rejected = [i for i, clause in enumerate(clauses) if all(-literal in positive for literal in clause)]
    assert len(rejected) == len(prisms)

    core_records = []
    for axis in range(7):
        a = 2 * axis
        reference = {b: b ^ 1 for b in matchings[a]}
        first, second = matchings[a], matchings[a + 1]
        pulled = transported(second, reference)
        overlap = len(matching_edges(first) & matching_edges(pulled))
        assert overlap == (6 if countercontrol else 0)
        core_rows = triangle_core(reference, first, second, reference)
        _, core_prisms = triangle_prisms(core_rows)
        assert len(core_prisms) == overlap
        assert not cap_violations(core_rows)
        shell_rows = [row >> 3 for row in core_rows[3:]]
        core_records.append({'axis': axis, 'shell_component_sizes': component_sizes(shell_rows),
                             'transported_matching_overlap': overlap,
                             'internal_prisms': len(core_prisms)})

    # These are the fixed zero and minus-two projectors of a hypothetical
    # complete84-point exterior. Only their known coordinate formulae and
    # the transition graph are evaluated on this partial control.
    trace_zero = Fraction(0)
    trace_minus_two = Fraction(0)
    for i, j in combinations(range(84), 2):
        if not transition[i] >> j & 1:
            continue
        signed_dot = sum((1 if a % 2 == b % 2 else -1)
                         for a in labels[i] for b in labels[j] if a // 2 == b // 2)
        support_dot = len({a // 2 for a in labels[i]} & {b // 2 for b in labels[j]})
        trace_zero += Fraction(signed_dot, 12)
        trace_minus_two += Fraction(1, 10) * (Fraction(support_dot) - Fraction(4, 7))
    assert trace_zero == 7 and trace_minus_two == Fraction(18, 5)
    return {'partition_at_all14_anchors': list(parts), 'countercontrol': countercontrol,
            'near_matchings': [[a, [[b, c] for b, c in sorted(matching.items())]]
                               for a, matching in sorted(matchings.items())],
            'all_seven_cross_matchings': 'reference sign reversal b -> b^1',
            'known_adjacency_rows': [str(row) for row in rows],
            'known_edges': sum(row.bit_count() for row in rows) // 2,
            'known_degree_histogram': sorted(Counter(row.bit_count() for row in rows).items()),
            'all4851_visible_upper_caps': 'PASS', 'known_triangles': len(triangles),
            'known_prisms': len(prisms), 'known_prisms_through_root': 0,
            'violated_clause_indices': rejected, 'triangle_cores': core_records,
            'transition_trace_on_fixed_zero_space': str(trace_zero),
            'transition_trace_on_fixed_minus_two_space': str(trace_minus_two),
            'full_SRG_or_incidence_completion': False}


def spectral_trace_control():
    records = []
    for prisms_at_root in range(85):
        m = Fraction(prisms_at_root)
        weights = {12: Fraction(2), -2: Fraction(18, 5) + m / 10,
                   0: 7 - m / 12, 3: Fraction(72, 5) + 2 * m / 105,
                   -4: -27 - m / 28}
        assert sum(weights.values()) == 0
        assert sum(value * weight for value, weight in weights.items()) == 168
        assert sum(value ** 2 * weight for value, weight in weights.items()) == 0
        assert sum(value ** 3 * weight for value, weight in weights.items()) == 5544 + 2 * m
        assert sum(value ** 4 * weight for value, weight in weights.items()) == 35784 - 6 * m
        if not prisms_at_root:
            records = [[value, str(weight)] for value, weight in sorted(weights.items())]
    return {'formal_integer_m_values_checked': 85, 'prism_free_projector_traces': records,
            'prism_free_trace_C3H': 5544, 'prism_free_trace_C4H': 35784,
            'scope': 'exact necessary identities, not a feasible complete adjacency matrix'}


def build(certificate_path, clause_path, replay=False):
    labels, variables = labels_and_variables()
    clauses, counts = near_axis_clauses(labels, variables)
    raw = (f'p cnf 3486 {len(clauses)}\n' + ''.join(
        ' '.join(map(str, clause)) + ' 0\n' for clause in clauses)).encode()
    compressed = gzip.compress(raw, mtime=0)
    record = {'status': 'exact globally-prism-free local reduction and partial controls PASS',
              'source_sha256': sha(Path(__file__).read_bytes()),
              'root_builder_sha256': sha(Path(__file__).with_name('root_full_caps.py').read_bytes()),
              'scope': 'globally prism-free SRG only; no graph or exclusion obtained',
              'primary_edge_order_sha256': sha(canonical({'labels': labels, 'edges': list(variables)})),
              'primary_variables': 3486, 'four_edge_clauses': len(clauses),
              'clauses_per_root_axis': counts, 'clause_path': str(clause_path.relative_to(ROOT)),
              'raw_clause_cnf_sha256': sha(raw), 'compressed_clause_cnf_sha256': sha(compressed),
              'small_characterization_control': small_characterization_control(),
              'partial_controls': [partial_control(parts, clauses, labels, variables) for parts in PARTITIONS],
              'root_local_countercontrol': partial_control((6,), clauses, labels, variables, True),
              'spectral_trace_control': spectral_trace_control(), 'solver_called': False}
    # Round-trip tuples exactly as JSON represents them before comparison.
    record = json.loads(json.dumps(record))
    if replay:
        assert certificate_path.read_text() and json.loads(certificate_path.read_text()) == record
        assert clause_path.read_bytes() == compressed
        assert gzip.decompress(clause_path.read_bytes()) == raw
    else:
        clause_path.parent.mkdir(parents=True, exist_ok=True)
        clause_path.write_bytes(compressed)
        certificate_path.write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps({key: value for key, value in record.items()
                      if key not in ('partial_controls', 'root_local_countercontrol')}, indent=2))
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--clauses', type=Path, required=True)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    build(args.certificate.resolve(), args.clauses.resolve(), args.replay)
