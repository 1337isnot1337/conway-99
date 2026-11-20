"""Complete independent-edge models for all four a=2 incidence orbits.

The exact selector census is replayed before construction. Every mixed,
degree, and exterior common-neighbor cap is imposed. No graph symmetry
or fractional edge assignment is used.
"""

import argparse
import gc
import hashlib
import json
from pathlib import Path
from threading import Timer
from types import SimpleNamespace
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

import complement_rook_a_incidence as incidence
import complement_rook_a_incidence_census as census
from two_rook_a0_fixed_completion import cap_plan, inspect, digest
from two_rook_iso_completion import allowed_edges, check_incidence
from two_rook_iso_pair_full_caps import forward_controls


def domain(census_path, case_index, census_cnf=None, census_proof=None, checker=None, replay_log=None):
    record = json.loads(census_path.read_text())
    if checker is not None:
        census.replay(SimpleNamespace(output=census_path, cnf=census_cnf, proof=census_proof,
                                     drat_trim=checker, drat_log=replay_log))
    assert record['status'] == 'complete incidence census; final blocked formula DRAT verified'
    assert record['labelled_designs'] == 576 and len(record['orbits']) == 4
    assert 0 <= case_index < 4
    saved = record['orbits'][case_index]
    selected = saved['representative']
    incidence.check_witness(selected, 2)
    assert saved['orbit_size'] == 144
    rows, _, triples, full_signatures, _, _ = incidence.domain()
    signatures = [full_signatures[s] for s in selected]
    design = [triples[s] for s in selected]
    assert len(signatures) == len(set(signatures)) == 72 and signatures == sorted(signatures)
    need = check_incidence(rows, signatures)
    dense = [[2-sum(((row >> j) & 1)+int(i == j) for j in signature)
              for i, row in enumerate(rows)]+[11] for signature in signatures]
    assert need == dense and all(sum(values[:-1]) == 33 for values in need)
    edges = allowed_edges(signatures, need)
    signature_hash = hashlib.sha256(json.dumps(signatures, separators=(',', ':')).encode()).hexdigest()
    return rows, signatures, need, edges, {
        'case_index': case_index, 'equivalent_designs': 144,
        'selected_signature_sha256': signature_hash,
        'signature_indices': selected, 'coordinate_triples': design,
    }


def build(args):
    started = time.monotonic()
    controls = forward_controls()
    rows, signatures, need, edges, detail = domain(
        args.census, args.case, args.census_cnf, args.census_proof,
        args.drat_trim, args.manifest.with_name(args.manifest.stem+'-census-replay.log'))
    pool, cnf = IDPool(), CNF()
    variables = {edge: pool.id(('edge', *edge)) for edge in edges}
    incident = [[] for _ in signatures]
    for (a, b), variable in variables.items():
        incident[a].append((b, variable))
        incident[b].append((a, variable))
    counts = set()
    impossible = []
    for t in range(72):
        for i in range(28):
            literals = [variable for s, variable in incident[t]
                        if i == 27 or i in signatures[s]]
            key = (tuple(literals), need[t][i])
            if key in counts:
                continue
            counts.add(key)
            assert need[t][i] >= 0
            if need[t][i] > len(literals):
                cnf.append([])
                impossible.append([t, i, need[t][i], len(literals)])
            else:
                cnf.extend(CardEnc.equals(literals, need[t][i], vpool=pool,
                                         encoding=EncType.seqcounter).clauses)
    base_variables, base_clauses = cnf.nv, len(cnf.clauses)
    plan = cap_plan(variables, signatures)
    packing = {tuple(sorted((-first, -second)))
               for _, _, overlap, _, paths in plan if overlap == 2 for _, first, second in paths}
    cnf.extend([list(clause) for clause in sorted(packing)])
    paths_added = 0
    for a, b, overlap, direct, paths in plan:
        if overlap == 2:
            continue
        terms = [] if direct is None else [direct]
        for w, first, second in paths:
            path = pool.id(('path', a, b, w))
            cnf.append([-first, -second, path])
            terms.append(path)
            paths_added += 1
        if len(terms) > 2-overlap:
            cnf.extend(CardEnc.atmost(terms, 2-overlap, vpool=pool,
                                     encoding=EncType.seqcounter).clauses)
    args.cnf.parent.mkdir(parents=True, exist_ok=True)
    cnf.to_file(args.cnf)
    sources = ['complement_rook_a2_fixed_completion.py', 'complement_rook_a_incidence.py',
               'complement_rook_a_incidence_census.py', 'two_rook_a0_fixed_completion.py',
               'two_rook_iso_completion.py', 'two_rook_iso_pair_full_caps.py']
    exact_domain = {'core_rows': rows, 'signatures': signatures, 'mixed_need': need,
                    'edge_variables': [[a, b, value] for (a, b), value in variables.items()]}
    domain_hash = hashlib.sha256(json.dumps(exact_domain, sort_keys=True, separators=(',', ':')).encode()).hexdigest()
    record = {'status': 'complete a=2 fixed-incidence model built; not yet solved', **detail,
              'census_path': str(args.census), 'census_sha256': digest(args.census),
              'census_cnf': str(args.census_cnf), 'census_cnf_sha256': digest(args.census_cnf),
              'census_proof': str(args.census_proof), 'census_proof_sha256': digest(args.census_proof),
              'source_hashes': {name: digest(Path(__file__).with_name(name)) for name in sources},
              'cnf_path': str(args.cnf), 'cnf_sha256': digest(args.cnf), 'domain_sha256': domain_hash,
              'core_vertices': 27, 'outside_vertices': 72, 'edge_variables': len(variables),
              'distinct_mixed_and_degree_counts': len(counts), 'impossible_count_rows': impossible,
              'base_variables': base_variables, 'base_clauses': base_clauses,
              'outside_pairs': len(plan), 'duplicate_zero_caps': 36,
              'packing_clauses': len(packing), 'path_variables': paths_added,
              'variables': cnf.nv, 'clauses': len(cnf.clauses), 'symmetry_clauses': 0,
              'orbit_equalities': 0, 'lazy_cuts': 0, 'full_outside_caps': True,
              'controls': controls, 'build_seconds': time.monotonic()-started}
    args.manifest.write_text(json.dumps(record, indent=2)+'\n')
    print(json.dumps({k: v for k, v in record.items() if k not in
                      ('source_hashes', 'signature_indices', 'coordinate_triples')}, indent=2), flush=True)
    return record


def solve(args):
    model = json.loads(args.manifest.read_text())
    for name, expected in model['source_hashes'].items():
        assert digest(Path(__file__).with_name(name)) == expected
    for path_key, hash_key in (('cnf_path', 'cnf_sha256'), ('census_path', 'census_sha256'),
                               ('census_cnf', 'census_cnf_sha256'), ('census_proof', 'census_proof_sha256')):
        assert digest(Path(model[path_key])) == model[hash_key]
    result = {'status': 'running', 'case_index': model['case_index'],
              'equivalent_designs': 144, 'manifest_path': str(args.manifest),
              'manifest_sha256': digest(args.manifest), 'cnf_path': model['cnf_path'],
              'cnf_sha256': model['cnf_sha256'], 'source_sha256': digest(Path(__file__)),
              'solver': 'glucose4', 'proof_enabled': True, 'full_outside_caps': True,
              'requested_wall_budget_seconds': args.seconds,
              'budget_includes_cnf_parse_and_solver_bootstrap': True,
              'symmetry_clauses': 0, 'lazy_cuts': 0, 'completed_witness': None}
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    started = time.monotonic()
    cnf = CNF(from_file=model['cnf_path'])
    assert (cnf.nv, len(cnf.clauses)) == (model['variables'], model['clauses'])
    with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
        del cnf
        gc.collect()
        remaining = args.seconds-(time.monotonic()-started)
        print(json.dumps({'case': model['case_index'], 'solver_ready_seconds': time.monotonic()-started,
                          'remaining_seconds': max(0, remaining)}), flush=True)
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
            result['status'] = 'UNKNOWN at wall budget; incidence orbit unresolved'
        elif answer is False:
            proof = solver.get_proof()
            assert proof is not None
            with args.proof.open('w') as stream:
                for line in proof:
                    stream.write(line+'\n')
            result.update(status='solver UNSAT; proof saved, independent verification pending',
                          proof_path=str(args.proof), proof_sha256=digest(args.proof), proof_lines=len(proof))
        else:
            rows, signatures, _, edges, detail = domain(Path(model['census_path']), model['case_index'])
            assert detail['selected_signature_sha256'] == model['selected_signature_sha256']
            result.update(status='exact99-vertex SRG candidate; independent validation required',
                          completed_witness=inspect({v for v in solver.get_model() if v > 0}, rows, signatures, edges))
    result['total_seconds'] = time.monotonic()-started
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({k: v for k, v in result.items() if k != 'completed_witness'}, indent=2), flush=True)
    return result


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    builder = commands.add_parser('build')
    builder.add_argument('--census', type=Path, required=True)
    builder.add_argument('--census-cnf', type=Path, required=True)
    builder.add_argument('--census-proof', type=Path, required=True)
    builder.add_argument('--drat-trim', type=Path, required=True)
    builder.add_argument('--case', type=int, choices=range(4), required=True)
    builder.add_argument('--cnf', type=Path, required=True)
    builder.add_argument('--manifest', type=Path, required=True)
    runner = commands.add_parser('solve')
    runner.add_argument('--manifest', type=Path, required=True)
    runner.add_argument('--seconds', type=float, default=120)
    runner.add_argument('--proof', type=Path, required=True)
    runner.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.command == 'build':
        build(args)
    else:
        assert 0 < args.seconds <= 120
        solve(args)
