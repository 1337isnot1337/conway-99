"""Exact principal-projector scan of the existing induced-type catalogue.

For a putative srg(99,14,1,2), both 27I-9A+J and 44I+11A-2J
are positive semidefinite. Every induced adjacency matrix inherits this
condition. A real symmetric integer matrix is PSD exactly when every
coefficient of det(tI+M) is nonnegative. Integer characteristic
polynomials make this a finite exact test, without numerical tolerances.
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations
import json
from pathlib import Path
import pickle
import time

from flint import fmpz_mat


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def polynomial(matrix):
    """Return the ascending integer coefficients of det(tI+M)."""
    if not matrix:
        return [1]
    return [int(x) for x in (-fmpz_mat(matrix)).charpoly()]


def projectors(rows):
    n = len(rows)
    return (
        [[27*(i == j)-9*((rows[i] >> j) & 1)+1 for j in range(n)]
         for i in range(n)],
        [[44*(i == j)+11*((rows[i] >> j) & 1)-2 for j in range(n)]
         for i in range(n)],
    )


def nullity(coefficients):
    return next(i for i, x in enumerate(coefficients) if x)


def induced_rows(rows, selected):
    return [sum(1 << j for j, old in enumerate(selected) if rows[i] >> old & 1)
            for i in selected]


def is_nine_rook(rows):
    return (len(rows) == 9 and all(row.bit_count() == 4 for row in rows)
            and all((rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1) == 2
                    for i, j in combinations(range(9), 2)))


def controls():
    assert polynomial([[1, 2], [2, 1]]) == [-3, 2, 1]
    assert polynomial([[1, 1], [1, 1]]) == [0, 2, 1]
    assert polynomial([[2, 1], [1, 2]]) == [3, 4, 1]
    rook = [sum(1 << j for j in range(9) if i != j
                and (i//3 == j//3 or i % 3 == j % 3)) for i in range(9)]
    for mask in range(1 << 9):
        selected = [i for i in range(9) if mask >> i & 1]
        rows = induced_rows(rook, selected)
        for matrix in projectors(rows):
            assert all(x >= 0 for x in polynomial(matrix))
    full = [polynomial(matrix) for matrix in projectors(rook)]
    assert [nullity(p) for p in full] == [1, 0]
    return {'known_matrix_controls': 3, 'rook_induced_subsets': 512,
            'rook_projector_polynomials': full}


def scan(data):
    graphs, levels, automorphisms, _ = data
    assert len(graphs) == 48965 and len(levels) == 11
    assert [len(level) for level in levels] == [1, 1, 2, 4, 9, 21, 62, 208, 916, 5311, 42430]
    stream = hashlib.sha256()
    outcomes, rejected, singular = Counter(), [], []
    for index, rows in enumerate(graphs):
        n = len(rows)
        assert all(not (rows[i] >> i & 1) for i in range(n))
        assert all(bool(rows[i] >> j & 1) == bool(rows[j] >> i & 1)
                   for i, j in combinations(range(n), 2))
        polys = [polynomial(matrix) for matrix in projectors(rows)]
        bad = [j for j, p in enumerate(polys) if any(x < 0 for x in p)]
        kernels = [nullity(p) for p in polys]
        stream.update((json.dumps([index, polys], separators=(',', ':'))+'\n').encode())
        outcomes[(n, 'excluded' if bad else 'PSD', *kernels)] += 1
        if bad or any(kernels):
            record = {'catalogue_type': index, 'order': n, 'rows': list(rows),
                      'automorphisms': automorphisms[index],
                      'projector_polynomials': polys, 'nullities': kernels}
            if bad:
                record['indefinite_projectors'] = bad
                rejected.append(record)
            else:
                singular.append(record)
    assert len(rejected) == 1 and len(singular) == 2
    excluded = rejected[0]
    rows = excluded['rows']
    isolated = [i for i, row in enumerate(rows) if not row]
    assert len(rows) == 10 and len(isolated) == 1
    assert is_nine_rook(induced_rows(rows, [i for i in range(10) if i != isolated[0]]))
    vector = [-1 if i == isolated[0] else 2 for i in range(10)]
    matrix = projectors(rows)[0]
    norm = sum(vector[i]*matrix[i][j]*vector[j] for i in range(10) for j in range(10))
    assert norm == -8
    excluded.update(identified_graph='R9 plus one isolated vertex',
                    negative_integer_vector=vector, negative_value=norm)
    assert is_nine_rook(singular[0]['rows'])
    rows = singular[1]['rows']
    pendant = [i for i, row in enumerate(rows) if row.bit_count() == 1]
    assert len(rows) == 10 and len(pendant) == 1
    assert is_nine_rook(induced_rows(rows, [i for i in range(10) if i != pendant[0]]))
    singular[0]['identified_graph'] = 'R9'
    singular[1]['identified_graph'] = 'R9 plus one pendant vertex'
    return {
        'status': 'exact principal-projector catalogue scan completed',
        'catalogue_types': len(graphs), 'maximum_order': 10,
        'all_polynomials_sha256': stream.hexdigest(),
        'distribution': [{'order': n, 'status': status, 'nullities': [a, b], 'types': count}
                         for (n, status, a, b), count in sorted(outcomes.items())],
        'excluded_count': len(rejected), 'excluded_types': rejected,
        'singular_PSD_count': len(singular), 'singular_PSD_types': singular,
        'new_forced_zeros_when_grid_count_is_zero': 0,
        'scope': 'Necessary local projectors only; no complete graph or global contradiction.',
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    started = time.monotonic()
    control = controls()
    if args.catalogue:
        with args.catalogue.open('rb') as stream:
            data = pickle.load(stream)
    else:
        from subgraph_counts import build
        data = build(10)
    result = scan(data)
    result.update(source_sha256=digest(Path(__file__)), controls=control,
                  elapsed_seconds=time.monotonic()-started)
    if args.catalogue:
        result['catalogue_cache_sha256'] = digest(args.catalogue)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items()
                      if k not in ('excluded_types', 'singular_PSD_types')}, indent=2), flush=True)
