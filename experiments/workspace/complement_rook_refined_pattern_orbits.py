"""Static closure of checked incidence-refined and positive-only patterns.

No SAT query is made. Replays the previous complete core-action audit,
binds the exact implication and deletion proofs, and exports signed
selector clauses with a source pattern and transport for every image.
"""

import argparse
import hashlib
import json
from pathlib import Path

import complement_rook_a_incidence as incidence
import complement_rook_incidence_master_cut_orbits as old
from complement_rook_incidence_core_simplification import propagation


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/grids-and-triangles'


def load(name):
    path = LOGS/name
    return path, json.loads(path.read_text())


def normalized(value):
    return json.loads(json.dumps(value))


def calculate():
    old_pilot_path, old_pilot = load('complement-rook-incidence-master-pilot01.json')
    old_replay_path, _ = load('complement-rook-incidence-master-pilot01-full-replay.json')
    old_orbits_path, old_orbits = load('complement-rook-incidence-master-cut-orbits.json')
    assert normalized(old.generate(old_pilot_path, old_replay_path)) == old_orbits
    rows, _, triples, _, _, _, domain_hash = old.domain()
    group = old.actions(rows, triples)
    action_hash = hashlib.sha256(json.dumps(group, separators=(',', ':')).encode()).hexdigest()
    assert action_hash == old_orbits['group_signature_action_sha256']

    simplified_path, simplified = load('complement-rook-incidence-core-simplification.json')
    assert simplified['status'] == 'all exact propagation and remaining tiny-master implications classified'
    assert simplified['source_sha256'] == old.digest(Path(__file__).with_name('complement_rook_incidence_core_simplification.py'))
    assert simplified['pilot_sha256'] == old.digest(old_pilot_path)
    assert simplified['full_replay_sha256'] == old.digest(old_replay_path)
    simplify_log = LOGS/'complement-rook-incidence-core-simplification-replay.log'
    replayed = json.loads(simplify_log.read_text())
    assert replayed['cases'] == 8 and replayed['queries'] == 98
    assert replayed['simplified_core_sizes'] == [22, 16, 18, 29, 28, 18, 18, 18]
    assert replayed['status'] == 'exact quota derivations, all SAT implication counterexamples, and any small DRAT implications replayed'

    pilot_path, pilot = load('complement-rook-core-deletion-pilot01.json')
    replay_path, replay = load('complement-rook-core-deletion-pilot01-full-replay.json')
    assert replay['status'] == 'independent full-baseline replay PASS' and replay['exit_code'] == 0
    assert replay['pilot_result_sha256'] == old.digest(pilot_path)
    proof_path = ROOT/replay['certificate']
    assert old.digest(proof_path) == replay['certificate_sha256']
    proof = json.loads(proof_path.read_text())
    units = proof['core_units']
    assert units == pilot['final_discovery_units'] == [16, 32, 33, 44, 57, 62, 72, 74, 85, 87, 143]
    assert proof['base_domain_sha256'] == domain_hash
    assert replay['replay_result']['learned_selector_clause'] == [-literal for literal in units]
    for path_key, hash_key in (('retained_cnf', 'retained_cnf_sha256'),
                               ('retained_proof', 'retained_proof_sha256')):
        assert old.digest(ROOT/proof[path_key]) == proof[hash_key]
    assert old.digest(ROOT/replay['replay_log']) == replay['replay_log_sha256']

    sources = [{'label': f'incidence-refined-case-{case["case"]}',
                'units': case['simplified_units'], 'original_case': case['case']}
               for case in simplified['cases']]
    sources.append({'label': 'positive-only-eleven', 'units': units, 'original_case': 1})
    patterns = {}
    source_records = []
    for source_index, source in enumerate(sources):
        orbit = {}
        for action_index, action in enumerate(group):
            image = old.signed_image(source['units'], action)
            orbit.setdefault(image, action_index)
            patterns.setdefault(image, {'source_index': source_index, 'action_index': action_index})
        source_records.append({**source, 'orbit_size': len(orbit)})
    ordered = sorted(patterns, key=lambda image: (len(image), image))
    masks = [sum(1 << (abs(literal)-1+(252 if literal < 0 else 0)) for literal in image)
             for image in ordered]
    subsumed = {}
    for j, image in enumerate(ordered):
        for i, other in enumerate(ordered):
            if len(other) >= len(image):
                break
            if masks[i] & masks[j] == masks[i]:
                subsumed[j] = i
                break
    records = [{'index': i, 'units': list(image), 'clause': [-literal for literal in image],
                **patterns[image], 'subsumed_by_index': subsumed.get(i)}
               for i, image in enumerate(ordered)]
    positive_orbit = sorted({old.signed_image(units, action) for action in group})
    assert len(positive_orbit) == 144
    coverage = []
    for design in old_pilot['designs']:
        members = {tuple(sorted(action[s] for s in design['selected_signatures'])) for action in group}
        covered = sum(any(old.contains_pattern(member, image) for image in positive_orbit) for member in members)
        coverage.append({'original_case': design['index'], 'designs': len(members),
                         'blocked_by_positive_pattern_images': covered})
    assert [item['blocked_by_positive_pattern_images'] for item in coverage] == [0, 144, 0, 0, 0, 0, 0, 0]
    _, _, _, _, _, equations = incidence.domain()
    known, steps = propagation(equations, units)
    deletions = []
    for literal in units:
        remaining, _ = propagation(equations, [value for value in units if value != literal])
        deletions.append({'removed_literal': literal, 'value_forced_by_quota_propagation': remaining.get(literal)})
    assert all(item['value_forced_by_quota_propagation'] is None for item in deletions)
    dependencies = [old_pilot_path, old_replay_path, old_orbits_path, simplified_path,
                    simplify_log, pilot_path, replay_path, proof_path]
    return {'status': 'checked pattern orbit closure; no new SAT query',
            'source_sha256': old.digest(Path(__file__)),
            'dependencies': [{'path': str(path.relative_to(ROOT)), 'sha256': old.digest(path)} for path in dependencies],
            'base_domain_sha256': domain_hash, 'group_order': len(group),
            'group_signature_action_sha256': action_hash,
            'semantic_action_checks': old_orbits['semantic_domain_checks'],
            'sources': source_records, 'distinct_patterns_before_subsumption': len(records),
            'strictly_subsumed_patterns': len(subsumed),
            'nonsubsumed_patterns': len(records)-len(subsumed), 'patterns': records,
            'positive_only_orbit': [list(image) for image in positive_orbit],
            'positive_only_clauses': [[-literal for literal in image] for image in positive_orbit],
            'known_design_orbit_coverage': coverage,
            'positive_pattern_triples': [{'selector': literal, 'triple': list(triples[literal-1])} for literal in units],
            'positive_pattern_quota_derivation': {'steps': steps,
                'forced_selected': sorted(literal for literal, value in known.items() if value),
                'forced_absent': sorted(literal for literal, value in known.items() if not value)},
            'one_literal_quota_deletion_checks': deletions,
            'solver_called': False, 'auxiliary_counter_permutation_asserted': False,
            'graph_automorphism_assumptions': False, 'whole_core_exclusion': False,
            'scope': 'necessary selector clauses and static coverage of the previously checked finite designs'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--write', action='store_true')
    args = parser.parse_args()
    result = calculate()
    if args.write:
        assert not args.certificate.exists()
        args.certificate.write_text(json.dumps(result, indent=2)+'\n')
    else:
        assert normalized(result) == json.loads(args.certificate.read_text())
    print(json.dumps({key: result[key] for key in ('status', 'group_order',
                      'distinct_patterns_before_subsumption', 'strictly_subsumed_patterns',
                      'nonsubsumed_patterns', 'solver_called')}, indent=2))
