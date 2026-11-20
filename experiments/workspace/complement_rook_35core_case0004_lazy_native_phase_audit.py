"""Read the frozen lazy run's explicit phase log; no model or solver call."""

import argparse
import hashlib
import json
from pathlib import Path
import re

from google.protobuf import text_format
from ortools.sat import cp_model_pb2


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/grids-and-triangles'
RUN = LOGS/'complement-rook-35core-case0004-lazy-native-run01'
RESULT_SHA = '3c0b23f7a44a4b11de99477bbdc2c2638b6028d12d8bb90d7d2fc5c44035fe1e'
COLD = LOGS/'complement-rook-35core-case0004-lazy-native-run01-cold-replay.json'
COLD_SHA = '5a0f7524aedb9dba19a705c30963d525db86cc969461f36073092a82bcd70f07'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def check(output):
    assert not output.exists()
    assert digest(RUN/'result.json') == RESULT_SHA and digest(COLD) == COLD_SHA
    result, cold = (json.loads(path.read_text()) for path in (RUN/'result.json', COLD))
    assert result['status'] == 'UNKNOWN: native call ended without a feasible candidate'
    assert cold['status'].startswith('PASS:') and cold['checked_iterations'] == 1
    assert cold['checked_complete_Boolean_candidates'] == 0 and not cold['solver_or_optimizer_called']
    assert result['owned_process']['child_reaped'] and not result['owned_process']['timed_out']
    child_path = ROOT/result['child_result']
    assert digest(child_path) == result['child_result_sha256']
    child = json.loads(child_path.read_text())
    assert child['production_solve_calls'] == len(child['completed_iterations']) == 1
    assert not child['case4_excluded'] and not child['full_graph_completion_found']
    saved = child['completed_iterations'][0]
    item_path = ROOT/saved['path']
    assert digest(item_path) == saved['sha256']
    item = json.loads(item_path.read_text())
    assert item['prefix_before'] == item['prefix_after']
    assert len(item['prefix_after']['prefix_clause_ids_in_order']) == 14
    assert item['prefix_after']['constraints'] == 2285
    assert item['explicit_solver_parameters'] == {
        'max_time_in_seconds': 10.0, 'num_search_workers': 1,
        'log_search_progress': True, 'log_to_stdout': True}
    assert 'candidate' not in item
    log_path = ROOT/result['owned_process']['log']
    assert digest(log_path) == result['owned_process']['log_sha256']
    log = log_path.read_text()
    response_path = ROOT/item['response_file']
    assert digest(response_path) == item['response_sha256']
    response = cp_model_pb2.CpSolverResponse()
    text_format.Parse(response_path.read_text(), response)
    assert response.status == 0 and len(response.solution) == 0
    search = re.findall(r'^Starting search at ([0-9.]+)s with 1 workers\.$', log, re.M)
    main = re.findall(r"^Starting subsolver 'main' search at ([0-9.]+)s$", log, re.M)
    assert len(search) == len(main) == 1
    task = re.search(r"'main':\s+1 \[\s*([0-9.]+)s,\s*([0-9.]+)s\]\s*([0-9.]+)s", log)
    assert task and len(set(task.groups())) == 1
    phases = [json.loads(line) for line in log.splitlines() if line.startswith('{"phase":')]
    assert [item['phase'] for item in phases] == [
        'replaying_frozen_inventory_and_registry', 'native_call', 'iteration_saved', 'terminal']
    stats = {key: int(getattr(response, key)) for key in (
        'num_booleans', 'num_integers', 'num_conflicts', 'num_branches',
        'num_binary_propagations', 'num_integer_propagations', 'num_restarts', 'num_lp_iterations')}
    assert stats['num_conflicts'] == 147 and stats['num_branches'] == 67183
    assert stats['num_lp_iterations'] == 75457
    for label, field in (('conflicts', 'num_conflicts'), ('branches', 'num_branches'),
                         ('lp_iterations', 'num_lp_iterations')):
        found = re.findall(r'^'+label+r': ([0-9]+)$', log, re.M)
        assert list(map(int, found)) == [stats[field]]
    report = {'status': 'PASS: explicit lazy-run phase timing and terminal statistics audited',
        'audit_source_sha256': digest(Path(__file__)), 'result_sha256': RESULT_SHA,
        'cold_replay_sha256': COLD_SHA, 'child_log_sha256': digest(log_path),
        'response_sha256': digest(response_path), 'native_calls': 1,
        'candidate_count': 0, 'appended_cover_count': 0,
        'solver_search_start_seconds_rounded': float(search[0]),
        'main_search_start_seconds_rounded': float(main[0]),
        'main_task_wall_seconds_rounded': float(task.group(1)),
        'response_solver_wall_seconds': response.wall_time,
        'response_solver_deterministic_time': response.deterministic_time,
        'child_elapsed_seconds': child['elapsed_seconds'],
        'child_peak_rss_kib': child['child_peak_rss_kib'],
        'parent_observed_child_seconds': result['owned_process']['elapsed_seconds'],
        'statistics': stats, 'checkpoint_phases': phases,
        'search_reached_quickly_from_explicit_log': True,
        'LP_iteration_count_is_not_a_per_phase_CPU_profile': True,
        'earlier_full_native_query_had_no_phase_log_and_is_not_reclassified': True,
        'frozen_prefix_unchanged': True, 'solver_or_optimizer_called': False,
        'native_model_rebuilt': False, 'case4_excluded': False,
        'interpretation': 'The lazy call spent most of its solver interval in its main task. It did not stall in initial presolve. No candidate or new mathematical restriction resulted.'}
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2))
    print('report_sha256', digest(output))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    check(args.output.resolve())
