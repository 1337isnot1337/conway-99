"""Bounded exact integer repair using only new order-ten core coordinates.

This is a local search, not an exhaustive feasibility test. It never calls an
optimizer. Every trial evaluates all48,965 induced counts with guarded integer
arithmetic and retains the old58 coordinates exactly. A passing candidate is
recomputed with Python integers and checked against all original equations.
"""

import argparse
import hashlib
import json
from pathlib import Path
import resource
import time

import numpy as np
from threadpoolctl import threadpool_limits

import grid_free_order10_scaled as counts
import grid_free_order10_moments as separator


INPUT_SHA = '639c079d9ef35b36a1681b7ff124d2326af35013c7f2fd808b4721c51aeb30d2'
FINDER_SHA = '12409f5ea1932d549cb69d9ca83e8cd4bd53d173b1a6ef136f9cdee6c095fc16'
SEPARATOR_SHA = '4c6886bd8d5dffa711aa20991af3bb87495262bd01d8227d2f64caac0040bbae'
LOOP_RESULT_SHA = '5030c57981c1d32e05c1c867082135e8706bb235a3f82253b552ebb682fc34fb'


def proposal(point, path, source):
    active = [j for j in range(1, 550) if j not in (56, 57)]
    values = [float(point[j]) for j in active]
    assert all(int(v) == point[j] for j, v in zip(active, values))
    record = {'status': 'integer count candidate represented losslessly for moment separation',
              'source_sha256': counts.digest(Path(__file__)), 'candidate_source': source,
              'case_index': 1, 'fixed_order_nine_point': False, 'prism_zero_required': True,
              'real_proposal': {'active_coordinates': active, 'ordinary_core_values': values,
                               'exact_real_feasibility_certified': False}}
    counts.save(path, record)


def run(cache, rounded, preparation, loop_result, initial_psd, prefix, seconds):
    started = time.monotonic()
    deadline = started+seconds
    assert counts.digest(rounded) == INPUT_SHA
    assert counts.digest(Path(counts.__file__)) == FINDER_SHA
    assert counts.digest(Path(separator.__file__)) == SEPARATOR_SHA
    assert counts.digest(loop_result) == LOOP_RESULT_SHA
    original = json.loads(rounded.read_text())
    point = original['rounded_core_values']
    assert len(point) == 550 and all(type(v) is int for v in point)
    assert point[0] == 1 and point[1] == point[56] == point[57] == 0
    initial = json.loads(initial_psd.read_text())
    separator.replay(initial_psd)
    assert initial['point_float'] == [float(v) for v in point[:58]]
    result = {'status': 'bounded exact repair started',
              'source_sha256': counts.digest(Path(__file__)),
              'input_hashes': {str(p): counts.digest(p) for p in
                               (cache, rounded, preparation, loop_result, initial_psd)},
              'maximum_seconds': seconds, 'changed_coordinates_minimum': 58,
              'old_coordinates_fixed': point[:58], 'optimizer_called': False,
              'exact_count_witness': False, 'PSD_feasibility_certified': False,
              'initial_exact_PSD_negative_blocks': initial['exact_negative_block_count']}
    output = prefix.with_name(prefix.name+'-result.json')
    if initial['exact_negative_block_count']:
        result['status'] = 'rounded old coordinates have an exact PSD violation; no repair attempted'
        counts.save(output, result)
        return result
    saved = json.loads(preparation.read_text())
    assert saved['source_sha256'] == FINDER_SHA
    assert saved['reduced_cache_sha256'] == counts.digest(cache)
    upper = [1]+[row['ordinary_count_upper_bound'] for row in saved['upper_bounds']]
    assert all(0 <= x <= bound for x, bound in zip(point, upper))
    data, cores, scale, raw = counts.load_reduced(cache)
    assert len(cores) == 549 and scale == 3628800
    assert not np.any(raw % scale)
    matrix = raw//scale
    assert not np.any(matrix[:6535, 58:])
    base_list = [sum(int(row[j])*point[int(j)] for j in np.flatnonzero(row))
                 for row in matrix]
    assert [(i, value) for i, value in enumerate(base_list) if value < 0] == [(48301, -1), (48915, -1)]
    magnitude = max(abs(v) for v in base_list)
    maximum_new_coefficient = max(abs(int(matrix[:, 58:].min())), abs(int(matrix[:, 58:].max())))
    # Every trial changes at most four units. This controls every sequential
    # addition as well as the final value, before fixed-width arithmetic.
    guard = magnitude+4*maximum_new_coefficient
    assert guard < (1 << 63)
    base = np.array(base_list, dtype=np.int64)
    cuts = [item['coefficients'] for item in json.loads(loop_result.read_text())['cuts']]
    assert len(cuts) == 14
    old_cut_values = [sum(a*x for a, x in zip(cut, point[:58])) for cut in cuts]
    assert all(value > 0 for value in old_cut_values)
    forms = []
    for row in (48301, 48915):
        terms = [[int(j), int(matrix[row, j])] for j in np.flatnonzero(matrix[row])]
        forms.append({'catalogue_type': row, 'rows': list(data[0][row]),
                      'exact_induced_form': terms, 'value_at_rounded_point': -1})
    result.update(failing_forms=forms, maximum_new_coefficient=maximum_new_coefficient,
                  maximum_absolute_base_count=magnitude, integer_evaluation_bound=guard,
                  held_cut_values=old_cut_values, old_count_forms_unchanged=True)
    counts.save(output, result)
    print(json.dumps({'failing_forms': forms, 'integer_evaluation_bound': guard}, indent=2), flush=True)
    checked, seen, found = 0, {()}, None
    best = (2, 2)

    def score(values):
        negative = values[values < 0]
        return len(negative), -sum(int(v) for v in negative)

    def trial(delta, values):
        nonlocal checked, found, best
        key = tuple(sorted((j, v) for j, v in delta.items() if v))
        if key in seen or sum(abs(v) for _, v in key) > 4:
            return None
        if any(j < 58 or not 0 <= point[j]+v <= upper[j] for j, v in key):
            return None
        seen.add(key)
        checked += 1
        # All fourteen forms use only coordinates0..57. The delta support
        # check above therefore verifies their exact values for every trial.
        assert all(value >= 0 for value in old_cut_values)
        value = score(values)
        best = min(best, value)
        if not value[0]:
            found = key
        return value, key, values

    initial_pool = sorted({int(j) for row in (48301, 48915)
                           for j in np.flatnonzero(matrix[row, 58:])+58})
    beam = []
    for step in (1, -1, 2, -2, 3, -3, 4, -4):
        for j in initial_pool:
            if time.monotonic() >= deadline-30:
                break
            if not any(int(matrix[row, j])*step > 0 for row in (48301, 48915)):
                continue
            item = trial({j: step}, base+step*matrix[:, j])
            if item is not None and abs(step) == 1:
                beam.append(item)
                if len(beam) > 64:
                    beam = sorted(beam, key=lambda row: (row[0], row[1]))[:32]
            if found:
                break
        if found or time.monotonic() >= deadline-30:
            break
    # A deliberately small beam extends unit changes only. This is a
    # witness finder, so failure of the beam does not exclude any point.
    beam = sorted(beam, key=lambda item: (item[0], item[1]))[:32]
    for depth in (2, 3, 4):
        if found or time.monotonic() >= deadline-30:
            break
        next_beam = []
        for _, key, values in beam:
            bad = np.flatnonzero(values < 0)
            pool = sorted({int(j) for row in bad for j in np.flatnonzero(matrix[row, 58:])+58})
            for j in pool:
                for step in (1, -1):
                    if time.monotonic() >= deadline-30:
                        break
                    if not any(int(matrix[row, j])*step > 0 for row in bad):
                        continue
                    delta = dict(key)
                    delta[j] = delta.get(j, 0)+step
                    item = trial(delta, values+step*matrix[:, j])
                    if item is not None:
                        next_beam.append(item)
                        if len(next_beam) > 64:
                            next_beam = sorted(next_beam, key=lambda row: (row[0], row[1]))[:32]
                    if found:
                        break
                if found or time.monotonic() >= deadline-30:
                    break
            if found or time.monotonic() >= deadline-30:
                break
        beam = sorted(next_beam, key=lambda item: (item[0], item[1]))[:32]
    result.update(trials_checked=checked, best_negative_score=list(best),
                  initial_coordinate_pool=initial_pool, search_l1_bound=4, beam_width=32)
    if found:
        repaired = list(point)
        for j, value in found:
            repaired[j] += value
        assert repaired[:58] == point[:58]
        verified = counts.exact_candidate(data, scale, raw, repaired, upper, False)
        assert 'induced_counts' in verified
        exact_cut_values = [sum(a*x for a, x in zip(cut, repaired[:58])) for cut in cuts]
        assert exact_cut_values == old_cut_values and all(v >= 0 for v in exact_cut_values)
        witness_path = prefix.with_name(prefix.name+'-witness.json')
        verified.update(source_sha256=result['source_sha256'],
                        changed_coordinates=[list(pair) for pair in found],
                        old_coordinates_unchanged=True, prism_zero=True,
                        fourteen_exact_cut_values=exact_cut_values,
                        PSD_feasibility_certified=False)
        counts.save(witness_path, verified)
        proposal_path = prefix.with_name(prefix.name+'-proposal.json')
        proposal(repaired, proposal_path, str(witness_path))
        separation_path = prefix.with_name(prefix.name+'-separation.json')
        separated = separator.scan(proposal_path, separation_path)
        separator.replay(separation_path)
        result.update(status='exact prism-zero order-ten count witness found; PSD not certified',
                      exact_count_witness=True, changed_coordinates=[list(pair) for pair in found],
                      original_equations_checked=verified['original_equations_checked'],
                      witness_path=str(witness_path), witness_sha256=counts.digest(witness_path),
                      proposal_path=str(proposal_path), proposal_sha256=counts.digest(proposal_path),
                      separation_path=str(separation_path), separator_sha256=counts.digest(separation_path),
                      exact_negative_PSD_blocks=separated['exact_negative_block_count'])
    else:
        result['status'] = 'bounded sparse exact repair found no witness; unresolved'
    result['seconds'] = time.monotonic()-started
    result['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    counts.save(output, result)
    print(json.dumps({k: v for k, v in result.items() if k not in
                      ('old_coordinates_fixed', 'failing_forms', 'initial_coordinate_pool')}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--cache', type=Path, required=True)
    parser.add_argument('--rounded', type=Path, required=True)
    parser.add_argument('--preparation', type=Path, required=True)
    parser.add_argument('--loop-result', type=Path, required=True)
    parser.add_argument('--initial-psd', type=Path, required=True)
    parser.add_argument('--prefix', type=Path, required=True)
    parser.add_argument('--seconds', type=float, default=240)
    args = parser.parse_args()
    assert 0 < args.seconds <= 300
    with threadpool_limits(limits=1):
        run(args.cache, args.rounded, args.preparation, args.loop_result,
            args.initial_psd, args.prefix, args.seconds)
