"""One bounded candidate query of the frozen native case4 model.

Preparation is separate. An owned child reconstructs the same binary
proto, then runs one 60-second, one-worker CP-SAT solve with no objective,
assumptions, or hint. The parent has a 180-second hard wall covering the
child's imports, reconstruction, solve, and exact candidate inspection.
The already audited watchdog persists UNKNOWN before terminating and
reaping a timed-out child. No INFEASIBLE status is a checked exclusion.
"""

import argparse
import gc
import json
from pathlib import Path
import resource
import sys
import tempfile
import time

from ortools.sat.python import cp_model

import complement_rook_35core_case0004_native_cpsat as native
import complement_rook_35core_case0004_coordinate_cover_cadical as watchdog


ROOT, LOGS = native.ROOT, native.LOGS
digest, canonical, portable, save = native.digest, native.canonical, native.portable, native.save
MODEL = LOGS / 'complement-rook-35core-case0004-native-cpsat-model.json'
MODEL_SHA = 'a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476'
COLD = LOGS / 'complement-rook-35core-case0004-native-cpsat-cold-replay.json'
COLD_SHA = 'a6627477382b47013a0b26984826a565df879b0f226dc2ad505da318e751b5a7'
NATIVE_MANIFEST = LOGS / 'complement-rook-35core-case0004-native-cpsat-preparation-artifacts.json'
NATIVE_MANIFEST_SHA = 'a4f6f6338b7de68ff0bb6215209f19b35c4867e584d49292e0c6ac1b2ce3f8f6'
WATCHDOG_PREPARATION = LOGS / 'complement-rook-35core-case0004-coordinate-cover-cadical-preparation.json'
WATCHDOG_PREPARATION_SHA = 'e7a4185a300a48edbe01d7103da8e765dab1ad9653e2678992d3f1c4e986d731'
DEPENDENCIES = {
    'complement_rook_35core_case0004_native_cpsat.py': '4462dae913abcb736c5ba5f7cffc3f3e7d50b748826cab3c89fffbfd3bd0e3eb',
    'complement_rook_35core_case0004_coordinate_cover_cadical.py': '1921f71964795d819e0369c9679dc1526df97c29bb1920a932c7ca449ba3de25',
}
LIMITS = {'CP_SAT_solver_seconds': 60, 'CP_SAT_workers': 1, 'owned_child_wall_seconds': 180}


def source_hashes():
    names = set(native.source_hashes()) | set(DEPENDENCIES) | {Path(__file__).name}
    return {name: digest(Path(__file__).with_name(name)) for name in sorted(names)}


def check_inputs(require_original_proto=False):
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    for path, expected in [(MODEL, MODEL_SHA), (COLD, COLD_SHA),
                           (NATIVE_MANIFEST, NATIVE_MANIFEST_SHA),
                           (WATCHDOG_PREPARATION, WATCHDOG_PREPARATION_SHA)]:
        assert digest(path) == expected
    for entry in json.loads(NATIVE_MANIFEST.read_text())['files']:
        assert digest(ROOT / entry['path']) == entry['sha256']
    model, cold = json.loads(MODEL.read_text()), json.loads(COLD.read_text())
    assert model['complete'] and model['main_case4_solver_queries'] == 0
    assert model['source_hashes'] == native.source_hashes()
    assert model['runtime_binding'] == native.runtime_binding()
    assert cold['status'].startswith('PASS:') and cold['model_sha256'] == MODEL_SHA
    assert cold['binary_proto_sha256'] == model['binary_proto_sha256']
    if require_original_proto:
        assert digest(Path(model['binary_proto'])) == model['binary_proto_sha256']
    watched = json.loads(WATCHDOG_PREPARATION.read_text())
    assert watched['source_hashes']['complement_rook_35core_case0004_coordinate_cover_cadical.py'] == DEPENDENCIES['complement_rook_35core_case0004_coordinate_cover_cadical.py']
    return model


def configured_solver():
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = LIMITS['CP_SAT_solver_seconds']
    solver.parameters.num_search_workers = LIMITS['CP_SAT_workers']
    return solver


def prepare(output):
    assert not output.exists()
    model = check_inputs(True)
    solver = configured_solver()  # No solve call in preparation.
    report = {
        'status': 'one native case4 candidate query prepared; no production solve',
        'complete': True, 'source_hashes': source_hashes(), 'limits': LIMITS,
        'native_model_sha256': MODEL_SHA, 'native_cold_replay_sha256': COLD_SHA,
        'native_preparation_manifest_sha256': NATIVE_MANIFEST_SHA,
        'runtime_binding_sha256': native.sha(canonical(model['runtime_binding'])),
        'binary_proto_sha256': model['binary_proto_sha256'],
        'variables': 1214, 'constraints': 180804,
        'solver_parameter_text': str(solver.parameters),
        'only_explicit_solver_parameters': {'max_time_in_seconds': 60, 'num_search_workers': 1},
        'watchdog_source_sha256': DEPENDENCIES['complement_rook_35core_case0004_coordinate_cover_cadical.py'],
        'previous_passed_watchdog_control_preparation_sha256': WATCHDOG_PREPARATION_SHA,
        'child_model_rebuilt_and_binary_hash_checked_before_solve': True,
        'hard_child_wall_includes_imports_reconstruction_solve_and_inspection': True,
        'timeout_persisted_before_kill_and_child_reaped': True,
        'RSS_is_recorded_not_an_OS_memory_limit': True,
        'objective_assumptions_hint_symmetry_or_extra_constraints': False,
        'production_queries': 0,
        'SAT_scope': 'Exact-checked partial64-column incidence only; no exterior graph.',
        'INFEASIBLE_and_UNKNOWN_scope': 'Unresolved; no checked exclusion or proof is claimed.',
    }
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)
    print('preparation_sha256', digest(output), flush=True)


def checked_preparation(path):
    record = json.loads(path.read_text())
    assert record['complete'] and record['source_hashes'] == source_hashes()
    assert record['limits'] == LIMITS and record['production_queries'] == 0
    model = check_inputs()
    assert record['native_model_sha256'] == MODEL_SHA and record['native_cold_replay_sha256'] == COLD_SHA
    assert record['binary_proto_sha256'] == model['binary_proto_sha256']
    assert record['runtime_binding_sha256'] == native.sha(canonical(model['runtime_binding']))
    assert record['solver_parameter_text'] == str(configured_solver().parameters)
    return record, model


def child(preparation, directory):
    started = time.monotonic()
    record, frozen = checked_preparation(preparation)
    result = {'status': 'rebuilding exact native model in owned child',
              'query_preparation_sha256': digest(preparation), 'source_hashes': source_hashes(),
              'native_model_sha256': MODEL_SHA, 'binary_proto_sha256': frozen['binary_proto_sha256'],
              'case4_excluded': False, 'full_graph_completion_found': False, 'production_solve_calls': 0}

    def checkpoint(phase, values):
        result.update(phase=phase, phase_values=values, elapsed_seconds=time.monotonic()-started,
                      child_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(directory / 'child-progress.json', result)
        print(json.dumps({'phase': phase, 'elapsed_seconds': result['elapsed_seconds'], **values}), flush=True)
        native.check_budget(started)

    checkpoint('starting', {})
    try:
        with tempfile.TemporaryDirectory(prefix='conway-case4-native-query-') as temporary:
            cover_path = Path(temporary) / 'covers.txt'
            cover = native.write_cover_body(cover_path)
            assert native.normalized(cover) == frozen['cover_replay_and_stream']
            checkpoint('full_cover_ledger_replayed', {'clauses': cover['clauses']})
            inventory = native.load_inventory()
            assert native.normalized(inventory) == frozen['primary_inventory']
            model = native.build_native(inventory, cover_path, checkpoint)
            rebuilt_path = Path(temporary) / 'rebuilt.pb'
            assert model.export_to_file(str(rebuilt_path))
            assert digest(rebuilt_path) == frozen['binary_proto_sha256']
            assert rebuilt_path.stat().st_size == frozen['binary_proto_bytes']
        solver = configured_solver()
        assert str(solver.parameters) == record['solver_parameter_text']
        result.update(reconstruction_seconds=time.monotonic()-started,
                      solver_parameter_text=str(solver.parameters), production_solve_calls=1)
        checkpoint('starting_one_60_second_solve', {'variables': 1214, 'constraints': 180804})
        solve_started = time.monotonic()
        answer = solver.solve(model)
        result['solve_stage_elapsed_seconds'] = time.monotonic()-solve_started
        result['backend_status_code'] = int(answer)
        result['backend_status'] = solver.status_name(answer)
        result['backend_statistics'] = {'conflicts': solver.num_conflicts, 'branches': solver.num_branches,
                                        'wall_time': solver.wall_time, 'user_time': solver.user_time}
        response = directory / 'response.txt'
        response.write_text(str(solver.response_proto) + '\n')
        result['response_file'] = portable(response)
        result['response_sha256'] = digest(response)
        values = list(solver.response_proto.solution)
        del solver, model
        gc.collect()
        if answer in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            assert len(values) == 1214 and all(value in (0, 1) for value in values)
            selected = [a for a, value in enumerate(values) if value]
            inspection = native.inspector.inspect_selected(selected)
            candidate = {'selected_columns': selected, 'inspection': inspection,
                         'native_model_sha256': MODEL_SHA,
                         'binary_proto_sha256': frozen['binary_proto_sha256'],
                         'complete_graph': False, 'remaining64_vertex_adjacency_unspecified': True}
            candidate_path = directory / 'candidate.json'
            save(candidate_path, candidate)
            result.update(status='SAT: exact-checked partial incidence only',
                          candidate=portable(candidate_path), candidate_sha256=digest(candidate_path))
        elif answer == cp_model.INFEASIBLE:
            result['status'] = 'INFEASIBLE: backend outcome only; no checked mathematical exclusion'
        elif answer == cp_model.UNKNOWN:
            result['status'] = 'UNKNOWN: bounded native search unresolved'
        else:
            result['status'] = 'ERROR: native solver returned MODEL_INVALID or an unexpected status'
        result.update(elapsed_seconds=time.monotonic()-started,
                      child_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(directory / 'child-result.json', result)
        print(json.dumps(result, indent=2), flush=True)
    except Exception as error:
        result.update(status='ERROR: query or exact inspection failed; no accepted candidate or exclusion',
                      error_type=type(error).__name__, error_message=str(error),
                      elapsed_seconds=time.monotonic()-started,
                      child_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(directory / 'child-result.json', result)
        raise


def solve(preparation, directory):
    assert not directory.exists()
    record, model = checked_preparation(preparation)
    directory.mkdir(parents=True)
    result_path = directory / 'result.json'
    started = time.monotonic()
    result = {'status': 'one owned native case4 query active',
              'query_preparation': portable(preparation), 'query_preparation_sha256': digest(preparation),
              'source_hashes': source_hashes(), 'native_model_sha256': MODEL_SHA,
              'binary_proto_sha256': model['binary_proto_sha256'], 'limits': LIMITS,
              'case4_excluded': False, 'full_graph_completion_found': False,
              'retries': 0, 'production_children': 1}
    save(result_path, result)

    def timeout(pid, elapsed):
        result.update(status='UNKNOWN: owned child hard wall exceeded',
                      timeout_pid=pid, elapsed_before_kill=elapsed,
                      no_partial_child_result_used=True)
        save(result_path, result)

    process = watchdog.owned_child([sys.executable, str(Path(__file__).resolve()), '_child',
                                   '--preparation', str(preparation), '--directory', str(directory)],
                                  directory / 'child.log', LIMITS['owned_child_wall_seconds'], timeout)
    result['owned_process'] = process
    if not process['timed_out']:
        child_path = directory / 'child-result.json'
        if process['returncode'] != 0 or not child_path.exists():
            result['status'] = 'ERROR: native child did not return an accepted terminal record'
        else:
            terminal = json.loads(child_path.read_text())
            assert terminal['query_preparation_sha256'] == digest(preparation)
            assert terminal['source_hashes'] == source_hashes()
            assert terminal['native_model_sha256'] == MODEL_SHA
            assert terminal['binary_proto_sha256'] == model['binary_proto_sha256']
            assert not terminal['case4_excluded'] and not terminal['full_graph_completion_found']
            result.update(status=terminal['status'], child_result=portable(child_path),
                          child_result_sha256=digest(child_path))
    result.update(parent_elapsed_seconds=time.monotonic()-started,
                  parent_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(result_path, result)
    print(json.dumps(result, indent=2), flush=True)


def replay(preparation, result_path, output):
    assert not output.exists()
    record, model = checked_preparation(preparation)
    result = json.loads(result_path.read_text())
    assert result['source_hashes'] == source_hashes() and result['limits'] == LIMITS
    assert result['query_preparation_sha256'] == digest(preparation)
    assert result['native_model_sha256'] == MODEL_SHA and result['binary_proto_sha256'] == model['binary_proto_sha256']
    assert result['production_children'] == 1 and result['retries'] == 0
    assert not result['case4_excluded'] and not result['full_graph_completion_found']
    process = result['owned_process']
    assert process['child_reaped'] and process['requested_wall_seconds'] == LIMITS['owned_child_wall_seconds']
    assert digest(ROOT / process['log']) == process['log_sha256']
    inspection = None
    if process['timed_out']:
        assert result['status'].startswith('UNKNOWN:') and result['no_partial_child_result_used']
        assert process['UNKNOWN_persisted_before_kill'] and process['returncode'] != 0
    elif 'child_result' in result:
        path = ROOT / result['child_result']
        assert digest(path) == result['child_result_sha256'] and process['returncode'] == 0
        terminal = json.loads(path.read_text())
        assert terminal['status'] == result['status'] and terminal['source_hashes'] == source_hashes()
        assert terminal['production_solve_calls'] == 1
        assert terminal['solver_parameter_text'] == record['solver_parameter_text']
        assert digest(ROOT / terminal['response_file']) == terminal['response_sha256']
        if terminal['status'].startswith('SAT:'):
            candidate_path = ROOT / terminal['candidate']
            assert digest(candidate_path) == terminal['candidate_sha256']
            candidate = json.loads(candidate_path.read_text())
            inspection = native.inspector.inspect_selected(candidate['selected_columns'])
            assert native.normalized(inspection) == candidate['inspection']
            assert not candidate['complete_graph']
    else:
        assert result['status'].startswith('ERROR:')
    with tempfile.TemporaryDirectory(prefix='conway-case4-native-query-cold-') as directory:
        cold_path = Path(directory) / 'cold.json'
        native.replay(MODEL, cold_path)
        cold = json.loads(cold_path.read_text())
    report = {'status': 'PASS: full cold native model and bounded outcome bindings replayed',
              'source_hashes': source_hashes(), 'query_preparation_sha256': digest(preparation),
              'result_sha256': digest(result_path), 'terminal_status': result['status'],
              'binary_proto_sha256': model['binary_proto_sha256'],
              'full_cold_model_replay': cold, 'exact_candidate_inspection': inspection,
              'production_query_repeated': False, 'case4_excluded': False,
              'full_graph_completion_found': False}
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--output', type=Path, required=True)
    for name in ('solve', '_child'):
        run = commands.add_parser(name)
        run.add_argument('--preparation', type=Path, required=True)
        run.add_argument('--directory', type=Path, required=True)
    check = commands.add_parser('replay')
    check.add_argument('--preparation', type=Path, required=True)
    check.add_argument('--result', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output.resolve())
    elif args.command == 'solve':
        solve(args.preparation.resolve(), args.directory.resolve())
    elif args.command == '_child':
        child(args.preparation.resolve(), args.directory.resolve())
    else:
        replay(args.preparation.resolve(), args.result.resolve(), args.output.resolve())
