"""Exact row compression of the complete case4 real selector LP.

No optimizer is imported. Every removed cover receives one retained input-row
witness. The same unit-box feasible set is preserved in both directions.
"""

import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import itertools
import json
from pathlib import Path
import resource
import time

import numpy as np

INPUT_NPZ_SHA = 'fb9ba6b1185f7796e39ac2904f077ad58238e89b0445305a22238c0374dd158f'
INPUT_STREAM_SHA = '444835c4d3c466dc9bb5c71646da13bf98e6eefdb3a492c51bcf54185b8919d5'
RECOVERY_SOURCE_SHA = 'e577327c9cc2471f119c755a49a179b9f94f1004a22de80152a4114787a7eec6'
N, M, NNZ, NATIVE = 1156, 174208, 11868882, 1992
ARRAY_NAMES = {'coefficients', 'column_indices', 'row_pointers', 'row_lower',
               'row_upper', 'row_origin_kind', 'row_origin_index', 'original_column_ids'}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def save(path, value):
    temporary = path.with_name(path.name+'.partial')
    assert not path.exists() and not temporary.exists()
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)


def save_gzip(path, value):
    raw = canonical(value)+b'\n'
    assert not path.exists()
    path.write_bytes(gzip.compress(raw, mtime=0))
    return {'path': path.name, 'sha256': digest(path.read_bytes()),
            'decompressed_sha256': digest(raw), 'decompressed_bytes': len(raw)}


def tick(deadline):
    if time.monotonic() > deadline:
        raise TimeoutError('bounded exact cover compression')


def load_arrays(path):
    assert digest(path.read_bytes()) == INPUT_NPZ_SHA
    with np.load(path, allow_pickle=False) as archive:
        assert set(archive.files) == ARRAY_NAMES
        arrays = {name: archive[name] for name in archive.files}
    assert all(value.dtype.kind in 'iu' for value in arrays.values())
    assert len(arrays['coefficients']) == len(arrays['column_indices']) == NNZ
    assert len(arrays['row_pointers']) == M+1
    assert int(arrays['row_pointers'][0]) == 0 and int(arrays['row_pointers'][-1]) == NNZ
    assert np.all(arrays['row_pointers'][1:] > arrays['row_pointers'][:-1])
    assert len(arrays['row_lower']) == len(arrays['row_upper']) == M
    assert np.all(arrays['row_lower'] <= arrays['row_upper'])
    assert np.all(arrays['row_origin_kind'][:NATIVE] == 0)
    assert np.all(arrays['row_origin_kind'][NATIVE:] == 1)
    assert np.all(arrays['row_origin_index'][1:NATIVE] > arrays['row_origin_index'][:NATIVE-1])
    assert np.all(arrays['row_origin_index'][NATIVE+1:] > arrays['row_origin_index'][NATIVE:-1])
    ids = arrays['original_column_ids']
    assert len(ids) == N and np.all(ids[1:] > ids[:-1]) and int(ids[-1]) < 1214
    assert len(set(range(1214))-set(map(int, ids))) == 58
    assert int(np.min(arrays['column_indices'])) >= 0 and int(np.max(arrays['column_indices'])) < N
    return arrays


def terms(arrays, row):
    start, stop = map(int, arrays['row_pointers'][row:row+2])
    return list(zip(map(int, arrays['column_indices'][start:stop]),
                    map(int, arrays['coefficients'][start:stop])))


def decode(arrays, deadline):
    covers, groups, grams, weighted = {}, defaultdict(list), {}, {}
    for row in range(M):
        if row % 1024 == 0:
            tick(deadline)
        pairs = terms(arrays, row)
        assert pairs == sorted(pairs) and len({a for a, c in pairs}) == len(pairs)
        if row < NATIVE:
            origin = int(arrays['row_origin_index'][row])
            if origin < 630:
                quota = int(arrays['row_lower'][row])
                assert quota == int(arrays['row_upper'][row]) and quota > 0
                assert all(c == 1 for a, c in pairs)
                grams[row] = (sum(1 << a for a, c in pairs), quota)
            elif origin >= 2211:
                negative = [(a, -c) for a, c in pairs if c < 0]
                assert len(negative) == 1 and int(arrays['row_lower'][row]) == 0
                guard, demand = negative[0]
                positive = [(a, c) for a, c in pairs if c > 0]
                assert len(positive)+1 == len(pairs) and demand > 0
                if max(c for a, c in positive) <= demand:
                    weighted[row] = (guard, sum(1 << a for a, c in positive), demand)
            continue
        negative = [(a, c) for a, c in pairs if c < 0]
        assert len(negative) == 1 and negative[0][1] == -1
        guard = negative[0][0]
        positive = [a for a, c in pairs if c > 0]
        assert len(positive)+1 == len(pairs) and all(c in (-1, 1) for a, c in pairs)
        assert positive and int(arrays['row_lower'][row]) == 0
        assert int(arrays['row_upper'][row]) == len(positive)
        bits = sum(1 << a for a in positive)
        assert not (bits >> guard & 1)
        covers[row] = (guard, bits)
        groups[guard].append(row)
    assert len(grams) == 396 and len(covers) == 172216
    return covers, groups, grams, weighted


def minimal_same_guard(covers, groups, deadline):
    retained, witnesses, comparisons = [], {}, 0
    per_guard = []
    for guard in sorted(groups):
        tick(deadline)
        candidates = sorted(groups[guard], key=lambda r: (covers[r][1].bit_count(), covers[r][1], r))
        kept = []
        for row in candidates:
            support = covers[row][1]
            witness = None
            for other in kept:
                comparisons += 1
                if comparisons % 65536 == 0:
                    tick(deadline)
                if covers[other][1] & support == covers[other][1]:
                    witness = other
                    break
            if witness is None:
                kept.append(row)
            else:
                witnesses[row] = witness
        retained.extend(kept)
        per_guard.append({'guard': guard, 'before': len(candidates), 'minimal': len(kept)})
    return retained, witnesses, comparisons, per_guard


def native_witness(support, guard, grams, weighted):
    for row, (same_guard, smaller, demand) in weighted.items():
        if same_guard == guard and smaller & support == smaller:
            return ['weighted_same_guard', row]
    for row, (family, quota) in grams.items():
        if (family & ~support).bit_count() <= quota-1:
            return ['Gram_unit_box', row]
    return None


def compress(arrays, covers, groups, grams, weighted, deadline):
    minimal, previous, comparisons, per_guard = minimal_same_guard(covers, groups, deadline)
    native = {}
    for i, row in enumerate(minimal):
        if i % 128 == 0:
            tick(deadline)
        guard, support = covers[row]
        witness = native_witness(support, guard, grams, weighted)
        if witness is not None:
            native[row] = witness
    retained_covers = sorted(row for row in minimal if row not in native)
    omissions = []
    for row in sorted(covers):
        if row in native:
            omissions.append([row, *native[row]])
        elif row in previous:
            witness = previous[row]
            # Replace any discarded intermediate cover by its retained native row.
            if witness in native:
                omissions.append([row, *native[witness]])
            else:
                omissions.append([row, 'same_guard_subset', witness])
    certificate = {
        'status': 'COMPLETE_EXACT_REAL_LP_ROW_COMPRESSION',
        'source_sha256': digest(Path(__file__).read_bytes()),
        'input_npz_sha256': INPUT_NPZ_SHA,
        'input_canonical_integer_stream_sha256': INPUT_STREAM_SHA,
        'published_recovery_source_sha256': RECOVERY_SOURCE_SHA,
        'original_columns': N, 'original_rows': M, 'original_nonzeros': NNZ,
        'unchanged_unit_box': [0, 1],
        'all_native_input_rows_retained': list(range(NATIVE)),
        'retained_cover_input_rows': retained_covers,
        'omitted_cover_witnesses': omissions,
        'same_guard_stage': {'retained_covers_before_native_screen': len(minimal),
            'removed_covers': len(previous), 'subset_comparisons': comparisons,
            'per_guard': per_guard},
        'native_screen': {'Gram_rows_available': len(grams),
            'eligible_weighted_rows': len(weighted),
            'minimal_covers_removed': len(native),
            'witness_counts': dict(Counter(w[0] for w in native.values()))},
        'proof_rules': {
            'same_guard_subset': 'Retained T subset S gives sum_S x-x_guard >= sum_T x-x_guard >= 0.',
            'Gram_unit_box': 'sum_E x=q and |E minus S|<=q-1 imply sum_S x>=q-|E minus S|>=1>=x_guard.',
            'weighted_same_guard': 'Retained sum_T w_b*x_b>=d*x_guard, with0<w_b<=d and T subset S, implies sum_S x>=x_guard.',
            'upper_bounds': 'Every removed cover upper bound follows from0<=x<=1: sum_S x-x_guard<=|S|.'},
        'every_omission_has_one_final_retained_input_row': True,
        'Boolean_integrality_used': False, 'optimizer_called': False,
        'case4_excluded': False}
    return certificate


def verify_certificate(arrays, covers, groups, grams, weighted, certificate):
    assert certificate['source_sha256'] == digest(Path(__file__).read_bytes())
    assert certificate['input_npz_sha256'] == INPUT_NPZ_SHA
    assert certificate['input_canonical_integer_stream_sha256'] == INPUT_STREAM_SHA
    assert certificate['all_native_input_rows_retained'] == list(range(NATIVE))
    keep = certificate['retained_cover_input_rows']
    assert keep == sorted(set(keep)) and all(row in covers for row in keep)
    kept = set(keep)
    seen = set(keep)
    rule_counts, duplicate_count = Counter(), 0
    for row, kind, witness in certificate['omitted_cover_witnesses']:
        assert row in covers and row not in seen
        seen.add(row)
        guard, support = covers[row]
        if kind == 'same_guard_subset':
            assert witness in kept
            other_guard, other_support = covers[witness]
            assert guard == other_guard and other_support & support == other_support
            duplicate_count += support == other_support
        elif kind == 'Gram_unit_box':
            assert witness in grams and witness < NATIVE
            family, quota = grams[witness]
            assert quota-(family & ~support).bit_count()-1 >= 0
        else:
            assert kind == 'weighted_same_guard' and witness in weighted and witness < NATIVE
            other_guard, other_support, demand = weighted[witness]
            assert other_guard == guard and other_support & support == other_support and demand > 0
        rule_counts[kind] += 1
    assert seen == set(covers) and len(seen) == 172216
    # Verify the final same-guard antichain without rerunning the selection algorithm.
    for rows in groups.values():
        selected = sorted((row for row in rows if row in kept), key=lambda r: covers[r][1].bit_count())
        for i, row in enumerate(selected):
            support = covers[row][1]
            assert all(covers[other][1] & support != covers[other][1] for other in selected[:i])
    retained = list(range(NATIVE))+keep
    nonzeros = sum(int(arrays['row_pointers'][r+1]-arrays['row_pointers'][r]) for r in retained)
    return {'status': 'PASS: every original row accounted for and every omission directly implied',
        'input_rows_checked': M, 'unchanged_native_rows': NATIVE,
        'input_cover_rows_checked': len(covers), 'retained_cover_rows': len(keep),
        'removed_cover_rows': len(covers)-len(keep), 'retained_rows': len(retained),
        'retained_nonzeros': nonzeros, 'omission_rule_counts': dict(rule_counts),
        'same_guard_identical_support_witnesses': duplicate_count,
        'final_same_guard_antichain_checked': True,
        'equivalent_over_all_real_unit_box_points': True,
        'optimizer_called': False, 'case4_excluded': False}, retained


def project_arrays(arrays, retained):
    spans = [(int(arrays['row_pointers'][r]), int(arrays['row_pointers'][r+1])) for r in retained]
    lengths = np.asarray([stop-start for start, stop in spans], dtype='<i8')
    projected = {
        'coefficients': np.concatenate([arrays['coefficients'][start:stop] for start, stop in spans]),
        'column_indices': np.concatenate([arrays['column_indices'][start:stop] for start, stop in spans]),
        'row_pointers': np.concatenate((np.asarray([0],dtype='<i8'),np.cumsum(lengths,dtype='<i8'))),
        'row_lower': arrays['row_lower'][retained], 'row_upper': arrays['row_upper'][retained],
        'row_origin_kind': arrays['row_origin_kind'][retained],
        'row_origin_index': arrays['row_origin_index'][retained],
        'original_column_ids': arrays['original_column_ids'],
        'retained_input_rows': np.asarray(retained,dtype='<i4')}
    assert int(projected['row_pointers'][-1]) == len(projected['coefficients'])
    return projected


def controls():
    covers = {0:(0,1<<1), 1:(0,(1<<1)|(1<<2)), 2:(0,1<<2), 3:(0,1<<1), 4:(1,1<<2)}
    groups = {0:[0,1,2,3],1:[4]}
    kept, removed, _comparisons, _groups = minimal_same_guard(covers,groups,time.monotonic()+5)
    assert set(kept) == {0,2,4} and removed == {3:0,1:0}
    points = 0
    for z in itertools.product(range(3),repeat=3):
        original = all(sum(z[a] for a in range(3) if support>>a&1) >= z[guard] for guard,support in covers.values())
        compressed = all(sum(z[a] for a in range(3) if covers[row][1]>>a&1) >= z[covers[row][0]] for row in kept)
        assert original == compressed
        points += 1
    return {'exact_fractional_grid_points': points,
        'duplicate_strict_subset_and_distinct_guard_control': True,
        'optimizer_called': False}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['prepare','replay'])
    parser.add_argument('--arrays',type=Path,required=True)
    parser.add_argument('--directory',type=Path,required=True)
    parser.add_argument('--seconds',type=int,default=120)
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    assert 0 < args.seconds <= 120
    started = time.monotonic()
    deadline = started+args.seconds
    arrays = load_arrays(args.arrays)
    decoded = decode(arrays,deadline)
    if args.mode == 'prepare':
        assert not args.directory.exists()
        args.directory.mkdir(parents=True)
        outcome = {'status':'RUNNING exact equivalent-row compression','source_sha256':digest(Path(__file__).read_bytes()),
                   'input_npz_sha256':INPUT_NPZ_SHA,'optimizer_called':False,'case4_excluded':False}
        try:
            control = controls()
            certificate = compress(arrays,*decoded,deadline)
            tick(deadline)
            check, retained = verify_certificate(arrays,*decoded,certificate)
            tick(deadline)
            projected = project_arrays(arrays,retained)
            certificate['verified_counts'] = check
            certificate['compressed_array_sha256'] = {name:digest(value.tobytes(order='C')) for name,value in projected.items()}
            binding = save_gzip(args.directory/'certificate.json.gz',certificate)
            path = args.directory/'arrays.npz'
            np.savez_compressed(path,**projected)
            outcome.update(status='COMPLETE_EXACT_REAL_LP_ROW_COMPRESSION',controls=control,
                same_guard_stage={k:v for k,v in certificate['same_guard_stage'].items() if k!='per_guard'},
                native_screen=certificate['native_screen'],verified_counts=check,certificate=binding,
                arrays={'path':path.name,'sha256':digest(path.read_bytes()),'bytes':path.stat().st_size})
        except Exception as error:
            outcome.update(status='INCOMPLETE: no compressed model accepted',error_type=type(error).__name__,error_message=str(error))
            raise
        finally:
            outcome.update(elapsed_seconds=time.monotonic()-started,peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
            save(args.directory/'preparation.json',outcome)
    else:
        assert args.output is not None and not args.output.exists()
        saved = json.loads((args.directory/'preparation.json').read_text())
        item = saved['certificate']
        compressed = (args.directory/item['path']).read_bytes()
        assert digest(compressed) == item['sha256']
        raw = gzip.decompress(compressed)
        assert digest(raw) == item['decompressed_sha256'] and len(raw) == item['decompressed_bytes']
        certificate = json.loads(raw)
        check, retained = verify_certificate(arrays,*decoded,certificate)
        assert check == certificate['verified_counts'] == saved['verified_counts']
        projected = project_arrays(arrays,retained)
        assert {name:digest(value.tobytes(order='C')) for name,value in projected.items()} == certificate['compressed_array_sha256']
        path = args.directory/saved['arrays']['path']
        assert digest(path.read_bytes()) == saved['arrays']['sha256']
        with np.load(path,allow_pickle=False) as archive:
            assert set(archive.files) == set(projected)
            assert all(np.array_equal(archive[name],value) for name,value in projected.items())
        outcome = dict(check,elapsed_seconds=time.monotonic()-started,
            source_sha256=digest(Path(__file__).read_bytes()),preparation_sha256=digest((args.directory/'preparation.json').read_bytes()),
            all_compressed_arrays_reconstructed=True,certificate_directly_replayed=True)
        save(args.output,outcome)
    print(json.dumps(outcome,indent=2),flush=True)


if __name__ == '__main__':
    main()
