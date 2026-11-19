"""Independent preparation arithmetic and source gate; no point/tensor scan."""

import ast
import gzip
import hashlib
from itertools import combinations
import json
from math import comb, factorial
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT/'experiments/workspace'
LOGS = ROOT/'experiments/logs/moments-and-counts'
SOURCE = WORK/'grid_free_order10_high_population_quartics.py'
PREPARATION = LOGS/'order10-high-population-quartics-preparation.json'
DOMAIN = LOGS/'order10-four-boolean-domains.json.gz'
BINDINGS = {
    SOURCE: 'c8b211fb25cf084260c968bbb5ddb0ee6d8f44eea711283d6f7ba592b8c56985',
    PREPARATION: 'f60c7989fe42817fa343c7aaf24111e89d4f0caf7e0ea445ea38d06da69fc7e7',
    DOMAIN: '5fd508dba5bcda5aeb8231ab39dd6b68df5c55ffffebb98b7344e874155bef35',
    WORK/'grid_free_order10_four_boolean_scan.py': '5a97b204d8830af614f22c6e72f6ca4c120ec5c6a31320b4b8841c7e0ce19286'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def evaluate(coefficients, x):
    result = 0
    for c in reversed(coefficients):
        result = result*x+c
    return result


def root_polynomial(roots):
    n = len(roots)
    return [(-1)**(n-k)*sum(__import__('math').prod(roots[i] for i in indices)
                              for indices in combinations(range(n), n-k)) for k in range(n+1)]


def listed_polynomials(upper):
    answer = {(1,), (0, 1), (upper, -1), (0, upper, -1)}
    for i in range(upper):
        for j in range(i, upper):
            answer.add(tuple(root_polynomial([i, i+1, j, j+1])))
        answer.add(tuple(-c for c in root_polynomial([0, upper, i, i+1])))
    return [list(p) for p in sorted(answer)]


def differences(coefficients):
    values = [evaluate(coefficients, x) for x in range(5)]
    result = []
    while values:
        result.append(values[0])
        values = [b-a for a, b in zip(values, values[1:])]
    return result


def audit():
    started = time.monotonic()
    for path, expected in BINDINGS.items():
        assert digest(path) == expected
    prepared, old = read(PREPARATION), read(DOMAIN)
    assert prepared['source_sha256'] == BINDINGS[SOURCE]
    assert prepared['domain_sha256'] == BINDINGS[DOMAIN]
    assert prepared['cache_parts'] == old['cache_parts']
    for item in prepared['cache_parts']:
        assert digest(ROOT/item['path']) == item['sha256']
    assert old['all_allowed_high_masks_retained'] and not old['point_or_zero_pruning']
    assert prepared['point_loaded'] is prepared['product_tensors_loaded'] is False
    assert [r['root_type'] for r in prepared['roots']] == [r['root_type'] for r in old['roots']] == list(range(38, 100))
    tree = ast.parse(SOURCE.read_text())
    stirling = next(ast.literal_eval(n.value) for n in tree.body if isinstance(n, ast.Assign)
                    and isinstance(n.targets[0], ast.Name) and n.targets[0].id == 'STIRLING')
    family_count = polynomial_count = bound_count = point_values = identity_values = 0
    for record, prior in zip(prepared['roots'], old['roots']):
        rows, high = prior['root_rows'], prior['high_masks']
        assert record['root_rows'] == rows and len(rows) == 6
        quotas = {(i, j): 2-int(bool(rows[i] >> j & 1))-(rows[i]&rows[j]).bit_count()
                  for i, j in combinations(range(6), 2)}
        assert min(quotas.values()) >= 0
        assert record['outside_common_neighbor_pair_quotas'] == [[i, j, q] for (i, j), q in quotas.items()]
        requested = [('all_high', high)]
        requested += [(f'degree_equals_{d}', [h for h in high if h.bit_count() == d]) for d in range(3, 7)]
        requested += [(f'degree_at_least_{d}', [h for h in high if h.bit_count() >= d]) for d in range(4, 7)]
        merged = {}
        for label, family in requested:
            if family:
                merged.setdefault(tuple(family), []).append(label)
        assert len(merged) == len(record['families'])
        for family, (masks, labels) in zip(record['families'], merged.items()):
            assert family['high_masks'] == list(masks) and family['family_labels'] == labels
            all_bounds = []
            for subset in range(64):
                vertices = [i for i in range(6) if subset >> i & 1]
                q = sum(quotas[i, j] for i, j in combinations(vertices, 2))
                contributions = [sum(int(bool(mask >> i & 1) and bool(mask >> j & 1))
                                     for i, j in combinations(vertices, 2)) for mask in masks]
                lower = min(contributions)
                assert contributions == [comb((mask&subset).bit_count(), 2) for mask in masks]
                if lower:
                    all_bounds.append({'core_subset_mask': subset, 'pair_quota_sum': q,
                        'minimum_contribution_per_selected_class': lower, 'integer_upper_bound': q//lower})
            assert all_bounds == family['all_positive_pair_capacity_bounds']
            upper = min(len(masks), *(b['integer_upper_bound'] for b in all_bounds))
            assert upper == family['upper_bound'] and 0 <= upper <= 10
            assert family['binary_class_count_bound'] == len(masks)
            assert family['polynomials'] == listed_polynomials(upper)
            for polynomial in family['polynomials']:
                beta = differences(polynomial)
                converted = [factorial(j)*sum(polynomial[k]*stirling[k][j]
                             for k in range(j, len(polynomial))) for j in range(5)]
                assert beta == converted
                for x in range(upper+1):
                    value = evaluate(polynomial, x)
                    assert value >= 0 and value == sum(beta[j]*comb(x, j) for j in range(5))
                    point_values += 1
                for weights in ([1]*(upper+1), [2*x+1 for x in range(upper+1)]):
                    elementary = [sum(w*comb(x, j) for x, w in enumerate(weights)) for j in range(5)]
                    assert sum(b*e for b, e in zip(beta, elementary)) == sum(w*evaluate(polynomial, x) for x, w in enumerate(weights)) >= 0
                    identity_values += 1
            bound_count += len(all_bounds)
            family_count += 1; polynomial_count += len(family['polynomials'])
    assert (family_count, polynomial_count) == (prepared['family_count'], prepared['polynomial_count']) == (153, 3583)
    report = {'status': 'PASS: independent high-population quartic preparation arithmetic and source review',
        'audit_source_sha256': digest(Path(__file__)), 'subject_source_sha256': BINDINGS[SOURCE],
        'preparation_sha256': BINDINGS[PREPARATION], 'domain_sha256': BINDINGS[DOMAIN],
        'root_domains_checked': 62, 'merged_population_families_checked': family_count,
        'positive_core_subset_capacity_bounds_recomputed': bound_count,
        'listed_polynomials_reconstructed': polynomial_count,
        'literal_nonnegativity_and_binomial_basis_checks': point_values,
        'integer_distribution_normalization_checks': identity_values,
        'source_review': [
            'For each core subset, total outside pair contributions equal the residual common-neighbor quota sum.',
            'All omitted outside classes have nonnegative contributions, so the minimum selected-class contribution yields the stated upper bound.',
            'Every high class is binary; duplicate family labels are merged without changing the selected mask domain.',
            'The polynomial list contains only stated necessary inequalities; no complete cone for small upper bounds is claimed.',
            'Finite differences independently agree with the factorial/Stirling conversion to elementary squarefree moments.',
            'Labelled product entries use count times automorphism order; all subsequent elementary and polynomial arithmetic uses Python integers.',
            'The frozen contraction guards and complete monomial-reference hash are checked before point polynomial evaluation.',
            'Negative extraction exactly reconstructs signed cached rows and automorphism-weighted induced forms, with a positive gcd.',
            'Selected negative forms remain optimizer-ineligible until fresh literal-product replay.',
            'Completed roots and their sampled forms are committed together under a blocked alarm signal; an unfinished root is named without counting its partial results.'],
        'timer_scope': 'The 60-second alarm covers cache contraction and scan after preparation/control recomputation and point input loading.',
        'total_invocation_wall_time_is_not_the_60_second_timer': True,
        'subject_modules_imported': False, 'count_point_loaded': False, 'product_tensors_loaded': False,
        'optimizer_or_eigensystem_called': False, 'point_scan_called': False,
        'whole_graph_or_component_excluded': False, 'seconds': time.monotonic()-started}
    output = LOGS/'order10-high-population-quartics-independent-review.json'
    assert not output.exists()
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2)); print('output_sha256', digest(output))


if __name__ == '__main__':
    audit()
