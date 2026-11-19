"""Direct2928-cut seed, complete retained clauses and24 potential families.

Only the original56,994-clause direct-cut formula is rebuilt. Every
individual potential and every shared-potential coefficient is checked
with integers. The parent62334-clause prefix is reproduced byte for
byte, then the twelve separately certified gap64 cuts yield necessary
seed explanations. No selector or second component is fixed.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import tempfile

import root_prism_free_f0_lazy_clauses as original
import root_prism_free_f0_bounded_lazy_transcript_bundle as parent_bundle
import root_prism_free_f0_shared_reserved_fallback as shared
import root_prism_free_f0_quadratic_portfolio as quadratic


ROOT, LOGS, BASE = original.ROOT, original.LOGS, original.BASE
individual, registry = original.individual, original.registry
digest, canonical, portable, save, load_json = original.digest, original.canonical, original.portable, original.save, original.load_json
State, is_false = original.State, original.is_false
MAXIMUM_CLAUSES, MAXIMUM_VARIABLES = original.MAXIMUM_CLAUSES, original.MAXIMUM_VARIABLES
SOURCES = {
    'root_prism_free_f0_lazy_clauses.py': 'cef5448b012be57277b87297d2e3ec2c017ccea1336080f4c40c2594f2ab7640',
    'root_prism_free_f0_lazy_registry.py': '9a9a2c40241dc3899b9692568a2ee4127d17d5a4b8c33972dfd9b59a57e43478',
    'root_prism_free_f0_bounded_lazy_transcript_bundle.py': '65153e9dc7ba86c43d451a26abb8129b8deb9b1abdc5e8fc556ed6502f5a5fec',
    'root_prism_free_f0_shared_reserved_fallback.py': '0685fc162e91a466ed033becb7d01259c4869f2afd9214474b4b0eae7dfcd066',
    'root_prism_free_f0_quadratic_portfolio.py': '33e6abf18bd9f87a3814b7486294ac9e5ef1f131a332b087fe3e7207fbf46319'}
RESULT = LOGS/'f0-bounded-lazy-continuation-run01/result.json'
RESULT_SHA = '88c4858aa36aaf3af15f4b53ce41be5c1fee3d8f2c237a49e2df026f1228bd86'
COLD = LOGS/'f0-bounded-lazy-continuation-run01-cold-replay.json'
COLD_SHA = '95996661c85ce21aa4ac6af219a1e773d170b664170380ef7012deb78676ae98'
MANIFEST = LOGS/'f0-bounded-lazy-continuation-run01-terminal-manifest.json'
MANIFEST_SHA = 'fcdba71c12c9520d8d35fd3f519ec9478595006cd95dba5f3cb94dbc7f2d600a'
GAP_MANIFEST = LOGS/'f0-terminal-bounded-query-run01-terminal-manifest.json'
GAP_MANIFEST_SHA = '707d5d801a9a847ada6ed923a79db234f0822717f7dc266a699f800d5f374443'
FINAL_CNF_SHA = '27e32a5d17bbad0b8101262b026d82fb8da82bed1ba13eb01b94fe64ebc42c1e'
CONTROL_INPUTS = {
    'f0-shared-reserved-fallback-controls.json': '38a906430f39f4606ca0f5ae562d1beadd55f754293fd7b27392071acd705cd5',
    'f0-quadratic-portfolio-controls.json': '439cddc0dea291651ad4db3fe0f13f1e00eb6863ff3010645afb2a685705fee2'}
REGISTRY = LOGS/'f0-allocated-lazy-terminal-registry.json.gz'
REGISTRY_SHA = 'bf8ca34d455554064a3c2259576d84764163e3a020071a97ab269daa23c35b8a'


def check_sources(require_registry=True):
    for name, expected in SOURCES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    original.check_sources(); shared.check_sources(); quadratic.check_sources()
    assert parent_bundle.verify(True)['record_count'] == 253
    for path, expected in ((RESULT, RESULT_SHA), (COLD, COLD_SHA), (MANIFEST, MANIFEST_SHA),
                           (GAP_MANIFEST, GAP_MANIFEST_SHA)):
        assert digest(path) == expected
    for manifest in (MANIFEST, GAP_MANIFEST):
        for entry in load_json(manifest)['files']:
            assert digest(ROOT/entry['path']) == entry['sha256']
    for name, expected in CONTROL_INPUTS.items():
        assert digest(LOGS/name) == expected
        assert not load_json(LOGS/name)['optimizer_or_solver_called']
    if require_registry:
        assert REGISTRY_SHA is not None and digest(REGISTRY) == REGISTRY_SHA


def bound_record(record, key):
    path = ROOT/record[key]
    assert digest(path) == record[key+'_sha256']
    return load_json(path)


def initial_portfolio(context):
    prepared = quadratic.read(quadratic.PREPARATION)
    portfolio = quadratic.Portfolio(prepared)
    _, _, _, _, triples, targets, neighbors, actions = context
    assert triples == portfolio.triples and targets == portfolio.targets and actions == portfolio.actions
    assert [[a, b] for a in range(480) for b in neighbors[a] if a < b] == portfolio.edges
    return portfolio


def calculate():
    check_sources(False)
    individual.checked_sources()
    _, domain, records, cnf, old_cuts, old_clauses, _, base_formula = individual.old.rebuild(False)
    assert (cnf.nv, len(cnf.clauses)) == (28308, 56994)
    triples, targets, neighbors, _, actions, _ = individual.box.load()
    context = (domain, records, old_cuts, old_clauses, triples, targets, neighbors, actions)
    population = registry.population(context)
    portfolio = initial_portfolio(context)
    result = load_json(RESULT)
    assert result['status'] == 'UNKNOWN: no exact shared certificate before shared budget; unresolved'
    assert result['final_cnf_sha256'] == FINAL_CNF_SHA
    rows = bound_record(result, 'individual-registry')
    assert len(rows) == 2640
    for cut in rows:
        individual.validate_cut(cut, triples, targets, neighbors)
    assert len({cut['normalized_predicate_sha256'] for cut in rows}) == len(rows)
    symmetric = bound_record(result, 'symmetric-registry')
    assert len(symmetric) == 276
    recovered = []
    for family in portfolio.families:
        terms, _ = quadratic.algebra.normalized([[a, c] for a, c in enumerate(family['old_allocation_raw_coefficients']) if c])
        recovered.extend(quadratic.algebra.moved_terms(terms, action['signature_image']) for action in actions)
    assert len(recovered) == 288
    for cut, terms in zip(symmetric, recovered):
        assert cut['signed_coefficients'] == terms and cut['predicate_sha256'] == quadratic.object_hash(terms)
    gap_result = LOGS/'f0-terminal-bounded-query-run01.json'
    for ai, terms in enumerate(recovered[276:]):
        symmetric.append(registry.signed_cut(terms, {
            'kind': 'separate bounded shared support-gap64 certificate',
            'gap_result_sha256': digest(gap_result), 'core_action_index': ai}))
    assert len(symmetric) == len({cut['predicate_sha256'] for cut in symmetric}) == 288
    assert len(portfolio.families) == 24 and portfolio.snapshot()['transported_predicates'] == 288
    retained = bound_record(result, 'explanation-registry')
    assert len(retained) == 5340
    state = State(cnf, rows, symmetric, actions, population)
    state.append_records(retained)
    assert (state.cnf.nv, len(state.cnf.clauses)) == (28308, 62334)
    assert state.clause_state_sha256 == result['final_snapshot']['clause_state_sha256']
    with tempfile.TemporaryDirectory(prefix='conway-f0-allocated-parent-') as directory:
        path = Path(directory)/'parent.cnf'; state.cnf.to_file(path)
        assert digest(path) == FINAL_CNF_SHA
    prefix = state.snapshot()
    last = result['iterations'][-1]
    point = bound_record(last, 'candidate')
    selected = point['selected_signature_ids']
    assert individual.old.inspect(selected, domain, records, old_cuts, old_clauses) == point['original_incidence_and_twelve_direct_cuts']
    assert all(not is_false(record['clause'], set(selected)) for record in retained)
    evaluation = state.evaluate(selected)
    assert evaluation['violations'] and evaluation['all_registered_integer_values']['symmetric'][276] == 64
    assert all(v['family'] == 'symmetric' and 276 <= v['registry_index'] < 288 for v in evaluation['violations'])
    source = {'kind': 'seed explanations of separately proved bounded support gap64',
              'candidate_sha256': last['candidate_sha256'], 'gap_result_sha256': digest(gap_result)}
    explanations, explanation_summary = state.proposals(selected, evaluation['violations'], source)
    assert explanation_summary['new_clauses_false_on_source'] > 0
    state.append_records(explanations)
    assert any(is_false(record['clause'], set(selected)) for record in explanations)
    payload = {'status': 'complete exact2928-cut seed plus24 potential families; no new query',
        'parent_result_sha256': RESULT_SHA, 'parent_cold_replay_sha256': COLD_SHA,
        'parent_terminal_manifest_sha256': MANIFEST_SHA, 'parent_final_cnf_sha256': FINAL_CNF_SHA,
        'bounded_gap64_manifest_sha256': GAP_MANIFEST_SHA, 'control_input_hashes': CONTROL_INPUTS,
        'base_formula': base_formula, 'individual_cuts': rows, 'symmetric_cuts': symmetric,
        'population_premise': population, 'verified_core_actions': actions,
        'direct_individual_potentials_checked': len(rows), 'signed_allocations_reconstructed': 288,
        'quadratic_preparation_sha256': quadratic.PREPARATION_SHA,
        'quadratic_initial_snapshot': portfolio.snapshot(),
        'retained_explanation_registry': result['explanation-registry'],
        'retained_explanation_registry_sha256': result['explanation-registry_sha256'],
        'retained_explanation_count': len(retained), 'parent_prefix_snapshot': prefix,
        'new_seed_explanation_source': source, 'new_seed_explanation_records': explanations,
        'new_seed_explanation_summary': explanation_summary,
        'terminal_candidate': last['candidate'], 'terminal_candidate_sha256': last['candidate_sha256'],
        'terminal_candidate_control': evaluation,
        'raw_registry_sha256': hashlib.sha256(canonical([rows, symmetric])).hexdigest(),
        'initial_snapshot': state.snapshot(), 'all2916_proved_parent_inequalities_retained': True,
        'all5340_parent_explanation_clauses_retained': True, 'all480_selectors_free': True,
        'terminal_candidate_fixed_or_preferred': False, 'second_component_or_alignment_fixed': False,
        'parent_UNKNOWN_unchanged': True, 'ancestor_continuation_formulas_rebuilt': False,
        'optimizer_or_solver_called': False}
    return payload, state, context, portfolio


def initial(complete_replay=False):
    assert type(complete_replay) is bool
    check_sources()
    payload, state, context, portfolio = calculate()
    assert canonical(payload) == canonical(load_json(REGISTRY))
    summary = {'status': 'exact2928-cut seed, parent prefix, gap64 explanations and24 potential families PASS',
        'exact_registry_sha256': REGISTRY_SHA, 'parent_result_sha256': RESULT_SHA,
        'parent_terminal_manifest_sha256': MANIFEST_SHA, 'bounded_gap64_manifest_sha256': GAP_MANIFEST_SHA,
        'parent_final_cnf_sha256': FINAL_CNF_SHA, 'individual_potentials_checked': 2640,
        'signed_inequalities_checked': 288, 'retained_parent_explanation_clauses': 5340,
        'new_explanation_summary': payload['new_seed_explanation_summary'],
        'initial_snapshot': state.snapshot(), 'quadratic_initial_snapshot': portfolio.snapshot(),
        'registry_start_rebased_to_complete_canonical_contents': True,
        'all480_selectors_free': True, 'no_fixed_selector_or_hint': True,
        'no_ancestor_continuation_CNF_rebuilt': True, 'optimizer_or_solver_called': False}
    return state, context, portfolio, summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['export', 'replay'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    if args.mode == 'export':
        assert not REGISTRY.exists()
        payload, state, _, portfolio = calculate()
        blob = gzip.compress(canonical(payload)+b'\n', mtime=0)
        if REGISTRY_SHA is not None:
            assert hashlib.sha256(blob).hexdigest() == REGISTRY_SHA
        REGISTRY.write_bytes(blob)
        report = {'status': 'exact2928-cut seed and potential portfolio exported; no query',
            'registry_sha256': digest(REGISTRY), 'individual_cuts': 2640, 'symmetric_cuts': 288,
            'snapshot': state.snapshot(), 'quadratic_snapshot': portfolio.snapshot()}
    else:
        _, _, _, report = initial(True)
    save(args.output, report); print(json.dumps(report, indent=2), flush=True)
