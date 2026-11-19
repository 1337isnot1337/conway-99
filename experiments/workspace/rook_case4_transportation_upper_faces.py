"""Complete forced-upper census on105 frozen case4 transportation flows.

Every equality is expanded into original Gram/capacity rows and the99
proved-zero premises. No case4 max-flow or numerical optimizer is run.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from pathlib import Path
import resource
import signal
import time

import rook_case4_transportation_seeded as parent
import rook_transportation_upper_faces as upper

ROOT=Path(__file__).resolve().parents[2]
PARENT_SHA='98a5c30e1e091899a48c27341b429e10f83856f41851975721383897fbe1be0c'
UPPER_SHA='db494ee5d8eae98f3b724e277c67723676c343e94f17ade6be528eab00007ccc'
PREP='experiments/logs/grids-and-triangles/rook-case4-transportation-seeded-preparation01'
PREP_SHA='a09533f977d74818efae4632245168a1a99b35bb8ecf13663c2345ba14edabca'
RESULT='experiments/logs/grids-and-triangles/rook-case4-transportation-seeded-run01.json'
RESULT_SHA='9bb4b9730bd866503116b8131f2804098b53a561da64851a6fef7a55ad001691'
REPLAY='experiments/logs/grids-and-triangles/rook-case4-transportation-seeded-run01-replay.json'
REPLAY_SHA='96b7a824f9afce82299bf8cd2d3ca7b0dac3d1cd3885071ad22f4c587a4dd7d9'
SECONDS=60
digest,canonical,save=parent.digest,parent.canonical,parent.save


def bindings():
    assert digest(Path(parent.__file__).read_bytes())==PARENT_SHA
    assert digest(Path(upper.__file__).read_bytes())==UPPER_SHA
    assert upper.original is parent.flow
    return {'source_sha256':digest(Path(__file__).read_bytes()),
        'upper_cell_helper_sha256':UPPER_SHA,'seeded_wrapper_sha256':PARENT_SHA,
        'seeded_preparation_sha256':PREP_SHA,'saved_flow_result_sha256':RESULT_SHA,
        'saved_replay_sha256':REPLAY_SHA,'ancestor_bindings':parent.bindings()}


def load(root):
    source=bindings()
    assert digest((root/PREP/'preparation.json').read_bytes())==PREP_SHA
    prepared,model,seed=parent.load(root,root/PREP)
    raw=(root/RESULT).read_bytes()
    assert digest(raw)==RESULT_SHA
    result=json.loads(raw)
    replay_raw=(root/REPLAY).read_bytes()
    assert digest(replay_raw)==REPLAY_SHA
    replay=json.loads(replay_raw)
    assert result['source_bindings']==parent.bindings()
    assert result['preparation_sha256']==PREP_SHA
    assert result['definition_sha256']==prepared['definition_sha256']
    assert result['complete_fixed_point']and not result['contradiction']
    assert result['events']==[]and result['new_zero_columns']==[]
    assert result['zero_columns']==seed['seed_zero_columns']==replay['zero_columns']
    assert replay['result_sha256']==RESULT_SHA and replay['complete_fixed_point']
    assert [r['projection_id']for r in result['terminal_flows']]==list(range(105))
    return source,model,seed,result['terminal_flows']


def full_lower_certificate(model,domain,record,zeros,reasons):
    """Prove-target <= a valid original upper row <= -capacity."""
    assert record['kind']=='forced_positive_upper'and record['capacity']>0
    full={(c['row'],c['column']):c for c in domain['cells']}
    target=tuple(record['cell']);cell=full[target]
    assert record['capacity']==cell['capacity_proof']['upper']
    cut=record['cut'];combination=Counter()
    for u in cut['rows']:combination['Gram',domain['row_Gram_ids'][u]]-=1
    for v in cut['columns']:combination['Gram',domain['column_Gram_ids'][v]]+=1
    for entry in cut['capacity_cells']:
        key=tuple(entry)
        if key==target:continue
        bound=full[key]['capacity_proof']
        combination[bound['kind'],bound['index']]+=1
    coefficients=[0]*1214;rhs=0;terms=[]
    for (kind,index),weight in sorted(combination.items()):
        if not weight:continue
        assert kind=='Gram'or weight>0
        support,quota=parent.original.row_data(model,kind,index)
        for a in support:coefficients[a]+=weight
        rhs+=quota*weight
        terms.append({'kind':kind,'index':index,'coefficient':weight,'rhs':quota})
    assert rhs==-record['capacity']
    indicator=set(cell['members'])
    remainder=[c+int(a in indicator)for a,c in enumerate(coefficients)]
    assert set(remainder)<={-1,0,1}
    negative=[a for a,c in enumerate(remainder)if c<0]
    assert set(negative)<=zeros
    assert all(a in reasons for a in negative)
    # The original upper bound is checked against the full literal support.
    bound=cell['capacity_proof']
    support,quota=parent.original.row_data(model,bound['kind'],bound['index'])
    assert support==cell['members']and quota==record['capacity']
    return {'projection_id':domain['id'],'cell':list(target),'residual_cut':cut,
        'original_upper_row_combination':terms,'combined_upper_rhs':rhs,
        'all1214_combined_coefficients':coefficients,
        'target_full_members':cell['members'],'target_population':record['capacity'],
        'target_original_upper_bound':bound,
        'negative_remainder_prior_zero_premises':[[a,reasons[a]]for a in negative],
        'positive_remainder_columns':[a for a,c in enumerate(remainder)if c>0],
        'remainder_nonnegative_after99_zeros':True,
        'proof':'The combined row is at least minus the target population after proved zeros. Its upper bound is minus the cell capacity. Together with the original capacity, this forces equality.'}


def calculate(root):
    source,model,seed,saved=load(root)
    zeros,reasons=parent.seed_state(seed)
    direct_Gram={}
    for index,(i,j,q,support)in enumerate(model['Gram_rows']):
        key=(tuple(a for a in support if a not in zeros),q)
        direct_Gram.setdefault(key,[]).append(index)
    equalities=[];positions={};projection_records=[];counts=Counter()
    for domain,flow_record in zip(model['domains'],saved):
        # Verify the final zero-face property too; this uses no max-flow call.
        parent.original.verify_flow_record(domain,zeros,parent.MODE,flow_record)
        active,capacities=parent.original.projected_state(domain,zeros,parent.MODE)
        values={e:0 for e in capacities}
        for u,v,f in flow_record['positive_cell_flows']:values[u,v]=f
        records=upper.upper_faces(domain['row_margins'],domain['column_margins'],capacities,values)
        assert [tuple(r['cell'])for r in records]==sorted(capacities)
        by_cell={tuple(r['cell']):r for r in records}
        complete=[]
        for cell in domain['cells']:
            key=(cell['row'],cell['column'])
            item={'cell':list(key),'full_members':cell['members'],'capacity_proof':cell['capacity_proof']}
            if key not in active:
                assert set(cell['members'])<=zeros
                # Such a cell is already identically zero on the current face.
                item.update(kind='inactive_zero_cell',forced_upper=cell['capacity_proof']['upper']==0,
                            upper_equals_zero=cell['capacity_proof']['upper']==0)
                counts['inactive_zero_cells']+=1
            else:
                record=by_cell[key]
                item.update(record)
                counts['active_cells']+=1
                if record['forced_upper']:
                    assert record['kind']=='forced_positive_upper'
                    upper.verify_cell_inequality(domain['row_margins'],domain['column_margins'],capacities,record)
                    certificate=full_lower_certificate(model,domain,record,zeros,reasons)
                    identity=(tuple(cell['members']),record['capacity'])
                    if identity not in positions:
                        positions[identity]=len(equalities)
                        live=tuple(a for a in cell['members']if a not in zeros)
                        equalities.append({'id':len(equalities),'full_members':cell['members'],
                            'active_members':list(live),'population':record['capacity'],
                            'first_full_certificate':certificate,'origins':[],
                            'direct_Gram_equality_rows_on_this_face':direct_Gram.get((live,record['capacity']),[])})
                    equality=equalities[positions[identity]]
                    equality['origins'].append({'projection_id':domain['id'],'cell':list(key),
                                                'original_upper_bound':cell['capacity_proof']})
                    item['equality_id']=equality['id']
                    counts['forced_positive_upper_cells']+=1
                    counts['forced_upper_'+cell['capacity_proof']['kind']]+=1
                else:counts[record['kind']]+=1
            complete.append(item)
        assert len(complete)==len(domain['cells'])
        projection_records.append({'projection_id':domain['id'],'core_vertex':domain['core_vertex'],
            'grid_pair':domain['grid_pair'],'cells':complete})
    assert len(projection_records)==105
    assert counts['active_cells']==1839 and counts['inactive_zero_cells']==23
    assert sum(len(r['cells'])for r in projection_records)==1862
    forced_ones=sorted({e['active_members'][0]for e in equalities
                        if e['population']==1 and len(e['active_members'])==1})
    assert not set(forced_ones)&zeros
    counts['distinct_full_support_equalities']=len(equalities)
    counts['direct_Gram_duplicates_on99_face']=sum(bool(e['direct_Gram_equality_rows_on_this_face'])for e in equalities)
    counts['not_direct_Gram_duplicates']=sum(not e['direct_Gram_equality_rows_on_this_face']for e in equalities)
    return {'status':'COMPLETE: every original cell classified from the105 saved flows',
        'source_bindings':source,'zero_columns':sorted(zeros),'projections':projection_records,
        'counts':dict(counts),'equalities':equalities,'forced_one_columns':forced_ones,
        'every_full1214_coefficient_expansion_checked':True,
        'deduplication_key':'identical full original member set and right-hand side only',
        'direct_Gram_duplicate_test':'active supports and quotas equal after proved99 zeros; no broader row-space independence claim',
        'all1862_original_cells_accounted_for':True,
        'all1839_active_cells_have_complete_upper_classification':True,
        'case4_max_flow_calls':0,'optimizer_calls':0,'joint_incidence_feasibility_claimed':False,
        'case4_excluded':False}


def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('mode',choices=('prepare','replay'))
    p.add_argument('--root',type=Path,default=ROOT)
    p.add_argument('--directory',type=Path,required=True)
    p.add_argument('--output',type=Path)
    a=p.parse_args();start=time.monotonic()
    def expired(_signum,_frame):raise TimeoutError('60second exact upper-face census/replay')
    previous=signal.signal(signal.SIGALRM,expired)
    signal.setitimer(signal.ITIMER_REAL,SECONDS)
    try:
        if a.mode=='prepare':
            assert not a.directory.exists()
            a.directory.mkdir(parents=True)
            controls=upper.controls()
            result=calculate(a.root)
            raw=canonical(result);compressed=gzip.compress(raw,mtime=0)
            (a.directory/'certificate.json.gz').write_bytes(compressed)
            report={'status':result['status'],'source_bindings':bindings(),'controls':controls,
                'certificate_raw_sha256':digest(raw),'certificate_gzip_sha256':digest(compressed),
                'certificate_raw_bytes':len(raw),'certificate_gzip_bytes':len(compressed),
                'counts':result['counts'],'forced_one_columns':result['forced_one_columns'],
                'case4_max_flow_calls':0,'optimizer_calls':0,'case4_excluded':False,
                'seconds':time.monotonic()-start,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
            save(a.directory/'preparation.json',report)
        else:
            assert a.output is not None and not a.output.exists()
            report=json.loads((a.directory/'preparation.json').read_text())
            assert report['source_bindings']==bindings()
            compressed=(a.directory/'certificate.json.gz').read_bytes()
            assert digest(compressed)==report['certificate_gzip_sha256']
            raw=gzip.decompress(compressed)
            assert digest(raw)==report['certificate_raw_sha256']
            actual=calculate(a.root)
            assert canonical(actual)==raw
            report={'status':'PASS: complete upper-face census and every original-row certificate replayed',
                'source_bindings':bindings(),'certificate_raw_sha256':digest(raw),
                'certificate_gzip_sha256':digest(compressed),'counts':actual['counts'],
                'forced_one_columns':actual['forced_one_columns'],
                'case4_max_flow_calls':0,'tiny_control_flows_repeated':False,
                'optimizer_calls':0,'case4_excluded':False,'seconds':time.monotonic()-start}
            save(a.output,report)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    print(json.dumps(report,indent=2),flush=True)


if __name__=='__main__':main()
