"""Two Gram equations and one triple capacity force18 original columns zero.

This standalone integer proof checks the entire1214-column domain. It uses
neither earlier zero premises nor LP extension rows, coordinate covers,
exterior-row potentials or a numerical optimizer.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
NATIVE='experiments/logs/grids-and-triangles/complement-rook-35core-case0004-native-cpsat-model.json'
NATIVE_SHA='a9004e97a2d166bf8b162609cfb538eae0dd4d26942b6df5119b6a88d65ec476'
PRIMARY_SHA='5a6af30f47826df629a3795ceea0a0a91b853cf8149860355ce1bd17ac0094b2'
EXPECTED=[302,309,315,329,335,342,809,816,822,828,841,848,
          1021,1027,1034,1041,1054,1061]


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
    assert [(i,j) for i,j,q,s in grams]==[(i,j)for i in range(35)for j in range(i,35)]
    masks=[0]*1214
    lookup={}
    for index,(i,j,quota,support) in enumerate(grams):
        assert support==sorted(set(support)) and type(quota)is int and quota>=0
        lookup[i,j]=(index,quota,support)
        if i==j:
            for a in support:masks[a]|=1<<i
    for i,j,quota,support in grams:
        assert support==[a for a,h in enumerate(masks) if h>>i&1 and h>>j&1]
    first=lookup[9,27]
    second=lookup[5,27]
    assert first[1]==1 and second[1]==2
    sites=[5,15,27]
    triple=next(item for item in inventory['triple_rows'] if item['triple']==sites)
    support=[a for a,h in enumerate(masks) if all(h>>i&1 for i in sites)]
    assert support==triple['members'] and len(support)==21
    assert triple['old_CNF_coverage']['extra_row_index']==5
    # The capacity is not one of the triples dominated by a quota-one pair.
    containing=[(i,j)for i,j,q,s in grams if q==1 and set(support)<=set(s)]
    assert not containing
    coefficients=[0]*1214
    for a in first[2]:coefficients[a]+=1
    for a in second[2]:coefficients[a]-=1
    for a in support:coefficients[a]+=1
    assert set(coefficients)=={0,1}
    positive=[a for a,c in enumerate(coefficients)if c]
    assert positive==EXPECTED
    assert first[1]-second[1]+1==0
    # This is also a direct saturation of one row of a transportation table.
    common_5_27=set(second[2])
    common_9_27=set(first[2])
    intersection=common_5_27&common_9_27
    assert common_5_27==intersection|set(support)
    assert not intersection&set(support)
    assert common_9_27-intersection==set(positive)
    signatures=[]
    for a in positive:
        sites_a=[i for i in range(35)if masks[a]>>i&1]
        assert sites_a[0]in(4,7,8) and sites_a[1]==9 and sites_a[-1]==27
        signatures.append([a,sites_a])
    return {
        'status':'PASS: exact full-domain two-Gram-plus-triple saturation certificate',
        'source_sha256':digest(Path(__file__).read_bytes()),
        'native_input_path':NATIVE,'native_input_sha256':NATIVE_SHA,
        'primary_inventory_sha256':PRIMARY_SHA,
        'all630_Gram_supports_reconstructed_from_diagonals':True,
        'complete_original_columns':1214,
        'Gram_row_combination':[
            {'pair':[9,27],'original_Gram_row':first[0],'multiplier':1,'rhs':1},
            {'pair':[5,27],'original_Gram_row':second[0],'multiplier':-1,'rhs':2}],
        'triple_capacity':{'sites':sites,'members':support,'upper_bound':1,
            'multiplier':1,'extra_triple_row_index':5,
            'dominating_quota_one_pairs':containing},
        'combined_rhs_upper_bound':0,
        'all1214_combined_coefficients':coefficients,
        'positive_coefficient_zero_columns':positive,
        'positive_column_core_signatures':signatures,
        'saturation':{'pair5_27_population':2,'pair9_27_population':1,
            'triple5_15_27_capacity':1,'intersection5_9_27_support':sorted(intersection),
            'pair5_27_is_disjoint_union_of_intersection_and_capacity_support':True,
            'therefore_triple_and_intersection_populations_are_each_exactly_one':True},
        'premise':'nonnegative real Gram weights and the stated triple capacity',
        'triple_capacity_necessity':'Two remaining graph vertices cannot share three core neighbors, since every distinct vertex pair has at most two common neighbors.',
        'earlier_zero_premises_used':False,'coordinate_covers_used':False,
        'exterior_row_cuts_used':False,'LP_extension_or_t_used':False,
        'upper_unit_boxes_used':False,'integrality_of_weights_used':False,
        'optimizer_called':False,'case4_excluded':False,
    }


def write(path,value):
    assert not path.exists()
    path.write_text(json.dumps(value,indent=2)+'\n')


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['write','replay'])
    parser.add_argument('--root',type=Path,default=ROOT)
    parser.add_argument('--certificate',type=Path,required=True)
    parser.add_argument('--output',type=Path)
    args=parser.parse_args()
    current=prove(args.root)
    if args.mode=='write':
        write(args.certificate,current)
        report={'status':current['status'],'certificate_sha256':digest(args.certificate.read_bytes()),
            'zero_columns':current['positive_coefficient_zero_columns']}
    else:
        assert canonical(current)==canonical(json.loads(args.certificate.read_text()))
        assert args.output is not None
        report={'status':'PASS: all1214 coefficients, two literal Gram rows and triple support replayed',
            'source_sha256':digest(Path(__file__).read_bytes()),
            'certificate_sha256':digest(args.certificate.read_bytes()),
            'full_columns':1214,'Gram_rows':2,'triple_capacities':1,
            'zero_columns':current['positive_coefficient_zero_columns'],
            'prior_zero_premises_used':False,'optimizer_called':False,'case4_excluded':False}
        write(args.output,report)
    print(json.dumps(report,indent=2))


if __name__=='__main__':
    main()
