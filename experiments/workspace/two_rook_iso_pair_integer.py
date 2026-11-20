"""Bounded edge completion for the forced two-isomorphic-rook incidence.

All 81 exterior vertices are present. The nine diagonal vertices are
arbitrary tips, not an assumed rook grid. No graph symmetry is imposed.
"""

import argparse
from collections import Counter
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

from two_rook_iso_completion import core, rook, check_incidence, allowed_edges


def data():
    rows = core()
    signatures = [(i, 9+i) for i in range(9)]
    signatures += [(i, 9+j) for i, j in product(range(9), repeat=2)
                   if i != j and not rook(i, j) for copy in range(2)]
    assert len(signatures) == 81
    need = check_incidence(rows, signatures)
    edges = allowed_edges(signatures, need)
    assert len(edges) == 3060
    return rows, signatures, need, edges


def build():
    started = time.monotonic()
    rows, signatures, need, edges = data()
    pool, cnf = IDPool(), CNF()
    variables = {edge: pool.id(('edge', *edge)) for edge in edges}
    incident = [[] for _ in signatures]
    for (a, b), variable in variables.items():
        incident[a].append((b, variable))
        incident[b].append((a, variable))
    seen = set()
    for t in range(81):
        for i in range(19):
            literals = [variable for s, variable in incident[t]
                        if i == 18 or i in signatures[s]]
            key = (tuple(literals), need[t][i])
            if key not in seen:
                seen.add(key)
                assert 0 <= need[t][i] <= len(literals)
                cnf.extend(CardEnc.equals(literals, need[t][i], vpool=pool,
                                         encoding=EncType.seqcounter).clauses)
    packing = set()
    for a, b in combinations(range(81), 2):
        if len(set(signatures[a]) & set(signatures[b])) < 2:
            continue
        for t in range(81):
            first, second = tuple(sorted((a, t))), tuple(sorted((b, t)))
            if first in variables and second in variables:
                packing.add(tuple(sorted((-variables[first], -variables[second]))))
    cnf.extend([list(clause) for clause in sorted(packing)])
    metadata = {'core_vertices': 18, 'outside_vertices': 81,
                'selection_variables': 0, 'edge_variables': len(variables),
                'variables_with_auxiliaries': cnf.nv, 'clauses': len(cnf.clauses),
                'packing_clauses': len(packing), 'orbit_equalities': 0,
                'tip_graph_assumptions': 0,
                'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'build_seconds': time.monotonic()-started}
    return cnf, variables, rows, signatures, metadata


def inspect_point(positive, variables, core_rows, signatures):
    rows = core_rows[:]+[0]*81
    for a, sites in enumerate(signatures, 18):
        for b in sites:
            rows[a] |= 1 << b
            rows[b] |= 1 << a
    selected_edges = []
    for (a, b), variable in variables.items():
        if variable in positive:
            i, j = 18+a, 18+b
            rows[i] |= 1 << j
            rows[j] |= 1 << i
            selected_edges.append([a, b])
    assert all(row.bit_count() == 14 for row in rows)
    assert all((rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1) == 2
               for i in range(18) for j in range(i+1, 99))
    defects, histogram = [], Counter()
    for i, j in combinations(range(99), 2):
        value = (rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1)
        histogram[value-2] += 1
        if value != 2:
            defects.append([i, j, value-2])
    cuts = []
    for a, b in combinations(range(81), 2):
        i, j = 18+a, 18+b
        overlap = len(set(signatures[a]) & set(signatures[b]))
        terms = [('edge', None)] if (rows[i] >> j) & 1 else []
        for c in range(81):
            if (rows[i] >> (18+c)) & 1 and (rows[j] >> (18+c)) & 1:
                terms.append(('via', c))
        if len(terms)+overlap <= 2:
            continue
        witness = terms[:3-overlap]
        cuts.append({'pair': [a, b], 'edge': any(kind == 'edge' for kind, _ in witness),
                     'via': [c for kind, c in witness if kind == 'via']})
    assert not defects or cuts
    return {'selected_edges': selected_edges,
            'degree_check': 'all99 vertices have degree14',
            'core_common_neighbor_check': 'all pairs involving the18-core are exact',
            'tip_edges': [[a, b] for a, b in selected_edges if a < 9 and b < 9],
            'common_neighbor_defect_histogram': [[k, v] for k, v in sorted(histogram.items())],
            'defective_pairs': len(defects), 'first_defects': defects[:30],
            'outside_cap_violations': len(cuts)}, cuts


def cut_clause(record, signatures, variables):
    a, b = record['pair']
    assert a < b and not set(record['via']) & {a, b}
    assert len(set(record['via'])) == len(record['via'])
    overlap = len(set(signatures[a]) & set(signatures[b]))
    assert int(record['edge'])+len(record['via'])+overlap == 3
    terms = [variables[a, b]] if record['edge'] else []
    for c in record['via']:
        terms += [variables[tuple(sorted((a, c)))], variables[tuple(sorted((b, c)))]]
    return sorted({-variable for variable in terms})


def run(seconds, rounds, output, cnf_path=None):
    cnf, variables, core_rows, signatures, metadata = build()
    metadata.update(solver='glucose4', wall_budget_seconds=seconds,
                    maximum_refinement_rounds=rounds)
    if cnf_path:
        cnf_path.parent.mkdir(parents=True, exist_ok=True)
        cnf.to_file(cnf_path)
        metadata.update(cnf_path=str(cnf_path), cnf_sha256=hashlib.sha256(cnf_path.read_bytes()).hexdigest())
    print(json.dumps({'built': metadata}), flush=True)
    result = {'status': 'unresolved', 'metadata': metadata, 'points': [], 'necessary_cuts': []}
    started, seen = time.monotonic(), set()
    with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
        for iteration in range(rounds):
            remaining = seconds-(time.monotonic()-started)
            if remaining <= 0:
                result['status'] = 'unknown at wall budget'
                break
            timer = Timer(remaining, solver.interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
            if answer is not True:
                result['status'] = 'solver UNSAT; independently checkable proof not yet obtained' if answer is False else 'unknown at wall budget'
                break
            point, cuts = inspect_point({v for v in solver.get_model() if v > 0}, variables, core_rows, signatures)
            result['points'].append(point)
            print(json.dumps({'round': iteration+1, 'defective_pairs': point['defective_pairs'],
                              'outside_cap_violations': point['outside_cap_violations'],
                              'seconds': time.monotonic()-started}), flush=True)
            if not point['defective_pairs']:
                result['status'] = 'exact99-vertex SRG candidate; independent validation required'
                break
            for record in cuts:
                clause = cut_clause(record, signatures, variables)
                key = tuple(clause)
                if key not in seen:
                    seen.add(key)
                    solver.add_clause(clause)
                    result['necessary_cuts'].append(record)
        else:
            result['status'] = 'refinement round limit; partial binary points only'
        result['solver_statistics'] = solver.accum_stats()
    result['seconds'] = time.monotonic()-started
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'status': result['status'], 'binary_points': len(result['points']),
                      'necessary_cuts': len(result['necessary_cuts']), 'seconds': result['seconds']}), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--rounds', type=int, default=20)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--cnf', type=Path)
    args = parser.parse_args()
    run(args.seconds, args.rounds, args.output, args.cnf)
