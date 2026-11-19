"""Rebuild a boundary joint CNF and verify a retained DRAT certificate."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from two_rook_tip_boundary_joint_integer import build


ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            result.update(block)
    return result.hexdigest()


def clauses(path):
    current = []
    with path.open() as stream:
        for line in stream:
            if not line.strip() or line.lstrip().startswith(('c', 'p')):
                continue
            for token in line.split():
                value = int(token)
                if value:
                    current.append(value)
                else:
                    yield tuple(current)
                    current = []
    assert not current


def replay(certificate_path, checker):
    certificate = json.loads(certificate_path.read_text())
    assert certificate['lazy_cuts'] == certificate['orbit_equalities'] == 0
    model_path = ROOT/certificate['model_manifest']
    assert digest(model_path) == certificate['model_manifest_sha256']
    model = json.loads(model_path.read_text())
    assert certificate['representative'] == model['representative']
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert digest(Path(__file__)) == certificate['wrapper_source_sha256']
    core = ROOT/certificate['core_file']
    proof = ROOT/certificate['proof_file']
    assert digest(core) == certificate['core_sha256']
    assert digest(proof) == certificate['proof_sha256']
    retained = list(clauses(core))
    assert len(retained) == certificate['retained_clauses']
    needed = {tuple(sorted(clause)) for clause in retained}

    with tempfile.TemporaryDirectory(prefix='rook-tip-boundary-replay-') as temporary:
        directory = Path(temporary)
        full = directory/'full.cnf'
        rebuilt = build(ROOT/model['domain_path'], ROOT/model['boundary_certificate'],
                        ROOT/model['hall_certificate'], model['representative'],
                        full, directory/'model.json')
        assert rebuilt['source_hashes'] == model['source_hashes']
        for key in ('cnf_sha256', 'domain_file_sha256', 'boundary_sha256', 'hall_sha256',
                    'domain_sha256', 'signature_variables', 'edge_variables', 'variables',
                    'clauses', 'packing_clauses', 'derived_positive_units',
                    'derived_negative_units'):
            assert rebuilt[key] == model[key]
        count = 0
        for clause in clauses(full):
            needed.discard(tuple(sorted(clause)))
            count += 1
        assert count == model['clauses'] and not needed

    checked = subprocess.run([str(checker), str(core), str(proof), '-t', '60', '-w'],
                             text=True, capture_output=True, timeout=60, check=False)
    print(checked.stdout, end='', flush=True)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (
        checked.returncode, checked.stdout, checked.stderr)
    result = {'status': 'full domain and CNF rebuilt; retained inclusion and DRAT verified',
              'representative': model['representative'],
              'signature_variables': model['signature_variables'],
              'edge_variables': model['edge_variables'],
              'full_cnf_sha256': model['cnf_sha256'],
              'variables': model['variables'], 'clauses': model['clauses'],
              'retained_clauses': len(retained)}
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certificate', type=Path)
    parser.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    replay(args.certificate.resolve(), args.drat_trim.resolve())
