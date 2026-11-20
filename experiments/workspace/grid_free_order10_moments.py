"""Separate a saved free-prefix proposal with existing order-nine PSD blocks.

Numerical eigensystems only propose integer vectors. Every recorded cut
is an exact integer linear form evaluated at the exact dyadic rationals
represented by the saved floats. This source never solves an LP.
"""

import argparse
from collections import defaultdict
from fractions import Fraction
from functools import reduce
import hashlib
import json
from math import gcd, lcm
from pathlib import Path
import pickle
import resource
import time

import numpy as np
from threadpoolctl import threadpool_limits

from grid_free_order10_scaled_cut import published_point


BASE = Path(__file__).resolve().parent


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def save(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name+'.pending')
    temporary.write_text(json.dumps(record, indent=2)+'\n')
    temporary.replace(path)


def point_from_proposal(path):
    proposal = json.loads(path.read_text())
    assert proposal['case_index'] == 1 and not proposal['fixed_order_nine_point']
    real = proposal['real_proposal']
    point = [0.0]*58
    point[0] = 1.0
    for i, x in zip(real['active_coordinates'], real['ordinary_core_values'], strict=True):
        if i < 58:
            point[i] = float(x)
    assert point[56:] == [0.0, 0.0]
    ratios = [x.as_integer_ratio() for x in point]
    denominator = lcm(*(d for _, d in ratios))
    numerator = [n*(denominator//d) for n, d in ratios]
    assert all(Fraction(n, denominator) == Fraction.from_float(x)
               for n, x in zip(numerator, point))
    return point, numerator, denominator


def load_forms():
    path = BASE/'moments-order9.pickle'
    with path.open('rb') as stream:
        graphs, levels, aut, cores, scale, inj, induced = pickle.load(stream)
    assert len(cores) == 57 and len(graphs) == 6535
    assert not np.any(induced % scale)
    rated = (induced//scale)*np.array(aut, dtype=object)[:, None]
    assert inj.dtype == object and rated.dtype == object
    return {'ordinary': inj, 'induced': rated}, digest(path)


def cache_files():
    files = [(p, 'ordinary') for p in sorted(BASE.glob('moments-?-?-512.pickle'))]
    files += [(p, 'induced') for p in sorted(BASE.glob('induced-moments-?-?-512.pickle'))]
    files += [(BASE/name, 'induced') for name in ('induced-spectral-7.pickle', 'induced-schur-7.pickle')]
    assert len(files) == 12
    return files


def numeric_matrix(T, order, embeddings):
    assert T.data.dtype.kind == 'i'
    assert T.shape[0] == order*(order+1)//2
    values = np.asarray(T@embeddings, dtype=float)
    lower = np.tril_indices(order)
    M = np.zeros((order, order), dtype=float)
    M[lower] = values
    M[(lower[1], lower[0])] = values
    assert np.all(np.isfinite(M))
    return M


def integer_form(T, vector, forms):
    """Contract a symmetric lower-triangle tensor with vv^T exactly."""
    order = len(vector)
    assert T.shape[0] == order*(order+1)//2
    weights = []
    for i in range(order):
        for j in range(i+1):
            weights.append(vector[i]*vector[j]*(1 if i == j else 2))
    coefficient = defaultdict(int)
    for row, weight in enumerate(weights):
        if weight:
            for k in range(T.indptr[row], T.indptr[row+1]):
                coefficient[int(T.indices[k])] += weight*int(T.data[k])
    entries = [(i, v) for i, v in sorted(coefficient.items()) if v]
    if not entries:
        return [0]*58, 0
    # Object multiplication prevents fixed-width overflow in the contraction.
    indices = [i for i, _ in entries]
    multipliers = np.array([v for _, v in entries], dtype=object)
    raw = multipliers@forms[indices]
    row = [int(v) for v in raw]
    common = reduce(gcd, [abs(v) for v in row], 0)
    if common:
        row = [v//common for v in row]
    return row, common


def exact_value(row, numerator, denominator):
    value = Fraction(sum(a*x for a, x in zip(row, numerator)), denominator)
    return [value.numerator, value.denominator]


def scan(proposal, output):
    started = time.monotonic()
    point, numerator, denominator = point_from_proposal(proposal)
    forms, forms_sha = load_forms()
    positive_control = published_point()
    numeric_embeddings = {kind: np.asarray(F, dtype=float)@np.array(point)
                          for kind, F in forms.items()}
    result = {'status': 'running numerical separation with exact cut gates',
              'scope': 'the saved free-prefix proposal against1416 existing cached PSD blocks',
              'source_sha256': digest(Path(__file__)),
              'proposal_path': str(proposal), 'proposal_sha256': digest(proposal),
              'order_nine_cache_sha256': forms_sha,
              'published_positive_control': positive_control,
              'point_float': point, 'point_exact_dyadic': {'numerators': numerator, 'denominator': denominator},
              'caches': [], 'negative_blocks': [], 'unique_integer_cuts': [],
              'numerical_negatives_without_exact_cut': [],
              'LP_called': False, 'new_moment_blocks_generated': False,
              'passing_blocks_PSD_certified': False}
    cut_index = {}
    examined = 0
    for path, kind in cache_files():
        with path.open('rb') as stream:
            blocks = pickle.load(stream)
        cache = {'file': path.name, 'sha256': digest(path), 'embedding_form': kind,
                 'blocks': len(blocks), 'largest_order': 0, 'exact_negative_blocks': 0,
                 'smallest_normalized_numeric_eigenvalue': 0.0}
        for index, (root, flags, T) in enumerate(blocks):
            order = len(flags)
            M = numeric_matrix(T, order, numeric_embeddings[kind])
            scales = np.sqrt(np.maximum(1.0, np.abs(np.diag(M))))
            normalized = M/scales[:, None]/scales[None, :]
            values, vectors = np.linalg.eigh(normalized)
            smallest = float(values[0])
            examined += 1
            cache['largest_order'] = max(cache['largest_order'], order)
            cache['smallest_normalized_numeric_eigenvalue'] = min(
                cache['smallest_normalized_numeric_eigenvalue'], smallest)
            if smallest >= -1e-8:
                continue
            direction = vectors[:, 0]/scales
            direction /= max(abs(direction))
            accepted = False
            for power in (8, 12, 20, 28, 36):
                vector = [int(round(float(v)*(2**power))) for v in direction]
                common = reduce(gcd, [abs(v) for v in vector], 0)
                assert common > 0
                vector = [v//common for v in vector]
                row, form_gcd = integer_form(T, vector, forms[kind])
                value = exact_value(row, numerator, denominator)
                if value[0] >= 0:
                    continue
                control_value = sum(a*x for a, x in zip(row, positive_control))
                assert control_value >= 0
                key = tuple(row)
                if key not in cut_index:
                    cut_index[key] = len(result['unique_integer_cuts'])
                    result['unique_integer_cuts'].append({'coefficients': row,
                                                         'exact_value_at_proposal': value,
                                                         'published_positive_control_value': control_value})
                result['negative_blocks'].append({
                    'cache_file': path.name, 'block_index': index, 'root_type': int(root),
                    'order': order, 'integer_vector': vector,
                    'positive_form_gcd': form_gcd, 'cut_index': cut_index[key],
                    'normalized_numeric_eigenvalue': smallest,
                    'exact_primitive_quadratic_value': value})
                cache['exact_negative_blocks'] += 1
                accepted = True
                break
            if not accepted:
                result['numerical_negatives_without_exact_cut'].append({
                    'cache_file': path.name, 'block_index': index,
                    'normalized_numeric_eigenvalue': smallest})
        result['caches'].append(cache)
        result['blocks_examined'] = examined
        result['seconds_so_far'] = time.monotonic()-started
        save(output, result)
        print(json.dumps(cache), flush=True)
        del blocks
    assert examined == 1416
    result['status'] = 'exact necessary PSD violations found' if result['negative_blocks'] else 'no exact violation found; PSD not certified'
    result['exact_negative_block_count'] = len(result['negative_blocks'])
    result['unique_integer_cut_count'] = len(result['unique_integer_cuts'])
    result['seconds'] = time.monotonic()-started
    result['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    save(output, result)
    print(json.dumps({k: result[k] for k in ('status', 'blocks_examined', 'exact_negative_block_count',
                                            'unique_integer_cut_count', 'seconds', 'peak_process_rss_kib')}), flush=True)
    return result


def replay(path):
    result = json.loads(path.read_text())
    assert result['source_sha256'] == digest(Path(__file__))
    proposal = Path(result['proposal_path'])
    assert result['proposal_sha256'] == digest(proposal)
    point, numerator, denominator = point_from_proposal(proposal)
    assert point == result['point_float']
    assert result['point_exact_dyadic'] == {'numerators': numerator, 'denominator': denominator}
    assert result['published_positive_control'] == published_point()
    forms, forms_sha = load_forms()
    assert forms_sha == result['order_nine_cache_sha256']
    grouped = defaultdict(list)
    for item in result['negative_blocks']:
        grouped[item['cache_file']].append(item)
    checked = 0
    for cache in result['caches']:
        source = BASE/cache['file']
        assert digest(source) == cache['sha256']
        with source.open('rb') as stream:
            blocks = pickle.load(stream)
        assert len(blocks) == cache['blocks']
        for item in grouped[cache['file']]:
            root, flags, T = blocks[item['block_index']]
            assert int(root) == item['root_type'] and len(flags) == item['order']
            assert len(item['integer_vector']) == len(flags)
            assert all(type(v) is int for v in item['integer_vector'])
            row, common = integer_form(T, item['integer_vector'], forms[cache['embedding_form']])
            assert common == item['positive_form_gcd'] > 0
            cut = result['unique_integer_cuts'][item['cut_index']]
            assert row == cut['coefficients']
            value = exact_value(row, numerator, denominator)
            assert value == cut['exact_value_at_proposal'] == item['exact_primitive_quadratic_value']
            assert value[0] < 0
            control = sum(a*x for a, x in zip(row, result['published_positive_control']))
            assert control == cut['published_positive_control_value'] >= 0
            checked += 1
    assert checked == result['exact_negative_block_count']
    checked_result = {'status': 'exact integer-vector PSD cut replay PASS',
                      'negative_blocks': checked,
                      'unique_integer_cuts': len(result['unique_integer_cuts']),
                      'LP_called': False, 'numerical_eigensystems_recomputed': False,
                      'passing_blocks_PSD_certified': False}
    print(json.dumps(checked_result, indent=2), flush=True)
    return checked_result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    run = sub.add_parser('scan')
    run.add_argument('--proposal', type=Path, required=True)
    run.add_argument('--output', type=Path, required=True)
    check = sub.add_parser('replay')
    check.add_argument('certificate', type=Path)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'scan':
            scan(args.proposal, args.output)
        else:
            replay(args.certificate)
