"""One bounded, incremental full eight-root projector discovery scan.

All 916 root domains and four blocks per root are retained in immutable
cache chunks. Every matrix is contracted with Python integers and checked
against its nine kernels before quotient separation. This stage saves
exact induced-count separators but does not independently reconstruct
their supported entries; that is a separate gate before optimizer use.
"""

import argparse
import gzip
import json
from pathlib import Path
import pickle
import resource
import signal
import time

import numpy as np
from threadpoolctl import threadpool_limits

import grid_free_order10_projector_probe as construction
import grid_free_order10_projector_domains as domains
import grid_free_order10_r8s1 as forms
from grid_free_order10_r8s1_scan import FullScanner
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
CHUNK_ROOTS = 32
PROBE_SHA = '0af37fafb7db4e68963fa602800e7aa3256b9cf56ef8ffd1ce4b06a48da16e7a'
REVIEWS = [ROOT/'experiments/logs/moments-and-counts'/name for name in (
    'order10-eight-root-projector-coordinator-review.json',
    'order10-eight-root-projector-probe-coordinator-review.json')]


def metadata(records, counts):
    assert files.digest(Path(construction.__file__)) == PROBE_SHA
    ordered = sorted(records)
    assert ordered == list(range(308, 1224))
    sizes = [records[root]['classes'] for root in ordered]
    return {
        'source_sha256': files.digest(Path(__file__)), 'construction_source_sha256': PROBE_SHA,
        'domain_source_sha256': construction.DOMAIN_SOURCE_SHA,
        'domain_certificate_sha256': construction.DOMAIN_SHA,
        'literal_oracle_source_sha256': files.digest(Path(construction.literal.__file__)),
        'transport_and_induced_form_source_sha256': files.digest(Path(forms.__file__)),
        'negative_direction_source_sha256': files.digest(Path(__file__).with_name('grid_free_order10_r8s1_scan.py')),
        'coordinator_reviews': [{'path': str(path.relative_to(ROOT)), 'sha256': files.digest(path)} for path in REVIEWS],
        'catalogue_sha256': domains.CATALOGUE_SHA,
        'integer_witness_path': str(construction.WITNESS.relative_to(ROOT)),
        'integer_witness_sha256': construction.WITNESS_SHA,
        'root_types': ordered, 'root_count': len(ordered), 'blocks': 4*len(ordered),
        'lower_entries': sum(m*(m+1)+(m+8)*(m+9) for m in sizes),
        'coefficient_placements_upper_bound': sum(2*(36+10*m+2*m*(m+1)) for m in sizes),
        'maximum_build_and_scan_seconds': 180, 'threads': 1, 'roots_per_cache_chunk': CHUNK_ROOTS,
        'all_masks_retained': True, 'point_dependent_cache_pruning': False,
        'integer_target': True, 'all_48965_induced_counts_nonnegative': all(value >= 0 for value in counts),
        'nine_kernels_checked_before_pivot_deletion': True,
        'full_count_contractions_use_Python_integers': True,
        'independent_separator_replay_deferred': True,
        'dense_reduction_loaded': False, 'optimizer_called': False,
    }


def run(args, preparation):
    total_started = time.monotonic()
    records, counts = construction.inputs()
    assert preparation == metadata(records, counts)
    assert files.digest(args.catalogue) == domains.CATALOGUE_SHA
    with args.catalogue.open('rb') as stream:
        data = pickle.load(stream)
    roots = data[1][8]
    assert roots == preparation['root_types']
    builder = construction.Builder(data)
    embeddings = [int(a)*c for a, c in zip(data[2], counts)]
    args.cache_dir.mkdir(parents=True, exist_ok=False)
    result = {
        'source_sha256': files.digest(Path(__file__)),
        'preparation_sha256': files.digest(args.preparation), 'preparation': preparation,
        'roots_completed': [], 'block_records': [], 'negative_blocks': [],
        'unique_induced_cuts': [], 'unconfirmed_numeric_negatives': [],
        'independent_literal_separator_replay_complete': False,
        'PSD_feasibility_certified': False, 'all_old_2405_blocks_rechecked': False,
    }
    cache_manifest = {
        'format': 1, 'point_independent': True, 'complete_root_family': False,
        'all_masks_retained_for_completed_roots': True, 'zero_flags_or_roots_removed': False,
        'construction_source_sha256': PROBE_SHA, 'driver_source_sha256': files.digest(Path(__file__)),
        'domain_certificate_sha256': construction.DOMAIN_SHA,
        'catalogue_sha256': domains.CATALOGUE_SHA, 'root_types_required': roots,
        'parts': [], 'root_types_completed': [],
    }
    pending, pending_roots, known = [], [], {}
    current_root, timed_out, error = None, False, None
    build_scan_started = time.monotonic()

    def flush():
        """Idempotent chunk commit, including recovery after a timer interrupt."""
        if not pending:
            return
        selected = list(pending_roots)
        name = 'roots-%04d-%04d.pickle.gz' % (selected[0], selected[-1])
        path = args.cache_dir/name
        payload = {
            'format': 1, 'point_independent': True, 'zero_flags_or_roots_removed': False,
            'construction_source_sha256': PROBE_SHA, 'domain_certificate_sha256': construction.DOMAIN_SHA,
            'catalogue_sha256': domains.CATALOGUE_SHA, 'root_types': selected,
            'all_four_blocks_per_root': True, 'blocks': list(pending),
        }
        blob = gzip.compress(pickle.dumps(payload, protocol=5), compresslevel=9, mtime=0)
        if path.exists():
            assert path.read_bytes() == blob
        else:
            temporary = path.with_suffix(path.suffix+'.tmp')
            temporary.write_bytes(blob)
            temporary.replace(path)
        part = {
            'path': name, 'sha256': files.digest(path), 'bytes': len(blob), 'root_types': selected,
            'blocks': len(pending), 'lower_entries': sum(b['tensor'].shape[0] for b in pending),
            'nonzero_tensor_coefficients': sum(b['tensor'].nnz for b in pending),
            'csr_bytes': sum(b['tensor'].data.nbytes+b['tensor'].indices.nbytes+b['tensor'].indptr.nbytes for b in pending),
        }
        old = next((p for p in cache_manifest['parts'] if p['path'] == name), None)
        if old is None:
            cache_manifest['parts'].append(part)
        else:
            assert old == part
        cache_manifest['root_types_completed'] = [root for p in cache_manifest['parts'] for root in p['root_types']]
        # The timer can interrupt compression or a write. Mask it only for the
        # short in-memory commit, so pending state cannot become inconsistent.
        old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
        try:
            pending.clear()
            pending_roots.clear()
        finally:
            signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
        files.save(args.cache_dir/'manifest.json', cache_manifest)
        files.save(args.output, result)

    def deadline(_signum, _frame):
        raise TimeoutError('bounded full eight-root projector discovery')

    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    try:
        for root in roots:
            current_root = root
            root_started = time.monotonic()
            record = records[root]
            blocks = builder.blocks(record)
            construction_seconds = time.monotonic()-root_started
            local_scans, local_negatives, local_unconfirmed = [], [], []
            for block in blocks:
                scan_started = time.monotonic()
                matrix = FullScanner.matrix(block['tensor'], block['order'], embeddings)
                K, pivots = construction.kernel(block, record)
                assert not any(int(x) for x in (matrix@K).flat)
                pivot_set = set(pivots)
                keep = [i for i in range(block['order']) if i not in pivot_set]
                vector, quadratic, smallest, zero = FullScanner.negative(matrix[np.ix_(keep, keep)])
                summary = {
                    'root_type': root, 'family': block['family'], 'projector': block['projector'],
                    'order': block['order'], 'quotient_order': len(keep),
                    'all_nine_kernels_checked_exactly': True,
                    'smallest_numeric_eigenvalue': smallest, 'exact_zero_quotient_rows': zero,
                }
                if vector is not None:
                    full = [0]*block['order']
                    for i, value in zip(keep, vector):
                        full[i] = value
                    v = np.asarray(full, dtype=object)
                    assert int(v@matrix@v) == quadratic < 0
                    terms, divisor = forms.induced_form(block['tensor'], full, data[2])
                    value = sum(coefficient*counts[index] for index, coefficient in terms)
                    assert value*divisor == quadratic < 0
                    local_negatives.append({
                        **summary, 'integer_vector': full, 'integer_quadratic_value': quadratic,
                        'primitive_induced_count_form': terms, 'induced_form_gcd': divisor,
                        'primitive_value_at_integer_witness': value,
                        'independent_literal_replay_complete': False,
                        'optimizer_eligible_before_independent_replay': False,
                    })
                elif smallest is not None and smallest < -1e-8:
                    local_unconfirmed.append(summary.copy())
                summary['seconds'] = time.monotonic()-scan_started
                local_scans.append(summary)
            root_record = {
                'root_type': root, 'classes': record['classes'],
                'construction_seconds': construction_seconds,
                'total_seconds': time.monotonic()-root_started,
                'lower_entries': sum(b['tensor'].shape[0] for b in blocks),
                'nonzero_tensor_coefficients': sum(b['tensor'].nnz for b in blocks),
                'csr_bytes': sum(b['tensor'].data.nbytes+b['tensor'].indices.nbytes+b['tensor'].indptr.nbytes for b in blocks),
            }
            # Commit only a root whose four complete blocks have been scanned.
            # Block SIGALRM during these short list/dictionary updates.
            old_mask = signal.pthread_sigmask(signal.SIG_BLOCK, {signal.SIGALRM})
            try:
                for negative in local_negatives:
                    key = tuple(map(tuple, negative['primitive_induced_count_form']))
                    if key not in known:
                        known[key] = len(result['unique_induced_cuts'])
                        result['unique_induced_cuts'].append({
                            'terms': negative['primitive_induced_count_form'],
                            'exact_value_at_witness': negative['primitive_value_at_integer_witness'],
                            'independent_literal_replay_complete': False})
                    negative['cut_index'] = known[key]
                result['roots_completed'].append(root_record)
                result['block_records'].extend(local_scans)
                result['negative_blocks'].extend(local_negatives)
                result['unconfirmed_numeric_negatives'].extend(local_unconfirmed)
                pending.extend(blocks)
                pending_roots.append(root)
                current_root = None
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK, old_mask)
            if len(pending_roots) >= CHUNK_ROOTS:
                flush()
                print(json.dumps({'roots_completed': len(result['roots_completed']),
                    'blocks_scanned': len(result['block_records']), 'negative_blocks': len(result['negative_blocks']),
                    'unique_exact_induced_forms_pending_replay': len(result['unique_induced_cuts']),
                    'seconds': time.monotonic()-build_scan_started}), flush=True)
    except TimeoutError:
        timed_out = True
    except Exception as problem:
        error = repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    build_scan_seconds = time.monotonic()-build_scan_started
    flush()
    completed = [r['root_type'] for r in result['roots_completed']]
    assert cache_manifest['root_types_completed'] == completed
    complete = completed == roots and len(result['block_records']) == 3664
    cache_manifest.update(complete_root_family=complete,
                          all_four_blocks_for_each_completed_root=True,
                          complete_block_count=sum(p['blocks'] for p in cache_manifest['parts']))
    files.save(args.cache_dir/'manifest.json', cache_manifest)
    manifest_path = (args.cache_dir/'manifest.json').resolve()
    result.update(
        status='complete 916-root projector discovery scan' if complete else 'partial 916-root projector discovery scan',
        complete_scan=complete, timed_out=timed_out, interrupted_root=current_root, error=error,
        roots_scanned=len(completed), blocks_scanned=len(result['block_records']),
        exact_negative_blocks=len(result['negative_blocks']), unique_induced_cut_count=len(result['unique_induced_cuts']),
        cache_manifest_path=str(manifest_path.relative_to(ROOT)) if manifest_path.is_relative_to(ROOT) else str(manifest_path),
        cache_manifest_sha256=files.digest(args.cache_dir/'manifest.json'),
        cache_bytes=sum(p['bytes'] for p in cache_manifest['parts']),
        csr_bytes=sum(p['csr_bytes'] for p in cache_manifest['parts']),
        nonzero_tensor_coefficients=sum(p['nonzero_tensor_coefficients'] for p in cache_manifest['parts']),
        build_and_scan_seconds=build_scan_seconds, total_seconds=time.monotonic()-total_started,
        peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    )
    files.save(args.output, result)
    print(json.dumps({key: result[key] for key in (
        'status','complete_scan','timed_out','interrupted_root','error','roots_scanned','blocks_scanned',
        'exact_negative_blocks','unique_induced_cut_count','cache_manifest_sha256','cache_bytes',
        'csr_bytes','nonzero_tensor_coefficients','build_and_scan_seconds','total_seconds','peak_rss_kib')}, indent=2), flush=True)
    if error:
        raise RuntimeError(error)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--prepare', action='store_true')
    parser.add_argument('--preparation', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--cache-dir', type=Path)
    parser.add_argument('--seconds', type=int, default=180)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 180
    if args.prepare:
        assert args.preparation is None and args.cache_dir is None
        records, counts = construction.inputs()
        result = metadata(records, counts)
        files.save(args.output, result)
        print(json.dumps({k: v for k, v in result.items() if k != 'root_types'}, indent=2), flush=True)
    else:
        assert args.preparation and args.cache_dir and not args.cache_dir.exists()
        preparation = json.loads(args.preparation.read_text())
        with threadpool_limits(limits=1):
            run(args, preparation)
