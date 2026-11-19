"""Exact r2s4 evaluation from the prepared 16 symbolic product entries.

All principal minors are checked with Python integers. A negative matrix
also receives a rational Schur-complement direction and an exact linear
induced-count cut. No optimizer, eigensystem, or dense reduction is used.
"""

import argparse
from collections import Counter
from fractions import Fraction
from functools import reduce
from itertools import combinations
import json
from math import gcd, lcm
from pathlib import Path
import pickle
import time

import grid_free_order10_higher_flags_products as products
import grid_free_order10_scaled as files


PRODUCT_SOURCE_SHA = '32b39c98538bd5358e64e7e794c9f6464704ea7f1fe9f6f171d9243f4af88a36'


def determinant(matrix):
    if not matrix:
        return 1
    if len(matrix) == 1:
        return matrix[0][0]
    return sum((-1)**j*matrix[0][j]*determinant([row[:j]+row[j+1:] for row in matrix[1:]])
               for j in range(len(matrix)))


def negative_rational(matrix):
    """Return a negative rational direction, or certify PSD recursively."""
    n = len(matrix)
    for i in range(n):
        if matrix[i][i] < 0:
            return [Fraction(int(i == j)) for j in range(n)]
    for i in range(n):
        if matrix[i][i] != 0:
            continue
        for j in range(n):
            if matrix[i][j]:
                entry = matrix[i][j]
                factor = matrix[j][j]//(2*abs(entry))+1
                vector = [Fraction(0)]*n
                vector[i] = -factor if entry > 0 else factor
                vector[j] = 1
                assert sum(vector[a]*matrix[a][b]*vector[b] for a in range(n) for b in range(n)) < 0
                return vector
    positive = next((i for i in range(n) if matrix[i][i] > 0), None)
    if positive is None:
        return None
    rest = [i for i in range(n) if i != positive]
    pivot = matrix[positive][positive]
    schur = [[matrix[a][b]-matrix[a][positive]*matrix[positive][b]/pivot for b in rest] for a in rest]
    lower = negative_rational(schur)
    if lower is None:
        return None
    vector = [Fraction(0)]*n
    for i, value in zip(rest, lower):
        vector[i] = value
    vector[positive] = -sum(matrix[positive][i]*vector[i] for i in rest)/pivot
    assert sum(vector[a]*matrix[a][b]*vector[b] for a in range(n) for b in range(n)) < 0
    return vector


def scan(preparation, witness, output):
    started = time.monotonic()
    assert files.digest(Path(products.__file__)) == PRODUCT_SOURCE_SHA
    prepared = json.loads(preparation.read_text())
    assert prepared['source_sha256'] == PRODUCT_SOURCE_SHA
    catalogue = Path(prepared['catalogue_path'])
    assert files.digest(catalogue) == prepared['catalogue_sha256']
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    point = json.loads(witness.read_text())
    assert point['original_equations_checked'] == 180445
    assert point['negative_induced_rows'] == point['nonintegral_induced_rows'] == 0
    induced = point['induced_counts']
    assert len(induced) == 48965 and all(type(value) is int and value >= 0 for value in induced)
    assert induced[99] == 0
    embeddings = [value*aut for value,aut in zip(induced,data[2])]
    projection = {row['root_type']:row for row in prepared['prism_zero_projection']}
    records, cuts = [], []
    for block in prepared['small_r2s4_symbolic_blocks']:
        root, n = block['root_type'], len(block['flag_rows'])
        matrix = [[0]*n for _ in range(n)]
        assert len(block['entries']) == n*(n+1)//2
        for entry in block['entries']:
            i,j = entry['flag_indices']
            value = sum(coefficient*embeddings[index] for index,coefficient in entry['labelled_embedding_terms'])
            matrix[i][j] = matrix[j][i] = value
        for i in projection[root]['prism_flag_indices']:
            assert not any(matrix[i])
        minors = []
        for size in range(1,n+1):
            for selected in combinations(range(n),size):
                value = determinant([[matrix[i][j] for j in selected] for i in selected])
                minors.append({'indices':list(selected),'determinant':value})
        positive = all(row['determinant'] >= 0 for row in minors)
        rational = negative_rational([[Fraction(value) for value in row] for row in matrix])
        assert positive == (rational is None)
        record = {'root_type':root,'order':n,'matrix':matrix,'principal_minors':minors,
                  'positive_semidefinite_exactly':positive,
                  'prism_rows_checked_exactly_zero':projection[root]['prism_flag_indices']}
        if rational is not None:
            denominator = lcm(*(value.denominator for value in rational))
            vector = [int(value*denominator) for value in rational]
            common = reduce(gcd,[abs(value) for value in vector],0)
            vector = [value//common for value in vector]
            quadratic = sum(vector[i]*matrix[i][j]*vector[j] for i in range(n) for j in range(n))
            assert quadratic < 0
            coefficients = Counter()
            for entry in block['entries']:
                i,j = entry['flag_indices']
                weight = vector[i]*vector[j]*(1 if i == j else 2)
                for index,value in entry['labelled_embedding_terms']:
                    coefficients[index] += weight*value*data[2][index]
            coefficients = {index:value for index,value in coefficients.items() if value}
            divisor = reduce(gcd,[abs(value) for value in coefficients.values()],0)
            terms = [[index,value//divisor] for index,value in sorted(coefficients.items())]
            value = sum(coefficient*induced[index] for index,coefficient in terms)
            assert value*divisor == quadratic < 0
            cut = {'root_type':root,'integer_vector':vector,'integer_quadratic_value':quadratic,
                   'primitive_induced_count_form':terms,'positive_form_gcd':divisor,
                   'exact_primitive_value':value}
            cuts.append(cut)
            record['negative_cut_index'] = len(cuts)-1
        records.append(record)
    assert {record['root_type'] for record in records} == {2,3}
    result = {'status':'both complete r2s4 blocks are exactly PSD at this count point' if not cuts else
                      'exact r2s4 separating inequalities found',
              'source_sha256':files.digest(Path(__file__)),'product_source_sha256':PRODUCT_SOURCE_SHA,
              'preparation_path':str(preparation),'preparation_sha256':files.digest(preparation),
              'witness_path':str(witness),'witness_sha256':files.digest(witness),
              'catalogue_sha256':prepared['catalogue_sha256'],
              'complete_family_roots':[2,3],'blocks':records,'exact_cuts':cuts,
              'principal_minors_checked':sum(len(record['principal_minors']) for record in records),
              'eigensystems_computed':False,'dense_reduction_loaded':False,'optimizer_called':False,
              'original_count_equations_replayed_here':False,
              'PSD_scope':'the two complete r2s4 blocks at the specified exact count witness only',
              'graph_constructed':False,'seconds':time.monotonic()-started}
    files.save(output,result)
    print(json.dumps(result,indent=2),flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--preparation',type=Path,required=True)
    parser.add_argument('--witness',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    scan(args.preparation,args.witness,args.output)
