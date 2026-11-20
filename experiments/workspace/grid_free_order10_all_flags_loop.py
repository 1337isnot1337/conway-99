"""Continue exact count separation with all four frozen moment families.

The 48 seeds are the previous 47 inequalities and one independently
reconstructed four-cycle-root inequality. The optional x521-zero face
changes only its variable upper bound. A numerical status or a complete
scan without a separator is not a mathematical existence conclusion.
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

import grid_free_order10_r6s2_loop as previous
import grid_free_order10_higher_flags_point_scan as higher


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
parent, COUNTS, BASE = previous.parent, previous.COUNTS, previous.BASE
PREVIOUS_SHA = '40838c0949db789308008a777b3c5433c47f27f2cc0229d2357775102f345933'
HIGHER_SHA = '5d1af5a24c9a509e35b9aeb47e47bd97eb01c09eb51fad32c2a72ceb87075c86'
INPUTS = {
    'prior_preparation': LOGS/'prism-zero-order10-r6s2-loop-preparation.json',
    'prior_loop': LOGS/'prism-zero-order10-r6s2-loop01.json',
    'prior_cut_certificate': LOGS/'prism-zero-order10-r6s2-loop01-round0-r6s2-separation.json',
    'prior_cut_replay': LOGS/'prism-zero-order10-r6s2-new-cuts-independent-replay.json',
    'higher_cut_certificate': LOGS/'order10-higher-flags-r4s3-scan.json',
    'higher_cut_replay': LOGS/'order10-higher-flags-r4s3-fresh-replay.json',
    'higher_cache': LOGS/'order10-higher-flags-full-cache.json',
}
INPUT_HASHES = {
    'prior_preparation': '916f3112831e781eadc55c107331f08db7fbfdee4a9f93df916ebb2e9be1c5fa',
    'prior_loop': '08366598ad71e2942e1cd1ea877616bd85c636f87a2c607e991834016a61644b',
    'prior_cut_certificate': 'fccbd4eeebba92b34f1f1fe69343633a59562f3e32817fc839aa29c490b65c19',
    'prior_cut_replay': 'c3be5a6bf23cbf2e81badf6d8ec176f6eb87182cbb8b8856acaa311e9dfa553d',
    'higher_cut_certificate': 'c70c9efc5588e0c15b9899770a137b37937f2037456f02e6b58077bb6165bcab',
    'higher_cut_replay': '0a6a50182903345149d9d6c61df745bb175bdeeb28bcd5bf0ba4cefa83c32802',
    'higher_cache': 'b5c076fabeee3d88c89f738bdd7f746bab9a8071acee0632dbe37137eddc47b8',
}


def dependencies():
    assert COUNTS.digest(Path(previous.__file__)) == PREVIOUS_SHA
    assert COUNTS.digest(Path(higher.__file__)) == HIGHER_SHA
    result = previous.dependencies()
    result.update({Path(previous.__file__).name: PREVIOUS_SHA,
                   Path(higher.__file__).name: HIGHER_SHA})
    for name in ('grid_free_order10_r6s2_new_cuts_replay.py',
                 'grid_free_order10_higher_flags_fresh_replay.py',
                 'grid_free_order10_higher_flags_products.py'):
        result[name] = COUNTS.digest(Path(__file__).with_name(name))
    return result


def reduce_induced(terms, raw, scale):
    assert terms and all(type(i) is int and type(c) is int and c for i, c in terms)
    assert len({i for i, _ in terms}) == len(terms)
    values = [sum(c*int(raw[i, j]) for i, c in terms) for j in range(550)]
    assert all(value % scale == 0 for value in values)
    values = [value//scale for value in values]
    divisor = reduce(gcd, map(abs, values), 0)
    assert divisor > 0
    return [value//divisor for value in values], divisor


def assemble(prior_preparation, prior_loop, prior_cut_certificate, prior_cut_replay,
             higher_cut_certificate, higher_cut_replay, higher_cache, x521_zero):
    dependencies()
    paths = dict(prior_preparation=prior_preparation, prior_loop=prior_loop,
                 prior_cut_certificate=prior_cut_certificate, prior_cut_replay=prior_cut_replay,
                 higher_cut_certificate=higher_cut_certificate, higher_cut_replay=higher_cut_replay,
                 higher_cache=higher_cache)
    assert set(paths) == set(INPUT_HASHES)
    for name, path in paths.items():
        assert COUNTS.digest(path) == INPUT_HASHES[name], name
    prepared = json.loads(prior_preparation.read_text())
    assert prepared['source_sha256'] == PREVIOUS_SHA and not prepared['x521_zero']
    assert prepared['dependency_hashes'] == previous.dependencies()
    old_paths = {name: Path(value) for name, value in prepared['inputs'].items()}
    for name, path in old_paths.items():
        assert COUNTS.digest(path) == prepared['input_hashes'][name]
    bundle = previous.assemble(**old_paths, x521_zero=False)
    assert bundle['report'] == prepared['model'] and bundle['held'] == prepared['initial_cuts']
    assert len(bundle['held']) == 44
    old_report = dict(bundle['report'])
    raw, scale = bundle['raw'], bundle['scale']
    loop = json.loads(prior_loop.read_text())
    assert loop['source_sha256'] == PREVIOUS_SHA and len(loop['cuts']) == 47
    assert [x['coefficients'] for x in loop['cuts'][:44]] == [x['coefficients'] for x in bundle['held']]
    old_certificate, old_proof = json.loads(prior_cut_certificate.read_text()), json.loads(prior_cut_replay.read_text())
    assert old_proof['complete'] and old_proof['products_reconstructed'] == 15979
    assert old_proof['source_sha256'] == COUNTS.digest(Path(__file__).with_name('grid_free_order10_r6s2_new_cuts_replay.py'))
    assert old_proof['input_sha256'][str(prior_cut_certificate)] == INPUT_HASHES['prior_cut_certificate']
    assert len(old_certificate['negative_blocks']) == len(old_certificate['unique_core_cuts']) == 3
    extra, controls = [], []
    for block in old_certificate['negative_blocks']:
        index = block['core_cut_index']
        coefficients, divisor = reduce_induced(block['primitive_induced_count_form'], raw, scale)
        assert divisor == block['core_form_gcd']
        assert coefficients == old_certificate['unique_core_cuts'][index]['coefficients']
        assert coefficients == loop['cuts'][44+index]['coefficients']
        value = sum(c*x for c, x in zip(coefficients, old_certificate['point_numerators']))
        assert value*divisor == block['primitive_induced_numerator'] < 0
        extra.append(loop['cuts'][44+index])
        controls.append({'family': 'r6s2', 'root_type': block['root_type'],
                         'positive_reduction_gcd': divisor, 'exact_core_numerator': value})
    certificate, proof = json.loads(higher_cut_certificate.read_text()), json.loads(higher_cut_replay.read_text())
    assert proof['complete'] and proof['completed_supported_entries'] == 78
    assert proof['certificate_sha256'] == INPUT_HASHES['higher_cut_certificate']
    assert proof['source_sha256'] == COUNTS.digest(Path(__file__).with_name('grid_free_order10_higher_flags_fresh_replay.py'))
    assert certificate['complete_generation'] and certificate['complete_full_family_scan']
    assert len(certificate['unique_induced_count_cuts']) == 1
    witness_path = Path(certificate['witness_path'])
    assert COUNTS.digest(witness_path) == certificate['witness_sha256'] == proof['witness_sha256']
    witness = json.loads(witness_path.read_text())
    assert witness['exact_count_and_held_cut_witness'] and witness['held_cut_count'] == 47
    cut = certificate['unique_induced_count_cuts'][0]
    terms = cut['terms']
    coefficients, divisor = reduce_induced(terms, raw, scale)
    induced_value = sum(c*witness['induced_counts'][i] for i, c in terms)
    core_value = sum(c*x for c, x in zip(coefficients, witness['rounded_core_values']))
    assert induced_value == cut['exact_value_at_witness'] == -101639192
    assert core_value*divisor == induced_value < 0
    extra.append({'coefficients': coefficients,
                  'origin': {'kind': 'independently reconstructed four-cycle flag separator',
                             'certificate_path': str(higher_cut_certificate),
                             'certificate_sha256': INPUT_HASHES['higher_cut_certificate'],
                             'independent_replay_sha256': INPUT_HASHES['higher_cut_replay']}})
    controls.append({'family': 'r4s3', 'root_type': 16, 'induced_terms': len(terms),
                     'positive_reduction_gcd': divisor, 'exact_core_value': core_value,
                     'exact_induced_value': induced_value})
    held = bundle['held']+extra
    assert len(held) == len({tuple(item['coefficients']) for item in held}) == 48
    active, upper, fixed = old_report['active_core_coordinates'], bundle['upper'], bundle['fixed']
    added, rhs = parent.cut_matrix(extra, active, upper, fixed)
    bundle['matrix'] = sparse.vstack([bundle['matrix'], added], format='csc')
    bundle['matrix'].sort_indices()
    bundle['rhs'] = np.concatenate((bundle['rhs'], rhs))
    bundle['held'] = held
    if x521_zero:
        bundle['column_upper'] = bundle['column_upper'].copy()
        assert bundle['column_upper'][active.index(521)] == 1
        bundle['column_upper'][active.index(521)] = 0
    zeros = sorted(set(old_report['required_zero_coordinates']) | ({521} if x521_zero else set()))
    bundle['higher'] = higher.FullScanner(bundle['data'], raw, scale, higher_cache, parent.REDUCTION_SHA)
    assert bundle['higher'].coverage['covers_full11_families']
    report = dict(old_report)
    report.update(parent_44cut_numerical_model_sha256=old_report['numerical_model_sha256'],
                  rows=bundle['matrix'].shape[0], nonzeros=int(bundle['matrix'].nnz),
                  free_columns=int(sum(bundle['column_upper'] > 0)), x521_zero=bool(x521_zero),
                  required_zero_coordinates=zeros, initial_cut_count=48,
                  base44_appended_distinct_core_rows=old_report['appended_distinct_core_rows'],
                  appended_distinct_core_rows=23,
                  initial_cut_coefficients_sha256=parent.vector_hash(held),
                  numerical_model_sha256=BASE.numerical_model_hash(bundle['matrix'], bundle['rhs'],
                                                                 bundle['lower'], bundle['column_upper']),
                  reconstructed_followup_r6_cuts=3, reconstructed_r4s3_cuts=1,
                  followup_seed_reduction_controls=controls, full_higher_flag_roots=11,
                  total_scanned_blocks=2405, higher_cache_sha256=INPUT_HASHES['higher_cache'],
                  positive_DP_bounds_and_scalings_unchanged=True)
    bundle['report'] = report
    return bundle


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
                          ('r6s2', bundle['r6'], 'unique_core_cuts'),
                          ('higher11', bundle['higher'], 'unique_core_cuts')]
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
    prep.add_argument('--output', type=Path, required=True)
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
            prepare(INPUTS, args.x521_zero, args.output.resolve())
        else:
            run(args.preparation.resolve(), args.output.resolve(), args.prefix.resolve(),
                args.rounds, args.seconds, args.scan_seconds)
