"""Complete case4 automorphisms, exact probe priorities and tiny controls.

Only preparation is exposed. No case4 failed-literal probe or solver is
run. The immutable forward propagator is reused on tiny Boolean controls.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import permutations, product
import json
from pathlib import Path
import struct

import complement_rook_35core_case0004_primary_propagation as rules


ROOT, LOGS = rules.ROOT, rules.LOGS
digest, canonical, save = rules.digest, rules.canonical, rules.save
RULE_SHA = '3e4b8a5118c0ee8e37aee03d5f265128b53af9ae8ffc169393fe2d731062d8f7'
ROW_DOMAIN = LOGS/'complement-rook-35core-case0004-exterior-rows.json.gz'
ROW_DOMAIN_SHA = '10377b5494b8d39e3b41f400b39af485c1db44d06232e1c03663a07f530e8628'
CLOSURE = LOGS/'complement-rook-35core-case0004-primary-propagation-closure-run01.json'
CLOSURE_SHA = 'eda7932e5821b4418ec7e8a4b420091d51993c8df35e18c3e788a810be4ac6d0'
COLD = LOGS/'complement-rook-35core-case0004-primary-propagation-closure-run01-cold-replay.json'
COLD_SHA = '59f09ae8729913bf4b79e8e8c2c3d4a56bc213ef38c215dbed301b6e5c1d6b3c'
LIMITS = {'maximum_probes': 32, 'seconds_per_probe': 5,
          'requested_batch_seconds': 60, 'stop_on_partial_trace': True,
          'solver_or_optimizer_calls': 0}


def image_mask(mask, permutation):
    return sum(1 << permutation[a] for a in rules.members(mask))


def preserves(rows, permutation):
    return sorted(permutation) == list(range(len(rows))) and all(
        image_mask(rows[a], permutation) == rows[permutation[a]] for a in range(len(rows)))


def complete_core_actions(core35, masks):
    """All automorphisms, using identifiable vertex sets and the rook lines."""
    assert len(core35) == 35
    degrees = [r.bit_count() for r in core35]
    assert [i for i, degree in enumerate(degrees) if degree == 4] == list(range(27, 35))
    assert [i for i, degree in enumerate(degrees) if degree == 14] == [0]
    core = [r & ((1 << 27)-1) for r in core35[:27]]
    assert set(map(int.bit_count, core)) == {6}
    relation_degrees = [sum(i != j and (core[i]&core[j]).bit_count() == 2 for j in range(27))
                        for i in range(27)]
    assert relation_degrees == [8]*18+[4]*9
    for p in range(9):
        assert [i for i in range(18) if core[18+p] >> i & 1] == [p, 9+p]
    rook = [sum(1 << q for q in range(9) if p != q and
                (p//3 == q//3 or p%3 == q%3)) for p in range(9)]
    assert [r & 511 for r in core[:9]] == rook
    assert [(r >> 18) & 511 for r in core[18:]] == [511 ^ (1 << p) ^ rook[p] for p in range(9)]
    reached = {0}
    while True:
        enlarged = reached | {q for p in reached for q in rules.members(rook[p])}
        if enlarged == reached:
            break
        reached = enlarged
    assert len(reached) == 9
    # The two families of three maximum cliques are the three rows and
    # three columns. Their permutations and optional family exchange give
    # all 6*6*2 rook automorphisms.
    maps9 = set()
    for rp, cp, exchange in product(permutations(range(3)), permutations(range(3)), (0, 1)):
        image = []
        for p in range(9):
            i, j = p//3, p%3
            if exchange:
                i, j = j, i
            image.append(3*rp[i]+cp[j])
        maps9.add(tuple(image))
    assert len(maps9) == 72 and all(preserves(rook, list(p)) for p in maps9)
    maps27 = []
    for g in sorted(maps9):
        for flip in (0, 1):
            image = [9*(base ^ flip if base < 2 else 2)+g[p]
                     for base in range(3) for p in range(9)]
            assert preserves(core, image)
            maps27.append(image)
    assert len({tuple(p) for p in maps27}) == 144
    root_fixed = [p for p in maps27 if p[0] == 0]
    assert len(root_fixed) == 8
    local = [r & ((1 << 27)-1) for r in core35[27:]]
    assert len(set(local)) == 8 and all(r.bit_count() == 3 for r in local)
    at = {mask: 27+i for i, mask in enumerate(local)}
    extension_checks, maps35 = [], []
    for p in root_fixed:
        transported = [image_mask(mask, p) for mask in local]
        missing = next((i for i, mask in enumerate(transported) if mask not in at), None)
        record = {'core27_action': p, 'transported_local_masks': transported}
        if missing is not None:
            record.update(extends=False, missing_local_index=missing,
                          reason='one local triple has no image among the fixed eight local vertices')
        else:
            full = p+[at[mask] for mask in transported]
            good = preserves(core35, full)
            record.update(extends=good, proposed35_action=full,
                          reason='all35 adjacency rows preserved' if good else 'local matching is not preserved')
            if good:
                maps35.append(full)
        extension_checks.append(record)
    assert maps35 and all(preserves(core35, p) for p in maps35)
    columns = {mask: a for a, mask in enumerate(masks)}
    assert len(columns) == len(masks) == 1214
    column_maps = []
    for p in maps35:
        image = [columns[image_mask(mask, p)] for mask in masks]
        assert sorted(image) == list(range(1214))
        column_maps.append(image)
    remaining, orbits = set(range(1214)), []
    while remaining:
        a = min(remaining)
        orbit = sorted({p[a] for p in column_maps})
        assert set(orbit) <= remaining
        remaining.difference_update(orbit)
        orbits.append(orbit)
    return {'complete_by_identifiable_set_and_rook_line_argument': True,
        'core35_degrees': degrees, 'core27_codegree_two_relation_degrees': relation_degrees,
        'complete_core27_actions': maps27, 'root_fixed_extension_checks': extension_checks,
        'complete_core35_actions': maps35, 'column_permutations': column_maps,
        'column_orbits': orbits, 'core27_group_order': 144,
        'root_fixed_candidates': 8, 'core35_group_order': len(maps35),
        'column_orbit_count': len(orbits)}


def augmented_rows(rows, previously_proved_absent, assumed_column):
    assert previously_proved_absent == sorted(set(previously_proved_absent))
    assert assumed_column not in previously_proved_absent
    premises = [rules.row([[a, 1]], 0, 0, 'previously_proved_absent', a)
                for a in previously_proved_absent]
    premises.append(rules.row([[assumed_column, 1]], 1, 1, 'single_positive_assumption', assumed_column))
    return premises+rows


def check_probe(n, rows, raw, units, prior, assumed, trace):
    assert len(trace['values']) == n
    extended = augmented_rows(rows, prior, assumed)
    checked = rules.verify_trace(n, extended, raw, trace)
    if trace['status'] == 'exact contradiction':
        # An inductive failed-literal conclusion is allowed only after the
        # entire explicit-assumption trace has passed integer replay.
        return {'assumption': [assumed, 1], 'previously_proved_absent': prior,
                'original_row_offset': len(prior)+1,
                'checked_trace': checked, 'newly_proved_absent': assumed}
    return {'assumption': [assumed, 1], 'previously_proved_absent': prior,
            'original_row_offset': len(prior)+1,
            'checked_trace': checked, 'newly_proved_absent': None,
            'satisfying_incidence_claimed': False}


def controls(output):
    assert not output.exists() and digest(Path(rules.__file__)) == RULE_SHA
    # The unique satisfying point is100. Forward closure initially fixes
    # nothing, while assuming either of the last two bits is1 contradicts.
    rows = [rules.row([[0, 1], [1, 1]], 1, 1, 'tiny', 0),
            rules.row([[0, 1], [2, 1]], 1, 1, 'tiny', 1),
            rules.row([[1, 1], [2, 1]], 0, 1, 'tiny', 2)]
    feasible = [v for v in product((0, 1), repeat=3)
                if all(r['lower'] <= sum(c*v[a] for a, c in r['terms']) <= r['upper'] for r in rows)]
    assert feasible == [(1, 0, 0)]
    initial = rules.propagate(3, rows, b'', [], 5)
    assert initial['complete'] and initial['values'] == [-1]*3
    prior, checks = [], []
    for assumed in (1, 2, 0):
        trace = rules.propagate(3, augmented_rows(rows, prior, assumed), b'', [], 5)
        checked = check_probe(3, rows, b'', [], prior, assumed, trace)
        if checked['newly_proved_absent'] is not None:
            assert all(v[assumed] == 0 for v in feasible)
            prior = sorted(prior+[assumed])
        checks.append({'trace': trace, 'check': checked})
    assert prior == [1, 2] and checks[-1]['check']['newly_proved_absent'] is None
    raw = struct.pack('<H', 0)+(1 << 1).to_bytes(rules.MASK_BYTES, 'little')
    covered_rows = [rules.row([[0, 1], [1, 1]], 0, 1, 'tiny', 0)]
    trace = rules.propagate(2, augmented_rows(covered_rows, [], 0), raw, [], 5)
    cover_check = check_probe(2, covered_rows, raw, [], [], 0, trace)
    assert cover_check['newly_proved_absent'] == 0
    report = {'status': 'PASS: explicit positive assumption and inductive failed-literal reasoning on tiny controls',
        'source_sha256': digest(Path(__file__)), 'rule_source_sha256': RULE_SHA,
        'enumerated_tiny_assignments': 8, 'unique_feasible_point': [1, 0, 0],
        'inductive_probe_checks': checks, 'guarded_cover_probe': {'trace': trace, 'check': cover_check},
        'case4_probes_run': 0, 'solver_or_optimizer_called': False}
    save(output, report)
    print(json.dumps(report, indent=2))


def prepare(output, controls_path):
    assert not output.exists()
    assert digest(Path(rules.__file__)) == RULE_SHA
    for path, expected in ((ROW_DOMAIN, ROW_DOMAIN_SHA), (CLOSURE, CLOSURE_SHA), (COLD, COLD_SHA)):
        assert digest(path) == expected
    controls = json.loads(controls_path.read_text())
    assert controls['source_sha256'] == digest(Path(__file__)) and controls['status'].startswith('PASS:')
    closure, cold = json.loads(CLOSURE.read_text()), json.loads(COLD.read_text())
    assert cold['result_sha256'] == CLOSURE_SHA and cold['status'].startswith('PASS:')
    assert closure['summary']['new_assignments'] == 0 and closure['trace']['complete']
    rows, raw, units, bindings = rules.load_inventory()
    assert bindings == closure['bindings']
    data = json.loads(gzip.decompress(ROW_DOMAIN.read_bytes()))
    core35, masks = data['core_adjacency_rows'], data['column_masks35']
    actions = complete_core_actions(core35, masks)
    zeros = set(closure['summary']['proved_absent_columns'])
    assert len(zeros) == 14
    alive = sum(1 << a for a in range(1214) if a not in zeros)
    conflicts, occurrences = [0]*1214, [0]*1214
    clique_rows = 0
    for r in rows:
        for a, c in r['terms']:
            occurrences[a] += 1
        if r['upper'] == 1 and r['lower'] in (0, 1) and all(c == 1 for a, c in r['terms']):
            support = sum(1 << a for a, c in r['terms'])
            clique_rows += 1
            for a, c in r['terms']:
                conflicts[a] |= support ^ (1 << a)
    candidates = [a for a in range(1214) if a not in zeros]
    assert len(candidates) == 1200
    priority = sorted(candidates, key=lambda a: (-(conflicts[a]&alive).bit_count(), -occurrences[a], a))
    ranking = [{'column': a, 'active_direct_conflict_count': (conflicts[a]&alive).bit_count(),
                'base_row_occurrences': occurrences[a], 'attachment_count': masks[a].bit_count()-3}
               for a in priority]
    # No orbit pruning or transported unit is silently introduced. The
    # complete core/column census is retained even if a group is nontrivial.
    report = {'status': 'complete case4 orbit and exact-priority preparation; no production probe',
        'complete': True, 'source_sha256': digest(Path(__file__)), 'rule_source_sha256': RULE_SHA,
        'controls_sha256': digest(controls_path), 'row_domain_sha256': ROW_DOMAIN_SHA,
        'original_forward_closure_sha256': CLOSURE_SHA, 'closure_cold_replay_sha256': COLD_SHA,
        'input_bindings': bindings, 'limits': LIMITS,
        'automorphism_census': actions,
        'all_initially_free_columns': sorted(candidates), 'candidate_count': len(candidates),
        'initial_absent_columns': sorted(zeros), 'priority_order': priority,
        'priority_records': ranking, 'planned_first32_columns': priority[:32],
        'priority_rule': 'Descending exact union of still-active neighbors forbidden by original quota-one/AMO rows; then descending row occurrences; then column ID.',
        'quota_one_or_AMO_priority_rows': clique_rows,
        'single_sweep_baseline_seconds': closure['closure_seconds'],
        '32_times_single_sweep_seconds_not_a_runtime_guarantee': 32*closure['closure_seconds'],
        'batch_is_partial_coverage_of1200_candidates': True,
        'no_orbit_pruning_or_native_presolve_premise': True,
        'each_probe_has_exactly_one_new_positive_assumption': True,
        'conditional_noncontradictory_inferences_never_become_global_units': True,
        'new_global_units_require_checked_contradiction_and_prior_proved_units': True,
        'case4_probes_run': 0, 'solver_or_optimizer_called': False, 'case4_excluded': False}
    save(output, report)
    print(json.dumps({k: v for k, v in report.items() if k not in (
        'automorphism_census', 'input_bindings', 'all_initially_free_columns', 'priority_order', 'priority_records')}, indent=2))
    print('automorphisms', actions['core35_group_order'], 'column_orbits', actions['column_orbit_count'])
    print('preparation_sha256', digest(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    test = commands.add_parser('controls')
    test.add_argument('--output', type=Path, required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--controls', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'controls':
        controls(args.output.resolve())
    else:
        prepare(args.output.resolve(), args.controls.resolve())
