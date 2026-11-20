"""Tiny direct-cut replay controls; no native import or production point search."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path
import time

SUBJECT=Path(__file__).with_name('rook_case4_full_span_parity_query.py')
SUBJECT_SHA='3a66af1c2500eebdb36001a004628460f936efc60584d411a2dbdc37d4a928da'


def run():
    started=time.monotonic()
    assert hashlib.sha256(SUBJECT.read_bytes()).hexdigest()==SUBJECT_SHA
    loader=importlib.util.spec_from_file_location('frozen_parity_query_controls',SUBJECT)
    subject=importlib.util.module_from_spec(loader);loader.loader.exec_module(subject)
    accepted,rejected=0,0
    for signed in (False,True):
        # The three literal 0/1 rows add to 2*x0+2*x1+2*x2+x3 = 3 or4.
        # Their real point has x0=x1=x2=1/2 and x3=0 or1 respectively.
        gram=[[0,0,0,[]] for _ in range(630)]
        gram[0]=[0,0,2 if signed else 1,[0,1,3]]
        gram[1]=[0,1,1,[1,2]];gram[2]=[0,2,1,[0,2]]
        nums=[1,1,1,2 if signed else 0]+[0]*1210
        assert all(sum(nums[a] for a in support)==2*q for i,j,q,support in gram)
        spec={'basis_original_Gram_witness_hex':['0x7']+['0x0']*285,
              'fixed_zero_columns':list(range(1102,1214)),
              'kept_original_columns':list(range(1102)),
              'denominator':'2','point_numerators1214':list(map(str,nums))}
        values=[0]*2491;values[0]=1;values[289]=1;values[2490]=0 if signed else 1
        vector={'values':values}
        cut={'original_Gram_row_ids':[0,1,2],
             'full_original1214_integer_coefficients':[2,2,2,1]+[0]*1210,
             'original_Gram_rhs_sum':4 if signed else 3,'parity_rhs':0 if signed else 1,
             'active_original_support':[3],'forbidden_ones':[3] if signed else [],
             'removed_proved_zero_odd_columns':[],
             'inequality':{'terms':[[3,1 if signed else -1]],'upper':0 if signed else -1},
             'exact_deficit_numerator':'2','point_denominator':'2'}
        result=subject.direct_cut_check(spec,vector,cut,gram)
        assert result['deficit_numerator']=='2' and result['support_size']==1
        accepted+=1
        changed=[]
        for kind in ('wrong_row','coefficient','rhs','deficit','signed_term','upper','nonboolean','missing','outside_flip','choice'):
            s,v,c=copy.deepcopy(spec),copy.deepcopy(vector),copy.deepcopy(cut)
            if kind=='wrong_row':c['original_Gram_row_ids']=[0,1]
            elif kind=='coefficient':c['full_original1214_integer_coefficients'][0]+=1
            elif kind=='rhs':c['original_Gram_rhs_sum']+=2
            elif kind=='deficit':c['exact_deficit_numerator']='3'
            elif kind=='signed_term':c['inequality']['terms'][0][1]*=-1
            elif kind=='upper':c['inequality']['upper']+=1
            elif kind=='nonboolean':v['values'][0]=True
            elif kind=='missing':v['values'].pop()
            elif kind=='outside_flip':v['values'][1388]=1
            else:v['values'][0]=0
            try:subject.direct_cut_check(s,v,c,gram)
            except AssertionError:rejected+=1;changed.append(kind)
            else:raise AssertionError(('tamper accepted',signed,kind))
        assert len(changed)==10
    return {'status':'PASS: two literal Gram cut controls and20 tamper rejections',
            'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
            'query_source_sha256':SUBJECT_SHA,'accepted_controls':accepted,'tamper_rejections':rejected,
            'signed_and_unsigned_forbidden_vertices_checked':True,'native_libraries_imported':False,
            'production_points_used':0,'optimizer_calls':0,'seconds':time.monotonic()-started}


if __name__=='__main__':
    if not __debug__:raise RuntimeError('assertions are required')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    result=run();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps(result))
