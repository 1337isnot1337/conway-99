"""Replay the minimum-H21 spectral witness using exact arithmetic only."""

import argparse
from itertools import combinations
import json
from pathlib import Path

import networkx as nx
import sympy as sp


def positive_pivots(M):
    M = M.copy()
    pivots = []
    for i in range(M.rows):
        pivot = M[i, i]
        assert pivot > 0
        pivots.append(str(pivot))
        for j in range(i+1, M.rows):
            for k in range(j, M.cols):
                M[j, k] -= M[j, i]*M[i, k]/pivot
                M[k, j] = M[j, k]
    return pivots


def run(labeling_file, output=None):
    source = Path(__file__).with_name('transversal-hemisphere-minimal21.g6')
    graph = nx.read_graph6(source)
    assert len(graph) == 21 and graph.number_of_edges() == 35
    neighbors = [set(graph[i]) for i in range(21)]
    assert all(not (neighbors[i] & neighbors[j]) for i,j in graph.edges())
    def independent(vertices):
        return all(j not in neighbors[i] for i,j in combinations(vertices, 2))
    assert not any(independent(S) for S in combinations(range(21), 8))
    witness = next(S for S in combinations(range(21), 7) if independent(S))
    saved = json.loads(Path(labeling_file).read_text())
    labels = saved['result']['labels']
    assert sorted(map(tuple, labels)) == list(combinations(range(7), 2))
    A = sp.Matrix(nx.to_numpy_array(graph, dtype=int).tolist())
    B = sp.zeros(21, 7)
    for i, axes in enumerate(labels):
        for a in axes:
            B[i, a] = 1
    assert B.T*B == 5*sp.eye(7)+sp.ones(7)
    K = sp.zeros(36)
    for a in range(7):
        K[0, 1+2*a] = K[1+2*a, 0] = 1
        K[0, 2+2*a] = K[2+2*a, 0] = 1
        K[1+2*a, 2+2*a] = K[2+2*a, 1+2*a] = 1
    for i in range(21):
        for j in range(21):
            K[15+i, 15+j] = A[i,j]
        for a in labels[i]:
            K[15+i, 1+2*a] = K[1+2*a, 15+i] = 1
    common = K*K+K
    assert all(common[i,j] <= 2 for i,j in combinations(range(36), 2))
    W = 3*sp.eye(36)-K+sp.ones(36)/9
    V = 4*sp.eye(36)+K-2*sp.ones(36)/11
    Q = 24*sp.eye(21)-8*A-3*B*B.T+2*sp.ones(21)
    P = 60*sp.eye(21)+15*A-4*B*B.T-2*sp.ones(21)
    for projector, root_coefficient, reduced, scale in [(W,4,Q,8), (V,-3,P,15)]:
        relation = sp.Matrix([root_coefficient]+[1]*14+[0]*21)
        assert projector*relation == sp.zeros(36, 1)
        near = projector[1:15, 1:15]
        positive_pivots(near)
        cross = projector[15:36, 1:15]
        assert projector[15:36, 15:36]-cross*near.inv()*cross.T == reduced/scale
    record = {'vertices': 21, 'edges': 35, 'independence_number': 7,
              'independent_set': list(witness), 'core_vertices': 36,
              'exact_q_positive_pivots': positive_pivots(Q),
              'exact_p_positive_pivots': positive_pivots(P),
              'full_projector_ranks': [35, 35], 'schur_identities_verified': True}
    if output:
        Path(output).write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--labeling', default='experiments/logs/independent-sets/transversal-hemisphere-minimal21-spectral.json')
    parser.add_argument('--output')
    args = parser.parse_args()
    run(args.labeling, args.output)
