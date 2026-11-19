"""Independent integer-matrix review of the frozen component-pair quotient.

No subject builder is imported. This checks its recorded39-core Gram,
positive quotient, rational embedding, entire-range bilinear identity,
complete complementary-profile product order, and all resulting leverage
values. It does not redo the66-component catalogue or enumerate pairs of
the39,168 complete columns. No solver is called.
"""

import argparse
from fractions import Fraction
import gzip
import hashlib
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT/'experiments/workspace/root_prism_free_f0_pair_gram.py'
SOURCE_SHA = '187feef008f6b0f5b1718a9d5d856e4a1b0820a3f1a023445090b691494d3aef'
CERT = ROOT/'experiments/logs/root-prism-free/f0-pair-gram-certificate.json.gz'
CERT_SHA = 'edb85ff422222961e6bc9b36322b74bcfce455bca262d6e189d7768f9ac91c98'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def product(a, b):
    return [[sum(x*y for x, y in zip(row, col)) for col in zip(*b)] for row in a]


def transpose(a):
    return [list(row) for row in zip(*a)]


def positive(matrix, saved):
    lower = [[Fraction(*entry) for entry in row] for row in saved['lower']]
    diagonal = [Fraction(*entry) for entry in saved['positive_diagonal']]
    n = len(matrix)
    assert len(lower) == len(diagonal) == n and all(len(row) == n for row in lower)
    assert all(diagonal[i] > 0 and lower[i][i] == 1 and not any(lower[i][i+1:]) for i in range(n))
    actual = [[sum(lower[i][k]*diagonal[k]*lower[j][k] for k in range(n))
               for j in range(n)] for i in range(n)]
    assert actual == matrix


def review():
    assert digest(SOURCE) == SOURCE_SHA and digest(CERT) == CERT_SHA
    saved = json.loads(gzip.decompress(CERT.read_bytes()))
    assert saved['source_sha256'] == SOURCE_SHA
    rows = list(map(int, saved['joined_core_rows']))
    assert len(rows) == 39
    gram = [[12*int(i == j)+2-(rows[i]&rows[j]).bit_count()-int(rows[i] >> j & 1)
             for j in range(39)] for i in range(39)]
    assert gram == saved['Gram']
    assert all(not rows[i] >> i & 1 for i in range(39))
    assert all((rows[i] >> j & 1) == (rows[j] >> i & 1) for i in range(39) for j in range(39))
    assert [row.bit_count() for row in rows] == [14]*3+[4]*36
    q = saved['positive_quotient']
    keep, embedding, ed = q['kept_coordinates'], q['embedding_numerator'], q['embedding_denominator']
    assert ed == 2 and len(keep) == 33 and keep == [i for i in range(39) if i not in [0,1,2,3,9,21]]
    principal = [[gram[i][j] for j in keep] for i in keep]
    assert principal == q['principal_Gram']
    assert [embedding[i] for i in keep] == [[ed*int(i == j) for j in range(33)] for i in range(33)]
    assert product(product(embedding, principal), transpose(embedding)) == [[ed*ed*v for v in row] for row in gram]
    positive(principal, q['positive_LDL'])
    scale, inverse = q['inverse_denominator'], q['inverse_numerator']
    assert scale == 4577040 and inverse == transpose(inverse)
    assert product(principal, inverse) == [[scale*int(i == j) for j in range(33)] for i in range(33)]
    reduction = saved['bilinear_reduction']
    component = [[gram[3+i][3+j] for j in range(18)] for i in range(18)]
    a_den, a_inv = reduction['component_inverse_denominator'], reduction['component_inverse_numerator']
    positive(component, reduction['component_positive_LDL'])
    assert product(component, a_inv) == [[a_den*int(i == j) for j in range(18)] for i in range(18)]
    assert scale % a_den == scale % 135 == scale % 36 == scale % 60 == 0
    form = [[0]*39 for _ in range(39)]
    for i in range(18):
        for j in range(18):
            form[3+i][3+j] = scale//a_den*a_inv[i][j]+scale//135-int(i//6 == j//6)*(scale//36)
            form[21+i][21+j] = scale//a_den*a_inv[i][j]
    assert product(product(transpose(embedding), form), embedding) == [[ed*ed*v for v in row] for row in inverse]
    triples = saved['component_triples']
    assert len(triples) == len({tuple(t) for t in triples}) == 480
    assert all(len(t) == len(set(t)) == 3 and all(0 <= i < 18 for i in t) for t in triples)
    profiles = [tuple(sum(i//6 == f for i in t) for f in range(3)) for t in triples]
    values = [sum(a_inv[i][j] for i in t for j in t) for t in triples]
    pairs = [(a,b) for a in range(480) for b in range(480)
             if all(x+y == 2 for x,y in zip(profiles[a],profiles[b]))]
    columns = [[3+i for i in triples[a]]+[21+j for j in triples[b]] for a,b in pairs]
    assert len(pairs) == 39168
    assert hashlib.sha256(canonical(pairs)).hexdigest() == saved['paired_column_order_sha256']
    assert hashlib.sha256(canonical(columns)).hexdigest() == saved['full_column_order_sha256']
    numerators = [scale//a_den*(values[a]+values[b])+scale//15-
                  (scale//36)*sum(p*p for p in profiles[a]) for a,b in pairs]
    assert numerators == saved['single_column_screen']['column_leverage_numerators']
    assert all(0 < v < scale for v in numerators)
    return {'status': 'PASS: independent exact quotient and entire-range bilinear review',
            'review_source_sha256': digest(Path(__file__)), 'subject_source_sha256': SOURCE_SHA,
            'subject_certificate_sha256': CERT_SHA,
            'full39_Gram_entries_checked': 1521, 'positive_quotient_rank': 33,
            'embedding_denominator': ed, 'inverse_denominator': scale,
            'component_inverse_denominator': a_den,
            'full_range_bilinear_congruence_checked': True,
            'complete_complementary_profile_product_columns': len(pairs),
            'all_factored_leverage_values_rechecked': True,
            'leverage_range': [str(Fraction(min(numerators),scale)),str(Fraction(max(numerators),scale))],
            'component_catalogue_rebuilt': False, 'complete_column_pairs_enumerated': False,
            'fixed_design_parity_diagnostic_rechecked': False, 'solver_called': False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists()
    started = time.monotonic()
    result = review()
    result['elapsed_seconds'] = time.monotonic()-started
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2), flush=True)
