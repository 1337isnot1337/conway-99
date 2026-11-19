"""Bounded prism-zero count separation with the complete r6,s2 family.

Rebuild the frozen 25-cut parent, append independently reconstructed seed
forms and the proved edge-component inequality, then separate optimal
numerical proposals with three fixed moment families. Only exact integer
cuts enter the model. Numerical infeasibility and a scan without a cut
are not mathematical feasibility or infeasibility certificates.
"""

import argparse
from functools import reduce
import gc
import json
from math import gcd, isfinite
from pathlib import Path
import resource
from threading import Timer
import time

import highspy
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits

import grid_free_order10_prism_zero_moments_loop as parent
import grid_free_order10_r6s2_point_scan as family


ROOT = Path(__file__).resolve().parents[2]
COUNTS = parent.counts
BASE = parent.baseline
PARENT_SHA = 'a65dc6b31ebebe7bcd14398f685537f642081a7517c2e0ec94eb96246ad6e473'
PARENT_PREPARATION_SHA = 'fce82618e5beef610d70fadbf7b0e5d955a43496c05c3621b78ee270ff87c820'
PARENT_MODEL_SHA = '62664e9c7d7fd5abe9ca61585e10f0d3714bbd72509dca0e7a54d725cbd5943e'
SEED_SHA = '839b2de78eb081edbf6e39c1f0085f5f1d56ee787a7eed58ec39cb41c0fb3708'
SEED_PROOF_SHA = '286bd12ea30bee3825c97507fb5781f3ec36396eb580fc0c5ec58772c660b550'
SEED_POINT_SHA = '3f75ad72024829c91995f3b22d50f89cd709af6b6d9d3b0806c5ee05f3097326'
EDGE_CERTIFICATE = ROOT/'experiments/logs/root-prism-free/edge-components-certificate.json'
EDGE_SHA = '42e75f205c0e2b9d4a0e18c8f8b2e075b79059629b2555a10cc6251b0c3678ce'


def dependencies():
    names = ['grid_free_order10_prism_zero_moments_loop.py',
             'grid_free_order10_r6s2_point_scan.py',
             'grid_free_order10_r6s2.py', 'grid_free_order10_r6s2_scan.py',
             'grid_free_order10_r6s2_fresh_replay.py',
             'grid_free_order10_r6s2_independent_audit.py',
             'root_prism_free_edge_components.py']
    return {name: COUNTS.digest(Path(__file__).with_name(name)) for name in names}


def seed_rows(certificate, proof_path, raw, scale):
    assert COUNTS.digest(certificate) == SEED_SHA
    assert COUNTS.digest(proof_path) == SEED_PROOF_SHA
    saved = json.loads(certificate.read_text())
    proof = json.loads(proof_path.read_text())
    assert saved['exact_negative_blocks'] == saved['unique_induced_count_cut_count'] == 18
    assert saved['complete_selected_subfamily_scan'] and not saved['timed_out']
    assert proof['complete'] and proof['completed_block_count'] == 18
    assert proof['completed_supported_entries'] == 374505
    assert proof['certificate_sha256'] == SEED_SHA
    assert {b['root_type'] for b in proof['completed_blocks']} == {
        b['root_type'] for b in saved['negative_blocks']}
    assert proof['source_sha256'] == COUNTS.digest(Path(__file__).with_name('grid_free_order10_r6s2_fresh_replay.py'))
    assert proof['oracle_source_sha256'] == COUNTS.digest(Path(__file__).with_name('grid_free_order10_r6s2_independent_audit.py'))
    point_path = Path(saved['witness_path'])
    assert COUNTS.digest(point_path) == saved['witness_sha256'] == SEED_POINT_SHA
    point = json.loads(point_path.read_text())
    ordinary, induced = point['rounded_core_values'], point['induced_counts']
    assert len(ordinary) == 550 and len(induced) == 48965
    result, controls = [], []
    for index, cut in enumerate(saved['unique_induced_count_cuts']):
        row = np.zeros(550, dtype=object)
        terms = cut['terms']
        assert all(type(i) is int and type(c) is int and c != 0 for i, c in terms)
        for graph, coefficient in terms:
            row += coefficient*raw[graph].astype(object)
        common = reduce(gcd, (abs(int(c)) for c in row), 0)
        assert common > 0
        coefficients = [int(c)//common for c in row]
        induced_value = sum(c*induced[i] for i, c in terms)
        core_value = sum(c*x for c, x in zip(coefficients, ordinary))
        assert induced_value == cut['exact_value_at_witness'] < 0
        assert common*core_value == scale*induced_value and core_value < 0
        result.append({'coefficients': coefficients,
                       'origin': {'kind': 'independently reconstructed r6s2 seed',
                                  'cut_index': index, 'certificate_path': str(certificate),
                                  'certificate_sha256': SEED_SHA,
                                  'fresh_product_proof_sha256': SEED_PROOF_SHA}})
        controls.append({'seed_index': index, 'induced_terms': len(terms),
                         'raw_core_form_gcd': common, 'reduction_scale': scale,
                         'exact_induced_value': induced_value, 'exact_core_value': core_value,
                         'core_form_nonzero_coordinates': sum(c != 0 for c in coefficients)})
    assert COUNTS.digest(EDGE_CERTIFICATE) == EDGE_SHA
    edge = json.loads(EDGE_CERTIFICATE.read_text())
    assert edge['source_sha256'] == COUNTS.digest(Path(__file__).with_name('root_prism_free_edge_components.py'))
    terms = edge['count_forms']['unconditional_nonnegative_row']
    assert terms == [[0, 4158], [1, -3], [521, -2]]
    coefficients = [0]*550
    for i, c in terms:
        coefficients[i] = c
    result.append({'coefficients': coefficients,
                   'origin': {'kind': 'unconditional edge-component inequality',
                              'certificate_path': str(EDGE_CERTIFICATE),
                              'certificate_sha256': EDGE_SHA}})
    return result, controls


def assemble(parent_preparation, seed_certificate, seed_proof, family_cache, x521_zero):
    assert COUNTS.digest(Path(parent.__file__)) == PARENT_SHA
    assert COUNTS.digest(parent_preparation) == PARENT_PREPARATION_SHA
    saved = json.loads(parent_preparation.read_text())
    assert saved['source_sha256'] == PARENT_SHA and saved['dependency_hashes'] == parent.dependencies()
    paths = {key: Path(value) for key, value in saved['inputs'].items()}
    for key, path in paths.items():
        assert COUNTS.digest(path) == saved['input_hashes'][key]
    data, scale, raw, metadata, numeric, held, r8, _ = parent.model(**paths)
    assert metadata == saved['model'] and held == saved['initial_cuts']
    assert metadata['numerical_model_sha256'] == PARENT_MODEL_SHA and len(held) == 25
    matrix, rhs, lower, column_upper, fixed, upper = numeric
    active = metadata['active_core_coordinates']
    zeros = set(metadata['prism_zero_core_coordinates'])
    assert len(zeros) == 58 and 521 not in zeros
    if x521_zero:
        column_upper = column_upper.copy()
        assert column_upper[active.index(521)] == 1
        column_upper[active.index(521)] = 0
        zeros.add(521)
    cache = json.loads(family_cache.read_text())
    assert cache['point_independent_tensors'] and not cache['root_or_flag_zero_pruning']
    assert cache['covers_full62_family'] and cache['cached_root_count'] == 62
    assert cache['all_cached_root_types'] == data[1][6]
    r6 = family.FullScanner(data, raw, scale, family_cache, parent.REDUCTION_SHA)
    extra, controls = seed_rows(seed_certificate, seed_proof, raw, scale)
    known = {tuple(item['coefficients']) for item in held}
    distinct = []
    for item in extra:
        key = tuple(item['coefficients'])
        if key not in known:
            known.add(key)
            distinct.append(item)
    added, added_rhs = parent.cut_matrix(distinct, active, upper, fixed)
    matrix = sparse.vstack([matrix, added], format='csc')
    matrix.sort_indices()
    rhs = np.concatenate((rhs, added_rhs))
    held = held+distinct
    report = {'parent_numerical_model_sha256': PARENT_MODEL_SHA,
              'rows': matrix.shape[0], 'columns': matrix.shape[1], 'nonzeros': int(matrix.nnz),
              'free_columns': int(sum(column_upper > 0)), 'x521_zero': bool(x521_zero),
              'required_zero_coordinates': sorted(zeros), 'active_core_coordinates': active,
              'old_linear_cuts': 25, 'reconstructed_r6_induced_cuts': 18,
              'appended_distinct_core_rows': len(distinct), 'initial_cut_count': len(held),
              'initial_cut_coefficients_sha256': parent.vector_hash(held),
              'numerical_model_sha256': BASE.numerical_model_hash(matrix, rhs, lower, column_upper),
              'positive_DP_bounds_and_scalings_unchanged': True,
              'unconditional_edge_component_row_included': True,
              'full_r6s2_roots': 62, 'full_r8s1_roots': 916, 'old_family_blocks': 1416,
              'root_or_flag_pruning_at_seed_point': False,
              'seed_reduction_controls': controls, 'reduced_cache_sha256': parent.REDUCTION_SHA,
              'objective': 'zero; pure feasibility'}
    return {'data': data, 'scale': scale, 'raw': raw, 'report': report,
            'matrix': matrix, 'rhs': rhs, 'lower': lower, 'column_upper': column_upper,
            'fixed': fixed, 'upper': upper, 'held': held, 'r8': r8, 'r6': r6}


def prepare(paths, x521_zero, output):
    assert not output.exists()
    started = time.monotonic()
    bundle = assemble(**paths, x521_zero=x521_zero)
    h, options = BASE.supported_options(120)
    saved = {'status': 'complete-family prism-zero loop prepared; no optimizer called',
             'source_sha256': COUNTS.digest(Path(__file__)), 'dependency_hashes': dependencies(),
             'inputs': {k: str(v) for k, v in paths.items()},
             'input_hashes': {k: COUNTS.digest(v) for k, v in paths.items()},
             'x521_zero': bool(x521_zero), 'model': bundle['report'], 'initial_cuts': bundle['held'],
             'highs_version': h.version(), 'supported_options': options,
             'maximum_rounds': 6, 'maximum_solver_seconds_per_round': 120,
             'maximum_seconds_per_new_family_scan': 180, 'threads': 1,
             'stop_on_nonoptimal_or_incomplete_scan': True, 'stop_on_no_fresh_exact_cut': True,
             'dual_extraction': False, 'PSD_feasibility_certified_by_scan': False,
             'preparation_seconds': time.monotonic()-started,
             'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    COUNTS.save(output, saved)
    print(json.dumps({k: v for k, v in saved.items() if k not in ('initial_cuts', 'model')}, indent=2), flush=True)
    print(json.dumps({k: v for k, v in bundle['report'].items() if k not in
                     ('active_core_coordinates', 'required_zero_coordinates', 'seed_reduction_controls')}, indent=2), flush=True)


def proposal_record(saved, record, values, active, upper):
    ordinary = [value*upper[j] for j, value in zip(active, values)]
    assert all(isfinite(value) for value in ordinary)
    return ordinary, {'status': 'numerical proposal; exact feasibility not certified',
        'source_sha256': saved['source_sha256'], 'numerical_model_sha256': record['numerical_model_sha256'],
        'numerical_status': record['numerical_status'], 'loop_round': record['round'],
        'case_index': 1, 'fixed_order_nine_point': False, 'x521_zero': saved['x521_zero'],
        'held_cut_count': record['held_cuts'], 'held_cut_coefficients_sha256': record['held_cut_coefficients_sha256'],
        'required_zero_coordinates': saved['model']['required_zero_coordinates'],
        'real_proposal': {'active_coordinates': active, 'scaled_values': values,
                          'ordinary_core_values': ordinary, 'exact_real_feasibility_certified': False}}


def rounded_check(bundle, ordinary, held):
    report, upper = bundle['report'], bundle['upper']
    point = [0]*550
    point[0] = 1
    for coordinate, value in zip(report['active_core_coordinates'], ordinary):
        point[coordinate] = min(upper[coordinate], max(0, int(round(value))))
    for coordinate in report['required_zero_coordinates']:
        point[coordinate] = 0
    checked = COUNTS.exact_candidate(bundle['data'], bundle['scale'], bundle['raw'], point, upper, False)
    values = [sum(c*x for c, x in zip(cut['coefficients'], point)) for cut in held]
    checked.update(source_sha256=COUNTS.digest(Path(__file__)), exact_held_cut_values=values,
                   negative_held_cuts=sum(v < 0 for v in values),
                   held_cut_coefficients_sha256=parent.vector_hash(held),
                   required_zero_coordinates=report['required_zero_coordinates'],
                   required_zeros_hold=all(point[j] == 0 for j in report['required_zero_coordinates']),
                   x521_zero=report['x521_zero'], PSD_feasibility_certified=False, graph_constructed=False)
    checked['exact_count_and_held_cut_witness'] = 'induced_counts' in checked and not checked['negative_held_cuts']
    return checked


def run(preparation, output, prefix, rounds=6, seconds=120, scan_seconds=180):
    assert 1 <= rounds <= 6 and 0 < seconds <= 120 and 0 < scan_seconds <= 180
    assert not output.exists()
    saved = json.loads(preparation.read_text())
    assert saved['source_sha256'] == COUNTS.digest(Path(__file__))
    assert saved['dependency_hashes'] == dependencies()
    paths = {k: Path(v) for k, v in saved['inputs'].items()}
    for key, path in paths.items():
        assert COUNTS.digest(path) == saved['input_hashes'][key]
    bundle = assemble(**paths, x521_zero=saved['x521_zero'])
    assert bundle['report'] == saved['model'] and bundle['held'] == saved['initial_cuts']
    matrix, rhs = bundle['matrix'], bundle['rhs']
    lower, column_upper = bundle['lower'], bundle['column_upper']
    fixed, upper = bundle['fixed'], bundle['upper']
    active = saved['model']['active_core_coordinates']
    held = bundle['held']
    known = {tuple(cut['coefficients']) for cut in held}
    h, options = BASE.supported_options(seconds)
    assert h.version() == saved['highs_version']
    h.HandleUserInterrupt = True
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = matrix.shape[1], matrix.shape[0]
    lp.col_cost_, lp.col_lower_, lp.col_upper_ = np.zeros(matrix.shape[1]), lower, column_upper
    lp.row_lower_, lp.row_upper_ = np.full(matrix.shape[0], -highspy.kHighsInf), rhs
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = matrix.indptr, matrix.indices, matrix.data
    assert h.passModel(lp) == highspy.HighsStatus.kOk
    result = {'status': 'running bounded complete-family prism-zero count loop',
              'source_sha256': saved['source_sha256'], 'preparation_sha256': COUNTS.digest(preparation),
              'maximum_rounds': rounds, 'solver_seconds_per_round': seconds,
              'new_family_scan_seconds': scan_seconds, 'threads': 1, 'options': options,
              'x521_zero': saved['x521_zero'], 'rounds': [], 'cuts': held,
              'exact_count_witness': False, 'exact_infeasibility_certificate': False,
              'PSD_feasibility_certified': False, 'graph_constructed': False}
    COUNTS.save(output, result)
    for index in range(rounds):
        stem = prefix.with_name(prefix.name+f'-round{index}')
        record = {'round': index, 'rows': matrix.shape[0], 'nonzeros': int(matrix.nnz),
                  'held_cuts': len(held), 'held_cut_coefficients_sha256': parent.vector_hash(held),
                  'numerical_model_sha256': BASE.numerical_model_hash(matrix, rhs, lower, column_upper)}
        print(json.dumps({'starting_round': index, 'rows': matrix.shape[0], 'held_cuts': len(held)}), flush=True)
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
        returned = BASE.returned_data(h)
        returned.update(source_sha256=saved['source_sha256'], loop_round=index,
                        numerical_model_sha256=record['numerical_model_sha256'], numerical_status=str(status))
        raw_path = stem.with_name(stem.name+'-solver-data.json.gz')
        parent.raw_save(raw_path, returned)
        record.update(returned_data_path=str(raw_path), returned_data_sha256=COUNTS.digest(raw_path),
                      returned_value_valid=returned['value_valid'], returned_dual_valid=returned['dual_valid'],
                      solver_info=returned['info'])
        values = returned['column_values']
        proposal_path = stem.with_name(stem.name+'-proposal.json')
        if returned['value_valid'] and len(values) == len(active) and all(type(v) is float and isfinite(v) for v in values):
            ordinary, proposal = proposal_record(saved, record, values, active, upper)
            proposal['preparation_sha256'] = COUNTS.digest(preparation)
            COUNTS.save(proposal_path, proposal)
            record.update(proposal_path=str(proposal_path), proposal_sha256=COUNTS.digest(proposal_path))
        if status != highspy.HighsModelStatus.kOptimal:
            result['status'] = 'stopped on numerical solver status; no exact infeasibility conclusion'
            record['proposal_scans'] = 'not run after nonoptimal status'
            result['rounds'].append(record)
            COUNTS.save(output, result)
            break
        assert 'proposal_sha256' in record
        scans, fresh, duplicate_violations = [], [], []
        specifications = [('old1416', parent.old_separator, 'unique_integer_cuts'),
                          ('r8s1', bundle['r8'], 'unique_core_cuts'),
                          ('r6s2', bundle['r6'], 'unique_core_cuts')]
        for name, scanner, key in specifications:
            path = stem.with_name(stem.name+f'-{name}-separation.json')
            separated = scanner.scan(proposal_path, path) if name == 'old1416' else scanner.scan(proposal_path, path, scan_seconds)
            replay = scanner.replay(path)
            replay_path = stem.with_name(stem.name+f'-{name}-replay.json')
            COUNTS.save(replay_path, replay)
            complete = separated['blocks_examined'] == 1416 if name == 'old1416' else separated['complete_scan']
            scans.append({'family': name, 'certificate_path': str(path), 'certificate_sha256': COUNTS.digest(path),
                          'replay_path': str(replay_path), 'replay_sha256': COUNTS.digest(replay_path),
                          'complete_scan': complete,
                          'blocks_scanned': separated['blocks_examined'] if name == 'old1416' else separated['blocks_scanned'],
                          'exact_negative_blocks': separated['exact_negative_block_count'],
                          'unique_integer_cuts': len(separated[key])})
            for cut_index, cut in enumerate(separated[key]):
                assert cut['exact_value_at_proposal'][0] < 0
                coefficients = cut['coefficients']+([0]*492 if name == 'old1416' else [])
                assert len(coefficients) == 550 and all(type(c) is int for c in coefficients)
                vector = tuple(coefficients)
                if vector in known:
                    duplicate_violations.append({'family': name, 'cut_index': cut_index})
                    continue
                known.add(vector)
                fresh.append({'coefficients': coefficients,
                              'origin': {'kind': 'exact '+name+' separator', 'round': index,
                                         'cut_index': cut_index, 'certificate_path': str(path),
                                         'certificate_sha256': COUNTS.digest(path)}})
        held.extend(fresh)
        record.update(scans=scans, fresh_exact_cuts=len(fresh), duplicate_exact_separators=duplicate_violations)
        complete = all(scan['complete_scan'] for scan in scans)
        if complete and not fresh:
            checked = rounded_check(bundle, ordinary, held)
            checked_path = stem.with_name(stem.name+'-rounded-counts.json')
            COUNTS.save(checked_path, checked)
            record.update(rounded_counts_path=str(checked_path), rounded_counts_sha256=COUNTS.digest(checked_path),
                          rounded_count_status=checked['status'],
                          exact_count_and_held_cut_witness=checked['exact_count_and_held_cut_witness'])
            result['exact_count_witness'] |= checked['exact_count_and_held_cut_witness']
        result['rounds'].append(record)
        result['cuts'] = held
        if not complete:
            result['status'] = 'stopped on incomplete bounded moment scan; unresolved'
        elif not fresh:
            result['status'] = 'stopped with no fresh exact separator; PSD not certified'
        else:
            added, added_rhs = parent.cut_matrix(fresh, active, upper, fixed)
            BASE.previous.append_rows(h, added, added_rhs)
            matrix = sparse.vstack([matrix, added], format='csc')
            matrix.sort_indices()
            rhs = np.concatenate((rhs, added_rhs))
        COUNTS.save(output, result)
        print(json.dumps(record), flush=True)
        if not complete or not fresh:
            break
        gc.collect()
    else:
        result['status'] = 'round bound reached; unresolved'
    result.update(cuts=held, peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    COUNTS.save(output, result)
    print(json.dumps({k: result[k] for k in ('status', 'exact_count_witness', 'exact_infeasibility_certificate')}, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    for name in ('parent-preparation', 'seed-certificate', 'seed-proof', 'family-cache', 'output'):
        prep.add_argument('--'+name, type=Path, required=True)
    prep.add_argument('--x521-zero', action='store_true')
    solve = sub.add_parser('run')
    for name in ('preparation', 'output', 'prefix'):
        solve.add_argument('--'+name, type=Path, required=True)
    solve.add_argument('--rounds', type=int, default=6)
    solve.add_argument('--seconds', type=float, default=120)
    solve.add_argument('--scan-seconds', type=float, default=180)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'prepare':
            paths = {name: getattr(args, name).resolve() for name in
                     ('parent_preparation', 'seed_certificate', 'seed_proof', 'family_cache')}
            prepare(paths, args.x521_zero, args.output.resolve())
        else:
            run(args.preparation.resolve(), args.output.resolve(), args.prefix.resolve(),
                args.rounds, args.seconds, args.scan_seconds)
