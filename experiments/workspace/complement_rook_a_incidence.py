"""Selector-only incidence tests for the complementary-rook parameter a.

Every one of the 252 signatures is retained. No exterior edges, symmetry
restriction, or prescribed incidence witness is imposed.
"""

import argparse
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import subprocess
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver


def rook(p, q):
    return p != q and (p//3 == q//3 or p % 3 == q % 3)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def domain():
    rows = [0]*27
    for i, j in combinations(range(27), 2):
        if i//9 == j//9:
            adjacent = rook(i % 9, j % 9) if i//9 < 2 else not rook(i % 9, j % 9)
        else:
            adjacent = i % 9 == j % 9
        if adjacent:
            rows[i] |= 1 << j
            rows[j] |= 1 << i
    assert all(row.bit_count() == 6 for row in rows)
    gram = [[12*int(i == j)+2-((rows[i] >> j) & 1)-(rows[i] & rows[j]).bit_count()
             for j in range(27)] for i in range(27)]
    triples = [(p, q, t) for p, q, t in product(range(9), repeat=3)
               if p != q and not rook(p, q) and t not in (p, q)]
    signatures = [(p, 9+q, 18+t) for p, q, t in triples]
    full = [tuple(x+9*i for i, x in enumerate(triple)) for triple in product(range(9), repeat=3)]
    assert signatures == [s for s in full if all(gram[i][j] > 0 for i, j in combinations(s, 2))]
    assert len(signatures) == 252
    counted = [s for s, (p, q, t) in enumerate(triples) if rook(p, t) and rook(q, t)]
    assert len(counted) == 72
    equations = []
    for first, second in ((0, 1), (0, 2), (1, 2)):
        for p, q in product(range(9), repeat=2):
            target = gram[9*first+p][9*second+q]
            if target:
                members = [s for s, triple in enumerate(triples) if triple[first] == p and triple[second] == q]
                equations.append((members, target))
    assert len(equations) == 180 and sum(target for _, target in equations) == 216
    return rows, gram, triples, signatures, counted, equations


def check_witness(selected, target):
    _, gram, triples, signatures, counted, _ = domain()
    assert selected == sorted(set(selected)) and len(selected) == 72
    assert all(0 <= s < 252 for s in selected)
    assert sum(s in set(counted) for s in selected) == target
    assert all(sum(i in signatures[s] and j in signatures[s] for s in selected) == gram[i][j]
               for i in range(27) for j in range(27))
    far = sum(not rook(triples[s][0], triples[s][2]) and not rook(triples[s][1], triples[s][2])
              for s in selected)
    assert far == target
    return {'selected_signatures': selected, 'selected_triples': [list(triples[s]) for s in selected],
            'a': target, 'both_far_count': far, 'full_gram_entries_checked': 729}


def zero_control():
    _, _, triples, _, _, _ = domain()
    position = {triple: i for i, triple in enumerate(triples)}
    permutation = (0, 5, 7, 8, 6, 1, 4, 2, 3)
    def add(p, q):
        return 3*((p//3+q//3) % 3)+(p % 3+q % 3) % 3
    def subtract(p, q):
        return 3*((p//3-q//3) % 3)+(p % 3-q % 3) % 3
    selected = sorted(position[p, add(t, permutation[subtract(p, t)]), t]
                      for t in range(9) for p in range(9) if p != t)
    return check_witness(selected, 0)


def build(target):
    _, _, _, _, counted, equations = domain()
    cnf, pool = CNF(), IDPool(start_from=253)
    for members, quota in equations:
        cnf.extend(CardEnc.equals([s+1 for s in members], quota,
                                 vpool=pool, encoding=EncType.seqcounter).clauses)
    cnf.extend(CardEnc.equals([s+1 for s in counted], target,
                             vpool=pool, encoding=EncType.seqcounter).clauses)
    return cnf


def verify_drat(checker, cnf_path, proof_path, log_path):
    checked = subprocess.run([str(checker.resolve()), str(cnf_path.resolve()), str(proof_path.resolve())],
                             capture_output=True, text=True, timeout=10, check=False)
    log_path.write_text(checked.stdout+checked.stderr)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (checked.stdout, checked.stderr)


def run(args):
    result = {'scope': 'selector-only incidence values; no exterior edge constraints',
              'source_sha256': digest(Path(__file__)), 'zero_incidence_control': zero_control(),
              'seconds_per_value': args.seconds, 'cases': []}
    control_cnf = build(0)
    positive = {s+1 for s in result['zero_incidence_control']['selected_signatures']}
    with Solver(name='glucose4', bootstrap_with=control_cnf.clauses) as solver:
        assert solver.solve(assumptions=[s if s in positive else -s for s in range(1, 253)])
    result['zero_control_CNF_check'] = 'pass'
    for target in range(1, args.max_a+1):
        cnf = build(target)
        cnf_path = args.prefix.with_name(args.prefix.name+f'-{target}.cnf')
        proof_path = args.prefix.with_name(args.prefix.name+f'-{target}.drat')
        log_path = args.output.with_name(args.output.stem+f'-{target}-drat.log')
        cnf.to_file(cnf_path)
        record = {'a': target, 'signature_selectors': 252, 'variables': cnf.nv,
                  'clauses': len(cnf.clauses), 'cnf_path': str(cnf_path),
                  'cnf_sha256': digest(cnf_path)}
        started = time.monotonic()
        with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
            remaining = max(0, args.seconds-(time.monotonic()-started))
            if remaining:
                timer = Timer(remaining, solver.interrupt)
                timer.start()
                try:
                    answer = solver.solve_limited(expect_interrupt=True)
                finally:
                    timer.cancel()
            else:
                answer = None
            record['solve_seconds'] = time.monotonic()-started
            record['solver_statistics'] = solver.accum_stats()
            if answer is True:
                chosen = {x for x in solver.get_model() if 1 <= x <= 252}
                record.update(status='SAT incidence; full Gram verified',
                              witness=check_witness(sorted(s-1 for s in chosen), target))
            elif answer is False:
                proof_path.write_text('\n'.join(solver.get_proof())+'\n')
                verify_drat(args.drat_trim, cnf_path, proof_path, log_path)
                record.update(status='UNSAT incidence; DRAT verified', proof_path=str(proof_path),
                              proof_sha256=digest(proof_path), drat_log=str(log_path))
            else:
                record['status'] = 'UNKNOWN; no incidence conclusion'
        result['cases'].append(record)
        args.output.write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({k: v for k, v in record.items() if k != 'witness'}), flush=True)
        if answer is not False:
            break
    return result


def replay(args):
    record = json.loads(args.output.read_text())
    assert record['source_sha256'] == digest(Path(__file__))
    assert record['zero_incidence_control'] == zero_control()
    assert record['zero_control_CNF_check'] == 'pass'
    for expected_a, case in enumerate(record['cases'], 1):
        assert case['a'] == expected_a
        cnf = build(expected_a)
        path = Path(case['cnf_path'])
        assert (cnf.nv, len(cnf.clauses)) == (case['variables'], case['clauses'])
        assert digest(path) == case['cnf_sha256']
        saved = CNF(from_file=str(path))
        assert saved.nv == cnf.nv and saved.clauses == cnf.clauses
        if case['status'].startswith('SAT'):
            assert case['witness'] == check_witness(case['witness']['selected_signatures'], expected_a)
        elif case['status'].startswith('UNSAT'):
            proof = Path(case['proof_path'])
            assert digest(proof) == case['proof_sha256']
            replay_log = Path(case['drat_log']).with_name(Path(case['drat_log']).stem+'-replay.log')
            verify_drat(args.drat_trim, path, proof, replay_log)
        else:
            assert case['status'] == 'UNKNOWN; no incidence conclusion'
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prefix', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--drat-trim', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=10)
    parser.add_argument('--max-a', type=int, default=36)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    assert 0 < args.seconds <= 10 and 1 <= args.max_a <= 36
    record = replay(args) if args.replay else run(args)
    print(json.dumps({'status': 'exact incidence sequence replay passed' if args.replay else 'bounded incidence sequence finished',
                      'tested': [[c['a'], c['status']] for c in record['cases']],
                      'first_positive_SAT_a': next((c['a'] for c in record['cases'] if c['status'].startswith('SAT')), None)}, indent=2))
