"""Prepare the complete case4 incidence constraints in native CP-SAT form.

There are exactly 1,214 Boolean variables. No SAT counter auxiliaries,
objective, assumptions, hints, or graph symmetry constraints are added.
All 1,365 nontrivial triple capacities are retained, including the 1,353
already implied by quota-one Gram equations in the old CNF.

This module exposes preparation, cold replay, and tiny known controls.
It does not expose a production query. A later CP-SAT INFEASIBLE result
would not itself be an accepted mathematical exclusion.
"""

import argparse
from collections import Counter
import gc
import gzip
import hashlib
import importlib
from itertools import combinations
import json
from pathlib import Path
import platform
import resource
import sys
import tempfile
import time

import google.protobuf
import ortools
from ortools.sat import cp_model_pb2, sat_parameters_pb2
from ortools.sat.python import cp_model, cp_model_helper

import complement_rook_35core_incidence as original
import complement_rook_35core_case0004_coordinate_cover_overlay as overlay
import complement_rook_35core_case0004_coordinate_cover_query as inspector


ROOT, LOGS = original.ROOT, original.LOGS
digest, canonical, portable = original.digest, original.canonical, original.portable
save = overlay.base_builder.save
SCOPE = LOGS / 'complement-rook-35core-case0004-native-cpsat-scope.json'
SCOPE_SHA = '984e6c305002fe1fa6ab7d4f67e3858c2a5d17116cb479d275971794a38a1fcc'
OLD_OVERLAY = LOGS / 'complement-rook-35core-case0004-coordinate-cover-overlay-model.json'
OLD_OVERLAY_SHA = '727874f9f98f5e1fab2b85478dbf2ab347333329fceab938b0a2806ae1a86a4b'
OLD_CNF_SHA = '5a805a4e302bf2a91aa3cb4d39aeaddb4759b7f9695633de18cfb0fa6d5883a2'
COVER_BODY_SHA = '6f4ccc4623e4a7b9a40236f84f05e1a3973dd8b1d6f95a82a5ff0b66e699a24a'
DEPENDENCIES = {
    'complement_rook_35core_incidence.py': '3440d21fb9d41f6146cdf5b8ef4f61feb513da9cb10e7775f3b085863a3949cf',
    'complement_rook_35core_case0004_coordinate_cover_overlay.py': '5597089c00a15f72927f31c8b05f5a6bed1198a0d7ebc16aacaeb6cd39cb1c4a',
    'complement_rook_35core_case0004_coordinate_cover_query.py': 'eb352386f55c5a1fd6ddb9c692ad934d8eef87904c00e86122172dc1ebc1f9d8',
}
LIMITS = {
    'primary_boolean_variables': 1214,
    'native_constraints': 180804,
    'binary_proto_bytes': 80000000,
    'cover_body_bytes': 60000000,
    'preparation_stage_elapsed_seconds': 180,
    'observed_process_peak_rss_kib': 1048576,
    'tiny_control_solver_seconds_per_model': 2,
    'planned_production_solver_seconds': 60,
    'planned_production_workers': 1,
}
FAMILIES = [
    ('Gram', 630), ('original_signature', 186), ('core_triple', 1365),
    ('Gram_conflict', 30), ('uncapped_row_cut', 60), ('coordinate_cover', 178533),
]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def normalized(value):
    return json.loads(canonical(value))


def source_hashes():
    names = set(overlay.source_hashes()) | set(DEPENDENCIES) | {Path(__file__).name}
    return {name: digest(Path(__file__).with_name(name)) for name in sorted(names)}


def runtime_binding():
    """Bind the installed wrapper, native CP runtime, and proto parser."""
    assert ortools.__version__ == '9.15.6755'
    assert google.protobuf.__version__ == '6.33.6'
    package = Path(ortools.__file__).parent
    upb = importlib.import_module('google._upb._message')
    paths = [Path(sys.executable).resolve(), Path(cp_model.__file__),
             Path(cp_model_helper.__file__), Path(cp_model_pb2.__file__),
             Path(sat_parameters_pb2.__file__), Path(upb.__file__)]
    libraries = sorted((package / '.libs').glob('*.so*'))
    assert any(path.name == 'libortools.so.9' for path in libraries)
    paths += libraries
    return {
        'python_version': platform.python_version(), 'python_implementation': platform.python_implementation(),
        'ortools_version': ortools.__version__, 'protobuf_version': google.protobuf.__version__,
        'files': [{'path': str(path.resolve()), 'bytes': path.stat().st_size,
                   'sha256': digest(path)} for path in paths],
        'runtime_installed_or_modified_by_this_source': False,
    }


def check_budget(started):
    elapsed = time.monotonic() - started
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    if elapsed > LIMITS['preparation_stage_elapsed_seconds']:
        raise RuntimeError('preparation time limit reached before a complete model was accepted')
    if rss > LIMITS['observed_process_peak_rss_kib']:
        raise RuntimeError('preparation observed RSS limit exceeded')


def load_inventory():
    """Reconstruct all original rows; no old CNF or solver is built."""
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert digest(SCOPE) == SCOPE_SHA and digest(OLD_OVERLAY) == OLD_OVERLAY_SHA
    old_overlay = json.loads(OLD_OVERLAY.read_text())
    assert old_overlay['cnf_sha256'] == OLD_CNF_SHA
    assert old_overlay['source_hashes'] == overlay.source_hashes()
    base, _, row_model, cuts, no_goods = overlay.base_builder.inputs()
    data = original.load(4)
    _, _, case, record, core, gram, rows, originals, triples, masks = data
    assert case['index'] == 4 and len(masks) == 1214
    assert masks == row_model['column_masks35'] and gram == row_model['Gram']
    assert core == row_model['core_adjacency_rows']
    assert sha(canonical(record)) == base['domain_record_sha256']
    assert record['column_domain_sha256'] == base['column_domain_sha256']
    assert record['Gram_sha256'] == base['Gram_sha256']
    pairs = [(i, j) for i in range(35) for j in range(i, 35)]
    assert len(rows) == len(pairs) == 630
    gram_rows = [[i, j, gram[i][j], members] for (i, j), members in zip(pairs, rows)]
    assert all(members == sorted(set(members)) and 0 <= quota <= len(members)
               for i, j, quota, members in gram_rows)
    assert sum(bool(row[3]) for row in gram_rows) == 396
    signature_rows = [[source, members] for source, members in sorted(originals.items()) if len(members) > 1]
    assert signature_rows == base['formula']['original_signature_multiplicity_rows']
    old_triples = base['formula']['triple_capacity_coverage']
    assert len(old_triples) == 1365
    nontrivial_triples = [(key, value) for key, value in sorted(triples.items()) if len(value) > 1]
    assert len(nontrivial_triples) == len(old_triples)
    triple_rows = []
    quota_one_count = extra_count = 0
    lookup = dict(zip(pairs, rows))
    for (triple, members), old in zip(nontrivial_triples, old_triples):
        assert list(triple) == old['triple'] and len(members) == old['support']
        assert members == sorted(set(members))
        if 'implied_by_Gram_pair' in old:
            pair = tuple(old['implied_by_Gram_pair'])
            assert pair in list(combinations(triple, 2)) and gram[pair[0]][pair[1]] == 1
            assert set(members) <= set(lookup[pair])
            quota_one_count += 1
        else:
            assert base['formula']['additional_triple_rows'][old['extra_row_index']] == [list(triple), members]
            extra_count += 1
        triple_rows.append({'triple': list(triple), 'members': members, 'old_CNF_coverage': old})
    assert (quota_one_count, extra_count) == (1353, 12)
    assert len(signature_rows) == 186 and len(triple_rows) == 1365
    assert len(no_goods) == 30 and len(cuts) == 60
    for cut in cuts:
        terms, target, demand = cut['positive_terms'], cut['target_column'], cut['positive_demand']
        assert type(demand) is int and demand > 0
        assert [b for b, weight in terms] == sorted({b for b, weight in terms})
        assert all(0 <= b < 1214 and b != target and type(weight) is int and weight > 0 for b, weight in terms)
        assert demand + sum(weight for b, weight in terms) < (1 << 63)
    return {
        'case': case, 'primary_variables': 1214,
        'domain_record_sha256': base['domain_record_sha256'],
        'column_domain_sha256': base['column_domain_sha256'], 'Gram_sha256': base['Gram_sha256'],
        'original_model_sha256': overlay.base_builder.BASE_SHA,
        'original_CNF_sha256': base['cnf_sha256'], 'old_complete_overlay_CNF_sha256': OLD_CNF_SHA,
        'Gram_rows': gram_rows, 'original_signature_rows': signature_rows,
        'triple_rows': triple_rows, 'triple_rows_previously_implied_by_quota_one': quota_one_count,
        'triple_rows_explicit_in_old_CNF': extra_count,
        'Gram_conflict_clauses': no_goods, 'uncapped_integer_cuts': cuts,
        'cut_result_sha256': overlay.base_builder.exact.RESULT_SHA,
        'cut_exact_replay_sha256': overlay.base_builder.exact.REPLAY_SHA,
        'row_domain_sha256': overlay.covers.intrinsic.DOMAIN_SHA,
        'complete_cover_certificate_sha256': overlay.COVERS_SHA,
    }


def write_cover_body(path):
    """Replay every cover witness, then release the large JSON ledger."""
    assert not path.exists() and digest(overlay.COVERS) == overlay.COVERS_SHA
    certificate = json.loads(gzip.decompress(overlay.COVERS.read_bytes()))
    ledger = overlay.verify_ledger(certificate)
    hasher = hashlib.sha256()
    count = literals = size = 0
    with path.open('wb') as stream:
        for clause in overlay.covers.clause_stream(certificate):
            raw = (' '.join(map(str, clause)) + ' 0\n').encode()
            stream.write(raw)
            hasher.update(raw)
            count += 1
            literals += len(clause)
            size += len(raw)
    assert (count, literals, size) == (178533, 12887146, 53309062)
    assert hasher.hexdigest() == COVER_BODY_SHA == certificate['canonical_retained_clause_body_sha256']
    assert size <= LIMITS['cover_body_bytes']
    report = {'complete_ledger_replay': ledger, 'clauses': count, 'literal_occurrences': literals,
              'body_bytes': size, 'body_sha256': hasher.hexdigest()}
    del certificate
    gc.collect()
    return report


def cover_stream(path):
    count = literals = 0
    hasher = hashlib.sha256()
    with path.open('rb') as stream:
        for raw in stream:
            hasher.update(raw)
            values = list(map(int, raw.split()))
            assert values and values[-1] == 0 and all(values[:-1])
            clause = values[:-1]
            assert -1214 <= clause[0] < 0 and all(0 < value <= 1214 for value in clause[1:])
            assert clause[1:] == sorted(set(clause[1:])) and -clause[0] not in clause[1:]
            assert raw == (' '.join(map(str, clause)) + ' 0\n').encode()
            count += 1
            literals += len(clause)
            yield clause
    assert count == 178533 and literals == 12887146 and hasher.hexdigest() == COVER_BODY_SHA


def row_cut_terms(cut):
    return sorted([(cut['target_column'], -cut['positive_demand'])] +
                  [(b, weight) for b, weight in cut['positive_terms']])


def build_native(inventory, cover_path, checkpoint=None):
    model = cp_model.CpModel()
    variables = [model.new_bool_var(f'x{a}') for a in range(1214)]
    for i, j, quota, members in inventory['Gram_rows']:
        model.add_linear_constraint(sum(variables[a] for a in members), quota, quota)
    for source, members in inventory['original_signature_rows']:
        model.add_at_most_one(variables[a] for a in members)
    for row in inventory['triple_rows']:
        model.add_at_most_one(variables[a] for a in row['members'])
    for clause in inventory['Gram_conflict_clauses']:
        model.add_bool_or(variables[-literal-1].Not() for literal in clause)
    for cut in inventory['uncapped_integer_cuts']:
        terms = row_cut_terms(cut)
        expression = cp_model.LinearExpr.weighted_sum([variables[a] for a, weight in terms],
                                                       [weight for a, weight in terms])
        # This upper bound is automatic for Boolean inputs; the exact
        # original inequality is the lower bound, without weight capping.
        model.add_linear_constraint(expression, 0, sum(weight for a, weight in cut['positive_terms']))
    assert len(model.proto.constraints) == 2271
    for index, clause in enumerate(cover_stream(cover_path)):
        model.add_bool_or(variables[literal-1] if literal > 0 else variables[-literal-1].Not()
                          for literal in clause)
        if checkpoint and (index + 1) % 16384 == 0:
            checkpoint('adding_native_covers', {'cover_constraints': index + 1})
    assert len(model.proto.variables) == 1214 and len(model.proto.constraints) == 180804
    assert model.validate() == ''
    assert not model.proto.has_objective() and not model.proto.has_floating_point_objective()
    assert not model.proto.assumptions and not model.proto.search_strategy
    assert not model.proto.has_solution_hint() and not model.proto.has_symmetry()
    return model


def audit_binary_proto(path, inventory, cover_path):
    """Read the exported bytes with a distinct standard protobuf parser."""
    assert path.stat().st_size <= LIMITS['binary_proto_bytes']
    proto = cp_model_pb2.CpModelProto()
    raw = path.read_bytes()
    assert proto.ParseFromString(raw) == len(raw)
    assert set(field.name for field, value in proto.ListFields()) == {'variables', 'constraints'}
    assert len(proto.variables) == 1214 and len(proto.constraints) == 180804
    for a, variable in enumerate(proto.variables):
        assert variable.name == f'x{a}' and list(variable.domain) == [0, 1]
    del raw
    types, intervals = Counter(), []
    position = 0

    def consume(kind, variables=None, coefficients=None, domain=None, literals=None):
        nonlocal position
        row = proto.constraints[position]
        assert row.WhichOneof('constraint') == kind
        assert not row.enforcement_literal and not row.name
        assert set(field.name for field, value in row.ListFields()) == {kind}
        if kind == 'linear':
            assert len(row.linear.vars) == len(row.linear.coeffs)
            assert sorted(zip(row.linear.vars, row.linear.coeffs)) == sorted(zip(variables, coefficients))
            assert len(set(row.linear.vars)) == len(row.linear.vars)
            assert list(row.linear.domain) == domain
        else:
            assert list(getattr(row, kind).literals) == literals
        types[kind] += 1
        position += 1

    start = position
    for i, j, quota, members in inventory['Gram_rows']:
        if members:
            consume('linear', members, [1] * len(members), [quota, quota])
        else:
            assert quota == 0
            consume('bool_and', literals=[])
    intervals.append(['Gram', start, position])
    for family, rows in [('original_signature', [members for source, members in inventory['original_signature_rows']]),
                         ('core_triple', [row['members'] for row in inventory['triple_rows']])]:
        start = position
        for members in rows:
            consume('at_most_one', literals=members)
        intervals.append([family, start, position])
    start = position
    for clause in inventory['Gram_conflict_clauses']:
        consume('bool_or', literals=[literal for literal in clause])
    intervals.append(['Gram_conflict', start, position])
    start = position
    for cut in inventory['uncapped_integer_cuts']:
        terms = row_cut_terms(cut)
        consume('linear', [a for a, weight in terms], [weight for a, weight in terms],
                [0, sum(weight for a, weight in cut['positive_terms'])])
    intervals.append(['uncapped_row_cut', start, position])
    start = position
    for clause in cover_stream(cover_path):
        consume('bool_or', literals=[literal-1 if literal > 0 else literal for literal in clause])
    intervals.append(['coordinate_cover', start, position])
    assert position == len(proto.constraints)
    assert [(name, end-begin) for name, begin, end in intervals] == FAMILIES
    assert types == Counter({'linear': 456, 'bool_and': 234, 'at_most_one': 1551, 'bool_or': 178563})
    return {'status': 'PASS: all exported Boolean variables and every native constraint match exact inputs',
            'variables': len(proto.variables), 'constraints': position,
            'constraint_type_counts': dict(sorted(types.items())),
            'zero_based_constraint_intervals_end_exclusive': intervals,
            'all_630_Gram_positions_retained': True, 'tautological_empty_zero_Gram_rows': 234,
            'all_1365_nontrivial_triple_capacities_retained': True,
            'quota_one_implied_triples_now_explicit': 1353,
            'original_uncapped_integer_row_cuts': 60,
            'native_literal_rule': 'positive DIMACS v maps to v-1; negative DIMACS v maps to v',
            'no_extra_proto_fields_enforcement_objective_assumptions_hint_or_symmetry': True,
            'binary_proto_bytes': path.stat().st_size, 'binary_proto_sha256': digest(path)}


def tiny_answer(model):
    assert model.validate() == ''
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = LIMITS['tiny_control_solver_seconds_per_model']
    solver.parameters.num_search_workers = 1
    status = solver.solve(model)
    assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE, cp_model.INFEASIBLE)
    return status != cp_model.INFEASIBLE


def controls(output):
    """Only small truth tables and the known nine-vertex rook graph."""
    assert not output.exists()
    started = time.monotonic()
    checked = Counter()
    for family, count in [('cardinality', 5), ('weighted', 4), ('cover', 3), ('empty_guard', 1)]:
        for assignment in range(1 << count):
            model = cp_model.CpModel()
            x = [model.new_bool_var(f'x{a}') for a in range(count)]
            values = [(assignment >> a) & 1 for a in range(count)]
            model.add_linear_constraint(0, 0, 0)
            if family == 'cardinality':
                model.add_linear_constraint(sum(x), 2, 2)
                model.add_at_most_one([x[0], x[2], x[4]])
                expected = sum(values) == 2 and sum(values[a] for a in (0, 2, 4)) <= 1
            elif family == 'weighted':
                model.add_linear_constraint(-8*x[0]+2*x[1]+5*x[2]+7*x[3], 0, 14)
                expected = 2*values[1]+5*values[2]+7*values[3] >= 8*values[0]
            elif family == 'cover':
                model.add_bool_or([x[0].Not(), x[1], x[2]])
                expected = not values[0] or bool(values[1] or values[2])
            else:
                model.add_linear_constraint(-3*x[0], 0, 0)
                expected = not values[0]
            for variable, value in zip(x, values):
                model.add(variable == value)
            assert tiny_answer(model) == expected
            checked[family] += 1

    adjacent = lambda a, b: a != b and (a//3 == b//3 or a % 3 == b % 3)
    core_sites, outside = [0, 1, 3, 4, 8], [2, 5, 6, 7]
    core = [sum(1 << j for j, b in enumerate(core_sites) if adjacent(a, b)) for a in core_sites]
    gram = [[2*int(i == j)+2-(core[i] & core[j]).bit_count()-int(core[i] >> j & 1)
             for j in range(5)] for i in range(5)]
    masks = [mask for mask in range(1, 32)
             if all(not(mask >> i & 1 and mask >> j & 1) or gram[i][j] > 0
                    for i in range(5) for j in range(5))
             and all(((core[i] | (1 << i)) & mask).bit_count() <= 2 for i in range(5))]
    actual = [sum(1 << i for i, b in enumerate(core_sites) if adjacent(a, b)) for a in outside]
    selected = sorted(masks.index(mask) for mask in actual)
    assert len(actual) == len(set(actual)) == len(selected) == 4
    assert all(sum((masks[a] >> i & 1)*(masks[a] >> j & 1) for a in selected) == gram[i][j]
               for i in range(5) for j in range(5))
    for deleted in (None, min(selected)):
        model = cp_model.CpModel()
        x = [model.new_bool_var(f'x{a}') for a in range(len(masks))]
        for i in range(5):
            for j in range(i, 5):
                members = [a for a, mask in enumerate(masks) if mask >> i & 1 and mask >> j & 1]
                model.add_linear_constraint(sum(x[a] for a in members), gram[i][j], gram[i][j])
        for triple in combinations(range(5), 3):
            members = [a for a, mask in enumerate(masks) if all(mask >> i & 1 for i in triple)]
            if len(members) > 1:
                model.add_at_most_one(x[a] for a in members)
        chosen = set(selected) - ({deleted} if deleted is not None else set())
        for a, variable in enumerate(x):
            model.add(variable == int(a in chosen))
        assert tiny_answer(model) == (deleted is None)
    report = {'status': 'PASS: native cardinality/linear/clause controls and genuine rook incidence control',
              'source_hashes': source_hashes(), 'runtime_binding': runtime_binding(),
              'truth_assignments_by_family': dict(checked), 'tiny_solver_queries': sum(checked.values())+2,
              'rook9_core_sites': core_sites, 'rook9_outside_sites': outside,
              'rook9_candidate_masks': masks, 'rook9_selected_column_ids': selected,
              'rook9_all25_Gram_positions_checked': True, 'rook9_positive_control': True,
              'rook9_deleted_column_negative_control': True, 'main_case4_solver_queries': 0,
              'elapsed_seconds': time.monotonic()-started}
    save(output, report)
    print(json.dumps({key: value for key, value in report.items() if key not in ('source_hashes', 'runtime_binding')}, indent=2), flush=True)
    print('controls_sha256', digest(output), flush=True)


def build_export(proto_path, started, checkpoint):
    assert not proto_path.exists()
    with tempfile.TemporaryDirectory(prefix='conway-case4-native-cp-') as directory:
        cover_path = Path(directory) / 'covers.txt'
        cover = write_cover_body(cover_path)
        checkpoint('all_cover_witnesses_replayed_and_stream_saved', {'clauses': cover['clauses']})
        inventory = load_inventory()
        checkpoint('complete_original_domain_and_rows_reconstructed', {'primary_variables': 1214})
        model = build_native(inventory, cover_path, checkpoint)
        checkpoint('complete_native_model_validated', {'variables': 1214, 'constraints': 180804})
        assert model.export_to_file(str(proto_path))
        assert proto_path.stat().st_size <= LIMITS['binary_proto_bytes']
        del model
        gc.collect()
        audit = audit_binary_proto(proto_path, inventory, cover_path)
        checkpoint('complete_exported_proto_audit_passed', audit)
    check_budget(started)
    return inventory, cover, audit


def prepare(model_path, proto_path, controls_path, progress_path):
    assert not model_path.exists() and not proto_path.exists() and not progress_path.exists()
    assert proto_path.suffix != '.txt'
    started = time.monotonic()
    runtime = runtime_binding()
    control = json.loads(controls_path.read_text())
    assert control['source_hashes'] == source_hashes() and control['runtime_binding'] == runtime
    assert control['status'].startswith('PASS:') and control['main_case4_solver_queries'] == 0
    state = {'status': 'native case4 preparation active; no production query', 'complete': False,
             'source_hashes': source_hashes(), 'limits': LIMITS, 'main_case4_solver_queries': 0}

    def checkpoint(phase, values):
        state.update(phase=phase, current=values, elapsed_seconds=time.monotonic()-started,
                     observed_peak_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        save(progress_path, state)
        print(json.dumps({'phase': phase, 'elapsed_seconds': state['elapsed_seconds'], **values}), flush=True)
        check_budget(started)

    checkpoint('starting', {})
    try:
        inventory, cover, audit = build_export(proto_path, started, checkpoint)
        result = {'status': 'complete native Boolean case4 model prepared and byte-audited; not queried',
                  'complete': True, 'case_index': 4, 'source_hashes': source_hashes(),
                  'runtime_binding': runtime, 'limits': LIMITS,
                  'scope_inventory_sha256': SCOPE_SHA,
                  'controls_file': portable(controls_path), 'controls_sha256': digest(controls_path),
                  'original_full_overlay_model_sha256': OLD_OVERLAY_SHA,
                  'original_full_overlay_CNF_sha256': OLD_CNF_SHA,
                  'primary_inventory': inventory, 'primary_inventory_sha256': sha(canonical(inventory)),
                  'cover_replay_and_stream': cover, 'proto_audit': audit,
                  'binary_proto': str(proto_path.resolve()), 'binary_proto_sha256': audit['binary_proto_sha256'],
                  'binary_proto_bytes': audit['binary_proto_bytes'],
                  'primary_equivalence': 'Same Boolean incidence constraints as the frozen full coordinate-cover CNF; the 1,353 added triple rows follow from its quota-one Gram equations.',
                  'additional_counter_variables': 0, 'full_exterior_edge_variables': 0,
                  'objective_assumptions_hints_or_graph_symmetry_added': False,
                  'all_inputs_kept_free_except_proved_constraints': True,
                  'full_cover_literal_family_held_as_Python_lists': False,
                  'planned_solver_parameters': {'max_time_in_seconds': 60, 'num_search_workers': 1},
                  'main_case4_solver_queries': 0,
                  'SAT_scope': 'Partial binary incidence only; must pass the frozen exact full inspector.',
                  'INFEASIBLE_or_UNKNOWN_scope': 'No accepted case4 exclusion without a separate mathematical certificate.',
                  'exact_candidate_inspector': 'complement_rook_35core_case0004_coordinate_cover_query.inspect_selected',
                  'preparation_seconds': time.monotonic()-started,
                  'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        save(model_path, result)
        state.update(status='native preparation complete; no production query', complete=True,
                     model_sha256=digest(model_path), binary_proto_sha256=result['binary_proto_sha256'])
        checkpoint('complete', {'model_sha256': digest(model_path), 'binary_proto_bytes': result['binary_proto_bytes']})
    except Exception as error:
        state.update(status='native preparation failed; no completed query model',
                     error_type=type(error).__name__, error_message=str(error),
                     elapsed_seconds=time.monotonic()-started)
        save(progress_path, state)
        raise
    print('model_sha256', digest(model_path), flush=True)


def replay(model_path, output):
    assert not output.exists()
    started = time.monotonic()
    saved = json.loads(model_path.read_text())
    assert saved['complete'] and saved['source_hashes'] == source_hashes()
    assert saved['runtime_binding'] == runtime_binding() and saved['limits'] == LIMITS
    assert digest(ROOT / saved['controls_file']) == saved['controls_sha256']
    assert saved['main_case4_solver_queries'] == 0 and saved['case_index'] == 4

    def checkpoint(phase, values):
        print(json.dumps({'phase': phase, 'elapsed_seconds': time.monotonic()-started}), flush=True)
        check_budget(started)

    with tempfile.TemporaryDirectory(prefix='conway-case4-native-cold-') as directory:
        inventory, cover, audit = build_export(Path(directory) / 'cold.pb', started, checkpoint)
    assert normalized(inventory) == saved['primary_inventory']
    assert sha(canonical(inventory)) == saved['primary_inventory_sha256']
    assert normalized(cover) == saved['cover_replay_and_stream']
    assert audit == saved['proto_audit']
    assert audit['binary_proto_sha256'] == saved['binary_proto_sha256']
    result = {'status': 'PASS: cold full native model and all exported constraint bytes replayed',
              'source_hashes': source_hashes(), 'model_sha256': digest(model_path),
              'runtime_binding_sha256': sha(canonical(saved['runtime_binding'])),
              'primary_inventory_sha256': saved['primary_inventory_sha256'],
              'binary_proto_sha256': audit['binary_proto_sha256'], 'proto_audit': audit,
              'main_case4_solver_queries': 0, 'tiny_controls_repeated': False,
              'case4_excluded': False, 'elapsed_seconds': time.monotonic()-started,
              'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    print('replay_sha256', digest(output), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    test = commands.add_parser('controls')
    test.add_argument('--output', type=Path, required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--model', type=Path, required=True)
    prep.add_argument('--proto', type=Path, required=True)
    prep.add_argument('--controls', type=Path, required=True)
    prep.add_argument('--progress', type=Path, required=True)
    check = commands.add_parser('replay')
    check.add_argument('--model', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'controls':
        controls(args.output.resolve())
    elif args.command == 'prepare':
        prepare(args.model.resolve(), args.proto.resolve(), args.controls.resolve(), args.progress.resolve())
    else:
        replay(args.model.resolve(), args.output.resolve())
