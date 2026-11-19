"""Small exact tip model: all Hall masks, all caps, and one rook-near edge.

This is a 36-edge-variable necessary projection, not a graph completion.
The model builder and SAT-point replay use only the standard library.
Solving uses PySAT; an UNSAT conclusion requires independent DRAT replay.
"""

import argparse
import hashlib
from itertools import combinations
import json
from pathlib import Path
import subprocess
from threading import Timer
import time

from two_rook_tip_hall_audit import verify as verify_hall
from two_rook_tip_psd_audit import congruence, tip_matrix, verify_congruence, rook


EDGES = list(combinations(range(9), 2))
VARIABLE = {edge: i+1 for i, edge in enumerate(EDGES)}


def edge_variable(a, b):
    return VARIABLE[tuple(sorted((a, b)))]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build(hall_path):
    hall = json.loads(hall_path.read_text())
    assert verify_hall(hall)['forbidden_masks'] == 153
    clauses = []
    for tip in range(9):
        # An independently written inverse of the canonical row/column shift.
        point = [3*((q//3+tip//3) % 3)+(q % 3+tip % 3) % 3 for q in range(9)]
        assert point[0] == tip and sorted(point) == list(range(9))
        assert all(rook(a, b) == rook(point[a], point[b]) for a, b in EDGES)
        for mask in hall['forbidden_masks']:
            clauses.append([(-1 if mask >> (q-1) & 1 else 1)*edge_variable(tip, point[q])
                            for q in range(1, 9)])
    assert len(clauses) == 1377
    for a, b in EDGES:
        others = [c for c in range(9) if c not in (a, b)]
        for common in combinations(others, 2):
            clauses.append([-edge_variable(a, b)]
                           + [-edge_variable(endpoint, c) for c in common for endpoint in (a, b)])
    assert len(clauses) == 1377+756
    for a, b in EDGES:
        others = [c for c in range(9) if c not in (a, b)]
        for common in combinations(others, 3):
            clauses.append([-edge_variable(endpoint, c) for c in common for endpoint in (a, b)])
    assert len(clauses) == 1377+756+1260
    clauses.append([edge_variable(0, 1)])
    assert len(clauses) == 3394
    assert len({tuple(sorted(clause)) for clause in clauses}) == 3394
    return clauses, set(hall['admitted_masks'])


def dimacs(clauses):
    return 'p cnf 36 3394\n'+''.join(' '.join(map(str, clause))+' 0\n' for clause in clauses)


def check_graph(edges, admitted, require_near=True):
    edge_set = {tuple(edge) for edge in edges}
    assert len(edge_set) == len(edges) and edge_set <= set(EDGES)
    if require_near:
        assert (0, 1) in edge_set
    neighbors = [set() for _ in range(9)]
    for a, b in edge_set:
        neighbors[a].add(b)
        neighbors[b].add(a)
    caps = [[a, b, len(neighbors[a] & neighbors[b])+int(b in neighbors[a])] for a, b in EDGES]
    assert all(value <= 2 for _, _, value in caps)
    masks = []
    for tip in range(9):
        mask = 0
        for other in neighbors[tip]:
            canonical = 3*((other//3-tip//3) % 3)+(other % 3-tip % 3) % 3
            assert canonical
            mask |= 1 << (canonical-1)
        assert mask in admitted
        masks.append(mask)
    return {'degrees': [len(row) for row in neighbors], 'tip_masks': masks,
            'maximum_cap': max(value for _, _, value in caps),
            'rook_near_edges': [list(edge) for edge in edges if rook(*edge)]}


def satisfies(clauses, edges):
    positive = {VARIABLE[tuple(edge)] for edge in edges}
    return all(any((literal > 0) == (abs(literal) in positive) for literal in clause)
               for clause in clauses)


def controls(clauses, admitted):
    for edges in ([], [list(edge) for edge in EDGES if not rook(*edge)]):
        check_graph(edges, admitted, require_near=False)
        assert satisfies(clauses[:-1], edges)
        assert not satisfies(clauses, edges)
    cases = 0
    for edge in (0, 1):
        for mask in range(128):
            count = mask.bit_count()
            pair_clauses = all(not edge or not all(mask >> i & 1 for i in common)
                               for common in combinations(range(7), 2))
            triple_clauses = all(not all(mask >> i & 1 for i in common)
                                 for common in combinations(range(7), 3))
            assert (pair_clauses and triple_clauses) == (count+edge <= 2)
            cases += 1
    return {'positive_controls_without_near_unit': 2,
            'exact_common_indicator_cases': cases}


def solve(args):
    from pysat.solvers import Solver
    clauses, admitted = build(args.hall)
    control = controls(clauses, admitted)
    args.cnf.write_text(dimacs(clauses))
    started = time.monotonic()
    with Solver(name='glucose4', bootstrap_with=clauses, with_proof=True) as solver:
        timer = Timer(args.seconds, solver.interrupt)
        timer.start()
        try:
            answer = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
        record = {'variables': 36, 'clauses': len(clauses), 'controls': control,
                  'source_sha256': digest(Path(__file__)), 'hall_certificate_sha256': digest(args.hall),
                  'cnf_sha256': digest(args.cnf), 'seconds': time.monotonic()-started,
                  'statistics': solver.accum_stats()}
        if answer is True:
            positive = {x for x in solver.get_model() if x > 0}
            edges = [list(edge) for edge, variable in VARIABLE.items() if variable in positive]
            assert satisfies(clauses, edges)
            checked = check_graph(edges, admitted)
            psd = congruence(tip_matrix(edges))
            verify_congruence(tip_matrix(edges), psd)
            record.update(status='SAT; exact tip point checked', tip_edges=edges,
                          point_check=checked, tip_psd=psd)
        elif answer is False:
            args.proof.write_text('\n'.join(solver.get_proof())+'\n')
            record.update(status='solver UNSAT; DRAT replay required', proof_sha256=digest(args.proof))
        else:
            record.update(status='unknown at wall budget')
    args.output.write_text(json.dumps(record, indent=2)+'\n')
    return record


def replay(args):
    record = json.loads(args.output.read_text())
    clauses, admitted = build(args.hall)
    assert record['source_sha256'] == digest(Path(__file__))
    assert record['hall_certificate_sha256'] == digest(args.hall)
    assert record['controls'] == controls(clauses, admitted)
    assert args.cnf.read_text() == dimacs(clauses)
    assert digest(args.cnf) == record['cnf_sha256']
    assert record['variables'] == 36 and record['clauses'] == 3394
    if record['status'] == 'SAT; exact tip point checked':
        edges = record['tip_edges']
        assert satisfies(clauses, edges)
        assert record['point_check'] == check_graph(edges, admitted)
        verify_congruence(tip_matrix(edges), record['tip_psd'])
        return {'status': 'exact SAT point, Hall/cap equations, and PSD certificate replay passed',
                'tip_edges': edges, 'tip_psd_status': record['tip_psd']['status'],
                'tip_psd_rank': record['tip_psd'].get('rank')}
    if record['status'] == 'solver UNSAT; DRAT replay required':
        assert args.drat_trim is not None
        assert digest(args.proof) == record['proof_sha256']
        checked = subprocess.run([str(args.drat_trim.resolve()), str(args.cnf.resolve()),
                                  str(args.proof.resolve())], capture_output=True, text=True,
                                 timeout=30, check=False)
        assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (checked.stdout, checked.stderr)
        return {'status': 'rebuilt CNF and independent DRAT proof verified',
                'checker_stdout': checked.stdout}
    assert record['status'] == 'unknown at wall budget'
    return {'status': 'saved run was inconclusive'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--hall', type=Path, required=True)
    parser.add_argument('--cnf', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--drat-trim', type=Path)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    result = replay(args) if args.replay else solve(args)
    print(json.dumps(result, indent=2))
