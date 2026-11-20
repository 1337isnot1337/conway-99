"""Exact postprocessing of the saved unresolved shared-edge dual ray.

Round only free equality multipliers. Set each nonnegative upper-bound
multiplier to the exact deficit of its primary column. This proves all
coefficient signs algebraically; a strictly negative integer RHS is the
remaining acceptance condition. No optimizer or solver is called.
"""

import argparse
from fractions import Fraction
import gzip
import hashlib
from itertools import product
import json
from math import gcd
from pathlib import Path

import root_prism_free_f0_carry_row_loop as loop
import root_prism_free_f0_shared_row_separator as shared


ROOT, LOGS = loop.ROOT, loop.LOGS
canonical, digest, load_json = loop.canonical, loop.digest, loop.load_json
SOURCES = {
    'root_prism_free_f0_carry_row_loop.py': 'ec85c752a5d3c5538250e0099286dcbad674e23ef9572f72bbd3ca72fb5ef403',
    'root_prism_free_f0_shared_row_separator.py': '7d8f3324826c1fa7fa05e79dbbee7c6e16b064dd01ef5e548160f6a7fe04368a'}
RESULT = LOGS/'f0-carry-row-loop-run01/result.json'
RESULT_SHA = 'ecc80a941a1b0d9e152788167210a5e8b7936f28b03ee50c35658895b453d3d3'


def repaired_ray(rows, n, multipliers):
    """Return an integer ray with exact nonnegative column coefficients.

    The ray need not have a negative RHS. Call the complete independent
    sign/RHS verifier before accepting it as an obstruction.
    """
    assert len(multipliers) == len(rows)
    assert all(type(value) is int for value in multipliers)
    coefficients = [0]*n
    for row, value in zip(rows, multipliers):
        for edge in row['support']:
            coefficients[edge] += value
    upper = [max(0, -value) for value in coefficients]
    vector = list(multipliers)+upper
    divisor = gcd(*vector)
    if divisor:
        vector = [value//divisor for value in vector]
    return vector


def controls():
    toy = [{'support': [0], 'rhs': 2}]
    assert shared.fixed.verify_ray(toy, 1, repaired_ray(toy, 1, [-1]))['rhs_dot_product'] == -1
    # Every point of this finite set is an explicit feasible box point.
    # For every integer multiplier choice, exact repair must give a
    # nonnegative RHS whenever that point has the recorded margins.
    tested = 0
    supports = [[0], [1], [2], [0, 1], [1, 2], [0, 1, 2]]
    for point in product((0, 1), repeat=3):
        rows = [{'support': support, 'rhs': sum(point[e] for e in support)}
                for support in supports]
        for multipliers in product((-1, 0, 1), repeat=len(rows)):
            ray = repaired_ray(rows, 3, multipliers)
            primary = list(ray[len(rows):])
            for row, value in zip(rows, ray[:len(rows)]):
                for edge in row['support']:
                    primary[edge] += value
            assert all(value >= 0 for value in primary+ray[len(rows):])
            rhs = sum(row['rhs']*value for row, value in zip(rows, ray[:len(rows)]))+sum(ray[len(rows):])
            assert rhs >= 0
            tested += 1
    return {'infeasible_box_positive_control': True,
            'feasible_box_integer_multiplier_controls': tested,
            'optimizer_or_solver_called': False}


def calculate():
    for name, expected in SOURCES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert digest(RESULT) == RESULT_SHA
    result = load_json(RESULT)
    assert result['status'] == 'UNKNOWN: numerical infeasibility without an exact ray; unresolved'
    step = result['iterations'][-1]
    assert step['iteration'] == 8 and step['exact_individual_boxes'] == 60
    assert step['exact_individual_obstructions'] == 0
    candidate_path, shared_path = ROOT/step['candidate'], ROOT/step['shared_rows']
    assert digest(candidate_path) == step['candidate_sha256']
    assert digest(shared_path) == step['shared_rows_sha256']
    candidate, numerical = load_json(candidate_path), load_json(shared_path)
    selected = candidate['selected_signature_ids']
    domain, records = loop.BASE.load(0)
    old_cuts, old_clauses, _ = loop.individual.old.load_cuts()
    triples, targets, neighbors, _, actions, _ = loop.individual.box.load()
    context = (domain, records, old_cuts, old_clauses, triples, targets, neighbors, actions)
    individual_registry = load_json(ROOT/result['individual-registry'])
    signed_registry = load_json(ROOT/result['symmetric-registry'])
    assert digest(ROOT/result['individual-registry']) == result['individual-registry_sha256']
    assert digest(ROOT/result['symmetric-registry']) == result['symmetric-registry_sha256']
    assert loop.inspect(selected, context, individual_registry, signed_registry) == candidate
    shared.replay(numerical, selected, triples, targets, neighbors)
    assert not numerical['exact_fixed_design_infeasibility']
    assert not numerical['exact_linear_feasibility']
    data, rows = shared.domain(selected, triples, targets, neighbors)
    n, m = len(data['edge_domain']), len(rows)
    exact_dyadic = [Fraction(float.fromhex(value)) for value in numerical['numerical_ray_hex'][:m]]
    # These fixed choices are recorded proposals. Only the subsequent
    # exact sign and strict RHS checks establish the certificate.
    multipliers = [round(-value) for value in exact_dyadic]
    ray = repaired_ray(rows, n, multipliers)
    checked = shared.fixed.verify_ray(rows, n, ray)
    potentials = shared.fixed.fixed_capacity_potentials(rows, data, ray)
    lifted = shared.lift(selected, potentials['integer_potentials60_by18'],
                         triples, targets, neighbors, actions)
    assert potentials['strict_gap'] > 0 and lifted['normalized_gap'] > 0
    return {'status': 'exact repaired shared-row ray and all12 universal selector transports PASS',
        'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': SOURCES,
        'frozen_terminal_result': loop.portable(RESULT), 'frozen_terminal_result_sha256': RESULT_SHA,
        'frozen_terminal_status_unchanged': result['status'],
        'candidate': loop.portable(candidate_path), 'candidate_sha256': digest(candidate_path),
        'numerical_shared_result': loop.portable(shared_path),
        'numerical_shared_result_sha256': digest(shared_path),
        'inventory': shared.inventory(data, rows),
        'reconstruction': {'free_multiplier_orientation': -1, 'rounding_scale': 1,
            'numeric_inputs_interpreted_as_exact_dyadic_rationals': True,
            'rounding': 'nearest integer, ties to even',
            'upper_multiplier_rule': 'max(0,-sum of integer equality coefficients on that primary column)',
            'whole_vector_common_gcd_removed': True,
            'numerical_upper_multipliers_discarded': True},
        'integer_ray': ray, 'exact_ray_check': checked,
        'fixed_capacity_potentials': potentials, 'universal_selector_lift': lifted,
        'controls': controls(), 'new_optimizer_or_solver_called': False,
        'fixed_candidate_excluded': True, 'whole_component_excluded': False,
        'full_graph_constructed': False, 'existing_formula_or_result_modified': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['generate', 'replay'])
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    report = calculate()
    if args.mode == 'generate':
        assert not args.certificate.exists()
        args.certificate.write_bytes(gzip.compress(canonical(report)+b'\n', mtime=0))
        summary = {k: v for k, v in report.items() if k not in
                   ('integer_ray', 'fixed_capacity_potentials', 'universal_selector_lift')}
        summary['potential_gap'] = report['fixed_capacity_potentials']['strict_gap']
        summary['universal_normalized_gap'] = report['universal_selector_lift']['normalized_gap']
        summary['complete_transports'] = len(report['universal_selector_lift']['transported_cuts'])
        summary['certificate_sha256'] = digest(args.certificate)
    else:
        assert canonical(report) == canonical(load_json(args.certificate))
        summary = {'status': 'pure exact repaired-ray/candidate/all12-transport replay PASS',
                   'source_sha256': digest(Path(__file__)),
                   'certificate_sha256': digest(args.certificate),
                   'exact_ray_check': report['exact_ray_check'],
                   'complete_transports': 12, 'optimizer_or_solver_called': False}
    if args.output:
        assert not args.output.exists()
        args.output.write_text(json.dumps(summary, indent=2)+'\n')
    print(json.dumps(summary, indent=2), flush=True)
