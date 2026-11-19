"""Export the exact order-ten dual as a reusable inequality on order-nine cores.

The original dual is immutable. This source also tests the proposed
denominator36 simplification using exact Fraction arithmetic.
"""

import argparse
import ast
from fractions import Fraction
from functools import reduce
import hashlib
import json
from math import gcd, lcm
from pathlib import Path
import pickle


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def published_point():
    path = Path(__file__).with_name('grid_free_core9_certificate.py')
    tree = ast.parse(path.read_text())
    node = next(node for node in tree.body if isinstance(node, ast.Assign)
                and any(isinstance(t, ast.Name) and t.id == 'INTEGER_POINT' for t in node.targets))
    point = ast.literal_eval(node.value)
    assert len(point) == 58 and point[0] == 1 and point[56:] == [0, 0]
    return point


def derive(rows, weights, upper, point):
    coefficients = [Fraction(0) for _ in range(550)]
    for row, weight in zip(rows, weights):
        assert type(weight) is int and weight >= 0
        for j, value in row['original_form']:
            coefficients[j] += Fraction(weight*value, row['primitive_divisor'])
    assert all(a.denominator == 1 for a in coefficients[58:])
    new = [int(a) for a in coefficients[58:]]
    bound_terms = [[j, a, upper[j]] for j, a in enumerate(new, 58) if a > 0]
    nonnegative_terms = [[j, -a] for j, a in enumerate(new, 58) if a < 0]
    contribution = sum(a*b for _, a, b in bound_terms)
    old = coefficients[:58]
    old[0] += contribution
    denominator = lcm(*(a.denominator for a in old))
    integer = [int(a*denominator) for a in old]
    common = reduce(gcd, [abs(a) for a in integer], 0)
    assert common > 0
    integer = [a//common for a in integer]
    evaluated = sum(a*x for a, x in zip(integer, point))
    rational_evaluation = sum(a*x for a, x in zip(old, point))
    assert Fraction(evaluated*common, denominator) == rational_evaluation
    return {'row_weights': weights, 'nonzero_row_weights': sum(w > 0 for w in weights),
            'new_positive_coefficients_eliminated_by_bounds': bound_terms,
            'new_negative_coefficients_eliminated_by_nonnegativity': nonnegative_terms,
            'upper_bound_contribution': contribution,
            'old_cut_rational_coefficients': [[a.numerator, a.denominator] for a in old],
            'clearing_denominator': denominator, 'integer_gcd_removed': common,
            'primitive_integer_old_cut': integer,
            'value_at_published_integer_point': evaluated,
            'rational_value_at_published_point': [rational_evaluation.numerator,
                                                  rational_evaluation.denominator],
            'exact_exclusion_of_published_point': evaluated < 0}


def export(cache, preparation, dual_path, output):
    prepared = json.loads(preparation.read_text())
    dual = json.loads(dual_path.read_text())
    assert dual['exact_exclusion'] and dual['case_index'] == 0
    assert digest(preparation) == dual['preparation_sha256']
    assert digest(cache) == dual['reduced_cache_sha256'] == prepared['reduced_cache_sha256']
    point = published_point()
    with cache.open('rb') as stream:
        data, cores, scale, inj, induced = pickle.load(stream)
    assert scale == 3628800 and induced.shape == (48965, 550)
    rows = []
    for item in dual['exact_reconstruction']['row_multipliers']:
        i, divisor = item['catalogue_type'], item['primitive_divisor']
        form = [(j, int(value)) for j, value in enumerate(induced[i]) if value]
        constant = sum(int(induced[i, j])*x for j, x in enumerate(point))
        assert divisor == reduce(gcd, [abs(constant)]+[abs(int(v)) for v in induced[i, 58:]])
        rows.append({'catalogue_type': i, 'graph_rows': list(data[0][i]),
                     'primitive_divisor': divisor, 'original_weight': item['multiplier'],
                     'original_form': form})
    old_types = [None]+cores[:57]
    old_graphs = [{'coordinate': j+1, 'catalogue_type': i, 'graph_rows': list(data[0][i]),
                   'automorphisms': data[2][i]} for j, i in enumerate(cores[:57])]
    del data, inj, induced
    upper = [1]+[b['ordinary_count_upper_bound'] for b in prepared['upper_bounds']]
    baseline = derive(rows, [r['original_weight'] for r in rows], upper, point)
    assert baseline['rational_value_at_published_point'] == [
        dual['exact_reconstruction']['aggregate']['maximum_over_exact_box'], 1]
    assert baseline['exact_exclusion_of_published_point']
    # All operations are integer; this is nearest-integer rounding of36w/1000.
    weights36 = [(36*r['original_weight']+500)//1000 for r in rows]
    simplified = derive(rows, weights36, upper, point)
    chosen = simplified if simplified['exact_exclusion_of_published_point'] else baseline
    needed_bounds = sorted({j for result in (baseline, simplified)
                            for j, _, _ in result['new_positive_coefficients_eliminated_by_bounds']})
    result = {'status': 'exact universal order-nine-core cut exported',
              'source_sha256': digest(Path(__file__)),
              'preparation_sha256': digest(preparation), 'dual_certificate_sha256': digest(dual_path),
              'reduced_cache_sha256': prepared['reduced_cache_sha256'],
              'count_scale': scale, 'published_integer_point': point,
              'old_coordinate_types': old_types, 'old_core_graphs': old_graphs,
              'induced_count_forms': rows,
              'needed_upper_bound_records': [prepared['upper_bounds'][j-1] for j in needed_bounds],
              'baseline': baseline, 'denominator36_simplification': simplified,
              'selected_cut': 'denominator36_simplification' if chosen is simplified else 'baseline',
              'scope': 'The selected58-entry integer dot product is nonnegative for every SRG(99,14,1,2) count vector. It is negative at the published point; it does not exclude all grid-free count vectors.',
              'model_forms_checked_against_exact_cache': True,
              'solver_called': False}
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'selected_cut': result['selected_cut'],
                      'baseline_upper_bounds': len(baseline['new_positive_coefficients_eliminated_by_bounds']),
                      'simplified_upper_bounds': len(simplified['new_positive_coefficients_eliminated_by_bounds']),
                      'simplified_lower_bounds': len(simplified['new_negative_coefficients_eliminated_by_nonnegativity']),
                      'simplified_value': simplified['value_at_published_integer_point'],
                      'selected_cut_coefficients': chosen['primitive_integer_old_cut']}, indent=2), flush=True)
    return result


def replay(path):
    saved = json.loads(path.read_text())
    assert saved['source_sha256'] == digest(Path(__file__))
    assert saved['published_integer_point'] == published_point()
    upper = [None]*550
    for bound in saved['needed_upper_bound_records']:
        upper[bound['coordinate']] = bound['ordinary_count_upper_bound']
    for label in ('baseline', 'denominator36_simplification'):
        expected = saved[label]
        actual = derive(saved['induced_count_forms'], expected['row_weights'], upper,
                        saved['published_integer_point'])
        assert actual == expected
    selected = saved[saved['selected_cut']]
    assert selected['exact_exclusion_of_published_point']
    print(json.dumps({'status': 'exact exported-row cut algebra replay PASS',
                      'selected_cut': saved['selected_cut'],
                      'upper_bounds_used': len(selected['new_positive_coefficients_eliminated_by_bounds']),
                      'value_at_published_point': selected['value_at_published_integer_point'],
                      'scope': 'Cached-form provenance is bound to export; this replay checks the saved exact row algebra.'}, indent=2), flush=True)
    return selected


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    make = sub.add_parser('export')
    for name in ('cache', 'preparation', 'dual', 'output'):
        make.add_argument('--'+name, type=Path, required=True)
    check = sub.add_parser('replay')
    check.add_argument('certificate', type=Path)
    args = parser.parse_args()
    if args.command == 'export':
        export(args.cache, args.preparation, args.dual, args.output)
    else:
        replay(args.certificate)
