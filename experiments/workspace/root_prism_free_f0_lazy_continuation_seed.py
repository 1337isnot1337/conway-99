"""Exact terminal seed for the next free480 lazy continuation.

Replay the frozen first lazy run and preserve every necessary clause
and every proved inequality. Only the registry's starting hash is reset
to its complete canonical contents. No selector or second component is
fixed, including the saved final candidate used as a prefix control.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path

from pysat.formula import CNF

import root_prism_free_f0_lazy_clauses as original
import root_prism_free_f0_lazy_row_loop as parent
import root_prism_free_f0_lazy_transcript_bundle as bundle


ROOT, LOGS, BASE = original.ROOT, original.LOGS, original.BASE
individual, shared, registry = original.individual, original.shared, original.registry
digest, canonical, portable, save, load_json = original.digest, original.canonical, original.portable, original.save, original.load_json
State, is_false = original.State, original.is_false
MAXIMUM_CLAUSES, MAXIMUM_VARIABLES = original.MAXIMUM_CLAUSES, original.MAXIMUM_VARIABLES
SOURCES = {
    'root_prism_free_f0_lazy_clauses.py': 'cef5448b012be57277b87297d2e3ec2c017ccea1336080f4c40c2594f2ab7640',
    'root_prism_free_f0_lazy_row_loop.py': '7b8301c96329ecbc6610c3dd74809793029e2e13d57027c7b7f9756bfd859e07',
    'root_prism_free_f0_lazy_transcript_bundle.py': 'f30a1370460134017072f9a52c3e470871546bd94bb0108a709d387fb7aa05b0'}
PREPARATION = LOGS/'f0-lazy-row-loop-preparation.json.gz'
PREPARATION_SHA = '5e32d4366e1e5224c6abd18298d0db3040f5e41a0c0bc984c962d9020e951c01'
RESULT = LOGS/'f0-lazy-row-loop-run01/result.json'
RESULT_SHA = '93037f2b7c0055aabc115ae3a269547f0ad17c7da904b78ab4b76ce9e6b42468'
COLD = LOGS/'f0-lazy-row-loop-run01-cold-replay.json'
COLD_SHA = '7cdfde151e90d1549d3247e5b11412b022c886f720bda4799291ddbdacda5b2a'
MANIFEST = LOGS/'f0-lazy-row-loop-run01-terminal-manifest.json'
MANIFEST_SHA = '28e1e1f276dba8d99bf784b76a14eac5e6e8b9f840cd806cd9ccc97d68db8528'
FINAL_CNF_SHA = '570f9e85c7eaa724d71a77b9654f7aad2c9052825fde876aaf20a87f484e24bc'
REGISTRY = LOGS/'f0-lazy-terminal-registry.json.gz'
REGISTRY_SHA = 'effd34510808030ee05914acbb7aa5beda412a6ef1a1cf2deb8fd3605e1596ea'


def check_sources(require_registry=True):
    for name, expected in SOURCES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    original.check_sources()
    restored = bundle.verify(True)
    assert restored['record_count'] == 79
    for path, expected in ((PREPARATION, PREPARATION_SHA), (RESULT, RESULT_SHA),
                           (COLD, COLD_SHA), (MANIFEST, MANIFEST_SHA)):
        assert digest(path) == expected
    for entry in load_json(MANIFEST)['files']:
        assert digest(ROOT/entry['path']) == entry['sha256']
    if require_registry:
        assert REGISTRY_SHA is not None and digest(REGISTRY) == REGISTRY_SHA


def terminal_payload(result, rows, symmetric, inherited):
    last = result['iterations'][-1]
    assert result['status'] == 'STOP: row-pass or overall budget; unresolved'
    assert result['row_passes'] == 20 and last['iteration'] == 24
    assert last['status'] == 'STOP: budget before row pass' and 'individual_rows' not in last
    assert result['final_cnf_sha256'] == FINAL_CNF_SHA
    point_path = ROOT/last['candidate']
    assert digest(point_path) == last['candidate_sha256']
    point = load_json(point_path)
    assert point['registry_evaluation']['all_registered_inequalities_hold']
    assert len(rows) == 1008 and len(symmetric) == 108
    return {'status': 'complete exact1116-cut terminal registry; no new query',
        'parent_loop_source_sha256': SOURCES['root_prism_free_f0_lazy_row_loop.py'],
        'parent_preparation_sha256': PREPARATION_SHA, 'parent_result_sha256': RESULT_SHA,
        'parent_cold_replay_sha256': COLD_SHA, 'parent_terminal_manifest_sha256': MANIFEST_SHA,
        'parent_final_cnf_sha256': FINAL_CNF_SHA,
        'parent_final_snapshot': result['final_snapshot'],
        'individual_cuts': rows, 'symmetric_cuts': symmetric,
        'population_premise': inherited['population_premise'],
        'verified_core_actions': inherited['verified_core_actions'],
        'retained_explanation_registry': result['explanation-registry'],
        'retained_explanation_registry_sha256': result['explanation-registry_sha256'],
        'terminal_candidate': last['candidate'], 'terminal_candidate_sha256': last['candidate_sha256'],
        'terminal_candidate_selected_signature_ids': point['selected_signature_ids'],
        'raw_registry_sha256': hashlib.sha256(canonical([rows, symmetric])).hexdigest(),
        'all1116_proved_inequalities_retained': True, 'all1980_explanation_clauses_retained': True,
        'all480_selectors_free': True, 'terminal_candidate_fixed_or_preferred': False,
        'second_component_or_alignment_fixed': False}


def calculate():
    check_sources(False)
    cnf, all_cuts, proofs, cold = parent.reconstruct(PREPARATION, RESULT)
    assert cold == load_json(COLD)
    result = load_json(RESULT)
    rows = load_json(ROOT/result['individual-registry'])
    symmetric = load_json(ROOT/result['symmetric-registry'])
    assert all_cuts == rows+symmetric and len(proofs) == 1980
    assert proofs == load_json(ROOT/result['explanation-registry'])
    inherited = load_json(original.REGISTRY)
    payload = terminal_payload(result, rows, symmetric, inherited)
    assert (cnf.nv, len(cnf.clauses)) == (28308, 58974)
    return payload, cnf, proofs, cold


def initial(complete_replay=False):
    # The parent replay is exact in either mode; this argument preserves
    # the frozen runner's interface, not a weaker verification path.
    assert type(complete_replay) is bool
    check_sources()
    payload, cnf, proofs, cold = calculate()
    assert canonical(payload) == canonical(load_json(REGISTRY))
    state = State(CNF(from_clauses=cnf.clauses[:56994]), payload['individual_cuts'], payload['symmetric_cuts'],
                  payload['verified_core_actions'], payload['population_premise'])
    state.append_records(proofs)
    assert state.cnf.nv == cnf.nv and state.cnf.clauses == cnf.clauses
    assert state.clause_state_sha256 == payload['parent_final_snapshot']['clause_state_sha256']
    assert state.registry_state_sha256 == payload['raw_registry_sha256']
    domain, records = BASE.load(0)
    old_cuts, old_clauses, _ = individual.old.load_cuts()
    triples, targets, neighbors, _, actions, _ = individual.box.load()
    assert triples == domain['signature_domain'] and actions == state.actions
    context = (domain, records, old_cuts, old_clauses, triples, targets, neighbors, actions)
    point = load_json(ROOT/payload['terminal_candidate'])
    selected = point['selected_signature_ids']
    fresh = parent.inspect_candidate(selected, state, context)
    # The exact formula and inequality values are unchanged. The new
    # starting registry hash is canonical rather than the old append chain.
    point['actual_prefix_snapshot'] = state.snapshot()
    point['registry_evaluation']['registry_snapshot'] = state.snapshot()
    assert point == fresh and fresh['registry_evaluation']['all_registered_inequalities_hold']
    summary = {'complete_parent_mathematical_and_prefix_replay': cold,
        'parent_terminal_bindings': {'preparation_sha256': PREPARATION_SHA, 'result_sha256': RESULT_SHA,
            'cold_replay_sha256': COLD_SHA, 'terminal_manifest_sha256': MANIFEST_SHA},
        'exact_registry_certificate_sha256': REGISTRY_SHA,
        'parent_terminal_status_preserved': 'STOP: row-pass or overall budget; unresolved',
        'same58974_parent_clauses_and_all1116_cuts_retained': True,
        'parent_clause_state_sha256': state.clause_state_sha256,
        'registry_start_rebased_to_complete_canonical_contents': True,
        'terminal_candidate_control': {'path': payload['terminal_candidate'],
            'sha256': payload['terminal_candidate_sha256'],
            'all1116_integer_values_sha256': fresh['registry_evaluation']['value_sha256'],
            'all1980_primary_explanations_satisfied': True,
            'exact_Gram_and_direct_cuts_pass': True, 'not_fixed_or_preferred_in_solver': True},
        'initial_snapshot': state.snapshot(), 'new_auxiliary_variables': 0,
        'no_ancestor_full_auxiliary_CNF_rebuilt': True}
    return state, context, summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['export', 'replay'])
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    if args.mode == 'export':
        assert not REGISTRY.exists()
        payload, _, _, _ = calculate()
        blob = gzip.compress(canonical(payload)+b'\n', mtime=0)
        if REGISTRY_SHA is not None:
            assert hashlib.sha256(blob).hexdigest() == REGISTRY_SHA
        REGISTRY.write_bytes(blob)
        report = {'status': 'exact terminal registry export PASS; no query',
                  'registry_sha256': digest(REGISTRY), 'parent_result_sha256': RESULT_SHA,
                  'individual_cuts': 1008, 'symmetric_cuts': 108, 'explanation_clauses': 1980}
    else:
        state, _, summary = initial(True)
        report = {'status': 'exact terminal seed and untested-candidate control replay PASS',
                  'source_sha256': digest(Path(__file__)), 'registry_sha256': REGISTRY_SHA,
                  'snapshot': state.snapshot(), 'summary': summary,
                  'optimizer_or_solver_called': False}
    save(args.output, report); print(json.dumps(report, indent=2), flush=True)
