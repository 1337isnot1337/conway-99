"""Prepare a native base plus the complete external coordinate registry.

All 2,271 original native constraints and all 14 proved cover units are
initially encoded. The other covers remain in an exact external registry.
A later candidate loop may append every newly violated registered cover.
No finite prefix is claimed equivalent to the complete frozen formula.
This source prepares/replays the inputs and runs tiny controls only.
"""

import argparse
from collections import Counter
import gc
import gzip
import hashlib
import json
from pathlib import Path
import resource
import struct
import tempfile
import time

from google.protobuf import text_format
from ortools.sat import cp_model_pb2
from ortools.sat.python import cp_model

import complement_rook_35core_case0004_native_cpsat as native


ROOT, LOGS = native.ROOT, native.LOGS
digest, canonical, portable, save = native.digest, native.canonical, native.portable, native.save
MODEL = LOGS / 'complement-rook-35core-case0004-native-cpsat-model.json'
MODEL_SHA = 'a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476'
COLD = LOGS / 'complement-rook-35core-case0004-native-cpsat-cold-replay.json'
COLD_SHA = 'a6627477382b47013a0b26984826a565df879b0f226dc2ad505da318e751b5a7'
NATIVE_SHA = '4462dae913abcb736c5ba5f7cffc3f3e7d50b748826cab3c89fffbfd3bd0e3eb'
PREFIX_CONSTRAINTS = 2271
N = 1214
MASK_BYTES = (N + 7) // 8
RECORD_BYTES = 2 + MASK_BYTES
LIMITS = {'native_calls': 8, 'solver_seconds_per_call': 10,
          'requested_child_seconds': 120, 'hard_parent_seconds': 180,
          'workers': 1, 'inserted_cover_clauses': 25000,
          'inserted_cover_literals': 2000000,
          'preparation_seconds': 180, 'observed_preparation_peak_rss_kib': 786432}
UNITS = [352, 353, 354, 355, 439, 552, 553, 645, 869, 873, 957, 1080, 1081, 1167]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def source_hashes():
    return dict(native.source_hashes(), **{Path(__file__).name: digest(Path(__file__))})


def check_inputs():
    assert digest(Path(native.__file__)) == NATIVE_SHA
    assert digest(MODEL) == MODEL_SHA and digest(COLD) == COLD_SHA
    model, cold = json.loads(MODEL.read_text()), json.loads(COLD.read_text())
    assert model['complete'] and model['source_hashes'] == native.source_hashes()
    assert model['runtime_binding'] == native.runtime_binding()
    assert cold['model_sha256'] == MODEL_SHA
    assert cold['binary_proto_sha256'] == model['binary_proto_sha256']
    inventory = native.load_inventory()
    assert native.normalized(inventory) == model['primary_inventory']
    return model, inventory


def clause_from(a, bits):
    return [-a-1] + [b+1 for b in native.overlay.covers.members(bits)]


def entry(raw, index):
    assert type(index) is int and 0 <= index < len(raw) // RECORD_BYTES
    offset = index * RECORD_BYTES
    a = struct.unpack_from('<H', raw, offset)[0]
    bits = int.from_bytes(memoryview(raw)[offset+2:offset+RECORD_BYTES], 'little')
    return a, bits


def registry_from_ledger():
    """Pack target uint16 plus a fixed 152-byte mask for each clause ID."""
    assert digest(native.overlay.COVERS) == native.overlay.COVERS_SHA
    certificate = json.loads(gzip.decompress(native.overlay.COVERS.read_bytes()))
    ledger = native.overlay.verify_ledger(certificate)
    raw = bytearray()
    body_hash = hashlib.sha256()
    unit_ids, clauses, literals = [], 0, 0
    for record in certificate['records']:
        a = record['target_column']
        for identifier in record['retained_unique_cover_ids']:
            bits = int(record['unique_covers'][identifier]['cover_bits_hex'], 16)
            assert 0 <= bits < (1 << N) and not (bits >> a & 1)
            raw += struct.pack('<H', a) + bits.to_bytes(MASK_BYTES, 'little')
            body_hash.update((' '.join(map(str, clause_from(a, bits))) + ' 0\n').encode())
            if not bits:
                unit_ids.append(clauses)
            clauses += 1
            literals += 1 + bits.bit_count()
    assert (clauses, literals) == (178533, 12887146)
    assert len(raw) == RECORD_BYTES * clauses == 27494082
    assert body_hash.hexdigest() == native.COVER_BODY_SHA
    raw = bytes(raw)
    assert [entry(raw, i)[0] for i in unit_ids] == UNITS
    result = {'cover_certificate_sha256': native.overlay.COVERS_SHA,
              'complete_ledger_replay': ledger,
              'registry_records': clauses, 'registry_literal_occurrences': literals,
              'record_bytes': RECORD_BYTES, 'target_uint16_bytes': 2,
              'little_endian_cover_mask_bytes': MASK_BYTES,
              'decompressed_bytes': len(raw), 'decompressed_sha256': sha(raw),
              'canonical_DIMACS_body_sha256': body_hash.hexdigest(),
              'initial_unit_clause_ids': unit_ids, 'initial_unit_targets': UNITS}
    del certificate
    gc.collect()
    return raw, result


def audit_registry(raw, metadata):
    assert len(raw) == metadata['decompressed_bytes'] == 178533 * RECORD_BYTES
    assert sha(raw) == metadata['decompressed_sha256']
    body = hashlib.sha256()
    previous = -1
    units, literals, target_counts = [], 0, Counter()
    for identifier in range(178533):
        a, bits = entry(raw, identifier)
        assert previous <= a < N and bits < (1 << N) and not (bits >> a & 1)
        previous = a
        body.update((' '.join(map(str, clause_from(a, bits))) + ' 0\n').encode())
        if not bits:
            units.append(identifier)
        literals += 1 + bits.bit_count()
        target_counts[a] += 1
    assert body.hexdigest() == metadata['canonical_DIMACS_body_sha256'] == native.COVER_BODY_SHA
    assert literals == 12887146 and units == metadata['initial_unit_clause_ids']
    assert [entry(raw, i)[0] for i in units] == UNITS
    return {'all_registry_records_checked': 178533, 'canonical_body_sha256': body.hexdigest(),
            'literal_occurrences': literals, 'unit_clause_ids': units,
            'largest_target_clause_count': max(target_counts.values())}


def prefix_proto(inventory, raw, unit_ids):
    """Recreate the original native prefix with standard protobuf fields."""
    proto = cp_model_pb2.CpModelProto()
    for a in range(N):
        variable = proto.variables.add()
        variable.name = f'x{a}'
        variable.domain.extend([0, 1])
    for i, j, quota, members in inventory['Gram_rows']:
        constraint = proto.constraints.add()
        if members:
            constraint.linear.vars.extend(members)
            constraint.linear.coeffs.extend([1] * len(members))
            constraint.linear.domain.extend([quota, quota])
        else:
            assert quota == 0
            constraint.bool_and.SetInParent()
    for source, members in inventory['original_signature_rows']:
        proto.constraints.add().at_most_one.literals.extend(members)
    for triple in inventory['triple_rows']:
        proto.constraints.add().at_most_one.literals.extend(triple['members'])
    for clause in inventory['Gram_conflict_clauses']:
        proto.constraints.add().bool_or.literals.extend(clause)
    for cut in inventory['uncapped_integer_cuts']:
        terms = native.row_cut_terms(cut)
        row = proto.constraints.add().linear
        row.vars.extend(a for a, weight in terms)
        row.coeffs.extend(weight for a, weight in terms)
        row.domain.extend([0, sum(weight for a, weight in cut['positive_terms'])])
    assert len(proto.constraints) == PREFIX_CONSTRAINTS
    for identifier in unit_ids:
        a, bits = entry(raw, identifier)
        assert bits == 0
        proto.constraints.add().bool_or.literals.append(-a-1)
    assert len(unit_ids) == 14 and len(proto.constraints) == 2285
    return proto


def check_full_prefix_agreement(proto, frozen):
    path = Path(frozen['binary_proto'])
    assert digest(path) == frozen['binary_proto_sha256']
    full = cp_model_pb2.CpModelProto()
    full.ParseFromString(path.read_bytes())
    assert len(full.variables) == N and len(full.constraints) == 180804
    assert list(full.variables) == list(proto.variables)
    assert list(full.constraints[:PREFIX_CONSTRAINTS]) == list(proto.constraints[:PREFIX_CONSTRAINTS])
    assert not full.HasField('objective') and not full.HasField('solution_hint')
    return {'full_native_proto_sha256': frozen['binary_proto_sha256'],
            'exact_unchanged_prefix_constraints': PREFIX_CONSTRAINTS,
            'all_original_variables_and_domains_unchanged': True}


def native_from_proto(proto):
    model = cp_model.CpModel()
    assert model.proto.parse_text_format(text_format.MessageToString(proto))
    assert model.validate() == ''
    assert len(model.proto.variables) == N and len(model.proto.constraints) == len(proto.constraints)
    return model


def evaluate(raw, values):
    assert len(values) == N and all(type(value) is int and value in (0, 1) for value in values)
    chosen = sum(1 << a for a, value in enumerate(values) if value)
    violations = []
    active_guards = 0
    for identifier in range(len(raw) // RECORD_BYTES):
        a, bits = entry(raw, identifier)
        if chosen >> a & 1:
            active_guards += 1
            if not chosen & bits:
                violations.append(identifier)
    return {'registry_records_evaluated': len(raw) // RECORD_BYTES,
            'selected_boolean_count': sum(values), 'clauses_with_active_guard': active_guards,
            'violated_clause_ids': violations, 'violated_clause_count': len(violations),
            'all_registered_covers_hold': not violations}


def plan_batch(raw, encoded_ids, proposed_ids, clause_limit=None, literal_limit=None):
    assert encoded_ids == sorted(set(encoded_ids)) and proposed_ids == sorted(set(proposed_ids))
    assert not set(encoded_ids) & set(proposed_ids)
    clause_limit = LIMITS['inserted_cover_clauses'] if clause_limit is None else clause_limit
    literal_limit = LIMITS['inserted_cover_literals'] if literal_limit is None else literal_limit
    old_literals = sum(1 + entry(raw, i)[1].bit_count() for i in encoded_ids)
    new_literals = sum(1 + entry(raw, i)[1].bit_count() for i in proposed_ids)
    accepted = len(encoded_ids)+len(proposed_ids) <= clause_limit and old_literals+new_literals <= literal_limit
    return {'accepted': accepted, 'old_encoded_cover_count': len(encoded_ids),
            'proposed_cover_count': len(proposed_ids), 'old_encoded_literal_count': old_literals,
            'proposed_literal_count': new_literals,
            'clause_limit': clause_limit, 'literal_limit': literal_limit,
            'no_mutation_performed_by_planner': True}


def append_batch(model, raw, encoded_ids, proposed_ids):
    planned = plan_batch(raw, encoded_ids, proposed_ids)
    if not planned['accepted']:
        return planned, encoded_ids
    assert len(model.proto.variables) == N
    assert len(model.proto.constraints) == PREFIX_CONSTRAINTS+len(encoded_ids)
    # All resource checks precede the first mutation. The order of clauses
    # in the native prefix is saved separately from the sorted membership.
    for identifier in proposed_ids:
        a, bits = entry(raw, identifier)
        clause = clause_from(a, bits)
        model.add_bool_or(model.get_bool_var_from_proto_index(v-1) if v > 0
                          else model.get_bool_var_from_proto_index(-v-1).Not() for v in clause)
    assert len(model.proto.variables) == N
    assert len(model.proto.constraints) == PREFIX_CONSTRAINTS+len(encoded_ids)+len(proposed_ids)
    return planned, sorted(encoded_ids+proposed_ids)


def prefix_assignment_check(values, inventory, raw, encoded_ids):
    assert len(values) == N and all(type(value) is int and value in (0, 1) for value in values)
    selected = [a for a, value in enumerate(values) if value]
    assert len(selected) == 64
    for i, j, quota, members in inventory['Gram_rows']:
        assert sum(values[a] for a in members) == quota
    for source, members in inventory['original_signature_rows']:
        assert sum(values[a] for a in members) <= 1
    for triple in inventory['triple_rows']:
        assert sum(values[a] for a in triple['members']) <= 1
    for clause in inventory['Gram_conflict_clauses']:
        assert any(values[-v-1] == 0 for v in clause)
    for cut in inventory['uncapped_integer_cuts']:
        assert sum(weight*values[b] for b, weight in cut['positive_terms']) >= cut['positive_demand']*values[cut['target_column']]
    chosen = sum(1 << a for a in selected)
    for identifier in encoded_ids:
        a, bits = entry(raw, identifier)
        assert not(chosen >> a & 1) or bool(chosen & bits)
    return {'selected_columns': selected, 'all630_Gram_positions': True,
            'all186_original_signature_groups': True, 'all1365_core_triple_capacities': True,
            'all30_Gram_conflicts_and60_uncapped_row_cuts': True,
            'encoded_cover_count_checked': len(encoded_ids), 'complete_graph': False}


def controls(output):
    assert not output.exists()
    # Exercise packed registry semantics on all 16 points. The extra N-4
    # coordinates are zero, so the production bit width is tested literally.
    descriptions = [(0, 1 << 1), (1, 1 << 0), (2, 1 << 3), (3, 0)]
    raw = b''.join(struct.pack('<H', a)+bits.to_bytes(MASK_BYTES, 'little') for a, bits in descriptions)
    checked = 0
    for assignment in range(16):
        values = [(assignment >> a) & 1 for a in range(4)] + [0] * (N-4)
        observed = evaluate(raw, values)
        expected = [i for i, (a, bits) in enumerate(descriptions)
                    if values[a] and not (bits & assignment)]
        assert observed['violated_clause_ids'] == expected
        checked += 1
    encoded, proposed = [3], [0, 1, 2]
    assert not plan_batch(raw, encoded, proposed, clause_limit=3)['accepted']
    assert not plan_batch(raw, encoded, proposed, literal_limit=6)['accepted']
    assert plan_batch(raw, encoded, proposed, clause_limit=4, literal_limit=7)['accepted']
    assert encoded == [3] and proposed == [0, 1, 2]
    # Tiny candidate loop uses a native exact-two base and the same literal
    # implication semantics. Every new clause is a registered consequence.
    model = cp_model.CpModel()
    x = [model.new_bool_var(f'x{a}') for a in range(4)]
    model.add(sum(x) == 2)
    model.add_bool_or([x[3].Not()])
    seen_ids = {3}
    records = []
    accepted = None
    for iteration in range(5):
        solver = cp_model.CpSolver()
        solver.parameters.num_search_workers = 1
        solver.parameters.max_time_in_seconds = 2
        status = solver.solve(model)
        assert status in (cp_model.OPTIMAL, cp_model.FEASIBLE, cp_model.INFEASIBLE)
        if status == cp_model.INFEASIBLE:
            raise AssertionError('known feasible tiny lazy model rejected')
        values4 = [int(solver.value(variable)) for variable in x]
        values = values4 + [0] * (N-4)
        report = evaluate(raw, values)
        missing = report['violated_clause_ids']
        assert not seen_ids.intersection(missing)
        records.append({'assignment': values4, 'new_clause_ids': missing})
        if not missing:
            accepted = values4
            break
        for identifier in missing:
            a, bits = descriptions[identifier]
            clause = [x[a].Not()] + [x[b] for b in range(4) if bits >> b & 1]
            model.add_bool_or(clause)
        seen_ids.update(missing)
    assert accepted == [1, 1, 0, 0]
    result = {'status': 'PASS: packed complete-registry semantics, atomic refusal, and tiny lazy candidate loop',
              'source_hashes': source_hashes(), 'complete_registry_assignment_controls': checked,
              'atomic_resource_refusal_controls': 2, 'exact_limit_acceptance_control': True,
              'tiny_native_calls': len(records), 'tiny_lazy_iterations': records,
              'unique_full_registry_tiny_solution': accepted,
              'no_visitation_block_or_hint': True, 'main_case4_queries': 0}
    save(output, result)
    print(json.dumps(result, indent=2), flush=True)
    print('controls_sha256', digest(output), flush=True)


def prepare(output, registry_path, prefix_path, controls_path):
    assert not any(path.exists() for path in (output, registry_path, prefix_path))
    started = time.monotonic()
    control = json.loads(controls_path.read_text())
    assert control['source_hashes'] == source_hashes() and control['status'].startswith('PASS:')
    frozen, inventory = check_inputs()
    raw, metadata = registry_from_ledger()
    registry_check = audit_registry(raw, metadata)
    proto = prefix_proto(inventory, raw, metadata['initial_unit_clause_ids'])
    full_agreement = check_full_prefix_agreement(proto, frozen)
    prefix_raw = proto.SerializeToString(deterministic=True)
    prefix_path.write_bytes(gzip.compress(prefix_raw, mtime=0))
    registry_path.write_bytes(gzip.compress(raw, mtime=0))
    model = native_from_proto(proto)
    with tempfile.TemporaryDirectory(prefix='conway-case4-lazy-prefix-') as directory:
        path = Path(directory) / 'prefix.pb'
        assert model.export_to_file(str(path))
        assert path.read_bytes() == prefix_raw
    assert len(model.proto.variables) == 1214 and len(model.proto.constraints) == 2285
    elapsed = time.monotonic()-started
    rss = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    assert elapsed <= LIMITS['preparation_seconds'] and rss <= LIMITS['observed_preparation_peak_rss_kib']
    result = {'status': 'complete external cover registry and native base prepared; no main query',
              'complete': True, 'source_hashes': source_hashes(), 'limits': LIMITS,
              'native_model_sha256': MODEL_SHA, 'native_cold_replay_sha256': COLD_SHA,
              'runtime_binding_sha256': sha(canonical(frozen['runtime_binding'])),
              'controls': portable(controls_path), 'controls_sha256': digest(controls_path),
              'primary_inventory_sha256': frozen['primary_inventory_sha256'],
              'registry': portable(registry_path), 'registry_sha256': digest(registry_path),
              'registry_metadata': metadata, 'registry_readback_check': registry_check,
              'prefix_proto': portable(prefix_path), 'prefix_proto_compressed_sha256': digest(prefix_path),
              'prefix_proto_decompressed_sha256': sha(prefix_raw), 'prefix_proto_decompressed_bytes': len(prefix_raw),
              'full_native_prefix_agreement': full_agreement,
              'variables': N, 'base_constraints': PREFIX_CONSTRAINTS,
              'initial_proved_units': 14, 'initial_native_constraints': 2285,
              'initial_prefix_clause_ids_in_order': metadata['initial_unit_clause_ids'],
              'complete_external_coordinate_covers': 178533,
              'no_objective_assumptions_hint_or_graph_symmetry': True,
              'all_candidates_must_be_saved_as_complete1214_Boolean_values': True,
              'every_candidate_requires_full_registry_evaluation': True,
              'all_newly_violated_covers_added_atomically_or_resource_stop': True,
              'acceptance_requires_frozen_complete_inspector': True,
              'finite_prefix_equivalent_to_complete_cover_formula': False,
              'INFEASIBLE_or_UNKNOWN_is_checked_exclusion': False,
              'main_case4_queries': 0, 'preparation_seconds': elapsed, 'peak_rss_kib': rss}
    save(output, result)
    print(json.dumps({key: value for key, value in result.items() if key not in ('source_hashes', 'registry_metadata')}, indent=2), flush=True)
    print('model_sha256', digest(output), flush=True)


def load_prepared(path, replay_ledger=False):
    model = json.loads(path.read_text())
    assert model['complete'] and model['source_hashes'] == source_hashes() and model['limits'] == LIMITS
    frozen, inventory = check_inputs()
    assert model['runtime_binding_sha256'] == sha(canonical(frozen['runtime_binding']))
    assert model['primary_inventory_sha256'] == frozen['primary_inventory_sha256']
    registry_path, prefix_path = ROOT/model['registry'], ROOT/model['prefix_proto']
    assert digest(registry_path) == model['registry_sha256']
    assert digest(prefix_path) == model['prefix_proto_compressed_sha256']
    raw, prefix_raw = gzip.decompress(registry_path.read_bytes()), gzip.decompress(prefix_path.read_bytes())
    assert sha(raw) == model['registry_metadata']['decompressed_sha256']
    assert sha(prefix_raw) == model['prefix_proto_decompressed_sha256']
    assert audit_registry(raw, model['registry_metadata']) == model['registry_readback_check']
    if replay_ledger:
        fresh, metadata = registry_from_ledger()
        assert fresh == raw and native.normalized(metadata) == model['registry_metadata']
    proto = prefix_proto(inventory, raw, model['initial_prefix_clause_ids_in_order'])
    assert proto.SerializeToString(deterministic=True) == prefix_raw
    return model, inventory, raw, proto


def replay(model_path, output):
    assert not output.exists()
    started = time.monotonic()
    model, inventory, raw, proto = load_prepared(model_path, True)
    native_model = native_from_proto(proto)
    assert len(native_model.proto.constraints) == 2285
    result = {'status': 'PASS: exact native prefix, complete registry and all cover witnesses replayed',
              'source_hashes': source_hashes(), 'model_sha256': digest(model_path),
              'registry_sha256': model['registry_sha256'],
              'prefix_proto_sha256': model['prefix_proto_decompressed_sha256'],
              'base_constraints': 2271, 'proved_units': 14,
              'all_registry_records_checked': 178533,
              'full_frozen_native_model_rebuilt': False,
              'solver_or_optimizer_called': False,
              'elapsed_seconds': time.monotonic()-started,
              'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    save(output, result)
    print(json.dumps(result, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    test = commands.add_parser('controls')
    test.add_argument('--output', type=Path, required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--output', type=Path, required=True)
    prep.add_argument('--registry', type=Path, required=True)
    prep.add_argument('--prefix', type=Path, required=True)
    prep.add_argument('--controls', type=Path, required=True)
    check = commands.add_parser('replay')
    check.add_argument('--model', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'controls':
        controls(args.output.resolve())
    elif args.command == 'prepare':
        prepare(args.output.resolve(), args.registry.resolve(), args.prefix.resolve(), args.controls.resolve())
    else:
        replay(args.model.resolve(), args.output.resolve())
