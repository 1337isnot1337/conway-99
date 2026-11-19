"""Rebuild the joint integer model and replay its retained DRAT certificate."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from pysat.formula import CNF

from two_rook_iso_joint_integer import build, controls


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def replay(manifest, checker):
    record = json.loads(manifest.read_text())
    for name, expected in record['source_files'].items():
        assert digest(manifest.parent/name) == expected
    assert record['lazy_cuts'] == record['orbit_equalities'] == 0
    assert controls()['status'] == 'exact pass'
    cnf, z, edges, rows, signatures, metadata = build()
    assert len(z) == record['signatures'] == 168
    assert len(edges) == record['edge_variables'] == 9846
    assert (cnf.nv, len(cnf.clauses)) == (record['variables'], record['clauses'])
    with tempfile.TemporaryDirectory(prefix='two-rook-integer-replay-') as directory:
        full = Path(directory)/'full.cnf'
        cnf.to_file(full)
        assert digest(full) == record['full_cnf_sha256']
    core = manifest.parent/record['core_file']
    proof = manifest.parent/record['proof_file']
    assert digest(core) == record['core_sha256']
    assert digest(proof) == record['proof_sha256']
    retained = CNF(from_file=str(core))
    assert len(retained.clauses) == record['retained_clauses']
    needed = {tuple(sorted(clause)) for clause in retained.clauses}
    for clause in cnf.clauses:
        needed.discard(tuple(sorted(clause)))
    assert not needed
    checked = subprocess.run([str(checker), str(core), str(proof), '-w'],
                             text=True, capture_output=True, timeout=60, check=False)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (checked.stdout, checked.stderr)
    result = {'status': 'rebuilt CNF, retained-clause inclusion, and DRAT proof verified',
              'signatures': len(signatures), 'candidate_edges': len(edges),
              'variables': cnf.nv, 'clauses': len(cnf.clauses),
              'retained_clauses': len(retained.clauses)}
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('manifest', type=Path)
    parser.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    replay(args.manifest.resolve(), args.drat_trim.resolve())
