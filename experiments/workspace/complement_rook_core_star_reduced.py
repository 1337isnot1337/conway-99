"""Remove proved-redundant counters from the frozen one-point stars.

Degree11 follows from the27 exact mixed rows and activation. Population72
follows from the Gram diagonals. This program deletes only their counter
clauses, compacts the remaining counters, and transports the old proofs
when every retained input survives. It makes no SAT query.
"""

import argparse
from bisect import bisect_right
import hashlib
import json
from pathlib import Path
import subprocess
import tempfile

from pysat.formula import CNF

import complement_rook_core_star_oracle as parent
from complement_rook_incidence_master import ROOT, clauses, digest
from complement_rook_joint_split import check_base
from complement_rook_projector_schur import actions


LOGS = ROOT/'experiments/logs/grids-and-triangles'
PARENT_DIRECTORY = LOGS/'complement-rook-core-star-preparation'
PRIMARY_MAX = parent.PRIMARY_MAX


def read_parent_models():
    result = []
    for name in ('R8', 'R3'):
        path = PARENT_DIRECTORY/f'{name}-model.json'
        model = json.loads(path.read_text())
        assert model['name'] == name and model['core_points'] == [int(name[1:])]
        assert model['source_hashes']['complement_rook_core_star_oracle.py'] == digest(Path(parent.__file__))
        for source, expected in model['source_hashes'].items():
            assert digest(Path(__file__).with_name(source)) == expected
        result.append((path, model))
    return result


def obtain_full_formulas(models):
    if all(Path(model['cnf']).is_file() for _, model in models):
        result = []
        for _, model in models:
            path = Path(model['cnf'])
            assert digest(path) == model['cnf_sha256']
            result.append(CNF(from_file=str(path)))
        return result, False
    # The large old caches are optional. Regenerate the exact star formulas
    # from the immutable parent; its all-R control binds the full baseline.
    _, _, stars, _, _, _ = parent.catalogue_and_prepare()
    result = [star.cnf for star in stars]
    with tempfile.TemporaryDirectory(prefix='rook-star-parent-rebuild-') as temporary:
        for index, (cnf, (_, model)) in enumerate(zip(result, models)):
            path = Path(temporary)/f'{index}.cnf'
            cnf.to_file(path)
            assert digest(path) == model['cnf_sha256']
    return result, True


def identities(model):
    base, rows, gram, triples, signatures, needs, variables = check_base(ROOT/model['base_manifest'], require_cnf=False)
    assert base['domain_sha256'] == model['base_domain_sha256']
    assert all(len(sites) == 3 for sites in signatures)
    assert [gram[i][i] for i in range(27)] == [8]*27
    assert all(row.bit_count() == 6 for row in rows)
    sources = set(model['candidate_sources'])
    point, = model['core_points']
    assert sources == {s for s, sites in enumerate(signatures) if point in sites}
    edges = {edge: variable for edge, variable in variables.items()
             if edge[0] in sources or edge[1] in sources}
    assert [{'signatures': list(edge), 'variable': variable} for edge, variable in edges.items()] == model['retained_edges']
    assert all(sum(needs[source][:27]) == 33 and needs[source][27] == 11 for source in sources)
    assert len(sources) == 28
    algebra = {'signature_weight': 3, 'Gram_diagonal': [8]*27,
            'population_from_Gram': sum(gram[i][i] for i in range(27))//3,
            'core_degrees': [6]*27, 'selected_star_sources': 8,
            'mixed_demand_sums_by_candidate_source': [[source, sum(needs[source][:27])] for source in sorted(sources)],
            'degree_from_mixed_sum': 11,
            'conditional_reason': 'source selected: sum27 mixed equations; source absent: all incident edges zero by activation',
            'counter_extension_reason': 'omitted cardinality equations follow on primary variables, so their sequential-counter auxiliaries can be supplied'}
    return algebra, (rows, triples, signatures, needs, variables)


def reduce_formula(model, full):
    assert (full.nv, len(full.clauses)) == (model['variables_including_unused_primary_id_gaps'], model['clauses'])
    mapping = list(range(full.nv+1))
    family = [None]*(full.nv+1)
    top = PRIMARY_MAX
    intervals, omitted = [], []
    for entry in model['counter_interval_map']:
        width = entry['old_last']-entry['old_first']+1
        first, last = entry['new_first'], entry['new_first']+width-1
        tag = entry['tag']
        is_population = tag == 'population'
        is_degree = tag.startswith('row:') and int(tag.rsplit(':', 1)[1]) == 27
        if is_population or is_degree:
            label = 'population' if is_population else 'degree'
            omitted.append({'tag': tag, 'first': first, 'last': last, 'family': label})
            for variable in range(first, last+1):
                mapping[variable] = 0
                family[variable] = label
        else:
            new_first = top+1
            top += width
            intervals.append({'tag': tag, 'old_first': first, 'old_last': last, 'new_first': new_first})
            for variable in range(first, last+1):
                mapping[variable] = new_first+variable-first
                family[variable] = 'retained'
    assert len(omitted) == 29 and sum(entry['family'] == 'degree' for entry in omitted) == 28
    assert all(label is not None for label in family[PRIMARY_MAX+1:])
    reduced = CNF()
    removed = {'population': 0, 'degree': 0}
    for clause in full.clauses:
        dropped = {family[abs(literal)] for literal in clause if mapping[abs(literal)] == 0}
        if dropped:
            assert len(dropped) == 1
            label, = dropped
            assert label in removed
            assert all(abs(literal) <= PRIMARY_MAX or family[abs(literal)] == label for literal in clause)
            removed[label] += 1
        else:
            reduced.append([mapping[abs(literal)] if literal > 0 else -mapping[abs(literal)] for literal in clause])
    assert removed == {label: model['clause_counts'][label] for label in removed}
    assert reduced.nv == top
    assert len(reduced.clauses) == len(full.clauses)-sum(removed.values())
    result = {'variables_including_unused_primary_id_gaps': top, 'clauses': len(reduced.clauses),
              'retained_edge_count': model['retained_edge_count'], 'selector_variables': 252,
              'primary_variable_numbers_unchanged': True, 'unused_primary_id_gaps': model['unused_primary_id_gaps'],
              'omitted_counter_blocks': omitted, 'removed_clause_counts': removed,
              'remaining_counter_interval_map': intervals,
              'primary_solution_equivalence_to_parent_star': True,
              'equivalence_to_full_joint_projection_claimed': False}
    return reduced, mapping, result


def transport_old_star_proof(model, reduced, mapping, directory, checker):
    old = model['transported_old_proof']
    for path_key, hash_key in (('retained_cnf', 'retained_cnf_sha256'),
                               ('retained_proof', 'retained_proof_sha256')):
        assert digest(ROOT/old[path_key]) == old[hash_key]
    available = {tuple(sorted(clause)) for clause in reduced.clauses}
    available.update((unit,) for unit in old['units'])
    extra = {}
    top = reduced.nv

    def move(literal, proof_only=False):
        nonlocal top
        variable = abs(literal)
        moved = mapping[variable] if variable < len(mapping) else 0
        if not moved:
            assert proof_only, 'An old input clause uses an omitted counter; it cannot be silently transported.'
            if variable not in extra:
                top += 1
                extra[variable] = top
            moved = extra[variable]
        return moved if literal > 0 else -moved

    inputs = []
    for clause in clauses(ROOT/old['retained_cnf']):
        moved = [move(literal) for literal in clause]
        assert tuple(sorted(moved)) in available
        inputs.append(moved)
    lines = []
    proof_variables = set()
    for line in (ROOT/old['retained_proof']).read_text().splitlines():
        tokens = line.split()
        assert tokens and tokens[-1] == '0'
        deletion = tokens[0] == 'd'
        values = [int(token) for token in tokens[int(deletion):-1]]
        proof_variables.update(map(abs, values))
        moved = [move(literal, True) for literal in values]
        lines.append(('d ' if deletion else '')+' '.join(map(str, moved))+(' ' if moved else '')+'0')
    images = [move(variable, True) for variable in proof_variables]
    assert len(set(images)) == len(images) and lines[-1] == '0'
    retained = directory/f'{model["name"]}-retained.cnf'
    proof = directory/f'{model["name"]}-retained.drat'
    log = directory/f'{model["name"]}-drat.log'
    cnf = CNF(from_clauses=inputs)
    cnf.nv = max(cnf.nv, top)
    cnf.to_file(retained)
    proof.write_text('\n'.join(lines)+'\n')
    checked = subprocess.run([str(checker), str(retained), str(proof), '-t', '30', '-w'],
                             capture_output=True, text=True, timeout=35, check=False)
    log.write_text(checked.stdout+checked.stderr)
    assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
    return {'status': 'old proof inputs survive the redundant-counter deletion; renamed proof DRAT verified',
            'units': old['units'], 'retained_cnf': parent.portable(retained), 'retained_cnf_sha256': digest(retained),
            'retained_proof': parent.portable(proof), 'retained_proof_sha256': digest(proof),
            'log': parent.portable(log), 'retained_input_clauses': len(inputs), 'retained_proof_lines': len(lines),
            'proof_only_extra_variable_map': [[a, b] for a, b in sorted(extra.items())],
            'omitted_input_clauses_substituted': 0,
            'all_retained_inputs_in_reduced_star_plus_units': True, 'new_SAT_solver_called': False}


def core_transports(domain, canonical_point=8):
    rows, triples, signatures, needs, variables = domain
    group = actions(rows, triples)
    families = [frozenset(s for s, sites in enumerate(signatures) if i in sites) for i in range(27)]
    reverse = {family: i for i, family in enumerate(families)}
    core_actions = []
    for action in group:
        assert sorted(action) == list(range(252))
        core = [reverse[frozenset(action[s] for s in family)] for family in families]
        assert sorted(core) == list(range(27))
        assert all({core[i] for i in sites} == set(signatures[action[s]]) for s, sites in enumerate(signatures))
        assert all(((rows[i] >> j) & 1) == ((rows[core[i]] >> core[j]) & 1) for i in range(27) for j in range(27))
        core_actions.append(core)
    source_family = families[canonical_point]
    source_edges = {edge for edge in variables if edge[0] in source_family or edge[1] in source_family}
    result = []
    for target in range(18):
        index = next(i for i, core in enumerate(core_actions) if core[canonical_point] == target)
        action, core = group[index], core_actions[index]
        inverse = [None]*252
        for s, image in enumerate(action):
            inverse[image] = s
        target_edges = {edge for edge in variables if edge[0] in families[target] or edge[1] in families[target]}
        assert {tuple(sorted((action[a], action[b]))) for a, b in source_edges} == target_edges
        assert all(needs[action[s]][core[i]] == needs[s][i] for s in range(252) for i in range(27))
        result.append({'target_core_point': target, 'target_label': f'{"RS"[target//9]}{target%9}',
                       'action_index': index, 'core_image': core, 'signature_image': action,
                       'inverse_signature_image': inverse,
                       'transported_star_edge_count': len(target_edges)})
    tip_sources = families[18]
    tip_edges = {edge for edge in variables if edge[0] in tip_sources or edge[1] in tip_sources}
    return {'canonical_core_point': canonical_point, 'canonical_label': f'R{canonical_point}',
            'covered_core_points': list(range(18)), 'transports': result,
            'master_use': 'map a design through the inverse signature action before a canonical-star query; map a certified cut back through the forward action',
            'graph_automorphism_assumption': False,
            'tip_star_domain_only': {'canonical_core_point': 18, 'label': 'T0',
                                    'candidate_signatures': len(tip_sources), 'eligible_incident_edges': len(tip_edges),
                                    'CNF_built': False, 'solver_called': False}}


def build(directory, cache, checker, replay=False):
    models = read_parent_models()
    full_formulas, parent_rebuilt = obtain_full_formulas(models)
    expected = None
    if replay:
        expected = json.loads((directory/'preparation.json').read_text())
        assert expected['source_sha256'] == digest(Path(__file__))
        work = Path(tempfile.mkdtemp(prefix='rook-star-reduced-replay-'))
        cache_work = work
    else:
        assert not directory.exists() and not cache.exists()
        directory.mkdir(parents=True)
        cache.mkdir(parents=True)
        work, cache_work = directory, cache
    records = []
    for (parent_path, model), full in zip(models, full_formulas):
        algebra, domain = identities(model)
        reduced, mapping, reduction = reduce_formula(model, full)
        path = cache_work/f'{model["name"]}.cnf'
        reduced.to_file(path)
        proof = transport_old_star_proof(model, reduced, mapping, work, checker)
        record = {**reduction, 'name': model['name'],
                  'source_sha256': digest(Path(__file__)), 'parent_model': parent.portable(parent_path),
                  'parent_model_sha256': digest(parent_path), 'parent_cnf_sha256': model['cnf_sha256'],
                  'base_domain_sha256': model['base_domain_sha256'],
                  'cnf': str(path.resolve()), 'cnf_sha256': digest(path),
                  'identities': algebra, 'transported_old_proof': proof}
        if replay:
            old_path = ROOT/next(item['path'] for item in expected['models'] if item['name'] == model['name'])
            old = json.loads(old_path.read_text())
            assert digest(old_path) == next(item['sha256'] for item in expected['models'] if item['name'] == model['name'])
            assert {k: v for k, v in old.items() if k not in ('cnf', 'transported_old_proof')} == {
                k: v for k, v in record.items() if k not in ('cnf', 'transported_old_proof')}
            assert {k: v for k, v in old['transported_old_proof'].items() if k not in ('retained_cnf', 'retained_proof', 'log')} == {
                k: v for k, v in proof.items() if k not in ('retained_cnf', 'retained_proof', 'log')}
        else:
            out = directory/f'{model["name"]}-model.json'
            out.write_text(json.dumps(record, indent=2)+'\n')
            records.append({'name': model['name'], 'path': parent.portable(out), 'sha256': digest(out),
                            **{key: record[key] for key in ('variables_including_unused_primary_id_gaps', 'clauses', 'cnf_sha256')}})
    transports = core_transports(domain)
    if replay:
        assert transports == expected['core_transports']
        result = {'status': 'reduced star identities, exact counter deletion, proof transport, and18 core actions replayed',
                  'parent_formulas_rebuilt_from_source': parent_rebuilt, 'new_SAT_solver_called': False}
    else:
        result = {'status': 'reduced stars prepared; primary-equivalent to frozen stars; no new SAT query',
                  'source_sha256': digest(Path(__file__)), 'models': records,
                  'core_transports': transports, 'parent_formulas_rebuilt_from_source': parent_rebuilt,
                  'new_SAT_solver_called': False, 'whole_core_exclusion': False}
        (directory/'preparation.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'core_transports'}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--directory', type=Path, required=True)
    parser.add_argument('--cache-directory', type=Path, required=True)
    parser.add_argument('--drat-trim', type=Path, required=True)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    build(args.directory.resolve(), args.cache_directory.resolve(), args.drat_trim.resolve(), args.replay)
