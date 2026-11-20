"""Attribute retained original-only case2 inputs to exact counter families.

This is a read-only structural audit, not a new proof or solver query.
The annotated reconstruction must match the frozen complete CNF bytes.
It also enumerates minimal partial matchings covered by the six already
certified first-local cases, without claiming any new case exclusion.
"""

import argparse
from collections import Counter, defaultdict
from itertools import combinations
import json
from pathlib import Path
import tempfile
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool

import complement_rook_35core_incidence as original
import complement_rook_35core_case0002_original_certificate as binding


ROOT, LOGS = original.ROOT, original.LOGS
digest, canonical = original.digest, original.canonical


def audit():
    assert digest(binding.BASE_MODEL) == binding.BASE_MODEL_SHA
    assert digest(binding.RESULT) == binding.RESULT_SHA
    model = original.checked_model(binding.BASE_MODEL)
    data = original.load(2)
    domain, index, case, record, core, gram, rows, originals, triples, masks = data
    pool, cnf, groups = IDPool(start_from=len(masks)+1), CNF(), []
    def add(kind, labels, members, quota, equality):
        first, old_top = len(cnf.clauses), pool.top
        literals = [member+1 for member in members]
        if literals:
            factory = CardEnc.equals if equality else CardEnc.atmost
            cnf.extend(factory(literals, quota, vpool=pool, encoding=EncType.seqcounter).clauses)
        else:
            assert quota == 0
        groups.append({'index': len(groups), 'kind': kind, 'labels': labels,
                       'quota': quota, 'member_count': len(members),
                       'member_columns_sha256': original.domains.sha(canonical(members)),
                       'clause_interval': [first, len(cnf.clauses)],
                       'auxiliary_interval': [old_top+1, pool.top+1]})
        return len(groups)-1
    seen = {}
    for pair, members in zip(original.domains.PAIRS, rows):
        quota = gram[pair[0]][pair[1]]
        key = tuple(members), quota
        if key in seen:
            groups[seen[key]]['labels'].append(list(pair))
        else:
            seen[key] = add('Gram', [list(pair)], members, quota, True)
    for source, members in sorted(originals.items()):
        if len(members) > 1:
            add('original_signature_multiplicity', [source], members, 1, False)
    for triple, members in sorted(triples.items()):
        if len(members) > 1 and all(gram[i][j] != 1 for i, j in combinations(triple, 2)):
            add('additional_core_triple', [list(triple)], members, 1, False)
    assert (cnf.nv, len(cnf.clauses)) == (114512, 233919)
    with tempfile.TemporaryDirectory(prefix='conway35-case2-support-') as directory:
        path = Path(directory)/'annotated.cnf'
        cnf.to_file(path)
        assert digest(path) == model['cnf_sha256']
    lookup = defaultdict(set)
    for group in groups:
        start, stop = group['clause_interval']
        for clause in cnf.clauses[start:stop]:
            lookup[tuple(sorted(clause))].add(group['index'])
    result = json.loads(binding.RESULT.read_text())
    retained = ROOT/result['retained_certificate']['cnf']
    assert digest(retained) == result['retained_certificate']['cnf_sha256']
    inputs = list(original.read_clauses(retained))
    chosen_counts, possible_counts, primary = Counter(), Counter(), set()
    ambiguous = 0
    for clause in inputs:
        alternatives = lookup[tuple(sorted(clause))]
        assert alternatives
        chosen_counts[min(alternatives)] += 1
        possible_counts.update(alternatives)
        ambiguous += len(alternatives) > 1
        primary.update(abs(value)-1 for value in clause if abs(value) <= len(masks))
    chosen = []
    for number in sorted(chosen_counts):
        group = dict(groups[number])
        group['assigned_retained_input_clauses'] = chosen_counts[number]
        group['possible_retained_input_clauses'] = possible_counts[number]
        chosen.append(group)
    kinds = Counter()
    for group in chosen:
        kinds[group['kind']] += group['assigned_retained_input_clauses']
    def block(i):
        return 'RSTL'[min(i//9, 3)]
    gram_coordinates = sorted({tuple(pair) for group in chosen if group['kind'] == 'Gram'
                               for pair in group['labels']})
    types = Counter(block(i)+block(j)+(' diagonal' if i == j else '') for i, j in gram_coordinates)
    touched = sorted({v for pair in gram_coordinates for v in pair} |
                     {v for group in chosen if group['kind'] == 'additional_core_triple'
                      for triple in group['labels'] for v in triple})
    # Coverage only: each claimed forbidden pattern uses previously checked case proofs.
    matchings = {case['index']: frozenset(map(tuple, case['matching'])) for case in index['cases'][:28]}
    excluded = {0, 1, 2, 3, 8, 21}
    patterns = sorted({tuple(sorted(part)) for matching in matchings.values()
                       for size in range(1, 5) for part in combinations(sorted(matching), size)},
                      key=lambda p: (len(p), p))
    minimal = []
    for pattern in patterns:
        members = sorted(i for i, matching in matchings.items() if set(pattern) <= matching)
        if set(members) <= excluded and not any(set(old['edges']) <= set(pattern) for old in minimal):
            minimal.append({'edges': pattern, 'covered_cases': members})
    return {
        'status': 'exact retained-family attribution and finite partial-matching coverage; no new solve',
        'source_sha256': digest(Path(__file__)),
        'original_model_sha256': binding.BASE_MODEL_SHA,
        'original_cnf_sha256': model['cnf_sha256'],
        'retained_cnf_sha256': digest(retained),
        'retained_inputs': len(inputs),
        'counter_groups_in_full_formula': len(groups),
        'retained_clause_attribution_rule': 'least indexed group among all exact clause occurrences',
        'retained_inputs_with_multiple_possible_groups': ambiguous,
        'retained_input_counts_by_assigned_family': dict(kinds),
        'assigned_groups_by_family': dict(Counter(g['kind'] for g in chosen)),
        'retained_counter_groups': chosen,
        'Gram_coordinate_rows_covered_by_assigned_groups': [list(pair) for pair in gram_coordinates],
        'Gram_coordinate_type_counts': dict(sorted(types.items())),
        'core_coordinates_in_assigned_Gram_and_triple_groups': touched,
        'retained_primary_columns': sorted(primary),
        'retained_primary_column_count': len(primary),
        'retained_original_signature_count': len({record['columns'][i][0] for i in primary}),
        'minimal_partial_matchings_covered_by_six_verified_cases': minimal,
        'scope': {'case2_only_for_counter_attribution': True,
                  'omitted_counter_does_not_remove_domain_dependence': True,
                  'partial_matching_coverage_is_not_a_new_individual_case_exclusion': True,
                  'solver_called': False, 'new_proof_claim': False},
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    start = time.monotonic()
    result = audit()
    result['elapsed_seconds'] = time.monotonic()-start
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    omitted = {'retained_counter_groups', 'Gram_coordinate_rows_covered_by_assigned_groups', 'retained_primary_columns'}
    print(json.dumps({k: v for k, v in result.items() if k not in omitted}, indent=2), flush=True)
