"""Read-only process/proof binding gate; no backend or proof checker call."""

import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT/'experiments/workspace'
LOGS = ROOT/'experiments/logs/grids-and-triangles'
SOURCE = WORK/'complement_rook_35core_case0004_coordinate_cover_cadical.py'
PREPARATION = LOGS/'complement-rook-35core-case0004-coordinate-cover-cadical-preparation.json'
SOURCE_SHA = '1921f71964795d819e0369c9679dc1526df97c29bb1920a932c7ca449ba3de25'
PREPARATION_SHA = 'e7a4185a300a48edbe01d7103da8e765dab1ad9653e2678992d3f1c4e986d731'
CNF_SHA = '5a805a4e302bf2a91aa3cb4d39aeaddb4759b7f9695633de18cfb0fa6d5883a2'


def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        while block := stream.read(1 << 20):
            result.update(block)
    return result.hexdigest()


def read(path):
    return json.loads(path.read_text())


def tiny_clauses(path, expected):
    lines = path.read_text().splitlines()
    assert lines[0] == f'p cnf 3 {expected}'
    clauses = []
    for line in lines[1:]:
        values = list(map(int, line.split()))
        assert values[-1] == 0 and all(1 <= abs(v) <= 3 for v in values[:-1])
        clauses.append(values[:-1])
    assert len(clauses) == expected
    return clauses


def satisfying(clauses):
    return [state for state in range(8)
            if all(any(bool(state >> (abs(v)-1)&1) == (v > 0) for v in clause) for clause in clauses)]


def review():
    started = time.monotonic()
    assert digest(SOURCE) == SOURCE_SHA and digest(PREPARATION) == PREPARATION_SHA
    prep = read(PREPARATION)
    assert prep['complete'] and prep['backend'] == 'cadical300'
    assert prep['production_solver_calls'] == 0 and prep['assumptions'] == []
    assert prep['CNF_changes'] == prep['symmetry_constraints_added'] == 0
    for name, expected in prep['source_hashes'].items():
        assert digest(WORK/name) == expected
    assert digest(ROOT/prep['previous_preparation']) == prep['previous_preparation_sha256']
    model_path = LOGS/'complement-rook-35core-case0004-coordinate-cover-overlay-model.json'
    assert digest(model_path) == prep['overlay_model_sha256']
    model = read(model_path)
    assert prep['formula'] == model['formula'] and prep['cnf_sha256'] == model['cnf_sha256'] == CNF_SHA
    assert (prep['formula']['variables'], prep['formula']['clauses']) == (134852, 439604)
    assert digest(Path(model['cnf'])) == CNF_SHA
    accepted = [item for item in prep['backend_attempts'] if item['passed']]
    assert len(accepted) == 1 and accepted[0]['backend'] == prep['backend']
    accepted = accepted[0]
    for key, hash_key in [('child_result', 'child_result_sha256'), ('proof', 'proof_sha256'),
                          ('direct_DRAT_log', 'direct_DRAT_log_sha256')]:
        assert digest(ROOT/accepted[key]) == accepted[hash_key]
    child_path = ROOT/accepted['child_result']
    child = read(child_path)
    assert child['runtime'] == accepted['runtime'] == prep['runtime']
    assert child['source_hashes'] == prep['source_hashes'] and child['solver_calls'] == 2
    assert child['sat']['answer'] is True and child['unsat']['answer'] is False
    for item in (prep['runtime']['python_wrapper'], prep['runtime']['native_extension']):
        assert digest(Path(item['path'])) == item['sha256']
    sat_path, unsat_path = child_path.parent/'sat.cnf', child_path.parent/'unsat.cnf'
    sat, unsat = tiny_clauses(sat_path, 7), tiny_clauses(unsat_path, 8)
    assert sat == unsat[:-1] and satisfying(sat) == [7] and satisfying(unsat) == []
    assert digest(sat_path) == child['sat']['CNF_sha256']
    assert digest(unsat_path) == child['unsat']['CNF_sha256']
    positive = {v for v in child['sat']['model'] if v > 0}
    assert all(any((v in positive) if v > 0 else (-v not in positive) for v in clause) for clause in sat)
    assert 's VERIFIED' in (ROOT/accepted['direct_DRAT_log']).read_text()
    assert (ROOT/accepted['proof']).read_text().splitlines()[-1] == '0'
    process = accepted['process']
    assert process['returncode'] == 0 and not process['timed_out'] and process['child_reaped']
    assert digest(ROOT/process['log']) == process['log_sha256']
    watch = prep['watchdog_control']
    timeout_path = ROOT/prep['control_directory']/'watchdog/timeout.json'
    assert digest(timeout_path) == watch['persisted_UNKNOWN_sha256']
    timeout = read(timeout_path)
    assert timeout['status'].startswith('UNKNOWN:') and timeout['no_partial_child_result_used']
    assert watch['process']['timed_out'] and watch['process']['child_reaped']
    assert watch['process']['UNKNOWN_persisted_before_kill'] and watch['process']['SIGKILL_sent_at_deadline']
    assert watch['process']['returncode'] == -9
    result = {'status': 'PASS: independent CaDiCaL process/proof source and artifact-binding review',
        'review_source_sha256': digest(Path(__file__)), 'subject_source_sha256': SOURCE_SHA,
        'preparation_sha256': PREPARATION_SHA, 'unchanged_existing_CNF_sha256_checked': CNF_SHA,
        'variables': 134852, 'clauses': 439604,
        'tiny_truth_tables_independently_checked': 2,
        'tiny_SAT_model_directly_checked': True,
        'saved_direct_DRAT_log_and_proof_hashes_checked': True,
        'saved_watchdog_status_kill_reap_binding_checked': True,
        'maximum_prepared_child_wall_seconds': prep['limits']['production_child_wall_seconds_including_imports_bootstrap_solve'],
        'source_review': [
            'The parent owns the sole production child and subtracts launch time from its wait deadline.',
            'The deadline includes child imports, runtime/hash checks, complete clause loading, solving, and child proof serialization.',
            'Timeout persistence precedes SIGKILL, and both timeout and exception paths attempt kill/reap before returning.',
            'A timed-out child result or partial proof is explicitly unaccepted, even if its output file exists.',
            'The child streams exactly the unchanged 439604 clauses under a bound full-CNF hash and uses no assumptions.',
            'SAT triggers the existing exact incidence, weighted-cut and complete coordinate-cover inspector; it does not claim a graph.',
            'UNSAT remains pending until direct DRAT succeeds; retained inputs must occur in the exact full formula.',
            'A separate cold replay rebuilds the complete formula and checks retained-input inclusion and DRAT again.',
            'Only indexed case 4 can be excluded; no other local type or whole Conway problem is declared excluded.',
            'Tiny-backend fallback is preparation-only; the production path has no retry or alternate-backend loop.'],
        'subject_modules_imported': False, 'CNF_regenerated': False,
        'watchdog_control_rerun': False, 'backend_called': False, 'DRAT_checker_called': False,
        'production_query_called': False, 'whole_local_set_excluded': False,
        'seconds': time.monotonic()-started}
    output = LOGS/'complement-rook-35core-case0004-coordinate-cover-cadical-independent-review.json'
    assert not output.exists()
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2)); print('output_sha256', digest(output))


if __name__ == '__main__':
    review()
