"""Optimizer-free control of the new quadratic cut/explanation transition.

Use the unchanged original base with an intentionally empty optional cut
registry. This is a weakened artificial control, not the production seed.
A saved Gram incidence triggers an exact quadratic allocation and the
ordinary explanation path. Replay checks the same append-only formula.
"""

import argparse
import json
from pathlib import Path
import tempfile

from pysat.formula import CNF

import root_prism_free_f0_allocated_lazy_continuation as loop


LOOP_SHA = '46b30a4e7c64db612cff606bd56aa05da44356547f617e977a8fa17ac0da4c8d'
PREPARATION = loop.LOGS/'f0-allocated-lazy-continuation-preparation.json.gz'
PREPARATION_SHA = '7eecf38db3acba31bf2e24d08937235977cce1c6c93d9426795a3f0bb713fc23'


def calculate():
    assert loop.digest(Path(loop.__file__)) == LOOP_SHA and loop.digest(PREPARATION) == PREPARATION_SHA
    prepared = loop.checked_preparation(PREPARATION, True)
    complete_state, context, portfolio = loop.input_state(prepared)
    original_hash = loop.digest(Path(prepared['cnf']))
    base = CNF(from_clauses=complete_state.cnf.clauses[:56994])
    assert base.nv == 28308 and len(base.clauses) == 56994
    def empty_optional_state():
        return loop.lazy.State(CNF(from_clauses=base.clauses), [], [], complete_state.actions, complete_state.population)
    state = empty_optional_state()
    quadratic_preparation = loop.lazy.quadratic.read(loop.lazy.quadratic.PREPARATION)
    selected = quadratic_preparation['saved_candidates'][32]['selected_signature_ids']
    point = loop.inspect_candidate(selected, state, context)
    assert point['registry_evaluation']['all_registered_inequalities_hold']
    candidate_sha = loop.lazy.quadratic.object_hash(point)
    transition = loop.apply_quadratic(state, portfolio, selected, 0, candidate_sha, context)
    assert transition['evaluation']['violations'] and transition['new_signed_cuts'] == 1
    source = {'kind': 'artificial weakened-registry exact allocation transition control',
              'candidate_sha256': candidate_sha,
              'quadratic_result_sha256': loop.lazy.quadratic.object_hash(transition)}
    with tempfile.TemporaryDirectory(prefix='allocation-transition-control-', dir=loop.LOGS) as directory:
        path = Path(directory)/'explanations.json.gz'
        step = loop.explain_candidate(state, selected, source, path)
        assert step['explanation_batch_added'] and not step['explanation_resource_error']
        assert step['explanation_summary']['new_clauses_false_on_source'] > 0
        assert any(loop.lazy.is_false(record['clause'], set(selected)) for record in state.records)
        clone = empty_optional_state()
        # Portfolio contents are unchanged by a candidate allocation, so the
        # same immutable portfolio is sufficient for this independent replay.
        replayed = loop.apply_quadratic(clone, portfolio, selected, 0, candidate_sha, context)
        assert replayed == transition
        loop.replay_batch(step, clone, selected, source)
        assert clone.cnf.clauses == state.cnf.clauses and clone.snapshot() == state.snapshot()
        assert clone.records == state.records and clone.symmetric == state.symmetric
        explanation_sha = step['explanation_batch_sha256']
    assert loop.digest(Path(prepared['cnf'])) == original_hash
    return {'status': 'exact quadratic-to-signed-cut-to-explanation transition and replay PASS',
        'source_sha256': loop.digest(Path(__file__)), 'loop_source_sha256': LOOP_SHA,
        'production_preparation_sha256': PREPARATION_SHA, 'production_CNF_unchanged_sha256': original_hash,
        'control_base_clauses': 56994, 'control_initial_optional_registry_count': 0,
        'saved_candidate_index': 32, 'candidate_primary_checks_passed': True,
        'quadratic_violations': transition['evaluation']['violations'],
        'new_signed_cuts': transition['new_signed_cuts'],
        'transition_sha256': loop.lazy.quadratic.object_hash(transition),
        'explanation_batch_sha256': explanation_sha, 'explanation_summary': step['explanation_summary'],
        'control_final_snapshot': state.snapshot(),
        'actual_production_registry_not_weakened': True, 'optimizer_or_solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = calculate(); loop.save(args.output, report)
    print(json.dumps(report, indent=2), flush=True)
