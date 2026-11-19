"""One bounded count-only C++ run for the universal empty-root packing domain."""

import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import time


ROOT = Path(__file__).resolve().parents[2]
WORK = ROOT/'experiments/workspace'
LOGS = ROOT/'experiments/logs/moments-and-counts'
CPP = WORK/'grid_free_order10_high_mask_packing_count.cpp'
SCOPE = LOGS/'order10-high-mask-packing-scope.json'
SCOPE_SHA = 'fd7544082a7186191abe92136a58ba7e69918bf455edec7f37a3ed4f933843a3'
SCOPE_SOURCE_SHA = '3de5de8e41e451a2073805eb8ad26cf38a8b67dcc6be8f1484125d7cee0e263c'
BINARY = Path('/tmp/conway99-high-mask-packing-count')


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.write_text(json.dumps(value, indent=2)+'\n')


def run(output):
    assert not output.exists()
    assert digest(SCOPE) == SCOPE_SHA
    assert digest(WORK/'grid_free_order10_high_mask_packing_scope.py') == SCOPE_SOURCE_SHA
    scope = json.loads(SCOPE.read_text())
    assert scope['source_sha256'] == SCOPE_SOURCE_SHA and scope['root_count'] == 62
    domain = scope['roots'][0]
    assert domain['root_type'] == 38 and domain['root_rows'] == [0]*6
    assert domain['pair_quotas'] == [2]*15 and len(domain['high_masks']) == 42
    assert domain['total_weight_only_subset_upper_bound'] == 15159780
    result = {'status': 'compiling one bounded empty-root packing counter',
        'source_sha256': digest(Path(__file__)), 'cpp_source_sha256': digest(CPP),
        'scope_certificate_sha256': SCOPE_SHA, 'scope_source_sha256': SCOPE_SOURCE_SHA,
        'full_six_root_domain_sha256': scope['domain_sha256'],
        'requested_count_wall_seconds': 10, 'external_watchdog_seconds': 12,
        'root_type': 38, 'high_masks': domain['high_masks'], 'pair_masks': domain['pair_masks'],
        'pair_quotas': domain['pair_quotas'], 'weighted_subset_upper_bound': 15159780,
        'packing_queries': 0, 'automatic_retries': 0,
        'atom_list_stored': False, 'count_point_loaded': False, 'product_tensors_loaded': False,
        'optimizer_or_new_tensor_called': False, 'outside_adjacency_imposed': False,
        'symmetry_quotient_used': False, 'graph_existence_resolved': False}
    progress = output.with_suffix('.progress.json')
    assert not progress.exists()
    save(progress, result)
    started = time.monotonic()
    flags = ['-std=c++17', '-O3', '-Wall', '-Wextra', '-Werror']
    command = ['g++', *flags, str(CPP), '-o', str(BINARY)]
    compiled = subprocess.run(command, cwd=ROOT, capture_output=True, text=True, timeout=30, check=False)
    compiler_log = output.with_suffix('.compile.log')
    compiler_log.write_text(compiled.stdout+compiled.stderr)
    if compiled.returncode:
        result.update(status='ERROR: compiler failure before any packing query',
                      compile_returncode=compiled.returncode,
                      compiler_log_sha256=digest(compiler_log), complete=False)
        save(output, result)
        print(json.dumps(result, indent=2))
        return 1
    version = subprocess.run(['g++', '--version'], capture_output=True, text=True, timeout=5, check=True).stdout
    result.update(compiler_flags=flags, compiler_version=version,
                  compiler_log_sha256=digest(compiler_log), binary_sha256=digest(BINARY),
                  status='running the single bounded count-only packing query', packing_queries=1)
    save(progress, result)
    query_started = time.monotonic()
    raw_path = output.with_suffix('.raw.json')
    error_path = output.with_suffix('.stderr.log')
    try:
        query = subprocess.run([str(BINARY), '10'], cwd=ROOT, capture_output=True,
                               text=True, timeout=12, check=False)
        raw_path.write_text(query.stdout)
        error_path.write_text(query.stderr)
        assert query.returncode == 0, f'counter exit {query.returncode}'
        observed = json.loads(query.stdout)
        assert observed['high_masks'] == domain['high_masks']
        assert observed['pair_masks'] == domain['pair_masks'] and observed['pair_quotas'] == [2]*15
        assert observed['empty_packing_included'] and not observed['atom_list_stored']
        assert not observed['outside_adjacency_imposed'] and not observed['symmetry_quotient_used']
        assert observed['requested_seconds'] == 10 and observed['complete'] == (not observed['timed_out'])
        assert len(observed['population_size_counts']) == 11
        assert observed['population_size_counts'][0] == 1
        assert sum(observed['population_size_counts']) == observed['packings_visited']
        assert sum(observed['pair_consumption_counts']) == observed['packings_visited']
        assert observed['packings_visited'] <= 15159780
        assert observed['candidate_tests'] <= 42*observed['packings_visited']
        tiny = next(c for c in scope['tiny_controls'] if c['label'] == 'empty_first12')
        assert observed['tiny_control_subsets'] == tiny['full_subset_assignments_checked'] == 4096
        assert {str(i): value for i, value in enumerate(observed['tiny_control_population_counts']) if value} == tiny['packing_counts_by_size']
        if observed['complete']:
            assert observed['packings_visited'] == 1+observed['candidate_tests']-observed['rejected_candidates']
        result.update(status='COMPLETE: exact empty-root pair-capacity packing count' if observed['complete']
                      else 'INCOMPLETE: valid packing-count lower bound at the fixed deadline',
                      complete=observed['complete'], result=observed,
                      raw_counter_output_sha256=digest(raw_path), stderr_sha256=digest(error_path))
    except subprocess.TimeoutExpired as problem:
        stdout, stderr = problem.stdout or b'', problem.stderr or b''
        raw_path.write_bytes(stdout.encode() if isinstance(stdout, str) else stdout)
        error_path.write_bytes(stderr.encode() if isinstance(stderr, str) else stderr)
        result.update(status='UNKNOWN: external watchdog terminated the sole counter process',
                      complete=False, external_watchdog_triggered=True,
                      raw_counter_output_sha256=digest(raw_path), stderr_sha256=digest(error_path),
                      partial_counter_output_not_accepted=True)
    except Exception as problem:
        result.update(status='ERROR: count result failed exact bindings or controls',
                      complete=False, error=repr(problem))
    result.update(query_wall_seconds=time.monotonic()-query_started,
                  total_seconds=time.monotonic()-started)
    save(output, result)
    print(json.dumps(result, indent=2)); print('output_sha256', digest(output))
    return int(result['status'].startswith('ERROR:'))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(run(args.output))
