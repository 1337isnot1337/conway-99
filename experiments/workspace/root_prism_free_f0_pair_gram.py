"""Exact full-domain one-column Gram screen for the split component0 pair.

The 39-core and its 39,168 columns are independent of the saved incidence
design. A separate diagnostic checks only the fixed-design quota system
modulo two. All arithmetic and replay use the standard library. No solver
or two-column census is called.
"""

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations
import json
from math import gcd, lcm
from pathlib import Path
import time

import root_prism_free_f0_components as components
import root_prism_free_f0_pair_clauses as motifs


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
FIXED_RESULT = LOGS/'f0-incidence-case00-run01/result.json'
FIXED_SHA = '64d5411e04764b0d7e7157c47b67d759e536a401fee8fe36e274943f2fda4abf'
DELETED = [0, 1, 2, 3, 9, 21]
KEEP = [i for i in range(39) if i not in DELETED]
canonical = components.canonical


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def matrix_product(a, b):
    columns = list(zip(*b))
    return [[sum(x*y for x, y in zip(row, col)) for col in columns] for row in a]


def transpose(a):
    return [list(row) for row in zip(*a)]


def exact_inverse(matrix):
    n = len(matrix)
    work = [[Fraction(x) for x in row]+[Fraction(i == j) for j in range(n)]
            for i, row in enumerate(matrix)]
    for j in range(n):
        pivot = next(i for i in range(j, n) if work[i][j])
        work[j], work[pivot] = work[pivot], work[j]
        scale = work[j][j]
        work[j] = [x/scale for x in work[j]]
        for i in range(n):
            if i != j and work[i][j]:
                factor = work[i][j]
                work[i] = [x-factor*y for x, y in zip(work[i], work[j])]
    inverse = [row[n:] for row in work]
    denominator = lcm(*(x.denominator for row in inverse for x in row))
    numerator = [[int(x*denominator) for x in row] for row in inverse]
    assert matrix_product(matrix, numerator) == [
        [denominator*int(i == j) for j in range(n)] for i in range(n)]
    return denominator, numerator


def positive_ldl(matrix):
    n = len(matrix)
    lower = [[Fraction(i == j) for j in range(n)] for i in range(n)]
    diagonal = []
    for i in range(n):
        value = Fraction(matrix[i][i])-sum(lower[i][k]**2*diagonal[k] for k in range(i))
        assert value > 0
        diagonal.append(value)
        for j in range(i+1, n):
            lower[j][i] = (matrix[j][i]-sum(lower[j][k]*lower[i][k]*diagonal[k]
                                          for k in range(i)))/value
    return {'lower': [[[v.numerator, v.denominator] for v in row] for row in lower],
            'positive_diagonal': [[v.numerator, v.denominator] for v in diagonal]}


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


def profile(triple):
    return tuple(sum(v//6 == fiber for v in triple) for fiber in range(3))


def load_core():
    """Rebuild the component itself; no fixed-design file enters this step."""
    saved = motifs.load()
    record = saved['representatives'][0]
    first, pool, qs = components.input_domain()
    p, r, q = record['description']
    local = components.core(first, pool[p], pool[r], qs[q])
    domain = components.component_domain(local)
    assert domain == record['domain'] and domain['admissible_triples'] == 480
    rows = [0]*39
    for offset in (3, 21):
        image = list(range(3))+list(range(offset, offset+18))
        for i, row in enumerate(local):
            for j in range(i+1, 21):
                if row >> j & 1:
                    components.edge(rows, image[i], image[j])
    assert [r.bit_count() for r in rows] == [14]*3+[4]*36
    assert components.caps(rows)
    gram = [[12*int(i == j)+2-(rows[i]&rows[j]).bit_count()-(rows[i] >> j & 1)
             for j in range(39)] for i in range(39)]
    triples = domain['signature_domain']
    pairs = [(i, j) for i, a in enumerate(triples) for j, b in enumerate(triples)
             if all(x+y == 2 for x, y in zip(profile(a), profile(b)))]
    assert len(pairs) == 39168
    columns = [[3+v for v in triples[i]]+[21+v for v in triples[j]] for i, j in pairs]
    assert all(len(set(h)) == 6 for h in columns)
    assert all(all(((rows[i] | (1 << i)) & sum(1 << v for v in h)).bit_count() <= 2
                   for i in range(39)) for h in columns)
    return record['description'], domain, rows, gram, pairs, columns


def kernel_vectors():
    vectors = [[int(i == j) for i in range(39)] for j in range(3)]
    for second in (1, 2):
        vectors.append([0]*3+[(1 if i//6 == 0 else -1 if i//6 == second else 0)
                              for _ in range(2) for i in range(18)])
    vectors.append([0]*3+[1]*18+[-1]*18)
    return vectors


def quotient(gram, kernels, deleted, saved=None):
    n, rank = len(gram), len(gram)-len(deleted)
    keep = [i for i in range(n) if i not in deleted]
    assert len(kernels) == len(deleted)
    assert matrix_product(kernels, gram) == [[0]*n for _ in kernels]
    pivot = [[row[i] for i in deleted] for row in kernels]
    pivot_den, pivot_num = exact_inverse(pivot)
    dependency = matrix_product(pivot_num, [[row[i] for i in keep] for row in kernels])
    embedding = [[0]*rank for _ in range(n)]
    for j, i in enumerate(keep):
        embedding[i][j] = pivot_den
    for j, i in enumerate(deleted):
        embedding[i] = [-value for value in dependency[j]]
    divisor = gcd(pivot_den, gcd(*(abs(x) for row in embedding for x in row)))
    embedding_den = pivot_den//divisor
    embedding = [[x//divisor for x in row] for row in embedding]
    principal = [[gram[i][j] for j in keep] for i in keep]
    assert matrix_product(kernels, embedding) == [[0]*rank for _ in kernels]
    assert matrix_product(matrix_product(embedding, principal), transpose(embedding)) == [
        [embedding_den**2*x for x in row] for row in gram]
    if saved is None:
        ldl = positive_ldl(principal)
        denominator, inverse = exact_inverse(principal)
    else:
        ldl = saved['positive_LDL']
        denominator, inverse = saved['inverse_denominator'], saved['inverse_numerator']
    determinant = check_ldl(principal, ldl)
    assert type(denominator) is int and denominator > 0
    assert len(inverse) == rank and all(len(row) == rank for row in inverse)
    assert all(type(value) is int for row in inverse for value in row)
    assert inverse == transpose(inverse)
    assert matrix_product(principal, inverse) == [
        [denominator*int(i == j) for j in range(rank)] for i in range(rank)]
    result = {'deleted_coordinates': deleted, 'kept_coordinates': keep,
              'kernel_vectors': kernels, 'embedding_denominator': embedding_den,
              'embedding_numerator': embedding, 'principal_Gram': principal,
              'positive_LDL': ldl, 'principal_determinant': determinant,
              'inverse_denominator': denominator, 'inverse_numerator': inverse,
              'exact_Gram_rank': rank}
    if saved is not None:
        assert result == saved
    return result


def bilinear_reduction(domain, gram, q, saved=None):
    a = domain['Gram']
    if saved is None:
        denominator, inverse = exact_inverse(a)
        ldl = positive_ldl(a)
    else:
        denominator, inverse = saved['component_inverse_denominator'], saved['component_inverse_numerator']
        ldl = saved['component_positive_LDL']
    check_ldl(a, ldl)
    assert matrix_product(a, inverse) == [[denominator*int(i == j) for j in range(18)] for i in range(18)]
    big_den = q['inverse_denominator']
    assert big_den % denominator == big_den % 36 == big_den % 135 == 0
    form = [[0]*39 for _ in range(39)]
    for offset in (3, 21):
        for i in range(18):
            for j in range(18):
                form[offset+i][offset+j] = (big_den//denominator)*inverse[i][j]
    for i in range(18):
        for j in range(18):
            form[3+i][3+j] += big_den//135-int(i//6 == j//6)*(big_den//36)
    e = q['embedding_numerator']
    assert matrix_product(matrix_product(transpose(e), form), e) == [
        [q['embedding_denominator']**2*v for v in row] for row in q['inverse_numerator']]
    values = [sum(inverse[i][j] for i in h for j in h) for h in domain['signature_domain']]
    result = {'component_inverse_denominator': denominator,
              'component_inverse_numerator': inverse, 'component_positive_LDL': ldl,
              'component_column_leverage_numerators': values,
              'complete_range_bilinear_identity_checked': True,
              'formula': 'r(a,c)+r(b,d)-1/60-dot(profile(a)-1,profile(c)-1)/36',
              'validity': 'size3 per component and complementary global profiles',
              'unrestricted_homogeneous_form': 'blockdiag(A_inverse,A_inverse) plus first block J/135-diag(J6)/36'}
    if saved is not None:
        assert result == saved
    return result


def single_screen(gram, pairs, columns, domain, q, reduction):
    keep, e = q['kept_coordinates'], q['embedding_numerator']
    ed, den, inverse = q['embedding_denominator'], q['inverse_denominator'], q['inverse_numerator']
    lookup = {v: i for i, v in enumerate(keep)}
    values, mismatches = [], []
    a_den = reduction['component_inverse_denominator']
    single = reduction['component_column_leverage_numerators']
    for index, (h, (a, b)) in enumerate(zip(columns, pairs)):
        support = [lookup[i] for i in h if i in lookup]
        assert all(sum(kernel[i] for i in h) == 0 for kernel in q['kernel_vectors'])
        assert [sum(row[j] for j in support) for row in e] == [ed*int(i in h) for i in range(39)]
        numerator = sum(inverse[i][j] for i in support for j in support)
        p = profile(domain['signature_domain'][a])
        expected = (den//a_den)*(single[a]+single[b])-den//60-(den//36)*sum((x-1)**2 for x in p)
        assert numerator == expected
        values.append(numerator)
        if numerator > den:
            mismatches.append(index)
    assert len(values) == 39168 and not mismatches and max(values) < den
    return {'columns_checked': len(values), 'kernel_compatible_columns': len(values),
            'column_leverage_numerators': values, 'leverage_denominator': den,
            'leverage_range': [[Fraction(min(values),den).numerator, Fraction(min(values),den).denominator],
                               [Fraction(max(values),den).numerator, Fraction(max(values),den).denominator]],
            'histogram': [[value, count] for value, count in sorted(Counter(values).items())],
            'excluded_columns': mismatches, 'equality_columns': sum(value == den for value in values),
            'all_columns_strictly_survive': True, 'all_additive_formula_values_checked': True}


def mod2_system(rows, rhs, variables):
    mask = (1 << variables)-1
    basis = {}
    for bits, value in zip(rows, rhs):
        current = bits | ((value % 2) << variables)
        while current & mask:
            pivot = (current & mask).bit_length()-1
            if pivot in basis:
                current ^= basis[pivot]
            else:
                basis[pivot] = current
                break
        else:
            if current:
                return None, len(basis)
    solution = 0
    for pivot in sorted(basis):
        row = basis[pivot]
        if ((row >> variables) ^ ((row & solution).bit_count() % 2)) & 1:
            solution |= 1 << pivot
    assert all((row & solution).bit_count() % 2 == value % 2 for row, value in zip(rows, rhs))
    return solution, len(basis)


def fixed_parity(domain):
    assert digest(FIXED_RESULT) == FIXED_SHA
    saved = json.loads(FIXED_RESULT.read_text())
    selected = saved['incidence_witness']['selected_columns']
    assert len(selected) == len(set(selected)) == 60
    design = [domain['signature_domain'][i] for i in selected]
    assert all(sum(i in h and j in h for h in design) == domain['Gram'][i][j]
               for i in range(18) for j in range(18))
    pairs = [(i,j) for i,a in enumerate(design) for j,b in enumerate(design)
             if all(x+y == 2 for x,y in zip(profile(a),profile(b)))]
    assert len(pairs) == 792
    rows, rhs = [], []
    for side in (0,1):
        for a in range(60):
            rows.append(sum(1 << k for k,p in enumerate(pairs) if p[side] == a))
            rhs.append(1)
    for i in range(18):
        for j in range(18):
            rows.append(sum(1 << k for k,(a,b) in enumerate(pairs) if i in design[a] and j in design[b]))
            rhs.append(2-int(i//6 == j//6))
    solution, rank = mod2_system(rows, rhs, len(pairs))
    assert solution is not None and rank == 338
    support = [i for i in range(len(pairs)) if solution >> i & 1]
    defects = sum((row & solution).bit_count() != value for row,value in zip(rows,rhs))
    assert defects > 0
    return {'scope': 'only the saved fixed-design792-variable quota system',
            'fixed_incidence_result_sha256': FIXED_SHA, 'equations': len(rows),
            'variables': len(pairs), 'mod2_rank': rank, 'mod2_consistent': True,
            'particular_mod2_solution_selected_indices': support,
            'integer_quota_defects_of_this_mod2_point': defects,
            'linear_mod2_inconsistency_certificate_exists': False,
            'integer_or_binary_feasibility_claimed': False,
            'packing_constraints_included': False,
            'other_moduli_or_nonlinear_certificates_excluded': False}


def controls():
    # Actual R9 incidences into the four vertices of a two-by-two square.
    rook = lambda a,b: a != b and (a//3 == b//3 or a%3 == b%3)
    sites = [0,1,3,4]
    outside = [v for v in range(9) if v not in sites]
    rows = [sum(int(rook(v,w)) << j for j,w in enumerate(sites)) for v in sites]
    gram = [[2*int(i == j)+2-(rows[i]&rows[j]).bit_count()-(rows[i] >> j & 1)
             for j in range(4)] for i in range(4)]
    columns = [[int(rook(v,w)) for w in sites] for v in outside]
    assert gram == [[sum(h[i]*h[j] for h in columns) for j in range(4)] for i in range(4)]
    q = quotient(gram, [[1,-1,-1,1]], [0])
    values = []
    for h in columns:
        x = [h[i] for i in q['kept_coordinates']]
        assert matrix_product(q['embedding_numerator'], [[v] for v in x]) == [[q['embedding_denominator']*v] for v in h]
        value = sum(x[i]*q['inverse_numerator'][i][j]*x[j] for i in range(3) for j in range(3))
        assert value <= q['inverse_denominator']
        values.append([value,q['inverse_denominator']])
    assert sum([1,-1,-1,1][i]*[1,0,0,0][i] for i in range(4)) != 0
    # G=I2 is the Gram of its two singleton columns; a new binary11 is impossible.
    identity = [[1,0],[0,1]]
    den, inv = exact_inverse(identity)
    assert sum(sum(row) for row in inv) == 2*den
    assert sum(sum(row) for row in identity)-2**2 == -2
    systems = 0
    for a in range(4):
        for b in range(4):
            for rhs in ((0,0),(0,1),(1,0),(1,1)):
                solution, _ = mod2_system([a,b], rhs, 2)
                possible = [x for x in range(4) if all((r&x).bit_count()%2 == v for r,v in zip((a,b),rhs))]
                assert (solution is not None) == bool(possible)
                systems += 1
    return {'rook9_actual_columns': 5, 'rook9_Gram_rank': 3,
            'rook9_leverage_numerator_denominators': values,
            'kernel_incompatible_binary_control_rejected': True,
            'binary_excess_leverage_control_direct_negative_value': -2,
            'exhaustive_two_by_two_mod2_systems': systems,
            'solver_called': False}


def calculate(saved=None):
    started = time.monotonic()
    description, domain, rows, gram, pairs, columns = load_core()
    q = quotient(gram, kernel_vectors(), DELETED, None if saved is None else saved['positive_quotient'])
    assert q['exact_Gram_rank'] == 33 and q['embedding_denominator'] == 2
    assert q['inverse_denominator'] == 4577040
    reduction = bilinear_reduction(domain, gram, q, None if saved is None else saved['bilinear_reduction'])
    screen = single_screen(gram, pairs, columns, domain, q, reduction)
    parity = fixed_parity(domain)
    possible_pairs = len(columns)*(len(columns)-1)//2
    return {'status': 'all39168 complete-domain columns pass exact one-column Gram test; no exclusion',
            'source_sha256': digest(Path(__file__)),
            'component_source_sha256': digest(Path(components.__file__)),
            'domain_certificate_sha256': motifs.DOMAIN_SHA,
            'scope': 'two full component0 copies, identity fiber alignment, conditional globally P=F=0 split shell',
            'fixed_incidence_design_used_for_full_domain_screen': False,
            'component_description': description, 'component_triples': domain['signature_domain'],
            'joined_core_rows': [str(r) for r in rows], 'Gram': gram,
            'paired_column_order_sha256': components.sha(canonical(pairs)),
            'full_column_order_sha256': components.sha(canonical(columns)),
            'positive_quotient': q, 'bilinear_reduction': reduction,
            'single_column_screen': screen, 'fixed_design_mod2_diagnostic': parity,
            'controls': controls(), 'pair_enumeration_performed': False,
            'optimizer_or_solver_called': False,
            'resource_counts': {'columns': len(columns), 'all_unordered_column_pairs': possible_pairs,
                                'dense_full_bilinear_int64_bytes': len(columns)**2*8,
                                'within_component_bilinear_entries': 480**2,
                                'within_component_bilinear_int64_bytes': 480**2*8},
            'elapsed_seconds_for_information_only': time.monotonic()-started}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate', type=Path, required=True)
    parser.add_argument('--replay', action='store_true')
    args = parser.parse_args()
    if args.replay:
        saved = json.loads(gzip.decompress(args.certificate.read_bytes()))
        actual = calculate(saved)
        actual['elapsed_seconds_for_information_only'] = saved['elapsed_seconds_for_information_only']
        assert actual == saved
    else:
        assert not args.certificate.exists()
        actual = calculate()
        args.certificate.write_bytes(gzip.compress(canonical(actual)+b'\n', mtime=0))
    screen = actual['single_column_screen']
    print(json.dumps({'status': actual['status'], 'mode': 'replay' if args.replay else 'generation',
                      'rank': actual['positive_quotient']['exact_Gram_rank'],
                      'columns_checked': screen['columns_checked'], 'excluded_columns': len(screen['excluded_columns']),
                      'leverage_range': screen['leverage_range'],
                      'fixed_design_mod2_rank': actual['fixed_design_mod2_diagnostic']['mod2_rank'],
                      'resource_counts': actual['resource_counts'],
                      'elapsed_seconds': actual['elapsed_seconds_for_information_only']}, indent=2), flush=True)
