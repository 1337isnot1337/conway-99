"""Rebuild and verify one signed-core cut from the baseline master pilot."""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from complement_rook_incidence_master import ROOT, check_model, clauses, digest, full_assumptions, materialize_units
from two_rook_tip_boundary_joint_integer import build as rebuild_base


def replay(certificate_path, checker, log):
    certificate = json.loads(certificate_path.read_text())
    assert certificate['status'] == 'explicit-core-unit proof DRAT verified; cut certified'
    assert certificate['certificate_wrapper_sha256'] == digest(Path(__file__))
    manifest_path = ROOT/certificate['manifest']
    assert digest(manifest_path) == certificate['manifest_sha256']
    model, base, _, _, gram, _, signatures, _ = check_model(manifest_path, require_base_cnf=False)
    assert certificate['source_sha256'] == model['source_hashes']['complement_rook_incidence_master.py']
    assert certificate['base_cnf_sha256'] == base['cnf_sha256']
    assert certificate['base_domain_sha256'] == base['domain_sha256']
    selected = certificate['selected_signatures']
    assumptions = full_assumptions(selected)
    assert all(sum(i in signatures[s] and j in signatures[s] for s in selected) == gram[i][j]
               for i in range(27) for j in range(27))
    units = certificate['core_units']
    assert units == sorted(set(units), key=abs) and set(units) <= set(assumptions)
    assert certificate['learned_selector_clause'] == [-literal for literal in units]
    retained_cnf = ROOT/certificate['retained_cnf']
    proof = ROOT/certificate['retained_proof']
    assert digest(retained_cnf) == certificate['retained_cnf_sha256']
    assert digest(proof) == certificate['retained_proof_sha256']
    retained = list(clauses(retained_cnf))
    assert len(retained) == certificate['retained_input_clauses']
    assert sum(1 for _ in proof.open()) == certificate['retained_proof_lines']
    needed = {tuple(sorted(clause)) for clause in retained}
    with tempfile.TemporaryDirectory(prefix='rook-master-cut-replay-') as temporary:
        directory = Path(temporary)
        rebuilt_path = directory/'base.cnf'
        rebuilt = rebuild_base(ROOT/base['domain_path'], ROOT/base['boundary_certificate'],
                               ROOT/base['hall_certificate'], base['representative'],
                               rebuilt_path, directory/'base-model.json')
        assert rebuilt['source_hashes'] == base['source_hashes']
        for key in ('cnf_sha256', 'domain_file_sha256', 'boundary_sha256', 'hall_sha256',
                    'domain_sha256', 'signature_variables', 'edge_variables', 'variables',
                    'clauses', 'packing_clauses', 'derived_positive_units',
                    'derived_negative_units', 'full_outside_caps_imposed',
                    'orbit_equalities', 'fixed_incidence_witnesses'):
            assert rebuilt[key] == base[key], key
        full = directory/'core-units.cnf'
        materialize_units(rebuilt_path, base['variables'], base['clauses'], units, full)
        assert digest(full) == certificate['core_unit_cnf_sha256']
        count = 0
        for clause in clauses(full):
            needed.discard(tuple(sorted(clause)))
            count += 1
        assert count == base['clauses']+len(units) and not needed
    checked = subprocess.run([str(checker), str(retained_cnf), str(proof), '-t', '30', '-w'],
                             text=True, capture_output=True, timeout=35, check=False)
    log.write_text(checked.stdout+checked.stderr)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (checked.returncode, checked.stdout, checked.stderr)
    record = {'status': 'full baseline and explicit signed-unit CNF rebuilt; retained inclusion and DRAT verified',
              'design_index': certificate['design_index'], 'core_unit_cnf_sha256': certificate['core_unit_cnf_sha256'],
              'core_literals': len(units), 'learned_selector_clause': certificate['learned_selector_clause'],
              'retained_input_clauses': len(retained), 'base_constraints_unchanged': True,
              'whole_core_exclusion': len(units) == 0}
    print(json.dumps(record, indent=2), flush=True)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('certificate', 'drat-trim', 'log'):
        parser.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    replay(args.certificate, args.drat_trim, args.log)
