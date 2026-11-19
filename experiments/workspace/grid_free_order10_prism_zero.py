"""One bounded IPM feasibility probe with the ordinary prism count fixed to zero.

The frozen order-ten count model and all fourteen certified cuts are retained.
Preparation performs no optimization. The run uses at most120 solver seconds,
one thread, and no crossover or dual-ray extraction. Every returned numerical
solution is preserved; exact count and cut checks govern witness acceptance.
"""

import argparse
import hashlib
from itertools import combinations, permutations
import json
from math import isfinite
from pathlib import Path
import resource
from threading import Timer
import time

import highspy
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits

import grid_free_order10_moments_loop as previous
import grid_free_order10_moments as separator
import grid_free_order10_scaled as counts


LOOP_SHA = '549233611473b1c3558bb19a26d6dbeb532463123684e023963f05dab58ed4f4'
LOOP_PREPARATION_SHA = 'bc52efaa911054ef463a16b3043f9a30921664cb1414c60847a84b775b219c97'
LOOP_RESULT_SHA = '5030c57981c1d32e05c1c867082135e8706bb235a3f82253b552ebb682fc34fb'
REDUCTION_AUDIT_SOURCE_SHA = '3f85d8597e34f36ca1f55fd578b96bbe29ef6e8decf88e40c319b73b35dbc5a2'
PRISM_ROWS = [28, 56, 49, 35, 7, 14]


def ordinary_embedding(pattern, host):
    edges = [(i, j) for i, j in combinations(range(len(pattern)), 2)
             if pattern[i] >> j & 1]
    for image in permutations(range(len(host)), len(pattern)):
        if all(host[image[i]] >> image[j] & 1 for i, j in edges):
            return list(image)
    return None


def coordinate_control(base_preparation):
    saved = json.loads(base_preparation.read_text())
    records = {row['coordinate']: row for row in saved['upper_bounds']}
    prism = records[1]
    assert prism['catalogue_type'] == 99 and prism['rows'] == PRISM_ROWS
    assert prism['automorphisms'] == 12 and prism['ordinary_count_upper_bound'] == 3234
    standard = [14, 21, 35, 49, 42, 28]
    iso = ordinary_embedding(PRISM_ROWS, standard)
    assert iso is not None
    assert all(bool(PRISM_ROWS[i] >> j & 1) == bool(standard[iso[i]] >> iso[j] & 1)
               for i, j in combinations(range(6), 2))
    containment = []
    for coordinate, edges in ((56, 17), (57, 18)):
        row = records[coordinate]
        assert len(row['rows']) == 9
        assert sum(v.bit_count() for v in row['rows']) == 2*edges
        image = ordinary_embedding(PRISM_ROWS, row['rows'])
        assert image is not None
        containment.append({'coordinate': coordinate, 'catalogue_type': row['catalogue_type'],
                            'host_rows': row['rows'], 'ordinary_prism_embedding': image})
    return {'coordinate': 1, 'catalogue_type': 99, 'rows': PRISM_ROWS,
            'count_kind': 'ordinary unlabeled prism copies', 'automorphisms': 12,
            'ordinary_count_upper_bound': 3234, 'standard_prism_rows': standard,
            'isomorphism_to_standard_prism': iso,
            'prism_containment_in_zeroed_nine_vertex_patterns': containment}


def read_certified_cuts(loop_preparation, loop_result):
    assert counts.digest(Path(previous.__file__)) == LOOP_SHA
    assert counts.digest(loop_preparation) == LOOP_PREPARATION_SHA
    assert counts.digest(loop_result) == LOOP_RESULT_SHA
    prepared = json.loads(loop_preparation.read_text())
    result = json.loads(loop_result.read_text())
    assert prepared['source_sha256'] == result['source_sha256'] == LOOP_SHA
    assert result['preparation_sha256'] == LOOP_PREPARATION_SHA
    assert len(result['cuts']) == 14
    paths = {name: Path(value) for name, value in prepared['inputs'].items()}
    for name, path in paths.items():
        assert counts.digest(path) == prepared['input_hashes'][name]
    seed = previous.initial_cuts(paths['moment_certificate'], paths['universal_certificate'])
    assert result['cuts'][:5] == seed
    replayed = {}
    for item in result['cuts'][5:]:
        origin = item['origin']
        assert origin['kind'] == 'exact PSD separator'
        path = Path(origin['certificate_path'])
        assert counts.digest(path) == origin['certificate_sha256']
        if path not in replayed:
            separator.replay(path)
            replayed[path] = json.loads(path.read_text())
        cut = replayed[path]['unique_integer_cuts'][origin['cut_index']]
        assert cut['coefficients'] == item['coefficients']
        assert cut['exact_value_at_proposal'][0] < 0
    assert len({tuple(row['coefficients']) for row in result['cuts']}) == 14
    assert all(len(row['coefficients']) == 58 and
               all(type(value) is int for value in row['coefficients'])
               for row in result['cuts'])
    return paths, result['cuts'], {str(p): counts.digest(p) for p in replayed}


def supported_options(seconds):
    h = highspy.Highs()
    options = {'output_flag': False, 'threads': 1, 'presolve': 'on',
               'solver': 'ipm', 'run_crossover': 'off', 'time_limit': float(seconds)}
    for name, value in options.items():
        assert h.setOptionValue(name, value) == highspy.HighsStatus.kOk
        status, actual = h.getOptionValue(name)
        assert status == highspy.HighsStatus.kOk and actual == value
    return h, options


def numerical_model_hash(matrix, rhs, lower, upper):
    h = hashlib.sha256()
    h.update(json.dumps({'format': 'CSC', 'shape': list(matrix.shape)},
                        sort_keys=True, separators=(',', ':')).encode())
    for name, values, dtype in [('start', matrix.indptr, '<i8'),
                                ('index', matrix.indices, '<i8'),
                                ('value', matrix.data, '<f8'),
                                ('row_upper', rhs, '<f8'),
                                ('column_lower', lower, '<f8'),
                                ('column_upper', upper, '<f8')]:
        h.update(name.encode())
        h.update(np.asarray(values, dtype=dtype).tobytes())
    return h.hexdigest()


def model(loop_preparation, loop_result, reduction_audit):
    paths, cuts, replayed = read_certified_cuts(loop_preparation, loop_result)
    audit = json.loads(reduction_audit.read_text())
    assert audit['source_sha256'] == REDUCTION_AUDIT_SOURCE_SHA
    assert audit['cache_sha256'] == counts.digest(paths['reduced_cache'])
    assert audit['original_equations_checked'] == 180445
    assert audit['distinct_nonzero_reduced_equations'] == 0
    assert audit['nonzero_reduced_equations'] == []
    assert audit['induced_count_forms_integral_coefficientwise'] is True
    assert audit['ordinary_count_forms_integral_coefficientwise'] is True
    data, scale, coefficients, metadata, numeric = previous.load_base(
        paths['reduced_cache'], paths['base_preparation'])
    base, rhs, fixed, upper = numeric
    active = metadata['active_core_coordinates']
    assert active[0] == 1 and len(active) == 547
    assert fixed == {0: 1, 56: 0, 57: 0}
    extra, extra_rhs = previous.cut_matrix(cuts, active, upper, fixed)
    matrix = sparse.vstack([base, extra], format='csc')
    matrix.sort_indices()
    rhs = np.concatenate((rhs, extra_rhs))
    lower, col_upper = np.zeros(len(active)), np.ones(len(active))
    prism_column = active.index(1)
    col_upper[prism_column] = 0.0
    control = coordinate_control(paths['base_preparation'])
    assert upper[1] == control['ordinary_count_upper_bound']
    metadata_out = {
        'rows': int(matrix.shape[0]), 'stored_columns': int(matrix.shape[1]),
        'free_columns': len(active)-1, 'nonzeros': int(matrix.nnz),
        'active_core_coordinates': active, 'base_fixed_coordinates': sorted(fixed.items()),
        'effective_fixed_coordinates': [[0, 1], [1, 0], [56, 0], [57, 0]],
        'prism_column_zero_based': prism_column, 'prism_numerical_bounds': [0, 0],
        'prism_scaling': upper[1], 'additional_count_cuts': 1, 'additional_PSD_cuts': 13,
        'cut_coefficients_sha256': hashlib.sha256(json.dumps(
            [row['coefficients'] for row in cuts], separators=(',', ':')).encode()).hexdigest(),
        'numerical_model_sha256': numerical_model_hash(matrix, rhs, lower, col_upper),
        'coordinate_control': control, 'base_input_hashes': {name: counts.digest(path)
                                                            for name, path in paths.items()},
        'additional_separator_certificate_hashes': replayed,
        'objective': 'zero; pure feasibility',
        'new_zero_propagation': False,
        'row_scaling': 'unchanged frozen base scaling plus frozen cut normalization',
    }
    assert metadata_out['rows'] == 47634 and metadata_out['nonzeros'] == 5427993
    return data, scale, coefficients, metadata_out, (matrix, rhs, lower, col_upper, fixed, upper), cuts


def prepare(loop_preparation, loop_result, reduction_audit, output):
    started = time.monotonic()
    _, _, _, metadata, _, _ = model(loop_preparation, loop_result, reduction_audit)
    h, options = supported_options(120)
    result = {
        'status': 'prism-zero IPM model prepared; no optimization run',
        'source_sha256': counts.digest(Path(__file__)),
        'inputs': {'loop_preparation': str(loop_preparation), 'loop_result': str(loop_result),
                   'reduction_audit': str(reduction_audit)},
        'input_hashes': {'loop_preparation': counts.digest(loop_preparation),
                         'loop_result': counts.digest(loop_result),
                         'reduction_audit': counts.digest(reduction_audit)},
        'dependency_hashes': {'grid_free_order10_moments_loop.py': LOOP_SHA,
                              'grid_free_order10_scaled.py': previous.FINDER_SHA,
                              'grid_free_order10_moments.py': previous.SEPARATOR_SHA,
                              'grid_free_order10_scaled_cut.py': previous.CUT_SHA},
        'model': metadata, 'highs_version': h.version(), 'supported_options': options,
        'maximum_solver_seconds': 120, 'maximum_solver_calls': 1,
        'dual_extraction': False, 'preparation_seconds': time.monotonic()-started,
        'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    counts.save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'model'}, indent=2), flush=True)
    print(json.dumps({k: v for k, v in metadata.items() if k != 'active_core_coordinates'}, indent=2), flush=True)
    return result


def numeric(value):
    value = float(value)
    return value if isfinite(value) else repr(value)


def returned_data(h):
    solution, info = h.getSolution(), h.getInfo()
    scalar_info = {}
    for name in dir(info):
        if name.startswith('_'):
            continue
        value = getattr(info, name)
        if type(value) in (str, bool, int):
            scalar_info[name] = value
        elif type(value) is float:
            scalar_info[name] = numeric(value)
    return {'value_valid': bool(solution.value_valid), 'dual_valid': bool(solution.dual_valid),
            'column_values': [numeric(v) for v in solution.col_value],
            'row_values': [numeric(v) for v in solution.row_value],
            'column_duals': [numeric(v) for v in solution.col_dual],
            'row_duals': [numeric(v) for v in solution.row_dual],
            'info': scalar_info}


def run(preparation, output, prefix, seconds):
    saved = json.loads(preparation.read_text())
    assert saved['source_sha256'] == counts.digest(Path(__file__))
    for name, digest in saved['dependency_hashes'].items():
        assert counts.digest(Path(__file__).with_name(name)) == digest
    paths = {key: Path(value) for key, value in saved['inputs'].items()}
    for key, path in paths.items():
        assert counts.digest(path) == saved['input_hashes'][key]
    data, scale, coefficients, metadata, numeric_model, cuts = model(**paths)
    assert metadata == saved['model']
    matrix, rhs, lower, col_upper, fixed, upper = numeric_model
    h, options = supported_options(seconds)
    assert h.version() == saved['highs_version']
    h.HandleUserInterrupt = True
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = matrix.shape[1], matrix.shape[0]
    lp.col_cost_, lp.col_lower_, lp.col_upper_ = np.zeros(matrix.shape[1]), lower, col_upper
    lp.row_lower_, lp.row_upper_ = np.full(matrix.shape[0], -highspy.kHighsInf), rhs
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = (
        matrix.indptr, matrix.indices, matrix.data)
    assert h.passModel(lp) == highspy.HighsStatus.kOk
    result = {'status': 'running the single bounded prism-zero IPM probe',
              'source_sha256': saved['source_sha256'], 'preparation_sha256': counts.digest(preparation),
              'numerical_model_sha256': metadata['numerical_model_sha256'],
              'options': options, 'fixed_order_nine_point': False,
              'effective_fixed_coordinates': metadata['effective_fixed_coordinates'],
              'solver_calls': 0, 'dual_extraction_performed': False,
              'exact_count_witness': False, 'PSD_feasibility_certified': False,
              'exact_infeasibility_certificate': False}
    counts.save(output, result)
    started = time.monotonic()
    timer = Timer(seconds, h.cancelSolve)
    timer.start()
    try:
        run_status = h.run()
    finally:
        timer.cancel()
    result.update(solver_calls=1, solver_seconds=time.monotonic()-started,
                  highs_run_status=str(run_status), numerical_status=str(h.getModelStatus()))
    raw = returned_data(h)
    raw.update(source_sha256=saved['source_sha256'], preparation_sha256=counts.digest(preparation),
               numerical_status=result['numerical_status'], numerical_model_sha256=metadata['numerical_model_sha256'],
               scope='Returned numerical data; validity flags and model status are retained.')
    raw_path = prefix.with_name(prefix.name+'-solver-data.json')
    counts.save(raw_path, raw)
    result.update(returned_data_path=str(raw_path), returned_data_sha256=counts.digest(raw_path),
                  returned_value_valid=raw['value_valid'], returned_dual_valid=raw['dual_valid'],
                  solver_info=raw['info'])
    result['status'] = 'bounded numerical result recorded; no exact infeasibility conclusion'
    counts.save(output, result)
    print(json.dumps({k: result[k] for k in ('numerical_status', 'solver_seconds',
                                           'returned_value_valid', 'returned_dual_valid')}, indent=2), flush=True)
    values = raw['column_values']
    if raw['value_valid'] and len(values) == matrix.shape[1] and all(type(v) is float for v in values):
        active = metadata['active_core_coordinates']
        ordinary = [value*upper[j] for j, value in zip(active, values)]
        proposal_path = prefix.with_name(prefix.name+'-proposal.json')
        proposal = {'status': 'returned numerical prism-zero proposal; exact feasibility not certified',
                    'source_sha256': saved['source_sha256'], 'preparation_sha256': counts.digest(preparation),
                    'numerical_status': result['numerical_status'], 'case_index': 1,
                    'fixed_order_nine_point': False, 'prism_zero_required': True,
                    'numerical_prism_coordinate': ordinary[active.index(1)],
                    'real_proposal': {'active_coordinates': active, 'scaled_values': values,
                                      'ordinary_core_values': ordinary,
                                      'exact_real_feasibility_certified': False}}
        counts.save(proposal_path, proposal)
        separation_path = prefix.with_name(prefix.name+'-separation.json')
        separated = separator.scan(proposal_path, separation_path)
        point = [0]*550
        for j, value in fixed.items():
            point[j] = value
        for j, value in zip(active, ordinary):
            point[j] = min(upper[j], max(0, int(round(value))))
        point[1] = 0
        assert point[1] == point[56] == point[57] == 0 and point[0] == 1
        checked = counts.exact_candidate(data, scale, coefficients, point, upper, False)
        cut_values = [sum(a*x for a, x in zip(cut['coefficients'], point[:58])) for cut in cuts]
        checked['fourteen_exact_cut_values'] = cut_values
        checked['negative_held_cuts'] = sum(value < 0 for value in cut_values)
        checked['prism_coordinate_fixed_exactly_to_zero'] = True
        checked_path = prefix.with_name(prefix.name+'-rounded-counts.json')
        counts.save(checked_path, checked)
        result.update(proposal_path=str(proposal_path), proposal_sha256=counts.digest(proposal_path),
                      separator_path=str(separation_path), separator_sha256=counts.digest(separation_path),
                      rounded_counts_path=str(checked_path), rounded_counts_sha256=counts.digest(checked_path),
                      exact_negative_PSD_blocks=separated['exact_negative_block_count'],
                      exact_separator_count=separated['unique_integer_cut_count'],
                      rounded_count_status=checked['status'],
                      rounded_negative_held_cuts=checked['negative_held_cuts'],
                      exact_count_witness=('induced_counts' in checked and not checked['negative_held_cuts']))
    else:
        result['proposal_processing'] = 'No finite returned primal point marked valid; no count or PSD scan.'
    result['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    counts.save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--loop-preparation', type=Path, required=True)
    prep.add_argument('--loop-result', type=Path, required=True)
    prep.add_argument('--reduction-audit', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    solve = sub.add_parser('run')
    solve.add_argument('--preparation', type=Path, required=True)
    solve.add_argument('--output', type=Path, required=True)
    solve.add_argument('--prefix', type=Path, required=True)
    solve.add_argument('--seconds', type=float, default=120)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'prepare':
            prepare(args.loop_preparation, args.loop_result, args.reduction_audit, args.output)
        else:
            assert 0 < args.seconds <= 120
            run(args.preparation, args.output, args.prefix, args.seconds)
