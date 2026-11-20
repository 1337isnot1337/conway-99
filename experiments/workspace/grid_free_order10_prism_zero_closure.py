"""Exact zero propagation from the single prism-count assumption x1=0.

A zero-constant induced-count form with no positive remaining coefficient
forces all supported nonnegative core coordinates to zero. The saved trace
uses only these implications. No count point or optimizer is needed.
"""

import argparse
from collections import Counter
from functools import reduce
import json
from math import gcd
from pathlib import Path
import time

import numpy as np
from threadpoolctl import threadpool_limits

import grid_free_order10_scaled as counts


def prism(rows):
    triangles = []
    for i, neighbors in enumerate(rows):
        for j in range(i+1, len(rows)):
            if not (neighbors >> j & 1):
                continue
            common = neighbors & rows[j] & ~((1 << (j+1))-1)
            while common:
                bit = common & -common
                common ^= bit
                triangles.append((1 << i) | (1 << j) | bit)
    for a, left in enumerate(triangles):
        for right in triangles[:a]:
            if left & right:
                continue
            if all((rows[i] & right).bit_count() == 1 for i in range(len(rows)) if left >> i & 1):
                if all((rows[i] & left).bit_count() == 1 for i in range(len(rows)) if right >> i & 1):
                    return True
    return False


def primitive_row(row):
    terms = [[int(j), int(row[j])] for j in np.flatnonzero(row)]
    divisor = reduce(gcd, [abs(value) for _, value in terms], 0)
    assert divisor > 0
    return [[j, value//divisor] for j, value in terms], divisor


def generate(cache, output):
    started = time.monotonic()
    data, cores, scale, matrix = counts.load_reduced(cache)
    assert cores[0] == 99 and prism(data[0][99])
    zeros = {1}
    positive = np.count_nonzero(matrix[:, 1:] > 0, axis=1)-(matrix[:, 1] > 0)
    negative = np.count_nonzero(matrix[:, 1:] < 0, axis=1)-(matrix[:, 1] < 0)
    zero_constant = matrix[:, 0] == 0
    trace = []
    while True:
        candidates = np.flatnonzero(zero_constant & (positive == 0) & (negative > 0))
        if not len(candidates):
            break
        row_index = int(candidates[0])
        row = matrix[row_index]
        fresh = [int(j) for j in np.flatnonzero(row < 0) if int(j) not in zeros]
        assert fresh and all(j > 0 for j in fresh)
        assert all(j in zeros for j in np.flatnonzero(row > 0))
        terms, divisor = primitive_row(row)
        trace.append({'induced_type': row_index, 'graph_rows': list(data[0][row_index]),
                      'primitive_count_inequality': terms, 'raw_positive_gcd': divisor,
                      'forced_zero_coordinates': fresh})
        for coordinate in fresh:
            zeros.add(coordinate)
            positive -= matrix[:, coordinate] > 0
            negative -= matrix[:, coordinate] < 0
        assert np.all(positive >= 0) and np.all(negative >= 0)
    graph_zeros = [j for j, root in enumerate(cores, 1) if prism(data[0][root])]
    induced_prisms = [i for i, graph in enumerate(data[0]) if prism(graph)]
    reached, frontier = {99}, [99]
    while frontier:
        parent = frontier.pop()
        if parent >= len(data[3]):
            continue
        for _, child in data[3][parent]:
            if child not in reached:
                reached.add(child)
                frontier.append(child)
    assert reached == set(induced_prisms)
    remaining = [0]+[j for j in range(1, 550) if j not in zeros]
    residual = matrix[np.ix_(induced_prisms, remaining)]
    nonzero = int(np.count_nonzero(residual))
    graph_remaining = [0]+[j for j in range(1, 550) if j not in set(graph_zeros)]
    graph_nonzero = int(np.count_nonzero(matrix[np.ix_(induced_prisms, graph_remaining)]))
    result = {'status': 'exact prism-containment zero closure; sign propagation recorded separately',
              'source_sha256': counts.digest(Path(__file__)),
              'finder_source_sha256': counts.digest(Path(counts.__file__)),
              'reduced_cache_path': str(cache), 'reduced_cache_sha256': counts.digest(cache),
              'assumptions': {'constant_coordinate': [0, 1], 'initial_zero_coordinates': [1],
                              'all_ordinary_core_counts_nonnegative': True,
                              'all_induced_count_forms_nonnegative': True},
              'scale': scale, 'forced_zero_coordinates': sorted(zeros),
              'zero_coordinate_count': len(zeros), 'trace': trace,
              'prism_containing_core_coordinates': graph_zeros,
              'prism_containing_induced_types': induced_prisms,
              'induced_prism_count': len(induced_prisms),
              'induced_prism_counts_by_order': dict(Counter(len(data[0][i]) for i in induced_prisms)),
              'extension_DAG_reaches_exactly_induced_prism_types': True,
              'remaining_coordinates_including_constant': remaining,
              'residual_prism_form_nonzero_coefficients': nonzero,
              'all_induced_prism_forms_vanish_coefficientwise': nonzero == 0,
              'prism_containing_core_zero_count': len(graph_zeros),
              'sign_propagation_recovers_all_prism_core_zeros': sorted(zeros) == graph_zeros,
              'free_core_coordinates_after_prism_containment': 549-len(graph_zeros),
              'remaining_after_prism_core_zeros': graph_remaining,
              'residual_after_prism_core_zeros': graph_nonzero,
              'all_induced_prism_forms_vanish_after_prism_core_zeros': graph_nonzero == 0,
              'free_core_coordinates': 549-len(zeros), 'optimizer_called': False,
              'count_point_used': False, 'seconds': time.monotonic()-started}
    counts.save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key not in
                     ('trace', 'prism_containing_induced_types', 'remaining_coordinates_including_constant',
                      'remaining_after_prism_core_zeros')}, indent=2), flush=True)
    return result


def replay(certificate):
    result = json.loads(certificate.read_text())
    assert result['source_sha256'] == counts.digest(Path(__file__))
    assert result['assumptions']['constant_coordinate'] == [0, 1]
    assert result['assumptions']['initial_zero_coordinates'] == [1]
    zeros = {1}
    for step in result['trace']:
        row = dict(step['primitive_count_inequality'])
        assert all(type(j) is int and type(value) is int for j, value in row.items())
        assert row.get(0, 0) == 0
        assert all(j in zeros for j, value in row.items() if value > 0)
        fresh = sorted(j for j, value in row.items() if value < 0 and j not in zeros)
        assert fresh == step['forced_zero_coordinates'] and fresh
        zeros.update(fresh)
    assert sorted(zeros) == result['forced_zero_coordinates']
    assert len(zeros) == result['zero_coordinate_count']
    cache = Path(result['reduced_cache_path'])
    assert counts.digest(cache) == result['reduced_cache_sha256']
    assert counts.digest(Path(counts.__file__)) == result['finder_source_sha256']
    data, cores, scale, matrix = counts.load_reduced(cache)
    assert scale == result['scale']
    for step in result['trace']:
        index = step['induced_type']
        assert list(data[0][index]) == step['graph_rows']
        row, divisor = primitive_row(matrix[index])
        assert row == step['primitive_count_inequality'] and divisor == step['raw_positive_gcd']
    graph_zeros = [j for j, root in enumerate(cores, 1) if prism(data[0][root])]
    assert graph_zeros == result['prism_containing_core_coordinates']
    assert len(graph_zeros) == result['prism_containing_core_zero_count'] == 58
    types = [i for i, rows in enumerate(data[0]) if prism(rows)]
    assert types == result['prism_containing_induced_types'] and len(types) == 1443
    remaining = [0]+[j for j in range(1, 550) if j not in zeros]
    assert int(np.count_nonzero(matrix[np.ix_(types, remaining)])) == result['residual_prism_form_nonzero_coefficients']
    graph_remaining = [0]+[j for j in range(1, 550) if j not in set(graph_zeros)]
    assert graph_remaining == result['remaining_after_prism_core_zeros']
    assert not np.any(matrix[np.ix_(types, graph_remaining)])
    reached, frontier = {99}, [99]
    while frontier:
        parent = frontier.pop()
        if parent >= len(data[3]):
            continue
        for _, child in data[3][parent]:
            if child not in reached:
                reached.add(child)
                frontier.append(child)
    assert reached == set(types)
    answer = {'status': 'exact sign trace and prism-containment closure replay PASS',
              'initial_zero_coordinate': 1, 'sign_rule_zero_coordinates': len(zeros),
              'prism_containing_core_zero_coordinates': 58,
              'trace_steps': len(result['trace']), 'vanishing_induced_prism_forms': 1443,
              'free_core_coordinates_after_prism_containment': 491,
              'count_point_used': False, 'optimizer_called': False}
    print(json.dumps(answer, indent=2), flush=True)
    return answer


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    build = sub.add_parser('generate')
    build.add_argument('--cache', type=Path, required=True)
    build.add_argument('--output', type=Path, required=True)
    check = sub.add_parser('replay')
    check.add_argument('--certificate', type=Path, required=True)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'generate':
            generate(args.cache, args.output)
        else:
            replay(args.certificate)
