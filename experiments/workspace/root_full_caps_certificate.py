"""Independently rebuild one complete rooted CNF and replay its retained proof."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from pysat.formula import CNF

from root_full_caps import anchor_units, digest, formula, forward_controls, rook_control
from root_full_caps_coverage import replay as replay_coverage


ROOT = Path(__file__).resolve().parents[2]


def replay(certificate_path, checker):
    certificate = json.loads(certificate_path.read_text())
    assert certificate['lazy_cuts'] == certificate['orbit_equalities'] == 0
    assert digest(Path(__file__)) == certificate['wrapper_source_sha256']
    model_path = ROOT/certificate['model_manifest']
    assert digest(model_path) == certificate['model_manifest_sha256']
    model = json.loads(model_path.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    coverage_path = ROOT/model['coverage_certificate']
    assert digest(coverage_path) == model['coverage_sha256']
    coverage = replay_coverage(coverage_path)
    index = certificate['case_index']
    assert 0 <= index < 11
    case = model['cases'][index]
    assert case['partition'] == certificate['partition'] == coverage['cases'][index]['partition']
    assert case['cnf_sha256'] == certificate['full_cnf_sha256']
    assert forward_controls() == model['forward_controls']
    assert rook_control() == model['rook_positive_control']
    cnf, variables, rows, labels, signatures, metadata = formula(14)
    assert json.loads(json.dumps(metadata)) == model['metadata']
    units = anchor_units(14, tuple(case['partition']), labels, variables)
    assert units == case['normalization_units']
    cnf.extend([[unit] for unit in units])
    assert (cnf.nv, len(cnf.clauses)) == (case['variables'], case['clauses'])
    with tempfile.TemporaryDirectory(prefix='root-full-caps-proof-') as temporary:
        full = Path(temporary)/'full.cnf'
        cnf.to_file(full)
        assert digest(full) == case['cnf_sha256']
    core, proof = ROOT/certificate['core_file'], ROOT/certificate['proof_file']
    assert digest(core) == certificate['core_sha256']
    assert digest(proof) == certificate['proof_sha256']
    retained = CNF(from_file=str(core))
    assert len(retained.clauses) == certificate['retained_clauses']
    needed = {tuple(sorted(clause)) for clause in retained.clauses}
    for clause in cnf.clauses:
        needed.discard(tuple(sorted(clause)))
    assert not needed
    checked = subprocess.run([str(checker), str(core), str(proof), '-t', '60', '-w'],
                             capture_output=True, text=True, timeout=60, check=False)
    print(checked.stdout, end='', flush=True)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (
        checked.returncode, checked.stdout, checked.stderr)
    result = {'status': 'rooted coverage, positive control, exact CNF, inclusion, and proof verified',
              'case_index': index, 'partition': case['partition'],
              'full_cnf_sha256': case['cnf_sha256'], 'variables': cnf.nv,
              'clauses': len(cnf.clauses), 'retained_clauses': len(retained.clauses),
              'scope': 'this normalization case only'}
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certificate', type=Path)
    parser.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    replay(args.certificate.resolve(), args.drat_trim.resolve())
