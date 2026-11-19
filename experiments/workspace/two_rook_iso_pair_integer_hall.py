"""Certified Hall-clause continuation of the fixed-tip lex edge model."""

import argparse
import json
from pathlib import Path
from threading import Timer
import time

from pysat.solvers import Solver

from two_rook_iso_pair_integer import inspect_point, cut_clause
from two_rook_iso_pair_integer_lex import build as lex_build, canonical_phases, digest, save
from two_rook_tip_hall_audit import verify as verify_hall, translate


def hall_clauses(variables, certificate):
    checked = verify_hall(certificate)
    forbidden = certificate['forbidden_masks']
    variable_edges = {variable: edge for edge, variable in variables.items()}
    clauses = []
    for tip in range(9):
        inverse = [next(p for p in range(9) if translate(p, tip) == q) for q in range(9)]
        assert inverse[0] == tip
        for mask in forbidden:
            clause = []
            for canonical in range(1, 9):
                other = inverse[canonical]
                variable = variables[tuple(sorted((tip, other)))]
                clause.append(-variable if mask >> (canonical-1) & 1 else variable)
            assert len(set(map(abs, clause))) == 8
            clauses.append(clause)
            # Independently decode its unique falsifying local assignment.
            decoded = 0
            for literal in clause:
                edge = variable_edges[abs(literal)]
                assert tip in edge
                other = edge[1] if edge[0] == tip else edge[0]
                canonical = translate(other, tip)
                assert canonical != 0
                if literal < 0:
                    decoded |= 1 << (canonical-1)
            assert decoded == mask
    assert len(clauses) == 1377
    assert len({tuple(sorted(clause)) for clause in clauses}) == 1377
    return clauses, {k: checked[k] for k in ('status', 'admitted_masks', 'forbidden_masks',
                                            'clauses_for_all_nine_tips')}


def build(seed, seed_path, hall_path):
    cnf, variables, rows, signatures, metadata, seen = lex_build(seed, seed_path)
    certificate = json.loads(hall_path.read_text())
    clauses, checked = hall_clauses(variables, certificate)
    cnf.extend(clauses)
    metadata['lex_source_sha256'] = metadata.pop('source_sha256')
    metadata.update(source_sha256=digest(Path(__file__)), hall_clauses=len(clauses),
                    hall_certificate=str(hall_path), hall_certificate_sha256=digest(hall_path),
                    hall_verifier_sha256=digest(Path(__file__).with_name('two_rook_tip_hall_audit.py')),
                    hall_replay=checked, tip_psd_cuts=0, clauses=len(cnf.clauses))
    return cnf, variables, rows, signatures, metadata, seen, set(certificate['admitted_masks'])


def check_tip_masks(point, admitted):
    edges = {tuple(edge) for edge in point['tip_edges']}
    for tip in range(9):
        mask = 0
        for other in range(9):
            if other != tip and tuple(sorted((tip, other))) in edges:
                mask |= 1 << (translate(other, tip)-1)
        assert mask in admitted


def run(seed_path, hall_path, seconds, rounds, output, initial_cnf, final_cnf):
    seed = json.loads(seed_path.read_text())
    cnf, variables, rows, signatures, metadata, seen, admitted = build(seed, seed_path, hall_path)
    metadata.update(solver='glucose4', wall_budget_seconds=seconds,
                    maximum_refinement_rounds=rounds,
                    phase_seed='last original partial point, after independent duplicate-label swaps')
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
            check_tip_masks(point, admitted)
            selected = {tuple(edge) for edge in point['selected_edges']}
            for a in range(9, 81, 2):
                assert tuple(int((tip, a) in selected) for tip in range(9)) >= tuple(int((tip, a+1) in selected) for tip in range(9))
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
    parser.add_argument('--hall-certificate', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=180)
    parser.add_argument('--rounds', type=int, default=100)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--initial-cnf', type=Path)
    parser.add_argument('--final-cnf', type=Path)
    args = parser.parse_args()
    run(args.seed, args.hall_certificate, args.seconds, args.rounds, args.output,
        args.initial_cnf, args.final_cnf)
