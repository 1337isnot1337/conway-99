"""Static refinement and core-automorphism closure of checked signed cuts.

No solver is called. This requires the completed full-rebuild replay
record. It removes only assumption units absent from retained input,
checks the exact primary-domain action, and exports every signed image.
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path

from complement_rook_projector_schur import ROOT, actions, domain


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_clauses(path):
    current = []
    with path.open() as source:
        for line in source:
            if not line.strip() or line.lstrip().startswith(('c', 'p')):
                continue
            for token in line.split():
                value = int(token)
                if value:
                    current.append(value)
                else:
                    yield tuple(current)
                    current = []
    assert not current


def signed_image(units, action):
    return tuple(sorted(((1 if literal > 0 else -1)*(action[abs(literal)-1]+1)
                         for literal in units), key=abs))


def contains_pattern(selected, units):
    chosen = set(selected)
    return all((literal > 0) == (abs(literal)-1 in chosen) for literal in units)


def source_type(triple):
    p, q, t = triple
    adjacent = lambda a, b: a != b and (a//3 == b//3 or a % 3 == b % 3)
    return 2-int(adjacent(p, t))-int(adjacent(q, t))


def generate(pilot_path, replay_path):
    pilot = json.loads(pilot_path.read_text())
    replay = json.loads(replay_path.read_text())
    assert pilot['status'] == 'eight-design pilot limit; no exhaustion or class exclusion'
    assert len(pilot['designs']) == len(pilot['certified_cuts']) == 8
    assert pilot['partial_SAT_visitation_blocks'] == []
    assert replay['status'] == 'all8 full baseline rebuilds, exact core-unit hashes, retained inclusions and DRAT replays PASS'
    assert len(replay['cases']) == 8
    assert replay['wrapper_sha256'] == digest(Path(__file__).with_name('complement_rook_incidence_master_certificate.py'))
    rows, gram, triples, signatures, masks, edges, domain_hash = domain()
    group = actions(rows, triples)
    edge_set = set(edges)
    families = [frozenset(s for s, sites in enumerate(signatures) if i in sites) for i in range(27)]
    family_index = {family: i for i, family in enumerate(families)}
    assert len(family_index) == 27
    needs = [[2-(rows[i] & mask).bit_count()-int(mask >> i & 1) for i in range(27)] for mask in masks]
    for action in group:
        core = [family_index[frozenset(action[s] for s in family)] for family in families]
        assert sorted(core) == list(range(27))
        assert all(((rows[i] >> j) & 1) == ((rows[core[i]] >> core[j]) & 1)
                   and gram[i][j] == gram[core[i]][core[j]] for i in range(27) for j in range(27))
        assert all({core[i] for i in sites} == set(signatures[action[s]]) for s, sites in enumerate(signatures))
        assert all(needs[action[s]][core[i]] == needs[s][i] for s in range(252) for i in range(27))
        assert {tuple(sorted((action[a], action[b]))) for a, b in edges} == edge_set
    cases = []
    originals = []
    refined = []
    clause_sources = {}
    design_orbits = {}
    all_designs = set()
    for index, (item, checked) in enumerate(zip(pilot['designs'], replay['cases'])):
        assert item['index'] == checked['case'] == index and checked['exit_code'] == 0
        certificate_path = ROOT/checked['certificate']
        assert digest(certificate_path) == checked['certificate_sha256']
        for path_key, hash_key in (('full_log', 'full_log_sha256'), ('drat_log', 'drat_log_sha256')):
            assert digest(ROOT/checked[path_key]) == checked[hash_key]
        assert 's VERIFIED' in (ROOT/checked['drat_log']).read_text()
        certificate = json.loads(certificate_path.read_text())
        assert certificate['base_domain_sha256'] == domain_hash
        assert certificate['status'] == 'explicit-core-unit proof DRAT verified; cut certified'
        retained_path = ROOT/certificate['retained_cnf']
        proof_path = ROOT/certificate['retained_proof']
        assert digest(retained_path) == certificate['retained_cnf_sha256']
        assert digest(proof_path) == certificate['retained_proof_sha256']
        retained = set(read_clauses(retained_path))
        original = tuple(certificate['core_units'])
        assert list(original) == sorted(set(original), key=abs)
        assert item['certified_cut'] == [-literal for literal in original]
        reduced = tuple(literal for literal in original if (literal,) in retained)
        dropped = [literal for literal in original if literal not in reduced]
        assert all((literal,) not in retained for literal in dropped)
        assert reduced and contains_pattern(item['selected_signatures'], reduced)
        originals.append(original)
        refined.append(reduced)
        orbit = {}
        for g, action in enumerate(group):
            image = signed_image(reduced, action)
            orbit.setdefault(image, g)
            clause_sources.setdefault(image, {'source_case': index, 'action_index': g})
        selected = item['selected_signatures']
        members = {tuple(sorted(action[s] for s in selected)) for action in group}
        canonical = min(members)
        all_designs.update(members)
        design_orbits.setdefault(canonical, []).append(index)
        literal_types = Counter((literal > 0, source_type(triples[abs(literal)-1])) for literal in reduced)
        cases.append({'case': index, 'a': item['a'],
                      'certificate': str(certificate_path.relative_to(ROOT)),
                      'certificate_sha256': digest(certificate_path),
                      'original_units': original, 'refined_units': reduced, 'dropped_unused_units': dropped,
                      'original_size': len(original), 'refined_size': len(reduced),
                      'positive_units': sum(literal > 0 for literal in reduced),
                      'negative_units': sum(literal < 0 for literal in reduced),
                      'literal_signature_type_counts': [{'positive': sign, 'type': kind, 'count': count}
                                                        for (sign, kind), count in sorted(literal_types.items())],
                      'signed_cut_orbit_size': len(orbit), 'labelled_design_orbit_size': len(members)})
    images = sorted(clause_sources, key=lambda units: (len(units), units))
    encoded = [sum(1 << (abs(literal)-1+(252 if literal < 0 else 0)) for literal in units) for units in images]
    redundant = {}
    for j, units in enumerate(images):
        for i, other in enumerate(images):
            if len(other) >= len(units):
                break
            if encoded[i] & encoded[j] == encoded[i]:
                redundant[j] = i
                break
    survivor_ids = [i for i in range(len(images)) if i not in redundant]
    survivors = [images[i] for i in survivor_ids]
    assert all(any(contains_pattern(design, units) for units in survivors) for design in all_designs)
    before = sum(any(contains_pattern(design, units) for units in originals) for design in all_designs)
    after_refinement = sum(any(contains_pattern(design, units) for units in refined) for design in all_designs)
    records = [{'index': i, 'units': units, 'clause': [-literal for literal in units],
                **clause_sources[units], 'subsumed_by_index': redundant.get(i)} for i, units in enumerate(images)]
    return {'status': 'exact signed-cut refinement and group closure verified; no new solver run',
            'source_sha256': digest(Path(__file__)),
            'domain_helper_sha256': digest(Path(__file__).with_name('complement_rook_projector_schur.py')),
            'pilot_sha256': digest(pilot_path), 'full_replay_sha256': digest(replay_path),
            'base_domain_sha256': domain_hash, 'group_order': len(group),
            'group_signature_action_sha256': hashlib.sha256(json.dumps(group, separators=(',', ':')).encode()).hexdigest(),
            'semantic_domain_checks': {'core_and_Gram_entries': 144*729, 'signatures': 144*252,
                                       'mixed_demands': 144*252*27, 'eligible_edges': 144*20934,
                                       'packing_preserved_by_signature_and_edge_transport': True},
            'auxiliary_counter_permutation_asserted': False,
            'cases': cases, 'unique_orbit_cuts': len(images),
            'strictly_subsumed_orbit_cuts': len(redundant), 'nonsubsumed_orbit_cuts': len(survivors),
            'orbit_cuts': records, 'nonsubsumed_cut_indices': survivor_ids,
            'design_orbits': [{'source_cases': indices, 'canonical_selected_signatures': canonical}
                              for canonical, indices in sorted(design_orbits.items())],
            'known_bad_labelled_designs_in_orbit_union': len(all_designs),
            'known_bad_designs_blocked_by_original_eight_cuts': before,
            'known_bad_designs_blocked_by_refined_eight_cuts': after_refinement,
            'known_bad_designs_blocked_by_closed_cuts': len(all_designs),
            'graph_automorphism_assumptions': 0, 'solver_called': False,
            'existing_pilot_modified': False, 'whole_core_exclusion': False,
            'scope': 'necessary signed patterns transported by relabeling; no master exhaustion or performance claim'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', type=Path, required=True)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = generate(args.pilot, args.replay)
    if args.write:
        args.certificate.write_text(json.dumps(result, indent=2)+'\n')
    else:
        assert json.loads(args.certificate.read_text()) == json.loads(json.dumps(result))
    summary = {key: value for key, value in result.items() if key not in ('cases', 'orbit_cuts', 'nonsubsumed_cut_indices', 'design_orbits')}
    summary['refined_core_sizes'] = [case['refined_size'] for case in result['cases']]
    summary['design_orbit_count'] = len(result['design_orbits'])
    print(json.dumps(summary, indent=2), flush=True)
