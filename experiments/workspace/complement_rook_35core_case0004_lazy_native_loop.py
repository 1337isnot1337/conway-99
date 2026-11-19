"""Bounded native case4 candidates with a complete external cover registry.

Only proved registered clauses may be appended. Every candidate is saved
in full and evaluated against the complete registry. A finite prefix is a
necessary relaxation; neither INFEASIBLE nor UNKNOWN is a checked proof.
Preparation and production are separate commands. Cold replay uses no
solver and reconstructs every saved prefix and candidate decision.
"""

import time
PROCESS_STARTED = time.monotonic()

import argparse
import gc
import gzip
import json
from pathlib import Path
import resource
import struct
import sys
import tempfile

from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

import complement_rook_35core_case0004_lazy_native as base
import complement_rook_35core_case0004_coordinate_cover_cadical as watchdog


ROOT, LOGS = base.ROOT, base.LOGS
digest, canonical, portable = base.digest, base.canonical, base.portable
MODEL = LOGS/'complement-rook-35core-case0004-lazy-native-model.json'
MODEL_SHA = 'aeb636198cb0b9749e2142a596404181edf92923d55d5bdf764a8f9432439b68'
COLD = LOGS/'complement-rook-35core-case0004-lazy-native-cold-replay.json'
COLD_SHA = 'ad169d4dece65473c87e814338741923ce12b5a8b655379d35051dabfe029571'
WATCHDOG_PREP = LOGS/'complement-rook-35core-case0004-coordinate-cover-cadical-preparation.json'
WATCHDOG_PREP_SHA = 'e7a4185a300a48edbe01d7103da8e765dab1ad9653e2678992d3f1c4e986d731'
DEPENDENCIES = {
    'complement_rook_35core_case0004_lazy_native.py':
        '5fe4d58400dc23e42ab154f8455ce47c4b061fbd2ae7c0e37f946d77c56aba0a',
    'complement_rook_35core_case0004_coordinate_cover_cadical.py':
        '1921f71964795d819e0369c9679dc1526df97c29bb1920a932c7ca449ba3de25',
}
LIMITS = {key: base.LIMITS[key] for key in (
    'native_calls', 'solver_seconds_per_call', 'requested_child_seconds',
    'hard_parent_seconds', 'workers', 'inserted_cover_clauses', 'inserted_cover_literals')}


def save(path, value):
    """A killed child must leave the preceding complete checkpoint readable."""
    temporary = path.with_name(path.name+'.writing')
    temporary.write_text(json.dumps(value, indent=2, allow_nan=False)+'\n')
    temporary.replace(path)


def sources():
    names = set(base.source_hashes()) | set(DEPENDENCIES) | {Path(__file__).name}
    return {name: digest(Path(__file__).with_name(name)) for name in sorted(names)}


def bindings():
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    for path, expected in ((MODEL, MODEL_SHA), (COLD, COLD_SHA),
                           (WATCHDOG_PREP, WATCHDOG_PREP_SHA)):
        assert digest(path) == expected
    model, cold = json.loads(MODEL.read_text()), json.loads(COLD.read_text())
    assert model['complete'] and model['source_hashes'] == base.source_hashes()
    assert model['limits'] == base.LIMITS and cold['model_sha256'] == MODEL_SHA
    assert cold['status'].startswith('PASS:') and not cold['solver_or_optimizer_called']
    assert model['runtime_binding_sha256'] == base.sha(canonical(base.native.runtime_binding()))
    for key, hash_key in (('registry', 'registry_sha256'),
                           ('prefix_proto', 'prefix_proto_compressed_sha256')):
        assert digest(ROOT/model[key]) == model[hash_key]
    assert digest(ROOT/model['controls']) == model['controls_sha256']
    return model


def parameter_record(seconds):
    assert 0 < seconds <= LIMITS['solver_seconds_per_call']
    return {'max_time_in_seconds': float(seconds), 'num_search_workers': 1,
            'log_search_progress': True, 'log_to_stdout': True}


def configured_solver(seconds):
    solver = cp_model.CpSolver()
    for name, value in parameter_record(seconds).items():
        setattr(solver.parameters, name, value)
    return solver


def append_proto(proto, raw, ids):
    """DIMACS positive b+1 becomes native b; negative -a-1 stays -a-1."""
    for identifier in ids:
        a, bits = base.entry(raw, identifier)
        clause = base.clause_from(a, bits)
        proto.constraints.add().bool_or.literals.extend(v-1 if v > 0 else v for v in clause)


def snapshot(proto, order):
    assert len(proto.variables) == base.N
    assert len(proto.constraints) == base.PREFIX_CONSTRAINTS+len(order)
    assert len(order) == len(set(order))
    assert not proto.HasField('objective') and not proto.HasField('floating_point_objective')
    assert not proto.HasField('solution_hint')
    assert not proto.assumptions and not proto.search_strategy
    raw = proto.SerializeToString(deterministic=True)
    return {'variables': base.N, 'constraints': len(proto.constraints),
            'binary_proto_sha256': base.sha(raw), 'binary_proto_bytes': len(raw),
            'prefix_clause_ids_in_order': list(order)}


def check_native_snapshot(model, proto, order, temporary):
    expected = snapshot(proto, order)
    assert model.validate() == '' and model.export_to_file(str(temporary))
    assert temporary.stat().st_size == expected['binary_proto_bytes']
    assert digest(temporary) == expected['binary_proto_sha256']
    return expected


def status_kind(answer):
    if answer in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return 'candidate'
    if answer == cp_model.UNKNOWN:
        return 'UNKNOWN: native call ended without a feasible candidate'
    if answer == cp_model.INFEASIBLE:
        return 'INFEASIBLE: native status only; no checked exclusion'
    return 'ERROR: invalid or unexpected native solver status'


def controls(output):
    assert not output.exists()
    # Tiny formula padded with true rows to exercise the production append
    # helper and literal numbering, without any case4 mathematical rows.
    raw = b''.join(struct.pack('<H', a)+bits.to_bytes(base.MASK_BYTES, 'little')
                   for a, bits in ((0, 1 << 1), (1, 1 << 2), (3, 0)))
    proto = cp_model_pb2.CpModelProto()
    for a in range(base.N):
        variable = proto.variables.add()
        variable.name = f'x{a}'
        variable.domain.extend((0, 1))
    for _ in range(base.PREFIX_CONSTRAINTS):
        proto.constraints.add().bool_and.SetInParent()
    order, encoded = [2], [2]
    append_proto(proto, raw, order)
    model = base.native_from_proto(proto)
    with tempfile.TemporaryDirectory(prefix='case4-lazy-loop-control-') as directory:
        path = Path(directory)/'prefix.pb'
        check_native_snapshot(model, proto, order, path)
        for batch in ([1], [0]):
            plan, encoded = base.append_batch(model, raw, encoded, batch)
            assert plan['accepted']
            order.extend(batch)
            append_proto(proto, raw, batch)
            check_native_snapshot(model, proto, order, path)
    assert order == [2, 1, 0] and encoded == [0, 1, 2]
    assert status_kind(cp_model.UNKNOWN).startswith('UNKNOWN:')
    assert status_kind(cp_model.INFEASIBLE).startswith('INFEASIBLE:')
    assert status_kind(cp_model.OPTIMAL) == status_kind(cp_model.FEASIBLE) == 'candidate'
    assert status_kind(cp_model.MODEL_INVALID).startswith('ERROR:')
    for status in (cp_model.UNKNOWN, cp_model.INFEASIBLE, cp_model.FEASIBLE,
                   cp_model.OPTIMAL, cp_model.MODEL_INVALID):
        response = cp_model_pb2.CpSolverResponse(status=int(status))
        copied = cp_model_pb2.CpSolverResponse()
        text_format.Parse(str(response), copied)
        assert copied.status == int(status)
        assert cp_model_pb2.CpSolverStatus.Name(copied.status) in (
            'UNKNOWN', 'INFEASIBLE', 'FEASIBLE', 'OPTIMAL', 'MODEL_INVALID')
    result = {'status': 'PASS: exact append order, literal orientation, native bytes and terminal decisions',
              'source_hashes': sources(), 'actual_native_prefix_byte_comparisons': 3,
              'chronological_prefix_distinct_from_sorted_membership': True,
              'terminal_status_controls': 5, 'response_text_parser_controls': 5,
              'solver_called': False, 'main_case4_queries': 0}
    save(output, result)
    print(json.dumps(result, indent=2), flush=True)


def prepare(output, control_path):
    assert not output.exists()
    model = bindings()
    control = json.loads(control_path.read_text())
    assert control['status'].startswith('PASS:') and control['source_hashes'] == sources()
    assert not control['solver_called']
    result = {'status': 'bounded lazy native candidate loop prepared; no production solve',
              'complete': True, 'source_hashes': sources(), 'limits': LIMITS,
              'lazy_model_sha256': MODEL_SHA, 'lazy_cold_replay_sha256': COLD_SHA,
              'runtime_binding_sha256': model['runtime_binding_sha256'],
              'registry_sha256': model['registry_sha256'],
              'initial_prefix_sha256': model['prefix_proto_decompressed_sha256'],
              'controls': portable(control_path), 'controls_sha256': digest(control_path),
              'explicit_solver_parameters': parameter_record(10),
              'solver_parameter_text_at_full_limit': str(configured_solver(10).parameters),
              'initial_variables': 1214, 'initial_constraints': 2285,
              'all_2271_original_base_constraints_and14_proved_units_retained': True,
              'complete_external_cover_count': 178533,
              'atomic_batch_counts_include_initial_units': True,
              'every_newly_violated_registered_cover_is_added_or_whole_batch_refused': True,
              'unknown_stops_immediately': True, 'no_visitation_blocks': True,
              'no_hint_objective_assumptions_or_symmetry_constraints': True,
              'all_candidates_saved_as1214_Boolean_values': True,
              'cold_replay_uses_no_solver': True,
              'one_owned_child_hard_wall_includes_imports_bootstrap_solve_and_inspection': True,
              'RSS_recorded_not_an_OS_memory_limit': True,
              'finite_prefix_equivalent_to_full_cover_formula': False,
              'INFEASIBLE_or_UNKNOWN_is_a_checked_exclusion': False,
              'accepted_point_is_only_partial_incidence': True, 'production_queries': 0}
    save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    print('preparation_sha256', digest(output), flush=True)


def checked_preparation(path):
    record = json.loads(path.read_text())
    assert record['complete'] and record['source_hashes'] == sources()
    assert record['limits'] == LIMITS and record['production_queries'] == 0
    model = bindings()
    assert record['lazy_model_sha256'] == MODEL_SHA and record['lazy_cold_replay_sha256'] == COLD_SHA
    assert record['registry_sha256'] == model['registry_sha256']
    assert record['initial_prefix_sha256'] == model['prefix_proto_decompressed_sha256']
    assert record['runtime_binding_sha256'] == model['runtime_binding_sha256']
    assert digest(ROOT/record['controls']) == record['controls_sha256']
    assert record['explicit_solver_parameters'] == parameter_record(10)
    return record, model


def child(preparation, directory):
    prepared, frozen = checked_preparation(preparation)
    result = {'status': 'active bounded lazy candidate loop', 'source_hashes': sources(),
              'preparation_sha256': digest(preparation), 'lazy_model_sha256': MODEL_SHA,
              'registry_sha256': frozen['registry_sha256'], 'limits': LIMITS,
              'production_solve_calls': 0, 'completed_iterations': [],
              'case4_excluded': False, 'full_graph_completion_found': False}

    def checkpoint(phase, details):
        result.update(phase=phase, phase_details=details,
                      elapsed_seconds=time.monotonic()-PROCESS_STARTED,
                      child_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(directory/'child-progress.json', result)
        print(json.dumps({'phase': phase, 'elapsed_seconds': result['elapsed_seconds'], **details}), flush=True)

    def finish(status, details=None):
        result['status'] = status
        if details:
            result.update(details)
        checkpoint('terminal', {'status': status})
        save(directory/'child-result.json', result)
        print(json.dumps({'terminal': status, 'native_calls': result['production_solve_calls']}), flush=True)

    checkpoint('replaying_frozen_inventory_and_registry', {})
    try:
        _, inventory, raw, proto = base.load_prepared(MODEL)
        model = base.native_from_proto(proto)
        order = list(frozen['initial_prefix_clause_ids_in_order'])
        encoded = sorted(order)
        with tempfile.TemporaryDirectory(prefix='case4-lazy-native-run-') as temporary:
            temp_proto = Path(temporary)/'current.pb'
            for iteration in range(LIMITS['native_calls']):
                remaining = LIMITS['requested_child_seconds']-(time.monotonic()-PROCESS_STARTED)
                if remaining <= 0:
                    finish('UNKNOWN: requested child budget reached before another native call')
                    return
                seconds = min(float(LIMITS['solver_seconds_per_call']), remaining)
                prefix = check_native_snapshot(model, proto, order, temp_proto)
                item_dir = directory/f'iteration{iteration:02d}'
                item_dir.mkdir()
                item = {'iteration': iteration, 'prefix_before': prefix,
                        'explicit_solver_parameters': parameter_record(seconds)}
                save(item_dir/'starting.json', item)
                solver = configured_solver(seconds)
                result['production_solve_calls'] += 1
                checkpoint('native_call', {'iteration': iteration, 'requested_solver_seconds': seconds,
                                          'prefix_constraints': prefix['constraints']})
                started = time.monotonic()
                answer = solver.solve(model)
                response = item_dir/'response.txt'
                response.write_text(str(solver.response_proto)+'\n')
                values = list(map(int, solver.response_proto.solution))
                item.update(backend_status_code=int(answer), backend_status=solver.status_name(answer),
                            solve_elapsed_seconds=time.monotonic()-started,
                            response_file=portable(response), response_sha256=digest(response),
                            native_statistics={'conflicts': solver.num_conflicts,
                                               'branches': solver.num_branches,
                                               'wall_time': solver.wall_time})
                del solver
                gc.collect()
                kind = status_kind(answer)
                terminal = kind if kind != 'candidate' else None
                if kind == 'candidate':
                    checked = base.prefix_assignment_check(values, inventory, raw, encoded)
                    evaluation = base.evaluate(raw, values)
                    missing = evaluation['violated_clause_ids']
                    assert not set(encoded).intersection(missing)
                    candidate = {'boolean_values1214': values, 'selected_columns': checked['selected_columns'],
                                 'prefix_check': checked, 'registry_evaluation': evaluation,
                                 'complete_graph': False}
                    if not missing:
                        candidate['full_frozen_inspection'] = base.native.inspector.inspect_selected(checked['selected_columns'])
                        terminal = 'SAT: exact-checked complete-registry partial incidence'
                        item['accepted_partial_incidence'] = True
                    else:
                        plan, new_encoded = base.append_batch(model, raw, encoded, missing)
                        item['atomic_batch_plan'] = plan
                        if plan['accepted']:
                            encoded = new_encoded
                            order.extend(missing)
                            append_proto(proto, raw, missing)
                            item['appended_clause_ids_in_order'] = missing
                        else:
                            assert new_encoded == encoded
                            item['appended_clause_ids_in_order'] = []
                            terminal = 'UNKNOWN: complete violated-cover batch exceeded atomic resource limits'
                    candidate_path = item_dir/'candidate.json'
                    save(candidate_path, candidate)
                    item.update(candidate=portable(candidate_path), candidate_sha256=digest(candidate_path))
                item['prefix_after'] = check_native_snapshot(model, proto, order, temp_proto)
                item['terminal_status'] = terminal
                item_path = item_dir/'result.json'
                save(item_path, item)
                result['completed_iterations'].append({'path': portable(item_path), 'sha256': digest(item_path)})
                result['final_prefix'] = item['prefix_after']
                checkpoint('iteration_saved', {'iteration': iteration, 'backend_status': item['backend_status'],
                                               'terminal_status': terminal,
                                               'encoded_cover_count': len(encoded)})
                if terminal is not None:
                    finish(terminal)
                    return
            finish('UNKNOWN: native-call budget exhausted after recorded necessary cover additions')
    except Exception as error:
        finish('ERROR: loop or exact inspection failed; no accepted candidate or exclusion',
               {'error_type': type(error).__name__, 'error_message': str(error)})
        raise


def run(preparation, directory):
    assert not directory.exists()
    prepared, frozen = checked_preparation(preparation)
    directory.mkdir(parents=True)
    path = directory/'result.json'
    result = {'status': 'one owned lazy native child active', 'source_hashes': sources(),
              'preparation': portable(preparation), 'preparation_sha256': digest(preparation),
              'lazy_model_sha256': MODEL_SHA, 'registry_sha256': frozen['registry_sha256'],
              'limits': LIMITS, 'production_children': 1, 'retries': 0,
              'case4_excluded': False, 'full_graph_completion_found': False}
    save(path, result)

    def timeout(pid, elapsed):
        result.update(status='UNKNOWN: owned lazy child hard wall exceeded', timeout_pid=pid,
                      elapsed_before_kill=elapsed, no_partial_child_result_used=True)
        save(path, result)

    started = time.monotonic()
    process = watchdog.owned_child([sys.executable, str(Path(__file__).resolve()), '_child',
                                   '--preparation', str(preparation), '--directory', str(directory)],
                                  directory/'child.log', LIMITS['hard_parent_seconds'], timeout)
    result['owned_process'] = process
    child_path = directory/'child-result.json'
    if not process['timed_out']:
        if process['returncode'] != 0 or not child_path.exists():
            result['status'] = 'ERROR: lazy child returned no accepted terminal record'
        else:
            terminal = json.loads(child_path.read_text())
            assert terminal['preparation_sha256'] == digest(preparation)
            assert terminal['source_hashes'] == sources() and terminal['limits'] == LIMITS
            assert not terminal['case4_excluded'] and not terminal['full_graph_completion_found']
            result.update(status=terminal['status'], child_result=portable(child_path),
                          child_result_sha256=digest(child_path))
    progress = directory/'child-progress.json'
    if progress.exists():
        result.update(last_progress=portable(progress), last_progress_sha256=digest(progress))
    result.update(parent_elapsed_seconds=time.monotonic()-started,
                  parent_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(path, result)
    print(json.dumps(result, indent=2), flush=True)


def replay(preparation, result_path, output):
    """Rebuild prefixes and check exact candidates, never call a solver."""
    assert not output.exists()
    prepared, frozen = checked_preparation(preparation)
    result = json.loads(result_path.read_text())
    assert result['source_hashes'] == sources() and result['limits'] == LIMITS
    assert result['preparation_sha256'] == digest(preparation)
    assert result['lazy_model_sha256'] == MODEL_SHA and result['registry_sha256'] == frozen['registry_sha256']
    assert result['production_children'] == 1 and result['retries'] == 0
    assert not result['case4_excluded'] and not result['full_graph_completion_found']
    process = result['owned_process']
    assert process['child_reaped'] and process['requested_wall_seconds'] == LIMITS['hard_parent_seconds']
    assert digest(ROOT/process['log']) == process['log_sha256']
    if 'last_progress' in result:
        assert digest(ROOT/result['last_progress']) == result['last_progress_sha256']
    checked_iterations, checked_candidates, accepted = 0, 0, False
    if process['timed_out']:
        assert result['status'].startswith('UNKNOWN:') and result['no_partial_child_result_used']
        assert process['UNKNOWN_persisted_before_kill'] and process['returncode'] != 0
    elif 'child_result' in result:
        assert process['returncode'] == 0
        path = ROOT/result['child_result']
        assert digest(path) == result['child_result_sha256']
        terminal = json.loads(path.read_text())
        assert terminal['status'] == result['status'] and terminal['source_hashes'] == sources()
        assert terminal['limits'] == LIMITS and terminal['preparation_sha256'] == digest(preparation)
        assert terminal['lazy_model_sha256'] == MODEL_SHA
        assert terminal['registry_sha256'] == frozen['registry_sha256']
        assert not terminal['case4_excluded'] and not terminal['full_graph_completion_found']
        _, inventory, raw, proto = base.load_prepared(MODEL)
        order = list(frozen['initial_prefix_clause_ids_in_order'])
        encoded = sorted(order)
        records = terminal['completed_iterations']
        assert len(records) == terminal['production_solve_calls'] <= LIMITS['native_calls']
        last_terminal = None
        for iteration, saved in enumerate(records):
            assert last_terminal is None
            path = ROOT/saved['path']
            assert digest(path) == saved['sha256']
            item = json.loads(path.read_text())
            assert item['iteration'] == iteration and item['prefix_before'] == snapshot(proto, order)
            seconds = item['explicit_solver_parameters']['max_time_in_seconds']
            assert item['explicit_solver_parameters'] == parameter_record(seconds)
            response_path = ROOT/item['response_file']
            assert digest(response_path) == item['response_sha256']
            response = cp_model_pb2.CpSolverResponse()
            text_format.Parse(response_path.read_text(), response)
            assert response.status == item['backend_status_code']
            assert cp_model_pb2.CpSolverStatus.Name(response.status) == item['backend_status']
            assert response.num_conflicts == item['native_statistics']['conflicts']
            assert response.num_branches == item['native_statistics']['branches']
            kind = status_kind(response.status)
            expected_terminal = kind if kind != 'candidate' else None
            if kind == 'candidate':
                candidate_path = ROOT/item['candidate']
                assert digest(candidate_path) == item['candidate_sha256']
                candidate = json.loads(candidate_path.read_text())
                values = candidate['boolean_values1214']
                assert values == list(response.solution)
                checked = base.prefix_assignment_check(values, inventory, raw, encoded)
                assert checked == candidate['prefix_check']
                assert checked['selected_columns'] == candidate['selected_columns']
                evaluated = base.evaluate(raw, values)
                assert evaluated == candidate['registry_evaluation'] and not candidate['complete_graph']
                missing = evaluated['violated_clause_ids']
                assert not set(encoded).intersection(missing)
                if not missing:
                    assert base.native.normalized(base.native.inspector.inspect_selected(checked['selected_columns'])) == candidate['full_frozen_inspection']
                    assert item['accepted_partial_incidence']
                    accepted = True
                    expected_terminal = 'SAT: exact-checked complete-registry partial incidence'
                else:
                    planned = base.plan_batch(raw, encoded, missing)
                    assert planned == item['atomic_batch_plan']
                    if planned['accepted']:
                        assert item['appended_clause_ids_in_order'] == missing
                        order.extend(missing)
                        encoded = sorted(encoded+missing)
                        append_proto(proto, raw, missing)
                    else:
                        assert item['appended_clause_ids_in_order'] == []
                        expected_terminal = 'UNKNOWN: complete violated-cover batch exceeded atomic resource limits'
                checked_candidates += 1
            assert item['prefix_after'] == snapshot(proto, order)
            assert item['terminal_status'] == expected_terminal
            last_terminal = expected_terminal
            checked_iterations += 1
        if records:
            assert terminal['final_prefix'] == snapshot(proto, order)
        if last_terminal is not None:
            assert terminal['status'] == last_terminal
        else:
            assert terminal['status'] in (
                'UNKNOWN: requested child budget reached before another native call',
                'UNKNOWN: native-call budget exhausted after recorded necessary cover additions')
            if 'native-call budget exhausted' in terminal['status']:
                assert len(records) == LIMITS['native_calls']
    else:
        assert result['status'].startswith('ERROR:')
    report = {'status': 'PASS: bounded outcome bindings and all completed terminal candidate decisions replayed',
              'source_hashes': sources(), 'preparation_sha256': digest(preparation),
              'result_sha256': digest(result_path), 'terminal_status': result['status'],
              'checked_iterations': checked_iterations, 'checked_complete_Boolean_candidates': checked_candidates,
              'accepted_partial_incidence': accepted, 'solver_or_optimizer_called': False,
              'timed_out_partial_child_transcript_used': False,
              'case4_excluded': False, 'full_graph_completion_found': False,
              'finite_prefix_equivalent_to_full_cover_formula': False}
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    control = commands.add_parser('controls')
    control.add_argument('--output', type=Path, required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--controls', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    for name in ('run', '_child'):
        sub = commands.add_parser(name)
        sub.add_argument('--preparation', type=Path, required=True)
        sub.add_argument('--directory', type=Path, required=True)
    cold = commands.add_parser('replay')
    cold.add_argument('--preparation', type=Path, required=True)
    cold.add_argument('--result', type=Path, required=True)
    cold.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'controls':
        controls(args.output.resolve())
    elif args.command == 'prepare':
        prepare(args.output.resolve(), args.controls.resolve())
    elif args.command == 'run':
        run(args.preparation.resolve(), args.directory.resolve())
    elif args.command == '_child':
        child(args.preparation.resolve(), args.directory.resolve())
    else:
        replay(args.preparation.resolve(), args.result.resolve(), args.output.resolve())
