"""Two complete source rows for the forced complementary-rook RS pair(0,4).

All21 tip pairs are covered by explicit core transports. A graph need not
have any automorphism. The two selected sources share exactly two core
neighbors, so their exterior neighborhoods are disjoint.
"""

import argparse
from collections import Counter
import gc
import hashlib
from itertools import combinations, permutations, product
import json
from pathlib import Path
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

import complement_rook_a_incidence as incidence
from complement_rook_row_projection import controls, digest, eligible, matching_rows


def coverage():
    rows, gram, triples, signatures, _, _ = incidence.domain()
    index = {triple: i for i, triple in enumerate(triples)}
    tips = [t for t in range(9) if (0, 4, t) in index]
    assert tips == [1, 2, 3, 5, 6, 7, 8] and gram[0][13] == 2
    fiber = {index[0, 4, t] for t in tips}
    stabilizer = []
    for rp, cp, transpose, swap in product(permutations(range(3)), permutations(range(3)), (0, 1), (0, 1)):
        points = [3*rp[p % 3]+cp[p//3] if transpose else 3*rp[p//3]+cp[p % 3] for p in range(9)]
        image_pair = (points[4], points[0]) if swap else (points[0], points[4])
        if image_pair != (0, 4):
            continue
        core = [9*(1-a if swap and a < 2 else a)+points[p] for a in range(3) for p in range(9)]
        assert sorted(core) == list(range(27))
        assert all(((rows[i] >> j) & 1) == ((rows[core[i]] >> core[j]) & 1)
                   and gram[i][j] == gram[core[i]][core[j]] for i in range(27) for j in range(27))
        image = [index[(points[q], points[p], points[t]) if swap else
                       (points[p], points[q], points[t])] for p, q, t in triples]
        assert sorted(image) == list(range(252)) and {image[s] for s in fiber} == fiber
        assert all(tuple(sorted(core[i] for i in signatures[s])) == signatures[image[s]] for s in range(252))
        stabilizer.append({'point_permutation': points, 'swap_first_two_bases': bool(swap),
                           'core_permutation': core, 'signature_permutation': image})
    stabilizer.sort(key=lambda g: g['core_permutation'])
    assert len(stabilizer) == 4
    group = {tuple(g['core_permutation']) for g in stabilizer}
    assert all(tuple(g[h[i]] for i in range(27)) in group for g in group for h in group)
    remaining = set(combinations(tips, 2))
    cases = []
    while remaining:
        representative = min(remaining)
        transports = {}
        for gi, g in enumerate(stabilizer):
            mapped = [g['point_permutation'][t] for t in representative]
            pair = tuple(sorted(mapped))
            transports.setdefault(pair, {'tips': list(pair), 'stabilizer_index': gi,
                                         'row_order': [pair.index(t) for t in mapped]})
        members = sorted(transports)
        assert set(members) <= remaining
        remaining.difference_update(members)
        cases.append({'representative_tips': list(representative), 'orbit_size': len(members),
                      'members': [transports[pair] for pair in members]})
    assert len(cases) == 8 and sum(case['orbit_size'] for case in cases) == 21
    assert sorted(case['orbit_size'] for case in cases) == [1, 2, 2, 2, 2, 4, 4, 4]
    return {'status': 'all21 forced tip pairs covered by8 explicitly transported cases',
            'fixed_RS_pair': [0, 4], 'RS_Gram_quota': 2, 'allowed_tips': tips,
            'stabilizer_order': 4, 'stabilizer': stabilizer, 'cases': cases,
            'graph_automorphism_assumption': False,
            'source_sha256': digest(Path(__file__))}


def domain(tips):
    rows, gram, triples, signatures, _, _ = incidence.domain()
    index = {triple: i for i, triple in enumerate(triples)}
    sources = [index[0, 4, t] for t in tips]
    assert len(sources) == 2 and len(set(sources)) == 2
    needs = [[2-sum(((rows[i] >> j) & 1)+int(i == j) for j in sites)
              for i in range(27)] for sites in signatures]
    assert all(min(need) >= 0 and sum(need) == 33 for need in needs)
    assert len(set(signatures[sources[0]]) & set(signatures[sources[1]])) == 2
    assert not eligible(*sources, signatures, needs)
    systems = []
    for source in sources:
        neighbors = [w for w in range(252) if w != source and eligible(source, w, signatures, needs)]
        assert not set(sources) & set(neighbors)
        zero = [w for w in neighbors if not set(signatures[w]) & set(signatures[source])]
        one = [w for w in neighbors if w not in zero]
        pairs = [(v, w) for v, w in combinations(zero, 2)
                 if not set(signatures[v]) & set(signatures[w])
                 and eligible(v, w, signatures, needs)]
        packing = [(v, w) for v, w in combinations(neighbors, 2)
                   if len(set(signatures[v]) & set(signatures[w])) >= 2]
        assert all(needs[source][i] == 1 for i in signatures[source])
        systems.append({'source': source, 'neighbors': neighbors, 'zero': zero,
                        'one': one, 'matching_pairs': pairs, 'packing_pairs': packing})
    primary_edges = [tuple(sorted((system['source'], w))) for system in systems for w in system['neighbors']]
    assert len(primary_edges) == len(set(primary_edges))
    assert all(pair not in set(primary_edges) for system in systems for pair in system['matching_pairs'])
    common_candidates = sorted(set(systems[0]['neighbors']) & set(systems[1]['neighbors']))
    return rows, gram, triples, signatures, needs, sources, systems, common_candidates


def copy_controls():
    possible = set()
    admitted = 0
    for ms, mt, su, sv, tu, tv in product((0, 1), repeat=6):
        if ms > min(su, sv) or mt > min(tu, tv) or su+tu > 1 or sv+tv > 1:
            continue
        admitted += 1
        assert not(ms and mt)
        possible.add((ms, mt))
    assert possible == {(0, 0), (1, 0), (0, 1)}
    return {'boolean_cases': 64, 'admitted_cases': admitted,
            'active_matching_copies_cannot_conflict': True}


def build(case_index, coverage_path, cnf_path, manifest_path):
    started = time.monotonic()
    certificate = json.loads(coverage_path.read_text())
    assert certificate == coverage()
    case = certificate['cases'][case_index]
    rows, gram, triples, signatures, needs, sources, systems, common = domain(case['representative_tips'])
    control = {'matching': controls(), 'matching_copy': copy_controls()}
    pool, cnf = IDPool(), CNF()
    selected = {s: pool.id(('select', s)) for s in range(252)}
    neighbor = [{w: pool.id(('neighbor', j, w)) for w in system['neighbors']}
                for j, system in enumerate(systems)]
    pairing = [{pair: pool.id(('pairing', j, *pair)) for pair in system['matching_pairs']}
               for j, system in enumerate(systems)]
    for source in sources:
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
    for j, system in enumerate(systems):
        source = system['source']
        for w, variable in neighbor[j].items():
            cnf.append([-variable, selected[w]])
        for i in range(27):
            literals = [variable for w, variable in neighbor[j].items() if i in signatures[w]]
            assert needs[source][i] <= len(literals)
            cnf.extend(CardEnc.equals(literals, needs[source][i], vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
        for key, target in (('neighbors', 11), ('zero', 8), ('one', 3)):
            cnf.extend(CardEnc.equals([neighbor[j][w] for w in system[key]], target, vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
        cnf.extend([[-neighbor[j][v], -neighbor[j][w]] for v, w in system['packing_pairs']])
        matching_rows(cnf, pool, {w: neighbor[j][w] for w in system['zero']}, pairing[j])
    cnf.extend([[-neighbor[0][w], -neighbor[1][w]] for w in common])
    exact_domain = {'core_rows': rows, 'core_gram': gram, 'signatures': signatures,
                    'mixed_demands': needs, 'sources': sources, 'systems': systems,
                    'disjointness_candidates': common, 'selector_variables': list(selected.items()),
                    'neighbor_variables': [list(system.items()) for system in neighbor],
                    'pairing_variables': [[[v, w, var] for (v, w), var in system.items()] for system in pairing]}
    cnf_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    cnf.to_file(cnf_path)
    record = {'status': 'forced duplicate two-row projection built; not yet solved',
              'case_index': case_index, 'representative_tips': case['representative_tips'],
              'covered_tip_pairs': case['orbit_size'], 'source_indices': sources,
              'source_triples': [triples[s] for s in sources],
              'coverage_path': str(coverage_path), 'coverage_sha256': digest(coverage_path),
              'candidate_selectors': 252, 'neighbor_variables': [len(x) for x in neighbor],
              'matching_variables': [len(x) for x in pairing],
              'packing_clauses': [len(x['packing_pairs']) for x in systems],
              'disjointness_clauses': len(common), 'distinct_gram_counts': len(equations),
              'parameter_a_unrestricted': True, 'fixed_incidence_design': False,
              'graph_symmetry_clauses': 0, 'full_exterior_graph': False,
              'cnf_path': str(cnf_path), 'cnf_sha256': digest(cnf_path),
              'variables': cnf.nv, 'clauses': len(cnf.clauses), 'controls': control,
              'domain_sha256': hashlib.sha256(json.dumps(exact_domain, sort_keys=True,
                                                        separators=(',', ':')).encode()).hexdigest(),
              'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in
                                ('complement_rook_duplicate_row_projection.py',
                                 'complement_rook_row_projection.py',
                                 'complement_rook_a_incidence.py',
                                 'complement_rook_a_incidence_census.py')},
              'build_seconds': time.monotonic()-started}
    manifest_path.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps(record, indent=2), flush=True)
    return record


def inspect_point(positive, tips):
    rows, gram, triples, signatures, needs, sources, systems, common = domain(tips)
    pool = IDPool()
    selector = {s: pool.id(('select', s)) for s in range(252)}
    neighbor = [{w: pool.id(('neighbor', j, w)) for w in system['neighbors']}
                for j, system in enumerate(systems)]
    pairing = [{pair: pool.id(('pairing', j, *pair)) for pair in system['matching_pairs']}
               for j, system in enumerate(systems)]
    selected = [s for s, variable in selector.items() if variable in positive]
    assert len(selected) == 72 and set(sources) <= set(selected)
    assert all(sum(i in signatures[s] and j in signatures[s] for s in selected) == gram[i][j]
               for i in range(27) for j in range(27))
    chosen = [[w for w, variable in variables.items() if variable in positive] for variables in neighbor]
    matches = [[pair for pair, variable in variables.items() if variable in positive] for variables in pairing]
    assert not set(chosen[0]) & set(chosen[1])
    for j, system in enumerate(systems):
        assert len(chosen[j]) == 11 and set(chosen[j]) <= set(selected)-set(sources)
        assert all(sum(i in signatures[w] for w in chosen[j]) == needs[sources[j]][i] for i in range(27))
        assert len(set(chosen[j]) & set(system['one'])) == 3
        assert len(set(chosen[j]) & set(system['zero'])) == 8
        assert not any(v in chosen[j] and w in chosen[j] for v, w in system['packing_pairs'])
        assert len(matches[j]) == 4
        degrees = Counter(v for pair in matches[j] for v in pair)
        assert all(degrees[v] == int(v in chosen[j]) for v in system['zero'])
    index = {s: 27+i for i, s in enumerate(selected)}
    adjacency = rows[:]+[0]*72
    for s in selected:
        for i in signatures[s]:
            adjacency[index[s]] |= 1 << i
            adjacency[i] |= 1 << index[s]
    outside_edges = set()
    for j, source in enumerate(sources):
        outside_edges.update(tuple(sorted((source, w))) for w in chosen[j])
        outside_edges.update(matches[j])
    assert len(outside_edges) == 30
    for v, w in outside_edges:
        adjacency[index[v]] |= 1 << index[w]
        adjacency[index[w]] |= 1 << index[v]
    assert all(adjacency[i].bit_count() == 14 for i in range(27))
    assert all(adjacency[index[s]].bit_count() == 14 for s in sources)
    assert all(row.bit_count() <= 14 for row in adjacency)
    assert all((adjacency[i] & adjacency[j]).bit_count()+int(adjacency[i] >> j & 1) <= 2
               for i, j in combinations(range(99), 2))
    for source in sources:
        local = [i for i in range(99) if adjacency[index[source]] >> i & 1]
        assert len(local) == 14 and all(sum(adjacency[v] >> w & 1 for w in local) == 1 for v in local)
    parameter_a = sum((p//3 == t//3 or p % 3 == t % 3)
                      and (q//3 == t//3 or q % 3 == t % 3)
                      for p, q, t in (triples[s] for s in selected))
    return {'status': 'exact incidence and two completed source neighborhoods; partial graph only',
            'selected_signature_indices': selected,
            'selected_signature_triples': [triples[s] for s in selected],
            'source_signature_indices': sources, 'source_triples': [triples[s] for s in sources],
            'neighbor_signature_indices': chosen, 'matching_signature_pairs': matches,
            'parameter_a': parameter_a, 'all729_gram_entries_checked': True,
            'all4851_partial_graph_caps_checked': True,
            'source_neighborhoods_are_disjoint_outside_core': True,
            'full99_vertex_graph_completed': False}


def solve(manifest_path, seconds, proof_path, output):
    model = json.loads(manifest_path.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    assert digest(Path(model['coverage_path'])) == model['coverage_sha256']
    assert digest(Path(model['cnf_path'])) == model['cnf_sha256']
    result = {'status': 'running', 'case_index': model['case_index'],
              'representative_tips': model['representative_tips'],
              'covered_tip_pairs': model['covered_tip_pairs'],
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
            result['status'] = 'UNKNOWN at budget; forced tip-pair orbit unresolved'
        elif answer is False:
            proof = solver.get_proof()
            assert proof is not None
            proof_path.write_text('\n'.join(proof)+'\n')
            result.update(status='solver UNSAT; saved proof awaits independent verification',
                          proof_path=str(proof_path), proof_sha256=digest(proof_path))
        else:
            result.update(status='SAT two-row partial witness verified; no complete graph claim',
                          partial_witness=inspect_point({v for v in solver.get_model() if v > 0}, model['representative_tips']))
    result['total_seconds'] = time.monotonic()-started
    output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'partial_witness'}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    cover = commands.add_parser('coverage')
    cover.add_argument('--output', type=Path, required=True)
    builder = commands.add_parser('build')
    builder.add_argument('--case', type=int, choices=range(8), required=True)
    builder.add_argument('--coverage', type=Path, required=True)
    builder.add_argument('--cnf', type=Path, required=True)
    builder.add_argument('--manifest', type=Path, required=True)
    runner = commands.add_parser('solve')
    runner.add_argument('--manifest', type=Path, required=True)
    runner.add_argument('--seconds', type=float, default=20)
    runner.add_argument('--proof', type=Path, required=True)
    runner.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'coverage':
        record = coverage()
        args.output.write_text(json.dumps(record, indent=2)+'\n')
        print(json.dumps({key: record[key] for key in ('status', 'allowed_tips', 'stabilizer_order', 'cases')}, indent=2))
    elif args.command == 'build':
        build(args.case, args.coverage, args.cnf, args.manifest)
    else:
        assert 0 < args.seconds <= 20
        solve(args.manifest, args.seconds, args.proof, args.output)
