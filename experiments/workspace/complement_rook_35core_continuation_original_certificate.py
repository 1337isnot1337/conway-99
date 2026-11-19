"""Compressed original-only proof package for a completed continuation.

Keep the immutable discovery results unchanged. Publish deterministic gzip
copies of their retained inputs/proofs, with raw and compressed hashes.
Replay reconstructs each original incidence formula and imports no Gram
downdate or overlay source. Only cases whose retained inputs all belong
to the original formula are admitted to this package.
"""

import argparse
import gzip
import json
from pathlib import Path
import subprocess
import tempfile

import complement_rook_35core_incidence as original


ROOT, LOGS = original.ROOT, original.LOGS
CASES = [4, 5, 6, 7, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 27]
PREPARATION = LOGS/'complement-rook-35core-first-local-continuation01-preparation/terminal.json'
PREPARATION_SHA = 'ee319b468a77ce7783dedcaf5828ad31331de99902aa8ad9c648ffbdd7dc35a2'
digest, portable = original.digest, original.portable


def prepare(terminal_path, directory):
    assert not directory.exists() and digest(PREPARATION) == PREPARATION_SHA
    terminal = json.loads(terminal_path.read_text())
    assert terminal['requested_cases'] == CASES
    assert terminal['complete_requested_queries'] and terminal['completed_cases'] == CASES
    assert terminal['preparation_terminal_sha256'] == PREPARATION_SHA
    for name, value in terminal['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == value
    prepared = json.loads(PREPARATION.read_text())
    models = {r['case_index']: r for r in prepared['case_records']}
    directory.mkdir(parents=True)
    records, not_covered = [], []
    for outcome in terminal['case_records']:
        if not outcome['status'].startswith('certified UNSAT:'):
            continue
        index = outcome['case_index']
        if not outcome['original_only_proof_binding_verified']:
            not_covered.append(index)
            continue
        assert outcome['retained_nonoriginal_Gram_inputs'] == 0
        result_path, cold_path = ROOT/outcome['result'], ROOT/outcome['cold_replay']
        assert digest(result_path) == outcome['result_sha256']
        assert digest(cold_path) == outcome['cold_replay_sha256']
        result, cold = json.loads(result_path.read_text()), json.loads(cold_path.read_text())
        assert cold['original_only_proof_binding_verified'] and cold['retained_distinct_inputs_outside_original_formula'] == 0
        assert cold['excluded_indexed_core'] == index and result['case_index'] == index
        assert result['status'].startswith('UNSAT with direct DRAT;')
        model_path = ROOT/models[index]['model']
        assert digest(model_path) == models[index]['model_sha256'] == outcome['model_sha256'] == result['model_sha256']
        overlay = json.loads(model_path.read_text())
        base_path = ROOT/overlay['base_model']
        assert digest(base_path) == overlay['base_model_sha256']
        base = original.checked_model(base_path)
        assert base['case']['index'] == index and base['cnf_sha256'] == cold['base_cnf_sha256']
        record = {'case_index': index, 'original_model': portable(base_path),
                  'original_model_sha256': digest(base_path), 'original_cnf_sha256': base['cnf_sha256'],
                  'original_source_hashes': base['source_hashes'],
                  'original_domain_record_sha256': base['domain_record_sha256'],
                  'discovery_result': portable(result_path), 'discovery_result_sha256': digest(result_path),
                  'discovery_cold_replay': portable(cold_path), 'discovery_cold_replay_sha256': digest(cold_path),
                  'retained_input_clauses': result['retained_certificate']['input_clauses']}
        for key, name in [('cnf', 'inputs.cnf'), ('proof', 'proof.drat')]:
            source = ROOT/result['retained_certificate'][key]
            raw = source.read_bytes()
            assert original.domains.sha(raw) == result['retained_certificate'][key+'_sha256']
            destination = directory/f'case{index:04d}-{name}.gz'
            destination.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
            assert gzip.decompress(destination.read_bytes()) == raw
            record[key] = {'gzip': portable(destination), 'gzip_sha256': digest(destination),
                           'gzip_bytes': destination.stat().st_size, 'raw_sha256': original.domains.sha(raw),
                           'raw_bytes': len(raw), 'discovery_raw_path': portable(source)}
        records.append(record)
    assert sorted([record['case_index'] for record in records]+not_covered) == sorted(terminal['certified_unsat_cases'])
    certificate = {'status': 'compressed original-only retained certificates prepared; cold replay required',
                   'source_sha256': digest(Path(__file__)),
                   'continuation_terminal': portable(terminal_path), 'continuation_terminal_sha256': digest(terminal_path),
                   'preparation_terminal_sha256': PREPARATION_SHA, 'cases': records,
                   'certified_cases_not_covered_by_this_original_only_package': not_covered,
                   'original_only': True, 'whole_local_set_excluded': False,
                   'replay_imports_no_downdate_or_overlay_source': True, 'new_solver_queries': 0}
    path = directory/'certificate.json'
    path.write_text(json.dumps(certificate, indent=2)+'\n')
    print(json.dumps({'certificate': portable(path), 'certificate_sha256': digest(path),
                      'cases': [r['case_index'] for r in records],
                      'compressed_bytes': sum(r[k]['gzip_bytes'] for r in records for k in ('cnf', 'proof')),
                      'raw_bytes': sum(r[k]['raw_bytes'] for r in records for k in ('cnf', 'proof'))}, indent=2), flush=True)


def replay(certificate_path, directory, checker, seconds):
    assert not directory.exists() and 0 < seconds <= 60
    certificate = json.loads(certificate_path.read_text())
    assert certificate['source_sha256'] == digest(Path(__file__))
    terminal_path = ROOT/certificate['continuation_terminal']
    assert digest(terminal_path) == certificate['continuation_terminal_sha256']
    terminal = json.loads(terminal_path.read_text())
    assert terminal['requested_cases'] == terminal['completed_cases'] == CASES and terminal['complete_requested_queries']
    directory.mkdir(parents=True)
    reports = []
    for record in certificate['cases']:
        index = record['case_index']
        assert index in terminal['certified_unsat_cases']
        base_path = ROOT/record['original_model']
        assert digest(base_path) == record['original_model_sha256']
        base = original.checked_model(base_path)
        assert base['source_hashes'] == record['original_source_hashes']
        data, cnf, metadata = original.rebuild(index)
        assert data[2]['index'] == index == base['case']['index']
        assert metadata == base['formula']
        assert original.domains.sha(original.canonical(data[3])) == record['original_domain_record_sha256'] == base['domain_record_sha256']
        with tempfile.TemporaryDirectory(prefix=f'conway35-original-case{index}-') as temporary:
            temporary = Path(temporary)
            full = temporary/'original.cnf'
            cnf.to_file(full)
            assert digest(full) == record['original_cnf_sha256'] == base['cnf_sha256']
            paths = {}
            for key in ('cnf', 'proof'):
                archive = ROOT/record[key]['gzip']
                assert digest(archive) == record[key]['gzip_sha256']
                raw = gzip.decompress(archive.read_bytes())
                assert original.domains.sha(raw) == record[key]['raw_sha256'] and len(raw) == record[key]['raw_bytes']
                paths[key] = temporary/('retained.cnf' if key == 'cnf' else 'retained.drat')
                paths[key].write_bytes(raw)
            inputs = list(original.read_clauses(paths['cnf']))
            assert len(inputs) == record['retained_input_clauses']
            needed = {tuple(sorted(clause)) for clause in inputs}
            needed.difference_update(tuple(sorted(clause)) for clause in cnf.clauses)
            assert not needed
            checked = subprocess.run([str(checker), str(paths['cnf']), str(paths['proof']), '-t', str(seconds), '-w'],
                                     capture_output=True, text=True, timeout=seconds+5, check=False)
            log = directory/f'case{index:04d}.drat.log'
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
        report = {'status': 'PASS: gzip/raw bindings, cold original formula, original-only retained inclusion and DRAT',
                  'case_index': index, 'original_cnf_sha256': base['cnf_sha256'],
                  'retained_input_clauses': len(inputs), 'nonoriginal_retained_inputs': 0,
                  'proof_raw_sha256': record['proof']['raw_sha256'],
                  'checker_log': portable(log), 'checker_log_sha256': digest(log),
                  'new_solver_queries': 0, 'downdate_sources_imported': False, 'whole_local_set_excluded': False}
        (directory/f'case{index:04d}-replay.json').write_text(json.dumps(report, indent=2)+'\n')
        reports.append(report)
        print(json.dumps(report), flush=True)
    summary = {'status': 'all packaged original-only certificates replayed',
               'source_sha256': digest(Path(__file__)), 'certificate_sha256': digest(certificate_path),
               'cases': reports, 'new_solver_queries': 0, 'whole_local_set_excluded': False}
    (directory/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--terminal', type=Path, required=True)
    prep.add_argument('--directory', type=Path, required=True)
    check = commands.add_parser('replay')
    check.add_argument('--certificate', type=Path, required=True)
    check.add_argument('--directory', type=Path, required=True)
    check.add_argument('--checker', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    check.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.terminal.resolve(), args.directory.resolve())
    else:
        replay(args.certificate.resolve(), args.directory.resolve(), args.checker.resolve(), args.seconds)
