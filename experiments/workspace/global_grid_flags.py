"""Global grid-line incidence relaxation with exact local support enumeration.

The LP is exploratory. A floating-point status is not a nonexistence proof.
"""
from collections import Counter
from itertools import combinations, combinations_with_replacement
import argparse
import json
from pathlib import Path

import networkx as nx
import numpy as np
from scipy.optimize import Bounds, LinearConstraint, linprog, milp


def bipartite_components(graph):
    return sum(nx.is_bipartite(graph.subgraph(c))
               for c in nx.connected_components(graph))


def root_types():
    out = []
    for graph in nx.graph_atlas_g():
        if len(graph) != 7 or graph.number_of_edges() > 15:
            continue
        complement = nx.complement(graph)
        rank_defect = bipartite_components(complement)
        good = True
        for e in list(complement.edges()):
            complement.remove_edge(*e)
            if bipartite_components(complement) > rank_defect:
                good = False
            complement.add_edge(*e)
            if not good:
                break
        if not good:
            continue
        # The archived proof also excludes a sole six-cycle support.
        nonisolated = [v for v, d in complement.degree() if d]
        if (len(nonisolated) == 6 and complement.number_of_edges() == 6
                and all(complement.degree(v) == 2 for v in nonisolated)
                and nx.is_connected(complement.subgraph(nonisolated))):
            continue
        degrees = dict(graph.degree())
        pairs = Counter()
        covered = Counter()
        disjoint = 0
        for u, v in graph.edges():
            key = tuple(sorted((degrees[u], degrees[v])))
            pairs[key] += 1
            remainder = graph.number_of_edges()-degrees[u]-degrees[v]+1
            disjoint += remainder
            if remainder == 0:
                covered[key] += 1
        out.append({"graph6": nx.to_graph6_bytes(graph, header=False).decode().strip(),
                    "edges": graph.number_of_edges(),
                    "disjoint": disjoint // 2,
                    "degrees": Counter(degrees.values()),
                    "pairs": pairs, "covered": covered})
    return out


def grid_types():
    triples = list(combinations_with_replacement(range(1, 7), 3))
    out = []
    for a, b in combinations_with_replacement(triples, 2):
        pairs, needs_cover = Counter(), Counter()
        for i in range(3):
            for j in range(3):
                key = tuple(sorted((a[i], b[j])))
                pairs[key] += 1
                red_a = sum(a[k] == 6 for k in range(3) if k != i)
                red_b = sum(b[k] == 6 for k in range(3) if k != j)
                # Intersections of distinct four-cycles in K4 have either
                # four edges or two opposite edges. Crossing squares cannot
                # use an edge of a triangle contained in six grids.
                if red_a and red_b:
                    needs_cover[key] += 1
        out.append({"rows": a, "columns": b, "pairs": pairs,
                    "needs_cover": needs_cover})
    return out


def build_model(roots, grids):
    size = len(roots)+len(grids)+7
    eq, rhs, ub, bounds = [], [], [], []
    row = np.zeros(size)
    row[:len(roots)] = 1
    eq.append(row)
    rhs.append(99)
    for key in combinations_with_replacement(range(1, 7), 2):
        row = np.array([r['pairs'][key] for r in roots]
                       + [-g['pairs'][key] for g in grids]+[0]*7, dtype=float)
        eq.append(row)
        rhs.append(0)
        row = np.array([-r['covered'][key] for r in roots]
                       + [g['needs_cover'][key] for g in grids]+[0]*7, dtype=float)
        ub.append(row)
        bounds.append(0)
    # At most four crossing witnesses per nongrid square.
    ub.append(np.array([r['disjoint'] for r in roots]
                       + [18]*len(grids)+[0]*7, dtype=float))
    bounds.append(4158)
    row = np.zeros(size)
    for i, grid in enumerate(grids):
        if grid['rows'] == grid['columns'] == (6, 6, 6):
            row[len(roots)+i] = 1
    ub.append(row)
    bounds.append(7)  # eight_red_exclusion.md
    # A triangle has the same grid multiplicity at all three of its points.
    for degree in range(7):
        row = np.array([r['degrees'][degree] for r in roots]
                       + [0]*(len(grids)+7), dtype=float)
        row[len(roots)+len(grids)+degree] = -3
        eq.append(row)
        rhs.append(0)
    return np.array(eq), np.array(rhs), np.array(ub), np.array(bounds)


def run(out_path, integer=False, cap=None, seconds=60):
    roots, grids = root_types(), grid_types()
    a, b, c, d = build_model(roots, grids)
    objective = np.r_[np.zeros(len(roots)), -np.ones(len(grids)), np.zeros(7)]
    if cap is not None:
        c = np.vstack([c, -objective])
        d = np.r_[d, cap]
    if integer:
        sol = milp(objective, integrality=np.ones(len(objective)),
                   bounds=Bounds(0, np.inf),
                   constraints=[LinearConstraint(a, b, b),
                                LinearConstraint(c, -np.inf, d)],
                   options={'time_limit': seconds})
    else:
        sol = linprog(objective, A_eq=a, b_eq=b, A_ub=c, b_ub=d,
                      bounds=(0, None), method='highs')
    result = {"root_types": len(roots), "grid_types": len(grids),
              "status": int(sol.status), "message": sol.message,
              "integral_counts": integer, "grid_cap": cap,
              "scope": "aggregate incidence relaxation; not a graph construction"}
    if sol.success:
        result['grid_upper_bound_numeric'] = -float(sol.fun)
        result['max_equation_residual'] = float(abs(a@sol.x-b).max())
        result['max_inequality_excess'] = float((c@sol.x-d).max())
        result['triangle_counts_by_grid_degree'] = list(map(float, sol.x[-7:]))
        if np.max(abs(sol.x-np.rint(sol.x))) < 1e-7:
            witness = np.rint(sol.x).astype(object)
            witness = np.array([int(x) for x in witness], dtype=object)
            assert all(x >= 0 for x in witness)
            assert np.array_equal(a.astype(int).astype(object)@witness,
                                  b.astype(int))
            assert all(c.astype(int).astype(object)@witness <= d.astype(int))
            result['integer_witness_checked_exactly'] = True
            sol.x = np.array(witness, dtype=float)
        result['root_support'] = [
            {"graph6": r['graph6'], "count": float(sol.x[i]),
             "edges": r['edges'], "disjoint": r['disjoint']}
            for i, r in enumerate(roots) if sol.x[i] > 1e-8]
        result['grid_support'] = [
            {"rows": g['rows'], "columns": g['columns'],
             "count": float(sol.x[len(roots)+i])}
            for i, g in enumerate(grids) if sol.x[len(roots)+i] > 1e-8]
    print(json.dumps(result, indent=2))
    if out_path:
        out_path.write_text(json.dumps(result, indent=2)+'\n')


def replay(path):
    data = json.loads(path.read_text())
    roots, grids = root_types(), grid_types()
    root_lookup = {r['graph6']: i for i, r in enumerate(roots)}
    grid_lookup = {(g['rows'], g['columns']): len(roots)+i for i, g in enumerate(grids)}
    witness = [0]*(len(roots)+len(grids)+7)
    for item in data['root_support']:
        witness[root_lookup[item['graph6']]] += round(item['count'])
    for item in data['grid_support']:
        key = (tuple(item['rows']), tuple(item['columns']))
        witness[grid_lookup[key]] += round(item['count'])
    witness[-7:] = [round(x) for x in data['triangle_counts_by_grid_degree']]
    witness = np.array(witness, dtype=object)
    a, b, c, d = build_model(roots, grids)
    assert all(x >= 0 for x in witness)
    assert np.array_equal(a.astype(int).astype(object)@witness, b.astype(int))
    assert all(c.astype(int).astype(object)@witness <= d.astype(int))
    grid_count = sum(witness[len(roots):len(roots)+len(grids)])
    print(f'exact aggregate witness checked: {grid_count} grids; includes all-red bound seven')


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--out', type=Path)
    p.add_argument('--integer', action='store_true')
    p.add_argument('--grid-cap', type=int)
    p.add_argument('--seconds', type=float, default=60)
    p.add_argument('--verify', type=Path)
    args = p.parse_args()
    if args.verify:
        replay(args.verify)
    else:
        run(args.out, args.integer, args.grid_cap, args.seconds)
