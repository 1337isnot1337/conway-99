"""Full original-coordinate proof of twelve integer Gram zeros after face99.

No LP, modular eliminator or numerical point is used. Forty-two original
Gram equations imply sum(H2)+2*sum(new12)=1 after the existing99 zeros.
Nonnegative integrality forces the twelve doubled coordinates to zero.
The separately proved H2 cover gives the same deduction in a real LP.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import time

import rook_case4_transportation_seed as seed

ROOT=Path(__file__).resolve().parents[2]
BASE='experiments/logs/grids-and-triangles/'
SEED_SHA='9eedacb4b62db8ad7058e291d04f83141fca306971ed278a58548ead4cd1e8a1'
INPUTS={
    'native':(BASE+'complement-rook-35core-case0004-native-cpsat-model.json','a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476'),
    'seed':(BASE+'rook-case4-transportation-seed-certificate.json','64d8e375280bc067097913de2dd6e2995c19de2a4807f63cecdcd80b811a85cf'),
    'covers':(BASE+'rook-case4-face99-parity-cover-certificate.json','644a7f637fb8ea42fd49a99487ead6eb544370ae463c9e303e86e8934d2f1a81'),
    'LP_certificate':(BASE+'rook-case4-face99-parity-generation-run01/exact-bound-certificate.json.gz','a950351d0bc982f4d20c2d25d392517620141fdd313182d75bf4f93d5dc0e740'),
    'LP_cold_replay':(BASE+'rook-case4-face99-parity-generation-run01-replay.json','ca9e2cbf2b4034a596db226658ca8a98349cee7d9413c0e7909ae6acf8a21d42'),
}
GRAM_COMBINATION=[
    [48,1],[124,-1],[155,-2],[185,-1],[203,1],[231,2],[295,1],
    [299,1],[302,1],[324,1],[327,1],[348,1],[351,1],[367,-1],
    [374,1],[389,-1],[393,1],[396,1],[403,-1],[410,-1],[412,-1],
    [413,-1],[415,-1],[416,-1],[418,-1],[434,1],[437,1],[453,1],
    [456,1],[471,1],[507,-1],[522,-1],[549,-1],[561,-1],[572,-1],
    [578,1],[579,1],[580,1],[583,1],[584,1],[591,-1],[609,-1],
]
NEW_ZEROS=list(range(1062,1068))+list(range(1125,1131))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def prove(root=ROOT):
    assert sha(Path(seed.__file__).read_bytes())==SEED_SHA
    data={}
    for name,(path,expected) in INPUTS.items():
        raw=(root/path).read_bytes()
        assert sha(raw)==expected,name
        data[name]=json.loads(gzip.decompress(raw) if path.endswith('.gz') else raw)
    prior=seed.prove(root)
    assert canonical(prior)==canonical(data['seed'])
    zeros=prior['seed_zero_columns']
    assert len(zeros)==99 and not set(zeros).intersection(NEW_ZEROS)
    zero_set=set(zeros)
    inventory=data['native']['primary_inventory']
    assert sha(canonical(inventory))==data['native']['primary_inventory_sha256']
    gram=inventory['Gram_rows']
    assert [(i,j) for i,j,q,s in gram]==[(i,j) for i in range(35) for j in range(i,35)]
    masks=[0]*1214
    for i,j,q,support in gram:
        if i==j:
            for a in support:masks[a]|=1<<i
    for i,j,q,support in gram:
        assert support==[a for a,h in enumerate(masks) if h>>i&1 and h>>j&1]
        assert type(q) is int and q>=0

    # Recheck both saved odd-cover identities from their original Gram rows.
    # This also retains H1 for the next complete propagation system.
    for cover in data['covers']['proofs']:
        coeff=[0]*1214;rhs=0
        for row in cover['original_Gram_row_sum']:
            i,j,q,support=gram[row['original_native_row']]
            assert row['core_pair']==[i,j] and row['quota']==q and row['coefficient']==1
            rhs+=q
            for a in support:coeff[a]+=1
        assert coeff==cover['full_original_integer_coefficients']
        assert rhs==cover['original_right_hand_side'] and rhs%2==1
        assert [a for a in range(1214) if a not in zero_set and coeff[a]%2]==cover['cover_support']
        assert cover['cover_lower_bound']==1 and len(cover['cover_support'])==42
    assert len(data['covers']['proofs'])==2
    H2=data['covers']['proofs'][1]['cover_support']

    full=[0]*1214;rhs=0;rows=[]
    assert len(GRAM_COMBINATION)==42 and GRAM_COMBINATION==sorted(GRAM_COMBINATION)
    for identifier,multiplier in GRAM_COMBINATION:
        i,j,q,support=gram[identifier]
        rhs+=multiplier*q
        for a in support:full[a]+=multiplier
        rows.append({'original_native_row':identifier,'multiplier':multiplier,'core_pair':[i,j],'quota':q})
    assert rhs==1
    H2_set,new_set=set(H2),set(NEW_ZEROS)
    assert H2_set.isdisjoint(new_set)
    omitted={a:full[a] for a in zeros if full[a]}
    for a in range(1214):
        assert full[a]==int(a in H2_set)+2*int(a in new_set)+omitted.get(a,0),a
    assert all(0<=a<1214 for a in NEW_ZEROS) and len(NEW_ZEROS)==12

    # The discovery certificate is checked only as provenance. The displayed
    # forty-two-row identity itself is checked directly above on all columns.
    retained=[]
    for identifier,(i,j,q,support) in enumerate(gram):
        if any(a not in zero_set for a in support):retained.append(identifier)
        else:assert q==0
    assert len(retained)==396
    from_LP=[];used_cover=[];extensions=[]
    for row,multiplier in data['LP_certificate']['sparse_integer_row_multipliers']:
        multiplier=int(multiplier)
        if row<167937:
            if row==167936:used_cover.append([row,multiplier])
            else:
                assert row<396
                from_LP.append([retained[row],multiplier])
        else:
            assert 167937<=row<169052 and multiplier<0
            extensions.append([row,multiplier])
    assert from_LP==GRAM_COMBINATION and used_cover==[[167936,-1]]
    assert len(extensions)==7 and sum(m for r,m in extensions)==-14
    cold=data['LP_cold_replay']
    assert cold['exact_zero_face_verified'] and not cold['exact_case4_exclusion_verified']
    assert cold['zero_original_columns']==NEW_ZEROS and cold['one_original_columns']==[]
    union=sorted(zero_set|new_set)
    assert len(union)==111
    return {'status':'PASS: full1214-coordinate integer Gram identity and twelve new zeros',
        'source_sha256':sha(Path(__file__).read_bytes()),'seed_source_sha256':SEED_SHA,
        'input_bindings':{k:{'path':p,'sha256':h} for k,(p,h) in INPUTS.items()},
        'prior_zero_columns':zeros,'original_Gram_combination':rows,
        'original_Gram_right_hand_side':rhs,'full_original_coefficients':full,
        'known_zero_terms':[[a,c] for a,c in sorted(omitted.items())],
        'H2_support':H2,'new_zero_columns':NEW_ZEROS,'all_zero_columns':union,
        'all1214_coefficients_checked':True,
        'direct_identity_on_prior_face':'sum_H2(x)+2*sum_new12(x)=1',
        'integer_proof':'All terms are nonnegative. Each doubled integer coordinate satisfies2*x<=1, hence is zero. The42-column H2 sum is then1.',
        'real_LP_proof':'The proved cover sum_H2(x)>=1 and nonnegativity force sum_new12(x)=0; every new coordinate is zero.',
        'real_scope_requires_H2_integer_cover':True,
        'both_integer_cover_rows':data['covers']['new_linear_rows'],
        'H1_retained_in_continuation':True,
        'integrality_used_for_new_zeros':True,'optimizer_calls':0,
        'modular_elimination_called':False,'numeric_point_used':False,
        'case4_excluded':False}


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','replay'))
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--certificate',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    a=p.parse_args();started=time.monotonic()
    assert not a.output.exists()
    result=prove(a.root)
    if a.mode=='prepare':
        assert not a.certificate.exists()
        a.certificate.write_text(json.dumps(result,indent=2)+'\n')
    else:assert canonical(json.loads(a.certificate.read_bytes()))==canonical(result)
    report={'status':'PASS: direct twelve-zero Gram proof '+a.mode,
        'source_sha256':result['source_sha256'],'certificate_sha256':sha(a.certificate.read_bytes()),
        'new_zero_columns':NEW_ZEROS,'all_zero_count':111,'Gram_rows':42,
        'all1214_coefficients_checked':True,'integer_proof_requires_parity_scan':False,
        'optimizer_calls':0,'case4_excluded':False,'seconds':time.monotonic()-started}
    a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2))
