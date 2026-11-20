"""Rebuild the complete case4 selector LP from three published inputs.

No lost checkpoint43 file, solver, OR-Tools, SciPy, or ancestor builder is
imported. NumPy is used only to store/replay typed sparse arrays. All row
assembly, zero proofs, substitutions and hashes use exact integers.
"""

import argparse
from array import array
from collections import Counter
import gzip
import hashlib
from itertools import product
import json
from pathlib import Path
import resource
import signal
import struct
import sys
import time

import numpy as np

ROOT = Path(__file__).resolve().parents[2]
INPUTS = {
    'native_model': {
        'path': 'experiments/logs/grids-and-triangles/complement-rook-35core-case0004-native-cpsat-model.json',
        'sha256': 'a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476',
        'git_blob': '89fece302243da184766735c7517aa67f00a0dbe'},
    'registry_metadata': {
        'path': 'experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lazy-native-model.json',
        'sha256': 'aeb636198cb0b9749e2142a596404181edf92923d55d5bdf764a8f9432439b68',
        'git_blob': '81e2234210465fef33d164207d37c4aa7a530560'},
    'registry': {
        'path': 'experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lazy-native-registry.bin.gz',
        'sha256': 'c32e31d9ce6ec6168cea1c9f6c6ea4165a2ca7a8f2144a59a31e5a1d6da7b543',
        'git_blob': 'd37d004e2d044f91e3fef5667a33640e602280c9'},
}
PRIMARY_SHA = '5a6af30f47826df629a3795ceea0a0a91b853cf8149860355ce1bd17ac0094b2'
RAW_REGISTRY_SHA = '3b819e29bc9aacdb5217b151f32b35cb186aa3b8a93a37784edc912ddac36736'
COVER_DIMACS_SHA = '6f4ccc4623e4a7b9a40236f84f05e1a3973dd8b1d6f95a82a5ff0b66e699a24a'
COVER_CERTIFICATE_SHA = 'a255f8876d3d827ff94d7df2f2640be6963348987043665dcd6fc53bf41dff8f'
EXPECTED_STREAM = '444835c4d3c466dc9bb5c71646da13bf98e6eefdb3a492c51bcf54185b8919d5'
EXPECTED_COUNTS = {
    'tautological_Gram': 234, 'retained_Gram': 396,
    'retained_original_signature': 186,
    'retained_core_triple': 1348, 'tautological_core_triple': 17,
    'retained_Gram_conflict': 4, 'tautological_Gram_conflict': 26,
    'retained_uncapped_row_cut': 58, 'tautological_uncapped_row_cut': 2,
    'retained_cover': 172216, 'tautological_cover': 6317,
}
EXPECTED_GRAM_ZEROS = [
    235,241,252,258,263,302,309,315,329,335,342,348,352,354,356,359,
    363,367,368,371,375,385,387,388,392,396,397,398,400,404,408,410,
    413,415,417,420,424,428,430,435,437,442,457,459,461,465]
EXPECTED_UNITS = [352,353,354,355,439,552,553,645,869,873,957,1080,1081,1167]
N = 1214
RECORD_BYTES = 154
HEADER = struct.Struct('<BIqqI')
TERM = struct.Struct('<Iq')
MAX_SECONDS = 180
MAX_RSS_KIB = 1048576


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def members(bits):
    while bits:
        bit = bits & -bits
        yield bit.bit_length()-1
        bits ^= bit


def checked_inputs(root):
    payloads = {}
    for name, item in INPUTS.items():
        raw = (root/item['path']).read_bytes()
        assert digest(raw) == item['sha256'], ('input raw hash', name)
        payloads[name] = raw
    native = json.loads(payloads['native_model'])
    metadata = json.loads(payloads['registry_metadata'])
    assert native['complete'] and metadata['complete']
    inventory = native['primary_inventory']
    assert digest(canonical(inventory)) == native['primary_inventory_sha256'] == PRIMARY_SHA
    assert metadata['primary_inventory_sha256'] == PRIMARY_SHA
    assert inventory['primary_variables'] == N
    assert inventory['case']['index'] == inventory['case']['matching_index'] == 4
    assert inventory['case']['local_set_orbit'] == 0
    assert metadata['native_model_sha256'] == INPUTS['native_model']['sha256']
    assert metadata['registry'] == INPUTS['registry']['path']
    assert metadata['registry_sha256'] == INPUTS['registry']['sha256']
    assert metadata['registry_metadata']['cover_certificate_sha256'] == COVER_CERTIFICATE_SHA
    assert inventory['complete_cover_certificate_sha256'] == COVER_CERTIFICATE_SHA
    raw = gzip.decompress(payloads['registry'])
    assert digest(raw) == metadata['registry_metadata']['decompressed_sha256'] == RAW_REGISTRY_SHA
    assert len(raw) == metadata['registry_metadata']['decompressed_bytes'] == 27494082
    assert len(raw) == 178533*RECORD_BYTES
    return inventory, metadata, raw


def normalize_row(terms, lower, upper, family):
    assert type(lower) is type(upper) is int and lower <= upper
    coefficients = Counter()
    for a, c in terms:
        assert type(a) is type(c) is int and 0 <= a < N
        coefficients[a] += c
    return {'terms': [[a, c] for a, c in sorted(coefficients.items()) if c],
            'lower': lower, 'upper': upper, 'family': family}


def original_rows(inventory):
    rows = []
    for i, j, quota, support in inventory['Gram_rows']:
        rows.append(normalize_row([[a, 1] for a in support], quota, quota, 'Gram'))
    for original, support in inventory['original_signature_rows']:
        rows.append(normalize_row([[a, 1] for a in support], 0, 1, 'original_signature'))
    for item in inventory['triple_rows']:
        rows.append(normalize_row([[a, 1] for a in item['members']], 0, 1, 'core_triple'))
    for clause in inventory['Gram_conflict_clauses']:
        assert len(clause) == 2 and all(type(v) is int and v < 0 for v in clause)
        rows.append(normalize_row([[-v-1, 1] for v in clause], 0, 1, 'Gram_conflict'))
    for cut in inventory['uncapped_integer_cuts']:
        target, demand = cut['target_column'], cut['positive_demand']
        assert type(demand) is int and demand > 0
        assert all(type(w) is int and w > 0 for a, w in cut['positive_terms'])
        terms = [[a, w] for a, w in cut['positive_terms']] + [[target, -demand]]
        rows.append(normalize_row(terms, 0, sum(w for a, w in cut['positive_terms']), 'uncapped_row_cut'))
    assert Counter(row['family'] for row in rows) == {
        'Gram': 630, 'original_signature': 186, 'core_triple': 1365,
        'Gram_conflict': 30, 'uncapped_row_cut': 60}
    assert len(rows) == 2271
    return rows


def prove_Gram_zeros(inventory):
    expected_pairs = [(i, j) for i in range(35) for j in range(i, 35)]
    entries = inventory['Gram_rows']
    assert [(i, j) for i, j, q, s in entries] == expected_pairs
    masks = [0]*N
    targets = [[0]*35 for _ in range(35)]
    for i, j, q, support in entries:
        assert support == sorted(set(support))
        assert type(q) is int and q >= 0
        targets[i][j] = targets[j][i] = q
        if i == j:
            for a in support:
                masks[a] |= 1 << i
    for i, j, q, support in entries:
        actual = [a for a, h in enumerate(masks) if (h >> i & 1) and (h >> j & 1)]
        assert actual == support
    assert targets[3][27] == targets[4][27] == 1 and targets[17][27] == 2
    coefficients = [((h >> 3 & 1)+(h >> 4 & 1)-(h >> 17 & 1))*(h >> 27 & 1) for h in masks]
    assert set(coefficients) == {0, 1}
    zeros = [a for a, c in enumerate(coefficients) if c]
    assert zeros == EXPECTED_GRAM_ZEROS
    return zeros, {
        'row_combination': [[[3, 27], 1], [[4, 27], 1], [[17, 27], -1]],
        'right_hand_side': 0,
        'all1214_coefficients_zero_or_one': True,
        'positive_coefficient_columns': zeros,
        'all630_supports_reconstructed_from_diagonals': True,
        'premise': 'nonnegative real Gram weights only'}


def registry_entry(raw, identifier):
    offset = RECORD_BYTES*identifier
    target = struct.unpack_from('<H', raw, offset)[0]
    bits = int.from_bytes(memoryview(raw)[offset+2:offset+RECORD_BYTES], 'little')
    return target, bits


def audit_registry(raw, metadata):
    body = hashlib.sha256()
    units, unit_ids, literals = [], [], 0
    previous = -1
    for identifier in range(178533):
        a, bits = registry_entry(raw, identifier)
        assert previous <= a < N and bits < 1 << N and not (bits >> a & 1)
        previous = a
        body.update((' '.join(map(str, [-a-1]+[b+1 for b in members(bits)]))+' 0\n').encode())
        literals += 1+bits.bit_count()
        if not bits:
            units.append(a)
            unit_ids.append(identifier)
    assert literals == 12887146
    assert body.hexdigest() == COVER_DIMACS_SHA == metadata['registry_metadata']['canonical_DIMACS_body_sha256']
    assert units == EXPECTED_UNITS == metadata['registry_metadata']['initial_unit_targets']
    assert unit_ids == metadata['initial_prefix_clause_ids_in_order']
    return units, {'records': 178533, 'literal_occurrences': literals,
        'canonical_DIMACS_body_sha256': body.hexdigest(),
        'unit_clause_ids': unit_ids, 'unit_targets': units,
        'necessity_provenance': 'the published complete ordered-pair/implication ledger bound by cover_certificate_sha256',
        'cover_certificate_sha256': COVER_CERTIFICATE_SHA}


def projected(terms, lower, upper, position):
    terms = [[position[a], c] for a, c in terms if a in position]
    assert terms == sorted(terms)
    minimum = sum(c for _, c in terms if c < 0)
    maximum = sum(c for _, c in terms if c > 0)
    assert lower <= maximum and upper >= minimum, 'box contradiction after fixed zeros'
    return terms, minimum, maximum, lower <= minimum and maximum <= upper


def controls():
    tests = 0
    for n in range(1, 5):
        for coefficients in product((-1, 0, 1), repeat=n):
            for zero_mask in range(1 << n):
                kept = [a for a in range(n) if not (zero_mask >> a & 1)]
                position = {a: j for j, a in enumerate(kept)}
                terms = [[a, c] for a, c in enumerate(coefficients) if c]
                reduced, low, high, _ = projected(terms, -n, n, position)
                values = [sum(c*point[a] for a, c in reduced) for point in product((0, 1), repeat=len(kept))]
                assert min(values) == low and max(values) == high
                for lower, upper in ((low, high), (low-1, high+1), (low, low), (high, high)):
                    _, _, _, omitted = projected(terms, lower, upper, position)
                    assert omitted == all(lower <= value <= upper for value in values)
                    tests += 1
    clauses = 0
    for n in range(1, 5):
        for target in range(n):
            others = [a for a in range(n) if a != target]
            for subset in range(1 << (n-1)):
                cover = [a for k, a in enumerate(others) if subset >> k & 1]
                for point in product((0, 1), repeat=n):
                    lhs = sum(point[a] for a in cover)-point[target]
                    assert ((not point[target]) or any(point[a] for a in cover)) == (0 <= lhs <= len(cover))
                    clauses += 1
    assert (tests, clauses) == (6216, 626)
    return {'exact_box_tautology_controls': tests, 'complete_small_cover_linearizations': clauses,
            'optimizer_called': False}


def build(root):
    assert sys.byteorder == 'little'
    inventory, metadata, registry = checked_inputs(root)
    rows = original_rows(inventory)
    gram_zeros, gram_certificate = prove_Gram_zeros(inventory)
    units, registry_check = audit_registry(registry, metadata)
    zeros = sorted(set(gram_zeros) | set(units))
    assert len(zeros) == 58 and len(set(gram_zeros) & set(units)) == 2
    kept = [a for a in range(N) if a not in set(zeros)]
    assert len(kept) == 1156
    position = {a: j for j, a in enumerate(kept)}
    active_bits = sum(1 << a for a in kept)
    coefficients, indices, pointers = array('q'), array('i'), array('q', [0])
    lower_bounds, upper_bounds = array('q'), array('q')
    kinds, identifiers = array('B'), array('i')
    counts, omitted_base, omitted_cover = Counter(), [], []
    stream = hashlib.sha256()
    maximum_coefficient = 0

    def append(kind, identifier, lower, upper, terms):
        nonlocal maximum_coefficient
        assert terms and terms == sorted(terms) and len({a for a, c in terms}) == len(terms)
        assert all(0 <= a < 1156 and type(c) is int and -(1 << 63) < c < 1 << 63 for a, c in terms)
        assert -(1 << 63) <= lower <= upper < 1 << 63
        stream.update(HEADER.pack(kind, identifier, lower, upper, len(terms)))
        stream.update(b''.join(TERM.pack(a, c) for a, c in terms))
        coefficients.extend(c for a, c in terms)
        indices.extend(a for a, c in terms)
        pointers.append(len(indices))
        lower_bounds.append(lower)
        upper_bounds.append(upper)
        kinds.append(kind)
        identifiers.append(identifier)
        maximum_coefficient = max(maximum_coefficient, max(abs(c) for a, c in terms))

    for identifier, row in enumerate(rows):
        terms, minimum, maximum, omitted = projected(row['terms'], row['lower'], row['upper'], position)
        if omitted:
            counts['tautological_'+row['family']] += 1
            omitted_base.append({'original_row': identifier, 'family': row['family'],
                'box_minimum': minimum, 'box_maximum': maximum,
                'original_lower': row['lower'], 'original_upper': row['upper']})
            continue
        counts['retained_'+row['family']] += 1
        append(0, identifier, row['lower'], row['upper'], terms)
    for identifier in range(178533):
        target, bits = registry_entry(registry, identifier)
        if target not in position:
            counts['tautological_cover'] += 1
            omitted_cover.append([identifier, target])
            continue
        support = bits & active_bits
        assert support and not (support >> target & 1)
        terms = sorted([[position[target], -1]]+[[position[a], 1] for a in members(support)])
        counts['retained_cover'] += 1
        append(1, identifier, 0, support.bit_count(), terms)
    assert dict(counts) == EXPECTED_COUNTS
    assert len(lower_bounds) == 174208 and len(coefficients) == len(indices) == 11868882
    assert len(pointers) == 174209 and maximum_coefficient == 1159
    assert len(omitted_base) == 279 and len(omitted_cover) == 6317
    assert stream.hexdigest() == EXPECTED_STREAM
    arrays = {
        'coefficients': np.frombuffer(coefficients, dtype='<i8'),
        'column_indices': np.frombuffer(indices, dtype='<i4'),
        'row_pointers': np.frombuffer(pointers, dtype='<i8'),
        'row_lower': np.frombuffer(lower_bounds, dtype='<i8'),
        'row_upper': np.frombuffer(upper_bounds, dtype='<i8'),
        'row_origin_kind': np.frombuffer(kinds, dtype='u1'),
        'row_origin_index': np.frombuffer(identifiers, dtype='<i4'),
        'original_column_ids': np.asarray(kept, dtype='<u2')}
    record = {
        'status': 'complete case4 selector LP recovered exactly; no optimizer',
        'source_sha256': digest(Path(__file__).read_bytes()),
        'input_bindings': INPUTS, 'primary_inventory_sha256': PRIMARY_SHA,
        'cover_certificate_sha256': COVER_CERTIFICATE_SHA,
        'case_index': 4, 'original_columns': N,
        'fixed_zero_columns': zeros, 'Gram_zero_certificate': gram_certificate,
        'registry_check': registry_check,
        'columns': 1156, 'rows': 174208, 'nonzeros': 11868882,
        'retained_original_primary_rows': 1992, 'retained_coordinate_covers': 172216,
        'all2271_native_rows_and178533_covers_covered': True,
        'all60_uncapped_exterior_row_cuts_accounted_for': True,
        'row_inventory': dict(counts),
        'omitted_base_rows_exact_box_witnesses': omitted_base,
        'omitted_covers_fixed_zero_target_witnesses': omitted_cover,
        'canonical_integer_stream_format': '<BIqqI header(kind,original_id,lower,upper,nterms), then <Iq(reduced_column,coefficient)',
        'canonical_integer_stream_sha256': stream.hexdigest(),
        'matched_pre_outage_integer_stream': True,
        'matched_lost_local_source_bytes_claimed': False,
        'maximum_absolute_integer_coefficient': maximum_coefficient,
        'finite_variable_bounds': {'lower': 0, 'upper': 1},
        'row_bounds_are_finite_integers': True,
        'array_sha256': {name: digest(value.tobytes(order='C')) for name, value in arrays.items()},
        'uncompressed_array_bytes': sum(value.nbytes for value in arrays.values()),
        'numpy_version': np.__version__, 'python_version': sys.version,
        'optimizer_or_solver_called': False,
        'integer_incidence_or_graph_constructed': False, 'case4_excluded': False}
    assert record['uncompressed_array_bytes'] == 147480936
    return record, arrays


def write_json(path, value):
    temporary = path.with_name(path.name+'.partial')
    assert not path.exists() and not temporary.exists()
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.rename(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'replay'])
    parser.add_argument('--root', type=Path, default=ROOT)
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--model', type=Path)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    started = time.monotonic()
    def deadline(_signum, _frame):
        raise TimeoutError('bounded180second complete LP preparation/replay')
    old = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, MAX_SECONDS)
    try:
        if args.mode == 'prepare':
            assert args.directory is not None and not args.directory.exists()
            args.directory.mkdir(parents=True)
            control = controls()
            record, arrays = build(args.root.resolve())
            path = args.directory/'arrays.npz'
            temporary = args.directory/'arrays.npz.partial'
            with temporary.open('wb') as stream:
                np.savez_compressed(stream, **arrays)
            temporary.rename(path)
            with np.load(path, allow_pickle=False) as archive:
                assert set(archive.files) == set(arrays)
                for name, value in arrays.items():
                    assert np.array_equal(archive[name], value)
            record['arrays'] = {'path': 'arrays.npz', 'sha256': digest(path.read_bytes()), 'bytes': path.stat().st_size}
            record['controls'] = control
            record['preparation_seconds'] = time.monotonic()-started
            record['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
            assert record['peak_rss_kib'] <= MAX_RSS_KIB
            write_json(args.directory/'model.json', record)
            report = {key: record[key] for key in (
                'status','source_sha256','columns','rows','nonzeros','canonical_integer_stream_sha256',
                'matched_pre_outage_integer_stream','row_inventory','arrays','uncompressed_array_bytes',
                'controls','preparation_seconds','peak_rss_kib','optimizer_or_solver_called','case4_excluded')}
            report['model_sha256'] = digest((args.directory/'model.json').read_bytes())
            write_json(args.directory/'preparation.json', report)
        else:
            assert args.model is not None and args.output is not None
            saved = json.loads(args.model.read_text())
            record, arrays = build(args.root.resolve())
            assert all(saved[key] == value for key, value in record.items())
            path = args.model.parent/saved['arrays']['path']
            assert digest(path.read_bytes()) == saved['arrays']['sha256']
            with np.load(path, allow_pickle=False) as archive:
                assert set(archive.files) == set(arrays)
                for name, value in arrays.items():
                    assert np.array_equal(archive[name], value)
            report = {'status': 'PASS: complete published-input recovery and exact sparse matrix cold replay',
                'source_sha256': record['source_sha256'], 'model_sha256': digest(args.model.read_bytes()),
                'columns': 1156, 'rows': 174208, 'nonzeros': 11868882,
                'canonical_integer_stream_sha256': EXPECTED_STREAM,
                'all_omission_witnesses_replayed': True,
                'seconds': time.monotonic()-started,
                'optimizer_or_solver_called': False, 'case4_excluded': False}
            write_json(args.output, report)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    main()
