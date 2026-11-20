"""Binary one-source-row projections for the complementary-rook core.

All 252 incidence selectors remain free. A selected source has all its
mixed/degree equations, neighbor packing, and the necessary perfect
matching on its eight neighbors disjoint from its core signature.
No graph automorphism or fixed incidence design is imposed.
"""

import argparse
from collections import Counter
import gc
import hashlib
from itertools import combinations
import json
from pathlib import Path
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

import complement_rook_a_incidence as incidence
from complement_rook_a_incidence_census import actions


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def eligible(s, t, signatures, needs):
    return (len(set(signatures[s]) & set(signatures[t])) <= 1
            and all(needs[s][i] > 0 for i in signatures[t])
            and all(needs[t][i] > 0 for i in signatures[s]))


def domain(orbit):
    rows, gram, triples, signatures, _, _ = incidence.domain()
    group = actions()
    minima = [min(g[s] for g in group) for s in range(252)]
    representatives = sorted(set(minima))
    assert [minima.count(s) for s in representatives] == [72, 144, 36]
    assert [triples[s] for s in representatives] == [(0, 4, 1), (0, 4, 2), (0, 4, 8)]
    assert 0 <= orbit < 3
    source = representatives[orbit]
    needs = [[2-sum(((rows[i] >> j) & 1)+int(i == j) for j in sites)
              for i in range(27)] for sites in signatures]
    assert all(min(need) >= 0 and sum(need) == 33 for need in needs)
    assert all(not(rows[i] >> j & 1) for i, j in combinations(signatures[source], 2))
    assert all(needs[source][i] == 1 for i in signatures[source])
    neighbors = [w for w in range(252) if w != source and eligible(source, w, signatures, needs)]
    zero = [w for w in neighbors if not set(signatures[w]) & set(signatures[source])]
    one = [w for w in neighbors if w not in zero]
    pairs = [(v, w) for v, w in combinations(zero, 2)
             if not set(signatures[v]) & set(signatures[w])
             and eligible(v, w, signatures, needs)]
    packing = [(v, w) for v, w in combinations(neighbors, 2)
               if len(set(signatures[v]) & set(signatures[w])) >= 2]
    return rows, gram, triples, signatures, needs, source, neighbors, zero, one, pairs, packing


def matching_rows(cnf, pool, selected, pairing):
    """Encode sum of incident pairing bits = the selected bit at each vertex."""
    incident = {v: [] for v in selected}
    for (v, w), variable in pairing.items():
        assert v in selected and w in selected and v != w
        incident[v].append(variable)
        incident[w].append(variable)
    for v, variables in incident.items():
        cnf.append([-selected[v]]+variables)
        for variable in variables:
            cnf.append([-variable, selected[v]])
        if len(variables) > 1:
            cnf.extend(CardEnc.atmost(variables, 1, vpool=pool,
                                     encoding=EncType.seqcounter).clauses)


def perfect_matching_exists(vertices, edges):
    vertices = frozenset(vertices)
    if not vertices:
        return True
    if len(vertices) % 2:
        return False
    v = min(vertices)
    return any(tuple(sorted((v, w))) in edges and
               perfect_matching_exists(vertices-{v, w}, edges)
               for w in vertices if w != v)


def controls():
    checked = accepted = 0
    for n in range(5):
        possible = list(combinations(range(n), 2))
        for mask in range(1 << len(possible)):
            edges = {edge for bit, edge in enumerate(possible) if mask >> bit & 1}
            pool, cnf = IDPool(), CNF()
            selected = {v: pool.id(('y', v)) for v in range(n)}
            pairing = {edge: pool.id(('pair', *edge)) for edge in sorted(edges)}
            matching_rows(cnf, pool, selected, pairing)
            with Solver(name='glucose4', bootstrap_with=cnf.clauses) as solver:
                for choice in range(1 << n):
                    vertices = {v for v in range(n) if choice >> v & 1}
                    assumptions = [variable if v in vertices else -variable
                                   for v, variable in selected.items()]
                    result = solver.solve(assumptions=assumptions)
                    assert result == perfect_matching_exists(vertices, edges)
                    checked += 1
                    accepted += result
                    if result:
                        positive = {v for v in solver.get_model() if v > 0}
                        degrees = Counter(v for edge, variable in pairing.items()
                                          if variable in positive for v in edge)
                        assert all(degrees[v] == int(v in vertices) for v in range(n))
    assert checked == 1099
    rook = [[int(p != q and (p//3 == q//3 or p % 3 == q % 3))
             for q in range(9)] for p in range(9)]
    assert all(sum(row) == 4 for row in rook)
    assert all(sum(rook[p][r]*rook[r][q] for r in range(9))+rook[p][q] == 2
               for p, q in combinations(range(9), 2))
    for v in range(9):
        neighbors = {w for w in range(9) if rook[v][w]}
        pairs = {edge for edge in combinations(sorted(neighbors), 2) if rook[edge[0]][edge[1]]}
        assert len(pairs) == 2 and perfect_matching_exists(neighbors, pairs)
    return {'status': 'exact matching controls PASS', 'small_cases': checked,
            'small_SAT_cases': accepted, 'rook_neighborhood_controls': 9}


def build(orbit, cnf_path, manifest_path):
    started = time.monotonic()
    control = controls()
    rows, gram, triples, signatures, needs, source, neighbors, zero, one, pairs, packing = domain(orbit)
    pool, cnf = IDPool(), CNF()
    selected = {s: pool.id(('select', s)) for s in range(252)}
    neighbor = {w: pool.id(('neighbor', w)) for w in neighbors}
    pairing = {edge: pool.id(('matching', *edge)) for edge in pairs}
    cnf.append([selected[source]])
    equations = set()
    for i in range(27):
        for j in range(i, 27):
            family = tuple(selected[s] for s, sites in enumerate(signatures) if i in sites and j in sites)
            key = (family, gram[i][j])
            if key in equations:
                continue
            equations.add(key)
            assert 0 <= gram[i][j] <= len(family)
            cnf.extend(CardEnc.equals(list(family), gram[i][j], vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
    cnf.extend(CardEnc.equals(list(selected.values()), 72, vpool=pool,
                             encoding=EncType.seqcounter).clauses)
    for w, variable in neighbor.items():
        cnf.append([-variable, selected[w]])
    for i in range(27):
        literals = [variable for w, variable in neighbor.items() if i in signatures[w]]
        assert needs[source][i] <= len(literals)
        cnf.extend(CardEnc.equals(literals, needs[source][i], vpool=pool,
                                 encoding=EncType.seqcounter).clauses)
    for vertices, target in ((neighbors, 11), (zero, 8), (one, 3)):
        cnf.extend(CardEnc.equals([neighbor[w] for w in vertices], target, vpool=pool,
                                 encoding=EncType.seqcounter).clauses)
    cnf.extend([[-neighbor[v], -neighbor[w]] for v, w in packing])
    matching_rows(cnf, pool, {w: neighbor[w] for w in zero}, pairing)
    cnf_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    cnf.to_file(cnf_path)
    exact_domain = {'core_rows': rows, 'core_gram': gram, 'signatures': signatures,
                    'mixed_demands': needs, 'source': source, 'neighbors': neighbors,
                    'zero_overlap_neighbors': zero, 'one_overlap_neighbors': one,
                    'matching_pairs': pairs, 'packing_pairs': packing,
                    'selector_variables': list(selected.items()),
                    'neighbor_variables': list(neighbor.items()),
                    'pairing_variables': [[*edge, variable] for edge, variable in pairing.items()]}
    record = {'status': 'unconditional one-source-row projection built; not yet solved',
              'orbit': orbit, 'source_index': source, 'source_triple': triples[source],
              'signature_orbit_size': (72, 144, 36)[orbit], 'candidate_selectors': 252,
              'neighbor_variables': len(neighbor), 'zero_overlap_candidates': len(zero),
              'one_overlap_candidates': len(one), 'matching_variables': len(pairing),
              'packing_clauses': len(packing), 'distinct_gram_counts': len(equations),
              'parameter_a_unrestricted': True, 'fixed_incidence_design': False,
              'graph_symmetry_clauses': 0, 'full_exterior_graph': False,
              'cnf_path': str(cnf_path), 'cnf_sha256': digest(cnf_path),
              'variables': cnf.nv, 'clauses': len(cnf.clauses), 'controls': control,
              'domain_sha256': hashlib.sha256(json.dumps(exact_domain, sort_keys=True,
                                                        separators=(',', ':')).encode()).hexdigest(),
              'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in
                                ('complement_rook_row_projection.py',
                                 'complement_rook_a_incidence.py',
                                 'complement_rook_a_incidence_census.py')},
              'build_seconds': time.monotonic()-started}
    manifest_path.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2), flush=True)
    return record


def inspect_point(positive, orbit):
    rows, gram, triples, signatures, needs, source, neighbors, zero, one, pairs, packing = domain(orbit)
    selected = [s for s in range(252) if s+1 in positive]
    assert source in selected and len(selected) == 72
    assert all(sum(i in signatures[s] and j in signatures[s] for s in selected) == gram[i][j]
               for i in range(27) for j in range(27))
    chosen = [w for offset, w in enumerate(neighbors, 253) if offset in positive]
    matching_offset = 253+len(neighbors)
    matched = [pair for offset, pair in enumerate(pairs, matching_offset) if offset in positive]
    assert len(chosen) == 11 and set(chosen) <= set(selected)-{source}
    assert all(sum(i in signatures[w] for w in chosen) == needs[source][i] for i in range(27))
    assert len(set(chosen) & set(one)) == 3 and len(set(chosen) & set(zero)) == 8
    assert not any(v in chosen and w in chosen for v, w in packing)
    assert len(matched) == 4
    degrees = Counter(v for pair in matched for v in pair)
    assert all(degrees[v] == int(v in chosen) for v in zero)
    assert all(not set(signatures[v]) & set(signatures[w])
               and eligible(v, w, signatures, needs) for v, w in matched)
    # Check the resulting99-point partial graph independently of auxiliary
    # SAT variables. The core and source degrees are complete; other
    # exterior vertices still have unspecified edges.
    index = {s: 27+i for i, s in enumerate(selected)}
    adjacency = rows[:]+[0]*72
    for s in selected:
        for i in signatures[s]:
            adjacency[index[s]] |= 1 << i
            adjacency[i] |= 1 << index[s]
    for v, w in [(source, w) for w in chosen]+matched:
        adjacency[index[v]] |= 1 << index[w]
        adjacency[index[w]] |= 1 << index[v]
    assert all(adjacency[i].bit_count() == 14 for i in range(27))
    assert adjacency[index[source]].bit_count() == 14
    assert all(row.bit_count() <= 14 for row in adjacency)
    assert all((adjacency[i] & adjacency[j]).bit_count()+int(adjacency[i] >> j & 1) <= 2
               for i, j in combinations(range(99), 2))
    source_neighbors = [j for j in range(99) if adjacency[index[source]] >> j & 1]
    assert all(sum(adjacency[v] >> w & 1 for w in source_neighbors) == 1 for v in source_neighbors)
    parameter_a = sum((p//3 == t//3 or p % 3 == t % 3)
                      and (q//3 == t//3 or q % 3 == t % 3)
                      for p, q, t in (triples[s] for s in selected))
    return {'status': 'exact72-column and completed-source-neighborhood partial witness',
            'selected_signature_indices': selected,
            'selected_signature_triples': [triples[s] for s in selected],
            'source_signature_index': source, 'source_triple': triples[source],
            'neighbor_signature_indices': chosen, 'matching_signature_pairs': matched,
            'parameter_a': parameter_a, 'all729_gram_entries_checked': True,
            'all4851_partial_graph_caps_checked': True,
            'source_neighborhood_is_seven_disjoint_edges': True,
            'full99_vertex_graph_completed': False}


def solve(manifest_path, seconds, proof_path, output):
    model = json.loads(manifest_path.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert digest(Path(model['cnf_path'])) == model['cnf_sha256']
    result = {'status': 'running', 'orbit': model['orbit'], 'source_triple': model['source_triple'],
              'manifest_path': str(manifest_path), 'manifest_sha256': digest(manifest_path),
              'cnf_sha256': model['cnf_sha256'], 'requested_seconds': seconds,
              'budget_includes_parse_and_bootstrap': True, 'proof_enabled': True,
              'solver': 'glucose4', 'partial_witness': None}
    output.write_text(json.dumps(result, indent=2)+'\n')
    started = time.monotonic()
    cnf = CNF(from_file=model['cnf_path'])
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
        del cnf
        gc.collect()
        remaining = seconds-(time.monotonic()-started)
        if remaining > 0:
            timer = Timer(remaining, solver.interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
        else:
            answer = None
        result['solve_return_seconds'] = time.monotonic()-started
        result['solver_statistics'] = solver.accum_stats()
        if answer is None:
            result['status'] = 'UNKNOWN at budget; source orbit unresolved'
        elif answer is False:
            proof = solver.get_proof()
            assert proof is not None
            proof_path.write_text('\n'.join(proof)+'\n')
            result.update(status='solver UNSAT; saved proof awaits independent verification',
                          proof_path=str(proof_path), proof_sha256=digest(proof_path))
        else:
            witness = inspect_point({v for v in solver.get_model() if v > 0}, model['orbit'])
            result.update(status='SAT partial witness verified exactly; no complete graph claim',
                          partial_witness=witness)
    result['total_seconds'] = time.monotonic()-started
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'partial_witness'}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    builder = commands.add_parser('build')
    builder.add_argument('--orbit', type=int, choices=range(3), required=True)
    builder.add_argument('--cnf', type=Path, required=True)
    builder.add_argument('--manifest', type=Path, required=True)
    runner = commands.add_parser('solve')
    runner.add_argument('--manifest', type=Path, required=True)
    runner.add_argument('--seconds', type=float, default=30)
    runner.add_argument('--proof', type=Path, required=True)
    runner.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'build':
        build(args.orbit, args.cnf, args.manifest)
    else:
        assert 0 < args.seconds <= 30
        solve(args.manifest, args.seconds, args.proof, args.output)
