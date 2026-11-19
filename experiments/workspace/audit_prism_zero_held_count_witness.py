"""Audit an order-ten count witness against original equations and held cuts.

Only saved induced counts, original catalogue identities, ordinary-count
bounds, direct prism detection, and integer cut evaluations are used.
No optimizer, reduced count matrix, repair routine, or PSD scanner is
loaded. The core-to-induced coefficient reduction is not rederived here.
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
BOUNDS = ROOT/'experiments/logs/moments-and-counts/grid-free-order10-scaled-preparation.json'
BOUNDS_SHA = 'b469897acd15b6078664625191005454e8bac56ae76318d57fd804089bcf8e50'
PRISM_HELPER_SHA = '5acb50547ba2f18a7dc7ad3f375c384131af7215cc84c4de07b1eddeaab93dcd'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def audit(args):
    started = time.monotonic()
    assert digest(args.witness) == args.sha256
    assert digest(args.cuts) == args.cuts_sha256
    assert digest(args.catalogue) == CATALOGUE_SHA
    assert digest(BOUNDS) == BOUNDS_SHA
    assert digest(Path(__file__).with_name('audit_prism_zero_count_witness.py')) == PRISM_HELPER_SHA
    saved = json.loads(args.witness.read_text())
    counts, point = saved['induced_counts'], saved['rounded_core_values']
    assert len(counts) == 48965 and len(point) == 550
    assert all(type(value) is int and value >= 0 for value in counts+point)
    assert point[0] == 1

    with args.catalogue.open('rb') as stream:
        data = pickle.load(stream)
    graphs, levels, automorphisms = data[:3]
    assert len(graphs) == 48965 and len(levels) == 11
    level_totals = []
    for order, indices in enumerate(levels):
        assert all(len(graphs[i]) == order for i in indices)
        actual = sum(counts[i] for i in indices)
        assert actual == comb(99,order)
        level_totals.append([order,len(indices),actual])

    equations = coefficients = 0
    for equation in identities(data,99,14):
        assert all(0 <= i <= len(counts) for i in equation)
        residual = sum(int(coefficient)*(counts[i-1] if i else 1)
                       for i,coefficient in equation.items())
        assert residual == 0, (equations,residual)
        equations += 1
        coefficients += len(equation)
    assert equations == 180445
    prism_types = [i for i,rows in enumerate(graphs) if has_prism(rows)]
    assert len(prism_types) == 1443 and all(counts[i] == 0 for i in prism_types)

    bounds = json.loads(BOUNDS.read_text())['upper_bounds']
    assert len(bounds) == 549
    prism_coordinates = []
    smallest_bound_slack = None
    for coordinate,bound in enumerate(bounds,1):
        assert bound['coordinate'] == coordinate
        index = bound['catalogue_type']
        assert list(graphs[index]) == bound['rows']
        assert automorphisms[index] == bound['automorphisms']
        upper = bound['ordinary_count_upper_bound']
        assert type(upper) is int and point[coordinate] <= upper
        slack = upper-point[coordinate]
        smallest_bound_slack = slack if smallest_bound_slack is None else min(smallest_bound_slack,slack)
        if has_prism(graphs[index]):
            assert point[coordinate] == 0
            prism_coordinates.append(coordinate)
    assert len(prism_coordinates) == 58
    if 'required_zero_coordinates' in saved:
        assert saved['required_zero_coordinates'] == prism_coordinates

    held = json.loads(args.cuts.read_text())
    cuts = held['cuts']
    assert len(cuts) == args.expected_cut_count
    if 'loop_sha256' in saved:
        assert saved['loop_sha256'] == args.cuts_sha256
    values, largest_term = [],0
    for cut in cuts:
        row = cut['coefficients']
        assert len(row) == 550 and all(type(value) is int for value in row)
        terms = [a*x for a,x in zip(row,point)]
        largest_term = max(largest_term,max(map(abs,terms),default=0))
        value = sum(terms)
        assert value >= 0
        values.append(value)
    assert values == saved['exact_held_cut_values']
    if 'held_cut_count' in saved:
        assert saved['held_cut_count'] == len(cuts)

    changed = None
    if args.initial is not None:
        assert args.initial_sha256 and digest(args.initial) == args.initial_sha256
        old = json.loads(args.initial.read_text())['rounded_core_values']
        assert len(old) == len(point) and all(type(value) is int for value in old)
        changed = [[i,a,b] for i,(a,b) in enumerate(zip(old,point)) if a != b]
        if args.expect_change:
            assert changed == [args.expect_change]
        if 'initial_rounded_sha256' in saved:
            assert saved['initial_rounded_sha256'] == args.initial_sha256
        if 'repair' in saved:
            repair = saved['repair']
            assert changed == [[repair['coordinate'],repair['before'],repair['after']]]
            assert repair['after']-repair['before'] == repair['delta']
    else:
        assert args.initial_sha256 is None and args.expect_change is None

    return {'status':f'independent original-count, prism-zero, bound and{len(cuts)}-cut audit PASS',
            'audit_source_sha256':digest(Path(__file__)), 'witness_sha256':args.sha256,
            'catalogue_sha256':CATALOGUE_SHA, 'cut_source_sha256':args.cuts_sha256,
            'ordinary_bound_preparation_sha256':BOUNDS_SHA,
            'identity_source_sha256':digest(Path(__file__).with_name('subgraph_counts.py')),
            'prism_helper_sha256':PRISM_HELPER_SHA,
            'nonnegative_integral_induced_counts':len(counts),
            'nonnegative_integral_core_values':len(point),
            'original_equations_checked':equations,'original_nonzero_coefficients_evaluated':coefficients,
            'level_totals_checked':len(levels),'level_totals':level_totals,
            'direct_prism_containing_types_checked_zero':len(prism_types),
            'ordinary_prism_coordinates_checked_zero':prism_coordinates,
            'ordinary_upper_bounds_checked':len(bounds),'minimum_ordinary_bound_slack':smallest_bound_slack,
            'exact_held_inequalities_checked':len(cuts),'held_inequality_values':values,
            'minimum_held_inequality_value':min(values),'largest_absolute_held_term':largest_term,
            'initial_witness_sha256':args.initial_sha256,'changed_core_coordinates':changed,
            'x521':point[521], 'core_to_induced_reduction_reconstructed':False,
            'held_inequality_coefficients_rederived':False,'all_arithmetic_is_unbounded_Python_integer':True,
            'optimizer_called':False,'dense_reduction_loaded':False,'PSD_claimed':False,
            'graph_constructed':False,'seconds':time.monotonic()-started}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('witness','catalogue','cuts','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--sha256',required=True)
    parser.add_argument('--cuts-sha256',required=True)
    parser.add_argument('--expected-cut-count',type=int,required=True)
    parser.add_argument('--initial',type=Path)
    parser.add_argument('--initial-sha256')
    parser.add_argument('--expect-change',type=int,nargs=3)
    args = parser.parse_args()
    assert not args.output.exists()
    result = audit(args)
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2),flush=True)
