"""Simplify checked signed cores using exact incidence implications.

First records exact quota-propagation steps from positive units alone.
Every remaining required-negative literal is queried in the tiny margin
master. SAT has an exact72-column Gram witness; UNSAT requires a fresh
explicit-positive-unit CNF and independent DRAT. No large oracle is used.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time

from pysat.formula import CNF
from pysat.solvers import Solver

import complement_rook_a_incidence as incidence
from complement_rook_incidence_master import ROOT, bounded, clauses, digest, master_formula


def propagation(equations, positive):
    known = {literal: 1 for literal in positive}
    steps = []
    while True:
        changed = False
        for row, (indices, quota) in enumerate(equations):
            members = [s+1 for s in indices]
            ones = [literal for literal in members if known.get(literal) == 1]
            unknown = [literal for literal in members if literal not in known]
            assert len(ones) <= quota <= len(ones)+len(unknown)
            if unknown and (len(ones) == quota or len(ones)+len(unknown) == quota):
                value = int(len(ones)+len(unknown) == quota)
                steps.append({'row_index': row, 'quota': quota, 'known_ones': ones,
                              'unknown_before': unknown, 'forced_value': value})
                known.update((literal, value) for literal in unknown)
                changed = True
        if not changed:
            break
    return known, steps


def check_selected(selected):
    _, _, triples, _, counted, _ = incidence.domain()
    a = sum(s in set(counted) for s in selected)
    checked = incidence.check_witness(selected, a)
    return {'selected_signatures': selected, 'a': a, 'full_Gram_entries_checked': checked['full_gram_entries_checked']}


def prove_implication(master, positive, target, prefix, checker):
    prefix = prefix.resolve()
    assumptions = positive+[target]
    assert len(assumptions) == len(set(assumptions)) and all(literal > 0 for literal in assumptions)
    formula = prefix.with_suffix('.cnf')
    proof_path = prefix.with_suffix('.drat')
    cnf = CNF(from_clauses=master.clauses+[[literal] for literal in assumptions])
    cnf.to_file(formula)
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
        answer = bounded(solver, 2)
        if answer is None:
            return {'status': 'UNKNOWN in fresh tiny implication proof'}
        assert answer is False
        proof = solver.get_proof()
        assert proof is not None
        engine_proof_lines = len(proof)
        # Bootstrap can detect unit inconsistency before the proof stream
        # starts. An explicit final empty clause is then a RUP claim that
        # the independent checker must verify against the actual input.
        appended_empty = not proof or proof[-1] != '0'
        if appended_empty:
            proof.append('0')
        proof_path.write_text('\n'.join(proof)+'\n')
    log = prefix.with_suffix('.log')
    checked = subprocess.run([str(checker), str(formula), str(proof_path), '-t', '5'],
                             capture_output=True, text=True, timeout=8, check=False)
    log.write_text(checked.stdout+checked.stderr)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
    return {'status': 'UNSAT implication DRAT verified', 'positive_units': assumptions,
            'cnf': str(formula.relative_to(ROOT)), 'cnf_sha256': digest(formula),
            'proof': str(proof_path.relative_to(ROOT)), 'proof_sha256': digest(proof_path),
            'log': str(log.relative_to(ROOT)), 'proof_lines': len(proof),
            'engine_proof_lines': engine_proof_lines, 'appended_terminal_empty_clause': appended_empty}


def generate(pilot_path, full_replay_path, directory, output, checker):
    pilot = json.loads(pilot_path.read_text())
    full_replay = json.loads(full_replay_path.read_text())
    assert full_replay['status'] == 'all8 full baseline rebuilds, exact core-unit hashes, retained inclusions and DRAT replays PASS'
    master, master_domain = master_formula()
    _, _, _, _, _, equations = incidence.domain()
    directory.mkdir(parents=True, exist_ok=True)
    record = {'status': 'incidence implication checks running', 'source_sha256': digest(Path(__file__)),
              'master_source_sha256': digest(Path(__file__).with_name('complement_rook_incidence_master.py')),
              'incidence_source_sha256': digest(Path(incidence.__file__)),
              'pilot_sha256': digest(pilot_path), 'full_replay_sha256': digest(full_replay_path),
              'master_domain_sha256': master_domain, 'master_variables': master.nv,
              'master_clauses': len(master.clauses), 'seconds_per_small_solve': 2,
              'cases': [], 'large_oracle_loaded': False, 'large_oracle_solved': False}
    started = time.monotonic()
    with Solver(name='glucose4', bootstrap_with=master.clauses) as oracle:
        for index, checked in enumerate(full_replay['cases']):
            assert checked['case'] == index and checked['exit_code'] == 0
            certificate_path = ROOT/checked['certificate']
            assert digest(certificate_path) == checked['certificate_sha256']
            original = json.loads(certificate_path.read_text())
            retained = set(clauses(ROOT/original['retained_cnf']))
            assert digest(ROOT/original['retained_cnf']) == original['retained_cnf_sha256']
            core = original['core_units']
            positive = [literal for literal in core if literal > 0]
            negative = [-literal for literal in core if literal < 0]
            used_negative = [literal for literal in negative if (-literal,) in retained]
            known, steps = propagation(equations, positive)
            original_selected = set(original['selected_signatures'])
            assert all(value == (literal-1 in original_selected) for literal, value in known.items())
            forced = [literal for literal in negative if known.get(literal) == 0]
            pending = [literal for literal in used_negative if known.get(literal) != 0]
            case = {'case': index, 'a': pilot['designs'][index]['a'],
                    'original_certificate': str(certificate_path.relative_to(ROOT)),
                    'original_certificate_sha256': digest(certificate_path), 'original_core': core,
                    'positive_units': positive, 'original_negative_variables': negative,
                    'retained_negative_variables': used_negative,
                    'quota_propagation_steps': steps,
                    'propagated_positive_variables': sorted(literal for literal, value in known.items() if value),
                    'propagated_negative_variables': sorted(literal for literal, value in known.items() if not value),
                    'original_negatives_forced_by_propagation': forced,
                    'remaining_implication_queries': pending, 'queries': []}
            record['cases'].append(case)
            for target in pending:
                query_started = time.monotonic()
                answer = bounded(oracle, 2, positive+[target])
                query = {'negative_variable': target, 'seconds': time.monotonic()-query_started}
                if answer is None:
                    query['status'] = 'UNKNOWN; implication undecided'
                    case['queries'].append(query)
                    record['status'] = 'UNKNOWN in tiny master; stopped without unverified simplification'
                    output.write_text(json.dumps(record, indent=2)+'\n')
                    return record
                if answer:
                    selected = sorted(literal-1 for literal in oracle.get_model() if 1 <= literal <= 252)
                    witness = check_selected(selected)
                    assert {literal-1 for literal in positive+[target]} <= set(selected)
                    query.update(status='SAT counterexample to implication from positive units alone', witness=witness)
                else:
                    query['certificate'] = prove_implication(master, positive, target,
                                                             directory/f'case-{index}-negative-{target}', checker)
                    query['status'] = query['certificate']['status']
                    if query['status'].startswith('UNKNOWN'):
                        case['queries'].append(query)
                        record['status'] = 'UNKNOWN in tiny fresh proof; stopped without unverified simplification'
                        output.write_text(json.dumps(record, indent=2)+'\n')
                        return record
                case['queries'].append(query)
                output.write_text(json.dumps(record, indent=2)+'\n')
            proved = set(forced) | {query['negative_variable'] for query in case['queries']
                                   if query['status'] == 'UNSAT implication DRAT verified'}
            kept = [literal for literal in used_negative if literal not in proved]
            units = sorted(positive+[-literal for literal in kept], key=abs)
            case.update(simplified_units=units, simplified_clause=[-literal for literal in units],
                        simplified_core_size=len(units), retained_negative_count=len(kept),
                        positive_only=not kept)
            print(json.dumps({'case': index, 'positive_units': len(positive),
                              'original_negative_units': len(negative), 'propagation_forced': len(forced),
                              'small_master_UNSAT_implications': sum(query['status'] == 'UNSAT implication DRAT verified' for query in case['queries']),
                              'SAT_counterexamples': sum(query['status'].startswith('SAT') for query in case['queries']),
                              'simplified_core_size': len(units)}), flush=True)
    record['status'] = 'all exact propagation and remaining tiny-master implications classified'
    record['total_seconds'] = time.monotonic()-started
    record['scope'] = 'shorter necessary signed patterns; no whole-core exclusion or positive-only assertion beyond the per-case results'
    output.write_text(json.dumps(record, indent=2)+'\n')
    return record


def replay(pilot_path, full_replay_path, certificate_path, checker, directory):
    record = json.loads(certificate_path.read_text())
    assert record['status'] == 'all exact propagation and remaining tiny-master implications classified'
    assert record['source_sha256'] == digest(Path(__file__))
    assert record['pilot_sha256'] == digest(pilot_path)
    assert record['full_replay_sha256'] == digest(full_replay_path)
    assert record['master_source_sha256'] == digest(Path(__file__).with_name('complement_rook_incidence_master.py'))
    assert record['incidence_source_sha256'] == digest(Path(incidence.__file__))
    master, master_domain = master_formula()
    assert (master.nv, len(master.clauses), master_domain) == (record['master_variables'], record['master_clauses'], record['master_domain_sha256'])
    _, _, _, _, _, equations = incidence.domain()
    full_replay = json.loads(full_replay_path.read_text())
    assert full_replay['status'] == 'all8 full baseline rebuilds, exact core-unit hashes, retained inclusions and DRAT replays PASS'
    assert len(record['cases']) == len(full_replay['cases']) == 8
    directory.mkdir(parents=True, exist_ok=True)
    for case, full_case in zip(record['cases'], full_replay['cases']):
        assert case['case'] == full_case['case'] and full_case['exit_code'] == 0
        assert case['original_certificate'] == full_case['certificate']
        assert case['original_certificate_sha256'] == full_case['certificate_sha256']
        original_path = ROOT/case['original_certificate']
        assert digest(original_path) == case['original_certificate_sha256']
        original = json.loads(original_path.read_text())
        assert original['core_units'] == case['original_core']
        positive = [literal for literal in original['core_units'] if literal > 0]
        assert positive == case['positive_units']
        known, steps = propagation(equations, positive)
        assert steps == case['quota_propagation_steps']
        assert case['propagated_positive_variables'] == sorted(literal for literal, value in known.items() if value)
        assert case['propagated_negative_variables'] == sorted(literal for literal, value in known.items() if not value)
        retained_path = ROOT/original['retained_cnf']
        assert digest(retained_path) == original['retained_cnf_sha256']
        retained = set(clauses(retained_path))
        negative = [-literal for literal in original['core_units'] if literal < 0]
        used = [literal for literal in negative if (-literal,) in retained]
        assert negative == case['original_negative_variables'] and used == case['retained_negative_variables']
        assert case['original_negatives_forced_by_propagation'] == [literal for literal in negative if known.get(literal) == 0]
        pending = [literal for literal in used if known.get(literal) != 0]
        assert pending == case['remaining_implication_queries']
        assert [query['negative_variable'] for query in case['queries']] == pending
        proved = {literal for literal in negative if known.get(literal) == 0}
        for query in case['queries']:
            target = query['negative_variable']
            if query['status'].startswith('SAT'):
                witness = check_selected(query['witness']['selected_signatures'])
                assert witness == query['witness']
                assert {literal-1 for literal in positive+[target]} <= set(witness['selected_signatures'])
            else:
                certificate = query['certificate']
                assert query['status'] == certificate['status'] == 'UNSAT implication DRAT verified'
                assert certificate['positive_units'] == positive+[target]
                rebuilt = directory/f'case-{case["case"]}-negative-{target}.cnf'
                CNF(from_clauses=master.clauses+[[literal] for literal in positive+[target]]).to_file(rebuilt)
                assert digest(rebuilt) == certificate['cnf_sha256']
                proof = ROOT/certificate['proof']
                assert digest(proof) == certificate['proof_sha256']
                checked = subprocess.run([str(checker), str(rebuilt), str(proof), '-t', '5'],
                                         capture_output=True, text=True, timeout=8, check=False)
                assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
                proved.add(target)
        units = sorted(positive+[-literal for literal in used if literal not in proved], key=abs)
        assert units == case['simplified_units']
        assert case['simplified_clause'] == [-literal for literal in units]
        assert case['simplified_core_size'] == len(units)
        assert case['retained_negative_count'] == sum(literal < 0 for literal in units)
        assert case['positive_only'] == all(literal > 0 for literal in units)
    result = {'status': 'exact quota derivations, all SAT implication counterexamples, and any small DRAT implications replayed',
              'cases': len(record['cases']), 'queries': sum(len(case['queries']) for case in record['cases']),
              'simplified_core_sizes': [case['simplified_core_size'] for case in record['cases']],
              'positive_only_cases': [case['case'] for case in record['cases'] if case['positive_only']],
              'large_oracle_solved': False}
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', type=Path, required=True)
    parser.add_argument('--full-replay', type=Path, required=True)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--drat-trim', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    if args.write:
        generate(args.pilot, args.full_replay, args.directory, args.certificate, args.drat_trim)
    else:
        replay(args.pilot, args.full_replay, args.certificate, args.drat_trim, args.directory)
