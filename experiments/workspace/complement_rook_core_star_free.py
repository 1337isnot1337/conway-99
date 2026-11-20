"""One free, proof-enabled60-second query of the frozen reduced R8 star.

No selector assumptions, cuts, extra caps, or phase hints are supplied.
SAT is checked directly as a partial star witness. UNSAT needs retained
DRAT and a separate cold rebuild of the parent baseline/star reduction.
"""

import argparse
import gc
import json
from pathlib import Path
import resource
import subprocess
import tempfile
import time

from pysat.formula import CNF
from pysat.solvers import Solver

import complement_rook_core_star_oracle as parent
import complement_rook_core_star_reduced as reduced
from complement_rook_incidence_master import ROOT, bounded, clauses, digest
from complement_rook_joint_split import check_base


def bindings(path, require_cnf=False):
    model = json.loads(path.read_text())
    assert model['name'] == 'R8'
    assert model['source_sha256'] == digest(Path(reduced.__file__))
    parent_path = ROOT/model['parent_model']
    assert digest(parent_path) == model['parent_model_sha256']
    old = json.loads(parent_path.read_text())
    for source, expected in old['source_hashes'].items():
        assert digest(Path(__file__).with_name(source)) == expected
    algebra, _ = reduced.identities(old)
    assert algebra == model['identities']
    base, rows, gram, triples, signatures, needs, variables = check_base(ROOT/old['base_manifest'], require_cnf=False)
    assert base['domain_sha256'] == model['base_domain_sha256'] == old['base_domain_sha256']
    star_sources = {s for s, sites in enumerate(signatures) if 8 in sites}
    edges = {edge: variable for edge, variable in variables.items()
             if edge[0] in star_sources or edge[1] in star_sources}
    assert len(star_sources) == 28 and len(edges) == 4456
    assert [{'signatures': list(edge), 'variable': variable} for edge, variable in edges.items()] == old['retained_edges']
    assert (model['variables_including_unused_primary_id_gaps'], model['clauses']) == (65774, 144864)
    if require_cnf:
        assert digest(Path(model['cnf'])) == model['cnf_sha256']
    return model, old, rows, gram, triples, signatures, needs, edges, star_sources


def supported_rows(signatures, needs, edges, star_sources):
    incident = [[] for _ in signatures]
    for (a, b), variable in edges.items():
        incident[a].append((b, variable))
        incident[b].append((a, variable))
    unique = {}
    raw = 0
    for source in range(252):
        targets = range(27) if source in star_sources else [8]
        for target in targets:
            raw += 1
            literals = tuple(variable for other, variable in incident[source] if target in signatures[other])
            key = source, literals, needs[source][target]
            unique.setdefault(key, (source, target, literals, needs[source][target]))
    assert raw == 980 and len(unique) == 952
    return list(unique.values())


def inspect(selected, selected_edges, domain):
    _, _, rows, gram, triples, signatures, needs, edges, star_sources = domain
    assert selected == sorted(set(selected)) and len(selected) == 72
    chosen = set(selected)
    assert chosen <= set(range(252))
    assert selected_edges == sorted(set(selected_edges))
    assert all(a < b and (a, b) in edges and a in chosen and b in chosen for a, b in selected_edges)
    assert all(sum(i in signatures[s] and j in signatures[s] for s in selected) == gram[i][j]
               for i in range(27) for j in range(27))
    active_ids = {edges[edge] for edge in selected_edges}
    neighbors = [set() for _ in signatures]
    for a, b in selected_edges:
        neighbors[a].add(b)
        neighbors[b].add(a)
    row_list = supported_rows(signatures, needs, edges, star_sources)
    for source, _, literals, quota in row_list:
        assert sum(variable in active_ids for variable in literals) == quota*(source in chosen)
    packing_pairs = 0
    masks = [sum(1 << i for i in sites) for sites in signatures]
    for source in range(252):
        adjacent = sorted(neighbors[source])
        for i, a in enumerate(adjacent):
            for b in adjacent[i+1:]:
                packing_pairs += 1
                assert (masks[a] & masks[b]).bit_count() <= 1
    selected_star = sorted(chosen & star_sources)
    assert len(selected_star) == 8
    assert all(len(neighbors[source]) == 11*(source in chosen) for source in star_sources)
    assert all(len(neighbors[source] & set(selected_star)) == 1 for source in selected_star)
    assert len(selected_edges) == 84
    # These pair equations are fully visible because both source rows are
    # retained. They are diagnostic only; the baseline did not impose them.
    defects = []
    values = []
    for i, a in enumerate(selected_star):
        for b in selected_star[i+1:]:
            value = (masks[a] & masks[b]).bit_count()+len(neighbors[a] & neighbors[b])+int(b in neighbors[a])
            values.append(value)
            if value != 2:
                defects.append({'signatures': [a, b], 'value': value, 'difference_from_two': value-2})
    assert sum(values) == 56
    rook = lambda a, b: a != b and (a//3 == b//3 or a % 3 == b % 3)
    parameter = sum(rook(triples[s][0], triples[s][2]) and rook(triples[s][1], triples[s][2]) for s in selected)
    return {'selected_signatures': selected, 'selected_signature_triples': [list(triples[s]) for s in selected],
            'selected_edges': [list(edge) for edge in selected_edges], 'selected_star_signatures': selected_star,
            'a': parameter, 'incidence_parameter_in_already_excluded_a_le_two': parameter <= 2,
            'full_Gram_entries_checked': 729, 'activation_checked_on_every_active_edge': True,
            'distinct_supported_mixed_rows_checked': len(row_list),
            'packing_neighbor_pairs_checked': packing_pairs,
            'selected_star_degree_check': 'all8 selected star sources have11 exterior neighbors',
            'selected_star_matching_check': 'one internal neighbor per selected star source',
            'visible_selected_star_pair_values_sum': sum(values),
            'visible_selected_star_pair_defects': defects,
            'visible_selected_star_upper_cap_violations': sum(item['difference_from_two'] > 0 for item in defects),
            'unmodeled_edge_variables_are_unknown': True, 'complete_graph': False}


def prepare(model_path, output):
    model, old, _, _, _, signatures, needs, edges, sources = bindings(model_path, True)
    supported = supported_rows(signatures, needs, edges, sources)
    record = {'status': 'one free reduced-star query prepared; no solver called',
              'source_sha256': digest(Path(__file__)), 'model': parent.portable(model_path),
              'model_sha256': digest(model_path), 'cnf': model['cnf'], 'cnf_sha256': model['cnf_sha256'],
              'variables': model['variables_including_unused_primary_id_gaps'], 'clauses': model['clauses'],
              'selectors': 252, 'retained_edges': len(edges), 'distinct_mixed_rows': len(supported),
              'packing_clauses': old['clause_counts']['packing'],
              'proof_enabled': True, 'solver_budget_seconds_including_bootstrap': 60,
              'direct_DRAT_budget_seconds': 60, 'replay_DRAT_budget_seconds': 60,
              'assumptions': [], 'added_cuts': [], 'added_graph_constraints': 0,
              'extra_a_bound': False, 'graph_automorphism_assumptions': 0,
              'SAT_scope': 'binary partial star witness only'}
    assert not output.exists()
    output.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2), flush=True)
    return record


def run(manifest_path, directory, output, checker):
    manifest = json.loads(manifest_path.read_text())
    assert manifest['source_sha256'] == digest(Path(__file__))
    model_path = ROOT/manifest['model']
    assert digest(model_path) == manifest['model_sha256']
    domain = bindings(model_path, True)
    model = domain[0]
    assert manifest['assumptions'] == manifest['added_cuts'] == []
    assert manifest['solver_budget_seconds_including_bootstrap'] == manifest['direct_DRAT_budget_seconds'] == 60
    assert not directory.exists() and not output.exists()
    directory.mkdir(parents=True)
    result = {'status': 'running one free reduced-star query',
              'source_sha256': digest(Path(__file__)), 'manifest': parent.portable(manifest_path),
              'manifest_sha256': digest(manifest_path), 'model_sha256': digest(model_path),
              'cnf_sha256': model['cnf_sha256'], 'assumptions': [], 'added_cuts': [],
              'completed_graph': None, 'whole_complementary_core_exclusion_established': False}

    def save():
        result['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        output.write_text(json.dumps(result, indent=2)+'\n')

    save()
    started = time.monotonic()
    try:
        cnf = CNF(from_file=model['cnf'])
        assert (cnf.nv, len(cnf.clauses)) == (65774, 144864)
        with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
            del cnf
            gc.collect()
            result['bootstrap_seconds'] = time.monotonic()-started
            answer = bounded(solver, 60-(time.monotonic()-started))
            result['solve_return_seconds'] = time.monotonic()-started
            result['solver_statistics'] = solver.accum_stats()
            if answer is None:
                result['status'] = 'UNKNOWN; free reduced-star feasibility unresolved'
            elif answer:
                positive = {literal for literal in solver.get_model() if literal > 0}
                selected = [s for s in range(252) if s+1 in positive]
                selected_edges = sorted(edge for edge, variable in domain[7].items() if variable in positive)
                result['partial_witness'] = inspect(selected, selected_edges, domain)
                result['status'] = 'SAT; exact binary partial-star witness directly checked'
            else:
                proof = solver.get_proof()
                assert proof is not None
                result['appended_terminal_empty_clause'] = not proof or proof[-1] != '0'
                if result['appended_terminal_empty_clause']:
                    proof.append('0')
                raw = Path('/tmp/conway-core-star-free-pilot01-R8.drat')
                assert not raw.exists()
                raw.write_text('\n'.join(proof)+'\n')
                result.update(status='solver UNSAT; direct DRAT pending',
                              raw_proof=str(raw), raw_proof_sha256=digest(raw), raw_proof_lines=len(proof))
        save()
        if result['status'].startswith('solver UNSAT'):
            retained, proof, log = directory/'retained.cnf', directory/'retained.drat', directory/'direct-drat.log'
            checked = subprocess.run([str(checker), model['cnf'], result['raw_proof'], '-t', '60', '-w',
                                      '-c', str(retained), '-l', str(proof)],
                                     capture_output=True, text=True, timeout=65, check=False)
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            inputs = list(clauses(retained))
            needed = {tuple(sorted(clause)) for clause in inputs}
            for clause in clauses(Path(model['cnf'])):
                needed.discard(tuple(sorted(clause)))
            assert not needed
            result['retained_certificate'] = {'retained_cnf': parent.portable(retained),
                'retained_cnf_sha256': digest(retained), 'retained_proof': parent.portable(proof),
                'retained_proof_sha256': digest(proof), 'retained_input_clauses': len(inputs),
                'direct_checker_log': parent.portable(log), 'direct_checker_log_sha256': digest(log),
                'full_cold_rebuild_pending': True}
            result['status'] = 'UNSAT with direct DRAT; cold baseline/star rebuild and proof replay required'
        result['total_seconds'] = time.monotonic()-started
        save()
    except Exception as error:
        result.update(status='error; no unverified exclusion promoted', error_type=type(error).__name__,
                      error_message=str(error))
        save()
        raise
    print(json.dumps({key: value for key, value in result.items() if key not in ('partial_witness', 'completed_graph')}, indent=2), flush=True)
    return result


def replay(result_path, checker, checker_log):
    result = json.loads(result_path.read_text())
    assert result['source_sha256'] == digest(Path(__file__))
    manifest_path = ROOT/result['manifest']
    assert digest(manifest_path) == result['manifest_sha256']
    manifest = json.loads(manifest_path.read_text())
    model_path = ROOT/manifest['model']
    assert digest(model_path) == manifest['model_sha256'] == result['model_sha256']
    domain = bindings(model_path)
    if result['status'].startswith('SAT;'):
        old = result['partial_witness']
        point = inspect(old['selected_signatures'], [tuple(edge) for edge in old['selected_edges']], domain)
        assert point == old
        record = {'status': 'saved binary partial-star witness independently replayed',
                  'a': point['a'], 'full_Gram_entries': 729, 'distinct_supported_mixed_rows': 952,
                  'selected_edges': len(point['selected_edges']),
                  'visible_star_cap_violations': point['visible_selected_star_upper_cap_violations'],
                  'complete_graph': False}
    else:
        assert result['status'] == 'UNSAT with direct DRAT; cold baseline/star rebuild and proof replay required'
        base, _, stars, _, _, _ = parent.catalogue_and_prepare()
        star = next(star for star in stars if star.name == 'R8')
        model, old = domain[:2]
        assert base['domain_sha256'] == model['base_domain_sha256']
        with tempfile.TemporaryDirectory(prefix='rook-star-free-cold-replay-') as temporary:
            path = Path(temporary)/'rebuilt.cnf'
            star.cnf.to_file(path)
            assert digest(path) == old['cnf_sha256']
            cnf, _, reduction = reduced.reduce_formula(old, star.cnf)
            assert all(model[key] == value for key, value in reduction.items())
            cnf.to_file(path)
            assert digest(path) == model['cnf_sha256'] == result['cnf_sha256']
        certificate = result['retained_certificate']
        retained, proof = ROOT/certificate['retained_cnf'], ROOT/certificate['retained_proof']
        assert digest(retained) == certificate['retained_cnf_sha256']
        assert digest(proof) == certificate['retained_proof_sha256']
        inputs = list(clauses(retained))
        assert len(inputs) == certificate['retained_input_clauses']
        needed = {tuple(sorted(clause)) for clause in inputs}
        for clause in cnf.clauses:
            needed.discard(tuple(sorted(clause)))
        assert not needed
        checked = subprocess.run([str(checker), str(retained), str(proof), '-t', '60', '-w'],
                                 capture_output=True, text=True, timeout=65, check=False)
        checker_log.write_text(checked.stdout+checked.stderr)
        assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
        record = {'status': 'full baseline and reduced-star cold rebuild, retained inclusion, and DRAT replay passed',
                  'variables': cnf.nv, 'clauses': len(cnf.clauses),
                  'retained_input_clauses': len(inputs), 'unconditional_within_complementary_core': True}
    print(json.dumps(record, indent=2), flush=True)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    prep = sub.add_parser('prepare')
    prep.add_argument('--model', type=Path, required=True)
    prep.add_argument('--output', type=Path, required=True)
    solve = sub.add_parser('run')
    for name in ('manifest', 'directory', 'output', 'drat-trim'):
        solve.add_argument('--'+name, type=Path, required=True)
    verify = sub.add_parser('replay')
    for name in ('result', 'drat-trim', 'checker-log'):
        verify.add_argument('--'+name, type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.model.resolve(), args.output.resolve())
    elif args.command == 'run':
        run(args.manifest.resolve(), args.directory.resolve(), args.output.resolve(), args.drat_trim.resolve())
    else:
        replay(args.result.resolve(), args.drat_trim.resolve(), args.checker_log.resolve())
