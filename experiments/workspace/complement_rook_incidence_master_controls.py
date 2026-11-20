"""Small assumption/core/DRUP controls for an incidence-master pilot.

This never loads the large joint formula. It checks signed assumption
cores, fresh explicit-unit certification, a positive toy master, and
the danger of reusing a cumulative assumption-proof transcript.
"""

import argparse
import hashlib
import inspect
from itertools import combinations, product
import json
from pathlib import Path
import subprocess

import pysat
from pysat.formula import CNF
from pysat.solvers import Glucose4, Solver


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def php(first):
    return [[first+2*i, first+2*i+1] for i in range(3)]+[
        [-(first+2*i+h), -(first+2*j+h)] for i, j in combinations(range(3), 2) for h in range(2)]


def satisfies(clauses, positive):
    return all(any((literal > 0) == (abs(literal) in positive) for literal in clause) for clause in clauses)


def check(checker, formula, proof, log, expected):
    completed = subprocess.run([str(checker), str(formula), str(proof), '-t', '5'],
                               text=True, capture_output=True, timeout=8, check=False)
    log.write_text(completed.stdout+completed.stderr)
    verified = completed.returncode == 0 and 's VERIFIED' in completed.stdout
    assert verified == expected, (completed.returncode, completed.stdout, completed.stderr)
    return {'return_code': completed.returncode, 'verified': verified,
            'log': str(log), 'log_sha256': digest(log)}


def certify_fresh(clauses, core, prefix, checker):
    assert len(core) == len(set(core))
    assert not any(-literal in core for literal in core)
    formula = prefix.with_suffix('.cnf')
    proof = prefix.with_suffix('.drat')
    cnf = CNF(from_clauses=clauses+[[literal] for literal in core])
    cnf.to_file(formula)
    # Solve the actual unit-augmented formula, with no assumptions.
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
        assert solver.solve() is False
        transcript = solver.get_proof()
    assert transcript and transcript[-1] == '0'
    proof.write_text('\n'.join(transcript)+'\n')
    checked = check(checker, formula, proof, prefix.with_suffix('.log'), True)
    return {'core_units': core, 'learned_selector_clause': [-literal for literal in core],
            'formula': str(formula), 'formula_sha256': digest(formula),
            'proof': str(proof), 'proof_sha256': digest(proof),
            'proof_lines': len(transcript), 'checker': checked,
            'certificate_scope': 'base formula plus these exact signed core units'}


def cumulative_control(directory, checker):
    clauses = [[-1]+clause for clause in php(3)]+[[-2]+clause for clause in php(9)]
    with Solver(name='glucose4', bootstrap_with=clauses, with_proof=True) as solver:
        assert solver.solve(assumptions=[1, -2]) is False
        first_core = solver.get_core()
        first_proof = solver.get_proof()
        assert first_core == [1]
        assert solver.solve(assumptions=[-1, 2]) is False
        second_core = solver.get_core()
        cumulative = solver.get_proof()
        assert second_core == [2]
    assert cumulative[:len(first_proof)] == first_proof
    assert first_proof[-1] == '0' and cumulative.count('0') >= 2
    formula = directory/'cumulative-second-core.cnf'
    raw = directory/'cumulative-proof.drat'
    CNF(from_clauses=clauses+[[literal] for literal in second_core]).to_file(formula)
    raw.write_text('\n'.join(cumulative)+'\n')
    failed = check(checker, formula, raw, directory/'cumulative-expected-rejection.log', False)
    fresh = certify_fresh(clauses, second_core, directory/'cumulative-second-fresh', checker)
    return {'status': 'negative control passed: cumulative proof cannot certify the different second core',
            'first_core': first_core, 'second_core': second_core,
            'first_proof_lines': len(first_proof), 'cumulative_proof_lines': len(cumulative),
            'empty_clauses_in_cumulative_proof': cumulative.count('0'),
            'raw_proof': str(raw), 'raw_proof_sha256': digest(raw),
            'raw_checker_expected_rejection': failed, 'fresh_certificate': fresh}


def run(directory, checker):
    directory.mkdir(parents=True, exist_ok=True)
    for first in (5, 11):
        block = php(first)
        assert not any(satisfies(block, {first+i for i, bit in enumerate(bits) if bit})
                       for bits in product((0, 1), repeat=6))
    # Four selectors, exactly two selected. Two separately guarded PHP
    # blocks forbid designs {1,2} and {3,4}; the other four are SAT.
    clauses = [[-1, -2, 3]+clause for clause in php(5)]
    clauses += [[1, -3, -4]+clause for clause in php(11)]
    margins = [list(subset) for subset in combinations(range(1, 5), 3)]
    margins += [[-literal for literal in subset] for subset in combinations(range(1, 5), 3)]
    base = CNF(from_clauses=clauses)
    base_path = directory/'toy-joint-base.cnf'
    base.to_file(base_path)
    truth_table = {}
    for selected in combinations(range(1, 5), 2):
        positive = set(selected)
        assert satisfies(margins, positive)
        expected = selected not in ((1, 2), (3, 4))
        # A guarded PHP block is satisfiable exactly when its guard is
        # already true; graph variables of the two blocks are disjoint.
        guard_check = (not (1 in positive and 2 in positive and 3 not in positive)
                       and not (1 not in positive and 3 in positive and 4 in positive))
        assert expected == guard_check
        truth_table[selected] = expected
    visited = []
    learned = []
    sat_blocks = []
    with Solver(name='glucose4', bootstrap_with=margins) as master, Solver(
            name='glucose4', bootstrap_with=clauses) as oracle:
        while master.solve():
            selected = tuple(i for i in range(1, 5) if i in master.get_model())
            assert len(selected) == 2 and selected not in [tuple(item['selected']) for item in visited]
            assumptions = [i if i in selected else -i for i in range(1, 5)]
            assert len(assumptions) == 4 and {abs(lit) for lit in assumptions} == {1, 2, 3, 4}
            answer = oracle.solve(assumptions=assumptions)
            assert answer == truth_table[selected]
            item = {'selected': selected, 'full_signed_assumptions': assumptions, 'SAT': answer}
            if answer:
                positive = {literal for literal in oracle.get_model() if literal > 0}
                assert satisfies(clauses, positive)
                assert all((literal > 0) == (abs(literal) in positive) for literal in assumptions)
                item['exact_positive_model'] = sorted(positive)
                block = [-i for i in selected]
                master.add_clause(block)
                sat_blocks.append(block)
                item['exploration_only_design_block'] = block
            else:
                core = oracle.get_core()
                assert core and set(core) <= set(assumptions)
                assert any(literal < 0 for literal in core)
                proof = certify_fresh(clauses, core, directory/f'toy-core-{len(learned)}', checker)
                # The cut enters the master only after exact proof checking.
                cut = proof['learned_selector_clause']
                master.add_clause(cut)
                learned.append(proof)
                item['checked_core_certificate'] = proof
                assert not satisfies([cut], set(selected))
                for other, sat in truth_table.items():
                    if sat:
                        assert satisfies([cut], set(other))
            visited.append(item)
    assert len(visited) == 6 and len(learned) == 2 and len(sat_blocks) == 4
    assert all(set(certificate['core_units']) for certificate in learned)
    cumulative = cumulative_control(directory, checker)
    return {'status': 'small assumption/core/master controls PASS; no large model loaded or solved',
            'source_sha256': digest(Path(__file__)), 'pysat_version': pysat.__version__,
            'pysat_solver_source_sha256': digest(Path(inspect.getfile(Glucose4))),
            'drat_checker_sha256': digest(checker), 'toy_base_sha256': digest(base_path),
            'guarded_PHP_blocks_checked_by_64_assignments_each': 2,
            'toy_master_designs': 6, 'exact_partial_SAT_controls': 4,
            'verified_signed_core_cuts': 2, 'designs': visited,
            'certified_cuts': [certificate['learned_selector_clause'] for certificate in learned],
            'SAT_exploration_blocks_are_not_theorems': sat_blocks,
            'cumulative_proof_negative_control': cumulative,
            'proof_rule': 'fresh base-plus-core-unit CNF, solve without assumptions, then independently verify DRUP',
            'large_joint_CNF_loaded': False, 'large_joint_solver_called': False,
            'full_core_exclusion_claim': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--drat-trim', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = run(args.directory, args.drat_trim)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('designs', 'cumulative_proof_negative_control')}, indent=2), flush=True)
