"""Append886 checked Gram-downdate clauses to frozen35-core case2.

The original domain and every original clause remain unchanged. Preparation
and cold replay rebuild the complete original formula, verify the exact
negative-vector certificate, and append precisely the saved binary fragment.
A query uses one fresh proof-enabled solver for at most60 seconds including
bootstrap. Only the indexed case2 is in scope.
"""

import argparse
import gc
import gzip
import json
from pathlib import Path
import resource
import subprocess
import tempfile
from threading import Timer
import time

from pysat.formula import CNF
from pysat.solvers import Solver

import complement_rook_35core_incidence as original
import complement_rook_35core_gram_downdate as downdate


ROOT, LOGS = original.ROOT, original.LOGS
BASE_MODEL = LOGS/'complement-rook-35core-first-local-sweep01/case0002-model.json'
BASE_MODEL_SHA = '84793fff0bfbb7bcbeb5b50974dfefad596b4dc72fa35619190eb1b871082883'
CERTIFICATE = LOGS/'complement-rook-35core-case0002-gram-downdate.json.gz'
CERTIFICATE_SHA = 'de5cbe02ea5cda392b139bed8e7468fc75e6e37bb7619aad8e743a396c859294'
FRAGMENT = LOGS/'complement-rook-35core-case0002-gram-downdate-clauses.cnf'
FRAGMENT_SHA = 'a86af34800a77f1a07f72d823e02d2832fecb39eb8775ce2526c0a7f5806d25e'
SOURCES = ('complement_rook_35core_gram_downdate_overlay.py',
           'complement_rook_35core_gram_downdate.py', *original.SOURCES)
digest, portable = original.digest, original.portable


def inputs():
    assert digest(BASE_MODEL) == BASE_MODEL_SHA
    base = original.checked_model(BASE_MODEL)
    assert base['case']['index'] == 2
    assert digest(CERTIFICATE) == CERTIFICATE_SHA and digest(FRAGMENT) == FRAGMENT_SHA
    raw = gzip.decompress(CERTIFICATE.read_bytes())
    saved = json.loads(raw)
    for name, expected in saved['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    actual = downdate.build(saved)
    assert downdate.canonical(actual)+b'\n' == raw
    assert FRAGMENT.read_bytes() == downdate.clause_bytes(actual)
    assert actual['case'] == base['case']
    assert actual['bindings']['case_domain_record_sha256'] == base['domain_record_sha256']
    assert actual['bindings']['column_domain_sha256'] == base['column_domain_sha256']
    assert actual['bindings']['Gram_sha256'] == base['Gram_sha256']
    clauses = [list(clause) for clause in original.read_clauses(FRAGMENT)]
    assert len(clauses) == len({tuple(clause) for clause in clauses}) == 886
    assert all(len(clause) == 2 and all(-1287 <= literal <= -1 for literal in clause) for clause in clauses)
    return base, actual, clauses


def append_bytes(base_bytes, base, clauses):
    first, body = base_bytes.split(b'\n', 1)
    variables, count = base['formula']['variables'], base['formula']['clauses']
    assert first == f'p cnf {variables} {count}'.encode()
    assert body.endswith(b'\n') and body.count(b'\n') == count
    assert (variables, count) == (114512, 233919)
    extra = ''.join(' '.join(map(str, clause))+' 0\n' for clause in clauses).encode()
    assert len(clauses) == 886 and extra.count(b'\n') == 886
    return f'p cnf {variables} {count+len(clauses)}\n'.encode()+body+extra


def rebuild():
    base, certificate, clauses = inputs()
    data, cnf, metadata = original.rebuild(2)
    assert metadata == base['formula']
    assert data[2] == base['case'] and data[3]['columns'] == certificate['attachment_columns']
    assert data[5] == certificate['Gram']
    assert original.domains.sha(original.canonical(data[3])) == base['domain_record_sha256']
    with tempfile.TemporaryDirectory(prefix='conway35-downdate-base-') as directory:
        path = Path(directory)/'original.cnf'
        cnf.to_file(path)
        raw = path.read_bytes()
    assert original.domains.sha(raw) == base['cnf_sha256']
    overlay = append_bytes(raw, base, clauses)
    return base, certificate, clauses, data, cnf, overlay


def prepare(model_path, cnf_path):
    assert not model_path.exists() and not cnf_path.exists()
    started = time.monotonic()
    base, certificate, clauses, data, cnf, overlay = rebuild()
    assert original.domains.sha(Path(base['cnf']).read_bytes()) == base['cnf_sha256']
    assert overlay == append_bytes(Path(base['cnf']).read_bytes(), base, clauses)
    cnf_path.write_bytes(overlay)
    model = {
        'status': 'case2 original formula plus886 exact Gram-downdate clauses prepared; not solved',
        'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in SOURCES},
        'base_model': portable(BASE_MODEL), 'base_model_sha256': BASE_MODEL_SHA,
        'base_cnf_sha256': base['cnf_sha256'],
        'certificate': portable(CERTIFICATE), 'certificate_sha256': CERTIFICATE_SHA,
        'binary_fragment': portable(FRAGMENT), 'binary_fragment_sha256': FRAGMENT_SHA,
        'case': base['case'], 'column_domain_sha256': base['column_domain_sha256'],
        'domain_record_sha256': base['domain_record_sha256'], 'Gram_sha256': base['Gram_sha256'],
        'cnf': str(cnf_path.resolve()), 'cnf_sha256': digest(cnf_path),
        'formula': {'primary_columns': 1287, 'variables': cnf.nv,
                    'original_clauses': len(cnf.clauses), 'additional_binary_clauses': len(clauses),
                    'clauses': len(cnf.clauses)+len(clauses), 'original_body_unchanged': True},
        'controls': {'full_original_domain_and_CNF_cold_rebuilt': True,
                     'all886_integer_negative_vectors_directly_checked': True,
                     'exact886_clause_bytes_checked': True,
                     'all_original_columns_retained': True, 'new_auxiliary_variables': 0},
        'graph_automorphism_assumptions': 0, 'other_cases_tested': False,
        'SAT_scope': 'necessary64-column incidence witness for indexed35-core case2; exterior graph unspecified',
        'UNSAT_scope': 'indexed35-core case2 only, after retained proof and full binding replay',
        'preparation_seconds': time.monotonic()-started,
    }
    assert model['formula']['variables'] == 114512 and model['formula']['clauses'] == 234805
    model_path.write_text(json.dumps(model, indent=2)+'\n')
    print(json.dumps(model, indent=2), flush=True)


def checked_model(model_path, require_cnf=False):
    model = json.loads(model_path.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    for path_key, hash_key in [('base_model', 'base_model_sha256'),
                               ('certificate', 'certificate_sha256'),
                               ('binary_fragment', 'binary_fragment_sha256')]:
        assert digest(ROOT/model[path_key]) == model[hash_key]
    assert model['base_model_sha256'] == BASE_MODEL_SHA
    assert model['certificate_sha256'] == CERTIFICATE_SHA and model['binary_fragment_sha256'] == FRAGMENT_SHA
    assert model['case']['index'] == 2
    if require_cnf:
        assert digest(Path(model['cnf'])) == model['cnf_sha256']
    return model


def inspect(selected):
    data = original.load(2)
    witness = original.inspect(selected, data)
    chosen = {column+1 for column in selected}
    clauses = list(original.read_clauses(FRAGMENT))
    assert len(clauses) == 886
    assert all(not all(-literal in chosen for literal in clause) for clause in clauses)
    witness['additional_downdate_clauses_checked'] = len(clauses)
    return witness


def solve(model_path, directory, seconds, checker, checker_seconds):
    assert not directory.exists() and 0 < seconds <= 60 and 0 < checker_seconds <= 60
    directory.mkdir(parents=True)
    model = checked_model(model_path, require_cnf=True)
    result = {'status': 'running one fresh case2 Gram-downdate overlay query',
              'model': portable(model_path), 'model_sha256': digest(model_path),
              'source_sha256': digest(Path(__file__)), 'cnf_sha256': model['cnf_sha256'],
              'case_index': 2, 'seconds_including_bootstrap': seconds,
              'direct_checker_seconds': checker_seconds, 'assumptions': [],
              'scope': 'one indexed35-core; no other matching cases',
              'whole_local_set_or_complementary_rook_core_excluded': False,
              'full_graph_completion': False}
    output = directory/'result.json'
    def save():
        result['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        output.write_text(json.dumps(result, indent=2)+'\n')
    started = time.monotonic()
    save()
    try:
        cnf = CNF(from_file=model['cnf'])
        assert (cnf.nv, len(cnf.clauses)) == (model['formula']['variables'], model['formula']['clauses'])
        with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
            del cnf
            gc.collect()
            result['bootstrap_seconds'] = time.monotonic()-started
            timer = Timer(max(0.001, seconds-result['bootstrap_seconds']), solver.interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
            result['solver_return_seconds'] = time.monotonic()-started
            result['solver_statistics'] = solver.accum_stats()
            if answer is None:
                result['status'] = 'UNKNOWN; indexed35-core case2 remains unresolved'
            elif answer:
                positive = {value for value in solver.get_model() if value > 0}
                selected = [i for i in range(model['formula']['primary_columns']) if i+1 in positive]
                result['incidence_witness'] = inspect(selected)
                result['status'] = 'SAT; exact case2 incidence witness checked, exterior graph unspecified'
            else:
                proof = solver.get_proof()
                assert proof is not None
                result['terminal_empty_clause_appended'] = not proof or proof[-1] != '0'
                if result['terminal_empty_clause_appended']:
                    proof.append('0')
                raw = directory/'raw.drat'
                raw.write_text('\n'.join(proof)+'\n')
                result.update(status='solver UNSAT; direct proof check pending',
                              raw_proof=portable(raw), raw_proof_sha256=digest(raw), raw_proof_lines=len(proof))
        save()
        if result['status'].startswith('solver UNSAT;'):
            retained, trimmed, log = directory/'retained.cnf', directory/'retained.drat', directory/'direct-drat.log'
            checked = subprocess.run([str(checker), model['cnf'], str(ROOT/result['raw_proof']),
                                      '-t', str(checker_seconds), '-w', '-c', str(retained), '-l', str(trimmed)],
                                     capture_output=True, text=True, timeout=checker_seconds+5, check=False)
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            inputs = list(original.read_clauses(retained))
            needed = {tuple(sorted(clause)) for clause in inputs}
            for clause in original.read_clauses(Path(model['cnf'])):
                needed.discard(tuple(sorted(clause)))
            assert not needed
            result['retained_certificate'] = {
                'cnf': portable(retained), 'cnf_sha256': digest(retained),
                'proof': portable(trimmed), 'proof_sha256': digest(trimmed),
                'input_clauses': len(inputs), 'checker_log': portable(log),
                'checker_log_sha256': digest(log)}
            result['status'] = 'UNSAT with direct DRAT; cold full rebuild and proof replay required'
        result['elapsed_seconds'] = time.monotonic()-started
        save()
    except Exception as error:
        result.update(status='error; no unchecked exclusion promoted', error_type=type(error).__name__,
                      error_message=str(error), elapsed_seconds=time.monotonic()-started)
        save()
        raise
    print(json.dumps({key: value for key, value in result.items() if key != 'incidence_witness'}, indent=2), flush=True)


def replay(model_path, result_path, checker, checker_seconds, output):
    assert not output.exists() and 0 < checker_seconds <= 60
    model = checked_model(model_path)
    base, certificate, clauses, data, cnf, overlay = rebuild()
    assert original.domains.sha(overlay) == model['cnf_sha256']
    assert base['cnf_sha256'] == model['base_cnf_sha256']
    assert model['formula'] == {'primary_columns': 1287, 'variables': cnf.nv,
                                'original_clauses': len(cnf.clauses),
                                'additional_binary_clauses': len(clauses),
                                'clauses': len(cnf.clauses)+len(clauses),
                                'original_body_unchanged': True}
    report = {'status': 'cold original formula, exact negative vectors and overlay bytes replay passed',
              'model_sha256': digest(model_path), 'base_cnf_sha256': base['cnf_sha256'],
              'overlay_cnf_sha256': model['cnf_sha256'], 'case_index': 2,
              'all886_direct_negative_vectors_checked': True,
              'whole_local_set_or_complementary_rook_core_excluded': False,
              'full_graph_completion': False}
    if result_path:
        result = json.loads(result_path.read_text())
        assert result['model_sha256'] == digest(model_path) and result['cnf_sha256'] == model['cnf_sha256']
        assert result['source_sha256'] == digest(Path(__file__)) and result['case_index'] == 2
        if result['status'].startswith('SAT;'):
            actual = inspect(result['incidence_witness']['selected_columns'])
            assert actual == result['incidence_witness']
            report['status'] = 'cold full formula and exact case2 incidence witness replay passed'
        elif result['status'].startswith('UNSAT with direct DRAT;'):
            proof_record = result['retained_certificate']
            retained, proof = ROOT/proof_record['cnf'], ROOT/proof_record['proof']
            assert digest(retained) == proof_record['cnf_sha256'] and digest(proof) == proof_record['proof_sha256']
            inputs = list(original.read_clauses(retained))
            assert len(inputs) == proof_record['input_clauses']
            needed = {tuple(sorted(clause)) for clause in inputs}
            needed.difference_update(tuple(sorted(clause)) for clause in cnf.clauses)
            needed.difference_update(tuple(sorted(clause)) for clause in clauses)
            assert not needed
            checked = subprocess.run([str(checker), str(retained), str(proof), '-t', str(checker_seconds), '-w'],
                                     capture_output=True, text=True, timeout=checker_seconds+5, check=False)
            log = output.with_suffix('.drat.log')
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            overlay_clause_set = {tuple(sorted(clause)) for clause in clauses}
            report.update(status='cold original/overlay rebuild, exact pair certificates, retained inclusion and DRAT passed',
                          excluded_scope='indexed35-core case2 only', retained_input_clauses=len(inputs),
                          retained_downdate_clauses=sum(tuple(sorted(clause)) in overlay_clause_set for clause in inputs),
                          checker_log=portable(log), checker_log_sha256=digest(log))
        else:
            assert result['status'].startswith('UNKNOWN;')
            report['status'] = 'cold formula and UNKNOWN binding checked; no exclusion'
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--model', type=Path, required=True)
    prep.add_argument('--cnf', type=Path, required=True)
    run = commands.add_parser('solve')
    run.add_argument('--model', type=Path, required=True)
    run.add_argument('--directory', type=Path, required=True)
    run.add_argument('--seconds', type=float, default=60)
    run.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    run.add_argument('--checker-seconds', type=int, default=60)
    check = commands.add_parser('replay')
    check.add_argument('--model', type=Path, required=True)
    check.add_argument('--result', type=Path)
    check.add_argument('--output', type=Path, required=True)
    check.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    check.add_argument('--checker-seconds', type=int, default=60)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.model.resolve(), args.cnf.resolve())
    elif args.command == 'solve':
        solve(args.model.resolve(), args.directory.resolve(), args.seconds,
              args.drat_trim.resolve(), args.checker_seconds)
    else:
        replay(args.model.resolve(), args.result.resolve() if args.result else None,
               args.drat_trim.resolve(), args.checker_seconds, args.output.resolve())
