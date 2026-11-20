"""Bound graph decorations of the complete empty-root packing orbits.

This script counts possible edge positions, not graph decorations. It
uses only common-neighbor caps that hold in every srg(99,14,1,2).
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT / 'experiments/logs/moments-and-counts'
ORBITS = LOGS / 'order10-high-mask-packing-orbits01.json'
ORBITS_SHA = 'a6ca65e8edeb1d4545e89c28833bf7526c693ce6066ec5b6f15a47d31853c61d'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def scope():
    assert sha(ORBITS) == ORBITS_SHA
    record = json.loads(ORBITS.read_text())
    assert record['complete'] and record['atom_orbits'] == 249
    array_path = ROOT / record['arrays']['path']
    assert sha(array_path) == record['arrays']['sha256']
    with np.load(array_path, allow_pickle=False) as data:
        for key in ('visible_atom_codes', 'atom_representatives', 'atom_sizes'):
            assert hashlib.sha256(data[key].tobytes(order='C')).hexdigest() == record['array_sha256'][key]
        codes = list(map(int, data['visible_atom_codes']))
        representatives = list(map(int, data['atom_representatives']))
        sizes = list(map(int, data['atom_sizes']))
    high = [mask for mask in range(64) if mask.bit_count() >= 3]
    assert len(high) == 42
    rows, histogram = [], Counter()
    total_bound = full_labelled_bound = 0
    for orbit, (representative, size) in enumerate(zip(representatives, sizes)):
        code = codes[representative]
        masks = [mask for i, mask in enumerate(high) if code >> i & 1]
        k = len(masks)
        assert k <= 10
        assert all(sum(bool(mask >> i & 1 and mask >> j & 1) for mask in masks) <= 2
                   for i, j in combinations(range(6), 2))
        overlaps = [(a, b, (masks[a] & masks[b]).bit_count())
                    for a, b in combinations(range(k), 2)]
        assert all(common <= 2 for _, _, common in overlaps)
        eligible = [(a, b) for a, b, common in overlaps if common <= 1]
        edge_count = len(eligible)
        bound = 1 << edge_count
        total_bound += bound
        full_labelled_bound += size * bound
        histogram[k, edge_count] += 1
        rows.append({'atom_orbit': orbit, 'representative_local_id': representative,
                     'atom_orbit_size': size, 'high_class_code': code,
                     'selected_high_masks': masks, 'high_vertices': k,
                     'eligible_edges': [list(edge) for edge in eligible],
                     'eligible_edge_count': edge_count,
                     'forced_nonedges_with_two_core_common_neighbors': sum(common == 2 for _, _, common in overlaps),
                     'unconstrained_edge_assignment_upper_bound': bound})
    assert len(rows) == 249 and sum(sizes) == 90776
    return {'status': 'complete edge-position bound on all empty-root packing orbits; no graph census',
            'orbit_preparation_sha256': ORBITS_SHA, 'orbit_arrays_sha256': record['arrays']['sha256'],
            'source_sha256': sha(Path(__file__)), 'atom_orbits': len(rows),
            'covered_structural_atoms': sum(sizes), 'maximum_high_vertices': max(row['high_vertices'] for row in rows),
            'maximum_eligible_edges': max(row['eligible_edge_count'] for row in rows),
            'sum_unconstrained_graph_bounds_over_representatives': total_bound,
            'sum_unconstrained_graph_bounds_over_all_atoms': full_labelled_bound,
            'histogram': [{'high_vertices': k, 'eligible_edges': edges, 'atom_orbits': count}
                          for (k, edges), count in sorted(histogram.items())],
            'representatives': rows,
            'necessary_graph_conditions': [
                'An edge between high vertices a,b requires |h_a intersect h_b| <= 1.',
                'For every root i and high vertex a, sum_{b adjacent a} 1[i in h_b] <= 1 if i in h_a, otherwise <= 2.',
                'For every high pair a,b, |h_a intersect h_b| + |N_H(a) intersect N_H(b)| <= 1 if adjacent, otherwise <= 2.',
                'The high-induced degree of a is at most 14-|h_a|.'
            ],
            'conditions_sufficient_for_exterior_completion': False,
            'host_graph_automorphism_assumed': False,
            'prism_or_F_free_hypothesis_imposed': False,
            'high_induced_graphs_enumerated': False,
            'moment_features_or_product_tensors_built': False,
            'optimizer_or_solver_called': False,
            'graph_existence_resolved': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    report = scope()
    report['seconds'] = time.monotonic() - started
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({key: value for key, value in report.items()
                      if key not in ('representatives', 'histogram')}, indent=2))
    print('result_sha256', sha(args.output))
