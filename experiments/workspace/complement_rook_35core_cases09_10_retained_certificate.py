"""Compact retained proofs for cases9/10 with only five small Gram cuts.

Generation rounds known exact negative vectors and checks the rounded
vectors directly. Replay imports only the original incidence builder: it
does not require the22-case downdate census, its inverses, or overlay code.
Every retained input is either an original CNF clause or one of the saved
directly justified binary clauses. No SAT query is made.
"""

import argparse
import gzip
import json
from pathlib import Path
import subprocess
import tempfile

import complement_rook_35core_incidence as original


ROOT, LOGS = original.ROOT, original.LOGS
MODEL_SHA = {9: '8e869e9d346cf18cb7f87a48d78df594c31c6b15f3621392c8661b209f2a6f7e',
             10: '0fd621e46b76da0369bcf0fe8c9b0f21a5c6b1a22cc72618ff6d44aeab706b03'}
EXPECTED_CUTS = {9: 2, 10: 3}
digest, portable, canonical = original.digest, original.portable, original.canonical


def exact_values(gram, masks, columns, vector):
    assert len(vector) == 35 and all(type(v) is int for v in vector)
    gram_value = sum(vector[i]*gram[i][j]*vector[j] for i in range(35) for j in range(35))
    dots = [sum(vector[i] for i in range(35) if masks[column] >> i & 1) for column in columns]
    return gram_value, dots, gram_value-sum(value*value for value in dots)


def cold_original(path, expected):
    assert digest(path) == expected
    model = original.checked_model(path)
    data, cnf, metadata = original.rebuild(model['case']['index'])
    assert metadata == model['formula']
    assert original.domains.sha(canonical(data[3])) == model['domain_record_sha256']
    with tempfile.TemporaryDirectory(prefix='conway35-compact-original-') as directory:
        rebuilt = Path(directory)/'original.cnf'
        cnf.to_file(rebuilt)
        assert digest(rebuilt) == model['cnf_sha256']
    return model, data, cnf


def outside_original(cnf, retained):
    inputs = list(original.read_clauses(retained))
    needed = {tuple(sorted(clause)) for clause in inputs}
    needed.difference_update(tuple(sorted(clause)) for clause in cnf.clauses)
    return inputs, needed


def generate():
    records = []
    for case_index in (9, 10):
        model_path = LOGS/f'complement-rook-35core-case{case_index:04d}-downdate-overlay-model.json'
        assert digest(model_path) == MODEL_SHA[case_index]
        overlay = json.loads(model_path.read_text())
        base_path = ROOT/overlay['base_model']
        model, data, cnf = cold_original(base_path, overlay['base_model_sha256'])
        assert model['case']['index'] == case_index
        result_path = LOGS/f'complement-rook-35core-case{case_index:04d}-downdate-overlay-run01/result.json'
        result = json.loads(result_path.read_text())
        assert result['model_sha256'] == MODEL_SHA[case_index] and result['status'].startswith('UNSAT with direct DRAT;')
        replay_path = LOGS/f'complement-rook-35core-case{case_index:04d}-downdate-overlay-cold-replay.json'
        replay = json.loads(replay_path.read_text())
        assert replay['status'] == 'cold original/overlay rebuild, direct cut certificates, retained inclusion and DRAT passed'
        assert replay['excluded_indexed_core'] == case_index
        proof_record = result['retained_certificate']
        retained, proof = ROOT/proof_record['cnf'], ROOT/proof_record['proof']
        assert digest(retained) == proof_record['cnf_sha256'] and digest(proof) == proof_record['proof_sha256']
        inputs, needed = outside_original(cnf, retained)
        assert len(needed) == EXPECTED_CUTS[case_index] == replay['retained_distinct_inputs_outside_original_formula']
        saved = json.loads(gzip.decompress((ROOT/overlay['certificate']).read_bytes()))
        assert saved['attachment_columns'] == data[3]['columns'] and saved['Gram'] == data[5]
        known = {tuple(sorted(-column-1 for column in witness['columns'])): witness
                 for witness in saved['scan']['additional_binary_exclusion_witnesses']}
        witnesses = []
        for clause in sorted(needed):
            prior = known[clause]
            columns = sorted(-literal-1 for literal in clause)
            vector = prior['negative_vector']
            maximum = max(map(abs, vector))
            chosen = None
            for scale in range(1, 129):
                candidate = [(2*v*scale+maximum)//(2*maximum) for v in vector]
                gram_value, dots, value = exact_values(data[5], data[9], columns, candidate)
                if value < 0:
                    chosen = {'rounding_scale': scale, 'negative_vector': candidate,
                              'Gram_quadratic_value': gram_value, 'column_dot_products': dots,
                              'negative_remainder_value': value}
                    break
            assert chosen is not None
            chosen.update(clause=list(clause), columns=columns,
                          attachment_columns=[data[3]['columns'][i] for i in columns],
                          original_signature_triples=[list(data[0][2][data[3]['columns'][i][0]]) for i in columns])
            witnesses.append(chosen)
        records.append({'case_index': case_index, 'original_model': portable(base_path),
                        'original_model_sha256': digest(base_path), 'original_cnf_sha256': model['cnf_sha256'],
                        'original_source_hashes': model['source_hashes'],
                        'domain_record_sha256': model['domain_record_sha256'],
                        'discovery_model_sha256': MODEL_SHA[case_index],
                        'discovery_result': portable(result_path), 'discovery_result_sha256': digest(result_path),
                        'discovery_cold_replay': portable(replay_path), 'discovery_cold_replay_sha256': digest(replay_path),
                        'retained_cnf': portable(retained), 'retained_cnf_sha256': digest(retained),
                        'retained_proof': portable(proof), 'retained_proof_sha256': digest(proof),
                        'retained_input_clauses': len(inputs), 'small_Gram_witnesses': witnesses,
                        'standalone_original_only_DRAT_proof': False})
    return {'status': 'compact exact dependencies for the two retained local-core proofs',
            'source_sha256': digest(Path(__file__)), 'cases': records,
            'retained_Gram_clauses_total': 5, 'whole_local_set_excluded': False,
            'replay_needs_no_downdate_inverse_or_census': True, 'solver_called': False}


def replay(certificate, directory, checker, seconds):
    assert not directory.exists() and 0 < seconds <= 60
    directory.mkdir(parents=True)
    assert certificate['source_sha256'] == digest(Path(__file__))
    assert [record['case_index'] for record in certificate['cases']] == [9, 10]
    reports = []
    for record in certificate['cases']:
        index = record['case_index']
        model, data, cnf = cold_original(ROOT/record['original_model'], record['original_model_sha256'])
        assert model['case']['index'] == index and model['cnf_sha256'] == record['original_cnf_sha256']
        assert model['source_hashes'] == record['original_source_hashes']
        assert model['domain_record_sha256'] == record['domain_record_sha256']
        retained, proof = ROOT/record['retained_cnf'], ROOT/record['retained_proof']
        assert digest(retained) == record['retained_cnf_sha256'] and digest(proof) == record['retained_proof_sha256']
        inputs, needed = outside_original(cnf, retained)
        assert len(inputs) == record['retained_input_clauses']
        assert len(needed) == EXPECTED_CUTS[index]
        found = set()
        for witness in record['small_Gram_witnesses']:
            clause = witness['clause']
            assert len(clause) == 2 and all(-len(data[9]) <= literal < 0 for literal in clause)
            columns = sorted(-literal-1 for literal in clause)
            assert columns == witness['columns'] and len(set(columns)) == 2
            assert [data[3]['columns'][i] for i in columns] == witness['attachment_columns']
            gram_value, dots, value = exact_values(data[5], data[9], columns, witness['negative_vector'])
            assert gram_value == witness['Gram_quadratic_value'] and dots == witness['column_dot_products']
            assert value == witness['negative_remainder_value'] and value < 0
            found.add(tuple(sorted(clause)))
        assert found == needed
        checked = subprocess.run([str(checker), str(retained), str(proof), '-t', str(seconds), '-w'],
                                 capture_output=True, text=True, timeout=seconds+5, check=False)
        log = directory/f'case{index:04d}.drat.log'
        log.write_text(checked.stdout+checked.stderr)
        assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
        report = {'status': 'PASS: cold original formula plus only the small direct Gram witnesses, retained inclusion and DRAT',
                  'case_index': index, 'original_cnf_sha256': model['cnf_sha256'],
                  'retained_input_clauses': len(inputs), 'small_Gram_clauses': len(found),
                  'small_vector_maxima': [max(map(abs, w['negative_vector'])) for w in record['small_Gram_witnesses']],
                  'negative_values': [w['negative_remainder_value'] for w in record['small_Gram_witnesses']],
                  'checker_log': portable(log), 'checker_log_sha256': digest(log),
                  'whole_local_set_excluded': False, 'solver_called': False}
        (directory/f'case{index:04d}-replay.json').write_text(json.dumps(report, indent=2)+'\n')
        reports.append(report)
    summary = {'status': 'both compact retained certificates replayed exactly',
               'source_sha256': digest(Path(__file__)), 'cases': reports, 'new_solver_queries': 0}
    (directory/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--replay', action='store_true')
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    parser.add_argument('--checker-seconds', type=int, default=60)
    args = parser.parse_args()
    if args.write:
        assert not args.certificate.exists()
        certificate = generate()
        args.certificate.write_text(json.dumps(certificate, indent=2)+'\n')
        print(json.dumps({'status': 'compact exact dependencies saved', 'certificate_sha256': digest(args.certificate),
                          'cases': [{'case': r['case_index'], 'cuts': r['small_Gram_witnesses']} for r in certificate['cases']]}, indent=2), flush=True)
    else:
        assert args.directory is not None
        replay(json.loads(args.certificate.read_text()), args.directory.resolve(), args.drat_trim.resolve(), args.checker_seconds)
