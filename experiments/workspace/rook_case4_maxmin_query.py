"""One bounded complete case4 max-min LP query and exact outcome replay.

Preparation exposes no optimizer call. The base matrix is recovered from
published inputs. The only added rows are 0 <= x_j-t <= 1, with 0 <= t <= 1.
No numerical support, fixed incidence, hint, or symmetry restriction is added.
"""

import argparse
from fractions import Fraction
import gzip
import hashlib
import importlib.metadata
import json
from pathlib import Path
import resource
import sys
from threading import Timer
import time

import numpy as np

import rook_case4_complete_lp_recovery as recovery
import rook_case4_finite_box_certificates as exact

BUILDER_SHA = 'e577327c9cc2471f119c755a49a179b9f94f1004a22de80152a4114787a7eec6'
EXACT_SHA = '353db5bb5d2c6b3d11b18889a853af364ea3d6c4d04bb78c56f0c4ee89d86de7'
BASE_MODEL_SHA = '9373396621ff2a713200c9832d9da82801b51f1c674233eaa81a1587a9f29b42'
BASE_NPZ_SHA = 'fb9ba6b1185f7796e39ac2904f077ad58238e89b0445305a22238c0374dd158f'
BASE_STREAM_SHA = '444835c4d3c466dc9bb5c71646da13bf98e6eefdb3a492c51bcf54185b8919d5'
BASE_ROWS, SELECTORS = 174208, 1156
VARIABLES, ROWS, NONZEROS = 1157, 175364, 11871194
LIMITS = {'production_run_calls': 1, 'threads': 1, 'solver_and_ray_seconds': 60,
          'combined_exact_reconstruction_seconds': 60, 'cold_exact_check_seconds': 60,
          'maximum_rational_common_denominator_bits': 4096}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def normalized(value):
    return json.loads(json.dumps(value))


def canonical(value):
    return json.dumps(normalized(value), sort_keys=True, separators=(',', ':')).encode()


def save(path, value):
    temporary = path.with_name(path.name+'.partial')
    temporary.write_text(json.dumps(normalized(value), indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def save_gzip(path, value):
    raw = canonical(value)+b'\n'
    temporary = path.with_name(path.name+'.partial')
    temporary.write_bytes(gzip.compress(raw, mtime=0))
    temporary.replace(path)
    return {'path': path.name, 'sha256': digest(path.read_bytes()),
            'decompressed_sha256': digest(raw), 'decompressed_bytes': len(raw)}


def read_gzip(directory, item):
    path = directory/item['path']
    assert digest(path.read_bytes()) == item['sha256']
    raw = gzip.decompress(path.read_bytes())
    assert digest(raw) == item['decompressed_sha256'] and len(raw) == item['decompressed_bytes']
    return json.loads(raw)


def source_bindings():
    assert digest(Path(recovery.__file__).read_bytes()) == BUILDER_SHA
    assert digest(Path(exact.__file__).read_bytes()) == EXACT_SHA
    return {'driver_sha256': digest(Path(__file__).read_bytes()),
            'recovery_builder_sha256': BUILDER_SHA, 'exact_helper_sha256': EXACT_SHA}


def runtime_binding():
    import highspy
    from highspy import _core
    h = highspy.Highs()
    assert hasattr(h, 'cancelSolve') and hasattr(h, 'getDualRayExist')
    ray_status, ray_exists = h.getDualRayExist()
    assert ray_status == highspy.HighsStatus.kOk and not ray_exists
    assert hasattr(h.getSolution(), 'dual_valid') and hasattr(h.getBasis(), 'valid')
    return {'empty_existing_ray_check': True, 'python_version': sys.version, 'numpy_version': np.__version__,
            'highspy_package_version': importlib.metadata.version('highspy'),
            'native_HiGHS_version': h.version(),
            'highspy_init_sha256': digest(Path(highspy.__file__).read_bytes()),
            'highspy_native_binary_name': Path(_core.__file__).name,
            'highspy_native_binary_sha256': digest(Path(_core.__file__).read_bytes())}


def load_base(model_path, arrays_path):
    source_bindings()
    assert digest(model_path.read_bytes()) == BASE_MODEL_SHA
    model = json.loads(model_path.read_text())
    assert model['source_sha256'] == BUILDER_SHA
    assert model['canonical_integer_stream_sha256'] == BASE_STREAM_SHA
    assert (model['columns'], model['rows'], model['nonzeros']) == (1156, 174208, 11868882)
    assert len(model['fixed_zero_columns']) == 58 and model['all2271_native_rows_and178533_covers_covered']
    assert model['array_sha256'] and model['row_inventory'] == recovery.EXPECTED_COUNTS
    if arrays_path is None:
        arrays_path = model_path.parent/model['arrays']['path']
    assert digest(arrays_path.read_bytes()) == model['arrays']['sha256'] == BASE_NPZ_SHA
    with np.load(arrays_path, allow_pickle=False) as archive:
        arrays = {name: archive[name] for name in archive.files}
    assert {name: digest(value.tobytes(order='C')) for name, value in arrays.items()} == model['array_sha256']
    assert all(value.dtype.kind in 'iu' for value in arrays.values())
    assert len(arrays['original_column_ids']) == SELECTORS
    assert len(arrays['coefficients']) == len(arrays['column_indices']) == 11868882
    assert len(arrays['row_pointers']) == BASE_ROWS+1
    assert len(arrays['row_lower']) == len(arrays['row_upper']) == BASE_ROWS
    return model, arrays


def extend(base):
    n, m = SELECTORS, BASE_ROWS
    added_indices = np.empty(2*n, dtype='<i4')
    added_indices[0::2] = np.arange(n, dtype='<i4')
    added_indices[1::2] = n
    arrays = {
        'coefficients': np.concatenate((base['coefficients'], np.tile(np.asarray([1,-1], dtype='<i8'), n))),
        'column_indices': np.concatenate((base['column_indices'], added_indices)),
        'row_pointers': np.concatenate((base['row_pointers'], int(base['row_pointers'][-1])+2*np.arange(1,n+1,dtype='<i8'))),
        'row_lower': np.concatenate((base['row_lower'], np.zeros(n, dtype='<i8'))),
        'row_upper': np.concatenate((base['row_upper'], np.ones(n, dtype='<i8'))),
        'original_column_ids': base['original_column_ids']}
    assert len(arrays['coefficients']) == len(arrays['column_indices']) == NONZEROS
    assert len(arrays['row_pointers']) == ROWS+1 and arrays['row_pointers'][-1] == NONZEROS
    assert len(arrays['row_lower']) == len(arrays['row_upper']) == ROWS
    assert all(value.dtype.kind in 'iu' for value in arrays.values())
    for j in range(n):
        at = int(arrays['row_pointers'][m+j])
        assert list(map(int, arrays['column_indices'][at:at+2])) == [j, n]
        assert list(map(int, arrays['coefficients'][at:at+2])) == [1, -1]
        assert int(arrays['row_lower'][m+j]) == 0 and int(arrays['row_upper'][m+j]) == 1
    return arrays


def matrix_binding(arrays):
    return {name: {'dtype': value.dtype.str, 'shape': list(value.shape),
                   'sha256': digest(value.tobytes(order='C'))} for name, value in arrays.items()}


def mathematical_model(arrays):
    record = {'base_model_sha256': BASE_MODEL_SHA, 'base_array_npz_sha256': BASE_NPZ_SHA,
        'base_integer_stream_sha256': BASE_STREAM_SHA,
        'selectors': SELECTORS, 'variables_including_t': VARIABLES,
        'rows': ROWS, 'nonzeros': NONZEROS, 't_column': SELECTORS,
        'original_rows': BASE_ROWS, 'added_extension_rows': SELECTORS,
        'extension_rule': 'row174208+j has +1 at selector j,-1 at t, and bounds[0,1]',
        'variable_lower': 0, 'variable_upper': 1,
        'objective': 'minimize -t (equivalently maximize t)',
        'minimization_cost_at_t': -1, 'other_costs': 0,
        'matrix_array_bindings': matrix_binding(arrays),
        'original_support_restriction_added': False,
        'new_fixed_selector_assumptions_added': False,
        'graph_symmetry_restriction_added': False}
    return record, digest(canonical(record))


def controls_without_timings():
    return normalized(exact.controls())


def prepare(model_path, arrays_path, output):
    assert not output.exists()
    started = time.monotonic()
    model, base = load_base(model_path, arrays_path)
    arrays = extend(base)
    math, signature = mathematical_model(arrays)
    record = {'status': 'complete max-min driver prepared; no optimizer called',
        'source_bindings': source_bindings(), 'runtime_binding': runtime_binding(),
        'mathematical_model': math, 'mathematical_model_sha256': signature,
        'limits': LIMITS, 'exact_arithmetic_controls': controls_without_timings(),
        'base_fixed_zero_columns': model['fixed_zero_columns'],
        'numerical_discovery_only_until_exact_check': True,
        'production_optimizer_calls': 0, 'case4_excluded': False,
        'initialization_seconds': time.monotonic()-started,
        'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output, record)
    print(json.dumps({key: value for key, value in record.items() if key != 'mathematical_model'}, indent=2), flush=True)


def checked_preparation(preparation, model_path, arrays_path, require_runtime):
    saved = json.loads(preparation.read_text())
    assert saved['source_bindings'] == source_bindings() and saved['limits'] == LIMITS
    model, base = load_base(model_path, arrays_path)
    arrays = extend(base)
    math, signature = mathematical_model(arrays)
    assert saved['mathematical_model'] == math and saved['mathematical_model_sha256'] == signature
    assert saved['base_fixed_zero_columns'] == model['fixed_zero_columns']
    if require_runtime:
        assert saved['runtime_binding'] == runtime_binding()
    return saved, model, arrays


def clean_number(value):
    number = float(value)
    return number if np.isfinite(number) else None


def native_query(arrays, log_path):
    bootstrap_started = time.monotonic()
    import highspy
    solver = highspy.Highs()
    options = [('output_flag', True), ('log_to_console', False), ('log_file', str(log_path)),
               ('threads', 1), ('parallel', 'off'), ('solver', 'simplex'),
               ('presolve', 'on'), ('random_seed', 0), ('time_limit', 60.0)]
    for name, value in options:
        assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
    assert max(abs(int(np.min(arrays['coefficients']))), abs(int(np.max(arrays['coefficients'])))) < 2**53
    assert np.all(np.abs(arrays['row_lower']) < 2**53) and np.all(np.abs(arrays['row_upper']) < 2**53)
    # All complete integer bindings passed before any floating conversion.
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = VARIABLES, ROWS
    lp.col_cost_ = np.zeros(VARIABLES)
    lp.col_cost_[-1] = -1.0
    lp.col_lower_, lp.col_upper_ = np.zeros(VARIABLES), np.ones(VARIABLES)
    lp.row_lower_, lp.row_upper_ = arrays['row_lower'].astype(float), arrays['row_upper'].astype(float)
    lp.a_matrix_.format_ = highspy.MatrixFormat.kRowwise
    assert int(arrays['row_pointers'][-1]) < 2**31
    lp.a_matrix_.start_ = arrays['row_pointers'].astype(np.int32)
    lp.a_matrix_.index_ = arrays['column_indices']
    lp.a_matrix_.value_ = arrays['coefficients'].astype(float)
    assert solver.passModel(lp) == highspy.HighsStatus.kOk
    solver.HandleUserInterrupt = True
    bootstrap_seconds = time.monotonic()-bootstrap_started
    bootstrap_peak_rss_kib = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    started = time.monotonic()
    timer = Timer(60.0, solver.cancelSolve)
    timer.daemon = True
    timer.start()
    ray = None
    ray_status = None
    try:
        run_status = solver.run()
        status = solver.getModelStatus()
        if status == highspy.HighsModelStatus.kInfeasible:
            remaining = 60.0-(time.monotonic()-started)
            if remaining > 0:
                exists_status, exists = solver.getDualRayExist()
                assert exists_status == highspy.HighsStatus.kOk
                ray_status = 'existing ray available' if exists else 'no existing ray; ray-generating solve skipped'
                if exists:
                    call, still_exists, candidate = solver.getDualRay()
                    assert call == highspy.HighsStatus.kOk and still_exists
                    if len(candidate) == ROWS and all(np.isfinite(float(v)) for v in candidate):
                        ray = list(map(float, candidate))
    finally:
        timer.cancel()
        timer.join()
    solution, basis, info = solver.getSolution(), solver.getBasis(), solver.getInfo()
    return {
        'model_status': str(status), 'run_status': str(run_status),
        'optimal': status == highspy.HighsModelStatus.kOptimal,
        'numerically_infeasible': status == highspy.HighsModelStatus.kInfeasible,
        'native_bootstrap_seconds': bootstrap_seconds,
        'native_bootstrap_peak_rss_kib': bootstrap_peak_rss_kib,
        'solver_and_ray_seconds': time.monotonic()-started,
        'requested_solver_seconds': 60, 'production_run_calls': 1,
        'ray_generating_additional_solve_allowed': False,
        'solution_value_valid': bool(solution.value_valid),
        'solution_dual_valid': bool(solution.dual_valid),
        'column_values': [clean_number(v) for v in solution.col_value],
        'row_duals': [clean_number(v) for v in solution.row_dual],
        'column_duals': [clean_number(v) for v in solution.col_dual],
        'basis_valid': bool(basis.valid),
        'basic_columns': [j for j, state in enumerate(basis.col_status) if state == highspy.HighsBasisStatus.kBasic],
        'column_basis_status': [str(state) for state in basis.col_status],
        'nonbasic_row_status': [[i, str(state)] for i, state in enumerate(basis.row_status) if state != highspy.HighsBasisStatus.kBasic],
        'objective': clean_number(info.objective_function_value),
        'simplex_iterations': int(info.simplex_iteration_count),
        'dual_ray_request_status': ray_status, 'dual_ray': ray,
        'options': [[name, value] for name, value in options if name != 'log_file']}


def stable_check(value):
    return normalized({key: item for key, item in value.items() if key != 'check_seconds'})


def reconstruct_bound(arrays, numeric, deadline):
    if numeric['numerically_infeasible']:
        values, with_objective = numeric.get('dual_ray'), False
    elif numeric['optimal'] and numeric['solution_dual_valid']:
        values, with_objective = numeric['row_duals'], True
    else:
        return None, []
    if values is None or len(values) != ROWS or any(value is None for value in values):
        return None, []
    attempts = []
    for multipliers, gamma, proposal in exact.integer_candidates(values, with_objective, deadline):
        exact.budget(deadline)
        checked = exact.check_bound(arrays, VARIABLES, multipliers, gamma, min(60, deadline-time.monotonic()))
        B = int(checked['objective_upper_bound_numerator'])
        attempts.append(dict(proposal, gamma=str(gamma), nonzero_rows=len(multipliers), exact_bound=str(B)))
        if B > 0 or (gamma == 0 and B == 0):
            continue
        implication = None
        if B == 0:
            implication = normalized(exact.face_implications(checked, multipliers, BASE_ROWS, arrays['original_column_ids']))
            if implication['positive_t_residual_contradicts_original_feasibility']:
                # The same row vector at gamma=0 gives a direct negative bound.
                gamma = 0
                checked = exact.check_bound(arrays, VARIABLES, multipliers, 0, min(60, deadline-time.monotonic()))
                B = int(checked['objective_upper_bound_numerator'])
                assert B < 0
                implication = None
        certificate = {'kind': 'finite_box_infeasibility' if B < 0 else 'zero_maxmin_face',
            'sparse_integer_row_multipliers': [[i, str(v)] for i, v in multipliers],
            'gamma': str(gamma), 'exact_check': stable_check(checked),
            'face_implications': implication, 'proposal_method': proposal,
            'mathematical_scope': 'complete case4 real selector relaxation with every native row and coordinate cover'}
        return certificate, attempts
    return None, attempts


def reconstruct_primal(arrays, numeric, deadline):
    values = numeric.get('column_values')
    if not numeric['solution_value_valid'] or values is None or len(values) != VARIABLES or any(v is None for v in values):
        return None, []
    attempts = []
    for numerators, denominator, proposal in exact.point_candidates(values, deadline):
        exact.budget(deadline)
        try:
            checked = exact.check_point(arrays, VARIABLES, numerators, denominator, min(60, deadline-time.monotonic()))
        except AssertionError as error:
            attempts.append(dict(proposal, accepted=False, first_failure=str(error)))
            continue
        restored = [0]*1214
        for j, a in enumerate(arrays['original_column_ids']):
            restored[int(a)] = numerators[j]
        point = {'kind': 'rational_complete_selector_point', 'common_denominator': str(denominator),
            'extended_numerators': list(map(str, numerators)),
            'original1214_selector_numerators': list(map(str, restored)),
            'exact_check': stable_check(checked), 'proposal_method': proposal,
            'binary_incidence_or_graph_claimed': False}
        attempts.append(dict(proposal, accepted=True))
        return point, attempts
    return None, attempts


def run(preparation, model_path, arrays_path, directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    result_path = directory/'result.json'
    started = time.monotonic()
    result = {'status': 'initializing one bounded complete max-min query',
        'source_bindings': source_bindings(), 'preparation_sha256': digest(preparation.read_bytes()),
        'base_model_sha256': BASE_MODEL_SHA, 'limits': LIMITS,
        'exact_infeasibility_certificate_found': False,
        'exact_zero_face_certificate_found': False, 'exact_rational_point_found': False,
        'case4_exclusion_verified': False, 'whole_graph_problem_resolved': False,
        'automatic_retry': False}
    save(result_path, result)
    try:
        prepared, model, arrays = checked_preparation(preparation, model_path, arrays_path, True)
        result['mathematical_model_sha256'] = prepared['mathematical_model_sha256']
        result['initialization_seconds'] = time.monotonic()-started
        result['initialization_peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(result_path, result)
        numeric = native_query(arrays, directory/'highs.log')
        result['numeric_artifact'] = save_gzip(directory/'numeric.json.gz', numeric)
        result['numerical_status'] = numeric['model_status']
        result['native_bootstrap_seconds'] = numeric['native_bootstrap_seconds']
        result['native_bootstrap_peak_rss_kib'] = numeric['native_bootstrap_peak_rss_kib']
        result['solver_and_ray_seconds'] = numeric['solver_and_ray_seconds']
        result['simplex_iterations'] = numeric['simplex_iterations']
        result['status'] = 'numerical outcome retained; separate exact reconstruction pending'
        save(result_path, result)
        exact_started = time.monotonic()
        deadline = exact_started+60
        try:
            certificate, attempts = reconstruct_bound(arrays, numeric, deadline)
            result['integer_bound_reconstruction_attempts'] = attempts
            if certificate is not None:
                certificate['mathematical_model_sha256'] = prepared['mathematical_model_sha256']
                result['exact_certificate'] = save_gzip(directory/'exact-bound-certificate.json.gz', certificate)
                if certificate['kind'] == 'finite_box_infeasibility':
                    result['exact_infeasibility_certificate_found'] = True
                    result['status'] = 'exact finite-box contradiction found; independent cold replay required'
                else:
                    result['exact_zero_face_certificate_found'] = True
                    result['new_zero_columns'] = certificate['face_implications']['zero_columns']
                    result['new_one_columns'] = certificate['face_implications']['one_columns']
                    result['status'] = 'exact complete-relaxation zero-face certificate found; cold replay required'
            if certificate is None and time.monotonic() < deadline:
                point, attempts = reconstruct_primal(arrays, numeric, deadline)
                result['rational_primal_reconstruction_attempts'] = attempts
                if point is not None:
                    point['mathematical_model_sha256'] = prepared['mathematical_model_sha256']
                    result['rational_point'] = save_gzip(directory/'exact-rational-point.json.gz', point)
                    result['exact_rational_point_found'] = True
                    result['status'] = ('exact strictly positive selector point found; cold replay required'
                        if point['exact_check']['strictly_positive_t'] else
                        'exact selector relaxation point found; cold replay required')
            if not any(result[key] for key in ('exact_infeasibility_certificate_found','exact_zero_face_certificate_found','exact_rational_point_found')):
                result['status'] = 'UNRESOLVED: numerical outcome retained without an accepted exact outcome'
        except TimeoutError as error:
            result['exact_stage_limit'] = str(error)
            result['status'] = 'UNRESOLVED: exact reconstruction limit; numerical record retained'
        result['exact_stage_seconds'] = time.monotonic()-exact_started
    except Exception as error:
        result['status'] = 'ERROR: no unchecked result promoted'
        result['error_type'], result['error_message'] = type(error).__name__, str(error)
        raise
    finally:
        result['elapsed_seconds'] = time.monotonic()-started
        result['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(result_path, result)
    print(json.dumps({key: value for key, value in result.items() if 'attempts' not in key}, indent=2), flush=True)


def cold_replay(preparation, model_path, arrays_path, result_path, output, root):
    assert not output.exists()
    started = time.monotonic()
    prepared, model, arrays = checked_preparation(preparation, model_path, arrays_path, False)
    fresh_record, fresh_base = recovery.build(root)
    # Runtime versions are discovery provenance, not mathematical premises.
    for key, value in fresh_record.items():
        if key not in ('python_version','numpy_version'):
            assert model[key] == value, ('cold base field', key)
    fresh = extend(fresh_base)
    assert matrix_binding(fresh) == prepared['mathematical_model']['matrix_array_bindings']
    result = json.loads(result_path.read_text())
    assert result['source_bindings'] == source_bindings()
    assert result['preparation_sha256'] == digest(preparation.read_bytes())
    assert result['mathematical_model_sha256'] == prepared['mathematical_model_sha256']
    numeric = read_gzip(result_path.parent, result['numeric_artifact'])
    assert numeric['production_run_calls'] == 1 and numeric['requested_solver_seconds'] == 60
    assert numeric['ray_generating_additional_solve_allowed'] is False
    report = {'status': 'PASS: complete published-input recovery and outcome binding replay',
        'source_bindings': source_bindings(), 'result_sha256': digest(result_path.read_bytes()),
        'preparation_sha256': digest(preparation.read_bytes()),
        'mathematical_model_sha256': prepared['mathematical_model_sha256'],
        'original_selector_columns': SELECTORS, 'all_extended_rows': ROWS,
        'all_extended_nonzeros': NONZEROS, 'optimizer_called': False,
        'exact_case4_exclusion_verified': False, 'new_global_zero_columns': [],
        'new_global_one_columns': [], 'exact_rational_point_verified': False,
        'whole_graph_problem_resolved': False}
    if result['exact_infeasibility_certificate_found'] or result['exact_zero_face_certificate_found']:
        certificate = read_gzip(result_path.parent, result['exact_certificate'])
        assert certificate['mathematical_model_sha256'] == prepared['mathematical_model_sha256']
        multipliers = [[int(i), int(v)] for i, v in certificate['sparse_integer_row_multipliers']]
        gamma = int(certificate['gamma'])
        checked = exact.check_bound(fresh, VARIABLES, multipliers, gamma, 60)
        assert stable_check(checked) == certificate['exact_check']
        if certificate['kind'] == 'finite_box_infeasibility':
            assert int(checked['objective_upper_bound_numerator']) < 0
            assert result['exact_infeasibility_certificate_found'] and not result['exact_zero_face_certificate_found']
            report['exact_case4_exclusion_verified'] = True
            report['status'] = 'PASS: complete cold finite-box Farkas exclusion of indexed case4'
        else:
            assert certificate['kind'] == 'zero_maxmin_face'
            assert gamma > 0 and int(checked['objective_upper_bound_numerator']) == 0
            implication = normalized(exact.face_implications(checked, multipliers, BASE_ROWS, fresh['original_column_ids']))
            assert implication == certificate['face_implications']
            assert result['new_zero_columns'] == implication['zero_columns']
            assert result['new_one_columns'] == implication['one_columns']
            report['new_global_zero_columns'] = implication['zero_columns']
            report['new_global_one_columns'] = implication['one_columns']
            report['conflicting_implications'] = implication['conflicting_columns']
            report['status'] = 'PASS: complete cold zero-face implications for indexed case4'
    if result['exact_rational_point_found']:
        point = read_gzip(result_path.parent, result['rational_point'])
        assert point['mathematical_model_sha256'] == prepared['mathematical_model_sha256']
        numerators = list(map(int, point['extended_numerators']))
        denominator = int(point['common_denominator'])
        checked = exact.check_point(fresh, VARIABLES, numerators, denominator, 60)
        assert stable_check(checked) == point['exact_check']
        restored = [0]*1214
        for j, a in enumerate(fresh['original_column_ids']):
            restored[int(a)] = numerators[j]
        assert list(map(str, restored)) == point['original1214_selector_numerators']
        report['exact_rational_point_verified'] = True
        report['strictly_positive_t'] = checked['strictly_positive_t']
        report['status'] = 'PASS: complete cold rational selector-relaxation point'
    report['seconds'] = time.monotonic()-started
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='mode', required=True)
    for mode in ('prepare', 'run', 'replay'):
        command = commands.add_parser(mode)
        command.add_argument('--model', type=Path, required=True)
        command.add_argument('--arrays', type=Path)
        if mode != 'prepare':
            command.add_argument('--preparation', type=Path, required=True)
        if mode == 'run':
            command.add_argument('--directory', type=Path, required=True)
        else:
            command.add_argument('--output', type=Path, required=True)
        if mode == 'replay':
            command.add_argument('--result', type=Path, required=True)
            command.add_argument('--root', type=Path, default=recovery.ROOT)
    args = parser.parse_args()
    if args.mode == 'prepare':
        prepare(args.model, args.arrays, args.output)
    elif args.mode == 'run':
        run(args.preparation, args.model, args.arrays, args.directory)
    else:
        cold_replay(args.preparation, args.model, args.arrays, args.result, args.output, args.root)


if __name__ == '__main__':
    main()
