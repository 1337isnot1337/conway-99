"""Generate and check compact DRAT certificates for high/low census exclusions."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from pysat.solvers import Solver
from coupled_shells_certificate import verify
from coupled_shells_low import extend_model


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def generate(block, orbit_index, destination, checker, revision):
    orbit = block['orbits'][orbit_index]
    cnf, *_ = extend_model(block['rows'], orbit)
    prefix = f"coupled-shells-low-{block['core']}-{orbit_index}"
    core_path = destination / (prefix + '-core.cnf')
    proof_path = destination / (prefix + '.drat')
    manifest_path = destination / (prefix + '-certificate.json')
    with tempfile.TemporaryDirectory(prefix='conway99-drat-') as temporary:
        full = Path(temporary) / 'full.cnf'
        raw = Path(temporary) / 'raw.drat'
        cnf.to_file(full)
        with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
            assert solver.solve() is False, 'reported exclusion did not reproduce'
            raw.write_text('\n'.join(solver.get_proof()) + '\n')
        run = subprocess.run([str(checker), str(full), str(raw), '-w',
                              '-c', str(core_path), '-l', str(proof_path)],
                             capture_output=True, text=True, timeout=60, check=False)
        assert run.returncode == 0 and 's VERIFIED' in run.stdout, (run.stdout, run.stderr)
        data = {
            'core': block['core'], 'orbit': orbit_index,
            'rows': block['rows'], 'template': orbit,
            'builder': 'coupled_shells_low.extend_model',
            'full_cnf_sha256': digest(full),
            'core_file': core_path.name, 'proof_file': proof_path.name,
            'sha256': {'full_cnf': digest(full), 'core_cnf': digest(core_path), 'proof': digest(proof_path)},
            'bytes': {'full_cnf': full.stat().st_size, 'core_cnf': core_path.stat().st_size,
                      'proof': proof_path.stat().st_size},
            'checker_source': 'https://github.com/marijnheule/drat-trim',
            'checker_revision': revision,
        }
        manifest_path.write_text(json.dumps(data, indent=2) + '\n')
    verify(manifest_path, checker)
    print(f"saved {manifest_path.name}: core {core_path.stat().st_size} bytes, "
          f"proof {proof_path.stat().st_size} bytes", flush=True)
    return data


def main():
    p = argparse.ArgumentParser()
    p.add_argument('orbits', type=Path); p.add_argument('results', type=Path)
    p.add_argument('--destination', type=Path, default=Path(__file__).parent)
    p.add_argument('--drat-trim', type=Path, required=True)
    p.add_argument('--checker-revision', default='2e3b2dc0ecf938addbd779d42877b6ed69d9a985')
    p.add_argument('--core', type=int, nargs='*')
    a = p.parse_args()
    data = {b['core']: b for b in json.loads(a.orbits.read_text())}
    results = json.loads(a.results.read_text())
    for item in results:
        if item['status'] != 'unsat' or (a.core is not None and item['core'] not in a.core):
            continue
        generate(data[item['core']], item['orbit'], a.destination.resolve(),
                 a.drat_trim.resolve(), a.checker_revision)


if __name__ == '__main__': main()
