"""Direct exact terminal seed plus twelve bounded-potential selector cuts.

Rebuild the original direct-cut formula once. Validate all row potentials
and all fifteen shared-potential families directly; retain the complete
parent clause prefix. No ancestor continuation formula is rebuilt.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tempfile

import root_prism_free_f0_lazy_clauses as original
import root_prism_free_f0_lazy_transcript_bundle as first_bundle
import root_prism_free_f0_lazy_continuation_transcript_bundle as parent_bundle
import root_prism_free_f0_bounded_shared_separator as bounded
import root_prism_free_f0_shared_bounded_fallback as shared


ROOT, LOGS, BASE = original.ROOT, original.LOGS, original.BASE
individual, registry = original.individual, original.registry
digest, canonical, portable, save, load_json = original.digest, original.canonical, original.portable, original.save, original.load_json
State, is_false = original.State, original.is_false
MAXIMUM_CLAUSES, MAXIMUM_VARIABLES = original.MAXIMUM_CLAUSES, original.MAXIMUM_VARIABLES
SOURCES = {
    'root_prism_free_f0_lazy_clauses.py': 'cef5448b012be57277b87297d2e3ec2c017ccea1336080f4c40c2594f2ab7640',
    'root_prism_free_f0_lazy_registry.py': '9a9a2c40241dc3899b9692568a2ee4127d17d5a4b8c33972dfd9b59a57e43478',
    'root_prism_free_f0_lazy_transcript_bundle.py': 'f30a1370460134017072f9a52c3e470871546bd94bb0108a709d387fb7aa05b0',
    'root_prism_free_f0_lazy_continuation_transcript_bundle.py': '0152cfcc6d2b22be3714bd43a3b643301ec7a7fbf485a6728e66306ca16c10ec',
    'root_prism_free_f0_bounded_shared_separator.py': 'bbdf21247d98cff416f68492415a3db6ec5f98f47d1ebb9367acac1604192798',
    'root_prism_free_f0_shared_bounded_fallback.py': '46ff20ca4269b71b80c2fd7e3ba2fec4f369b7dca3d4e08272a935cdfde72f1a'}
RESULT = LOGS/'f0-lazy-continuation-run01/result.json'
RESULT_SHA = '3bb89930202266409acfce6ca52949b5c370928216ce64e9123e22daf5f9e593'
COLD = LOGS/'f0-lazy-continuation-run01-cold-replay.json'
COLD_SHA = '7bd045ab660f3aedd2bd9c514c9e2fa8a91a4f07f415cebba2c133adc73b2330'
MANIFEST = LOGS/'f0-lazy-continuation-run01-terminal-manifest.json'
MANIFEST_SHA = 'a71e03191ed2eee685f0992923e84ad6e9900aebfc40c9ad00f29a2d639caa0d'
GAP_MANIFEST = LOGS/'f0-bounded-shared-separator-run01-terminal-manifest.json'
GAP_MANIFEST_SHA = 'ed6d480740a9bf08843494b0979a2ebc1305f0da69855a4b65d0970571d88010'
FALLBACK_CONTROLS = LOGS/'f0-shared-bounded-fallback-controls.json'
FALLBACK_CONTROLS_SHA = 'ad871ca5e7902e86be9d79b5211d8dd7c478a24f13f0da0d161d73b252de4fd5'
FINAL_CNF_SHA = '24cf3a35390b72ba17d18e33e3c62eddd7cf0c00970de9227d94320ceefe7031'
REGISTRY = LOGS/'f0-bounded-lazy-terminal-registry.json.gz'
REGISTRY_SHA = 'b761423e5fa45a9f893988586fd7e5a89414d8902c94530a1532cb91472f1a01'


def check_sources(require_registry=True):
    for name, expected in SOURCES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    original.check_sources(); shared.check_sources()
    assert first_bundle.verify(True)['record_count'] == 79
    assert parent_bundle.verify(True)['record_count'] == 62
    for path, expected in ((RESULT, RESULT_SHA), (COLD, COLD_SHA), (MANIFEST, MANIFEST_SHA),
                           (GAP_MANIFEST, GAP_MANIFEST_SHA), (FALLBACK_CONTROLS, FALLBACK_CONTROLS_SHA)):
        assert digest(path) == expected
    for manifest in (MANIFEST, GAP_MANIFEST):
        for entry in load_json(manifest)['files']:
            assert digest(ROOT/entry['path']) == entry['sha256']
    controls = load_json(FALLBACK_CONTROLS)
    assert controls['source_sha256'] == SOURCES['root_prism_free_f0_shared_bounded_fallback.py']
    assert controls['status'].startswith('PASS:') and not controls['optimizer_or_solver_called']
    if require_registry:
        assert REGISTRY_SHA is not None and digest(REGISTRY) == REGISTRY_SHA


def bound_record(record, key):
    path = ROOT/record[key]
    assert digest(path) == record[key+'_sha256']
    return load_json(path)


def later_shared_family(result, iteration, context):
    _, _, _, _, triples, targets, neighbors, actions = context
    step = result['iterations'][iteration]
    selected = bound_record(step, 'candidate')['selected_signature_ids']
    raw = bound_record(step, 'shared_rows')
    shared.original.replay(raw, selected, triples, targets, neighbors)
    assert raw['exact_fixed_design_infeasibility']
    lifted = shared.original.lift(selected, raw['fixed_capacity_potentials']['integer_potentials60_by18'],
                                  triples, targets, neighbors, actions)
    assert lifted == bound_record(step, 'symmetric_lift')
    cuts = [registry.signed_cut(t['signed_coefficients'], {
        'kind': 'lazy loop exact shared-row lift', 'iteration': iteration,
        'shared_result_sha256': step['shared_rows_sha256'], 'core_action_index': t['core_action_index']})
        for t in lifted['transported_cuts']]
    proof = {'shared_record': step['shared_rows'], 'shared_record_sha256': step['shared_rows_sha256'],
             'lift_sha256': step['symmetric_lift_sha256'], 'exact_ray_check': raw['exact_ray_check'],
             'global_edges': lifted['complete_global_edges'], 'normalized_gap': lifted['normalized_gap'],
             'transports': 12}
    return cuts, proof


def calculate():
    check_sources(False)
    baseline, cnf, context = registry.calculate(False)
    assert canonical(baseline) == canonical(load_json(original.REGISTRY))
    assert (cnf.nv, len(cnf.clauses)) == (28308, 56994)
    _, _, _, _, triples, targets, neighbors, actions = context
    result = load_json(RESULT)
    assert result['status'] == 'UNKNOWN: numerical infeasibility without an exact ray; unresolved'
    assert result['final_cnf_sha256'] == FINAL_CNF_SHA
    rows = bound_record(result, 'individual-registry')
    assert len(rows) == 1188 and rows[:660] == baseline['individual_cuts']
    for cut in rows:
        individual.validate_cut(cut, triples, targets, neighbors)
    assert len({cut['normalized_predicate_sha256'] for cut in rows}) == len(rows)

    symmetric, proofs = list(baseline['symmetric_cuts']), list(baseline['shared_proof_families'])
    first = load_json(first_bundle.RESULT)
    assert digest(first_bundle.RESULT) == first_bundle.RESULT_SHA
    for parent, iterations in ((first, (7, 9, 12)), (result, (9, 10, 12, 13, 15))):
        for iteration in iterations:
            family, proof = later_shared_family(parent, iteration, context)
            symmetric.extend(family); proofs.append(proof)
    assert len(symmetric) == 168 and symmetric == bound_record(result, 'symmetric-registry')

    preparation = LOGS/'f0-bounded-shared-separator-preparation.json.gz'
    gap_result = LOGS/'f0-bounded-shared-separator-run01.json'
    gap_replay, lifted = bounded.reconstruct(preparation, gap_result)
    assert gap_replay['exact_support_gap'] == 33
    assert lifted == load_json(LOGS/'f0-bounded-shared-separator-run01-universal-cuts.json')
    new_cuts = [registry.signed_cut(t['signed_coefficients'], {
        'kind': 'separate bounded shared support-gap certificate', 'gap_result_sha256': digest(gap_result),
        'core_action_index': t['core_action_index']}) for t in lifted['transported_cuts']]
    symmetric.extend(new_cuts)
    assert len(symmetric) == len({cut['predicate_sha256'] for cut in symmetric}) == 180
    proofs.append({'kind': 'bounded mixed-row support separator', 'result': portable(gap_result),
        'result_sha256': digest(gap_result), 'raw_gap': 33,
        'lift_sha256': digest(LOGS/'f0-bounded-shared-separator-run01-universal-cuts.json'),
        'transports': 12})
    assert len(proofs) == 15

    retained = bound_record(result, 'explanation-registry')
    assert len(retained) == 2448
    state = State(cnf, rows, symmetric, actions, baseline['population_premise'])
    state.append_records(retained)
    assert (state.cnf.nv, len(state.cnf.clauses)) == (28308, 59442)
    assert state.clause_state_sha256 == result['final_snapshot']['clause_state_sha256']
    with tempfile.TemporaryDirectory(prefix='conway-f0-bounded-lazy-parent-') as directory:
        path = Path(directory)/'parent.cnf'; state.cnf.to_file(path)
        assert digest(path) == FINAL_CNF_SHA
    parent_prefix_snapshot = state.snapshot()

    last = result['iterations'][-1]
    point = bound_record(last, 'candidate')
    selected = point['selected_signature_ids']
    domain, records, old_cuts, old_clauses, *_ = context
    assert individual.old.inspect(selected, domain, records, old_cuts, old_clauses) == point['original_incidence_and_twelve_direct_cuts']
    assert all(not is_false(record['clause'], set(selected)) for record in retained)
    evaluation = state.evaluate(selected)
    assert evaluation['violations']
    assert evaluation['all_registered_integer_values']['symmetric'][168] == 33
    assert all(v['family'] == 'symmetric' and 168 <= v['registry_index'] < 180
               and v['signed_value'] > 0 for v in evaluation['violations'])
    source = {'kind': 'seed explanations of separately proved bounded support gap',
              'candidate_sha256': last['candidate_sha256'], 'gap_result_sha256': digest(gap_result)}
    explanations, explanation_summary = state.proposals(selected, evaluation['violations'], source)
    assert explanation_summary['new_clauses_false_on_source'] > 0
    state.append_records(explanations)
    assert any(is_false(record['clause'], set(selected)) for record in explanations)
    payload = {'status': 'complete exact1368-cut terminal registry and retained prefix; no new query',
        'parent_result_sha256': RESULT_SHA, 'parent_cold_replay_sha256': COLD_SHA,
        'parent_terminal_manifest_sha256': MANIFEST_SHA, 'parent_final_cnf_sha256': FINAL_CNF_SHA,
        'bounded_gap_manifest_sha256': GAP_MANIFEST_SHA,
        'fallback_controls_sha256': FALLBACK_CONTROLS_SHA,
        'individual_cuts': rows, 'symmetric_cuts': symmetric,
        'population_premise': baseline['population_premise'], 'verified_core_actions': actions,
        'direct_individual_potentials_checked': len(rows), 'shared_proof_families': proofs,
        'retained_explanation_registry': result['explanation-registry'],
        'retained_explanation_registry_sha256': result['explanation-registry_sha256'],
        'retained_explanation_count': len(retained), 'parent_prefix_snapshot': parent_prefix_snapshot,
        'new_seed_explanation_source': source, 'new_seed_explanation_records': explanations,
        'new_seed_explanation_summary': explanation_summary,
        'terminal_candidate': last['candidate'], 'terminal_candidate_sha256': last['candidate_sha256'],
        'terminal_candidate_control': evaluation,
        'raw_registry_sha256': hashlib.sha256(canonical([rows, symmetric])).hexdigest(),
        'initial_snapshot': state.snapshot(), 'all1356_proved_parent_inequalities_retained': True,
        'all2448_parent_explanation_clauses_retained': True,
        'all480_selectors_free': True, 'terminal_candidate_fixed_or_preferred': False,
        'second_component_or_alignment_fixed': False, 'parent_UNKNOWN_unchanged': True,
        'ancestor_continuation_formulas_rebuilt': False, 'optimizer_or_solver_called': False}
    return payload, state, context


def initial(complete_replay=False):
    assert type(complete_replay) is bool
    check_sources()
    payload, state, context = calculate()
    assert canonical(payload) == canonical(load_json(REGISTRY))
    summary = {'status': 'direct exact1368-cut seed, parent prefix and new necessary explanations PASS',
        'exact_registry_sha256': REGISTRY_SHA, 'parent_result_sha256': RESULT_SHA,
        'parent_terminal_manifest_sha256': MANIFEST_SHA, 'bounded_gap_manifest_sha256': GAP_MANIFEST_SHA,
        'parent_final_cnf_sha256': FINAL_CNF_SHA,
        'individual_potentials_checked': 1188, 'shared_families_checked': 15,
        'signed_inequalities_checked': 180, 'retained_parent_explanation_clauses': 2448,
        'new_explanation_summary': payload['new_seed_explanation_summary'],
        'initial_snapshot': state.snapshot(), 'registry_start_rebased_to_complete_canonical_contents': True,
        'all480_selectors_free': True, 'no_fixed_selector_or_hint': True,
        'no_ancestor_continuation_CNF_rebuilt': True, 'optimizer_or_solver_called': False}
    return state, context, summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['export', 'replay'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    if args.mode == 'export':
        assert not REGISTRY.exists()
        payload, state, _ = calculate()
        blob = gzip.compress(canonical(payload)+b'\n', mtime=0)
        if REGISTRY_SHA is not None:
            assert hashlib.sha256(blob).hexdigest() == REGISTRY_SHA
        REGISTRY.write_bytes(blob)
        report = {'status': 'exact1368-cut registry export and new clause seed PASS; no query',
            'registry_sha256': digest(REGISTRY), 'individual_cuts': 1188,
            'symmetric_cuts': 180, 'snapshot': state.snapshot()}
    else:
        state, _, summary = initial(True)
        report = {'status': 'exact bounded-lazy seed replay PASS; no query',
            'source_sha256': digest(Path(__file__)), 'registry_sha256': REGISTRY_SHA,
            'snapshot': state.snapshot(), 'summary': summary, 'optimizer_or_solver_called': False}
    save(args.output, report); print(json.dumps(report, indent=2), flush=True)
