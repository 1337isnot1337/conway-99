"""Prepare a separate global-prism-free overlay on four frozen root cases.

Every complete cap, anchor unit, maximum-zero side unit, and lex clause
is retained. The only additions are the34,440 certified near-axis prism
clauses. These four cases cover globally prism-free graphs; they do not
cover all graphs with a prism-free chosen root. No solver is called.
"""

import argparse
import gzip
import hashlib
import json
from pathlib import Path
import shutil

import root_full_caps as base
import root_full_caps_anchor_max_solve as old
import root_full_caps_lex as lex
import root_prism_free_structure as structure


ROOT = Path(__file__).resolve().parents[2]
SUPPORT = ('root_prism_free_overlay.py', 'root_prism_free_solve.py',
           'root_prism_free_certificate.py')
SCOPE = 'globally prism-free SRG case; not every graph with a prism-free chosen root'


def portable(path):
    path = path.resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def structure_data(path):
    record = json.loads(path.read_text())
    assert record['source_sha256'] == base.digest(Path(structure.__file__))
    assert record['root_builder_sha256'] == base.digest(Path(base.__file__))
    assert record['scope'] == 'globally prism-free SRG only; no graph or exclusion obtained'
    assert record['solver_called'] is False
    assert record['four_edge_clauses'] == 34440 and record['primary_variables'] == 3486
    labels, variables = structure.labels_and_variables()
    _, actual_labels, _, _, _, actual_variables, _ = lex.primary_domain(14)
    assert labels == actual_labels and variables == actual_variables
    clauses, counts = structure.near_axis_clauses(labels, variables)
    assert counts == record['clauses_per_root_axis']
    data = gzip.decompress((ROOT/record['clause_path']).read_bytes())
    assert base.digest(ROOT/record['clause_path']) == record['compressed_clause_cnf_sha256']
    assert structure.sha(data) == record['raw_clause_cnf_sha256']
    body = ''.join(' '.join(map(str, clause)) + ' 0\n' for clause in clauses).encode()
    assert data == b'p cnf 3486 34440\n' + body
    assert structure.sha(structure.canonical({'labels': labels, 'edges': list(variables)})) == \
        record['primary_edge_order_sha256']
    return record, clauses, body


def completed_maximum(path):
    record = json.loads(path.read_text())
    assert record['status'] == ('bounded maximum-anchor batch completed; '
                                'maximum-anchor cases 0 through 6 not tested here')
    assert [case['index'] for case in record['cases']] == [7, 8, 9, 10]
    assert all(case['status'] == 'UNKNOWN; maximum-anchor case remains open' for case in record['cases'])
    return record


def invariant_clauses(case, clauses):
    original = {tuple(clause) for clause in clauses}
    records = []
    for generator in case['generators']:
        lifted = lex.lift(tuple(case['partition']), generator['image'])
        image = lifted['edge_image']
        assert structure.sha(structure.canonical(image)) == generator['edge_image_sha256']
        moved = {tuple(sorted(-image[-literal - 1] for literal in clause)) for clause in clauses}
        assert moved == original
        records.append({'generator_image': generator['image'],
                        'edge_image_sha256': generator['edge_image_sha256'],
                        'preserved_clauses': len(moved)})
    assert len(records) == case['generator_count']
    return records


def assembled_hash(base_path, variables, clause_count, body):
    result = hashlib.sha256()
    with base_path.open('rb') as incoming:
        assert incoming.readline() == f'p cnf {variables} {clause_count}\n'.encode()
        result.update(f'p cnf {variables} {clause_count + 34440}\n'.encode())
        last = b''
        for block in iter(lambda: incoming.read(1024 * 1024), b''):
            result.update(block)
            last = block
        assert last.endswith(b'0\n')
    result.update(body)
    return result.hexdigest()


def prepare(model_paths, structure_path, previous_batch, output_directory, cache_directory):
    record, clauses, body = structure_data(structure_path)
    previous = completed_maximum(previous_batch)
    models = [old.check_bindings(path)[0] for path in model_paths]
    assert [model['case']['index'] for model in models] == [7, 8, 9, 10]
    sources = {name: base.digest(Path(__file__).with_name(name)) for name in SUPPORT}
    output_directory.mkdir(parents=True, exist_ok=True)
    cache_directory.mkdir(parents=True, exist_ok=True)
    results = []
    for path, model, prior in zip(model_paths, models, previous['cases']):
        case = model['case']
        assert prior['model_sha256'] == base.digest(path)
        index = case['index']
        output = output_directory/f'case-{index:02d}-model.json'
        cached = cache_directory/f'case-{index:02d}.cnf'
        assert not output.exists() and not cached.exists(), 'Use fresh overlay paths.'
        invariance = invariant_clauses(case, clauses)
        result = {
            'status': 'global-prism-free overlay prepared; no solve', 'scope': SCOPE,
            'case_index': index, 'partition': case['partition'],
            'previous_model': portable(path), 'previous_model_sha256': base.digest(path),
            'previous_cnf': model['cnf'], 'previous_cnf_sha256': model['cnf_sha256'],
            'previous_variables': model['variables'], 'previous_clauses': model['clauses'],
            'previous_batch': portable(previous_batch), 'previous_batch_sha256': base.digest(previous_batch),
            'structure_certificate': portable(structure_path),
            'structure_certificate_sha256': base.digest(structure_path),
            'structure_source_sha256': record['source_sha256'],
            'raw_overlay_sha256': record['raw_clause_cnf_sha256'],
            'primary_edge_order_sha256': record['primary_edge_order_sha256'],
            'new_clauses': 34440, 'new_variables': 0,
            'variables': model['variables'], 'clauses': model['clauses'] + 34440,
            'cnf': str(cached),
            'cnf_sha256': assembled_hash(Path(model['cnf']), model['variables'], model['clauses'], body),
            'matching_stabilizer_order': case['stabilizer_order'],
            'matching_stabilizer_generators': case['generator_count'],
            'clause_invariance': invariance, 'source_hashes': sources,
            'all_previous_complete_caps_retained': True,
            'all_previous_lex_and_anchor_clauses_retained': True,
            'minimum_partition_normalization_added': False,
            'graph_automorphism_assumptions': 0, 'solver_called': False,
            'excludes_whole_old_same_index_case': False,
        }
        base.save(output, result)
        results.append(result)
        print(json.dumps({key: result[key] for key in ('case_index', 'partition', 'variables', 'clauses',
                                                      'matching_stabilizer_generators', 'cnf_sha256')}), flush=True)
    return results


def check_bindings(path, check_cnf=False, check_previous_cnf=False):
    model = json.loads(path.read_text())
    assert model['scope'] == SCOPE
    assert model['status'] == 'global-prism-free overlay prepared; no solve'
    assert model['new_clauses'] == 34440 and model['new_variables'] == 0
    assert model['graph_automorphism_assumptions'] == 0
    assert model['all_previous_complete_caps_retained']
    assert model['all_previous_lex_and_anchor_clauses_retained']
    assert not model['minimum_partition_normalization_added']
    assert not model['excludes_whole_old_same_index_case'] and not model['solver_called']
    for name, expected in model['source_hashes'].items():
        assert base.digest(Path(__file__).with_name(name)) == expected
    previous_path = ROOT/model['previous_model']
    assert base.digest(previous_path) == model['previous_model_sha256']
    previous, analysis = old.check_bindings(previous_path, check_cnf=check_previous_cnf)
    assert previous['case']['index'] == model['case_index']
    assert previous['case']['partition'] == model['partition']
    assert previous['cnf'] == model['previous_cnf']
    assert previous['cnf_sha256'] == model['previous_cnf_sha256']
    assert previous['variables'] == model['variables'] == model['previous_variables']
    assert previous['clauses'] == model['previous_clauses'] == model['clauses'] - 34440
    previous_batch = ROOT/model['previous_batch']
    assert base.digest(previous_batch) == model['previous_batch_sha256']
    completed_maximum(previous_batch)
    structure_path = ROOT/model['structure_certificate']
    assert base.digest(structure_path) == model['structure_certificate_sha256']
    certificate, clauses, body = structure_data(structure_path)
    assert certificate['source_sha256'] == model['structure_source_sha256']
    assert certificate['raw_clause_cnf_sha256'] == model['raw_overlay_sha256']
    assert certificate['primary_edge_order_sha256'] == model['primary_edge_order_sha256']
    assert model['clause_invariance'] == invariant_clauses(previous['case'], clauses)
    if check_previous_cnf:
        assert assembled_hash(Path(previous['cnf']), model['variables'], previous['clauses'], body) == model['cnf_sha256']
    if check_cnf:
        assert base.digest(Path(model['cnf'])) == model['cnf_sha256']
    return model, previous, analysis, clauses, body


def materialize(path):
    model, previous, _, _, body = check_bindings(path, check_previous_cnf=True)
    target = Path(model['cnf'])
    assert not target.exists(), 'Do not overwrite a prepared full formula.'
    pending = target.with_name(target.name + '.pending')
    assert not pending.exists()
    with Path(previous['cnf']).open('rb') as incoming, pending.open('wb') as outgoing:
        assert incoming.readline() == f'p cnf {model["variables"]} {previous["clauses"]}\n'.encode()
        outgoing.write(f'p cnf {model["variables"]} {model["clauses"]}\n'.encode())
        shutil.copyfileobj(incoming, outgoing)
        outgoing.write(body)
    assert base.digest(pending) == model['cnf_sha256']
    pending.replace(target)
    print(json.dumps({'status': 'exact overlay formula materialized; no solve',
                      'case_index': model['case_index'], 'variables': model['variables'],
                      'clauses': model['clauses'], 'cnf_sha256': model['cnf_sha256']}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    preparation = sub.add_parser('prepare')
    preparation.add_argument('models', type=Path, nargs=4)
    preparation.add_argument('--structure', type=Path, required=True)
    preparation.add_argument('--previous-batch', type=Path, required=True)
    preparation.add_argument('--output-directory', type=Path, required=True)
    preparation.add_argument('--cache-directory', type=Path, required=True)
    build = sub.add_parser('materialize')
    build.add_argument('model', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.models, args.structure, args.previous_batch, args.output_directory, args.cache_directory)
    else:
        materialize(args.model)
