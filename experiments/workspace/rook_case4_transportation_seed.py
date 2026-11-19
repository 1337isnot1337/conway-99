"""Exact99-zero seed for a new case4 transportation continuation.

The88 short Gram/triple zeros are rederived from original rows. The14
published empty covers are located in the full frozen registry, and each
unit is independently justified by a complete exterior-neighbor dominance
test. Their intersection has three columns. No flow or optimizer is run.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path
import struct

import rook_case4_transportation_short_faces as short

ROOT=Path(__file__).resolve().parents[2]
SHORT_SHA='dd760f7943df8fee0ca1c7c0ef8343085d5b959f4f9def2c3d8c55b7963976b9'
SHORT_CERT='experiments/logs/grids-and-triangles/rook-case4-transportation-short-faces-certificate.json'
SHORT_CERT_SHA='a6eb6d2b31d228a9377f536c6c913441b5d4e19faf72d5331f3db95496463297'
METADATA='experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lazy-native-model.json'
METADATA_SHA='aeb636198cb0b9749e2142a596404181edf92923d55d5bdf764a8f9432439b68'
REGISTRY='experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lazy-native-registry.bin.gz'
REGISTRY_SHA='c32e31d9ce6ec6168cea1c9f6c6ea4165a2ca7a8f2144a59a31e5a1d6da7b543'
REGISTRY_RAW_SHA='3b819e29bc9aacdb5217b151f32b35cb186aa3b8a93a37784edc912ddac36736'
COVER_CERT_SHA='a255f8876d3d827ff94d7df2f2640be6963348987043665dcd6fc53bf41dff8f'
DOMAIN='experiments/logs/grids-and-triangles/complement-rook-35core-case0004-exterior-rows.json.gz'
DOMAIN_SHA='10377b5494b8d39e3b41f400b39af485c1db44d06232e1c03663a07f530e8628'
DOMAIN_RAW_SHA='15fc5b70efe7b16c5bcb25a67edc8a490e26ebb783090f45d6c734f5bebb7b40'
UNITS=[352,353,354,355,439,552,553,645,869,873,957,1080,1081,1167]


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def checked(root,path,expected):
    raw=(root/path).read_bytes()
    assert digest(raw)==expected
    return raw


def prove(root):
    assert digest(Path(short.__file__).read_bytes())==SHORT_SHA
    short_raw=checked(root,SHORT_CERT,SHORT_CERT_SHA)
    proof=short.prove(root)
    assert canonical(proof)==canonical(json.loads(short_raw))
    native=json.loads(checked(root,short.NATIVE,short.NATIVE_SHA))['primary_inventory']
    assert native['complete_cover_certificate_sha256']==COVER_CERT_SHA
    metadata=json.loads(checked(root,METADATA,METADATA_SHA))
    assert metadata['complete']and metadata['primary_inventory_sha256']==short.PRIMARY_SHA
    assert metadata['registry_metadata']['cover_certificate_sha256']==COVER_CERT_SHA
    assert metadata['registry_sha256']==REGISTRY_SHA and metadata['registry']==REGISTRY
    raw=gzip.decompress(checked(root,REGISTRY,REGISTRY_SHA))
    assert digest(raw)==REGISTRY_RAW_SHA==metadata['registry_metadata']['decompressed_sha256']
    assert len(raw)==178533*154==metadata['registry_metadata']['decompressed_bytes']
    units=[]
    previous=-1
    view=memoryview(raw)
    for index in range(178533):
        offset=index*154
        target=struct.unpack_from('<H',view,offset)[0]
        bits=int.from_bytes(view[offset+2:offset+154],'little')
        assert previous<=target<1214 and bits<1<<1214 and not(bits>>target&1)
        previous=target
        if not bits:units.append([index,target])
    assert [a for index,a in units]==UNITS==metadata['registry_metadata']['initial_unit_targets']
    assert [index for index,a in units]==metadata['initial_prefix_clause_ids_in_order']

    raw_domain=gzip.decompress(checked(root,DOMAIN,DOMAIN_SHA))
    assert digest(raw_domain)==DOMAIN_RAW_SHA
    domain=json.loads(raw_domain)
    assert domain['case_index']==4
    core=domain['core_adjacency_rows']
    masks=domain['column_masks35']
    assert len(core)==35 and len(masks)==len(set(masks))==1214
    assert all(type(v)is int and 0<=v<1<<35 for v in core+masks)
    assert all(not(core[i]>>i&1)for i in range(35))
    assert all((core[i]>>j&1)==(core[j]>>i&1)for i in range(35)for j in range(35))
    G=[[12*(i==j)+2-(core[i]&core[j]).bit_count()-(core[i]>>j&1)
        for j in range(35)]for i in range(35)]
    assert G==domain['Gram']
    for i,j,q,support in native['Gram_rows']:
        assert G[i][j]==q
        assert support==[a for a,h in enumerate(masks)if h>>i&1 and h>>j&1]
    targets=[[2-(h>>i&1)-(core[i]&h).bit_count()for i in range(35)]+[14-h.bit_count()]
             for h in masks]
    assert targets==domain['row_targets36']and all(min(t)>=0 for t in targets)
    zero_masks=[sum(1<<i for i in range(35)if t[i]==0)for t in targets]
    augmented=[h|(1<<35)for h in masks]
    unit_proofs=[]
    for registry_id,a in units:
        neighbors=[b for b in range(1214)if b!=a and (masks[a]&masks[b]).bit_count()<=1
                   and not(masks[b]&zero_masks[a])and not(masks[a]&zero_masks[b])]
        assert neighbors==domain['eligible_neighbor_column_ids'][a]
        witness=None
        for i in range(36):
            for j in range(36):
                demand=targets[a][i]-targets[a][j]
                if demand>0 and not any(augmented[b]>>i&1 and not(augmented[b]>>j&1)for b in neighbors):
                    witness=(i,j,demand)
                    break
            if witness is not None:break
        assert witness is not None
        i,j,demand=witness
        products=[[b,(augmented[b]>>i&1)-(augmented[b]>>j&1)]for b in neighbors]
        assert max((v for b,v in products),default=0)<=0
        unit_proofs.append({'target':a,'registry_clause_id':registry_id,'original_clause':[-a-1],
            'coordinate_pair':[i,j],'positive_original_demand':demand,
            'target_coordinates':targets[a],
            'complete_eligible_neighbor_columns':neighbors,'all_neighbor_difference_products':products,
            'positive_difference_cover':[],
            'proof':'A selected source would require positive mixed/degree coordinate difference; every complete eligible neighbor has nonpositive difference.'})
    zeros=sorted(set(proof['all_zero_columns'])|set(UNITS))
    assert len(zeros)==99 and sorted(set(proof['all_zero_columns'])&set(UNITS))==[352,354,957]
    reasons={}
    for step in proof['steps']:
        for a in step['new_zero_columns']:reasons[str(a)]={'seed_kind':'short_row_combination','step':step['step']}
    for item in unit_proofs:
        reasons.setdefault(str(item['target']),{'seed_kind':'empty_cover','registry_clause_id':item['registry_clause_id']})
    assert sorted(map(int,reasons))==zeros
    return {'status':'PASS:99-zero union rederived from full original rows and literal empty-cover dominance',
        'source_sha256':digest(Path(__file__).read_bytes()),'short_source_sha256':SHORT_SHA,
        'short_certificate_path':SHORT_CERT,'short_certificate_sha256':SHORT_CERT_SHA,
        'native_input_sha256':short.NATIVE_SHA,'primary_inventory_sha256':short.PRIMARY_SHA,
        'registry_metadata_sha256':METADATA_SHA,'registry_gzip_sha256':REGISTRY_SHA,
        'registry_raw_sha256':REGISTRY_RAW_SHA,'cover_certificate_sha256':COVER_CERT_SHA,
        'exterior_domain_gzip_sha256':DOMAIN_SHA,'exterior_domain_raw_sha256':DOMAIN_RAW_SHA,
        'all178533_registry_records_checked':True,'all14_empty_covers_reproved_directly':True,
        'complete_neighbor_reconstruction_targets':UNITS,'unit_proofs':unit_proofs,
        'short_zero_columns':proof['all_zero_columns'],'empty_cover_units':UNITS,
        'intersection':[352,354,957],'seed_zero_columns':zeros,'seed_reasons':reasons,
        'numeric_proposal_used':False,'flow_or_optimizer_called':False,
        'case4_excluded':False}


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
    actual=prove(a.root)
    if a.mode=='write':save(a.certificate,actual)
    else:
        assert a.output is not None and canonical(actual)==canonical(json.loads(a.certificate.read_text()))
        save(a.output,{'status':'PASS:99 exact seed zeros and14 full-domain empty-cover proofs replayed',
            'source_sha256':actual['source_sha256'],'certificate_sha256':digest(a.certificate.read_bytes()),
            'seed_zero_columns':actual['seed_zero_columns'],'flow_or_optimizer_called':False})
    print(json.dumps({'mode':a.mode,'certificate_sha256':digest(a.certificate.read_bytes()),
                     'seed_zero_columns':len(actual['seed_zero_columns'])},indent=2))


if __name__=='__main__':
    main()
