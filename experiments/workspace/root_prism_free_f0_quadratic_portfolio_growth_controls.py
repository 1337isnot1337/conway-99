"""Exact nonduplicate future-family registration and replay controls.

The additional potential is an artificial integer perturbation of a
known family. This is algebraic API coverage, not a new optimizer result.
"""

import argparse
import json
from pathlib import Path

import root_prism_free_f0_quadratic_portfolio as q


SUBJECT_SHA = '33e6abf18bd9f87a3814b7486294ac9e5ef1f131a332b087fe3e7207fbf46319'


def calculate():
    assert q.digest(Path(q.__file__)) == SUBJECT_SHA
    prepared = q.read(q.PREPARATION)
    portfolio = q.Portfolio(prepared)
    family = portfolio.families[0]
    selected = family['selected_generation_signature_ids']
    potential = [[0]*18 for _ in range(480)]
    for a, vector in family['nonzero_target_potentials']:
        potential[a] = [100*x for x in vector]
    potential[selected[0]][0] += 1
    demand, positive = q.algebra.quantities(portfolio.triples, portfolio.targets, portfolio.edges, potential)
    coefficients, _, gap = q.algebra.best_allocation(demand, positive, selected)
    assert gap > 0
    terms, divisor = q.algebra.normalized([[a, c] for a, c in enumerate(coefficients) if c])
    lifted = {'selected_signature_ids_for_allocation_only': selected,
        'nonzero_target_potentials': [[a, v] for a, v in enumerate(potential) if any(v)],
        'raw_gap': gap, 'coefficient_gcd': divisor, 'normalized_gap': gap//divisor,
        'transported_cuts': [{'core_action_index': i,
            'signed_coefficients': q.algebra.moved_terms(terms, action['signature_image'])}
            for i, action in enumerate(portfolio.actions)]}
    before = portfolio.snapshot()
    origin = {'kind': 'exact artificial integer-potential growth control; no optimizer'}
    change = portfolio.add_shared_lift(lifted, origin)
    assert change['new_family'] and change['family_index'] == 24
    assert portfolio.snapshot()['base_potential_families'] == 25
    values = portfolio.evaluate(selected)
    assert values['all_negative_Q_values'][24*12] == gap
    cuts = portfolio.allocation_cuts(selected, values, 0, q.object_hash(selected))
    assert all(sum(c for a, c in cut['signed_coefficients'] if a in set(selected)) > 0 for cut in cuts)
    duplicate = portfolio.add_shared_lift(lifted, {'kind': 'same control repeated'})
    assert not duplicate['new_family'] and duplicate['family_index'] == 24
    clone = q.Portfolio(prepared)
    assert clone.snapshot() == before and clone.add_shared_lift(lifted, origin) == change
    assert clone.snapshot() == portfolio.snapshot() and clone.evaluate(selected) == values
    assert clone.allocation_cuts(selected, values, 0, q.object_hash(selected)) == cuts
    return {'status': 'new potential family, duplicate recognition and complete exact replay controls PASS',
        'source_sha256': q.digest(Path(__file__)), 'subject_sha256': SUBJECT_SHA,
        'preparation_sha256': q.PREPARATION_SHA, 'before': before, 'new_family_registration': change,
        'duplicate_registration': duplicate, 'after': portfolio.snapshot(),
        'artificial_generation_gap': gap, 'negative_Q_cuts_replayed': len(cuts),
        'optimizer_or_solver_called': False, 'new_numerical_result_claimed': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = calculate(); args.output.write_bytes(q.canonical(report)+b'\n')
    print(json.dumps(report, indent=2), flush=True)
