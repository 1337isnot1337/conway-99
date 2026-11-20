"""One bounded deletion pass on the checked case1 signed pattern.

No new master designs or graph constraints enter this pilot. Assumption
queries are discovery evidence only. The final subset needs a fresh
explicit-unit proof and the existing full-baseline certificate replay.
"""

import argparse
import gc
import json
from pathlib import Path
import resource
import time

from pysat.formula import CNF
from pysat.solvers import Solver

from complement_rook_incidence_master import (
    ROOT, bounded, certify_core, check_model, digest, full_assumptions,
    inspect_point, relative,
)


def deletion_order(units):
    assert units == sorted(set(units), key=abs)
    assert [literal for literal in units if literal < 0] == [-184]
    return [-184]+[literal for literal in units if literal > 0]


def controls():
    # Removing an irrelevant negative assumption must preserve UNSAT;
    # removing either positive assumption then gives an explicit SAT model.
    current = [1, 2, -184]
    transcript = []
    with Solver(name='glucose4', bootstrap_with=[[-1, -2]]) as oracle:
        for literal in deletion_order(current):
            trial = [other for other in current if other != literal]
            answer = bounded(oracle, 1, trial)
            assert answer is not None
            if answer:
                positive = {value for value in oracle.get_model() if value > 0}
                assert all((value > 0) == (abs(value) in positive) for value in trial)
            else:
                assert set(oracle.get_core()) <= set(trial)
                current = trial
            transcript.append({'removed_literal': literal,
                               'answer': 'SAT' if answer else 'UNSAT',
                               'retained_units': current[:]})
    assert current == [1, 2]
    assert [item['answer'] for item in transcript] == ['UNSAT', 'SAT', 'SAT']
    # UNKNOWN and SAT both retain the literal. Only an actual False result
    # authorizes a discovery deletion.
    assert [answer is False for answer in (False, True, None)] == [True, False, False]
    return {'status': 'signed deletion and UNKNOWN-retention controls PASS',
            'transcript': transcript, 'production_queries_seconds': 2,
            'production_search_seconds_including_bootstrap': 60}


def run(manifest_path, simplification_path, directory, output, checker, proof_index):
    control = controls()
    model, base, master, rows, gram, triples, signatures, variables = check_model(manifest_path)
    del master
    simplified = json.loads(simplification_path.read_text())
    assert simplified['status'] == 'all exact propagation and remaining tiny-master implications classified'
    assert simplified['source_sha256'] == digest(Path(__file__).with_name('complement_rook_incidence_core_simplification.py'))
    case = simplified['cases'][1]
    assert case['case'] == 1
    original_path = ROOT/case['original_certificate']
    assert digest(original_path) == case['original_certificate_sha256']
    original = json.loads(original_path.read_text())
    selected = original['selected_signatures']
    current = case['simplified_units'][:]
    assert current == [4, 6, 11, 12, 16, 32, 33, 44, 57, 62, 72, 74, 85, 87, 143, -184]
    assert set(current) <= set(full_assumptions(selected))
    order = deletion_order(current)
    assert proof_index >= 1000
    # The immutable helper uses this global /tmp prefix. Avoid overwriting
    # the eight original pilot caches or any earlier deletion attempt.
    prefix = Path(f'/tmp/conway-complement-rook-master-design-{proof_index}-core')
    assert not prefix.with_suffix('.cnf').exists()
    assert not prefix.with_suffix('.drat').exists()
    directory = directory.resolve()
    directory.mkdir(parents=True, exist_ok=True)
    assert not output.exists(), 'Preserve prior pilot outcomes; use a new output path.'
    result = {'status': 'bounded deletion discovery running',
              'source_sha256': digest(Path(__file__)), 'control': control,
              'manifest': relative(manifest_path), 'manifest_sha256': digest(manifest_path),
              'simplification_certificate': relative(simplification_path),
              'simplification_certificate_sha256': digest(simplification_path),
              'original_design_index': 1, 'original_certificate': relative(original_path),
              'original_certificate_sha256': digest(original_path),
              'original_selected_signatures': selected, 'starting_units': current[:],
              'deletion_order': order, 'queries': [], 'proof_index': proof_index,
              'base_variables': base['variables'], 'base_clauses': base['clauses'],
              'base_cnf_sha256': base['cnf_sha256'], 'base_domain_sha256': base['domain_sha256'],
              'seconds_per_query': 2, 'search_seconds_including_bootstrap': 60,
              'fresh_proof_seconds_including_bootstrap': 30, 'DRAT_seconds': 30,
              'new_master_designs': 0, 'new_graph_constraints': 0,
              'new_a_bound': False, 'Schur_clauses_added': 0,
              'partial_witnesses_are_graph_completions': False,
              'full_base_replay_pending': True, 'whole_core_exclusion_established': False}

    def save():
        result['current_discovery_units'] = current[:]
        result['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        output.write_text(json.dumps(result, indent=2)+'\n')

    save()
    started = time.monotonic()
    try:
        joint = CNF(from_file=str(ROOT/base['cnf_path']))
        assert (joint.nv, len(joint.clauses)) == (base['variables'], base['clauses'])
        with Solver(name='glucose4', bootstrap_with=joint.clauses) as oracle:
            del joint
            gc.collect()
            result['bootstrap_seconds'] = time.monotonic()-started
            print(json.dumps({'phase': 'proof-free baseline ready',
                              'seconds': result['bootstrap_seconds']}), flush=True)
            for literal in order:
                remaining = 60-(time.monotonic()-started)
                if remaining <= 0:
                    result['search_stop'] = '60-second budget reached; untested literals retained'
                    break
                assert literal in current
                before = current[:]
                trial = [other for other in current if other != literal]
                query_started = time.monotonic()
                answer = bounded(oracle, min(2, remaining), trial)
                item = {'removed_literal': literal, 'units_before': before,
                        'trial_units': trial, 'seconds': time.monotonic()-query_started,
                        'cumulative_oracle_statistics': oracle.accum_stats()}
                if answer is None:
                    item['status'] = 'UNKNOWN; literal retained'
                elif answer:
                    positive = {value for value in oracle.get_model() if value > 0}
                    assert all((value > 0) == (abs(value) in positive) for value in trial)
                    point, defects = inspect_point(positive, list(range(1, 253)), variables, rows, signatures)
                    assert all(len(set(signatures[cut['pair'][0]]) & set(signatures[cut['pair'][1]])) < 2
                               for cut in defects)
                    item['status'] = 'SAT of necessary model; literal retained'
                    item['partial_point'] = point
                    if point['defective_pairs'] == 0:
                        item['status'] = 'complete99-vertex candidate; independent validation required'
                        result['complete_graph_candidate'] = point
                else:
                    core = oracle.get_core()
                    assert core is not None and set(core) <= set(trial)
                    item['status'] = 'UNSAT discovery; literal deleted pending fresh proof'
                    item['reported_assumption_core'] = sorted(set(core), key=abs)
                    current = trial
                item['units_after'] = current[:]
                result['queries'].append(item)
                save()
                print(json.dumps({'removed_literal': literal, 'status': item['status'],
                                  'seconds': item['seconds'], 'current_size': len(current)}), flush=True)
                if 'complete_graph_candidate' in result:
                    result['search_stop'] = 'complete graph candidate; stopped for independent validation'
                    break
            else:
                result['search_stop'] = 'one deterministic pass completed'
            result['final_oracle_statistics'] = oracle.accum_stats()
        result['search_seconds'] = time.monotonic()-started
        result['final_discovery_units'] = current[:]
        result['positive_only_discovery'] = all(literal > 0 for literal in current)
        save()
        if 'complete_graph_candidate' in result:
            result['status'] = 'complete graph candidate requires independent validation'
            save()
            return result
        # Only this independent explicit-unit proof, followed by full replay,
        # can turn deletion discoveries into a published necessary pattern.
        print(json.dumps({'phase': 'fresh explicit-unit certification',
                          'units': current, 'proof_index': proof_index}), flush=True)
        certificate = certify_core(manifest_path, model, base, selected, current,
                                   proof_index, directory, checker)
        result['fresh_certificate'] = certificate
        if certificate['status'].startswith('UNKNOWN'):
            result['status'] = 'final subset remains discovery only; fresh proof UNKNOWN'
        else:
            assert certificate['status'] == 'explicit-core-unit proof DRAT verified; cut certified'
            result['status'] = 'final subset has fresh retained proof; independent full-baseline replay pending'
        save()
    except Exception as error:
        result['status'] = 'error; no unverified deletion promoted'
        result['error_type'] = type(error).__name__
        result['error_message'] = str(error)
        save()
        raise
    print(json.dumps({'status': result['status'], 'search_stop': result['search_stop'],
                      'queries': len(result['queries']), 'final_discovery_units': current,
                      'search_seconds': result['search_seconds']}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('controls')
    runner = sub.add_parser('run')
    for name in ('manifest', 'simplification', 'directory', 'output', 'drat-trim'):
        runner.add_argument('--'+name, type=Path, required=True)
    runner.add_argument('--proof-index', type=int, default=1001)
    args = parser.parse_args()
    if args.command == 'controls':
        print(json.dumps(controls(), indent=2))
    else:
        run(args.manifest, args.simplification, args.directory, args.output,
            args.drat_trim, args.proof_index)
