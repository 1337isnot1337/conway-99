"""Bind a terminal native outcome without rebuilding or repeating a solve.

For a feasible assignment only, call the frozen exact incidence inspector.
Other statuses remain unresolved. The exported native model was already
fully cold-rebuilt before the query; this audit checks that binding and
the current source/runtime files instead of rebuilding it again.
"""

import argparse
import hashlib
import json
from pathlib import Path

from google.protobuf import text_format
from ortools.sat import cp_model_pb2


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT / 'experiments/workspace'
LOGS = ROOT / 'experiments/logs/grids-and-triangles'
PREFIX = 'complement-rook-35core-case0004-native-cpsat-'
BINDINGS = {
    'model.json': 'a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476',
    'cold-replay.json': 'a6627477382b47013a0b26984826a565df879b0f226dc2ad505da318e751b5a7',
    'preparation-artifacts.json': 'a4f6f6338b7de68ff0bb6215209f19b35c4867e584d49292e0c6ac1b2ce3f8f6',
    'query-preparation.json': 'e222ebdad0db2706fe5decdd454d1de3369f476ff3118165f6f68a0e1c003ef0',
    'query-preparation-artifacts.json': '3e26a1bd2ef0124a97222987c9af369d8693da5279657fdd0e4dd638b893d85a',
    'coordinator-review.json': '09fd7780aa5ba819ae6791a46a54deb47ec63d8a2e207a4a31d1b92f611b6542',
}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalized(value):
    return json.loads(json.dumps(value, sort_keys=True, separators=(',', ':')))


def audit(result_path):
    inputs = {}
    for name, expected in BINDINGS.items():
        path = LOGS / (PREFIX + name)
        assert digest(path) == expected
        inputs[name] = json.loads(path.read_text())
    model, prep, cold = inputs['model.json'], inputs['query-preparation.json'], inputs['cold-replay.json']
    for name in ('preparation-artifacts.json', 'query-preparation-artifacts.json'):
        for entry in inputs[name]['files']:
            path = ROOT / entry['path']
            assert digest(path) == entry['sha256'] and path.stat().st_size == entry['bytes']
    for name, expected in prep['source_hashes'].items():
        assert digest(WORK / name) == expected
    for name, expected in model['source_hashes'].items():
        assert prep['source_hashes'][name] == expected
    for entry in model['runtime_binding']['files']:
        path = Path(entry['path'])
        assert digest(path) == entry['sha256'] and path.stat().st_size == entry['bytes']
    assert cold['model_sha256'] == BINDINGS['model.json']
    assert cold['binary_proto_sha256'] == prep['binary_proto_sha256'] == model['binary_proto_sha256']
    result = json.loads(result_path.read_text())
    assert result['source_hashes'] == prep['source_hashes']
    assert result['native_model_sha256'] == BINDINGS['model.json']
    assert result['query_preparation_sha256'] == BINDINGS['query-preparation.json']
    assert result['binary_proto_sha256'] == model['binary_proto_sha256']
    assert result['limits'] == prep['limits'] == {
        'CP_SAT_solver_seconds': 60, 'CP_SAT_workers': 1, 'owned_child_wall_seconds': 180}
    assert result['production_children'] == 1 and result['retries'] == 0
    assert result['case4_excluded'] is False and result['full_graph_completion_found'] is False
    process = result['owned_process']
    assert process['child_reaped'] and process['requested_wall_seconds'] == 180
    assert digest(ROOT / process['log']) == process['log_sha256']
    candidate_inspection = None
    backend = None
    if process['timed_out']:
        assert result['status'] == 'UNKNOWN: owned child hard wall exceeded'
        assert result['no_partial_child_result_used'] and process['UNKNOWN_persisted_before_kill']
        assert 'child_result' not in result
    elif 'child_result' in result:
        path = ROOT / result['child_result']
        assert digest(path) == result['child_result_sha256'] and process['returncode'] == 0
        child = json.loads(path.read_text())
        assert child['status'] == result['status'] and child['source_hashes'] == prep['source_hashes']
        assert child['native_model_sha256'] == BINDINGS['model.json']
        assert child['binary_proto_sha256'] == model['binary_proto_sha256']
        assert child['query_preparation_sha256'] == BINDINGS['query-preparation.json']
        assert child['production_solve_calls'] == 1
        assert child['solver_parameter_text'] == prep['solver_parameter_text']
        assert child['case4_excluded'] is False and child['full_graph_completion_found'] is False
        response_path = ROOT / child['response_file']
        assert digest(response_path) == child['response_sha256']
        response = cp_model_pb2.CpSolverResponse()
        text_format.Parse(response_path.read_text(), response)
        assert response.status == child['backend_status_code']
        assert cp_model_pb2.CpSolverStatus.Name(response.status) == child['backend_status']
        assert response.num_conflicts == child['backend_statistics']['conflicts']
        assert response.num_branches == child['backend_statistics']['branches']
        backend = {'status': child['backend_status'], 'statistics': child['backend_statistics'],
                   'reconstruction_seconds': child['reconstruction_seconds'],
                   'solve_stage_elapsed_seconds': child['solve_stage_elapsed_seconds'],
                   'child_elapsed_seconds': child['elapsed_seconds'],
                   'child_peak_rss_kib': child['child_peak_rss_kib']}
        if response.status in (cp_model_pb2.OPTIMAL, cp_model_pb2.FEASIBLE):
            assert result['status'] == 'SAT: exact-checked partial incidence only'
            candidate_path = ROOT / child['candidate']
            assert digest(candidate_path) == child['candidate_sha256']
            candidate = json.loads(candidate_path.read_text())
            assert len(response.solution) == 1214 and all(value in (0, 1) for value in response.solution)
            assert candidate['selected_columns'] == [a for a, value in enumerate(response.solution) if value]
            assert candidate['native_model_sha256'] == BINDINGS['model.json']
            assert candidate['binary_proto_sha256'] == model['binary_proto_sha256']
            from complement_rook_35core_case0004_coordinate_cover_query import inspect_selected
            candidate_inspection = inspect_selected(candidate['selected_columns'])
            assert normalized(candidate_inspection) == candidate['inspection']
            assert candidate['complete_graph'] is False
        elif response.status == cp_model_pb2.INFEASIBLE:
            assert result['status'] == 'INFEASIBLE: backend outcome only; no checked mathematical exclusion'
            assert 'candidate' not in child
        elif response.status == cp_model_pb2.UNKNOWN:
            assert result['status'] == 'UNKNOWN: bounded native search unresolved'
            assert 'candidate' not in child
        else:
            assert result['status'].startswith('ERROR:')
    else:
        assert result['status'].startswith('ERROR:')
    return {'status': 'PASS: terminal native outcome/source/runtime/proto bindings checked',
            'source_sha256': digest(Path(__file__)), 'input_bindings': BINDINGS,
            'result_sha256': digest(result_path), 'terminal_status': result['status'],
            'backend_outcome': backend, 'exact_candidate_inspection': candidate_inspection,
            'source_files_checked': len(prep['source_hashes']),
            'runtime_files_checked': len(model['runtime_binding']['files']),
            'prior_complete_cold_proto_replay_sha256': BINDINGS['cold-replay.json'],
            'binary_proto_sha256': model['binary_proto_sha256'],
            'new_model_reconstruction': False, 'solver_or_optimizer_called': False,
            'CP_SAT_model_or_solver_imported': False,
            'exact_inspector_imported_only_for_SAT': candidate_inspection is not None,
            'case4_excluded': False, 'complete_graph_found': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--result', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = audit(args.result.resolve())
    args.output.write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps(report, indent=2), flush=True)
    print('audit_sha256', digest(args.output), flush=True)
