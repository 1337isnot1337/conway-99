"""Test the unique minimum (3,8;21,35) graph as a rooted hemisphere.

The graph6 input comes from the House of Graphs minimal Ramsey collection:
https://houseofgraphs.org/data/ramsey/minramsey/Ramseygraphs_3_8_21_e35.g6
The catalogue's uniqueness is a published input, not asserted by this search.
"""

import argparse
from itertools import combinations
import json
from pathlib import Path
import time

import networkx as nx
import numpy as np
from ortools.sat.python import cp_model


def core(A, incidence):
    n = len(A)
    K = np.zeros((15+n, 15+n), dtype=np.int64)
    K[0, 1:15] = K[1:15, 0] = 1
    for a in range(7):
        K[1+2*a, 2+2*a] = K[2+2*a, 1+2*a] = 1
    K[15:, 15:] = A
    for i in range(n):
        for a in range(7):
            K[15+i, 1+2*a] = K[1+2*a, 15+i] = incidence[i, a]
    return K


def run(seconds=45, output=None):
    source = Path(__file__).with_name('transversal-hemisphere-minimal21.g6')
    graph = nx.read_graph6(source)
    A = nx.to_numpy_array(graph, dtype=np.int64)
    assert len(A) == 21 and int(A.sum()) == 70
    assert np.trace(A @ A @ A) == 0
    # Verify the advertised independence number directly, without a solver.
    assert not any(not A[np.ix_(S, S)].any() for S in combinations(range(21), 8))
    assert any(not A[np.ix_(S, S)].any() for S in combinations(range(21), 7))
    common = A @ A
    assert max(common[np.triu_indices(21, 1)]) == 2
    model = cp_model.CpModel()
    B = [[model.new_bool_var(f'b{i}_{a}') for a in range(7)] for i in range(21)]
    for i in range(21):
        model.add(sum(B[i]) == 2)
    for a in range(7):
        model.add(sum(B[i][a] for i in range(21)) == 6)
    for a, b in combinations(range(7), 2):
        products = []
        for i in range(21):
            z = model.new_bool_var('')
            model.add_multiplication_equality(z, [B[i][a], B[i][b]])
            products.append(z)
        model.add(sum(products) == 1)
    model.add(B[0][0] == 1)
    model.add(B[0][1] == 1)
    for i in range(21):
        for a in range(7):
            model.add(sum(B[j][a] for j in np.flatnonzero(A[i]))+B[i][a] <= 2)
    for i, j in combinations(range(21), 2):
        if common[i, j]+A[i, j] == 2:
            for a in range(7):
                model.add(B[i][a]+B[j][a] <= 1)
    solver = cp_model.CpSolver()
    solver.parameters.num_workers = 2
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.random_seed = 1
    start = time.monotonic()
    status = solver.solve(model)
    record = {'status': solver.status_name(status), 'seconds': time.monotonic()-start,
              'conflicts': solver.num_conflicts, 'branches': solver.num_branches}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        B = np.array([[solver.value(x) for x in row] for row in B], dtype=np.int64)
        assert np.all(B.sum(axis=1) == 2) and np.all(B.sum(axis=0) == 6)
        assert np.all(B.T @ B == np.eye(7, dtype=np.int64)*5+1)
        K = core(A, B)
        assert max((K @ K+K)[np.triu_indices(len(K), 1)]) <= 2
        record['negative_projector_min_eigenvalue'] = float(np.linalg.eigvalsh(3*np.eye(len(K))-K+1/9)[0])
        record['positive_projector_min_eigenvalue'] = float(np.linalg.eigvalsh(4*np.eye(len(K))+K-2/11)[0])
        record['labels'] = [np.flatnonzero(row).tolist() for row in B]
        if output:
            Path(output).write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--seconds', type=int, default=45)
    parser.add_argument('--output')
    args = parser.parse_args()
    run(args.seconds, args.output)
