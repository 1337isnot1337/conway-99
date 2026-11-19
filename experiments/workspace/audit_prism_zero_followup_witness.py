"""Check later count witnesses against original identities and held cuts.

No numerical finder, repair routine, or moment scanner is imported.
This replay checks the saved induced counts directly. It checks the
core-coordinate zeros, upper bounds, and25 certified linear rows separately;
the producing package supplies their reduced-matrix reconstruction.
"""

import argparse
import hashlib
import json
from math import comb
from pathlib import Path
import pickle
import time

from audit_prism_zero_count_witness import has_prism
from subgraph_counts import identities


ROOT = Path(__file__).resolve().parents[2]
CATALOGUE_SHA = '1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'
CUT_PREPARATION = ROOT/'experiments/logs/moments-and-counts/prism-zero-order10-ipm-zero-closure-preparation.json'
CUT_PREPARATION_SHA = 'fce82618e5beef610d70fadbf7b0e5d955a43496c05c3621b78ee270ff87c820'
BOUND_PREPARATION = ROOT/'experiments/logs/moments-and-counts/grid-free-order10-scaled-preparation.json'
BOUND_PREPARATION_SHA = 'b469897acd15b6078664625191005454e8bac56ae76318d57fd804089bcf8e50'
PRISM_HELPER_SHA = '5acb50547ba2f18a7dc7ad3f375c384131af7215cc84c4de07b1eddeaab93dcd'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(witness, expected_sha, catalogue, face=False):
    started = time.monotonic()
    assert digest(witness) == expected_sha
    assert digest(catalogue) == CATALOGUE_SHA
    assert digest(Path(__file__).with_name('audit_prism_zero_count_witness.py')) == PRISM_HELPER_SHA
    assert digest(CUT_PREPARATION) == CUT_PREPARATION_SHA
    assert digest(BOUND_PREPARATION) == BOUND_PREPARATION_SHA
    saved = json.loads(witness.read_text())
    counts, point = saved['induced_counts'], saved['rounded_core_values']
    assert len(counts) == 48965 and len(point) == 550
    assert all(type(value) is int and value >= 0 for value in counts+point)
    assert point[0] == 1
    data = pickle.loads(catalogue.read_bytes())
    graphs, levels, automorphisms = data[:3]
    assert len(graphs) == len(counts) and len(levels) == 11
    for order, indices in enumerate(levels):
        assert all(len(graphs[i]) == order for i in indices)
        assert sum(counts[i] for i in indices) == comb(99, order)
    equations = 0
    for equation in identities(data, 99, 14):
        assert sum(coefficient*(counts[i-1] if i else 1)
                   for i, coefficient in equation.items()) == 0
        equations += 1
    assert equations == 180445
    prism_types = [i for i, rows in enumerate(graphs) if has_prism(rows)]
    assert len(prism_types) == 1443 and all(counts[i] == 0 for i in prism_types)
    bounds = json.loads(BOUND_PREPARATION.read_text())['upper_bounds']
    prism_cores = []
    assert len(bounds) == 549
    for coordinate, bound in enumerate(bounds, 1):
        assert bound['coordinate'] == coordinate
        index = bound['catalogue_type']
        assert list(graphs[index]) == bound['rows']
        assert automorphisms[index] == bound['automorphisms']
        assert point[coordinate] <= bound['ordinary_count_upper_bound']
        if has_prism(graphs[index]):
            assert point[coordinate] == 0
            prism_cores.append(coordinate)
    assert len(prism_cores) == 58
    prepared = json.loads(CUT_PREPARATION.read_text())
    assert prepared['model']['prism_zero_core_coordinates'] == prism_cores
    cuts = prepared['initial_cuts']
    assert len(cuts) == 25
    values = []
    for cut in cuts:
        row = cut['coefficients']
        assert len(row) == 550 and all(type(v) is int for v in row)
        value = sum(a*x for a, x in zip(row, point))
        assert value >= 0
        values.append(value)
    assert values == saved['exact_held_cut_values']
    if face:
        assert point[521] == 0 and counts[48936] == 0
    else:
        assert point[521] == counts[48936]
    return {'status': 'independent original-count and25-cut audit PASS',
            'source_sha256': digest(Path(__file__)), 'witness_sha256': expected_sha,
            'catalogue_sha256': CATALOGUE_SHA, 'cut_preparation_sha256': CUT_PREPARATION_SHA,
            'bound_preparation_sha256': BOUND_PREPARATION_SHA,
            'nonnegative_integral_counts': len(counts), 'original_equations_checked': equations,
            'level_totals_checked': len(levels), 'prism_containing_induced_zeros': len(prism_types),
            'prism_containing_core_zeros': len(prism_cores), 'ordinary_bounds_checked': len(bounds),
            'certified_linear_cuts_checked': len(cuts), 'minimum_held_cut_value': min(values),
            'x521': point[521], 'x521_zero_required': face,
            'core_to_induced_matrix_reconstruction_repeated': False,
            'optimizer_called': False, 'finder_imported': False, 'PSD_claimed': False,
            'graph_constructed': False, 'seconds': time.monotonic()-started}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('witness', 'catalogue', 'output'):
        parser.add_argument('--'+name, type=Path, required=True)
    parser.add_argument('--sha256', required=True)
    parser.add_argument('--x521-zero', action='store_true')
    args = parser.parse_args()
    result = audit(args.witness, args.sha256, args.catalogue, args.x521_zero)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
