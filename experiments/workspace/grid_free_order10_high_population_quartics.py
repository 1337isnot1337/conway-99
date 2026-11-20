"""Exact bounded-integer quartics for populations of high-mask classes.

Every population bound comes from nonnegative outside common-neighbor
contributions to original root-pair quotas. All polynomial expectations
use only frozen moments through degree four. Preparation and point scan
are separate; a negative form still needs fresh literal-product replay.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from math import comb, factorial, gcd
from pathlib import Path
import pickle
import resource
import signal
import struct
import time

from threadpoolctl import threadpool_limits

import grid_free_order10_four_boolean_scan as old


ROOT, LOGS = old.ROOT, old.LOGS
OLD_SHA = '5a97b204d8830af614f22c6e72f6ca4c120ec5c6a31320b4b8841c7e0ce19286'
STIRLING = ((1, 0, 0, 0, 0), (0, 1, 0, 0, 0),
            (0, 1, 1, 0, 0), (0, 1, 3, 1, 0), (0, 1, 7, 6, 1))
MAX_FORMS = 4


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def multiply(a, b):
    c = [0]*(len(a)+len(b)-1)
    for i, x in enumerate(a):
        for j, y in enumerate(b):
            c[i+j] += x*y
    while len(c) > 1 and c[-1] == 0:
        c.pop()
    return c


def polynomials(upper):
    result = {(1,), (0, 1), (upper, -1), (0, upper, -1)}
    for i in range(upper):
        pair = multiply([-i, 1], [-i-1, 1])
        for j in range(i, upper):
            result.add(tuple(multiply(pair, multiply([-j, 1], [-j-1, 1]))))
        result.add(tuple(multiply([0, upper, -1], pair)))
    return [list(p) for p in sorted(result)]


def falling_coefficients(polynomial):
    assert len(polynomial) <= 5
    return [factorial(j)*sum(polynomial[k]*STIRLING[k][j]
                             for k in range(j, len(polynomial))) for j in range(5)]


def value(polynomial, x):
    return sum(c*x**k for k, c in enumerate(polynomial))


def root_families(record):
    high, rows = record['high_masks'], record['root_rows']
    assert len(rows) == 6
    quotas = {(i, j): 2-((rows[i] >> j)&1)-(rows[i]&rows[j]).bit_count()
              for i, j in combinations(range(6), 2)}
    assert min(quotas.values()) >= 0
    specifications = [('all_high', tuple(high))]
    specifications += [(f'degree_equals_{d}', tuple(h for h in high if h.bit_count() == d))
                       for d in range(3, 7)]
    specifications += [(f'degree_at_least_{d}', tuple(h for h in high if h.bit_count() >= d))
                       for d in range(4, 7)]
    merged = {}
    for label, family in specifications:
        if family:
            merged.setdefault(family, []).append(label)
    families = []
    for family, labels in merged.items():
        bounds = []
        for subset in range(64):
            positions = [i for i in range(6) if subset >> i & 1]
            minimum = min(comb((h&subset).bit_count(), 2) for h in family)
            quota = sum(quotas[i, j] for i, j in combinations(positions, 2))
            if minimum:
                bounds.append({'core_subset_mask': subset, 'pair_quota_sum': quota,
                               'minimum_contribution_per_selected_class': minimum,
                               'integer_upper_bound': quota//minimum})
        assert bounds and bounds[-1]['core_subset_mask'] == 63
        upper = min(len(family), *(b['integer_upper_bound'] for b in bounds))
        assert 0 <= upper <= 10
        polys = polynomials(upper)
        assert all(value(p, x) >= 0 for p in polys for x in range(upper+1))
        families.append({'family_labels': labels, 'high_masks': list(family),
                         'upper_bound': upper, 'binary_class_count_bound': len(family),
                         'all_positive_pair_capacity_bounds': bounds,
                         'polynomials': polys})
    return {'root_type': record['root_type'], 'root_rows': rows,
            'outside_common_neighbor_pair_quotas': [[i, j, q] for (i, j), q in quotas.items()],
            'families': families, 'all_empty_mask_families_omitted_by_domain_only': True}


def controls():
    checked = identity = 0
    for upper in range(11):
        for polynomial in polynomials(upper):
            beta = falling_coefficients(polynomial)
            for x in range(upper+1):
                expected = value(polynomial, x)
                assert expected >= 0
                assert expected == sum(beta[j]*comb(x, j) for j in range(5))
                checked += 1
            # Integer mixtures test normalization of unnormalized moments.
            for masses in ([1]*(upper+1), [(x*x+3*x+1) % 7 for x in range(upper+1)]):
                elementary = [sum(masses[x]*comb(x, j) for x in range(upper+1)) for j in range(5)]
                observed = sum(beta[j]*elementary[j] for j in range(5))
                assert observed == sum(masses[x]*value(polynomial, x) for x in range(upper+1)) >= 0
                identity += 1
    # On the actual9-rook graph, every core subset has the claimed pair inventory.
    adjacent = lambda a, b: a != b and (a//3 == b//3 or a % 3 == b % 3)
    rook = 0
    for core in combinations(range(9), 6):
        outside = [v for v in range(9) if v not in core]
        rows = [sum(1 << j for j, v in enumerate(core) if adjacent(u, v)) for u in core]
        for subset in range(64):
            selected = [i for i in range(6) if subset >> i & 1]
            lhs = sum(comb(sum(adjacent(v, core[i]) for i in selected), 2) for v in outside)
            rhs = sum(2-int(adjacent(core[i], core[j]))-(rows[i]&rows[j]).bit_count()
                      for i, j in combinations(selected, 2))
            assert lhs == rhs
            rook += 1
    return {'literal_polynomial_and_falling_basis_checks': checked,
            'integer_distribution_controls': identity,
            'actual_rook9_core_subset_pair_inventory_controls': rook,
            'optimizer_or_solver_called': False}


def preparation():
    assert old.domains.digest(Path(old.__file__)) == OLD_SHA
    assert old.domains.digest(old.DOMAIN) == old.DOMAIN_SHA
    ledger = old.read(old.DOMAIN)
    assert ledger['source_sha256'] == old.domains.digest(Path(old.domains.__file__))
    assert ledger['all_allowed_high_masks_retained'] and not ledger['point_or_zero_pruning']
    roots = [root_families(record) for record in ledger['roots']]
    assert [r['root_type'] for r in roots] == list(range(38, 100))
    return {'status': 'complete bounded high-population quartic family prepared; no point scan',
            'source_sha256': old.domains.digest(Path(__file__)), 'contraction_helper_sha256': OLD_SHA,
            'domain_sha256': old.DOMAIN_SHA, 'point_sha256_for_future_scan': old.POINT_SHA,
            'cache_parts': ledger['cache_parts'], 'roots': roots,
            'family_count': sum(len(r['families']) for r in roots),
            'polynomial_count': sum(len(f['polynomials']) for r in roots for f in r['families']),
            'controls': controls(), 'maximum_scan_seconds': 60,
            'maximum_exported_negative_forms': MAX_FORMS,
            'point_loaded': False, 'product_tensors_loaded': False,
            'new_tensors_or_reduction_generated': False,
            'negative_form_requires_fresh_literal_product_replay': True,
            'component_or_graph_excluded': False}


def export_form(family, polynomial, record, tensor, automorphisms, counts, expected):
    beta = falling_coefficients(polynomial)
    singles = dict(record['single_flag_positions'])
    pairs = {tuple(item['masks']): item['flag_positions'] for item in record['pair_flag_positions']}
    row_weights = Counter()
    reference_hash = hashlib.sha256()
    visited = 0
    for degree, weight in enumerate(beta):
        if not weight:
            continue
        for masks in combinations(family['high_masks'], degree):
            references = old.domains.monomial_rows(masks, singles, pairs)
            reference_hash.update(canonical([degree, weight, list(masks), references]))
            visited += 1
            for row in references:
                row_weights[row] += weight
    labelled = Counter()
    for row, weight in row_weights.items():
        for k in range(tensor.indptr[row], tensor.indptr[row+1]):
            labelled[int(tensor.indices[k])] += weight*int(tensor.data[k])
    induced = {i: c*automorphisms[i] for i, c in sorted(labelled.items()) if c}
    actual = sum(c*counts[i] for i, c in induced.items())
    assert actual == expected < 0
    divisor = gcd(*map(abs, induced.values()))
    assert divisor > 0 and expected % divisor == 0
    return {'root_type': record['root_type'], 'family_labels': family['family_labels'],
            'high_masks': family['high_masks'], 'upper_bound': family['upper_bound'],
            'ordinary_power_coefficients': polynomial, 'squarefree_degree_coefficients': beta,
            'complete_monomial_reference_sha256': reference_hash.hexdigest(),
            'monomials_with_nonzero_degree_coefficient': visited,
            'weighted_cached_product_rows': [[r, c] for r, c in sorted(row_weights.items()) if c],
            'primitive_induced_count_form': [[i, c//divisor] for i, c in induced.items()],
            'coefficient_gcd': divisor, 'exact_labelled_value': expected,
            'primitive_value_at_integer_witness': expected//divisor,
            'independent_literal_product_replay_complete': False, 'optimizer_eligible': False}


def scan(prepared, output, seconds):
    assert prepared == preparation()
    ledger, counts, catalogue = old.inputs()
    automorphisms = [int(a) for a in catalogue[2]]
    embeddings = [a*c for a, c in zip(automorphisms, counts)]
    by_root = {r['root_type']: r for r in ledger['roots']}
    domains = {r['root_type']: r for r in prepared['roots']}
    result = {'status': 'running exact high-population quartic scan',
              'source_sha256': old.domains.digest(Path(__file__)),
              'preparation': prepared, 'root_records': [], 'negative_forms': [],
              'optimizer_or_solver_called': False, 'component_or_graph_excluded': False}
    current, error, timed_out = None, None, False
    started = time.monotonic()
    def deadline(_signal, _frame):
        raise TimeoutError('bounded high-population quartic scan')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        for _, blocks in old.domains.cache_parts():
            for root, flags, tensor in blocks:
                current = int(root)
                record = by_root[current]
                assert len(flags) == record['cached_flag_count']
                assert [f['masks'][0] for f in flags if f['size'] == 1] == record['high_masks']
                values, bounds = old.cached_values(tensor, embeddings)
                singles = dict(record['single_flag_positions'])
                pairs = {tuple(item['masks']): item['flag_positions'] for item in record['pair_flag_positions']}
                moments, stream = {}, hashlib.sha256()
                for degree in range(5):
                    for masks in combinations(record['high_masks'], degree):
                        references = old.domains.monomial_rows(masks, singles, pairs)
                        stream.update(struct.pack('<qq', degree, len(references)))
                        stream.update(struct.pack('<'+'q'*degree, *masks))
                        stream.update(struct.pack('<'+'q'*len(references), *references))
                        moments[masks] = sum(int(values[row]) for row in references)
                assert stream.hexdigest() == record['monomial_product_row_reference_sha256']
                assert moments[()] == embeddings[current]
                families, pending_forms = [], []
                for family in domains[current]['families']:
                    elementary = [sum(moments[T] for T in combinations(family['high_masks'], k)) for k in range(5)]
                    observed = [sum(c*e for c, e in zip(falling_coefficients(p), elementary)) for p in family['polynomials']]
                    negatives = [i for i, v in enumerate(observed) if v < 0]
                    for i in negatives:
                        if len(result['negative_forms'])+len(pending_forms) >= MAX_FORMS:
                            break
                        pending_forms.append(export_form(family, family['polynomials'][i],
                            record, tensor, automorphisms, counts, observed[i]))
                    families.append({'family_labels': family['family_labels'],
                        'upper_bound': family['upper_bound'], 'elementary_moment_sums': elementary,
                        'all_polynomial_values': observed, 'negative_polynomial_indices': negatives})
                blocked = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
                try:
                    result['root_records'].append({'root_type': current, 'families': families, 'arithmetic_bounds': bounds})
                    result['negative_forms'].extend(pending_forms)
                    current = None
                finally:
                    signal.pthread_sigmask(signal.SIG_SETMASK, blocked)
    except TimeoutError:
        timed_out = True
    except Exception as problem:
        error = repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    result['root_records'].sort(key=lambda r: r['root_type'])
    complete = [r['root_type'] for r in result['root_records']] == list(range(38, 100)) and not error and not timed_out
    families = [f for r in result['root_records'] for f in r['families']]
    result.update(status='complete exact high-population quartic scan' if complete else 'UNKNOWN: incomplete high-population quartic scan',
        complete=complete, error=error, timed_out=timed_out, unfinished_root=current,
        family_count=len(families), polynomial_count=sum(len(f['all_polynomial_values']) for f in families),
        negative_polynomials=sum(len(f['negative_polynomial_indices']) for f in families),
        scan_seconds=time.monotonic()-started, peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    if complete:
        assert result['family_count'] == prepared['family_count']
        assert result['polynomial_count'] == prepared['polynomial_count']
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('preparation', 'root_records', 'negative_forms')}, indent=2))
    print('output_sha256', old.domains.digest(output))
    return int(error is not None)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    assert 0 < args.seconds <= 60
    if args.prepare:
        assert not args.preparation.exists()
        result = preparation()
        args.preparation.write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({k: v for k, v in result.items() if k != 'roots'}, indent=2))
        print('output_sha256', old.domains.digest(args.preparation))
    else:
        assert args.output is not None and not args.output.exists()
        with threadpool_limits(limits=1):
            raise SystemExit(scan(old.read(args.preparation), args.output, args.seconds))
