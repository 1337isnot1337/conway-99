"""Exact, primary-only clause explanations for the free480 cut registry.

Every clause is checked directly against a proved integer inequality.
The optional population60 premise follows from the original diagonal
Gram rows. Verified core relabelings transport implications, rather than
asserting automorphisms of an unknown completed graph.
"""

import argparse
from collections import Counter
import hashlib
from itertools import permutations, product
import json
from pathlib import Path

import integer_cut_clause_explanations as explain
import root_prism_free_f0_lazy_registry as registry


ROOT, LOGS, BASE = registry.ROOT, registry.LOGS, registry.BASE
individual, shared = registry.individual, registry.shared
digest, canonical, portable, load_json = registry.digest, registry.canonical, registry.portable, registry.load_json
save = individual.save
DEPENDENCIES = {
    'integer_cut_clause_explanations.py': 'f57d51b8be3fefd7a5d1035c52cc5758c719adb6a79d16a0909f1a54fdaa59f3',
    'root_prism_free_f0_lazy_registry.py': '9a9a2c40241dc3899b9692568a2ee4127d17d5a4b8c33972dfd9b59a57e43478'}
REGISTRY = LOGS/'f0-lazy-registry.json.gz'
REGISTRY_SHA = 'b8e008d3c89122ae8a7b96c1c7c68d506e3a6345cc2a0ccd334f4f79597d0dc1'
MAXIMUM_CLAUSES, MAXIMUM_VARIABLES = 2000000, 1000000


def check_sources():
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert digest(REGISTRY) == REGISTRY_SHA
    registry.checked_sources()


def canonical_clause(clause):
    assert all(type(lit) is int and lit for lit in clause)
    assert len({abs(lit) for lit in clause}) == len(clause)
    return sorted(clause, key=abs)


def is_false(clause, selected):
    return all((abs(lit)-1 in selected) == (lit < 0) for lit in clause)


def transport_terms(terms, image):
    result = [[image[a-1]+1, c] for a, c in terms]
    result.sort()
    assert len({a for a, _ in result}) == len(result)
    return result


def transport_clause(clause, image):
    return canonical_clause([(1 if lit > 0 else -1)*(image[abs(lit)-1]+1) for lit in clause])


def explain_both(terms, selected, universe, population):
    chosen = set(selected)
    assignment = {a: a-1 in chosen for a in universe}
    assert sum(assignment.values()) == population
    raw = [explain.independent_explanation(terms, 0, assignment),
           explain.cardinality_explanation(terms, 0, assignment, universe, population)]
    return [('independent', canonical_clause(raw[0]['clause'])),
            ('population', canonical_clause(raw[1]['clause']))]


def proof_for_clause(terms, clause, kind, universe, population):
    assert kind in ('independent', 'population')
    bound = (explain.verify_clause(terms, 0, clause) if kind == 'independent'
             else explain.verify_clause(terms, 0, clause, universe, population))
    assert not bound['cardinality_infeasible'] and bound['minimum'] > 0
    return {'rhs': 0, 'exact_falsifying_assignment_bound': bound,
            'strict_integer_margin': bound['minimum'],
            'population_premise': population if kind == 'population' else None}


class State:
    """Append-only necessary clauses, with independently replayable proofs."""

    def __init__(self, cnf, rows, symmetric, actions, population):
        self.cnf = cnf
        self.rows, self.symmetric = list(rows), list(symmetric)
        self.actions, self.population = actions, population
        self.universe = population['universe']
        assert self.universe == list(range(1, 481)) and population['population'] == 60
        assert len(actions) == 12 and actions[0]['signature_image'] == list(range(480))
        self.base_count, self.base_nv = len(cnf.clauses), cnf.nv
        assert (self.base_count, self.base_nv) == (56994, 28308)
        self.base_body_sha256 = hashlib.sha256(canonical(cnf.clauses)).hexdigest()
        self.registry_state_sha256 = hashlib.sha256(canonical([self.rows, self.symmetric])).hexdigest()
        self.clause_state_sha256 = self.base_body_sha256
        self.records = []
        self.clause_keys = {tuple(canonical_clause(clause)) for clause in cnf.clauses
                            if all(abs(lit) <= 480 for lit in clause)}
        self.row_keys = {cut['normalized_predicate_sha256']: i for i, cut in enumerate(self.rows)}
        self.signed_keys = {cut['predicate_sha256']: i for i, cut in enumerate(self.symmetric)}
        assert len(self.row_keys) == len(self.rows) and len(self.signed_keys) == len(self.symmetric)
        self.terms = {'individual': [registry.cut_terms('individual', cut) for cut in self.rows],
                      'symmetric': [registry.cut_terms('symmetric', cut) for cut in self.symmetric]}

    def snapshot(self):
        return {'individual_cuts': len(self.rows), 'symmetric_cuts': len(self.symmetric),
                'registry_state_sha256': self.registry_state_sha256,
                'clauses': len(self.cnf.clauses), 'variables': self.cnf.nv,
                'explanation_clauses': len(self.records),
                'clause_state_sha256': self.clause_state_sha256}

    def cut(self, family, index):
        assert family in ('individual', 'symmetric') and type(index) is int
        entries = self.rows if family == 'individual' else self.symmetric
        assert 0 <= index < len(entries)
        return entries[index]

    def key(self, family, index):
        cut = self.cut(family, index)
        return cut['normalized_predicate_sha256'] if family == 'individual' else cut['predicate_sha256']

    def evaluate(self, selected):
        selected = set(selected)
        values, violations = {}, []
        for family in ('individual', 'symmetric'):
            numbers = [sum(c for a, c in terms if a-1 in selected) for terms in self.terms[family]]
            values[family] = numbers
            for index, value in enumerate(numbers):
                if value > 0:
                    violations.append({'family': family, 'registry_index': index,
                                       'predicate_sha256': self.key(family, index), 'signed_value': value})
        return {'all_registered_integer_values': values,
                'value_sha256': hashlib.sha256(canonical(values)).hexdigest(),
                'violations': violations, 'all_registered_inequalities_hold': not violations,
                'registry_snapshot': self.snapshot()}

    def add_cut(self, family, cut, context):
        _, _, _, _, triples, targets, neighbors, _ = context
        if family == 'individual':
            individual.validate_cut(cut, triples, targets, neighbors)
            key, keys, entries = cut['normalized_predicate_sha256'], self.row_keys, self.rows
        else:
            assert family == 'symmetric'
            assert cut == registry.signed_cut(cut['signed_coefficients'], cut['origin'])
            key, keys, entries = cut['predicate_sha256'], self.signed_keys, self.symmetric
        if key in keys:
            return {'origin': cut['origin'], 'registry_index': keys[key], 'new_cut': False}
        index = len(entries)
        entries.append(cut); keys[key] = index
        self.terms[family].append(registry.cut_terms(family, cut))
        self.registry_state_sha256 = hashlib.sha256(canonical(
            [self.registry_state_sha256, family, index, cut])).hexdigest()
        return {'origin': cut['origin'], 'registry_index': index, 'new_cut': True}

    def verify_record(self, record):
        family, index = record['family'], record['registry_index']
        assert record['predicate_sha256'] == self.key(family, index)
        action = record['core_action_index']
        assert type(action) is int and 0 <= action < len(self.actions)
        image = self.actions[action]['signature_image']
        terms = transport_terms(self.terms[family][index], image)
        assert record['transported_coefficients_sha256'] == hashlib.sha256(canonical(terms)).hexdigest()
        clause = record['clause']
        assert clause == canonical_clause(clause) and all(1 <= abs(lit) <= 480 for lit in clause)
        assert record['proof'] == proof_for_clause(terms, clause, record['kind'], self.universe,
                                                   self.population['population'])
        return clause

    def proposals(self, selected, violations, source):
        selected = set(selected)
        fresh, local_keys = [], set(self.clause_keys)
        attempted = duplicates = 0
        for violation in violations:
            family, index = violation['family'], violation['registry_index']
            terms = self.terms[family][index]
            assert sum(c for a, c in terms if a-1 in selected) == violation['signed_value'] > 0
            assert violation['predicate_sha256'] == self.key(family, index)
            explanations = explain_both(terms, selected, self.universe, self.population['population'])
            for kind, base_clause in explanations:
                assert is_false(base_clause, selected)
                for action, mapping in enumerate(self.actions):
                    image = mapping['signature_image']
                    clause = transport_clause(base_clause, image)
                    attempted += 1
                    key = tuple(clause)
                    if key in local_keys:
                        duplicates += 1
                        continue
                    transported = transport_terms(terms, image)
                    record = {'family': family, 'registry_index': index,
                        'predicate_sha256': self.key(family, index), 'core_action_index': action,
                        'kind': kind, 'clause': clause,
                        'transported_coefficients_sha256': hashlib.sha256(canonical(transported)).hexdigest(),
                        'proof': proof_for_clause(transported, clause, kind, self.universe, self.population['population']),
                        'source': source}
                    self.verify_record(record)
                    fresh.append(record); local_keys.add(key)
        assert attempted == len(violations)*2*len(self.actions)
        return fresh, {'violated_inequalities': len(violations), 'attempted_explanations': attempted,
                       'duplicate_literal_lists': duplicates, 'new_clauses': len(fresh),
                       'new_clauses_false_on_source': sum(is_false(record['clause'], selected) for record in fresh),
                       'new_literal_occurrences': sum(len(record['clause']) for record in fresh),
                       'generated_both_families': True, 'all12_core_transports': True}

    def append_records(self, records, solver=None):
        if len(self.cnf.clauses)+len(records) > MAXIMUM_CLAUSES or self.cnf.nv > MAXIMUM_VARIABLES:
            raise RuntimeError('necessary explanation batch exceeds formula resource limit; no batch clauses added')
        clauses = []
        for record in records:
            clause = self.verify_record(record)
            assert tuple(clause) not in self.clause_keys
            self.clause_keys.add(tuple(clause))
            self.records.append(record); clauses.append(clause)
            self.clause_state_sha256 = hashlib.sha256(canonical([self.clause_state_sha256, clause])).hexdigest()
        self.cnf.extend(clauses)
        assert self.cnf.nv == self.base_nv and len(self.cnf.clauses) == self.base_count+len(self.records)
        if solver is not None and clauses:
            solver.append_formula(clauses)


def initial(complete_replay=False):
    check_sources()
    proved, cnf, context = registry.calculate(complete_replay)
    assert canonical(proved) == canonical(load_json(REGISTRY))
    state = State(cnf, proved['individual_cuts'], proved['symmetric_cuts'],
                  proved['verified_core_actions'], proved['population_premise'])
    seed_reports = []
    for index, seed in enumerate(proved['seed_candidates']):
        selected = seed['selected_signature_ids']
        outcome = state.evaluate(selected)
        assert outcome['violations']
        source = {'kind': 'bound prior proved-rejected candidate', 'registry_certificate_sha256': REGISTRY_SHA,
                  'seed_index': index, 'selected_signature_ids_sha256': hashlib.sha256(canonical(selected)).hexdigest()}
        records, summary = state.proposals(selected, outcome['violations'], source)
        state.append_records(records)
        seed_reports.append({'seed_index': index, 'all_registry_values_sha256': outcome['value_sha256'],
                             **summary, 'after': state.snapshot()})
    for seed in proved['seed_candidates']:
        selected = set(seed['selected_signature_ids'])
        assert any(is_false(record['clause'], selected) for record in state.records)
    summary = {'registry_certificate_sha256': REGISTRY_SHA,
        'initial_individual_inequalities': len(state.rows), 'initial_signed_inequalities': len(state.symmetric),
        'base_body_sha256': state.base_body_sha256, 'population_premise': proved['population_premise'],
        'seed_reports': seed_reports, 'all30_seed_candidates_rejected': True,
        'initial_snapshot': state.snapshot(), 'new_auxiliary_variables': 0,
        'no_ancestor_auxiliary_CNF_rebuilt': True}
    return state, context, summary


def controls():
    # This tests the actual explanation/transport adapter without a SAT solver.
    universe = [1, 2, 3]
    points = list(product((False, True), repeat=3))
    maps = list(permutations(range(3)))
    implications = semantic = checked = 0
    for coefficients in product(range(-2, 3), repeat=3):
        terms = [[i+1, c] for i, c in enumerate(coefficients) if c]
        for values in points:
            if sum(c*values[i] for i, c in enumerate(coefficients)) <= 0:
                continue
            selected = {i for i, value in enumerate(values) if value}
            for kind, clause in explain_both(terms, selected, universe, len(selected)):
                assert is_false(clause, selected)
                for image in maps:
                    transported_terms = transport_terms(terms, image)
                    transported_clause = transport_clause(clause, image)
                    proof_for_clause(transported_terms, transported_clause, kind, universe, len(selected))
                    for candidate in points:
                        if kind == 'population' and sum(candidate) != len(selected):
                            continue
                        observed = sum(c*candidate[a-1] for a, c in transported_terms)
                        if observed <= 0:
                            assert not is_false(transported_clause, {i for i, v in enumerate(candidate) if v})
                        semantic += 1
                    checked += 1
                implications += 1
    assert canonical_clause([3, -1, 2]) == [-1, 2, 3]
    try:
        canonical_clause([1, -1])
    except AssertionError:
        pass
    else:
        raise AssertionError('tautological/duplicate-variable clause admitted')
    return {'status': 'PASS: exact explanation adapter, all finite transports and population semantics',
        'base_explanation_pairs': implications//2, 'transported_exact_implications': checked,
        'explicit_boolean_implication_checks': semantic, 'primary_only': True,
        'optimizer_or_solver_called': False, 'source_sha256': digest(Path(__file__)),
        'dependency_source_hashes': DEPENDENCIES}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controls', action='store_true', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = controls()
    save(args.output, report)
    print(json.dumps(report, indent=2), flush=True)
