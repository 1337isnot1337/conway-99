"""Check or regenerate a conditional full-incidence DRAT certificate.

The assumptions fix part of an H/Z core in the builder's canonical Z
labeling.  The result is a necessary cut for that ordered incidence
template, not exclusion of the whole template or an unlabeled pattern.
"""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile
from threading import Timer

from pysat.formula import CNF
from pysat.solvers import Solver
from coupled_shells_incidence import build


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def formula(record):
    cnf, edge, *_ = build(record['rows'], record['template'])
    cnf.extend([[edge[i, j] if value else -edge[i, j]]
                for i, j, value in record['assumptions']])
    return cnf


def verify(path, checker):
    record = json.loads(path.read_text()); cnf = formula(record)
    with tempfile.TemporaryDirectory(prefix='conway99-fixed-replay-') as temporary:
        full = Path(temporary)/'full.cnf'; cnf.to_file(full)
        assert digest(full) == record['full_cnf_sha256']
    core = path.parent/record['core_file']; proof = path.parent/record['proof_file']
    assert digest(core) == record['core_cnf_sha256']
    assert digest(proof) == record['proof_sha256']
    original = {tuple(sorted(c)) for c in cnf.clauses}
    assert all(tuple(sorted(c)) in original for c in CNF(from_file=core).clauses)
    run = subprocess.run([str(checker), str(core), str(proof), '-w'],
                         capture_output=True, text=True, timeout=60, check=False)
    assert run.returncode == 0 and 's VERIFIED' in run.stdout, (run.stdout, run.stderr)
    print('PASS:', path.name, 'with', len(record['assumptions']), 'conditional H/Z literals.')
    print('Scope: all H/L and Z/L incidences are free; the entire template is not excluded.')


def main():
    p = argparse.ArgumentParser()
    p.add_argument('--orbits', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-shells-orbits.json'))
    p.add_argument('--assumptions', type=Path,
                   default=Path('experiments/logs/eigenlattices/coupled-zero-fixed-core-0-1-assumptions.json'))
    p.add_argument('--manifest', type=Path,
                   default=Path('experiments/workspace/coupled-zero-fixed-core-0-1-certificate.json'))
    p.add_argument('--drat-trim', type=Path, required=True)
    p.add_argument('--verify', action='store_true')
    a = p.parse_args(); checker = a.drat_trim.resolve()
    if not a.verify:
        record = json.loads(a.assumptions.read_text())
        block = next(b for b in json.loads(a.orbits.read_text()) if b['core'] == record['core'])
        record.update(rows=block['rows'], template=block['orbits'][record['orbit']],
                      builder='coupled_shells_incidence.build',
                      checker_revision='2e3b2dc0ecf938addbd779d42877b6ed69d9a985')
        cnf = formula(record)
        core = a.manifest.with_name(a.manifest.stem.replace('-certificate', '-core')+'.cnf')
        proof = a.manifest.with_name(a.manifest.stem.replace('-certificate', '')+'.drat')
        with tempfile.TemporaryDirectory(prefix='conway99-fixed-proof-') as temporary:
            full = Path(temporary)/'full.cnf'; raw = Path(temporary)/'raw.drat'
            cnf.to_file(full)
            with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
                timer = Timer(45, solver.interrupt); timer.start()
                try:
                    status = solver.solve_limited(expect_interrupt=True)
                finally:
                    timer.cancel()
                assert status is False, f'Conditional exclusion not reproduced: {status}'
                raw.write_text('\n'.join(solver.get_proof())+'\n')
            run = subprocess.run([str(checker), str(full), str(raw), '-w',
                                  '-c', str(core), '-l', str(proof)],
                                 capture_output=True, text=True, timeout=60, check=False)
            assert run.returncode == 0 and 's VERIFIED' in run.stdout, (run.stdout, run.stderr)
            record.update(core_file=core.name, proof_file=proof.name,
                          full_cnf_sha256=digest(full), core_cnf_sha256=digest(core),
                          proof_sha256=digest(proof), core_bytes=core.stat().st_size,
                          proof_bytes=proof.stat().st_size)
            a.manifest.write_text(json.dumps(record, indent=2)+'\n')
        print('Saved core/proof bytes:', record['core_bytes'], record['proof_bytes'])
    verify(a.manifest, checker)


if __name__ == '__main__':
    main()
