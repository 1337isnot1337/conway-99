"""Dynamic shared-edge box and exact global selector-cut lift.

The supplied sixty signatures are a proposed incidence, never a global
normalization. Query is bounded separately; replay and lift are exact
and call no optimizer. All generated selector cuts range over the full
480-signature domain and its complete eligible-edge graph.
"""

from collections import Counter
from fractions import Fraction
import hashlib
import json
from math import gcd, isfinite
from pathlib import Path
import time

import root_prism_free_f0_row_box_design_linear as fixed
import root_prism_free_f0_symmetric_selector_cut as allocation


DEPENDENCIES = {
    'root_prism_free_f0_row_box_design_linear.py': 'c0d9e70f98e94176bf78bc518b41270940b930ab69cf34b26f42b71ff31a0871',
    'root_prism_free_f0_symmetric_selector_cut.py': '15ec937609b7de44b808e9de7053bb9ee080ddf732a3defd2b23577c026fe274'}
canonical, digest = allocation.canonical, allocation.digest


def check_sources():
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected


def save(path, data):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(data, indent=2)+'\n')
    temporary.replace(path)


def domain(selected, triples, targets, neighbors):
    assert selected == sorted(set(selected)) and len(selected) == 60
    edges = [[u, v] for u in range(60) for v in range(u) if selected[v] in neighbors[selected[u]]]
    incident = [[] for _ in selected]
    for e, (a, b) in enumerate(edges):
        incident[a].append((b, e)); incident[b].append((a, e))
    rows = []
    for a in range(60):
        rows.append({'kind': 'degree', 'vertex': a, 'support': sorted(e for _, e in incident[a]), 'rhs': 8})
        for i in range(18):
            rows.append({'kind': 'mixed', 'vertex': a, 'core_vertex': i,
                         'support': sorted(e for b, e in incident[a] if i in triples[selected[b]]),
                         'rhs': targets[selected[a]][i]})
    data = {'design': [triples[a] for a in selected], 'targets': [targets[a] for a in selected],
            'edge_domain': edges, 'selected_signature_ids': selected}
    assert len(rows) == 1140 and sum(len(row['support']) for row in rows) == 8*len(edges)
    return data, rows


def inventory(data, rows):
    n = len(data['edge_domain'])
    return {'primary_edges': n, 'equations': len(rows), 'standard_form_rows': len(rows)+n,
            'standard_form_variables': 2*n, 'standard_form_nonzeros': 10*n,
            'data_sha256': hashlib.sha256(canonical(data)).hexdigest(),
            'rows_sha256': hashlib.sha256(canonical(rows)).hexdigest()}


def query(selected, triples, targets, neighbors, output, candidate_sha, seconds):
    assert not output.exists() and 0 < seconds <= 60
    started = time.monotonic()
    check_sources()
    data, rows = domain(selected, triples, targets, neighbors)
    n, m = len(data['edge_domain']), len(rows)
    report = {'status': 'RUNNING: one shared-edge box', 'source_sha256': digest(Path(__file__)),
        'dependency_source_hashes': DEPENDENCIES, 'selected_signature_ids': selected,
        'candidate_sha256': candidate_sha, 'inventory': inventory(data, rows),
        'requested_seconds': seconds, 'optimizer_calls': 0,
        'exact_linear_feasibility': False, 'exact_fixed_design_infeasibility': False,
        'full_graph_constructed': False}
    save(output, report)
    try:
        import highspy
        import numpy as np
        from scipy import sparse
        rr, cc = [], []
        for i, row in enumerate(rows):
            for e in row['support']:
                rr.append(i); cc.append(e)
        for e in range(n):
            rr.extend([m+e, m+e]); cc.extend([e, n+e])
        matrix = sparse.csc_matrix((np.ones(len(rr)), (rr, cc)), shape=(m+n, 2*n))
        rhs = np.asarray([row['rhs'] for row in rows]+[1]*n, dtype=float)
        assert matrix.nnz == report['inventory']['standard_form_nonzeros']
        lp = highspy.HighsLp()
        lp.num_col_, lp.num_row_ = 2*n, m+n
        lp.col_cost_, lp.col_lower_ = np.zeros(2*n), np.zeros(2*n)
        lp.col_upper_ = np.full(2*n, highspy.kHighsInf)
        lp.row_lower_, lp.row_upper_ = rhs, rhs
        lp.a_matrix_.format_ = highspy.MatrixFormat.kColwise
        lp.a_matrix_.start_, lp.a_matrix_.index_, lp.a_matrix_.value_ = matrix.indptr, matrix.indices, matrix.data
        remaining = seconds-(time.monotonic()-started)
        if remaining <= 0:
            report['status'] = 'UNKNOWN: shared-edge setup exhausted budget'
        else:
            solver = highspy.Highs()
            for name, value in [('output_flag', False), ('threads', 1), ('solver', 'simplex'),
                                ('presolve', 'on'), ('time_limit', remaining)]:
                assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
            assert solver.passModel(lp) == highspy.HighsStatus.kOk
            report.update(optimizer_calls=1, requested_optimizer_seconds=remaining)
            save(output, report)
            solver.run()
            status = solver.getModelStatus()
            report.update(numerical_status=str(status), optimizer_return_seconds=time.monotonic()-started)
            if status == highspy.HighsModelStatus.kOptimal:
                numeric = list(map(float, solver.getSolution().col_value[:n]))
                assert all(isfinite(value) for value in numeric)
                report['numerical_primary_hex'] = [value.hex() for value in numeric]
                exact = [Fraction(value).limit_denominator(1000000) for value in numeric]
                try:
                    check = fixed.verify_point(rows, n, exact)
                except AssertionError:
                    report['status'] = 'UNKNOWN: numerical shared point without exact reconstruction'
                else:
                    report.update(status='EXACT RATIONAL SYMMETRIC ROW BOX; no graph construction',
                        rational_primary=[[value.numerator, value.denominator] for value in exact],
                        exact_point_check=check, exact_linear_feasibility=True)
            elif status == highspy.HighsModelStatus.kInfeasible:
                report['status'] = 'UNKNOWN: numerical infeasibility without an exact ray'
                _, exists, numerical = solver.getDualRay()
                if exists:
                    numeric = list(map(float, numerical))
                    assert len(numeric) == m+n and all(isfinite(value) for value in numeric)
                    report['numerical_ray_hex'] = [value.hex() for value in numeric]
                    accepted = False
                    for vector, method in fixed.ray_candidates(numeric):
                        for sign in (1, -1):
                            ray = [sign*value for value in vector]
                            try:
                                check = fixed.verify_ray(rows, n, ray)
                            except AssertionError:
                                continue
                            report.update(status='EXACT INTEGER SHARED-ROW OBSTRUCTION',
                                integer_ray=ray, exact_ray_check=check, ray_reconstruction=method,
                                fixed_capacity_potentials=fixed.fixed_capacity_potentials(rows, data, ray),
                                exact_fixed_design_infeasibility=True)
                            accepted = True
                            break
                        if accepted:
                            break
            else:
                report['status'] = 'UNKNOWN: nonoptimal shared-edge LP'
    except Exception as error:
        report.update(status='ERROR: shared-edge query stopped', error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic()-started
        report['cooperative_budget_overrun_seconds'] = max(0, report['elapsed_seconds']-seconds)
        save(output, report)
    return report


def replay(report, selected, triples, targets, neighbors):
    check_sources()
    assert report['source_sha256'] == digest(Path(__file__))
    assert report['dependency_source_hashes'] == DEPENDENCIES and report['selected_signature_ids'] == selected
    data, rows = domain(selected, triples, targets, neighbors)
    assert report['inventory'] == inventory(data, rows) and report['optimizer_calls'] in (0, 1)
    assert not (report['exact_linear_feasibility'] and report['exact_fixed_design_infeasibility'])
    n = len(data['edge_domain'])
    if report['exact_linear_feasibility']:
        values = [Fraction(a, b) for a, b in report['rational_primary']]
        assert fixed.verify_point(rows, n, values) == report['exact_point_check']
        assert report['status'].startswith('EXACT RATIONAL')
    if report['exact_fixed_design_infeasibility']:
        assert fixed.verify_ray(rows, n, report['integer_ray']) == report['exact_ray_check']
        assert fixed.fixed_capacity_potentials(rows, data, report['integer_ray']) == report['fixed_capacity_potentials']
        assert report['status'] == 'EXACT INTEGER SHARED-ROW OBSTRUCTION'
    assert not report['status'].startswith('RUNNING:')


def lift(selected, local_potentials, triples, targets, neighbors, actions):
    check_sources()
    assert selected == sorted(set(selected)) and len(selected) == len(local_potentials) == 60
    assert all(len(row) == 18 and all(type(value) is int for value in row) for row in local_potentials)
    potentials = [[0]*18 for _ in range(480)]
    for a, vector in zip(selected, local_potentials):
        potentials[a] = list(vector)
    edges = [[a, b] for a in range(480) for b in neighbors[a] if a < b]
    assert len(edges) == 68394
    support = set(selected)
    delta, coefficients, positive = allocation.allocate(triples, targets, edges, potentials, support)
    gap = sum(coefficients[a] for a in selected)
    assert gap > 0
    divisor = gcd(*(abs(value) for value in coefficients))
    assert divisor > 0 and gap % divisor == 0
    transports = []
    for index, action in enumerate(actions):
        move, image = action['component_image'], action['signature_image']
        inverse = [0]*480
        for a, b in enumerate(image):
            inverse[b] = a
        transported = [[0]*18 for _ in range(480)]
        for a, vector in enumerate(potentials):
            for i, value in enumerate(vector):
                transported[image[a]][move[i]] = value
        moved_support = {image[a] for a in selected}
        _, moved, _ = allocation.allocate(triples, targets, edges, transported, moved_support, inverse)
        assert all(moved[image[a]] == coefficients[a] for a in range(480))
        terms = [[a, value//divisor] for a, value in enumerate(moved) if value]
        assert sum(value for a, value in terms if a in moved_support) == gap//divisor
        transports.append({'core_action_index': index, 'signed_coefficients': terms,
                           'transported_selection_gap': gap//divisor})
    assert len(transports) == 12
    return {'source_sha256': digest(Path(__file__)), 'selected_signature_ids_for_allocation_only': selected,
        'nonzero_target_potentials': [[a, vector] for a, vector in enumerate(potentials) if any(vector)],
        'complete_global_edges': len(edges), 'global_edge_sha256': hashlib.sha256(canonical(edges)).hexdigest(),
        'positive_edge_count': len(positive), 'positive_edge_type_counts': dict(Counter(e['kind'] for e in positive)),
        'positive_edge_allocation_sha256': hashlib.sha256(canonical(positive)).hexdigest(),
        'total_target_demand_at_saved_selection': sum(delta[a] for a in selected),
        'internal_positive_capacity': sum(e['weight'] for e in positive if e['kind'] == 'internal'),
        'raw_gap': gap, 'coefficient_gcd': divisor, 'normalized_gap': gap//divisor,
        'transported_cuts': transports, 'saved_selection_is_not_a_cut_hypothesis': True,
        'optimizer_or_solver_called': False}


def seed_control(triples, targets, neighbors, actions):
    check_sources()
    for name in ('f0-row-box-design-exterior-model.json.gz', 'f0-row-box-design-linear-run01.json'):
        assert digest(allocation.LOGS/name) == allocation.INPUTS[name]
    assert digest(allocation.LOGS/'f0-symmetric-selector-cut-certificate.json.gz') == '3aea5e48c4a35eb7e023708231f3dbf585634c25de25484f364276041260f846'
    model = fixed.exterior.load_json(fixed.exterior.LOGS/'f0-row-box-design-exterior-model.json.gz')
    result = fixed.exterior.load_json(fixed.exterior.LOGS/'f0-row-box-design-linear-run01.json')
    certificate = allocation.read(allocation.LOGS/'f0-symmetric-selector-cut-certificate.json.gz')
    selected = model['data']['design_source_indices']
    data, rows = domain(selected, triples, targets, neighbors)
    assert rows == model['linear_rows'] and data['edge_domain'] == model['data']['edge_domain']
    assert fixed.verify_ray(rows, len(data['edge_domain']), result['integer_ray']) == result['exact_ray_check']
    potentials = fixed.fixed_capacity_potentials(rows, data, result['integer_ray'])
    assert potentials == result['fixed_capacity_potentials']
    lifted = lift(selected, potentials['integer_potentials60_by18'], triples, targets, neighbors, actions)
    assert lifted['normalized_gap'] == 2
    for new, old in zip(lifted['transported_cuts'], certificate['transported_cuts']):
        signed = sorted(old['positive_terms']+[[a, -weight] for a, weight in old['negative_side_positive_weights']])
        assert new['signed_coefficients'] == signed
    return {'status': 'dynamic shared domain, fixed ray and all12 published selector lifts replay PASS',
            'source_sha256': digest(Path(__file__)), 'primary_edges': len(data['edge_domain']),
            'standard_form_inventory': inventory(data, rows), 'normalized_gap': 2,
            'optimizer_or_solver_called': False}
