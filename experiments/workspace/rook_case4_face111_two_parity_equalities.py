"""Prove H1=H2=1 on the111-zero face using one signature capacity.

The existing33-Gram identity makes H1 an odd nonnegative integer. H2=1
and one original-signature capacity give H1<=2. Thus H1=1. No optimizer,
numerical point, branch assumption or new parity search occurs.
"""
import argparse
import hashlib
import json
from pathlib import Path
import time

import rook_case4_face99_parity_face as previous

ROOT = Path(__file__).resolve().parents[2]
BASE = 'experiments/logs/grids-and-triangles/'
PREVIOUS_SHA = '52621284ad3b8344c5b64e99b028a8e5e063f32e91468399ad69ab4ee69e93cc'
PREVIOUS_CERTIFICATE = BASE+'rook-case4-face99-parity-face-certificate.json'
PREVIOUS_CERTIFICATE_SHA = '717c3e4103dd56bdd260f52b0f50c5a06f4245b834d92194357481d3163e229e'
CAPACITY_ROW, ORIGINAL_SIGNATURE = 51,96


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def prove(root=ROOT):
    assert digest(Path(previous.__file__).read_bytes()) == PREVIOUS_SHA
    raw = (root/PREVIOUS_CERTIFICATE).read_bytes()
    assert digest(raw) == PREVIOUS_CERTIFICATE_SHA
    prior = previous.prove(root)
    assert canonical(prior) == canonical(json.loads(raw))
    zeros = prior['all_zero_columns']
    zero_set = set(zeros)
    assert len(zeros) == 111
    records = {}
    for name in ('native','covers'):
        path,expected = previous.INPUTS[name]
        data = (root/path).read_bytes()
        assert digest(data) == expected
        records[name] = json.loads(data)
    inv = records['native']['primary_inventory']
    assert digest(canonical(inv)) == records['native']['primary_inventory_sha256']
    full_supports = [[a for a,c in row['terms']] for row in prior['both_integer_cover_rows']]
    live = [sorted(set(support)-zero_set) for support in full_supports]
    assert list(map(len,full_supports)) == [42,42] and list(map(len,live)) == [36,42]
    A = sorted(set(live[0])-set(live[1]))
    B = sorted(set(live[1])-set(live[0]))
    assert A == [259,260,261,262]
    assert B == [590,591,592,593,594,595,730,731,732,733]
    signature,support = inv['original_signature_rows'][CAPACITY_ROW]
    assert signature == ORIGINAL_SIGNATURE and support == [258,259,260,261,262]
    assert sorted(set(support)-zero_set) == A and sorted(set(support)&zero_set) == [258]

    cover = records['covers']['proofs'][0]
    coefficient = [0]*1214
    rhs,rows = 0,[]
    gram = inv['Gram_rows']
    assert len(cover['original_Gram_row_sum']) == 33
    for record in cover['original_Gram_row_sum']:
        row = record['original_native_row']
        i,j,quota,members = gram[row]
        assert record['core_pair'] == [i,j] and record['quota'] == quota and record['coefficient'] == 1
        rhs += quota
        for a in members:
            coefficient[a] += 1
        rows.append({'original_native_row':row,'multiplier':1,'core_pair':[i,j],'quota':quota})
    assert coefficient == cover['full_original_integer_coefficients'] and rhs == 45
    assert sorted(a for a,c in enumerate(coefficient) if a not in zero_set and c%2) == live[0]
    quotient = []
    for a,c in enumerate(coefficient):
        if a not in zero_set:
            q = c-int(a in set(live[0]))
            assert q >= 0 and q%2 == 0
            if q:
                quotient.append([a,q//2])
    # Recheck the algebra of the two support sums on every original column.
    difference = [int(a in set(live[0]))-int(a in set(live[1])) for a in range(1214)]
    assert difference == [int(a in set(A))-int(a in set(B)) for a in range(1214)]
    assert prior['original_Gram_right_hand_side'] == 1
    assert prior['direct_identity_on_prior_face'] == 'sum_H2(x)+2*sum_new12(x)=1'
    assert set(prior['new_zero_columns']) <= zero_set
    return {
        'status':'PASS: both parity supports equal one on the111-zero nonnegative integer face',
        'source_sha256':digest(Path(__file__).read_bytes()),
        'prior_source_sha256':PREVIOUS_SHA,'prior_certificate_sha256':PREVIOUS_CERTIFICATE_SHA,
        'native_input':{'path':previous.INPUTS['native'][0],'sha256':previous.INPUTS['native'][1]},
        'odd_cover_input':{'path':previous.INPUTS['covers'][0],'sha256':previous.INPUTS['covers'][1]},
        'proved_zero_columns':zeros,'original_cover_supports':full_supports,
        'live_cover_supports':live,'positive_difference_A':A,'negative_difference_B':B,
        'original_signature_capacity':{'row':CAPACITY_ROW,'signature':signature,
            'support':support,'upper':1,'proved_zero_members':[258],'remaining_support':A},
        'H1_original_Gram_combination':rows,'H1_original_right_hand_side':rhs,
        'H1_full_original_integer_coefficients':coefficient,
        'H1_live_integer_half_coefficients':quotient,
        'H1_integer_identity':'2*sum(q_a*x_a)+sum_H1(x)=45',
        'H2_exact_value':1,'difference_identity':'sum_H1(x)=1+sum_A(x)-sum_B(x)',
        'H1_upper_bound':2,'H1_odd':True,'H1_nonnegative':True,'H1_exact_value':1,
        'proof':'The capacity gives sum_A<=1, while sum_B>=0. Thus0<=H1<=2. The integer Gram identity makes H1 odd, hence H1=1. H2=1 already follows from the checked42-Gram identity and proved zeros.',
        'additional_equality':'sum_A(x)=sum_B(x)','common_A_B_upper_bound':1,
        'new_integer_cover_ranges':[[1,1],[1,1]],
        'all1214_parity_and_difference_coefficients_checked':True,
        'new_zero_columns':[],'new_one_columns':[],
        'valid_for_nonnegative_integer_incidence':True,
        'old_real_feasible_set_preservation_claimed':False,
        'optimizer_calls':0,'parity_search_performed':False,'case4_excluded':False,
    }


def controls():
    count = 0
    for a in range(2):
        for b in range(12):
            h = 1+a-b
            if h >= 0 and h%2 == 1:
                assert h == 1 and a == b
            count += 1
    return {'small_integer_bound_cases':count,'odd_nonnegative_at_most_two_is_one':True,'optimizer_calls':0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=('prepare','replay'))
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--certificate',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    started = time.monotonic()
    assert not args.output.exists()
    proof = prove(args.root)
    checked = controls()
    if args.mode == 'prepare':
        assert not args.certificate.exists()
        args.certificate.write_text(json.dumps(proof,indent=2)+'\n')
    else:
        assert canonical(json.loads(args.certificate.read_bytes())) == canonical(proof)
    report = {'status':'PASS: full original-row proof of H1=H2=1 '+args.mode,
        'source_sha256':proof['source_sha256'],'certificate_sha256':digest(args.certificate.read_bytes()),
        'prior_certificate_sha256':PREVIOUS_CERTIFICATE_SHA,'all111_zeros_reproved':True,
        'original_Gram_rows_for_H1_parity':33,'original_signature_capacity_row':CAPACITY_ROW,
        'live_cover_sizes':[36,42],'cover_ranges':[[1,1],[1,1]],
        'controls':checked,'optimizer_calls':0,'case4_excluded':False,'seconds':time.monotonic()-started}
    args.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2),flush=True)


if __name__ == '__main__':
    main()
