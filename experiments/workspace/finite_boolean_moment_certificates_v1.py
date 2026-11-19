"""Exact inequalities from a complete finite Boolean atom domain.

Monomials and atoms are nonnegative integer bit masks. A monomial is one
on an atom exactly when its mask is a subset of the atom. This helper
does not generate a domain or solve an LP. It checks integer multiplier
candidates on every supplied atom, including atoms removed by zero moments.
Graph-domain necessity and literal graph-product lifting remain separate.
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from math import comb, gcd
from pathlib import Path
import random
import time


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def polynomial(terms, universe, maximum_degree=4):
    """Combine duplicate terms without changing their integer polynomial."""
    assert type(universe) is int and universe >= 0
    assert type(maximum_degree) is int and 0 <= maximum_degree <= 4
    combined = Counter()
    for mask, coefficient in terms:
        assert type(mask) is int and type(coefficient) is int
        assert 0 <= mask and not mask & ~universe
        assert mask.bit_count() <= maximum_degree
        combined[mask] += coefficient
    return {mask: c for mask, c in sorted(combined.items()) if c}


def features(atom, maximum_degree=4):
    bits = []
    while atom:
        bit = atom & -atom
        bits.append(bit)
        atom -= bit
    yield 0
    for degree in range(1, min(maximum_degree, len(bits))+1):
        for selected in combinations(bits, degree):
            yield sum(selected)


def evaluate(coefficients, atom, maximum_degree=4):
    n = atom.bit_count()
    feature_count = sum(comb(n, k) for k in range(min(n, maximum_degree)+1))
    if len(coefficients) <= feature_count:
        return sum(c for mask, c in coefficients.items() if atom & mask == mask)
    return sum(coefficients.get(mask, 0) for mask in features(atom, maximum_degree))


def context(terms, moments, atoms, universe, maximum_degree):
    coefficients = polynomial(terms, universe, maximum_degree)
    assert isinstance(moments, dict) and moments.get(0, 0) > 0
    assert all(type(mask) is int and 0 <= mask and not mask & ~universe
               and mask.bit_count() <= maximum_degree
               and type(value) is int and value >= 0
               for mask, value in moments.items())
    assert set(coefficients).issubset(moments)
    domain = tuple(atoms)
    assert domain and list(domain) == sorted(set(domain))
    assert all(type(atom) is int and atom >= 0 and not atom & ~universe for atom in domain)
    return coefficients, domain


def expectation(coefficients, moments):
    assert set(coefficients).issubset(moments)
    return sum(c*moments[mask] for mask, c in coefficients.items())


def primitive(coefficients):
    divisor = gcd(*(abs(c) for c in coefficients.values()))
    if not divisor:
        divisor = 1
    return {mask: c//divisor for mask, c in sorted(coefficients.items()) if c}, divisor


def atom_summary(coefficients, domain, maximum_degree):
    stream = hashlib.sha256()
    least = greatest = None
    zero_count = 0
    for atom in domain:
        value = evaluate(coefficients, atom, maximum_degree)
        stream.update((str(value)+'\n').encode())
        least = value if least is None else min(least, value)
        greatest = value if greatest is None else max(greatest, value)
        zero_count += value == 0
    return {'minimum_on_full_domain': least, 'maximum_on_full_domain': greatest,
            'zero_value_atoms': zero_count, 'ordered_atom_value_sha256': stream.hexdigest()}


def finish(raw, shifted, moments, domain, universe, maximum_degree, method, details):
    reduced, divisor = primitive(shifted)
    summary = atom_summary(reduced, domain, maximum_degree)
    assert summary['minimum_on_full_domain'] >= 0
    exact_value = expectation(reduced, moments)
    assert expectation(shifted, moments) == divisor*exact_value
    return {'status': 'EXACT_SEPARATOR' if exact_value < 0 else 'NO_SEPARATOR_FROM_THIS_MULTIPLIER',
        'method': method, 'universe_mask': universe, 'maximum_degree': maximum_degree,
        'full_atom_count': len(domain), 'ordered_full_domain_sha256': digest(domain),
        'all_moment_data_sha256': digest(sorted(moments.items())),
        'root_population': moments[0], 'raw_integer_polynomial': list(map(list, raw.items())),
        'primitive_polynomial': list(map(list, reduced.items())), 'normalization_gcd': divisor,
        'exact_value_at_supplied_moments': exact_value, **summary, **details,
        'every_full_atom_checked_with_python_integers': True,
        'domain_necessity_proved_by_this_helper': False,
        'literal_graph_product_replay_complete': False, 'optimizer_or_solver_called': False}


def constant_shift(terms, moments, atoms, universe, maximum_degree=4):
    """Subtract the exact minimum on the complete domain from the constant."""
    raw, domain = context(terms, moments, atoms, universe, maximum_degree)
    minimum = min(evaluate(raw, atom, maximum_degree) for atom in domain)
    shifted = dict(raw)
    shifted[0] = shifted.get(0, 0)-minimum
    shifted = polynomial(shifted.items(), universe, maximum_degree)
    assert expectation(shifted, moments) == expectation(raw, moments)-minimum*moments[0]
    return finish(raw, shifted, moments, domain, universe, maximum_degree,
        'exact full-domain constant shift', {'constant_subtracted': minimum,
        'zero_features': [], 'zero_penalty_multiplier': 0,
        'retained_atom_count': len(domain), 'removed_atom_count': 0})


def zero_filter_penalty(terms, moments, atoms, universe, zero_features, maximum_degree=4):
    """Restore a fixed-point zero restriction by an exact nonnegative penalty.

    A removed atom contains at least one selected zero monomial. After a
    constant shift makes p nonnegative on retained atoms, the integer M
    makes p+M*q nonnegative on every removed atom, where q counts those
    zero monomials. The penalty has zero expectation at the supplied point.
    """
    raw, domain = context(terms, moments, atoms, universe, maximum_degree)
    zeros = list(zero_features)
    assert zeros == sorted(set(zeros)) and 0 not in zeros
    assert all(mask in moments and moments[mask] == 0 for mask in zeros)
    q = polynomial(((mask, 1) for mask in zeros), universe, maximum_degree)
    evaluated = [(atom, evaluate(raw, atom, maximum_degree), evaluate(q, atom, maximum_degree))
                 for atom in domain]
    retained_values = [p for _, p, penalty in evaluated if penalty == 0]
    minimum = min(retained_values) if retained_values else 0
    multiplier = 0
    removed_count = 0
    for _, p, penalty in evaluated:
        if not penalty:
            assert p-minimum >= 0
            continue
        assert penalty > 0
        removed_count += 1
        # ceil((minimum-p)/penalty), valid for arbitrary signed numerators.
        multiplier = max(multiplier, -((p-minimum)//penalty))
    shifted = Counter(raw)
    shifted[0] -= minimum
    for mask in zeros:
        shifted[mask] += multiplier
    shifted = polynomial(shifted.items(), universe, maximum_degree)
    assert expectation(q, moments) == 0
    assert expectation(shifted, moments) == expectation(raw, moments)-minimum*moments[0]
    return finish(raw, shifted, moments, domain, universe, maximum_degree,
        'exact zero-filter penalty recovery', {'constant_subtracted': minimum,
        'zero_features': zeros, 'zero_penalty_multiplier': multiplier,
        'retained_atom_count': len(retained_values), 'removed_atom_count': removed_count,
        'retained_domain_empty': not bool(retained_values),
        'zero_filter_chosen_only_from_exact_zero_moments': True})


def replay(certificate, moments, atoms):
    """Check the final polynomial and the explicit repair identity directly."""
    universe, degree = certificate['universe_mask'], certificate['maximum_degree']
    raw, domain = context(certificate['raw_integer_polynomial'], moments, atoms, universe, degree)
    assert digest(domain) == certificate['ordered_full_domain_sha256']
    assert digest(sorted(moments.items())) == certificate['all_moment_data_sha256']
    assert certificate['root_population'] == moments[0]
    assert certificate['full_atom_count'] == len(domain)
    zeros = certificate['zero_features']
    assert zeros == sorted(set(zeros)) and 0 not in zeros
    assert all(mask in moments and moments[mask] == 0 for mask in zeros)
    multiplier = certificate['zero_penalty_multiplier']
    constant = certificate['constant_subtracted']
    assert type(multiplier) is int and multiplier >= 0 and type(constant) is int
    q = polynomial(((mask, 1) for mask in zeros), universe, degree)
    restored = Counter(raw)
    restored[0] -= constant
    for mask in zeros:
        restored[mask] += multiplier
    restored = polynomial(restored.items(), universe, degree)
    reduced, divisor = primitive(restored)
    assert list(map(list, reduced.items())) == certificate['primitive_polynomial']
    assert divisor == certificate['normalization_gcd']
    summary = atom_summary(reduced, domain, degree)
    assert summary['minimum_on_full_domain'] >= 0
    assert all(certificate[key] == value for key, value in summary.items())
    value = expectation(reduced, moments)
    assert value == certificate['exact_value_at_supplied_moments']
    assert certificate['status'] == ('EXACT_SEPARATOR' if value < 0 else 'NO_SEPARATOR_FROM_THIS_MULTIPLIER')
    removed = sum(evaluate(q, atom, degree) > 0 for atom in domain)
    assert removed == certificate['removed_atom_count']
    assert len(domain)-removed == certificate['retained_atom_count']
    return {'status': 'PASS: full-domain integer polynomial and repair identity',
            'certificate_sha256': digest(certificate), 'exact_moment_value': value,
            'full_atom_count': len(domain), 'optimizer_or_solver_called': False}


def controls():
    full = [0, 1, 2, 3]
    inconsistent = {0: 1, 1: 1, 2: 1, 3: 0}
    plain = constant_shift([(0, -36), (1, -1), (2, -1), (3, 1)], inconsistent, full, 3)
    assert plain['constant_subtracted'] == -37
    assert plain['primitive_polynomial'] == [[0, 1], [1, -1], [2, -1], [3, 1]]
    assert plain['status'] == 'EXACT_SEPARATOR' and plain['exact_value_at_supplied_moments'] == -1
    penalty = zero_filter_penalty([(0, 1), (1, -1), (2, -1)], inconsistent, full, 3, [3])
    assert penalty['zero_penalty_multiplier'] == 1 and penalty['constant_subtracted'] == 0
    assert penalty['primitive_polynomial'] == plain['primitive_polynomial']
    assert penalty['retained_atom_count'] == 3 and penalty['removed_atom_count'] == 1
    huge = 2**201+1
    scaled = constant_shift([(0, -36*huge), (1, -2*huge), (1, huge),
                             (2, -huge), (3, huge)], inconsistent, full, 3)
    assert scaled['normalization_gcd'] == huge
    assert scaled['primitive_polynomial'] == plain['primitive_polynomial']
    # Empty retained domain: x1 is zero in the data, but every allowed atom has x1=1.
    empty = zero_filter_penalty([(0, -1)], {0: 3, 1: 0}, [1], 1, [1])
    assert empty['retained_domain_empty'] and empty['primitive_polynomial'] == [[0, -1], [1, 1]]
    assert empty['exact_value_at_supplied_moments'] == -3
    for certificate, moments, atoms in [(plain, inconsistent, full), (penalty, inconsistent, full),
                                       (scaled, inconsistent, full), (empty, {0: 3, 1: 0}, [1])]:
        replay(certificate, moments, atoms)

    rng = random.Random(992014)
    distributions = generated = evaluations = 0
    for n in range(1, 6):
        universe = (1 << n)-1
        monomials = sorted(mask for mask in range(1 << n) if mask.bit_count() <= 4)
        for cap in range(n+1):
            atoms = [mask for mask in range(1 << n) if mask.bit_count() <= cap]
            for sample in range(8):
                masses = [rng.randrange(4) for _ in atoms]
                masses[0] += 1
                moments = {mask: sum(weight for atom, weight in zip(atoms, masses)
                                    if atom & mask == mask) for mask in monomials}
                terms = [(mask, rng.randrange(-20, 21)) for mask in monomials]
                zeros = [mask for mask in monomials if mask and moments[mask] == 0]
                for certificate in (constant_shift(terms, moments, atoms, universe),
                                    zero_filter_penalty(terms, moments, atoms, universe, zeros)):
                    assert certificate['status'] == 'NO_SEPARATOR_FROM_THIS_MULTIPLIER'
                    replay(certificate, moments, atoms)
                    coefficients = dict(certificate['primitive_polynomial'])
                    # Direct evaluation uses every monomial, independently of the optimized path.
                    observed = 0
                    for atom, mass in zip(atoms, masses):
                        value = sum(coefficient for mask, coefficient in coefficients.items()
                                    if all(not (mask >> i & 1) or atom >> i & 1 for i in range(n)))
                        assert value >= 0
                        observed += mass*value
                        evaluations += 1
                    assert observed == certificate['exact_value_at_supplied_moments']
                    generated += 1
                distributions += 1
    return {'status': 'PASS: exact full-domain shifts and zero-filter penalty recovery',
            'known_separation_controls': 4, 'largest_control_coefficient_bits': huge.bit_length(),
            'genuine_nonnegative_integer_distributions': distributions,
            'checked_nonseparating_polynomials': generated,
            'independent_literal_atom_evaluations': evaluations,
            'empty_retained_domain_control': True, 'duplicate_terms_control': True,
            'optimizer_or_solver_called': False,
            'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--controls', action='store_true', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    result = controls()
    result['seconds'] = time.monotonic()-started
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
