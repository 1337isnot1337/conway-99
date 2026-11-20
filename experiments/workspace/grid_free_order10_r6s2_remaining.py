"""Prepare and generate the seven oversized r6s2 blocks, separately.

The immutable55-block cache is reused, never rewritten. This continuation
builds point-independent full tensors for the other seven root types.
It performs no matrix scan, eigensystem, optimization, or core reduction.
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

import grid_free_order10_r6s2 as family
import grid_free_order10_scaled as counts


FAMILY_SHA = '3772c728ec764dbec0142865696bb747c06e47b29495964af867103618b75a6d'
FAMILY_PREPARATION_SHA = '1ff172888ebdd1a139710cb25e0a0f29c8044a1d81ba4972c0085f9827d691ea'
OLD_CERTIFICATE_SHA = '839b2de78eb081edbf6e39c1f0085f5f1d56ee787a7eed58ec39cb41c0fb3708'
OLD_CACHE_SHA = '84d69eb567b961f8cdce332f66b152a2cac803feb50a5a7b161d67479b31fb5c'
FRESH_REPLAY_SHA = '286bd12ea30bee3825c97507fb5781f3ec36396eb580fc0c5ec58772c660b550'


def inputs(family_preparation, old_certificate, fresh_replay):
    assert counts.digest(Path(family.__file__)) == FAMILY_SHA
    assert counts.digest(family_preparation) == FAMILY_PREPARATION_SHA
    assert counts.digest(old_certificate) == OLD_CERTIFICATE_SHA
    assert counts.digest(fresh_replay) == FRESH_REPLAY_SHA
    prepared = json.loads(family_preparation.read_text())
    old = json.loads(old_certificate.read_text())
    proof = json.loads(fresh_replay.read_text())
    assert proof['complete'] and proof['completed_block_count'] == 18
    assert proof['completed_supported_entries'] == 374505
    assert old['complete_selected_subfamily_scan'] and old['blocks_completed'] == 55
    catalogue = Path(prepared['catalogue_path'])
    old_cache = Path(old['generated_cache_path'])
    assert counts.digest(catalogue) == prepared['catalogue_sha256'] == family.CATALOGUE_SHA
    assert counts.digest(old_cache) == old['generated_cache_sha256'] == OLD_CACHE_SHA
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    payload = pickle.loads(gzip.decompress(old_cache.read_bytes()))
    assert payload['family_source_sha256'] == FAMILY_SHA
    assert payload['point_independent_tensors'] and not payload['root_or_flag_zero_pruning']
    old_roots = [root for root, _, _ in payload['blocks']]
    assert len(old_roots) == len(set(old_roots)) == 55
    assert set(old_roots) == set(prepared['selected_root_types'])
    records = {record['root_type']: record for record in prepared['all_62_root_domains']}
    for root, flags, tensor in payload['blocks']:
        assert len(flags) == records[root]['flags']
        assert tensor.shape == (len(flags)*(len(flags)+1)//2, 48965)
    remaining = sorted(set(data[1][6])-set(old_roots), key=lambda root: (records[root]['flags'], root))
    assert set(remaining) == set(prepared['oversize_root_types'])
    assert len(remaining) == 7 and all(records[root]['flags'] > 512 for root in remaining)
    assert sum(records[root]['lower_entries'] for root in remaining) == 2870660
    return prepared, old, data, payload, records, remaining


def prepare(family_preparation, old_certificate, fresh_replay, output):
    started = time.monotonic()
    prepared, old, data, payload, records, remaining = inputs(
        family_preparation, old_certificate, fresh_replay)
    # Small exact reuse control, independent of the count point: the prism
    # block has four flags and ten lower entries.
    builder = family.Builder(data)
    flags, tensor = builder.block(99)
    old_flags, old_tensor = next((f, t) for root, f, t in payload['blocks'] if root == 99)
    assert len(flags) == len(old_flags) == 4 and (tensor != old_tensor).nnz == 0
    paths = {'family_preparation': family_preparation, 'old_certificate': old_certificate,
             'fresh_replay': fresh_replay}
    result = {'status': 'seven-root continuation prepared; no large generation',
              'source_sha256': counts.digest(Path(__file__)), 'family_source_sha256': FAMILY_SHA,
              'inputs': {key: str(path) for key, path in paths.items()},
              'input_hashes': {key: counts.digest(path) for key, path in paths.items()},
              'catalogue_path': prepared['catalogue_path'], 'catalogue_sha256': family.CATALOGUE_SHA,
              'old_cache_path': old['generated_cache_path'], 'old_cache_sha256': OLD_CACHE_SHA,
              'old_cache_root_types': sorted(root for root, _, _ in payload['blocks']),
              'remaining_root_types_in_visit_order': remaining,
              'remaining_root_dimensions': [[root, records[root]['flags']] for root in remaining],
              'remaining_lower_entries': 2870660, 'largest_remaining_order': 1248,
              'full_family_root_types': data[1][6], 'full_family_lower_entries': 3913479,
              'full_family_maximum_order': 1248,
              'zero_root_or_flag_pruning': False, 'count_point_used': False,
              'small_reuse_control': {'root': 99, 'flags': 4, 'lower_entries': 10,
                                      'fresh_tensor_matches_immutable_old_tensor': True},
              'proposed_generation_seconds': 300,
              'rough_seconds_by_old_entry_rate': old['seconds']*2870660/old['lower_entries_completed'],
              'rate_estimate_is_not_a_runtime_guarantee': True,
              'supports_separate_immutable_resume_stage': True,
              'optimizer_called': False, 'eigensystems_computed': False, 'dense_reduction_loaded': False,
              'preparation_seconds': time.monotonic()-started,
              'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    counts.save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    return result


def write_cache(path, blocks, roots, complete):
    payload = {'format': 1, 'family': 'induced r6s2 whole-flag outside degree at least3',
               'source_sha256': counts.digest(Path(__file__)), 'family_source_sha256': FAMILY_SHA,
               'catalogue_sha256': family.CATALOGUE_SHA, 'point_independent_tensors': True,
               'root_or_flag_zero_pruning': False, 'selected_root_types': roots,
               'completed_root_types': [root for root, _, _ in blocks],
               'complete_selected_subfamily': complete, 'cache_role': 'seven previously oversized roots',
               'blocks': blocks}
    pending = path.with_name(path.name+'.pending')
    pending.write_bytes(gzip.compress(pickle.dumps(payload, protocol=5), mtime=0))
    pending.replace(path)


def generate(preparation, output, new_cache, combined_manifest, seconds=300, resume=None):
    assert 0 < seconds <= 300
    assert not output.exists() and not new_cache.exists() and not combined_manifest.exists()
    saved = json.loads(preparation.read_text())
    assert saved['source_sha256'] == counts.digest(Path(__file__))
    paths = {key: Path(value) for key, value in saved['inputs'].items()}
    for key, path in paths.items():
        assert counts.digest(path) == saved['input_hashes'][key]
    _, _, data, old_payload, records, order = inputs(**paths)
    assert order == saved['remaining_root_types_in_visit_order']
    blocks, completed_records = [], []
    if resume is not None:
        prior = json.loads(resume.read_text())
        assert prior['source_sha256'] == saved['source_sha256']
        assert prior['preparation_sha256'] == counts.digest(preparation)
        prior_cache = Path(prior['generated_cache_path'])
        assert counts.digest(prior_cache) == prior['generated_cache_sha256']
        previous = pickle.loads(gzip.decompress(prior_cache.read_bytes()))
        assert previous['family_source_sha256'] == FAMILY_SHA
        assert previous['point_independent_tensors'] and not previous['root_or_flag_zero_pruning']
        blocks = list(previous['blocks'])
        completed_records = list(prior['blocks'])
        assert len({root for root, _, _ in blocks}) == len(blocks)
        assert {root for root, _, _ in blocks} <= set(order)
        assert {root for root, _, _ in blocks} == {record['root_type'] for record in completed_records}
    done = {root for root, _, _ in blocks}
    result = {'status': 'running bounded seven-root continuation',
              'source_sha256': saved['source_sha256'], 'family_source_sha256': FAMILY_SHA,
              'preparation_path': str(preparation), 'preparation_sha256': counts.digest(preparation),
              'catalogue_sha256': family.CATALOGUE_SHA, 'old_cache_sha256': OLD_CACHE_SHA,
              'maximum_generation_seconds': seconds, 'required_remaining_roots': order,
              'blocks_inherited': len(blocks), 'blocks': completed_records,
              'count_point_used': False, 'root_or_flag_zero_pruning': False,
              'optimizer_called': False, 'eigensystems_computed': False, 'dense_reduction_loaded': False}
    if resume is not None:
        result.update(resume_path=str(resume), resume_sha256=counts.digest(resume))
    counts.save(output, result)
    builder = family.Builder(data)
    started = time.monotonic()
    timed_out = False

    def deadline(_signum, _frame):
        raise TimeoutError('bounded seven-root continuation')

    old_handler = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, seconds)
    try:
        for root in order:
            if root in done:
                continue
            block_started = time.monotonic()
            flags, tensor = builder.block(root)
            assert len(flags) == records[root]['flags']
            sums = np.asarray(tensor.sum(axis=1)).ravel()
            assert max(sums, default=0) <= 26
            flag_records = [{'size': flag['size'], 'masks': flag['masks'], 'edge': flag['edge'],
                             'rows': flag['rows'], 'type': flag['type']} for flag in flags]
            record = {'root_type': root, 'flag_count': len(flags), 'lower_entries': tensor.shape[0],
                      'tensor_nonzeros': tensor.nnz, 'maximum_tensor_row_sum': int(max(sums, default=0)),
                      'seconds': time.monotonic()-block_started}
            blocks.append((root, flag_records, tensor))
            result['blocks'].append(record)
            counts.save(output, result)
            print(json.dumps(record), flush=True)
    except TimeoutError:
        timed_out = True
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)
    recorded = {record['root_type'] for record in result['blocks']}
    blocks = [block for block in blocks if block[0] in recorded]
    roots = {root for root, _, _ in blocks}
    result['blocks'] = [record for record in result['blocks'] if record['root_type'] in roots]
    complete = roots == set(order)
    write_cache(new_cache, blocks, order, complete)
    all_roots = sorted(set(saved['old_cache_root_types']) | roots)
    assert not set(saved['old_cache_root_types']) & roots
    combined = {'format': 1, 'family': 'induced r6s2 whole-flag outside degree at least3',
                'source_sha256': counts.digest(Path(__file__)), 'family_source_sha256': FAMILY_SHA,
                'catalogue_sha256': family.CATALOGUE_SHA, 'point_independent_tensors': True,
                'root_or_flag_zero_pruning': False, 'full_family_root_types': data[1][6],
                'all_cached_root_types': all_roots, 'cached_root_count': len(all_roots),
                'covers_full62_family': set(all_roots) == set(data[1][6]),
                'cache_parts': [{'path': saved['old_cache_path'], 'sha256': OLD_CACHE_SHA,
                                 'root_types': saved['old_cache_root_types']},
                                {'path': str(new_cache), 'sha256': counts.digest(new_cache),
                                 'root_types': sorted(roots)}]}
    counts.save(combined_manifest, combined)
    result.update(status='all seven remaining root tensors generated' if complete else
                         'bounded continuation incomplete; completed tensors preserved',
                  timed_out=timed_out, complete_seven_roots=complete,
                  completed_root_count=len(blocks), completed_lower_entries=sum(t.shape[0] for _, _, t in blocks),
                  completed_tensor_nonzeros=sum(t.nnz for _, _, t in blocks),
                  generated_cache_path=str(new_cache), generated_cache_sha256=counts.digest(new_cache),
                  combined_manifest_path=str(combined_manifest), combined_manifest_sha256=counts.digest(combined_manifest),
                  combined_root_count=len(all_roots), covers_full62_family=combined['covers_full62_family'],
                  seconds=time.monotonic()-started,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    counts.save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key != 'blocks'}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    for name in ('family-preparation', 'old-certificate', 'fresh-replay', 'output'):
        prep.add_argument('--'+name, type=Path, required=True)
    build = sub.add_parser('generate')
    for name in ('preparation', 'output', 'new-cache', 'combined-manifest'):
        build.add_argument('--'+name, type=Path, required=True)
    build.add_argument('--seconds', type=float, default=300)
    build.add_argument('--resume', type=Path)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'prepare':
            prepare(args.family_preparation, args.old_certificate, args.fresh_replay, args.output)
        else:
            generate(args.preparation, args.output, args.new_cache, args.combined_manifest, args.seconds, args.resume)
