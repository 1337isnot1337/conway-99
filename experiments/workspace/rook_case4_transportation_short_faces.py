"""Six short original-row certificates for88 case4 zero columns.

This standalone checker reconstructs all literal Gram/triple supports and
uses no transportation routine, numerical point, LP extension or optimizer.
The first two steps use Gram alone. The last four add triple capacities.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
NATIVE='experiments/logs/grids-and-triangles/complement-rook-35core-case0004-native-cpsat-model.json'
NATIVE_SHA='a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476'
PRIMARY_SHA='5a6af30f47826df629a3795ceea0a0a91b853cf8149860355ce1bd17ac0094b2'
COMBINATIONS=[
 [('Gram',[3,27],1),('Gram',[4,27],1),('Gram',[17,27],-1)],
 [('Gram',[6,27],1),('Gram',[7,27],1),('Gram',[11,27],-1),('Gram',[14,27],-1)],
 [('Gram',[9,27],1),('Gram',[5,27],-1),('triple',[5,15,27],1)],
 [('Gram',[12,27],1),('Gram',[8,27],-1),('triple',[8,13,27],1)],
 [('Gram',[13,27],1),('Gram',[8,27],-1),('triple',[8,12,27],1)],
 [('Gram',[14,27],1),('Gram',[7,27],-1),('triple',[7,11,27],1)],
]
NEW_TWELVE=[101,115,121,126,133,140,145,149,788,793,799,804]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def prove(root):
    raw=(root/NATIVE).read_bytes()
    assert digest(raw)==NATIVE_SHA
    inventory=json.loads(raw)['primary_inventory']
    assert digest(canonical(inventory))==PRIMARY_SHA
    assert inventory['primary_variables']==1214 and inventory['case']['index']==4
    grams=inventory['Gram_rows']
    assert [(i,j)for i,j,q,s in grams]==[(i,j)for i in range(35)for j in range(i,35)]
    masks=[0]*1214
    lookup={}
    for index,(i,j,q,s)in enumerate(grams):
        assert s==sorted(set(s))and type(q)is int and q>=0
        assert all(type(a)is int and 0<=a<1214 for a in s)
        lookup['Gram',(i,j)]=(index,q,s)
        if i==j:
            for a in s:masks[a]|=1<<i
    for i,j,q,s in grams:
        assert s==[a for a,h in enumerate(masks)if h>>i&1 and h>>j&1]
    triples=inventory['triple_rows']
    assert len(triples)==1365
    for index,entry in enumerate(triples):
        sites=entry['triple']
        assert len(sites)==3 and sites==sorted(set(sites))
        support=[a for a,h in enumerate(masks)if all(h>>i&1 for i in sites)]
        assert support==entry['members']and len(support)>1
        key=('triple',tuple(sites))
        assert key not in lookup
        lookup[key]=(index,1,support)
    zeros=set()
    reason={}
    steps=[]
    for step,combination in enumerate(COMBINATIONS):
        coefficients=[0]*1214
        rhs=0
        terms=[]
        for kind,sites,multiplier in combination:
            assert kind=='Gram'or multiplier>0
            index,quota,support=lookup[kind,tuple(sites)]
            for a in support:coefficients[a]+=multiplier
            rhs+=quota*multiplier
            terms.append({'kind':kind,'sites':sites,'original_row':index,
                          'multiplier':multiplier,'rhs':quota,'support':support})
        assert rhs==0 and set(coefficients)<={-1,0,1}
        negative=[a for a,c in enumerate(coefficients)if c<0]
        assert set(negative)<=zeros
        positive=[a for a,c in enumerate(coefficients)if c>0]
        new=[a for a in positive if a not in zeros]
        assert len(new)==[46,24,6,4,4,4][step]
        steps.append({'step':step,'terms':terms,'combined_rhs_upper_bound':0,
            'all1214_coefficients':coefficients,
            'negative_prior_zero_premises':[[a,reason[a]]for a in negative],
            'positive_columns':positive,'new_zero_columns':new,
            'nonnegative_after_prior_zeros':True})
        for a in new:zeros.add(a);reason[a]=step
    assert len(zeros)==88
    assert sorted(a for s in steps[3:]for a in s['new_zero_columns'])==NEW_TWELVE
    return {'status':'PASS:88 original-column zeros from six exact short row combinations',
        'source_sha256':digest(Path(__file__).read_bytes()),
        'native_input_path':NATIVE,'native_input_sha256':NATIVE_SHA,
        'primary_inventory_sha256':PRIMARY_SHA,'full_columns':1214,
        'all630_Gram_supports_and1365_triple_supports_rebuilt':True,
        'steps':steps,'Gram_only_zero_columns':sorted(a for s in steps[:2]for a in s['new_zero_columns']),
        'all_zero_columns':sorted(zeros),'new_twelve_columns':NEW_TWELVE,
        'nonnegative_real_weights_suffice':True,'upper_unit_boxes_used':False,
        'coordinate_covers_used':False,'transportation_algorithm_used':False,
        'optimizer_called':False,'case4_excluded':False}


def save(path,value):
    assert not path.exists()
    path.write_text(json.dumps(value,indent=2)+'\n')


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('write','replay'))
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--certificate',type=Path,required=True)
    p.add_argument('--output',type=Path)
    a=p.parse_args()
    proof=prove(a.root)
    if a.mode=='write':
        save(a.certificate,proof)
    else:
        assert canonical(proof)==canonical(json.loads(a.certificate.read_text()))
        assert a.output is not None
        save(a.output,{'status':'PASS: six complete coefficient identities and zero induction replayed',
            'source_sha256':proof['source_sha256'],'certificate_sha256':digest(a.certificate.read_bytes()),
            'zero_columns':proof['all_zero_columns'],'new_twelve_columns':NEW_TWELVE,
            'transportation_or_optimizer_called':False,'case4_excluded':False})
    print(json.dumps({'mode':a.mode,'certificate_sha256':digest(a.certificate.read_bytes()),
                     'zero_columns':len(proof['all_zero_columns']),'new_twelve_columns':NEW_TWELVE},indent=2))


if __name__=='__main__':
    main()
