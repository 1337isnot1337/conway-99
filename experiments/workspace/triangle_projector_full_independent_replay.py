"""Independent exact contraction and PSD-certificate replay.

No catalogue, tensor enumerator, source query helper, or optimizer is imported.
The saved scalar coefficients multiply unlabelled induced graph counts.
"""
import argparse
import gzip
import hashlib
from math import isqrt
import json
from pathlib import Path
import time
from flint import fmpz_mat

EXPECTED = {
    'source': 'd26499a0eec07c2c80a28818f0a40319fc0b14f54140a28253c820eb00d44f2a',
    'preparation': '48a3788a0ca55dd445971f71dba46be49f4291b0ddd6b920beebb5de87e66fb7',
    'compressed_model': '9305dffa83a024f574321dd5843244724d3cd82b569c0749d2ed135ccdc01938',
    'raw_model': '819aa1954ce038865404433995eb401ad7111cad0a21992f4ba8c42e3e04687c',
    'point': '0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df',
    'query': 'd58954dcb0a6aa53de59feba73c8bb8864666ae7bad96ecbd48d490e7280d0a0',
}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--point', type=Path, required=True)
    parser.add_argument('--query', type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    inputs = {
        'source': args.source.read_bytes(),
        'preparation': (args.preparation/'preparation.json').read_bytes(),
        'compressed_model': (args.preparation/'model.json.gz').read_bytes(),
        'point': args.point.read_bytes(),
        'query': args.query.read_bytes(),
    }
    inputs['raw_model'] = gzip.decompress(inputs['compressed_model'])
    assert {key: digest(raw) for key, raw in inputs.items()} == EXPECTED
    preparation = json.loads(inputs['preparation'])
    model = json.loads(inputs['raw_model'])
    point = json.loads(inputs['point'])
    query = json.loads(inputs['query'])
    assert preparation['source_sha256'] == query['source_sha256'] == EXPECTED['source']
    assert preparation['model_raw_sha256'] == query['model_raw_sha256'] == EXPECTED['raw_model']
    assert query['preparation_sha256'] == EXPECTED['preparation']
    assert query['point_sha256'] == EXPECTED['point']
    assert query['status'] == 'EXACT_ALL_NINE_FULL_TRIANGLE_PROJECTOR_BLOCKS_PSD'
    counts = point['induced_counts']
    assert len(counts) == 48965 and all(type(x) is int and x >= 0 for x in counts)
    blocks = model['blocks']
    domains = {d['root_type']: d for d in model['domains']}
    saved = {b['root_type']: b for b in query['blocks']}
    assert len(blocks) == len(domains) == len(saved) == 9
    assert {b['root_type'] for b in blocks} == set(range(8, 17)) == set(domains) == set(saved)
    report = []
    terms_checked = lower_checked = all_entries_checked = 0
    for block in blocks:
        root = block['root_type']
        n = block['order']
        assert n == len(domains[root]['classes']) == saved[root]['order']
        assert block['lower_entries'] == n*(n+1)//2
        matrix = [[0]*n for _ in range(n)]
        positions = set()
        for entry, graph, coefficient in block['terms']:
            assert all(type(x) is int for x in (entry, graph, coefficient))
            assert 0 <= entry < n*(n+1)//2 and 0 <= graph < len(counts) and coefficient != 0
            assert (entry, graph) not in positions
            positions.add((entry, graph))
            i = (isqrt(8*entry+1)-1)//2
            j = entry-i*(i+1)//2
            assert 0 <= j <= i < n
            value = coefficient*counts[graph]
            matrix[i][j] += value
            if i != j:
                matrix[j][i] += value
            terms_checked += 1
        claimed = [[int(x) for x in row] for row in saved[root]['matrix']]
        assert matrix == claimed
        assert all(matrix[i][j] == matrix[j][i] for i in range(n) for j in range(n))
        lower_checked += n*(n+1)//2
        all_entries_checked += n*n
        # Compute det(tI-M), then change t to -t and multiply by (-1)^n.
        # This independently checks the sign convention det(tI+M).
        minus_polynomial = list(map(int, fmpz_mat(matrix).charpoly()))
        plus_polynomial = [(-1 if (n+k)%2 else 1)*c for k,c in enumerate(minus_polynomial)]
        assert len(plus_polynomial) == n+1 and plus_polynomial[-1] == 1
        assert plus_polynomial == list(map(int, saved[root]['det_tI_plus_matrix_coefficients']))
        assert all(c >= 0 for c in plus_polynomial)
        nullity = next(i for i,c in enumerate(plus_polynomial) if c)
        assert saved[root]['exact_positive_semidefinite'] is True
        classes = domains[root]['classes']
        vectors = [[1]*n]
        vectors += [[int(c['root_intersection_mask'] & (1 << j) != 0) for c in classes] for j in range(4)]
        vectors += [[c['outside_masks'].count(mask) for c in classes] for mask in range(16)]
        kernel_checks = [all(sum(row[j]*v[j] for j in range(n)) == 0 for row in matrix) for v in vectors]
        assert len(kernel_checks) == 21 and all(kernel_checks)
        assert kernel_checks[:5] == saved[root]['constant_and_four_root_incidence_null_checks']
        kernel_rank = fmpz_mat(vectors).rank()
        assert kernel_rank <= nullity
        report.append({
            'root_type': root, 'order': n, 'rank': n-nullity, 'nullity': nullity,
            'tensor_terms': len(block['terms']),
            'all_21_incidence_kernel_checks': kernel_checks,
            'incidence_kernel_span_rank': kernel_rank,
            'nullity_beyond_incidence_span': nullity-kernel_rank,
            'trace': sum(matrix[i][i] for i in range(n)),
            'matrix_sha256': digest(json.dumps(matrix,separators=(',',':')).encode()),
            'characteristic_coefficients_sha256': digest(json.dumps(plus_polynomial,separators=(',',':')).encode()),
            'all_coefficients_nonnegative': True,
        })
    assert terms_checked == preparation['tensor_nonzeros'] == 135819
    assert lower_checked == preparation['lower_entries'] == 21190
    assert sum(b['order'] for b in report) == preparation['classes'] == 574
    result = {
        'status': 'PASS_INDEPENDENT_FULL_TRIANGLE_CONTRACTION_PSD_AND_INCIDENCE_KERNELS',
        'audit_source_sha256': digest(Path(__file__).read_bytes()),
        'bindings': EXPECTED,
        'blocks': report,
        'all_nine_blocks_checked': True,
        'exact_tensor_terms_contracted': terms_checked,
        'exact_lower_entries_checked': lower_checked,
        'exact_symmetric_matrix_entries_checked': all_entries_checked,
        'unbounded_integer_contraction': True,
        'exact_characteristic_polynomials_recomputed': 9,
        'PSD_reason': 'A real symmetric matrix has real eigenvalues. Its monic det(tI+M) with all coefficients nonnegative has no positive root; therefore no eigenvalue is negative.',
        'query_source_imported': False, 'tensor_enumeration_repeated': False,
        'catalogue_loaded': False, 'optimizer_called': False,
        'unrestricted_existence_resolved': False,
        'seconds': time.monotonic()-started,
    }
    print(json.dumps(result, indent=2))

if __name__ == '__main__':
    main()
