"""Cheap cache/domain and exact contraction controls for the r6s2 scanner.

This loads no dense reduction and performs no optimizer call. The seven
new tensors receive sampled independent literal-product checks. All 18
old exact negative directions are checked through the new matrix API.
"""

import argparse
import json
from pathlib import Path
import pickle
import resource
import time

import numpy as np
from threadpoolctl import threadpool_limits

import grid_free_order10_r6s2_independent_audit as oracle
import grid_free_order10_r6s2_point_scan as subject
import grid_free_order10_r8s1 as forms
import grid_free_order10_scaled as counts


ORACLE_SHA = '46bbbf5521383fc14925644e1dcb82ebeca99094b5726b8f23e3d774aa6f643f'


def main(cache, old_certificate, output):
    started = time.monotonic()
    assert counts.digest(Path(oracle.__file__)) == ORACLE_SHA
    saved = json.loads(old_certificate.read_text())
    catalogue = Path(saved['catalogue_path'])
    witness = Path(saved['witness_path'])
    assert counts.digest(catalogue) == saved['catalogue_sha256']
    assert counts.digest(witness) == saved['witness_sha256']
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    blocks, coverage, parts = subject.cache_contents(data, cache)
    assert coverage['covers_full62_family'] and coverage['cached_root_count'] == 62
    assert coverage['cached_lower_entries'] == 3913479
    lookup = {root: (flags, tensor) for root, flags, tensor in blocks}
    selected55 = set(coverage['selected55_root_types'])
    ids = {oracle.canonical(tuple(rows)): i for i, rows in enumerate(data[0])}
    product_checks, ten_vertex_checks = 0, 0
    sampled_roots = []
    for root, flags, tensor in blocks:
        if root in selected55:
            continue
        sampled_roots.append(root)
        positions = oracle.samples(flags)
        for a, i in enumerate(positions):
            for j in positions[:a+1]:
                expected, _ = oracle.direct_product(6, tuple(flags[i]['rows']), tuple(flags[j]['rows']), ids)
                row = i*(i+1)//2+j
                actual = {int(tensor.indices[k]): int(tensor.data[k])
                          for k in range(tensor.indptr[row], tensor.indptr[row+1])}
                assert dict(expected) == actual
                product_checks += 1
                ten_vertex_checks += any(len(data[0][index]) == 10 for index in actual)
    assert len(sampled_roots) == 7
    point = json.loads(witness.read_text())
    induced = point['induced_counts']
    embeddings = [value*aut for value, aut in zip(induced, data[2])]
    quadratic_checks = []
    for block in saved['negative_blocks']:
        flags, tensor = lookup[block['root_type']]
        matrix = subject.FullScanner.matrix(tensor, len(flags), embeddings)
        vector = np.array(block['integer_vector'], dtype=object)
        quadratic = int(vector@matrix@vector)
        assert quadratic == block['integer_quadratic_value'] < 0
        terms, divisor = forms.induced_form(tensor, list(vector), data[2])
        assert terms == block['primitive_induced_count_form']
        assert divisor == block['positive_form_gcd']
        assert sum(value*induced[index] for index, value in terms)*divisor == quadratic
        quadratic_checks.append({'root_type': block['root_type'], 'quadratic_value': quadratic})
    assert len(quadratic_checks) == 18
    # The flag value 2 gives this exact rank-one moment matrix. Replacing
    # its second moment by the first moment would incorrectly reject it.
    nonbinary = np.array([[1, 2], [2, 4]], dtype=object)
    direction, _, _, _ = subject.FullScanner.negative(nonbinary)
    assert direction is None
    altered = np.array([[1, 2], [2, 2]], dtype=object)
    direction, quadratic, _, _ = subject.FullScanner.negative(altered)
    assert direction is not None and quadratic < 0
    result = {'status': 'r6s2 cache/domain and exact contraction controls PASS',
              'source_sha256': counts.digest(Path(__file__)),
              'scanner_source_sha256': counts.digest(Path(subject.__file__)),
              'independent_product_oracle_sha256': ORACLE_SHA,
              'cache_path': str(cache), 'cache_sha256': counts.digest(cache),
              'cache_parts': parts, 'coverage': coverage,
              'old_certificate_path': str(old_certificate),
              'old_certificate_sha256': counts.digest(old_certificate),
              'witness_sha256': counts.digest(witness),
              'new_roots_sampled': sampled_roots,
              'independent_saved_tensor_entries_checked': product_checks,
              'sampled_entries_with_order_ten_terms': ten_vertex_checks,
              'old_negative_quadratic_checks': quadratic_checks,
              'nonbinary_second_moment_control': {'first': 2, 'second': 4, 'passed': True},
              'dense_reduction_loaded': False, 'core_form_reduction_replayed': False,
              'optimizer_called': False, 'complete_tensor_reconstruction': False,
              'seconds': time.monotonic()-started,
              'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    counts.save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--old-certificate', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        main(args.cache, args.old_certificate, args.output)
