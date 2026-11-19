"""Diagnose the frozen shared-edge UNKNOWN without repeating its LP.

The terminal record has no saved numerical ray. A bound-source control
checks that every successful getDualRay exists branch would have saved
the ray before attempting any integer reconstruction. No missing ray,
basis, scale trial or numerical cause is invented.
"""

import argparse
import ast
import hashlib
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
SOURCE = ROOT/'experiments/workspace/root_prism_free_f0_shared_deficit_separator.py'
SOURCE_SHA = '6bc6944ed00713d384251ab54e54684e6f5ea29300f9ff243df5282f522375bf'
RESULT = LOGS/'f0-lazy-continuation-run01/result.json'
RESULT_SHA = '3bb89930202266409acfce6ca52949b5c370928216ce64e9123e22daf5f9e593'
COLD = LOGS/'f0-lazy-continuation-run01-cold-replay.json'
COLD_SHA = '7bd045ab660f3aedd2bd9c514c9e2fa8a91a4f07f415cebba2c133adc73b2330'
SHARED = LOGS/'f0-lazy-continuation-run01/iteration016/shared-rows.json'
SHARED_SHA = '2b7b8796a2642dc77ebea1126582c9a39497f35530856b35084c183ff75fe3b7'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def ray_path_control():
    tree = ast.parse(SOURCE.read_text())
    query = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == 'query')
    ray_assignments = [node for node in ast.walk(query) if isinstance(node, ast.Assign)
                       and isinstance(node.value, ast.Call) and isinstance(node.value.func, ast.Attribute)
                       and node.value.func.attr == 'getDualRay']
    assert len(ray_assignments) == 1
    assignment = ray_assignments[0]
    assert len(assignment.targets) == 1 and isinstance(assignment.targets[0], ast.Tuple)
    assert [node.id for node in assignment.targets[0].elts] == ['_', 'exists', 'numerical']
    branches = [node for node in ast.walk(query) if isinstance(node, ast.If)
                and isinstance(node.test, ast.Name) and node.test.id == 'exists']
    assert len(branches) == 1
    branch = branches[0]
    saves = [i for i, node in enumerate(branch.body) if isinstance(node, ast.Assign)
             and any(isinstance(target, ast.Subscript) and isinstance(target.value, ast.Name)
                     and target.value.id == 'report' and isinstance(target.slice, ast.Constant)
                     and target.slice.value == 'numerical_ray_hex' for target in node.targets)]
    trials = [i for i, node in enumerate(branch.body) if isinstance(node, ast.For)
              and isinstance(node.iter, ast.Call) and isinstance(node.iter.func, ast.Name)
              and node.iter.func.id == 'deficit_ray_candidates']
    assert len(saves) == len(trials) == 1 and saves[0] < trials[0]
    return {'getDualRay_exists_branch_saves_hex_before_all_deficit_trials': True,
            'getDualRay_API_status_assigned_to_discarded_name': True,
            'exists_branch_AST_sha256': hashlib.sha256(ast.dump(branch).encode()).hexdigest()}


def calculate():
    for path, expected in ((SOURCE, SOURCE_SHA), (RESULT, RESULT_SHA), (COLD, COLD_SHA), (SHARED, SHARED_SHA)):
        assert digest(path) == expected
    result = json.loads(RESULT.read_text())
    cold = json.loads(COLD.read_text())
    raw = json.loads(SHARED.read_text())
    assert result['status'] == 'UNKNOWN: numerical infeasibility without an exact ray; unresolved'
    assert cold['result_sha256'] == RESULT_SHA and cold['status'].endswith('PASS')
    assert raw['source_sha256'] == SOURCE_SHA and raw['optimizer_calls'] == 1
    assert raw['status'] == 'UNKNOWN: numerical infeasibility without an exact ray'
    assert raw['numerical_status'] == 'HighsModelStatus.kInfeasible'
    assert not raw['exact_linear_feasibility'] and not raw['exact_fixed_design_infeasibility']
    for name in ('numerical_ray_hex', 'integer_ray', 'ray_reconstruction', 'error_type', 'error_message'):
        assert name not in raw
    path = ray_path_control()
    n = raw['inventory']['primary_edges']
    assert raw['inventory']['equations'] == 1140
    return {'status': 'PASS: frozen UNKNOWN has no saved dual ray; recovery was not attempted on a recorded vector',
        'source_sha256': digest(Path(__file__)), 'shared_helper_sha256': SOURCE_SHA,
        'result_sha256': RESULT_SHA, 'cold_replay_sha256': COLD_SHA, 'shared_record_sha256': SHARED_SHA,
        'inventory': raw['inventory'], 'reported_numerical_status': raw['numerical_status'],
        'reported_optimizer_calls': 1, 'reported_optimizer_return_seconds': raw['optimizer_return_seconds'],
        'recorded_total_shared_seconds': raw['elapsed_seconds'], 'bound_source_control': path,
        'inferred_getDualRay_exists_value': False,
        'inference_scope': 'normal frozen code path plus absence of numerical_ray_hex; API return status was not stored',
        'saved_numerical_ray_available': False, 'saved_basis_available_in_this_record': False,
        'per_scale_integer_rhs_values': None,
        'per_scale_recovery_limitation': 'No equality multiplier vector was saved; no scale RHS can be reconstructed.',
        'true_feasibility_or_infeasibility_determined': False,
        'new_proposed_separation_problem': {
            'potential_variables': 1080, 'positive_capacity_variables': n,
            'total_variables': 1080+n, 'edge_inequality_rows': n,
            'maximum_constraint_nonzeros': 7*n,
            'bounds': '-1<=v[a,i]<=1;0<=t[a,b]<=6',
            'constraints': 't[a,b]>=sum(i in h[b])v[a,i]+sum(i in h[a])v[b,i]',
            'objective': 'maximize sum(a,i)q[a,i]*v[a,i]-sum(eligible edges)t[a,b]',
            'degree_redundancy': 'each neighbor triple has3 coordinates;sum_i q[a,i]=24 implies degree8',
            'certificate_rule': 'integer v with exact sum(v*q)-sum_edges max(0,edge_weight)>0',
            'need_not_extract_a_solver_dual_ray': True,
            'save_all_proposed_potential_coordinates_before_exact_reconstruction': True,
            'source_domain_and_control_review_required_before_query': True},
        'optimizer_or_solver_called': False, 'original_LP_repeated': False,
        'frozen_UNKNOWN_unchanged': True}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    report = calculate()
    args.output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)
