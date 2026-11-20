"""Complete universal packing list and all 62 root domains; no count point.

The independent enumerator uses fifteen integer residual capacities, not
the two-bitset state of the frozen C++ census.  Pairwise mask intersections
above two are separately excluded with explicit witnesses.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from pathlib import Path
import resource
import signal
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT/'experiments/workspace'
LOGS = ROOT/'experiments/logs/moments-and-counts'
DOMAIN = LOGS/'order10-four-boolean-domains.json.gz'
DOMAIN_SHA = '5fd508dba5bcda5aeb8231ab39dd6b68df5c55ffffebb98b7344e874155bef35'
COUNT = LOGS/'order10-high-mask-packing-count01.json'
COUNT_SHA = '9637c67a8e1d729a9ddc1867ca4c563e3f3f35555e6d1c1c1514df6c06e5f18d'
SCOPE = LOGS/'order10-high-mask-packing-scope.json'
SCOPE_SHA = 'fd7544082a7186191abe92136a58ba7e69918bf455edec7f37a3ed4f933843a3'
PAIRS = tuple(combinations(range(6), 2))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def pair_coordinates(mask):
    return tuple(p for p, (i, j) in enumerate(PAIRS) if mask >> i & 1 and mask >> j & 1)


def integer_quota_enumeration(high):
    support = [pair_coordinates(h) for h in high]
    remaining = [2]*15
    codes = []
    candidate_tests = 0
    def visit(first, code):
        nonlocal candidate_tests
        codes.append(code)
        for at in range(first, len(high)):
            candidate_tests += 1
            if any(remaining[p] == 0 for p in support[at]):
                continue
            for p in support[at]:
                remaining[p] -= 1
            visit(at+1, code | (1 << at))
            for p in support[at]:
                remaining[p] += 1
    visit(0, 0)
    assert remaining == [2]*15
    assert len(codes) == len(set(codes))
    return sorted(codes), candidate_tests


def attach(rows, mask):
    n = len(rows)
    return tuple(row | (((mask >> i)&1) << n) for i, row in enumerate(rows))+(mask,)


def caps(rows):
    return all((rows[i]&rows[j]).bit_count()+((rows[i] >> j)&1) <= 2
               for i in range(len(rows)) for j in range(i))


def outside_pair_controls(high):
    count, forbidden_pairs = 0, []
    for i, j in combinations(range(len(high)), 2):
        a, b = high[i], high[j]
        common = (a&b).bit_count()
        for edge in (0, 1):
            rows = attach(attach((0,)*6, a), b | (edge << 6))
            assert (rows[6]&rows[7]).bit_count() == common
            assert caps(rows) == (common+edge <= 2)
            count += 1
        if common >= 3:
            forbidden_pairs.append([i, j, a&b])
    return {'literal_two_vertex_extensions_checked': count,
            'incompatible_global_class_pairs': forbidden_pairs,
            'proof': 'Two selected classes with at least three common root neighbors violate the outside-pair common-neighbor cap regardless of their mutual adjacency.',
            'outside_adjacency_value_fixed_in_domain': False}


def prepare(output, atoms_path, usage_path, result):
    assert digest(DOMAIN) == DOMAIN_SHA and digest(COUNT) == COUNT_SHA and digest(SCOPE) == SCOPE_SHA
    domain, frozen, scope = read(DOMAIN), read(COUNT), read(SCOPE)
    assert frozen['complete'] and frozen['result']['complete'] and not frozen['result']['timed_out']
    assert digest(WORK/'grid_free_order10_high_mask_packing_count.cpp') == frozen['cpp_source_sha256']
    assert digest(WORK/'grid_free_order10_high_mask_packing_count.py') == frozen['source_sha256']
    assert digest(WORK/'grid_free_order10_high_mask_packing_scope.py') == scope['source_sha256']
    assert domain['all_allowed_high_masks_retained'] and not domain['point_or_zero_pruning']
    assert digest(WORK/'grid_free_order10_four_boolean_domains.py') == domain['source_sha256']
    high = [h for h in range(64) if h.bit_count() >= 3]
    assert high == frozen['high_masks'] == domain['roots'][0]['high_masks'] and len(high) == 42
    codes, tests = integer_quota_enumeration(high)
    assert len(codes) == frozen['result']['packings_visited'] == 132062
    assert tests == frozen['result']['candidate_tests'] == 1346729
    population = Counter(code.bit_count() for code in codes)
    assert [population[k] for k in range(11)] == frozen['result']['population_size_counts']
    assert codes[0] == 0 and all(0 <= code < (1 << 42) for code in codes)
    array = np.asarray(codes, dtype='<u8')
    assert np.all(array[1:] > array[:-1])

    # Independent coordinatewise accumulation; at most 42 additions in
    # each uint8 coordinate, so no fixed-width wraparound is possible.
    usage = np.zeros((len(codes), 15), dtype=np.uint8)
    for i, mask in enumerate(high):
        member = ((array >> np.uint64(i)) & np.uint64(1)).astype(np.uint8)
        for pair in pair_coordinates(mask):
            usage[:, pair] += member
    assert int(usage.max()) <= 2
    used = usage.sum(axis=1, dtype=np.uint64)
    observed_usage = np.bincount(used.astype(np.int64), minlength=31).tolist()
    assert observed_usage == frozen['result']['pair_consumption_counts']
    pair_bits = np.asarray([1 << p for p in range(15)], dtype=np.uint16)
    once = ((usage > 0).astype(np.uint16)*pair_bits).sum(axis=1, dtype=np.uint32).astype(np.uint16)
    twice = ((usage == 2).astype(np.uint16)*pair_bits).sum(axis=1, dtype=np.uint32).astype(np.uint16)
    assert np.all((once & twice) == twice)
    atoms_path.write_bytes(array.tobytes(order='C'))
    assert atoms_path.stat().st_size == 1056496
    np.savez_compressed(usage_path, pair_usage=usage, once=once, twice=twice)
    result.update(universal_census_complete=True, universal_atom_count=len(codes),
                  independent_candidate_tests=tests,
                  population_size_counts=[population[k] for k in range(11)],
                  independent_pair_consumption_counts=observed_usage,
                  atoms={'path': str(atoms_path.relative_to(ROOT)), 'sha256': digest(atoms_path),
                         'format': 'sorted little-endian uint64; each bit is a universal high-class index',
                         'bytes': atoms_path.stat().st_size},
                  pair_usage={'path': str(usage_path.relative_to(ROOT)), 'sha256': digest(usage_path),
                              'shape': list(usage.shape), 'maximum_entry': 2})

    control = outside_pair_controls(high)
    visible = np.ones(len(codes), dtype=bool)
    witnesses = np.full((len(codes), 2), -1, dtype=np.int16)
    for i, j, _ in control['incompatible_global_class_pairs']:
        bad = ((array & np.uint64(1 << i)) != 0)&((array & np.uint64(1 << j)) != 0)
        first = bad & visible
        witnesses[first, 0] = i; witnesses[first, 1] = j
        visible[bad] = False
    removed = np.flatnonzero(~visible)
    assert np.all(witnesses[removed] >= 0)
    assert np.all(witnesses[visible] == -1)
    removed_records = [[int(i), int(witnesses[i, 0]), int(witnesses[i, 1])] for i in removed]
    for atom, i, j in removed_records:
        assert codes[atom] >> i & 1 and codes[atom] >> j & 1
        assert (high[i]&high[j]).bit_count() >= 3
    result.update(outside_pair_controls=control,
                  universal_visible_atom_ids=np.flatnonzero(visible).tolist(),
                  universal_removed_pair_cap_witnesses=removed_records)

    index = {mask: i for i, mask in enumerate(high)}
    root_records = result['roots']
    for record, bounded in zip(domain['roots'], scope['roots']):
        root, rows = record['root_type'], tuple(record['root_rows'])
        allowed = [h for h in high if caps(attach(rows, h))]
        assert allowed == record['high_masks']
        quotas = [2-((rows[i] >> j)&1)-(rows[i]&rows[j]).bit_count() for i, j in PAIRS]
        assert quotas == bounded['pair_quotas'] and all(q in (0, 1, 2) for q in quotas)
        allowed_bits = sum(1 << index[h] for h in allowed)
        forbidden_bits = ((1 << 42)-1) ^ allowed_bits
        membership = (array & np.uint64(forbidden_bits)) == 0
        literal_quota = (usage <= np.asarray(quotas, dtype=np.uint8)).all(axis=1)
        zero = sum(1 << p for p, q in enumerate(quotas) if q == 0)
        one = sum(1 << p for p, q in enumerate(quotas) if q == 1)
        bit_quota = ((once & np.uint16(zero)) == 0)&((twice & np.uint16(one)) == 0)
        assert np.array_equal(literal_quota, bit_quota)
        baseline = np.flatnonzero(membership & literal_quota)
        filtered = baseline[visible[baseline]]
        excluded = baseline[~visible[baseline]]
        assert len(baseline) == len(filtered)+len(excluded)
        assert len(baseline) <= bounded['weighted_subset_upper_bound_after_size_filter']
        assert len(baseline) and baseline[0] == filtered[0] == 0
        baseline_hist = Counter(codes[int(i)].bit_count() for i in baseline)
        visible_hist = Counter(codes[int(i)].bit_count() for i in filtered)
        root_records.append({'root_type': root, 'root_rows': list(rows), 'high_masks': allowed,
            'global_class_indices': [index[h] for h in allowed], 'allowed_global_class_bits': allowed_bits,
            'pair_quotas': quotas, 'pair_quota_atom_ids': baseline.tolist(),
            'visible_pair_cap_atom_ids': filtered.tolist(), 'removed_by_outside_pair_cap_atom_ids': excluded.tolist(),
            'pair_quota_atom_count': len(baseline), 'visible_pair_cap_atom_count': len(filtered),
            'pair_quota_population_counts': [baseline_hist[k] for k in range(11)],
            'visible_population_counts': [visible_hist[k] for k in range(11)],
            'integer_coordinate_and_two_bitset_filter_results_identical': True,
            'complete': True})
    assert [r['root_type'] for r in root_records] == list(range(38, 100))
    assert root_records[0]['pair_quota_atom_ids'] == list(range(132062))
    result.update(complete=True,
        status='complete universal list, independent census validation and all62 root domains',
        total_pair_quota_root_atoms=sum(r['pair_quota_atom_count'] for r in root_records),
        total_visible_pair_cap_root_atoms=sum(r['visible_pair_cap_atom_count'] for r in root_records),
        universal_visible_atom_count=int(np.count_nonzero(visible)),
        universal_removed_by_outside_pair_cap=int(np.count_nonzero(~visible)),
        completed_root_domains=62)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--atoms', type=Path, required=True)
    parser.add_argument('--pair-usage', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    assert 0 < args.seconds <= 60
    assert not any(p.exists() for p in (args.output, args.atoms, args.pair_usage))
    result = {'status': 'running independent packing-list and root-domain preparation',
        'source_sha256': digest(Path(__file__)), 'domain_sha256': DOMAIN_SHA,
        'frozen_Cpp_census_sha256': COUNT_SHA, 'scope_sha256': SCOPE_SHA,
        'universal_high_masks': [h for h in range(64) if h.bit_count() >= 3],
        'roots': [], 'complete': False, 'universal_census_complete': False,
        'count_point_loaded': False, 'product_tensors_loaded': False,
        'optimizer_or_new_tensor_called': False, 'outside_adjacency_imposed': False,
        'point_or_zero_pruning': False, 'graph_existence_resolved': False}
    started = time.monotonic()
    def deadline(_signum, _frame):
        raise TimeoutError('bounded independent packing-domain preparation')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    error = None
    try:
        prepare(args.output, args.atoms, args.pair_usage, result)
    except TimeoutError:
        result.update(status='UNKNOWN: incomplete packing-domain preparation', timed_out=True)
    except Exception as problem:
        error = repr(problem)
        result.update(status='ERROR: packing-domain preparation check failed', error=error)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    result.update(seconds=time.monotonic()-started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    raw = json.dumps(result, indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw)
    print(json.dumps({k: v for k, v in result.items() if k not in
        ('roots', 'outside_pair_controls', 'universal_visible_atom_ids', 'universal_removed_pair_cap_witnesses')}, indent=2))
    print('output_sha256', digest(args.output))
    raise SystemExit(int(error is not None))


if __name__ == '__main__':
    main()
