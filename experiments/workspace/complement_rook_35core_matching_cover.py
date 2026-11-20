"""Exact matching cover and144 transported conditional edge clauses.

No solver is called. Existing checked35-core proofs are dependencies.
Optional --verify-proofs cold-rebuilds and rechecks those dependencies.
The clauses are necessary for actual graphs, not claimed consequences
of the older weak joint incidence/edge CNF.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
from itertools import combinations
import json
from pathlib import Path

import complement_rook_projector_schur as universe
import complement_rook_35core_incidence as incidence


ROOT, LOGS = incidence.ROOT, incidence.LOGS
SWEEP = LOGS/'complement-rook-35core-first-local-sweep01'
digest, canonical = incidence.digest, incidence.canonical


def matchings(vertices):
    if not vertices:
        yield ()
        return
    a = vertices[0]
    for b in vertices[1:]:
        for tail in matchings(tuple(v for v in vertices if v not in (a,b))):
            yield ((a,b),)+tail


def cycles(neighbors):
    unseen, result = set(range(len(neighbors))), []
    assert all(len(row) == 2 for row in neighbors)
    while unseen:
        start = min(unseen)
        ordered = [start]
        previous, current = start, min(neighbors[start])
        while current != start:
            assert current not in ordered
            ordered.append(current)
            following = next(v for v in neighbors[current] if v != previous)
            previous, current = current, following
        assert all(v in unseen for v in ordered)
        unseen -= set(ordered)
        result.append(ordered)
    return sorted(result, key=lambda row:(len(row),row))


def proof_dependencies():
    progress_path, manifest_path = SWEEP/'progress.json', SWEEP/'manifest.json'
    progress, manifest = json.loads(progress_path.read_text()), json.loads(manifest_path.read_text())
    assert progress['manifest_sha256'] == digest(manifest_path)
    assert progress['all27_new_cases_processed'] and progress['active_case'] is None
    assert [item['case_index'] for item in progress['completed_cases']] == list(range(1,28))
    assert not progress['first_local_set_excluded'] and not progress['whole_complementary_core_excluded']
    zero_stem = 'complement-rook-35core-incidence-case0000'
    paths = [(0, LOGS/(zero_stem+'-model.json'), LOGS/(zero_stem+'-pilot01/result.json'),
              LOGS/(zero_stem+'-pilot01-cold-replay.json'))]
    for item in progress['completed_cases']:
        for key in ('model','result','replay','stages_log'):
            assert digest(ROOT/item[key]) == item[key+'_sha256']
        paths.append((item['case_index'],ROOT/item['model'],ROOT/item['result'],ROOT/item['replay']))
    dependencies, outcomes = [], {}
    for index, model_path, result_path, replay_path in paths:
        model = incidence.checked_model(model_path)
        result, replay = json.loads(result_path.read_text()), json.loads(replay_path.read_text())
        assert result['model_sha256'] == replay['model_sha256'] == digest(model_path)
        assert result['cnf_sha256'] == replay['cnf_sha256'] == model['cnf_sha256']
        assert result['case_index'] == model['case']['index'] == index
        dependency = {'index':index,'model':incidence.portable(model_path),'model_sha256':digest(model_path),
                      'result':incidence.portable(result_path),'result_sha256':digest(result_path),
                      'cold_replay':incidence.portable(replay_path),'cold_replay_sha256':digest(replay_path)}
        if result['status'].startswith('UNSAT with direct DRAT;'):
            assert replay['status'] == 'cold domain/full-CNF rebuild, retained inclusion, and DRAT replay passed'
            assert replay['excluded_indexed_core'] == index
            certificate = result['retained_certificate']
            for key in ('cnf','proof','checker_log'):
                assert digest(ROOT/certificate[key]) == certificate[key+'_sha256']
            assert digest(ROOT/replay['checker_log']) == replay['checker_log_sha256']
            outcomes[index] = 'verified UNSAT'
            dependency['retained_certificate'] = certificate
        else:
            assert result['status'].startswith('UNKNOWN;')
            assert replay['status'] == 'cold formula rebuild and UNKNOWN binding checked; no exclusion'
            outcomes[index] = 'UNKNOWN'
        dependency['outcome'] = outcomes[index]
        dependencies.append(dependency)
    verified = sorted(index for index,outcome in outcomes.items() if outcome == 'verified UNSAT')
    assert verified == progress['verified_cases_including_previous_zero'] == [0,1,3,8,21]
    return manifest, dependencies, outcomes


def result():
    manifest, dependencies, outcomes = proof_dependencies()
    rows, _, triples, signatures, _, edge_list, domain_hash = universe.domain()
    edges = set(edge_list)
    edge_ids = {pair:253+i for i,pair in enumerate(edge_list)}
    actions = universe.actions(rows,triples)
    index_path = incidence.PREFIX/'all-core-index.json'
    index = json.loads(index_path.read_text())
    assert index['base_domain_sha256'] == domain_hash
    cases = [case for case in index['cases'] if case['local_set_orbit'] == 0]
    assert [case['index'] for case in cases] == list(range(28))
    local = cases[0]['selected_signatures']
    assert local == [0,1,9,10,18,20,26,27]
    known = [tuple(sorted(tuple(sorted((local[a],local[b]))) for a,b in case['matching'])) for case in cases]
    complete = {matching for matching in matchings(tuple(local)) if all(edge in edges for edge in matching)}
    assert len(known) == len(set(known)) == 28 and set(known) == complete

    q_labels = [triples[s][1] for s in local]
    q_groups = defaultdict(list)
    for i,q in enumerate(q_labels):
        q_groups[q].append(i)
    q_pairs = [tuple(group) for _,group in sorted(q_groups.items())]
    assert len(q_pairs) == 4 and all(len(pair) == 2 for pair in q_pairs)
    profiles = []
    for case in cases:
        matching = case['matching']
        neighbors = [set() for _ in range(8)]
        for a,b in q_pairs+[tuple(edge) for edge in matching]:
            neighbors[a].add(b)
            neighbors[b].add(a)
        components = cycles(neighbors)
        lengths = sorted(map(len,components))
        assert lengths in ([4,4],[8])
        four_details = []
        for component in components:
            if len(component) == 4:
                labels = sorted({q_labels[i] for i in component})
                assert len(labels) == 2
                four_details.append({'local_vertices':component,'S_labels':labels,
                                     'S_labels_rook_adjacent':universe.rook(*labels)})
        label_edges = sorted(sorted((q_labels[a],q_labels[b])) for a,b in matching)
        profiles.append({'index':case['index'],'matching':matching,'Q_union_M_cycles':components,
                         'cycle_lengths':lengths,'four_cycle_details':four_details,
                         'projected_S_label_edges':label_edges,
                         'rook_adjacent_S_label_edge_count':sum(universe.rook(*pair) for pair in label_edges),
                         'outcome':outcomes[case['index']]})

    target = (18,26)
    containing = [i for i,matching in enumerate(known) if target in matching]
    assert containing == [0,1,8,21]
    assert all(outcomes[i] == 'verified UNSAT' for i in containing)
    other_selectors = [s for s in local if s not in target]
    assert other_selectors == [0,1,9,10,20,27]
    base_clause = sorted([-edge_ids[target]]+[-s-1 for s in other_selectors])
    activation_controls = 0
    for mask in range(512):
        selected = [bool(mask >> i & 1) for i in range(8)]
        active_edge = bool(mask >> 8 & 1)
        if active_edge and not (selected[4] and selected[6]):
            continue
        full = not(active_edge and all(selected))
        reduced = not(active_edge and all(selected[i] for i in range(8) if i not in (4,6)))
        assert full == reduced
        activation_controls += 1
    assert activation_controls == 320

    families = [frozenset(s for s,h in enumerate(signatures) if i in h) for i in range(27)]
    family_lookup = {family:i for i,family in enumerate(families)}
    assert len(family_lookup) == 27
    images, clause_sets, stabilizer, centers = [],set(),[],Counter()
    for action_index,action in enumerate(actions):
        core_map = [family_lookup[frozenset(action[s] for s in family)] for family in families]
        assert sorted(core_map) == list(range(27))
        assert all((rows[i] >> j & 1) == (rows[core_map[i]] >> core_map[j] & 1)
                   for i in range(27) for j in range(27))
        assert all({core_map[i] for i in signatures[s]} == set(signatures[action[s]]) for s in range(252))
        image_local = sorted(action[s] for s in local)
        image_edge = tuple(sorted(action[s] for s in target))
        image_others = sorted(action[s] for s in other_selectors)
        assert image_edge in edges and len(set(image_local)) == 8
        if image_local == local:
            stabilizer.append(action_index)
        image_known = [tuple(sorted(tuple(sorted((action[a],action[b]))) for a,b in matching)) for matching in known]
        image_complete = {matching for matching in matchings(tuple(image_local)) if all(edge in edges for edge in matching)}
        assert set(image_known) == image_complete and len(image_complete) == 28
        assert [i for i,matching in enumerate(image_known) if image_edge in matching] == containing
        clause = tuple(sorted([-edge_ids[image_edge]]+[-s-1 for s in image_others]))
        assert len(clause) == len(set(clause)) == 7
        assert set(image_others)|set(image_edge) == set(image_local)
        common = set.intersection(*(set(signatures[s]) for s in image_local))
        assert len(common) == 1
        center = common.pop()
        assert center < 18
        centers[center] += 1
        clause_sets.add(clause)
        images.append({'action_index':action_index,'core_vertex_transport':core_map,
                       'signature_transport':action,'local_signature_image':image_local,
                       'common_core_point':center,'forbidden_edge_image':list(image_edge),
                       'six_other_selectors':image_others,'negative_clause':list(clause),
                       'complete_image_matching_count':28,
                       'matching_image_coverage_sha256':hashlib.sha256(canonical(image_known)).hexdigest(),
                       'checked_cover_case_indices':containing})
    assert len(stabilizer) == 1 and len(clause_sets) == len(images) == 144
    assert centers == Counter({i:8 for i in range(18)})
    # Distinct clauses of the same length cannot subsume one another.
    assert all(len(clause) == 7 for clause in clause_sets)
    return {'status':'complete28-matching outcome cover and144 exact conditional-edge clause transports',
            'source_sha256':digest(Path(__file__)), 'universe_source_sha256':digest(Path(universe.__file__)),
            'incidence_source_sha256':digest(Path(incidence.__file__)), 'base_domain_sha256':domain_hash,
            'sweep_manifest_sha256':digest(SWEEP/'manifest.json'),'sweep_progress_sha256':digest(SWEEP/'progress.json'),
            'complete_index_sha256':digest(index_path),'proof_dependencies':dependencies,
            'local_signatures':local,'Q_pairs_by_equal_S_label':[list(pair) for pair in q_pairs],
            'matching_profiles':profiles,'verified_cases':[0,1,3,8,21],'UNKNOWN_cases':[i for i in range(28) if outcomes[i]=='UNKNOWN'],
            'whole_local_set_excluded':False,'whole_complementary_core_excluded':False,
            'conditional_forbidden_edge':list(target),'edge_variable':edge_ids[target],
            'edge_cover_cases':containing,'endpoint_activation_valid_assignments_checked':activation_controls,
            'base_negative_clause':base_clause,'local_set_stabilizer_action_indices':stabilizer,
            'exported_clause_primary_variable_count':len(signatures)+len(edge_list),
            'transported_clauses':images,'distinct_nonsubsumed_clause_count':144,
            'clauses_per_R_or_S_core_point':[[i,centers[i]] for i in range(18)],
            'semantic_irredundancy_claimed':False,'old_weak_joint_CNF_entailment_claimed':False,
            'scope':'necessary actual-graph clauses from checked local core exclusions and complete matching coverage',
            'solver_called':False,'proof_dependencies_rechecked_by_this_function':False}


def verify_proofs(certificate, checker, directory):
    assert not directory.exists()
    directory.mkdir(parents=True)
    reports = []
    for dependency in certificate['proof_dependencies']:
        if dependency['outcome'] != 'verified UNSAT':
            continue
        output = directory/f"case{dependency['index']:04d}-replay.json"
        report = incidence.replay(ROOT/dependency['model'],ROOT/dependency['result'],checker,60,output)
        assert report['excluded_indexed_core'] == dependency['index']
        reports.append({'index':dependency['index'],'report':incidence.portable(output),'sha256':digest(output)})
    summary = {'status':'all five retained proof dependencies cold-rebuilt and DRAT rechecked',
               'certificate_source_sha256':digest(Path(__file__)),'cases':reports,'new_solver_queries':0}
    (directory/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate',type=Path,required=True)
    parser.add_argument('--replay',action='store_true')
    parser.add_argument('--clauses',type=Path)
    parser.add_argument('--verify-proofs',type=Path)
    parser.add_argument('--drat-trim',type=Path,default=Path('/tmp/conway99-drat-trim/drat-trim'))
    args = parser.parse_args()
    actual = result()
    if args.replay:
        assert json.loads(args.certificate.read_text()) == actual
    else:
        assert not args.certificate.exists()
        args.certificate.write_text(json.dumps(actual,indent=2)+'\n')
    if args.clauses:
        clauses = sorted({tuple(item['negative_clause']) for item in actual['transported_clauses']})
        expected = f"p cnf {actual['exported_clause_primary_variable_count']} {len(clauses)}\n"
        expected += ''.join(' '.join(map(str,clause))+' 0\n' for clause in clauses)
        if args.replay:
            assert args.clauses.read_text() == expected
        else:
            assert not args.clauses.exists()
            args.clauses.write_text(expected)
    if args.verify_proofs:
        verify_proofs(actual,args.drat_trim.resolve(),args.verify_proofs.resolve())
    print(json.dumps({'status':actual['status'],'verified_cases':actual['verified_cases'],
                      'UNKNOWN_count':len(actual['UNKNOWN_cases']), 'forbidden_edge':actual['conditional_forbidden_edge'],
                      'edge_cover_cases':actual['edge_cover_cases'],'base_clause':actual['base_negative_clause'],
                      'local_set_stabilizer':actual['local_set_stabilizer_action_indices'],
                      'transported_distinct_clauses':actual['distinct_nonsubsumed_clause_count'],
                      'proof_dependencies_rechecked':bool(args.verify_proofs)},indent=2),flush=True)
