"""Complete intrinsic row tests on all1214 optional case4 columns.

No incidence point, optimizer, or SAT solver is used. Ordered support
dominance gives integer target exclusions. Exact finite-field span tests
give either a checked neighbor combination or a checked annihilating
dual. Field3 arithmetic uses two bit planes and has independent small
exhaustive controls.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import resource
import time


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/grids-and-triangles'
DOMAIN = LOGS / 'complement-rook-35core-case0004-exterior-rows.json.gz'
DOMAIN_SHA = '10377b5494b8d39e3b41f400b39af485c1db44d06232e1c03663a07f530e8628'
OLD_UNITS = LOGS / 'complement-rook-35core-case0004-row-cut-units.json'
OLD_UNITS_SHA = '395854ca6bce2e47379b2160359eea1e146cfc1593da9cc519d7f44a07b8082b'
WIDTH = 36
MASK = (1 << WIDTH)-1


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def add3(a, b):
    a1, a2 = a
    b1, b2 = b
    az, bz = MASK ^ (a1 | a2), MASK ^ (b1 | b2)
    return ((az & b1) | (a1 & bz) | (a2 & b2),
            (az & b2) | (a2 & bz) | (a1 & b1))


def sub3(a, b):
    return add3(a, (b[1], b[0]))


def dot3(a, b):
    return ((a[0] & b[0]).bit_count() + (a[1] & b[1]).bit_count()
            - (a[0] & b[1]).bit_count() - (a[1] & b[0]).bit_count()) % 3


def pack3(values):
    return (sum(1 << i for i, v in enumerate(values) if v % 3 == 1),
            sum(1 << i for i, v in enumerate(values) if v % 3 == 2))


def unpack3(pair):
    assert not pair[0] & pair[1] and (pair[0] | pair[1]) <= MASK
    return [int(pair[0] >> i & 1) + 2*int(pair[1] >> i & 1) for i in range(WIDTH)]


def span2(neighbors, vectors, target, upper):
    basis, origin = [0]*WIDTH, [0]*WIDTH
    chosen = []
    processed = 0
    for b in neighbors:
        value, combination = vectors[b], 1 << len(chosen)
        processed += 1
        while value:
            pivot = value.bit_length()-1
            if basis[pivot]:
                value ^= basis[pivot]
                combination ^= origin[pivot]
            else:
                basis[pivot], origin[pivot] = value, combination
                chosen.append(b)
                break
        if len(chosen) == upper:
            break
    assert len(chosen) <= upper
    remainder, combination = target, 0
    for pivot in reversed(range(WIDTH)):
        if remainder >> pivot & 1 and basis[pivot]:
            remainder ^= basis[pivot]
            combination ^= origin[pivot]
    record = {'prime': 2, 'rank': len(chosen), 'ambient_rank_bound': upper,
              'basis_origin_columns': chosen, 'neighbor_columns_processed': processed,
              'in_span': remainder == 0}
    if remainder == 0:
        terms = [[b, 1] for i, b in enumerate(chosen) if combination >> i & 1]
        actual = 0
        for b, coefficient in terms:
            actual ^= vectors[b]
        assert actual == target
        record['neighbor_combination'] = terms
    else:
        assert processed == len(neighbors)
        free = (remainder & -remainder).bit_length()-1
        assert basis[free] == 0
        dual = 1 << free
        for pivot in range(WIDTH):
            if basis[pivot] and (basis[pivot] & dual).bit_count() % 2:
                dual |= 1 << pivot
        assert all((dual & vectors[b]).bit_count() % 2 == 0 for b in neighbors)
        assert (dual & target).bit_count() % 2 == 1
        record.update(dual_vector=[int(dual >> i & 1) for i in range(WIDTH)],
                      every_neighbor_dual_product=0, target_dual_product=1)
    return record


def span3(neighbors, vectors, target, upper):
    basis, origin = [None]*WIDTH, [None]*WIDTH
    chosen = []
    processed = 0
    for b in neighbors:
        value, combination = vectors[b], (1 << len(chosen), 0)
        processed += 1
        while value[0] | value[1]:
            pivot = (value[0] | value[1]).bit_length()-1
            if basis[pivot] is None:
                if value[1] >> pivot & 1:
                    value, combination = (value[1], value[0]), (combination[1], combination[0])
                assert value[0] >> pivot & 1
                basis[pivot], origin[pivot] = value, combination
                chosen.append(b)
                break
            if value[0] >> pivot & 1:
                value, combination = sub3(value, basis[pivot]), sub3(combination, origin[pivot])
            else:
                value, combination = add3(value, basis[pivot]), add3(combination, origin[pivot])
        if len(chosen) == upper:
            break
    assert len(chosen) <= upper
    remainder, combination = target, (0, 0)
    for pivot in reversed(range(WIDTH)):
        if basis[pivot] is None:
            continue
        if remainder[0] >> pivot & 1:
            remainder, combination = sub3(remainder, basis[pivot]), add3(combination, origin[pivot])
        elif remainder[1] >> pivot & 1:
            remainder, combination = add3(remainder, basis[pivot]), sub3(combination, origin[pivot])
    record = {'prime': 3, 'rank': len(chosen), 'ambient_rank_bound': upper,
              'basis_origin_columns': chosen, 'neighbor_columns_processed': processed,
              'in_span': remainder == (0, 0)}
    if remainder == (0, 0):
        terms = [[b, int(combination[0] >> i & 1)+2*int(combination[1] >> i & 1)]
                 for i, b in enumerate(chosen) if (combination[0] | combination[1]) >> i & 1]
        actual = (0, 0)
        for b, coefficient in terms:
            vector = vectors[b] if coefficient == 1 else (vectors[b][1], vectors[b][0])
            actual = add3(actual, vector)
        assert actual == target
        record['neighbor_combination'] = terms
    else:
        assert processed == len(neighbors)
        occupied = remainder[0] | remainder[1]
        free = (occupied & -occupied).bit_length()-1
        assert basis[free] is None
        dual = (1 << free, 0)
        for pivot in range(WIDTH):
            if basis[pivot] is not None:
                value = (-dot3(basis[pivot], dual)) % 3
                if value == 1:
                    dual = (dual[0] | (1 << pivot), dual[1])
                elif value == 2:
                    dual = (dual[0], dual[1] | (1 << pivot))
        if dot3(dual, target) == 2:
            dual = (dual[1], dual[0])
        assert all(dot3(dual, vectors[b]) == 0 for b in neighbors)
        assert dot3(dual, target) == 1
        record.update(dual_vector=unpack3(dual), every_neighbor_dual_product=0, target_dual_product=1)
    return record


def direct_field_check(record, neighbors, masks, target):
    """Use integer coordinate sums, independent of packed field arithmetic."""
    p = record['prime']
    assert record['rank'] == len(record['basis_origin_columns'])
    assert set(record['basis_origin_columns']) <= set(neighbors)
    if record['in_span']:
        terms = record['neighbor_combination']
        assert len({b for b, c in terms}) == len(terms)
        assert all(b in neighbors and 0 < c < p for b, c in terms)
        assert all(sum(c*int(masks[b] >> i & 1) for b, c in terms) % p == target[i] % p
                   for i in range(WIDTH))
    else:
        dual = record['dual_vector']
        assert len(dual) == WIDTH and all(type(v) is int and 0 <= v < p for v in dual)
        assert all(sum(v for i, v in enumerate(dual) if masks[b] >> i & 1) % p == 0
                   for b in neighbors)
        assert sum(v*t for v, t in zip(dual, target)) % p == 1


def controls():
    binary_checks = ternary_checks = packed_checks = 0
    vectors2 = list(range(1, 8))
    for subset in range(1 << 7):
        neighbors = [i for i in range(7) if subset >> i & 1]
        reachable = {0}
        for b in neighbors:
            reachable |= {v ^ vectors2[b] for v in list(reachable)}
        for target in range(8):
            record = span2(neighbors, vectors2, target, 3)
            assert record['in_span'] == (target in reachable)
            direct_field_check(record, neighbors, vectors2, [int(target >> i & 1) for i in range(WIDTH)])
            binary_checks += 1
    plain = list(product(range(3), repeat=3))
    vectors3 = [pack3(v) for v in plain]
    for i, left in enumerate(plain):
        for j, right in enumerate(plain):
            assert unpack3(add3(vectors3[i], vectors3[j]))[:3] == [(a+b) % 3 for a, b in zip(left, right)]
            assert dot3(vectors3[i], vectors3[j]) == sum(a*b for a, b in zip(left, right)) % 3
            packed_checks += 1
    families = [[]] + [[i] for i in range(27)] + [list(pair) for pair in combinations(range(27), 2)]
    families += [[1, 3, 9], [4, 10, 12], [5, 11, 17]]
    for neighbors in families:
        reachable = {(0, 0, 0)}
        for b in neighbors:
            reachable = {tuple((v[i]+c*plain[b][i]) % 3 for i in range(3))
                         for v in reachable for c in range(3)}
        for i, target in enumerate(plain):
            record = span3(neighbors, vectors3, vectors3[i], 3)
            assert record['in_span'] == (target in reachable)
            if record['in_span']:
                terms = record['neighbor_combination']
                assert all(sum(c*plain[b][j] for b, c in terms) % 3 == target[j] for j in range(3))
            else:
                dual = record['dual_vector']
                assert all(sum(dual[j]*plain[b][j] for j in range(3)) % 3 == 0 for b in neighbors)
                assert sum(dual[j]*target[j] for j in range(3)) % 3 == 1
            ternary_checks += 1
    return {'GF2_exhaustive_span_and_witness_cases': binary_checks,
            'GF3_packed_addition_and_dot_cases': packed_checks,
            'GF3_explicit_reachable_span_and_witness_cases': ternary_checks,
            'optimizer_or_solver_called': False}


def load():
    assert digest(DOMAIN) == DOMAIN_SHA and digest(OLD_UNITS) == OLD_UNITS_SHA
    model = json.loads(gzip.decompress(DOMAIN.read_bytes()))
    old = json.loads(OLD_UNITS.read_text())
    known = sorted(c['zero_based_column'] for c in old['certificates'])
    assert known == [1080, 1081]
    core, masks = model['core_adjacency_rows'], model['column_masks35']
    assert len(core) == 35 and len(masks) == 1214
    targets = [[2-int(mask >> i & 1)-(core[i] & mask).bit_count() for i in range(35)]
               + [14-mask.bit_count()] for mask in masks]
    assert targets == model['row_targets36'] and all(min(row) >= 0 for row in targets)
    zeros = [sum(1 << i for i in range(35) if row[i] == 0) for row in targets]
    neighbors = [[] for _ in masks]
    for a, b in combinations(range(len(masks)), 2):
        if (masks[a] & masks[b]).bit_count() > 1 or masks[b] & zeros[a] or masks[a] & zeros[b]:
            continue
        neighbors[a].append(b)
        neighbors[b].append(a)
    assert neighbors == model['eligible_neighbor_column_ids']
    assert sum(map(len, neighbors)) == 551156
    for mask, target in zip(masks, targets):
        assert all(((mask >> start) & 511).bit_count() == 1 for start in (0, 9, 18))
        assert all(sum(target[start:start+9]) == target[-1] for start in (0, 9, 18))
    return model, targets, zeros, neighbors, known


def calculate(seconds):
    started = time.monotonic()
    check = controls()
    model, targets, zeros, neighbors, known = load()
    n = len(targets)
    vectors2 = [mask | (1 << 35) for mask in model['column_masks35']]
    vectors3 = [(mask, 0) for mask in vectors2]
    coordinate_supports = [sum(1 << b for b, mask in enumerate(vectors2) if mask >> i & 1)
                           for i in range(WIDTH)]
    records = []
    for a in range(n):
        if time.monotonic()-started >= seconds:
            break
        neighborhood = sum(1 << b for b in neighbors[a])
        supports = [row & neighborhood for row in coordinate_supports]
        dominance = [[i, j] for i in range(WIDTH) for j in range(WIDTH)
                     if targets[a][i] > targets[a][j] and supports[i] & ~supports[j] == 0]
        for i, j in dominance:
            assert all(not(vectors2[b] >> i & 1) or vectors2[b] >> j & 1 for b in neighbors[a])
        # Zero mixed coordinates and three independent base-sum/degree
        # identities bound the rank over either field. The three blocks
        # have nonzero coordinates because every eligible column meets each.
        assert neighbors[a] and all(any(targets[a][start:start+9]) for start in (0, 9, 18))
        upper = WIDTH-zeros[a].bit_count()-3
        target2 = sum(1 << i for i, value in enumerate(targets[a]) if value % 2)
        field2 = span2(neighbors[a], vectors2, target2, upper)
        field3 = span3(neighbors[a], vectors3, pack3(targets[a]), upper)
        direct_field_check(field2, neighbors[a], vectors2, targets[a])
        direct_field_check(field3, neighbors[a], vectors2, targets[a])
        records.append({'column': a, 'original_signature_and_attachment': model['columns'][a],
            'target36': targets[a], 'eligible_neighbor_count': len(neighbors[a]),
            'ordered_dominance_pairs': dominance,
            'dominance_target_excluded': bool(dominance), 'GF2': field2, 'GF3': field3})
        if len(records) % 128 == 0:
            print(json.dumps({'completed_columns': len(records), 'total_columns': n,
                              'elapsed_seconds': time.monotonic()-started}), flush=True)
    excluded_by = {
        'support_dominance': [r['column'] for r in records if r['dominance_target_excluded']],
        'GF2': [r['column'] for r in records if not r['GF2']['in_span']],
        'GF3': [r['column'] for r in records if not r['GF3']['in_span']],
    }
    all_excluded = sorted(set().union(*map(set, excluded_by.values())))
    complete = len(records) == n
    return {'status': 'complete intrinsic-row census with exact witnesses' if complete else 'UNKNOWN: bounded census incomplete',
        'source_sha256': digest(Path(__file__)), 'row_domain_sha256': DOMAIN_SHA,
        'old_two_unit_certificate_sha256': OLD_UNITS_SHA,
        'case_index': 4, 'all_optional_columns': n, 'complete': complete,
        'complete_eligible_unordered_edges': sum(map(len, neighbors))//2,
        'all_unordered_candidate_pairs_checked': n*(n-1)//2,
        'covered_column_indices': list(range(len(records))), 'uncovered_column_indices': list(range(len(records), n)),
        'ordered_coordinate_pairs_checked': len(records)*WIDTH*WIDTH,
        'records': records, 'excluded_by': excluded_by, 'all_excluded_targets': all_excluded,
        'previously_explicitly_excluded_targets': known,
        'new_targets_beyond_previous_explicit_units': sorted(set(all_excluded)-set(known)),
        'summary': {'dominance_excluded_targets': len(excluded_by['support_dominance']),
                    'dominance_witness_pairs': sum(len(r['ordered_dominance_pairs']) for r in records),
                    'GF2_excluded_targets': len(excluded_by['GF2']), 'GF3_excluded_targets': len(excluded_by['GF3']),
                    'union_excluded_targets': len(all_excluded),
                    'GF2_rank_histogram': dict(sorted(Counter(r['GF2']['rank'] for r in records).items())),
                    'GF3_rank_histogram': dict(sorted(Counter(r['GF3']['rank'] for r in records).items())),
                    'positive_field_combination_certificates': sum(r[name]['in_span'] for r in records for name in ('GF2', 'GF3')),
                    'negative_field_dual_certificates': sum(not r[name]['in_span'] for r in records for name in ('GF2', 'GF3'))},
        'controls': check, 'point_independent': True, 'optimizer_or_solver_called': False,
        'scope': 'Necessary single-source exterior-row tests on the complete frozen case4 optional-column domain. Field membership is only a modular necessary condition, not a nonnegative or binary row witness. No incidence design or whole case is excluded by passing tests.'}


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
        result = {'status': 'PASS: complete intrinsic-row census, all field witnesses and dominance pairs replayed',
                  'source_sha256': digest(Path(__file__)), 'certificate_sha256': digest(args.replay),
                  'complete': True, 'summary': result['summary'], 'optimizer_or_solver_called': False}
    raw = canonical(result)+b'\n'
    args.output.write_bytes(gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('records', 'covered_column_indices', 'uncovered_column_indices')}, indent=2), flush=True)
    print(json.dumps({'output_sha256': digest(args.output), 'elapsed_seconds': time.monotonic()-started,
                      'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}), flush=True)
