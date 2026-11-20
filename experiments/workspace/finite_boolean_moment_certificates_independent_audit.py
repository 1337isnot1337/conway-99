"""Independent read-only arithmetic/source audit of the Boolean helper.

No subject module is imported and its control suite is not rerun.
Three separate hand-sized integer cases check the shift/penalty signs,
normalization, noncontiguous bits, both evaluation identities and an
empty retained domain. The v1-to-v2 difference is metadata only.
"""

import argparse
import ast
from copy import deepcopy
import hashlib
from itertools import combinations
import json
from math import gcd
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'experiments/workspace/finite_boolean_moment_certificates.py'
SOURCE_SHA = 'cdc37c56d4e379fc3774a832d942fb4cfb2eb787746bfdd3f9071880e791ee1e'
OLD = SOURCE.with_name('finite_boolean_moment_certificates_v1.py')
OLD_SHA = 'edd903db520a6fee0f436f5161289c394d354e739d03afe4873c3d37e7ab626c'
CONTROLS = ROOT/'experiments/logs/moments-and-counts/finite-boolean-moment-certificate-controls02.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def metadata_delta():
    old, new = ast.parse(OLD.read_text()), ast.parse(SOURCE.read_text())
    normalized = deepcopy(new)
    old_control = next(n for n in old.body if isinstance(n, ast.FunctionDef) and n.name == 'controls')
    new_control = next(n for n in normalized.body if isinstance(n, ast.FunctionDef) and n.name == 'controls')
    def field(function):
        matches = []
        for node in ast.walk(function):
            if isinstance(node, ast.Dict):
                for index, key in enumerate(node.keys):
                    if isinstance(key, ast.Constant) and key.value == 'largest_control_coefficient_bits':
                        matches.append((node, index))
        assert len(matches) == 1
        return matches[0]
    a, i = field(old_control); b, j = field(new_control)
    assert ast.dump(a.values[i]) == ast.dump(ast.parse('huge.bit_length()', mode='eval').body)
    assert ast.dump(b.values[j]) == ast.dump(ast.parse('(36*huge).bit_length()', mode='eval').body)
    b.values[j] = deepcopy(a.values[i])
    assert ast.dump(normalized) == ast.dump(old)
    scale = 2**201+1
    assert scale.bit_length() == 202 and (36*scale).bit_length() == 207
    return {'entire_source_AST_unchanged_except_metadata_expression': True,
            'old_scale_bit_length': 202, 'actual_largest_raw_coefficient_bits': 207}


def value(polynomial, atom):
    return sum(coefficient for mask, coefficient in polynomial.items() if mask & atom == mask)


def independent_repair(polynomial, moments, atoms, zeros):
    evaluated = [(a, value(polynomial, a), sum(mask & a == mask for mask in zeros)) for a in atoms]
    retained = [p for _, p, q in evaluated if q == 0]
    minimum = min(retained) if retained else 0
    # Independent ceiling formula, valid also for negative numerators.
    penalty = max([0]+[(minimum-p+q-1)//q for _, p, q in evaluated if q])
    result = dict(polynomial); result[0] = result.get(0, 0)-minimum
    for mask in zeros:
        result[mask] = result.get(mask, 0)+penalty
    result = {mask: c for mask, c in sorted(result.items()) if c}
    divisor = gcd(*(abs(c) for c in result.values())) or 1
    primitive = {mask: c//divisor for mask, c in result.items()}
    atom_values = [value(primitive, atom) for atom in atoms]
    assert min(atom_values) >= 0
    observed = sum(c*moments[mask] for mask, c in primitive.items())
    assert divisor*observed == sum(c*moments[mask] for mask, c in polynomial.items())-minimum*moments[0]
    return {'constant_subtracted': minimum, 'penalty': penalty,
            'primitive': list(map(list, primitive.items())), 'divisor': divisor,
            'atom_values': atom_values, 'moment_value': observed,
            'retained_count': len(retained)}


def calculate():
    assert digest(SOURCE) == SOURCE_SHA and digest(OLD) == OLD_SHA
    controls = json.loads(CONTROLS.read_text())
    assert controls['source_sha256'] == SOURCE_SHA and controls['largest_control_coefficient_bits'] == 207
    delta = metadata_delta()
    atoms = [0, 1, 4, 5, 16, 17, 20, 21]
    moments = {0: 2, 1: 2, 4: 2, 5: 0, 16: 1, 17: 0, 20: 0, 21: 0}
    first = independent_repair({0: 5, 1: -2, 4: -3}, moments, atoms, [5])
    assert first == {'constant_subtracted': 2, 'penalty': 2,
        'primitive': [[0, 3], [1, -2], [4, -3], [5, 2]], 'divisor': 1,
        'atom_values': [3, 1, 0, 0, 3, 1, 0, 0], 'moment_value': -4, 'retained_count': 6}
    second = independent_repair({0: 4, 1: -1, 2: -2, 3: -2},
                                {0: 3, 1: 0, 2: 0, 3: 1}, [0, 1, 2, 3], [1, 2])
    assert second['penalty'] == 3 and second['moment_value'] == -2
    assert second['primitive'] == [[1, 2], [2, 1], [3, -2]]
    empty = independent_repair({0: -2}, {0: 5, 1: 0, 2: 0}, [1, 2, 3], [1, 2])
    assert empty['retained_count'] == 0 and empty['divisor'] == 2
    assert empty['primitive'] == [[0, -1], [1, 1], [2, 1]] and empty['moment_value'] == -5
    scale = 2**120+3
    huge = independent_repair({0: 5*scale, 1: -2*scale, 4: -3*scale}, moments, atoms, [5])
    assert huge['divisor'] == scale and huge['primitive'] == first['primitive']
    assert huge['moment_value'] == -4
    ceil_checks = 0
    for p in range(-4, 5):
        for minimum in range(-4, 5):
            for q in range(1, 5):
                proposed = -((p-minimum)//q)
                assert (proposed-1)*q < minimum-p <= proposed*q
                assert proposed == (minimum-p+q-1)//q
                ceil_checks += 1
    polynomial = dict(first['primitive']); branches = set()
    for atom in atoms:
        bits = [1 << i for i in range(5) if atom >> i & 1]
        masks = [sum(group) for k in range(len(bits)+1) for group in combinations(bits, k)]
        assert value(polynomial, atom) == sum(polynomial.get(mask, 0) for mask in masks)
        branches.add('term' if len(polynomial) <= len(masks) else 'feature')
    assert branches == {'term', 'feature'}
    return {'status': 'PASS: independent finite Boolean moment arithmetic and full source review',
        'source_sha256': digest(Path(__file__)), 'subject_source_sha256': SOURCE_SHA,
        'preserved_v1_source_sha256': OLD_SHA, 'controls02_sha256': digest(CONTROLS),
        'metadata_correction': delta, 'hand_cases': [first, second, empty],
        'large_integer_gcd_control': huge, 'signed_ceiling_controls': ceil_checks,
        'sparse_term_and_feature_evaluation_identities_checked': True,
        'reviewed_mathematics': [
            'The constant monomial is1 on every atom. Subtracting minimum m changes unnormalized expectation by-m*moments[0].',
            'q is a sum of exact-zero monomials, hence nonnegative on atoms and has zero supplied expectation.',
            'M=max(0,max_removed ceil((m-p)/q)) makes p-m+M*q nonnegative on every full-domain atom.',
            'Empty retained domain uses m=0; the same full-domain check still proves the resulting inequality.',
            'A positive gcd divides every coefficient and the exact expectation; the zero polynomial uses gcd1.',
            'Term-subset evaluation and enumeration of present-atom features coincide for degree-bounded masks, including noncontiguous bits.',
            'A negative exact supplied expectation contradicts a nonnegative measure supported on the supplied complete atom domain.'
        ],
        'assumptions_and_limits': [
            'The caller must separately prove that the supplied nonempty atom list is a complete necessary domain.',
            'The caller must separately prove the graph-product interpretation of the moment coordinates.',
            'The helper accepts Python integer nonnegative moments, positive population, and degree at most4.',
            'Replay certifies the final polynomial and repair identity; minimality of shift/penalty and the method label are not needed for validity.'
        ],
        'subject_module_imported': False, 'subject_controls_rerun': False,
        'optimizer_or_solver_called': False, 'LP_tensor_or_graph_domain_built': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = calculate()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
