"""Rebuild a global-prism-free case and check its retained UNSAT proof.

An exclusion applies to one of the four cases covering globally
prism-free graphs. It is not an exclusion of the old same-index case
whose chosen root alone was prism-free.
"""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from pysat.formula import CNF, IDPool

import root_full_caps as base
import root_full_caps_coverage as coverage
import root_full_caps_lex as lex
import root_full_caps_anchor_max_solve as maximum
import root_prism_free_overlay as overlay
import root_prism_free_structure as structure


ROOT = overlay.ROOT


def replay(certificate_path, checker):
    certificate = json.loads(certificate_path.read_text())
    assert certificate['scope'] == overlay.SCOPE
    assert certificate['excludes_whole_old_same_index_case'] is False
    assert certificate['lazy_cuts'] == certificate['graph_automorphism_assumptions'] == 0
    assert certificate['wrapper_source_sha256'] == base.digest(Path(__file__))
    model_path = ROOT/certificate['model']
    assert base.digest(model_path) == certificate['model_sha256']
    model, previous, analysis, added, _ = overlay.check_bindings(model_path)
    index = model['case_index']
    case = previous['case']
    assert certificate['case_index'] == index == case['index']
    assert certificate['partition'] == model['partition'] == case['partition']
    assert certificate['full_cnf_sha256'] == model['cnf_sha256']
    assert lex.replay(ROOT/previous['analysis']) == analysis
    max_certificate = maximum.maximum_certificate(ROOT/previous['maximum_anchor_certificate'], full_replay=True)
    structure_path = ROOT/model['structure_certificate']
    structure_record = json.loads(structure_path.read_text())
    structure.build(structure_path, ROOT/structure_record['clause_path'], replay=True)
    original = json.loads((ROOT/analysis['base_manifest']).read_text())
    matching_path = ROOT/original['coverage_certificate']
    assert base.digest(matching_path) == original['coverage_sha256']
    matching = coverage.replay(matching_path)
    assert matching['cases'][index]['partition'] == case['partition']
    assert base.forward_controls() == original['forward_controls']
    assert base.rook_control() == original['rook_positive_control']

    cnf, variables, _, labels, _, metadata = base.formula(14)
    assert json.loads(json.dumps(metadata)) == original['metadata']
    units = base.anchor_units(14, tuple(case['partition']), labels, variables)
    assert units == original['cases'][index]['normalization_units']
    cnf.extend([[unit] for unit in units])
    assert (cnf.nv, len(cnf.clauses)) == (case['base_variables'], case['base_clauses'])
    with tempfile.TemporaryDirectory(prefix='root-prism-free-replay-') as temporary:
        path = Path(temporary)/'rebuilt.cnf'
        cnf.to_file(path)
        assert base.digest(path) == case['base_cnf_sha256']
        pool = IDPool(start_from=cnf.nv + 1)
        for generator in case['generators']:
            lifted = lex.lift(tuple(case['partition']), generator['image'])
            cnf.extend(lex.lex_clauses(list(range(1, 3487)), lifted['lex_right'], pool))
        assert (cnf.nv, len(cnf.clauses)) == (case['total_variables'], case['total_clauses'])
        cnf.to_file(path)
        assert base.digest(path) == previous['lex_cnf_sha256']
        side_units = max_certificate['cases'][index]['clauses']
        assert len(side_units) == 84 and all(len(clause) == 1 and clause[0] < 0 for clause in side_units)
        cnf.extend(side_units)
        assert (cnf.nv, len(cnf.clauses)) == (previous['variables'], previous['clauses'])
        cnf.to_file(path)
        assert base.digest(path) == previous['cnf_sha256']
        assert len(added) == 34440 and all(len(clause) == 4 for clause in added)
        cnf.extend(added)
        assert (cnf.nv, len(cnf.clauses)) == (model['variables'], model['clauses'])
        cnf.to_file(path)
        assert base.digest(path) == model['cnf_sha256']

    core, proof = ROOT/certificate['core_file'], ROOT/certificate['proof_file']
    assert base.digest(core) == certificate['core_sha256']
    assert base.digest(proof) == certificate['proof_sha256']
    retained = CNF(from_file=str(core))
    assert len(retained.clauses) == certificate['retained_clauses']
    needed = {tuple(sorted(clause)) for clause in retained.clauses}
    for clause in cnf.clauses:
        needed.discard(tuple(sorted(clause)))
    assert not needed
    checked = subprocess.run([str(checker), str(core), str(proof), '-t', '60', '-w'],
                             text=True, capture_output=True, timeout=65, check=False)
    print(checked.stdout, end='', flush=True)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (
        checked.returncode, checked.stdout, checked.stderr)
    result = {'status': 'global-prism-free coverage, exact full formula, retained inclusion, and proof verified',
              'scope': overlay.SCOPE, 'case_index': index, 'partition': case['partition'],
              'full_cnf_sha256': model['cnf_sha256'], 'variables': cnf.nv,
              'clauses': len(cnf.clauses), 'retained_clauses': len(retained.clauses),
              'excludes_whole_old_same_index_case': False}
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certificate', type=Path)
    parser.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    replay(args.certificate.resolve(), args.drat_trim.resolve())
