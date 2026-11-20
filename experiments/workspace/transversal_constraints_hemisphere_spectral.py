"""Search axis labelings of a specified H21 with exact spectral cuts.

For the 36-vertex root/neighborhood/hemisphere core, eliminating the near
vertices from 9 times the negative projector gives, up to positive scale,
Q = 24 I - 8 A - 3 B B^T + 2 J.  Each integer vector v therefore imposes
the exact linear cut v^T Q v >= 0 on the shared-axis indicators.

CP-SAT statuses are solver results, not standalone infeasibility certificates.
Every cut is recorded as integers and can be checked independently.
"""

import argparse
from functools import reduce
from itertools import combinations
import json
from math import gcd
from pathlib import Path
import time

import networkx as nx
import numpy as np
from ortools.sat.python import cp_model
import sympy as sp

from transversal_constraints_hemisphere import core


def exact_psd(M):
    """Symmetric rational Gaussian elimination with exact pivot signs."""
    K = sp.Matrix(M.tolist())
    n = K.rows
    for i in range(n):
        if K[i, i] < 0:
            return False
        if K[i, i] == 0:
            if any(K[i, j] for j in range(i+1, n)):
                return False
            continue
        for j in range(i+1, n):
            for k in range(j, n):
                K[j, k] -= K[j, i]*K[i, k]/K[i, i]
                K[k, j] = K[j, k]
    return True


def run(seconds=45, rounds=100, output=None):
    source = Path(__file__).with_name('transversal-hemisphere-minimal21.g6')
    G = nx.read_graph6(source)
    A = nx.to_numpy_array(G, dtype=np.int64)
    common = A @ A
    model = cp_model.CpModel()
    B = [[model.new_bool_var(f'b{i}_{a}') for a in range(7)] for i in range(21)]
    for i in range(21):
        model.add(sum(B[i]) == 2)
    for a in range(7):
        model.add(sum(B[i][a] for i in range(21)) == 6)
    # Canonical column order removes all axis permutations.
    for a in range(6):
        model.add(sum((1 << (20-i))*(B[i][a]-B[i][a+1]) for i in range(21)) >= 1)
    for a, b in combinations(range(7), 2):
        products = []
        for i in range(21):
            z = model.new_bool_var('')
            model.add_multiplication_equality(z, [B[i][a], B[i][b]])
            products.append(z)
        model.add(sum(products) == 1)
    for i in range(21):
        for a in range(7):
            model.add(sum(B[j][a] for j in np.flatnonzero(A[i]))+B[i][a] <= 2)
    shared = {}
    for i, j in combinations(range(21), 2):
        if common[i, j]+A[i, j] == 2:
            for a in range(7):
                model.add(B[i][a]+B[j][a] <= 1)
        else:
            shared[i, j] = model.new_bool_var(f'c{i}_{j}')
            products = []
            for a in range(7):
                z = model.new_bool_var('')
                model.add_multiplication_equality(z, [B[i][a], B[j][a]])
                products.append(z)
            model.add(sum(products) == shared[i, j])
    cuts = []
    start = time.monotonic()
    final = None
    for iteration in range(rounds):
        left = seconds - (time.monotonic()-start)
        if left <= 0:
            break
        solver = cp_model.CpSolver()
        solver.parameters.num_workers = 2
        solver.parameters.max_time_in_seconds = left
        solver.parameters.random_seed = 1
        status = solver.solve(model)
        record = {'iteration': iteration, 'status': solver.status_name(status),
                  'seconds': time.monotonic()-start, 'conflicts': solver.num_conflicts,
                  'branches': solver.num_branches}
        if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            print(json.dumps(record), flush=True)
            final = record
            break
        b = np.array([[solver.value(x) for x in row] for row in B], dtype=np.int64)
        assert np.all(b.sum(axis=1) == 2) and np.all(b.sum(axis=0) == 6)
        assert np.all(b.T @ b == np.eye(7, dtype=np.int64)*5+1)
        K = core(A, b)
        assert max((K @ K+K)[np.triu_indices(len(K), 1)]) <= 2
        Q = 24*np.eye(21, dtype=np.int64)-8*A-3*b@b.T+2
        P = 60*np.eye(21, dtype=np.int64)+15*A-4*b@b.T-2
        qvalues, qvectors = np.linalg.eigh(Q)
        pvalues, pvectors = np.linalg.eigh(P)
        record['q_min'] = float(qvalues[0])
        record['p_min'] = float(pvalues[0])
        added = 0
        for kind, values, vectors, matrix in [('q', qvalues, qvectors, Q),
                                              ('p', pvalues, pvectors, P)]:
            for ix in np.flatnonzero(values < -1e-7):
                # Only the exact integer violation justifies the cut.
                v = np.rint(1000*vectors[:, ix]).astype(np.int64)
                divisor = reduce(gcd, map(int, v), 0)
                if divisor:
                    v //= divisor
                violation = int(v @ matrix @ v)
                assert violation < 0
                if kind == 'q':
                    factor = 6
                    rhs = int(18*(v@v)-8*(v@A@v)+2*v.sum()**2)
                else:
                    factor = 8
                    rhs = int(52*(v@v)+15*(v@A@v)-2*v.sum()**2)
                model.add(sum(int(factor*v[i]*v[j])*variable
                              for (i,j), variable in shared.items()) <= rhs)
                cuts.append({'kind': kind, 'vector': v.tolist(), 'rhs': rhs,
                             'violated_value': violation})
                added += 1
        record['new_cuts'] = added
        print(json.dumps(record), flush=True)
        if not added:
            assert exact_psd(Q) and exact_psd(P)
            record['labels'] = [np.flatnonzero(row).tolist() for row in b]
            record['exact_psd'] = True
            final = record
            break
    if final is None:
        final = {'status': 'LIMIT', 'seconds': time.monotonic()-start}
    result = {'result': final, 'cuts': cuts}
    if output:
        Path(output).write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'summary': final, 'total_cuts': len(cuts)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=int, default=45)
    parser.add_argument('--rounds', type=int, default=100)
    parser.add_argument('--output')
    args = parser.parse_args()
    run(args.seconds, args.rounds, args.output)
