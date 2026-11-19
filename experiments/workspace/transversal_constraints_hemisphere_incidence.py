"""Exact-signature exterior relaxation for a specified rooted H21.

Input is a K7-edge labeling of H21.  Variables select, fractionally, the
H-neighbor set of every one of the 63 remaining signed outer labels.
All common-neighbor equations within the 36-vertex core are imposed.
Single-column spectral pruning uses exact rational integer arithmetic.
"""

import argparse
from collections import Counter
from itertools import combinations
import json
from pathlib import Path
import time

import networkx as nx
import numpy as np
import scipy.sparse as sparse
from scipy.optimize import linprog
import sympy as sp

from transversal_constraints_hemisphere_spectral import exact_psd


def inverse_integer(M):
    assert exact_psd(M)
    inverse = sp.Matrix(M.tolist()).inv()
    denominator = int(sp.ilcm(*(v.q for v in inverse)))
    numerator = np.array(inverse*denominator, dtype=object)
    numerator = np.array([[int(v) for v in row] for row in numerator], dtype=object)
    assert np.array_equal(np.array(M, dtype=object) @ numerator,
                          denominator*np.eye(len(M), dtype=object))
    return numerator, denominator


def build(labeling, spectral=True):
    G = nx.read_graph6(Path(__file__).with_name('transversal-hemisphere-minimal21.g6'))
    A = nx.to_numpy_array(G, dtype=np.int64)
    B = np.zeros((21, 7), dtype=np.int64)
    for i, anchors in enumerate(labeling):
        B[i, anchors] = 1
    assert np.all(B.sum(axis=1) == 2)
    assert np.all(B.T @ B == np.eye(7, dtype=np.int64)*5+1)
    residual = 2-A-A@A-B@B.T
    assert all(residual[i,j] >= 0 for i,j in combinations(range(21), 2))
    compatibility = nx.from_numpy_array((residual > 0).astype(np.int64))
    compatibility.remove_edges_from(nx.selfloop_edges(compatibility))
    sets = [()] + [tuple(S) for S in nx.enumerate_all_cliques(compatibility)]
    signatures = np.zeros((len(sets), 21), dtype=np.int64)
    for k, S in enumerate(sets):
        signatures[k, list(S)] = 1
    AS = signatures @ A + signatures
    BS = signatures @ B
    if spectral:
        Q = 24*np.eye(21, dtype=np.int64)-8*A-3*B@B.T+2
        P = 60*np.eye(21, dtype=np.int64)+15*A-4*B@B.T-2
        Qnum, Qden = inverse_integer(Q)
        Pnum, Pden = inverse_integer(P)
    # Near indices 2a (u_a), 2a+1 (t_a).
    labels = [w for w in combinations(range(14), 2)
              if w[0]//2 != w[1]//2 and any(v % 2 for v in w)]
    assert len(labels) == 63
    pairs = list(combinations(range(21), 2))
    row_labels = [('label', w) for w in labels]
    row_labels += [('anchor', i, a) for i in range(21) for a in range(14)]
    row_labels += [('pair', i, j) for i,j in pairs]
    b = [1]*63
    AB = A @ B
    b += [int(2-B[i,a//2]-(AB[i,a//2] if a % 2 == 0 else 0))
          for i in range(21) for a in range(14)]
    b += [int(residual[i,j]) for i,j in pairs]
    pair_rows = {pair: 63+294+k for k,pair in enumerate(pairs)}
    row, col, data, variables = [], [], [], []
    domain_sizes = []
    for k, w in enumerate(labels):
        e = np.array([2*a in w for a in range(7)], dtype=np.int64)
        t = np.array([2*a+1 in w for a in range(7)], dtype=np.int64)
        eligible = np.all(BS <= (2-e-t)[None,:], axis=1)
        eligible &= np.all(AS <= (2-B@e)[None,:], axis=1)
        indices = np.flatnonzero(eligible)
        if spectral and len(indices):
            q = np.array(2-8*signatures[indices]-3*(B@e)-(B@t), dtype=object)
            p = np.array(15*signatures[indices]-4*(B@e)+(B@t)-2, dtype=object)
            allowed = np.array([v <= 20*Qden for v in np.sum((q@Qnum)*q, axis=1)])
            allowed &= np.array([v <= 50*Pden for v in np.sum((p@Pnum)*p, axis=1)])
            indices = indices[allowed]
        domain_sizes.append(len(indices))
        for ix in indices:
            S = sets[ix]
            c = len(variables)
            variables.append((k, sum(1 << i for i in S)))
            rows = [k]
            rows += [63+14*i+a for i in S for a in w]
            rows += [pair_rows[pair] for pair in combinations(sorted(S), 2)]
            row += rows
            col += [c]*len(rows)
            data += [1]*len(rows)
    M = sparse.coo_matrix((data, (row, col)), shape=(len(b), len(variables))).tocsr()
    info = {'signatures': len(sets), 'signature_size_histogram': dict(Counter(map(len, sets))),
            'domain_sizes': domain_sizes, 'rows': len(b), 'columns': len(variables),
            'nonzeros': len(data), 'spectral': spectral}
    return M, np.array(b, dtype=np.int64), variables, labels, row_labels, info


def run(labeling_file, seconds=30, spectral=True, output=None):
    saved = json.loads(Path(labeling_file).read_text())
    labeling = saved.get('result', saved)['labels']
    start = time.monotonic()
    A, b, variables, labels, row_labels, info = build(labeling, spectral)
    info['build_seconds'] = time.monotonic()-start
    print(json.dumps({'build': info}), flush=True)
    result = linprog(np.zeros(A.shape[1]), A_eq=A, b_eq=b, bounds=(0, None),
                     method='highs-ipm', options={'time_limit': seconds})
    record = {'status': int(result.status), 'message': result.message,
              'seconds': time.monotonic()-start}
    if result.success:
        record['max_equality_residual'] = float(max(abs(A@result.x-b)))
        record['minimum_variable'] = float(min(result.x))
        record['positive_variables'] = int(sum(result.x > 1e-8))
    print(json.dumps(record), flush=True)
    if output:
        Path(output).write_text(json.dumps({'build': info, 'result': record}, indent=2)+'\n')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--labeling', default='experiments/logs/independent-sets/transversal-hemisphere-minimal21-spectral.json')
    parser.add_argument('--seconds', type=int, default=30)
    parser.add_argument('--no-spectral', action='store_true')
    parser.add_argument('--output')
    args = parser.parse_args()
    run(args.labeling, args.seconds, not args.no_spectral, args.output)
