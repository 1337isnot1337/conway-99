"""Prepare one bounded-only separator for the latest frozen terminal point.

This driver never calls the original feasibility query. It binds the
complete terminal registry and uses the existing generic bounded model,
query and exact replay. Numerical statuses establish no conclusion.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

import root_prism_free_f0_bounded_lazy_continuation as parent
import root_prism_free_f0_bounded_lazy_transcript_bundle as bundle
import root_prism_free_f0_shared_bounded_fallback as shared


ROOT, LOGS = parent.ROOT, parent.LOGS
digest, canonical, portable, save, read = parent.digest, parent.canonical, parent.portable, parent.save, parent.load_json
SOURCES = {
    'root_prism_free_f0_bounded_lazy_continuation.py': '361484188521fc5c741be4aa8a7e1a10a9b4e76116ae51d8d9e76b272bc78dd2',
    'root_prism_free_f0_bounded_lazy_transcript_bundle.py': '65153e9dc7ba86c43d451a26abb8129b8deb9b1abdc5e8fc556ed6502f5a5fec',
    'root_prism_free_f0_shared_bounded_fallback.py': '46ff20ca4269b71b80c2fd7e3ba2fec4f369b7dca3d4e08272a935cdfde72f1a'}
RESULT = LOGS/'f0-bounded-lazy-continuation-run01/result.json'
RESULT_SHA = '88c4858aa36aaf3af15f4b53ce41be5c1fee3d8f2c237a49e2df026f1228bd86'
COLD = LOGS/'f0-bounded-lazy-continuation-run01-cold-replay.json'
COLD_SHA = '95996661c85ce21aa4ac6af219a1e773d170b664170380ef7012deb78676ae98'
MANIFEST = LOGS/'f0-bounded-lazy-continuation-run01-terminal-manifest.json'
MANIFEST_SHA = 'fcdba71c12c9520d8d35fd3f519ec9478595006cd95dba5f3cb94dbc7f2d600a'
MAXIMUM_SECONDS = 60


def check_inputs():
    for name, expected in SOURCES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    shared.check_sources()
    assert bundle.verify(True)['record_count'] == 253
    for path, expected in ((RESULT, RESULT_SHA), (COLD, COLD_SHA), (MANIFEST, MANIFEST_SHA)):
        assert digest(path) == expected
    for entry in read(MANIFEST)['files']:
        assert digest(ROOT/entry['path']) == entry['sha256']


def bound(record, key):
    path = ROOT/record[key]
    assert digest(path) == record[key+'_sha256']
    return read(path)


def calculate():
    check_inputs()
    result = read(RESULT); last = result['iterations'][-1]
    assert result['status'] == 'UNKNOWN: no exact shared certificate before shared budget; unresolved'
    assert last['iteration'] == 80
    candidate = bound(last, 'candidate'); selected = candidate['selected_signature_ids']
    domain, records = parent.BASE.load(0)
    old_cuts, old_clauses, _ = parent.individual.old.load_cuts()
    triples, targets, neighbors, _, actions, _ = parent.individual.box.load()
    assert parent.individual.old.inspect(selected, domain, records, old_cuts, old_clauses) == candidate['original_incidence_and_twelve_direct_cuts']
    rows_registry = bound(result, 'individual-registry')
    signed_registry = bound(result, 'symmetric-registry')
    explanations = bound(result, 'explanation-registry')
    assert (len(rows_registry), len(signed_registry), len(explanations)) == (2640, 276, 5340)
    chosen = set(selected)
    assert all(sum(weight for b, weight in cut['weights'] if b in chosen)
               >= cut['demand']*int(cut['target'] in chosen) for cut in rows_registry)
    assert all(sum(c for a, c in cut['signed_coefficients'] if a in chosen) <= 0 for cut in signed_registry)
    assert all(not parent.lazy.is_false(record['clause'], chosen) for record in explanations)
    assert candidate['registry_evaluation']['all_registered_inequalities_hold']
    boxes = bound(last, 'individual_rows')
    parent.individual.check_rows(boxes, selected, triples, targets, neighbors, actions)
    assert boxes['all60_processed'] and boxes['exact_rational_boxes'] == 60 and not boxes['exact_integer_obstructions']
    raw = bound(last, 'shared_rows')
    shared.replay(raw, selected, triples, targets, neighbors)
    assert raw['bounded_potential_calls'] == 0 and raw['original_feasibility_calls'] == 1
    assert not raw['exact_linear_feasibility'] and not raw['exact_fixed_design_infeasibility']
    original = raw['original_feasibility']
    assert original['numerical_status'] == 'HighsModelStatus.kInfeasible'
    assert 'numerical_ray_hex' not in original and 'numerical_primary_hex' not in original
    data, rows = shared.domain(selected, triples, targets, neighbors)
    assert shared.inventory(data, rows) == raw['inventory']
    lp, model_hash = shared.exact_model(data, rows)
    assert model_hash == raw['bounded_model_sha256']
    assert (lp['variables'], len(lp['rows']), lp['nonzeros']) == (2306, 1226, 8582)
    zero = shared.bounded.check_normalized_point(data, lp, [[0]*18 for _ in range(60)], 1)
    assert zero['integer_support_gap'] == 0
    controls = shared.controls()
    check = {'candidate_sha256': last['candidate_sha256'],
        'sixty_exact_row_boxes_sha256': last['individual_rows_sha256'],
        'terminal_shared_wrapper_sha256': last['shared_rows_sha256'],
        'original_phase_sha256': raw['original_feasibility_sha256'],
        'all2916_integer_registry_inequalities_hold': True,
        'all5340_actual_explanation_clauses_hold': True,
        'original_incidence_Gram_and_motif_conditions_hold': True,
        'complete60_exact_row_boxes_replayed': True,
        'saved_ray_or_potential_available_for_arithmetic_repair': False,
        'original_feasibility_call_will_not_be_repeated': True,
        'degree8_redundancy_rechecked_on_actual_supports': True}
    specification = {'data': data, 'original_rows': rows, 'bounded_potential_LP': lp}
    model = {'variables': lp['variables'], 'potential_variables': 1080,
        'capacity_variables': 1226, 'inequality_rows': 1226, 'nonzeros': 8582,
        'model_sha256': model_hash,
        'specification_sha256': hashlib.sha256(canonical(specification)).hexdigest()}
    return specification, model, check, controls, (triples, targets, neighbors, actions)


def prepare(output):
    assert not output.exists()
    started = time.monotonic()
    spec, model, check, controls, _ = calculate()
    report = {'status': 'terminal bounded-only separation prepared; no optimizer call',
        'source_sha256': digest(Path(__file__)), 'source_bindings': SOURCES,
        'parent_result_sha256': RESULT_SHA, 'parent_cold_replay_sha256': COLD_SHA,
        'parent_terminal_manifest_sha256': MANIFEST_SHA,
        'specification': spec, 'model': model, 'exact_checks': check, 'controls': controls,
        'maximum_seconds_including_setup': MAXIMUM_SECONDS, 'maximum_optimizer_calls': 1,
        'threads': 1, 'optimizer': 'simplex', 'bounded_only': True,
        'no_original_feasibility_retry': True, 'strict_integer_gap_required': True,
        'parent_UNKNOWN_unchanged': True, 'component_exclusion': False,
        'optimizer_or_solver_called': False, 'seconds': time.monotonic()-started}
    output.write_bytes(gzip.compress(canonical(report)+b'\n', mtime=0))
    print(json.dumps({k:v for k,v in report.items() if k not in ('specification','controls')}, indent=2), flush=True)


def checked_preparation(path):
    check_inputs()
    saved = read(path)
    assert saved['source_sha256'] == digest(Path(__file__)) and saved['source_bindings'] == SOURCES
    assert saved['parent_result_sha256'] == RESULT_SHA and saved['parent_cold_replay_sha256'] == COLD_SHA
    assert saved['parent_terminal_manifest_sha256'] == MANIFEST_SHA
    assert saved['maximum_seconds_including_setup'] == MAXIMUM_SECONDS
    assert hashlib.sha256(canonical(saved['specification'])).hexdigest() == saved['model']['specification_sha256']
    spec = saved['specification']
    lp, model_hash = shared.exact_model(spec['data'], spec['original_rows'])
    assert lp == spec['bounded_potential_LP'] and model_hash == saved['model']['model_sha256']
    return saved


def query(preparation, output, seconds):
    assert not output.exists() and 0 < seconds <= MAXIMUM_SECONDS
    started = time.monotonic()
    report = {'status': 'RUNNING: one terminal bounded-only separator',
        'source_sha256': digest(Path(__file__)), 'preparation': portable(preparation),
        'preparation_sha256': digest(preparation), 'requested_seconds_including_setup': seconds,
        'optimizer_calls': 0, 'exact_separator': False, 'exact_shared_box_feasibility': False,
        'original_feasibility_query_called': False, 'parent_UNKNOWN_unchanged': True,
        'component_exclusion': False, 'graph_constructed': False}
    save(output, report)
    try:
        saved = checked_preparation(preparation)
        spec = saved['specification']; report['model_sha256'] = saved['model']['model_sha256']
        remaining = seconds-(time.monotonic()-started)
        report['remaining_seconds_after_setup'] = remaining
        if remaining <= 0:
            report['status'] = 'UNKNOWN: setup exhausted budget; no bounded query'
        else:
            phase_path = output.with_name(output.stem+'-bounded.json')
            phase = shared.bounded_query(spec['data'], spec['original_rows'], phase_path, remaining)
            shared.replay_bounded(phase, spec['data'], spec['original_rows'])
            report.update(status=phase['status'], bounded_phase=portable(phase_path),
                bounded_phase_sha256=digest(phase_path), optimizer_calls=phase['optimizer_calls'],
                exact_separator=phase['exact_separator'])
    except Exception as error:
        report.update(status='ERROR: bounded-only query stopped', error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic()-started
        report['cooperative_budget_overrun_seconds'] = max(0, report['elapsed_seconds']-seconds)
        save(output, report)
    print(json.dumps(report, indent=2), flush=True)


def reconstruct(preparation, result_path=None):
    saved = checked_preparation(preparation)
    spec, model, checks, controls, context = calculate()
    assert (spec, model, checks, controls) == (saved['specification'], saved['model'], saved['exact_checks'], saved['controls'])
    report = {'status': 'PASS: cold terminal candidate, full registry, exact boxes and bounded-only model',
        'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation),
        'model_sha256': model['model_sha256'], 'parent_UNKNOWN_preserved': True,
        'original_feasibility_query_called': False, 'optimizer_or_solver_called': False}
    if result_path is None:
        return report, None
    result = read(result_path)
    assert result['source_sha256'] == digest(Path(__file__)) and result['preparation_sha256'] == digest(preparation)
    assert not result['status'].startswith(('RUNNING:', 'ERROR:'))
    assert result['model_sha256'] == model['model_sha256']
    assert 0 < result['requested_seconds_including_setup'] <= MAXIMUM_SECONDS
    assert not result['original_feasibility_query_called'] and not result['exact_shared_box_feasibility']
    assert result['optimizer_calls'] in (0, 1)
    lifted = None
    if 'bounded_phase' in result:
        phase = bound(result, 'bounded_phase')
        assert 0 < phase['requested_seconds_including_setup'] == result['remaining_seconds_after_setup'] <= MAXIMUM_SECONDS
        shared.replay_bounded(phase, spec['data'], spec['original_rows'])
        assert result['optimizer_calls'] == phase['optimizer_calls'] and result['exact_separator'] == phase['exact_separator']
        if phase['exact_separator']:
            triples, targets, neighbors, actions = context
            lifted = shared.lift(spec['data']['selected_signature_ids'], phase['certificate']['integer_potentials60_by18'],
                                 triples, targets, neighbors, actions)
            assert lifted['raw_gap'] == phase['certificate']['check']['integer_support_gap'] > 0
            report.update(status='PASS: exact terminal support separator and all12 universal cuts',
                          exact_support_gap=lifted['raw_gap'])
    else:
        assert not result['exact_separator'] and result['optimizer_calls'] == 0
    report.update(result_sha256=digest(result_path), exact_separator=result['exact_separator'],
                  component_exclusion=False)
    return report, lifted


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare'); prep.add_argument('--output', type=Path, required=True)
    run = commands.add_parser('query'); run.add_argument('--preparation', type=Path, required=True)
    run.add_argument('--output', type=Path, required=True); run.add_argument('--seconds', type=float, default=60)
    replay = commands.add_parser('replay'); replay.add_argument('--preparation', type=Path, required=True)
    replay.add_argument('--result', type=Path); replay.add_argument('--output', type=Path, required=True)
    replay.add_argument('--lift-output', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output.resolve())
    elif args.command == 'query':
        query(args.preparation.resolve(), args.output.resolve(), args.seconds)
    else:
        assert not args.output.exists()
        report, lifted = reconstruct(args.preparation.resolve(), args.result.resolve() if args.result else None)
        if lifted is not None:
            assert args.lift_output is not None and not args.lift_output.exists()
            save(args.lift_output, lifted)
            report.update(lift=portable(args.lift_output), lift_sha256=digest(args.lift_output))
        else:
            assert args.lift_output is None
        save(args.output, report); print(json.dumps(report, indent=2), flush=True)
