"""Evaluate the exact C4 symmetry blocks at a separate integer count point."""

import argparse
import gzip
from itertools import combinations
import json
from pathlib import Path
import pickle
import time

import sympy as sp

import grid_free_order10_higher_flags_small_scan as exact
import grid_free_order10_r8s1_scan as matrices
import grid_free_order10_scaled as files


STRUCTURE_SHA = '07c0e618bb3b3b530bf2a52c40f9baaba62935ffca73442c64d679a54d495fea'
CACHE_SHA = '7707ae4036a0f5889a6356e6d658e742aa969d7385652cb2635418607c6aa943'


def evaluate(structure,witness,catalogue,cache,output):
    started = time.monotonic()
    assert files.digest(structure) == STRUCTURE_SHA and files.digest(cache) == CACHE_SHA
    saved = json.loads(structure.read_text())
    assert files.digest(catalogue) == saved['catalogue_sha256']
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    point = json.loads(witness.read_text())
    assert point['original_equations_checked'] == 180445
    assert point['negative_induced_rows'] == point['nonintegral_induced_rows'] == 0
    induced = point['induced_counts']
    assert all(type(value) is int and value >= 0 for value in induced)
    payload = pickle.loads(gzip.decompress(cache.read_bytes()))
    _,flags,tensor = next(block for block in payload['blocks'] if block[0] == 16)
    embeddings = [value*aut for value,aut in zip(induced,data[2])]
    M = sp.Matrix(matrices.FullScanner.matrix(tensor,len(flags),embeddings).tolist())
    R = sp.zeros(15)
    for i,j in enumerate(saved['rotation']['flag_action']):
        R[j,i] = 1
    bases,labels = [],[]
    for block in saved['one_dimensional_isotypic_blocks']:
        columns = block['basis_columns']
        if columns:
            bases.append(sp.Matrix.hstack(*(sp.Matrix(column) for column in columns)))
            labels.append([block['rotation_character'],block['reflection_character']])
    B = sp.Matrix.hstack(*(sp.Matrix(column) for column in saved['multiplicity_basis_columns']))
    K = B.T*M*B
    assert (R*B).T*M*(R*B) == K and B.T*M*(R*B) == sp.zeros(3)
    W = sp.Matrix.hstack(*bases,B,R*B)
    assert int(W.det()) == saved['full_integer_change_of_basis_determinant']
    assert W.T*M*W == sp.diag(*(base.T*M*base for base in bases),K,K)
    blocks = []
    for label,base in zip(labels+['two_dimensional_multiplicity'],bases+[B]):
        matrix = [[int(value) for value in row] for row in (base.T*M*base).tolist()]
        minors = []
        for size in range(1,len(matrix)+1):
            for indices in combinations(range(len(matrix)),size):
                value = exact.determinant([[matrix[i][j] for j in indices] for i in indices])
                minors.append({'indices':list(indices),'determinant':value})
        blocks.append({'character':label,'order':len(matrix),'matrix':matrix,
                       'rank':int(sp.Matrix(matrix).rank()),'principal_minors':minors,
                       'positive_semidefinite_exactly':all(item['determinant'] >= 0 for item in minors)})
    cut = saved['variance_cut']
    value = sum(coefficient*induced[index] for index,coefficient in cut['primitive_induced_count_form'])
    assert value*cut['positive_form_gcd'] == K[0,0]
    for form in saved['multiplicity_entry_forms']:
        i,j = form['entry']
        scalar = sum(c*induced[index] for index,c in form['primitive_induced_count_form'])
        assert scalar*form['positive_gcd'] == K[i,j]
    positive = all(block['positive_semidefinite_exactly'] for block in blocks)
    result = {'status':'full C4 block is exactly PSD at the new count point' if positive else
                      'new count point fails an exact C4 symmetry-block principal minor',
              'source_sha256':files.digest(Path(__file__)),'structure_sha256':STRUCTURE_SHA,
              'cache_sha256':CACHE_SHA,'witness_path':str(witness),'witness_sha256':files.digest(witness),
              'catalogue_sha256':saved['catalogue_sha256'],
              'root_type':16,'blocks':blocks,'full_C4_positive_semidefinite_exactly':positive,
              'full_C4_rank':sum(block['rank'] for block in blocks[:-1])+2*blocks[-1]['rank'],
              'variance_primitive_value':value,'variance_quadratic_value':int(K[0,0]),
              'principal_minors_checked':sum(len(block['principal_minors']) for block in blocks),
              'congruence_checked_exactly':True,'eigensystems_computed':False,
              'dense_reduction_loaded':False,'optimizer_called':False,
              'scope':'the one fifteen-flag C4 block at this integer point, not all2405 blocks',
              'seconds':time.monotonic()-started}
    files.save(output,result)
    print(json.dumps({key:value for key,value in result.items() if key != 'blocks'},indent=2),flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('structure','witness','catalogue','cache','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    args = parser.parse_args()
    evaluate(args.structure,args.witness,args.catalogue,args.cache,args.output)
