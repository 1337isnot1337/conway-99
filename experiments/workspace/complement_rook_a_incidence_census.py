"""Bounded exact a=2 incidence orbit census; no exterior graph-edge model."""

import argparse
import hashlib
from itertools import permutations, product
import json
from pathlib import Path
from threading import Timer
import time

from pysat.formula import CNF
from pysat.solvers import Solver

import complement_rook_a_incidence as incidence


def actions():
    rows, gram, triples, _, _, _ = incidence.domain()
    position = {triple: i for i, triple in enumerate(triples)}
    answer = []
    for row, column, transpose, swap in product(permutations(range(3)), permutations(range(3)), (False, True), (False, True)):
        point = [3*row[p % 3]+column[p//3] if transpose else 3*row[p//3]+column[p % 3]
                 for p in range(9)]
        core = [9*((1-base) if swap and base < 2 else base)+point[p]
                for base in range(3) for p in range(9)]
        assert sorted(core) == list(range(27))
        assert all(((rows[i] >> j) & 1) == ((rows[core[i]] >> core[j]) & 1)
                   and gram[i][j] == gram[core[i]][core[j]]
                   for i in range(27) for j in range(27))
        action = [position[(point[q], point[p], point[t]) if swap else
                           (point[p], point[q], point[t])] for p, q, t in triples]
        assert sorted(action) == list(range(252))
        answer.append(action)
    assert len({tuple(action) for action in answer}) == 144
    return sorted(answer)


def orbit(selected, group):
    return sorted({tuple(sorted(action[s] for s in selected)) for action in group})


def run(args):
    group = actions()
    cnf = incidence.build(2)
    record = {'scope': 'a=2 selector-only incidence orbit census',
              'source_sha256': incidence.digest(Path(__file__)),
              'incidence_source_sha256': incidence.digest(Path(incidence.__file__)),
              'group_order': 144, 'wall_budget_seconds': args.seconds,
              'labelled_design_cap': args.max_designs, 'orbits': [], 'labelled_designs': 0,
              'status': 'running'}
    covered = set()
    started = time.monotonic()
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
        while True:
            remaining = args.seconds-(time.monotonic()-started)
            if remaining <= 0:
                record['status'] = 'partial census; wall budget reached'
                break
            timer = Timer(remaining, solver.interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
            if answer is None:
                record['status'] = 'partial census; solver UNKNOWN at wall budget'
                break
            if answer is False:
                record['status'] = 'solver exhausted; proof replay pending'
                args.proof.write_text('\n'.join(solver.get_proof())+'\n')
                record['proof_sha256'] = incidence.digest(args.proof)
                break
            selected = sorted(v-1 for v in solver.get_model() if 1 <= v <= 252)
            incidence.check_witness(selected, 2)
            members = orbit(selected, group)
            assert not covered.intersection(members)
            if len(covered)+len(members) > args.max_designs:
                record['status'] = 'partial census; next whole orbit would exceed design cap'
                record['unrecorded_incidence_witness'] = incidence.check_witness(selected, 2)
                break
            representative = list(members[0])
            incidence.check_witness(representative, 2)
            record['orbits'].append({'representative': representative, 'orbit_size': len(members)})
            for member in members:
                clause = [-(s+1) for s in member]
                solver.add_clause(clause)
                cnf.append(clause)
            covered.update(members)
            record['labelled_designs'] = len(covered)
            record['elapsed_seconds'] = time.monotonic()-started
            args.output.write_text(json.dumps(record, indent=2)+'\n')
            print(json.dumps({'orbits': len(record['orbits']), 'labelled_designs': len(covered),
                              'seconds': record['elapsed_seconds']}), flush=True)
        record['solver_statistics'] = solver.accum_stats()
    record['search_seconds'] = time.monotonic()-started
    cnf.to_file(args.cnf)
    record.update(final_cnf_sha256=incidence.digest(args.cnf), variables=cnf.nv,
                  clauses=len(cnf.clauses))
    if record['status'] == 'solver exhausted; proof replay pending':
        incidence.verify_drat(args.drat_trim, args.cnf, args.proof, args.drat_log)
        record['status'] = 'complete incidence census; final blocked formula DRAT verified'
    args.output.write_text(json.dumps(record, indent=2)+'\n')
    return record


def replay(args):
    record = json.loads(args.output.read_text())
    assert record['source_sha256'] == incidence.digest(Path(__file__))
    assert record['incidence_source_sha256'] == incidence.digest(Path(incidence.__file__))
    group = actions()
    assert record['group_order'] == len(group) == 144
    cnf = incidence.build(2)
    covered = set()
    for saved in record['orbits']:
        representative = saved['representative']
        incidence.check_witness(representative, 2)
        members = orbit(representative, group)
        assert list(members[0]) == representative and len(members) == saved['orbit_size']
        assert not covered.intersection(members)
        covered.update(members)
        cnf.extend([[-(s+1) for s in member] for member in members])
    assert record['labelled_designs'] == len(covered) <= record['labelled_design_cap']
    assert (cnf.nv, len(cnf.clauses)) == (record['variables'], record['clauses'])
    assert incidence.digest(args.cnf) == record['final_cnf_sha256']
    saved_cnf = CNF(from_file=str(args.cnf))
    assert saved_cnf.nv == cnf.nv and saved_cnf.clauses == cnf.clauses
    if record['status'].startswith('complete'):
        assert incidence.digest(args.proof) == record['proof_sha256']
        incidence.verify_drat(args.drat_trim, args.cnf, args.proof, args.drat_log)
    else:
        assert record['status'].startswith('partial')
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cnf', type=Path, required=True)
    parser.add_argument('--proof', type=Path, required=True)
    parser.add_argument('--drat-log', type=Path, required=True)
    parser.add_argument('--drat-trim', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--max-designs', type=int, default=50000)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    assert 0 < args.seconds <= 60 and 0 < args.max_designs <= 50000
    record = replay(args) if args.replay else run(args)
    print(json.dumps({'status': record['status'], 'orbits': len(record['orbits']),
                      'labelled_designs': record['labelled_designs'],
                      'replayed': args.replay}, indent=2))
