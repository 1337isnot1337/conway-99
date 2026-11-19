"""Complete case4 incidence CNF plus30 Gram conflicts and60 exact row cuts.

Every added weighted inequality is replayed from an integer exterior-row
potential. The frozen unsigned threshold DAG is an exact existential
Boolean encoding; its auxiliaries begin above every original variable.
Preparation refuses the whole overlay if any cut exceeds its resource
limit. No partial overlay is exposed as a completed query model.
"""

import argparse
from collections import Counter, defaultdict
import gc
import hashlib
import json
from pathlib import Path
import resource
import subprocess
import tempfile
import time

import complement_rook_35core_incidence as original
import complement_rook_35core_case0004_symmetric_lp as exact
import root_prism_free_f0_weighted_threshold as weighted


ROOT, LOGS = original.ROOT, original.LOGS
BASE = LOGS / 'complement-rook-35core-first-local-sweep01/case0004-model.json'
BASE_SHA = '43fc0c40a724f4c287df770fce58abc45835ee7534f2b7e5cd06d3baf380cfde'
DEPENDENCIES = {
    'complement_rook_35core_incidence.py': '3440d21fb9d41f6146cdf5b8ef4f61feb513da9cb10e7775f3b085863a3949cf',
    'complement_rook_35core_case0004_symmetric_lp.py': '458e6306ba9c1efe09d7ce9b13e26554c48b3fa1083bffbc0ef0f0ff2601af52',
    'root_prism_free_f0_weighted_threshold.py': 'a0c4b38d7787c8e6565ab122e0fdf41655ea40a9f0f218c0f860cd59d3f05144',
}
LIMITS = {'branch_states_per_cut': 250000, 'total_variables': 1000000,
          'total_clauses': 2000000, 'complete_row_cut_count': 60}
digest, canonical, portable = original.digest, original.canonical, original.portable


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalized(value):
    return json.loads(canonical(value))


def clause_bytes(clauses):
    return ''.join(' '.join(map(str, clause)) + ' 0\n' for clause in clauses).encode()


def save(path, value):
    temporary = path.with_suffix(path.suffix + '.tmp')
    temporary.write_text(json.dumps(value, indent=2) + '\n')
    temporary.replace(path)


def source_hashes():
    names = sorted(set(DEPENDENCIES) | set(original.SOURCES) | {Path(__file__).name})
    return {name: digest(Path(__file__).with_name(name)) for name in names}


def inputs():
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert digest(BASE) == BASE_SHA
    inventory, row_model, cuts = exact.load_inputs()
    base = original.checked_model(BASE)
    assert inventory['base_model_sha256'] == BASE_SHA
    assert inventory['original_CNF_sha256'] == base['cnf_sha256']
    assert row_model['base_model_sha256'] == BASE_SHA
    assert row_model['original_CNF_sha256'] == base['cnf_sha256']
    assert len(cuts) == LIMITS['complete_row_cut_count']
    assert row_model['column_masks35'] == inventory['column_masks35']
    assert len(row_model['column_masks35']) == 1214
    no_goods = [[-a-1, -b-1] for row in inventory['optional_binary_cuts']
                for a, b in [row['support']]]
    assert len(no_goods) == len({tuple(c) for c in no_goods}) == 30
    assert all(len(c) == 2 and all(-1214 <= v < 0 for v in c) for c in no_goods)
    return base, inventory, row_model, cuts, no_goods


def actual_cut_controls(cut, clauses, metadata):
    """Construct canonical auxiliaries on deterministic complete input points.

    The generic tiny exhaustive control proves existential semantics
    independently. These tests additionally exercise the actual variable
    offsets, all actual weights, guard handling, and new-clause tails.
    """
    target = cut['target_column'] + 1
    terms = [(b+1, w) for b, w in cut['positive_terms']]
    demand = cut['positive_demand']
    variables = {v for v, _ in terms}
    old_top, new_top = metadata['initial_top'], metadata['final_top']
    assert target <= 1214 and all(1 <= v <= 1214 and v != target for v in variables)
    assert all(abs(v) in variables | {target} or old_top < abs(v) <= new_top
               for clause in clauses for v in clause)
    groups = defaultdict(list)
    for clause in clauses:
        if clause and clause[0] < -old_top:
            node = -clause[0]
            assert all(abs(v) < node for v in clause[1:])
            groups[node].append(clause[1:])
    assert set(groups) == set(range(old_top+1, new_top+1))
    subsets = [set(), set(variables), {v for v in variables if v % 2},
               {v for v in variables if not v % 2}]
    running, subtotal = set(), 0
    for variable, weight in sorted(terms, key=lambda pair: (-pair[1], pair[0])):
        if subtotal < demand <= subtotal + weight:
            subsets.append(set(running))
            subsets.append(running | {variable})
            break
        running.add(variable)
        subtotal += weight
    seen = set()
    checks = 0
    for subset in subsets:
        for guard in (False, True):
            chosen = subset | ({target} if guard else set())
            key = tuple(sorted(chosen))
            if key in seen:
                continue
            seen.add(key)
            values = {v: v in chosen for v in variables | {target}}

            def truth(literal):
                value = values[abs(literal)]
                return value if literal > 0 else not value

            for node in sorted(groups):
                values[node] = all(any(truth(v) for v in tail) for tail in groups[node])
            expected = not guard or sum(w for v, w in terms if v in chosen) >= demand
            observed = all(any(truth(v) for v in clause) for clause in clauses)
            assert observed == expected
            normalized_terms = metadata['normalized_terms']
            normalized_value = sum(w for v, w in normalized_terms if v in chosen)
            assert (normalized_value >= metadata['normalized_demand']) == (
                sum(w for v, w in terms if v in chosen) >= demand)
            checks += 1
    return checks


def rebuild(progress=None):
    """Cold-build every original clause and every complete extra cut."""
    base, inventory, row_model, cuts, no_goods = inputs()
    data, cnf, old_metadata = original.rebuild(4)
    assert normalized(old_metadata) == base['formula']
    assert original.domains.sha(canonical(data[3])) == base['domain_record_sha256']
    assert data[3]['columns'] == row_model['columns'] == inventory['columns']
    assert data[5] == row_model['Gram'] == inventory['Gram']
    assert data[-1] == row_model['column_masks35']
    with tempfile.TemporaryDirectory(prefix='conway-case4-row-cut-base-') as directory:
        path = Path(directory) / 'original.cnf'
        cnf.to_file(path)
        raw = path.read_bytes()
    assert sha(raw) == base['cnf_sha256']
    first, original_body = raw.split(b'\n', 1)
    assert first == f"p cnf {base['formula']['variables']} {base['formula']['clauses']}".encode()
    assert clause_bytes(cnf.clauses) == original_body
    assert (cnf.nv, len(cnf.clauses)) == (107207, 218863)
    original_clause_count, original_top = len(cnf.clauses), cnf.nv
    cnf.extend(no_goods)
    records = []
    top = cnf.nv
    control_assignments = 0
    for index, cut in enumerate(cuts):
        target = cut['target_column'] + 1
        terms = [(b+1, w) for b, w in cut['positive_terms']]
        added, new_top, record = weighted.guarded_threshold(
            target, terms, cut['positive_demand'], top, LIMITS['branch_states_per_cut'])
        if new_top > LIMITS['total_variables']:
            raise RuntimeError('complete overlay variable budget exceeded; no query model returned')
        if len(cnf.clauses) + len(added) > LIMITS['total_clauses']:
            raise RuntimeError('complete overlay clause budget exceeded; no query model returned')
        checks = actual_cut_controls(cut, added, record)
        control_assignments += checks
        record.update(cut_index=index, target_column=cut['target_column'],
                      exact_integer_cut_sha256=sha(canonical(cut)),
                      clause_start_zero_based=len(cnf.clauses),
                      added_clause_body_sha256=sha(clause_bytes(added)),
                      actual_complete_input_controls=checks)
        cnf.extend(added)
        top = new_top
        assert cnf.nv == top
        records.append(record)
        if progress:
            progress(index, record, top, len(cnf.clauses))
    assert len(records) == LIMITS['complete_row_cut_count']
    assert clause_bytes(cnf.clauses[:original_clause_count]) == original_body
    assert cnf.clauses[original_clause_count:original_clause_count+30] == no_goods
    assert cnf.nv <= LIMITS['total_variables'] and len(cnf.clauses) <= LIMITS['total_clauses']
    metadata = {
        'primary_columns': 1214, 'variables': cnf.nv, 'clauses': len(cnf.clauses),
        'original_variables': original_top, 'original_clauses': original_clause_count,
        'certified_Gram_conflict_clauses': len(no_goods), 'exact_exterior_row_cuts': len(cuts),
        'weighted_threshold_clauses': sum(record['clauses'] for record in records),
        'weighted_threshold_auxiliary_variables': top-original_top,
        'weighted_threshold_branch_states': sum(record['branch_states'] for record in records),
        'largest_cut_branch_states': max(record['branch_states'] for record in records),
        'largest_cut_auxiliary_variables': max(record['auxiliary_variables'] for record in records),
        'largest_normalized_demand': max(record['normalized_demand'] for record in records),
        'threshold_demand_histogram': dict(sorted(Counter(record['normalized_demand'] for record in records).items())),
        'forced_absent_columns': [cut['target_column'] for cut in cuts if not cut['positive_terms']],
        'actual_cut_complete_input_control_assignments': control_assignments,
        'unchanged_original_clause_body_sha256': sha(original_body),
        'added_clause_body_sha256': sha(clause_bytes(cnf.clauses[original_clause_count:])),
    }
    assert metadata['forced_absent_columns'] == [1080, 1081]
    assert metadata['clauses'] == original_clause_count + 30 + metadata['weighted_threshold_clauses']
    return base, inventory, row_model, cuts, no_goods, data, cnf, metadata, records


def prepare(model_path, cnf_path, progress_path):
    assert not model_path.exists() and not cnf_path.exists() and not progress_path.exists()
    started = time.monotonic()
    state = {'status': 'preparing all60 exact Boolean row cuts; no incidence query',
             'source_hashes': source_hashes(), 'limits': LIMITS,
             'completed_cut_indices': [], 'complete': False, 'SAT_queries': 0}

    def checkpoint(index, record, variables, clauses):
        state['completed_cut_indices'].append(index)
        state.update(variables=variables, clauses=clauses,
                     last_cut_branch_states=record['branch_states'],
                     elapsed_seconds=time.monotonic()-started)
        save(progress_path, state)
        if index % 10 == 9 or index == 59:
            print(json.dumps({'complete_cut_prefix': index+1, 'variables': variables,
                              'clauses': clauses}), flush=True)

    save(progress_path, state)
    try:
        generic_controls = weighted.controls()
        rebuilt = rebuild(checkpoint)
        base, inventory, row_model, cuts, no_goods, data, cnf, metadata, records = rebuilt
        assert generic_controls['source_sha256'] == DEPENDENCIES['root_prism_free_f0_weighted_threshold.py']
        cnf_path.parent.mkdir(parents=True, exist_ok=True)
        cnf.to_file(cnf_path)
        model = {
            'status': 'complete original case4 formula plus30 Gram conflicts and60 row cuts; not solved',
            'complete': True, 'source_hashes': source_hashes(),
            'prefix_certificate_sha256': original.PREFIX_SHA,
            'base_model': portable(BASE), 'base_model_sha256': BASE_SHA,
            'base_cnf_sha256': base['cnf_sha256'],
            'row_cut_result': portable(exact.RESULT), 'row_cut_result_sha256': exact.RESULT_SHA,
            'row_cut_exact_replay': portable(exact.REPLAY), 'row_cut_exact_replay_sha256': exact.REPLAY_SHA,
            'row_domain_sha256': exact.previous.separator.MODEL_SHA,
            'complete_ordered_cut_list_sha256': sha(canonical(cuts)),
            'no_good_primary_clauses': no_goods,
            'case': base['case'], 'domain_record_sha256': base['domain_record_sha256'],
            'column_domain_sha256': base['column_domain_sha256'], 'Gram_sha256': base['Gram_sha256'],
            'cnf': str(cnf_path.resolve()), 'cnf_sha256': digest(cnf_path),
            'cnf_bytes': cnf_path.stat().st_size, 'formula': metadata,
            'cut_encodings': records, 'limits': LIMITS,
            'generic_exact_encoding_controls': generic_controls,
            'Boolean_equivalence': 'Original primary-feasible incidence formula AND all30 exact Gram conflicts AND all60 original integer guarded inequalities; every new auxiliary is existential.',
            'full_exterior_adjacency_variables': 0, 'fixed_incidence_design': False,
            'graph_automorphism_constraints': False, 'SAT_queries': 0,
            'SAT_scope': 'Partial binary incidence only; every original margin, triple, no-good and row inequality must be checked directly.',
            'UNSAT_scope': 'Only indexed35-core case4 and its actual verified relabelings.',
            'build_seconds': time.monotonic()-started,
            'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        }
        save(model_path, model)
        state.update(status='all60 complete cuts prepared; no incidence query', complete=True,
                     model_sha256=digest(model_path), cnf_sha256=model['cnf_sha256'],
                     elapsed_seconds=time.monotonic()-started)
        save(progress_path, state)
    except Exception as error:
        state.update(status='preparation refused or failed; no completed query model',
                     error_type=type(error).__name__, error_message=str(error),
                     elapsed_seconds=time.monotonic()-started)
        save(progress_path, state)
        raise
    print(json.dumps({key: value for key, value in model.items() if key != 'cut_encodings'}, indent=2), flush=True)


def checked_model(model_path, require_cnf=False):
    model = original.checked_model(model_path, require_cnf)
    assert model['complete'] and model['source_hashes'] == source_hashes()
    assert model['case']['index'] == 4 and model['limits'] == LIMITS
    assert model['base_model_sha256'] == BASE_SHA
    assert model['row_cut_result_sha256'] == exact.RESULT_SHA
    assert model['row_cut_exact_replay_sha256'] == exact.REPLAY_SHA
    assert model['formula']['exact_exterior_row_cuts'] == 60
    return model


def inspect_overlay(selected, inventory, cuts):
    chosen = set(selected)
    assert len(chosen) == len(selected) == 64
    for cut in inventory['optional_binary_cuts']:
        assert sum(c in chosen for c in cut['support']) <= 1
    for cut in cuts:
        supply = sum(weight for c, weight in cut['positive_terms'] if c in chosen)
        assert supply >= cut['positive_demand'] * (cut['target_column'] in chosen)
    return {'status': 'all30 Gram conflicts and60 original uncapped integer row inequalities checked',
            'selected_columns': len(selected), 'forced_absent_columns_checked': [1080, 1081],
            'remaining64_vertex_adjacency_unspecified': True, 'complete_graph': False}


def solve(model_path, directory, seconds, checker, checker_seconds):
    assert 0 < seconds <= 60 and 0 < checker_seconds <= 60
    model = checked_model(model_path, True)
    result = original.solve(model_path, directory, seconds, checker, checker_seconds)
    if result['status'].startswith('SAT;'):
        _, inventory, _, cuts, _ = inputs()
        check = inspect_overlay(result['incidence_witness']['selected_columns'], inventory, cuts)
        save(directory / 'row-cut-witness-check.json', check)
    return result


def replay(model_path, result_path, output, checker, checker_seconds):
    assert not output.exists() and 0 < checker_seconds <= 60
    model = checked_model(model_path)
    base, inventory, row_model, cuts, no_goods, data, cnf, metadata, records = rebuild()
    assert normalized(metadata) == model['formula']
    assert normalized(records) == model['cut_encodings']
    assert no_goods == model['no_good_primary_clauses']
    assert sha(canonical(cuts)) == model['complete_ordered_cut_list_sha256']
    assert weighted.controls() == model['generic_exact_encoding_controls']
    with tempfile.TemporaryDirectory(prefix='conway-case4-row-cut-replay-') as directory:
        path = Path(directory) / 'full.cnf'
        cnf.to_file(path)
        assert digest(path) == model['cnf_sha256'] and path.stat().st_size == model['cnf_bytes']
    report = {'status': 'cold full domain/original-CNF/30 exact conflicts/60 exact thresholds replay PASS',
              'model_sha256': digest(model_path), 'source_hashes': source_hashes(),
              'base_cnf_sha256': base['cnf_sha256'], 'cnf_sha256': model['cnf_sha256'],
              'case_index': 4, 'formula': metadata,
              'all60_integer_potential_certificates_rechecked': True,
              'all_original_clauses_preserved': True,
              'whole_local_set_excluded': False, 'full_graph': False}
    if result_path:
        result = json.loads(result_path.read_text())
        assert result['model_sha256'] == digest(model_path)
        assert result['source_sha256'] == DEPENDENCIES['complement_rook_35core_incidence.py']
        assert result['cnf_sha256'] == model['cnf_sha256'] and result['case_index'] == 4
        report['result_sha256'] = digest(result_path)
        if result['status'].startswith('SAT;'):
            actual = original.inspect(result['incidence_witness']['selected_columns'], data)
            assert normalized(actual) == result['incidence_witness']
            report['overlay_witness_check'] = inspect_overlay(actual['selected_columns'], inventory, cuts)
            report['status'] = 'cold full formula and exact partial incidence witness replay PASS'
        elif result['status'].startswith('UNSAT with direct DRAT;'):
            item = result['retained_certificate']
            retained, proof = ROOT / item['cnf'], ROOT / item['proof']
            assert digest(retained) == item['cnf_sha256'] and digest(proof) == item['proof_sha256']
            inputs_used = list(original.read_clauses(retained))
            assert len(inputs_used) == item['input_clauses']
            needed = {tuple(sorted(clause)) for clause in inputs_used}
            original_inputs, conflict_inputs, threshold_inputs = set(), set(), set()
            for index, clause in enumerate(cnf.clauses):
                key = tuple(sorted(clause))
                if key in needed:
                    if index < metadata['original_clauses']:
                        original_inputs.add(key)
                    elif index < metadata['original_clauses'] + 30:
                        conflict_inputs.add(key)
                    else:
                        threshold_inputs.add(key)
            assert needed == original_inputs | conflict_inputs | threshold_inputs
            checked = subprocess.run([str(checker), str(retained), str(proof), '-t', str(checker_seconds), '-w'],
                                     capture_output=True, text=True, timeout=checker_seconds+5, check=False)
            log = output.with_suffix('.drat.log')
            log.write_text(checked.stdout + checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            report.update(status='cold full formula, exact cut certificates, retained inclusion and DRAT replay PASS',
                          excluded_indexed_core=4, retained_input_clauses=len(inputs_used),
                          retained_distinct_original_inputs=len(original_inputs),
                          retained_distinct_conflict_inputs_outside_original=len(conflict_inputs-original_inputs),
                          retained_distinct_threshold_inputs_outside_previous=len(threshold_inputs-original_inputs-conflict_inputs),
                          original_only_proof_binding_verified=needed <= original_inputs,
                          checker_log=portable(log), checker_log_sha256=digest(log))
        else:
            assert result['status'].startswith('UNKNOWN;')
            report['status'] = 'cold full formula and UNKNOWN binding replay PASS; no exclusion'
    save(output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--model', type=Path, required=True)
    prep.add_argument('--cnf', type=Path, required=True)
    prep.add_argument('--progress', type=Path, required=True)
    run = commands.add_parser('solve')
    run.add_argument('--model', type=Path, required=True)
    run.add_argument('--directory', type=Path, required=True)
    run.add_argument('--seconds', type=float, default=60)
    run.add_argument('--checker-seconds', type=int, default=60)
    run.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    check = commands.add_parser('replay')
    check.add_argument('--model', type=Path, required=True)
    check.add_argument('--result', type=Path)
    check.add_argument('--output', type=Path, required=True)
    check.add_argument('--checker-seconds', type=int, default=60)
    check.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.model.resolve(), args.cnf.resolve(), args.progress.resolve())
    elif args.command == 'solve':
        solve(args.model.resolve(), args.directory.resolve(), args.seconds,
              args.drat_trim.resolve(), args.checker_seconds)
    else:
        replay(args.model.resolve(), args.result.resolve() if args.result else None, args.output.resolve(),
               args.drat_trim.resolve(), args.checker_seconds)
