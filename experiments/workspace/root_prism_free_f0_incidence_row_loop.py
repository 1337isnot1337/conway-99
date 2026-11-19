"""Bounded free480-selector incidence / exact exterior-row separation loop.

Preparation calls no incidence solver or optimizer. The loop keeps all
original Gram/motif clauses, the twelve old row cuts, and full weighted
inequalities certified by integer row potentials. There are no visitation
blocks, fixed incidence designs, or second-component restrictions.

An incremental UNSAT answer is explicitly uncertified. The separate
certificate driver must rebuild the final formula, obtain a fresh proof,
and check it before a conditional component exclusion can be claimed.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations
import json
from math import isfinite
from pathlib import Path
import resource
import tempfile
from threading import Timer
import time

from pysat.formula import CNF
from pysat.solvers import Solver

import root_prism_free_f0_exterior_row_box_separation as box
import root_prism_free_f0_exterior_row_cut_overlay as old
import root_prism_free_f0_weighted_threshold as threshold


ROOT, LOGS = old.ROOT, old.LOGS
BASE = old.base
BOX_RESULT = LOGS/'f0-exterior-row-box-separation-run01/result.json'
BOX_RESULT_SHA = '328fddcc22b7ee2bfdd2a5c93189cef12240a56eee5804073a0848e64e7a749f'
BOX_PREPARATION = LOGS/'f0-exterior-row-box-separation-preparation.json.gz'
BOX_PREPARATION_SHA = '4ef94dc28a84fea3c236aac46ec7e5f2fa471cb6831014954bb0ba53b3fa43a0'
ENCODER_CONTROLS = LOGS/'f0-weighted-threshold-controls.json'
EXPECTED_SOURCES = {
    'root_prism_free_f0_exterior_row_box_separation.py': '60366da662c74ee8d3ca367dc532c16b652952101fa5725a3248fc5a53a773bd',
    'root_prism_free_f0_exterior_row_cut_overlay.py': '0a1739251220c3b27564cc9ea0d2e64bad4c9aa8db9a93182fc7cc91ea7c0353',
    'root_prism_free_f0_weighted_threshold.py': 'a0c4b38d7787c8e6565ab122e0fdf41655ea40a9f0f218c0f860cd59d3f05144'}
LIMITS = {'maximum_incidences': 20, 'SAT_seconds_per_call': 10,
          'row_pass_seconds': 60, 'overall_seconds': 180,
          'maximum_threshold_states_per_cut': 250000,
          'maximum_formula_variables': 1000000,
          'maximum_formula_clauses': 2000000}
digest, canonical, portable = box.digest, box.canonical, box.portable


def save(path, data):
    box.save(path, data)


def load_json(path):
    raw = path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix == '.gz' else raw)


def checked_sources():
    for name, expected in EXPECTED_SOURCES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    controls = load_json(ENCODER_CONTROLS)
    assert controls['source_sha256'] == EXPECTED_SOURCES['root_prism_free_f0_weighted_threshold.py']
    assert controls['status'].endswith('PASS') and controls['incidence_query_called'] is False
    assert digest(BOX_RESULT) == BOX_RESULT_SHA
    assert digest(BOX_PREPARATION) == BOX_PREPARATION_SHA
    return controls


def make_cut(transport, origin, triples, targets, neighbors):
    target = transport['target']
    vector = transport['integer_vector']
    assert type(target) is int and 0 <= target < 480
    assert len(vector) == 18 and all(type(value) is int for value in vector)
    demand = sum(x*y for x, y in zip(vector, targets[target]))
    weights = [[b, sum(vector[i] for i in triples[b])] for b in neighbors[target]]
    weights = [[b, weight] for b, weight in weights if weight > 0]
    assert demand == transport['integer_demand'] > 0
    assert weights == transport['positive_weighted_terms']
    normalized, bound, _ = threshold.normalize([(b+1, w) for b, w in weights], demand)
    predicate = {'target': target+1, 'demand': bound, 'terms': sorted(normalized)}
    return {'target': target, 'integer_vector': list(vector), 'demand': demand,
            'weights': weights, 'origin': origin,
            'normalized_predicate_sha256': hashlib.sha256(canonical(predicate)).hexdigest()}


def validate_cut(cut, triples, targets, neighbors):
    transport = {'target': cut['target'], 'integer_vector': cut['integer_vector'],
                 'integer_demand': cut['demand'], 'positive_weighted_terms': cut['weights']}
    assert make_cut(transport, cut['origin'], triples, targets, neighbors) == cut


def encode_cut(cut, top):
    return threshold.guarded_threshold(cut['target']+1,
        [(b+1, weight) for b, weight in cut['weights']], cut['demand'], top,
        maximum_states=LIMITS['maximum_threshold_states_per_cut'])


def add_cut(cnf, registry, encodings, cut):
    keys = {record['normalized_predicate_sha256']: i for i, record in enumerate(registry)}
    key = cut['normalized_predicate_sha256']
    if key in keys:
        return keys[key], False
    clauses, top, encoding = encode_cut(cut, cnf.nv)
    if top > LIMITS['maximum_formula_variables'] or len(cnf.clauses)+len(clauses) > LIMITS['maximum_formula_clauses']:
        raise RuntimeError('complete necessary-cut formula resource limit; no partial cut added')
    encoding.update(cut_index=len(registry), clause_start=len(cnf.clauses),
                    clause_body_sha256=hashlib.sha256(canonical(clauses)).hexdigest())
    cnf.extend(clauses)
    assert cnf.nv == top
    registry.append(cut)
    encodings.append(encoding)
    return len(registry)-1, True


def weighted_outcomes(selected, registry):
    chosen = set(selected)
    return [{'cut_index': i, 'target': cut['target'],
             'left': sum(weight for b, weight in cut['weights'] if b in chosen),
             'right': cut['demand']*int(cut['target'] in chosen)}
            for i, cut in enumerate(registry)]


def inspect(selected, domain, records, old_cuts, old_clauses, registry):
    point = old.inspect(selected, domain, records, old_cuts, old_clauses)
    values = weighted_outcomes(selected, registry)
    assert all(value['left'] >= value['right'] for value in values)
    return {'original_incidence_and_twelve_old_cuts': point,
            'full_weighted_cut_outcomes': values, 'selected_signature_ids': selected,
            'full_graph_or_exterior_graph_constructed': False}


def initial(complete_replay=False):
    controls = checked_sources()
    previous, domain, records, cnf, old_cuts, old_clauses, _, old_formula = old.rebuild(complete_replay)
    triples, targets, neighbors, selected, actions, _ = box.load()
    assert triples == domain['signature_domain']
    result = load_json(BOX_RESULT)
    assert result['all60_selected_rows_processed'] and result['exact_row_obstruction_count'] == 3
    registry, encodings, aliases = [], [], []
    for row in result['rows']:
        if 'exact_obstruction' not in row:
            continue
        proof = row['exact_obstruction']
        assert proof == box.obstruction(row['target'], proof['integer_vector'], triples,
                                       targets, neighbors, selected, actions)
        for transport in proof['all12_verified_core_transports']:
            origin = {'kind': 'frozen60-row pass', 'result_sha256': BOX_RESULT_SHA,
                      'source_target': row['target'], 'core_action_index': transport['core_action_index']}
            cut = make_cut(transport, origin, triples, targets, neighbors)
            index, added = add_cut(cnf, registry, encodings, cut)
            aliases.append({'source_target': row['target'], 'core_action_index': transport['core_action_index'],
                            'registry_index': index, 'new_cut': added})
    assert len(aliases) == 36 and len(registry) == 36
    failed = [value for value in weighted_outcomes(selected, registry) if value['left'] < value['right']]
    assert {110, 349, 479} <= {value['target'] for value in failed}
    metadata = {'primary_variables': 480, 'variables': cnf.nv, 'clauses': len(cnf.clauses),
                'literal_occurrences': sum(map(len, cnf.clauses)),
                'old_overlay_formula': old_formula, 'initial_full_weighted_cuts': len(registry),
                'initial_added_clauses': len(cnf.clauses)-old_formula['clauses'],
                'initial_added_auxiliary_variables': cnf.nv-old_formula['variables'],
                'frozen_replacement_incidence_failed_cut_outcomes': failed,
                'fixed_incidence_or_second_component': False, 'visitation_blocks': False}
    context = (domain, records, old_cuts, old_clauses, triples, targets, neighbors, actions)
    return cnf, registry, encodings, aliases, metadata, context, previous, controls


def prepare(output, cnf_path):
    assert not output.exists() and not cnf_path.exists()
    started = time.monotonic()
    cnf, registry, encodings, aliases, formula, _, previous, controls = initial()
    cnf.to_file(cnf_path)
    preparation = {'status': 'bounded free480 incidence/row loop prepared; no incidence query or LP',
        'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': EXPECTED_SOURCES,
        'base_model_source_hashes': previous['source_hashes'],
        'old_overlay_model_sha256': digest(LOGS/'f0-exterior-row-cut-overlay-model.json'),
        'box_result_sha256': BOX_RESULT_SHA, 'box_preparation_sha256': BOX_PREPARATION_SHA,
        'encoder_controls_sha256': digest(ENCODER_CONTROLS), 'encoder_controls': controls,
        'formula': formula, 'initial_cut_registry': registry, 'initial_encodings': encodings,
        'initial_cut_aliases': aliases, 'limits': LIMITS,
        'cnf': str(cnf_path), 'cnf_sha256': digest(cnf_path), 'cnf_bytes': cnf_path.stat().st_size,
        'scope': 'component0 in globallyP=F=0 split18+18; no first incidence or second component fixed',
        'incidence_SAT_scope': 'necessary incidence only, even if all separate row boxes are feasible',
        'UNSAT_scope': 'only after fresh complete formula proof and cold replay; conditional component0 only',
        'no_visitation_blocks': True, 'all480_primary_selectors_free': True,
        'initial_full_weighted_inequalities_instead_of_cover_clauses': True,
        'additional_constraints_only_from_replayed_integer_row_potentials': True,
        'PB_support': 'pysat.pb unavailable; pure guarded-threshold decision DAG used',
        'loop_stop_conditions': ['UNSAT', 'UNKNOWN', 'no retained row obstruction', 'error',
                                 'incidence budget', 'overall budget', 'encoding resource limit'],
        'incidence_solver_or_optimizer_called': False, 'seconds': time.monotonic()-started}
    output.write_bytes(gzip.compress(canonical(preparation)+b'\n', mtime=0))
    print(json.dumps({k: v for k, v in preparation.items() if k not in
        ('initial_cut_registry', 'initial_encodings', 'initial_cut_aliases')}, indent=2), flush=True)


def checked_preparation(path, require_cnf=False):
    prepared = load_json(path)
    assert prepared['source_sha256'] == digest(Path(__file__))
    assert prepared['dependency_source_hashes'] == EXPECTED_SOURCES
    assert checked_sources() == prepared['encoder_controls']
    for name, value in prepared['base_model_source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == value
    assert prepared['limits'] == LIMITS
    assert prepared['box_result_sha256'] == BOX_RESULT_SHA
    assert prepared['box_preparation_sha256'] == BOX_PREPARATION_SHA
    assert digest(ENCODER_CONTROLS) == prepared['encoder_controls_sha256']
    assert digest(LOGS/'f0-exterior-row-cut-overlay-model.json') == prepared['old_overlay_model_sha256']
    if require_cnf:
        assert digest(Path(prepared['cnf'])) == prepared['cnf_sha256']
    return prepared


def summarize_rows(report):
    report['status_counts'] = dict(sorted(Counter(row['status'] for row in report['rows']).items()))
    report['exact_integer_obstructions'] = sum('exact_obstruction' in row for row in report['rows'])
    report['exact_rational_boxes'] = sum('exact_box_witness' in row for row in report['rows'])
    report['processed_rows'] = sum(not row['status'].startswith(('PENDING', 'NOT RUN')) for row in report['rows'])
    report['all60_processed'] = report['processed_rows'] == 60


def separate(selected, triples, targets, neighbors, actions, output, candidate_sha, global_deadline):
    import numpy as np
    from scipy.optimize import linprog
    started = time.monotonic()
    deadline = min(global_deadline, started+LIMITS['row_pass_seconds'])
    report = {'status': 'running bounded row pass', 'source_sha256': digest(Path(__file__)),
              'candidate_sha256': candidate_sha, 'selected_signature_ids': selected,
              'maximum_pass_seconds': LIMITS['row_pass_seconds'],
              'rows': [{'position': position, 'target': a, 'status': 'PENDING'} for position, a in enumerate(selected)]}
    stop = None
    for row in report['rows']:
        remaining = deadline-time.monotonic()
        if remaining <= 0:
            stop = 'UNKNOWN: row-pass or overall time budget'
            break
        a = row['target']
        inside = sorted(set(neighbors[a])&set(selected))
        q, count = targets[a], len(inside)
        objective = np.array([-value for value in q]+[1]*count, dtype=float)
        matrix = np.zeros((count, 18+count), dtype=float)
        for i, b in enumerate(inside):
            matrix[i, triples[b]] = 1
            matrix[i, 18+i] = -1
        row.update(status='RUNNING', eligible_selected_neighbors=inside,
                   requested_LP_seconds=remaining, LP_variables=18+count, LP_inequalities=count)
        summarize_rows(report)
        save(output, report)
        row_started = time.monotonic()
        try:
            answer = linprog(objective, A_ub=matrix, b_ub=np.zeros(count),
                bounds=[(-1, 1)]*18+[(0, None)]*count, method='highs-ds',
                options={'time_limit': max(0.001, remaining), 'presolve': True})
        except Exception as error:
            row.update(status='ERROR: LP call', error=repr(error), seconds=time.monotonic()-row_started)
            stop = 'ERROR: LP call'
            break
        row.update(numerical_status=int(answer.status), numerical_message=str(answer.message),
                   seconds=time.monotonic()-row_started, numerical_iterations=int(answer.nit))
        if answer.fun is not None and isfinite(float(answer.fun)):
            row['numerical_separation_value'] = -float(answer.fun)
        vector = None
        if answer.x is not None and all(isfinite(float(x)) for x in answer.x[:18]):
            numeric = [float(x) for x in answer.x[:18]]
            row['numerical_vector_hex'] = [x.hex() for x in numeric]
            vector = box.integer_vector(numeric, triples, q, inside)
        if vector is not None:
            row['exact_obstruction'] = box.obstruction(a, vector, triples, targets, neighbors, selected, actions)
            row['status'] = 'EXACT INTEGER ROW CAPACITY OBSTRUCTION'
        elif answer.status == 0:
            witness = box.rational_box_witness(answer.ineqlin.marginals, triples, q, inside)
            if witness is not None:
                row['exact_box_witness'] = witness
                row['status'] = 'EXACT RATIONAL BOX ROW WITNESS'
            else:
                row['status'] = 'UNKNOWN: numerical optimum without exact certificate'
                stop = row['status']
        else:
            row['status'] = 'UNKNOWN: LP limit without exact certificate' if answer.status == 1 else 'ERROR: LP status'
            stop = row['status']
        if answer.status == 1:
            stop = 'UNKNOWN: LP time limit, even if a valid integer cut was recovered'
        if answer.status not in (0, 1):
            stop = 'ERROR: unexpected LP status'
        summarize_rows(report)
        report['elapsed_seconds'] = time.monotonic()-started
        save(output, report)
        if stop:
            break
    for row in report['rows']:
        if row['status'] == 'PENDING':
            row['status'] = 'NOT RUN: '+str(stop)
    summarize_rows(report)
    report['status'] = stop or 'COMPLETE: all60 exact row outcomes'
    report['elapsed_seconds'] = time.monotonic()-started
    report['cooperative_budget_overrun_seconds'] = max(0, time.monotonic()-deadline)
    save(output, report)
    return report


def check_rows(report, selected, triples, targets, neighbors, actions):
    assert report['source_sha256'] == digest(Path(__file__))
    assert report['selected_signature_ids'] == selected and len(report['rows']) == 60
    for position, (row, a) in enumerate(zip(report['rows'], selected)):
        assert row['position'] == position and row['target'] == a
        assert row['status'] not in ('PENDING', 'RUNNING')
        inside = sorted(set(neighbors[a])&set(selected))
        if 'eligible_selected_neighbors' in row:
            assert row['eligible_selected_neighbors'] == inside
        if 'exact_obstruction' in row:
            proof = row['exact_obstruction']
            assert proof == box.obstruction(a, proof['integer_vector'], triples, targets, neighbors, selected, actions)
            assert row['status'] == 'EXACT INTEGER ROW CAPACITY OBSTRUCTION'
        if 'exact_box_witness' in row:
            witness = row['exact_box_witness']
            den, nums = witness['denominator'], witness['numerators']
            assert type(den) is int and den > 0 and len(nums) == len(inside)
            assert all(type(n) is int and 0 <= n <= den for n in nums)
            assert witness['neighbor_signature_ids'] == inside
            assert [sum(n for b, n in zip(inside, nums) if i in triples[b]) for i in range(18)] == [den*q for q in targets[a]]
            assert sum(nums) == 8*den
            binary = all(n in (0, den) for n in nums)
            support = [b for b, n in zip(inside, nums) if n]
            packing = binary and all(len(set(triples[b])&set(triples[c])) <= 1 for b, c in combinations(support, 2))
            assert witness['binary_neighbor_weights'] == binary
            assert witness['binary_neighbor_pair_packing_checked_and_passed'] == packing
            assert row['status'] == 'EXACT RATIONAL BOX ROW WITNESS'
        if row['status'].startswith('EXACT INTEGER'):
            assert 'exact_obstruction' in row
        if row['status'].startswith('EXACT RATIONAL'):
            assert 'exact_box_witness' in row
    reproduced = json.loads(json.dumps(report))
    summarize_rows(reproduced)
    assert reproduced == report
    if report['status'].startswith('COMPLETE:'):
        assert report['all60_processed']
        assert report['exact_integer_obstructions']+report['exact_rational_boxes'] == 60


def row_cut_candidates(rows, iteration, triples, targets, neighbors):
    cuts = []
    for row in rows['rows']:
        if 'exact_obstruction' not in row:
            continue
        for transport in row['exact_obstruction']['all12_verified_core_transports']:
            origin = {'kind': 'loop exact row obstruction', 'iteration': iteration,
                      'source_target': row['target'], 'core_action_index': transport['core_action_index']}
            cuts.append(make_cut(transport, origin, triples, targets, neighbors))
    return cuts


def run(preparation_path, directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    started = time.monotonic()
    deadline = started+LIMITS['overall_seconds']
    result_path = directory/'result.json'
    result = {'status': 'RUNNING: bounded free480 incidence/row loop',
        'source_sha256': digest(Path(__file__)), 'preparation': portable(preparation_path),
        'preparation_sha256': digest(preparation_path), 'limits': LIMITS, 'iterations': [],
        'fixed_incidence_or_second_component': False, 'visitation_blocks': False,
        'whole_component_excluded': False, 'full_graph_completion': False}
    save(result_path, result)
    cnf = None
    registry = encodings = None
    try:
        prepared = checked_preparation(preparation_path, True)
        result['initial_cnf_sha256'] = prepared['cnf_sha256']
        cnf = CNF(from_file=prepared['cnf'])
        assert cnf.nv == prepared['formula']['variables'] and len(cnf.clauses) == prepared['formula']['clauses']
        registry = json.loads(json.dumps(prepared['initial_cut_registry']))
        encodings = json.loads(json.dumps(prepared['initial_encodings']))
        domain, records = BASE.load(0)
        old_cuts, old_clauses, _ = old.load_cuts()
        triples, targets, neighbors, _, actions, _ = box.load()
        with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=False) as solver:
            result['bootstrap_and_input_checks_seconds'] = time.monotonic()-started
            for iteration in range(LIMITS['maximum_incidences']):
                remaining = deadline-time.monotonic()
                if remaining <= 0:
                    result['status'] = 'STOP: overall budget; no component exclusion'
                    break
                step_dir = directory/f'iteration{iteration:02d}'
                step_dir.mkdir()
                step = {'iteration': iteration, 'status': 'RUNNING: SAT query',
                        'cut_count_before': len(registry), 'variables_before': cnf.nv,
                        'clauses_before': len(cnf.clauses), 'requested_SAT_seconds': min(LIMITS['SAT_seconds_per_call'], remaining)}
                result['iterations'].append(step)
                save(result_path, result)
                solver.clear_interrupt()
                sat_started = time.monotonic()
                timer = Timer(step['requested_SAT_seconds'], solver.interrupt)
                timer.start()
                try:
                    answer = solver.solve_limited(expect_interrupt=True)
                finally:
                    timer.cancel()
                step['SAT_seconds'] = time.monotonic()-sat_started
                step['cooperative_SAT_overrun_seconds'] = max(0, step['SAT_seconds']-step['requested_SAT_seconds'])
                step['cumulative_solver_statistics'] = solver.accum_stats()
                if answer is None:
                    step['status'] = 'UNKNOWN: SAT call budget'
                    result['status'] = 'UNKNOWN: SAT call budget; no component exclusion'
                    break
                if answer is False:
                    step['status'] = 'UNSAT: incremental answer, uncertified'
                    result['status'] = 'UNSAT_UNCERTIFIED: fresh final-formula proof required'
                    break
                positive = {literal for literal in solver.get_model() if literal > 0}
                selected = [a for a in range(480) if a+1 in positive]
                candidate = inspect(selected, domain, records, old_cuts, old_clauses, registry)
                candidate_path = step_dir/'candidate.json'
                save(candidate_path, candidate)
                step.update(status='SAT: exact incidence checked; row pass running',
                            candidate=portable(candidate_path), candidate_sha256=digest(candidate_path))
                save(result_path, result)
                rows_path = step_dir/'rows.json'
                rows = separate(selected, triples, targets, neighbors, actions, rows_path,
                                digest(candidate_path), deadline)
                check_rows(rows, selected, triples, targets, neighbors, actions)
                step.update(rows=portable(rows_path), rows_sha256=digest(rows_path),
                            row_status=rows['status'], processed_rows=rows['processed_rows'],
                            exact_integer_obstructions=rows['exact_integer_obstructions'],
                            exact_rational_boxes=rows['exact_rational_boxes'])
                generated = row_cut_candidates(rows, iteration, triples, targets, neighbors)
                maps, new_count = [], 0
                for cut in generated:
                    before = len(cnf.clauses)
                    try:
                        index, added = add_cut(cnf, registry, encodings, cut)
                    except RuntimeError as error:
                        step['encoding_resource_error'] = str(error)
                        result['status'] = 'STOP: encoding resource limit; no component exclusion'
                        break
                    if added:
                        solver.append_formula(cnf.clauses[before:])
                        new_count += 1
                    maps.append({'origin': cut['origin'], 'registry_index': index, 'new_cut': added})
                step.update(cut_transport_maps=maps, generated_transports=len(generated),
                            new_weighted_cuts=new_count, cut_count_after=len(registry),
                            variables_after=cnf.nv, clauses_after=len(cnf.clauses))
                step['status'] = 'SAT incidence separated by exact weighted cuts' if new_count else 'SAT incidence; no new weighted cut retained'
                save(directory/'cut-registry.json', registry)
                save(directory/'cut-encodings.json', encodings)
                save(result_path, result)
                print(json.dumps({'iteration': iteration, 'status': step['status'],
                    'row_status': rows['status'], 'obstructions': rows['exact_integer_obstructions'],
                    'new_cuts': new_count, 'total_cuts': len(registry),
                    'elapsed_seconds': time.monotonic()-started}), flush=True)
                if 'encoding_resource_error' in step:
                    break
                if not rows['status'].startswith('COMPLETE:'):
                    result['status'] = rows['status']+'; loop stopped without component exclusion'
                    break
                if not new_count:
                    assert not rows['exact_integer_obstructions']
                    result['status'] = 'STOP: no retained row obstruction; necessary incidence only'
                    break
            else:
                result['status'] = 'STOP: incidence budget; no component exclusion'
    except Exception as error:
        result.update(status='ERROR: loop stopped; no unchecked exclusion', error_type=type(error).__name__,
                      error_message=str(error))
        raise
    finally:
        if cnf is not None and registry is not None and encodings is not None:
            final_cnf = directory/'final.cnf'
            cnf.to_file(final_cnf)
            save(directory/'cut-registry.json', registry)
            save(directory/'cut-encodings.json', encodings)
            result.update(final_cnf=portable(final_cnf), final_cnf_sha256=digest(final_cnf),
                final_variables=cnf.nv, final_clauses=len(cnf.clauses),
                cut_registry=portable(directory/'cut-registry.json'),
                cut_registry_sha256=digest(directory/'cut-registry.json'),
                cut_encodings=portable(directory/'cut-encodings.json'),
                cut_encodings_sha256=digest(directory/'cut-encodings.json'), final_weighted_cut_count=len(registry))
        result['elapsed_seconds'] = time.monotonic()-started
        result['cooperative_overall_overrun_seconds'] = max(0, result['elapsed_seconds']-LIMITS['overall_seconds'])
        result['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(result_path, result)
    print(json.dumps({k: v for k, v in result.items() if k != 'iterations'}, indent=2), flush=True)


def reconstruct(preparation_path, result_path=None):
    prepared = checked_preparation(preparation_path)
    cnf, registry, encodings, aliases, formula, context, _, _ = initial(True)
    assert registry == prepared['initial_cut_registry'] and encodings == prepared['initial_encodings']
    assert aliases == prepared['initial_cut_aliases'] and formula == prepared['formula']
    with tempfile.TemporaryDirectory(prefix='conway-f0-row-loop-initial-') as directory:
        file = Path(directory)/'initial.cnf'
        cnf.to_file(file)
        assert digest(file) == prepared['cnf_sha256']
    if result_path is None:
        return cnf, registry, encodings, {'status': 'cold complete initial formula and weighted encodings replay PASS',
            'preparation_sha256': digest(preparation_path), 'variables': cnf.nv, 'clauses': len(cnf.clauses),
            'initial_weighted_cut_count': len(registry), 'incidence_solver_or_optimizer_called': False}
    result = load_json(result_path)
    assert result['status'] != 'RUNNING: bounded free480 incidence/row loop'
    assert result['source_sha256'] == digest(Path(__file__))
    assert result['preparation_sha256'] == digest(preparation_path) and result['limits'] == LIMITS
    domain, records, old_cuts, old_clauses, triples, targets, neighbors, actions = context
    exact_obstructions = exact_boxes = checked_candidates = 0
    for iteration, step in enumerate(result['iterations']):
        assert step['iteration'] == iteration and step['cut_count_before'] == len(registry)
        assert step['variables_before'] == cnf.nv and step['clauses_before'] == len(cnf.clauses)
        if 'candidate' not in step:
            assert step['status'].startswith(('UNKNOWN:', 'UNSAT:'))
            assert iteration == len(result['iterations'])-1
            continue
        candidate_path = ROOT/step['candidate']
        assert digest(candidate_path) == step['candidate_sha256']
        candidate = load_json(candidate_path)
        selected = candidate['selected_signature_ids']
        assert inspect(selected, domain, records, old_cuts, old_clauses, registry) == candidate
        checked_candidates += 1
        rows_path = ROOT/step['rows']
        assert digest(rows_path) == step['rows_sha256']
        rows = load_json(rows_path)
        assert rows['candidate_sha256'] == digest(candidate_path)
        check_rows(rows, selected, triples, targets, neighbors, actions)
        assert step['row_status'] == rows['status'] and step['processed_rows'] == rows['processed_rows']
        assert step['exact_integer_obstructions'] == rows['exact_integer_obstructions']
        assert step['exact_rational_boxes'] == rows['exact_rational_boxes']
        exact_obstructions += rows['exact_integer_obstructions']
        exact_boxes += rows['exact_rational_boxes']
        generated = row_cut_candidates(rows, iteration, triples, targets, neighbors)
        assert len(generated) == step['generated_transports']
        saved_maps = step['cut_transport_maps']
        assert len(saved_maps) <= len(generated)
        if len(saved_maps) < len(generated):
            assert 'encoding_resource_error' in step and iteration == len(result['iterations'])-1
        maps = []
        for cut in generated[:len(saved_maps)]:
            index, added = add_cut(cnf, registry, encodings, cut)
            maps.append({'origin': cut['origin'], 'registry_index': index, 'new_cut': added})
        assert maps == saved_maps
        assert sum(record['new_cut'] for record in maps) == step['new_weighted_cuts']
        assert step['cut_count_after'] == len(registry)
        assert step['variables_after'] == cnf.nv and step['clauses_after'] == len(cnf.clauses)
    assert result['final_weighted_cut_count'] == len(registry)
    assert result['final_variables'] == cnf.nv and result['final_clauses'] == len(cnf.clauses)
    registry_path, encoding_path = ROOT/result['cut_registry'], ROOT/result['cut_encodings']
    assert digest(registry_path) == result['cut_registry_sha256'] and load_json(registry_path) == registry
    assert digest(encoding_path) == result['cut_encodings_sha256'] and load_json(encoding_path) == encodings
    with tempfile.TemporaryDirectory(prefix='conway-f0-row-loop-final-') as directory:
        file = Path(directory)/'final.cnf'
        cnf.to_file(file)
        assert digest(file) == result['final_cnf_sha256']
    report = {'status': 'cold complete incidence domain, initial/final CNF and all exact cut/row replays PASS',
        'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation_path),
        'result_sha256': digest(result_path), 'final_cnf_sha256': result['final_cnf_sha256'],
        'checked_incidence_candidates': checked_candidates, 'exact_integer_obstructions': exact_obstructions,
        'exact_rational_row_boxes': exact_boxes, 'full_weighted_cuts': len(registry),
        'variables': cnf.nv, 'clauses': len(cnf.clauses),
        'incidence_solver_or_optimizer_called': False, 'UNSAT_proof_checked': False,
        'whole_component_excluded': False, 'full_graph_completion': False}
    return cnf, registry, encodings, report


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--output', type=Path, required=True)
    prep.add_argument('--cnf', type=Path, required=True)
    execute = commands.add_parser('run')
    execute.add_argument('--preparation', type=Path, required=True)
    execute.add_argument('--directory', type=Path, required=True)
    check = commands.add_parser('replay')
    check.add_argument('--preparation', type=Path, required=True)
    check.add_argument('--result', type=Path)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output.resolve(), args.cnf.resolve())
    elif args.command == 'run':
        run(args.preparation.resolve(), args.directory.resolve())
    else:
        assert not args.output.exists()
        _, _, _, report = reconstruct(args.preparation.resolve(), args.result.resolve() if args.result else None)
        save(args.output, report)
        print(json.dumps(report, indent=2), flush=True)
