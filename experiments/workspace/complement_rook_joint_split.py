"""Eight explicit two-unit splits of the existing full complementary-rook model.

The base formula is unchanged. Every selector and eligible exterior edge
remains independent. The formula has mixed/degree and core-pair packing
constraints, but does not impose all exterior common-neighbor caps.
"""

import argparse
import gc
import hashlib
from itertools import combinations
import json
from pathlib import Path
import resource
from threading import Timer
import time

from pysat.formula import CNF
from pysat.solvers import Solver

import complement_rook_a_incidence as incidence
from complement_rook_duplicate_row_projection import coverage as expected_coverage
from two_rook_iso_joint_integer import inspect_point
from two_rook_iso_completion import allowed_edges
from two_rook_tip_boundary_joint_integer import digest


ROOT = Path(__file__).resolve().parents[2]


def check_base(manifest_path, require_cnf=True):
    manifest = json.loads(manifest_path.read_text())
    assert manifest['representative'] == 3943553752
    assert (manifest['signature_variables'], manifest['edge_variables']) == (252, 20934)
    assert (manifest['variables'], manifest['clauses']) == (1156482, 2575728)
    assert manifest['derived_positive_units'] == manifest['derived_negative_units'] == 0
    assert manifest['orbit_equalities'] == manifest['fixed_incidence_witnesses'] == 0
    assert manifest['full_outside_caps_imposed'] is False
    for name, expected in manifest['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    for path_key, hash_key in (('domain_path', 'domain_file_sha256'),
                               ('boundary_certificate', 'boundary_sha256'),
                               ('hall_certificate', 'hall_sha256')):
        assert digest(ROOT/manifest[path_key]) == manifest[hash_key]
    if require_cnf:
        assert digest(ROOT/manifest['cnf_path']) == manifest['cnf_sha256']
    exported = json.loads((ROOT/manifest['domain_path']).read_text())
    saved = next(case for case in exported['cases'] if case['representative'] == 3943553752)
    rows, G, triples, signatures, _, _ = incidence.domain()
    assert rows == saved['core_rows'] and G == saved['core_gram']
    assert [list(sites) for sites in signatures] == saved['core_signatures']
    needs = [[2-sum(((rows[i] >> j) & 1)+int(i == j) for j in sites)
              for i in range(27)]+[11] for sites in signatures]
    assert [need[:-1] for need in needs] == saved['mixed_need']
    edges = allowed_edges(signatures, needs)
    assert len(edges) == 20934
    # The audited base builder allocates all252 selectors first, followed
    # immediately by its20934 edge variables, before any counters.
    variables = {edge: 253+i for i, edge in enumerate(edges)}
    domain = {'core_rows': rows, 'gram': G, 'signatures': signatures,
              'mixed_need': needs,
              'edge_variables': [[v, w, var] for (v, w), var in variables.items()]}
    domain_hash = hashlib.sha256(json.dumps(domain, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    assert domain_hash == manifest['domain_sha256']
    return manifest, rows, G, triples, signatures, needs, variables


def split_prefix(base_path, variables, clauses):
    """Hash the unchanged body with the header adjusted for two extra clauses."""
    hasher = hashlib.sha256()
    with base_path.open('rb') as stream:
        assert stream.readline() == f'p cnf {variables} {clauses}\n'.encode()
        hasher.update(f'p cnf {variables} {clauses+2}\n'.encode())
        last = b''
        for block in iter(lambda: stream.read(1024*1024), b''):
            hasher.update(block)
            last = block
        assert last.endswith(b'0\n')
    return hasher


def split_hash(prefix, units):
    assert len(units) == 2 and len(set(units)) == 2
    hasher = prefix.copy()
    for unit in units:
        hasher.update(f'{unit} 0\n'.encode())
    return hasher.hexdigest()


def materialize(base_path, variables, clauses, units, output):
    with base_path.open('rb') as source, output.open('wb') as target:
        assert source.readline() == f'p cnf {variables} {clauses}\n'.encode()
        target.write(f'p cnf {variables} {clauses+2}\n'.encode())
        for block in iter(lambda: source.read(1024*1024), b''):
            target.write(block)
        for unit in units:
            target.write(f'{unit} 0\n'.encode())


def prepare(base_manifest, coverage_path, output_directory):
    base, _, G, triples, _, _, _ = check_base(base_manifest)
    covered = json.loads(coverage_path.read_text())
    assert covered == expected_coverage()
    assert covered['RS_Gram_quota'] == G[0][13] == 2
    position = {triple: i for i, triple in enumerate(triples)}
    prefix = split_prefix(ROOT/base['cnf_path'], base['variables'], base['clauses'])
    sources = ('complement_rook_joint_split.py', 'complement_rook_a_incidence.py',
               'complement_rook_duplicate_row_projection.py', 'complement_rook_row_projection.py',
               'complement_rook_a_incidence_census.py')
    source_hashes = {name: digest(Path(__file__).with_name(name)) for name in sources}
    output_directory.mkdir(parents=True, exist_ok=True)
    records = []
    for i, case in enumerate(covered['cases']):
        indices = [position[0, 4, t] for t in case['representative_tips']]
        units = [s+1 for s in indices]
        assert all(1 <= literal <= 252 for literal in units)
        record = {
            'status': 'existing full joint model plus exactly two selected-signature units prepared',
            'case_index': i, 'representative_tips': case['representative_tips'],
            'covered_tip_pairs': case['orbit_size'], 'signature_indices': indices,
            'selected_signature_units': units, 'additional_clauses': [[unit] for unit in units],
            'base_model_manifest': str(base_manifest), 'base_manifest_sha256': digest(base_manifest),
            'base_cnf_path': base['cnf_path'], 'base_cnf_sha256': base['cnf_sha256'],
            'coverage_path': str(coverage_path), 'coverage_sha256': digest(coverage_path),
            'base_domain_sha256': base['domain_sha256'],
            'variables': base['variables'], 'clauses': base['clauses']+2,
            'split_cnf_sha256': split_hash(prefix, units), 'source_hashes': source_hashes,
            'signature_variables': 252, 'edge_variables': 20934,
            'full_outside_caps_imposed': False, 'extra_a_bound_added': False,
            'orbit_equalities': 0, 'fixed_incidence_witnesses': 0, 'lazy_cuts': 0,
            'assembly': 'parse bound base CNF and append exactly the two singleton clauses in saved order',
        }
        path = output_directory/f'complement-rook-joint-split-{i}-model.json'
        path.write_text(json.dumps(record, indent=2)+'\n')
        records.append(record)
        print(json.dumps({key: record[key] for key in
                          ('case_index', 'representative_tips', 'selected_signature_units',
                           'variables', 'clauses', 'split_cnf_sha256')}), flush=True)
    assert sum(record['covered_tip_pairs'] for record in records) == 21
    return records


def check_case(path, require_cnf=True):
    case = json.loads(path.read_text())
    for name, expected in case['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    base_path = ROOT/case['base_model_manifest']
    assert digest(base_path) == case['base_manifest_sha256']
    base, rows, G, triples, signatures, needs, variables = check_base(base_path, require_cnf)
    coverage_path = ROOT/case['coverage_path']
    assert digest(coverage_path) == case['coverage_sha256']
    covered = json.loads(coverage_path.read_text())
    assert covered == expected_coverage()
    member = covered['cases'][case['case_index']]
    assert member['representative_tips'] == case['representative_tips']
    assert member['orbit_size'] == case['covered_tip_pairs']
    assert [triples[s] for s in case['signature_indices']] == [(0, 4, t) for t in case['representative_tips']]
    assert case['selected_signature_units'] == [s+1 for s in case['signature_indices']]
    assert case['additional_clauses'] == [[unit] for unit in case['selected_signature_units']]
    assert (case['variables'], case['clauses']) == (base['variables'], base['clauses']+2)
    assert case['base_domain_sha256'] == base['domain_sha256']
    assert case['base_cnf_sha256'] == base['cnf_sha256']
    assert not case['extra_a_bound_added'] and not case['full_outside_caps_imposed']
    assert case['orbit_equalities'] == case['fixed_incidence_witnesses'] == case['lazy_cuts'] == 0
    if require_cnf:
        prefix = split_prefix(ROOT/base['cnf_path'], base['variables'], base['clauses'])
        assert split_hash(prefix, case['selected_signature_units']) == case['split_cnf_sha256']
    return case, base, rows, signatures, variables


def solve(manifest_path, seconds, proof_path, output):
    case, base, rows, signatures, variables = check_case(manifest_path)
    result = {'status': 'running', 'case_index': case['case_index'],
              'representative_tips': case['representative_tips'],
              'covered_tip_pairs': case['covered_tip_pairs'],
              'manifest_path': str(manifest_path), 'manifest_sha256': digest(manifest_path),
              'split_cnf_sha256': case['split_cnf_sha256'], 'selected_signature_units': case['selected_signature_units'],
              'requested_seconds': seconds, 'budget_includes_parse_and_bootstrap': True,
              'solver': 'glucose4', 'proof_enabled': True, 'full_outside_caps_imposed': False,
              'extra_a_bound_added': False, 'lazy_cuts_added': 0,
              'binary_point': None, 'completed_witness': None}
    output.write_text(json.dumps(result, indent=2)+'\n')
    started = time.monotonic()
    cnf = CNF(from_file=str(ROOT/base['cnf_path']))
    assert (cnf.nv, len(cnf.clauses)) == (base['variables'], base['clauses'])
    for clause in case['additional_clauses']:
        cnf.append(clause)
    assert (cnf.nv, len(cnf.clauses)) == (case['variables'], case['clauses'])
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
        del cnf
        gc.collect()
        remaining = seconds-(time.monotonic()-started)
        result['bootstrap_seconds'] = time.monotonic()-started
        print(json.dumps({'case': case['case_index'], 'bootstrap_seconds': result['bootstrap_seconds'],
                          'remaining_seconds': max(0, remaining)}), flush=True)
        if remaining > 0:
            timer = Timer(remaining, solver.interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
        else:
            answer = None
        result['solve_return_seconds'] = time.monotonic()-started
        result['solver_statistics'] = solver.accum_stats()
        if answer is None:
            result['status'] = 'UNKNOWN at budget; no point or exclusion'
        elif answer is False:
            proof = solver.get_proof()
            assert proof is not None
            proof_path.parent.mkdir(parents=True, exist_ok=True)
            proof_path.write_text('\n'.join(proof)+'\n')
            result.update(status='solver UNSAT; saved proof awaits independent verification',
                          proof_path=str(proof_path), proof_sha256=digest(proof_path), proof_lines=len(proof))
        else:
            positive = {v for v in solver.get_model() if v > 0}
            assert set(case['selected_signature_units']) <= positive
            point, violations = inspect_point(positive, list(range(1, 253)), variables, rows, signatures)
            result['binary_point'] = point
            result['cap_violation_witnesses'] = violations
            if point['defective_pairs']:
                result['status'] = 'SAT of necessary model; explicit exterior defects remain'
            else:
                assert not violations
                result.update(status='exact99-vertex SRG candidate; independent validation required',
                              completed_witness=point)
    result['total_seconds'] = time.monotonic()-started
    result['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('binary_point', 'completed_witness', 'cap_violation_witnesses')}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    builder = commands.add_parser('prepare')
    builder.add_argument('--base-manifest', type=Path, required=True)
    builder.add_argument('--coverage', type=Path, required=True)
    builder.add_argument('--output-directory', type=Path, required=True)
    runner = commands.add_parser('solve')
    runner.add_argument('--manifest', type=Path, required=True)
    runner.add_argument('--seconds', type=float, default=30)
    runner.add_argument('--proof', type=Path, required=True)
    runner.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.base_manifest, args.coverage, args.output_directory)
    else:
        assert 0 < args.seconds <= 30
        solve(args.manifest, args.seconds, args.proof, args.output)
