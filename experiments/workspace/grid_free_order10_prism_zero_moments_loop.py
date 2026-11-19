"""Bounded IPM separation with the proved prism-containment zero closure.

The frozen 47,634-row prism-zero baseline is reconstructed without changing
its positive DP bounds or scaling. Fifty-eight core counts are fixed to
zero and eleven certified order-ten moment cuts are appended. Preparation
calls no optimizer. A run has at most six sequential 120-second IPM calls
and at most 180 seconds per complete-cache r8,s1 scan. Only exact integer
separators can be added. Numerical infeasibility is not a proof.
"""

import argparse
import gc
import gzip
import hashlib
import json
from pathlib import Path
import pickle
import resource
from threading import Timer
import time

import highspy
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits

import grid_free_order10_prism_zero_v2 as baseline
import grid_free_order10_prism_zero_closure as closure
import grid_free_order10_r8s1_scan as new_separator
import grid_free_order10_moments as old_separator
import grid_free_order10_scaled as counts


BASELINE_SOURCE_SHA = 'ec972814b45828107d9c97f7c94e9760fef7973b360f3af7da8c8a33bc4e1ab3'
BASELINE_PREPARATION_SHA = '2fed8e077cc715c36ebfedca1c687bb11e116a613f11cf8ded11e85d02ee0913'
BASELINE_MODEL_SHA = 'cd09cf494efafa04cd850ffa593d8d55679fb39393118d0d06189ee5a3a0e596'
CLOSURE_SOURCE_SHA = '1940942c270880ca5d8853c860074bd5c79a3dcc8d5283fd9a3bd5ad52d77bc0'
CLOSURE_SHA = 'cde1bd353eb39fe8aa713080a5acfb6ae78f3dd13244d9255c9217541060919c'
NEW_CUTS_SHA = '65b73756822af0c57daa27489ec3f6eaaa8372d10d875ec23c0e942034513d15'
REDUCTION_SHA = '0ad45482ea273b3412e8d308d47eabab366678f4a7e446e4a9f32791c563af65'


def vector_hash(cuts):
    return hashlib.sha256(json.dumps([row['coefficients'] for row in cuts],
                                    separators=(',', ':')).encode()).hexdigest()


def dependencies():
    names = ['grid_free_order10_prism_zero_v2.py',
             'grid_free_order10_prism_zero_closure.py',
             'grid_free_order10_r8s1_scan.py', 'grid_free_order10_r8s1.py',
             'grid_free_order10_moments_loop.py', 'grid_free_order10_moments.py',
             'grid_free_order10_scaled.py', 'grid_free_order10_scaled_cut.py']
    return {name: counts.digest(Path(__file__).with_name(name)) for name in names}


def load_dense_once(cache, bound_records, bridge_row=None):
    """Use the hash-bound reduction once; export the tiny bridge row before disposal."""
    assert counts.digest(cache) == REDUCTION_SHA
    with cache.open('rb') as stream:
        data, cores, scale, inj, induced = pickle.load(stream)
    assert len(data[0]) == 48965 and len(data[1][10]) == 42430
    assert list(cores) == [item['catalogue_type'] for item in bound_records]
    assert len(cores) == 549 and scale == 3628800
    assert induced.shape == inj.shape == (48965, 550)
    for coordinate, item in enumerate(bound_records, 1):
        index = cores[coordinate-1]
        assert item['coordinate'] == coordinate
        assert list(data[0][index]) == item['rows']
        assert data[2][index] == item['automorphisms']
    # This optional export is unrelated to the optimization. No motif bound
    # or partition face is introduced into the numerical model.
    assert cores[520] == 48936 and data[2][48936] == 8
    ordinary = [[j, int(value)] for j, value in enumerate(inj[48936]) if value]
    induced_raw = [[j, int(value)] for j, value in enumerate(induced[48936]) if value]
    assert ordinary == [[521, 8]] and induced_raw == [[521, scale]]
    bridge = {'status': 'exact edge-component count row verified',
              'source_sha256': counts.digest(Path(__file__)),
              'reduced_cache_path': str(cache), 'reduced_cache_sha256': REDUCTION_SHA,
              'coordinate': 521, 'catalogue_type': 48936, 'automorphisms': 8,
              'stored_graph_rows': list(data[0][48936]),
              'ordinary_labelled_embedding_form': ordinary,
              'ordinary_unlabelled_count_form': [[521, 1]],
              'induced_raw_form': induced_raw, 'induced_scale': scale,
              'induced_unlabelled_count_form': [[521, 1]],
              'no_additional_model_bound_or_face': True}
    if bridge_row is not None:
        counts.save(bridge_row, bridge)
    lo, hi = int(induced.min()), int(induced.max())
    assert -(1 << 63) <= lo <= hi < (1 << 63)
    del inj
    gc.collect()
    raw = induced.astype(np.int64)
    del induced
    gc.collect()
    return data, cores, scale, raw, bridge


def closure_control(certificate, data, cores, raw, scale):
    assert counts.digest(Path(closure.__file__)) == CLOSURE_SOURCE_SHA
    assert counts.digest(certificate) == CLOSURE_SHA
    saved = json.loads(certificate.read_text())
    assert saved['source_sha256'] == CLOSURE_SOURCE_SHA
    assert saved['reduced_cache_sha256'] == REDUCTION_SHA and saved['scale'] == scale
    zeros = {1}
    for step in saved['trace']:
        index = step['induced_type']
        assert list(data[0][index]) == step['graph_rows']
        terms, divisor = closure.primitive_row(raw[index])
        assert terms == step['primitive_count_inequality']
        assert divisor == step['raw_positive_gcd']
        row = dict(terms)
        assert row.get(0, 0) == 0 and all(j in zeros for j, v in terms if v > 0)
        fresh = sorted(j for j, v in terms if v < 0 and j not in zeros)
        assert fresh == step['forced_zero_coordinates'] and fresh
        zeros.update(fresh)
    assert sorted(zeros) == saved['forced_zero_coordinates'] and len(zeros) == 28
    graph_zeros = [j for j, index in enumerate(cores, 1) if closure.prism(data[0][index])]
    assert graph_zeros == saved['prism_containing_core_coordinates'] and len(graph_zeros) == 58
    types = [i for i, rows in enumerate(data[0]) if closure.prism(rows)]
    assert types == saved['prism_containing_induced_types'] and len(types) == 1443
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
    remaining = [0]+[j for j in range(1, 550) if j not in set(graph_zeros)]
    assert not np.any(raw[np.ix_(types, remaining)])
    return graph_zeros, {'sign_trace_steps': len(saved['trace']),
                         'sign_rule_zero_coordinates': len(zeros),
                         'prism_containing_core_zero_coordinates': len(graph_zeros),
                         'vanishing_induced_prism_forms': len(types),
                         'extension_DAG_agrees_with_containment': True,
                         'coefficientwise_zero_check_passed': True}


def full_cache_seed_control(scanner, certificate):
    """Embed all old pruned directions into full blocks and check their forms."""
    assert counts.digest(certificate) == NEW_CUTS_SHA
    saved = json.loads(certificate.read_text())
    assert saved['source_sha256'] == new_separator.CONSTRUCTION_SHA
    assert saved['reduced_cache_sha256'] == REDUCTION_SHA
    witness_path = Path(saved['witness_path'])
    assert counts.digest(witness_path) == saved['witness_sha256']
    witness = json.loads(witness_path.read_text())
    point = witness['rounded_core_values']
    counts_at_point = scanner.count_numerators(point)
    assert counts_at_point == witness['induced_counts']
    embeddings = [value*a for value, a in zip(counts_at_point, scanner.data[2])]
    used = set()
    for block in saved['negative_blocks']:
        masks, tensor = scanner.lookup[block['root_type']]
        positions = {mask: i+1 for i, mask in enumerate(masks)}
        vector = [0]*(len(masks)+1)
        vector[0] = block['integer_vector'][0]
        for mask, value in zip(block['flag_masks'], block['integer_vector'][1:], strict=True):
            vector[positions[mask]] = value
        matrix = scanner.matrix(tensor, len(vector), embeddings)
        v = np.array(vector, dtype=object)
        assert int(v@matrix@v) == block['integer_quadratic_value'] < 0
        terms, divisor = new_separator.construction.induced_form(tensor, vector, scanner.data[2])
        assert terms == block['primitive_induced_count_form']
        assert divisor == block['induced_form_gcd']
        core, common = new_separator.construction.reduced_form(terms, scanner.raw, scanner.scale)
        assert common == block['core_form_gcd']
        index = block['core_cut_index']
        assert core == saved['unique_core_cuts'][index]['coefficients']
        assert sum(a*x for a, x in zip(core, point)) < 0
        used.add(index)
    assert used == set(range(11))
    return saved, {'repaired_integer_count_forms_checked': len(counts_at_point),
                   'old_integer_directions_embedded_in_full_cache': len(saved['negative_blocks']),
                   'exact_full_cache_seed_cuts_checked': len(used)}


def cut_matrix(cuts, active, upper, fixed):
    position = {j: i for i, j in enumerate(active)}
    values, columns, starts, rhs = [], [], [0], []
    for item in cuts:
        row = item['coefficients']
        assert len(row) == 550 and all(type(v) is int for v in row)
        constant = sum(row[j]*value for j, value in fixed.items())
        terms = [(position[j], row[j]*upper[j]) for j in active if row[j]]
        divisor = max([abs(constant)]+[abs(value) for _, value in terms])
        assert divisor > 0
        for column, value in terms:
            columns.append(column)
            values.append(-value/divisor)
        starts.append(len(values))
        rhs.append(constant/divisor)
    matrix = sparse.csr_matrix((np.array(values, dtype=float),
                                np.array(columns, dtype=np.int32), np.array(starts, dtype=np.int32)),
                               shape=(len(cuts), len(active)))
    assert np.all(np.isfinite(matrix.data)) and np.all(np.isfinite(rhs))
    return matrix, np.array(rhs)


def model(baseline_preparation, zero_closure, new_cuts, full_cache, bridge_row=None):
    assert counts.digest(Path(baseline.__file__)) == BASELINE_SOURCE_SHA
    assert counts.digest(baseline_preparation) == BASELINE_PREPARATION_SHA
    baseline_saved = json.loads(baseline_preparation.read_text())
    inputs = {key: Path(value) for key, value in baseline_saved['inputs'].items()}
    for key, path in inputs.items():
        assert counts.digest(path) == baseline_saved['input_hashes'][key]
    paths, old_cuts, _ = baseline.read_certified_cuts(inputs['loop_preparation'], inputs['loop_result'])
    audit = json.loads(inputs['reduction_audit'].read_text())
    assert audit['source_sha256'] == baseline.REDUCTION_AUDIT_SOURCE_SHA
    assert audit['cache_sha256'] == REDUCTION_SHA
    assert audit['original_equations_checked'] == 180445
    assert audit['distinct_nonzero_reduced_equations'] == 0 and audit['nonzero_reduced_equations'] == []
    assert audit['induced_count_forms_integral_coefficientwise']
    assert audit['ordinary_count_forms_integral_coefficientwise']
    base_saved = json.loads(paths['base_preparation'].read_text())
    data, cores, scale, raw, bridge = load_dense_once(
        paths['reduced_cache'], base_saved['upper_bounds'], bridge_row)
    bounds = counts.bounds_for(data, cores)
    assert bounds == base_saved['upper_bounds']
    metadata, numeric = counts.make_model(raw, bounds, False)
    assert metadata == base_saved['cases'][1] and numeric is not None
    base, base_rhs, fixed, upper = numeric
    active = metadata['active_core_coordinates']
    assert fixed == {0: 1, 56: 0, 57: 0}
    assert active == [j for j in range(1, 550) if j not in (56, 57)]
    extra, extra_rhs = baseline.previous.cut_matrix(old_cuts, active, upper, fixed)
    matrix = sparse.vstack([base, extra], format='csc')
    matrix.sort_indices()
    rhs = np.concatenate((base_rhs, extra_rhs))
    lower, column_upper = np.zeros(len(active)), np.ones(len(active))
    column_upper[active.index(1)] = 0
    assert baseline.numerical_model_hash(matrix, rhs, lower, column_upper) == BASELINE_MODEL_SHA
    assert baseline_saved['model']['numerical_model_sha256'] == BASELINE_MODEL_SHA
    assert matrix.shape == (47634, 547) and matrix.nnz == 5427993
    zeros, zero_control = closure_control(zero_closure, data, cores, raw, scale)
    for coordinate in zeros:
        if coordinate in active:
            column_upper[active.index(coordinate)] = 0
        else:
            assert fixed[coordinate] == 0
    assert sum(column_upper > 0) == 491
    scanner = new_separator.FullScanner(data, raw, scale, full_cache, REDUCTION_SHA)
    seed_saved, seed_control = full_cache_seed_control(scanner, new_cuts)
    seed = [{'coefficients': cut['coefficients']+[0]*492, 'origin': cut['origin']} for cut in old_cuts]
    for index, cut in enumerate(seed_saved['unique_core_cuts']):
        seed.append({'coefficients': cut['coefficients'],
                     'origin': {'kind': 'initial exact r8s1 separator', 'cut_index': index,
                                'certificate_path': str(new_cuts), 'certificate_sha256': NEW_CUTS_SHA}})
    assert len(seed) == len({tuple(cut['coefficients']) for cut in seed}) == 25
    extra, extra_rhs = cut_matrix(seed[14:], active, upper, fixed)
    matrix = sparse.vstack([matrix, extra], format='csc')
    matrix.sort_indices()
    rhs = np.concatenate((rhs, extra_rhs))
    report = {'rows': matrix.shape[0], 'stored_columns': matrix.shape[1],
              'free_columns': int(sum(column_upper > 0)), 'nonzeros': int(matrix.nnz),
              'baseline_rows': 47634, 'baseline_nonzeros': 5427993,
              'baseline_numerical_model_sha256': BASELINE_MODEL_SHA,
              'initial_old_cuts': 14, 'initial_new_r8s1_cuts': 11, 'initial_cut_count': 25,
              'active_core_coordinates': active, 'prism_zero_core_coordinates': zeros,
              'effective_fixed_coordinates': [[0, 1]]+[[j, 0] for j in zeros],
              'positive_DP_bounds_and_scalings_unchanged': True,
              'initial_cut_coefficients_sha256': vector_hash(seed),
              'numerical_model_sha256': baseline.numerical_model_hash(matrix, rhs, lower, column_upper),
              'full_r8s1_blocks': len(scanner.blocks), 'old_family_blocks': 1416,
              'zero_closure_control': zero_control, 'full_cache_seed_control': seed_control,
              'reduction_audit_path': str(inputs['reduction_audit']),
              'reduction_audit_sha256': counts.digest(inputs['reduction_audit']),
              'reduced_cache_sha256': REDUCTION_SHA, 'full_cache_sha256': new_separator.CACHE_SHA,
              'objective': 'zero; pure feasibility', 'additional_edge_component_bound': False,
              'row_scaling': 'unchanged baseline; added cuts normalized by original positive DP scales'}
    assert report['rows'] == 47645
    return data, scale, raw, report, (matrix, rhs, lower, column_upper, fixed, upper), seed, scanner, bridge


def prepare(baseline_preparation, zero_closure, new_cuts, full_cache, output, bridge_row=None):
    started = time.monotonic()
    _, _, _, metadata, _, seed, _, bridge = model(
        baseline_preparation, zero_closure, new_cuts, full_cache, bridge_row)
    h, options = baseline.supported_options(120)
    paths = {'baseline_preparation': baseline_preparation, 'zero_closure': zero_closure,
             'new_cuts': new_cuts, 'full_cache': full_cache}
    result = {'status': 'zero-closure IPM loop prepared; no optimization run',
              'source_sha256': counts.digest(Path(__file__)), 'dependency_hashes': dependencies(),
              'inputs': {key: str(path) for key, path in paths.items()},
              'input_hashes': {key: counts.digest(path) for key, path in paths.items()},
              'model': metadata, 'initial_cuts': seed, 'highs_version': h.version(),
              'supported_options': options, 'maximum_rounds': 6,
              'maximum_solver_seconds_per_round': 120, 'maximum_new_scan_seconds_per_round': 180,
              'threads': 1, 'same_Highs_instance_reused': True, 'dual_extraction': False,
              'stop_on_nonoptimal_solver_status': True, 'stop_on_incomplete_new_scan': True,
              'stop_on_no_fresh_exact_cut': True, 'PSD_feasibility_certified_by_scan': False,
              'edge_component_row_control': bridge,
              'preparation_seconds': time.monotonic()-started,
              'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    if bridge_row is not None:
        result.update(edge_component_row_path=str(bridge_row), edge_component_row_sha256=counts.digest(bridge_row))
    counts.save(output, result)
    print(json.dumps({key: value for key, value in result.items()
                      if key not in ('initial_cuts', 'edge_component_row_control', 'model')}, indent=2), flush=True)
    print(json.dumps({key: value for key, value in metadata.items()
                      if key not in ('active_core_coordinates', 'effective_fixed_coordinates')}, indent=2), flush=True)
    return result


def raw_save(path, record):
    temporary = path.with_name(path.name+'.pending')
    temporary.write_bytes(gzip.compress((json.dumps(record, separators=(',', ':'))+'\n').encode(), mtime=0))
    temporary.replace(path)


def run(preparation, output, prefix, rounds, seconds, scan_seconds):
    assert 1 <= rounds <= 6 and 0 < seconds <= 120 and 0 < scan_seconds <= 180
    saved = json.loads(preparation.read_text())
    assert saved['source_sha256'] == counts.digest(Path(__file__))
    assert saved['dependency_hashes'] == dependencies()
    paths = {key: Path(value) for key, value in saved['inputs'].items()}
    for key, path in paths.items():
        assert counts.digest(path) == saved['input_hashes'][key]
    data, scale, raw, metadata, numeric, held, scanner, _ = model(**paths)
    assert metadata == saved['model'] and held == saved['initial_cuts']
    matrix, rhs, lower, column_upper, fixed, upper = numeric
    active = metadata['active_core_coordinates']
    zeros = metadata['prism_zero_core_coordinates']
    h, options = baseline.supported_options(seconds)
    assert h.version() == saved['highs_version']
    h.HandleUserInterrupt = True
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = matrix.shape[1], matrix.shape[0]
    lp.col_cost_, lp.col_lower_, lp.col_upper_ = np.zeros(matrix.shape[1]), lower, column_upper
    lp.row_lower_, lp.row_upper_ = np.full(matrix.shape[0], -highspy.kHighsInf), rhs
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = matrix.indptr, matrix.indices, matrix.data
    assert h.passModel(lp) == highspy.HighsStatus.kOk
    known = {tuple(cut['coefficients']) for cut in held}
    result = {'status': 'running bounded prism-zero moment loop',
              'source_sha256': saved['source_sha256'], 'preparation_sha256': counts.digest(preparation),
              'maximum_rounds': rounds, 'solver_seconds_per_round': seconds,
              'new_scan_seconds_per_round': scan_seconds, 'threads': 1, 'options': options,
              'prism_zero_core_coordinates': zeros, 'fixed_order_nine_point': False,
              'rounds': [], 'cuts': held, 'dual_extraction_performed': False,
              'exact_infeasibility_certificate': False, 'exact_count_witness': False,
              'PSD_feasibility_certified': False}
    counts.save(output, result)
    for round_index in range(rounds):
        model_sha = baseline.numerical_model_hash(matrix, rhs, lower, column_upper)
        record = {'round': round_index, 'rows': matrix.shape[0], 'nonzeros': int(matrix.nnz),
                  'held_cuts': len(held), 'held_cut_coefficients_sha256': vector_hash(held),
                  'numerical_model_sha256': model_sha}
        print(json.dumps({'starting_round': round_index, 'rows': matrix.shape[0],
                          'held_cuts': len(held)}), flush=True)
        assert h.setOptionValue('time_limit', h.getRunTime()+seconds) == highspy.HighsStatus.kOk
        started = time.monotonic()
        timer = Timer(seconds, h.cancelSolve)
        timer.start()
        try:
            run_status = h.run()
        finally:
            timer.cancel()
        status = h.getModelStatus()
        record.update(numerical_status=str(status), highs_run_status=str(run_status),
                      solver_seconds=time.monotonic()-started)
        returned = baseline.returned_data(h)
        returned.update(source_sha256=saved['source_sha256'], loop_round=round_index,
                        numerical_model_sha256=model_sha, numerical_status=str(status),
                        preparation_sha256=counts.digest(preparation))
        raw_path = prefix.with_name(prefix.name+f'-round{round_index}-solver-data.json.gz')
        raw_save(raw_path, returned)
        record.update(returned_data_path=str(raw_path), returned_data_sha256=counts.digest(raw_path),
                      returned_value_valid=returned['value_valid'], returned_dual_valid=returned['dual_valid'],
                      solver_info=returned['info'])
        values = returned['column_values']
        proposal_path = prefix.with_name(prefix.name+f'-round{round_index}-proposal.json')
        if returned['value_valid'] and len(values) == len(active) and all(type(v) is float for v in values):
            ordinary = [value*upper[j] for j, value in zip(active, values)]
            proposal = {'status': 'numerical prism-zero proposal; exact feasibility not certified',
                        'source_sha256': saved['source_sha256'], 'preparation_sha256': counts.digest(preparation),
                        'loop_round': round_index, 'numerical_model_sha256': model_sha,
                        'numerical_status': str(status), 'case_index': 1, 'fixed_order_nine_point': False,
                        'held_cut_count': len(held), 'held_cut_coefficients_sha256': vector_hash(held),
                        'required_prism_zero_coordinates': zeros,
                        'numerical_fixed_zero_residuals': [[j, ordinary[active.index(j)]]
                                                          for j in zeros if j in active],
                        'real_proposal': {'active_coordinates': active, 'scaled_values': values,
                                          'ordinary_core_values': ordinary,
                                          'exact_real_feasibility_certified': False}}
            counts.save(proposal_path, proposal)
            record.update(proposal_path=str(proposal_path), proposal_sha256=counts.digest(proposal_path))
        if status != highspy.HighsModelStatus.kOptimal:
            result['status'] = 'stopped on numerical solver status; no exact infeasibility conclusion'
            record['proposal_scans'] = 'not run after nonoptimal solver status'
            result['rounds'].append(record)
            counts.save(output, result)
            print(json.dumps(record), flush=True)
            break
        assert 'proposal_sha256' in record
        old_path = prefix.with_name(prefix.name+f'-round{round_index}-old-separation.json')
        old = old_separator.scan(proposal_path, old_path)
        old_separator.replay(old_path)
        new_path = prefix.with_name(prefix.name+f'-round{round_index}-r8s1-separation.json')
        new = scanner.scan(proposal_path, new_path, scan_seconds)
        replay = scanner.replay(new_path)
        replay_path = prefix.with_name(prefix.name+f'-round{round_index}-r8s1-replay.json')
        counts.save(replay_path, replay)
        fresh = []
        for kind, separated, path, key in [('old1416', old, old_path, 'unique_integer_cuts'),
                                           ('complete_r8s1', new, new_path, 'unique_core_cuts')]:
            for index, cut in enumerate(separated[key]):
                assert cut['exact_value_at_proposal'][0] < 0
                coefficients = cut['coefficients']+([0]*492 if kind == 'old1416' else [])
                assert len(coefficients) == 550
                vector = tuple(coefficients)
                if vector not in known:
                    known.add(vector)
                    fresh.append({'coefficients': coefficients,
                                  'origin': {'kind': 'exact '+kind+' separator', 'round': round_index,
                                             'cut_index': index, 'certificate_path': str(path),
                                             'certificate_sha256': counts.digest(path)}})
        held.extend(fresh)
        point = [0]*550
        point[0] = 1
        for coordinate, value in zip(active, ordinary):
            point[coordinate] = min(upper[coordinate], max(0, int(round(value))))
        for coordinate in zeros:
            point[coordinate] = 0
        checked = counts.exact_candidate(data, scale, raw, point, upper, False)
        cut_values = [sum(a*x for a, x in zip(cut['coefficients'], point)) for cut in held]
        checked.update(exact_held_cut_values=cut_values,
                       negative_held_cuts=sum(value < 0 for value in cut_values),
                       held_cut_coefficients_sha256=vector_hash(held),
                       all_58_prism_core_zeros_imposed_exactly=True,
                       PSD_feasibility_certified=False)
        checked_path = prefix.with_name(prefix.name+f'-round{round_index}-rounded-counts.json')
        counts.save(checked_path, checked)
        record.update(old_separator_path=str(old_path), old_separator_sha256=counts.digest(old_path),
                      old_blocks_scanned=old['blocks_examined'], old_exact_negative_blocks=old['exact_negative_block_count'],
                      r8s1_separator_path=str(new_path), r8s1_separator_sha256=counts.digest(new_path),
                      r8s1_replay_path=str(replay_path), r8s1_replay_sha256=counts.digest(replay_path),
                      r8s1_blocks_scanned=new['blocks_scanned'], r8s1_complete_scan=new['complete_scan'],
                      r8s1_exact_negative_blocks=new['exact_negative_block_count'], fresh_exact_cuts=len(fresh),
                      rounded_counts_path=str(checked_path), rounded_counts_sha256=counts.digest(checked_path),
                      rounded_count_status=checked['status'], rounded_negative_held_cuts=checked['negative_held_cuts'])
        record['exact_count_and_held_cut_witness'] = 'induced_counts' in checked and not checked['negative_held_cuts']
        result['exact_count_witness'] |= record['exact_count_and_held_cut_witness']
        result['rounds'].append(record)
        result['cuts'] = held
        if not new['complete_scan']:
            result['status'] = 'stopped on bounded incomplete r8s1 scan; unresolved'
        elif not fresh:
            result['status'] = 'stopped with no fresh exact separator; PSD feasibility not certified'
        else:
            extra, extra_rhs = cut_matrix(fresh, active, upper, fixed)
            baseline.previous.append_rows(h, extra, extra_rhs)
            matrix = sparse.vstack([matrix, extra], format='csc')
            matrix.sort_indices()
            rhs = np.concatenate((rhs, extra_rhs))
        counts.save(output, result)
        print(json.dumps(record), flush=True)
        if not new['complete_scan'] or not fresh:
            break
        gc.collect()
    else:
        result['status'] = 'round bound reached; unresolved'
    result.update(cuts=held, peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    counts.save(output, result)
    print(json.dumps({key: result[key] for key in ('status', 'exact_count_witness', 'PSD_feasibility_certified')},
                     indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    for name in ('baseline-preparation', 'zero-closure', 'new-cuts', 'full-cache', 'output'):
        prep.add_argument('--'+name, type=Path, required=True)
    prep.add_argument('--bridge-row', type=Path)
    solve = sub.add_parser('run')
    for name in ('preparation', 'output', 'prefix'):
        solve.add_argument('--'+name, type=Path, required=True)
    solve.add_argument('--rounds', type=int, default=6)
    solve.add_argument('--seconds', type=float, default=120)
    solve.add_argument('--scan-seconds', type=float, default=180)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'prepare':
            prepare(args.baseline_preparation, args.zero_closure, args.new_cuts,
                    args.full_cache, args.output, args.bridge_row)
        else:
            run(args.preparation, args.output, args.prefix, args.rounds, args.seconds, args.scan_seconds)
