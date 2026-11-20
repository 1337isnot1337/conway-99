"""Bounded LP row generation over the complete frozen case4 selector model.

Preparation and replay never call an optimizer. Production starts with every
native row and every max-min extension row, then adds only original cover rows.
Compression is used to select a smaller equivalent cover pool. Numerical row
selection is discovery; an accepted rational point is checked on the full
uncompressed matrix, and an accepted bound uses exact original-row indices.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import resource
from threading import Timer
import time

import numpy as np
import scipy
from scipy.sparse import csr_matrix

import rook_case4_cover_compression as compression
import rook_case4_maxmin_query as frozen

MAXMIN_SHA = 'f5c664a20983a9a5f8a6601fe67f1d00aed701b29751b77b543ee3aa3afdd322'
COMPRESSION_SHA = '293787214bb7ad4c20a60ef03d8d2c0eee8f1142d3b015f80d285cc6a9ad1164'
COMPRESSION_CERT_SHA = 'ecd80cb44cfc6464bab1e8c711229bef2a7da9d9334900f24d422d6a46841834'
COMPRESSION_RAW_SHA = 'f25952503b94cdad6ac8fe9e20ff0fbba380ceebf2dec87118ce34fdf280c6f7'
NATIVE, COVER_POOL = 1992, 125429
LIMITS = {
    'maximum_run_calls': 30,
    'cumulative_solver_and_existing_ray_seconds': 120,
    'numerical_phase_wall_seconds_including_bootstrap_and_scans': 180,
    'maximum_new_cover_rows_per_call': 512,
    'maximum_total_added_cover_rows': 29*512,
    'threads': 1,
    'violation_tolerance': 1e-7,
    'combined_exact_reconstruction_seconds': 60,
    'cold_exact_check_seconds': 60,
    'maximum_rational_common_denominator_bits': 4096,
    'preparation_compression_decode_seconds': 60,
}
OPTIONS = [['output_flag', True], ['log_to_console', False],
           ['threads', 1], ['parallel', 'off'], ['solver', 'simplex'],
           ['presolve', 'on'], ['random_seed', 0]]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return frozen.canonical(value)


def save(path, value):
    frozen.save(path, value)


def row_ids_hash(rows):
    return digest(np.asarray(rows, dtype='<i8').tobytes())


def source_bindings():
    assert digest(Path(frozen.__file__).read_bytes()) == MAXMIN_SHA
    assert digest(Path(compression.__file__).read_bytes()) == COMPRESSION_SHA
    previous = frozen.source_bindings()
    return {'driver_sha256': digest(Path(__file__).read_bytes()),
            'frozen_maxmin_sha256': MAXMIN_SHA,
            'frozen_exact_helper_sha256': previous['exact_helper_sha256'],
            'frozen_recovery_sha256': previous['recovery_builder_sha256'],
            'frozen_compression_sha256': COMPRESSION_SHA}


def runtime_binding():
    return dict(frozen.runtime_binding(), scipy_version=scipy.__version__)


def initial_row_ids():
    return list(range(NATIVE))+list(range(frozen.BASE_ROWS, frozen.ROWS))


def load_inputs(model_path, arrays_path, compression_path):
    source_bindings()
    model, base = frozen.load_base(model_path, arrays_path)
    raw_gz = compression_path.read_bytes()
    assert digest(raw_gz) == COMPRESSION_CERT_SHA
    raw = gzip.decompress(raw_gz)
    assert digest(raw) == COMPRESSION_RAW_SHA
    certificate = json.loads(raw)
    decoded = compression.decode(base, time.monotonic()+LIMITS['preparation_compression_decode_seconds'])
    report, retained = compression.verify_certificate(base, *decoded, certificate)
    pool = certificate['retained_cover_input_rows']
    assert retained == list(range(NATIVE))+pool
    assert len(pool) == COVER_POOL and pool == sorted(set(pool))
    assert len(retained) == 127421 and report['retained_nonzeros'] == 8483109
    assert all(NATIVE <= row < frozen.BASE_ROWS for row in pool)
    arrays = frozen.extend(base)
    return model, base, arrays, pool, report


def full_float_matrix(arrays):
    # Exact integer input hashes are checked before this conversion.
    for name in ('coefficients', 'row_lower', 'row_upper'):
        assert np.all(np.abs(arrays[name]) < 2**53)
    return csr_matrix((arrays['coefficients'].astype(float), arrays['column_indices'],
                       arrays['row_pointers']), shape=(frozen.ROWS, frozen.VARIABLES))


def choose_rows(violation, pool, active, batch, tolerance):
    """Discovery rule: largest violation first, original row ID breaks ties."""
    assert batch > 0 and tolerance >= 0
    candidates = [int(row) for row in pool
                  if row not in active and float(violation[row]) > tolerance]
    candidates.sort(key=lambda row: (-float(violation[row]), row))
    return candidates[:batch], len(candidates)


def inspect_numeric_point(matrix, arrays, values, pool, active):
    point = np.asarray(values, dtype=float)
    assert point.shape == (frozen.VARIABLES,) and np.all(np.isfinite(point))
    activity = matrix @ point
    assert activity.shape == (frozen.ROWS,) and np.all(np.isfinite(activity))
    violation = np.maximum(np.maximum(arrays['row_lower']-activity,
                                     activity-arrays['row_upper']), 0.0)
    selected, eligible_count = choose_rows(violation, pool, active,
        LIMITS['maximum_new_cover_rows_per_call'], LIMITS['violation_tolerance'])
    tol = LIMITS['violation_tolerance']
    pool_array = np.asarray(pool, dtype=np.int64)
    active_array = np.asarray(sorted(active), dtype=np.int64)
    return {'all_original_and_extension_rows_scanned': frozen.ROWS,
        'full_matrix_nonzeros_scanned': frozen.NONZEROS,
        'retained_cover_rows_scanned': len(pool),
        'active_rows_scanned': len(active),
        'full_row_violation_count': int(np.count_nonzero(violation > tol)),
        'maximum_full_row_violation': float(np.max(violation)),
        'maximum_active_row_violation': float(np.max(violation[active_array])),
        'maximum_retained_cover_violation': float(np.max(violation[pool_array])),
        'maximum_variable_bound_violation': float(max(0.0, -np.min(point), np.max(point)-1)),
        'violated_unseen_retained_covers': eligible_count,
        'selected_new_cover_rows': selected,
        'selection_rule': 'descending floating violation, then ascending original row ID',
        'exact_feasibility_claimed': False}


def set_model(solver, matrix, arrays, rows, variables):
    import highspy
    part = matrix[np.asarray(rows, dtype=np.int64)].tocsr()
    assert part.nnz < 2**31
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = variables, len(rows)
    lp.col_cost_ = np.zeros(variables)
    lp.col_cost_[-1] = -1.0
    lp.col_lower_, lp.col_upper_ = np.zeros(variables), np.ones(variables)
    lp.row_lower_ = np.asarray(arrays['row_lower'])[rows].astype(float)
    lp.row_upper_ = np.asarray(arrays['row_upper'])[rows].astype(float)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    lp.a_matrix_.start_ = part.indptr.astype(np.int32)
    lp.a_matrix_.index_ = part.indices.astype(np.int32)
    lp.a_matrix_.value_ = part.data
    assert solver.passModel(lp) == highspy.HighsStatus.kOk


def append_rows(solver, matrix, arrays, rows):
    import highspy
    assert rows and len(rows) == len(set(rows))
    part = matrix[np.asarray(rows, dtype=np.int64)].tocsr()
    assert part.nnz < 2**31
    before = solver.getNumRow()
    status = solver.addRows(len(rows), np.asarray(arrays['row_lower'])[rows].astype(float),
        np.asarray(arrays['row_upper'])[rows].astype(float), part.nnz,
        part.indptr.astype(np.int32), part.indices.astype(np.int32), part.data)
    assert status == highspy.HighsStatus.kOk and solver.getNumRow() == before+len(rows)


def controls():
    # These controls inspect an assembled native model, but never call run().
    import highspy
    toy = frozen.exact.toy_arrays([[1, 1, 0], [1, 0, -1], [0, 1, -1],
                                  [-1, 1, 0]], [1, 0, 0, 0], [1, 1, 1, 1])
    C = csr_matrix((np.asarray(toy['coefficients'], dtype=float), toy['column_indices'],
                    toy['row_pointers']), shape=(4, 3))
    h = highspy.Highs()
    assert h.setOptionValue('output_flag', False) == highspy.HighsStatus.kOk
    order = [0, 2]
    set_model(h, C, toy, order, 3)
    append_rows(h, C, toy, [3, 1])
    order += [3, 1]
    for local, original in enumerate(order):
        status, lower, upper, count = h.getRow(local)
        assert status == highspy.HighsStatus.kOk
        status, columns, coefficients = h.getRowEntries(local)
        assert status == highspy.HighsStatus.kOk
        expected = C.getrow(original)
        assert list(columns) == list(expected.indices)
        assert list(coefficients) == list(expected.data) and count == expected.nnz
        assert lower == toy['row_lower'][original] and upper == toy['row_upper'][original]
    assert h.getRunTime() == 0 and not h.getSolution().value_valid
    chosen, count = choose_rows([0.1, 0.5, 0.5, 0.2], [0, 1, 2, 3], {0}, 2, 0.05)
    assert chosen == [1, 2] and count == 3
    assert choose_rows([0, 0, 0, 0], [0, 1, 2, 3], set(), 2, 0)[0] == []
    assert choose_rows([0.1, 0.5, 0.5, 0.2], [0, 1, 2, 3], {0, 1, 2}, 2, 0.05)[0] == [3]
    local = [5, -2, 3, -7]
    expanded = [0]*4
    for row, value in zip(order, local):
        expanded[row] = value
    assert np.array_equal(C.T @ np.asarray(expanded), C[order].T @ np.asarray(local))
    return {'native_rows_checked_without_optimization': 4,
        'nonmonotone_original_row_ID_insertion_checked': True,
        'tie_break_batch_and_seen_row_controls': 3,
        'local_to_global_multiplier_control': True,
        'finite_box_controls': frozen.controls_without_timings(),
        'optimizer_calls': 0}


def definition(arrays, pool, compression_report):
    math, full_hash = frozen.mathematical_model(arrays)
    initial = initial_row_ids()
    initial_nnz = sum(int(arrays['row_pointers'][r+1]-arrays['row_pointers'][r]) for r in initial)
    model = {'complete_original_maxmin_model': math,
        'complete_original_maxmin_model_sha256': full_hash,
        'compression_certificate_sha256': COMPRESSION_CERT_SHA,
        'compression_certificate_decompressed_sha256': COMPRESSION_RAW_SHA,
        'compression_replay': compression_report,
        'retained_cover_pool_count': len(pool), 'retained_cover_pool_original_ID_sha256': row_ids_hash(pool),
        'initial_rows': len(initial), 'initial_rows_original_ID_sha256': row_ids_hash(initial),
        'initial_row_ranges': [[0, NATIVE], [frozen.BASE_ROWS, frozen.ROWS]],
        'initial_nonzeros': initial_nnz,
        'maximum_active_rows': len(initial)+LIMITS['maximum_total_added_cover_rows'],
        'all_original_rows_required_for_rational_primal_acceptance': frozen.ROWS,
        'only_original_rows_may_be_added': True,
        'numerical_row_selection': 'at most512 unseen covers, greatest violation first, ties by original row ID',
        'subset_ray_scope': 'a checked finite-box certificate using an active subset is valid for the complete LP',
        'basis_policy': 'one persistent native solver; appendRows without reset or reload',
        'no_new_selector_assumptions_or_symmetry': True,
        'limits': LIMITS, 'native_options': OPTIONS}
    return model, digest(canonical(model))


def prepare(model_path, arrays_path, compression_path, output):
    assert not output.exists()
    started = time.monotonic()
    model, base, arrays, pool, report = load_inputs(model_path, arrays_path, compression_path)
    spec, spec_hash = definition(arrays, pool, report)
    record = {'status': 'bounded complete-pool row generation prepared; no optimizer called',
        'source_bindings': source_bindings(), 'runtime_binding': runtime_binding(),
        'definition': spec, 'definition_sha256': spec_hash,
        'controls': controls(), 'fixed_zero_original_columns': model['fixed_zero_columns'],
        'production_optimizer_calls': 0, 'case4_excluded': False,
        'seconds': time.monotonic()-started,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output, record)
    print(json.dumps({k:v for k,v in record.items() if k != 'definition'}, indent=2), flush=True)


def checked_preparation(preparation, model_path, arrays_path, compression_path, require_runtime):
    record = json.loads(preparation.read_text())
    assert record['source_bindings'] == source_bindings()
    model, base, arrays, pool, report = load_inputs(model_path, arrays_path, compression_path)
    spec, spec_hash = definition(arrays, pool, report)
    assert record['definition'] == spec and record['definition_sha256'] == spec_hash
    assert record['fixed_zero_original_columns'] == model['fixed_zero_columns']
    if require_runtime:
        assert record['runtime_binding'] == runtime_binding()
    return record, model, base, arrays, pool


def cold_arrays(model, base, arrays, root):
    rebuilt_model, rebuilt_base = frozen.recovery.build(root)
    for key, value in rebuilt_model.items():
        if key not in ('python_version', 'numpy_version'):
            assert model[key] == value, ('cold base field', key)
    assert set(base) == set(rebuilt_base)
    for key in base:
        assert np.array_equal(base[key], rebuilt_base[key]), ('cold base array', key)
    rebuilt = frozen.extend(rebuilt_base)
    assert frozen.matrix_binding(rebuilt) == frozen.matrix_binding(arrays)
    return rebuilt


def preflight_replay(preparation, model_path, arrays_path, compression_path, root, output):
    assert not output.exists()
    started = time.monotonic()
    prepared, model, base, arrays, pool = checked_preparation(
        preparation, model_path, arrays_path, compression_path, False)
    cold_arrays(model, base, arrays, root)
    control = controls()
    assert control == prepared['controls']
    record = {'status': 'PASS: full published-input reconstruction, compression accounting and native assembly controls',
        'source_bindings': source_bindings(), 'preparation_sha256': digest(preparation.read_bytes()),
        'definition_sha256': prepared['definition_sha256'],
        'original_rows': frozen.BASE_ROWS, 'extended_rows': frozen.ROWS,
        'retained_cover_pool_count': len(pool), 'all_input_arrays_rebuilt': True,
        'optimizer_calls': 0, 'case4_excluded': False,
        'seconds': time.monotonic()-started,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output, record)
    print(json.dumps(record, indent=2), flush=True)


def native_once(solver, rows, seconds, index):
    import highspy
    assert 0 < seconds <= LIMITS['cumulative_solver_and_existing_ray_seconds']
    # Native time accounting can accumulate across run() calls. The independent
    # timer uses the remaining measured wall budget, regardless of that detail.
    internal_limit = max(0.0, float(solver.getRunTime()))+seconds
    assert solver.setOptionValue('time_limit', internal_limit) == highspy.HighsStatus.kOk
    solver.HandleUserInterrupt = True
    started = time.monotonic()
    timer = Timer(seconds, solver.cancelSolve)
    timer.daemon = True
    timer.start()
    ray, ray_status = None, None
    try:
        call_status = solver.run()  # The only production optimizer entrypoint.
        status = solver.getModelStatus()
        if status == highspy.HighsModelStatus.kInfeasible and time.monotonic()-started < seconds:
            call, exists = solver.getDualRayExist()
            assert call == highspy.HighsStatus.kOk
            ray_status = 'existing ray available' if exists else 'absent; no ray-generating extra solve'
            if exists:
                call, exists, candidate = solver.getDualRay()
                assert call == highspy.HighsStatus.kOk and exists
                if len(candidate) == len(rows) and np.all(np.isfinite(candidate)):
                    ray = list(map(float, candidate))
    finally:
        timer.cancel()
        timer.join()
    elapsed = time.monotonic()-started
    solution, basis, info = solver.getSolution(), solver.getBasis(), solver.getInfo()
    return {'call_index': index, 'active_original_row_ids': rows[:],
        'active_original_row_ids_sha256': row_ids_hash(rows),
        'requested_solver_and_existing_ray_seconds': seconds,
        'native_absolute_time_limit': internal_limit,
        'solver_and_existing_ray_seconds': elapsed,
        'model_status': str(status), 'run_status': str(call_status),
        'optimal': call_status != highspy.HighsStatus.kError and status == highspy.HighsModelStatus.kOptimal,
        'numerically_infeasible': call_status != highspy.HighsStatus.kError and status == highspy.HighsModelStatus.kInfeasible,
        'solution_value_valid': bool(solution.value_valid),
        'solution_dual_valid': bool(solution.dual_valid),
        'column_values': [frozen.clean_number(v) for v in solution.col_value],
        'row_duals': [frozen.clean_number(v) for v in solution.row_dual],
        'column_duals': [frozen.clean_number(v) for v in solution.col_dual],
        'basis_valid': bool(basis.valid),
        'column_basis_status': [str(v) for v in basis.col_status],
        'nonbasic_original_row_status': [[rows[i],str(v)] for i,v in enumerate(basis.row_status)
                                        if v != highspy.HighsBasisStatus.kBasic],
        'simplex_iterations_reported': int(info.simplex_iteration_count),
        'objective': frozen.clean_number(info.objective_function_value),
        'dual_ray_request_status': ray_status, 'dual_ray': ray,
        'extra_ray_generating_solve_allowed': False}


def expanded_numeric(record):
    rows = record['active_original_row_ids']
    assert len(rows) == len(set(rows)) and all(0 <= row < frozen.ROWS for row in rows)
    numeric = {key:record[key] for key in ('optimal', 'numerically_infeasible',
        'solution_value_valid', 'solution_dual_valid', 'column_values')}
    for name in ('row_duals', 'dual_ray'):
        values = record[name]
        if values is None or len(values) != len(rows) or any(v is None for v in values):
            numeric[name] = None
        else:
            expanded = [0.0]*frozen.ROWS
            for row, value in zip(rows, values):
                expanded[row] = value
            numeric[name] = expanded
    return numeric


def run(preparation, model_path, arrays_path, compression_path, directory):
    import highspy
    assert not directory.exists()
    directory.mkdir(parents=True)
    result_path = directory/'result.json'
    started = time.monotonic()
    result = {'status': 'initializing bounded original-row generation',
        'source_bindings': source_bindings(), 'preparation_sha256': digest(preparation.read_bytes()),
        'limits': LIMITS, 'iterations': [], 'automatic_retry': False,
        'production_run_calls': 0, 'solver_and_existing_ray_seconds': 0.0,
        'added_cover_rows': 0,
        'exact_infeasibility_certificate_found': False,
        'exact_zero_face_certificate_found': False, 'exact_rational_point_found': False,
        'case4_exclusion_verified': False, 'whole_graph_problem_resolved': False}
    save(result_path, result)
    try:
        prepared, model, base, arrays, pool = checked_preparation(
            preparation, model_path, arrays_path, compression_path, True)
        result['definition_sha256'] = prepared['definition_sha256']
        result['input_replay_seconds'] = time.monotonic()-started
        phase_start = time.monotonic()
        phase_deadline = phase_start+LIMITS['numerical_phase_wall_seconds_including_bootstrap_and_scans']
        matrix = full_float_matrix(arrays)
        h = highspy.Highs()
        for name, value in OPTIONS+[('log_file', str(directory/'highs.log'))]:
            assert h.setOptionValue(name, value) == highspy.HighsStatus.kOk
        rows, active = initial_row_ids(), set(initial_row_ids())
        set_model(h, matrix, arrays, rows, frozen.VARIABLES)
        result['native_bootstrap_seconds'] = time.monotonic()-phase_start
        solve_time, added_count, last_numeric = 0.0, 0, None
        for iteration in range(LIMITS['maximum_run_calls']):
            before_call = time.monotonic()
            remaining = min(LIMITS['cumulative_solver_and_existing_ray_seconds']-solve_time,
                            phase_deadline-before_call)
            if remaining <= 0:
                result['numerical_stop_reason'] = 'solver or phase budget exhausted before next call'
                break
            numeric = native_once(h, rows, remaining, iteration)
            numeric['numerical_phase_elapsed_before_call'] = before_call-phase_start
            solve_time += numeric['solver_and_existing_ray_seconds']
            last_numeric = numeric
            item = {'call_index': iteration, 'active_rows': len(rows),
                'numeric_artifact': frozen.save_gzip(directory/f'iteration-{iteration:02d}-numeric.json.gz', numeric),
                'added_after_call': [], 'scan': None}
            result['iterations'].append(item)
            result['solver_and_existing_ray_seconds'] = solve_time
            result['production_run_calls'] = len(result['iterations'])
            result['status'] = 'numerical call saved; complete-pool inspection pending'
            save(result_path, result)
            if not numeric['optimal'] or not numeric['solution_value_valid']:
                result['numerical_stop_reason'] = ('native infeasibility; exact certificate required'
                    if numeric['numerically_infeasible'] else 'nonoptimal/invalid result; no retry')
                break
            if (len(numeric['column_values']) != frozen.VARIABLES or
                    any(v is None for v in numeric['column_values'])):
                result['numerical_stop_reason'] = 'nonfinite or incomplete primal proposal'
                break
            scan_started = time.monotonic()
            scan = inspect_numeric_point(matrix, arrays, numeric['column_values'], pool, active)
            item['scan'] = scan
            item['scan_seconds'] = time.monotonic()-scan_started
            candidates = scan['selected_new_cover_rows']
            if not candidates:
                result['numerical_stop_reason'] = 'no unseen retained cover violated; full exact acceptance still required'
                break
            if (iteration+1 >= LIMITS['maximum_run_calls'] or
                    solve_time >= LIMITS['cumulative_solver_and_existing_ray_seconds'] or
                    time.monotonic() >= phase_deadline):
                result['numerical_stop_reason'] = 'budget exhausted with violated covers still present'
                break
            assert not active.intersection(candidates)
            assert len(candidates) <= LIMITS['maximum_new_cover_rows_per_call']
            assert added_count+len(candidates) <= LIMITS['maximum_total_added_cover_rows']
            append_rows(h, matrix, arrays, candidates)
            rows.extend(candidates)
            active.update(candidates)
            added_count += len(candidates)
            item['added_after_call'] = candidates
            result['added_cover_rows'] = added_count
            result['status'] = 'frozen original covers appended; next call uses the existing solver and basis'
            save(result_path, result)
            print(json.dumps({'call':iteration, 'status':numeric['model_status'],
                'active_rows':item['active_rows'], 'new_rows':len(candidates),
                'unseen_violations':scan['violated_unseen_retained_covers'],
                'solver_seconds':solve_time}), flush=True)
        result['numerical_phase_seconds'] = time.monotonic()-phase_start
        result['added_cover_rows'] = added_count
        result['status'] = 'bounded numerical phase terminal; separate exact stage pending'
        save(result_path, result)
        exact_start = time.monotonic()
        deadline = exact_start+LIMITS['combined_exact_reconstruction_seconds']
        try:
            certificate = None
            if last_numeric is not None:
                numeric = expanded_numeric(last_numeric)
                certificate, attempts = frozen.reconstruct_bound(arrays, numeric, deadline)
                result['bound_reconstruction_attempts'] = attempts
                if certificate is not None:
                    certificate['definition_sha256'] = prepared['definition_sha256']
                    certificate['source_call_index'] = last_numeric['call_index']
                    assert {r for r,v in certificate['sparse_integer_row_multipliers']} <= set(last_numeric['active_original_row_ids'])
                    result['exact_certificate'] = frozen.save_gzip(directory/'exact-bound-certificate.json.gz', certificate)
                    key = ('exact_infeasibility_certificate_found' if certificate['kind'] == 'finite_box_infeasibility'
                           else 'exact_zero_face_certificate_found')
                    result[key] = True
                    result['status'] = 'exact original-row bound found; independent cold replay required'
                if certificate is None and time.monotonic() < deadline:
                    point, attempts = frozen.reconstruct_primal(arrays, numeric, deadline)
                    result['primal_reconstruction_attempts'] = attempts
                    if point is not None:
                        point['definition_sha256'] = prepared['definition_sha256']
                        point['source_call_index'] = last_numeric['call_index']
                        result['rational_point'] = frozen.save_gzip(directory/'exact-rational-point.json.gz', point)
                        result['exact_rational_point_found'] = True
                        result['status'] = 'all original rows passed exactly; independent cold replay required'
            if not any(result[k] for k in ('exact_infeasibility_certificate_found',
                    'exact_zero_face_certificate_found', 'exact_rational_point_found')):
                result['status'] = 'UNRESOLVED: retained numerical proposals give no accepted exact outcome'
        except TimeoutError as error:
            result['exact_stage_limit'] = str(error)
            result['status'] = 'UNRESOLVED: exact-stage limit; numerical records retained'
        result['exact_stage_seconds'] = time.monotonic()-exact_start
    except Exception as error:
        result['status'] = 'ERROR: no unchecked outcome promoted'
        result['error_type'], result['error_message'] = type(error).__name__, str(error)
        raise
    finally:
        result['elapsed_seconds'] = time.monotonic()-started
        result['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(result_path, result)
    print(json.dumps({k:v for k,v in result.items() if k != 'iterations' and 'attempts' not in k}, indent=2), flush=True)


def replay(preparation, model_path, arrays_path, compression_path, root, result_path, output):
    assert not output.exists()
    started = time.monotonic()
    prepared, model, base, arrays, pool = checked_preparation(
        preparation, model_path, arrays_path, compression_path, False)
    arrays = cold_arrays(model, base, arrays, root)
    result = json.loads(result_path.read_text())
    assert result['source_bindings'] == source_bindings() and result['limits'] == LIMITS
    assert result['preparation_sha256'] == digest(preparation.read_bytes())
    assert result['definition_sha256'] == prepared['definition_sha256']
    assert 0 <= len(result['iterations']) <= LIMITS['maximum_run_calls']
    matrix = full_float_matrix(arrays)
    rows, active, spent = initial_row_ids(), set(initial_row_ids()), 0.0
    records, added_count = [], 0
    for i, item in enumerate(result['iterations']):
        assert item['call_index'] == i
        numeric = frozen.read_gzip(result_path.parent, item['numeric_artifact'])
        assert numeric['call_index'] == i and numeric['active_original_row_ids'] == rows
        assert numeric['active_original_row_ids_sha256'] == row_ids_hash(rows)
        assert numeric['extra_ray_generating_solve_allowed'] is False
        requested = numeric['requested_solver_and_existing_ray_seconds']
        assert 0 < requested <= LIMITS['cumulative_solver_and_existing_ray_seconds']-spent+1e-9
        assert requested <= LIMITS['numerical_phase_wall_seconds_including_bootstrap_and_scans']-numeric['numerical_phase_elapsed_before_call']+1e-9
        spent += numeric['solver_and_existing_ray_seconds']
        assert numeric['solver_and_existing_ray_seconds'] >= 0
        if item['scan'] is not None:
            assert numeric['optimal'] and numeric['solution_value_valid']
            scan = inspect_numeric_point(matrix, arrays, numeric['column_values'], pool, active)
            assert scan == item['scan']
        additions = item['added_after_call']
        if additions:
            assert i+1 < LIMITS['maximum_run_calls']
            assert item['scan'] is not None and additions == item['scan']['selected_new_cover_rows']
            assert not active.intersection(additions) and set(additions) <= set(pool)
            assert len(additions) <= LIMITS['maximum_new_cover_rows_per_call']
            rows.extend(additions)
            active.update(additions)
            added_count += len(additions)
            assert added_count <= LIMITS['maximum_total_added_cover_rows']
        if i+1 < len(result['iterations']):
            assert additions and numeric['optimal']
        records.append(numeric)
    assert result['production_run_calls'] == len(records)
    assert result['added_cover_rows'] == added_count
    assert abs(result['solver_and_existing_ray_seconds']-spent) < 1e-9
    report = {'status': 'PASS: complete original matrix, exact compression and bounded prefix transcript',
        'source_bindings': source_bindings(), 'preparation_sha256': digest(preparation.read_bytes()),
        'result_sha256': digest(result_path.read_bytes()), 'definition_sha256': prepared['definition_sha256'],
        'original_rows_rebuilt': frozen.BASE_ROWS, 'extended_rows_rebuilt': frozen.ROWS,
        'retained_cover_pool_checked': len(pool), 'native_calls_recorded': len(records),
        'added_original_cover_rows': added_count, 'solver_seconds_recorded': spent,
        'optimizer_called_by_replay': False, 'exact_case4_exclusion_verified': False,
        'exact_zero_face_verified': False, 'exact_rational_point_verified': False,
        'whole_graph_problem_resolved': False}
    if result['exact_infeasibility_certificate_found'] or result['exact_zero_face_certificate_found']:
        cert = frozen.read_gzip(result_path.parent, result['exact_certificate'])
        assert cert['definition_sha256'] == prepared['definition_sha256']
        source = records[cert['source_call_index']]
        multipliers = [[int(r),int(v)] for r,v in cert['sparse_integer_row_multipliers']]
        assert {r for r,v in multipliers} <= set(source['active_original_row_ids'])
        gamma = int(cert['gamma'])
        check = frozen.exact.check_bound(arrays, frozen.VARIABLES, multipliers, gamma,
                                       LIMITS['cold_exact_check_seconds'])
        assert frozen.stable_check(check) == cert['exact_check']
        if cert['kind'] == 'finite_box_infeasibility':
            assert int(check['objective_upper_bound_numerator']) < 0
            assert result['exact_infeasibility_certificate_found'] and not result['exact_zero_face_certificate_found']
            report['exact_case4_exclusion_verified'] = True
        else:
            assert cert['kind'] == 'zero_maxmin_face' and gamma > 0
            assert int(check['objective_upper_bound_numerator']) == 0
            implication = frozen.normalized(frozen.exact.face_implications(
                check, multipliers, frozen.BASE_ROWS, arrays['original_column_ids']))
            assert implication == cert['face_implications']
            report['exact_zero_face_verified'] = True
            report['zero_original_columns'] = implication['zero_columns']
            report['one_original_columns'] = implication['one_columns']
    if result['exact_rational_point_found']:
        point = frozen.read_gzip(result_path.parent, result['rational_point'])
        assert point['definition_sha256'] == prepared['definition_sha256']
        assert 0 <= point['source_call_index'] < len(records)
        nums, den = list(map(int, point['extended_numerators'])), int(point['common_denominator'])
        check = frozen.exact.check_point(arrays, frozen.VARIABLES, nums, den,
                                       LIMITS['cold_exact_check_seconds'])
        assert frozen.stable_check(check) == point['exact_check']
        restored = [0]*1214
        for j,a in enumerate(arrays['original_column_ids']):
            restored[int(a)] = nums[j]
        assert point['original1214_selector_numerators'] == list(map(str, restored))
        report['exact_rational_point_verified'] = True
        report['strictly_positive_t'] = check['strictly_positive_t']
    report['seconds'] = time.monotonic()-started
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode', required=True)
    for mode in ('prepare', 'preflight', 'run', 'replay'):
        c = commands.add_parser(mode)
        c.add_argument('--model', type=Path, required=True)
        c.add_argument('--arrays', type=Path, required=True)
        c.add_argument('--compression', type=Path, required=True)
        if mode != 'prepare':
            c.add_argument('--preparation', type=Path, required=True)
        if mode == 'run':
            c.add_argument('--directory', type=Path, required=True)
        else:
            c.add_argument('--output', type=Path, required=True)
        if mode in ('preflight', 'replay'):
            c.add_argument('--root', type=Path, default=frozen.recovery.ROOT)
        if mode == 'replay':
            c.add_argument('--result', type=Path, required=True)
    a = parser.parse_args()
    if a.mode == 'prepare':
        prepare(a.model, a.arrays, a.compression, a.output)
    elif a.mode == 'preflight':
        preflight_replay(a.preparation, a.model, a.arrays, a.compression, a.root, a.output)
    elif a.mode == 'run':
        run(a.preparation, a.model, a.arrays, a.compression, a.directory)
    else:
        replay(a.preparation, a.model, a.arrays, a.compression, a.root, a.result, a.output)


if __name__ == '__main__':
    main()
