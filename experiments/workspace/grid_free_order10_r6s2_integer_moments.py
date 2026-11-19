"""Scan all three frozen moment families at the repaired integer point.

The scanner interface receives lossless float representations of integers.
Every exported cut is replayed exactly. An empty separator list does not
constitute a positive-semidefinite certificate.
"""

import argparse
import gc
import json
from pathlib import Path
import resource
import time

from threadpoolctl import threadpool_limits

import grid_free_order10_moments as old
import grid_free_order10_r8s1_scan as r8
import grid_free_order10_r6s2_point_scan as r6
import grid_free_order10_scaled as counts


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
WITNESS = LOGS/'prism-zero-order10-r6s2-repair01-witness.json'
WITNESS_SHA = '190c779b4a8758d9df90ccc13a54538d8e120710e224b9150dd3aa4b591bd53d'
REDUCED_SHA = '0ad45482ea273b3412e8d308d47eabab366678f4a7e446e4a9f32791c563af65'
SOURCES = [(old, '4c6886bd8d5dffa711aa20991af3bb87495262bd01d8227d2f64caac0040bbae'),
           (r8, '71f06ef752adff6d49f88136b9e82f054f6485a2b2867c2cd4ef9f7ef7f82887'),
           (r6, '7bb2542e4e69cadade0f096ee578252a804a1c0ff2e0e2d555ce943886654a11'),
           (counts, '12409f5ea1932d549cb69d9ca83e8cd4bd53d173b1a6ef136f9cdee6c095fc16')]


def run(cache, prefix):
    started = time.monotonic()
    target = prefix.with_name(prefix.name+'-result.json')
    assert not target.exists()
    assert counts.digest(WITNESS) == WITNESS_SHA
    assert counts.digest(cache) == REDUCED_SHA
    for module, digest in SOURCES:
        assert counts.digest(Path(module.__file__)) == digest
    witness = json.loads(WITNESS.read_text())
    point = witness['rounded_core_values']
    assert witness['exact_count_and_held_cut_witness'] and witness['held_cut_count'] == 47
    assert witness['original_equations_checked'] == 180445
    assert len(point) == 550 and all(type(value) is int for value in point)
    assert all(0 <= value < 2**53 and float(value).as_integer_ratio() == (value, 1)
               for value in point)
    active = [j for j in range(1, 550) if j not in (56, 57)]
    proposal = prefix.with_name(prefix.name+'-input.json')
    counts.save(proposal, {'status': 'exact integer count witness supplied losslessly to scanners',
        'source_sha256': counts.digest(Path(__file__)), 'witness_sha256': WITNESS_SHA,
        'case_index': 1, 'fixed_order_nine_point': False,
        'real_proposal': {'active_coordinates': active,
                          'ordinary_core_values': [float(point[j]) for j in active],
                          'exact_real_feasibility_certified': True,
                          'scope': 'count equations, bounds, prism zeros, and 47 held inequalities only'}})
    assert old.point_from_proposal(proposal)[1:] == (point[:58], 1)
    assert r8.exact_point(proposal)[1:] == (point, 1)
    result = {'status': 'integer-point moment scans running',
              'source_sha256': counts.digest(Path(__file__)), 'witness_sha256': WITNESS_SHA,
              'scanner_source_sha256': {Path(m.__file__).name: sha for m, sha in SOURCES},
              'reduced_cache_sha256': REDUCED_SHA, 'proposal_path': str(proposal),
              'proposal_sha256': counts.digest(proposal), 'families': [],
              'all_550_float_inputs_are_exact_integers': True,
              'all_scanner_input_denominators_are_one': True,
              'numerical_precursor_used': False, 'optimizer_called': False,
              'PSD_feasibility_certified': False, 'graph_constructed': False}
    counts.save(target, result)
    path = prefix.with_name(prefix.name+'-old1416.json')
    first = old.scan(proposal, path)
    replay_path = prefix.with_name(prefix.name+'-old1416-replay.json')
    counts.save(replay_path, old.replay(path))
    assert first['blocks_examined'] == 1416
    result['families'].append({'family': 'old1416', 'blocks_scanned': 1416, 'complete_scan': True,
        'certificate_path': str(path), 'certificate_sha256': counts.digest(path),
        'replay_path': str(replay_path), 'replay_sha256': counts.digest(replay_path),
        'exact_negative_blocks': first['exact_negative_block_count'],
        'unique_integer_cuts': first['unique_integer_cut_count'],
        'unconfirmed_numeric_negatives': first['numerical_negatives_without_exact_cut']})
    counts.save(target, result)
    data, cores, scale, raw = counts.load_reduced(cache)
    assert len(cores) == 549
    specifications = [('r8s1', r8, LOGS/'order10-r8s1-full-blocks.pickle.gz', 916),
                      ('r6s2', r6, LOGS/'order10-r6s2-full-cache.json', 62)]
    for name, module, tensor_path, expected_blocks in specifications:
        scanner = module.FullScanner(data, raw, scale, tensor_path, REDUCED_SHA)
        assert scanner.count_numerators(point) == witness['induced_counts']
        if name == 'r6s2':
            assert scanner.coverage['covers_full62_family']
        path = prefix.with_name(prefix.name+'-'+name+'.json')
        record = scanner.scan(proposal, path, seconds=180)
        assert record['point_numerators'] == point and record['point_denominator'] == 1
        replay_path = prefix.with_name(prefix.name+'-'+name+'-replay.json')
        counts.save(replay_path, scanner.replay(path))
        result['families'].append({'family': name, 'expected_blocks': expected_blocks,
            'blocks_scanned': record['blocks_scanned'], 'complete_scan': record['complete_scan'],
            'certificate_path': str(path), 'certificate_sha256': counts.digest(path),
            'replay_path': str(replay_path), 'replay_sha256': counts.digest(replay_path),
            'exact_negative_blocks': record['exact_negative_block_count'],
            'unique_integer_cuts': record['unique_integer_cut_count'],
            'unconfirmed_numeric_negatives': record['unconfirmed_numeric_negatives']})
        counts.save(target, result)
        del scanner
        gc.collect()
    negative = sum(record['exact_negative_blocks'] for record in result['families'])
    complete = all(record['complete_scan'] for record in result['families'])
    result.update(status='exact moment violation found and replayed' if negative else
                         ('complete scans found no separator; PSD not certified' if complete else
                          'bounded scan incomplete; no PSD conclusion'),
                  complete_scan=complete, exact_negative_blocks=negative,
                  blocks_scanned=sum(record['blocks_scanned'] for record in result['families']),
                  all_48965_integer_counts_reproduced=True,
                  seconds=time.monotonic()-started,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    counts.save(target, result)
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--prefix', type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        run(args.cache, args.prefix)
