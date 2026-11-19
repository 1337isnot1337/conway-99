"""Exact weighted thresholds through carry-save and ripple binary adders.

All gates have full Tseitin equivalences. The encoder first compresses
each weight-bit bucket to at most two bits, adds the resulting two rows,
then compares the exact binary sum with a constant. Auxiliary variables
are fresh and existential; no primary variable is assigned by a gate.
"""

import argparse
from collections import Counter
import hashlib
from itertools import product
import json
from math import gcd
from pathlib import Path


TABLES = {
    'xor2': (False, True, True, False),
    'and2': (False, False, False, True),
    'or2': (False, True, True, True),
    'xor3': (False, True, True, False, True, False, False, True),
    'majority3': (False, False, False, True, False, True, True, True),
}


def negate(value):
    return not value if type(value) is bool else -value


def canonical(value):
    return json.dumps(value, separators=(',', ':'), sort_keys=True).encode()


class Circuit:
    """One monotone ID pool and full truth-table gate definitions."""

    def __init__(self, top, maximum_states):
        assert type(top) is int and top >= 0
        assert type(maximum_states) is int and maximum_states >= 0
        self.initial_top = self.top = top
        self.maximum_states = maximum_states
        self.clauses = []
        self.definitions = []
        self.counts = Counter()

    def clause(self, values):
        result = []
        seen = set()
        for value in values:
            if type(value) is bool:
                if value:
                    return
                continue
            assert type(value) is int and value != 0 and abs(value) <= self.top
            if -value in seen:
                return
            if value not in seen:
                seen.add(value)
                result.append(value)
        self.clauses.append(result)

    def gate(self, kind, inputs):
        table = TABLES[kind]
        inputs = tuple(inputs)
        assert len(table) == 2**len(inputs)
        assert all(type(value) is bool or
                   (type(value) is int and 0 < abs(value) <= self.top)
                   for value in inputs)
        if self.top-self.initial_top >= self.maximum_states:
            raise RuntimeError('carry gate resource limit; no partial formula returned')
        self.top += 1
        output = self.top
        # Each clause forbids one input valuation with the wrong output.
        # Repeated or complemented inputs and Boolean constants are valid:
        # impossible abstract valuations simplify to tautological clauses.
        for bits, expected in zip(product((False, True), repeat=len(inputs)), table):
            forbidden = [negate(value) if bit else value
                         for value, bit in zip(inputs, bits)]
            self.clause(forbidden + [output if expected else -output])
        self.definitions.append([kind, list(inputs), output])
        self.counts[kind] += 1
        return output

    def add_bits(self, values):
        # Arithmetic inputs contain only literals and constant zero.
        inputs = [value for value in values if type(value) is not bool]
        assert all(type(value) is not bool or value is False for value in values)
        if not inputs:
            return False, False
        if len(inputs) == 1:
            return inputs[0], False
        assert len(inputs) in (2, 3)
        if len(inputs) == 2:
            return self.gate('xor2', inputs), self.gate('and2', inputs)
        return self.gate('xor3', inputs), self.gate('majority3', inputs)


def normalize(terms, demand):
    """Merge equal literals, cap at demand, then divide a common gcd."""
    assert type(demand) is int and demand > 0
    merged = Counter()
    for literal, weight in terms:
        assert type(literal) is int and literal != 0
        assert type(weight) is int and weight > 0
        merged[literal] += weight
    capped = sorted((literal, min(weight, demand))
                    for literal, weight in merged.items())
    divisor = gcd(*(weight for _, weight in capped)) if capped else 1
    normalized = [(literal, weight//divisor) for literal, weight in capped]
    return normalized, (demand+divisor-1)//divisor, divisor


def literal_threshold(terms, demand, top, guard=None, maximum_states=250000,
                      include_trace=False):
    """Encode guard -> sum(weight * truth(literal)) >= demand.

    A None guard means the threshold is unconditional. Supplied literals
    and the optional signed guard use IDs at most top. Failure at the
    resource bound returns no partial clauses to the caller.
    """
    assert type(top) is int and top >= 0
    assert type(demand) is int
    terms = list(terms)
    assert all(type(literal) is int and 0 < abs(literal) <= top and
               type(weight) is int and weight > 0 for literal, weight in terms)
    assert guard is None or (type(guard) is int and 0 < abs(guard) <= top)
    circuit = Circuit(top, maximum_states)
    metadata = {'original_terms': [list(row) for row in terms],
                'original_demand': demand, 'guard': guard, 'initial_top': top}
    normalized, threshold, divisor = normalize(terms, demand) if demand > 0 else ([], 0, 1)
    total = sum(weight for _, weight in normalized)
    metadata.update(normalized_terms=[list(row) for row in normalized],
                    normalized_demand=threshold, weight_gcd=divisor,
                    normalized_weight_sum=total)
    sum_bits = []
    compressed_rows = []
    full_adders = ripple_full = ripple_half = 0
    if demand <= 0:
        comparison = True
    elif total < threshold:
        comparison = False
    else:
        buckets = [[] for _ in range(total.bit_length())]
        for literal, weight in normalized:
            for bit in range(weight.bit_length()):
                if (weight >> bit) & 1:
                    buckets[bit].append(literal)
        bit = 0
        while bit < len(buckets):
            while len(buckets[bit]) > 2:
                inputs = [buckets[bit].pop() for _ in range(3)]
                summand, carry = circuit.add_bits(inputs)
                buckets[bit].append(summand)
                if bit+1 == len(buckets):
                    buckets.append([])
                buckets[bit+1].append(carry)
                full_adders += 1
            bit += 1
        assert all(len(bucket) <= 2 for bucket in buckets)
        compressed_rows = [list(bucket) for bucket in buckets]
        carry = False
        for bucket in buckets:
            inputs = list(bucket) + ([carry] if type(carry) is int else [])
            ripple_full += len(inputs) == 3
            ripple_half += len(inputs) == 2
            summand, carry = circuit.add_bits(inputs)
            sum_bits.append(summand)
        if type(carry) is int:
            sum_bits.append(carry)
        while sum_bits and sum_bits[-1] is False:
            sum_bits.pop()
        # For the low i+1 bits, comparison means sum_low >= threshold_low.
        # Threshold bit0: sum_bit OR previous; bit1: sum_bit AND previous.
        comparison = True
        width = max(len(sum_bits), threshold.bit_length())
        for bit in range(width):
            summand = sum_bits[bit] if bit < len(sum_bits) else False
            kind = 'and2' if (threshold >> bit) & 1 else 'or2'
            comparison = circuit.gate(kind, [summand, comparison])
    final_clause = [comparison] if guard is None else [-guard, comparison]
    circuit.clause(final_clause)
    metadata.update(final_top=circuit.top, auxiliary_variables=circuit.top-top,
                    clauses=len(circuit.clauses),
                    literal_occurrences=sum(map(len, circuit.clauses)),
                    carry_save_full_adders=full_adders,
                    ripple_full_adders=ripple_full, ripple_half_adders=ripple_half,
                    gate_counts=dict(sorted(circuit.counts.items())),
                    sum_bits=sum_bits, comparator=comparison,
                    gate_definition_sha256=hashlib.sha256(canonical(circuit.definitions)).hexdigest(),
                    full_Tseitin_equivalences=True,
                    all_input_ids_at_most=top,
                    maximum_gate_states=maximum_states)
    if include_trace:
        metadata['gate_definitions'] = circuit.definitions
        metadata['compressed_bit_buckets'] = compressed_rows
    return circuit.clauses, circuit.top, metadata


def guarded_threshold(target, terms, demand, top, maximum_states=250000):
    assert type(target) is int and 0 < target <= top
    assert all(type(v) is int and 0 < v <= top for v, _ in terms)
    assert len({v for v, _ in terms}) == len(terms)
    return literal_threshold(terms, demand, top, target, maximum_states)


def signed_atmost_zero(terms, top, maximum_states=250000):
    terms = sorted(terms)
    assert all(type(v) is int and 0 < v <= top and
               type(c) is int and c != 0 for v, c in terms)
    assert len({v for v, _ in terms}) == len(terms)
    literals = [(v if c < 0 else -v, abs(c)) for v, c in terms]
    demand = sum(c for _, c in terms if c > 0)
    clauses, final_top, metadata = literal_threshold(literals, demand, top,
                                                    maximum_states=maximum_states)
    return clauses, final_top, {
        'signed_terms': [list(row) for row in terms],
        'positive_weighted_literals': [list(row) for row in literals],
        'positive_literal_threshold': demand,
        'initial_top': top, 'final_top': final_top,
        'auxiliary_variables': final_top-top, 'clauses': len(clauses),
        'literal_occurrences': sum(map(len, clauses)),
        'underlying_carry_threshold': metadata,
        'no_original_selector_fixed': True,
        'primary_assignment_restriction': 'original signed sum is at most zero'}


def literal_value(literal, values):
    if type(literal) is bool:
        return literal
    value = values[abs(literal)]
    return value if literal > 0 else not value


def evaluate_trace(metadata, values):
    values = dict(values)
    for kind, inputs, output in metadata['gate_definitions']:
        index = 0
        for literal in inputs:
            index = 2*index + int(literal_value(literal, values))
        values[output] = TABLES[kind][index]
    return values


def controls():
    from pysat.solvers import Solver
    formulas = assignments = gate_assignments = 0
    for kind, table in TABLES.items():
        arity = (len(table)-1).bit_length()
        # Include constants, repeated inputs, and complementary input literals.
        examples = [list(range(1, arity+1)), [1]*arity,
                    [1 if i % 2 == 0 else -1 for i in range(arity)],
                    [False]+list(range(1, arity)), [True]+list(range(1, arity))]
        for inputs in examples:
            circuit = Circuit(arity, 10)
            output = circuit.gate(kind, inputs)
            for bits in product((False, True), repeat=arity+1):
                values = {i+1: bit for i, bit in enumerate(bits[:-1])}
                values[output] = bits[-1]
                index = 0
                for literal in inputs:
                    index = 2*index + int(literal_value(literal, values))
                satisfies = all(any(literal_value(v, values) for v in clause)
                                for clause in circuit.clauses)
                assert satisfies == (bits[-1] == table[index])
                gate_assignments += 1

    def test_threshold(terms, demand, n, guard):
        nonlocal formulas, assignments
        clauses, final_top, metadata = literal_threshold(
            terms, demand, n+3, guard=guard, include_trace=True)
        assert final_top == metadata['final_top']
        assert all(abs(v) <= final_top for clause in clauses for v in clause)
        with Solver(name='minisat22', bootstrap_with=clauses) as solver:
            for bits in product((False, True), repeat=n):
                values = {i+1: bit for i, bit in enumerate(bits)}
                threshold = sum(weight*literal_value(v, values) for v, weight in terms) >= demand
                expected = threshold if guard is None else (not literal_value(guard, values) or threshold)
                assumptions = [i+1 if bit else -(i+1) for i, bit in enumerate(bits)]
                assert solver.solve(assumptions=assumptions) == expected
                extended = evaluate_trace(metadata, values)
                assert all(any(literal_value(v, extended) for v in clause)
                           for clause in clauses) == expected
                if metadata['sum_bits']:
                    normalized_sum = sum(weight*literal_value(v, values)
                                         for v, weight in metadata['normalized_terms'])
                    assert sum((1 << i)*literal_value(v, extended)
                               for i, v in enumerate(metadata['sum_bits'])) == normalized_sum
                assignments += 1
        formulas += 1

    for n in range(5):
        for weights in product((1, 2, 3), repeat=n):
            terms = [(i+1, weight) for i, weight in enumerate(weights)]
            for demand in range(sum(weights)+2):
                test_threshold(terms, demand, n, None)
                test_threshold(terms, demand, n+1, n+1)
    alias_cases = [([(1, 2), (1, 3), (-1, 4), (2, 5)], 2),
                   ([(1, 1), (-1, 1)], 1),
                   ([(1, 1), (2, 31), (-3, 1024)], 3),
                   ([(1, 6), (-2, 9), (3, 12)], 3)]
    for terms, n in alias_cases:
        demands = sorted({-1, 0, 1, 2, 3, 7, sum(w for _, w in terms),
                          sum(w for _, w in terms)+1})
        for demand in demands:
            for guard in (None, 1, -1):
                test_threshold(terms, demand, n, guard)

    signed_formulas = signed_assignments = 0
    samples = [()]
    for n in range(1, 5):
        samples.extend(product((-2, -1, 0, 1, 2), repeat=n))
    samples.extend([(7, -13, 4, -2), (100, -3, -2), (-6, 9, -12),
                    (2, 1, 1, 1, 3, -8), (333, -999, 111, -27)])
    for coefficients in samples:
        n = len(coefficients)
        terms = [(i+1, c) for i, c in enumerate(coefficients) if c]
        clauses, top, metadata = signed_atmost_zero(terms, n+3)
        assert top == metadata['final_top']
        with Solver(name='minisat22', bootstrap_with=clauses) as solver:
            for bits in product((0, 1), repeat=n):
                assumptions = [i+1 if bit else -(i+1) for i, bit in enumerate(bits)]
                expected = sum(c*bit for c, bit in zip(coefficients, bits)) <= 0
                assert solver.solve(assumptions=assumptions) == expected
                signed_assignments += 1
        signed_formulas += 1
    try:
        literal_threshold([(1, 3), (2, 3), (3, 3), (4, 3)], 5, 4, maximum_states=1)
    except RuntimeError:
        pass
    else:
        raise AssertionError('resource limit did not reject construction')
    return {'status': 'carry-save, ripple, comparator and signed controls PASS',
            'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'gate_truth_assignments': gate_assignments,
            'weighted_formulas': formulas, 'weighted_primary_assignments': assignments,
            'signed_formulas': signed_formulas,
            'signed_primary_assignments': signed_assignments,
            'direct_gate_trace_and_exact_binary_sum_checked': True,
            'aliases_complements_constants_and_guard_aliases_checked': True,
            'all_full_Tseitin_equivalences_checked': True,
            'fresh_auxiliary_ids_and_resource_refusal_checked': True,
            'tiny_boolean_solver_only': True,
            'incidence_or_LP_query_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = controls()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
