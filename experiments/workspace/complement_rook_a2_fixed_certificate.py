"""Retain and replay complete-edge exclusions for one a=2 incidence orbit.

Replay reconstructs the exact full formula, checks that every retained input
clause belongs to it, and independently verifies the retained DRAT proof.
The complete 576-design incidence census is replayed during reconstruction.
"""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace

from complement_rook_a2_fixed_completion import build, digest


ROOT = Path(__file__).resolve().parents[2]


def relative(path):
    return str(path.resolve().relative_to(ROOT))


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


def run_checker(checker, cnf, proof, log, extra=()):
    checked = subprocess.run([str(checker), str(cnf), str(proof), '-t', '60', '-w',
                              *map(str, extra)], text=True, capture_output=True,
                             timeout=65, check=False)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(checked.stdout+checked.stderr)
    print(checked.stdout, end='', flush=True)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (
        checked.returncode, checked.stdout, checked.stderr)


def certify(args):
    model = json.loads(args.manifest.read_text())
    outcome = json.loads(args.result.read_text())
    assert outcome['status'] == 'solver UNSAT; proof saved, independent verification pending'
    assert outcome['case_index'] == model['case_index']
    assert outcome['manifest_sha256'] == digest(args.manifest)
    assert outcome['cnf_sha256'] == model['cnf_sha256']
    assert outcome['source_sha256'] == model['source_hashes']['complement_rook_a2_fixed_completion.py']
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    full, raw_proof = ROOT/model['cnf_path'], ROOT/outcome['proof_path']
    assert digest(full) == model['cnf_sha256']
    assert digest(raw_proof) == outcome['proof_sha256']
    args.core.parent.mkdir(parents=True, exist_ok=True)
    args.proof.parent.mkdir(parents=True, exist_ok=True)
    run_checker(args.drat_trim, full, raw_proof, args.log,
                ('-c', args.core, '-l', args.proof))
    retained = list(clauses(args.core))
    certificate = {
        'status': 'retained complete-edge certificate; exact full-formula replay required',
        'case_index': model['case_index'], 'equivalent_incidence_designs': 144,
        'total_a2_incidence_designs': 576, 'total_a2_incidence_orbits': 4,
        'whole_complementary_rook_case_excluded': False,
        'all_a2_orbits_excluded_by_this_certificate': False,
        'model_manifest': relative(args.manifest),
        'model_manifest_sha256': digest(args.manifest),
        'solver_result': relative(args.result), 'solver_result_sha256': digest(args.result),
        'wrapper_source_sha256': digest(Path(__file__)),
        'full_cnf_sha256': model['cnf_sha256'],
        'raw_proof_sha256': outcome['proof_sha256'],
        'core_file': relative(args.core), 'core_sha256': digest(args.core),
        'proof_file': relative(args.proof), 'proof_sha256': digest(args.proof),
        'retained_clauses': len(retained),
        'retained_proof_lines': sum(1 for _ in args.proof.open()),
        'selected_signature_sha256': model['selected_signature_sha256'],
        'domain_sha256': model['domain_sha256'],
        'symmetry_clauses': 0, 'lazy_cuts': 0, 'full_outside_caps': True,
        'proof_checker_sha256_at_generation': digest(args.drat_trim),
    }
    args.certificate.write_text(json.dumps(certificate, indent=2)+'\n')
    return certificate


def replay(certificate_path, checker, log):
    certificate = json.loads(certificate_path.read_text())
    assert certificate['symmetry_clauses'] == certificate['lazy_cuts'] == 0
    assert certificate['full_outside_caps'] is True
    assert certificate['equivalent_incidence_designs'] == 144
    assert digest(Path(__file__)) == certificate['wrapper_source_sha256']
    model_path = ROOT/certificate['model_manifest']
    assert digest(model_path) == certificate['model_manifest_sha256']
    model = json.loads(model_path.read_text())
    assert model['case_index'] == certificate['case_index']
    assert model['cnf_sha256'] == certificate['full_cnf_sha256']
    assert model['domain_sha256'] == certificate['domain_sha256']
    assert model['selected_signature_sha256'] == certificate['selected_signature_sha256']
    outcome_path = ROOT/certificate['solver_result']
    assert digest(outcome_path) == certificate['solver_result_sha256']
    outcome = json.loads(outcome_path.read_text())
    assert outcome['proof_sha256'] == certificate['raw_proof_sha256']
    assert outcome['manifest_sha256'] == certificate['model_manifest_sha256']
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    core, proof = ROOT/certificate['core_file'], ROOT/certificate['proof_file']
    assert digest(core) == certificate['core_sha256']
    assert digest(proof) == certificate['proof_sha256']
    retained = list(clauses(core))
    assert len(retained) == certificate['retained_clauses']
    needed = {tuple(sorted(clause)) for clause in retained}
    with tempfile.TemporaryDirectory(prefix='rook-a2-replay-') as temporary:
        directory = Path(temporary)
        full = directory/'full.cnf'
        rebuilt = build(SimpleNamespace(
            census=ROOT/model['census_path'], census_cnf=ROOT/model['census_cnf'],
            census_proof=ROOT/model['census_proof'], drat_trim=checker,
            case=model['case_index'], cnf=full, manifest=directory/'model.json'))
        rebuilt = json.loads(json.dumps(rebuilt))
        assert rebuilt['source_hashes'] == model['source_hashes']
        for key in ('case_index', 'equivalent_designs', 'signature_indices',
                    'coordinate_triples', 'selected_signature_sha256',
                    'cnf_sha256', 'census_sha256', 'census_cnf_sha256',
                    'census_proof_sha256', 'domain_sha256', 'edge_variables',
                    'distinct_mixed_and_degree_counts', 'impossible_count_rows',
                    'base_variables', 'base_clauses', 'outside_pairs',
                    'duplicate_zero_caps', 'packing_clauses', 'path_variables',
                    'variables', 'clauses', 'symmetry_clauses', 'orbit_equalities',
                    'lazy_cuts', 'full_outside_caps', 'controls'):
            assert rebuilt[key] == model[key], (key, rebuilt[key], model[key])
        count = 0
        for clause in clauses(full):
            needed.discard(tuple(sorted(clause)))
            count += 1
        assert count == model['clauses'] and not needed
    run_checker(checker, core, proof, log)
    result = {
        'status': 'full a=2 case CNF rebuilt; retained inclusion and DRAT verified',
        'case_index': model['case_index'], 'excluded_equivalent_designs': 144,
        'total_a2_incidence_orbits': 4,
        'whole_complementary_rook_case_excluded': False,
        'full_cnf_sha256': model['cnf_sha256'],
        'variables': model['variables'], 'clauses': model['clauses'],
        'retained_clauses': len(retained), 'symmetry_clauses': 0, 'lazy_cuts': 0,
    }
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    generator = commands.add_parser('certify')
    for name in ('manifest', 'result', 'core', 'proof', 'certificate', 'log', 'drat-trim'):
        generator.add_argument('--'+name, type=Path, required=True)
    verifier = commands.add_parser('replay')
    for name in ('certificate', 'log', 'drat-trim'):
        verifier.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'certify':
        certify(args)
    else:
        replay(args.certificate, args.drat_trim, args.log)
