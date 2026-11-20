"""Prepare one complete high-mask packing moment matrix, without an LP.

Rows are all squarefree monomials through degree four on the 42 empty-root
high classes. Columns retain the complete pair-capacity baseline. Structural
and fixed-point zero filters are saved as explicit column maps, never as an
unrecorded change of the universal domain.
"""

import argparse
from collections import Counter
import gc
import gzip
import hashlib
from itertools import combinations
import json
from math import comb
from pathlib import Path
import pickle
import resource
import signal
import struct
import time

import numpy as np

import grid_free_order10_four_boolean_domains as old
import grid_free_order10_four_boolean_scan as contraction


ROOT = old.ROOT
WORK = ROOT/'experiments/workspace'
LOGS = ROOT/'experiments/logs/moments-and-counts'
PACKING = LOGS/'order10-high-mask-packing-domains02.json.gz'
PACKING_SHA = '27c27163aa7429d75df5d430072ece5dd045df2d54caa8a6d57a28db45db0a71'
PACKING_SOURCE_SHA = '0887869f50f0684f99bc000fd804f5400cfe59c2a5e322633d1d9b00fdf36637'
OLD_SOURCE_SHA = '52ab6687063ca4e16930013cbb159658337e8f8ce007f3d82c1d39d3c9a042d6'
CONTRACTION_SHA = '5a97b204d8830af614f22c6e72f6ca4c120ec5c6a31320b4b8841c7e0ce19286'
CERTIFICATE_HELPER = WORK/'finite_boolean_moment_certificates.py'
CERTIFICATE_HELPER_SHA = 'edd903db520a6fee0f436f5161289c394d354e739d03afe4873c3d37e7ab626c'
ROOT_TYPE = 38
INT32_MAX = (1 << 31)-1
INT64_MAX = (1 << 63)-1


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def array_digest(array):
    return hashlib.sha256(array.tobytes(order='C')).hexdigest()


def relative(path):
    return str(path.resolve().relative_to(ROOT))


def record_file(path):
    return {'path': relative(path), 'sha256': digest(path), 'bytes': path.stat().st_size}


def positions(code):
    answer = []
    while code:
        bit = code & -code
        answer.append(bit.bit_length()-1)
        code -= bit
    return answer


def layout(n):
    counts = [comb(n, d) for d in range(5)]
    offsets = [0]
    for count in counts:
        offsets.append(offsets[-1]+count)
    masks = np.zeros(offsets[-1], dtype='<u8')
    seen = np.zeros(offsets[-1], dtype=bool)
    for degree in range(5):
        for chosen in combinations(range(n), degree):
            row = offsets[degree]+sum(comb(i, j+1) for j, i in enumerate(chosen))
            assert not seen[row]
            seen[row] = True
            masks[row] = sum(1 << i for i in chosen)
    assert seen.all() and masks[0] == 0
    assert len(set(map(int, masks))) == len(masks)
    binomial = [[comb(i, d) for d in range(5)] for i in range(n)]
    return counts, offsets, masks, binomial


def column_rows(chosen, offsets, binomial):
    """Increasing colex rows; explicit loops avoid a 5.8-million-item dict."""
    answer = [0]
    answer.extend(offsets[1]+a for a in chosen)
    for j, b in enumerate(chosen):
        for a in chosen[:j]:
            answer.append(offsets[2]+a+binomial[b][2])
    for k, c in enumerate(chosen):
        for j, b in enumerate(chosen[:k]):
            for a in chosen[:j]:
                answer.append(offsets[3]+a+binomial[b][2]+binomial[c][3])
    for ell, d in enumerate(chosen):
        for k, c in enumerate(chosen[:ell]):
            for j, b in enumerate(chosen[:k]):
                for a in chosen[:j]:
                    answer.append(offsets[4]+a+binomial[b][2]+binomial[c][3]+binomial[d][4])
    assert len(answer) == sum(comb(len(chosen), d) for d in range(5))
    return answer


def controls():
    cases, entries = 0, 0
    for n in range(9):
        _, offsets, masks, table = layout(n)
        for code in range(1 << n):
            generated = column_rows(positions(code), offsets, table)
            literal = [i for i, mask in enumerate(map(int, masks)) if mask & code == mask]
            assert generated == literal
            assert generated == sorted(set(generated)) and generated[0] == 0
            cases += 1
            entries += len(generated)
    assert cases == 511
    return {'literal_boolean_columns_checked': cases,
            'literal_one_entries_checked': entries,
            'class_counts_checked': list(range(9)),
            'independent_complete_monomial_containment_comparison': True}


def inputs():
    assert digest(PACKING) == PACKING_SHA
    assert digest(WORK/'grid_free_order10_high_mask_packing_domains.py') == PACKING_SOURCE_SHA
    assert digest(Path(old.__file__)) == OLD_SOURCE_SHA
    assert digest(Path(contraction.__file__)) == CONTRACTION_SHA
    assert digest(CERTIFICATE_HELPER) == CERTIFICATE_HELPER_SHA
    packing = read(PACKING)
    assert packing['source_sha256'] == PACKING_SOURCE_SHA
    assert packing['complete'] and packing['universal_census_complete']
    assert packing['completed_root_domains'] == 62
    assert not packing['point_or_zero_pruning'] and not packing['outside_adjacency_imposed']
    atoms_path = ROOT/packing['atoms']['path']
    assert digest(atoms_path) == packing['atoms']['sha256']
    atoms = np.fromfile(atoms_path, dtype='<u8')
    assert len(atoms) == 132062 and atoms[0] == 0 and np.all(atoms[1:] > atoms[:-1])
    assert int(atoms[-1]) < (1 << 42)
    root = next(item for item in packing['roots'] if item['root_type'] == ROOT_TYPE)
    assert root['root_rows'] == [0]*6 and root['pair_quotas'] == [2]*15
    assert root['pair_quota_atom_ids'] == list(range(len(atoms)))
    assert root['global_class_indices'] == list(range(42))
    assert root['high_masks'] == packing['universal_high_masks']
    visible = np.asarray(root['visible_pair_cap_atom_ids'], dtype=np.int32)
    assert len(visible) == 90776 and visible[0] == 0 and np.all(visible[1:] > visible[:-1])
    ledger, counts, catalogue = contraction.inputs()
    old_record = next(item for item in ledger['roots'] if item['root_type'] == ROOT_TYPE)
    assert old_record['high_masks'] == root['high_masks']
    return packing, atoms, visible, ledger, old_record, counts, catalogue


def build_matrix(atoms, masks, offsets, binomial):
    cardinalities = np.asarray([int(code).bit_count() for code in atoms], dtype=np.int32)
    lengths = np.asarray([sum(comb(int(k), d) for d in range(5)) for k in cardinalities], dtype=np.int64)
    nnz = sum(map(int, lengths))
    assert nnz == 5804664 and nnz <= INT32_MAX
    assert int(lengths.max()) == 386 and len(masks) == 124314 < INT32_MAX
    indptr = np.zeros(len(atoms)+1, dtype=np.int32)
    indptr[1:] = np.cumsum(lengths, dtype=np.int64)
    assert int(indptr[-1]) == nnz
    indices = np.empty(nnz, dtype=np.int32)
    for column, code in enumerate(map(int, atoms)):
        rows = column_rows(positions(code), offsets, binomial)
        lo, hi = int(indptr[column]), int(indptr[column+1])
        assert len(rows) == hi-lo
        indices[lo:hi] = rows
    # Every stored row is distinct and is a monomial contained in its atom.
    # The exact cardinality then proves that no required monomial is missing.
    for first in range(0, len(atoms), 2048):
        last = min(first+2048, len(atoms))
        lo, hi = int(indptr[first]), int(indptr[last])
        local_lengths = lengths[first:last]
        repeated_atoms = np.repeat(atoms[first:last], local_lengths)
        row_masks = masks[indices[lo:hi]]
        assert np.all((repeated_atoms & row_masks) == row_masks)
        same_column = np.ones(max(0, hi-lo-1), dtype=bool)
        boundaries = indptr[first+1:last].astype(np.int64)-lo-1
        same_column[boundaries] = False
        assert np.all(np.diff(indices[lo:hi])[same_column] > 0)
    assert np.all(indices[indptr[:-1]] == 0)
    return indices, indptr, lengths, cardinalities


def load_root_tensor(ledger, record):
    assert digest(old.INDEX) == old.INDEX_SHA
    index = read(old.INDEX)
    assert index['point_independent_tensors'] and not index['root_or_flag_zero_pruning']
    assert index['covers_full62_family'] and index['cached_root_count'] == 62
    assert index['family_source_sha256'] == old.FAMILY_SHA
    parts = [item for item in index['cache_parts'] if ROOT_TYPE in item['root_types']]
    assert len(parts) == 1
    item = parts[0]
    assert item in ledger['cache_parts']
    path = ROOT/item['path']
    assert digest(path) == item['sha256']
    saved = pickle.loads(gzip.decompress(path.read_bytes()))
    assert saved['point_independent_tensors'] and not saved['root_or_flag_zero_pruning']
    assert saved['family_source_sha256'] == old.FAMILY_SHA
    assert saved['catalogue_sha256'] == old.CATALOGUE_SHA
    assert sorted(int(root) for root, _, _ in saved['blocks']) == sorted(item['root_types'])
    selected = [(flags, tensor) for root, flags, tensor in saved['blocks'] if int(root) == ROOT_TYPE]
    assert len(selected) == 1
    flags, tensor = selected[0]
    assert len(flags) == record['cached_flag_count']
    assert tensor.shape == (record['cached_tensor_lower_rows'], 48965)
    assert [int(flag['masks'][0]) for flag in flags if flag['size'] == 1] == record['high_masks']
    del saved, selected
    gc.collect()
    return flags, tensor, item


def moments(record, tensor, automorphisms, counts, offsets, monomial_masks):
    high = record['high_masks']
    singles = dict(record['single_flag_positions'])
    pairs = {tuple(item['masks']): item['flag_positions'] for item in record['pair_flag_positions']}
    embeddings = [int(a)*int(c) for a, c in zip(automorphisms, counts)]
    product_values, bounds = contraction.cached_values(tensor, embeddings)
    result = np.zeros(len(monomial_masks), dtype=np.int64)
    references = np.full((len(result), 4), -1, dtype=np.int32)
    reference_counts = np.zeros(len(result), dtype=np.uint8)
    visited = np.zeros(len(result), dtype=bool)
    stream = hashlib.sha256()
    for degree in range(5):
        for chosen in combinations(range(42), degree):
            subset = tuple(high[i] for i in chosen)
            refs = old.monomial_rows(subset, singles, pairs)
            assert len(refs) <= 4 and all(0 <= row < tensor.shape[0] for row in refs)
            row = offsets[degree]+sum(comb(i, j+1) for j, i in enumerate(chosen))
            assert not visited[row]
            visited[row] = True
            assert int(monomial_masks[row]) == sum(1 << i for i in chosen)
            value = sum(int(product_values[r]) for r in refs)
            assert 0 <= value <= INT64_MAX
            result[row] = value
            reference_counts[row] = len(refs)
            references[row, :len(refs)] = refs
            stream.update(struct.pack('<qq', degree, len(refs)))
            stream.update(struct.pack('<'+'q'*degree, *subset))
            stream.update(struct.pack('<'+'q'*len(refs), *refs))
    assert visited.all()
    assert stream.hexdigest() == record['monomial_product_row_reference_sha256']
    assert int(reference_counts.sum(dtype=np.int64)) == record['monomial_product_row_references']
    assert int(result[0]) == embeddings[ROOT_TYPE]
    assert np.all(result <= result[0])
    return result, references, reference_counts, bounds


def row_counts(indices, indptr, columns, row_count):
    selected = np.zeros(len(indptr)-1, dtype=bool)
    selected[columns] = True
    expanded = np.repeat(selected, np.diff(indptr))
    counts = np.bincount(indices[expanded], minlength=row_count)
    assert len(counts) == row_count and int(counts.max(initial=0)) <= len(columns)
    return counts.astype(np.int64)


def filters(atoms, visible, indices, indptr, monomial_masks, moment_values):
    zero_rows = np.flatnonzero(moment_values == 0).astype(np.int32)
    positive_rows = np.flatnonzero(moment_values > 0).astype(np.int32)
    zero_flag = moment_values == 0
    hit = zero_flag[indices]
    # Accumulation is int64. An atom of size ten has 386 stored features;
    # uint8 accumulation would be invalid here.
    zero_hits = np.add.reduceat(hit.astype(np.int64), indptr[:-1])
    assert int(zero_hits.max(initial=0)) <= 386
    candidates = np.where(hit, indices, len(moment_values)).astype(np.int32)
    zero_witness = np.minimum.reduceat(candidates, indptr[:-1])
    zero_witness[zero_hits == 0] = -1
    removed_baseline = np.flatnonzero(zero_hits > 0).astype(np.int32)
    baseline_survivors = np.flatnonzero(zero_hits == 0).astype(np.int32)
    visible_removed = visible[zero_hits[visible] > 0]
    active_columns = visible[zero_hits[visible] == 0]
    assert len(visible_removed)+len(active_columns) == len(visible)
    for atom_id in map(int, removed_baseline):
        row = int(zero_witness[atom_id])
        assert row >= 0 and moment_values[row] == 0
        mask = int(monomial_masks[row])
        assert int(atoms[atom_id]) & mask == mask
    assert np.all(zero_witness[baseline_survivors] == -1)
    baseline_rows = np.bincount(indices, minlength=len(moment_values)).astype(np.int64)
    visible_rows = row_counts(indices, indptr, visible, len(moment_values))
    active_row_counts = row_counts(indices, indptr, active_columns, len(moment_values))
    assert np.all(active_row_counts[zero_rows] == 0)
    unsupported = positive_rows[active_row_counts[positive_rows] == 0]
    g = int(moment_values[0])
    if g == 0:
        assert np.all(moment_values == 0)
        status = 'zero root mass; all supplied moments are exactly zero; no LP required'
    elif not len(active_columns):
        status = 'positive root mass but exact-zero filtering removes every atom'
    elif len(unsupported):
        status = 'positive moment has no support in the complete filtered atom domain'
    else:
        status = 'matrix and exact-zero filters prepared; feasibility has not been tested'
    lengths = np.diff(indptr).astype(np.int64)
    summary = {
        'baseline_shape': [len(moment_values), len(atoms)],
        'baseline_nnz': int(indptr[-1]),
        'baseline_supported_rows': int(np.count_nonzero(baseline_rows)),
        'visible_shape': [len(moment_values), len(visible)],
        'visible_nnz': sum(int(lengths[i]) for i in visible),
        'visible_supported_rows': int(np.count_nonzero(visible_rows)),
        'exact_zero_moment_rows': len(zero_rows),
        'positive_moment_rows': len(positive_rows),
        'baseline_columns_removed_by_zero_moments': len(removed_baseline),
        'baseline_columns_surviving_zero_moments': len(baseline_survivors),
        'visible_columns_removed_by_zero_moments': len(visible_removed),
        'zero_filtered_shape': [len(positive_rows), len(active_columns)],
        'zero_filtered_nnz': sum(int(lengths[i]) for i in active_columns),
        'positive_rows_without_filtered_support': len(unsupported),
        'root_labelled_embedding_mass': g,
        'maximum_zero_features_in_one_atom': int(zero_hits.max(initial=0)),
        'every_removed_column_has_an_exact_zero_feature_witness': True,
        'zero_filter_applies_only_to_bound_integer_point': True,
        'status': status,
    }
    arrays = {'zero_rows': zero_rows, 'positive_rows': positive_rows,
        'zero_hits': zero_hits, 'zero_witness_row': zero_witness,
        'baseline_zero_removed_columns': removed_baseline,
        'baseline_zero_survivor_columns': baseline_survivors,
        'visible_columns': visible, 'visible_zero_removed_columns': visible_removed,
        'active_columns': active_columns, 'unsupported_positive_rows': unsupported,
        'baseline_row_support_counts': baseline_rows,
        'visible_row_support_counts': visible_rows,
        'active_row_support_counts': active_row_counts}
    return arrays, summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--matrix', type=Path, required=True)
    parser.add_argument('--moments', type=Path, required=True)
    parser.add_argument('--filters', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=60)
    args = parser.parse_args()
    assert 0 < args.seconds <= 60
    for name in ('output', 'matrix', 'moments', 'filters'):
        setattr(args, name, getattr(args, name).resolve())
    progress = args.output.with_suffix('.progress.json')
    assert not any(path.exists() for path in (args.output, args.matrix, args.moments, args.filters, progress))
    started = time.monotonic()
    result = {'status': 'running empty-root packing feature preparation', 'complete': False,
        'root_type': ROOT_TYPE, 'source_sha256': digest(Path(__file__)),
        'packing_domain_sha256': PACKING_SHA, 'packing_source_sha256': PACKING_SOURCE_SHA,
        'boolean_domain_source_sha256': OLD_SOURCE_SHA,
        'contraction_source_sha256': CONTRACTION_SHA,
        'integer_count_point_sha256': contraction.POINT_SHA,
        'exact_certificate_helper_sha256': CERTIFICATE_HELPER_SHA,
        'catalogue_sha256': old.CATALOGUE_SHA, 'cache_index_sha256': old.INDEX_SHA,
        'requested_preparation_seconds': args.seconds, 'artifacts': {},
        'optimizer_called': False, 'feasibility_query_run': False,
        'new_product_tensors_generated': False, 'reduced_count_matrix_loaded': False,
        'outside_edges_assigned': False, 'symmetry_assumptions_imposed': False,
        'graph_existence_resolved': False}
    def checkpoint(stage):
        result.update(stage=stage, seconds=time.monotonic()-started,
                      peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        progress.write_text(json.dumps(result, indent=2)+'\n')
        print(json.dumps({'stage': stage, 'seconds': result['seconds'],
                          'peak_rss_kib': result['peak_rss_kib']}), flush=True)
    def deadline(_signum, _frame):
        raise TimeoutError('bounded packing feature preparation')
    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    error, timed_out = None, False
    try:
        result['controls'] = controls()
        packing, atoms, visible, ledger, record, counts, catalogue = inputs()
        result['atom_file'] = packing['atoms']
        degree_counts, offsets, monomial_masks, binomial = layout(42)
        assert degree_counts == [1, 42, 861, 11480, 111930]
        result.update(monomials_by_degree=degree_counts, degree_offsets=offsets,
            feature_order='degree blocks; increasing combinatorial colex rank within each degree',
            matrix_entry='1 exactly when the row monomial is contained in the column atom',
            high_masks=record['high_masks'], universal_class_bit_count=42)
        checkpoint('inputs and 511 literal feature-column controls passed')
        indices, indptr, lengths, cardinalities = build_matrix(atoms, monomial_masks, offsets, binomial)
        np.savez_compressed(args.matrix, indices=indices, indptr=indptr,
            shape=np.asarray([len(monomial_masks), len(atoms)], dtype=np.int64),
            monomial_masks=monomial_masks, atom_codes=atoms, cardinalities=cardinalities,
            degree_offsets=np.asarray(offsets, dtype=np.int32))
        result['artifacts']['matrix'] = record_file(args.matrix)
        result['matrix_array_sha256'] = {name: array_digest(array) for name, array in
            (('indices', indices), ('indptr', indptr), ('monomial_masks', monomial_masks), ('atom_codes', atoms))}
        result['matrix_format'] = 'CSC with implicit coefficient one at every stored entry; int32 indices and pointers'
        checkpoint('complete baseline feature matrix saved and every column checked')
        flags, tensor, cache_part = load_root_tensor(ledger, record)
        automorphisms = list(map(int, catalogue[2]))
        moment_values, references, reference_counts, bounds = moments(record, tensor, automorphisms, counts, offsets, monomial_masks)
        np.savez_compressed(args.moments, moments=moment_values, cached_product_rows=references,
            cached_product_row_counts=reference_counts, monomial_masks=monomial_masks)
        result['artifacts']['moments'] = record_file(args.moments)
        result.update(cache_part=cache_part, contraction_bounds=bounds,
            product_reference_sha256=record['monomial_product_row_reference_sha256'],
            moment_array_sha256=array_digest(moment_values),
            maximum_moment=int(moment_values.max(initial=0)),
            labelled_embedding_normalization='Aut(type) times the saved unlabeled induced count; no free-label divisor')
        del tensor, flags, catalogue
        gc.collect()
        checkpoint('all degree-zero-through-four moments and cached references saved')
        filter_arrays, summary = filters(atoms, visible, indices, indptr, monomial_masks, moment_values)
        np.savez_compressed(args.filters, **filter_arrays)
        result['artifacts']['filters'] = record_file(args.filters)
        result.update(summary=summary, complete=True,
            status='complete empty-root packing matrix and exact-zero filter preparation; no LP',
            future_weight_domain='nonnegative weights without upper bounds; constant row fixes their total mass',
            future_zero_filter_certificate='Use the bound finite_boolean_moment_certificates.zero_filter_penalty helper and check every full structurally allowed atom.',
            future_constant_shift_certificate='Use the bound finite_boolean_moment_certificates.constant_shift helper on every full structurally allowed atom.',
            fresh_literal_product_replay_required_for_any_future_cut=True)
        checkpoint('complete preparation')
    except TimeoutError:
        timed_out = True
        result.update(status='UNKNOWN: incomplete feature preparation', timed_out=True, complete=False)
    except Exception as problem:
        error = repr(problem)
        result.update(status='ERROR: feature preparation check failed', error=error, complete=False)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    result.update(seconds=time.monotonic()-started, timed_out=timed_out,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k not in ('high_masks', 'controls')}, indent=2), flush=True)
    print('output_sha256', digest(args.output), flush=True)
    raise SystemExit(int(error is not None))


if __name__ == '__main__':
    main()
