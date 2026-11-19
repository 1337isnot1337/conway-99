"""Complete binary edge model for the surviving complementary-rook a=0 design.

The incidence census and its two Farkas exclusions are replayed first.
The remaining 72-column design is fixed, but no edge symmetry is imposed.
Every outside common-neighbor cap is encoded before solving.
"""

import argparse
from collections import Counter
import gc
import hashlib
from itertools import combinations
import json
from pathlib import Path
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

from two_rook_iso_completion import allowed_edges, check_incidence
from two_rook_iso_pair_full_caps import forward_controls
from two_rook_pair_structural import core, run as replay_structural, sites, tip_cycle_types


CERTIFICATE_HASH = '2842d990148ed3968804d8355bcc0284e81ad66c298e02dfbedf373deff9d0ec'
SIGNATURE_HASH = '7d66efd0001a6debfae045fe4cce71c6f9af7ca875167123b7188defa95890f0'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


def domain(certificate_path, replay=True):
    assert digest(certificate_path) == CERTIFICATE_HASH
    checked = replay_structural(certificate_path) if replay else None
    if checked is not None:
        assert checked['a0_designs'] == 16 and checked['exactly_excluded_a0_designs'] == 14
    certificate = json.loads(certificate_path.read_text())
    assert [i for i, case in enumerate(certificate['cases']) if 'ray' not in case] == [2]
    case = certificate['cases'][2]
    design = [tuple(signature) for signature in case['signatures']]
    assert len(design) == len(set(design)) == 72 and design == sorted(design)
    assert case['orbit_size'] == 2 and 'rational_point' in case
    assert tip_cycle_types(design) == [[1, 8]]*9
    signatures = [sites(signature) for signature in design]
    signature_hash = hashlib.sha256(json.dumps(signatures, separators=(',', ':')).encode()).hexdigest()
    assert signature_hash == SIGNATURE_HASH
    matrix = core()
    rows = [sum(value << j for j, value in enumerate(row)) for row in matrix]
    need = check_incidence(rows, signatures)
    dense_need = [[2-sum(matrix[i][j]+int(i == j) for j in signature)
                   for i in range(27)]+[11] for signature in signatures]
    assert need == dense_need
    assert all(row.bit_count() == 6 for row in rows)
    edges = allowed_edges(signatures, need)
    assert len(edges) == 1764
    assert case['quotient']['eligible_edges'] == len(edges)
    return rows, signatures, need, edges, checked


def cap_plan(variables, signatures):
    adjacency = [0]*72
    for a, b in variables:
        adjacency[a] |= 1 << b
        adjacency[b] |= 1 << a
    plan = []
    for a, b in combinations(range(72), 2):
        overlap = len(set(signatures[a]) & set(signatures[b]))
        common = adjacency[a] & adjacency[b]
        paths = []
        while common:
            bit = common & -common
            common -= bit
            w = bit.bit_length()-1
            assert w not in (a, b)
            paths.append((w, variables[tuple(sorted((a, w)))],
                          variables[tuple(sorted((b, w)))]))
        expected = [w for w in range(72)
                    if tuple(sorted((a, w))) in variables
                    and tuple(sorted((b, w))) in variables]
        assert [w for w, _, _ in paths] == expected
        direct = variables.get((a, b))
        if overlap == 2:
            assert direct is None
        plan.append((a, b, overlap, direct, paths))
    assert Counter(item[2] for item in plan) == {0: 1836, 1: 684, 2: 36}
    return plan


def build(certificate_path, cnf_path, manifest_path):
    started = time.monotonic()
    control = forward_controls()
    rows, signatures, need, edges, checked = domain(certificate_path)
    pool, cnf = IDPool(), CNF()
    variables = {edge: pool.id(('edge', *edge)) for edge in edges}
    incident = [[] for _ in signatures]
    for (a, b), variable in variables.items():
        incident[a].append((b, variable))
        incident[b].append((a, variable))
    counts = set()
    for t in range(72):
        for i in range(28):
            literals = [variable for s, variable in incident[t]
                        if i == 27 or i in signatures[s]]
            key = (tuple(literals), need[t][i])
            if key in counts:
                continue
            counts.add(key)
            assert 0 <= need[t][i] <= len(literals)
            cnf.extend(CardEnc.equals(literals, need[t][i], vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
    base_variables, base_clauses = cnf.nv, len(cnf.clauses)
    plan = cap_plan(variables, signatures)
    packing = {tuple(sorted((-first, -second)))
               for _, _, overlap, _, paths in plan if overlap == 2
               for _, first, second in paths}
    cnf.extend([list(clause) for clause in sorted(packing)])
    paths_added = 0
    for a, b, overlap, direct, paths in plan:
        if overlap == 2:
            continue
        terms = [] if direct is None else [direct]
        for w, first, second in paths:
            path = pool.id(('path', a, b, w))
            cnf.append([-first, -second, path])
            terms.append(path)
            paths_added += 1
        if len(terms) > 2-overlap:
            cnf.extend(CardEnc.atmost(terms, 2-overlap, vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
    cnf_path.parent.mkdir(parents=True, exist_ok=True)
    cnf.to_file(cnf_path)
    sources = ['two_rook_a0_fixed_completion.py', 'two_rook_pair_structural.py',
               'two_rook_iso_completion.py', 'two_rook_iso_pair_full_caps.py']
    exact_domain = {'core_rows': rows, 'signatures': signatures, 'mixed_need': need,
                    'edges': [[a, b, variable] for (a, b), variable in variables.items()]}
    domain_hash = hashlib.sha256(json.dumps(exact_domain, sort_keys=True,
                                           separators=(',', ':')).encode()).hexdigest()
    record = {'status': 'complete fixed-incidence CNF built and audited; not yet solved',
              'core_vertices': 27, 'outside_vertices': 72, 'incidence_case_index': 2,
              'equivalent_incidence_designs': 2, 'selected_signature_sha256': SIGNATURE_HASH,
              'structural_certificate': str(certificate_path),
              'structural_certificate_sha256': digest(certificate_path),
              'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in sources},
              'cnf_path': str(cnf_path), 'cnf_sha256': digest(cnf_path),
              'domain_sha256': domain_hash, 'edge_variables': len(variables),
              'distinct_mixed_and_degree_counts': len(counts),
              'base_variables': base_variables, 'base_clauses': base_clauses,
              'outside_pairs': len(plan), 'path_variables': paths_added,
              'duplicate_zero_caps': 36, 'packing_clauses': len(packing),
              'variables': cnf.nv, 'clauses': len(cnf.clauses),
              'orbit_equalities': 0, 'symmetry_clauses': 0, 'lazy_cuts': 0,
              'full_outside_caps': True, 'controls': control,
              'exact_domain_checks': 'all Gram entries, dense mixed needs, all2556 path domains',
              'structural_replay': checked, 'build_seconds': time.monotonic()-started}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({key: value for key, value in record.items()
                      if key not in ('source_hashes', 'structural_replay')}), flush=True)
    return record


def inspect(positive, rows, signatures, edges):
    adjacency = rows[:]+[0]*72
    for a, signature in enumerate(signatures, 27):
        for b in signature:
            adjacency[a] |= 1 << b
            adjacency[b] |= 1 << a
    selected = []
    for variable, (a, b) in enumerate(edges, 1):
        if variable in positive:
            adjacency[27+a] |= 1 << (27+b)
            adjacency[27+b] |= 1 << (27+a)
            selected.append([a, b])
    assert len(selected) == 396
    assert all(row.bit_count() == 14 for row in adjacency)
    assert all(not (adjacency[i] >> i & 1) for i in range(99))
    assert all((adjacency[i] >> j & 1) == (adjacency[j] >> i & 1)
               for i, j in combinations(range(99), 2))
    counts = Counter((adjacency[i] & adjacency[j]).bit_count()+int(adjacency[i] >> j & 1)
                     for i, j in combinations(range(99), 2))
    assert counts == {2: 4851}
    return {'selected_edges': selected, 'selected_signatures': [list(s) for s in signatures],
            'degree_check': 'all99 degrees14', 'common_neighbor_check': 'all4851 pairs exact',
            'adjacency_lists': [[j for j in range(99) if row >> j & 1] for row in adjacency]}


def solve(manifest_path, seconds, proof_path, output):
    assert seconds > 0
    model = json.loads(manifest_path.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    cnf_path, certificate_path = Path(model['cnf_path']), Path(model['structural_certificate'])
    assert digest(cnf_path) == model['cnf_sha256']
    assert digest(certificate_path) == model['structural_certificate_sha256']
    result = {'status': 'running', 'manifest_path': str(manifest_path),
              'manifest_sha256': digest(manifest_path), 'cnf_path': str(cnf_path),
              'cnf_sha256': model['cnf_sha256'], 'source_sha256': digest(Path(__file__)),
              'solver': 'glucose4', 'proof_enabled': True, 'full_outside_caps': True,
              'requested_wall_budget_seconds': seconds,
              'budget_includes_cnf_parse_and_solver_bootstrap': True,
              'symmetry_clauses': 0, 'lazy_cuts': 0, 'completed_witness': None}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'start': result}), flush=True)
    started = time.monotonic()
    cnf = CNF(from_file=str(cnf_path))
    assert (cnf.nv, len(cnf.clauses)) == (model['variables'], model['clauses'])
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
        del cnf
        gc.collect()
        remaining = seconds-(time.monotonic()-started)
        print(json.dumps({'solver_ready_seconds': time.monotonic()-started,
                          'remaining_seconds': max(0, remaining)}), flush=True)
        if remaining > 0:
            timer = Timer(remaining, solver.interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
        else:
            answer = None
        result['solve_return_seconds'] = time.monotonic()-started
        result['solver_statistics'] = solver.accum_stats()
        if answer is None:
            result['status'] = 'unknown at wall budget; fixed incidence remains unresolved'
        elif answer is False:
            proof = solver.get_proof()
            assert proof is not None
            proof_path.parent.mkdir(parents=True, exist_ok=True)
            with proof_path.open('w') as stream:
                for line in proof:
                    stream.write(line+'\n')
            result.update(status='solver UNSAT; saved proof awaits independent verification',
                          proof_path=str(proof_path), proof_sha256=digest(proof_path),
                          proof_lines=len(proof))
        else:
            rows, signatures, need, edges, _ = domain(certificate_path, replay=False)
            point = inspect({v for v in solver.get_model() if v > 0}, rows, signatures, edges)
            result.update(status='exact99-vertex SRG candidate; independent validation required',
                          completed_witness=point)
    result['total_seconds'] = time.monotonic()-started
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key != 'completed_witness'}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    build_parser = commands.add_parser('build')
    build_parser.add_argument('--structural-certificate', type=Path, required=True)
    build_parser.add_argument('--cnf', type=Path, required=True)
    build_parser.add_argument('--manifest', type=Path, required=True)
    solve_parser = commands.add_parser('solve')
    solve_parser.add_argument('manifest', type=Path)
    solve_parser.add_argument('--seconds', type=float, default=120)
    solve_parser.add_argument('--proof', type=Path, required=True)
    solve_parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'build':
        build(args.structural_certificate, args.cnf, args.manifest)
    else:
        solve(args.manifest, args.seconds, args.proof, args.output)
