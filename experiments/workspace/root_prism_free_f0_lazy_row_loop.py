"""Free480 continuation using exact lazy consequences of proved PB cuts.

Only the original incidence/direct-cut CNF and primary explanation
clauses enter SAT. Every registered integer inequality is evaluated on
each candidate before any row LP. A violated inequality contributes two
checked explanation families, with all12 verified core transports.
There are no visitation blocks, fixed incidences or graph symmetries.
Incremental UNSAT requires a separate fresh proof and cold DRAT replay.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import resource
import tempfile
from threading import Timer
import time

from pysat.formula import CNF
from pysat.solvers import Solver

import root_prism_free_f0_lazy_clauses as lazy


ROOT, LOGS, BASE = lazy.ROOT, lazy.LOGS, lazy.BASE
individual, shared, registry = lazy.individual, lazy.shared, lazy.registry
digest, canonical, portable, save, load_json = lazy.digest, lazy.canonical, lazy.portable, lazy.save, lazy.load_json
DEPENDENCIES = {
    'root_prism_free_f0_lazy_clauses.py': 'cef5448b012be57277b87297d2e3ec2c017ccea1336080f4c40c2594f2ab7640',
    'root_prism_free_f0_lazy_registry.py': '9a9a2c40241dc3899b9692568a2ee4127d17d5a4b8c33972dfd9b59a57e43478',
    'root_prism_free_f0_incidence_row_loop.py': '5f4f536052f97ba725f10ebb77e7f55b0e94c57947e643e97d7df6915e762352',
    'root_prism_free_f0_shared_deficit_separator.py': '6bc6944ed00713d384251ab54e54684e6f5ea29300f9ff243df5282f522375bf'}
CONTROLS = LOGS/'f0-lazy-clauses-controls.json'
CONTROLS_SHA = 'ea051c6f6fe6d573e785fd72a4ff21a3b31123db8e53e0ed992105036647bd32'
LIMITS = {'maximum_SAT_refinement_calls': 500, 'maximum_row_passes': 20,
          'SAT_seconds_per_call': 10, 'row_pass_seconds': 60, 'shared_LP_seconds': 60,
          'overall_seconds': 180, 'maximum_formula_variables': 1000000,
          'maximum_formula_clauses': 2000000}


def save_gzip(path, data):
    assert not path.exists()
    path.write_bytes(gzip.compress(canonical(data)+b'\n', mtime=0))


def check_sources():
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    lazy.check_sources()
    assert digest(CONTROLS) == CONTROLS_SHA
    controls = load_json(CONTROLS)
    assert controls['source_sha256'] == DEPENDENCIES['root_prism_free_f0_lazy_clauses.py']
    assert controls['status'].startswith('PASS:') and not controls['optimizer_or_solver_called']
    assert LIMITS['row_pass_seconds'] == individual.LIMITS['row_pass_seconds']
    assert (LIMITS['maximum_formula_clauses'], LIMITS['maximum_formula_variables']) == (
        lazy.MAXIMUM_CLAUSES, lazy.MAXIMUM_VARIABLES)
    return controls


def formula(state):
    return {'primary_variables': 480, 'variables': state.cnf.nv,
        'clauses': len(state.cnf.clauses), 'literal_occurrences': sum(map(len, state.cnf.clauses)),
        'base_variables': state.base_nv, 'base_clauses': state.base_count,
        'base_body_sha256': state.base_body_sha256,
        'registered_individual_inequalities': len(state.rows),
        'registered_signed_inequalities': len(state.symmetric),
        'explanation_clauses': len(state.records), 'new_auxiliary_variables': 0,
        'all480_selectors_free': True, 'fixed_second_component_or_incidence': False,
        'encoding': 'necessary exact independent and population60 clause explanations only',
        'registry_not_claimed_equivalent_to_finite_explanation_CNF': True}


def prepare(output, cnf_path):
    assert not output.exists() and not cnf_path.exists()
    started = time.monotonic()
    controls = check_sources()
    state, _, seed = lazy.initial()
    state.cnf.to_file(cnf_path)
    report = {'status': 'free480 lazy732-cut continuation prepared; no incidence/LP query',
        'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': DEPENDENCIES,
        'exact_registry': portable(lazy.REGISTRY), 'exact_registry_sha256': lazy.REGISTRY_SHA,
        'adapter_controls_sha256': CONTROLS_SHA, 'adapter_controls': controls,
        'limits': LIMITS, 'formula': formula(state), 'seed_control': seed,
        'initial_explanation_records': state.records,
        'initial_snapshot': state.snapshot(),
        'cnf': str(cnf_path), 'cnf_sha256': digest(cnf_path), 'cnf_bytes': cnf_path.stat().st_size,
        'scope': 'all first-incidence selections for component0 in globallyP=F=0 split18+18; second component unrestricted',
        'no_visitation_blocks_or_graph_symmetry': True,
        'complete_registry_evaluated_before_any_LP': True,
        'row_LP_only_after_all_registry_inequalities_hold': True,
        'shared_LP_only_after_complete60_exact_individual_boxes': True,
        'stop_conditions': ['incremental UNSAT requiring fresh proof', 'UNKNOWN or uncertified result',
            'exact symmetric row-box feasibility', 'resource/time/SAT-call/row-pass limit', 'error'],
        'no_Gram_equality_shifts': True, 'optimizer_or_incidence_solver_called': False,
        'seconds': time.monotonic()-started}
    save_gzip(output, report)
    print(json.dumps({k: v for k, v in report.items() if k not in
        ('initial_explanation_records', 'seed_control')}, indent=2), flush=True)


def checked_preparation(path, require_cnf=False):
    report = load_json(path)
    assert report['source_sha256'] == digest(Path(__file__))
    assert report['dependency_source_hashes'] == DEPENDENCIES and report['limits'] == LIMITS
    assert check_sources() == report['adapter_controls']
    assert report['adapter_controls_sha256'] == CONTROLS_SHA
    assert report['exact_registry_sha256'] == lazy.REGISTRY_SHA
    if require_cnf:
        assert digest(Path(report['cnf'])) == report['cnf_sha256']
    return report


def input_state(prepared):
    """Load a hash-bound preparation; do not regenerate ancestor formulas."""
    proved = load_json(lazy.REGISTRY)
    loaded = CNF(from_file=prepared['cnf'])
    base = CNF(from_clauses=loaded.clauses[:56994])
    state = lazy.State(base, proved['individual_cuts'], proved['symmetric_cuts'],
                       proved['verified_core_actions'], proved['population_premise'])
    assert state.base_body_sha256 == prepared['formula']['base_body_sha256']
    state.append_records(prepared['initial_explanation_records'])
    assert state.cnf.nv == loaded.nv and state.cnf.clauses == loaded.clauses
    assert state.snapshot() == prepared['initial_snapshot'] and formula(state) == prepared['formula']
    domain, records = BASE.load(0)
    old_cuts, old_clauses, _ = individual.old.load_cuts()
    triples, targets, neighbors, _, actions, _ = individual.box.load()
    assert triples == domain['signature_domain'] and actions == state.actions
    return state, (domain, records, old_cuts, old_clauses, triples, targets, neighbors, actions)


def inspect_candidate(selected, state, context):
    domain, records, old_cuts, old_clauses, _, _, _, _ = context
    point = individual.old.inspect(selected, domain, records, old_cuts, old_clauses)
    assert len(selected) == 60 and selected == sorted(set(selected))
    chosen = set(selected)
    assert all(not lazy.is_false(record['clause'], chosen) for record in state.records)
    values = state.evaluate(selected)
    return {'selected_signature_ids': selected, 'original_incidence_and_twelve_direct_cuts': point,
        'actual_primary_explanation_prefix_checked': len(state.records),
        'actual_prefix_snapshot': state.snapshot(), 'registry_evaluation': values,
        'all_registered_PB_evaluated_before_any_all_cut_inspector_or_LP': True,
        'full_graph_or_exterior_graph_constructed': False}


def symmetric_candidates(lifted, iteration, shared_sha):
    return [registry.signed_cut(t['signed_coefficients'], {
        'kind': 'lazy loop exact shared-row lift', 'iteration': iteration,
        'shared_result_sha256': shared_sha, 'core_action_index': t['core_action_index']})
        for t in lifted['transported_cuts']]


def explain_candidate(state, selected, source, path, solver=None):
    evaluated = state.evaluate(selected)
    assert evaluated['violations']
    records, summary = state.proposals(selected, evaluated['violations'], source)
    assert summary['new_clauses_false_on_source'] > 0
    payload = {'source': source, 'registry_evaluation': evaluated,
               'summary': summary, 'records': records}
    save_gzip(path, payload)
    try:
        state.append_records(records, solver)
        error = None
    except RuntimeError as failure:
        error = str(failure)
    return {'explanation_batch': portable(path), 'explanation_batch_sha256': digest(path),
            'explanation_summary': summary, 'explanation_batch_added': error is None,
            'explanation_resource_error': error}


def add_row_cuts(state, local, iteration, context):
    _, _, _, _, triples, targets, neighbors, _ = context
    candidates = individual.row_cut_candidates(local, iteration, triples, targets, neighbors)
    maps = [state.add_cut('individual', cut, context) for cut in candidates]
    return maps


def finish_step(step, state, row_passes):
    step['after'] = state.snapshot()
    step['row_passes_after'] = row_passes


def run(preparation_path, directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic(); deadline = started+LIMITS['overall_seconds']
    output = directory/'result.json'
    report = {'status': 'RUNNING: free480 lazy individual/shared-row loop',
        'source_sha256': digest(Path(__file__)), 'preparation': portable(preparation_path),
        'preparation_sha256': digest(preparation_path), 'limits': LIMITS,
        'iterations': [], 'fixed_incidence_or_second_component': False,
        'visitation_blocks': False, 'whole_component_excluded': False, 'full_graph_completion': False}
    save(output, report)
    state, context, row_passes = None, None, 0
    try:
        prepared = checked_preparation(preparation_path, True)
        state, context = input_state(prepared)
        _, _, _, _, triples, targets, neighbors, actions = context
        with Solver(name='glucose4', bootstrap_with=state.cnf.clauses, with_proof=False) as solver:
            report['bootstrap_and_input_checks_seconds'] = time.monotonic()-started
            for iteration in range(LIMITS['maximum_SAT_refinement_calls']):
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    report['status'] = 'STOP: overall budget; unresolved'; break
                step_dir = directory/f'iteration{iteration:03d}'; step_dir.mkdir()
                step = {'iteration': iteration, 'status': 'RUNNING: SAT',
                        'before': state.snapshot(), 'row_passes_before': row_passes,
                        'requested_SAT_seconds': min(LIMITS['SAT_seconds_per_call'], remaining)}
                report['iterations'].append(step); save(output, report)
                solver.clear_interrupt()
                sat_started = time.monotonic()
                timer = Timer(step['requested_SAT_seconds'], solver.interrupt); timer.start()
                try:
                    answer = solver.solve_limited(expect_interrupt=True)
                finally:
                    timer.cancel()
                step.update(SAT_seconds=time.monotonic()-sat_started,
                            cumulative_solver_statistics=solver.accum_stats())
                if answer is None:
                    step['status'] = 'UNKNOWN: SAT call budget'
                    report['status'] = 'UNKNOWN: SAT call budget; no exclusion'
                    finish_step(step, state, row_passes); break
                if not answer:
                    step['status'] = 'UNSAT: incremental answer, uncertified'
                    report['status'] = 'UNSAT_UNCERTIFIED: fresh final-formula proof required'
                    finish_step(step, state, row_passes); break
                positive = {v for v in solver.get_model() if v > 0}
                # Inspect the actual returned full assignment, then independently
                # replay the primary constraints in the saved candidate record.
                assert all(any((lit > 0) == (abs(lit) in positive) for lit in clause)
                           for clause in state.cnf.clauses)
                selected = [a for a in range(480) if a+1 in positive]
                candidate = inspect_candidate(selected, state, context)
                candidate_path = step_dir/'candidate.json'; save(candidate_path, candidate)
                step.update(candidate=portable(candidate_path), candidate_sha256=digest(candidate_path),
                    returned_full_CNF_assignment_checked=True,
                    registered_PB_violations=len(candidate['registry_evaluation']['violations']))
                save(output, report)
                if candidate['registry_evaluation']['violations']:
                    source = {'kind': 'lazy registered PB violation', 'iteration': iteration,
                              'candidate_sha256': digest(candidate_path)}
                    step.update(explain_candidate(state, selected, source, step_dir/'explanations.json.gz', solver))
                    if step['explanation_resource_error']:
                        step['status'] = 'STOP: explanation resource limit'
                        report['status'] = 'STOP: explanation resource limit; unresolved'
                    else:
                        step['status'] = 'SAT candidate rejected by proved registered PB clauses; no row LP'
                    finish_step(step, state, row_passes); save(output, report)
                    print(json.dumps({'iteration': iteration, 'status': step['status'],
                        'new_clauses': step['explanation_summary']['new_clauses'],
                        'elapsed_seconds': time.monotonic()-started}), flush=True)
                    if step['explanation_resource_error']:
                        break
                    continue

                # This is the only route to a row LP. No old all-cut inspector
                # rejects a candidate before the exact lazy evaluation above.
                assert candidate['registry_evaluation']['all_registered_inequalities_hold']
                if row_passes >= LIMITS['maximum_row_passes'] or time.monotonic() >= deadline:
                    step['status'] = 'STOP: budget before row pass'
                    report['status'] = 'STOP: row-pass or overall budget; unresolved'
                    finish_step(step, state, row_passes); break
                row_passes += 1
                step['status'] = 'SAT: all registry inequalities hold; individual rows running'; save(output, report)
                rows_path = step_dir/'individual-rows.json'
                local = individual.separate(selected, triples, targets, neighbors, actions,
                    rows_path, digest(candidate_path), deadline)
                individual.check_rows(local, selected, triples, targets, neighbors, actions)
                step.update(individual_rows=portable(rows_path), individual_rows_sha256=digest(rows_path),
                    individual_status=local['status'], exact_individual_obstructions=local['exact_integer_obstructions'],
                    exact_individual_boxes=local['exact_rational_boxes'])
                step['individual_transport_maps'] = add_row_cuts(state, local, iteration, context)
                step['new_individual_cuts'] = sum(item['new_cut'] for item in step['individual_transport_maps'])
                save(output, report)
                if local['exact_integer_obstructions']:
                    assert step['new_individual_cuts'] > 0
                    source = {'kind': 'lazy newly proved individual-row cut', 'iteration': iteration,
                        'candidate_sha256': digest(candidate_path), 'row_report_sha256': digest(rows_path)}
                    step.update(explain_candidate(state, selected, source, step_dir/'explanations.json.gz', solver))
                    if step['explanation_resource_error']:
                        step['status'] = 'STOP: explanation resource limit'
                        report['status'] = 'STOP: explanation resource limit; unresolved'
                    elif not local['status'].startswith('COMPLETE:'):
                        step['status'] = local['status']; report['status'] = local['status']+'; unresolved'
                    else:
                        step['status'] = 'SAT incidence rejected by new exact individual-row cuts'
                    finish_step(step, state, row_passes); save(output, report)
                    print(json.dumps({'iteration': iteration, 'status': step['status'],
                        'new_individual_cuts': step['new_individual_cuts'],
                        'new_clauses': step['explanation_summary']['new_clauses'],
                        'elapsed_seconds': time.monotonic()-started}), flush=True)
                    if step['explanation_resource_error'] or not local['status'].startswith('COMPLETE:'):
                        break
                    continue
                assert not step['new_individual_cuts']
                if not local['status'].startswith('COMPLETE:'):
                    step['status'] = local['status']; report['status'] = local['status']+'; unresolved'
                    finish_step(step, state, row_passes); break
                assert local['all60_processed'] and local['exact_rational_boxes'] == 60
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    step['status'] = 'STOP: budget before shared-edge query'
                    report['status'] = 'STOP: overall budget; unresolved'
                    finish_step(step, state, row_passes); break
                shared_path = step_dir/'shared-rows.json'
                step['status'] = 'SAT: all60 exact row boxes pass; shared-edge query running'
                save(output, report)
                common = shared.query(selected, triples, targets, neighbors, shared_path,
                    digest(candidate_path), min(LIMITS['shared_LP_seconds'], remaining))
                shared.replay(common, selected, triples, targets, neighbors)
                step.update(shared_rows=portable(shared_path), shared_rows_sha256=digest(shared_path),
                            shared_status=common['status'])
                if common['exact_linear_feasibility']:
                    step['status'] = 'SAT incidence with exact rational symmetric row box'
                    report['status'] = 'STOP: exact symmetric row-box feasible; no graph construction'
                    finish_step(step, state, row_passes); break
                if not common['exact_fixed_design_infeasibility']:
                    step['status'] = common['status']; report['status'] = common['status']+'; unresolved'
                    finish_step(step, state, row_passes); break
                lifted = shared.lift(selected, common['fixed_capacity_potentials']['integer_potentials60_by18'],
                                     triples, targets, neighbors, actions)
                lift_path = step_dir/'symmetric-cut.json'; save(lift_path, lifted)
                step.update(symmetric_lift=portable(lift_path), symmetric_lift_sha256=digest(lift_path))
                candidates = symmetric_candidates(lifted, iteration, digest(shared_path))
                maps = [state.add_cut('symmetric', cut, context) for cut in candidates]
                step.update(symmetric_transport_maps=maps, new_symmetric_cuts=sum(item['new_cut'] for item in maps))
                assert step['new_symmetric_cuts'] > 0
                source = {'kind': 'lazy newly proved symmetric-row cut', 'iteration': iteration,
                    'candidate_sha256': digest(candidate_path), 'shared_report_sha256': digest(shared_path)}
                step.update(explain_candidate(state, selected, source, step_dir/'explanations.json.gz', solver))
                if step['explanation_resource_error']:
                    step['status'] = 'STOP: explanation resource limit'
                    report['status'] = 'STOP: explanation resource limit; unresolved'
                else:
                    step['status'] = 'SAT incidence rejected by new exact shared-row cuts'
                finish_step(step, state, row_passes); save(output, report)
                print(json.dumps({'iteration': iteration, 'status': step['status'],
                    'new_symmetric_cuts': step['new_symmetric_cuts'],
                    'new_clauses': step['explanation_summary']['new_clauses'],
                    'elapsed_seconds': time.monotonic()-started}), flush=True)
                if step['explanation_resource_error']:
                    break
            else:
                report['status'] = 'STOP: SAT refinement-call limit; unresolved'
    except Exception as error:
        report.update(status='ERROR: stopped without unchecked conclusion', error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        if state is not None:
            path = directory/'final.cnf'; state.cnf.to_file(path)
            report.update(final_cnf=portable(path), final_cnf_sha256=digest(path),
                          final_snapshot=state.snapshot(), final_formula=formula(state))
            for name, data in [('individual-registry', state.rows), ('symmetric-registry', state.symmetric),
                               ('explanation-registry', state.records)]:
                path = directory/(name+'.json.gz'); save_gzip(path, data)
                report[name] = portable(path); report[name+'_sha256'] = digest(path)
        report['row_passes'] = row_passes
        report['elapsed_seconds'] = time.monotonic()-started
        report['cooperative_overall_overrun_seconds'] = max(0, report['elapsed_seconds']-LIMITS['overall_seconds'])
        report['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(output, report)
    print(json.dumps({k: v for k, v in report.items() if k != 'iterations'}, indent=2), flush=True)


def bound_record(step, key):
    path = ROOT/step[key]
    assert digest(path) == step[key+'_sha256']
    return load_json(path)


def replay_batch(step, state, selected, expected_source):
    saved = bound_record(step, 'explanation_batch')
    evaluated = state.evaluate(selected)
    assert evaluated['violations']
    records, summary = state.proposals(selected, evaluated['violations'], expected_source)
    assert summary['new_clauses_false_on_source'] > 0
    assert saved == {'source': expected_source, 'registry_evaluation': evaluated,
                     'summary': summary, 'records': records}
    assert step['explanation_summary'] == summary
    if step['explanation_batch_added']:
        assert step['explanation_resource_error'] is None
        state.append_records(records)
    else:
        assert step['explanation_resource_error']
        before = state.snapshot()
        try:
            state.append_records(records)
        except RuntimeError as error:
            assert str(error) == step['explanation_resource_error']
        else:
            raise AssertionError('saved resource refusal not reproduced')
        assert state.snapshot() == before


def reconstruct(preparation_path, result_path=None):
    prepared = checked_preparation(preparation_path)
    state, context, seed = lazy.initial(True)
    assert seed == prepared['seed_control'] and state.records == prepared['initial_explanation_records']
    assert state.snapshot() == prepared['initial_snapshot'] and formula(state) == prepared['formula']
    with tempfile.TemporaryDirectory(prefix='conway-f0-lazy-initial-') as directory:
        path = Path(directory)/'initial.cnf'; state.cnf.to_file(path)
        assert digest(path) == prepared['cnf_sha256']
    base_report = {'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation_path),
        'exact_registry_sha256': lazy.REGISTRY_SHA, 'no_ancestor_auxiliary_CNF_rebuilt': True,
        'optimizer_or_solver_called': False, 'UNSAT_proof_checked': False,
        'whole_component_excluded': False, 'full_graph_completion': False}
    if result_path is None:
        report = dict(base_report, status='cold lazy base, all732 exact cuts, seed explanations and population replay PASS',
                      cnf_sha256=prepared['cnf_sha256'], snapshot=state.snapshot())
        return state.cnf, state.rows+state.symmetric, state.records, report
    result = load_json(result_path)
    assert not result['status'].startswith(('RUNNING:', 'ERROR:'))
    assert result['source_sha256'] == digest(Path(__file__)) and result['preparation_sha256'] == digest(preparation_path)
    assert result['limits'] == LIMITS and len(result['iterations']) <= LIMITS['maximum_SAT_refinement_calls']
    _, _, _, _, triples, targets, neighbors, actions = context
    checked_candidates = refinements = row_passes = exact_rows = exact_boxes = shared_rays = shared_points = 0
    for iteration, step in enumerate(result['iterations']):
        assert step['iteration'] == iteration and step['before'] == state.snapshot()
        assert step['row_passes_before'] == row_passes
        if 'candidate' not in step:
            assert step['status'].startswith(('UNSAT:', 'UNKNOWN:')) and iteration == len(result['iterations'])-1
            assert step['after'] == state.snapshot() and step['row_passes_after'] == row_passes
            continue
        candidate = bound_record(step, 'candidate'); selected = candidate['selected_signature_ids']
        assert inspect_candidate(selected, state, context) == candidate
        assert step['registered_PB_violations'] == len(candidate['registry_evaluation']['violations'])
        checked_candidates += 1
        expected_source = None
        if candidate['registry_evaluation']['violations']:
            assert 'individual_rows' not in step and 'shared_rows' not in step
            expected_source = {'kind': 'lazy registered PB violation', 'iteration': iteration,
                               'candidate_sha256': step['candidate_sha256']}
            refinements += 1
        elif 'individual_rows' in step:
            row_passes += 1
            assert row_passes <= LIMITS['maximum_row_passes']
            local = bound_record(step, 'individual_rows')
            assert local['candidate_sha256'] == step['candidate_sha256']
            individual.check_rows(local, selected, triples, targets, neighbors, actions)
            assert local['status'] == step['individual_status']
            assert (local['exact_integer_obstructions'], local['exact_rational_boxes']) == (
                step['exact_individual_obstructions'], step['exact_individual_boxes'])
            exact_rows += local['exact_integer_obstructions']; exact_boxes += local['exact_rational_boxes']
            maps = add_row_cuts(state, local, iteration, context)
            assert maps == step['individual_transport_maps']
            assert sum(item['new_cut'] for item in maps) == step['new_individual_cuts']
            if local['exact_integer_obstructions']:
                assert step['new_individual_cuts'] > 0 and 'shared_rows' not in step
                expected_source = {'kind': 'lazy newly proved individual-row cut', 'iteration': iteration,
                    'candidate_sha256': step['candidate_sha256'], 'row_report_sha256': step['individual_rows_sha256']}
            if 'shared_rows' in step:
                assert not local['exact_integer_obstructions'] and local['exact_rational_boxes'] == 60
                assert local['all60_processed'] and local['status'].startswith('COMPLETE:')
                common = bound_record(step, 'shared_rows')
                assert common['candidate_sha256'] == step['candidate_sha256']
                shared.replay(common, selected, triples, targets, neighbors)
                assert common['status'] == step['shared_status']
                shared_rays += common['exact_fixed_design_infeasibility']; shared_points += common['exact_linear_feasibility']
                if common['exact_fixed_design_infeasibility']:
                    lifted = shared.lift(selected, common['fixed_capacity_potentials']['integer_potentials60_by18'],
                                         triples, targets, neighbors, actions)
                    assert lifted == bound_record(step, 'symmetric_lift')
                    candidates = symmetric_candidates(lifted, iteration, step['shared_rows_sha256'])
                    maps = [state.add_cut('symmetric', cut, context) for cut in candidates]
                    assert maps == step['symmetric_transport_maps']
                    assert sum(item['new_cut'] for item in maps) == step['new_symmetric_cuts'] > 0
                    expected_source = {'kind': 'lazy newly proved symmetric-row cut', 'iteration': iteration,
                        'candidate_sha256': step['candidate_sha256'], 'shared_report_sha256': step['shared_rows_sha256']}
        else:
            assert step['status'] == 'STOP: budget before row pass'
            assert iteration == len(result['iterations'])-1
        if expected_source is not None:
            replay_batch(step, state, selected, expected_source)
            if not step['explanation_batch_added']:
                assert iteration == len(result['iterations'])-1
        else:
            assert 'explanation_batch' not in step
        assert step['after'] == state.snapshot() and step['row_passes_after'] == row_passes
    assert row_passes == result['row_passes']
    assert state.snapshot() == result['final_snapshot'] and formula(state) == result['final_formula']
    for name, data in [('individual-registry', state.rows), ('symmetric-registry', state.symmetric),
                       ('explanation-registry', state.records)]:
        assert bound_record(result, name) == data
    with tempfile.TemporaryDirectory(prefix='conway-f0-lazy-final-') as directory:
        path = Path(directory)/'final.cnf'; state.cnf.to_file(path)
        assert digest(path) == result['final_cnf_sha256']
    report = dict(base_report,
        status='cold lazy final formula, exact registry, candidate prefixes, clause bounds and row/shared witnesses replay PASS',
        result_sha256=digest(result_path), final_cnf_sha256=result['final_cnf_sha256'],
        checked_candidates=checked_candidates, registry_only_refinements=refinements, row_passes=row_passes,
        exact_individual_obstructions=exact_rows, exact_individual_boxes=exact_boxes,
        exact_shared_rays=shared_rays, exact_shared_points=shared_points,
        final_snapshot=state.snapshot(), all_explanation_clauses_checked=len(state.records))
    return state.cnf, state.rows+state.symmetric, state.records, report


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
