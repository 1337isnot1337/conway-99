"""Six checked local cores cover three edges and one two-edge pattern.

All28 admitted local matchings are enumerated independently. The four
patterns are transported under all144 explicit core relabelings; endpoint
activation removes redundant selectors. The resulting clauses are necessary
for actual graphs, not claimed consequences of the older weak joint CNF.
Existing certificates are immutable dependencies. No solver is called.
"""

import argparse
from collections import Counter
import json
from pathlib import Path

import complement_rook_35core_matching_cover as previous
import complement_rook_35core_case0002_original_certificate as case2


ROOT, LOGS = previous.ROOT, previous.LOGS
incidence, universe = previous.incidence, previous.universe
digest, canonical = previous.digest, previous.canonical
VERIFIED = [0, 1, 2, 3, 8, 21]
PATTERNS = [([(0, 2)], [0, 1]), ([(1, 2)], [8, 21]),
            ([(4, 6)], [0, 1, 8, 21]), ([(0, 4), (1, 5)], [2, 3])]


def dependencies():
    _, old, outcomes = previous.proof_dependencies()
    result = [item for item in old if item['outcome'] == 'verified UNSAT']
    replay_path = LOGS/'complement-rook-35core-case0002-original-only-replay.json'
    replay = json.loads(replay_path.read_text())
    assert replay['status'] == 'PASS: cold original case2 formula rebuilt, all retained inputs included, DRAT verified'
    assert replay['source_sha256'] == digest(Path(case2.__file__))
    assert replay['original_model_sha256'] == case2.BASE_MODEL_SHA == digest(case2.BASE_MODEL)
    assert replay['discovery_result_sha256'] == case2.RESULT_SHA == digest(case2.RESULT)
    assert replay['all_retained_inputs_are_original_formula_clauses']
    assert not replay['additional_spectral_or_downdate_premises_required']
    for key in ('retained_cnf', 'retained_proof', 'checker_log'):
        assert digest(ROOT/replay[key]) == replay[key+'_sha256']
    result.append({'index': 2, 'kind': 'original-only retained proof',
                   'model': incidence.portable(case2.BASE_MODEL), 'model_sha256': case2.BASE_MODEL_SHA,
                   'original_only_replay': incidence.portable(replay_path), 'original_only_replay_sha256': digest(replay_path),
                   'original_cnf_sha256': replay['original_cnf_sha256'],
                   'retained_cnf': replay['retained_cnf'], 'retained_cnf_sha256': replay['retained_cnf_sha256'],
                   'retained_proof': replay['retained_proof'], 'retained_proof_sha256': replay['retained_proof_sha256'],
                   'outcome': 'verified UNSAT'})
    result.sort(key=lambda item: item['index'])
    assert [item['index'] for item in result] == VERIFIED
    return result


def core_rows(rows, signatures, local, matching):
    result = list(rows)+[0]*8
    position = {source: 27+i for i, source in enumerate(local)}
    for source, vertex in position.items():
        for point in signatures[source]:
            result[vertex] |= 1 << point
            result[point] |= 1 << vertex
    for a, b in matching:
        result[position[a]] |= 1 << position[b]
        result[position[b]] |= 1 << position[a]
    return result


def activation_control(pattern):
    endpoints = {v for edge in pattern for v in edge}
    count = 0
    for mask in range(1 << (8+len(pattern))):
        selected = [bool(mask >> i & 1) for i in range(8)]
        active = [bool(mask >> (8+i) & 1) for i in range(len(pattern))]
        if any(active[e] and not(selected[a] and selected[b]) for e, (a, b) in enumerate(pattern)):
            continue
        full = not(all(active) and all(selected))
        reduced = not(all(active) and all(selected[i] for i in range(8) if i not in endpoints))
        assert full == reduced
        count += 1
    assert count == (320 if len(pattern) == 1 else 400)
    return count


def result():
    proof_dependencies = dependencies()
    rows, _, triples, signatures, _, edge_list, domain_hash = universe.domain()
    edges = set(edge_list)
    edge_ids = {edge: 253+i for i, edge in enumerate(edge_list)}
    index_path = incidence.PREFIX/'all-core-index.json'
    index = json.loads(index_path.read_text())
    assert index['base_domain_sha256'] == domain_hash
    cases = index['cases'][:28]
    assert [c['index'] for c in cases] == list(range(28))
    local = cases[0]['selected_signatures']
    assert local == [0, 1, 9, 10, 18, 20, 26, 27]
    known = [tuple(sorted(tuple(sorted((local[a], local[b]))) for a, b in case['matching'])) for case in cases]
    all105 = list(previous.matchings(tuple(local)))
    complete = {m for m in all105 if all(edge in edges for edge in m)}
    assert len(all105) == 105 and len(complete) == len(set(known)) == 28 and set(known) == complete
    patterns = []
    for number, (local_edges, covered) in enumerate(PATTERNS):
        target = sorted(tuple(sorted((local[a], local[b]))) for a, b in local_edges)
        actual = [i for i, matching in enumerate(known) if set(target) <= set(matching)]
        assert actual == covered and set(covered) <= set(VERIFIED)
        endpoints = {v for edge in target for v in edge}
        others = [source for source in local if source not in endpoints]
        clause = sorted([-edge_ids[edge] for edge in target]+[-source-1 for source in others])
        patterns.append({'index': number, 'local_position_edges': [list(edge) for edge in local_edges],
                         'signature_edges': [list(edge) for edge in target], 'cover_cases': covered,
                         'remaining_selectors': others, 'edge_variables': [edge_ids[edge] for edge in target],
                         'base_negative_clause': clause,
                         'endpoint_activation_controls': activation_control(local_edges)})
    actions = universe.actions(rows, triples)
    families = [frozenset(s for s, h in enumerate(signatures) if i in h) for i in range(27)]
    family_position = {family: i for i, family in enumerate(families)}
    assert len(family_position) == 27
    originals = {i: core_rows(rows, signatures, local, known[i]) for i in VERIFIED}
    transports, raw_clauses, centers = [], [], Counter()
    for action_index, action in enumerate(actions):
        vertex_map = [family_position[frozenset(action[s] for s in family)] for family in families]
        assert sorted(vertex_map) == list(range(27))
        assert all((rows[i] >> j & 1) == (rows[vertex_map[i]] >> vertex_map[j] & 1)
                   for i in range(27) for j in range(27))
        assert all({vertex_map[i] for i in signatures[s]} == set(signatures[action[s]]) for s in range(252))
        image_local = sorted(action[s] for s in local)
        image_position = {s: 27+i for i, s in enumerate(image_local)}
        full_map = vertex_map+[image_position[action[s]] for s in local]
        images = [tuple(sorted(tuple(sorted((action[a], action[b]))) for a, b in matching)) for matching in known]
        image_complete = {m for m in previous.matchings(tuple(image_local)) if all(edge in edges for edge in m)}
        assert len(image_complete) == 28 and set(images) == image_complete
        for case_index in VERIFIED:
            target = core_rows(rows, signatures, image_local, images[case_index])
            assert all((originals[case_index][i] >> j & 1) == (target[full_map[i]] >> full_map[j] & 1)
                       for i in range(35) for j in range(35))
        common = set.intersection(*(set(signatures[s]) for s in image_local))
        assert len(common) == 1
        center = common.pop()
        assert center < 18
        centers[center] += 1
        image_patterns = []
        for pattern in patterns:
            target = sorted(tuple(sorted((action[a], action[b]))) for a, b in pattern['signature_edges'])
            actual_cover = [i for i, matching in enumerate(images) if set(target) <= set(matching)]
            assert actual_cover == pattern['cover_cases']
            others = sorted(action[s] for s in pattern['remaining_selectors'])
            assert set(others) | {v for edge in target for v in edge} == set(image_local)
            clause = tuple(sorted([-edge_ids[edge] for edge in target]+[-s-1 for s in others]))
            assert len(clause) == len(set(clause)) == (7 if len(target) == 1 else 6)
            raw_clauses.append(clause)
            image_patterns.append({'pattern_index': pattern['index'], 'signature_edges': [list(edge) for edge in target],
                                   'remaining_selectors': others, 'negative_clause': list(clause),
                                   'checked_cover_cases': actual_cover})
        transports.append({'action_index': action_index, 'core_vertex_transport': vertex_map,
                           'full35_vertex_transport': full_map, 'signature_transport': action,
                           'local_signature_image': image_local, 'common_core_point': center,
                           'complete_image_matching_count': 28,
                           'matching_image_coverage_sha256': universe.hashlib.sha256(canonical(images)).hexdigest(),
                           'checked_full35_core_transports': VERIFIED, 'patterns': image_patterns})
    assert len(transports) == 144 and centers == Counter({i: 8 for i in range(18)})
    unique = sorted(set(raw_clauses), key=lambda clause: (len(clause), clause))
    retained, discarded = [], []
    for clause in unique:
        smaller = next((old for old in retained if set(old) <= set(clause)), None)
        if smaller is None:
            retained.append(clause)
        else:
            discarded.append({'clause': list(clause), 'subsuming_clause': list(smaller)})
    assert len(raw_clauses) == len(unique) == len(retained) == 576 and not discarded
    assert Counter(map(len, retained)) == Counter({6: 144, 7: 432})
    return {'status': 'exact six-case cover of four patterns and all144 core transports',
            'source_sha256': digest(Path(__file__)),
            'source_dependencies': {Path(module.__file__).name: digest(Path(module.__file__))
                                    for module in (previous, case2, incidence, universe)},
            'base_domain_sha256': domain_hash, 'complete_index_sha256': digest(index_path),
            'proof_dependencies': proof_dependencies, 'verified_case_indices': VERIFIED,
            'local_signatures': local, 'all105_matchings_checked': True,
            'all28_admitted_matchings': [[list(edge) for edge in matching] for matching in known],
            'patterns': patterns, 'transports': transports,
            'raw_clause_count': len(raw_clauses), 'distinct_clause_count': len(unique),
            'subsumption_discarded_clauses': discarded, 'exported_clause_count': len(retained),
            'exported_clause_lengths': {'6': 144, '7': 432},
            'exported_clauses': [list(clause) for clause in retained],
            'exported_primary_variable_count': len(signatures)+len(edge_list),
            'full35_core_adjacency_transport_checks': len(transports)*len(VERIFIED)*35*35,
            'scope': {'necessary_for_actual_graphs': True, 'whole_local_set_excluded': False,
                      'old_weak_joint_CNF_entailment_claimed': False, 'semantic_irredundancy_claimed': False,
                      'graph_automorphism_assumption': False, 'solver_called': False,
                      'proof_dependencies_rechecked_by_generation': False}}


def fragment(certificate):
    clauses = certificate['exported_clauses']
    return (f'p cnf {certificate["exported_primary_variable_count"]} {len(clauses)}\n'+
            ''.join(' '.join(map(str, clause))+' 0\n' for clause in clauses)).encode()


def verify_proofs(certificate, directory, checker):
    assert not directory.exists()
    directory.mkdir(parents=True)
    records = []
    for dep in certificate['proof_dependencies']:
        output = directory/f'case{dep["index"]:04d}-replay.json'
        if dep['index'] == 2:
            case2.replay(output, checker, 60)
        else:
            incidence.replay(ROOT/dep['model'], ROOT/dep['result'], checker, 60, output)
        records.append({'index': dep['index'], 'report': incidence.portable(output), 'sha256': digest(output)})
    summary = {'status': 'all six original-formula retained proofs cold-rebuilt and DRAT checked',
               'cases': records, 'new_solver_queries': 0}
    (directory/'summary.json').write_text(json.dumps(summary, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--clauses', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--replay', action='store_true')
    parser.add_argument('--verify-proofs', type=Path)
    parser.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    args = parser.parse_args()
    actual = result()
    raw = canonical(actual)+b'\n'
    if args.write:
        assert not args.certificate.exists() and not args.clauses.exists()
        args.certificate.write_bytes(raw)
        args.clauses.write_bytes(fragment(actual))
    else:
        assert args.certificate.read_bytes() == raw and args.clauses.read_bytes() == fragment(actual)
    if args.verify_proofs:
        verify_proofs(actual, args.verify_proofs.resolve(), args.drat_trim.resolve())
    print(json.dumps({'status': 'PASS', 'mode': 'write' if args.write else 'exact replay',
                      'certificate_sha256': digest(args.certificate), 'clauses_sha256': digest(args.clauses),
                      'proof_dependency_cases': VERIFIED, 'patterns': actual['patterns'],
                      'transport_count': 144, 'raw_clauses': 576, 'distinct_nonsubsumed_clauses': 576,
                      'clause_lengths': actual['exported_clause_lengths'],
                      'solver_called': False, 'whole_local_set_excluded': False}, indent=2), flush=True)
