"""Complete rooted SRG model with exhaustive anchor-matching normalization.

The root and its k neighbors are mandatory, not a construction assumption.
For k=14 this covers every hypothetical SRG(99,14,1,2). No automorphism,
grid existence, root-grid bound, or seed quotient is imposed.
"""

import argparse
from collections import Counter
import gc
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import shutil
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

from root_full_caps_coverage import canonical_matching, partitions, replay as replay_coverage


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


def save(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.pending')
    temporary.write_text(json.dumps(record, indent=2)+'\n')
    temporary.replace(path)


def domain(degree):
    # The norm-14 strengthening is justified for degree14. Degree4 is the
    # explicit nine-rook control, which also satisfies every extra clause.
    # No arbitrary-degree model is exposed with this strengthening.
    assert degree in (4, 14)
    labels = [pair for pair in combinations(range(degree), 2) if pair[0] ^ 1 != pair[1]]
    outside = len(labels)
    assert outside == degree*(degree-2)//2
    assert 1+degree+outside == 1+degree*degree//2
    rows = [0]*(degree+1)
    rows[0] = sum(1 << (1+a) for a in range(degree))
    for a in range(degree):
        rows[1+a] = 1 | (1 << (1+(a ^ 1)))
    signatures = [(1+a, 1+b) for a, b in labels]
    gram = [[(degree-2)*int(i == j)+2-int(rows[i] >> j & 1)
             -(rows[i] & rows[j]).bit_count() for j in range(degree+1)]
            for i in range(degree+1)]
    actual = [[sum(i in signature and j in signature for signature in signatures)
               for j in range(degree+1)] for i in range(degree+1)]
    assert actual == gram
    need = []
    for pair, signature in zip(labels, signatures):
        mask = sum(1 << i for i in signature)
        mixed = [2-(row & mask).bit_count()-int(i in signature)
                 for i, row in enumerate(rows)]
        assert mixed == [0]+[2-int(a in pair)-int((a ^ 1) in pair)
                             for a in range(degree)]
        assert min(mixed) >= 0 and sum(mixed) == 2*(degree-2)
        need.append(mixed+[degree-2])
    edges = list(combinations(range(outside), 2))
    assert all(len(set(signatures[a]) & set(signatures[b])) <= 1
               and all(need[a][i] > 0 for i in signatures[b])
               and all(need[b][i] > 0 for i in signatures[a]) for a, b in edges)
    return rows, labels, signatures, need, edges


def forward_controls():
    cases = 0
    for paths in range(5):
        for direct, quota in product((False, True), range(3)):
            pool, cnf = IDPool(), CNF()
            primary = [pool.id(('primary', i)) for i in range(2*paths+int(direct))]
            terms = []
            for i in range(paths):
                path = pool.id(('path', i))
                cnf.append([-primary[2*i], -primary[2*i+1], path])
                terms.append(path)
            if direct:
                terms.append(primary[-1])
            if len(terms) > quota:
                cnf.extend(CardEnc.atmost(terms, quota, vpool=pool,
                                         encoding=EncType.seqcounter).clauses)
            with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
                for values in product((False, True), repeat=len(primary)):
                    actual = sum(values[2*i] and values[2*i+1] for i in range(paths))
                    actual += values[-1] if direct else 0
                    assumptions = [v if value else -v for v, value in zip(primary, values)]
                    assert solver.solve(assumptions=assumptions) == (actual <= quota)
                    cases += 1
    assert cases == 3069
    return {'status': 'exact pass', 'primary_assignments_checked': cases}


def broken_rook_clauses(degree, labels, variables):
    index = {pair: i for i, pair in enumerate(labels)}
    clauses, cells = [], []
    for first, second in combinations(range(degree//2), 2):
        cell = [index[(2*first+a, 2*second+b)] for a, b in product(range(2), repeat=2)]
        sides = [(cell[0], cell[1]), (cell[0], cell[2]),
                 (cell[1], cell[3]), (cell[2], cell[3])]
        literals = [variables[tuple(sorted(edge))] for edge in sides]
        assert len(set(literals)) == 4
        for missing in range(4):
            clauses.append([literal if i == missing else -literal
                            for i, literal in enumerate(literals)])
        cells.append({'axes': [first, second], 'vertices': cell, 'side_variables': literals})
    assert len(clauses) == 4*(degree//2)*(degree//2-1)//2
    # Only the four sides are constrained. Diagonal cell edges remain variables.
    return clauses, cells


def formula(degree):
    rows, labels, signatures, need, edges = domain(degree)
    outside = len(labels)
    pool, cnf = IDPool(), CNF()
    variables = {edge: pool.id(('edge', *edge)) for edge in edges}
    incident = [[] for _ in labels]
    for (a, b), variable in variables.items():
        incident[a].append((b, variable))
        incident[b].append((a, variable))
    counts = set()
    for t in range(outside):
        for i in range(degree+2):
            literals = [variable for s, variable in incident[t]
                        if i == degree+1 or i in signatures[s]]
            key = (tuple(literals), need[t][i])
            if key in counts:
                continue
            counts.add(key)
            assert 0 <= need[t][i] <= len(literals)
            cnf.extend(CardEnc.equals(literals, need[t][i], vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
    mixed_variables, mixed_clauses = cnf.nv, len(cnf.clauses)
    overlaps, path_count = Counter(), 0
    for a, b in edges:
        overlap = len(set(signatures[a]) & set(signatures[b]))
        overlaps[overlap] += 1
        terms = [variables[a, b]]
        centers = []
        for w in range(outside):
            if w in (a, b):
                continue
            first = variables[tuple(sorted((a, w)))]
            second = variables[tuple(sorted((b, w)))]
            path = pool.id(('path', a, b, w))
            cnf.append([-first, -second, path])
            terms.append(path)
            centers.append(w)
            path_count += 1
        assert centers == sorted(set(range(outside))-{a, b})
        cnf.extend(CardEnc.atmost(terms, 2-overlap, vpool=pool,
                                 encoding=EncType.seqcounter).clauses)
    expected_shared = degree*(degree-2)*(degree-3)//2
    assert overlaps == {0: len(edges)-expected_shared, 1: expected_shared}
    assert path_count == len(edges)*(outside-2)
    extra, cells = broken_rook_clauses(degree, labels, variables)
    cnf.extend(extra)
    record = {'degree': degree, 'vertices': 1+degree+outside,
              'core_vertices': degree+1, 'outside_vertices': outside,
              'edge_variables': len(variables), 'mixed_and_degree_counts': len(counts),
              'mixed_variables': mixed_variables, 'mixed_clauses': mixed_clauses,
              'path_variables': path_count, 'outside_pair_overlaps': dict(sorted(overlaps.items())),
              'outside_pair_caps': len(edges), 'broken_rook_clauses': len(extra),
              'broken_rook_cells': len(cells), 'variables': cnf.nv,
              'base_clauses': len(cnf.clauses), 'orbit_equalities': 0,
              'grid_existence_assumptions': 0, 'root_grid_bound_assumptions': 0,
              'diagonal_cell_edges_forbidden_unconditionally': 0}
    return cnf, variables, rows, labels, signatures, record


def anchor_units(degree, parts, labels, variables):
    assert tuple(parts) in set(partitions((degree-2)//2))
    index = {pair: i for i, pair in enumerate(labels)}
    units = []
    for a, b in canonical_matching(parts):
        first, second = index[0, 2+a], index[0, 2+b]
        units.append(variables[tuple(sorted((first, second)))])
    assert len(units) == len(set(units)) == (degree-2)//2
    return sorted(units)


def inspect(positive, degree, rows, labels, signatures, variables):
    offset = degree+1
    adjacency = rows[:]+[0]*len(labels)
    for a, signature in enumerate(signatures, offset):
        for b in signature:
            adjacency[a] |= 1 << b
            adjacency[b] |= 1 << a
    selected = []
    for (a, b), variable in variables.items():
        if variable in positive:
            adjacency[offset+a] |= 1 << (offset+b)
            adjacency[offset+b] |= 1 << (offset+a)
            selected.append([a, b])
    vertices = len(adjacency)
    assert vertices == 1+degree*degree//2
    assert all(row.bit_count() == degree and not (row >> i & 1)
               for i, row in enumerate(adjacency))
    assert all((adjacency[i] >> j & 1) == (adjacency[j] >> i & 1)
               for i, j in combinations(range(vertices), 2))
    assert all((adjacency[i] & adjacency[j]).bit_count()+int(adjacency[i] >> j & 1) == 2
               for i, j in combinations(range(vertices), 2))
    return {'vertices': vertices, 'degree': degree, 'all_pair_equations_exact': True,
            'outside_labels': [list(pair) for pair in labels], 'outside_edges': selected,
            'adjacency_lists': [[j for j in range(vertices) if row >> j & 1]
                                for row in adjacency]}


def rook_control():
    cnf, variables, rows, labels, signatures, metadata = formula(4)
    # Construct the nine-point rook graph directly from grid coordinates,
    # independently of the rooted equation system.
    coordinates = [(0, 0), (0, 1), (0, 2), (1, 0), (2, 0),
                   (1, 1), (2, 1), (1, 2), (2, 2)]
    grid = [[int(i != j and (p[0] == q[0] or p[1] == q[1]))
             for j, q in enumerate(coordinates)] for i, p in enumerate(coordinates)]
    assert all(sum(row) == 4 for row in grid)
    assert all(sum(grid[i][w]*grid[j][w] for w in range(9))+grid[i][j] == 2
               for i, j in combinations(range(9), 2))
    assert [[a for a in range(4) if grid[5+i][1+a]] for i in range(4)] == [list(e) for e in labels]
    assumptions = [variable if grid[5+a][5+b] else -variable
                   for (a, b), variable in variables.items()]
    units = anchor_units(4, (1,), labels, variables)
    cnf.extend([[unit] for unit in units])
    with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
        assert solver.solve(assumptions=assumptions)
        exact = inspect({v for v in solver.get_model() if v > 0}, 4, rows, labels, signatures, variables)
        assert exact['adjacency_lists'] == [[j for j in range(9) if grid[i][j]] for i in range(9)]
        assert solver.solve()
        inspect({v for v in solver.get_model() if v > 0}, 4, rows, labels, signatures, variables)
    return {'status': 'direct nine-rook control and free normalized solve both pass',
            'vertices': 9, 'pair_equations_checked': 36,
            'primary_edge_variables': len(variables), 'anchor_partition': [1],
            'broken_rook_clauses_checked': metadata['broken_rook_clauses']}


def write_case(base, target, variables, clauses, units):
    with base.open('rb') as source, target.open('wb') as destination:
        assert source.readline() == f'p cnf {variables} {clauses}\n'.encode()
        destination.write(f'p cnf {variables} {clauses+len(units)}\n'.encode())
        shutil.copyfileobj(source, destination)
        for unit in units:
            destination.write(f'{unit} 0\n'.encode())


def build(coverage_path, cnf_directory, manifest_path):
    started = time.monotonic()
    coverage = replay_coverage(coverage_path)
    assert coverage['axes'] == 6 and coverage['matching_count'] == 10395 and coverage['partitions'] == 11
    control = forward_controls()
    rook = rook_control()
    cnf, variables, rows, labels, signatures, metadata = formula(14)
    assert len(labels) == 84 and len(variables) == 3486
    assert metadata['outside_pair_overlaps'] == {0: 2562, 1: 924}
    assert metadata['broken_rook_clauses'] == 84
    cnf_directory.mkdir(parents=True, exist_ok=True)
    base = cnf_directory/'base.cnf'
    cnf.to_file(base)
    base_hash = digest(base)
    del cnf
    gc.collect()
    cases = []
    for case in coverage['cases']:
        units = anchor_units(14, tuple(case['partition']), labels, variables)
        path = cnf_directory/f'case-{case["index"]:02d}.cnf'
        write_case(base, path, metadata['variables'], metadata['base_clauses'], units)
        cases.append({**case, 'normalization_units': units, 'cnf_path': str(path),
                      'cnf_sha256': digest(path), 'variables': metadata['variables'],
                      'clauses': metadata['base_clauses']+len(units)})
    domain_record = {'core_rows': rows, 'labels': labels, 'signatures': signatures,
                     'edge_variables': [[a, b, variable] for (a, b), variable in variables.items()]}
    domain_hash = hashlib.sha256(json.dumps(domain_record, sort_keys=True,
                                          separators=(',', ':')).encode()).hexdigest()
    source_names = ['root_full_caps.py', 'root_full_caps_coverage.py', 'root_full_caps_batch.py',
                    'root_full_caps_certificate.py']
    record = {'status': 'unrestricted eleven-case model built; timed batch not launched',
              'scope': 'every hypothetical SRG(99,14,1,2), up to rooted coordinate labels',
              'metadata': metadata, 'forward_controls': control, 'rook_positive_control': rook,
              'domain_sha256': domain_hash, 'coverage_certificate': str(coverage_path),
              'coverage_sha256': digest(coverage_path),
              'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in source_names},
              'base_cnf': str(base), 'base_cnf_sha256': base_hash, 'cases': cases,
              'build_seconds': time.monotonic()-started}
    save(manifest_path, record)
    print(json.dumps({key: value for key, value in record.items()
                      if key not in ('source_hashes', 'cases')}), flush=True)
    print(json.dumps({'cases': cases}), flush=True)
    return record


def solve_case(manifest_path, index, seconds, proof_path, output):
    assert seconds > 0
    model = json.loads(manifest_path.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert digest(Path(model['coverage_certificate'])) == model['coverage_sha256']
    assert len(model['cases']) == 11 and [case['index'] for case in model['cases']] == list(range(11))
    case = model['cases'][index]
    assert digest(Path(case['cnf_path'])) == case['cnf_sha256']
    result = {'status': 'running', 'case_index': index, 'partition': case['partition'],
              'manifest_path': str(manifest_path), 'manifest_sha256': digest(manifest_path),
              'cnf_path': case['cnf_path'], 'cnf_sha256': case['cnf_sha256'],
              'solver': 'glucose4', 'proof_enabled': True,
              'requested_wall_budget_seconds': seconds,
              'budget_includes_cnf_parse_and_solver_bootstrap': True,
              'full_outside_caps': True, 'lazy_cuts': 0, 'completed_witness': None}
    save(output, result)
    print(json.dumps({'start': result}), flush=True)
    started = time.monotonic()
    cnf = CNF(from_file=case['cnf_path'])
    assert (cnf.nv, len(cnf.clauses)) == (case['variables'], case['clauses'])
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
            result['status'] = 'unknown at wall budget; this normalization case remains open'
        elif answer is False:
            proof = solver.get_proof()
            assert proof is not None
            proof_path.parent.mkdir(parents=True, exist_ok=True)
            with proof_path.open('w') as stream:
                for line in proof:
                    stream.write(line+'\n')
            result.update(status='solver UNSAT; saved proof requires independent verification',
                          proof_path=str(proof_path), proof_sha256=digest(proof_path),
                          proof_lines=len(proof))
        else:
            rows, labels, signatures, need, edges = domain(14)
            variables = {edge: i+1 for i, edge in enumerate(edges)}
            point = inspect({v for v in solver.get_model() if v > 0}, 14, rows, labels,
                            signatures, variables)
            result.update(status='exact99-vertex SRG candidate; independent validation required',
                          completed_witness=point)
    result['total_seconds'] = time.monotonic()-started
    save(output, result)
    print(json.dumps({key: value for key, value in result.items()
                      if key != 'completed_witness'}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    builder = commands.add_parser('build')
    builder.add_argument('--coverage', type=Path, required=True)
    builder.add_argument('--cnf-directory', type=Path, required=True)
    builder.add_argument('--manifest', type=Path, required=True)
    solver = commands.add_parser('solve')
    solver.add_argument('manifest', type=Path)
    solver.add_argument('--case', type=int, choices=range(11), required=True)
    solver.add_argument('--seconds', type=float, default=180)
    solver.add_argument('--proof', type=Path, required=True)
    solver.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'build':
        build(args.coverage, args.cnf_directory, args.manifest)
    else:
        solve_case(args.manifest, args.case, args.seconds, args.proof, args.output)
