"""Replay a frozen local rook-interface UNSAT certificate.

Regenerate the full necessary CNF, check its digest and retained-clause
inclusion, then verify the trimmed proof using the supplied drat-trim.
"""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from pysat.formula import CNF

from seven_red_interfaces import build


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(manifest, checker):
    record = json.loads(manifest.read_text())
    builder = Path(__file__).with_name('seven_red_interfaces.py')
    assert digest(builder) == record['builder_sha256']
    assert record['y'] is None and record['require_both_coordinates'] is False
    assert record['bases'] in (6, 7)
    cnf, _, metadata = build(None, bases=record['bases'], require_both=False)
    assert (cnf.nv, len(cnf.clauses)) == (record['variables'], record['clauses'])
    with tempfile.TemporaryDirectory(prefix='rook-interface-replay-') as directory:
        full = Path(directory)/'full.cnf'
        cnf.to_file(full)
        assert digest(full) == record['full_cnf_sha256']
    core = manifest.parent/record['core_file']
    proof = manifest.parent/record['proof_file']
    assert digest(core) == record['core_sha256']
    assert digest(proof) == record['proof_sha256']
    clauses = {tuple(sorted(clause)) for clause in cnf.clauses}
    retained = CNF(from_file=core)
    assert all(tuple(sorted(clause)) in clauses for clause in retained.clauses)
    checked = subprocess.run([str(checker), str(core), str(proof), '-w'],
                             text=True, capture_output=True, timeout=60, check=False)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (checked.stdout, checked.stderr)
    result = {'bases': record['bases'], 'retained_clauses': len(retained.clauses),
              'status': 'regenerated CNF, retained clauses, and proof verified'}
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    replay(args.manifest.resolve(), args.drat_trim.resolve())
