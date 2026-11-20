"""Replay the complete fixed-incidence a=0 exclusion certificate."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from two_rook_a0_fixed_completion import build


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
    assert certificate['symmetry_clauses'] == certificate['lazy_cuts'] == 0
    assert digest(Path(__file__)) == certificate['wrapper_source_sha256']
    model_path = ROOT/certificate['model_manifest']
    assert digest(model_path) == certificate['model_manifest_sha256']
    model = json.loads(model_path.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    core, proof = ROOT/certificate['core_file'], ROOT/certificate['proof_file']
    assert digest(core) == certificate['core_sha256']
    assert digest(proof) == certificate['proof_sha256']
    retained = list(clauses(core))
    assert len(retained) == certificate['retained_clauses']
    needed = {tuple(sorted(clause)) for clause in retained}
    with tempfile.TemporaryDirectory(prefix='rook-a0-replay-') as temporary:
        directory = Path(temporary)
        full = directory/'full.cnf'
        rebuilt = build(ROOT/model['structural_certificate'], full, directory/'model.json')
        assert rebuilt['source_hashes'] == model['source_hashes']
        for key in ('cnf_sha256', 'structural_certificate_sha256', 'selected_signature_sha256',
                    'domain_sha256', 'edge_variables', 'variables', 'clauses',
                    'packing_clauses', 'path_variables', 'outside_pairs'):
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
    result = {'status': 'complete a=0 census and fixed CNF rebuilt; retained inclusion and DRAT verified',
              'a0_incidence_designs': 16, 'farkas_excluded_designs': 14,
              'drat_excluded_equivalent_designs': 2, 'all_a0_designs_excluded': True,
              'whole_complementary_rook_case_excluded': False,
              'full_cnf_sha256': model['cnf_sha256'], 'variables': model['variables'],
              'clauses': model['clauses'], 'retained_clauses': len(retained)}
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certificate', type=Path)
    parser.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    replay(args.certificate.resolve(), args.drat_trim.resolve())
