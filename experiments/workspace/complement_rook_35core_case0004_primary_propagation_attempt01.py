"""Exact primary propagation rules and controls for case4; preparation only.

This file exposes a deterministic interval/cover closure routine, but its
CLI runs only tiny controls or prepares the complete immutable inventory.
No case4 closure, failed-literal probe, CP-SAT or other solver is run by
either command. Every inferred literal has an original-row reason.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import product
import json
from pathlib import Path
import struct
import time


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/grids-and-triangles'
N = 1214
MASK_BYTES, RECORD_BYTES = 152, 154
NATIVE = LOGS/'complement-rook-35core-case0004-native-cpsat-model.json'
NATIVE_SHA = 'a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476'
LAZY = LOGS/'complement-rook-35core-case0004-lazy-native-model.json'
LAZY_SHA = 'aeb636198cb0b9749e2142a596404181edf92923d55d5bdf764a8f9432439b68'
COLD = LOGS/'complement-rook-35core-case0004-lazy-native-cold-replay.json'
COLD_SHA = 'ad169d4dece65473c87e814338741923ce12b5a8b655379d35051dabfe029571'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')


def members(bits):
    while bits:
        bit = bits & -bits
        yield bit.bit_length()-1
        bits -= bit


def cover(raw, identifier):
    assert 0 <= identifier < len(raw)//RECORD_BYTES
    offset = RECORD_BYTES*identifier
    return (struct.unpack_from('<H', raw, offset)[0],
            int.from_bytes(memoryview(raw)[offset+2:offset+RECORD_BYTES], 'little'))


def row(terms, lower, upper, family, source):
    assert type(lower) is type(upper) is int and lower <= upper
    coefficients = Counter()
    for variable, coefficient in terms:
        assert type(variable) is type(coefficient) is int and variable >= 0
        coefficients[variable] += coefficient
    return {'terms': [[a, c] for a, c in sorted(coefficients.items()) if c],
            'lower': lower, 'upper': upper, 'family': family, 'source': source}


def rows_from_inventory(inventory):
    result = []
    for i, j, quota, support in inventory['Gram_rows']:
        result.append(row([[a, 1] for a in support], quota, quota, 'Gram', [i, j]))
    for original, support in inventory['original_signature_rows']:
        result.append(row([[a, 1] for a in support], 0, 1, 'original_signature', original))
    for record in inventory['triple_rows']:
        result.append(row([[a, 1] for a in record['members']], 0, 1, 'core_triple', record['triple']))
    for identifier, clause in enumerate(inventory['Gram_conflict_clauses']):
        assert len(clause) == 2 and all(v < 0 for v in clause)
        result.append(row([[-v-1, 1] for v in clause], 0, 1, 'Gram_conflict', identifier))
    for identifier, cut in enumerate(inventory['uncapped_integer_cuts']):
        target, demand = cut['target_column'], cut['positive_demand']
        assert type(demand) is int and demand > 0
        assert all(type(w) is int and w > 0 for a, w in cut['positive_terms'])
        terms = [[a, w] for a, w in cut['positive_terms']] + [[target, -demand]]
        result.append(row(terms, 0, sum(w for a, w in cut['positive_terms']),
                          'uncapped_row_cut', identifier))
    assert Counter(r['family'] for r in result) == {
        'Gram': 630, 'original_signature': 186, 'core_triple': 1365,
        'Gram_conflict': 30, 'uncapped_row_cut': 60}
    assert len(result) == 2271 and all(0 <= a < N for r in result for a, c in r['terms'])
    return result


def load_inventory():
    for path, expected in ((NATIVE, NATIVE_SHA), (LAZY, LAZY_SHA), (COLD, COLD_SHA)):
        assert digest(path) == expected
    native, lazy, cold = (json.loads(p.read_text()) for p in (NATIVE, LAZY, COLD))
    assert native['complete'] and lazy['complete'] and cold['status'].startswith('PASS:')
    assert cold['model_sha256'] == LAZY_SHA
    for name, expected in lazy['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    inventory = native['primary_inventory']
    assert sha(canonical(inventory)) == native['primary_inventory_sha256']
    assert inventory['primary_variables'] == N and inventory['case'] == 4
    rows = rows_from_inventory(inventory)
    registry = ROOT/lazy['registry']
    assert digest(registry) == lazy['registry_sha256']
    raw = gzip.decompress(registry.read_bytes())
    assert sha(raw) == lazy['registry_metadata']['decompressed_sha256']
    assert len(raw) == RECORD_BYTES*178533
    units = []
    literals = 0
    for identifier in range(178533):
        a, bits = cover(raw, identifier)
        assert 0 <= a < N and bits < (1 << N) and not (bits >> a & 1)
        literals += 1+bits.bit_count()
        if not bits:
            units.append(identifier)
    assert literals == 12887146 and units == lazy['initial_prefix_clause_ids_in_order']
    assert len(units) == 14
    bindings = {'native_model_sha256': NATIVE_SHA, 'lazy_model_sha256': LAZY_SHA,
                'complete_ledger_cold_replay_sha256': COLD_SHA,
                'primary_inventory_sha256': native['primary_inventory_sha256'],
                'canonical_integer_rows_sha256': sha(canonical(rows)),
                'registry_sha256': lazy['registry_sha256'],
                'registry_raw_sha256': sha(raw), 'original_input_source_hashes': lazy['source_hashes']}
    return rows, raw, units, bindings


def bounds(terms, values):
    fixed = sum(c*values[a] for a, c in terms if values[a] != -1)
    minimum = fixed+sum(min(0, c) for a, c in terms if values[a] == -1)
    maximum = fixed+sum(max(0, c) for a, c in terms if values[a] == -1)
    return minimum, maximum


def row_event(r, values):
    """First interval contradiction or impossible value; no divisibility rule."""
    minimum, maximum = bounds(r['terms'], values)
    common = {'original_minimum': minimum, 'original_maximum': maximum}
    if minimum > r['upper'] or maximum < r['lower']:
        return {'kind': 'contradiction', **common}
    for a, c in r['terms']:
        if values[a] != -1:
            continue
        for forbidden in (0, 1):
            low = minimum-min(0, c)+c*forbidden
            high = maximum-max(0, c)+c*forbidden
            if low > r['upper'] or high < r['lower']:
                return {'kind': 'assignment', 'variable': a, 'value': 1-forbidden,
                        'forbidden_value': forbidden, 'conditional_minimum': low,
                        'conditional_maximum': high, **common}
    return None


def cover_event(a, bits, values, one_bits, zero_bits):
    if values[a] == 0 or bits & one_bits:
        return None
    remaining = bits & ~zero_bits
    if not remaining:
        if values[a] == 1:
            return {'kind': 'contradiction'}
        return {'kind': 'assignment', 'variable': a, 'value': 0, 'forbidden_value': 1}
    if values[a] == 1 and remaining.bit_count() == 1:
        b = remaining.bit_length()-1
        assert values[b] == -1
        return {'kind': 'assignment', 'variable': b, 'value': 1, 'forbidden_value': 0}
    return None


def propagate(n, rows, raw, initial_unit_ids, seconds):
    """Pure exact closure; this is called only on tiny controls by this CLI."""
    started = time.monotonic()
    values, reasons = [-1]*n, [-1]*n
    one_bits = zero_bits = 0
    records = []
    sweeps = 0

    def budget():
        if time.monotonic()-started > seconds:
            raise TimeoutError('exact propagation budget reached')

    def record(event, origin, support):
        nonlocal one_bits, zero_bits
        event = dict(event, origin=origin,
                     prior_assignment_indices=sorted({reasons[a] for a in support if values[a] != -1}))
        assert all(i >= 0 for i in event['prior_assignment_indices'])
        if event['kind'] == 'assignment':
            a, value = event['variable'], event['value']
            assert values[a] == -1 and value in (0, 1)
            assert len(records) < n  # No variable can receive a second assignment.
            values[a], reasons[a] = value, len(records)
            if value:
                one_bits |= 1 << a
            else:
                zero_bits |= 1 << a
        records.append(event)
        assert len(records) <= n+1  # At most n literals plus a final contradiction.
        return event['kind'] == 'contradiction'

    try:
        for identifier in initial_unit_ids:
            a, bits = cover(raw, identifier)
            assert bits == 0
            event = cover_event(a, bits, values, one_bits, zero_bits)
            if event:
                assert not record(event, {'family': 'cover', 'id': identifier}, [a])
        while True:
            before = len(records)
            sweeps += 1
            assert sweeps <= n+1
            for identifier, r in enumerate(rows):
                budget()
                while True:
                    event = row_event(r, values)
                    if event is None:
                        break
                    if record(event, {'family': 'base_row', 'id': identifier}, [a for a, c in r['terms']]):
                        return {'status': 'exact contradiction', 'complete': True,
                                'records': records, 'values': values, 'sweeps': sweeps}
            for identifier in range(len(raw)//RECORD_BYTES):
                if identifier % 128 == 0:
                    budget()
                a, bits = cover(raw, identifier)
                event = cover_event(a, bits, values, one_bits, zero_bits)
                if event and record(event, {'family': 'cover', 'id': identifier}, [a, *members(bits)]):
                    return {'status': 'exact contradiction', 'complete': True,
                            'records': records, 'values': values, 'sweeps': sweeps}
            if len(records) == before:
                return {'status': 'exact interval and guarded-cover fixed point', 'complete': True,
                        'records': records, 'values': values, 'sweeps': sweeps}
    except TimeoutError:
        return {'status': 'partial exact propagation; time limit reached', 'complete': False,
                'records': records, 'values': values, 'sweeps': sweeps}


def verify_trace(n, rows, raw, report):
    """Replay each reason using conditional extrema, without row_event."""
    values, reasons = [-1]*n, [-1]*n
    contradiction = False
    for index, item in enumerate(report['records']):
        assert not contradiction
        origin = item['origin']
        if origin['family'] == 'base_row':
            r = rows[origin['id']]
        else:
            assert origin['family'] == 'cover'
            a, bits = cover(raw, origin['id'])
            r = row([[a, -1]]+[[b, 1] for b in members(bits)], 0, bits.bit_count(), 'cover', origin['id'])
        support = [a for a, c in r['terms']]
        assert item['prior_assignment_indices'] == sorted({reasons[a] for a in support if values[a] != -1})
        conditional = list(values)
        if item['kind'] == 'assignment':
            a, value = item['variable'], item['value']
            assert values[a] == -1 and value in (0, 1) and a in support
            assert item['forbidden_value'] == 1-value
            conditional[a] = 1-value
        else:
            assert item['kind'] == 'contradiction'
            contradiction = True
        minimum = sum(c*conditional[a] if conditional[a] != -1 else min(0, c) for a, c in r['terms'])
        maximum = sum(c*conditional[a] if conditional[a] != -1 else max(0, c) for a, c in r['terms'])
        assert minimum > r['upper'] or maximum < r['lower']
        if origin['family'] == 'base_row':
            original_low = sum(c*values[a] if values[a] != -1 else min(0, c) for a, c in r['terms'])
            original_high = sum(c*values[a] if values[a] != -1 else max(0, c) for a, c in r['terms'])
            assert item['original_minimum'] == original_low and item['original_maximum'] == original_high
            if not contradiction:
                assert item['conditional_minimum'] == minimum and item['conditional_maximum'] == maximum
        if not contradiction:
            original_low = sum(c*values[a] if values[a] != -1 else min(0, c) for a, c in r['terms'])
            original_high = sum(c*values[a] if values[a] != -1 else max(0, c) for a, c in r['terms'])
            assert original_low <= r['upper'] and original_high >= r['lower']
            values[item['variable']] = item['value']
            reasons[item['variable']] = index
    assert values == report['values']
    assert contradiction == (report['status'] == 'exact contradiction')
    if report['complete'] and not contradiction:
        # Recheck every conditional interval directly, without using the
        # forward row-event routine that generated the trace.
        for r in rows:
            low = sum(c*values[a] if values[a] != -1 else min(0, c) for a, c in r['terms'])
            high = sum(c*values[a] if values[a] != -1 else max(0, c) for a, c in r['terms'])
            assert low <= r['upper'] and high >= r['lower']
            for a, c in r['terms']:
                if values[a] == -1:
                    for value in (0, 1):
                        trial = {b: values[b] for b, _ in r['terms']}
                        trial[a] = value
                        minimum = sum(w*trial[b] if trial[b] != -1 else min(0, w) for b, w in r['terms'])
                        maximum = sum(w*trial[b] if trial[b] != -1 else max(0, w) for b, w in r['terms'])
                        assert minimum <= r['upper'] and maximum >= r['lower']
        ones = sum(1 << a for a, value in enumerate(values) if value == 1)
        zeros = sum(1 << a for a, value in enumerate(values) if value == 0)
        for identifier in range(len(raw)//RECORD_BYTES):
            a, bits = cover(raw, identifier)
            if values[a] != 0 and not bits & ones:
                remaining = bits & ~zeros
                assert remaining
                assert values[a] != 1 or remaining.bit_count() >= 2
    return {'all_records_checked': len(report['records']), 'contradiction': contradiction,
            'complete_fixed_point_rechecked': report['complete'] and not contradiction}


def controls(output):
    assert not output.exists()
    assignments = list(product((0, 1), repeat=3))
    partials = list(product((-1, 0, 1), repeat=3))
    compatible = {p: [v for v in assignments if all(a == -1 or a == b for a, b in zip(p, v))] for p in partials}
    counts = Counter()
    for coefficients in product(range(-2, 3), repeat=3):
        terms = [[a, c] for a, c in enumerate(coefficients) if c]
        weights = {v: sum(c*x for c, x in zip(coefficients, v)) for v in assignments}
        for lower in range(-3, 4):
            for upper in range(lower, 4):
                r = row(terms, lower, upper, 'control', 0)
                for p in partials:
                    event = row_event(r, p)
                    feasible = [v for v in compatible[p] if lower <= weights[v] <= upper]
                    if event is not None:
                        if event['kind'] == 'contradiction':
                            assert not feasible
                        else:
                            assert all(v[event['variable']] == event['value'] for v in feasible)
                    counts['signed_row_partial_truth_assignments'] += 1
    for a in range(4):
        others = [b for b in range(4) if b != a]
        for chosen in range(8):
            bits = sum(1 << b for i, b in enumerate(others) if chosen >> i & 1)
            for p in product((-1, 0, 1), repeat=4):
                ones = sum(1 << b for b, v in enumerate(p) if v == 1)
                zeros = sum(1 << b for b, v in enumerate(p) if v == 0)
                event = cover_event(a, bits, p, ones, zeros)
                feasible = [v for v in product((0, 1), repeat=4)
                            if all(x == -1 or x == y for x, y in zip(p, v))
                            and (v[a] == 0 or any(v[b] for b in members(bits)))]
                if event:
                    if event['kind'] == 'contradiction':
                        assert not feasible
                    else:
                        assert all(v[event['variable']] == event['value'] for v in feasible)
                counts['guarded_cover_partial_truth_assignments'] += 1
    raw = b''.join(struct.pack('<H', a)+bits.to_bytes(MASK_BYTES, 'little')
                   for a, bits in ((0, 0), (3, 1 << 2)))
    rows = [row([[0, 1], [1, 1]], 1, 1, 'control', 0),
            row([[1, 1], [2, 1]], 0, 1, 'control', 1)]
    closed = propagate(4, rows, raw, [0], 10)
    assert closed['complete'] and closed['values'] == [0, 1, 0, 0]
    verify_trace(4, rows, raw, closed)
    inconsistent = rows+[row([[3, 1]], 1, 1, 'control', 2)]
    proof = propagate(4, inconsistent, raw, [0], 10)
    assert proof['status'] == 'exact contradiction'
    verify_trace(4, inconsistent, raw, proof)
    huge = row([[0, 1 << 100], [1, -(1 << 99)]], 1 << 100, 1 << 100, 'bigint', 0)
    bigproof = propagate(2, [huge], b'', [], 10)
    assert bigproof['values'] == [1, 0]
    verify_trace(2, [huge], b'', bigproof)
    report = {'status': 'PASS: exact signed Boolean bounds, cover rules and reason-chain replay',
              'source_sha256': digest(Path(__file__)), 'counts': dict(counts),
              'satisfiable_chain': closed, 'inconsistent_chain': proof,
              'integer100_bit_control': bigproof,
              'case4_closure_run': False, 'failed_literal_probing_run': False,
              'solver_or_optimizer_called': False}
    save(output, report)
    print(json.dumps({k: v for k, v in report.items() if not k.endswith('chain')}, indent=2))


def prepare(output, control_path):
    assert not output.exists()
    control = json.loads(control_path.read_text())
    assert control['status'].startswith('PASS:') and control['source_sha256'] == digest(Path(__file__))
    rows, raw, units, bindings = load_inventory()
    report = {'status': 'complete native-constraint exact propagation inventory prepared; no case4 closure',
        'source_sha256': digest(Path(__file__)), 'complete': True, 'bindings': bindings,
        'controls_sha256': digest(control_path), 'variables': N,
        'base_integer_rows': len(rows), 'base_term_occurrences': sum(len(r['terms']) for r in rows),
        'family_counts': dict(Counter(r['family'] for r in rows)),
        'complete_external_covers': len(raw)//RECORD_BYTES,
        'initial_unit_clause_ids': units, 'initial_absent_columns': [cover(raw, i)[0] for i in units],
        'all1365_triple_capacities_retained': True, 'all60_uncapped_row_inequalities_retained': True,
        'all178533_covers_retained': True,
        'rule': 'A Boolean value is excluded only if its exact conditional integer interval misses the original row bounds.',
        'prior_assignment_indices_required_for_every_reason': True,
        'maximum_new_primary_assignments': N, 'maximum_records_including_final_contradiction': N+1,
        'maximum_complete_monotone_sweeps': N+1, 'repeat_assignment_refused': True,
        'arbitrary_precision_integer_arithmetic': True,
        'no_native_presolve_inference_trusted': True,
        'case4_closure_run': False, 'failed_literal_probing_run': False,
        'solver_or_optimizer_called': False, 'case4_excluded': False}
    save(output, report)
    print(json.dumps(report, indent=2))
    print('preparation_sha256', digest(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='mode', required=True)
    test = sub.add_parser('controls')
    test.add_argument('--output', type=Path, required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--controls', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.mode == 'controls':
        controls(args.output.resolve())
    else:
        prepare(args.output.resolve(), args.controls.resolve())
