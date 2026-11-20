"""Gram-only control for the first local eight-signature set.

All252 original selectors remain. The only constraints are the complete
27-core Gram equalities and eight positive selector units. There are no
matching, local-attachment, learned-pattern, or exterior-edge constraints.
"""

import argparse
from collections import defaultdict
import json
from pathlib import Path
import subprocess
import tempfile
from threading import Timer
import time

from pysat.solvers import Solver

import complement_rook_projector_schur as universe
import complement_rook_35core_incidence as encoder


ROOT = universe.ROOT
LOCAL = [0, 1, 9, 10, 18, 20, 26, 27]
SOURCES = ('complement_rook_35core_local_incidence_control.py',
           'complement_rook_35core_incidence.py', 'complement_rook_projector_schur.py')
digest, portable = encoder.digest, encoder.portable


def build():
    domain = universe.domain()
    _, gram, _, signatures, masks, _, _ = domain
    pairs = [(i, j) for i in range(27) for j in range(i, 27)]
    rows = [[s for s, mask in enumerate(masks) if mask >> i & 1 and mask >> j & 1]
            for i, j in pairs]
    triples = {tuple(sites): [s] for s, sites in enumerate(signatures)}
    cnf, metadata = encoder.assemble(gram, rows, {s: [s] for s in range(252)}, triples, 252)
    assert metadata['original_signature_multiplicity_rows'] == []
    assert metadata['additional_triple_rows'] == []
    assert metadata['clause_counts']['original_signature_at_most_one'] == 0
    assert metadata['clause_counts']['additional_core_triple_at_most_one'] == 0
    assert metadata['all_Gram_rows'] == 378 and metadata['clauses'] == 19800
    base = cnf.copy()
    cnf.extend([[s+1] for s in LOCAL])
    assert len(cnf.clauses) == 19808
    return domain, base, cnf, metadata


def inspect(selected, domain, require_local=True):
    _, gram, triples, signatures, _, _, _ = domain
    assert selected == sorted(set(selected)) and len(selected) == 72
    assert all(0 <= s < 252 for s in selected)
    assert all(sum(i in signatures[s] and j in signatures[s] for s in selected) == gram[i][j]
               for i in range(27) for j in range(27))
    if require_local:
        assert set(LOCAL) <= set(selected)
        assert [s for s in selected if signatures[s][0] == 0] == LOCAL
    a = sum(universe.rook(triples[s][0], triples[s][2]) and universe.rook(triples[s][1], triples[s][2])
            for s in selected)
    return {'selected_signatures': selected, 'selected_triples': [list(triples[s]) for s in selected],
            'a': a, 'dense_Gram_entries_checked': 729, 'first_local_set_required': require_local,
            'matching_unspecified': True, 'exterior_edges_unspecified': True, 'complete_graph': False}


def positive_control(domain, base):
    triples = domain[2]
    position = {triple: s for s, triple in enumerate(triples)}
    permutation = (0, 5, 7, 8, 6, 1, 4, 2, 3)
    add = lambda p, q: 3*((p//3+q//3) % 3)+(p % 3+q % 3) % 3
    sub = lambda p, q: 3*((p//3-q//3) % 3)+(p % 3-q % 3) % 3
    chosen = sorted(position[p, add(t, permutation[sub(p, t)]), t]
                    for t in range(9) for p in range(9) if p != t)
    witness = inspect(chosen, domain, False)
    assert witness['a'] == 0
    with Solver(name='glucose3', bootstrap_with=base.clauses) as solver:
        assert solver.solve(assumptions=[s+1 if s in chosen else -s-1 for s in range(252)])
    return {'unconditioned_Gram_baseline_positive_control': 'explicit72-column incidence accepted',
            'witness': witness, 'no_a_constraint_added_to_main_model': True}


def cold_replay(directory, checker, output):
    model = json.loads((directory/'model.json').read_text())
    result = json.loads((directory/'result.json').read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert result['model_sha256'] == digest(directory/'model.json')
    domain, _, cnf, _ = build()
    with tempfile.TemporaryDirectory(prefix='conway35-local-Gram-control-') as temporary:
        path = Path(temporary)/'rebuilt.cnf'
        cnf.to_file(path)
        assert digest(path) == model['cnf_sha256']
    record = {'status': 'full Gram-only formula cold rebuilt', 'model_sha256': digest(directory/'model.json'),
              'cnf_sha256': model['cnf_sha256'], 'unit_selectors': [s+1 for s in LOCAL],
              'learned_or_matching_constraints': 0}
    if result['status'].startswith('SAT;'):
        actual = inspect(result['witness']['selected_signatures'], domain)
        assert json.loads(json.dumps(actual)) == result['witness']
        record.update(status='SAT incidence witness and full conditional Gram CNF cold replay passed',
                      dense_Gram_entries_checked=729, a=actual['a'], complete_graph=False)
    elif result['status'].startswith('UNSAT with direct DRAT;'):
        certificate = result['certificate']
        retained, proof = directory/'retained.cnf', directory/'retained.drat'
        assert digest(retained) == certificate['cnf_sha256'] and digest(proof) == certificate['proof_sha256']
        needed = {tuple(sorted(clause)) for clause in encoder.read_clauses(retained)}
        needed.difference_update(tuple(sorted(clause)) for clause in cnf.clauses)
        assert not needed
        checked = subprocess.run([str(checker), str(retained), str(proof), '-t', '60', '-w'],
                                 capture_output=True, text=True, timeout=65, check=False)
        log = output.with_suffix('.drat.log')
        log.write_text(checked.stdout+checked.stderr)
        assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
        record.update(status='Gram-only full-CNF rebuild, retained inclusion, and DRAT replay passed',
                      first_local_set_excluded=True, whole_complementary_core_excluded=False,
                      checker_log=portable(log), checker_log_sha256=digest(log))
    else:
        assert result['status'].startswith('UNKNOWN;')
        record['status'] = 'UNKNOWN binding checked; local-set incidence remains open'
    assert not output.exists()
    output.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2), flush=True)
    return record


def run(directory, checker):
    assert not directory.exists()
    directory.mkdir(parents=True)
    domain, base, cnf, metadata = build()
    control = positive_control(domain, base)
    path = directory/'full.cnf'
    cnf.to_file(path)
    model = {'status': 'Gram-only conditional incidence formula built',
             'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in SOURCES},
             'base_domain_sha256': domain[-1], 'unit_selectors': [s+1 for s in LOCAL],
             'selected_local_signature_indices': LOCAL, 'primary_variables': 252,
             'variables': cnf.nv, 'clauses': len(cnf.clauses), 'Gram_clauses': 19800,
             'cnf_sha256': digest(path), 'matching_constraints': 0, 'attachment_constraints': 0,
             'learned_pattern_constraints': 0, 'exterior_edge_variables': 0,
             'requested_solver_seconds_including_bootstrap': 10, 'direct_checker_seconds': 60,
             'positive_control': control}
    (directory/'model.json').write_text(json.dumps(model, indent=2)+'\n')
    result = {'status': 'running Gram-only local-set control', 'model_sha256': digest(directory/'model.json')}
    result_path = directory/'result.json'
    result_path.write_text(json.dumps(result, indent=2)+'\n')
    started = time.monotonic()
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
        result['bootstrap_seconds'] = time.monotonic()-started
        timer = Timer(max(0.001, 10-result['bootstrap_seconds']), solver.interrupt)
        timer.start()
        try:
            answer = solver.solve_limited(expect_interrupt=True)
        finally:
            timer.cancel()
        result['solve_return_seconds'] = time.monotonic()-started
        result['solver_statistics'] = solver.accum_stats()
        if answer is None:
            result['status'] = 'UNKNOWN; local-set Gram incidence remains open'
        elif answer:
            positive = {literal for literal in solver.get_model() if literal > 0}
            result['witness'] = inspect([s for s in range(252) if s+1 in positive], domain)
            result['status'] = 'SAT; exact72-column local-set incidence control'
        else:
            proof = solver.get_proof()
            assert proof is not None
            if not proof or proof[-1] != '0':
                proof.append('0')
            raw = directory/'raw.drat'
            raw.write_text('\n'.join(proof)+'\n')
            result.update(status='solver UNSAT; direct DRAT pending', raw_proof_sha256=digest(raw))
    result_path.write_text(json.dumps(result, indent=2)+'\n')
    if result['status'].startswith('solver UNSAT;'):
        retained, proof, log = directory/'retained.cnf', directory/'retained.drat', directory/'direct-drat.log'
        checked = subprocess.run([str(checker), str(path), str(directory/'raw.drat'), '-t', '60', '-w',
                                  '-c', str(retained), '-l', str(proof)], capture_output=True, text=True,
                                 timeout=65, check=False)
        log.write_text(checked.stdout+checked.stderr)
        assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
        result['certificate'] = {'cnf_sha256': digest(retained), 'proof_sha256': digest(proof),
                                 'retained_input_clauses': sum(1 for _ in encoder.read_clauses(retained)),
                                 'checker_log_sha256': digest(log)}
        result['status'] = 'UNSAT with direct DRAT; cold Gram-only rebuild pending'
    result['elapsed_seconds'] = time.monotonic()-started
    result_path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'witness'}, indent=2), flush=True)
    cold_replay(directory, checker, directory/'cold-replay.json')
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    parser.add_argument('--replay-output', type=Path)
    args = parser.parse_args()
    if args.replay_output:
        cold_replay(args.directory.resolve(), args.drat_trim.resolve(), args.replay_output.resolve())
    else:
        run(args.directory.resolve(), args.drat_trim.resolve())
