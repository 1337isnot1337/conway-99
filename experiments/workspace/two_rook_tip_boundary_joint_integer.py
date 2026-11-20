"""Joint incidence and edge models for the two surviving rook-tip cores.

Both complete signature domains are supplied by a separately replayed
finite boundary census. No fixed incidence or graph symmetry is imposed.
Construction/audit and proof-enabled bounded solving are separate.
"""

import argparse
import gc
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

from two_rook_iso_completion import allowed_edges, gram
from two_rook_iso_joint_integer import conditional_count, inspect_point
from two_rook_tip_rook_boundary_export import generate as replay_export


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


def controls():
    cases = 0
    sizes_quotas = [(size, quota) for size in range(6) for quota in (0, 1, 2, 11)]
    sizes_quotas += [(size, 11) for size in (10, 11, 12)]
    for size, quota in sizes_quotas:
        pool, cnf = IDPool(), CNF()
        selected = pool.id('selected')
        literals = [pool.id(('edge', i)) for i in range(size)]
        cnf.extend([[-literal, selected] for literal in literals])
        conditional_count(cnf, pool, literals, quota, selected)
        with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
            for chosen, values in product((False, True), product((False, True), repeat=size)):
                assumptions = [selected if chosen else -selected]
                assumptions += [literal if value else -literal
                                for literal, value in zip(literals, values)]
                assert solver.solve(assumptions=assumptions) == (sum(values) == quota*chosen)
                cases += 1
    assert cases == 14840
    return {'status': 'exact pass', 'conditional_cardinality_assignments': cases,
            'quotas_tested': [0, 1, 2, 11]}


def load_domain(domain_path, boundary_path, hall_path, representative):
    exported = json.loads(domain_path.read_text())
    assert exported == replay_export(boundary_path, hall_path)
    case = next(c for c in exported['cases'] if c['representative'] == representative)
    rows, G = case['core_rows'], case['core_gram']
    signatures = [tuple(sites) for sites in case['core_signatures']]
    assert len(rows) == 27 and all(row.bit_count() == 6 for row in rows)
    assert G == gram(rows)
    assert len(signatures) == len(set(signatures))
    assert all(len(sites) == 3 and {i//9 for i in sites} == {0, 1, 2}
               for sites in signatures)
    need = []
    for sites in signatures:
        mask = sum(1 << i for i in sites)
        values = [2-(row & mask).bit_count()-int(i in sites)
                  for i, row in enumerate(rows)]
        assert min(values) >= 0 and sum(values) == 33
        need.append(values+[11])
    assert [row[:-1] for row in need] == case['mixed_need']
    assert case['outside_degree_if_selected'] == 11 and case['selected_vertex_count'] == 72
    expected = {3679836361: (188, 12010), 3943553752: (252, 20934)}
    assert representative in expected and len(signatures) == expected[representative][0]
    edges = allowed_edges(signatures, need)
    assert len(edges) == expected[representative][1]
    return rows, G, signatures, need, edges, case


def build(domain_path, boundary_path, hall_path, representative, cnf_path, manifest_path):
    started = time.monotonic()
    control = controls()
    rows, G, signatures, need, edges, case = load_domain(
        domain_path, boundary_path, hall_path, representative)
    pool, cnf = IDPool(), CNF()
    selected = [pool.id(('selected', s)) for s in range(len(signatures))]
    edge_variables = {edge: pool.id(('edge', *edge)) for edge in edges}
    incident = [[] for _ in signatures]
    for (a, b), variable in edge_variables.items():
        cnf.extend([[-variable, selected[a]], [-variable, selected[b]]])
        incident[a].append((b, variable))
        incident[b].append((a, variable))

    gram_seen = set()
    for i in range(27):
        for j in range(i, 27):
            literals = [selected[s] for s, sites in enumerate(signatures)
                        if i in sites and j in sites]
            key = (tuple(literals), G[i][j])
            if key in gram_seen:
                continue
            gram_seen.add(key)
            assert 0 <= G[i][j] <= len(literals)
            cnf.extend(CardEnc.equals(literals, G[i][j], vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
    cnf.extend(CardEnc.equals(selected, 72, vpool=pool,
                             encoding=EncType.seqcounter).clauses)
    for s in case['forced_one_indices']:
        cnf.append([selected[s]])
    for s in case['forced_zero_indices']:
        cnf.append([-selected[s]])

    mixed_seen = set()
    for t in range(len(signatures)):
        for i in range(28):
            literals = [variable for s, variable in incident[t]
                        if i == 27 or i in signatures[s]]
            key = (selected[t], tuple(literals), need[t][i])
            if key in mixed_seen:
                continue
            mixed_seen.add(key)
            conditional_count(cnf, pool, literals, need[t][i], selected[t])

    neighbor_variables = [dict(neighbors) for neighbors in incident]
    packing = set()
    for i, j in combinations(range(27), 2):
        family = [s for s, sites in enumerate(signatures) if i in sites and j in sites]
        if len(family) < 2:
            continue
        for t in range(len(signatures)):
            literals = [neighbor_variables[t][s] for s in family
                        if s in neighbor_variables[t]]
            for first, second in combinations(literals, 2):
                packing.add(tuple(sorted((-first, -second))))
    cnf.extend([list(clause) for clause in sorted(packing)])
    cnf_path.parent.mkdir(parents=True, exist_ok=True)
    cnf.to_file(cnf_path)
    sources = ['two_rook_tip_boundary_joint_integer.py', 'two_rook_iso_joint_integer.py',
               'two_rook_iso_completion.py', 'two_rook_tip_rook_boundary_export.py',
               'two_rook_tip_rook_boundary.py', 'two_rook_tip_hall_audit.py']
    domain_record = {'core_rows': rows, 'gram': G, 'signatures': signatures,
                     'mixed_need': need,
                     'edge_variables': [[a, b, v] for (a, b), v in edge_variables.items()]}
    domain_hash = hashlib.sha256(json.dumps(domain_record, sort_keys=True,
                                          separators=(',', ':')).encode()).hexdigest()
    record = {'status': 'joint integer model built and audited; not yet solved',
              'representative': representative, 'labelled_orbit_size': case['labelled_orbit_size'],
              'cnf_path': str(cnf_path), 'cnf_sha256': digest(cnf_path),
              'domain_path': str(domain_path), 'domain_file_sha256': digest(domain_path),
              'boundary_certificate': str(boundary_path), 'boundary_sha256': digest(boundary_path),
              'hall_certificate': str(hall_path), 'hall_sha256': digest(hall_path),
              'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in sources},
              'domain_sha256': domain_hash, 'core_vertices': 27, 'selected_outside_vertices': 72,
              'signature_variables': len(selected), 'edge_variables': len(edge_variables),
              'variables': cnf.nv, 'clauses': len(cnf.clauses),
              'activation_clauses': 2*len(edge_variables),
              'distinct_gram_counts': len(gram_seen), 'population_count': 1,
              'mixed_and_degree_counts': len(mixed_seen), 'packing_clauses': len(packing),
              'derived_positive_units': len(case['forced_one_indices']),
              'derived_negative_units': len(case['forced_zero_indices']),
              'orbit_equalities': 0, 'fixed_incidence_witnesses': 0,
              'full_outside_caps_imposed': False,
              'conditional_control': control, 'build_seconds': time.monotonic()-started}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({key: value for key, value in record.items()
                      if key != 'source_hashes'}), flush=True)
    return record


def solve(manifest_path, seconds, proof_path, output):
    assert seconds > 0
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    for path_key, hash_key in [('cnf_path', 'cnf_sha256'),
                               ('domain_path', 'domain_file_sha256'),
                               ('boundary_certificate', 'boundary_sha256'),
                               ('hall_certificate', 'hall_sha256')]:
        assert digest(Path(manifest[path_key])) == manifest[hash_key]
    result = {'status': 'running', 'representative': manifest['representative'],
              'manifest_path': str(manifest_path), 'manifest_sha256': digest(manifest_path),
              'source_sha256': digest(Path(__file__)), 'cnf_path': manifest['cnf_path'],
              'cnf_sha256': manifest['cnf_sha256'], 'solver': 'glucose4',
              'proof_enabled': True, 'requested_wall_budget_seconds': seconds,
              'budget_includes_cnf_parse_and_solver_bootstrap': True,
              'orbit_equalities': 0, 'fixed_incidence_witnesses': 0,
              'lazy_cuts_added': 0, 'binary_point': None, 'completed_witness': None}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'start': result}), flush=True)
    started = time.monotonic()
    cnf = CNF(from_file=manifest['cnf_path'])
    assert (cnf.nv, len(cnf.clauses)) == (manifest['variables'], manifest['clauses'])
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
            result['status'] = 'unknown at wall budget; no point or exclusion obtained'
        elif answer is False:
            proof = solver.get_proof()
            assert proof is not None
            proof_path.parent.mkdir(parents=True, exist_ok=True)
            with proof_path.open('w') as stream:
                for line in proof:
                    stream.write(line+'\n')
            result.update(status='solver UNSAT; proof saved, independent verification pending',
                          proof_path=str(proof_path), proof_sha256=digest(proof_path),
                          proof_lines=len(proof))
        else:
            exported = json.loads(Path(manifest['domain_path']).read_text())
            case = next(c for c in exported['cases']
                        if c['representative'] == manifest['representative'])
            rows = case['core_rows']
            signatures = [tuple(sites) for sites in case['core_signatures']]
            need = [values+[11] for values in case['mixed_need']]
            edges = allowed_edges(signatures, need)
            selected = list(range(1, len(signatures)+1))
            variables = {edge: len(selected)+i+1 for i, edge in enumerate(edges)}
            positive = {variable for variable in solver.get_model() if variable > 0}
            point, violations = inspect_point(positive, selected, variables, rows, signatures)
            result['binary_point'] = point
            result['cap_violation_witnesses'] = violations
            if point['defective_pairs']:
                result['status'] = 'partial binary point; full graph completion unresolved'
            else:
                assert not violations
                result.update(status='exact99-vertex SRG candidate; independent validation required',
                              completed_witness=point)
    result['total_seconds'] = time.monotonic()-started
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('binary_point', 'completed_witness',
                                     'cap_violation_witnesses')}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    build_parser = commands.add_parser('build')
    build_parser.add_argument('--domains', type=Path, required=True)
    build_parser.add_argument('--boundary-certificate', type=Path, required=True)
    build_parser.add_argument('--hall-certificate', type=Path, required=True)
    build_parser.add_argument('--representative', type=int, required=True)
    build_parser.add_argument('--cnf', type=Path, required=True)
    build_parser.add_argument('--manifest', type=Path, required=True)
    solve_parser = commands.add_parser('solve')
    solve_parser.add_argument('manifest', type=Path)
    solve_parser.add_argument('--seconds', type=float, default=200)
    solve_parser.add_argument('--proof', type=Path, required=True)
    solve_parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'build':
        build(args.domains, args.boundary_certificate, args.hall_certificate,
              args.representative, args.cnf, args.manifest)
    else:
        solve(args.manifest, args.seconds, args.proof, args.output)
