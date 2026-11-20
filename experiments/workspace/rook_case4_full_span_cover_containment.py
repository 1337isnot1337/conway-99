"""Exact finite containment census for the new42-column parity cover; no solve."""
import argparse
import hashlib
import json
from pathlib import Path
import time

import numpy as np

ROOT=Path(__file__).resolve().parents[2]
LOG='experiments/logs/grids-and-triangles/'
INPUTS={
 'model':(LOG+'rook-case4-face112-weighted-parity-model01/model.json','c6cd72c995ce1a47db90fe7263f643131bc555ed50e329c7734536f5cf870ac3'),
 'arrays':(LOG+'rook-case4-face112-weighted-parity-model01/arrays.npz','59a06470793e6959a67ae30dfb29ecf0de4c8aa74661e1335d7676aa612c1e7e'),
 'model_cold':(LOG+'rook-case4-face112-weighted-parity-model01-cold-replay.json','567185c755134fcf7c15bb7be762bb2a70a503254259b2eb44a92f91abb39156'),
 'current_registry':(LOG+'rook-case4-parity-discovery-cycle-run02/result.json','fd0737a2c47664b52cf8cd48024a10e6936b3110f3cd2c8344b4081ff424adea'),
 'registry_cold':(LOG+'rook-case4-parity-discovery-cycle-run02-bindings.json','164f8c09048b9c9502d45cff407b0a78102b87aa9524bcc46e0d92b3b28590ca'),
 'cut':(LOG+'rook-case4-full-span-parity-query-run01/cut.json','f9080c52f570d3a9eabf461eabd6ef4dde6ac2fc2454ecc75367fe658d9e3fd7'),
 'cut_cold':(LOG+'rook-case4-full-span-parity-query-run01-cold.json','28cc396064b7e6ae5e7ad0ac401de0929aa3ea25b20d88483a1020abc79d620c'),
}


def sha(raw):return hashlib.sha256(raw).hexdigest()


def load(name):
    path,digest=INPUTS[name];raw=(ROOT/path).read_bytes();assert sha(raw)==digest
    return json.loads(raw) if name!='arrays' else ROOT/path


def bound(terms,upper,target):
    """Return m when a>=m*1_H with a nonnegative and m>0."""
    assert len({j for j,c in terms})==len(terms)
    if any(c<0 for j,c in terms):return None
    values={j:c for j,c in terms if c}
    if not target<=values.keys():return None
    minimum=min(values[j] for j in target)
    assert minimum>0
    return minimum


def controls():
    assert bound([[2,1],[7,1],[9,3]],2,{2,7})==1
    assert bound([[2,2],[7,3],[9,1]],4,{2,7})==2
    assert bound([[2,1],[7,1],[9,-1]],2,{2,7}) is None
    assert bound([[2,1],[9,1]],2,{2,7}) is None
    checks=0
    for upper in (1,2,4):
        terms=[[0,2],[1,3],[2,1]];m=bound(terms,upper,{0,1})
        for x0 in range(3):
            for x1 in range(3):
                for x2 in range(3):
                    if 2*x0+3*x1+x2<=upper:
                        assert m*(x0+x1)<=upper
                    checks+=1
    return {'literal_containment_controls':4,'nonnegative_integer_bound_controls':checks}


def run():
    started=time.monotonic();deadline=started+60
    model=load('model');cold=load('model_cold')
    assert cold['model_sha256']==INPUTS['model'][1] and cold['status'].startswith('PASS:')
    with np.load(load('arrays'),allow_pickle=False) as archive:
        names=['coefficients','column_indices','row_pointers','row_lower','row_upper',
               'original_column_ids','row_origin_kind','row_origin_index']
        arrays={name:archive[name] for name in names}
    for name,value in arrays.items():
        assert value.dtype.kind in 'iu' and sha(value.tobytes())==model['array_sha256'][name]
    assert len(arrays['row_lower'])==model['rows']==166013 and model['columns']==1102
    assert list(map(int,arrays['original_column_ids']))==[a for a in range(1214) if a not in set(model['fixed_zero_columns'])]
    current=load('current_registry');registry_cold=load('registry_cold')
    assert registry_cold['result']=={'path':INPUTS['current_registry'][0],'sha256':INPUTS['current_registry'][1]}
    assert registry_cold['status'].startswith('PASS:') and registry_cold['registered_cuts']==3
    cuts=current['registry'];assert len(cuts)==3
    new=load('cut');new_cold=load('cut_cold')
    assert new['status']=='EXACT_VIOLATED_PARITY_CUT' and new['parity_rhs']==1
    assert new['forbidden_ones']==[] and new['inequality']['upper']==-1
    H=new['active_original_support'];target=set(H)
    assert len(H)==42 and H==sorted(target)
    assert new['inequality']['terms']==[[a,-1] for a in H]
    assert new_cold['status'].startswith('PASS:') and new_cold['cut_arithmetic']['support_size']==42
    containers=[];small=[];counts={'row_orientations':0,'negative_coefficient':0,'support_missing':0,'containers':0}
    ledger=hashlib.sha256()
    def examine(row_id,terms,lower,upper,origin):
        if time.monotonic()>=deadline:raise TimeoutError('containment census budget')
        for sign,endpoint in ((1,upper),(-1,-lower)):
            coefficients=[[j,sign*c] for j,c in terms]
            counts['row_orientations']+=1
            if any(c<0 for j,c in coefficients):
                reason='negative_coefficient';counts[reason]+=1
                ledger.update(f'{row_id}:{sign}:{reason}\n'.encode());continue
            m=bound(coefficients,endpoint,target)
            if m is None:
                reason='support_missing';counts[reason]+=1
                ledger.update(f'{row_id}:{sign}:{reason}\n'.encode());continue
            counts['containers']+=1
            record={'row_id':row_id,'orientation':sign,'origin':origin,'nonnegative_terms':coefficients,
                    'upper':endpoint,'minimum_target_coefficient':m,
                    'target_sum_upper_fraction':[endpoint,m],
                    'literal_upper_is_one_or_two':endpoint in (1,2),
                    'target_upper_at_most_two':endpoint<=2*m}
            containers.append(record)
            if endpoint<=2*m:small.append(record)
            ledger.update(f'{row_id}:{sign}:container:{endpoint}:{m}\n'.encode())
    original=arrays['original_column_ids'];ptr=arrays['row_pointers']
    # Every retained selector row is inspected, with both finite sides.
    for r in range(166013):
        start,end=map(int,ptr[r:r+2])
        terms=[[int(original[j]),int(c)] for j,c in zip(arrays['column_indices'][start:end],arrays['coefficients'][start:end])]
        examine(r,terms,int(arrays['row_lower'][r]),int(arrays['row_upper'][r]),
                {'kind':int(arrays['row_origin_kind'][r]),'index':int(arrays['row_origin_index'][r])})
    for i,entry in enumerate(cuts):
        row=entry['certificate']['inequality'];terms=row['terms']
        examine(167115+i,terms,sum(min(c,0) for a,c in terms),row['upper'],{'dynamic_registry_index':i})
    assert counts['row_orientations']==2*(166013+3)
    assert sum(counts[k] for k in ['negative_coefficient','support_missing','containers'])==counts['row_orientations']
    return {'status':'COMPLETE: finite current-row nonnegative containment census',
            'source_sha256':sha(Path(__file__).read_bytes()),'inputs':INPUTS,'controls':controls(),
            'target_original_columns':H,'selector_rows_checked':166016,
            'maxmin_extension_rows_excluded_by_singleton_support':1102,
            'unit_box_upper_rows_excluded_by_singleton_support':1102,
            'counts':counts,'classification_stream_sha256':ledger.hexdigest(),
            'nonnegative_containers':containers,'upper_at_most_two_witnesses':small,
            'odd_sum_forced_one_by_this_family':bool(small),
            'small_bound_interpretation':'If a>=m*1_H>=0 and a*x<=U<=2m, odd positive integer sum_H x is exactly1.',
            'scope':'Literal retained rows and three frozen dynamic cuts only; no search over row combinations.',
            'optimizer_calls':0,'model_rebuilds':0,'seconds':time.monotonic()-started}


if __name__=='__main__':
    if not __debug__:raise RuntimeError('assertions are required')
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args();assert not args.output.exists()
    result=run();args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,sort_keys=True,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','counts','odd_sum_forced_one_by_this_family','seconds']}))
