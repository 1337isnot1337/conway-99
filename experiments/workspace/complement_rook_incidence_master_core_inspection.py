"""Attribute retained pilot clauses to exact joint-model equation rows.

Regenerates the baseline as a hash-checked stream once, retaining only
origins of the eight small proof cores. No CNF file or solver is used.
Duplicate clause origins are kept; counter-variable ownership supplies
a conservative lower bound on the source rows actually used by a proof.
"""

import argparse
from collections import Counter, defaultdict
import hashlib
from functools import lru_cache
from itertools import combinations
import json
from pathlib import Path

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool

from complement_rook_incidence_master import ROOT, clauses, digest
from complement_rook_joint_split import check_base
from two_rook_iso_joint_integer import conditional_count


def smallest_core_star(groups, used_edges, inverse_edges, signatures, variables):
    """Find a smallest core-point star containing this proof attribution.

For I, include every candidate signature touching I, all edges incident
to those candidates, all their rows, and outside mixed rows targeting I.
This is a static hitting-set calculation on at most27 core coordinates.
"""
    masks = [sum(1 << i for i in sites) for sites in signatures]
    constraints = set()
    for group in groups:
        if group['family'] in ('mixed', 'degree'):
            mask = masks[group['source']]
            if group['core_row'] is not None:
                mask |= 1 << group['core_row']
            constraints.add(mask)
    for variable in used_edges:
        a, b = inverse_edges[variable]
        constraints.add(masks[a] | masks[b])
    minimal = []
    for mask in sorted(constraints, key=lambda value: (value.bit_count(), value)):
        if not any(other & mask == other for other in minimal):
            minimal.append(mask)

    @lru_cache(None)
    def search(remaining, budget):
        if not remaining:
            return ()
        if budget == 0:
            return None
        options = min(remaining, key=int.bit_count)
        while options:
            bit = options & -options
            options -= bit
            reduced = tuple(mask for mask in remaining if not mask & bit)
            tail = search(reduced, budget-1)
            if tail is not None:
                return (bit.bit_length()-1,)+tail
        return None

    for size in range(10):
        chosen = search(tuple(minimal), size)
        if chosen is not None:
            break
    assert chosen is not None and len(chosen) == size
    points = sorted(chosen)
    selected_mask = sum(1 << i for i in points)
    assert all(mask & selected_mask for mask in constraints)
    star_sources = {s for s, mask in enumerate(masks) if mask & selected_mask}
    star_edges = {variable for (a, b), variable in variables.items() if a in star_sources or b in star_sources}
    assert used_edges <= star_edges
    assert all(group['source'] in star_sources or group['core_row'] in points
               for group in groups if group['family'] in ('mixed', 'degree'))
    return {'core_points': points, 'core_point_labels': [f'{"RST"[i//9]}{i%9}' for i in points],
            'minimum_size_for_this_attribution': size, 'signature_candidates': len(star_sources),
            'eligible_incident_edges': len(star_edges),
            'raw_mixed_degree_row_requirements_before_duplicate_removal': 28*len(star_sources)+(252-len(star_sources))*len(points),
            'minimal_hitting_constraints': len(minimal), 'search_states': search.cache_info().misses,
            'all_used_edges_and_mixed_rows_contained': True,
            'scope': 'a smaller necessary submodel containing this retained proof; no new solve'}


def inspect(pilot_path, replay_path):
    pilot = json.loads(pilot_path.read_text())
    replay = json.loads(replay_path.read_text())
    assert replay['status'] == 'all8 full baseline rebuilds, exact core-unit hashes, retained inclusions and DRAT replays PASS'
    pilot_manifest = json.loads((ROOT/pilot['manifest']).read_text())
    assert digest(ROOT/pilot['manifest']) == pilot['manifest_sha256']
    base_path = ROOT/pilot_manifest['base_manifest']
    base, rows, gram, triples, signatures, needs, variables = check_base(base_path, require_cnf=False)
    retained_cases = []
    wanted = set()
    certificates = []
    for index, checked in enumerate(replay['cases']):
        assert checked['case'] == index and checked['exit_code'] == 0
        certificate_path = ROOT/checked['certificate']
        assert digest(certificate_path) == checked['certificate_sha256']
        certificate = json.loads(certificate_path.read_text())
        assert digest(ROOT/certificate['retained_cnf']) == certificate['retained_cnf_sha256']
        retained = list(clauses(ROOT/certificate['retained_cnf']))
        assert len(retained) == certificate['retained_input_clauses']
        retained_cases.append(retained)
        wanted.update(tuple(sorted(clause)) for clause in retained)
        certificates.append(certificate)
    found = defaultdict(set)
    detail = {}
    intervals = []
    current_tag = None
    generated = 0
    maximum = 0
    hasher = hashlib.sha256(f"p cnf {base['variables']} {base['clauses']}\n".encode())

    class Stream:
        def append(self, clause):
            nonlocal generated, maximum
            assert clause and current_tag is not None
            generated += 1
            maximum = max(maximum, max(map(abs, clause)))
            hasher.update((' '.join(map(str, clause))+' 0\n').encode())
            key = tuple(sorted(clause))
            if key in wanted:
                found[key].add(current_tag)

        def extend(self, new_clauses):
            for clause in new_clauses:
                self.append(clause)

    stream, pool = Stream(), IDPool()
    selected = [pool.id(('selected', s)) for s in range(252)]
    allocated = {edge: pool.id(('edge', *edge)) for edge in variables}
    assert allocated == variables
    incident = [[] for _ in signatures]
    for (a, b), variable in variables.items():
        for endpoint in (a, b):
            current_tag = f'activation:{variable}:{endpoint}'
            detail[current_tag] = {'family': 'activation', 'edge_variable': variable,
                                   'edge_endpoints': [a, b], 'selector_signature': endpoint}
            stream.append([-variable, selected[endpoint]])
        incident[a].append((b, variable))
        incident[b].append((a, variable))
    assert generated == base['activation_clauses']
    gram_seen = set()
    for i in range(27):
        for j in range(i, 27):
            literals = [selected[s] for s, sites in enumerate(signatures) if i in sites and j in sites]
            key = (tuple(literals), gram[i][j])
            if key in gram_seen:
                continue
            gram_seen.add(key)
            current_tag = f'gram:{i}:{j}'
            detail[current_tag] = {'family': 'gram', 'core_pair': [i, j], 'quota': gram[i][j],
                                   'selector_literals': literals}
            previous = pool.top
            stream.extend(CardEnc.equals(literals, gram[i][j], vpool=pool, encoding=EncType.seqcounter).clauses)
            if pool.top > previous:
                intervals.append((previous+1, pool.top, current_tag))
    assert len(gram_seen) == base['distinct_gram_counts']
    current_tag = 'population'
    detail[current_tag] = {'family': 'population', 'quota': 72}
    previous = pool.top
    stream.extend(CardEnc.equals(selected, 72, vpool=pool, encoding=EncType.seqcounter).clauses)
    intervals.append((previous+1, pool.top, current_tag))
    assert base['derived_positive_units'] == base['derived_negative_units'] == 0
    mixed_seen = set()
    for t in range(252):
        for i in range(28):
            literals = [variable for s, variable in incident[t] if i == 27 or i in signatures[s]]
            key = (selected[t], tuple(literals), needs[t][i])
            if key in mixed_seen:
                continue
            mixed_seen.add(key)
            current_tag = f'row:{t}:{i}'
            detail[current_tag] = {'family': 'degree' if i == 27 else 'mixed',
                                   'source': t, 'source_triple': triples[t],
                                   'core_row': None if i == 27 else i,
                                   'quota_if_selected': needs[t][i], 'edge_literals': literals}
            previous = pool.top
            conditional_count(stream, pool, literals, needs[t][i], selected[t])
            if pool.top > previous:
                intervals.append((previous+1, pool.top, current_tag))
    assert len(mixed_seen) == base['mixed_and_degree_counts']
    neighbor_variables = [dict(neighbors) for neighbors in incident]
    packing = set()
    for i, j in combinations(range(27), 2):
        family = [s for s, sites in enumerate(signatures) if i in sites and j in sites]
        if len(family) < 2:
            continue
        for t in range(252):
            literals = [neighbor_variables[t][s] for s in family if s in neighbor_variables[t]]
            for first, second in combinations(literals, 2):
                packing.add(tuple(sorted((-first, -second))))
    assert len(packing) == base['packing_clauses']
    inverse_edges = {variable: edge for edge, variable in variables.items()}
    for clause in sorted(packing):
        first, second = [inverse_edges[-literal] for literal in clause]
        center, = set(first) & set(second)
        a, = set(first)-{center}
        b, = set(second)-{center}
        shared = sorted(set(signatures[a]) & set(signatures[b]))
        assert len(shared) == 2
        current_tag = f'packing:{center}:{min(a,b)}:{max(a,b)}'
        if tuple(sorted(clause)) in wanted:
            detail[current_tag] = {'family': 'packing', 'source': center,
                                   'source_triple': triples[center],
                                   'neighbor_signatures': sorted((a, b)), 'shared_core_pair': shared}
        stream.append(clause)
    assert (generated, maximum, pool.top) == (base['clauses'], base['variables'], base['variables'])
    assert hasher.hexdigest() == base['cnf_sha256']
    # Exact counter ownership, independent of how a duplicate primary-only
    # clause might be attributed among its several valid occurrences.
    owner = [None]*(base['variables']+1)
    for first, last, tag in intervals:
        for variable in range(first, last+1):
            assert owner[variable] is None
            owner[variable] = tag
    cases = []
    for index, (retained, certificate) in enumerate(zip(retained_cases, certificates)):
        core_units = set(certificate['core_units'])
        origins = {}
        chosen_groups = defaultdict(list)
        all_groups = set()
        for clause in retained:
            key = tuple(sorted(clause))
            possible = set(found[key])
            if len(clause) == 1 and clause[0] in core_units:
                tag = f'assumption:{clause[0]}'
                possible.add(tag)
                detail[tag] = {'family': 'assumption', 'literal': clause[0]}
            assert possible, (index, clause)
            origins[key] = sorted(possible)
            # Prefer explicit assumption origins, then actual generator
            # order is immaterial: every chosen group contains this clause.
            chosen = min(possible, key=lambda tag: (detail[tag]['family'] != 'assumption', tag))
            chosen_groups[chosen].append(list(clause))
            all_groups.update(possible)
        used_aux = {abs(literal) for clause in retained for literal in clause if abs(literal) > 21186}
        mandatory_groups = {owner[variable] for variable in used_aux}
        assert None not in mandatory_groups
        mandatory_rows = sorted((tag for tag in mandatory_groups if detail[tag]['family'] in ('mixed', 'degree')),
                                key=lambda tag: (detail[tag]['source'], detail[tag]['core_row'] if detail[tag]['core_row'] is not None else 27))
        mandatory_sources = sorted({detail[tag]['source'] for tag in mandatory_rows})
        source_rows = defaultdict(list)
        for tag in mandatory_rows:
            source_rows[detail[tag]['source']].append(detail[tag]['core_row'])
        used_edges = {abs(literal) for clause in retained for literal in clause if 253 <= abs(literal) <= 21186}
        literal_owners = defaultdict(set)
        for tag, group_clauses in chosen_groups.items():
            if detail[tag]['family'] not in ('mixed', 'degree', 'packing'):
                continue
            for clause in group_clauses:
                for literal in clause:
                    if 253 <= abs(literal) <= 21186:
                        literal_owners[abs(literal)].add(detail[tag]['source'])
        shared_primary = [{'edge_variable': variable, 'endpoints': inverse_edges[variable], 'row_sources': sorted(sources)}
                          for variable, sources in sorted(literal_owners.items()) if len(sources) > 1]
        selected = set(certificate['selected_signatures'])
        groups = [{**detail[tag], 'tag': tag, 'retained_clauses_assigned': group_clauses}
                  for tag, group_clauses in sorted(chosen_groups.items())]
        counts = Counter(group['family'] for group in groups)
        clause_counts = Counter()
        for group in groups:
            clause_counts[group['family']] += len(group['retained_clauses_assigned'])
        local_sources = sorted({group['source'] for group in groups if group['family'] in ('mixed', 'degree', 'packing')})
        star = smallest_core_star(groups, used_edges, inverse_edges, signatures, variables)
        cases.append({'case': index, 'a': pilot['designs'][index]['a'],
                      'retained_input_clauses': len(retained), 'all_retained_clauses_attributed': True,
                      'distinct_primary_edge_variables': len(used_edges),
                      'group_counts_for_one_valid_attribution': dict(counts),
                      'clause_counts_for_one_valid_attribution': dict(clause_counts),
                      'mandatory_mixed_or_degree_counter_sources': mandatory_sources,
                      'mandatory_counter_source_count': len(mandatory_sources),
                      'mandatory_row_details': [{'source': source, 'triple': triples[source],
                                                'selected_in_original_design': source in selected,
                                                'core_rows_none_means_degree': row_indices}
                                               for source, row_indices in sorted(source_rows.items())],
                      'local_centers_in_one_valid_attribution': local_sources,
                      'smallest_core_point_star_for_attributed_proof': star,
                      'clauses_with_multiple_possible_origins': sum(len(tags) > 1 for tags in origins.values()),
                      'shared_primary_edge_variables_across_assigned_source_rows': shared_primary,
                      'groups': groups,
                      'duplicate_origins': [{'clause': list(key), 'possible_tags': tags}
                                            for key, tags in sorted(origins.items()) if len(tags) > 1]})
    return {'status': 'full baseline stream hash and all8 retained-core equation origins verified',
            'source_sha256': digest(Path(__file__)), 'pilot_sha256': digest(pilot_path),
            'full_replay_sha256': digest(replay_path), 'base_manifest_sha256': digest(base_path),
            'baseline_cnf_sha256': hasher.hexdigest(), 'baseline_clauses_regenerated_as_stream': generated,
            'baseline_variables': maximum, 'cases': cases,
            'solver_called': False, 'large_cnf_saved': False,
            'scope': 'structure of these retained proofs; no assertion that smaller-row models are feasible or infeasible'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--pilot', type=Path, required=True)
    parser.add_argument('--replay', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    result = inspect(args.pilot, args.replay)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    for case in result['cases']:
        print(json.dumps({key: value for key, value in case.items()
                          if key not in ('groups', 'duplicate_origins', 'shared_primary_edge_variables_across_assigned_source_rows')}), flush=True)
