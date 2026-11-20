"""Retain and independently replay a two-unit joint-model split exclusion."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from complement_rook_joint_split import ROOT, check_case, digest, materialize
from two_rook_tip_boundary_joint_integer import build as build_base


def relative(path):
    return str(path.resolve().relative_to(ROOT))


def clauses(path):
    current = []
    with path.open() as stream:
        for line in stream:
            if not line.strip() or line.lstrip().startswith(('c', 'p')):
                continue
            for token in line.split():
                literal = int(token)
                if literal:
                    current.append(literal)
                else:
                    yield tuple(current)
                    current = []
    assert not current


def checked_drat(checker, formula, proof, log, extra=()):
    checked = subprocess.run([str(checker), str(formula), str(proof), '-t', '60', '-w',
                              *map(str, extra)], text=True, capture_output=True,
                             timeout=65, check=False)
    log.write_text(checked.stdout+checked.stderr)
    print(checked.stdout, end='', flush=True)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (
        checked.returncode, checked.stdout, checked.stderr)


def certify(args):
    case, base, _, _, _ = check_case(args.manifest)
    result = json.loads(args.result.read_text())
    assert result['status'] == 'solver UNSAT; saved proof awaits independent verification'
    assert result['manifest_sha256'] == digest(args.manifest)
    assert result['split_cnf_sha256'] == case['split_cnf_sha256']
    assert result['selected_signature_units'] == case['selected_signature_units']
    raw = ROOT/result['proof_path']
    assert digest(raw) == result['proof_sha256']
    with tempfile.TemporaryDirectory(prefix='rook-joint-split-trim-') as temporary:
        full = Path(temporary)/'split.cnf'
        materialize(ROOT/base['cnf_path'], base['variables'], base['clauses'],
                    case['selected_signature_units'], full)
        assert digest(full) == case['split_cnf_sha256']
        checked_drat(args.drat_trim, full, raw, args.log,
                     ('-c', args.core, '-l', args.proof))
    certificate = {
        'status': 'retained joint split proof; full-formula replay required',
        'case_index': case['case_index'], 'representative_tips': case['representative_tips'],
        'covered_tip_pairs': case['covered_tip_pairs'],
        'case_manifest': relative(args.manifest), 'case_manifest_sha256': digest(args.manifest),
        'solver_result': relative(args.result), 'solver_result_sha256': digest(args.result),
        'wrapper_source_sha256': digest(Path(__file__)),
        'base_cnf_sha256': base['cnf_sha256'], 'split_cnf_sha256': case['split_cnf_sha256'],
        'selected_signature_units': case['selected_signature_units'],
        'raw_proof_sha256': result['proof_sha256'],
        'core_file': relative(args.core), 'core_sha256': digest(args.core),
        'proof_file': relative(args.proof), 'proof_sha256': digest(args.proof),
        'retained_clauses': sum(1 for _ in clauses(args.core)),
        'retained_proof_lines': sum(1 for _ in args.proof.open()),
        'extra_a_bound_added': False, 'full_outside_caps_imposed': False,
        'orbit_equalities': 0, 'fixed_incidence_witnesses': 0, 'lazy_cuts': 0,
        'proof_checker_sha256_at_generation': digest(args.drat_trim),
    }
    args.certificate.write_text(json.dumps(certificate, indent=2)+'\n')
    return certificate


def replay(certificate_path, checker, log):
    certificate = json.loads(certificate_path.read_text())
    assert digest(Path(__file__)) == certificate['wrapper_source_sha256']
    case_path = ROOT/certificate['case_manifest']
    assert digest(case_path) == certificate['case_manifest_sha256']
    case, base, _, _, _ = check_case(case_path, require_cnf=False)
    assert case['case_index'] == certificate['case_index']
    assert case['representative_tips'] == certificate['representative_tips']
    assert case['selected_signature_units'] == certificate['selected_signature_units']
    assert case['split_cnf_sha256'] == certificate['split_cnf_sha256']
    assert base['cnf_sha256'] == certificate['base_cnf_sha256']
    assert certificate['orbit_equalities'] == certificate['fixed_incidence_witnesses'] == certificate['lazy_cuts'] == 0
    assert not certificate['extra_a_bound_added'] and not certificate['full_outside_caps_imposed']
    result_path = ROOT/certificate['solver_result']
    assert digest(result_path) == certificate['solver_result_sha256']
    result = json.loads(result_path.read_text())
    assert result['proof_sha256'] == certificate['raw_proof_sha256']
    core, proof = ROOT/certificate['core_file'], ROOT/certificate['proof_file']
    assert digest(core) == certificate['core_sha256']
    assert digest(proof) == certificate['proof_sha256']
    retained = list(clauses(core))
    assert len(retained) == certificate['retained_clauses']
    needed = {tuple(sorted(clause)) for clause in retained}
    with tempfile.TemporaryDirectory(prefix='rook-joint-split-replay-') as temporary:
        directory = Path(temporary)
        rebuilt_base_path = directory/'base.cnf'
        rebuilt = build_base(ROOT/base['domain_path'], ROOT/base['boundary_certificate'],
                             ROOT/base['hall_certificate'], base['representative'],
                             rebuilt_base_path, directory/'base-model.json')
        assert rebuilt['source_hashes'] == base['source_hashes']
        for key in ('cnf_sha256', 'domain_file_sha256', 'boundary_sha256', 'hall_sha256',
                    'domain_sha256', 'signature_variables', 'edge_variables', 'variables',
                    'clauses', 'packing_clauses', 'derived_positive_units',
                    'derived_negative_units', 'full_outside_caps_imposed',
                    'orbit_equalities', 'fixed_incidence_witnesses'):
            assert rebuilt[key] == base[key], key
        full = directory/'split.cnf'
        materialize(rebuilt_base_path, base['variables'], base['clauses'],
                    case['selected_signature_units'], full)
        assert digest(full) == case['split_cnf_sha256']
        count = 0
        for clause in clauses(full):
            needed.discard(tuple(sorted(clause)))
            count += 1
        assert count == case['clauses'] and not needed
    checked_drat(checker, core, proof, log)
    checked = {'status': 'full base CNF and exact two-unit split rebuilt; retained inclusion and DRAT verified',
               'case_index': case['case_index'], 'representative_tips': case['representative_tips'],
               'excluded_tip_pairs': case['covered_tip_pairs'],
               'split_cnf_sha256': case['split_cnf_sha256'],
               'variables': case['variables'], 'clauses': case['clauses'],
               'retained_clauses': len(retained), 'extra_a_bound_added': False,
               'full_outside_caps_imposed': False, 'lazy_cuts': 0}
    print(json.dumps(checked), flush=True)
    return checked


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
