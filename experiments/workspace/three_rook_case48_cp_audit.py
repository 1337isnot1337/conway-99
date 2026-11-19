"""Independent CP-SAT audit of the remaining three-rook interface core.

No SAT builder or saved signature/edge list is imported. The 27-point
core, Gram deficits, outside signatures, eligible edges, and every
constraint are rebuilt directly from the specified permutation.
"""
from __future__ import annotations

import argparse
from itertools import combinations, product
import json
from pathlib import Path
import time

import ortools
from ortools.sat.python import cp_model


PERMUTATION = (0, 5, 7, 8, 6, 1, 4, 2, 3)


def rook_adjacent(a, b):
    return a != b and (a//3 == b//3 or a % 3 == b % 3)


def target_core():
    rows = [0]*27
    for i in range(27):
        for j in range(i):
            bi, x = divmod(i, 9)
            bj, y = divmod(j, 9)
            adjacent = rook_adjacent(x, y) if bi == bj else (
                x == y if bj == 0 else x == PERMUTATION[y])
            if adjacent:
                rows[i] |= 1 << j
                rows[j] |= 1 << i
    assert all(row.bit_count() == 6 for row in rows)
    return rows


def gram_deficits(rows, degree):
    n = len(rows)
    return [[(degree-2)*int(i == j)+2-(rows[i] & rows[j]).bit_count()-((rows[i] >> j) & 1)
             for j in range(n)] for i in range(n)]


def signatures_for_core(rows, candidates, degree):
    n = len(rows)
    G = gram_deficits(rows, degree)
    assert min(map(min, G)) >= 0
    signatures = []
    demands = []
    for signature in candidates:
        signature = tuple(signature)
        if any(G[i][j] == 0 for i, j in combinations(signature, 2)):
            continue
        mask = sum(1 << i for i in signature)
        demand = tuple(2-int(i in signature)-(rows[i] & mask).bit_count() for i in range(n))
        if min(demand) < 0:
            continue
        signatures.append(signature)
        demands.append(demand)
    return G, signatures, demands


def build_feasibility(rows, G, signatures, demands, degree, outside):
    n = len(rows)
    count = len(signatures)
    masks = [sum(1 << i for i in signature) for signature in signatures]
    edges = []
    for s, t in combinations(range(count), 2):
        if (masks[s] & masks[t]).bit_count() > 1:
            continue
        if any(demands[s][i] < 1 for i in signatures[t]):
            continue
        if any(demands[t][i] < 1 for i in signatures[s]):
            continue
        edges.append((s, t))

    model = cp_model.CpModel()
    selected = [model.new_bool_var(f'z_{s}') for s in range(count)]
    adjacent = [model.new_bool_var(f'a_{s}_{t}') for s, t in edges]
    neighborhoods = [[] for _ in signatures]
    for variable, (s, t) in zip(adjacent, edges):
        model.add(variable <= selected[s])
        model.add(variable <= selected[t])
        neighborhoods[s].append((t, variable))
        neighborhoods[t].append((s, variable))
    model.add(sum(selected) == outside)
    point_rows = [[] for _ in range(n)]
    pair_rows = {pair: [] for pair in combinations(range(n), 2)}
    for s, signature in enumerate(signatures):
        for i in signature:
            point_rows[i].append(selected[s])
        for pair in combinations(signature, 2):
            pair_rows[pair].append(selected[s])
    for i, variables in enumerate(point_rows):
        model.add(sum(variables) == G[i][i])
    positive_gram_pairs = 0
    for (i, j), variables in pair_rows.items():
        if variables or G[i][j]:
            model.add(sum(variables) == G[i][j])
            positive_gram_pairs += 1

    mixed_count = 0
    packing_count = 0
    for t, neighbors in enumerate(neighborhoods):
        point_terms = [[] for _ in range(n)]
        pair_terms = {}
        for s, variable in neighbors:
            for i in signatures[s]:
                point_terms[i].append(variable)
            for pair in combinations(signatures[s], 2):
                pair_terms.setdefault(pair, []).append(variable)
        model.add(sum(variable for _, variable in neighbors) == (degree-len(signatures[t]))*selected[t])
        for i in range(n):
            model.add(sum(point_terms[i]) == demands[t][i]*selected[t])
            mixed_count += 1
        for variables in pair_terms.values():
            if len(variables) >= 2:
                # Two neighbors of t containing the same core pair would
                # have those two points and t as three common neighbors.
                model.add(sum(variables) <= selected[t])
                packing_count += 1
    metadata = {'core_order': n, 'outside_vertices': outside,
                'signatures': count, 'eligible_edges': len(edges),
                'positive_gram_pair_equations': positive_gram_pairs,
                'mixed_equations': mixed_count, 'degree_equations': count,
                'nontrivial_core_pair_neighbor_packing_rows': packing_count,
                'variables': len(model.proto.variables), 'constraints': len(model.proto.constraints)}
    return model, metadata, selected, adjacent, edges


def solve(model, seconds, workers):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = seconds
    solver.parameters.num_search_workers = workers
    solver.parameters.random_seed = 0
    start = time.monotonic()
    status = solver.solve(model)
    return solver, {'status': solver.status_name(status), 'seconds': time.monotonic()-start,
                    'conflicts': solver.num_conflicts, 'branches': solver.num_branches,
                    'response_stats': solver.response_stats()}


def positive_control():
    full = [sum(1 << j for j in range(9) if rook_adjacent(i, j)) for i in range(9)]
    assert all((full[i] & full[j]).bit_count() == 2-int(rook_adjacent(i, j))
               for i, j in combinations(range(9), 2))
    rows = [full[i] & ((1 << 6)-1) for i in range(6)]
    actual_signatures = [tuple(i for i in range(6) if (full[w] >> i) & 1) for w in range(6, 9)]
    G, signatures, demands = signatures_for_core(rows, actual_signatures, 4)
    assert len(signatures) == 3
    model, metadata, selected, adjacent, edges = build_feasibility(rows, G, signatures, demands, 4, 3)
    solver, answer = solve(model, 5, 1)
    assert answer['status'] == 'OPTIMAL'
    assert all(solver.value(x) == 1 for x in selected+adjacent)
    assert len(edges) == 3
    return {**metadata, **answer, 'known_graph': 'nine-vertex rook graph',
            'recovered_outside_triangle': True}


def run(seconds, workers):
    result = {'ortools_version': ortools.__version__, 'positive_control': positive_control()}
    rows = target_core()
    candidates = product(range(9), range(9, 18), range(18, 27))
    G, signatures, demands = signatures_for_core(rows, candidates, 14)
    model, metadata, selected, adjacent, edges = build_feasibility(rows, G, signatures, demands, 14, 72)
    assert len(signatures) == 168 and len(edges) == 9846
    result.update({'permutation_1_to_2': list(PERMUTATION), 'model': metadata,
                   'core_adjacency_bit_rows': rows, 'gram_deficits': G,
                   'signatures': [list(s) for s in signatures],
                   'eligible_edges': [list(e) for e in edges]})
    print(json.dumps({'positive_control': result['positive_control']['status'], 'model': metadata}), flush=True)
    solver, answer = solve(model, seconds, workers)
    result['solve'] = answer
    if answer['status'] in ('FEASIBLE', 'OPTIMAL'):
        result['selected_signatures'] = [s for s, variable in enumerate(selected) if solver.value(variable)]
        result['selected_edges'] = [list(edge) for edge, variable in zip(edges, adjacent) if solver.value(variable)]
    print(json.dumps(answer), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    result = run(args.seconds, args.workers)
    if args.output:
        args.output.write_text(json.dumps(result, indent=2)+'\n')
