"""Bounded full-pool generation on the complete112-face model plus H3.

All 1,960 retained original native rows, both unit sums, four certified
pair capacities, the27-term H3 row and1,102 max-min rows start active.
All164,044 original coordinate covers stay in the pool. Exact acceptance
checks all167,113 rows and the complete original-coordinate proof bindings.
No candidate, basis, positive-selector or symmetry assumption is added.
"""
import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import numpy as np
import scipy
from scipy.sparse import csr_matrix

import rook_case4_face112_h3_model_v2 as builder
import rook_case4_cover_generation as previous
import rook_case4_maxmin_query as frozen

BUILDER_SHA = 'd06dfcadee54deeb81c244c9e11c80bd8687fdc682dcd01e274130fab1a0e2b7'
PARENT_DRIVER_SHA = 'e0e245f1cfc20ff4e5eef7f148ee57b7a97af5829094bf57a0ff9247784942bc'
PREVIOUS_SHA = '6fb1b38194b8a5614ab7db219150dcc458f307b8a1dfb20f6fd55cd77b6325f2'
MAXMIN_SHA = 'f5c664a20983a9a5f8a6601fe67f1d00aed701b29751b77b543ee3aa3afdd322'
BASE_MODEL_SHA = '1928eb76274865e219747f631fee2d7a327ed7acd3a845986844be13c9e34265'
BASE_NPZ_SHA = '4e2de2786d3036cf995953791192500cb4aaa5b0c5079f3d97ea465a4cf64e46'
BASE_STREAM_SHA = '0e200a4ed28e0ac7b415c3c886704af512d3a1346a33ff6bfb8a9da3fad53c0a'
BASE_COLD_PATH = 'experiments/logs/grids-and-triangles/rook-case4-face112-h3-model02-cold-replay.json'
BASE_COLD_SHA = '56864810924bacb6b331db728a4ce32810d8e6f2dfe7c196e0a73e0b2f583a97'
SELECTORS, BASE_ROWS, VARIABLES, ROWS, NONZEROS = 1102, 166011, 1103, 167113, 10769398
PARENT_ROWS, NEW_PARITY_ROWS = 166004, 2
NATIVE, COVER_POOL = 1960, 164044
LIMITS = {
    'maximum_run_calls':30,
    'cumulative_solver_and_existing_ray_seconds':120,
    'numerical_phase_wall_seconds_including_bootstrap_and_scans':180,
    'maximum_new_cover_rows_per_call':512,
    'maximum_total_added_cover_rows':29*512,
    'threads':1, 'violation_tolerance':1e-7,
    'combined_exact_reconstruction_seconds':60,
    'cold_exact_check_seconds':60,
    'maximum_rational_common_denominator_bits':4096,
}
OPTIONS = [list(item) for item in previous.OPTIONS]
exact,normalized,stable_check = frozen.exact,frozen.normalized,frozen.stable_check
set_model,append_rows,choose_rows = previous.set_model,previous.append_rows,previous.choose_rows
native_once = previous.native_once


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return frozen.canonical(value)


def save(path,value):
    frozen.save(path,value)


def row_ids_hash(rows):
    return digest(np.asarray(rows,dtype='<i8').tobytes())


def source_bindings():
    assert digest(Path(builder.__file__).read_bytes()) == BUILDER_SHA
    assert digest(Path(__file__).with_name('rook_case4_face112_cover_generation.py').read_bytes()) == PARENT_DRIVER_SHA
    assert digest(Path(previous.__file__).read_bytes()) == PREVIOUS_SHA
    assert digest(Path(frozen.__file__).read_bytes()) == MAXMIN_SHA
    old = previous.source_bindings()
    current = builder.source_bindings()
    for key in LIMITS:
        assert LIMITS[key] == previous.LIMITS[key]
    return {'driver_sha256':digest(Path(__file__).read_bytes()),
        'exact_face_builder_sha256':BUILDER_SHA,
        'reviewed_parent_generation_driver_sha256':PARENT_DRIVER_SHA,
        'complete112_premise_loader_sha256':current['complete_premise_loader_sha256'],
        'direct_H3_verifier_sha256':current['direct_H3_verifier_sha256'],
        'unchanged_native_row_assembly_and_call_helper_sha256':PREVIOUS_SHA,
        'frozen_serialization_runtime_helper_sha256':MAXMIN_SHA,
        'frozen_exact_helper_sha256':old['frozen_exact_helper_sha256'],
        'frozen_recovery_sha256':current['published_input_recovery_sha256'],
        'bound_audit_sha256':builder.INPUTS['bound_audit'][1],
        'complete_base_cold_replay_sha256':BASE_COLD_SHA}


def runtime_binding():
    return previous.runtime_binding()


def initial_row_ids():
    return list(range(NATIVE))+list(range(PARENT_ROWS,ROWS))


def load_inputs(model_path,arrays_path):
    source_bindings()
    assert digest(model_path.read_bytes()) == BASE_MODEL_SHA
    assert digest(arrays_path.read_bytes()) == BASE_NPZ_SHA
    model,base = builder.load(model_path,arrays_path)
    assert model['canonical_integer_stream_sha256'] == BASE_STREAM_SHA
    pool = list(range(NATIVE,PARENT_ROWS))
    assert len(pool) == COVER_POOL
    assert model['added_integer_cover_row_ids'] == [PARENT_ROWS,PARENT_ROWS+1]
    assert model['added_integer_covers'] == NEW_PARITY_ROWS
    assert model['integer_cover_ranges'] == [[1,1],[1,1]]
    assert model['added_pair_row_ids'] == list(range(BASE_ROWS-5,BASE_ROWS-1))
    assert model['added_pair_rows'] == [[259,590],[259,591],[259,593],[259,732]]
    assert model['third_parity_cover_row'] == BASE_ROWS-1
    assert model['third_parity_cover_range'] == [1,3]
    assert len(model['third_parity_cover_original_support']) == 27
    assert model['all_parent_array_prefixes_equal']
    arrays = extend(base)
    return model,base,arrays,pool


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


def full_float_matrix(arrays):
    # Exact integer input hashes are checked before this conversion.
    for name in ('coefficients', 'row_lower', 'row_upper'):
        assert np.all(np.abs(arrays[name]) < 2**53)
    return csr_matrix((arrays['coefficients'].astype(float), arrays['column_indices'],
                       arrays['row_pointers']), shape=(ROWS, VARIABLES))


def inspect_numeric_point(matrix, arrays, values, pool, active):
    point = np.asarray(values, dtype=float)
    assert point.shape == (VARIABLES,) and np.all(np.isfinite(point))
    activity = matrix @ point
    assert activity.shape == (ROWS,) and np.all(np.isfinite(activity))
    violation = np.maximum(np.maximum(arrays['row_lower']-activity,
                                     activity-arrays['row_upper']), 0.0)
    selected, eligible_count = choose_rows(violation, pool, active,
        LIMITS['maximum_new_cover_rows_per_call'], LIMITS['violation_tolerance'])
    tol = LIMITS['violation_tolerance']
    pool_array = np.asarray(pool, dtype=np.int64)
    active_array = np.asarray(sorted(active), dtype=np.int64)
    return {'all_original_and_extension_rows_scanned': ROWS,
        'full_matrix_nonzeros_scanned': NONZEROS,
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




def controls():
    result = previous.controls()
    assert result['optimizer_calls'] == 0
    # Every original feasible x extends with t=0. Conversely every extended
    # point restricts to its original x. These exact rational grid controls
    # exercise zero, unequal and full coordinates without an optimizer.
    cases=0
    from itertools import product
    for den in range(1,5):
        for point in product(range(den+1),repeat=3):
            feasible_t=[t for t in range(den+1)
                        if all(0 <= x-t <= den for x in point)]
            assert feasible_t == list(range(min(point)+1))
            cases+=1
    result['rational_maxmin_extension_controls']=cases
    result['all_cover_rows_in_new_pool']=COVER_POOL
    result['no_compression_or_new_selector_assumption']=True
    return result


def definition(model,arrays,pool):
    math = {'base_model_sha256':BASE_MODEL_SHA,'base_array_npz_sha256':BASE_NPZ_SHA,
        'base_integer_stream_sha256':BASE_STREAM_SHA,
        'selectors':SELECTORS,'variables_including_t':VARIABLES,
        'rows':ROWS,'nonzeros':NONZEROS,'t_column':SELECTORS,
        'original_rows':BASE_ROWS,'added_extension_rows':SELECTORS,
        'extension_rule':'row166011+j has +1 at selector j,-1 at t, bounds[0,1]',
        'variable_lower':0,'variable_upper':1,
        'objective':'minimize -t (equivalently maximize t)',
        'matrix_array_bindings':frozen.matrix_binding(arrays),
        'fixed_zero_original_columns':model['fixed_zero_columns'],
        'proved_face_only':True,'new_selector_assumptions_added':False,
        'symmetry_restriction_added':False}
    initial=initial_row_ids()
    initial_nnz=sum(int(arrays['row_pointers'][r+1]-arrays['row_pointers'][r]) for r in initial)
    assert len(initial)==3069 and initial_nnz==27969
    assert len(initial)==len(set(initial)) and not set(initial).intersection(pool)
    assert set(initial)|set(pool)==set(range(ROWS))
    spec={'complete_original_maxmin_model':math,
        'complete_original_maxmin_model_sha256':digest(canonical(math)),
        'retained_cover_pool_count':len(pool),
        'retained_cover_pool_original_ID_sha256':row_ids_hash(pool),
        'all_remaining_covers_in_pool_without_compression':True,
        'initial_rows':len(initial),'initial_rows_original_ID_sha256':row_ids_hash(initial),
        'initial_row_ranges':[[0,NATIVE],[PARENT_ROWS,ROWS]],
        'always_active_proved_parity_equalities':[PARENT_ROWS,PARENT_ROWS+1],
        'always_active_certified_pair_rows':list(range(BASE_ROWS-5,BASE_ROWS-1)),
        'always_active_third_parity_cover_row':BASE_ROWS-1,
        'third_parity_cover_range':[1,3],
        'third_parity_cover_original_support':model['third_parity_cover_original_support'],
        'unit_sum_ranges':[[1,1],[1,1]],'certified_pair_original_columns':model['added_pair_rows'],
        'complete_premise_input_bindings':model['proof_input_bindings'],
        'H3_parent_input_bindings':model['parent_input_bindings'],
        'initial_nonzeros':initial_nnz,
        'maximum_active_rows':len(initial)+LIMITS['maximum_total_added_cover_rows'],
        'all_original_rows_required_for_rational_primal_acceptance':ROWS,
        'only_original_rows_may_be_added':True,
        'numerical_row_selection':'at most512 unseen covers, greatest violation first, ties by original row ID',
        'subset_ray_scope':'an exact finite-box certificate on an active subset applies to the entire face LP',
        'basis_policy':'one persistent native solver; appendRows without reset or reload',
        'original1214_restoration_rule':'insert zero at every one of the112 proved-zero columns',
        'no_new_selector_assumptions_or_symmetry':True,
        'limits':LIMITS,'native_options':OPTIONS}
    return spec,digest(canonical(spec))


def prepare(model_path,arrays_path,output):
    assert not output.exists()
    started=time.monotonic()
    model,base,arrays,pool=load_inputs(model_path,arrays_path)
    spec,spec_hash=definition(model,arrays,pool)
    record={'status':'bounded full-pool face112 generation with both unit sums, four pair capacities and H3 prepared; no optimizer',
        'source_bindings':source_bindings(),'runtime_binding':runtime_binding(),
        'definition':spec,'definition_sha256':spec_hash,'controls':controls(),
        'fixed_zero_original_columns':model['fixed_zero_columns'],
        'production_optimizer_calls':0,'case4_excluded':False,
        'seconds':time.monotonic()-started,
        'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output,record)
    print(json.dumps({k:v for k,v in record.items() if k!='definition'},indent=2),flush=True)


def checked_preparation(preparation,model_path,arrays_path,require_runtime):
    record=json.loads(preparation.read_text())
    assert record['source_bindings']==source_bindings()
    model,base,arrays,pool=load_inputs(model_path,arrays_path)
    spec,spec_hash=definition(model,arrays,pool)
    assert record['definition']==spec and record['definition_sha256']==spec_hash
    assert record['fixed_zero_original_columns']==model['fixed_zero_columns']
    if require_runtime:
        assert record['runtime_binding']==runtime_binding()
    return record,model,base,arrays,pool


def cold_arrays(model,base,arrays,root):
    rebuilt_model,rebuilt_base=builder.build(root)
    for key,value in rebuilt_model.items():
        if key not in ('numpy_version','python_version'):
            assert model[key] == value,('cold face model',key)
    assert set(base)==set(rebuilt_base)
    for key in base:
        assert np.array_equal(base[key],rebuilt_base[key]),('cold face array',key)
    rebuilt=extend(rebuilt_base)
    assert frozen.matrix_binding(rebuilt)==frozen.matrix_binding(arrays)
    return rebuilt


def preflight_replay(preparation,model_path,arrays_path,root,output):
    assert not output.exists()
    started=time.monotonic()
    prepared,model,base,arrays,pool=checked_preparation(preparation,model_path,arrays_path,False)
    raw=(root/BASE_COLD_PATH).read_bytes()
    assert digest(raw)==BASE_COLD_SHA
    cold=json.loads(raw)
    assert cold['status'].startswith('PASS:')
    assert cold['model_sha256']==BASE_MODEL_SHA
    assert cold['source_bindings']==builder.source_bindings()
    assert cold['canonical_integer_stream_sha256']==BASE_STREAM_SHA
    assert cold['arrays']['sha256']==BASE_NPZ_SHA
    assert (cold['columns'],cold['rows'],cold['nonzeros'])==(SELECTORS,BASE_ROWS,builder.NONZEROS)
    assert cold['all_omission_witnesses_replayed'] and cold['all_row_column_transports_checked']
    control=controls()
    assert control==prepared['controls']
    report={'status':'PASS: frozen complete cold model bound; extended arrays, pool partition and native assembly controls checked',
        'source_bindings':source_bindings(),'preparation_sha256':digest(preparation.read_bytes()),
        'definition_sha256':prepared['definition_sha256'],
        'original_rows':BASE_ROWS,'extended_rows':ROWS,
        'retained_cover_pool_count':len(pool),'all_input_arrays_loaded_and_hashed':True,
        'prior_complete_cold_replay_sha256':BASE_COLD_SHA,'duplicate_base_rebuild_performed':False,
        'terminal_exact_acceptance_still_rebuilds_all_inputs':True,
        'optimizer_calls':0,'case4_excluded':False,
        'seconds':time.monotonic()-started,
        'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output,report)
    print(json.dumps(report,indent=2),flush=True)


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
            'mathematical_scope': 'complete case4 real selector relaxation on the proved112-zero face with every original native row, coordinate cover, both proved unit sums, four certified pair capacities and the third parity cover'}
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


def expanded_numeric(record):
    rows = record['active_original_row_ids']
    assert len(rows) == len(set(rows)) and all(0 <= row < ROWS for row in rows)
    numeric = {key:record[key] for key in ('optimal', 'numerically_infeasible',
        'solution_value_valid', 'solution_dual_valid', 'column_values')}
    for name in ('row_duals', 'dual_ray'):
        values = record[name]
        if values is None or len(values) != len(rows) or any(v is None for v in values):
            numeric[name] = None
        else:
            expanded = [0.0]*ROWS
            for row, value in zip(rows, values):
                expanded[row] = value
            numeric[name] = expanded
    return numeric


def run(preparation, model_path, arrays_path, directory):
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
            preparation, model_path, arrays_path, True)
        result['definition_sha256'] = prepared['definition_sha256']
        result['input_replay_seconds'] = time.monotonic()-started
        phase_start = time.monotonic()
        phase_deadline = phase_start+LIMITS['numerical_phase_wall_seconds_including_bootstrap_and_scans']
        matrix = full_float_matrix(arrays)
        h = highspy.Highs()
        for name, value in OPTIONS+[('log_file', str(directory/'highs.log'))]:
            assert h.setOptionValue(name, value) == highspy.HighsStatus.kOk
        rows, active = initial_row_ids(), set(initial_row_ids())
        set_model(h, matrix, arrays, rows, VARIABLES)
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
            if (len(numeric['column_values']) != VARIABLES or
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
                certificate, attempts = reconstruct_bound(arrays, numeric, deadline)
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
                    point, attempts = reconstruct_primal(arrays, numeric, deadline)
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


def replay(preparation, model_path, arrays_path, root, result_path, output):
    assert not output.exists()
    started = time.monotonic()
    prepared, model, base, arrays, pool = checked_preparation(
        preparation, model_path, arrays_path, False)
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
    report = {'status': 'PASS: complete face112 plus H3 matrix, exact zero/equality/pair/parity proofs and bounded prefix transcript',
        'source_bindings': source_bindings(), 'preparation_sha256': digest(preparation.read_bytes()),
        'result_sha256': digest(result_path.read_bytes()), 'definition_sha256': prepared['definition_sha256'],
        'original_rows_rebuilt': BASE_ROWS, 'extended_rows_rebuilt': ROWS,
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
        check = frozen.exact.check_bound(arrays, VARIABLES, multipliers, gamma,
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
                check, multipliers, BASE_ROWS, arrays['original_column_ids']))
            assert implication == cert['face_implications']
            report['exact_zero_face_verified'] = True
            report['zero_original_columns'] = implication['zero_columns']
            report['one_original_columns'] = implication['one_columns']
    if result['exact_rational_point_found']:
        point = frozen.read_gzip(result_path.parent, result['rational_point'])
        assert point['definition_sha256'] == prepared['definition_sha256']
        assert 0 <= point['source_call_index'] < len(records)
        nums, den = list(map(int, point['extended_numerators'])), int(point['common_denominator'])
        check = frozen.exact.check_point(arrays, VARIABLES, nums, den,
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
        if mode != 'prepare':
            c.add_argument('--preparation', type=Path, required=True)
        if mode == 'run':
            c.add_argument('--directory', type=Path, required=True)
        else:
            c.add_argument('--output', type=Path, required=True)
        if mode in ('preflight', 'replay'):
            c.add_argument('--root', type=Path, default=builder.recovery.ROOT)
        if mode == 'replay':
            c.add_argument('--result', type=Path, required=True)
    a = parser.parse_args()
    if a.mode == 'prepare':
        prepare(a.model, a.arrays, a.output)
    elif a.mode == 'preflight':
        preflight_replay(a.preparation, a.model, a.arrays, a.root, a.output)
    elif a.mode == 'run':
        run(a.preparation, a.model, a.arrays, a.directory)
    else:
        replay(a.preparation, a.model, a.arrays, a.root, a.result, a.output)


if __name__ == '__main__':
    main()
