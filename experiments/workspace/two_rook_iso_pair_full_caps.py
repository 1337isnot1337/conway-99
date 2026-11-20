"""Complete outside caps for two rook-isomorphic grids.

Construction/audit and proof-enabled solving are separate commands.
A SAT point must be a complete SRG candidate, not a partial edge point.
"""

import argparse
from collections import Counter
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

from two_rook_iso_pair_integer import inspect_point, data
from two_rook_iso_pair_integer_hall import build as hall_build
from two_rook_iso_pair_integer_hall_replay import read_artifact


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def forward_controls():
    cases = 0
    for paths in range(5):
        for direct, quota in product((False, True), range(3)):
            pool, cnf = IDPool(), CNF()
            primary = [pool.id(('x', i)) for i in range(2*paths+int(direct))]
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
    return {'status': 'exact pass', 'forward_path_cardinality_cases': cases}


def cap_plan(variables, signatures):
    candidates = [0]*81
    for a, b in variables:
        candidates[a] |= 1 << b
        candidates[b] |= 1 << a
    plan = []
    for a, b in combinations(range(81), 2):
        overlap = len(set(signatures[a]) & set(signatures[b]))
        common = candidates[a] & candidates[b]
        paths = []
        while common:
            bit = common & -common
            common -= bit
            w = bit.bit_length()-1
            paths.append((w, variables[tuple(sorted((a, w)))],
                           variables[tuple(sorted((b, w)))]))
        plan.append((a, b, overlap, variables.get((a, b)), paths))
    assert Counter(p[2] for p in plan) == {0: 2628, 1: 576, 2: 36}
    return plan


def compare_points(plan, variables, signatures, record):
    comparisons, violations = 0, []
    for point in record['points']:
        selected = {tuple(edge) for edge in point['selected_edges']}
        assert len(selected) == 486 and selected <= set(variables)
        positive = {variables[edge] for edge in selected}
        neighbors = [0]*81
        for a, b in selected:
            neighbors[a] |= 1 << b
            neighbors[b] |= 1 << a
        assert all(row.bit_count() == 12 for row in neighbors)
        bad = 0
        for a, b, overlap, direct, paths in plan:
            direct_value = (neighbors[a] & neighbors[b]).bit_count()+int((a, b) in selected)
            encoded_value = int(direct in positive)+sum(x in positive and y in positive for _, x, y in paths)
            assert direct_value == encoded_value
            if overlap == 2:
                assert direct_value == 0
            bad += direct_value > 2-overlap
            comparisons += 1
        assert bad == point['outside_cap_violations']
        violations.append(bad)
    assert len(record['points']) == 31 and all(violations)
    return {'status': 'all saved points independently match every planned cap',
            'points': len(record['points']), 'pair_comparisons': comparisons,
            'violating_caps_per_point': violations}


def build(seed_path, hall_path, points_path, cnf_path, manifest_path):
    control = forward_controls()
    seed = json.loads(seed_path.read_text())
    cnf, variables, rows, signatures, metadata, seen, admitted = hall_build(seed, seed_path, hall_path)
    initial_variables, initial_clauses = cnf.nv, len(cnf.clauses)
    plan = cap_plan(variables, signatures)
    comparison = compare_points(plan, variables, signatures, read_artifact(points_path))
    duplicate_clauses = {tuple(sorted((-x, -y))) for _, _, c, _, paths in plan if c == 2
                         for _, x, y in paths}
    assert len(duplicate_clauses) == 2772
    for clause in cnf.clauses:
        if len(clause) == 2:
            duplicate_clauses.discard(tuple(sorted(clause)))
    assert not duplicate_clauses

    pool = IDPool(start_from=cnf.nv+1)
    path_count = 0
    for a, b, overlap, direct, paths in plan:
        if overlap == 2:
            assert direct is None
            continue  # The exact zero cap is the checked duplicate packing.
        terms = [] if direct is None else [direct]
        for w, first, second in paths:
            path = pool.id(('path', a, b, w))
            cnf.append([-first, -second, path])
            terms.append(path)
            path_count += 1
        quota = 2-overlap
        if len(terms) > quota:
            cnf.extend(CardEnc.atmost(terms, quota, vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
    cnf_path.parent.mkdir(parents=True, exist_ok=True)
    cnf.to_file(cnf_path)
    source_names = ['two_rook_iso_pair_full_caps.py', 'two_rook_iso_pair_integer.py',
                    'two_rook_iso_pair_integer_lex.py', 'two_rook_iso_pair_integer_hall.py',
                    'two_rook_iso_pair_integer_hall_replay.py',
                    'two_rook_iso_completion.py', 'two_rook_tip_hall_audit.py']
    domain_record = {'core_rows': rows, 'signatures': signatures,
                     'edge_variables': [[a, b, v] for (a, b), v in variables.items()]}
    domain_hash = hashlib.sha256(json.dumps(domain_record, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    record = {'status': 'complete-cap CNF built and audited; not yet solved',
              'cnf_path': str(cnf_path), 'cnf_sha256': digest(cnf_path),
              'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in source_names},
              'domain_sha256': domain_hash, 'core_vertices': 18, 'outside_vertices': 81,
              'edge_variables': len(variables), 'initial_variables': initial_variables,
              'initial_clauses': initial_clauses, 'path_variables': path_count,
              'cardinality_auxiliaries': cnf.nv-initial_variables-path_count,
              'variables': cnf.nv, 'clauses': len(cnf.clauses),
              'all_outside_pairs': len(plan), 'explicit_pair_caps': 3204,
              'duplicate_zero_caps_checked': 36, 'orbit_equalities': 0,
              'tip_graph_assumptions': 0, 'forward_control': control,
              'saved_point_comparison': comparison,
              'hall_record': str(points_path), 'hall_record_sha256': digest(points_path),
              'initial_model_metadata': metadata}
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({k: v for k, v in record.items() if k not in
                     ('initial_model_metadata', 'source_hashes', 'saved_point_comparison')}), flush=True)
    print(json.dumps(comparison), flush=True)
    return record


def solve(manifest_path, seconds, proof_path, output):
    assert seconds > 0
    manifest = json.loads(manifest_path.read_text())
    for name, expected in manifest['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    cnf_path = Path(manifest['cnf_path'])
    assert digest(cnf_path) == manifest['cnf_sha256']
    result = {'status': 'running', 'manifest_path': str(manifest_path),
              'manifest_sha256': digest(manifest_path),
              'source_sha256': digest(Path(__file__)),
              'cnf_path': str(cnf_path), 'cnf_sha256': manifest['cnf_sha256'],
              'solver': 'glucose4', 'proof_enabled': True,
              'requested_wall_budget_seconds': seconds,
              'budget_includes_cnf_parse_and_solver_bootstrap': True,
              'lazy_cuts_added': 0, 'completed_witness': None}
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'start': result}), flush=True)
    started = time.monotonic()
    cnf = CNF(from_file=str(cnf_path))
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
            result['status'] = 'unknown at wall budget; no graph or exclusion obtained'
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
            core_rows, signatures, need, edges = data()
            variables = {edge: i+1 for i, edge in enumerate(edges)}
            positive = {variable for variable in solver.get_model() if variable > 0}
            point, cuts = inspect_point(positive, variables, core_rows, signatures)
            assert point['defective_pairs'] == 0 and not cuts
            adjacency = core_rows[:]+[0]*81
            for a, signature in enumerate(signatures, 18):
                for b in signature:
                    adjacency[a] |= 1 << b
                    adjacency[b] |= 1 << a
            for a, b in point['selected_edges']:
                adjacency[18+a] |= 1 << (18+b)
                adjacency[18+b] |= 1 << (18+a)
            point['adjacency_lists'] = [[j for j in range(99) if row >> j & 1]
                                        for row in adjacency]
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
    build_parser.add_argument('--seed', type=Path, required=True)
    build_parser.add_argument('--hall-certificate', type=Path, required=True)
    build_parser.add_argument('--points', type=Path, required=True)
    build_parser.add_argument('--cnf', type=Path, required=True)
    build_parser.add_argument('--manifest', type=Path, required=True)
    solve_parser = commands.add_parser('solve')
    solve_parser.add_argument('manifest', type=Path)
    solve_parser.add_argument('--seconds', type=float, default=180)
    solve_parser.add_argument('--proof', type=Path, required=True)
    solve_parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'build':
        build(args.seed, args.hall_certificate, args.points, args.cnf, args.manifest)
    else:
        solve(args.manifest, args.seconds, args.proof, args.output)
