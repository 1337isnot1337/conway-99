"""Duplicate-label lex continuation of the two-grid edge completion search.

Only adjacency vectors to the nine fixed tips are ordered. No graph
automorphism or ordering of the full outside-neighborhood rows is assumed.
"""

import argparse
import hashlib
from itertools import product
import json
from pathlib import Path
from threading import Timer
import time

from pysat.solvers import Solver

from two_rook_iso_pair_integer import build as base_build, inspect_point, cut_clause


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def lex_controls():
    cases = 0
    for size in range(10):
        for pairs in product(((0, 0), (1, 0), (0, 1)), repeat=size):
            first = tuple(p[0] for p in pairs)
            second = tuple(p[1] for p in pairs)
            clauses = all(not second[j] or any(first[:j]) for j in range(size))
            assert clauses == (first >= second)
            cases += 1
    return {'disjoint_tip_vector_cases': cases, 'status': 'exact pass'}


def build(seed, seed_path):
    cnf, variables, rows, signatures, metadata = base_build()
    assert metadata['source_sha256'] == seed['metadata']['source_sha256']
    clauses = []
    for a in range(9, 81, 2):
        b = a+1
        assert signatures[a] == signatures[b]
        earlier = []
        for tip in range(9):
            first, second = (tip, a), (tip, b)
            assert (first in variables) == (second in variables)
            if second in variables:
                clauses.append([-variables[second], *earlier])
                earlier.append(variables[first])
    assert len(clauses) == 252
    cnf.extend(clauses)
    initial_cuts = seed['necessary_cuts']
    seen = set()
    for record in initial_cuts:
        clause = cut_clause(record, signatures, variables)
        assert tuple(clause) not in seen
        seen.add(tuple(clause))
        cnf.append(clause)
    metadata['base_source_sha256'] = metadata.pop('source_sha256')
    metadata.update(source_sha256=digest(Path(__file__)), lex_clauses=len(clauses),
                    lex_coordinates='the9 fixed diagonal tips only',
                    lex_control=lex_controls(), initial_cut_count=len(initial_cuts),
                    seed_record=str(seed_path), seed_record_sha256=digest(seed_path),
                    clauses=len(cnf.clauses))
    return cnf, variables, rows, signatures, metadata, seen


def canonical_phases(seed, variables):
    """A starting phase preference, not an additional constraint."""
    edges = {tuple(edge) for edge in seed['points'][-1]['selected_edges']}
    permutation = list(range(81))
    for a in range(9, 81, 2):
        b = a+1
        first = tuple(int((tip, a) in edges) for tip in range(9))
        second = tuple(int((tip, b) in edges) for tip in range(9))
        if first < second:
            permutation[a], permutation[b] = b, a
    renamed = {tuple(sorted((permutation[a], permutation[b]))) for a, b in edges}
    assert renamed <= set(variables)
    return [variable if edge in renamed else -variable for edge, variable in variables.items()]


def save(path, result):
    if path:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(result, indent=2)+'\n')


def run(seed_path, seconds, rounds, output, initial_cnf, final_cnf):
    seed = json.loads(seed_path.read_text())
    cnf, variables, rows, signatures, metadata, seen = build(seed, seed_path)
    metadata.update(solver='glucose4', wall_budget_seconds=seconds,
                    maximum_refinement_rounds=rounds,
                    phase_seed='last partial point, after independent duplicate-label swaps')
    if initial_cnf:
        initial_cnf.parent.mkdir(parents=True, exist_ok=True)
        cnf.to_file(initial_cnf)
        metadata.update(initial_cnf=str(initial_cnf), initial_cnf_sha256=digest(initial_cnf))
    print(json.dumps({'built': metadata}), flush=True)
    result = {'status': 'running', 'metadata': metadata, 'points': [],
              'initial_cuts': seed['necessary_cuts'], 'necessary_cuts': []}
    started = time.monotonic()
    with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
        solver.set_phases(canonical_phases(seed, variables))
        for iteration in range(rounds):
            remaining = seconds-(time.monotonic()-started)
            if remaining <= 0:
                result['status'] = 'unknown at wall budget'
                break
            timer = Timer(remaining, solver.interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
            if answer is not True:
                result['status'] = 'solver UNSAT; independently checkable proof not yet obtained' if answer is False else 'unknown at wall budget'
                break
            point, cuts = inspect_point({v for v in solver.get_model() if v > 0}, variables, rows, signatures)
            selected = {tuple(edge) for edge in point['selected_edges']}
            for a in range(9, 81, 2):
                first = tuple(int((tip, a) in selected) for tip in range(9))
                second = tuple(int((tip, a+1) in selected) for tip in range(9))
                assert first >= second
            result['points'].append(point)
            print(json.dumps({'round': iteration+1, 'defective_pairs': point['defective_pairs'],
                              'outside_cap_violations': point['outside_cap_violations'],
                              'seconds': time.monotonic()-started}), flush=True)
            if not point['defective_pairs']:
                result['status'] = 'exact99-vertex SRG candidate; independent validation required'
                break
            for record in cuts:
                clause = cut_clause(record, signatures, variables)
                key = tuple(clause)
                if key not in seen:
                    seen.add(key)
                    solver.add_clause(clause)
                    cnf.append(clause)
                    result['necessary_cuts'].append(record)
            result['elapsed_seconds'] = time.monotonic()-started
            save(output, result)
        else:
            result['status'] = 'refinement round limit; partial binary points only'
        result['solver_statistics'] = solver.accum_stats()
    result['seconds'] = time.monotonic()-started
    if final_cnf:
        final_cnf.parent.mkdir(parents=True, exist_ok=True)
        cnf.to_file(final_cnf)
        result.update(final_cnf=str(final_cnf), final_cnf_sha256=digest(final_cnf),
                      final_clauses=len(cnf.clauses))
    save(output, result)
    print(json.dumps({'status': result['status'], 'binary_points': len(result['points']),
                      'new_necessary_cuts': len(result['necessary_cuts']),
                      'all_necessary_cuts': len(seen), 'seconds': result['seconds']}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('seed', type=Path)
    parser.add_argument('--seconds', type=float, default=180)
    parser.add_argument('--rounds', type=int, default=100)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--initial-cnf', type=Path)
    parser.add_argument('--final-cnf', type=Path)
    args = parser.parse_args()
    run(args.seed, args.seconds, args.rounds, args.output, args.initial_cnf, args.final_cnf)
