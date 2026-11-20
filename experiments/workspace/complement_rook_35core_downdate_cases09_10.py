"""Fresh exact overlays for35-core cases9 and10, and no other cases.

Append only their839/490 certified binary conflicts to the frozen original
CNF bodies. Reuse the immutable, audited incidence solve routine; the model
binds this wrapper and every certificate source. Cold replay rebuilds the
original formula, all exact cuts, and the overlay. No symmetry is imposed.
"""

import argparse
import gzip
import json
from pathlib import Path
import subprocess
import tempfile
import time

import complement_rook_35core_incidence as original
import complement_rook_35core_downdate_census as census


ROOT, LOGS = original.ROOT, original.LOGS
MANIFEST = LOGS/'complement-rook-35core-first-local-downdates01-artifacts.json'
MANIFEST_SHA = '21c3aeddd103d6146699a0f0efc88b80e348c9f066db1402de9d81432994c185'
TERMINAL = LOGS/'complement-rook-35core-first-local-downdates01/terminal.json'
EXPECTED = {9: 839, 10: 490}
SOURCES = ('complement_rook_35core_downdate_cases09_10.py', *original.SOURCES, *census.SOURCES)
digest, portable, canonical = original.digest, original.portable, original.canonical


def inputs(case_index):
    assert case_index in EXPECTED and digest(MANIFEST) == MANIFEST_SHA
    manifest = json.loads(MANIFEST.read_text())
    hashes = {item['path']: item['sha256'] for item in manifest['artifacts']}
    assert digest(TERMINAL) == hashes[portable(TERMINAL)]
    terminal = json.loads(TERMINAL.read_text())
    assert terminal['complete'] and terminal['completed_cases'] == census.CASES
    for name, expected in terminal['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    item = next(record for record in terminal['case_records'] if record['case_index'] == case_index)
    cert_path, fragment = ROOT/item['certificate'], ROOT/item['binary_fragment']
    assert digest(cert_path) == item['certificate_sha256'] and digest(fragment) == item['binary_fragment_sha256']
    raw = gzip.decompress(cert_path.read_bytes())
    assert original.domains.sha(raw) == item['decompressed_certificate_sha256']
    saved = json.loads(raw)
    actual = census.build(case_index, census.context(), saved=saved)
    assert canonical(actual)+b'\n' == raw and census.clauses(actual) == fragment.read_bytes()
    base_path = ROOT/saved['original_model']
    assert digest(base_path) == saved['original_model_sha256']
    base = original.checked_model(base_path)
    assert base['case'] == saved['case']
    for key in ('domain_record_sha256', 'column_domain_sha256', 'Gram_sha256'):
        assert base[key] == saved[key]
    assert base['cnf_sha256'] == saved['original_cnf_sha256']
    clauses = list(original.read_clauses(fragment))
    assert len(clauses) == len({tuple(c) for c in clauses}) == EXPECTED[case_index]
    assert all(len(c) == 2 and all(-len(saved['attachment_columns']) <= v < 0 for v in c) for c in clauses)
    return base_path, base, cert_path, fragment, saved, clauses


def append_bytes(raw, base, clauses):
    first, body = raw.split(b'\n', 1)
    n, count = base['formula']['variables'], base['formula']['clauses']
    assert first == f'p cnf {n} {count}'.encode()
    assert body.endswith(b'\n') and body.count(b'\n') == count
    tail = ''.join(' '.join(map(str, c))+' 0\n' for c in clauses).encode()
    return f'p cnf {n} {count+len(clauses)}\n'.encode()+body+tail


def rebuild(case_index):
    base_path, base, cert_path, fragment, certificate, clauses = inputs(case_index)
    data, cnf, metadata = original.rebuild(case_index)
    assert metadata == base['formula']
    assert data[3]['columns'] == certificate['attachment_columns'] and data[5] == certificate['Gram']
    with tempfile.TemporaryDirectory(prefix=f'conway35-case{case_index}-base-') as directory:
        path = Path(directory)/'base.cnf'
        cnf.to_file(path)
        raw = path.read_bytes()
    assert original.domains.sha(raw) == base['cnf_sha256']
    return base_path, base, cert_path, fragment, data, cnf, clauses, append_bytes(raw, base, clauses)


def prepare(case_index, model_path, cnf_path):
    assert not model_path.exists() and not cnf_path.exists()
    started = time.monotonic()
    base_path, base, cert_path, fragment, data, cnf, clauses, raw = rebuild(case_index)
    assert digest(Path(base['cnf'])) == base['cnf_sha256']
    assert raw == append_bytes(Path(base['cnf']).read_bytes(), base, clauses)
    cnf_path.write_bytes(raw)
    model = {'status': 'fresh original formula plus certified pair clauses prepared; not solved',
             'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in SOURCES},
             'prefix_certificate_sha256': original.PREFIX_SHA,
             'census_artifact_manifest': portable(MANIFEST), 'census_artifact_manifest_sha256': MANIFEST_SHA,
             'base_model': portable(base_path), 'base_model_sha256': digest(base_path),
             'base_cnf_sha256': base['cnf_sha256'],
             'certificate': portable(cert_path), 'certificate_sha256': digest(cert_path),
             'binary_fragment': portable(fragment), 'binary_fragment_sha256': digest(fragment),
             'case': base['case'], 'domain_record_sha256': base['domain_record_sha256'],
             'column_domain_sha256': base['column_domain_sha256'], 'Gram_sha256': base['Gram_sha256'],
             'cnf': str(cnf_path.resolve()), 'cnf_sha256': digest(cnf_path),
             'formula': {'primary_columns': len(data[3]['columns']), 'variables': cnf.nv,
                         'original_clauses': len(cnf.clauses), 'additional_binary_clauses': len(clauses),
                         'clauses': len(cnf.clauses)+len(clauses)},
             'controls': {'cold_original_CNF_hash_matched': True, 'all_exact_certificate_tests_replayed': True,
                          'every_added_clause_has_direct_integer_negative_vector': True,
                          'original_body_unchanged': True, 'new_variables': 0},
             'solver_implementation': 'unmodified complement_rook_35core_incidence.solve',
             'maximum_query_seconds_including_bootstrap': 60,
             'scope': 'one indexed35-core only; no fixed incidence or graph symmetry',
             'preparation_seconds': time.monotonic()-started}
    model_path.write_text(json.dumps(model, indent=2)+'\n')
    print(json.dumps(model, indent=2), flush=True)


def checked(model_path, require_cnf=False):
    model = original.checked_model(model_path, require_cnf)
    assert model['case']['index'] in EXPECTED
    assert model['census_artifact_manifest_sha256'] == MANIFEST_SHA == digest(MANIFEST)
    for key in ('base_model', 'certificate', 'binary_fragment'):
        assert digest(ROOT/model[key]) == model[key+'_sha256']
    assert model['formula']['additional_binary_clauses'] == EXPECTED[model['case']['index']]
    return model


def witness_overlay_check(model, witness):
    selected = set(witness['selected_columns'])
    clauses = list(original.read_clauses(ROOT/model['binary_fragment']))
    assert all(not all(-value-1 in selected for value in clause) for clause in clauses)
    return {'status': 'all certified binary overlay clauses satisfied by the exact original incidence witness',
            'case_index': model['case']['index'], 'binary_clauses_checked': len(clauses), 'full_graph': False}


def solve(model_path, directory, seconds, checker, checker_seconds):
    assert 0 < seconds <= 60 and 0 < checker_seconds <= 60
    model = checked(model_path, True)
    result = original.solve(model_path, directory, seconds, checker, checker_seconds)
    if result['status'].startswith('SAT;'):
        report = witness_overlay_check(model, result['incidence_witness'])
        (directory/'overlay-witness-check.json').write_text(json.dumps(report, indent=2)+'\n')


def replay(model_path, result_path, output, checker, checker_seconds):
    assert not output.exists() and 0 < checker_seconds <= 60
    model = checked(model_path)
    index = model['case']['index']
    base_path, base, cert_path, fragment, data, cnf, clauses, raw = rebuild(index)
    assert original.domains.sha(raw) == model['cnf_sha256']
    assert model['formula'] == {'primary_columns': len(data[3]['columns']), 'variables': cnf.nv,
                                'original_clauses': len(cnf.clauses), 'additional_binary_clauses': len(clauses),
                                'clauses': len(cnf.clauses)+len(clauses)}
    report = {'status': 'cold original and overlay rebuild, exact cut certificates replayed',
              'model_sha256': digest(model_path), 'base_cnf_sha256': base['cnf_sha256'],
              'cnf_sha256': model['cnf_sha256'], 'case_index': index,
              'whole_local_set_excluded': False, 'full_graph': False}
    if result_path:
        result = json.loads(result_path.read_text())
        assert result['model_sha256'] == digest(model_path) and result['cnf_sha256'] == model['cnf_sha256']
        assert result['source_sha256'] == digest(Path(original.__file__)) and result['case_index'] == index
        if result['status'].startswith('SAT;'):
            actual = original.inspect(result['incidence_witness']['selected_columns'], data)
            assert actual == result['incidence_witness']
            report['overlay_witness_check'] = witness_overlay_check(model, actual)
            report['status'] = 'cold formula and exact partial incidence witness replay passed'
        elif result['status'].startswith('UNSAT with direct DRAT;'):
            record = result['retained_certificate']
            retained, proof = ROOT/record['cnf'], ROOT/record['proof']
            assert digest(retained) == record['cnf_sha256'] and digest(proof) == record['proof_sha256']
            inputs = list(original.read_clauses(retained))
            assert len(inputs) == record['input_clauses']
            outside_original = {tuple(sorted(c)) for c in inputs}
            outside_original.difference_update(tuple(sorted(c)) for c in cnf.clauses)
            assert outside_original <= {tuple(sorted(c)) for c in clauses}
            checked_proof = subprocess.run([str(checker), str(retained), str(proof), '-t', str(checker_seconds), '-w'],
                                            capture_output=True, text=True, timeout=checker_seconds+5, check=False)
            log = output.with_suffix('.drat.log')
            log.write_text(checked_proof.stdout+checked_proof.stderr)
            assert checked_proof.returncode == 0 and 's VERIFIED' in checked_proof.stdout
            report.update(status='cold original/overlay rebuild, direct cut certificates, retained inclusion and DRAT passed',
                          retained_input_clauses=len(inputs),
                          retained_distinct_inputs_outside_original_formula=len(outside_original),
                          original_only_proof_binding_verified=not outside_original,
                          excluded_indexed_core=index, checker_log=portable(log), checker_log_sha256=digest(log))
        else:
            assert result['status'].startswith('UNKNOWN;')
            report['status'] = 'cold overlay and UNKNOWN binding replay passed; no exclusion'
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--case', type=int, choices=sorted(EXPECTED), required=True)
    prep.add_argument('--model', type=Path, required=True)
    prep.add_argument('--cnf', type=Path, required=True)
    run = commands.add_parser('solve')
    run.add_argument('--model', type=Path, required=True)
    run.add_argument('--directory', type=Path, required=True)
    run.add_argument('--seconds', type=float, default=60)
    run.add_argument('--checker-seconds', type=int, default=60)
    run.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    check = commands.add_parser('replay')
    check.add_argument('--model', type=Path, required=True)
    check.add_argument('--result', type=Path)
    check.add_argument('--output', type=Path, required=True)
    check.add_argument('--checker-seconds', type=int, default=60)
    check.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.case, args.model.resolve(), args.cnf.resolve())
    elif args.command == 'solve':
        solve(args.model.resolve(), args.directory.resolve(), args.seconds, args.drat_trim.resolve(), args.checker_seconds)
    else:
        replay(args.model.resolve(), args.result.resolve() if args.result else None,
               args.output.resolve(), args.drat_trim.resolve(), args.checker_seconds)
