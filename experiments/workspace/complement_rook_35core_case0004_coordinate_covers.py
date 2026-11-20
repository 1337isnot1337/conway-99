"""Complete cheap coordinate-difference covers for case4 optional rows.

For each positive target difference, retain the necessary Boolean cover.
Identical covers are merged. Only same-target supersets are removed,
with an explicit retained subset witness for every removal. This module
measures and certifies the full family; it calls no solver.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import product
import json
from pathlib import Path
import resource
import time

import complement_rook_35core_case0004_intrinsic_rows as intrinsic


ROOT, LOGS = intrinsic.ROOT, intrinsic.LOGS
INTRINSIC_SHA = '24eb86e47e6f5a741721fe9174e7d3762bc74edd290c89d489dd5ddedb900c11'
CENSUS = LOGS / 'complement-rook-35core-case0004-intrinsic-rows.json.gz'
CENSUS_SHA = '0d1c096865678958737e34551fb55a203fd65b9dc8b0b5613bd9f1dfd26185e9'
canonical, digest = intrinsic.canonical, intrinsic.digest


def members(bits):
    answer = []
    while bits:
        low = bits & -bits
        answer.append(low.bit_length()-1)
        bits ^= low
    return answer


def controls():
    # Exact support containment implies same-target clause containment.
    checked = 0
    for small in range(16):
        for large in range(16):
            if small & ~large:
                continue
            for assignment in range(16):
                for guard in (0, 1):
                    first = not guard or bool(small & assignment)
                    second = not guard or bool(large & assignment)
                    assert not first or second
                    checked += 1
    # A genuine9-rook partial core supplies exact mixed/degree rows.
    adjacent = lambda a, b: a != b and (a//3 == b//3 or a % 3 == b % 3)
    core_sites, outside = [0, 1, 3, 4, 8], [2, 5, 6, 7]
    core = [sum(1 << j for j, b in enumerate(core_sites) if adjacent(a, b)) for a in core_sites]
    masks = [sum(1 << j for j, b in enumerate(core_sites) if adjacent(a, b)) for a in outside]
    targets = [[2-int(mask >> i & 1)-(core[i] & mask).bit_count() for i in range(5)]
               + [4-mask.bit_count()] for mask in masks]
    checked_covers = weakened = 0
    for a in range(4):
        actual = [b for b in range(4) if adjacent(outside[a], outside[b])]
        assert targets[a] == [sum(masks[b] >> i & 1 for b in actual) for i in range(5)] + [len(actual)]
        eligible = [b for b in range(4) if b != a and (masks[a] & masks[b]).bit_count() <= 1
                    and all(targets[a][i] or not (masks[b] >> i & 1) for i in range(5))
                    and all(targets[b][i] or not (masks[a] >> i & 1) for i in range(5))]
        assert set(actual) <= set(eligible)
        vectors = [mask | (1 << 5) for mask in masks]
        for i in range(6):
            for j in range(6):
                demand = targets[a][i]-targets[a][j]
                if demand <= 0:
                    continue
                cover = [b for b in eligible if vectors[b] >> i & 1 and not (vectors[b] >> j & 1)]
                assert len(set(actual) & set(cover)) >= demand
                assert cover
                checked_covers += 1
                weakened += demand > 1
    return {'complete_small_same_target_subsumption_assignments': checked,
            'rook9_positive_coordinate_cover_controls': checked_covers,
            'rook9_control_demands_weakened_to_one': weakened,
            'optimizer_or_solver_called': False}


def prepare_target(a, targets, vectors, neighbors, coordinate_supports):
    neighborhood = sum(1 << b for b in neighbors[a])
    supports = [bits & neighborhood for bits in coordinate_supports]
    origins = []
    for i in range(36):
        for j in range(36):
            demand = targets[a][i]-targets[a][j]
            if demand > 0:
                cover = supports[i] & ~supports[j]
                origins.append((i, j, demand, cover))
    unique = sorted({bits for _, _, _, bits in origins}, key=lambda bits: (bits.bit_count(), bits))
    position = {bits: i for i, bits in enumerate(unique)}
    retained = []
    cover_records = []
    for index, bits in enumerate(unique):
        witness = next((old for old in retained if unique[old] & ~bits == 0), None)
        if witness is None:
            retained.append(index)
            classification = 'retained'
        else:
            assert unique[witness] != bits and unique[witness] & ~bits == 0
            classification = 'implied_by_same_target_unit' if unique[witness] == 0 else 'implied_by_same_target_strict_subset'
        cover_records.append({'cover_bits_hex': format(bits, 'x'), 'positive_literals': bits.bit_count(),
                              'classification': classification, 'retained_subset_witness_id': witness})
    assert all(unique[i] & ~unique[j] and unique[j] & ~unique[i]
               for index, i in enumerate(retained) for j in retained[:index])
    assert all(not (bits >> a & 1) for bits in unique)
    ledger = [[i, j, demand, position[bits], demand > 1] for i, j, demand, bits in origins]
    for i, j, demand, index, weakened in ledger:
        bits = unique[index]
        assert bits == supports[i] & ~supports[j]
        assert weakened == (demand > 1)
    # Independently reconstruct the complete support of every retained
    # clause directly from neighbor coordinates. All remaining covers
    # have the exact bitmap ledger and a retained subset witness.
    representative_pair = {}
    for i, j, demand, index, weakened in ledger:
        representative_pair.setdefault(index, (i, j))
    for index in retained:
        i, j = representative_pair[index]
        expected = [b for b in neighbors[a] if vectors[b] >> i & 1 and not (vectors[b] >> j & 1)]
        assert members(unique[index]) == expected
    unit = bool(unique and unique[0] == 0)
    if unit:
        assert retained == [0]
        assert all(record['retained_subset_witness_id'] == 0 for record in cover_records[1:])
    return {'target_column': a, 'negative_guard_literal': -a-1,
            'all_positive_difference_pairs': ledger,
            'pair_record_format': ['coordinate_i', 'coordinate_j', 'positive_original_demand', 'unique_cover_id', 'demand_weakened_to_one'],
            'unique_covers': cover_records, 'retained_unique_cover_ids': retained,
            'empty_cover_forces_target_absent': unit,
            'retained_clause_count': len(retained),
            'retained_literal_count': sum(1+unique[i].bit_count() for i in retained)}


def clause_stream(certificate):
    assert certificate['complete']
    for record in certificate['records']:
        a = record['target_column']
        assert record['negative_guard_literal'] == -a-1
        for index in record['retained_unique_cover_ids']:
            bits = int(record['unique_covers'][index]['cover_bits_hex'], 16)
            assert not (bits >> a & 1)
            yield [-a-1] + [b+1 for b in members(bits)]


def calculate(seconds):
    started = time.monotonic()
    assert digest(Path(intrinsic.__file__)) == INTRINSIC_SHA and digest(CENSUS) == CENSUS_SHA
    previous = json.loads(gzip.decompress(CENSUS.read_bytes()))
    assert previous['complete'] and previous['all_optional_columns'] == 1214
    model, targets, zeros, neighbors, known = intrinsic.load()
    assert len(targets) == 1214
    vectors = [mask | (1 << 35) for mask in model['column_masks35']]
    coordinate_supports = [sum(1 << b for b, mask in enumerate(vectors) if mask >> i & 1)
                           for i in range(36)]
    records = []
    for a in range(1214):
        if time.monotonic()-started >= seconds:
            break
        records.append(prepare_target(a, targets, vectors, neighbors, coordinate_supports))
        if len(records) % 128 == 0:
            print(json.dumps({'completed_targets': len(records), 'elapsed_seconds': time.monotonic()-started}), flush=True)
    complete = len(records) == 1214
    units = [record['target_column'] for record in records if record['empty_cover_forces_target_absent']]
    if complete:
        assert units == previous['all_excluded_targets']
    summary = {
        'optional_target_columns': 1214, 'completed_targets': len(records),
        'all_ordered_coordinate_pairs_covered': len(records)*36*36,
        'positive_target_difference_pairs': sum(len(record['all_positive_difference_pairs']) for record in records),
        'demands_weakened_to_one': sum(row[4] for record in records for row in record['all_positive_difference_pairs']),
        'unique_same_target_covers': sum(len(record['unique_covers']) for record in records),
        'retained_minimal_cover_clauses': sum(record['retained_clause_count'] for record in records),
        'retained_literal_occurrences': sum(record['retained_literal_count'] for record in records),
        'same_target_strict_supersets_removed': sum(record['classification'] == 'implied_by_same_target_strict_subset'
                                                   for target in records for record in target['unique_covers']),
        'same_target_nonempty_covers_implied_by_unit': sum(record['classification'] == 'implied_by_same_target_unit'
                                                         for target in records for record in target['unique_covers']),
        'unit_clauses': len(units),
        'largest_retained_clause_literals': max((1+record['unique_covers'][i]['positive_literals']
                                               for record in records for i in record['retained_unique_cover_ids']), default=0),
        'largest_target_retained_clause_count': max((r['retained_clause_count'] for r in records), default=0),
    }
    summary['duplicate_origins_merged'] = summary['positive_target_difference_pairs']-summary['unique_same_target_covers']
    assert summary['unique_same_target_covers'] == (summary['retained_minimal_cover_clauses']
        + summary['same_target_strict_supersets_removed'] + summary['same_target_nonempty_covers_implied_by_unit'])
    result = {'status': 'complete coordinate-difference cover family and same-target implication ledger' if complete
                       else 'UNKNOWN: coordinate-cover census incomplete',
        'source_sha256': digest(Path(__file__)), 'intrinsic_source_sha256': INTRINSIC_SHA,
        'row_domain_sha256': intrinsic.DOMAIN_SHA, 'intrinsic_certificate_sha256': CENSUS_SHA,
        'case_index': 4, 'complete': complete, 'records': records, 'summary': summary,
        'covered_target_columns': list(range(len(records))), 'uncovered_target_columns': list(range(len(records), 1214)),
        'unit_target_columns': units, 'controls': controls(),
        'guarded_cover_derivation': '(t_i-t_j)*x_a <= sum_{eligible b:w_b[i]>w_b[j]} x_b, weakened to demand1 for Boolean x_a.',
        'cross_target_subsumption_used': False, 'stronger_demands_not_encoded': True,
        'point_independent': True, 'optimizer_or_solver_called': False,
        'whole_case_or_local_set_excluded': False,
        'scope': 'Complete family of ordered coordinate-difference guard clauses for the frozen case4 domain, after exact same-target deduplication and subset implication. No main formula or query is changed.'}
    if complete:
        hasher = hashlib.sha256()
        count = literals = 0
        histogram = Counter()
        for clause in clause_stream(result):
            hasher.update((' '.join(map(str, clause))+' 0\n').encode())
            count += 1
            literals += len(clause)
            histogram[len(clause)] += 1
        assert count == summary['retained_minimal_cover_clauses'] and literals == summary['retained_literal_occurrences']
        result['canonical_retained_clause_body_sha256'] = hasher.hexdigest()
        result['retained_clause_size_histogram'] = dict(sorted(histogram.items()))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    parser.add_argument('--seconds', type=float, default=120)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 120
    started = time.monotonic()
    result = calculate(args.seconds)
    if args.replay:
        saved = json.loads(gzip.decompress(args.replay.read_bytes()))
        assert result['complete'] and saved == json.loads(canonical(result))
        result = {'status': 'PASS: complete coordinate covers, weakening and all same-target implications replayed',
                  'source_sha256': digest(Path(__file__)), 'certificate_sha256': digest(args.replay),
                  'summary': result['summary'], 'clause_body_sha256': result['canonical_retained_clause_body_sha256'],
                  'optimizer_or_solver_called': False}
    raw = canonical(result)+b'\n'
    args.output.write_bytes(gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('records', 'covered_target_columns', 'uncovered_target_columns')}, indent=2), flush=True)
    print(json.dumps({'output_sha256': digest(args.output), 'elapsed_seconds': time.monotonic()-started,
                      'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}), flush=True)
