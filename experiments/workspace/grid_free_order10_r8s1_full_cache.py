"""Build the point-independent complete916-root order-ten induced flag cache.

No root or flag is pruned using a count point. This separates cache
coverage from numerical separation at a particular proposal.
"""

import argparse
import gzip
import json
from pathlib import Path
import pickle
import resource
import signal
import time

from threadpoolctl import threadpool_limits

import grid_free_order10_scaled as counts
import grid_free_order10_r8s1 as construction


CONSTRUCTION_SHA = '77e27f09dde9a9c2d57082a60abbab5ac7698875856c7856fe1dc376d6998469'


def generate(catalogue, cache, output, seconds):
    started = time.monotonic()
    assert counts.digest(Path(construction.__file__)) == CONSTRUCTION_SHA
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    assert len(data[0]) == 48965 and len(data[1][8]) == 916
    builder = construction.Builder(data)
    controls, _ = construction.rook_controls(builder)
    # With pruning disabled, these values play no role in tensor entries
    # or flag selection. They merely satisfy the shared builder's interface.
    dummy_counts = [1]*len(data[0])
    blocks, metadata = [], []
    timed_out = False

    def deadline(_signum, _frame):
        raise TimeoutError('complete cache generation time bound')

    previous_handler = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, max(0.001, seconds-(time.monotonic()-started)))
    try:
        for root in data[1][8]:
            masks, tensor, details = builder.block(root, dummy_counts, remove_zero_flags=False)
            expected = [mask for mask, _ in data[3][root] if mask.bit_count() >= 3]
            assert masks == expected
            assert details['full_flags'] == details['retained_flags'] == len(masks)+1
            assert details['exact_zero_flag_masks'] == []
            blocks.append((root, masks, tensor))
            metadata.append({'root_type': root, 'flags': len(masks)+1,
                             'lower_entries': int(tensor.shape[0]),
                             'tensor_nonzeros': int(tensor.nnz)})
            if len(blocks) % 128 == 0:
                print(json.dumps({'complete_root_blocks_built': len(blocks)}), flush=True)
    except TimeoutError:
        timed_out = True
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous_handler)
    complete = len(blocks) == 916 and not timed_out
    payload = {'format': 2, 'root_order': 8, 'outside_flag_size': 1, 'induced': True,
               'point_independent': True, 'zero_flags_or_roots_removed': False,
               'source_sha256': counts.digest(Path(__file__)),
               'construction_source_sha256': CONSTRUCTION_SHA,
               'catalogue_sha256': counts.digest(catalogue),
               'complete_root_family': complete, 'blocks': blocks}
    temporary = cache.with_name(cache.name+'.pending')
    temporary.write_bytes(gzip.compress(pickle.dumps(payload, protocol=5), mtime=0))
    temporary.replace(cache)
    result = {'status': 'complete point-independent916-root cache built' if complete else
                        'partial point-independent cache; incomplete coverage',
              'source_sha256': payload['source_sha256'],
              'construction_source_sha256': CONSTRUCTION_SHA,
              'catalogue_path': str(catalogue), 'catalogue_sha256': counts.digest(catalogue),
              'cache_path': str(cache), 'cache_sha256': counts.digest(cache),
              'cache_bytes': cache.stat().st_size, 'point_independent': True,
              'zero_flags_or_roots_removed': False, 'complete_root_family': complete,
              'root_blocks': len(blocks), 'nontrivial_blocks': sum(row['flags'] > 1 for row in metadata),
              'maximum_flags': max(row['flags'] for row in metadata),
              'lower_entries': sum(row['lower_entries'] for row in metadata),
              'tensor_nonzeros': sum(row['tensor_nonzeros'] for row in metadata),
              'explicit_transports_checked': builder.transports_checked,
              'direct_rook_controls': controls, 'block_metadata': metadata,
              'timed_out': timed_out, 'maximum_seconds': seconds,
              'seconds': time.monotonic()-started,
              'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
              'optimizer_called': False, 'numerical_eigensystems_computed': False}
    counts.save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'block_metadata'}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, required=True)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=120)
    args = parser.parse_args()
    assert 0 < args.seconds <= 180
    with threadpool_limits(limits=1):
        generate(args.catalogue, args.cache, args.output, args.seconds)
