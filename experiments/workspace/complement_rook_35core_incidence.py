"""Exact binary incidence model for one indexed complementary-rook35-core.

The primary variables select complete attachment columns. Full Gram
equalities, original-signature uniqueness, and core-triple packing are
necessary for a completion. No edges among the remaining64 vertices
are modeled. A SAT result is only an incidence witness.
"""

import argparse
from collections import Counter, defaultdict
import gc
import gzip
from itertools import combinations
import json
from pathlib import Path
import resource
import subprocess
import tempfile
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

import complement_rook_35core_domains as domains


ROOT, LOGS = domains.ROOT, domains.LOGS
PREFIX = LOGS/'complement-rook-35core-domains-prefix01'
PREFIX_SHA = 'a567f58470e42ab275bf330af30fa424786eb2243c568ba1c750b6bb5cc80a90'
SOURCES = ('complement_rook_35core_incidence.py', 'complement_rook_35core_domains.py',
           'complement_rook_projector_schur.py', 'complement_rook_local_star_census.py')
canonical, digest = domains.canonical, domains.digest


def portable(path):
    return str(path.resolve().relative_to(ROOT))


def load(case_index):
    certificate_path = PREFIX/'certificate.json'
    assert digest(certificate_path) == PREFIX_SHA
    certificate = json.loads(certificate_path.read_text())
    assert certificate['source_sha256'] == digest(Path(domains.__file__))
    archive = ROOT/certificate['archive']
    assert digest(archive) == certificate['archive_sha256']
    raw = gzip.decompress(archive.read_bytes())
    assert domains.sha(raw) == certificate['decompressed_jsonl_sha256']
    saved = {item['index']: item for item in map(json.loads, raw.splitlines())}
    assert case_index in saved
    domain, index = domains.load_domain()
    assert canonical(index)+b'\n' == (PREFIX/'all-core-index.json').read_bytes()
    assert digest(PREFIX/'all-core-index.json') == certificate['index_sha256']
    case = index['cases'][case_index]
    record = domains.analyze_core(domain, case)
    assert json.loads(json.dumps(record)) == saved[case_index]
    core, gram, _ = domains.core_matrix(domain, case)
    rows, originals, triples, masks, _ = domains.sparse_rows(domain, core, gram, record['columns'])
    return domain, index, case, record, core, gram, rows, originals, triples, masks


def assemble(gram, row_members, original_groups, triple_members, column_count):
    """Build exact counts; all counter auxiliaries share one fresh ID pool."""
    pairs = [(i, j) for i in range(len(gram)) for j in range(i, len(gram))]
    assert len(pairs) == len(row_members)
    lookup = dict(zip(pairs, row_members))
    pool, cnf = IDPool(start_from=column_count+1), CNF()
    counts, equality_coverage = {}, []
    clause_counts = {}
    for pair, members in zip(pairs, row_members):
        i, j = pair
        assert members == sorted(set(members))
        quota = gram[i][j]
        assert quota >= 0
        key = tuple(members), quota
        if key not in counts:
            counts[key] = len(counts)
            literals = [member+1 for member in members]
            if quota > len(literals):
                cnf.append([])
            elif literals:
                cnf.extend(CardEnc.equals(literals, quota, vpool=pool,
                                          encoding=EncType.seqcounter).clauses)
            else:
                assert quota == 0
        equality_coverage.append([i, j, counts[key]])
    clause_counts['Gram_equalities'] = len(cnf.clauses)

    multiplicity_rows = []
    for original, members in sorted(original_groups.items()):
        if len(members) > 1:
            multiplicity_rows.append([original, members])
            cnf.extend(CardEnc.atmost([member+1 for member in members], 1, vpool=pool,
                                      encoding=EncType.seqcounter).clauses)
    clause_counts['original_signature_at_most_one'] = len(cnf.clauses)-sum(clause_counts.values())

    triple_coverage, extra_rows = [], []
    for triple, members in sorted(triple_members.items()):
        if len(members) <= 1:
            continue
        quota_one = [pair for pair in combinations(triple, 2) if gram[pair[0]][pair[1]] == 1]
        if quota_one:
            witness = min(quota_one)
            assert set(members) <= set(lookup[witness])
            triple_coverage.append({'triple': list(triple), 'support': len(members),
                                    'implied_by_Gram_pair': list(witness)})
        else:
            assert all(gram[i][j] >= 2 for i, j in combinations(triple, 2))
            extra_rows.append([list(triple), members])
            cnf.extend(CardEnc.atmost([member+1 for member in members], 1, vpool=pool,
                                      encoding=EncType.seqcounter).clauses)
            triple_coverage.append({'triple': list(triple), 'support': len(members),
                                    'extra_row_index': len(extra_rows)-1})
    clause_counts['additional_core_triple_at_most_one'] = len(cnf.clauses)-sum(clause_counts.values())
    assert sum(clause_counts.values()) == len(cnf.clauses)
    assert all(abs(literal) <= pool.top for clause in cnf.clauses for literal in clause)
    description = {
        'primary_columns': column_count, 'variables': cnf.nv, 'clauses': len(cnf.clauses),
        'clause_counts': clause_counts, 'all_Gram_rows': len(pairs),
        'distinct_Gram_equations_including_empty_zero': len(counts),
        'Gram_equation_coverage': equality_coverage,
        'original_signature_multiplicity_rows': multiplicity_rows,
        'nontrivial_triple_capacity_rows': len(triple_coverage),
        'triple_capacity_coverage': triple_coverage, 'additional_triple_rows': extra_rows,
        'auxiliary_variables_begin_at': column_count+1,
    }
    return cnf, description


def controls():
    """Exhaust small counter semantics and a known9-rook incidence point."""
    assignments = 0
    for count in range(7):
        literals = list(range(1, count+1))
        for quota in range(count+1):
            pool = IDPool(start_from=count+1)
            cnf = CNF(from_clauses=CardEnc.equals(literals, quota, vpool=pool,
                                                 encoding=EncType.seqcounter).clauses)
            with Solver(name='glucose3', bootstrap_with=cnf.clauses) as solver:
                for mask in range(1 << count):
                    assumptions = [v if mask >> (v-1) & 1 else -v for v in literals]
                    assert solver.solve(assumptions=assumptions) == (mask.bit_count() == quota)
                    assignments += 1
        pool = IDPool(start_from=count+1)
        cnf = CNF(from_clauses=CardEnc.atmost(literals, 1, vpool=pool,
                                            encoding=EncType.seqcounter).clauses)
        with Solver(name='glucose3', bootstrap_with=cnf.clauses) as solver:
            for mask in range(1 << count):
                assumptions = [v if mask >> (v-1) & 1 else -v for v in literals]
                assert solver.solve(assumptions=assumptions) == (mask.bit_count() <= 1)
                assignments += 1

    rook = lambda i, j: i != j and (i//3 == j//3 or i % 3 == j % 3)
    selected_core, outside = [0, 1, 3, 4, 8], [2, 5, 6, 7]
    core = [sum(1 << j for j, v in enumerate(selected_core) if rook(u, v)) for u in selected_core]
    gram = [[2*int(i == j)+2-(core[i] & core[j]).bit_count()-int(core[i] >> j & 1)
             for j in range(5)] for i in range(5)]
    column_masks = [mask for mask in range(1, 32)
                    if all(not(mask >> i & 1 and mask >> j & 1) or gram[i][j] > 0
                           for i in range(5) for j in range(5))
                    and all(((core[i] | (1 << i)) & mask).bit_count() <= 2 for i in range(5))]
    pairs = [(i, j) for i in range(5) for j in range(i, 5)]
    rows = [[c for c, mask in enumerate(column_masks) if mask >> i & 1 and mask >> j & 1] for i, j in pairs]
    triple_rows = defaultdict(list)
    for column, mask in enumerate(column_masks):
        for triple in combinations([i for i in range(5) if mask >> i & 1], 3):
            triple_rows[triple].append(column)
    cnf, metadata = assemble(gram, rows, {c: [c] for c in range(len(column_masks))},
                             triple_rows, len(column_masks))
    actual = [sum(1 << i for i, v in enumerate(selected_core) if rook(u, v)) for u in outside]
    assert len(actual) == len(set(actual)) == 4 and set(actual) <= set(column_masks)
    chosen = {column_masks.index(mask) for mask in actual}
    assumptions = [c+1 if c in chosen else -c-1 for c in range(len(column_masks))]
    assert all(sum((column_masks[c] >> i & 1)*(column_masks[c] >> j & 1) for c in chosen) == gram[i][j]
               for i in range(5) for j in range(5))
    with Solver(name='glucose3', bootstrap_with=cnf.clauses) as solver:
        assert solver.solve(assumptions=assumptions)
        changed = assumptions[:]
        changed[min(chosen)] *= -1
        assert not solver.solve(assumptions=changed)
    return {'small_counter_truth_assignments': assignments,
            'rook9_core_vertices': selected_core, 'rook9_outside_vertices': outside,
            'rook9_candidate_columns': len(column_masks), 'rook9_exact_incidence_positive_control': True,
            'rook9_deleted_column_negative_control': True,
            'main35core_solver_called': False}


def rebuild(case_index):
    data = load(case_index)
    _, _, _, record, _, gram, rows, originals, triples, _ = data
    cnf, metadata = assemble(gram, rows, originals, triples, len(record['columns']))
    if case_index == 0:
        assert len(record['columns']) == 1206
        assert len(metadata['original_signature_multiplicity_rows']) == 186
        assert len(metadata['additional_triple_rows']) == 12
        assert metadata['nontrivial_triple_capacity_rows'] == 1347
    return data, cnf, metadata


def prepare(case_index, model_path, cnf_path):
    assert not model_path.exists() and not cnf_path.exists()
    started = time.monotonic()
    control = controls()
    data, cnf, metadata = rebuild(case_index)
    domain, index, case, record, core, gram, *_ = data
    cnf_path.parent.mkdir(parents=True, exist_ok=True)
    cnf.to_file(cnf_path)
    result = {'status': 'exact35-core binary incidence formula prepared; main model not solved',
        'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in SOURCES},
        'prefix_certificate': portable(PREFIX/'certificate.json'), 'prefix_certificate_sha256': PREFIX_SHA,
        'root_census_sha256': domains.CENSUS_SHA, 'complete_index_cases': len(index['cases']),
        'case': case, 'domain_record_sha256': domains.sha(canonical(record)),
        'column_domain_sha256': record['column_domain_sha256'], 'Gram_sha256': record['Gram_sha256'],
        'cnf': str(cnf_path.resolve()), 'cnf_sha256': digest(cnf_path),
        'formula': metadata, 'controls': control,
        'population_and_attachment_counts_are_derived': [64, 4, 40, 20],
        'remaining_exterior_edge_variables': 0, 'graph_automorphism_assumptions': 0,
        'additional_a_or_spectral_constraints': 0, 'selected_incidence_design_fixed': False,
        'SAT_scope': 'binary necessary incidence witness for one35-core; no exterior completion',
        'UNSAT_scope': 'one indexed35-core and its verified relabelings only',
        'build_seconds': time.monotonic()-started}
    model_path.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'formula'}, indent=2), flush=True)
    print(json.dumps({key: value for key, value in metadata.items() if key not in
                      ('Gram_equation_coverage', 'original_signature_multiplicity_rows',
                       'triple_capacity_coverage', 'additional_triple_rows')}, indent=2), flush=True)
    return result


def inspect(selected, data):
    domain, _, case, record, core, gram, _, _, _, masks = data
    assert selected == sorted(set(selected)) and len(selected) == 64
    assert all(0 <= column < len(masks) for column in selected)
    columns = [record['columns'][column] for column in selected]
    originals = [source for source, _ in columns]
    assert len(set(originals)) == 64
    assert all(sum((masks[c] >> i & 1)*(masks[c] >> j & 1) for c in selected) == gram[i][j]
               for i in range(35) for j in range(35))
    overlaps = Counter((masks[a] & masks[b]).bit_count() for a, b in combinations(selected, 2))
    assert all(value <= 2 for value in overlaps)
    attachments = Counter(attachment.bit_count() for _, attachment in columns)
    assert attachments == Counter({0: 4, 1: 40, 2: 20})
    old_gram, triples, old_signatures = domain[1:4]
    old_selected = sorted(originals+case['selected_signatures'])
    assert len(old_selected) == len(set(old_selected)) == 72
    assert all(sum(i in old_signatures[s] and j in old_signatures[s] for s in old_selected) == old_gram[i][j]
               for i in range(27) for j in range(27))
    rook = lambda p, q: p != q and (p//3 == q//3 or p % 3 == q % 3)
    parameter = sum(rook(triples[s][0], triples[s][2]) and rook(triples[s][1], triples[s][2])
                    for s in old_selected)
    return {'selected_columns': selected, 'selected_attachment_columns': columns,
            'selected_original72_signatures': old_selected, 'a': parameter,
            'a_in_previously_excluded_zero_one_two': parameter <= 2,
            'full35_Gram_entries_checked': 1225, 'old27_Gram_entries_checked': 729,
            'original_signature_multiplicity_checked': True, 'selected_column_pair_checks': 2016,
            'selected_column_overlap_histogram': dict(sorted(overlaps.items())),
            'selected_attachment_counts': [attachments[d] for d in range(3)],
            'remaining64_vertex_adjacency_unspecified': True, 'complete_graph': False}


def read_clauses(path):
    with path.open() as stream:
        for line in stream:
            if not line or line[0] in 'cp':
                continue
            values = list(map(int, line.split()))
            assert values and values[-1] == 0
            yield values[:-1]


def checked_model(model_path, require_cnf=False):
    model = json.loads(model_path.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert model['prefix_certificate_sha256'] == PREFIX_SHA
    if require_cnf:
        assert digest(Path(model['cnf'])) == model['cnf_sha256']
    return model


def solve(model_path, directory, seconds, checker, checker_seconds):
    assert not directory.exists() and 0 < seconds <= 120 and 0 < checker_seconds <= 60
    directory.mkdir(parents=True)
    model = checked_model(model_path, True)
    result_path = directory/'result.json'
    result = {'status': 'running one35-core binary incidence model',
        'model': portable(model_path), 'model_sha256': digest(model_path),
        'source_sha256': digest(Path(__file__)), 'case_index': model['case']['index'],
        'cnf_sha256': model['cnf_sha256'], 'requested_solver_seconds_including_bootstrap': seconds,
        'requested_direct_checker_seconds': checker_seconds, 'assumptions': [],
        'whole_complementary_core_excluded': False, 'full_graph_completion_found': False}

    def save():
        result['peak_process_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        result_path.write_text(json.dumps(result, indent=2)+'\n')

    save()
    started = time.monotonic()
    try:
        cnf = CNF(from_file=model['cnf'])
        assert (cnf.nv, len(cnf.clauses)) == (model['formula']['variables'], model['formula']['clauses'])
        with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
            del cnf
            gc.collect()
            result['bootstrap_seconds'] = time.monotonic()-started
            timer = Timer(max(0.001, seconds-result['bootstrap_seconds']), solver.interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
            result['solve_return_seconds'] = time.monotonic()-started
            result['solver_statistics'] = solver.accum_stats()
            if answer is None:
                result['status'] = 'UNKNOWN; this35-core incidence feasibility remains unresolved'
            elif answer:
                positive = {literal for literal in solver.get_model() if literal > 0}
                selected = [c for c in range(model['formula']['primary_columns']) if c+1 in positive]
                result['incidence_witness'] = inspect(selected, load(model['case']['index']))
                result['status'] = 'SAT; exact binary35-core incidence witness directly checked'
            else:
                proof = solver.get_proof()
                assert proof is not None
                result['terminal_empty_clause_appended'] = not proof or proof[-1] != '0'
                if result['terminal_empty_clause_appended']:
                    proof.append('0')
                raw = directory/'raw.drat'
                raw.write_text('\n'.join(proof)+'\n')
                result.update(status='solver UNSAT; direct DRAT pending', raw_proof=portable(raw),
                              raw_proof_sha256=digest(raw), raw_proof_lines=len(proof))
        save()
        if result['status'].startswith('solver UNSAT'):
            retained, proof, log = directory/'retained.cnf', directory/'retained.drat', directory/'direct-drat.log'
            checked = subprocess.run([str(checker), model['cnf'], str(ROOT/result['raw_proof']),
                                      '-t', str(checker_seconds), '-w', '-c', str(retained), '-l', str(proof)],
                                     capture_output=True, text=True, timeout=checker_seconds+5, check=False)
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            inputs = list(read_clauses(retained))
            needed = {tuple(sorted(clause)) for clause in inputs}
            for clause in read_clauses(Path(model['cnf'])):
                needed.discard(tuple(sorted(clause)))
            assert not needed
            result['retained_certificate'] = {'cnf': portable(retained), 'cnf_sha256': digest(retained),
                'proof': portable(proof), 'proof_sha256': digest(proof), 'input_clauses': len(inputs),
                'checker_log': portable(log), 'checker_log_sha256': digest(log)}
            result['status'] = 'UNSAT with direct DRAT; cold domain/formula rebuild and proof replay required'
        result['elapsed_seconds'] = time.monotonic()-started
        save()
    except Exception as error:
        result.update(status='error; no unchecked exclusion promoted', error_type=type(error).__name__,
                      error_message=str(error), elapsed_seconds=time.monotonic()-started)
        save()
        raise
    print(json.dumps({key: value for key, value in result.items() if key != 'incidence_witness'}, indent=2), flush=True)
    return result


def replay(model_path, result_path, checker, checker_seconds, output):
    model = checked_model(model_path)
    data, cnf, metadata = rebuild(model['case']['index'])
    assert json.loads(json.dumps(metadata)) == model['formula']
    assert domains.sha(canonical(data[3])) == model['domain_record_sha256']
    with tempfile.TemporaryDirectory(prefix='conway35-incidence-replay-') as directory:
        rebuilt_path = Path(directory)/'rebuilt.cnf'
        cnf.to_file(rebuilt_path)
        assert digest(rebuilt_path) == model['cnf_sha256']
    record = {'status': 'cold attachment domain and exact full CNF rebuilt',
              'model_sha256': digest(model_path), 'cnf_sha256': model['cnf_sha256'],
              'case_index': model['case']['index'], 'whole_complementary_core_excluded': False}
    if result_path is not None:
        result = json.loads(result_path.read_text())
        assert result['model_sha256'] == digest(model_path)
        assert result['source_sha256'] == digest(Path(__file__))
        assert result['cnf_sha256'] == model['cnf_sha256']
        if result['status'].startswith('SAT;'):
            witness = inspect(result['incidence_witness']['selected_columns'], data)
            assert json.loads(json.dumps(witness)) == result['incidence_witness']
            record.update(status='cold formula rebuild and exact binary incidence witness replay passed',
                          a=witness['a'], complete_graph=False)
        elif result['status'].startswith('UNSAT with direct DRAT;'):
            certificate = result['retained_certificate']
            retained, proof = ROOT/certificate['cnf'], ROOT/certificate['proof']
            assert digest(retained) == certificate['cnf_sha256'] and digest(proof) == certificate['proof_sha256']
            inputs = list(read_clauses(retained))
            assert len(inputs) == certificate['input_clauses']
            needed = {tuple(sorted(clause)) for clause in inputs}
            needed.difference_update(tuple(sorted(clause)) for clause in cnf.clauses)
            assert not needed
            checked = subprocess.run([str(checker), str(retained), str(proof), '-t', str(checker_seconds), '-w'],
                                     capture_output=True, text=True, timeout=checker_seconds+5, check=False)
            log = output.with_suffix('.drat.log')
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            record.update(status='cold domain/full-CNF rebuild, retained inclusion, and DRAT replay passed',
                          retained_input_clauses=len(inputs), checker_log=portable(log),
                          checker_log_sha256=digest(log), excluded_indexed_core=model['case']['index'])
        else:
            assert result['status'].startswith('UNKNOWN;')
            record['status'] = 'cold formula rebuild and UNKNOWN binding checked; no exclusion'
    assert not output.exists()
    output.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2), flush=True)
    return record


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    build = commands.add_parser('prepare')
    build.add_argument('--case', type=int, default=0)
    build.add_argument('--model', type=Path, required=True)
    build.add_argument('--cnf', type=Path, required=True)
    run = commands.add_parser('solve')
    run.add_argument('--model', type=Path, required=True)
    run.add_argument('--directory', type=Path, required=True)
    run.add_argument('--seconds', type=float, required=True)
    run.add_argument('--drat-trim', type=Path, required=True)
    run.add_argument('--checker-seconds', type=int, default=30)
    check = commands.add_parser('replay')
    check.add_argument('--model', type=Path, required=True)
    check.add_argument('--result', type=Path)
    check.add_argument('--drat-trim', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    check.add_argument('--checker-seconds', type=int, default=30)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.case, args.model.resolve(), args.cnf.resolve())
    elif args.command == 'solve':
        solve(args.model.resolve(), args.directory.resolve(), args.seconds, args.drat_trim.resolve(), args.checker_seconds)
    else:
        replay(args.model.resolve(), args.result.resolve() if args.result else None,
               args.drat_trim.resolve(), args.checker_seconds, args.output.resolve())
