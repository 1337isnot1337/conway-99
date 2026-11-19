"""Exact root-symmetry decomposition of the fifteen-flag C4 block.

This separate calculation leaves every earlier cut and cache unchanged.
It verifies tensor coefficient invariance under all eight root symmetries,
constructs rational representation projectors, and independently rebuilds
a two-flag variance cut. No dense core reduction or optimizer is used.
"""

from collections import Counter
from functools import reduce
import gzip
from itertools import permutations
import json
from math import gcd
from pathlib import Path
import pickle
import time
import argparse

import sympy as sp

import grid_free_order10_higher_flags_domains as domains
import grid_free_order10_r6s2_independent_audit as oracle
import grid_free_order10_r8s1_scan as matrices
import grid_free_order10_scaled as files


CACHE_SHA = '7707ae4036a0f5889a6356e6d658e742aa969d7385652cb2635418607c6aa943'
SCAN_SHA = 'c70c9efc5588e0c15b9899770a137b37937f2037456f02e6b58077bb6165bcab'
WITNESS_SHA = '190c779b4a8758d9df90ccc13a54538d8e120710e224b9150dd3aa4b591bd53d'
DOMAIN_SOURCE_SHA = 'a2fb1b18940423cdd6d36bce91bac54cbe3eecc8622c2418642b8a9559c8c6f0'
ORACLE_SHA = '46bbbf5521383fc14925644e1dcb82ebeca99094b5726b8f23e3d774aa6f643f'


def stored_row(tensor,i,j):
    a,b = max(i,j),min(i,j)
    row = a*(a+1)//2+b
    return {int(tensor.indices[k]):int(tensor.data[k])
            for k in range(tensor.indptr[row],tensor.indptr[row+1])}


def integer_basis(matrix):
    columns = []
    for column in matrix.columnspace():
        values = [int(value) for value in column]
        divisor = reduce(gcd,[abs(value) for value in values],0)
        columns.append(sp.Matrix([value//divisor for value in values]))
    return sp.Matrix.hstack(*columns) if columns else sp.zeros(matrix.rows,0)


def primitive_form(tensor,left,right,aut):
    weights = Counter()
    for i in range(len(left)):
        for j in range(i+1):
            coefficient = left[i]*right[j] if i == j else left[i]*right[j]+left[j]*right[i]
            if coefficient:
                for index,multiplicity in stored_row(tensor,i,j).items():
                    weights[index] += int(coefficient)*multiplicity*aut[index]
    terms = [[index,value] for index,value in sorted(weights.items()) if value]
    divisor = reduce(gcd,[abs(value) for _,value in terms],0)
    assert divisor > 0
    return [[index,value//divisor] for index,value in terms],divisor


def main(scan_path,output):
    started = time.monotonic()
    assert files.digest(scan_path) == SCAN_SHA
    assert files.digest(Path(domains.__file__)) == DOMAIN_SOURCE_SHA
    assert files.digest(Path(oracle.__file__)) == ORACLE_SHA
    saved = json.loads(scan_path.read_text())
    cache,witness,catalogue = (Path(saved[key]) for key in
                              ('generated_cache_path','witness_path','catalogue_path'))
    assert files.digest(cache) == CACHE_SHA
    assert files.digest(witness) == WITNESS_SHA
    assert files.digest(catalogue) == saved['catalogue_sha256']
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    payload = pickle.loads(gzip.decompress(cache.read_bytes()))
    root,flags,tensor = next(block for block in payload['blocks'] if block[0] == 16)
    root_rows = tuple(data[0][root])
    lookup = {tuple(flag['rows']):i for i,flag in enumerate(flags)}
    assert len(flags) == 15 and root_rows == (12,12,3,3)
    group = []
    for order in permutations(range(4)):
        if domains.relabel(root_rows,order) != root_rows:
            continue
        action = []
        for flag in flags:
            graph = domains.relabel(flag['rows'],tuple(order)+tuple(range(4,len(flag['rows']))))
            action.append(lookup[domains.normal(graph,4)])
        assert sorted(action) == list(range(15))
        permutation = sp.zeros(15)
        for i,j in enumerate(action):
            permutation[j,i] = 1
        group.append((order,action,permutation))
    assert len(group) == 8
    coefficient_checks = 0
    for _,action,_ in group:
        for i in range(15):
            for j in range(i+1):
                assert stored_row(tensor,i,j) == stored_row(tensor,action[i],action[j])
                coefficient_checks += 1
    identity = sp.eye(15)
    rotation_order,rotation_action,R = next(g for g in group if g[2]**4 == identity and g[2]**2 != identity)
    reflection_order,reflection_action,S = next(g for g in group if g[2]**2 == identity and
                                               g[2] != identity and g[2] != R**2 and g[2]*R*g[2] == R.T)
    generated = {tuple((S**a*R**b)) for a in range(2) for b in range(4)}
    assert generated == {tuple(P) for _,_,P in group}
    point = json.loads(witness.read_text())
    induced = point['induced_counts']
    embeddings = [value*aut for value,aut in zip(induced,data[2])]
    M = sp.Matrix(matrices.FullScanner.matrix(tensor,15,embeddings).tolist())
    assert all(P.T*M*P == M for _,_,P in group)
    one_dimensional, bases, total_projection = [],[],sp.zeros(15)
    for a in (1,-1):
        for b in (1,-1):
            N = (identity+a*R+R**2+a*R**3)*(identity+b*S)
            Q = N/8
            assert Q == Q.T and Q*Q == Q
            B = integer_basis(N)
            assert B.cols == Q.rank()
            if B.cols:
                bases.append(B)
            total_projection += Q
            one_dimensional.append({'rotation_character':a,'reflection_character':b,
                                    'multiplicity':B.cols,'basis_columns':[[int(v) for v in B[:,j]] for j in range(B.cols)],
                                    'matrix_at_witness':[[int(value) for value in row] for row in (B.T*M*B).tolist()]})
    Q2 = (identity-R**2)/2
    assert Q2 == Q2.T and Q2*Q2 == Q2
    assert total_projection+Q2 == identity
    B = integer_basis((identity-R**2)*(identity+S))
    assert B.cols == 3 and Q2.rank() == 6
    assert S*B == B and S*R*B == -R*B
    K = B.T*M*B
    assert (R*B).T*M*(R*B) == K and B.T*M*(R*B) == sp.zeros(3)
    W = sp.Matrix.hstack(*bases,B,R*B)
    assert W.shape == (15,15) and W.det() != 0
    expected = sp.diag(*(base.T*M*base for base in bases),K,K)
    assert W.T*M*W == expected
    old_vector = sp.Matrix(saved['negative_blocks'][0]['integer_vector'])
    assert Q2*old_vector == old_vector
    small_forms = []
    for i in range(3):
        for j in range(i+1):
            terms,divisor = primitive_form(tensor,list(B[:,i]),list(B[:,j]),data[2])
            value = sum(c*induced[index] for index,c in terms)
            assert value*divisor == K[i,j]
            small_forms.append({'entry':[i,j],'primitive_induced_count_form':terms,
                                'positive_gcd':divisor,'primitive_value_at_witness':int(value)})
    vector = list(B[:,0])
    assert vector == [int(i == 3)-int(i == 4) for i in range(15)]
    assert int((B[:,0].T*M*B[:,0])[0]) == -11200
    # Rebuild the three products of the two-flag variance directly.
    ids = {oracle.canonical(tuple(rows)):i for i,rows in enumerate(data[0])}
    fresh_weights = Counter()
    fresh_entries = []
    for i,j,weight in ((3,3,1),(4,3,-2),(4,4,1)):
        terms,by_q = oracle.direct_product(4,tuple(flags[i]['rows']),tuple(flags[j]['rows']),ids)
        assert terms == stored_row(tensor,i,j)
        for index,multiplicity in terms.items():
            fresh_weights[index] += weight*multiplicity*data[2][index]
        fresh_entries.append({'flags':[i,j],'labelled_embedding_terms':[[k,v] for k,v in sorted(terms.items())],
                              'accepted_completions_by_overlap':dict(sorted(by_q.items()))})
    terms = [[index,value] for index,value in sorted(fresh_weights.items()) if value]
    divisor = reduce(gcd,[abs(value) for _,value in terms],0)
    primitive = [[index,value//divisor] for index,value in terms]
    assert primitive == small_forms[0]['primitive_induced_count_form']
    assert divisor == small_forms[0]['positive_gcd']
    value = sum(c*induced[index] for index,c in primitive)
    assert value*divisor == -11200
    unused = set(range(15));orbits = []
    while unused:
        i = min(unused)
        orbit = sorted({action[i] for _,action,_ in group})
        orbits.append(orbit)
        unused -= set(orbit)
    result = {'status':'exact C4 symmetry decomposition and independently reconstructed variance cut',
              'source_sha256':files.digest(Path(__file__)),'scan_sha256':SCAN_SHA,'cache_sha256':CACHE_SHA,
              'witness_sha256':WITNESS_SHA,'catalogue_sha256':saved['catalogue_sha256'],
              'domain_source_sha256':DOMAIN_SOURCE_SHA,'independent_product_oracle_sha256':ORACLE_SHA,
              'root_type':16,'root_rows':list(root_rows),'flag_orbits':orbits,
              'root_automorphisms':[{'root_order':list(order),'flag_action':action} for order,action,_ in group],
              'exact_tensor_invariance_checks':coefficient_checks,
              'rotation':{'root_order':list(rotation_order),'flag_action':rotation_action},
              'reflection':{'root_order':list(reflection_order),'flag_action':reflection_action},
              'one_dimensional_isotypic_blocks':one_dimensional,
              'two_dimensional_isotypic_rank':6,'multiplicity_block_order':3,
              'multiplicity_basis_columns':[[int(v) for v in B[:,j]] for j in range(3)],
              'multiplicity_matrix_at_witness':[[int(value) for value in row] for row in K.tolist()],
              'multiplicity_entry_forms':small_forms,
              'full_integer_change_of_basis_determinant':int(W.det()),
              'full_congruence_block_orders':[base.cols for base in bases]+[3,3],
              'old_negative_direction_lies_in_two_dimensional_isotypic_space':True,
              'variance_cut':{'flag_pair':[3,4],'integer_vector':[int(v) for v in vector],
                              'quadratic_value_at_witness':-11200,'positive_form_gcd':divisor,
                              'primitive_induced_count_form':primitive,'primitive_value_at_witness':value,
                              'fresh_product_count':3,'fresh_products':fresh_entries,
                              'universal_reason':'sum over labelled C4 roots of the square of the difference of two labelled flag counts'},
              'dense_reduction_loaded':False,'optimizer_called':False,'eigensystems_computed':False,
              'earlier_sources_or_cuts_modified':False,'seconds':time.monotonic()-started}
    files.save(output,result)
    print(json.dumps({key:value for key,value in result.items() if key not in
          ('root_automorphisms','one_dimensional_isotypic_blocks','multiplicity_entry_forms')},indent=2),flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--scan',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    main(args.scan,args.output)
