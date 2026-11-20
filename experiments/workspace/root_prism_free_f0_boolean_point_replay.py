"""Independent integer replay of the Boolean-cut augmentation of the F0 point.

The earlier exact baseline certificate is bound byte for byte. This checker
imports no model builder and reconstructs every new full cut's value and
its literal coefficient-sum quotient, including discarded tautologies.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def read(path, expected=None):
    raw = path.read_bytes()
    if expected:
        assert digest(raw) == expected, str(path)
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw), digest(raw)


def replay(root, baseline_path):
    logs = root/'experiments/logs/root-prism-free'
    baseline, baseline_sha = read(baseline_path, 'eb872efde0768eb514c954c57a1f8049785980d2a73e158f1d29842cc0a072cb')
    original, exact_sha = read(logs/'f0-fractional-native-run01-exact.json', '560487737d9569be679565a317acfca5425b28267014ec771f4e3440f9374837')
    model, model_sha = read(logs/'f0-boolean-fractional-model.json.gz', '703206929c9c85a40ac4ddcbfb1708c716c288482cf50c77a32249404e35b782')
    point, point_sha = read(logs/'f0-boolean-fractional-model-point.json', '047417fc0e266bce4fa29a58b2483c16f6c3bd8549de941ab220245c5e8ba2c7')
    assert model['validation'] == baseline['validation']
    assert model['matrix']['equalities'] == baseline['matrix']['equalities']
    assert model['matrix']['inequalities'][:11373] == baseline['matrix']['inequalities']
    assert point['point'] == original['point'] and point['original_exact_file_sha256'] == exact_sha
    d = int(point['point']['denominator'])
    numerators = list(map(int, point['point']['numerators']))
    assert len(numerators) == 5847 and d > 0 and all(0 <= n <= d for n in numerators)
    for row in model['matrix']['equalities']:
        assert sum(c*numerators[j] for j, c in row['terms']) == row['rhs']*d
    inequalities = model['matrix']['inequalities']
    slacks = [row['rhs']*d-sum(c*numerators[j] for j, c in row['terms']) for row in inequalities]
    assert len(slacks) == 11449 and min(slacks) >= 0
    orbit_of = [-1]*480
    for o, members in enumerate(model['validation']['selector_orbits']):
        for a in members:
            assert orbit_of[a] == -1
            orbit_of[a] = o
    assert min(orbit_of) >= 0
    full = model['Boolean_validation']['full_rows']
    mapping = model['Boolean_validation']['full_to_matrix']
    assert len(full) == len(mapping) == 4416
    direct_slacks = []
    for i, (row, link) in enumerate(zip(full, mapping)):
        coefficients = [0]*42
        for a, coefficient in row['terms']:
            coefficients[orbit_of[a]] += int(coefficient)
        rhs = int(row['rhs'])
        value = sum(c*numerators[o] for o, c in enumerate(coefficients))
        slack = rhs*d-value
        assert slack >= 0
        if link['unit_box_tautology']:
            assert all(c <= 0 for c in coefficients) and rhs >= 0
        else:
            literal = [(o, c) for o, c in enumerate(coefficients) if c]
            q = inequalities[link['matrix_inequality']]
            divisor = int(link['divisor'])
            assert divisor > 0
            assert literal == [(j, divisor*c) for j, c in q['terms']]
            assert rhs == divisor*q['rhs']
            assert slack == divisor*slacks[link['matrix_inequality']]
        if i >= 4404:
            direct_slacks.append(str(slack))
    assert direct_slacks == point['exact_check']['direct_cut_slack_numerators']
    return {'status': 'PASS: independent integer replay of complete Boolean augmentation',
            'source_sha256': digest(Path(__file__).read_bytes()),
            'baseline_file_sha256': baseline_sha, 'baseline_exact_sha256': exact_sha,
            'model_file_sha256': model_sha, 'point_file_sha256': point_sha,
            'baseline_validation_and_matrix_prefix_unchanged': True,
            'baseline_exact_point_unchanged': True,
            'quotient_equalities_checked': len(model['matrix']['equalities']),
            'quotient_inequalities_checked': len(inequalities),
            'quotient_bounds_checked': len(numerators), 'literal_Boolean_rows_checked': len(full),
            'literal_coefficient_sum_quotients_reconstructed': True,
            'direct_twelve_slack_numerators': direct_slacks,
            'common_denominator': str(d), 'denominator_bits': d.bit_length(),
            'earlier_full_baseline_certificate_bound_not_rederived': True,
            'optimizer_called': False, 'graph_constructed': False, 'component_excluded': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--baseline', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.root, args.baseline)
    with args.output.open('x') as handle:
        json.dump(result, handle, indent=2)
        handle.write('\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
