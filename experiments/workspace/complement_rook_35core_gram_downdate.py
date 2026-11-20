"""Exact one- and two-column Gram downdates for indexed35-core case2.

Only standard-library arithmetic is used. The complete attachment domain
is rebuilt and bound to the frozen prefix. A rank31 congruence, positive
rational LDL, and integer inverse identity justify the small Schur tests.
Every exported binary exclusion also has a directly checked integral
negative vector for the full35-by35 Gram remainder. No solver is called.
"""

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations, permutations
import json
from math import gcd
from pathlib import Path
import time

import complement_rook_35core_domains as domains


ROOT, LOGS = domains.ROOT, domains.LOGS
PREFIX = LOGS/'complement-rook-35core-domains-prefix01'
PREFIX_SHA = 'a567f58470e42ab275bf330af30fa424786eb2243c568ba1c750b6bb5cc80a90'
SOURCE_NAMES = ('complement_rook_35core_gram_downdate.py',
                'complement_rook_35core_domains.py',
                'complement_rook_projector_schur.py',
                'complement_rook_local_star_census.py')
DELETED = [0, 9, 18, 27]
KEEP = [i for i in range(35) if i not in DELETED]
canonical, digest = domains.canonical, domains.digest


def portable(path):
    return str(path.resolve().relative_to(ROOT))


def multiply(a, b):
    columns = list(zip(*b))
    return [[sum(x*y for x, y in zip(row, col)) for col in columns] for row in a]


def transpose(a):
    return [list(row) for row in zip(*a)]


def fraction_pair(value):
    value = Fraction(value)
    return [value.numerator, value.denominator]


def positive_ldl(matrix):
    """Save the complete congruence, rather than just pivot signs."""
    n = len(matrix)
    lower = [[Fraction(i == j) for j in range(n)] for i in range(n)]
    diagonal = []
    for i in range(n):
        diagonal.append(Fraction(matrix[i][i])-
                        sum(lower[i][k]**2*diagonal[k] for k in range(i)))
        assert diagonal[i] > 0
        for j in range(i+1, n):
            lower[j][i] = (matrix[j][i]-sum(lower[j][k]*lower[i][k]*diagonal[k]
                                           for k in range(i)))/diagonal[i]
    result = {'lower': [[fraction_pair(x) for x in row] for row in lower],
              'positive_diagonal': [fraction_pair(x) for x in diagonal]}
    check_ldl(matrix, result)
    return result


def check_ldl(matrix, saved):
    n = len(matrix)
    lower = [[Fraction(*value) for value in row] for row in saved['lower']]
    diagonal = [Fraction(*value) for value in saved['positive_diagonal']]
    assert len(lower) == len(diagonal) == n and all(len(row) == n for row in lower)
    assert all(value > 0 for value in diagonal)
    assert all(lower[i][i] == 1 and all(lower[i][j] == 0 for j in range(i+1, n))
               for i in range(n))
    assert all(sum(lower[i][k]*diagonal[k]*lower[j][k] for k in range(n)) == matrix[i][j]
               for i in range(n) for j in range(n))
    determinant = Fraction(1)
    for value in diagonal:
        determinant *= value
    assert determinant.denominator == 1
    return determinant.numerator


def load_case():
    prefix_certificate = PREFIX/'certificate.json'
    assert digest(prefix_certificate) == PREFIX_SHA
    binding = json.loads(prefix_certificate.read_text())
    assert binding['source_sha256'] == digest(Path(domains.__file__))
    archive = ROOT/binding['archive']
    assert digest(archive) == binding['archive_sha256']
    raw = gzip.decompress(archive.read_bytes())
    assert domains.sha(raw) == binding['decompressed_jsonl_sha256']
    saved_records = {item['index']: item for item in map(json.loads, raw.splitlines())}
    domain, index = domains.load_domain()
    assert canonical(index)+b'\n' == (PREFIX/'all-core-index.json').read_bytes()
    assert digest(PREFIX/'all-core-index.json') == binding['index_sha256']
    case = index['cases'][2]
    record = domains.analyze_core(domain, case)
    assert json.loads(json.dumps(record)) == saved_records[2]
    core, gram, kernels = domains.core_matrix(domain, case)
    _, _, _, masks, _ = domains.sparse_rows(domain, core, gram, record['columns'])
    bindings = {
        'prefix_certificate': portable(prefix_certificate),
        'prefix_certificate_sha256': PREFIX_SHA,
        'attachment_archive': portable(archive),
        'attachment_archive_sha256': binding['archive_sha256'],
        'decompressed_attachment_archive_sha256': binding['decompressed_jsonl_sha256'],
        'complete_core_index': portable(PREFIX/'all-core-index.json'),
        'complete_core_index_sha256': binding['index_sha256'],
        'complete_index_cases': len(index['cases']),
        'root_census_sha256': domains.CENSUS_SHA,
        'base_domain_sha256': domain[-1],
        'case_domain_record_sha256': domains.sha(canonical(record)),
        'column_domain_sha256': record['column_domain_sha256'],
        'Gram_sha256': record['Gram_sha256'],
    }
    return case, record, core, gram, kernels, masks, bindings


def quotient(gram, kernels, saved=None):
    pivot = [[row[i] for i in DELETED] for row in kernels]
    assert pivot == [[1, 0, 0, 0], [1, -1, 0, 0],
                     [1, 0, -1, 0], [-2, 1, 1, 1]]
    determinant = sum((-1)**sum(p[i] > p[j] for i in range(4) for j in range(i+1, 4)) *
                      pivot[0][p[0]]*pivot[1][p[1]]*pivot[2][p[2]]*pivot[3][p[3]]
                      for p in permutations(range(4)))
    assert determinant == 1
    inverse_pivot = [[1, 0, 0, 0], [1, -1, 0, 0],
                     [1, 0, -1, 0], [0, 1, 1, 1]]
    assert multiply(pivot, inverse_pivot) == [[int(i == j) for j in range(4)] for i in range(4)]
    free_kernels = [[row[i] for i in KEEP] for row in kernels]
    dependent = multiply(inverse_pivot, free_kernels)
    embedding = [[0]*31 for _ in range(35)]
    for j, i in enumerate(KEEP):
        embedding[i][j] = 1
    for j, i in enumerate(DELETED):
        embedding[i] = [-value for value in dependent[j]]
    principal = [[gram[i][j] for j in KEEP] for i in KEEP]
    assert multiply(kernels, embedding) == [[0]*31 for _ in range(4)]
    assert multiply(multiply(embedding, principal), transpose(embedding)) == gram
    if saved is None:
        ldl = positive_ldl(principal)
        scale, inverse = domains.base_helper.exact_inverse(principal)
    else:
        ldl = saved['positive_LDL']
        scale, inverse = saved['inverse_denominator'], saved['inverse_numerator']
    determinant = check_ldl(principal, ldl)
    assert type(scale) is int and scale > 0
    assert len(inverse) == 31 and all(len(row) == 31 for row in inverse)
    assert all(type(value) is int for row in inverse for value in row)
    assert inverse == transpose(inverse)
    assert multiply(principal, inverse) == [[scale*int(i == j) for j in range(31)] for i in range(31)]
    result = {'deleted_coordinates': DELETED, 'kept_coordinates': KEEP,
              'kernel_vectors': kernels, 'kernel_pivot_determinant': 1,
              'embedding': embedding, 'principal_Gram': principal,
              'positive_LDL': ldl, 'principal_determinant': determinant,
              'inverse_denominator': scale, 'inverse_numerator': inverse,
              'exact_Gram_rank': 31,
              'identities_checked': ['kernel*embedding=0', 'G=E*K*E^T',
                                     'K=L*diag(d)*L^T with all d>0', 'K*Q=D*I']}
    if saved is not None:
        assert result == saved
    return result


def primitive(vector):
    divisor = 0
    for value in vector:
        divisor = gcd(divisor, abs(value))
    assert divisor > 0
    vector = [value//divisor for value in vector]
    if next(value for value in vector if value) < 0:
        vector = [-value for value in vector]
    return vector


def quadratic(matrix, vector):
    return sum(vector[i]*sum(value*vector[j] for j, value in enumerate(row))
               for i, row in enumerate(matrix))


def residual_value(gram, vector, masks):
    return quadratic(gram, vector)-sum(sum(vector[i] for i in range(len(vector)) if mask >> i & 1)**2
                                        for mask in masks)


def pair_vector(gram, keep, qx, qy, n_x, n_y, cross, scale, masks):
    a, b = scale-n_x, scale-n_y
    assert a >= 0 and b >= 0 and a*b < cross*cross
    if a > 0:
        coefficients = [cross, a]
    elif b > 0:
        coefficients = [b, cross]
    else:
        coefficients = [1, 1 if cross > 0 else -1]
    c0, c1 = coefficients
    assert a*c0*c0-2*cross*c0*c1+b*c1*c1 < 0
    vector = [0]*len(gram)
    for i, x, y in zip(keep, qx, qy):
        vector[i] = c0*x+c1*y
    vector = primitive(vector)
    value = residual_value(gram, vector, masks)
    assert value < 0
    return vector, value


def scan(gram, columns, masks, q):
    scale, inverse = q['inverse_denominator'], q['inverse_numerator']
    embedding = q['embedding']
    coordinates = [[j for j, i in enumerate(KEEP) if mask >> i & 1] for mask in masks]
    for mask, support in zip(masks, coordinates):
        assert [sum(row[j] for j in support) for row in embedding] == [int(mask >> i & 1) for i in range(35)]
    qx = [[sum(row[j] for j in support) for row in inverse] for support in coordinates]
    numerators = [sum(vector[j] for j in support) for vector, support in zip(qx, coordinates)]
    single_failures = []
    for index, numerator in enumerate(numerators):
        if numerator > scale:
            vector = [0]*35
            for i, value in zip(KEEP, qx[index]):
                vector[i] = value
            vector = primitive(vector)
            value = residual_value(gram, vector, [masks[index]])
            assert value < 0
            single_failures.append({'column': index, 'negative_vector': vector,
                                    'negative_quadratic_value': value})
    assert not single_failures  # This artifact is deliberately scoped to case2.
    assert all(0 < numerator < scale for numerator in numerators)
    sites = [[i for i in range(35) if mask >> i & 1] for mask in masks]
    counts, negative_pairs, new_witnesses = Counter(), [], []
    minimum_determinant = None
    for left, right in combinations(range(len(masks)), 2):
        cross = sum(qx[left][j] for j in coordinates[right])
        determinant = (scale-numerators[left])*(scale-numerators[right])-cross*cross
        candidate = [determinant, left, right, cross]
        if minimum_determinant is None or candidate < minimum_determinant:
            minimum_determinant = candidate
        overlap_mask = masks[left] & masks[right]
        common = [i for i in sites[left] if overlap_mask >> i & 1]
        same_original = columns[left][0] == columns[right][0]
        shared_triple = overlap_mask.bit_count() >= 3
        quota_one = any(gram[i][j] == 1 for place, i in enumerate(common) for j in common[place:])
        classification = f'{int(same_original)}{int(shared_triple)}{int(quota_one)}'
        counts['all:'+classification] += 1
        if determinant < 0:
            counts['negative:'+classification] += 1
            negative_pairs.append([left, right])
            if classification == '000':
                vector, value = pair_vector(gram, KEEP, qx[left], qx[right], numerators[left],
                                            numerators[right], cross, scale, [masks[left], masks[right]])
                new_witnesses.append({'columns': [left, right], 'inverse_cross_numerator': cross,
                                      'Schur_determinant_numerator': determinant,
                                      'negative_vector': vector, 'negative_quadratic_value': value})
    count = len(masks)*(len(masks)-1)//2
    assert sum(value for key, value in counts.items() if key.startswith('all:')) == count
    assert len(masks) == 1287 and count == 827541
    assert len(negative_pairs) == 5545 and len(new_witnesses) == 886
    assert counts['negative:000']+counts['negative:001'] == 1434
    return {'column_leverage_numerators': numerators,
            'single_exclusions': single_failures,
            'leverage_range_numerators': [min(numerators), max(numerators)],
            'pairs_checked': count,
            'classification_bits': ['same_original_signature', 'shared_core_triple', 'shared_quota_one_Gram_pair'],
            'classification_counts': dict(sorted(counts.items())),
            'all_negative_pairs': negative_pairs,
            'negative_pairs_beyond_multiplicity_and_triple_packing': 1434,
            'negative_pairs_beyond_all_three_elementary_tests': len(new_witnesses),
            'additional_binary_exclusion_witnesses': new_witnesses,
            'minimum_Schur_determinant_numerator': minimum_determinant,
            'arithmetic': 'Python arbitrary-precision integers and fractions; no floating point or fixed-width sums',
            'largest_absolute_inverse_numerator': max(abs(value) for row in inverse for value in row),
            'inverse_denominator_exceeds_signed_int64': scale > 2**63-1}


def controls():
    """An actual small incidence Gram and an impossible duplicate pair."""
    gram = [[2, 1], [1, 2]]
    actual_masks = [1, 2, 3]
    assert all(sum((mask >> i & 1)*(mask >> j & 1) for mask in actual_masks) == gram[i][j]
               for i in range(2) for j in range(2))
    scale, inverse = domains.base_helper.exact_inverse(gram)
    assert (scale, inverse) == (3, [[2, -1], [-1, 2]])
    qx = [[sum(row[j] for j in range(2) if mask >> j & 1) for row in inverse]
          for mask in actual_masks]
    numerators = [sum(vector[j] for j in range(2) if mask >> j & 1)
                  for vector, mask in zip(qx, actual_masks)]
    assert all(value <= scale for value in numerators)
    for i, j in combinations(range(3), 2):
        cross = sum(qx[i][k] for k in range(2) if actual_masks[j] >> k & 1)
        assert (scale-numerators[i])*(scale-numerators[j])-cross*cross == 0
    vector, value = pair_vector(gram, [0, 1], qx[2], qx[2], 2, 2, 2, 3, [3, 3])
    assert vector == [1, 1] and value == -2
    return {'exact_small_incidence_columns': actual_masks,
            'all_three_actual_pairs_pass': True,
            'impossible_duplicate_pair_vector': vector,
            'impossible_duplicate_pair_value': value,
            'solver_called': False}


def build(saved=None):
    case, record, core, gram, kernels, masks, bindings = load_case()
    q = quotient(gram, kernels, None if saved is None else saved['quotient'])
    result = {'version': 1,
              'status': 'exact additional binary Gram-downdate consequences for indexed35-core case2',
              'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in SOURCE_NAMES},
              'bindings': bindings, 'case': case, 'core_adjacency_bit_rows': core,
              'Gram': gram, 'attachment_columns': record['columns'],
              'quotient': q, 'scan': scan(gram, record['columns'], masks, q),
              'controls': controls(),
              'scope': {'case_index': 2, 'other_cases_tested': False,
                        'new_solver_call': False, 'whole_core_excluded': False,
                        'constraints_are_consequences_of_the_existing_Gram_equations': True,
                        'semantic_irredundancy_claim': False}}
    return result


def clause_bytes(certificate):
    witnesses = certificate['scan']['additional_binary_exclusion_witnesses']
    clauses = [tuple(-column-1 for column in witness['columns']) for witness in witnesses]
    assert len(clauses) == len(set(clauses)) == 886
    return (f'p cnf {len(certificate["attachment_columns"])} {len(clauses)}\n'+
            ''.join(f'{a} {b} 0\n' for a, b in clauses)).encode()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--clauses', type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    started = time.monotonic()
    if args.write:
        assert not args.certificate.exists() and not args.clauses.exists()
        certificate = build()
        raw = canonical(certificate)+b'\n'
        data = gzip.compress(raw, compresslevel=9, mtime=0) if args.certificate.suffix == '.gz' else raw
        args.certificate.parent.mkdir(parents=True, exist_ok=True)
        args.certificate.write_bytes(data)
        args.clauses.write_bytes(clause_bytes(certificate))
    else:
        data = args.certificate.read_bytes()
        raw = gzip.decompress(data) if args.certificate.suffix == '.gz' else data
        saved = json.loads(raw)
        for name, expected in saved['source_hashes'].items():
            assert digest(Path(__file__).with_name(name)) == expected
        certificate = build(saved)
        assert canonical(certificate)+b'\n' == raw
        assert args.clauses.read_bytes() == clause_bytes(certificate)
    summary = {'status': 'PASS', 'mode': 'write' if args.write else 'exact replay',
               'case_index': 2, 'columns': len(certificate['attachment_columns']),
               'rank': certificate['quotient']['exact_Gram_rank'],
               'inverse_denominator': certificate['quotient']['inverse_denominator'],
               'single_exclusions': len(certificate['scan']['single_exclusions']),
               'pairs_checked': certificate['scan']['pairs_checked'],
               'negative_pairs': len(certificate['scan']['all_negative_pairs']),
               'additional_directly_checked_negative_vectors': 886,
               'certificate': portable(args.certificate), 'certificate_sha256': digest(args.certificate),
               'decompressed_certificate_sha256': hashlib.sha256(raw).hexdigest(),
               'certificate_bytes': len(data), 'decompressed_certificate_bytes': len(raw),
               'binary_clauses': portable(args.clauses), 'binary_clauses_sha256': digest(args.clauses),
               'elapsed_seconds': time.monotonic()-started, 'solver_called': False,
               'whole_core_exclusion': False}
    print(json.dumps(summary, indent=2), flush=True)


if __name__ == '__main__':
    main()
