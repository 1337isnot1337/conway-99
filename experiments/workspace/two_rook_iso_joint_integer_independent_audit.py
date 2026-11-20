"""Independent reduction and encoding audit of the full case48 integer model.

Constructs a dense core without importing its builder, checks every domain
and edge decision, captures the actual cardinality requests, reconstructs
packing clauses by a different loop, and exhausts conditional controls.
It binds the audited reduction to the exact CNF hash. This program does
not itself check a DRAT proof or assert full graph nonexistence.
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations, product
import json
from pathlib import Path

from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

import two_rook_iso_joint_integer as target
from two_rook_iso_joint_incidence import domain


MATCHING = (0, 5, 7, 8, 6, 1, 4, 2, 3)
EXPECTED_SOURCE = '6f62d78af4dfca5e141e0541b4572433a08b628f474e972288ce38a18032202e'
EXPECTED_CNF = 'c2c22ac69a93bae270d23906670b24cab87f270c6db579076a0b91560d3c4e1e'


def independent_domain():
    matrix = [[0]*27 for _ in range(27)]
    for i, j in combinations(range(27), 2):
        a, x = divmod(i, 9)
        b, y = divmod(j, 9)
        if a == b:
            adjacent = x//3 == y//3 or x % 3 == y % 3
        elif a == 0:
            adjacent = x == y
        else:
            assert (a, b) == (1, 2)
            adjacent = MATCHING[x] == y
        matrix[i][j] = matrix[j][i] = int(adjacent)
    assert all(sum(row) == 6 for row in matrix)
    gram = [[12*int(i == j)+2-matrix[i][j]
             -sum(matrix[i][k]*matrix[k][j] for k in range(27))
             for j in range(27)] for i in range(27)]
    signatures, needs = [], []
    for x, y, z in product(range(9), repeat=3):
        sites = (x, 9+y, 18+z)
        if any(gram[i][j] <= 0 for i, j in combinations(sites, 2)):
            continue
        need = [2-int(i in sites)-sum(matrix[i][j] for j in sites)
                for i in range(27)]
        if any(value < 0 for value in need):
            continue
        signatures.append(sites)
        needs.append(need+[11])
    masks = [sum(1 << i for i in s) for s in signatures]
    edges = []
    for a, b in combinations(range(len(signatures)), 2):
        if (masks[a] & masks[b]).bit_count()+1 > 2:
            continue
        if any(needs[a][i] == 0 for i in signatures[b]):
            continue
        if any(needs[b][i] == 0 for i in signatures[a]):
            continue
        edges.append((a, b))
    return matrix, gram, signatures, needs, masks, edges


def conditional_controls():
    # Exhaust every activation and literal assignment, including the
    # actual degree quota11 and cases where quota exceeds the supply.
    settings = [(count, quota) for count in range(9) for quota in range(count+2)]
    settings += [(11, 11), (12, 11), (12, 12), (12, 13)]
    total = 0
    for count, quota in settings:
        pool = IDPool()
        selected = pool.id(('selected', count, quota))
        literals = [pool.id(('literal', i)) for i in range(count)]
        cnf = CNF()
        cnf.extend([[-literal, selected] for literal in literals])
        target.conditional_count(cnf, pool, literals, quota, selected)
        with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
            for values in product((0, 1), repeat=count):
                for active in (0, 1):
                    assumptions = [selected if active else -selected]
                    assumptions += [literal if value else -literal
                                    for literal, value in zip(literals, values)]
                    expected = sum(values) == quota*active
                    assert solver.solve(assumptions=assumptions) == expected
                    total += 1
    return {'settings': len(settings), 'complete_boolean_assignments': total}


def audit(cnf_path):
    source_hash = hashlib.sha256(Path(target.__file__).read_bytes()).hexdigest()
    assert source_hash == EXPECTED_SOURCE
    matrix, gram, signatures, needs, masks, edge_pairs = independent_domain()
    assert len(signatures) == 168 and len(edge_pairs) == 9846
    supplied_rows, supplied_gram, supplied_signatures, supplied_needs = domain()
    expected_rows = [sum(bit << j for j, bit in enumerate(row)) for row in matrix]
    assert supplied_rows == expected_rows
    assert supplied_gram == gram and supplied_signatures == signatures and supplied_needs == needs

    original_card = target.CardEnc
    original_conditional = target.conditional_count
    requests, conditional_requests = [], []

    class Capture:
        @staticmethod
        def equals(literals, quota, **kwargs):
            requests.append(('equals', tuple(literals), quota))
            return original_card.equals(literals, quota, **kwargs)

        @staticmethod
        def atmost(literals, quota, **kwargs):
            requests.append(('atmost', tuple(literals), quota))
            return original_card.atmost(literals, quota, **kwargs)

        @staticmethod
        def atleast(literals, quota, **kwargs):
            requests.append(('atleast', tuple(literals), quota))
            return original_card.atleast(literals, quota, **kwargs)

    def capture_conditional(cnf, pool, literals, quota, selected):
        conditional_requests.append((selected, tuple(literals), quota))
        return original_conditional(cnf, pool, literals, quota, selected)

    target.CardEnc = Capture
    target.conditional_count = capture_conditional
    try:
        cnf, z, variables, rows, sites, metadata = target.build()
    finally:
        target.CardEnc = original_card
        target.conditional_count = original_conditional
    assert rows == expected_rows and sites == signatures
    assert list(variables) == edge_pairs
    assert len(set(z+list(variables.values()))) == 168+9846
    assert set(z+list(variables.values())) == set(range(1, 168+9846+1))

    expected_requests = []
    seen = set()
    for i in range(27):
        for j in range(i, 27):
            literals = tuple(z[s] for s, signature in enumerate(signatures)
                             if i in signature and j in signature)
            key = (literals, gram[i][j])
            if key not in seen:
                expected_requests.append(('equals', literals, gram[i][j]))
                seen.add(key)
    expected_requests.append(('equals', tuple(z), 72))
    gram_requests = len(expected_requests)

    incident = [[] for _ in signatures]
    activation = []
    for (a, b), variable in variables.items():
        incident[a].append((b, variable))
        incident[b].append((a, variable))
        activation.extend([[-variable, z[a]], [-variable, z[b]]])
    assert cnf.clauses[:len(activation)] == activation
    expected_conditional = []
    too_small = set()
    seen = set()
    for t in range(168):
        for i in range(28):
            literals = tuple(variable for s, variable in incident[t]
                             if i == 27 or i in signatures[s])
            quota = needs[t][i]
            key = (z[t], literals, quota)
            if key in seen:
                continue
            seen.add(key)
            expected_conditional.append(key)
            if quota > len(literals):
                too_small.add(z[t])
                continue
            if quota < len(literals):
                expected_requests.append(('atmost', literals, quota))
            if quota:
                expected_requests.append(('atleast', literals, quota))
    assert conditional_requests == expected_conditional
    assert requests == expected_requests
    unit_literals = {clause[0] for clause in cnf.clauses if len(clause) == 1}
    assert all(-selected in unit_literals for selected in too_small)

    # Independent organization: choose the two neighbors first and test
    # their signature intersection, rather than first choosing a core pair.
    packing = set()
    for neighbors in incident:
        for (a, va), (b, vb) in combinations(neighbors, 2):
            if (masks[a] & masks[b]).bit_count() >= 2:
                packing.add(tuple(sorted((-va, -vb))))
    assert len(packing) == 62692
    assert cnf.clauses[-len(packing):] == [list(clause) for clause in sorted(packing)]
    cnf.to_file(cnf_path)
    cnf_hash = hashlib.sha256(cnf_path.read_bytes()).hexdigest()
    assert cnf_hash == EXPECTED_CNF
    controls = conditional_controls()
    return {
        'status': 'independent domain, mathematical reduction, and CNF binding pass',
        'source_sha256': source_hash, 'cnf_sha256': cnf_hash,
        'core_vertices': 27, 'candidate_signatures': len(signatures),
        'signature_selection_variables': len(z), 'candidate_edge_variables': len(variables),
        'activation_clauses': len(activation), 'gram_cardinality_requests': gram_requests,
        'conditional_cardinality_requests': len(conditional_requests),
        'conditional_quotas': sorted({quota for _, _, quota in conditional_requests}),
        'conditional_request_calls': dict(Counter(kind for kind, _, _ in requests)),
        'packing_clauses_independently_reconstructed': len(packing),
        'total_cnf_variables': cnf.nv, 'total_cnf_clauses': len(cnf.clauses),
        'conditional_controls': controls,
        'fixed_incidence_witness_used': False, 'orbit_identifications_used': False,
        'lazy_cuts_used_in_audited_cnf': False,
        'scope': 'audits the necessary full case48 integer model; DRAT replay is a separate required check',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cnf', type=Path, default=Path(
        '/tmp/conway-two-rook-iso-joint-integer-independent.cnf'))
    parser.add_argument('--output', type=Path)
    parser.add_argument('--verify', type=Path)
    args = parser.parse_args()
    result = audit(args.cnf)
    if args.verify:
        assert json.loads(args.verify.read_text()) == result
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result), flush=True)
