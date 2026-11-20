"""Bounded count/PSD cutting-plane search, with exact integer separators only.

Preparation performs no optimization. A run has at most six sequential
30-second single-thread LP rounds. Every numerical proposal and exact
separator certificate is retained. No dual extraction is performed here.
"""

import argparse
import gc
import hashlib
import json
from pathlib import Path
import resource
from threading import Timer
import time

import highspy
import numpy as np
from scipy import sparse
from threadpoolctl import threadpool_limits

import grid_free_order10_moments as separator
import grid_free_order10_scaled as counts
import grid_free_order10_scaled_cut as count_cut


FINDER_SHA = '12409f5ea1932d549cb69d9ca83e8cd4bd53d173b1a6ef136f9cdee6c095fc16'
SEPARATOR_SHA = '4c6886bd8d5dffa711aa20991af3bb87495262bd01d8227d2f64caac0040bbae'
CUT_SHA = 'd656c4b104c683aa2b313c41f44a7e3f83b071632b772c8163c5523882ac243c'


def initial_cuts(moment_certificate, universal_certificate):
    assert counts.digest(Path(separator.__file__)) == SEPARATOR_SHA
    assert counts.digest(Path(count_cut.__file__)) == CUT_SHA
    separator.replay(moment_certificate)
    count_cut.replay(universal_certificate)
    moments = json.loads(moment_certificate.read_text())
    universal = json.loads(universal_certificate.read_text())
    cuts = [{'coefficients': item['coefficients'],
             'origin': {'kind': 'initial exact PSD separator', 'cut_index': i,
                        'certificate_sha256': counts.digest(moment_certificate)}}
            for i, item in enumerate(moments['unique_integer_cuts'])]
    assert len(cuts) == 4
    chosen = universal[universal['selected_cut']]
    assert not chosen['new_positive_coefficients_eliminated_by_bounds']
    cuts.append({'coefficients': chosen['primitive_integer_old_cut'],
                 'origin': {'kind': 'universal order-ten count cut',
                            'certificate_sha256': counts.digest(universal_certificate)}})
    assert len({tuple(c['coefficients']) for c in cuts}) == 5
    assert all(len(c['coefficients']) == 58 and all(type(v) is int for v in c['coefficients']) for c in cuts)
    return cuts


def cut_matrix(cuts, active, upper, fixed):
    position = {j: i for i, j in enumerate(active)}
    values, columns, starts, rhs = [], [], [0], []
    for item in cuts:
        row = item['coefficients']
        assert len(row) == 58
        constant = sum(row[i]*v for i, v in fixed.items() if i < 58)
        terms = [(position[j], row[j]*upper[j]) for j in range(1, 58)
                 if j in position and row[j]]
        scale = max([abs(constant)]+[abs(v) for _, v in terms])
        assert scale > 0 and terms
        for j, value in terms:
            columns.append(j)
            values.append(-value/scale)
        starts.append(len(values))
        rhs.append(constant/scale)
    matrix = sparse.csr_matrix((np.array(values), np.array(columns, dtype=np.int32),
                                np.array(starts, dtype=np.int32)), shape=(len(cuts), len(active)))
    assert np.all(np.isfinite(matrix.data)) and np.all(np.isfinite(rhs))
    return matrix, np.array(rhs)


def load_base(cache, preparation):
    assert counts.digest(Path(counts.__file__)) == FINDER_SHA
    saved = json.loads(preparation.read_text())
    assert saved['source_sha256'] == FINDER_SHA
    assert counts.digest(cache) == saved['reduced_cache_sha256']
    data, cores, scale, coefficients = counts.load_reduced(cache)
    bounds = counts.bounds_for(data, cores)
    assert bounds == saved['upper_bounds']
    metadata, numeric = counts.make_model(coefficients, bounds, False)
    assert metadata == saved['cases'][1] and numeric is not None
    assert not metadata['forced_zero_coordinates']
    return data, scale, coefficients, metadata, numeric


def prepare(cache, base_preparation, moments, universal, output):
    started = time.monotonic()
    seed = initial_cuts(moments, universal)
    _, _, coefficients, metadata, numeric = load_base(cache, base_preparation)
    A, b, fixed, upper = numeric
    extra, rhs = cut_matrix(seed, metadata['active_core_coordinates'], upper, fixed)
    result = {
        'status': 'bounded cutting-plane model prepared; no optimization run',
        'source_sha256': counts.digest(Path(__file__)),
        'dependency_hashes': {'grid_free_order10_scaled.py': FINDER_SHA,
                              'grid_free_order10_moments.py': SEPARATOR_SHA,
                              'grid_free_order10_scaled_cut.py': CUT_SHA},
        'inputs': {'reduced_cache': str(cache), 'base_preparation': str(base_preparation),
                   'moment_certificate': str(moments), 'universal_certificate': str(universal)},
        'input_hashes': {'reduced_cache': counts.digest(cache),
                         'base_preparation': counts.digest(base_preparation),
                         'moment_certificate': counts.digest(moments),
                         'universal_certificate': counts.digest(universal)},
        'base_rows': A.shape[0], 'variables': A.shape[1], 'base_nonzeros': int(A.nnz),
        'initial_cuts': seed, 'additional_rows': len(seed), 'additional_nonzeros': int(extra.nnz),
        'smallest_added_normalized_coefficient': float(np.min(np.abs(extra.data))),
        'initial_total_rows': A.shape[0]+len(seed), 'initial_total_nonzeros': int(A.nnz+extra.nnz),
        'fixed_coordinates': sorted(fixed.items()),
        'maximum_rounds': 6, 'maximum_solver_seconds_per_round': 30,
        'threads': 1, 'objective': 'pure feasibility',
        'basis_reuse': 'same highspy instance; append exact necessary cuts between rounds',
        'dual_extraction': False, 'preparation_seconds': time.monotonic()-started,
        'peak_process_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
    }
    counts.save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'initial_cuts'}, indent=2), flush=True)
    return result


def append_rows(h, matrix, rhs):
    status = h.addRows(matrix.shape[0], np.full(matrix.shape[0], -highspy.kHighsInf), rhs,
                       matrix.nnz, matrix.indptr, matrix.indices, matrix.data)
    assert status == highspy.HighsStatus.kOk


def run(preparation, output, prefix, rounds, seconds, extension_audit=None):
    prepared = json.loads(preparation.read_text())
    assert prepared['source_sha256'] == counts.digest(Path(__file__))
    for name, expected in prepared['dependency_hashes'].items():
        assert counts.digest(Path(__file__).with_name(name)) == expected
    paths = {name: Path(value) for name, value in prepared['inputs'].items()}
    for name, path in paths.items():
        assert counts.digest(path) == prepared['input_hashes'][name]
    seed = initial_cuts(paths['moment_certificate'], paths['universal_certificate'])
    assert seed == prepared['initial_cuts']
    data, scale, coefficients, metadata, numeric = load_base(paths['reduced_cache'], paths['base_preparation'])
    A, b, fixed, upper = numeric
    A = A.tocsc()
    h = highspy.Highs()
    h.setOptionValue('output_flag', False)
    h.setOptionValue('threads', 1)
    h.setOptionValue('presolve', 'on')
    h.setOptionValue('solver', 'simplex')
    h.HandleUserInterrupt = True
    lp = highspy.HighsLp()
    lp.num_col_, lp.num_row_ = A.shape[1], A.shape[0]
    lp.col_cost_ = np.zeros(A.shape[1])
    lp.col_lower_ = np.zeros(A.shape[1])
    lp.col_upper_ = np.ones(A.shape[1])
    lp.row_lower_ = np.full(A.shape[0], -highspy.kHighsInf)
    lp.row_upper_ = b
    lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
    lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = A.indptr, A.indices, A.data
    assert h.passModel(lp) == highspy.HighsStatus.kOk
    extra, rhs = cut_matrix(seed, metadata['active_core_coordinates'], upper, fixed)
    append_rows(h, extra, rhs)
    held = list(seed)
    known = {tuple(c['coefficients']) for c in held}
    result = {'status': 'running bounded exact-separator loop',
              'source_sha256': prepared['source_sha256'],
              'preparation_sha256': counts.digest(preparation),
              'max_rounds': rounds, 'solver_seconds_per_round': seconds,
              'threads': 1, 'fixed_order_nine_point': False,
              'initial_cuts': len(seed), 'cuts': held, 'rounds': [],
              'exact_count_witness': False, 'PSD_feasibility_certified': False,
              'dual_extraction_performed': False}
    if extension_audit:
        result['extension_audit'] = str(extension_audit)
        result['extension_audit_sha256'] = counts.digest(extension_audit)
    counts.save(output, result)
    for round_index in range(rounds):
        record = {'round': round_index, 'held_cuts': len(held),
                  'rows': A.shape[0]+len(held)}
        print(json.dumps({'starting_round': round_index, 'held_cuts': len(held)}), flush=True)
        h.setOptionValue('time_limit', h.getRunTime()+seconds)
        started = time.monotonic()
        timer = Timer(seconds, h.cancelSolve)
        timer.start()
        try:
            h.run()
        finally:
            timer.cancel()
        status = h.getModelStatus()
        record.update(numerical_status=str(status), solver_seconds=time.monotonic()-started)
        info = h.getInfo()
        record['simplex_iterations'] = int(info.simplex_iteration_count)
        if status != highspy.HighsModelStatus.kOptimal:
            result['status'] = 'stopped on numerical solver status; no exact infeasibility conclusion'
            result['rounds'].append(record)
            counts.save(output, result)
            print(json.dumps(record), flush=True)
            break
        z = [float(v) for v in h.getSolution().col_value]
        assert len(z) == len(metadata['active_core_coordinates'])
        values = [float(v)*upper[i] for i, v in zip(metadata['active_core_coordinates'], z)]
        proposal_path = prefix.with_name(prefix.name+f'-round{round_index}-proposal.json')
        separation_path = prefix.with_name(prefix.name+f'-round{round_index}-separation.json')
        proposal = {'status': 'numerical count/cut proposal; exact feasibility not certified',
                    'source_sha256': prepared['source_sha256'], 'preparation_sha256': counts.digest(preparation),
                    'loop_round': round_index, 'case_index': 1, 'fixed_order_nine_point': False,
                    'held_cut_count': len(held),
                    'held_cut_coefficients_sha256': hashlib.sha256(
                        json.dumps([c['coefficients'] for c in held], separators=(',', ':')).encode()).hexdigest(),
                    'real_proposal': {'active_coordinates': metadata['active_core_coordinates'],
                                      'scaled_values': z, 'ordinary_core_values': values,
                                      'exact_real_feasibility_certified': False}}
        counts.save(proposal_path, proposal)
        separated = separator.scan(proposal_path, separation_path)
        fresh = []
        for ci, cut in enumerate(separated['unique_integer_cuts']):
            key = tuple(cut['coefficients'])
            assert cut['exact_value_at_proposal'][0] < 0
            if key not in known:
                known.add(key)
                fresh.append({'coefficients': cut['coefficients'],
                              'origin': {'kind': 'exact PSD separator', 'round': round_index,
                                         'cut_index': ci, 'certificate_path': str(separation_path),
                                         'certificate_sha256': counts.digest(separation_path)}})
        record.update(proposal_path=str(proposal_path), proposal_sha256=counts.digest(proposal_path),
                      separator_path=str(separation_path), separator_sha256=counts.digest(separation_path),
                      exact_negative_blocks=separated['exact_negative_block_count'],
                      exact_separator_count=separated['unique_integer_cut_count'],
                      fresh_cuts=len(fresh))
        result['rounds'].append(record)
        if not fresh:
            result['status'] = 'stopped with no fresh exact PSD separator; feasibility not certified'
            if not separated['unique_integer_cuts']:
                point = [0]*550
                for i, value in fixed.items():
                    point[i] = value
                for i, value in zip(metadata['active_core_coordinates'], values):
                    point[i] = min(upper[i], max(0, int(round(value))))
                result['final_rounded_count_check'] = counts.exact_candidate(
                    data, scale, coefficients, point, upper, False)
                result['exact_count_witness'] = 'induced_counts' in result['final_rounded_count_check']
            counts.save(output, result)
            print(json.dumps(record), flush=True)
            break
        held.extend(fresh)
        extra, rhs = cut_matrix(fresh, metadata['active_core_coordinates'], upper, fixed)
        append_rows(h, extra, rhs)
        result['cuts'] = held
        counts.save(output, result)
        print(json.dumps(record), flush=True)
        gc.collect()
    else:
        result['status'] = 'round bound reached; unresolved'
    result['cuts'] = held
    result['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    counts.save(output, result)
    print(json.dumps({'status': result['status'], 'rounds': len(result['rounds']),
                      'held_cuts': len(held), 'exact_count_witness': result['exact_count_witness'],
                      'PSD_feasibility_certified': False}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    for name in ('cache', 'base-preparation', 'moments', 'universal', 'output'):
        prep.add_argument('--'+name, type=Path, required=True)
    solve = sub.add_parser('run')
    for name in ('preparation', 'output', 'prefix'):
        solve.add_argument('--'+name, type=Path, required=True)
    solve.add_argument('--extension-audit', type=Path)
    solve.add_argument('--rounds', type=int, default=6)
    solve.add_argument('--seconds', type=float, default=30)
    args = parser.parse_args()
    with threadpool_limits(limits=1):
        if args.command == 'prepare':
            prepare(args.cache, args.base_preparation, args.moments, args.universal, args.output)
        else:
            assert 1 <= args.rounds <= 6 and 0 < args.seconds <= 30
            run(args.preparation, args.output, args.prefix, args.rounds, args.seconds, args.extension_audit)
