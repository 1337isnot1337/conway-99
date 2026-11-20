"""Append-only exact mixed-row potential portfolio for Boolean incidences.

All potential families and their12 core transports are checked before a
new row LP, after the existing linear registry passes.  A negativeQ
produces a necessary signed linear cut by optimal endpoint allocation.
New exact shared certificates may append a complete potential orbit.
No candidate, second incidence or graph automorphism is assumed.
"""

import argparse
import hashlib
import json
from itertools import combinations
from pathlib import Path
import time

import root_prism_free_f0_quadratic_allocation as algebra


ROOT, LOGS = algebra.ROOT, algebra.LOGS
canonical, digest, object_hash, read = algebra.canonical, algebra.digest, algebra.object_hash, algebra.read
SOURCE_SHA = 'd5b5e8fd8e24a6ece19c4fcd4982239d83e3d004376092976cc86c2de0b3571c'
PREPARATION = LOGS/'f0-quadratic-allocation-preparation.json.gz'
PREPARATION_SHA = '7ab2ec935cdbbb7035a0fd95d5a7ca514aed508b7d5efbe953c5265176733589'
SCAN = LOGS/'f0-quadratic-allocation-scan.json.gz'
SCAN_SHA = 'ba2e83a0ae513bce846f9e7765b527584b342bdd5f8d382e2625da38fad99399'


def check_sources():
    assert digest(Path(algebra.__file__)) == SOURCE_SHA
    assert digest(PREPARATION) == PREPARATION_SHA and digest(SCAN) == SCAN_SHA


class Portfolio:
    def __init__(self, prepared):
        check_sources()
        assert prepared['source_sha256'] == SOURCE_SHA
        raw = algebra.checked(LOGS/'f0-exterior-row-domains02.json.gz',
                              algebra.INPUTS['f0-exterior-row-domains02.json.gz'])
        triples, targets, gram, edges, actions = algebra.domain(raw, prepared['verified_core_actions'])
        assert triples == prepared['signature_domain'] and targets == prepared['row_targets']
        self.triples, self.targets, self.gram = triples, targets, gram
        self.edges, self.actions, self.motifs = edges, actions, raw['motif_pairs']
        self.inverses = []
        for action in actions:
            inverse = [0]*480
            for a, b in enumerate(action['signature_image']):
                inverse[b] = a
            self.inverses.append(inverse)
        self.families, self.lookups, self.keys = [], [], {}
        for family in prepared['potential_families']:
            self.validate(family)
            self._append(family)
        self.state_sha256 = object_hash(self.families)

    def validate(self, family):
        algebra.inspect_selection(family['selected_generation_signature_ids'], self.triples, self.gram, self.motifs)
        sparse = family['nonzero_target_potentials']
        assert sparse == sorted(sparse) and len({a for a, _ in sparse}) == len(sparse)
        potentials = [[0]*18 for _ in range(480)]
        for a, vector in sparse:
            assert a in family['selected_generation_signature_ids'] and len(vector) == 18
            assert any(vector) and all(type(x) is int for x in vector)
            potentials[a] = list(vector)
        demand, positive = algebra.quantities(self.triples, self.targets, self.edges, potentials)
        assert demand == family['target_demands'] and positive == family['positive_edges']
        base_hash = object_hash([[[a, d] for a, d in enumerate(demand) if d], positive])
        assert base_hash == family['base_quadratic_predicate_sha256']
        coefficients, _, gap = algebra.best_allocation(demand, positive, family['selected_generation_signature_ids'])
        terms, divisor = algebra.normalized([[a, c] for a, c in enumerate(coefficients) if c])
        assert coefficients == family['old_allocation_raw_coefficients']
        assert gap == family['generation_raw_gap'] > 0 and divisor == family['old_allocation_coefficient_gcd']
        assert family['generation_normalized_gap'] == gap//divisor
        for index, action in enumerate(self.actions):
            image = action['signature_image']
            moved_d = sorted([image[a], d] for a, d in enumerate(demand) if d)
            moved_p = sorted([min(image[a], image[b]), max(image[a], image[b]), w] for a, b, w in positive)
            assert family['transports'][index] == {'core_action_index': index,
                'quadratic_predicate_sha256': object_hash([moved_d, moved_p]),
                'existing_linear_predicate_sha256': object_hash(algebra.moved_terms(terms, image)),
                'known_generation_selection_raw_gap': gap}

    def _append(self, family):
        assert family['family_index'] == len(self.families)
        self.families.append(family)
        self.lookups.append({480*a+b: w for a, b, w in family['positive_edges']})
        for transport in family['transports']:
            key = transport['quadratic_predicate_sha256']
            assert key not in self.keys
            self.keys[key] = family['family_index']

    def snapshot(self):
        return {'base_potential_families': len(self.families),
                'transported_predicates': len(self.keys), 'state_sha256': self.state_sha256}

    def evaluate(self, selected):
        assert selected == sorted(set(selected)) and len(selected) == 60
        assert all(type(a) is int and 0 <= a < 480 for a in selected)
        moved = [sorted(inverse[a] for a in selected) for inverse in self.inverses]
        pairs = [[480*a+b for a, b in combinations(chosen, 2)] for chosen in moved]
        values, violations = [], []
        for family_index, family in enumerate(self.families):
            demand, weights = family['target_demands'], self.lookups[family_index]
            for action_index, chosen in enumerate(moved):
                gap = sum(demand[a] for a in chosen)-sum(weights.get(key, 0) for key in pairs[action_index])
                values.append(gap)
                if gap > 0:
                    violations.append({'family_index': family_index, 'core_action_index': action_index,
                        'quadratic_predicate_sha256': family['transports'][action_index]['quadratic_predicate_sha256'],
                        'exact_negative_Q': gap})
        return {'portfolio_snapshot': self.snapshot(), 'selected_signature_ids': selected,
                'all_negative_Q_values': values, 'violations': violations,
                'all_quadratic_inequalities_hold': not violations,
                'Boolean_selector_evaluation': True, 'optimizer_or_solver_called': False}

    def allocation_cuts(self, selected, evaluation, iteration, candidate_sha):
        assert evaluation['portfolio_snapshot'] == self.snapshot()
        assert evaluation['selected_signature_ids'] == selected
        assert evaluation == self.evaluate(selected)
        assert evaluation['violations']
        cuts = []
        for violation in evaluation['violations']:
            fi, ai = violation['family_index'], violation['core_action_index']
            family = self.families[fi]
            chosen = sorted(self.inverses[ai][a] for a in selected)
            coefficients, endpoints, gap = algebra.best_allocation(family['target_demands'], family['positive_edges'], chosen)
            assert gap == violation['exact_negative_Q'] > 0
            terms, divisor = algebra.normalized([[a, c] for a, c in enumerate(coefficients) if c])
            moved = algebra.moved_terms(terms, self.actions[ai]['signature_image'])
            assert sum(c for a, c in moved if a in set(selected)) == gap//divisor > 0
            cuts.append({'signed_coefficients': moved, 'predicate_sha256': object_hash(moved),
                'origin': {'kind': 'optimal endpoint allocation of retained quadratic mixed-row potential',
                    'iteration': iteration, 'candidate_sha256': candidate_sha,
                    'portfolio_state_sha256': self.state_sha256, 'family_index': fi,
                    'core_action_index': ai, 'quadratic_predicate_sha256': violation['quadratic_predicate_sha256'],
                    'endpoint_choices_sha256': object_hash(endpoints), 'raw_gap': gap,
                    'coefficient_gcd': divisor, 'normalized_gap': gap//divisor}})
        return cuts

    def add_shared_lift(self, lifted, origin):
        """Caller first replays the exact shared certificate and its lift."""
        record, _ = algebra.family_record(len(self.families), lifted, origin,
            self.triples, self.targets, self.gram, self.edges, self.actions, self.motifs)
        hashes = {t['quadratic_predicate_sha256'] for t in record['transports']}
        matched = hashes.intersection(self.keys)
        before = self.snapshot()
        if matched:
            existing = {self.keys[key] for key in matched}
            assert len(existing) == 1
            index = next(iter(existing))
            assert hashes == {t['quadratic_predicate_sha256'] for t in self.families[index]['transports']}
            return {'new_family': False, 'family_index': index, 'before': before, 'after': before,
                    'incoming_family_sha256': object_hash(record)}
        # A stabilizer may identify transports of a future potential. The
        # initial families have none; keep only unique predicate keys while
        # retaining all12 evaluations in the family record.
        index = len(self.families)
        self.families.append(record)
        self.lookups.append({480*a+b: w for a, b, w in record['positive_edges']})
        for key in hashes:
            assert key not in self.keys
            self.keys[key] = index
        self.state_sha256 = object_hash([self.state_sha256, record])
        return {'new_family': True, 'family_index': index, 'before': before, 'after': self.snapshot(),
                'incoming_family_sha256': object_hash(record)}


def controls():
    check_sources()
    prepared, scan = read(PREPARATION), read(SCAN)
    started = time.perf_counter()
    portfolio = Portfolio(prepared)
    construction_seconds = time.perf_counter()-started
    checked = 0
    eval_seconds = 0
    for record in scan['new_endpoint_allocation_cuts']:
        selected = record['selected_signature_ids']
        started = time.perf_counter(); evaluation = portfolio.evaluate(selected)
        eval_seconds += time.perf_counter()-started
        expected = scan['per_candidate'][record['candidate_index']]
        assert evaluation['all_negative_Q_values'] == expected['negative_Q_values']
        cuts = portfolio.allocation_cuts(selected, evaluation, 0, object_hash(selected))
        assert any(c['predicate_sha256'] == record['predicate_sha256'] for c in cuts)
        checked += 1
    # Registering an already present family is a no-op, with exact orbit
    # agreement. The gap64 lift exercises the same future-certificate API.
    lifted = algebra.checked(LOGS/'f0-terminal-bounded-query-run01-universal-cuts.json',
                             algebra.INPUTS['f0-terminal-bounded-query-run01-universal-cuts.json'])
    before = portfolio.snapshot()
    duplicate = portfolio.add_shared_lift(lifted, {'kind': 'duplicate control'})
    assert not duplicate['new_family'] and portfolio.snapshot() == before
    return {'status': 'exact runtime portfolio/candidate allocation/duplicate-orbit controls PASS',
        'source_sha256': digest(Path(__file__)), 'algebra_source_sha256': SOURCE_SHA,
        'preparation_sha256': PREPARATION_SHA, 'scan_sha256': SCAN_SHA,
        'snapshot': portfolio.snapshot(), 'saved_new_allocation_controls': checked,
        'duplicate_family_control': duplicate, 'portfolio_construction_seconds': construction_seconds,
        'measured_three_candidate_evaluation_seconds': eval_seconds,
        'arithmetic_timing_only_no_throughput_claim': True,
        'optimizer_or_solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = controls(); args.output.write_bytes(canonical(report)+b'\n')
    print(json.dumps(report, indent=2), flush=True)
