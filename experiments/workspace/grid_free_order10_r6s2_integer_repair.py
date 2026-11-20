"""Try bounded one-coordinate integer repairs of the 47-cut count point.

This is a witness search, not an infeasibility test. Every trial uses
guarded integer arithmetic for all induced counts and Python integers
for all held cuts. Acceptance repeats every original count equation.
No optimizer or moment scanner is called.
"""

import argparse
import json
from pathlib import Path
import resource
import time

import numpy as np

import grid_free_order10_scaled as counts


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
ROUNDED = LOGS/'prism-zero-order10-r6s2-loop01-round1-rounded-counts.json'
ROUNDED_SHA = '1e9c60d376b35a4b5bf41c06f7ae89036d431a9a05c1b498f08372154f236fa5'
LOOP = LOGS/'prism-zero-order10-r6s2-loop01.json'
LOOP_SHA = '08366598ad71e2942e1cd1ea877616bd85c636f87a2c607e991834016a61644b'
BOUNDS = LOGS/'grid-free-order10-scaled-preparation.json'
BOUNDS_SHA = 'b469897acd15b6078664625191005454e8bac56ae76318d57fd804089bcf8e50'
REDUCED_SHA = '0ad45482ea273b3412e8d308d47eabab366678f4a7e446e4a9f32791c563af65'
COUNTS_SHA = '12409f5ea1932d549cb69d9ca83e8cd4bd53d173b1a6ef136f9cdee6c095fc16'


def run(cache, output, witness_output, maximum_step=8):
    started = time.monotonic()
    assert 1 <= maximum_step <= 8
    assert not output.exists() and not witness_output.exists()
    paths = [(ROUNDED, ROUNDED_SHA), (LOOP, LOOP_SHA),
             (BOUNDS, BOUNDS_SHA), (cache, REDUCED_SHA),
             (Path(counts.__file__), COUNTS_SHA)]
    for path, expected in paths:
        assert counts.digest(path) == expected, str(path)
    initial = json.loads(ROUNDED.read_text())
    loop = json.loads(LOOP.read_text())
    point = initial['rounded_core_values']
    zero_coordinates = initial['required_zero_coordinates']
    held = [item['coefficients'] for item in loop['cuts']]
    assert len(point) == 550 and len(held) == 47
    assert all(type(value) is int for value in point)
    assert point[0] == 1 and all(point[j] == 0 for j in zero_coordinates)
    assert len(zero_coordinates) == 58
    assert initial['negative_induced_rows'] == 1
    assert initial['nonintegral_induced_rows'] == 0
    assert initial['first_negative_rows'] == [[48668, -14515200]]
    upper = [1]+[item['ordinary_count_upper_bound']
                 for item in json.loads(BOUNDS.read_text())['upper_bounds']]
    assert len(upper) == 550 and all(0 <= x <= b for x, b in zip(point, upper))
    data, cores, scale, raw = counts.load_reduced(cache)
    assert len(cores) == 549 and scale == 3628800
    assert not np.any(raw % scale)
    matrix = raw//scale
    assert not np.any(matrix[:6535, 58:])
    base_list = [sum(int(row[j])*point[int(j)] for j in np.flatnonzero(row))
                 for row in matrix]
    assert [(i, value) for i, value in enumerate(base_list) if value < 0] == [(48668, -4)]
    max_base = max(abs(value) for value in base_list)
    max_coefficient = max(abs(int(matrix[:, 58:].min())), abs(int(matrix[:, 58:].max())))
    guard = max_base+maximum_step*max_coefficient
    assert guard < (1 << 63)
    base = np.asarray(base_list, dtype=np.int64)
    cut_values = [sum(a*x for a, x in zip(row, point)) for row in held]
    assert cut_values == initial['exact_held_cut_values']
    assert min(cut_values) >= 0
    bad = 48668
    pool = [int(j) for j in np.flatnonzero(matrix[bad])
            if j >= 58 and j not in zero_coordinates]
    result = {'status': 'bounded one-coordinate repair exhausted without a witness',
              'source_sha256': counts.digest(Path(__file__)),
              'input_sha256': {str(p): h for p, h in paths},
              'ordinary_prefix_coordinates_fixed': 58,
              'required_zero_coordinates': zero_coordinates,
              'maximum_absolute_coordinate_change': maximum_step,
              'candidate_coordinates': pool,
              'failing_induced_type': bad, 'failing_graph_rows': list(data[0][bad]),
              'initial_failing_count': -4,
              'failing_induced_form': [[int(j), int(matrix[bad, j])]
                                       for j in np.flatnonzero(matrix[bad])],
              'fixed_width_evaluation_bound': guard,
              'held_cuts': len(held), 'trials': [],
              'exact_count_witness': False, 'PSD_feasibility_certified': False,
              'optimizer_called': False, 'graph_constructed': False}
    found = None
    for distance in range(1, maximum_step+1):
        for j in pool:
            for delta in (distance, -distance):
                if matrix[bad, j]*delta <= 0 or not 0 <= point[j]+delta <= upper[j]:
                    continue
                values = base+delta*matrix[:, j]
                exact_cuts = [value+delta*row[j] for value, row in zip(cut_values, held)]
                negatives = np.flatnonzero(values < 0)
                trial = {'coordinate': j, 'delta': delta,
                         'negative_induced_rows': len(negatives),
                         'negative_held_cuts': sum(value < 0 for value in exact_cuts)}
                result['trials'].append(trial)
                if not len(negatives) and not trial['negative_held_cuts']:
                    found = (j, delta, exact_cuts)
                    break
            if found:
                break
        if found:
            break
    if found:
        coordinate, delta, exact_cuts = found
        repaired = point.copy()
        repaired[coordinate] += delta
        assert repaired[:58] == point[:58]
        assert all(repaired[j] == 0 for j in zero_coordinates)
        checked = counts.exact_candidate(data, scale, raw, repaired, upper, False)
        assert 'induced_counts' in checked and checked['original_equations_checked'] == 180445
        assert min(exact_cuts) >= 0
        checked.update(source_sha256=counts.digest(Path(__file__)),
                       initial_rounded_sha256=ROUNDED_SHA, loop_sha256=LOOP_SHA,
                       repair={'coordinate': coordinate, 'delta': delta,
                               'before': point[coordinate], 'after': repaired[coordinate]},
                       exact_held_cut_values=exact_cuts,
                       negative_held_cuts=0, required_zero_coordinates=zero_coordinates,
                       required_zeros_hold=True, exact_count_and_held_cut_witness=True,
                       held_cut_count=47, PSD_feasibility_certified=False,
                       graph_constructed=False)
        counts.save(witness_output, checked)
        result.update(status='exact count and 47-cut integer witness found',
                      exact_count_witness=True, repair=checked['repair'],
                      repaired_failing_count=checked['induced_counts'][bad],
                      witness_path=str(witness_output), witness_sha256=counts.digest(witness_output),
                      minimum_held_cut_value=min(exact_cuts), x521=repaired[521])
    result.update(seconds=time.monotonic()-started,
                  peak_process_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    counts.save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('cache', 'output', 'witness-output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--maximum-step', type=int, default=8)
    args = parser.parse_args()
    run(args.cache, args.output, args.witness_output, args.maximum_step)
