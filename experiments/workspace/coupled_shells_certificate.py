"""Replay a compact norm-16 incidence exclusion certificate.

Regenerate the full CNF, verify every retained input clause belongs to it,
then run an independent DRAT checker on the saved core and proof.  No SAT
search is needed to replay an already generated certificate.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from pysat.formula import CNF
from coupled_shells_low import extend_model


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify(manifest_path, checker):
    data = json.loads(manifest_path.read_text())
    base = manifest_path.parent
    core_path = base / data['core_file']
    proof_path = base / data['proof_file']
    assert digest(core_path) == data['sha256']['core_cnf']
    assert digest(proof_path) == data['sha256']['proof']
    cnf, *_ = extend_model(data['rows'], data['template'])
    with tempfile.TemporaryDirectory(prefix='conway99-certificate-') as folder:
        full = Path(folder) / 'full.cnf'
        cnf.to_file(full)
        assert digest(full) == data['full_cnf_sha256'], 'CNF builder differs from the certified snapshot'
    original = {tuple(sorted(c)) for c in cnf.clauses}
    core = CNF(from_file=core_path)
    assert all(tuple(sorted(c)) in original for c in core.clauses), 'retained clause is not in full CNF'
    print(f"full CNF: {cnf.nv} variables, {len(cnf.clauses)} clauses; SHA-256 agrees", flush=True)
    print(f"core: all {len(core.clauses)} clauses occur in the generated formula", flush=True)
    run = subprocess.run([str(checker), str(core_path), str(proof_path), '-w'],
                         capture_output=True, text=True, timeout=60, check=False)
    assert run.returncode == 0 and 's VERIFIED' in run.stdout, (run.returncode, run.stdout, run.stderr)
    print(run.stdout.strip().replace('\r', ''), flush=True)


def main():
    p = argparse.ArgumentParser()
    p.add_argument('manifest', type=Path)
    p.add_argument('--drat-trim', type=Path, required=True)
    a = p.parse_args()
    verify(a.manifest.resolve(), a.drat_trim.resolve())


if __name__ == '__main__': main()
