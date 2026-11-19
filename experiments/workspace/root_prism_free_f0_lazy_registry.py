"""Direct exact proof registry for a later lazy incidence continuation.

Rebuild only the original 56,994-clause direct-cut base. Check every
integer row potential and six complete shared-potential proof families
directly, with hash-bound transcript provenance. No ancestor auxiliary
CNF, optimizer, or incidence solver is regenerated.
"""

import argparse
import gzip
import hashlib
import json
from math import gcd
from pathlib import Path

import integer_cut_clause_explanations as explain
import root_prism_free_f0_incidence_row_loop as individual
import root_prism_free_f0_shared_row_separator as old_shared
import root_prism_free_f0_shared_deficit_separator as shared
import root_prism_free_f0_symmetric_selector_cut as first_shared
import root_prism_free_f0_shared_ray_repair as repair
import root_prism_free_f0_deficit_transcript_bundle as bundle


ROOT, LOGS, BASE = individual.ROOT, individual.LOGS, individual.BASE
digest, canonical, portable, load_json = individual.digest, individual.canonical, individual.portable, individual.load_json
SOURCES = {
    'integer_cut_clause_explanations.py': 'f57d51b8be3fefd7a5d1035c52cc5758c719adb6a79d16a0909f1a54fdaa59f3',
    'root_prism_free_f0_incidence_row_loop.py': '5f4f536052f97ba725f10ebb77e7f55b0e94c57947e643e97d7df6915e762352',
    'root_prism_free_f0_shared_row_separator.py': '7d8f3324826c1fa7fa05e79dbbee7c6e16b064dd01ef5e548160f6a7fe04368a',
    'root_prism_free_f0_shared_deficit_separator.py': '6bc6944ed00713d384251ab54e54684e6f5ea29300f9ff243df5282f522375bf',
    'root_prism_free_f0_symmetric_selector_cut.py': '15ec937609b7de44b808e9de7053bb9ee080ddf732a3defd2b23577c026fe274',
    'root_prism_free_f0_shared_ray_repair.py': '4a214635d5ba1ec73477a3acdfd36c30cb65be3c4c4fb662ee19a615388c07d3',
    'root_prism_free_f0_deficit_transcript_bundle.py': '4f04550ba62076768744f2963bffe97287ed5f2b548ea2eb0b9ca939abe9a76f'}
INPUTS = {
    'f0-deficit-row-loop-run01-terminal-manifest.json': 'd2e4aab728d3481587d584dfbad6b522ead655cf324622519e1a4241f779b6a8',
    'f0-deficit-row-loop-run01-transcript-bundle.json': 'b916565f0d9d089d3d49fb1b0ce30005d2e14a1450980450fa8827ab7d740cbe',
    'f0-deficit-row-loop-run01-cold-replay.json': '42b0f761c83e087a855a4719fde38a30c4e751f42dc90f122ef111b4c6460c73',
    'f0-deficit-row-loop-run01/result.json': '13b47be2d896887c3b23c435499bc6b4ba75c541469a3de229cebeb98b14a8fe',
    'f0-symmetric-row-loop-run01/result.json': '03c7cfa9cfde1a23df0e3b3b2ffe6e1650801eaf5daf9e79a0403f45574fd20b',
    'f0-carry-row-loop-run01/result.json': 'ecc80a941a1b0d9e152788167210a5e8b7936f28b03ee50c35658895b453d3d3',
    'f0-incidence-row-loop-run01/result.json': '4af22d0933e676079ca376c87c498add890c406d3f1b1751e473951d01f24098',
    'f0-symmetric-selector-cut-certificate.json.gz': '3aea5e48c4a35eb7e023708231f3dbf585634c25de25484f364276041260f846',
    'f0-carry-row-loop-run01-shared-ray-repair.json.gz': '96e945d1211147e2ad13ed3468f51d72bd3ef87319ca33153eda6248e0b5c7c5',
    'f0-clause-explanation-pilot-independent-audit.json': 'c0b4d68651b8e7980d66498d36e5d9b182e5bdf77c7ee3db1a800faaff50b61d'}
PARENT_RESULT = LOGS/'f0-deficit-row-loop-run01/result.json'


def checked_sources():
    for name, expected in SOURCES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    restored = bundle.verify(True)
    assert restored['record_count'] == 39
    for name, expected in INPUTS.items():
        assert digest(LOGS/name) == expected
    manifest = load_json(LOGS/'f0-deficit-row-loop-run01-terminal-manifest.json')
    for entry in manifest['files']:
        assert digest(ROOT/entry['path']) == entry['sha256']
    individual.checked_sources()
    old_shared.check_sources()
    shared.check_sources()
    return {'parent_manifest_sha256': INPUTS['f0-deficit-row-loop-run01-terminal-manifest.json'],
            'transcript_archive_sha256': restored['archive_sha256'],
            'exact_transcript_records': 39,
            'no_ancestor_auxiliary_CNF_rebuilt': True}


def signed_cut(terms, origin):
    assert terms == sorted(terms) and len({a for a, _ in terms}) == len(terms)
    assert all(type(a) is int and 0 <= a < 480 and type(c) is int and c for a, c in terms)
    divisor = gcd(*(abs(c) for _, c in terms))
    normalized = [[a, c//divisor] for a, c in terms]
    return {'signed_coefficients': normalized, 'origin': origin,
            'predicate_sha256': hashlib.sha256(canonical(normalized)).hexdigest()}


def cut_terms(family, cut):
    if family == 'individual':
        terms = [(cut['target']+1, cut['demand'])]
        terms += [(a+1, -weight) for a, weight in cut['weights']]
    else:
        assert family == 'symmetric'
        terms = [(a+1, coefficient) for a, coefficient in cut['signed_coefficients']]
    result = [[a, c] for a, c in explain.coefficients(terms).items()]
    assert all(1 <= a <= 480 and c for a, c in result)
    return result


def population(context):
    domain, _, _, _, triples, _, _, _ = context
    assert len(triples) == 480 and all(len(set(h)) == 3 for h in triples)
    raw = load_json(LOGS/'f0-exterior-row-domains02.json.gz')
    core = raw['component_core_rows']
    gram = [[12*int(i == j)+2-(core[i+3]&core[j+3]).bit_count()
             -((core[i+3] >> (j+3)) & 1) for j in range(18)] for i in range(18)]
    model = individual.old.base.checked_model(individual.old.BASE_MODEL)
    coverage = model['formula']['Gram_position_coverage']
    assert [(i, j) for i, j, *_ in coverage] == [(i, j) for i in range(18) for j in range(i, 18)]
    for i, j, quota, member_count, _ in coverage:
        assert quota == gram[i][j]
        assert member_count == sum(i in h and j in h for h in triples)
    assert triples == domain['signature_domain']
    assert [gram[i][i] for i in range(18)] == [10]*18
    assert sum(gram[i][i] for i in range(18)) == 3*60
    return {'population': 60, 'universe': list(range(1, 481)),
            'derivation': 'sum18 original diagonal Gram equations:3*sum(z)=180',
            'all171_Gram_positions_rechecked': True,
            'each_signature_in_exactly_three_diagonal_supports': True,
            'base_model_sha256': individual.old.BASE_MODEL_SHA}


def bound_step_file(step, key):
    path = ROOT/step[key]
    assert digest(path) == step[key+'_sha256']
    return load_json(path)


def shared_family(result, iteration, helper, context):
    _, _, _, _, triples, targets, neighbors, actions = context
    step = result['iterations'][iteration]
    selected = bound_step_file(step, 'candidate')['selected_signature_ids']
    raw = bound_step_file(step, 'shared_rows')
    helper.replay(raw, selected, triples, targets, neighbors)
    assert raw['exact_fixed_design_infeasibility']
    lifted = helper.lift(selected, raw['fixed_capacity_potentials']['integer_potentials60_by18'],
                         triples, targets, neighbors, actions)
    assert lifted == bound_step_file(step, 'symmetric_lift')
    cuts = [signed_cut(t['signed_coefficients'], {
        'kind': 'loop exact shared-row lift', 'iteration': iteration,
        'shared_result_sha256': step['shared_rows_sha256'],
        'core_action_index': t['core_action_index']}) for t in lifted['transported_cuts']]
    proof = {'shared_record': step['shared_rows'], 'shared_record_sha256': step['shared_rows_sha256'],
             'exact_ray_check': raw['exact_ray_check'],
             'lift_sha256': step['symmetric_lift_sha256'],
             'complete_global_edge_count': lifted['complete_global_edges'],
             'normalized_gap': lifted['normalized_gap'], 'transport_count': len(cuts)}
    return cuts, proof


def seeds(context, results):
    domain, records, old_cuts, old_clauses, _, _, _, _, = context
    found = {}
    def add(selected, origin):
        point = individual.old.inspect(selected, domain, records, old_cuts, old_clauses)
        key = tuple(selected)
        if key not in found:
            found[key] = {'selected_signature_ids': selected, 'origins': [],
                          'base_inspection_sha256': hashlib.sha256(canonical(point)).hexdigest()}
        found[key]['origins'].append(origin)
    _, _, _, selected, _, _ = individual.box.load()
    name = 'f0-exterior-row-cut-overlay-run01/result.json'
    add(selected, {'path': portable(LOGS/name), 'sha256': individual.box.INPUTS[name]})
    first_path = LOGS/'f0-incidence-row-loop-run01/result.json'
    first = load_json(first_path)
    for result_path, result in [(first_path, first)]+results:
        for step in result['iterations']:
            if 'candidate' in step:
                selected = bound_step_file(step, 'candidate')['selected_signature_ids']
                add(selected, {'path': step['candidate'], 'sha256': step['candidate_sha256'],
                               'result': portable(result_path), 'result_sha256': digest(result_path),
                               'iteration': step['iteration']})
    return list(found.values())


def calculate(complete_replay=False):
    provenance = checked_sources()
    _, domain, records, cnf, old_cuts, old_clauses, _, base_formula = individual.old.rebuild(complete_replay)
    assert cnf.nv == 28308 and len(cnf.clauses) == 56994
    triples, targets, neighbors, _, actions, _ = individual.box.load()
    context = (domain, records, old_cuts, old_clauses, triples, targets, neighbors, actions)
    pop = population(context)
    parent = load_json(PARENT_RESULT)
    rows_path = ROOT/parent['individual-registry']
    assert digest(rows_path) == parent['individual-registry_sha256']
    rows = load_json(rows_path)
    assert len(rows) == 647
    for cut in rows:
        individual.validate_cut(cut, triples, targets, neighbors)
    last = parent['iterations'][-1]
    selected = bound_step_file(last, 'candidate')['selected_signature_ids']
    final_rows = bound_step_file(last, 'individual_rows')
    individual.check_rows(final_rows, selected, triples, targets, neighbors, actions)
    additional = individual.row_cut_candidates(final_rows, last['iteration'], triples, targets, neighbors)
    seen = {cut['normalized_predicate_sha256'] for cut in rows}
    missing = []
    for cut in additional:
        if cut['normalized_predicate_sha256'] not in seen:
            individual.validate_cut(cut, triples, targets, neighbors)
            missing.append(len(rows)); rows.append(cut)
            seen.add(cut['normalized_predicate_sha256'])
    assert len(missing) == 13 and len(rows) == len(seen) == 660

    proofs, symmetric = [], []
    first_path = LOGS/'f0-symmetric-selector-cut-certificate.json.gz'
    first = first_shared.calculate()
    assert canonical(first) == canonical(load_json(first_path))
    for transport in first['transported_cuts']:
        terms = sorted(transport['positive_terms']+[[a, -w] for a, w in transport['negative_side_positive_weights']])
        symmetric.append(signed_cut(terms, {'kind': 'published symmetric selector cut',
            'certificate_sha256': INPUTS[first_path.name], 'core_action_index': transport['core_action_index']}))
    proofs.append({'kind': 'published full-domain certificate', 'path': portable(first_path),
                   'sha256': digest(first_path), 'complete_direct_calculation_replayed': True, 'transports': 12})
    older_path = LOGS/'f0-symmetric-row-loop-run01/result.json'
    older = load_json(older_path)
    cuts, proof = shared_family(older, 4, old_shared, context)
    symmetric.extend(cuts); proofs.append(proof)
    repaired_path = LOGS/'f0-carry-row-loop-run01-shared-ray-repair.json.gz'
    repaired = repair.calculate()
    assert canonical(repaired) == canonical(load_json(repaired_path))
    for transport in repaired['universal_selector_lift']['transported_cuts']:
        symmetric.append(signed_cut(transport['signed_coefficients'], {
            'kind': 'separate exact-deficit repair of frozen parent UNKNOWN',
            'repair_certificate_sha256': digest(repaired_path),
            'core_action_index': transport['core_action_index']}))
    proofs.append({'kind': 'separate exact repaired ray', 'path': portable(repaired_path),
                   'sha256': digest(repaired_path), 'exact_ray_check': repaired['exact_ray_check'], 'transports': 12})
    for iteration in (9, 10, 11):
        cuts, proof = shared_family(parent, iteration, shared, context)
        symmetric.extend(cuts); proofs.append(proof)
    signed_path = ROOT/parent['symmetric-registry']
    assert digest(signed_path) == parent['symmetric-registry_sha256']
    assert symmetric == load_json(signed_path)
    assert len(symmetric) == len({cut['predicate_sha256'] for cut in symmetric}) == 72
    carried_path = LOGS/'f0-carry-row-loop-run01/result.json'
    candidates = seeds(context, [(older_path, older), (carried_path, load_json(carried_path)), (PARENT_RESULT, parent)])
    assert len(candidates) == 30
    for record in candidates:
        selected = set(record['selected_signature_ids'])
        values = [sum(c for a, c in cut_terms(family, cut) if a-1 in selected)
                  for family, registry in [('individual', rows), ('symmetric', symmetric)] for cut in registry]
        assert max(values) > 0
        record['complete_registry_value_sha256'] = hashlib.sha256(canonical(values)).hexdigest()
        record['violated_proved_inequalities'] = sum(value > 0 for value in values)
    report = {'status': 'direct complete732-cut mathematical registry and30 prior candidate controls PASS',
        'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': SOURCES,
        'input_hashes': INPUTS, 'parent_provenance': provenance,
        'base_formula': base_formula, 'population_premise': pop,
        'individual_cuts': rows, 'symmetric_cuts': symmetric,
        'direct_individual_potentials_checked': len(rows),
        'previously_unencoded_individual_indices': missing,
        'shared_proof_families': proofs, 'shared_family_count': len(proofs),
        'signed_inequalities_checked': len(symmetric), 'seed_candidates': candidates,
        'verified_core_actions': actions, 'complete_global_edges': 68394,
        'raw_registry_sha256': hashlib.sha256(canonical([rows, symmetric])).hexdigest(),
        'all480_selectors_free': True, 'no_candidate_or_second_component_fixed': True,
        'ancestor_auxiliary_CNF_rebuilt': False, 'optimizer_or_incidence_solver_called': False}
    return report, cnf, context


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'replay'])
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report, _, _ = calculate(args.mode == 'replay')
    if args.mode == 'prepare':
        assert not args.certificate.exists()
        args.certificate.write_bytes(gzip.compress(canonical(report)+b'\n', mtime=0))
    else:
        assert canonical(report) == canonical(load_json(args.certificate))
    summary = {k: v for k, v in report.items() if k not in
               ('individual_cuts', 'symmetric_cuts', 'seed_candidates', 'verified_core_actions', 'base_formula')}
    summary['certificate_sha256'] = digest(args.certificate)
    summary['seed_candidates'] = len(report['seed_candidates'])
    args.output.write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2), flush=True)
