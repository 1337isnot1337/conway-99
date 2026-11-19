"""Read-only independent arithmetic and existing-CNF audit of case4 cuts.

No subject module is imported. No formula is rebuilt and no solver is
called. The literal prepared CNF, if present at its bound path, is checked
against the original complete-CNF hash and every saved appended block.
"""

import argparse
import gzip
import hashlib
from itertools import combinations
import json
from math import gcd
from pathlib import Path
import time


ROOT=Path(__file__).resolve().parents[2]
LOGS=ROOT/'experiments/logs/grids-and-triangles'
BOUND={
    'source':('experiments/workspace/complement_rook_35core_case0004_row_cut_boolean.py','2b231f418645d13c18fa4995277858e9b4fe5b770000e7ea742b5e5336fbfe45'),
    'model':('experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-cut-boolean-model.json','51268b36baee6ba62c7925ab85a18724d5e9b28006cb2a62f6bd3228f862346a'),
    'base':('experiments/logs/grids-and-triangles/complement-rook-35core-first-local-sweep01/case0004-model.json','43fc0c40a724f4c287df770fce58abc45835ee7534f2b7e5cd06d3baf380cfde'),
    'inventory':('experiments/logs/grids-and-triangles/complement-rook-35core-case0004-lp-model.json.gz','18e7b79a7e83c1c40f0c0c29301703400f26b42401f0b07a2f21783a298119a6'),
    'row_domain':('experiments/logs/grids-and-triangles/complement-rook-35core-case0004-exterior-rows.json.gz','10377b5494b8d39e3b41f400b39af485c1db44d06232e1c03663a07f530e8628'),
    'cut_result':('experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-loop-run01.json','9b0713b668e2c0ae47139007cdf6ad8961be2fb0e9caf2b42e0193a5528ecaa6'),
    'weighted_encoder':('experiments/workspace/root_prism_free_f0_weighted_threshold.py','a0c4b38d7787c8e6565ab122e0fdf41655ea40a9f0f218c0f860cd59d3f05144'),
    'preflight':('experiments/logs/grids-and-triangles/complement-rook-35core-case0004-row-cut-boolean-preflight.json','9482cabcb5fc0a615fd6cfc57c0394f1678fc9830ed73e39460b1769cd4009b1'),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':')).encode()


def run():
    started=time.monotonic()
    values={}
    for name,(path,expected) in BOUND.items():
        raw=(ROOT/path).read_bytes()
        assert sha(raw)==expected
        if not path.endswith('.py'):
            values[name]=json.loads(gzip.decompress(raw) if path.endswith('.gz') else raw)
    model,base=values['model'],values['base']
    inventory,row=values['inventory'],values['row_domain']
    cuts=values['cut_result']['exact_cuts']
    assert len(cuts)==60 and values['preflight']['cnf_sha256']==model['cnf_sha256']
    assert model['base_cnf_sha256']==base['cnf_sha256']==inventory['original_CNF_sha256']==row['original_CNF_sha256']
    assert model['domain_record_sha256']==base['domain_record_sha256']==inventory['domain_record_sha256']==row['domain_record_sha256']
    masks=row['column_masks35']
    core=row['core_adjacency_rows']
    assert len(core)==35 and len(masks)==len(set(masks))==1214
    assert masks==inventory['column_masks35'] and row['columns']==inventory['columns']
    assert all(not (core[i] >> i&1) and all((core[i] >> j&1)==(core[j] >> i&1) for j in range(35)) for i in range(35))
    target=[[2-(mask >> i&1)-(core[i]&mask).bit_count() for i in range(35)]+[14-mask.bit_count()] for mask in masks]
    assert target==row['row_targets36'] and all(min(t)>=0 for t in target)
    zeros=[sum(1 << i for i,q in enumerate(t[:35]) if q==0) for t in target]
    neighbors=[[] for _ in masks]
    for a,b in combinations(range(len(masks)),2):
        if (masks[a]&masks[b]).bit_count()<=1 and not (masks[b]&zeros[a] or masks[a]&zeros[b]):
            neighbors[a].append(b)
            neighbors[b].append(a)
    assert neighbors==row['eligible_neighbor_column_ids']
    assert sum(map(len,neighbors))//2==275578
    gram=[[12*(i==j)+2-(core[i]&core[j]).bit_count()-(core[i] >> j&1) for j in range(35)] for i in range(35)]
    assert gram==row['Gram']==inventory['Gram']
    for witness in inventory['optional_binary_cut_negative_witnesses']:
        vector=witness['negative_vector']
        assert len(vector)==35 and all(type(v) is int for v in vector)
        value=sum(vector[i]*gram[i][j]*vector[j] for i in range(35) for j in range(35))
        value-=sum(sum(vector[i] for i in range(35) if masks[c] >> i&1)**2 for c in witness['columns'])
        assert value==witness['negative_value']<0
    no_goods=[[-a-1,-b-1] for cut in inventory['optional_binary_cuts'] for a,b in [cut['support']]]
    assert len(no_goods)==30 and no_goods==model['no_good_primary_clauses']
    assert sha(canonical(cuts))==model['complete_ordered_cut_list_sha256']
    old_top=107207
    next_clause=218863+30
    empty=[]
    for i,(cut,encoding) in enumerate(zip(cuts,model['cut_encodings'])):
        a=cut['target_column']
        vector=cut['integer_vector']
        assert len(vector)==36 and all(type(v) is int for v in vector)
        demand=sum(v*t for v,t in zip(vector,target[a]))
        assert demand==cut['positive_demand']>0
        products=[(b,vector[-1]+sum(vector[j] for j in range(35) if masks[b] >> j&1)) for b in neighbors[a]]
        positive=[[b,w] for b,w in products if w>0]
        assert positive==cut['positive_terms']
        assert encoding['cut_index']==i and encoding['target_column']==a and encoding['target']==a+1
        assert encoding['exact_integer_cut_sha256']==sha(canonical(cut))
        capped=[(b+1,min(w,demand)) for b,w in positive]
        divisor=gcd(*(w for _,w in capped)) if capped else 1
        normalized=sorted([[v,w//divisor] for v,w in capped],key=lambda pair:(-pair[1],pair[0]))
        assert normalized==encoding['normalized_terms']
        assert encoding['normalized_demand']==(demand+divisor-1)//divisor
        assert encoding['capped_weight_gcd']==divisor
        assert encoding['initial_top']==old_top and encoding['final_top']>=old_top
        assert encoding['auxiliary_variables']==encoding['final_top']-old_top
        assert encoding['clause_start_zero_based']==next_clause
        old_top=encoding['final_top']
        next_clause+=encoding['clauses']
        if not positive:
            assert encoding['root_predicate'] is False
            assert encoding['clauses']==1 and encoding['auxiliary_variables']==0
            assert encoding['added_clause_body_sha256']==sha(f'-{a+1} 0\n'.encode())
            empty.append([i,a,a+1,demand])
    assert empty==[[34,1080,1081,2],[35,1081,1082,2]]
    assert old_top==model['formula']['variables']==134852
    assert next_clause==model['formula']['clauses']==261071
    raw=Path(model['cnf']).read_bytes()
    assert sha(raw)==model['cnf_sha256'] and len(raw)==model['cnf_bytes']
    header,body=raw.split(b'\n',1)
    assert header==b'p cnf 134852 261071'
    lines=body.splitlines(keepends=True)
    assert len(lines)==261071
    original_body=b''.join(lines[:218863])
    assert sha(b'p cnf 107207 218863\n'+original_body)==base['cnf_sha256']
    assert sha(original_body)==model['formula']['unchanged_original_clause_body_sha256']
    expected_conflicts=b''.join((' '.join(map(str,clause))+' 0\n').encode() for clause in no_goods)
    assert b''.join(lines[218863:218893])==expected_conflicts
    for cut,encoding in zip(cuts,model['cut_encodings']):
        start=encoding['clause_start_zero_based']
        block=lines[start:start+encoding['clauses']]
        assert sha(b''.join(block))==encoding['added_clause_body_sha256']
        primaries={cut['target_column']+1}|{b+1 for b,w in cut['positive_terms']}
        for line in block:
            literals=list(map(int,line.split()))
            assert literals[-1]==0
            assert all(abs(v) in primaries or encoding['initial_top']<abs(v)<=encoding['final_top'] for v in literals[:-1])
    return {'status':'PASS: independent read-only case4 overlay source review and integer/existing-CNF audit',
        'audit_source_sha256':sha(Path(__file__).read_bytes()),
        'bindings':{name:{'path':path,'sha256':expected} for name,(path,expected) in BOUND.items()},
        'actual_complete_CNF_sha256':model['cnf_sha256'],'original_CNF_recovered_from_prefix_sha256':base['cnf_sha256'],
        'independently_recomputed_row_targets':1214,'independently_recomputed_eligible_edges':275578,
        'exact_negative_Gram_vectors_replayed':30,'exact_integer_row_potentials_replayed':60,
        'all_capped_gcd_thresholds_recomputed':True,'all_appended_block_hashes_checked':True,
        'all_new_variable_intervals_disjoint_and_above_original':True,'empty_support_units':empty,
        'source_math_review':{
            'necessity':'For every actual completion, v dot row_target times x_a is sum_b (v dot (h_b,1))*y_ab, bounded above by sum_b max(v dot (h_b,1),0)*x_b.',
            'original_formula':'The complete original clause body and all 30 certified conflict clauses are retained; no fixed incidence or graph automorphism condition is added.',
            'threshold_semantics':'Positive-weight capping and ceiling after gcd preserve Boolean thresholds. Forward suffix predicates are existentially exact, with fresh IDs for each cut and a guard on the source selector.',
            'resources':'Exhausting a preparation limit refuses the complete overlay instead of adding an arbitrary constraint.',
            'SAT_path':'Original incidence inspector plus every uncapped integer inequality and Gram conflict; no exterior graph claim.',
            'UNSAT_path':'Full cold formula reconstruction, exact row potentials, retained input inclusion and an independent DRAT verification are required.',
            'scope':'Only indexed 35-core case4 and its separately verified relabelings; cuts are necessities of actual completions, not asserted consequences of the old incidence CNF alone.'},
        'subject_modules_imported':False,'CNF_rebuilt':False,'solver_called':False,
        'DRAT_run_by_this_audit':False,'new_feasibility_or_exclusion_claim':False,
        'seconds':time.monotonic()-started}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    assert not args.output.exists()
    result=run()
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))
    print('output_sha256',sha(args.output.read_bytes()))
