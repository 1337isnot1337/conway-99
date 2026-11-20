"""Check exact bounded-flag ranges in completed r6s2 tensors, separately.

Binary diagonal ranges are identities. For the remaining degree-two edge
flags, the diagonal bound follows from two marked-pair count extensions.
Cross ranges are checked exactly at specified integer points; a passing
point does not prove that all such inequalities follow from count rows.
"""

import argparse
from collections import Counter
from functools import reduce
import json
from math import gcd
from pathlib import Path
import pickle
import time

import grid_free_order10_r6s2 as family
import grid_free_order10_r6s2_independent_audit as oracle
import grid_free_order10_r6s2_point_scan as caches
import grid_free_order10_scaled as counts


FAMILY_SHA = '3772c728ec764dbec0142865696bb747c06e47b29495964af867103618b75a6d'
ORACLE_SHA = '46bbbf5521383fc14925644e1dcb82ebeca99094b5726b8f23e3d774aa6f643f'
CACHE_READER_SHA = '7bb2542e4e69cadade0f096ee578252a804a1c0ff2e0e2d555ce943886654a11'


def row(tensor, i, j):
    a, b = max(i, j), min(i, j)
    position = a*(a+1)//2+b
    return {int(tensor.indices[k]): int(tensor.data[k])
            for k in range(tensor.indptr[position], tensor.indptr[position+1])}


def flag_bound(flag):
    if flag['size'] == 0 or any(mask.bit_count() >= 3 for mask in flag['masks']):
        return 1
    assert flag['size'] == 2 and flag['edge'] == 1
    assert all(mask.bit_count() == 2 for mask in flag['masks'])
    return 2


def residual(rows, pair):
    a, b = pair
    return 2-((rows[a] >> b) & 1)-(rows[a] & rows[b]).bit_count()


def primitive_range(tensor, i, j, bound, aut):
    coefficients = Counter({index: bound*value for index, value in row(tensor, 0, j).items()})
    coefficients.subtract(row(tensor, i, j))
    terms = [[index, coefficient*aut[index]] for index, coefficient in sorted(coefficients.items()) if coefficient]
    divisor = reduce(gcd, [abs(value) for _, value in terms], 0)
    assert divisor > 0
    return [[index, value//divisor] for index, value in terms], divisor


def audit(certificate, witnesses, output, cache_path=None):
    started = time.monotonic()
    assert counts.digest(Path(family.__file__)) == FAMILY_SHA
    assert counts.digest(Path(oracle.__file__)) == ORACLE_SHA
    assert counts.digest(Path(caches.__file__)) == CACHE_READER_SHA
    saved = json.loads(certificate.read_text())
    cache = Path(saved['generated_cache_path']) if cache_path is None else cache_path
    catalogue = Path(saved['catalogue_path'])
    if cache_path is None:
        assert counts.digest(cache) == saved['generated_cache_sha256']
    assert counts.digest(catalogue) == saved['catalogue_sha256']
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    blocks, coverage, bindings = caches.cache_contents(data, cache)
    ids = {oracle.canonical(tuple(rows)): i for i, rows in enumerate(data[0])}
    points = []
    for path in witnesses:
        point = json.loads(path.read_text())
        assert point['original_equations_checked'] == 180445
        assert point['negative_induced_rows'] == point['nonintegral_induced_rows'] == 0
        induced = point['induced_counts']
        assert len(induced) == 48965 and all(type(value) is int and value >= 0 for value in induced)
        points.append({'path': str(path), 'sha256': counts.digest(path),
                       'x521': point['rounded_core_values'][521], 'counts': induced,
                       'embeddings': [count*aut for count, aut in zip(induced, data[2])],
                       'checked_ordered_ranges': 0, 'negative_range_count': 0,
                       'negative_diagonal_count': 0, 'blocks': [], 'exact_cuts': []})
    diagonal = {'binary_identities': 0, 'two_copy_term_forbidden': 0,
                'two_marked_pair_extension_bounds': 0, 'extension_examples': []}
    for root, flags, tensor in blocks:
        bounds = [flag_bound(flag) for flag in flags]
        for i, flag in enumerate(flags):
            first = row(tensor, 0, i)
            assert first == {flag['type']: 1}
            square = row(tensor, i, i)
            if bounds[i] == 1:
                assert square == first
                diagonal['binary_identities'] += 1
                continue
            extra = Counter(square)
            extra.subtract(first)
            extra = {index: value for index, value in extra.items() if value}
            if not extra:
                diagonal['two_copy_term_forbidden'] += 1
                continue
            assert len(extra) == 1
            target, multiplicity = next(iter(extra.items()))
            assert multiplicity == 1 and len(data[0][target]) == 10
            a, b = flag['masks']
            original = tuple(flag['rows'])
            intermediate = tuple(value | (((a >> j) & 1) << 8) for j, value in enumerate(original))+(a,)
            last_mask = b | (1 << 8)
            final = tuple(value | (((last_mask >> j) & 1) << 9) for j, value in enumerate(intermediate))+(last_mask,)
            assert oracle.valid(intermediate) and oracle.valid(final)
            assert ids[oracle.canonical(final)] == target
            pair_a, pair_b = oracle.members(a), oracle.members(b)
            assert len(pair_a) == len(pair_b) == 2
            assert residual(original, pair_a) == residual(intermediate, pair_b) == 1
            diagonal['two_marked_pair_extension_bounds'] += 1
            if len(diagonal['extension_examples']) < 8:
                diagonal['extension_examples'].append({'root_type': root, 'flag_index': i,
                    'flag_type': flag['type'], 'intermediate_type': ids[oracle.canonical(intermediate)],
                    'double_copy_type': target, 'first_marked_pair': pair_a, 'second_marked_pair': pair_b,
                    'both_remaining_common_neighbor_quotas': 1})
        for point in points:
            matrix = family.exact_matrix(tensor, len(flags), point['embeddings'])
            negative, negative_diagonal, worst = 0, 0, None
            for i, bound in enumerate(bounds):
                for j in range(len(flags)):
                    value = bound*matrix[0, j]-matrix[i, j]
                    if value < 0:
                        negative += 1
                        negative_diagonal += i == j
                        if worst is None or value < worst[2]:
                            worst = (i, j, int(value))
            assert negative_diagonal == 0
            point['checked_ordered_ranges'] += len(flags)**2
            point['negative_range_count'] += negative
            point['negative_diagonal_count'] += negative_diagonal
            record = {'root_type': root, 'flags': len(flags), 'ordered_ranges_checked': len(flags)**2,
                      'negative_ranges': negative, 'negative_diagonal_ranges': negative_diagonal}
            if worst is not None:
                i, j, value = worst
                terms, divisor = primitive_range(tensor, i, j, bounds[i], data[2])
                primitive_value = sum(coefficient*point['counts'][index] for index, coefficient in terms)
                assert primitive_value*divisor == value < 0
                record.update(worst_flag_pair=[i, j], bound=bounds[i], exact_worst_value=value)
                point['exact_cuts'].append({'root_type': root, 'left_flag_index': i, 'right_flag_index': j,
                    'left_flag_bound': bounds[i], 'primitive_induced_count_form': terms,
                    'positive_form_gcd': divisor, 'exact_primitive_value': primitive_value})
            point['blocks'].append(record)
    for point in points:
        del point['counts'], point['embeddings']
    result = {'status': 'exact diagonal derivations and pointwise flag-range scan completed',
              'source_sha256': counts.digest(Path(__file__)), 'family_source_sha256': FAMILY_SHA,
              'independent_graph_source_sha256': ORACLE_SHA,
              'cache_reader_source_sha256': CACHE_READER_SHA,
              'certificate_sha256': counts.digest(certificate), 'cache_sha256': counts.digest(cache),
              'catalogue_sha256': counts.digest(catalogue),
              'completed_blocks': len(blocks), 'coverage': coverage, 'cache_parts': bindings,
              'diagonal_derivations': diagonal,
              'all_diagonal_ranges_follow_from_existing_count_rows': True,
              'general_cross_range_redundancy_proved': False,
              'point_checks': points, 'maximum_exported_cuts_per_block_and_point': 1,
              'eigensystems_computed': False, 'optimizer_called': False, 'dense_reduction_loaded': False,
              'scope': 'the completed cached subfamily; a passing point does not prove redundancy of cross ranges',
              'seconds': time.monotonic()-started}
    counts.save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key != 'point_checks'}, indent=2), flush=True)
    for point in points:
        print(json.dumps({key: value for key, value in point.items() if key not in ('blocks', 'exact_cuts')}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--cache', type=Path)
    parser.add_argument('--witness', type=Path, action='append', required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    audit(args.certificate, args.witness, args.output, args.cache)
