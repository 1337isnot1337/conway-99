"""Independent direct truth audit of the frozen carry threshold encoder.

No SAT solver or incidence formula is loaded. Gate clauses are checked
against ordinary Boolean arithmetic. Large-weight circuits are evaluated
by an independent gate interpreter and compared with integer sums.
"""

import argparse
import hashlib
import importlib.util
from itertools import product
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SUBJECT = Path(__file__).with_name('root_prism_free_f0_carry_threshold.py')
SUBJECT_SHA = '942efb35d35429d88d7cc9c3bc14aa7a116972186f60abeebe50db89214ec75f'
SEMANTICS = {
    'xor2': (2, lambda xs: sum(xs) % 2 == 1),
    'and2': (2, lambda xs: all(xs)),
    'or2': (2, lambda xs: any(xs)),
    'xor3': (3, lambda xs: sum(xs) % 2 == 1),
    'majority3': (3, lambda xs: sum(xs) >= 2),
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def truth(literal, values):
    if type(literal) is bool:
        return literal
    return values[abs(literal)] if literal > 0 else not values[abs(literal)]


def trace(metadata, primary):
    values = dict(primary)
    last = metadata['initial_top']
    for kind, inputs, output in metadata['gate_definitions']:
        assert output == last+1
        assert all(type(v) is bool or 0 < abs(v) < output for v in inputs)
        values[output] = SEMANTICS[kind][1]([truth(v, values) for v in inputs])
        last = output
    assert last == metadata['final_top']
    return values


def calculate():
    assert digest(SUBJECT) == SUBJECT_SHA
    spec = importlib.util.spec_from_file_location('frozen_carry_subject', SUBJECT)
    subject = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(subject)
    gate_cases = 0
    inputs_domain = [False, True, 1, -1, 2, -2, 3, -3]
    for kind, (arity, function) in SEMANTICS.items():
        for inputs in product(inputs_domain, repeat=arity):
            circuit = subject.Circuit(3, 1)
            output = circuit.gate(kind, inputs)
            assert output == 4
            for bits in product((False, True), repeat=4):
                values = {i+1: v for i, v in enumerate(bits)}
                expected = function([truth(v, values) for v in inputs])
                accepted = all(any(truth(v, values) for v in clause) for clause in circuit.clauses)
                assert accepted == (values[output] == expected)
                gate_cases += 1
    large = 1 << 80
    cases = [
        ([(1, large+3), (2, (large >> 1)+5), (-3, large+7)], 3),
        ([(1, large), (-1, large), (2, 3), (2, 7)], 2),
        ([(1, 257), (-2, 511), (3, 1025), (-4, 2047)], 4),
        ([], 1),
    ]
    threshold_cases = formula_cases = 0
    for terms, n in cases:
        total = sum(w for _, w in terms)
        demands = sorted(set([-1, 0, 1, total//2, total, total+1, large-1, large, large+1]))
        for demand in demands:
            for guard in (None, 1, -1):
                clauses, top, metadata = subject.literal_threshold(
                    terms, demand, n+5, guard=guard, include_trace=True)
                assert metadata['final_top'] == top
                for bits in product((False, True), repeat=n):
                    primary = {i+1: b for i, b in enumerate(bits)}
                    integer_test = sum(w*truth(v, primary) for v, w in terms) >= demand
                    expected = integer_test if guard is None else (not truth(guard, primary) or integer_test)
                    values = trace(metadata, primary)
                    accepted = all(any(truth(v, values) for v in clause) for clause in clauses)
                    assert accepted == expected
                    if metadata['sum_bits']:
                        computed = sum((1 << i)*truth(v, values) for i, v in enumerate(metadata['sum_bits']))
                        normalized = sum(w*truth(v, primary) for v, w in metadata['normalized_terms'])
                        assert computed == normalized
                    threshold_cases += 1
                formula_cases += 1
    signed_cases = 0
    for coefficients in ([large+7, -(large >> 1)-3, (1 << 70)+1, -2*large],
                         [3, 6, 9], [-3, -6, -9], [0, 0, 0], [7, -13, 4, -2]):
        n = len(coefficients)
        terms = [(i+1, c) for i, c in enumerate(coefficients) if c]
        clauses, top, _ = subject.signed_atmost_zero(terms, n+5)
        literals = [(v if c < 0 else -v, abs(c)) for v, c in terms]
        reference, reference_top, metadata = subject.literal_threshold(
            literals, sum(c for _, c in terms if c > 0), n+5, include_trace=True)
        assert clauses == reference and top == reference_top
        for bits in product((False, True), repeat=n):
            values = trace(metadata, {i+1: b for i, b in enumerate(bits)})
            accepted = all(any(truth(v, values) for v in clause) for clause in clauses)
            assert accepted == (sum(c*b for c, b in zip(coefficients, bits)) <= 0)
            signed_cases += 1
    try:
        subject.literal_threshold([(1, 3), (2, 5)], 4, 2, maximum_states=0)
    except RuntimeError:
        pass
    else:
        raise AssertionError('a resource refusal must not return a partial formula')
    return {'status': 'PASS: independent gate truth, integer-circuit and source audit',
        'audit_source_sha256': digest(Path(__file__)), 'subject_sha256': SUBJECT_SHA,
        'direct_gate_CNF_truth_assignments': gate_cases,
        'large_weight_threshold_formulas': formula_cases,
        'large_weight_threshold_assignments': threshold_cases,
        'large_weight_signed_assignments': signed_cases,
        'maximum_tested_weight_bit_length': 82,
        'checks': ['full gate equivalences including constants, repeated inputs and complements',
                   'carry-save identity sum=xor+2*majority and two-row ripple arithmetic',
                   'low-to-high constant comparator recurrence',
                   'exact integer weight merging, Boolean capping and gcd normalization',
                   'signed literal and guard aliases', 'fresh strictly increasing auxiliary IDs',
                   'resource refusal returns no usable partial formula'],
        'SAT_solver_called': False, 'optimizer_called': False, 'incidence_formula_loaded': False,
        'scope': 'The complete source was read. Primitive clauses and independent integer circuit traces were checked; no main incidence formula or future continuation was rebuilt.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = calculate()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
