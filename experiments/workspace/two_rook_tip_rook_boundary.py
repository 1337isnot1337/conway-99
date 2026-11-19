"""Exact labelled-rook tip boundary census and binary incidence propagation.

Only the standard library and the frozen Hall-certificate verifier are used.
No graph-completion solver is launched.  Surviving incidence domains are
necessary reductions, not asserted completions.
"""

import argparse
from collections import Counter, deque
from fractions import Fraction
from functools import reduce
from itertools import combinations, permutations, product
import json
from math import gcd, lcm
from pathlib import Path

from two_rook_tip_hall_audit import verify as verify_hall


EDGES = tuple(combinations(range(9), 2))
EDGE_INDEX = {edge: i for i, edge in enumerate(EDGES)}


def rook(a, b):
    return a != b and (a//3 == b//3 or a % 3 == b % 3)


ROOT_CODE = sum(1 << i for i, edge in enumerate(EDGES) if rook(*edge))


def encode(edges):
    return sum(1 << EDGE_INDEX[edge] for edge in {tuple(sorted(edge)) for edge in edges})


def rows(code):
    result = [0]*9
    for i, (a, b) in enumerate(EDGES):
        if code >> i & 1:
            result[a] |= 1 << b
            result[b] |= 1 << a
    return result


def partitions():
    for first_pair in combinations(range(1, 9), 2):
        first = (0, *first_pair)
        remaining = sorted(set(range(9))-set(first))
        for second_pair in combinations(remaining[1:], 2):
            second = (remaining[0], *second_pair)
            yield (first, second, tuple(sorted(set(remaining)-set(second))))


def catalogue_by_partitions():
    multiplicity = Counter()
    count = 0
    for partition in partitions():
        count += 1
        for second in permutations(partition[1]):
            for third in permutations(partition[2]):
                columns = tuple(zip(partition[0], second, third))
                edges = {tuple(sorted(edge)) for line in (*partition, *columns)
                         for edge in combinations(line, 2)}
                assert len(edges) == 18
                multiplicity[encode(edges)] += 1
    assert count == 280 and len(multiplicity) == 5040
    assert sum(multiplicity.values()) == 10080 and set(multiplicity.values()) == {2}
    return sorted(multiplicity)


def catalogue_by_root_neighborhood():
    """Independent 70*3*24 construction from the two local triangles at 0."""
    answer = []
    for neighbors in combinations(range(1, 9), 4):
        for partner in neighbors[1:]:
            first = (neighbors[0], partner)
            second = tuple(sorted(set(neighbors)-set(first)))
            far = tuple(sorted(set(range(1, 9))-set(neighbors)))
            for assigned in permutations(far):
                edges = {(0, p) for p in neighbors}
                edges.add(first)
                edges.add(second)
                for i, j in product(range(2), repeat=2):
                    point = assigned[2*i+j]
                    edges.add(tuple(sorted((point, first[i]))))
                    edges.add(tuple(sorted((point, second[j]))))
                for a, b in ((0, 1), (2, 3), (0, 2), (1, 3)):
                    edges.add(tuple(sorted((assigned[a], assigned[b]))))
                assert len(edges) == 18
                answer.append(encode(edges))
    assert len(answer) == len(set(answer)) == 5040
    return sorted(answer)


def hall_masks(code):
    adjacency = rows(code)
    masks = []
    for tip in range(9):
        mask = 0
        for other in range(9):
            if adjacency[tip] >> other & 1:
                canonical = 3*((other//3-tip//3) % 3)+(other % 3-tip % 3) % 3
                assert canonical
                mask |= 1 << (canonical-1)
        masks.append(mask)
    return masks


def automorphisms():
    answer = []
    for first, second, swap in product(permutations(range(3)), permutations(range(3)), (False, True)):
        permutation = [3*first[p % 3]+second[p//3] if swap else 3*first[p//3]+second[p % 3]
                       for p in range(9)]
        assert sorted(permutation) == list(range(9))
        assert all(rook(a, b) == rook(permutation[a], permutation[b]) for a, b in EDGES)
        answer.append(permutation)
    assert len({tuple(p) for p in answer}) == 72
    return sorted(answer)


def relabel(code, permutation):
    return encode([tuple(sorted((permutation[a], permutation[b])))
                   for i, (a, b) in enumerate(EDGES) if code >> i & 1])


def nullspace(matrix):
    a = [[Fraction(x) for x in row] for row in matrix]
    width = len(a[0])
    pivots = []
    for column in range(width):
        row = next((i for i in range(len(pivots), len(a)) if a[i][column]), None)
        if row is None:
            continue
        pivot = len(pivots)
        a[pivot], a[row] = a[row], a[pivot]
        value = a[pivot][column]
        a[pivot] = [x/value for x in a[pivot]]
        for i in range(len(a)):
            if i != pivot and a[i][column]:
                value = a[i][column]
                a[i] = [x-value*y for x, y in zip(a[i], a[pivot])]
        pivots.append(column)
    basis = []
    for free in range(width):
        if free in pivots:
            continue
        vector = [Fraction(0)]*width
        vector[free] = Fraction(1)
        for i, pivot in enumerate(pivots):
            vector[pivot] = -a[i][free]
        denominator = lcm(*(v.denominator for v in vector))
        integer = [int(v*denominator) for v in vector]
        divisor = reduce(gcd, integer)
        integer = [v//divisor for v in integer]
        if next(x for x in integer if x) < 0:
            integer = [-x for x in integer]
        assert all(sum(x*y for x, y in zip(row, integer)) == 0 for row in matrix)
        basis.append(integer)
    return basis


def core(code):
    tip = rows(code)
    adjacency = [0]*27
    for a, b in combinations(range(27), 2):
        if a//9 == b//9:
            adjacent = bool(tip[a % 9] >> (b % 9) & 1) if a//9 == 2 else rook(a % 9, b % 9)
        else:
            adjacent = a % 9 == b % 9
        if adjacent:
            adjacency[a] |= 1 << b
            adjacency[b] |= 1 << a
    assert all(row.bit_count() == 6 for row in adjacency)
    gram = [[12*int(a == b)+2-int(adjacency[a] >> b & 1)
             -(adjacency[a] & adjacency[b]).bit_count() for b in range(27)]
            for a in range(27)]
    assert min(min(row) for row in gram) >= 0
    return adjacency, gram


def incidence_domain(code):
    adjacency, gram = core(code)
    tip = rows(code)
    common = nullspace([[int(rook(a, b))-int(a == b) for b in range(9)] for a in range(9)]
                       + [[int(tip[a] >> b & 1)-int(a == b) for b in range(9)] for a in range(9)])
    lifted = [vector*3 for vector in common]
    for vector in lifted:
        assert all(sum(row[j]*vector[j] for j in range(27)) == 0 for row in gram)
    full_kernel = nullspace(gram)
    assert len(full_kernel) == 2+len(common)
    pair_allowed, allowed = [], []
    excluded_by_kernel = []
    for p, q, t in product(range(9), repeat=3):
        signature = (p, 9+q, 18+t)
        if not all(gram[a][b] > 0 for a, b in combinations(signature, 2)):
            continue
        mask = sum(1 << a for a in signature)
        assert all(2-(row & mask).bit_count()-int(i in signature) >= 0
                   for i, row in enumerate(adjacency))
        triple = [p, q, t]
        pair_allowed.append(triple)
        violation = next((i for i, vector in enumerate(common)
                          if vector[p]+vector[q]+vector[t]), None)
        if violation is None:
            assert all(sum(vector[i] for i in signature) == 0 for vector in full_kernel)
            allowed.append(triple)
        else:
            excluded_by_kernel.append({'triple': triple, 'kernel_index': violation})
    equations = []
    for first, second in ((0, 1), (0, 2), (1, 2)):
        for a, b in product(range(9), repeat=2):
            target = gram[9*first+a][9*second+b]
            if target:
                variables = [i for i, signature in enumerate(allowed)
                             if signature[first] == a and signature[second] == b]
                equations.append({'core_pair': [9*first+a, 9*second+b],
                                  'target': target, 'variables': variables})
    assert sum(row['target'] for row in equations) == 216
    return {'pair_allowed_signatures': pair_allowed,
            'common_rook_one_basis': common, 'core_gram_rank': 27-len(full_kernel),
            'kernel_excluded_signatures': excluded_by_kernel,
            'signatures': allowed, 'equations': equations}


def propagate(domain):
    equations = domain['equations']
    state = [-1]*len(domain['signatures'])
    incident = [[] for _ in state]
    unknown = [set(row['variables']) for row in equations]
    residual = [row['target'] for row in equations]
    for row, variables in enumerate(unknown):
        for variable in variables:
            incident[variable].append(row)
    assert all(len(row) == 3 for row in incident)
    queue = deque(range(len(equations)))
    trace = []
    while queue:
        row = queue.popleft()
        left, target = unknown[row], residual[row]
        if target < 0 or target > len(left):
            return {'status': 'excluded by exact binary margin propagation',
                    'trace': trace, 'contradiction_row': row,
                    'residual_target': target, 'remaining_variables': sorted(left)}
        if not left or target not in (0, len(left)):
            continue
        value = int(target == len(left))
        selected = sorted(left)
        trace.append({'row': row, 'forced_value': value, 'variables': selected})
        for variable in selected:
            assert state[variable] == -1
            state[variable] = value
            for affected in incident[variable]:
                unknown[affected].remove(variable)
                residual[affected] -= value
                queue.append(affected)
    return {'status': 'survives exact binary margin propagation', 'trace': trace,
            'forced_one_variables': [i for i, value in enumerate(state) if value == 1],
            'forced_zero_variables': [i for i, value in enumerate(state) if value == 0],
            'unassigned_variables': [i for i, value in enumerate(state) if value == -1]}


def check_rook_psd(code):
    adjacency = rows(code)
    k = [[3*int(i == j)-3*int(adjacency[i] >> j & 1)+1 for j in range(9)] for i in range(9)]
    assert all(sum(k[i][h]*k[h][j] for h in range(9)) == 9*k[i][j]
               for i in range(9) for j in range(9))
    assert all(sum(row) == 0 for row in k)
    # Symmetry and K^2=9K imply PSD. H=(K_R+2K_Z)/3.
    assert sum(k[i][i] for i in range(9)) == 36


def replay_propagation(domain, certificate):
    """Independently replay each forced step without the queue implementation."""
    state = [-1]*len(domain['signatures'])
    for step in certificate['trace']:
        equation = domain['equations'][step['row']]
        unknown = [i for i in equation['variables'] if state[i] == -1]
        residual = equation['target']-sum(state[i] == 1 for i in equation['variables'])
        assert unknown == step['variables'] and unknown
        if step['forced_value'] == 0:
            assert residual == 0
        else:
            assert step['forced_value'] == 1 and residual == len(unknown)
        for variable in unknown:
            state[variable] = step['forced_value']
    if certificate['status'].startswith('excluded'):
        equation = domain['equations'][certificate['contradiction_row']]
        unknown = [i for i in equation['variables'] if state[i] == -1]
        residual = equation['target']-sum(state[i] == 1 for i in equation['variables'])
        assert certificate['remaining_variables'] == unknown
        assert certificate['residual_target'] == residual
        assert residual < 0 or residual > len(unknown)
    else:
        assert certificate['status'] == 'survives exact binary margin propagation'
        assert certificate['forced_one_variables'] == [i for i, x in enumerate(state) if x == 1]
        assert certificate['forced_zero_variables'] == [i for i, x in enumerate(state) if x == 0]
        assert certificate['unassigned_variables'] == [i for i, x in enumerate(state) if x == -1]
        for equation in domain['equations']:
            count = sum(state[i] == -1 for i in equation['variables'])
            residual = equation['target']-sum(state[i] == 1 for i in equation['variables'])
            assert residual == 0 if count == 0 else 0 < residual < count


def generate(hall_path):
    hall = json.loads(hall_path.read_text())
    assert verify_hall(hall)['admitted_masks'] == 103
    admitted = set(hall['admitted_masks'])
    catalogue = catalogue_by_partitions()
    assert catalogue == catalogue_by_root_neighborhood()
    accepted = []
    for code in catalogue:
        check_rook_psd(code)
        if all(mask in admitted for mask in hall_masks(code)):
            accepted.append(code)
    assert len(accepted) == 89
    autos = automorphisms()
    remaining = set(accepted)
    cases = []
    while remaining:
        representative = min(remaining)
        transport = {}
        for permutation in autos:
            transport.setdefault(relabel(representative, permutation), permutation)
        assert set(transport) <= remaining
        remaining -= set(transport)
        domain = incidence_domain(representative)
        cases.append({'representative': representative,
                      'rook_edge_overlap': (representative & ROOT_CODE).bit_count(),
                      'orbit': [{'code': code, 'permutation': transport[code]} for code in sorted(transport)],
                      'domain': domain, 'propagation': propagate(domain)})
    return {'point_order': 'p=3*row+column', 'edge_order': [list(e) for e in EDGES],
            'all_rook_codes': catalogue, 'hall_survivor_codes': accepted, 'cases': cases}


def verify(record, hall_path):
    # Full reconstruction includes a second, independent catalogue generator.
    expected = generate(hall_path)
    assert record == expected
    cases = []
    for case in record['cases']:
        domain, propagation = case['domain'], case['propagation']
        replay_propagation(domain, propagation)
        cases.append({'representative': case['representative'], 'orbit_size': len(case['orbit']),
                      'rook_edge_overlap': case['rook_edge_overlap'],
                      'pair_allowed_signatures': len(domain['pair_allowed_signatures']),
                      'kernel_allowed_signatures': len(domain['signatures']),
                      'core_gram_rank': domain['core_gram_rank'],
                      'status': propagation['status'],
                      'unassigned_variables': len(propagation.get('unassigned_variables', [])),
                      'forced_one_variables': len(propagation.get('forced_one_variables', []))})
    return {'status': 'exact labelled-rook coverage and incidence propagation replay passed',
            'labelled_rook_graphs': 5040, 'Hall_survivors': 89,
            'root_automorphism_orbits': len(cases), 'cases': cases,
            'remaining_labelled_cases': sum(len(c['orbit']) for c in record['cases']
                                           if c['propagation']['status'].startswith('survives'))}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hall', type=Path, required=True)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        record = generate(args.hall)
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(verify(json.loads(args.certificate.read_text()), args.hall), indent=2))
