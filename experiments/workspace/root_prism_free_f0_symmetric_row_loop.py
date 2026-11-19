"""Bounded free480 incidence loop with individual and symmetric row cuts.

Every SAT incidence is checked exactly. Individual row obstructions are
used first. Only a complete exact60-box pass invokes one shared-edge LP.
An exact shared-edge ray is lifted to the complete signature domain.
No candidate visitation blocks, fixed incidence, or graph symmetry is
imposed. Incremental UNSAT requires a separate fresh proof certificate.
"""

import argparse
import gzip
import hashlib
import json
from math import gcd
from pathlib import Path
import resource
import tempfile
from threading import Timer
import time

from pysat.formula import CNF
from pysat.solvers import Solver

import root_prism_free_f0_incidence_row_loop as individual
import root_prism_free_f0_shared_row_separator as shared
import root_prism_free_f0_signed_threshold as signed
import root_prism_free_f0_symmetric_selector_cut as seed


ROOT, LOGS, BASE = individual.ROOT, individual.LOGS, individual.BASE
digest, canonical, portable, save, load_json = individual.digest, individual.canonical, individual.portable, individual.save, individual.load_json
DEPENDENCIES = {
    'root_prism_free_f0_incidence_row_loop.py': '5f4f536052f97ba725f10ebb77e7f55b0e94c57947e643e97d7df6915e762352',
    'root_prism_free_f0_shared_row_separator.py': '7d8f3324826c1fa7fa05e79dbbee7c6e16b064dd01ef5e548160f6a7fe04368a',
    'root_prism_free_f0_signed_threshold.py': '605b4984ef30374950d19eb66fe37465026e0719fa3a6cb73bfbe68c92e0b1ad',
    'root_prism_free_f0_symmetric_selector_cut.py': '15ec937609b7de44b808e9de7053bb9ee080ddf732a3defd2b23577c026fe274'}
SEED = LOGS/'f0-symmetric-selector-cut-certificate.json.gz'
SEED_SHA = '3aea5e48c4a35eb7e023708231f3dbf585634c25de25484f364276041260f846'
CONTROLS = LOGS/'f0-signed-threshold-controls.json'
LIMITS = dict(individual.LIMITS, shared_LP_seconds=60)


def check_sources():
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    individual.checked_sources()
    shared.check_sources()
    assert digest(SEED) == SEED_SHA
    controls = load_json(CONTROLS)
    assert controls['source_sha256'] == DEPENDENCIES['root_prism_free_f0_signed_threshold.py']
    assert controls['status'].endswith('PASS')
    return controls


def signed_cut(terms, origin):
    assert terms == sorted(terms) and len({a for a, _ in terms}) == len(terms)
    assert all(type(a) is int and 0 <= a < 480 and type(c) is int and c for a, c in terms)
    divisor = gcd(*(abs(c) for _, c in terms))
    assert divisor > 0
    normalized = [[a, c//divisor] for a, c in terms]
    return {'signed_coefficients': normalized, 'origin': origin,
            'predicate_sha256': hashlib.sha256(canonical(normalized)).hexdigest()}


def add_signed(cnf, registry, encodings, cut):
    keys = {record['predicate_sha256']: i for i, record in enumerate(registry)}
    if cut['predicate_sha256'] in keys:
        return keys[cut['predicate_sha256']], False
    clauses, top, record = signed.signed_atmost_zero([(a+1, c) for a, c in cut['signed_coefficients']],
        cnf.nv, maximum_states=LIMITS['maximum_threshold_states_per_cut'])
    if top > LIMITS['maximum_formula_variables'] or len(cnf.clauses)+len(clauses) > LIMITS['maximum_formula_clauses']:
        raise RuntimeError('signed formula resource limit; no partial cut added')
    record.update(cut_index=len(registry), clause_start=len(cnf.clauses),
                  clause_body_sha256=hashlib.sha256(canonical(clauses)).hexdigest())
    cnf.extend(clauses)
    assert cnf.nv == top
    registry.append(cut); encodings.append(record)
    return len(registry)-1, True


def signed_outcomes(selected, registry):
    chosen = set(selected)
    return [{'cut_index': i, 'signed_sum': sum(c for a, c in cut['signed_coefficients'] if a in chosen)}
            for i, cut in enumerate(registry)]


def inspect(selected, context, rows, symmetric):
    domain, records, old_cuts, old_clauses, _, _, _, _ = context
    first = individual.inspect(selected, domain, records, old_cuts, old_clauses, rows)
    values = signed_outcomes(selected, symmetric)
    assert all(value['signed_sum'] <= 0 for value in values)
    return {'selected_signature_ids': selected, 'individual_row_cut_inspection': first,
            'symmetric_selector_cut_outcomes': values, 'full_graph_constructed': False}


def initial(complete_replay=False):
    controls = check_sources()
    cnf, rows, row_encodings, row_aliases, old_formula, context, _, _ = individual.initial(complete_replay)
    certificate = load_json(SEED)
    assert canonical(seed.calculate()) == canonical(certificate)
    symmetric, symmetric_encodings = [], []
    for transport in certificate['transported_cuts']:
        terms = sorted(transport['positive_terms']+[[a, -w] for a, w in transport['negative_side_positive_weights']])
        cut = signed_cut(terms, {'kind': 'published symmetric selector cut',
            'certificate_sha256': SEED_SHA, 'core_action_index': transport['core_action_index']})
        _, added = add_signed(cnf, symmetric, symmetric_encodings, cut)
        assert added
    assert len(symmetric) == 12
    _, _, _, _, triples, targets, neighbors, actions = context
    helper_control = shared.seed_control(triples, targets, neighbors, actions)
    selected = certificate['selected_signature_ids_for_potential_support_and_allocation_only']
    outcomes = signed_outcomes(selected, symmetric)
    assert any(value['signed_sum'] == 2 for value in outcomes)
    formula = {'primary_variables': 480, 'variables': cnf.nv, 'clauses': len(cnf.clauses),
        'literal_occurrences': sum(map(len, cnf.clauses)), 'individual_initial_formula': old_formula,
        'old_twelve_direct_cuts_retained': True, 'individual_weighted_cuts': len(rows),
        'symmetric_signed_cuts': len(symmetric),
        'added_signed_clauses': len(cnf.clauses)-old_formula['clauses'],
        'added_signed_auxiliary_variables': cnf.nv-old_formula['variables'],
        'previous_all_box_incidence_cut_values': outcomes,
        'all480_selectors_free': True, 'fixed_second_component_or_incidence': False}
    return cnf, rows, row_encodings, symmetric, symmetric_encodings, formula, context, helper_control, controls


def prepare(output, cnf_path):
    assert not output.exists() and not cnf_path.exists()
    started = time.monotonic()
    cnf, rows, row_encodings, symmetric, symmetric_encodings, formula, _, helper_control, controls = initial()
    cnf.to_file(cnf_path)
    report = {'status': 'free480 individual/shared-row continuation prepared; no main query',
        'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': DEPENDENCIES,
        'published_signed_certificate_sha256': SEED_SHA,
        'signed_encoder_controls_sha256': digest(CONTROLS), 'signed_encoder_controls': controls,
        'dynamic_shared_helper_control': helper_control,
        'limits': LIMITS, 'formula': formula,
        'initial_individual_cuts': rows, 'initial_individual_encodings': row_encodings,
        'initial_symmetric_cuts': symmetric, 'initial_symmetric_encodings': symmetric_encodings,
        'cnf': str(cnf_path), 'cnf_sha256': digest(cnf_path), 'cnf_bytes': cnf_path.stat().st_size,
        'scope': 'all first-incidence selections for component0 in globallyP=F=0 split18+18; second component unrestricted',
        'visitation_blocks_or_graph_symmetry': False,
        'initial_and_future_cuts_only_from_exact_potentials': True,
        'shared_query_only_after_complete60_exact_individual_boxes': True,
        'stop_conditions': ['incremental UNSAT requiring fresh proof', 'UNKNOWN or uncertified result',
            'exact symmetric box feasibility', 'resource/time/incidence limit', 'error'],
        'optimizer_or_incidence_solver_called': False, 'seconds': time.monotonic()-started}
    output.write_bytes(gzip.compress(canonical(report)+b'\n', mtime=0))
    print(json.dumps({k: v for k, v in report.items() if k not in
        ('initial_individual_cuts', 'initial_individual_encodings', 'initial_symmetric_cuts', 'initial_symmetric_encodings')}, indent=2), flush=True)


def checked_preparation(path, require_cnf=False):
    report = load_json(path)
    assert report['source_sha256'] == digest(Path(__file__))
    assert report['dependency_source_hashes'] == DEPENDENCIES and report['limits'] == LIMITS
    assert check_sources() == report['signed_encoder_controls']
    assert digest(CONTROLS) == report['signed_encoder_controls_sha256']
    assert report['published_signed_certificate_sha256'] == SEED_SHA
    if require_cnf:
        assert digest(Path(report['cnf'])) == report['cnf_sha256']
    return report


def counters(step, cnf, rows, symmetric):
    step.update(individual_cut_count_after=len(rows), symmetric_cut_count_after=len(symmetric),
                variables_after=cnf.nv, clauses_after=len(cnf.clauses))


def append_individual(cnf, registry, encodings, candidates, solver=None):
    maps = []
    for cut in candidates:
        before = len(cnf.clauses)
        index, added = individual.add_cut(cnf, registry, encodings, cut)
        if solver is not None and added:
            solver.append_formula(cnf.clauses[before:])
        maps.append({'origin': cut['origin'], 'registry_index': index, 'new_cut': added})
    return maps


def symmetric_candidates(lifted, iteration, shared_sha):
    return [signed_cut(transport['signed_coefficients'], {'kind': 'loop exact shared-row lift',
        'iteration': iteration, 'shared_result_sha256': shared_sha,
        'core_action_index': transport['core_action_index']}) for transport in lifted['transported_cuts']]


def run(preparation_path, directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic()
    deadline = started+LIMITS['overall_seconds']
    output = directory/'result.json'
    report = {'status': 'RUNNING: free480 individual/shared-row loop',
        'source_sha256': digest(Path(__file__)), 'preparation': portable(preparation_path),
        'preparation_sha256': digest(preparation_path), 'limits': LIMITS, 'iterations': [],
        'fixed_incidence_or_second_component': False, 'visitation_blocks': False,
        'whole_component_excluded': False, 'full_graph_completion': False}
    save(output, report)
    cnf = None
    row_registry = row_encodings = signed_registry = signed_encodings = None
    try:
        prepared = checked_preparation(preparation_path, True)
        cnf = CNF(from_file=prepared['cnf'])
        assert (cnf.nv, len(cnf.clauses)) == (prepared['formula']['variables'], prepared['formula']['clauses'])
        row_registry = prepared['initial_individual_cuts']; row_encodings = prepared['initial_individual_encodings']
        signed_registry = prepared['initial_symmetric_cuts']; signed_encodings = prepared['initial_symmetric_encodings']
        domain, records = BASE.load(0)
        old_cuts, old_clauses, _ = individual.old.load_cuts()
        triples, targets, neighbors, _, actions, _ = individual.box.load()
        context = (domain, records, old_cuts, old_clauses, triples, targets, neighbors, actions)
        with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=False) as solver:
            report['bootstrap_and_input_checks_seconds'] = time.monotonic()-started
            for iteration in range(LIMITS['maximum_incidences']):
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    report['status'] = 'STOP: overall budget; unresolved'
                    break
                step_dir = directory/f'iteration{iteration:02d}'
                step_dir.mkdir()
                step = {'iteration': iteration, 'status': 'RUNNING: SAT',
                    'individual_cut_count_before': len(row_registry), 'symmetric_cut_count_before': len(signed_registry),
                    'variables_before': cnf.nv, 'clauses_before': len(cnf.clauses),
                    'requested_SAT_seconds': min(LIMITS['SAT_seconds_per_call'], remaining)}
                report['iterations'].append(step); save(output, report)
                solver.clear_interrupt()
                sat_started = time.monotonic()
                timer = Timer(step['requested_SAT_seconds'], solver.interrupt); timer.start()
                try:
                    answer = solver.solve_limited(expect_interrupt=True)
                finally:
                    timer.cancel()
                step['SAT_seconds'] = time.monotonic()-sat_started
                step['cumulative_solver_statistics'] = solver.accum_stats()
                if answer is None:
                    step['status'] = 'UNKNOWN: SAT call budget'
                    report['status'] = 'UNKNOWN: SAT call budget; no exclusion'
                    break
                if not answer:
                    step['status'] = 'UNSAT: incremental answer, uncertified'
                    report['status'] = 'UNSAT_UNCERTIFIED: fresh final-formula proof required'
                    break
                positive = {v for v in solver.get_model() if v > 0}
                selected = [a for a in range(480) if a+1 in positive]
                candidate = inspect(selected, context, row_registry, signed_registry)
                candidate_path = step_dir/'candidate.json'; save(candidate_path, candidate)
                step.update(status='SAT: exact candidate; individual rows running',
                            candidate=portable(candidate_path), candidate_sha256=digest(candidate_path))
                save(output, report)
                rows_path = step_dir/'individual-rows.json'
                local = individual.separate(selected, triples, targets, neighbors, actions,
                                            rows_path, digest(candidate_path), deadline)
                individual.check_rows(local, selected, triples, targets, neighbors, actions)
                step.update(individual_rows=portable(rows_path), individual_rows_sha256=digest(rows_path),
                    individual_status=local['status'], exact_individual_obstructions=local['exact_integer_obstructions'],
                    exact_individual_boxes=local['exact_rational_boxes'])
                generated = individual.row_cut_candidates(local, iteration, triples, targets, neighbors)
                step['individual_generated_transports'] = len(generated)
                step['individual_transport_maps'] = []
                for cut in generated:
                    try:
                        maps = append_individual(cnf, row_registry, row_encodings, [cut], solver)
                    except RuntimeError as error:
                        step['resource_error'] = str(error); break
                    step['individual_transport_maps'].extend(maps)
                step['new_individual_cuts'] = sum(item['new_cut'] for item in step['individual_transport_maps'])
                counters(step, cnf, row_registry, signed_registry)
                save(output, report)
                if 'resource_error' in step:
                    step['status'] = 'STOP: individual-cut resource limit'
                    report['status'] = 'STOP: encoding resource limit; unresolved'
                    break
                if not local['status'].startswith('COMPLETE:'):
                    step['status'] = local['status']; report['status'] = local['status']+'; unresolved'
                    break
                if step['new_individual_cuts']:
                    step['status'] = 'SAT incidence rejected by exact individual-row cuts'
                else:
                    assert local['exact_integer_obstructions'] == 0 and local['exact_rational_boxes'] == 60
                    remaining = deadline-time.monotonic()
                    if remaining <= 0:
                        step['status'] = 'STOP: budget before shared-edge query'
                        report['status'] = 'STOP: overall budget; unresolved'
                        break
                    shared_path = step_dir/'shared-rows.json'
                    common = shared.query(selected, triples, targets, neighbors, shared_path,
                        digest(candidate_path), min(LIMITS['shared_LP_seconds'], remaining))
                    shared.replay(common, selected, triples, targets, neighbors)
                    step.update(shared_rows=portable(shared_path), shared_rows_sha256=digest(shared_path),
                                shared_status=common['status'])
                    if common['exact_linear_feasibility']:
                        step['status'] = 'SAT incidence with exact rational symmetric row box'
                        report['status'] = 'STOP: exact symmetric row-box feasible; no graph construction'
                        break
                    if not common['exact_fixed_design_infeasibility']:
                        step['status'] = common['status']; report['status'] = common['status']+'; unresolved'
                        break
                    lifted = shared.lift(selected, common['fixed_capacity_potentials']['integer_potentials60_by18'],
                                         triples, targets, neighbors, actions)
                    lift_path = step_dir/'symmetric-cut.json'; save(lift_path, lifted)
                    step.update(symmetric_lift=portable(lift_path), symmetric_lift_sha256=digest(lift_path),
                                symmetric_transport_maps=[])
                    candidates = symmetric_candidates(lifted, iteration, digest(shared_path))
                    for cut in candidates:
                        before = len(cnf.clauses)
                        try:
                            index, added = add_signed(cnf, signed_registry, signed_encodings, cut)
                        except RuntimeError as error:
                            step['resource_error'] = str(error); break
                        if added:
                            solver.append_formula(cnf.clauses[before:])
                        step['symmetric_transport_maps'].append({'origin': cut['origin'], 'registry_index': index, 'new_cut': added})
                    step['new_symmetric_cuts'] = sum(item['new_cut'] for item in step['symmetric_transport_maps'])
                    counters(step, cnf, row_registry, signed_registry)
                    if 'resource_error' in step:
                        step['status'] = 'STOP: signed-cut resource limit'
                        report['status'] = 'STOP: encoding resource limit; unresolved'
                        break
                    assert step['new_symmetric_cuts'] > 0
                    step['status'] = 'SAT incidence rejected by exact shared-row selector cuts'
                save(output, report)
                print(json.dumps({'iteration': iteration, 'status': step['status'],
                    'new_individual_cuts': step['new_individual_cuts'],
                    'new_symmetric_cuts': step.get('new_symmetric_cuts', 0),
                    'elapsed_seconds': time.monotonic()-started}), flush=True)
            else:
                report['status'] = 'STOP: incidence limit; unresolved'
    except Exception as error:
        report.update(status='ERROR: stopped without unchecked conclusion', error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        if cnf is not None and row_registry is not None and signed_registry is not None:
            path = directory/'final.cnf'; cnf.to_file(path)
            report.update(final_cnf=portable(path), final_cnf_sha256=digest(path),
                final_variables=cnf.nv, final_clauses=len(cnf.clauses),
                final_individual_cut_count=len(row_registry), final_symmetric_cut_count=len(signed_registry),
                final_weighted_cut_count=len(row_registry)+len(signed_registry))
            for name, data in [('individual-registry', row_registry), ('individual-encodings', row_encodings),
                               ('symmetric-registry', signed_registry), ('symmetric-encodings', signed_encodings)]:
                path = directory/(name+'.json'); save(path, data)
                report[name] = portable(path); report[name+'_sha256'] = digest(path)
        report['elapsed_seconds'] = time.monotonic()-started
        report['cooperative_overall_overrun_seconds'] = max(0, report['elapsed_seconds']-LIMITS['overall_seconds'])
        report['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(output, report)
    print(json.dumps({k: v for k, v in report.items() if k != 'iterations'}, indent=2), flush=True)


def reconstruct(preparation_path, result_path=None):
    prepared = checked_preparation(preparation_path)
    cnf, row_registry, row_encodings, signed_registry, signed_encodings, formula, context, helper_control, _ = initial(True)
    for actual, key in [(row_registry, 'initial_individual_cuts'), (row_encodings, 'initial_individual_encodings'),
                        (signed_registry, 'initial_symmetric_cuts'), (signed_encodings, 'initial_symmetric_encodings')]:
        assert actual == prepared[key]
    assert formula == prepared['formula'] and helper_control == prepared['dynamic_shared_helper_control']
    with tempfile.TemporaryDirectory(prefix='conway-f0-symmetric-initial-') as directory:
        path = Path(directory)/'initial.cnf'; cnf.to_file(path)
        assert digest(path) == prepared['cnf_sha256']
    initial_report = {'status': 'cold complete initial incidence/signed-cut formula and dynamic shared helper replay PASS',
        'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation_path),
        'cnf_sha256': prepared['cnf_sha256'], 'variables': cnf.nv, 'clauses': len(cnf.clauses),
        'optimizer_or_solver_called': False}
    if result_path is None:
        return cnf, row_registry+signed_registry, row_encodings+signed_encodings, initial_report
    result = load_json(result_path)
    assert not result['status'].startswith('RUNNING:')
    assert result['source_sha256'] == digest(Path(__file__)) and result['preparation_sha256'] == digest(preparation_path)
    assert result['limits'] == LIMITS
    _, _, _, _, triples, targets, neighbors, actions = context
    checked_candidates = exact_rows = exact_boxes = shared_rays = shared_points = 0
    for iteration, step in enumerate(result['iterations']):
        assert step['iteration'] == iteration
        assert step['individual_cut_count_before'] == len(row_registry) and step['symmetric_cut_count_before'] == len(signed_registry)
        assert (step['variables_before'], step['clauses_before']) == (cnf.nv, len(cnf.clauses))
        if 'candidate' not in step:
            assert step['status'].startswith(('UNSAT:', 'UNKNOWN:')) and iteration == len(result['iterations'])-1
            continue
        candidate_path = ROOT/step['candidate']; assert digest(candidate_path) == step['candidate_sha256']
        candidate = load_json(candidate_path); selected = candidate['selected_signature_ids']
        assert inspect(selected, context, row_registry, signed_registry) == candidate
        checked_candidates += 1
        rows_path = ROOT/step['individual_rows']; assert digest(rows_path) == step['individual_rows_sha256']
        local = load_json(rows_path); assert local['candidate_sha256'] == digest(candidate_path)
        individual.check_rows(local, selected, triples, targets, neighbors, actions)
        assert local['status'] == step['individual_status']
        assert local['exact_integer_obstructions'] == step['exact_individual_obstructions']
        assert local['exact_rational_boxes'] == step['exact_individual_boxes']
        exact_rows += local['exact_integer_obstructions']; exact_boxes += local['exact_rational_boxes']
        generated = individual.row_cut_candidates(local, iteration, triples, targets, neighbors)
        assert len(generated) == step['individual_generated_transports']
        count = len(step['individual_transport_maps'])
        assert count <= len(generated)
        if count < len(generated):
            assert 'resource_error' in step and iteration == len(result['iterations'])-1
        maps = append_individual(cnf, row_registry, row_encodings, generated[:count])
        assert maps == step['individual_transport_maps']
        assert sum(item['new_cut'] for item in maps) == step['new_individual_cuts']
        if 'shared_rows' in step:
            assert not generated and local['exact_rational_boxes'] == 60 and local['all60_processed']
            path = ROOT/step['shared_rows']; assert digest(path) == step['shared_rows_sha256']
            common = load_json(path); assert common['candidate_sha256'] == digest(candidate_path)
            shared.replay(common, selected, triples, targets, neighbors)
            assert common['status'] == step['shared_status']
            shared_rays += common['exact_fixed_design_infeasibility']; shared_points += common['exact_linear_feasibility']
            if common['exact_fixed_design_infeasibility']:
                lift_path = ROOT/step['symmetric_lift']; assert digest(lift_path) == step['symmetric_lift_sha256']
                lifted = shared.lift(selected, common['fixed_capacity_potentials']['integer_potentials60_by18'],
                                     triples, targets, neighbors, actions)
                assert lifted == load_json(lift_path)
                candidates = symmetric_candidates(lifted, iteration, digest(path))
                count = len(step['symmetric_transport_maps']); assert count <= len(candidates)
                if count < len(candidates):
                    assert 'resource_error' in step and iteration == len(result['iterations'])-1
                maps = []
                for cut in candidates[:count]:
                    index, added = add_signed(cnf, signed_registry, signed_encodings, cut)
                    maps.append({'origin': cut['origin'], 'registry_index': index, 'new_cut': added})
                assert maps == step['symmetric_transport_maps']
                assert sum(item['new_cut'] for item in maps) == step['new_symmetric_cuts']
        assert step['individual_cut_count_after'] == len(row_registry) and step['symmetric_cut_count_after'] == len(signed_registry)
        assert (step['variables_after'], step['clauses_after']) == (cnf.nv, len(cnf.clauses))
    assert result['final_individual_cut_count'] == len(row_registry) and result['final_symmetric_cut_count'] == len(signed_registry)
    assert result['final_weighted_cut_count'] == len(row_registry)+len(signed_registry)
    for name, data in [('individual-registry', row_registry), ('individual-encodings', row_encodings),
                       ('symmetric-registry', signed_registry), ('symmetric-encodings', signed_encodings)]:
        path = ROOT/result[name]
        assert digest(path) == result[name+'_sha256'] and load_json(path) == data
    assert (cnf.nv, len(cnf.clauses)) == (result['final_variables'], result['final_clauses'])
    with tempfile.TemporaryDirectory(prefix='conway-f0-symmetric-final-') as directory:
        path = Path(directory)/'final.cnf'; cnf.to_file(path)
        assert digest(path) == result['final_cnf_sha256']
    report = {'status': 'cold complete final formula, candidate prefixes, exact individual/shared witnesses and lifts replay PASS',
        'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation_path),
        'result_sha256': digest(result_path), 'final_cnf_sha256': result['final_cnf_sha256'],
        'checked_candidates': checked_candidates, 'exact_individual_obstructions': exact_rows,
        'exact_individual_boxes': exact_boxes, 'exact_shared_rays': shared_rays, 'exact_shared_points': shared_points,
        'individual_cut_count': len(row_registry), 'symmetric_cut_count': len(signed_registry),
        'variables': cnf.nv, 'clauses': len(cnf.clauses),
        'optimizer_or_solver_called': False, 'UNSAT_proof_checked': False,
        'whole_component_excluded': False, 'full_graph_completion': False}
    return cnf, row_registry+signed_registry, row_encodings+signed_encodings, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--output', type=Path, required=True); prep.add_argument('--cnf', type=Path, required=True)
    execute = commands.add_parser('run')
    execute.add_argument('--preparation', type=Path, required=True); execute.add_argument('--directory', type=Path, required=True)
    check = commands.add_parser('replay')
    check.add_argument('--preparation', type=Path, required=True); check.add_argument('--result', type=Path)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output.resolve(), args.cnf.resolve())
    elif args.command == 'run':
        run(args.preparation.resolve(), args.directory.resolve())
    else:
        assert not args.output.exists()
        _, _, _, report = reconstruct(args.preparation.resolve(), args.result.resolve() if args.result else None)
        save(args.output, report); print(json.dumps(report, indent=2), flush=True)
