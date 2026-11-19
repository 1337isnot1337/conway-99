"""Point-independent weighted bounds and tiny controls for high-mask packings.

No full 42-mask packing census, count-point query, tensor load, or optimizer
is exposed.  Actual packing enumeration here is restricted to <=12 masks.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path
import resource
import signal
import time


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT/'experiments/workspace'
LOGS = ROOT/'experiments/logs/moments-and-counts'
DOMAIN = LOGS/'order10-four-boolean-domains.json.gz'
DOMAIN_SHA = '5fd508dba5bcda5aeb8231ab39dd6b68df5c55ffffebb98b7344e874155bef35'
PAIRS = tuple(combinations(range(6), 2))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def pair_mask(mask, pairs=PAIRS):
    return sum(1 << k for k, (i, j) in enumerate(pairs) if mask >> i & 1 and mask >> j & 1)


def capacities(rows):
    return [2-((rows[i] >> j)&1)-(rows[i]&rows[j]).bit_count() for i, j in PAIRS]


def weighted_subset_counts(weights, budget):
    """Exact 0/1 subset counts under only the total-weight constraint."""
    assert all(type(w) is int and w > 0 for w in weights) and 0 <= budget <= 30
    h = len(weights)
    dp = [[0]*(h+1) for _ in range(budget+1)]
    dp[0][0] = 1
    processed = 0
    for weight in weights:
        for total in range(budget, weight-1, -1):
            for size in range(processed+1, 0, -1):
                dp[total][size] += dp[total-weight][size-1]
        processed += 1
    return [sum(row[size] for row in dp) for size in range(h+1)]


def tiny_packings(pair_masks, quotas):
    assert len(pair_masks) <= 12 and all(q in (0, 1, 2) for q in quotas)
    once = sum(1 << p for p, q in enumerate(quotas) if q < 2)
    twice = sum(1 << p for p, q in enumerate(quotas) if q == 0)
    found, tests = set(), 0
    def visit(start, once_used, twice_used, selected):
        nonlocal tests
        assert selected not in found
        found.add(selected)
        for i in range(start, len(pair_masks)):
            tests += 1
            mask = pair_masks[i]
            if mask & twice_used:
                continue
            visit(i+1, once_used | mask, twice_used | (once_used & mask), selected | (1 << i))
    visit(0, once, twice, 0)
    direct = set()
    for selected in range(1 << len(pair_masks)):
        use = [sum(int(bool(selected >> i & 1) and bool(mask >> p & 1))
                   for i, mask in enumerate(pair_masks)) for p in range(len(quotas))]
        if all(a <= q for a, q in zip(use, quotas)):
            direct.add(selected)
    assert found == direct
    counts = Counter(s.bit_count() for s in found)
    return {'masks': len(pair_masks), 'pair_masks': pair_masks, 'quotas': quotas,
            'full_subset_assignments_checked': 1 << len(pair_masks),
            'feasible_packings': len(found), 'depth_first_candidate_tests': tests,
            'packing_counts_by_size': {str(k): counts[k] for k in sorted(counts)},
            'complete_packing_code_sha256': hashlib.sha256(canonical(sorted(found))).hexdigest()}


def controls(records):
    empty = records[0]
    assert empty['root_type'] == 38 and empty['root_rows'] == [0]*6
    with_one = next(r for r in records if 1 in capacities(r['root_rows']) and len(r['high_masks']) >= 12)
    with_zero = next(r for r in records if 0 in capacities(r['root_rows']) and len(r['high_masks']) >= 10)
    specifications = [('empty_first12', empty, empty['high_masks'][:12]),
                      ('empty_last12', empty, empty['high_masks'][-12:]),
                      ('quota_one_first12', with_one, with_one['high_masks'][:12]),
                      ('quota_zero_first10', with_zero, with_zero['high_masks'][:10])]
    result = []
    for label, record, high in specifications:
        result.append({'label': label, 'root_type': record['root_type'], 'high_masks': high,
                       **tiny_packings([pair_mask(m) for m in high], capacities(record['root_rows']))})
    pairs4 = tuple(combinations(range(4), 2))
    masks4 = [m for m in range(16) if m.bit_count() >= 3]
    for quota in (0, 1, 2):
        result.append({'label': f'synthetic_four_sites_uniform_quota_{quota}',
                       'high_masks': masks4,
                       **tiny_packings([pair_mask(m, pairs4) for m in masks4], [quota]*6)})
    return result


def root_bound(record):
    high, rows = record['high_masks'], record['root_rows']
    quotas = capacities(rows)
    assert len(rows) == 6 and all(q in (0, 1, 2) for q in quotas)
    masks = [pair_mask(h) for h in high]
    assert all(m.bit_count() == comb(h.bit_count(), 2) for h, m in zip(high, masks))
    zero = sum(1 << p for p, q in enumerate(quotas) if q == 0)
    assert all(not (m & zero) for m in masks)
    budget = sum(quotas)
    counts = weighted_subset_counts([m.bit_count() for m in masks], budget)
    size_bound = max(i for i, count in enumerate(counts) if count)
    assert size_bound <= 10
    occupancy = {'initial_once_mask': sum(1 << p for p, q in enumerate(quotas) if q < 2),
                 'initial_twice_mask': zero}
    subset_bounds = []
    if high:
        for core_subset in range(64):
            minimum = min(comb((h&core_subset).bit_count(), 2) for h in high)
            if minimum:
                total = sum(q for (i, j), q in zip(PAIRS, quotas)
                            if core_subset >> i & 1 and core_subset >> j & 1)
                subset_bounds.append({'core_subset': core_subset, 'quota_sum': total,
                                      'minimum_contribution': minimum, 'size_upper_bound': total//minimum})
        improved = min(size_bound, *(b['size_upper_bound'] for b in subset_bounds))
    else:
        improved = 0
    bound = sum(counts[:improved+1])
    return {'root_type': record['root_type'], 'root_rows': rows, 'high_masks': high,
            'pair_masks': masks, 'pair_quotas': quotas, **occupancy,
            'high_mask_count_by_degree': {str(k): sum(h.bit_count() == k for h in high) for k in range(3, 7)},
            'total_pair_budget': budget, 'weighted_subset_counts_by_size': counts,
            'total_weight_only_subset_upper_bound': sum(counts),
            'total_weight_size_bound': size_bound, 'all_core_subset_size_bounds': subset_bounds,
            'size_bound_after_core_subset_capacities': improved,
            'weighted_subset_upper_bound_after_size_filter': bound,
            'maximum_degree_at_most_four_moment_incidences_per_atom': sum(comb(improved, j) for j in range(5)),
            'full_packing_census_performed': False}


def prepare():
    assert digest(DOMAIN) == DOMAIN_SHA
    domain = read(DOMAIN)
    assert digest(WORK/'grid_free_order10_four_boolean_domains.py') == domain['source_sha256']
    assert domain['all_allowed_high_masks_retained'] and not domain['point_or_zero_pruning']
    assert [r['root_type'] for r in domain['roots']] == list(range(38, 100))
    records = [root_bound(r) for r in domain['roots']]
    universal = records[0]
    assert universal['root_rows'] == [0]*6 and len(universal['high_masks']) == 42
    assert universal['high_mask_count_by_degree'] == {'3': 20, '4': 15, '5': 6, '6': 1}
    assert universal['pair_quotas'] == [2]*15 and universal['total_pair_budget'] == 30
    assert all(set(r['high_masks']).issubset(universal['high_masks']) for r in records)
    assert all(r['weighted_subset_upper_bound_after_size_filter'] <= universal['total_weight_only_subset_upper_bound'] for r in records)
    tiny = controls(domain['roots'])
    return {'status': 'complete point-independent packing bounds and tiny enumeration controls; no full census',
        'source_sha256': digest(Path(__file__)), 'domain_sha256': DOMAIN_SHA,
        'root_count': 62, 'pair_coordinates': [list(p) for p in PAIRS], 'roots': records,
        'universal_weight_generating_polynomial': '(1+t^3)^20*(1+t^6)^15*(1+t^10)^6*(1+t^15)',
        'universal_total_pair_budget': 30,
        'universal_weight_only_subset_upper_bound': universal['total_weight_only_subset_upper_bound'],
        'universal_weight_only_counts_by_size': universal['weighted_subset_counts_by_size'],
        'sum_of_per_root_weight_and_size_upper_bounds': sum(r['weighted_subset_upper_bound_after_size_filter'] for r in records),
        'maximum_selected_high_masks': 10,
        'maximum_squarefree_moment_incidences_through_degree_four_per_atom': 386,
        'tiny_controls': tiny, 'tiny_full_subset_assignments_checked': sum(r['full_subset_assignments_checked'] for r in tiny),
        'outside_adjacency_imposed': False, 'point_or_zero_pruning': False,
        'count_point_loaded': False, 'product_tensors_loaded': False,
        'optimizer_or_new_tensor_called': False, 'full_packing_census_performed': False,
        'graph_existence_resolved': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 60
    started = time.monotonic()
    def deadline(_signum, _frame):
        raise TimeoutError('bounded packing scope preparation')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    try:
        result = prepare()
        args.output.write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({k: v for k, v in result.items() if k not in ('roots', 'tiny_controls')}, indent=2))
        print('output_sha256', digest(args.output))
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
        print('seconds', time.monotonic()-started, 'peak_rss_kib', resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)


if __name__ == '__main__':
    main()
