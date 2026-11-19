"""Bounded exact Gram-downdate preparation for22 unresolved local matchings.

Each completed case binds the entire frozen attachment domain, an exact
positive quotient, all single and pair tests, and direct integral witnesses
for every proposed new unit or binary clause. Progress is saved per case.
No CNF overlay is built and no solver is called.
"""

import argparse
from collections import Counter
import gzip
from itertools import combinations
import json
from pathlib import Path
import time

import complement_rook_35core_gram_downdate as exact


ROOT, LOGS = exact.ROOT, exact.LOGS
CASES = [4, 5, 6, 7, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 22, 23, 24, 25, 26, 27]
SOURCES = ('complement_rook_35core_downdate_census.py', *exact.SOURCE_NAMES)
digest, canonical, portable = exact.digest, exact.canonical, exact.portable


class BudgetExpired(Exception):
    pass


def budget(deadline):
    if deadline is not None and time.monotonic() >= deadline:
        raise BudgetExpired('The bounded census deadline was reached; this case is not certified complete.')


def context():
    prefix_path = exact.PREFIX/'certificate.json'
    assert digest(prefix_path) == exact.PREFIX_SHA
    binding = json.loads(prefix_path.read_text())
    assert binding['source_sha256'] == digest(Path(exact.domains.__file__))
    archive = ROOT/binding['archive']
    assert digest(archive) == binding['archive_sha256']
    raw = gzip.decompress(archive.read_bytes())
    assert exact.domains.sha(raw) == binding['decompressed_jsonl_sha256']
    saved = {record['index']: record for record in map(json.loads, raw.splitlines())}
    domain, index = exact.domains.load_domain()
    assert canonical(index)+b'\n' == (exact.PREFIX/'all-core-index.json').read_bytes()
    assert digest(exact.PREFIX/'all-core-index.json') == binding['index_sha256']
    assert set(CASES) <= saved.keys() and set(CASES) | {0, 1, 2, 3, 8, 21} == set(range(28))
    return domain, index, saved, binding


def scan(gram, columns, masks, q, deadline):
    scale, inverse = q['inverse_denominator'], q['inverse_numerator']
    coordinates = [[j for j, i in enumerate(exact.KEEP) if mask >> i & 1] for mask in masks]
    for mask, support in zip(masks, coordinates):
        assert [sum(row[j] for j in support) for row in q['embedding']] == [int(mask >> i & 1) for i in range(35)]
    qx = [[sum(row[j] for j in support) for row in inverse] for support in coordinates]
    numerators = [sum(vector[j] for j in support) for vector, support in zip(qx, coordinates)]
    assert all(value > 0 for value in numerators)
    singles, rejected = [], set()
    for column, numerator in enumerate(numerators):
        if numerator > scale:
            vector = [0]*35
            for i, value in zip(exact.KEEP, qx[column]):
                vector[i] = value
            vector = exact.primitive(vector)
            value = exact.residual_value(gram, vector, [masks[column]])
            assert value < 0
            singles.append({'column': column, 'negative_vector': vector, 'negative_quadratic_value': value})
            rejected.add(column)
    sites = [[i for i in range(35) if mask >> i & 1] for mask in masks]
    counts, negative_pairs, additional = Counter(), [], []
    minimum_determinant = None
    for left in range(len(masks)):
        if left % 32 == 0:
            budget(deadline)
        for right in range(left+1, len(masks)):
            shared = masks[left] & masks[right]
            common = [i for i in sites[left] if shared >> i & 1]
            bits = (columns[left][0] == columns[right][0], shared.bit_count() >= 3,
                    any(gram[i][j] == 1 for place, i in enumerate(common) for j in common[place:]))
            classification = ''.join(str(int(value)) for value in bits)
            counts['all:'+classification] += 1
            if left in rejected or right in rejected:
                counts['excluded_by_single:'+classification] += 1
                continue
            cross = sum(qx[left][j] for j in coordinates[right])
            determinant = (scale-numerators[left])*(scale-numerators[right])-cross*cross
            candidate = [determinant, left, right, cross]
            if minimum_determinant is None or candidate < minimum_determinant:
                minimum_determinant = candidate
            counts['Schur_tested:'+classification] += 1
            if determinant < 0:
                negative_pairs.append([left, right])
                counts['negative:'+classification] += 1
                if classification == '000':
                    vector, value = exact.pair_vector(gram, exact.KEEP, qx[left], qx[right],
                                                      numerators[left], numerators[right], cross, scale,
                                                      [masks[left], masks[right]])
                    additional.append({'columns': [left, right], 'inverse_cross_numerator': cross,
                                       'Schur_determinant_numerator': determinant,
                                       'negative_vector': vector, 'negative_quadratic_value': value})
    count = len(masks)*(len(masks)-1)//2
    assert sum(v for k, v in counts.items() if k.startswith('all:')) == count
    assert sum(v for k, v in counts.items() if k.startswith(('Schur_tested:', 'excluded_by_single:'))) == count
    assert len(negative_pairs) == sum(v for k, v in counts.items() if k.startswith('negative:'))
    return {'column_leverage_numerators': numerators, 'single_exclusion_witnesses': singles,
            'leverage_range_numerators': [min(numerators), max(numerators)],
            'all_column_pairs_accounted_for': count,
            'pairs_tested_after_single_exclusions': sum(v for k, v in counts.items() if k.startswith('Schur_tested:')),
            'classification_bits': ['same_original_signature', 'shared_core_triple', 'shared_quota_one_Gram_pair'],
            'classification_counts': dict(sorted(counts.items())),
            'negative_pairs_between_surviving_single_columns': negative_pairs,
            'additional_binary_exclusion_witnesses': additional,
            'minimum_Schur_determinant_numerator': minimum_determinant,
            'arithmetic': 'Python arbitrary-precision integers and exact fractions',
            'largest_absolute_inverse_numerator': max(abs(value) for row in inverse for value in row)}


def build(case_index, ctx, deadline=None, saved=None):
    budget(deadline)
    domain, index, saved_records, prefix = ctx
    case = index['cases'][case_index]
    assert case_index in CASES and case['local_set_orbit'] == 0
    record = exact.domains.analyze_core(domain, case)
    assert json.loads(json.dumps(record)) == saved_records[case_index]
    core, gram, kernels = exact.domains.core_matrix(domain, case)
    _, _, _, masks, _ = exact.domains.sparse_rows(domain, core, gram, record['columns'])
    model_path = LOGS/f'complement-rook-35core-first-local-sweep01/case{case_index:04d}-model.json'
    model = json.loads(model_path.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert case == model['case']
    assert exact.domains.sha(canonical(record)) == model['domain_record_sha256']
    assert record['column_domain_sha256'] == model['column_domain_sha256']
    assert record['Gram_sha256'] == model['Gram_sha256']
    q = exact.quotient(gram, kernels, None if saved is None else saved['quotient'])
    budget(deadline)
    result = {'version': 1,
              'status': 'complete exact one/two-column Gram-downdate preparation for one indexed35-core',
              'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in SOURCES},
              'case': case, 'original_model': portable(model_path), 'original_model_sha256': digest(model_path),
              'original_cnf_sha256': model['cnf_sha256'],
              'original_variables': model['formula']['variables'], 'original_clauses': model['formula']['clauses'],
              'prefix_certificate_sha256': exact.PREFIX_SHA,
              'complete_index_sha256': prefix['index_sha256'],
              'column_domain_sha256': record['column_domain_sha256'],
              'domain_record_sha256': model['domain_record_sha256'], 'Gram_sha256': record['Gram_sha256'],
              'core_adjacency_bit_rows': core, 'Gram': gram, 'attachment_columns': record['columns'],
              'quotient': q, 'scan': scan(gram, record['columns'], masks, q, deadline),
              'scope': {'solver_called': False, 'overlay_CNF_built': False, 'whole_core_excluded': False,
                        'cuts_follow_from_original_Gram_equalities': True,
                        'pair_conflicts_with_a_rejected_single_are_covered_by_its_unit_clause': True}}
    if saved is not None:
        assert result == saved
    return result


def clauses(certificate):
    scan = certificate['scan']
    result = [[-w['column']-1] for w in scan['single_exclusion_witnesses']]
    result.extend([[-i-1 for i in witness['columns']] for witness in scan['additional_binary_exclusion_witnesses']])
    assert len(result) == len({tuple(clause) for clause in result})
    return (f'p cnf {len(certificate["attachment_columns"])} {len(result)}\n'+
            ''.join(' '.join(map(str, clause))+' 0\n' for clause in result)).encode()


def summary(certificate):
    s = certificate['scan']
    units, pairs = len(s['single_exclusion_witnesses']), len(s['additional_binary_exclusion_witnesses'])
    return {'case_index': certificate['case']['index'], 'columns': len(certificate['attachment_columns']),
            'exact_Gram_rank': certificate['quotient']['exact_Gram_rank'],
            'inverse_denominator': certificate['quotient']['inverse_denominator'],
            'single_exclusions': units, 'all_pairs_accounted_for': s['all_column_pairs_accounted_for'],
            'negative_pairs_after_single_exclusions': len(s['negative_pairs_between_surviving_single_columns']),
            'additional_binary_exclusions': pairs,
            'original_variables': certificate['original_variables'],
            'original_clauses': certificate['original_clauses'],
            'overlay_clauses_if_built': certificate['original_clauses']+units+pairs}


def atomic_json(path, value):
    temporary = path.with_suffix('.writing')
    temporary.write_text(json.dumps(value, indent=2)+'\n')
    temporary.replace(path)


def generate(directory, seconds):
    assert not directory.exists() and 0 < seconds <= 120
    directory.mkdir(parents=True)
    started, deadline = time.monotonic(), time.monotonic()+seconds
    progress = {'status': 'running bounded exact preparation; no solver', 'complete': False,
                'requested_cases': CASES, 'completed_cases': [], 'unprocessed_cases': CASES[:],
                'wall_budget_seconds': seconds,
                'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in SOURCES},
                'case_records': [], 'controls': exact.controls(), 'solver_called': False,
                'full_CNF_builds': 0, 'scope': '22 unresolved matchings of the first local8 set only'}
    def save():
        progress['elapsed_seconds'] = time.monotonic()-started
        atomic_json(directory/'progress.json', progress)
    save()
    try:
        ctx = context()
        progress['complete_index_sha256'] = ctx[-1]['index_sha256']
        for case_index in CASES:
            budget(deadline)
            case_started = time.monotonic()
            certificate = build(case_index, ctx, deadline)
            raw = canonical(certificate)+b'\n'
            path, fragment = directory/f'case{case_index:04d}.json.gz', directory/f'case{case_index:04d}-clauses.cnf'
            path.write_bytes(gzip.compress(raw, compresslevel=9, mtime=0))
            fragment.write_bytes(clauses(certificate))
            item = summary(certificate)
            item.update(certificate=portable(path), certificate_sha256=digest(path),
                        decompressed_certificate_sha256=exact.domains.sha(raw),
                        binary_fragment=portable(fragment), binary_fragment_sha256=digest(fragment),
                        compressed_certificate_bytes=path.stat().st_size,
                        case_seconds=time.monotonic()-case_started)
            progress['case_records'].append(item)
            progress['completed_cases'].append(case_index)
            progress['unprocessed_cases'] = [i for i in CASES if i not in progress['completed_cases']]
            save()
            print(json.dumps(item), flush=True)
        progress.update(status='complete exact preparation for all22 requested cases; no solver', complete=True)
    except BudgetExpired as error:
        progress.update(status='bounded preparation stopped at deadline; unprocessed cases remain open',
                        stop_reason=str(error))
    except Exception as error:
        progress.update(status='preparation stopped on an error; no incomplete case promoted',
                        error_type=type(error).__name__, error_message=str(error))
        save()
        raise
    save()
    atomic_json(directory/'terminal.json', progress)
    print(json.dumps({key: value for key, value in progress.items() if key != 'case_records'}, indent=2), flush=True)


def replay(directory, case_index, output):
    assert not output.exists() and case_index in CASES
    progress = json.loads((directory/'terminal.json').read_text())
    for name, expected in progress['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    item = next(record for record in progress['case_records'] if record['case_index'] == case_index)
    path, fragment = ROOT/item['certificate'], ROOT/item['binary_fragment']
    assert digest(path) == item['certificate_sha256'] and digest(fragment) == item['binary_fragment_sha256']
    raw = gzip.decompress(path.read_bytes())
    assert exact.domains.sha(raw) == item['decompressed_certificate_sha256']
    saved = json.loads(raw)
    certificate = build(case_index, context(), saved=saved)
    assert canonical(certificate)+b'\n' == raw and clauses(certificate) == fragment.read_bytes()
    report = summary(certificate)
    report.update(status='PASS: complete domain, exact quotient, all pairs and every exported negative vector replayed',
                  certificate_sha256=digest(path), binary_fragment_sha256=digest(fragment), solver_called=False)
    output.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    gen = commands.add_parser('generate')
    gen.add_argument('--directory', type=Path, required=True)
    gen.add_argument('--seconds', type=float, default=120)
    check = commands.add_parser('replay')
    check.add_argument('--directory', type=Path, required=True)
    check.add_argument('--case', type=int, required=True)
    check.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'generate':
        generate(args.directory.resolve(), args.seconds)
    else:
        replay(args.directory.resolve(), args.case, args.output.resolve())
