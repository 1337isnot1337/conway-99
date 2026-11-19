"""Replay case2's retained proof against the original incidence formula.

The proof was discovered in a run with886 redundant Gram-downdate clauses.
None occurs among its retained inputs. This verifier rebuilds only the
original formula and checks input inclusion and DRAT; it does not import
the downdate or overlay modules and does not require their certificates.
"""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
import time

import complement_rook_35core_incidence as original


ROOT, LOGS = original.ROOT, original.LOGS
BASE_MODEL = LOGS/'complement-rook-35core-first-local-sweep01/case0002-model.json'
BASE_MODEL_SHA = '84793fff0bfbb7bcbeb5b50974dfefad596b4dc72fa35619190eb1b871082883'
RESULT = LOGS/'complement-rook-35core-case0002-gram-downdate-overlay-run01/result.json'
RESULT_SHA = '58ab353cc3b6c503c2f2290b6a2a6a9648af2337155facae6563608d0526aca2'
digest, portable = original.digest, original.portable


def replay(output, checker, seconds):
    assert not output.exists() and 0 < seconds <= 60
    started = time.monotonic()
    assert digest(BASE_MODEL) == BASE_MODEL_SHA and digest(RESULT) == RESULT_SHA
    model = original.checked_model(BASE_MODEL)
    assert model['case']['index'] == 2
    data, cnf, metadata = original.rebuild(2)
    assert metadata == model['formula']
    assert original.domains.sha(original.canonical(data[3])) == model['domain_record_sha256']
    assert data[3]['column_domain_sha256'] == model['column_domain_sha256']
    assert data[3]['Gram_sha256'] == model['Gram_sha256']
    with tempfile.TemporaryDirectory(prefix='conway35-case2-original-') as directory:
        rebuilt = Path(directory)/'original.cnf'
        cnf.to_file(rebuilt)
        assert digest(rebuilt) == model['cnf_sha256']
    result = json.loads(RESULT.read_text())
    assert result['case_index'] == 2 and result['status'].startswith('UNSAT with direct DRAT;')
    certificate = result['retained_certificate']
    retained, proof = ROOT/certificate['cnf'], ROOT/certificate['proof']
    assert digest(retained) == certificate['cnf_sha256'] and digest(proof) == certificate['proof_sha256']
    inputs = list(original.read_clauses(retained))
    assert len(inputs) == certificate['input_clauses'] == 23913
    needed = {tuple(sorted(clause)) for clause in inputs}
    needed.difference_update(tuple(sorted(clause)) for clause in cnf.clauses)
    assert not needed, 'The original-only conclusion requires every retained input to belong to the original formula.'
    checked = subprocess.run([str(checker), str(retained), str(proof), '-t', str(seconds), '-w'],
                             capture_output=True, text=True, timeout=seconds+5, check=False)
    log = output.with_suffix('.drat.log')
    log.write_text(checked.stdout+checked.stderr)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
    report = {
        'status': 'PASS: cold original case2 formula rebuilt, all retained inputs included, DRAT verified',
        'source_sha256': digest(Path(__file__)),
        'original_source_hashes': model['source_hashes'],
        'original_model': portable(BASE_MODEL), 'original_model_sha256': BASE_MODEL_SHA,
        'original_cnf_sha256': model['cnf_sha256'],
        'original_variables': cnf.nv, 'original_clauses': len(cnf.clauses),
        'discovery_result': portable(RESULT), 'discovery_result_sha256': RESULT_SHA,
        'retained_cnf': portable(retained), 'retained_cnf_sha256': digest(retained),
        'retained_proof': portable(proof), 'retained_proof_sha256': digest(proof),
        'retained_input_clauses': len(inputs),
        'all_retained_inputs_are_original_formula_clauses': True,
        'additional_spectral_or_downdate_premises_required': False,
        'checker_log': portable(log), 'checker_log_sha256': digest(log),
        'checker_seconds': seconds, 'elapsed_seconds': time.monotonic()-started,
        'excluded_scope': 'indexed35-core case2 only',
        'whole_local_eight_set_excluded': False,
        'solver_called': False,
    }
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    parser.add_argument('--checker-seconds', type=int, default=60)
    args = parser.parse_args()
    replay(args.output.resolve(), args.drat_trim.resolve(), args.checker_seconds)
