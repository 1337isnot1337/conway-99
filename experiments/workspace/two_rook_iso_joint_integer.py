"""Bounded full integer incidence/edge search for the two-arm rook core.

No orbit equalities or graph-symmetry assumptions are imposed. A binary
linear-model point is checked on all 99 vertices. Necessary forbidden
edge clauses can be added for actual outside common-neighbor violations.
An unverified solver UNSAT status is not an exclusion certificate.
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

from two_rook_iso_joint_incidence import domain
from two_rook_iso_completion import allowed_edges, check_incidence


def conditional_count(cnf, pool, literals, quota, selected):
    """Assuming every literal implies selected, impose sum = quota*selected."""
    if quota > len(literals):
        cnf.append([-selected])
        return
    if quota < len(literals):
        cnf.extend(CardEnc.atmost(literals, quota, vpool=pool,
                                 encoding=EncType.seqcounter).clauses)
    if quota:
        clauses = CardEnc.atleast(literals, quota, vpool=pool,
                                  encoding=EncType.seqcounter).clauses
        cnf.extend([[-selected, *clause] for clause in clauses])


def controls():
    cases = 0
    for count in range(6):
        for quota in (0, 1, 2, 5):
            pool = IDPool()
            selected = pool.id('selected')
            literals = [pool.id(('x', i)) for i in range(count)]
            cnf = CNF()
            cnf.extend([[-literal, selected] for literal in literals])
            conditional_count(cnf, pool, literals, quota, selected)
            with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
                for choice, values in product((False, True), product((False, True), repeat=count)):
                    expected = sum(values) == quota*choice
                    assumptions = [selected if choice else -selected]
                    assumptions += [literal if value else -literal for literal, value in zip(literals, values)]
                    assert solver.solve(assumptions=assumptions) == expected
                    cases += 1
    return {'conditional_count_truth_table_cases': cases, 'status': 'exact pass'}


def build():
    started = time.monotonic()
    core_rows, G, signatures, need = domain()
    edges = allowed_edges(signatures, need)
    pool, cnf = IDPool(), CNF()
    z = [pool.id(('selected', s)) for s in range(len(signatures))]
    variables = {edge: pool.id(('edge', *edge)) for edge in edges}
    incident = [[] for _ in signatures]
    for (a, b), variable in variables.items():
        cnf.extend([[-variable, z[a]], [-variable, z[b]]])
        incident[a].append((b, variable))
        incident[b].append((a, variable))

    counts_seen = set()
    for i in range(27):
        for j in range(i, 27):
            literals = [z[s] for s, sites in enumerate(signatures) if i in sites and j in sites]
            key = (tuple(literals), G[i][j])
            if key in counts_seen:
                continue
            counts_seen.add(key)
            assert 0 <= G[i][j] <= len(literals)
            cnf.extend(CardEnc.equals(literals, G[i][j], vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
    cnf.extend(CardEnc.equals(z, 72, vpool=pool, encoding=EncType.seqcounter).clauses)

    mixed_seen = set()
    for t in range(len(signatures)):
        for i in range(28):
            literals = [variable for s, variable in incident[t]
                        if i == 27 or i in signatures[s]]
            key = (z[t], tuple(literals), need[t][i])
            if key in mixed_seen:
                continue
            mixed_seen.add(key)
            conditional_count(cnf, pool, literals, need[t][i], z[t])

    # Neighbor signatures containing the same core pair form a packing.
    # Activation plus unconditional at-most-one is exactly <= z_t here.
    neighbor_variables = [dict(neighbors) for neighbors in incident]
    packing_clauses = set()
    for i, j in combinations(range(27), 2):
        family = [s for s, sites in enumerate(signatures) if i in sites and j in sites]
        if len(family) < 2:
            continue
        for t in range(len(signatures)):
            literals = [neighbor_variables[t][s] for s in family if s in neighbor_variables[t]]
            for a, b in combinations(literals, 2):
                packing_clauses.add(tuple(sorted((-a, -b))))
    cnf.extend([list(clause) for clause in sorted(packing_clauses)])
    metadata = {'signatures': len(signatures), 'candidate_edges': len(edges),
                'signature_variables': len(z), 'edge_variables': len(variables),
                'variables_with_auxiliaries': cnf.nv, 'clauses': len(cnf.clauses),
                'packing_clauses': len(packing_clauses), 'orbit_equalities': 0,
                'source_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                'build_seconds': time.monotonic()-started}
    return cnf, z, variables, core_rows, signatures, metadata


def inspect_point(positive, z, edge_variables, core_rows, signatures):
    selected = [s for s, literal in enumerate(z) if literal in positive]
    assert len(selected) == 72
    chosen = [signatures[s] for s in selected]
    check_incidence(core_rows, chosen)
    labels = {s: 27+i for i, s in enumerate(selected)}
    rows = core_rows[:]+[0]*72
    selected_edges = []
    for s in selected:
        a = labels[s]
        for b in signatures[s]:
            rows[a] |= 1 << b
            rows[b] |= 1 << a
    for (a, b), variable in edge_variables.items():
        if variable in positive:
            assert a in labels and b in labels
            i, j = labels[a], labels[b]
            rows[i] |= 1 << j
            rows[j] |= 1 << i
            selected_edges.append([a, b])
    assert all(row.bit_count() == 14 for row in rows)
    assert all((rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1) == 2
               for i in range(27) for j in range(i+1, 99))
    defects, histogram = [], Counter()
    for i, j in combinations(range(99), 2):
        value = (rows[i] & rows[j]).bit_count()+((rows[i] >> j) & 1)
        histogram[value-2] += 1
        if value != 2:
            defects.append([i, j, value-2])
    cuts = []
    for a, b in combinations(selected, 2):
        i, j = labels[a], labels[b]
        overlap = len(set(signatures[a]) & set(signatures[b]))
        terms = []
        if (rows[i] >> j) & 1:
            terms.append(('edge', None))
        for c in selected:
            k = labels[c]
            if (rows[i] >> k) & 1 and (rows[j] >> k) & 1:
                terms.append(('via', c))
        if len(terms)+overlap <= 2:
            continue
        witness = terms[:3-overlap]
        use_edge = any(kind == 'edge' for kind, _ in witness)
        via = [c for kind, c in witness if kind == 'via']
        cuts.append({'pair': [a, b], 'edge': use_edge, 'via': via})
    assert not defects or cuts
    return {'selected_signatures': selected, 'selected_edges': selected_edges,
            'degree_check': 'all 99 vertices have degree14',
            'core_common_neighbor_check': 'all pairs involving the core are exact',
            'common_neighbor_defect_histogram': [[difference, count] for difference, count in sorted(histogram.items())],
            'defective_pairs': len(defects), 'first_defects': defects[:30],
            'outside_cap_violations': len(cuts)}, cuts


def cut_clause(record, signatures, edge_variables):
    a, b = record['pair']
    assert a < b
    overlap = len(set(signatures[a]) & set(signatures[b]))
    assert len(set(record['via'])) == len(record['via'])
    assert not set(record['via']) & {a, b}
    assert int(record['edge'])+len(record['via'])+overlap == 3
    variables = []
    if record['edge']:
        variables.append(edge_variables[a, b])
    for c in record['via']:
        variables.append(edge_variables[tuple(sorted((a, c)))])
        variables.append(edge_variables[tuple(sorted((b, c)))])
    return sorted({-variable for variable in variables})


def run(seconds, rounds, output, cnf_path=None):
    control = controls()
    cnf, z, edges, core_rows, signatures, metadata = build()
    metadata.update(control=control, solver='glucose4', wall_budget_seconds=seconds,
                    maximum_refinement_rounds=rounds)
    if cnf_path:
        cnf_path.parent.mkdir(parents=True, exist_ok=True)
        cnf.to_file(cnf_path)
        metadata.update(cnf_path=str(cnf_path), cnf_sha256=hashlib.sha256(cnf_path.read_bytes()).hexdigest())
    print(json.dumps({'built': metadata}), flush=True)
    result = {'status': 'unresolved', 'metadata': metadata, 'points': [], 'necessary_cuts': []}
    started = time.monotonic()
    seen = set()
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
            point, cuts = inspect_point({v for v in solver.get_model() if v > 0}, z, edges, core_rows, signatures)
            result['points'].append(point)
            print(json.dumps({'round': iteration+1, 'defective_pairs': point['defective_pairs'],
                              'outside_cap_violations': point['outside_cap_violations'],
                              'seconds': time.monotonic()-started}), flush=True)
            if not point['defective_pairs']:
                result['status'] = 'exact 99-vertex SRG candidate; independent validation required'
                break
            for record in cuts:
                clause = cut_clause(record, signatures, edges)
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
