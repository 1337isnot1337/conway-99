"""Exact four-Gram-row facial certificate for the complete case4 domain.

This standard-library checker does not use a solver or a numerical LP point.
It reconstructs all630 Gram supports from the35 diagonal supports, checks the
old three-row zero certificate, and then checks the new four-row relation.
"""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path

NATIVE_SHA = 'a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476'
PRIMARY_SHA = '5a6af30f47826df629a3795ceea0a0a91b853cf8149860355ce1bd17ac0094b2'
OLD_PAIRS = [(3,27,1), (4,27,1), (17,27,-1)]
NEW_PAIRS = [(6,27,1), (7,27,1), (11,27,-1), (14,27,-1)]
OLD_ZEROS = [235,241,252,258,263,302,309,315,329,335,342,348,352,354,356,359,
             363,367,368,371,375,385,387,388,392,396,397,398,400,404,408,410,
             413,415,417,420,424,428,430,435,437,442,457,459,461,465]
NEW_POSITIVE = [772,779,783,809,816,822,828,841,848,923,926,928,931,934,
                937,941,955,957,959,963,966,970,973,977]


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':')).encode()


def build(native_path):
    raw = native_path.read_bytes()
    assert sha(raw) == NATIVE_SHA
    inventory = json.loads(raw)['primary_inventory']
    assert sha(canonical(inventory)) == PRIMARY_SHA
    assert inventory['primary_variables'] == 1214
    assert inventory['case']['index'] == inventory['case']['matching_index'] == 4
    entries = inventory['Gram_rows']
    pairs = [(i,j) for i in range(35) for j in range(i,35)]
    assert [(i,j) for i,j,q,support in entries] == pairs
    index = {pair:k for k,pair in enumerate(pairs)}
    masks = [0]*1214
    for i,j,q,support in entries:
        assert type(q) is int and q >= 0 and support == sorted(set(support))
        assert all(type(a) is int and 0 <= a < 1214 for a in support)
        if i == j:
            for a in support:
                masks[a] |= 1 << i
    for i,j,q,support in entries:
        assert support == [a for a,h in enumerate(masks) if (h >> i & 1) and (h >> j & 1)]

    def relation(combination):
        coefficient = [0]*1214
        rhs, rows = 0, []
        for i,j,sign in combination:
            original = index[i,j]
            a,b,quota,support = entries[original]
            rhs += sign*quota
            for column in support:
                coefficient[column] += sign
            rows.append({'original_Gram_row':original, 'core_pair':[i,j],
                         'multiplier':sign, 'quota':quota, 'support':support})
        return coefficient, rhs, rows

    old, old_rhs, old_rows = relation(OLD_PAIRS)
    assert old_rhs == 0 and set(old) == {0,1}
    assert [a for a,c in enumerate(old) if c] == OLD_ZEROS
    new, rhs, rows = relation(NEW_PAIRS)
    negative = [a for a,c in enumerate(new) if c < 0]
    positive = [a for a,c in enumerate(new) if c > 0]
    assert rhs == 0 and set(new) == {-1,0,1}
    assert len(negative) == 25 and set(negative) <= set(OLD_ZEROS)
    assert positive == NEW_POSITIVE and not set(positive).intersection(OLD_ZEROS)
    combined = [a+b for a,b in zip(old,new)]
    assert set(combined) == {0,1}
    combined_positive = [a for a,c in enumerate(combined) if c]
    assert len(combined_positive) == 45
    zeros = sorted(set(OLD_ZEROS)|set(positive))
    assert len(zeros) == 70
    return {'status':'EXACT_CASE4_FOUR_GRAM_ROW_FACE',
        'source_sha256':sha(Path(__file__).read_bytes()),
        'native_input_sha256':NATIVE_SHA, 'primary_inventory_sha256':PRIMARY_SHA,
        'all630_Gram_supports_checked_from_diagonals':True,
        'complete_original_columns':1214,
        'old_three_row_certificate':{'rows':old_rows, 'rhs':old_rhs,
                                    'coefficient_counts':dict(Counter(old)), 'zero_columns':OLD_ZEROS},
        'new_four_row_relation':{'rows':rows, 'rhs':rhs,
                                'all1214_coefficients':new,
                                'negative_columns':negative, 'positive_columns':positive,
                                'all_negative_columns_previously_proved_zero':True},
        'single_seven_row_nonnegative_certificate':{
            'rows':old_rows+rows, 'rhs':0,
            'coefficient_counts':dict(Counter(combined)),
            'positive_columns':combined_positive},
        'Gram_only_zero_columns_after_both_relations':zeros,
        'new_Gram_only_zero_columns':positive,
        'proof':'The old relation is a zero sum of nonnegative weights. In the new zero relation every negative term is already zero, so all24 positive terms vanish. Equivalently the sum of the seven displayed rows has only nonnegative coefficients.',
        'uses_integrality':False, 'uses_coordinate_covers':False,
        'uses_exterior_row_cuts':False, 'uses_LP_extension_or_t':False,
        'optimizer_called':False, 'case4_excluded':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','replay'))
    p.add_argument('--native',type=Path,required=True)
    p.add_argument('--certificate',type=Path)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args()
    assert not a.output.exists()
    actual=build(a.native)
    if a.mode=='replay':
        assert a.certificate is not None
        saved=json.loads(a.certificate.read_text())
        assert canonical(actual)==canonical(saved)
        value={'status':'PASS: optimizer-free complete-domain four/seven-row arithmetic replay',
               'source_sha256':actual['source_sha256'],
               'certificate_sha256':sha(a.certificate.read_bytes()),
               'all630_Gram_supports_checked':True,'all1214_coefficients_checked':True,
               'new_Gram_zero_count':24,'total_Gram_zero_count':70,
               'optimizer_called':False,'case4_excluded':False}
    else:
        value=actual
    with a.output.open('x') as f:
        json.dump(value,f,indent=2)
        f.write('\n')
    print(json.dumps({'status':value['status'],'output':str(a.output),
                      'sha256':sha(a.output.read_bytes())},indent=2))


if __name__=='__main__':
    main()
