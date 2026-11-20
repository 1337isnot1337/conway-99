"""One bounded query of the frozen streamed case4 coordinate-cover formula.

The full CNF is read one clause at a time. SAT is checked as a partial
incidence, against all original uncapped cuts and every coordinate cover.
UNSAT needs a direct DRAT check, then a separate cold formula rebuild,
retained-input inclusion check and DRAT replay. No automatic retry exists.
"""

import argparse
import gc
import gzip
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import tempfile
from threading import Timer
import time

from pysat.solvers import Solver

import complement_rook_35core_case0004_coordinate_cover_overlay as overlay


ROOT, LOGS = overlay.ROOT, overlay.LOGS
MODEL = LOGS / 'complement-rook-35core-case0004-coordinate-cover-overlay-model.json'
MODEL_SHA = '727874f9f98f5e1fab2b85478dbf2ab347333329fceab938b0a2806ae1a86a4b'
COLD = LOGS / 'complement-rook-35core-case0004-coordinate-cover-overlay-replay.json'
COLD_SHA = 'f9c9a3b0ead3b4e8d856b78790d7630fe89c355efebbd4e2c83329e2c284c9ec'
OVERLAY_SOURCE_SHA = '5597089c00a15f72927f31c8b05f5a6bed1198a0d7ebc16aacaeb6cd39cb1c4a'
CNF_SHA = '5a805a4e302bf2a91aa3cb4d39aeaddb4759b7f9695633de18cfb0fa6d5883a2'
LIMITS = {'solver_seconds_including_streamed_bootstrap': 60,
          'direct_DRAT_seconds': 60, 'cold_DRAT_seconds': 60,
          'query_count': 1, 'automatic_retries': 0}
digest, portable = overlay.digest, overlay.portable
save, normalized = overlay.base_builder.save, overlay.base_builder.normalized
original = overlay.base_builder.original


def source_hashes():
    answer = overlay.source_hashes()
    answer[Path(__file__).name] = digest(Path(__file__))
    return dict(sorted(answer.items()))


def checked_model(require_cnf=False):
    assert digest(Path(overlay.__file__)) == OVERLAY_SOURCE_SHA
    assert digest(MODEL) == MODEL_SHA and digest(COLD) == COLD_SHA
    model = json.loads(MODEL.read_text())
    cold = json.loads(COLD.read_text())
    assert model['complete'] and model['source_hashes'] == overlay.source_hashes()
    assert model['case']['index'] == 4 and model['solver_queries'] == 0
    assert model['base_model_sha256'] == overlay.BASE_SHA
    assert model['cover_certificate_sha256'] == overlay.COVERS_SHA
    assert model['formula']['variables'] == 134852 and model['formula']['clauses'] == 439604
    assert model['formula']['added_primary_cover_clauses'] == 178533
    assert model['formula']['new_auxiliary_variables'] == 0
    assert model['cnf_sha256'] == CNF_SHA
    assert cold['model_sha256'] == MODEL_SHA and cold['full_CNF_sha256'] == CNF_SHA
    assert cold['formula'] == model['formula'] and cold['source_hashes'] == overlay.source_hashes()
    assert cold['status'].startswith('PASS: cold')
    if require_cnf:
        path = Path(model['cnf'])
        assert digest(path) == CNF_SHA and path.stat().st_size == model['formula']['CNF_bytes']
    return model


def read_full_clauses(path, variables, clauses):
    """Strict one-line DIMACS parser, matching the frozen streamed writer."""
    with path.open('rb') as stream:
        assert stream.readline() == f'p cnf {variables} {clauses}\n'.encode()
        count = largest = 0
        for line in stream:
            assert count < clauses
            values = list(map(int, line.split()))
            assert values and values[-1] == 0 and all(values[:-1])
            clause = values[:-1]
            assert all(abs(value) <= variables for value in clause)
            largest = max(largest, max(map(abs, clause), default=0))
            count += 1
            yield clause
        assert count == clauses and largest == variables


def clause_key(clause):
    # Exact normalized bytes keep retained-input memory proportional to
    # its text size, not to a Python integer per occurrence.
    return ' '.join(map(str, sorted(clause))).encode()


def retained_inclusion(full_path, retained_path, formula):
    needed = set()
    input_count = 0
    for clause in original.read_clauses(retained_path):
        needed.add(clause_key(clause))
        input_count += 1
    found = set()
    groups = [set() for _ in range(4)]
    boundaries = [218863, 218893, 261071]
    for index, clause in enumerate(read_full_clauses(full_path, formula['variables'], formula['clauses'])):
        key = clause_key(clause)
        if key in needed:
            group = sum(index >= boundary for boundary in boundaries)
            groups[group].add(key)
            found.add(key)
    assert found == needed
    previous = set()
    attribution = {}
    for name, present in zip(('original_incidence', 'Gram_pair_conflicts', 'weighted_row_cut_encoding',
                              'coordinate_covers'), groups):
        attribution[name] = len(present - previous)
        previous.update(present)
    assert previous == needed
    return {'all_retained_inputs_in_full_formula': True, 'retained_input_clause_lines': input_count,
            'retained_distinct_input_clauses': len(needed),
            'first_available_input_family_counts': attribution,
            'original_incidence_only_binding': needed <= groups[0],
            'old60_cut_formula_only_binding': needed <= groups[0] | groups[1] | groups[2]}


def controls():
    parse_checks = invalid_checks = cover_checks = 0
    with tempfile.TemporaryDirectory(prefix='conway-cover-query-controls-') as directory:
        path = Path(directory) / 'tiny.cnf'
        clauses = [[1, -2], [], [2, 2, -3], [4], [-1, -4]]
        raw = b'p cnf 4 5\n' + b''.join((' '.join(map(str, clause))+' 0\n').encode()
                                        for clause in clauses)
        path.write_bytes(raw)
        assert list(read_full_clauses(path, 4, 5)) == clauses
        parse_checks += len(clauses)
        invalid = [raw.replace(b'p cnf 4 5\n', b'p cnf 4 4\n', 1),
                   raw.replace(b'1 -2 0\n', b'1 -2\n', 1),
                   raw.replace(b'1 -2 0\n', b'1 0 -2 0\n', 1),
                   raw.replace(b'1 -2 0\n', b'5 -2 0\n', 1),
                   raw + b'1 0\n', raw.rsplit(b'-1 -4 0\n', 1)[0]]
        for bad in invalid:
            path.write_bytes(bad)
            try:
                list(read_full_clauses(path, 4, 5))
            except AssertionError:
                invalid_checks += 1
            else:
                raise AssertionError('invalid streamed formula accepted')
        path.write_bytes(raw)
    assert clause_key([3, -1, 2]) == clause_key([2, 3, -1])
    assert clause_key([1, 1]) != clause_key([1])
    for cover in range(8):
        for assignment in range(16):
            present = assignment & 1
            supply = (cover & (assignment >> 1)).bit_count()
            for demand in (1, 2, 3):
                if demand*present <= supply:
                    assert not present or supply >= 1
                cover_checks += 1
    return {'streamed_exact_clause_controls': parse_checks, 'rejected_invalid_streams': invalid_checks,
            'coordinate_demand_weakening_assignments': cover_checks,
            'clause_key_preserves_literal_multiplicity': True, 'solver_or_optimizer_called': False}


def prepare(output):
    assert not output.exists()
    started = time.monotonic()
    model = checked_model(True)
    counts = {'clauses': 0, 'literal_occurrences': 0, 'largest_clause': 0}
    for clause in read_full_clauses(Path(model['cnf']), 134852, 439604):
        counts['clauses'] += 1
        counts['literal_occurrences'] += len(clause)
        counts['largest_clause'] = max(counts['largest_clause'], len(clause))
    assert counts['literal_occurrences'] == model['formula']['total_literal_occurrences']
    record = {'status': 'one streamed 60-second query/proof wrapper prepared; no query',
              'complete': True, 'source_hashes': source_hashes(), 'limits': LIMITS,
              'overlay_model': portable(MODEL), 'overlay_model_sha256': MODEL_SHA,
              'cold_full_model_replay': portable(COLD), 'cold_full_model_replay_sha256': COLD_SHA,
              'cnf': model['cnf'], 'cnf_sha256': CNF_SHA, 'formula': model['formula'],
              'streamed_parser_inventory': counts, 'controls': controls(),
              'full_clause_list_materialized': False, 'all2521_cores_covered': False,
              'case_index': 4, 'solver_queries': 0,
              'SAT_scope': 'Only a partial64-column incidence; original Gram/multiplicity/triples,30 conflicts,60 uncapped weighted cuts,and all coordinate covers must pass.',
              'UNSAT_scope': 'Only indexed35-core case4, after direct and separate cold retained-input/DRAT checks.',
              'preparation_seconds': time.monotonic()-started,
              'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output, record)
    print(json.dumps(record, indent=2), flush=True)


def checked_preparation(path, require_cnf=False):
    record = json.loads(path.read_text())
    assert record['complete'] and record['source_hashes'] == source_hashes() and record['limits'] == LIMITS
    assert record['overlay_model_sha256'] == MODEL_SHA and record['cold_full_model_replay_sha256'] == COLD_SHA
    assert record['cnf_sha256'] == CNF_SHA and record['case_index'] == 4 and record['solver_queries'] == 0
    model = checked_model(require_cnf)
    assert record['formula'] == model['formula']
    return record, model


def inspect_selected(selected):
    data = original.load(4)
    incidence = original.inspect(selected, data)
    _, inventory, row_model, cuts, _ = overlay.base_builder.inputs()
    assert data[-1] == row_model['column_masks35']
    weighted = overlay.base_builder.inspect_overlay(selected, inventory, cuts)
    assert digest(overlay.COVERS) == overlay.COVERS_SHA
    certificate = json.loads(gzip.decompress(overlay.COVERS.read_bytes()))
    chosen_bits = sum(1 << a for a in selected)
    unique_checked = origins_checked = retained_checked = 0
    for record in certificate['records']:
        absent = not(chosen_bits >> record['target_column'] & 1)
        for item in record['unique_covers']:
            assert absent or bool(chosen_bits & int(item['cover_bits_hex'], 16))
            unique_checked += 1
        for i, j, demand, index, weakened in record['all_positive_difference_pairs']:
            assert demand > 0 and weakened == (demand > 1)
            assert absent or bool(chosen_bits & int(record['unique_covers'][index]['cover_bits_hex'], 16))
            origins_checked += 1
        retained_checked += len(record['retained_unique_cover_ids'])
    assert (unique_checked, origins_checked, retained_checked) == (239299, 476766, 178533)
    assert all(not(chosen_bits >> a & 1) for a in certificate['unit_target_columns'])
    return {'incidence': incidence, 'uncapped_30_conflict_60_row_cut_check': weighted,
            'all_coordinate_cover_checks': {'unique_same_target_covers': unique_checked,
                'all_positive_coordinate_origins': origins_checked, 'retained_clauses': retained_checked,
                'unit_targets_checked': certificate['unit_target_columns'],
                'demands_above_one_checked_only_after_the_recorded_weakening': True},
            'complete_graph': False, 'remaining64_vertex_adjacency_unspecified': True}


def solve(preparation, directory, seconds, checker, checker_seconds):
    assert 0 < seconds <= LIMITS['solver_seconds_including_streamed_bootstrap']
    assert 0 < checker_seconds <= LIMITS['direct_DRAT_seconds'] and not directory.exists()
    prep, model = checked_preparation(preparation, True)
    directory.mkdir(parents=True)
    result_path = directory / 'result.json'
    result = {'status': 'running one frozen case4 coordinate-cover query',
              'source_hashes': source_hashes(), 'preparation': portable(preparation),
              'preparation_sha256': digest(preparation), 'model_sha256': MODEL_SHA,
              'cnf_sha256': CNF_SHA, 'case_index': 4, 'assumptions': [],
              'requested_seconds_including_streamed_bootstrap': seconds,
              'requested_direct_checker_seconds': checker_seconds,
              'solver_call_count': 0, 'automatic_retries': 0,
              'whole_local_set_excluded': False, 'full_graph_completion_found': False}

    def checkpoint():
        result['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(result_path, result)

    checkpoint()
    started = time.monotonic()
    try:
        with Solver(name='glucose4', with_proof=True) as solver:
            count = 0
            stream = read_full_clauses(Path(model['cnf']), 134852, 439604)
            try:
                for clause in stream:
                    if count % 1024 == 0 and time.monotonic()-started >= seconds:
                        break
                    solver.add_clause(clause)
                    count += 1
                else:
                    assert count == 439604
            finally:
                stream.close()
            result['bootstrap_clauses_added'] = count
            result['bootstrap_seconds'] = time.monotonic()-started
            result['bootstrap_complete'] = count == 439604
            answer = None
            if count == 439604 and time.monotonic()-started < seconds:
                timer = Timer(max(0.001, seconds-(time.monotonic()-started)), solver.interrupt)
                result['solver_call_count'] = 1
                timer.start()
                try:
                    answer = solver.solve_limited(expect_interrupt=True)
                finally:
                    timer.cancel()
            result['solve_return_seconds'] = time.monotonic()-started
            result['solver_statistics'] = solver.accum_stats()
            if answer is None:
                result['status'] = 'UNKNOWN; indexed35-core case4 remains unresolved'
                result['timeout_phase'] = 'solve' if result['solver_call_count'] else 'streamed_bootstrap'
            elif answer:
                positive = {value for value in solver.get_model() if value > 0}
                selected = [a for a in range(1214) if a+1 in positive]
                result['partial_witness'] = inspect_selected(selected)
                result['status'] = 'SAT; exact partial incidence and all original/coordinate cuts checked'
            else:
                proof = solver.get_proof()
                assert proof is not None
                result['terminal_empty_clause_appended'] = not proof or proof[-1] != '0'
                if result['terminal_empty_clause_appended']:
                    proof.append('0')
                raw = directory / 'raw.drat'
                raw.write_text('\n'.join(proof)+'\n')
                result.update(status='solver UNSAT; direct DRAT pending', raw_proof=portable(raw),
                              raw_proof_sha256=digest(raw), raw_proof_lines=len(proof))
        gc.collect()
        checkpoint()
        if result['status'].startswith('solver UNSAT;'):
            retained, proof, log = directory/'retained.cnf', directory/'retained.drat', directory/'direct-drat.log'
            checked = subprocess.run([str(checker), model['cnf'], str(ROOT/result['raw_proof']),
                                      '-t', str(checker_seconds), '-w', '-c', str(retained), '-l', str(proof)],
                                     capture_output=True, text=True, timeout=checker_seconds+5, check=False)
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            inclusion = retained_inclusion(Path(model['cnf']), retained, model['formula'])
            result['retained_certificate'] = {'cnf': portable(retained), 'cnf_sha256': digest(retained),
                'proof': portable(proof), 'proof_sha256': digest(proof),
                'checker_executable_sha256': digest(checker), 'checker_log': portable(log),
                'checker_log_sha256': digest(log), 'input_inclusion': inclusion}
            result['status'] = 'UNSAT with direct DRAT; cold complete-model/input/proof replay still required'
        result['elapsed_seconds'] = time.monotonic()-started
        checkpoint()
    except Exception as error:
        result.update(status='error; no unchecked exclusion promoted', error_type=type(error).__name__,
                      error_message=str(error), elapsed_seconds=time.monotonic()-started)
        checkpoint()
        raise
    print(json.dumps({key: value for key, value in result.items() if key != 'partial_witness'}, indent=2), flush=True)


def replay(preparation, result_path, output, checker, checker_seconds):
    assert not output.exists() and 0 < checker_seconds <= LIMITS['cold_DRAT_seconds']
    prep, model = checked_preparation(preparation)
    result = json.loads(result_path.read_text())
    assert result['source_hashes'] == source_hashes() and result['preparation_sha256'] == digest(preparation)
    assert result['model_sha256'] == MODEL_SHA and result['cnf_sha256'] == CNF_SHA
    assert result['case_index'] == 4 and result['assumptions'] == []
    started = time.monotonic()
    report = {'status': 'cold full formula replay pending', 'source_hashes': source_hashes(),
              'preparation_sha256': digest(preparation), 'model_sha256': MODEL_SHA,
              'result_sha256': digest(result_path), 'cnf_sha256': CNF_SHA,
              'case_index': 4, 'whole_local_set_excluded': False,
              'complete_graph': False, 'solver_query_called': False}
    with tempfile.TemporaryDirectory(prefix='conway-case4-cover-query-cold-') as directory:
        full_path = Path(directory) / 'full.cnf'
        base, ledger, formula = overlay.build(full_path)
        assert normalized(formula) == model['formula'] and normalized(ledger) == model['cover_ledger_check']
        assert digest(full_path) == CNF_SHA
        report['cold_complete_formula_rebuilt'] = True
        if result['status'].startswith('SAT;'):
            selected = result['partial_witness']['incidence']['selected_columns']
            actual = inspect_selected(selected)
            assert normalized(actual) == result['partial_witness']
            report.update(status='PASS: cold full model and exact partial incidence/cut replay',
                          all_original_incidence_and_uncapped_cuts_checked=True,
                          all_coordinate_covers_checked=True)
        elif result['status'].startswith('UNSAT with direct DRAT;'):
            item = result['retained_certificate']
            retained, proof = ROOT/item['cnf'], ROOT/item['proof']
            assert digest(retained) == item['cnf_sha256'] and digest(proof) == item['proof_sha256']
            inclusion = retained_inclusion(full_path, retained, formula)
            assert normalized(inclusion) == item['input_inclusion']
            checked = subprocess.run([str(checker), str(retained), str(proof), '-t', str(checker_seconds), '-w'],
                                     capture_output=True, text=True, timeout=checker_seconds+5, check=False)
            log = output.with_suffix('.drat.log')
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            report.update(status='PASS: cold full model, exact retained-input inclusion and DRAT replay',
                          excluded_indexed_core=4, input_inclusion=inclusion,
                          checker_log=portable(log), checker_log_sha256=digest(log),
                          checker_executable_sha256=digest(checker))
        else:
            assert result['status'].startswith('UNKNOWN;')
            report['status'] = 'PASS: cold full model and UNKNOWN binding; no exclusion'
    report.update(elapsed_seconds=time.monotonic()-started,
                  peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--output', type=Path, required=True)
    run = commands.add_parser('solve')
    run.add_argument('--preparation', type=Path, required=True)
    run.add_argument('--directory', type=Path, required=True)
    run.add_argument('--seconds', type=float, default=60)
    run.add_argument('--checker-seconds', type=int, default=60)
    run.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    check = commands.add_parser('replay')
    check.add_argument('--preparation', type=Path, required=True)
    check.add_argument('--result', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    check.add_argument('--checker-seconds', type=int, default=60)
    check.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output.resolve())
    elif args.command == 'solve':
        solve(args.preparation.resolve(), args.directory.resolve(), args.seconds,
              args.drat_trim.resolve(), args.checker_seconds)
    else:
        replay(args.preparation.resolve(), args.result.resolve(), args.output.resolve(),
               args.drat_trim.resolve(), args.checker_seconds)
