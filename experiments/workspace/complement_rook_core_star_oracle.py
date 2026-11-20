"""Prepare exact core-point-star subsystems of the frozen joint model.

Keeps every incidence selector and Gram row. Only exterior edges incident
to a specified core-point star and the equations supported by those edges
are retained. Counter variables are renamed by explicit interval maps.
No SAT solver is called. Existing proofs are transported and DRAT checked.
"""

import argparse
from bisect import bisect_right
from collections import Counter, defaultdict
import hashlib
from itertools import combinations
import json
from pathlib import Path
import subprocess

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool

from complement_rook_incidence_master import ROOT, clauses, digest
from complement_rook_incidence_master_core_inspection import smallest_core_star
from complement_rook_joint_split import check_base
from two_rook_iso_joint_integer import conditional_count


LOGS = ROOT/'experiments/logs/grids-and-triangles'
PRIMARY_MAX = 21186


def portable(path):
    path = path.resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def row_key(source, literals, quota):
    return source+1, tuple(literals), quota


class Star:
    def __init__(self, name, points, signatures, needs, variables, incident, identity_control=None):
        self.name, self.points = name, sorted(points)
        assert len(self.points) == len(set(self.points)) and all(0 <= i < 27 for i in self.points)
        self.sources = {s for s, sites in enumerate(signatures) if set(sites) & set(self.points)}
        self.edges = {edge: variable for edge, variable in variables.items()
                      if edge[0] in self.sources or edge[1] in self.sources}
        self.edge_ids = set(self.edges.values())
        self.row_keys = set()
        for source in range(252):
            targets = range(28) if source in self.sources else self.points
            for target in targets:
                literals = [variable for other, variable in incident[source]
                            if target == 27 or target in signatures[other]]
                assert set(literals) <= self.edge_ids
                self.row_keys.add(row_key(source, literals, needs[source][target]))
        self.cnf = None if identity_control else CNF()
        self.identity_control = identity_control
        self.top = PRIMARY_MAX
        self.counter_intervals = []
        self.copied_groups = set()
        self.family_groups, self.family_clauses = Counter(), Counter()
        self.clause_count = self.maximum = 0
        self.control_hash = None
        if identity_control:
            self.control_hash = hashlib.sha256(
                f'p cnf {identity_control[0]} {identity_control[1]}\n'.encode())

    def accepts(self, group):
        family = group['family']
        if family == 'activation':
            return group['edge_variable'] in self.edge_ids
        if family in ('gram', 'population'):
            return True
        if family in ('mixed', 'degree'):
            return group['key'] in self.row_keys
        assert family == 'packing'
        return set(group['edge_variables']) <= self.edge_ids

    def copy_group(self, tag, group, old_clauses, first, last):
        if not self.accepts(group):
            return
        self.copied_groups.add(tag)
        self.family_groups[group['family']] += 1
        width = max(0, last-first+1)
        new_first = self.top+1
        self.top += width
        if width:
            self.counter_intervals.append({'tag': tag, 'old_first': first, 'old_last': last,
                                           'new_first': new_first})

        def move(literal):
            variable = abs(literal)
            if variable <= PRIMARY_MAX:
                assert variable <= 252 or variable in self.edge_ids
                return literal
            assert first <= variable <= last
            moved = new_first+variable-first
            return moved if literal > 0 else -moved

        for clause in old_clauses:
            moved = [move(literal) for literal in clause]
            self.clause_count += 1
            self.maximum = max(self.maximum, max(map(abs, moved)))
            self.family_clauses[group['family']] += 1
            if self.cnf is None:
                assert moved == clause
                self.control_hash.update((' '.join(map(str, moved))+' 0\n').encode())
            else:
                self.cnf.append(moved)

    def summary(self):
        assert self.maximum == self.top
        return {'name': self.name, 'core_points': self.points,
                'core_point_labels': [f'{"RST"[i//9]}{i%9}' for i in self.points],
                'candidate_sources': sorted(self.sources), 'candidate_source_count': len(self.sources),
                'retained_edge_count': len(self.edges), 'selector_variables': 252,
                'retained_primary_variable_count': 252+len(self.edges),
                'raw_mixed_degree_rows_before_deduplication': 28*len(self.sources)+(252-len(self.sources))*len(self.points),
                'distinct_mixed_degree_rows': len(self.row_keys),
                'variables_including_unused_primary_id_gaps': self.top,
                'clauses': self.clause_count, 'group_counts': dict(self.family_groups),
                'clause_counts': dict(self.family_clauses),
                'primary_variable_numbers_unchanged': True,
                'unused_primary_id_gaps': 20934-len(self.edges),
                'counter_interval_map': self.counter_intervals}


def load_proofs():
    old_path = LOGS/'complement-rook-incidence-master-pilot01-full-replay.json'
    old = json.loads(old_path.read_text())
    assert old['status'] == 'all8 full baseline rebuilds, exact core-unit hashes, retained inclusions and DRAT replays PASS'
    specifications = []
    for index, points in ((4, [8]), (5, [3])):
        record = old['cases'][index]
        assert record['case'] == index and record['exit_code'] == 0
        specifications.append((f'case{index}', ROOT/record['certificate'], record['certificate_sha256'], points))
    new_path = LOGS/'complement-rook-core-deletion-pilot01-full-replay.json'
    new = json.loads(new_path.read_text())
    assert new['status'] == 'independent full-baseline replay PASS' and new['exit_code'] == 0
    specifications.append(('positive-eleven', ROOT/new['certificate'], new['certificate_sha256'], None))
    loaded = []
    for name, path, expected, points in specifications:
        assert digest(path) == expected
        certificate = json.loads(path.read_text())
        assert certificate['status'] == 'explicit-core-unit proof DRAT verified; cut certified'
        retained = ROOT/certificate['retained_cnf']
        proof = ROOT/certificate['retained_proof']
        assert digest(retained) == certificate['retained_cnf_sha256']
        assert digest(proof) == certificate['retained_proof_sha256']
        inputs = list(clauses(retained))
        assert len(inputs) == certificate['retained_input_clauses']
        loaded.append({'name': name, 'path': path, 'certificate': certificate,
                       'retained': retained, 'proof': proof, 'inputs': inputs, 'star_points': points})
    return loaded, [old_path, new_path]


def catalogue_and_prepare():
    manifest_path = LOGS/'two-rook-tip-boundary-joint-3943553752-model.json'
    base, rows, gram, triples, signatures, needs, variables = check_base(manifest_path, require_cnf=False)
    assert len(variables) == 20934 and max(variables.values()) == PRIMARY_MAX
    proofs, dependencies = load_proofs()
    assert all(item['certificate']['base_domain_sha256'] == base['domain_sha256'] for item in proofs)
    wanted = {tuple(sorted(clause)) for item in proofs for clause in item['inputs']}
    incident = [[] for _ in signatures]
    for (a, b), variable in variables.items():
        incident[a].append((b, variable))
        incident[b].append((a, variable))
    stars = [Star('R8', [8], signatures, needs, variables, incident),
             Star('R3', [3], signatures, needs, variables, incident)]
    control = Star('all-R identity control', range(9), signatures, needs, variables, incident,
                   identity_control=(base['variables'], base['clauses']))
    assert len(control.sources) == 252 and len(control.edges) == 20934
    found, details = defaultdict(set), {}
    intervals = []
    generated = maximum = 0
    hasher = hashlib.sha256(f'p cnf {base["variables"]} {base["clauses"]}\n'.encode())
    pool = IDPool(start_from=PRIMARY_MAX+1)
    z = list(range(1, 253))

    def emit(tag, group, group_clauses, previous):
        nonlocal generated, maximum
        first, last = previous+1, pool.top
        if first <= last:
            intervals.append((first, last, tag))
        for clause in group_clauses:
            assert clause
            generated += 1
            maximum = max(maximum, max(map(abs, clause)))
            hasher.update((' '.join(map(str, clause))+' 0\n').encode())
            key = tuple(sorted(clause))
            if key in wanted:
                found[key].add(tag)
                details[tag] = {key: value for key, value in group.items() if key != 'key'}
        for star in stars+[control]:
            star.copy_group(tag, group, group_clauses, first, last)

    for (a, b), variable in variables.items():
        for endpoint in (a, b):
            emit(f'activation:{variable}:{endpoint}', {'family': 'activation', 'edge_variable': variable},
                 [[-variable, z[endpoint]]], pool.top)
    assert generated == base['activation_clauses']
    seen = set()
    for i in range(27):
        for j in range(i, 27):
            literals = [z[s] for s, sites in enumerate(signatures) if i in sites and j in sites]
            key = tuple(literals), gram[i][j]
            if key in seen:
                continue
            seen.add(key)
            previous = pool.top
            encoded = CardEnc.equals(literals, gram[i][j], vpool=pool, encoding=EncType.seqcounter).clauses
            emit(f'gram:{i}:{j}', {'family': 'gram', 'core_pair': [i, j], 'quota': gram[i][j]}, encoded, previous)
    assert len(seen) == base['distinct_gram_counts']
    previous = pool.top
    encoded = CardEnc.equals(z, 72, vpool=pool, encoding=EncType.seqcounter).clauses
    emit('population', {'family': 'population', 'quota': 72}, encoded, previous)
    assert base['derived_positive_units'] == base['derived_negative_units'] == 0
    seen = set()
    for source in range(252):
        for target in range(28):
            literals = [variable for other, variable in incident[source]
                        if target == 27 or target in signatures[other]]
            key = row_key(source, literals, needs[source][target])
            if key in seen:
                continue
            seen.add(key)
            previous = pool.top
            encoded = []
            conditional_count(encoded, pool, literals, needs[source][target], z[source])
            emit(f'row:{source}:{target}',
                 {'family': 'degree' if target == 27 else 'mixed', 'source': source,
                  'core_row': None if target == 27 else target, 'quota': needs[source][target], 'key': key},
                 encoded, previous)
    assert len(seen) == base['mixed_and_degree_counts']
    neighbors = [dict(entries) for entries in incident]
    packing = set()
    for i, j in combinations(range(27), 2):
        family = [s for s, sites in enumerate(signatures) if i in sites and j in sites]
        if len(family) < 2:
            continue
        for source in range(252):
            literals = [neighbors[source][s] for s in family if s in neighbors[source]]
            packing.update(tuple(sorted((-a, -b))) for a, b in combinations(literals, 2))
    assert len(packing) == base['packing_clauses']
    inverse = {variable: edge for edge, variable in variables.items()}
    for clause in sorted(packing):
        first, second = [inverse[-literal] for literal in clause]
        source, = set(first) & set(second)
        a, = set(first)-{source}
        b, = set(second)-{source}
        emit(f'packing:{source}:{min(a,b)}:{max(a,b)}',
             {'family': 'packing', 'source': source, 'edge_variables': sorted(-literal for literal in clause)},
             [list(clause)], pool.top)
    assert (generated, maximum, pool.top) == (base['clauses'], base['variables'], base['variables'])
    assert hasher.hexdigest() == base['cnf_sha256']
    assert (control.top, control.clause_count, control.control_hash.hexdigest()) == (
        base['variables'], base['clauses'], base['cnf_sha256'])

    starts = [first for first, _, _ in intervals]
    support = []
    for item in proofs:
        unit_set = set(item['certificate']['core_units'])
        chosen, origins = {}, {}
        for clause in item['inputs']:
            key = tuple(sorted(clause))
            possible = set(found[key])
            if len(clause) == 1 and clause[0] in unit_set:
                tag = f'assumption:{clause[0]}'
                possible.add(tag)
                details[tag] = {'family': 'assumption', 'literal': clause[0]}
            assert possible
            tag = min(possible, key=lambda name: (details[name]['family'] != 'assumption', name))
            chosen[tag] = details[tag]
            origins[key] = sorted(possible)
        used_edges = {abs(literal) for clause in item['inputs'] for literal in clause
                      if 253 <= abs(literal) <= PRIMARY_MAX}
        counter_tags = set()
        for clause in item['inputs']:
            for literal in clause:
                variable = abs(literal)
                if variable <= PRIMARY_MAX:
                    continue
                position = bisect_right(starts, variable)-1
                first, last, tag = intervals[position]
                assert first <= variable <= last
                counter_tags.add(tag)
        mandatory_sources = {details[tag]['source'] for tag in counter_tags
                             if details[tag]['family'] in ('mixed', 'degree')}
        smallest = smallest_core_star(list(chosen.values()), used_edges, inverse, signatures, variables)
        support.append({'name': item['name'], 'certificate': portable(item['path']),
                        'certificate_sha256': digest(item['path']),
                        'retained_input_clauses': len(item['inputs']),
                        'group_counts': dict(Counter(group['family'] for group in chosen.values())),
                        'mandatory_mixed_counter_sources': sorted(mandatory_sources),
                        'distinct_primary_edge_variables': len(used_edges),
                        'smallest_core_point_star_for_attributed_proof': smallest,
                        'clauses_with_multiple_origins': sum(len(tags) > 1 for tags in origins.values())})
        item['origins'] = origins
    for star in stars:
        assert star.cnf.nv == star.top and len(star.cnf.clauses) == star.clause_count
        assert len(star.sources) == 28 and len(star.edges) == 4456
        assert star.family_groups['mixed']+star.family_groups['degree'] == len(star.row_keys)
    return base, manifest_path, stars, proofs, support, dependencies


def transport_proof(star, item, directory, checker):
    certificate = item['certificate']
    units = certificate['core_units']
    intervals = star.counter_intervals
    starts = [entry['old_first'] for entry in intervals]
    extra = {}
    top = star.top

    def move(literal, allow_extra=False):
        nonlocal top
        variable = abs(literal)
        if variable <= PRIMARY_MAX:
            moved = variable
        else:
            position = bisect_right(starts, variable)-1
            entry = intervals[position] if position >= 0 else None
            if entry and variable <= entry['old_last']:
                moved = entry['new_first']+variable-entry['old_first']
            else:
                assert allow_extra, f'An input counter is not in the retained subsystem: {variable}'
                if variable not in extra:
                    top += 1
                    extra[variable] = top
                moved = extra[variable]
        return moved if literal > 0 else -moved

    available = {tuple(sorted(clause)) for clause in star.cnf.clauses}
    available.update((unit,) for unit in units)
    mapped_inputs = []
    for clause in item['inputs']:
        if len(clause) == 1 and clause[0] in units:
            assert 1 <= abs(clause[0]) <= 252
        else:
            assert set(item['origins'][tuple(sorted(clause))]) & star.copied_groups
            assert all(abs(literal) <= 252 or abs(literal) > PRIMARY_MAX or abs(literal) in star.edge_ids
                       for literal in clause)
        moved = [move(literal) for literal in clause]
        assert tuple(sorted(moved)) in available
        mapped_inputs.append(moved)
    mapped_lines = []
    original_proof_variables = set()
    for line in item['proof'].read_text().splitlines():
        tokens = line.split()
        assert tokens and tokens[-1] == '0'
        deletion = tokens[0] == 'd'
        values = [int(token) for token in tokens[int(deletion):-1]]
        assert all(values)
        original_proof_variables.update(map(abs, values))
        moved = [move(literal, allow_extra=True) for literal in values]
        mapped_lines.append(('d ' if deletion else '')+' '.join(map(str, moved))+(' ' if moved else '')+'0')
    image = {variable: abs(move(variable, allow_extra=True)) for variable in original_proof_variables}
    assert len(set(image.values())) == len(image)
    assert mapped_lines[-1] == '0'
    prefix = directory/f'{item["name"]}-{star.name}'
    retained = prefix.with_name(prefix.name+'-retained.cnf')
    proof = prefix.with_name(prefix.name+'-retained.drat')
    log = prefix.with_name(prefix.name+'-drat.log')
    assert not retained.exists() and not proof.exists() and not log.exists()
    cnf = CNF(from_clauses=mapped_inputs)
    cnf.nv = max(cnf.nv, top)
    cnf.to_file(retained)
    proof.write_text('\n'.join(mapped_lines)+'\n')
    checked = subprocess.run([str(checker), str(retained), str(proof), '-t', '30', '-w'],
                             capture_output=True, text=True, timeout=35, check=False)
    log.write_text(checked.stdout+checked.stderr)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
    return {'status': 'old retained proof transported to the exact star subsystem and DRAT verified',
            'original_certificate': portable(item['path']), 'original_certificate_sha256': digest(item['path']),
            'units': units, 'retained_cnf': portable(retained), 'retained_cnf_sha256': digest(retained),
            'retained_proof': portable(proof), 'retained_proof_sha256': digest(proof),
            'log': portable(log), 'log_sha256': digest(log), 'retained_input_clauses': len(mapped_inputs),
            'mapped_proof_lines': len(mapped_lines),
            'proof_only_extra_counter_map': [[old, new] for old, new in sorted(extra.items())],
            'input_inclusion_verified_against_full_star_plus_units': True,
            'new_solver_called': False}


def prepare(output_directory, cache_directory, checker):
    assert not output_directory.exists() and not cache_directory.exists()
    output_directory.mkdir(parents=True)
    cache_directory.mkdir(parents=True)
    base, manifest_path, stars, proofs, support, dependencies = catalogue_and_prepare()
    source_files = ['complement_rook_core_star_oracle.py',
                    'complement_rook_incidence_master_core_inspection.py',
                    'complement_rook_incidence_master.py', 'complement_rook_joint_split.py',
                    'two_rook_iso_joint_integer.py']
    models = []
    for star, item in zip(stars, proofs[:2]):
        assert star.points == item['star_points']
        cnf_path = cache_directory/f'{star.name}.cnf'
        star.cnf.to_file(cnf_path)
        model = {**star.summary(), 'status': 'necessary star subsystem prepared; no new SAT query',
                 'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in source_files},
                 'base_manifest': portable(manifest_path), 'base_manifest_sha256': digest(manifest_path),
                 'base_cnf_sha256': base['cnf_sha256'], 'base_domain_sha256': base['domain_sha256'],
                 'baseline_stream_regenerated_clauses': base['clauses'],
                 'identity_full_subsystem_control': 'all nine R coordinates reproduce the full baseline byte hash',
                 'cnf': str(cnf_path.resolve()), 'cnf_sha256': digest(cnf_path),
                 'retained_edges': [{'signatures': list(edge), 'variable': variable} for edge, variable in star.edges.items()],
                 'all_gram_and_population_rows_retained': True,
                 'all_supported_packing_retained': True,
                 'graph_automorphism_assumptions': 0, 'extra_graph_constraints': 0,
                 'equivalent_to_selected_full_model_subsystem': True,
                 'equivalent_to_full_model_projection_claimed': False,
                 'SAT_is_only_a_partial_witness': True,
                 'transported_old_proof': transport_proof(star, item, output_directory, checker)}
        path = output_directory/f'{star.name}-model.json'
        path.write_text(json.dumps(model, indent=2)+'\n')
        models.append({'path': portable(path), 'sha256': digest(path),
                       **{key: model[key] for key in ('name', 'candidate_source_count', 'retained_edge_count',
                          'variables_including_unused_primary_id_gaps', 'clauses', 'group_counts', 'clause_counts')}})
    record = {'status': 'two one-core-point subsystems prepared and old proofs transported; no SAT solve',
              'source_sha256': digest(Path(__file__)),
              'base_manifest_sha256': digest(manifest_path), 'base_cnf_sha256': base['cnf_sha256'],
              'dependencies': [{'path': portable(path), 'sha256': digest(path)} for path in dependencies],
              'models': models, 'retained_proof_support': support,
              'new_SAT_solver_called': False, 'whole_core_exclusion': False,
              'scope': 'exact row-subsystem preparation and proof support; no new incidence master search'}
    path = output_directory/'preparation.json'
    path.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2), flush=True)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-directory', type=Path, required=True)
    parser.add_argument('--cache-directory', type=Path, required=True)
    parser.add_argument('--drat-trim', type=Path, required=True)
    args = parser.parse_args()
    prepare(args.output_directory.resolve(), args.cache_directory.resolve(), args.drat_trim.resolve())
