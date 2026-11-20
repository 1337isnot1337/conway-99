"""Exact query and certificate replay for the two conditioned triangle blocks.

The model is frozen and complete for its two stated four-roots. A query
performs only Python-integer contraction and exact characteristic polynomials.
Any negative direction is converted to an exact induced-count inequality.
"""
import argparse
from collections import Counter
import gzip
import hashlib
import json
from math import gcd, isqrt
from pathlib import Path
import time
from flint import fmpz_mat
import triangle_incidence_projector_moments as helper

BINDINGS={
 'helper_source':'1e7a8b7380314d6dfd8ff05954a13662bc011378f5759ad675ec1bc281fa19e9',
 'builder_source':'7fb335261db4c828bfc477c2525bc7bc098eac5ce7dab6941892256b8a48886c',
 'preparation':'a01a4e845fcff7a4a2c0edbe9542248f33205640f385463e853821353e8bc65a',
 'model_gzip':'8f398368e80ff36cba74969c8526b660c21155476b7d3cd58e0f0b7c81aeb9a0',
 'model_raw':'8bd186531a14656a2ecf06857742532b26ff53fa3fb4f75cc2b6bd8322e51ef6',
 'point':'0b78eb2cfc0966f66d72b083f71315e4a079e4b25f59f276c58dd93d189b49df',
}

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def read_inputs(directory,point_path):
    assert digest(Path(helper.__file__).read_bytes())==BINDINGS['helper_source']
    builder=Path(__file__).with_name('triangle_projector_core_triangle_conditioning.py')
    assert digest(builder.read_bytes())==BINDINGS['builder_source']
    raw=(directory/'preparation.json').read_bytes()
    assert digest(raw)==BINDINGS['preparation']
    preparation=json.loads(raw)
    assert preparation['source_sha256']==BINDINGS['builder_source']
    compressed=(directory/'model.json.gz').read_bytes()
    assert digest(compressed)==BINDINGS['model_gzip']==preparation['model_gzip_sha256']
    raw=gzip.decompress(compressed)
    assert digest(raw)==BINDINGS['model_raw']==preparation['model_raw_sha256']
    specification=json.loads(raw)
    assert [b['root_type'] for b in specification['blocks']]==[14,15]
    assert [b['order'] for b in specification['blocks']]==[41,34]
    assert sum(len(b['terms']) for b in specification['blocks'])==11211
    raw=point_path.read_bytes()
    assert digest(raw)==BINDINGS['point']
    counts=json.loads(raw)['induced_counts']
    assert len(counts)==48965 and all(type(c) is int and c>=0 for c in counts)
    return specification,counts

def location(entry):
    i=(isqrt(8*entry+1)-1)//2
    j=entry-i*(i+1)//2
    assert 0<=j<=i
    return i,j

def contract(block,counts):
    n=block['order']
    matrix=[[0]*n for _ in range(n)]
    seen=set()
    for entry,t,c in block['terms']:
        assert all(type(v) is int for v in (entry,t,c)) and c
        assert 0<=entry<n*(n+1)//2 and 0<=t<len(counts) and (entry,t) not in seen
        seen.add((entry,t))
        i,j=location(entry)
        matrix[i][j]+=c*counts[t]
        if i!=j:matrix[j][i]+=c*counts[t]
    return matrix

def characteristic(matrix):
    n=len(matrix)
    minus=list(map(int,fmpz_mat(matrix).charpoly()))
    plus=[(-1 if (n+i)%2 else 1)*v for i,v in enumerate(minus)]
    assert len(plus)==n+1 and plus[-1]==1
    return plus

def vector_form(block,vector,counts):
    form=Counter()
    for entry,t,c in block['terms']:
        i,j=location(entry)
        form[t]+=c*vector[i]*vector[j]*(1 if i==j else 2)
    form={t:c for t,c in form.items() if c}
    value=sum(c*counts[t] for t,c in form.items())
    divisor=0
    for c in form.values():divisor=gcd(divisor,abs(c))
    assert divisor>0 and value%divisor==0
    return [[t,str(c//divisor)] for t,c in sorted(form.items())],str(value//divisor),value

def controls():
    examples=[([[1,1],[1,1]],True),([[1,2],[2,1]],False),([[0,1],[1,0]],False)]
    report=[]
    for matrix,expected in examples:
        polynomial=characteristic(matrix)
        assert all(c>=0 for c in polynomial)==expected
        block={'order':2,'terms':[[0,0,matrix[0][0]],[1,1,matrix[1][0]],[2,2,matrix[1][1]]]}
        block['terms']=[x for x in block['terms'] if x[2]]
        assert contract(block,[1,1,1])==matrix
        item={'matrix':matrix,'PSD':expected,'charpoly':polynomial}
        if not expected:
            v,value=helper.exact_negative_vector(matrix,time.monotonic()+5)
            form,primitive,reconstructed=vector_form(block,v,[1,1,1])
            assert value==reconstructed<0 and int(primitive)<0
            item.update(integer_vector=v,value=value,primitive_form=form)
        report.append(item)
    return {'status':'PASS_EXACT_CONTRACTION_PSD_AND_NEGATIVE_FORM_CONTROLS','examples':report,'count_point_loaded':False,'optimizer_called':False}

def query(args):
    assert 0<args.seconds<=30 and not args.output.exists()
    start=time.monotonic()
    deadline=start+args.seconds
    specification,counts=read_inputs(args.preparation,args.point)
    terminal={'status':'INCOMPLETE','source_sha256':digest(Path(__file__).read_bytes()),
              'bindings':BINDINGS,'blocks':[],'complete_two_block_coverage':False,
              'optimizer_called':False,'graph_existence_resolved':False}
    try:
        for domain,block in zip(specification['domains'],specification['blocks']):
            helper.check_time(deadline)
            matrix=contract(block,counts)
            fixed=domain['fixed_triangle_class']
            assert all(matrix[fixed][j]==0 for j in range(len(matrix)))
            polynomial=characteristic(matrix)
            positive=all(c>=0 for c in polynomial)
            record={'root_type':block['root_type'],'order':len(matrix),
                    'matrix':[[str(x) for x in row] for row in matrix],
                    'det_tI_plus_matrix_coefficients':list(map(str,polynomial)),
                    'exact_positive_semidefinite':positive,
                    'fixed_core_triangle_row_zero':True}
            if not positive:
                vector,value=helper.exact_negative_vector(matrix,deadline)
                form,primitive,reconstructed=vector_form(block,vector,counts)
                assert reconstructed==value<0
                record.update(integer_negative_vector=list(map(str,vector)),
                              quadratic_value=str(value),
                              primitive_induced_count_inequality=form,
                              primitive_value=primitive)
            terminal['blocks'].append(record)
        helper.check_time(deadline)
        terminal['complete_two_block_coverage']=True
        terminal['status']='EXACT_BOTH_CONDITIONED_TRIANGLE_BLOCKS_PSD' if all(b['exact_positive_semidefinite'] for b in terminal['blocks']) else 'EXACT_CONDITIONED_TRIANGLE_SEPARATOR'
    except Exception as error:
        terminal.update(status='INCOMPLETE_NO_WHOLE_MODEL_CONCLUSION',error_type=type(error).__name__,error_message=str(error))
        raise
    finally:
        terminal['seconds']=time.monotonic()-start
        args.output.write_text(json.dumps(terminal,indent=2)+'\n')
        print(json.dumps({k:v for k,v in terminal.items() if k!='blocks'},indent=2),flush=True)

def replay(args):
    assert not args.output.exists()
    start=time.monotonic()
    specification,counts=read_inputs(args.preparation,args.point)
    raw=args.result.read_bytes()
    result=json.loads(raw)
    assert result['source_sha256']==digest(Path(__file__).read_bytes()) and result['bindings']==BINDINGS
    assert result['complete_two_block_coverage'] and len(result['blocks'])==2
    report=[]
    for domain,block,saved in zip(specification['domains'],specification['blocks'],result['blocks']):
        assert saved['root_type']==block['root_type'] and saved['order']==block['order']
        matrix=contract(block,counts)
        assert matrix==[[int(x) for x in row] for row in saved['matrix']]
        assert all(matrix[domain['fixed_triangle_class']][j]==0 for j in range(len(matrix)))
        polynomial=characteristic(matrix)
        assert polynomial==list(map(int,saved['det_tI_plus_matrix_coefficients']))
        positive=all(c>=0 for c in polynomial)
        assert positive==saved['exact_positive_semidefinite']
        item={'root_type':block['root_type'],'order':block['order'],'exact_positive_semidefinite':positive}
        if positive:
            item['nullity']=next(i for i,c in enumerate(polynomial) if c)
        else:
            vector=list(map(int,saved['integer_negative_vector']))
            assert len(vector)==len(matrix)
            value=sum(vector[i]*matrix[i][j]*vector[j] for i in range(len(matrix)) for j in range(len(matrix)))
            form,primitive,reconstructed=vector_form(block,vector,counts)
            assert value==reconstructed==int(saved['quadratic_value'])<0
            assert form==saved['primitive_induced_count_inequality'] and primitive==saved['primitive_value']
            item['primitive_value']=primitive
        report.append(item)
    expected='EXACT_BOTH_CONDITIONED_TRIANGLE_BLOCKS_PSD' if all(b['exact_positive_semidefinite'] for b in report) else 'EXACT_CONDITIONED_TRIANGLE_SEPARATOR'
    assert result['status']==expected
    replay={'status':'PASS_COLD_EXACT_CONDITIONED_QUERY_REPLAY','source_sha256':digest(Path(__file__).read_bytes()),
            'result_sha256':digest(raw),'bindings':BINDINGS,'blocks':report,
            'complete_two_block_coverage':True,'tensor_generation_repeated':False,'optimizer_called':False,
            'seconds':time.monotonic()-start}
    args.output.write_text(json.dumps(replay,indent=2)+'\n')
    print(json.dumps(replay,indent=2))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['controls','query','replay'])
    parser.add_argument('--preparation',type=Path)
    parser.add_argument('--point',type=Path)
    parser.add_argument('--output',type=Path)
    parser.add_argument('--result',type=Path)
    parser.add_argument('--seconds',type=float,default=30)
    args=parser.parse_args()
    if args.mode=='controls':
        assert digest(Path(helper.__file__).read_bytes())==BINDINGS['helper_source']
        print(json.dumps(controls(),indent=2))
    elif args.mode=='query':
        assert args.preparation and args.point and args.output
        query(args)
    else:
        assert args.preparation and args.point and args.output and args.result
        replay(args)

if __name__=='__main__':
    main()
