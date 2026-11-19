"""Exact domain and inverse preparation for all eight-root projector blocks.

This does not construct order-ten product tensors or load the dense core
reduction. Generation uses FLINT rational inverses only after exact
Sylvester checks. Replay checks the saved inverses with Python integers.
All neighborhood masks are retained, including sizes zero, one and two.
"""

import argparse
from collections import Counter
import hashlib
import json
from math import gcd, lcm
from pathlib import Path
import pickle
import resource
import time


CATALOGUE_SHA = '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'
PROJECTORS = [('minus', 27, -9, 1), ('plus', 44, 11, -2)]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def determinant(rows):
    """Fraction-free determinant, with unbounded Python integer entries."""
    a = [list(map(int, row)) for row in rows]
    n = len(a)
    if not n:
        return 1
    sign, previous = 1, 1
    for k in range(n-1):
        if a[k][k] == 0:
            pivot = next((i for i in range(k+1, n) if a[i][k]), None)
            if pivot is None:
                return 0
            a[k], a[pivot] = a[pivot], a[k]
            sign = -sign
        pivot = a[k][k]
        for i in range(k+1, n):
            for j in range(k+1, n):
                value = pivot*a[i][j]-a[i][k]*a[k][j]
                assert value % previous == 0
                a[i][j] = value//previous
            a[i][k] = 0
        previous = pivot
    return sign*a[-1][-1]


def caps(rows):
    return all((rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1) <= 2
               for i in range(len(rows)) for j in range(i))


def attach(rows, mask):
    r = len(rows)
    return tuple(row | (((mask >> i) & 1) << r)
                 for i, row in enumerate(rows))+(mask,)


def masks_for(rows):
    """Direct full adjacency-cap check, independent of extensions()."""
    return [mask for mask in range(1 << len(rows)) if caps(attach(rows, mask))]


def gram(rows, diagonal, edge, constant):
    n = len(rows)
    return [[diagonal*(i == j)+edge*((rows[i] >> j) & 1)+constant
             for j in range(n)] for i in range(n)]


def leading_minors(matrix):
    result = [determinant([row[:k] for row in matrix[:k]])
              for k in range(1, len(matrix)+1)]
    assert all(value > 0 for value in result), result
    return result


def inverse_data(matrix):
    # The caller has checked every leading principal minor before this call.
    from flint import fmpq_mat
    inverse = fmpq_mat(matrix).inv()
    denominator = lcm(*(int(x.q) for x in inverse.entries()))
    numerator = [[int(inverse[i, j]*denominator) for j in range(len(matrix))]
                 for i in range(len(matrix))]
    return denominator, numerator


def verify_inverse(matrix, denominator, numerator):
    n = len(matrix)
    assert type(denominator) is int and denominator > 0
    assert len(numerator) == n and all(len(row) == n for row in numerator)
    assert all(type(x) is int for row in numerator for x in row)
    assert all(numerator[i][j] == numerator[j][i]
               for i in range(n) for j in range(n))
    assert all(sum(matrix[i][k]*numerator[k][j] for k in range(n))
               == denominator*(i == j) for i in range(n) for j in range(n))
    assert gcd(denominator, *(x for row in numerator for x in row)) == 1


def projection_record(rows, masks, parameters, stored=None):
    name, diagonal, edge, constant = parameters
    r = len(rows)
    matrix = gram(rows, diagonal, edge, constant)
    minors = leading_minors(matrix)
    if stored is None:
        denominator, numerator = inverse_data(matrix)
    else:
        denominator = stored['inverse_denominator']
        numerator = stored['inverse_numerator']
    verify_inverse(matrix, denominator, numerator)

    crosses = [[constant+edge*((mask >> i) & 1) for i in range(r)]
               for mask in masks]
    first = [[sum(c[k]*numerator[k][j] for k in range(r))
              for j in range(r)] for c in crosses]
    first_bound = max(sum(abs(c[k]*numerator[k][j]) for k in range(r))
                      for c in crosses for j in range(r))
    maximum_cross_by_coordinate = [max(abs(c[i]) for c in crosses)
                                   for i in range(r)]
    second_bound = max(sum(abs(row[i])*maximum_cross_by_coordinate[i]
                           for i in range(r)) for row in first)

    # Every c_mask is an integer linear combination of c_0 and the r
    # singleton crosses. Hence these (r+1)^2 pairings determine the gcd
    # of the denominator and every possible inverse-product numerator.
    pivot_masks = [0]+[1 << i for i in range(r)]
    pivots = [masks.index(mask) for mask in pivot_masks]
    pivot_products = [[sum(first[i][k]*crosses[j][k] for k in range(r))
                       for j in pivots] for i in pivots]
    divisor = gcd(denominator, *(x for row in pivot_products for x in row))
    for mask, cross in zip(masks, crosses):
        combination = [sum(crosses[pivots[i+1]][j] for i in range(r)
                           if mask >> i & 1)
                       -(mask.bit_count()-1)*crosses[pivots[0]][j]
                       for j in range(r)]
        assert combination == cross
    result = {
        'projector': name,
        'parameters': [diagonal, edge, constant],
        'root_leading_principal_minors': minors,
        'root_positive_definite_before_inversion': True,
        'inverse_denominator': denominator,
        'inverse_numerator': numerator,
        'inverse_identity_checked_exactly': True,
        'schur_common_divisor': divisor,
        'schur_denominator': denominator//divisor,
        'cross_pivot_pairings': pivot_products,
        'max_abs_inverse_numerator': max(abs(x) for row in numerator for x in row),
        'first_product_absolute_sum_bound': first_bound,
        'second_product_absolute_sum_bound': second_bound,
        'reduced_schur_coefficient_absolute_bound':
            (denominator//divisor)*max(abs(constant), abs(edge+constant),
                                      abs(diagonal+constant))+second_bound//divisor,
        'first_and_second_products_fit_signed_int64':
            max(first_bound, second_bound) < 1 << 63,
    }
    if stored is not None:
        assert result == stored
    return result


def record(rows, index, stored=None):
    rows = tuple(rows)
    assert len(rows) == 8 and caps(rows)
    masks = masks_for(rows)
    assert all(mask in masks for mask in [0]+[1 << i for i in range(8)])
    by_size = Counter(mask.bit_count() for mask in masks)
    residual_degrees = [14-row.bit_count() for row in rows]
    residual_pairs = [[i, j, 2-((rows[i] >> j) & 1)-(rows[i] & rows[j]).bit_count()]
                      for i in range(8) for j in range(i)]
    for i, j, residual in residual_pairs:
        pair = (1 << i) | (1 << j)
        assert (pair in masks) == (residual > 0)
        if residual == 0:
            assert all(mask & pair != pair for mask in masks)
    # A mask of size at least three can occur at most once at a fixed root:
    # two distinct vertices with that mask would have three common neighbors.
    high = [mask for mask in masks if mask.bit_count() >= 3]
    result = {
        'root_type': index, 'root_rows': list(rows), 'masks': masks,
        'classes': len(masks), 'masks_by_size': dict(sorted(by_size.items())),
        'high_masks_binary': len(high),
        'residual_degrees': residual_degrees,
        'residual_pairs': residual_pairs,
        'spectral_order': 8+len(masks), 'schur_order': len(masks),
        'spectral_order_after_nine_kernel_pivots': len(masks)-1,
        'schur_order_after_nine_kernel_pivots': len(masks)-9,
        'projectors': [projection_record(rows, masks, p,
                        None if stored is None else stored['projectors'][i])
                       for i, p in enumerate(PROJECTORS)],
    }
    if stored is not None:
        # JSON object keys are strings; the independent reconstruction uses ints.
        result['masks_by_size'] = {str(k): v for k, v in result['masks_by_size'].items()}
        assert result == stored
    return result


def rook_control(stored=None):
    host = tuple(sum(1 << j for j in range(9) if i != j and
                     (i//3 == j//3 or i % 3 == j % 3)) for i in range(9))
    rows = tuple(row & 255 for row in host[:8])
    outside_mask = host[8]
    assert attach(rows, outside_mask) == host
    masks = masks_for(rows)
    assert outside_mask in masks
    results = []
    for i, parameters in enumerate(PROJECTORS):
        saved = None if stored is None else stored['projectors'][i]['inverse_certificate']
        certificate = projection_record(rows, masks, parameters, saved)
        name, diagonal, edge, constant = parameters
        cross = [constant+edge*((outside_mask >> j) & 1) for j in range(8)]
        denominator = certificate['inverse_denominator']
        numerator = certificate['inverse_numerator']
        projected_numerator = ((diagonal+constant)*denominator
            -sum(cross[a]*numerator[a][b]*cross[b] for a in range(8) for b in range(8)))
        assert projected_numerator >= 0
        assert (projected_numerator == 0) == (name == 'minus')
        full = gram(host, diagonal, edge, constant)
        assert determinant(full)*denominator == projected_numerator*certificate['root_leading_principal_minors'][-1]
        results.append({'projector': name, 'inverse_certificate': certificate,
                        'actual_outside_mask': outside_mask,
                        'one_vertex_schur_numerator': projected_numerator,
                        'one_vertex_schur_denominator': denominator,
                        'full_nine_rook_projector_is_PSD': True})
    result = {'host_rows': list(host), 'root_rows': list(rows), 'projectors': results,
              'control_scope': 'Direct root-plus-one-vertex Gram and exact Schur identity; not SRG(99,14,1,2) count identities.'}
    if stored is not None:
        assert result == stored
    return result


def summary(records):
    sizes = [item['classes'] for item in records]
    projectors = [p for item in records for p in item['projectors']]
    by_size = Counter()
    for item in records:
        by_size.update({int(k): v for k, v in item['masks_by_size'].items()})
    return {
        'root_count': len(records), 'root_orders': [8],
        'all_outside_classes': sum(sizes),
        'masks_by_size': {str(k): v for k, v in sorted(by_size.items())},
        'minimum_classes': min(sizes), 'maximum_classes': max(sizes),
        'spectral_blocks_both_projectors': 2*len(records),
        'schur_blocks_both_projectors': 2*len(records),
        'spectral_lower_entries_both_projectors': sum((m+8)*(m+9) for m in sizes),
        'schur_lower_entries_both_projectors': sum(m*(m+1) for m in sizes),
        'spectral_quotient_lower_entries_both_projectors': sum((m-1)*m for m in sizes),
        'schur_quotient_lower_entries_both_projectors': sum((m-9)*(m-8) for m in sizes),
        'spectral_coefficient_placements_upper_bound': sum(2*(36+9*m+m*(m+1)) for m in sizes),
        'schur_coefficient_placements_upper_bound': sum(2*(m+m*(m+1)) for m in sizes),
        'root_PD_certificates': len(projectors),
        'leading_principal_minors_checked': 8*len(projectors),
        'minimum_leading_principal_minor': min(min(p['root_leading_principal_minors']) for p in projectors),
        'maximum_inverse_denominator': max(p['inverse_denominator'] for p in projectors),
        'maximum_reduced_schur_denominator': max(p['schur_denominator'] for p in projectors),
        'maximum_first_product_absolute_sum_bound': max(p['first_product_absolute_sum_bound'] for p in projectors),
        'maximum_second_product_absolute_sum_bound': max(p['second_product_absolute_sum_bound'] for p in projectors),
        'maximum_reduced_schur_coefficient_absolute_bound': max(p['reduced_schur_coefficient_absolute_bound'] for p in projectors),
        'all_inverse_product_bounds_fit_signed_int64': all(p['first_and_second_products_fit_signed_int64'] for p in projectors),
        'construction_and_replay_arithmetic': 'Python integers, plus exact FLINT rational inversion during generation only',
    }


def load_data(catalogue):
    assert digest(catalogue) == CATALOGUE_SHA
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    assert len(data[0]) == 48965 and len(data[1][8]) == 916
    return data


def generate(catalogue, output):
    started = time.monotonic()
    assert not output.exists()
    data = load_data(catalogue)
    graphs, levels = data[:2]
    from subgraph_counts import extensions
    records = []
    for root in levels[8]:
        item = record(graphs[root], root)
        assert item['masks'] == [mask for mask, _ in extensions(graphs[root])]
        records.append(item)
    result = {
        'status': 'complete eight-root domain and exact inverse preparation',
        'source_sha256': digest(Path(__file__)), 'catalogue_sha256': CATALOGUE_SHA,
        'reference_extension_source_sha256': digest(Path(__file__).with_name('subgraph_counts.py')),
        'summary': summary(records), 'roots': records,
        'direct_nine_rook_control': rook_control(),
        'all_masks_compared_to_existing_extensions': True,
        'point_dependent_pruning': False, 'product_tensors_generated': False,
        'dense_reduction_loaded': False, 'optimizer_called': False,
        'seconds': time.monotonic()-started,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('roots', 'direct_nine_rook_control')}, indent=2), flush=True)
    print('certificate_sha256', digest(output), flush=True)


def replay(catalogue, certificate, output):
    started = time.monotonic()
    assert not output.exists()
    saved = json.loads(certificate.read_text())
    assert saved['source_sha256'] == digest(Path(__file__))
    assert saved['catalogue_sha256'] == CATALOGUE_SHA
    data = load_data(catalogue)
    graphs, levels = data[:2]
    assert [item['root_type'] for item in saved['roots']] == levels[8]
    for item in saved['roots']:
        root = item['root_type']
        assert item['root_rows'] == list(graphs[root])
        record(graphs[root], root, item)
    assert summary(saved['roots']) == saved['summary']
    rook_control(saved['direct_nine_rook_control'])
    result = {
        'status': 'exact domain, PD and inverse replay PASS',
        'source_sha256': digest(Path(__file__)), 'certificate_sha256': digest(certificate),
        'catalogue_sha256': CATALOGUE_SHA, 'summary': saved['summary'],
        'rational_inverses_recomputed': False,
        'saved_inverses_verified_by_integer_matrix_identity': True,
        'all_arithmetic_is_unbounded_Python_integer': True,
        'product_tensors_generated': False, 'dense_reduction_loaded': False,
        'optimizer_called': False, 'seconds': time.monotonic()-started,
    }
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path, default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--replay', type=Path)
    args = parser.parse_args()
    if args.replay is None:
        generate(args.catalogue, args.output)
    else:
        replay(args.catalogue, args.replay, args.output)
