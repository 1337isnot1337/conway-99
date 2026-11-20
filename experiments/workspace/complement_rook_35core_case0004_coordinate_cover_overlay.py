"""Stream the complete coordinate-cover family after the frozen60-cut CNF.

The original261071-clause body is copied byte for byte. All178533
certified cover clauses are appended, using primary variables only.
No list containing the12.9million added literals is materialized.
This source prepares and cold-replays the formula; it exposes no solve.
"""

import argparse
from collections import Counter
import gc
import gzip
import hashlib
import json
from pathlib import Path
import resource
import tempfile
import time

import complement_rook_35core_case0004_row_cut_boolean as base_builder
import complement_rook_35core_case0004_coordinate_covers as covers


ROOT, LOGS = base_builder.ROOT, base_builder.LOGS
BASE = LOGS / 'complement-rook-35core-case0004-row-cut-boolean-model.json'
BASE_SHA = '51268b36baee6ba62c7925ab85a18724d5e9b28006cb2a62f6bd3228f862346a'
COVERS = LOGS / 'complement-rook-35core-case0004-coordinate-covers.json.gz'
COVERS_SHA = 'a255f8876d3d827ff94d7df2f2640be6963348987043665dcd6fc53bf41dff8f'
REPLAY = LOGS / 'complement-rook-35core-case0004-coordinate-covers-replay.json'
REPLAY_SHA = '692671bd70bd39f7a89547235b88b81af8b6a7717c76f95e719cee8ca1f2ca18'
DEPENDENCIES = {
    'complement_rook_35core_case0004_row_cut_boolean.py': '2b231f418645d13c18fa4995277858e9b4fe5b770000e7ea742b5e5336fbfe45',
    'complement_rook_35core_case0004_coordinate_covers.py': 'f4692deb00982e7f3a3153faafc2cc6084db0c5827ff12d11beaf5e3d493357a',
    'complement_rook_35core_case0004_intrinsic_rows.py': '24eb86e47e6f5a741721fe9174e7d3762bc74edd290c89d489dd5ddedb900c11',
}
LIMITS = {'added_clauses': 200000, 'added_literal_occurrences': 15000000}
digest, canonical, portable = base_builder.digest, base_builder.canonical, base_builder.portable


def source_hashes():
    names = set(DEPENDENCIES) | set(base_builder.source_hashes()) | {Path(__file__).name}
    return {name: digest(Path(__file__).with_name(name)) for name in sorted(names)}


def verify_ledger(certificate):
    """Check coverage and implications without reusing the greedy census."""
    assert certificate['complete'] and certificate['source_sha256'] == DEPENDENCIES['complement_rook_35core_case0004_coordinate_covers.py']
    assert certificate['row_domain_sha256'] == covers.intrinsic.DOMAIN_SHA
    assert certificate['intrinsic_certificate_sha256'] == covers.CENSUS_SHA
    model, targets, zeros, neighbors, old_units = covers.intrinsic.load()
    assert certificate['covered_target_columns'] == list(range(1214))
    assert not certificate['uncovered_target_columns']
    assert len(certificate['records']) == 1214
    vectors = [mask | (1 << 35) for mask in model['column_masks35']]
    coordinate_supports = [sum(1 << b for b, vector in enumerate(vectors) if vector >> i & 1)
                           for i in range(36)]
    counts = Counter()
    unit_targets = []
    for a, record in enumerate(certificate['records']):
        assert record['target_column'] == a and record['negative_guard_literal'] == -a-1
        neighbor_bits = sum(1 << b for b in neighbors[a])
        support = [row & neighbor_bits for row in coordinate_supports]
        bits = [int(item['cover_bits_hex'], 16) for item in record['unique_covers']]
        assert bits == sorted(set(bits), key=lambda value: (value.bit_count(), value))
        assert all(0 <= value < (1 << 1214) and not(value >> a & 1) for value in bits)
        expected_pairs = [(i, j, targets[a][i]-targets[a][j]) for i in range(36) for j in range(36)
                          if targets[a][i] > targets[a][j]]
        ledger = record['all_positive_difference_pairs']
        assert [tuple(row[:3]) for row in ledger] == expected_pairs
        used = set()
        for i, j, demand, index, weakened in ledger:
            assert type(index) is int and 0 <= index < len(bits)
            assert weakened == (demand > 1)
            assert bits[index] == support[i] & ~support[j]
            used.add(index)
            counts['positive_target_difference_pairs'] += 1
            counts['demands_weakened_to_one'] += weakened
        assert used == set(range(len(bits)))
        kept = record['retained_unique_cover_ids']
        assert kept == sorted(set(kept))
        assert all(0 <= index < len(bits) for index in kept)
        # Antichain plus a kept subset for every omitted cover is an
        # independent certificate of the complete minimal-cover family.
        for offset, i in enumerate(kept):
            assert all(bits[i] & ~bits[j] and bits[j] & ~bits[i] for j in kept[:offset])
        kept_set = set(kept)
        for index, item in enumerate(record['unique_covers']):
            assert item['positive_literals'] == bits[index].bit_count()
            if index in kept_set:
                assert item['classification'] == 'retained' and item['retained_subset_witness_id'] is None
            else:
                witness = item['retained_subset_witness_id']
                assert witness in kept_set and bits[witness] != bits[index]
                assert bits[witness] & ~bits[index] == 0
                expected = 'implied_by_same_target_unit' if bits[witness] == 0 else 'implied_by_same_target_strict_subset'
                assert item['classification'] == expected
                counts['same_target_nonempty_covers_implied_by_unit' if bits[witness] == 0
                       else 'same_target_strict_supersets_removed'] += 1
        unit = bool(bits and bits[0] == 0)
        assert record['empty_cover_forces_target_absent'] == unit
        if unit:
            assert kept == [0]
            unit_targets.append(a)
        assert record['retained_clause_count'] == len(kept)
        assert record['retained_literal_count'] == sum(1+bits[index].bit_count() for index in kept)
        counts['unique_same_target_covers'] += len(bits)
        counts['retained_minimal_cover_clauses'] += len(kept)
        counts['retained_literal_occurrences'] += record['retained_literal_count']
    assert unit_targets == certificate['unit_target_columns']
    assert unit_targets == [352, 353, 354, 355, 439, 552, 553, 645, 869, 873, 957, 1080, 1081, 1167]
    counts['unit_clauses'] = len(unit_targets)
    counts['duplicate_origins_merged'] = counts['positive_target_difference_pairs']-counts['unique_same_target_covers']
    for key, value in counts.items():
        assert certificate['summary'][key] == value
    assert counts['retained_minimal_cover_clauses'] <= LIMITS['added_clauses']
    assert counts['retained_literal_occurrences'] <= LIMITS['added_literal_occurrences']
    return {'status': 'PASS: complete ordered-pair coverage and exact same-target implication ledger',
            'checked_targets': 1214, 'ordered_coordinate_pairs': 1214*36*36,
            'counts': dict(sorted(counts.items())), 'unit_target_columns': unit_targets,
            'previous_explicit_unit_targets': old_units,
            'unit_targets_not_previously_explicit': sorted(set(unit_targets)-set(old_units)),
            'independent_of_the_greedy_minimal_cover_construction': True,
            'optimizer_or_solver_called': False}


def build(cnf_path, progress=None):
    assert not cnf_path.exists()
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert digest(BASE) == BASE_SHA and digest(COVERS) == COVERS_SHA and digest(REPLAY) == REPLAY_SHA
    base = base_builder.checked_model(BASE)
    base_rebuilt = base_builder.rebuild()
    _, _, _, _, _, data, original_cnf, metadata, encoding_records = base_rebuilt
    assert base_builder.normalized(metadata) == base['formula']
    assert base_builder.normalized(encoding_records) == base['cut_encodings']
    assert (original_cnf.nv, len(original_cnf.clauses)) == (134852, 261071)
    original_literals = sum(map(len, original_cnf.clauses))
    with tempfile.TemporaryDirectory(prefix='conway-case4-coordinate-base-') as directory:
        base_cnf_path = Path(directory) / 'base.cnf'
        original_cnf.to_file(base_cnf_path)
        assert digest(base_cnf_path) == base['cnf_sha256']
        del base_rebuilt, data, original_cnf, metadata, encoding_records
        gc.collect()
        if progress:
            progress('complete60_cut_base_rebuilt', {'base_cnf_sha256': base['cnf_sha256']})
        certificate = json.loads(gzip.decompress(COVERS.read_bytes()))
        ledger = verify_ledger(certificate)
        if progress:
            progress('complete_cover_ledger_verified', ledger['counts'])
        count = certificate['summary']['retained_minimal_cover_clauses']
        assert count == 178533
        prefix_hasher, suffix_hasher = hashlib.sha256(), hashlib.sha256()
        prefix_bytes = suffix_bytes = prefix_lines = written = literals = 0
        cnf_path.parent.mkdir(parents=True, exist_ok=True)
        with cnf_path.open('wb') as target, base_cnf_path.open('rb') as old:
            assert old.readline() == b'p cnf 134852 261071\n'
            target.write(f'p cnf 134852 {261071+count}\n'.encode())
            while True:
                chunk = old.read(1 << 20)
                if not chunk:
                    break
                target.write(chunk)
                prefix_hasher.update(chunk)
                prefix_bytes += len(chunk)
                prefix_lines += chunk.count(b'\n')
            assert prefix_lines == 261071
            for clause in covers.clause_stream(certificate):
                assert clause[0] < 0 and all(0 < value <= 1214 for value in clause[1:])
                assert len(clause) == len(set(clause)) and -clause[0] not in clause[1:]
                raw = (' '.join(map(str, clause))+' 0\n').encode()
                target.write(raw)
                suffix_hasher.update(raw)
                suffix_bytes += len(raw)
                written += 1
                literals += len(clause)
                if progress and written % 32768 == 0:
                    progress('streaming_cover_suffix', {'clauses_written': written, 'literal_occurrences': literals})
        assert written == count and literals == certificate['summary']['retained_literal_occurrences']
        assert suffix_hasher.hexdigest() == certificate['canonical_retained_clause_body_sha256']
        formula = {
            'primary_columns': 1214, 'variables': 134852, 'clauses': 261071+written,
            'base_clauses': 261071, 'base_literal_occurrences': original_literals,
            'added_primary_cover_clauses': written, 'added_literal_occurrences': literals,
            'total_literal_occurrences': original_literals+literals,
            'new_auxiliary_variables': 0,
            'cover_unit_target_columns': ledger['unit_target_columns'],
            'cover_unit_DIMACS_clauses': [[-a-1] for a in ledger['unit_target_columns']],
            'cover_units_not_previously_explicit': ledger['unit_targets_not_previously_explicit'],
            'all14_cover_units_retained_including_two_already_in_base': True,
            'unchanged_base_clause_body_sha256': prefix_hasher.hexdigest(),
            'unchanged_base_clause_body_bytes': prefix_bytes,
            'added_clause_body_sha256': suffix_hasher.hexdigest(),
            'added_clause_body_bytes': suffix_bytes,
            'CNF_sha256': digest(cnf_path), 'CNF_bytes': cnf_path.stat().st_size,
        }
    return base, ledger, formula


def prepare(model_path, cnf_path, progress_path):
    assert not model_path.exists() and not cnf_path.exists() and not progress_path.exists()
    started = time.monotonic()
    state = {'status': 'preparing a streamed coordinate-cover overlay', 'complete': False,
             'source_hashes': source_hashes(), 'solver_queries': 0}

    def checkpoint(phase, values):
        state.update(phase=phase, current=values, elapsed_seconds=time.monotonic()-started)
        base_builder.save(progress_path, state)
        print(json.dumps({'phase': phase, **values}), flush=True)

    checkpoint('starting', {})
    try:
        base, ledger, formula = build(cnf_path, checkpoint)
        model = {'status': 'complete frozen60-cut base plus every retained coordinate-cover clause prepared; not solved',
            'complete': True, 'source_hashes': source_hashes(), 'limits': LIMITS,
            'prefix_certificate_sha256': base['prefix_certificate_sha256'],
            'base_model': portable(BASE), 'base_model_sha256': BASE_SHA,
            'base_cnf_sha256': base['cnf_sha256'],
            'cover_certificate': portable(COVERS), 'cover_certificate_sha256': COVERS_SHA,
            'cover_cold_replay_sha256': REPLAY_SHA, 'cover_ledger_check': ledger,
            'case': base['case'], 'domain_record_sha256': base['domain_record_sha256'],
            'column_domain_sha256': base['column_domain_sha256'], 'Gram_sha256': base['Gram_sha256'],
            'cnf': str(cnf_path.resolve()), 'cnf_sha256': formula['CNF_sha256'], 'formula': formula,
            'clauses_streamed_without_full_literal_list': True,
            'base_clause_body_preserved_byte_for_byte': True,
            'all_optional_selectors_retained': True, 'fixed_incidence_design': False,
            'graph_automorphism_constraints': False, 'full_exterior_edge_variables': 0,
            'solver_queries': 0, 'scope': 'Only indexed35-core case4. SAT is partial incidence; any UNSAT claim needs a separate checked proof.',
            'preparation_seconds': time.monotonic()-started,
            'peak_rss_kib': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
        base_builder.save(model_path, model)
        state.update(status='streamed complete overlay prepared; no solver', complete=True,
                     model_sha256=digest(model_path), cnf_sha256=formula['CNF_sha256'])
        checkpoint('complete', formula)
    except Exception as error:
        state.update(status='preparation failed; no completed query model',
                     error_type=type(error).__name__, error_message=str(error))
        checkpoint('error', {})
        raise
    print(json.dumps(model, indent=2), flush=True)


def replay(model_path, output):
    assert not output.exists()
    model = json.loads(model_path.read_text())
    assert model['complete'] and model['source_hashes'] == source_hashes()
    assert model['base_model_sha256'] == BASE_SHA and model['cover_certificate_sha256'] == COVERS_SHA
    assert model['limits'] == LIMITS
    with tempfile.TemporaryDirectory(prefix='conway-case4-coordinate-cold-') as directory:
        base, ledger, formula = build(Path(directory) / 'cold.cnf')
        assert base_builder.normalized(ledger) == model['cover_ledger_check']
        assert base_builder.normalized(formula) == model['formula']
        assert formula['CNF_sha256'] == model['cnf_sha256']
    report = {'status': 'PASS: cold complete60-cut base, all coordinate-cover witnesses and streamed full CNF replayed',
              'source_hashes': source_hashes(), 'model_sha256': digest(model_path),
              'full_CNF_sha256': model['cnf_sha256'], 'formula': formula,
              'solver_or_optimizer_called': False, 'case4_excluded': False}
    base_builder.save(output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--model', type=Path, required=True)
    prep.add_argument('--cnf', type=Path, required=True)
    prep.add_argument('--progress', type=Path, required=True)
    check = commands.add_parser('replay')
    check.add_argument('--model', type=Path, required=True)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.model.resolve(), args.cnf.resolve(), args.progress.resolve())
    else:
        replay(args.model.resolve(), args.output.resolve())
