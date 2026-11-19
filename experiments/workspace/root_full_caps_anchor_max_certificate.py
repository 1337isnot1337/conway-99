"""Rebuild a complete maximum-anchor case and verify its retained proof.

The exclusion, if verified, concerns a new maximum-anchor case. It does
not by itself exclude every graph in the old same-index rooted case.
"""

import argparse
import json
from pathlib import Path
import subprocess
import tempfile

from pysat.formula import CNF, IDPool

import root_full_caps as base
import root_full_caps_coverage as base_coverage
import root_full_caps_lex as lex
from root_full_caps_anchor_max_solve import ROOT, check_bindings, maximum_certificate


def replay(certificate_path, checker):
    certificate = json.loads(certificate_path.read_text())
    assert certificate['excludes_old_same_index_case'] is False
    assert certificate['lazy_cuts'] == certificate['graph_automorphism_assumptions'] == 0
    assert base.digest(Path(__file__)) == certificate['wrapper_source_sha256']
    model_path = ROOT/certificate['model']
    assert base.digest(model_path) == certificate['model_sha256']
    model, analysis = check_bindings(model_path, check_cnf=False)
    assert lex.replay(ROOT/model['analysis']) == analysis
    maximum = maximum_certificate(ROOT/model['maximum_anchor_certificate'], full_replay=True)
    original = json.loads((ROOT/analysis['base_manifest']).read_text())
    matching_coverage_path = ROOT/original['coverage_certificate']
    assert base.digest(matching_coverage_path) == original['coverage_sha256']
    matching_coverage = base_coverage.replay(matching_coverage_path)
    index, case = certificate['case_index'], model['case']
    assert index == case['index']
    assert certificate['partition'] == case['partition'] == matching_coverage['cases'][index]['partition']
    assert certificate['full_cnf_sha256'] == model['cnf_sha256']
    assert base.forward_controls() == original['forward_controls']
    assert base.rook_control() == original['rook_positive_control']
    cnf, variables, _, labels, _, metadata = base.formula(14)
    assert json.loads(json.dumps(metadata)) == original['metadata']
    units = base.anchor_units(14, tuple(case['partition']), labels, variables)
    assert units == original['cases'][index]['normalization_units']
    cnf.extend([[unit] for unit in units])
    assert (cnf.nv, len(cnf.clauses)) == (case['base_variables'], case['base_clauses'])
    with tempfile.TemporaryDirectory(prefix='root-full-caps-anchor-max-replay-') as temporary:
        path = Path(temporary)/'rebuilt.cnf'
        cnf.to_file(path)
        assert base.digest(path) == case['base_cnf_sha256']
        pool = IDPool(start_from=cnf.nv+1)
        for generator in case['generators']:
            lifted = lex.lift(tuple(case['partition']), generator['image'])
            cnf.extend(lex.lex_clauses(list(range(1, 3487)), lifted['lex_right'], pool))
        assert (cnf.nv, len(cnf.clauses)) == (case['total_variables'], case['total_clauses'])
        cnf.to_file(path)
        assert base.digest(path) == model['lex_cnf_sha256']
        extra = maximum['cases'][index]['clauses']
        assert len(extra) == 84 and all(len(clause) == 1 and clause[0] < 0 for clause in extra)
        sides = {-clause[0] for clause in extra}
        assert len(sides) == 84
        for generator in case['generators']:
            image = lex.lift(tuple(case['partition']), generator['image'])['edge_image']
            assert {image[v-1] for v in sides} == sides
        cnf.extend(extra)
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
                             capture_output=True, text=True, timeout=60, check=False)
    print(checked.stdout, end='', flush=True)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout, (
        checked.returncode, checked.stdout, checked.stderr)
    result = {'status': 'maximum-anchor union coverage, lex coverage, exact CNF, inclusion, and proof verified',
              'case_index': index, 'partition': case['partition'],
              'full_cnf_sha256': model['cnf_sha256'], 'variables': cnf.nv,
              'clauses': len(cnf.clauses), 'retained_clauses': len(retained.clauses),
              'scope': 'this new maximum-anchor normalization case only',
              'excludes_old_same_index_case': False}
    print(json.dumps(result), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('certificate', type=Path)
    parser.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    replay(args.certificate.resolve(), args.drat_trim.resolve())
