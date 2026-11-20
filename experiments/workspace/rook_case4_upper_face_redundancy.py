"""Exact Gram redundancy of all170 saved upper-cell equalities.

The check uses original Gram rows and the99 independently proved zeros.
It calls no flow routine or optimizer. Two equalities use two Gram rows;
the other168 are single-row identities after zero substitution.
"""
import argparse
import gzip
import hashlib
import json
from pathlib import Path

import rook_case4_transportation_seed as seed

ROOT=Path(__file__).resolve().parents[2]
SEED_SHA='9eedacb4b62db8ad7058e291d04f83141fca306971ed278a58548ead4cd1e8a1'
CERT='experiments/logs/grids-and-triangles/rook-case4-transportation-upper-preparation01/certificate.json.gz'
CERT_SHA='065a60238630ddcf31281dc84e031c00ae0a728aea01788ab23eedff22dfc1fb'
NATIVE=seed.short.NATIVE


def sha(raw):return hashlib.sha256(raw).hexdigest()


def calculate(root):
    assert sha(Path(seed.__file__).read_bytes())==SEED_SHA
    proof=seed.prove(root);zeros=set(proof['seed_zero_columns'])
    raw=(root/CERT).read_bytes();assert sha(raw)==CERT_SHA
    certificate=json.loads(gzip.decompress(raw))
    assert certificate['zero_columns']==sorted(zeros)
    assert certificate['counts']['distinct_full_support_equalities']==170
    raw=(root/NATIVE).read_bytes();assert sha(raw)==seed.short.NATIVE_SHA
    inventory=json.loads(raw)['primary_inventory'];grams=inventory['Gram_rows']
    row_index={(i,j):k for k,(i,j,q,s)in enumerate(grams)}
    combinations={
        (5,15,27):[((5,27),1),((9,27),-1)],
        (7,11,27):[((7,27),1),((14,27),-1)],
    }
    records=[];single=double=0
    for equality in certificate['equalities']:
        assert equality['id']==len(records)
        support=equality['full_members'];population=equality['population']
        direct=equality['direct_Gram_equality_rows_on_this_face']
        if direct:
            rows=[(direct[0],1)];single+=1
        else:
            bound=equality['first_full_certificate']['target_original_upper_bound']
            assert bound['kind']=='triple'
            triple=inventory['triple_rows'][bound['index']]
            assert triple['members']==support
            sites=tuple(triple['triple'])
            rows=[(row_index[pair],coefficient)for pair,coefficient in combinations[sites]]
            double+=1
        remainder=[int(a in set(support))for a in range(1214)]
        rhs=population;expanded=[]
        for index,multiplier in rows:
            i,j,q,members=grams[index]
            rhs-=multiplier*q
            for a in members:remainder[a]-=multiplier
            expanded.append({'original_Gram_row':index,'core_pair':[i,j],
                             'coefficient':multiplier,'rhs':q})
        nonzero=[[a,c]for a,c in enumerate(remainder)if c]
        assert rhs==0 and all(a in zeros for a,c in nonzero)
        assert equality['active_members']==[a for a in support if a not in zeros]
        records.append({'equality_id':equality['id'],'target_full_members':support,
            'target_population':population,'Gram_combination':expanded,
            'remaining_coefficients_only_on_proved_zeros':nonzero,'rhs_difference':rhs})
    assert (single,double)==(168,2)
    return {'status':'PASS: all170 forced-upper equalities already follow from Gram on the99-zero face',
        'source_sha256':sha(Path(__file__).read_bytes()),'seed_source_sha256':SEED_SHA,
        'upper_census_certificate_sha256':CERT_SHA,'native_input_sha256':seed.short.NATIVE_SHA,
        'zero_columns':sorted(zeros),'single_Gram_row_equalities':single,
        'two_Gram_row_equalities':double,'records':records,
        'all1214_columns_checked_per_identity':True,'new_affine_rank_from_these_equalities':0,
        'flow_or_optimizer_called':False,'case4_excluded':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('write','replay'))
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--certificate',type=Path,required=True)
    p.add_argument('--output',type=Path)
    a=p.parse_args();actual=calculate(a.root)
    if a.mode=='write':
        assert not a.certificate.exists();a.certificate.write_text(json.dumps(actual,indent=2)+'\n')
    else:
        assert a.output is not None and not a.output.exists()
        assert actual==json.loads(a.certificate.read_text())
        report={'status':actual['status'],'source_sha256':actual['source_sha256'],
            'certificate_sha256':sha(a.certificate.read_bytes()),
            'single_Gram_row_equalities':168,'two_Gram_row_equalities':2,
            'all1214_columns_checked_per_identity':True,'flow_or_optimizer_called':False}
        a.output.write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps({'status':actual['status'],'certificate_sha256':sha(a.certificate.read_bytes())},indent=2))


if __name__=='__main__':main()
