"""Independent integer replay of the fixed-prefix order-ten contradiction.

This verifier does not import the LP finder or its dual-ray implementation.
It reads exact reduced forms, checks every contributing primitive row,
reconstructs the sum, and verifies each used embedding bound from an
explicit vertex order and an independently recomputed automorphism order.
"""

import argparse
import ast
from functools import reduce
import hashlib
import json
from math import gcd, lcm
from pathlib import Path
import pickle

import pynauty


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def point_literal():
    path = Path(__file__).with_name('grid_free_core9_certificate.py')
    for statement in ast.parse(path.read_text()).body:
        if isinstance(statement, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'INTEGER_POINT'
                                                   for t in statement.targets):
            point = ast.literal_eval(statement.value)
            assert len(point) == 58 and point[0] == 1 and point[-2:] == [0, 0]
            return point, digest(path)
    raise AssertionError('Missing point literal')


def replay(cache, preparation_path, certificate_path, compact_path=None):
    preparation = json.loads(preparation_path.read_text())
    certificate = json.loads(certificate_path.read_text())
    assert certificate['case_index'] == 0 and certificate['fixed_order_nine_point']
    assert certificate['exact_exclusion']
    assert digest(preparation_path) == certificate['preparation_sha256']
    assert digest(cache) == certificate['reduced_cache_sha256'] == preparation['reduced_cache_sha256']
    point, point_sha = point_literal()
    with cache.open('rb') as stream:
        data, cores, scale, inj, induced = pickle.load(stream)
    del inj
    graphs, _, automorphisms, _ = data
    assert len(graphs) == 48965 and len(cores) == 549 and scale == 3628800
    assert induced.shape == (48965, 550)
    active = list(range(58, 550))
    assert preparation['cases'][0]['active_core_coordinates'] == active
    assert preparation['cases'][0]['forced_zero_coordinates'] == []
    proof = certificate['exact_reconstruction']
    rows = proof['row_multipliers']
    compact = json.loads(compact_path.read_text()) if compact_path else None
    if compact:
        assert compact['dual_certificate_sha256'] == digest(certificate_path)
        assert compact['preparation_sha256'] == digest(preparation_path)
        assert compact['reduced_cache_sha256'] == certificate['reduced_cache_sha256']
        assert compact['published_integer_point'] == point
        assert compact['old_coordinate_types'] == [None]+list(cores[:57])
        assert [r['catalogue_type'] for r in compact['induced_count_forms']] == [r['catalogue_type'] for r in rows]
        simplified = compact['denominator36_simplification']
        assert len(simplified['row_weights']) == len(rows)
        assert all(type(w) is int and w >= 0 for w in simplified['row_weights'])
    assert len({r['catalogue_type'] for r in rows}) == len(rows)
    aggregate = [0]*493
    denominator = lcm(*(r['primitive_divisor'] for r in rows))
    global_form = [0]*550
    simplified_form = [0]*550
    for row_number, item in enumerate(rows):
        index, divisor, weight = (item[k] for k in ('catalogue_type', 'primitive_divisor', 'multiplier'))
        assert type(weight) is int and weight > 0 and divisor > 0
        original = [int(x) for x in induced[index]]
        if compact:
            embedded = compact['induced_count_forms'][row_number]
            assert embedded['graph_rows'] == list(graphs[index])
            assert embedded['original_form'] == [[j, a] for j, a in enumerate(original) if a]
            assert embedded['primitive_divisor'] == divisor and embedded['original_weight'] == weight
        fixed_constant = sum(a*x for a, x in zip(original[:58], point))
        form = [fixed_constant]+original[58:]
        assert reduce(gcd, map(abs, form), 0) == divisor
        for j, value in enumerate(form):
            assert value % divisor == 0
            aggregate[j] += weight*(value//divisor)
        for j, value in enumerate(original):
            global_form[j] += weight*(denominator//divisor)*value
            if compact:
                simplified_form[j] += simplified['row_weights'][row_number]*(denominator//divisor)*value
    del induced
    claimed = proof['aggregate']
    assert aggregate[0] == claimed['constant']
    assert [[j, a] for j, a in zip(active, aggregate[1:]) if a] == claimed['coefficients']
    assert [[j, -a] for j, a in zip(active, aggregate[1:]) if a < 0] == claimed['lower_bound_terms']
    assert [[j, a] for j, a in zip(active, aggregate[1:]) if a > 0] == [
        [j, a] for j, a, _ in claimed['upper_bound_terms']]
    maximum = aggregate[0]
    checked_bounds = []
    for coordinate, coefficient, claimed_upper in claimed['upper_bound_terms']:
        assert coefficient == aggregate[1+coordinate-58] and coefficient > 0
        bound = preparation['upper_bounds'][coordinate-1]
        assert bound['coordinate'] == coordinate and bound['catalogue_type'] == cores[coordinate-1]
        graph = graphs[cores[coordinate-1]]
        assert list(graph) == bound['rows']
        n = len(graph)
        adjacency = {i: [j for j in range(n) if graph[i] >> j & 1] for i in range(n)}
        automorphism_data = pynauty.autgrp(pynauty.Graph(n, adjacency_dict=adjacency))
        group_size = automorphism_data[1]*(10**automorphism_data[2])
        assert group_size == int(group_size)
        aut = int(group_size)
        assert aut == automorphisms[cores[coordinate-1]] == bound['automorphisms']
        order = bound['minimizing_vertex_order']
        assert sorted(order) == list(range(n))
        chosen = set()
        product = 1
        factors = []
        for v in order:
            neighbors = [u for u in chosen if graph[v] >> u & 1]
            adjacent_pair = any(graph[u] >> w & 1 for u in neighbors for w in neighbors if u != w)
            factor = 99 if not neighbors else 14 if len(neighbors) == 1 else 1 if adjacent_pair else 2
            factors.append(factor)
            product *= factor
            chosen.add(v)
        assert factors == bound['factors'] and product == bound['minimum_labelled_embedding_bound']
        upper = product//aut
        assert upper == claimed_upper == bound['ordinary_count_upper_bound']
        maximum += coefficient*upper
        checked_bounds.append({'coordinate': coordinate, 'upper': upper, 'automorphisms': aut})
    assert maximum == claimed['maximum_over_exact_box'] == -67377959
    assert maximum < 0
    cut = global_form[:58]
    cut[0] += sum(global_form[j]*upper for j, _, upper in claimed['upper_bound_terms'])
    common = reduce(gcd, map(abs, cut), 0)
    cut = [a//common for a in cut]
    evaluation = sum(a*x for a, x in zip(cut, point))
    assert evaluation == maximum*denominator//common < 0
    result = {'status': 'independent exact fixed-prefix dual replay PASS',
            'source_sha256': digest(Path(__file__)), 'point_source_sha256': point_sha,
            'preparation_sha256': digest(preparation_path), 'certificate_sha256': digest(certificate_path),
            'induced_rows_used': len(rows), 'upper_bounds_used': checked_bounds,
            'lower_bounds_used': len(claimed['lower_bound_terms']),
            'exact_negative_constant': maximum,
            'global_order_nine_cut': cut, 'global_cut_value_at_frozen_point': evaluation,
            'scope': 'Excludes this fixed count prefix; does not exclude all zero-grid count assignments.'}
    if compact:
        assert all(a <= 0 for a in simplified_form[58:])
        assert sum(a < 0 for a in simplified_form[58:]) == 21
        simple_cut = simplified_form[:58]
        common = reduce(gcd, map(abs, simple_cut), 0)
        simple_cut = [a//common for a in simple_cut]
        assert simple_cut == simplified['primitive_integer_old_cut']
        value = sum(a*x for a, x in zip(simple_cut, point))
        assert value == simplified['value_at_published_integer_point'] == -2564720
        result['simplified_certificate'] = {
            'status': 'independent simplified universal cut replay PASS',
            'compact_sha256': digest(compact_path),
            'all_embedded_forms_match_exact_cache': True,
            'integer_weights': simplified['row_weights'],
            'ordinary_nonnegativity_terms': 21, 'ordinary_upper_bounds_used': 0,
            'universal_order_nine_cut': simple_cut,
            'value_at_frozen_point': value,
        }
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--compact', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.cache, args.preparation, args.certificate, args.compact)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
