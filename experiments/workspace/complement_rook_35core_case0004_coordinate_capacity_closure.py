"""Exact absence closure at original coordinate demands for case4.

Start with the14 proved intrinsic units. For every still-possible target,
compare each original positive coordinate demand with the number of
eligible candidates not already proved absent. Also check its degree.
Every new unit saves a complete cover and earlier-proof provenance.
No optimizer, SAT solver, or incidence point is used.
"""

import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import resource
import time

import complement_rook_35core_case0004_intrinsic_rows as intrinsic


ROOT, LOGS = intrinsic.ROOT, intrinsic.LOGS
INTRINSIC_SHA = '24eb86e47e6f5a741721fe9174e7d3762bc74edd290c89d489dd5ddedb900c11'
SEEDS = LOGS / 'complement-rook-35core-case0004-intrinsic-rows.json.gz'
SEEDS_SHA = '0d1c096865678958737e34551fb55a203fd65b9dc8b0b5613bd9f1dfd26185e9'
EXPECTED_SEEDS = [352, 353, 354, 355, 439, 552, 553, 645, 869, 873, 957, 1080, 1081, 1167]
digest, canonical = intrinsic.digest, intrinsic.canonical


def members(bits):
    answer = []
    while bits:
        low = bits & -bits
        answer.append(low.bit_length()-1)
        bits ^= low
    return answer


def scan_target(a, targets, neighbors, coordinate_supports, absent_bits):
    dimension = len(targets[a])
    original_neighbors = sum(1 << b for b in neighbors[a])
    active_neighbors = original_neighbors & ~absent_bits
    supports = [bits & original_neighbors for bits in coordinate_supports]
    degree_margin = active_neighbors.bit_count()-targets[a][-1]
    first = ('degree', None, None, targets[a][-1], original_neighbors) if degree_margin < 0 else None
    minimum, minimizing_pair, positive = None, None, 0
    for i in range(dimension):
        for j in range(dimension):
            demand = targets[a][i]-targets[a][j]
            if demand <= 0:
                continue
            positive += 1
            cover = supports[i] & ~supports[j]
            capacity = (cover & ~absent_bits).bit_count()
            margin = capacity-demand
            if minimum is None or margin < minimum:
                minimum, minimizing_pair = margin, [i, j, demand, capacity]
            if margin < 0 and first is None:
                first = ('coordinate_difference', i, j, demand, cover)
    summary = {'target_column': a, 'active_eligible_neighbors': active_neighbors.bit_count(),
               'degree_demand': targets[a][-1], 'degree_margin': degree_margin,
               'all_ordered_coordinate_pairs_checked': dimension*dimension,
               'positive_original_demands_checked': positive,
               'minimum_coordinate_capacity_margin': minimum,
               'first_minimizing_pair_i_j_demand_capacity': minimizing_pair}
    return summary, first


def make_proof(a, witness, stage, earlier, proof_index, proof_id, initial=False):
    kind, i, j, demand, cover = witness
    original = members(cover)
    removed = [b for b in original if b in earlier]
    remaining = [b for b in original if b not in earlier]
    assert len(remaining) < demand
    assert all(b in proof_index for b in removed)
    return {'proof_id': proof_id, 'target_column': a, 'stage': stage,
            'initial_intrinsic_unit': initial, 'kind': kind,
            'coordinate_i': i, 'coordinate_j': j, 'original_demand': demand,
            'full_original_cover': original, 'removed_columns': removed,
            'removed_column_provenance': [[b, proof_index[b]] for b in removed],
            'remaining_columns': remaining, 'remaining_capacity': len(remaining),
            'strict_deficit': demand-len(remaining), 'demand_weakened': False}


def close(targets, vectors, neighbors, seeds, seconds):
    started = time.monotonic()
    n, dimension = len(targets), len(targets[0])
    assert len(vectors) == len(neighbors) == n
    assert all(len(row) == dimension and min(row) >= 0 for row in targets)
    assert all(vector >> (dimension-1) & 1 for vector in vectors)
    coordinate_supports = [sum(1 << b for b, vector in enumerate(vectors) if vector >> i & 1)
                           for i in range(dimension)]
    proofs, proof_index = [], {}
    for a in seeds:
        _, witness = scan_target(a, targets, neighbors, coordinate_supports, 0)
        assert witness is not None and witness[0] == 'coordinate_difference' and witness[-1] == 0
        proof = make_proof(a, witness, 0, set(), {}, len(proofs), True)
        proofs.append(proof)
        proof_index[a] = proof['proof_id']
    absent = set(seeds)
    rounds = []
    complete = False
    for stage in range(1, n+2):
        if time.monotonic()-started >= seconds:
            break
        before = sorted(absent)
        absent_bits = sum(1 << a for a in before)
        pending, scans = [], []
        open_targets = [a for a in range(n) if a not in absent]
        for a in open_targets:
            if time.monotonic()-started >= seconds:
                break
            summary, witness = scan_target(a, targets, neighbors, coordinate_supports, absent_bits)
            scans.append(summary)
            if witness is not None:
                pending.append((a, witness))
        covered = len(scans) == len(open_targets)
        new_ids = []
        for a, witness in pending:
            proof = make_proof(a, witness, stage, absent, proof_index, len(proofs))
            proofs.append(proof)
            proof_index[a] = proof['proof_id']
            new_ids.append(proof['proof_id'])
        # All witnesses in this stage use exactly the prior-stage set.
        absent.update(a for a, _ in pending)
        rounds.append({'stage': stage, 'prior_absent_columns': before,
                       'covered_targets': [row['target_column'] for row in scans],
                       'uncovered_targets': open_targets[len(scans):],
                       'full_stage_coverage': covered, 'target_scans': scans,
                       'new_targets': [a for a, _ in pending], 'new_proof_ids': new_ids,
                       'positive_original_demands_checked': sum(row['positive_original_demands_checked'] for row in scans),
                       'degree_checks': len(scans)})
        if covered and not pending:
            complete = True
            break
        if not covered:
            break
    return {'complete': complete, 'initial_absent_columns': list(seeds), 'proofs': proofs,
            'rounds': rounds, 'all_proved_absent_columns': sorted(absent),
            'new_absent_columns': sorted(absent-set(seeds)),
            'remaining_target_columns': [a for a in range(n) if a not in absent],
            'terminal_reason': 'fixed point' if complete else 'time limit before a complete fixed-point check'}


def verify(result, targets, vectors, neighbors):
    """Check proof lists directly and terminal capacities by cooccurrences.

    This verifier does not use bitset differences for terminal counts.
    It counts each active neighbor's coordinate incidences and ordered
    cooccurrences, then uses |S_i minus S_j| = |S_i|-|S_i intersect S_j|.
    """
    checked, proof_index = [], {}
    for index, proof in enumerate(result['proofs']):
        assert proof['proof_id'] == index and proof['target_column'] not in proof_index
        a, stage = proof['target_column'], proof['stage']
        earlier = {row['target_column'] for row in checked if row['stage'] < stage}
        if proof['kind'] == 'degree':
            assert proof['coordinate_i'] is None and proof['coordinate_j'] is None
            demand, original = targets[a][-1], list(neighbors[a])
        else:
            assert proof['kind'] == 'coordinate_difference'
            i, j = proof['coordinate_i'], proof['coordinate_j']
            demand = targets[a][i]-targets[a][j]
            original = [b for b in neighbors[a] if (vectors[b] >> i & 1) > (vectors[b] >> j & 1)]
        assert demand > 0 and proof['original_demand'] == demand
        removed = [b for b in original if b in earlier]
        remaining = [b for b in original if b not in earlier]
        assert proof['full_original_cover'] == original
        assert proof['removed_columns'] == removed and proof['remaining_columns'] == remaining
        assert proof['removed_column_provenance'] == [[b, proof_index[b]] for b in removed]
        assert proof['remaining_capacity'] == len(remaining) < demand
        assert proof['strict_deficit'] == demand-len(remaining) and not proof['demand_weakened']
        if proof['initial_intrinsic_unit']:
            assert stage == 0 and not original and a in result['initial_absent_columns']
        else:
            assert stage > 0 and a not in result['initial_absent_columns']
        checked.append(proof)
        proof_index[a] = index
    absent = set(proof_index)
    assert sorted(absent) == result['all_proved_absent_columns']
    assert sorted(absent-set(result['initial_absent_columns'])) == result['new_absent_columns']
    remaining = [a for a in range(len(targets)) if a not in absent]
    assert remaining == result['remaining_target_columns']
    terminal_positive = terminal_degree = 0
    if result['complete']:
        assert result['rounds'][-1]['new_targets'] == []
        assert result['rounds'][-1]['covered_targets'] == remaining
        assert result['rounds'][-1]['prior_absent_columns'] == sorted(absent)
        terminal = result['rounds'][-1]['target_scans']
        dimension = len(targets[0])
        supports = [members(vector) for vector in vectors]
        for a, saved in zip(remaining, terminal):
            active = [b for b in neighbors[a] if b not in absent]
            single = [0]*dimension
            joint = [[0]*dimension for _ in range(dimension)]
            for b in active:
                for i in supports[b]:
                    single[i] += 1
                    for j in supports[b]:
                        joint[i][j] += 1
            assert len(active) >= targets[a][-1]
            terminal_degree += 1
            minimum, minimizing_pair, positive = None, None, 0
            for i in range(dimension):
                for j in range(dimension):
                    demand = targets[a][i]-targets[a][j]
                    if demand <= 0:
                        continue
                    capacity = single[i]-joint[i][j]
                    assert capacity >= demand
                    positive += 1
                    margin = capacity-demand
                    if minimum is None or margin < minimum:
                        minimum, minimizing_pair = margin, [i, j, demand, capacity]
            assert saved == {'target_column': a, 'active_eligible_neighbors': len(active),
                'degree_demand': targets[a][-1], 'degree_margin': len(active)-targets[a][-1],
                'all_ordered_coordinate_pairs_checked': dimension*dimension,
                'positive_original_demands_checked': positive,
                'minimum_coordinate_capacity_margin': minimum,
                'first_minimizing_pair_i_j_demand_capacity': minimizing_pair}
            terminal_positive += positive
    return {'exact_unit_proofs_checked': len(checked),
            'terminal_targets_checked_by_independent_cooccurrence_counts': terminal_degree,
            'terminal_positive_original_demands_checked': terminal_positive,
            'all_new_units_use_earlier_stage_provenance_only': True,
            'optimizer_or_solver_called': False}


def controls():
    # Demand2 removes target0 although its demand1 cover is nonempty.
    # The removal then leaves target1 with too few degree neighbors.
    targets = [[2, 0, 2], [1, 1, 2], [0, 0, 0]]
    vectors, neighbors = [5, 5, 6], [[1, 2], [0, 2], [0, 1]]
    toy = close(targets, vectors, neighbors, [], 10)
    assert toy['complete'] and toy['new_absent_columns'] == [0, 1]
    assert [row['new_targets'] for row in toy['rounds']] == [[0], [1], []]
    assert toy['proofs'][0]['kind'] == 'coordinate_difference' and toy['proofs'][0]['original_demand'] == 2
    assert len(toy['proofs'][0]['full_original_cover']) == 1
    assert toy['proofs'][1]['kind'] == 'degree' and toy['proofs'][1]['removed_column_provenance'] == [[0, 0]]
    verify(toy, targets, vectors, neighbors)
    # A genuine nine-vertex rook graph is a positive row-feasibility control.
    adjacent = lambda a, b: a != b and (a//3 == b//3 or a % 3 == b % 3)
    sites, outside = [0, 1, 3, 4, 8], [2, 5, 6, 7]
    core = [sum(1 << j for j, b in enumerate(sites) if adjacent(a, b)) for a in sites]
    masks = [sum(1 << j for j, b in enumerate(sites) if adjacent(a, b)) for a in outside]
    targets = [[2-int(mask >> i & 1)-(core[i] & mask).bit_count() for i in range(5)]
               + [4-mask.bit_count()] for mask in masks]
    neighbors = [[b for b in range(4) if b != a and (masks[a] & masks[b]).bit_count() <= 1
                  and all(targets[a][i] or not(masks[b] >> i & 1) for i in range(5))
                  and all(targets[b][i] or not(masks[a] >> i & 1) for i in range(5))] for a in range(4)]
    vectors = [mask | (1 << 5) for mask in masks]
    for a in range(4):
        actual = [b for b in range(4) if adjacent(outside[a], outside[b])]
        assert set(actual) <= set(neighbors[a])
        assert [sum(vectors[b] >> i & 1 for b in actual) for i in range(6)] == targets[a]
    rook = close(targets, vectors, neighbors, [], 10)
    assert rook['complete'] and not rook['all_proved_absent_columns']
    verify(rook, targets, vectors, neighbors)
    return {'original_demand_stronger_than_nonempty_cover_control': True,
            'two_stage_provenance_and_degree_cascade_control': True,
            'rook9_actual_rows_preserved': 4, 'optimizer_or_solver_called': False}


def calculate(seconds):
    assert digest(Path(intrinsic.__file__)) == INTRINSIC_SHA and digest(SEEDS) == SEEDS_SHA
    saved = json.loads(gzip.decompress(SEEDS.read_bytes()))
    assert saved['complete'] and saved['all_excluded_targets'] == EXPECTED_SEEDS
    model, targets, zeros, neighbors, old_units = intrinsic.load()
    assert len(targets) == len(neighbors) == 1214
    vectors = [mask | (1 << 35) for mask in model['column_masks35']]
    assert sum(len(row) for row in neighbors) == 551156
    all_positive = sum(sum(i > j for i in row for j in row) for row in targets)
    assert all_positive == 476766
    result = close(targets, vectors, neighbors, EXPECTED_SEEDS, seconds)
    verification = verify(result, targets, vectors, neighbors)
    result.update(status='complete original-demand and degree absence closure' if result['complete']
                        else 'UNKNOWN: absence closure stopped before full fixed point',
                  source_sha256=digest(Path(__file__)), intrinsic_source_sha256=INTRINSIC_SHA,
                  row_domain_sha256=intrinsic.DOMAIN_SHA, initial_unit_certificate_sha256=SEEDS_SHA,
                  case_index=4, optional_columns=1214, augmented_coordinates=36,
                  complete_eligible_directed_entries=551156,
                  all_original_positive_coordinate_differences=all_positive,
                  original_demands_never_weakened=True,
                  synchronous_stages=True, verification=verification, controls=controls(),
                  all_targets_tested_without_an_incidence_point=True,
                  optimizer_or_solver_called=False, case4_excluded=False,
                  scope='Point-independent necessary target exclusions in indexed35-core case4 only; a fixed point is not incidence or graph feasibility.')
    if result['complete']:
        terminal = result['rounds'][-1]['target_scans']
        result['terminal_minimum_margin_histogram'] = dict(sorted(Counter(
            row['minimum_coordinate_capacity_margin'] for row in terminal).items()))
        result['terminal_degree_margin_histogram'] = dict(sorted(Counter(row['degree_margin'] for row in terminal).items()))
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    parser.add_argument('--seconds', type=float, default=60)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 120
    started = time.monotonic()
    result = calculate(args.seconds)
    if args.replay:
        saved = json.loads(gzip.decompress(args.replay.read_bytes()))
        assert result['complete'] and saved == json.loads(canonical(result))
        result = {'status': 'PASS: complete original-demand/degree closure and exact provenance replayed',
                  'source_sha256': digest(Path(__file__)), 'certificate_sha256': digest(args.replay),
                  'initial_unit_columns': result['initial_absent_columns'],
                  'new_absent_columns': result['new_absent_columns'],
                  'all_proved_absent_columns': result['all_proved_absent_columns'],
                  'remaining_target_count': len(result['remaining_target_columns']),
                  'verification': result['verification'], 'optimizer_or_solver_called': False}
    raw = canonical(result)+b'\n'
    args.output.write_bytes(gzip.compress(raw, mtime=0) if args.output.suffix == '.gz' else raw)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('proofs', 'rounds', 'remaining_target_columns')}, indent=2), flush=True)
    print(json.dumps({'output_sha256': digest(args.output), 'elapsed_seconds': time.monotonic()-started,
                      'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}), flush=True)
