"""Exterior graph constraints for one fixed first-component incidence.

The second eighteen-vertex component and its incidence remain unspecified.
For the saved 18-by-60 incidence H and component adjacency A, the eventual
exterior adjacency D has degree eight and satisfies H D = 2J - H - A H.
Every outside pair also obeys common_D(u,v)+common_H(u,v)+D(u,v)<=2.
This is a necessary partial-completion model, not an SRG construction.
"""

import argparse
from collections import Counter
import gc
import hashlib
from itertools import combinations
import json
from pathlib import Path
import resource
import subprocess
import tempfile
from threading import Timer
import time

from pysat.card import CardEnc, EncType
from pysat.formula import CNF, IDPool
from pysat.solvers import Solver

import root_prism_free_f0_coupling as coupling


ROOT = Path(__file__).resolve().parents[2]


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def portable(path):
    path = Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def save(path, data):
    Path(path).write_text(json.dumps(data, indent=2)+'\n')


def inputs():
    _, domain, selected, _ = coupling.load()
    design = [domain['signature_domain'][i] for i in selected]
    masks = [sum(1 << i for i in triple) for triple in design]
    adjacency = [(row >> 3) & ((1 << 18)-1) for row in domain['core_rows'][3:21]]
    assert len(masks) == len(set(masks)) == 60
    assert all(mask.bit_count() == 3 for mask in masks)
    assert all(row.bit_count() == 3 for row in adjacency)
    targets = [[2-int(mask >> i & 1)-(adjacency[i] & mask).bit_count()
                for i in range(18)] for mask in masks]
    assert all(sum(row) == 24 and all(q in (0, 1, 2) for q in row) for row in targets)
    overlaps = [[(a & b).bit_count() for b in masks] for a in masks]
    assert all(overlaps[u][v] <= 2 for u in range(60) for v in range(u))
    # A proposed edge must fit both endpoint columns of H D, in addition
    # to the adjacent-pair common-neighbor cap.
    edges = [(u, v) for u in range(60) for v in range(u)
             if overlaps[u][v] <= 1
             and all(targets[u][i] > 0 for i in design[v])
             and all(targets[v][i] > 0 for i in design[u])]
    return {'design': design, 'design_source_indices': selected,
            'component_adjacency_rows': adjacency, 'masks': masks,
            'targets': targets, 'overlaps': overlaps, 'edge_domain': edges}


def build(data):
    edges, masks = data['edge_domain'], data['masks']
    variables = {tuple(sorted(edge)): i+1 for i, edge in enumerate(edges)}
    pool = IDPool(start_from=len(edges)+1)
    cnf, counters = CNF(), Counter()

    def edge(u, v):
        return variables.get(tuple(sorted((u, v))))

    def equality(literals, target, kind):
        assert 0 <= target <= len(literals), (kind, target, len(literals))
        clauses = CardEnc.equals(lits=literals, bound=target, vpool=pool,
                                 encoding=EncType.seqcounter).clauses
        cnf.extend(clauses)
        counters[kind+'_rows'] += 1
        counters[kind+'_clauses'] += len(clauses)

    for v in range(60):
        neighbors = [(w, edge(v, w)) for w in range(60) if w != v and edge(v, w)]
        equality([x for _, x in neighbors], 8, 'degree')
        for i in range(18):
            equality([x for w, x in neighbors if masks[w] >> i & 1],
                     data['targets'][v][i], 'mixed_Gram')

    for u, v in combinations(range(60), 2):
        bound = 2-data['overlaps'][u][v]
        both = [(edge(u, w), edge(v, w)) for w in range(60)
                if w not in (u, v) and edge(u, w) and edge(v, w)]
        direct = edge(u, v)
        if bound == 0:
            assert direct is None
            cnf.extend([[-a, -b] for a, b in both])
            counters['zero_capacity_pair_clauses'] += len(both)
        else:
            common = []
            for a, b in both:
                y = pool.id()
                # y is exactly the conjunction of the two edge variables.
                cnf.extend([[-a, -b, y], [a, -y], [b, -y]])
                common.append(y)
            literals = common+([direct] if direct else [])
            clauses = CardEnc.atmost(lits=literals, bound=bound, vpool=pool,
                                     encoding=EncType.seqcounter).clauses
            cnf.extend(clauses)
            counters['common_neighbor_variables'] += len(common)
            counters['positive_capacity_pair_clauses'] += 3*len(common)+len(clauses)
        counters['outside_pair_caps'] += 1
    assert counters['mixed_Gram_rows'] == 1080 and counters['outside_pair_caps'] == 1770
    return cnf, {'primary_variables': len(edges), 'variables': cnf.nv,
                 'clauses': len(cnf.clauses), 'literals': sum(map(len, cnf.clauses)),
                 'constraints': dict(counters)}


def inspect(chosen, data):
    assert chosen == sorted(set(chosen))
    assert all(0 <= i < len(data['edge_domain']) for i in chosen)
    rows = [0]*60
    for index in chosen:
        u, v = data['edge_domain'][index]
        rows[u] |= 1 << v
        rows[v] |= 1 << u
    assert len(chosen) == 240 and all(row.bit_count() == 8 for row in rows)
    masks, adjacency = data['masks'], data['component_adjacency_rows']
    for v in range(60):
        for i in range(18):
            direct = int(masks[v] >> i & 1)
            core_common = (adjacency[i] & masks[v]).bit_count()
            outside_common = sum((rows[v] >> w & 1)*(masks[w] >> i & 1) for w in range(60))
            assert direct+core_common+outside_common == 2
    caps = Counter()
    for u, v in combinations(range(60), 2):
        common = (rows[u] & rows[v]).bit_count()+(masks[u] & masks[v]).bit_count()
        adjacent = rows[u] >> v & 1
        assert common+adjacent <= 2
        caps[(adjacent, common)] += 1
    return {'selected_edge_indices': chosen, 'adjacency_rows': rows,
            'edges': 240, 'all_degrees': 8, 'mixed_equations_checked': 1080,
            'outside_pair_caps_checked': 1770,
            'pair_cap_histogram': {str(k): v for k, v in sorted(caps.items())},
            'second_component_incidence_specified': False,
            'full_graph_constructed': False}


def prepare(model_path, cnf_path):
    assert not model_path.exists() and not cnf_path.exists()
    started = time.monotonic()
    data = inputs()
    cnf, formula = build(data)
    cnf.to_file(cnf_path)
    model = {'status': 'complete fixed-first exterior partial-completion model',
             'source_sha256': digest(__file__),
             'coupling_source_sha256': digest(coupling.__file__),
             'incidence_result_sha256': digest(coupling.RESULT),
             'data': data, 'formula': formula, 'cnf': str(cnf_path.resolve()),
             'cnf_sha256': digest(cnf_path), 'cnf_bytes': cnf_path.stat().st_size,
             'scope': 'one fixed component-zero first incidence; no second incidence fixed',
             'missing_second_shell_vertices': 18, 'full_graph_constructed': False,
             'seconds': time.monotonic()-started}
    save(model_path, model)
    print(json.dumps({k: v for k, v in model.items() if k != 'data'}, indent=2), flush=True)


def checked_model(path):
    model = json.loads(path.read_text())
    assert model['source_sha256'] == digest(__file__)
    assert model['coupling_source_sha256'] == digest(coupling.__file__)
    assert model['incidence_result_sha256'] == digest(coupling.RESULT)
    return model


def read_clauses(path):
    with Path(path).open() as stream:
        for line in stream:
            if line.strip() and line[0] not in 'cp':
                row = list(map(int, line.split()))
                assert row[-1] == 0
                yield row[:-1]


def solve(args):
    assert not args.directory.exists() and 0 < args.seconds <= 60
    args.directory.mkdir(parents=True)
    model = checked_model(args.model)
    assert digest(model['cnf']) == model['cnf_sha256']
    result = {'status': 'running one fixed-first exterior query',
              'source_sha256': digest(__file__), 'model_sha256': digest(args.model),
              'cnf_sha256': model['cnf_sha256'], 'requested_seconds_including_bootstrap': args.seconds,
              'assumptions': [], 'full_graph_constructed': False,
              'whole_component_or_split_case_excluded': False}
    output = args.directory/'result.json'
    save(output, result)
    started = time.monotonic()
    try:
        cnf = CNF(from_file=model['cnf'])
        assert (cnf.nv, len(cnf.clauses)) == (model['formula']['variables'], model['formula']['clauses'])
        with Solver(name='glucose4', bootstrap_with=cnf.clauses, with_proof=True) as solver:
            del cnf
            gc.collect()
            result['bootstrap_seconds'] = time.monotonic()-started
            timer = Timer(max(0.001, args.seconds-result['bootstrap_seconds']), solver.interrupt)
            timer.start()
            try:
                answer = solver.solve_limited(expect_interrupt=True)
            finally:
                timer.cancel()
            result['solver_return_seconds'] = time.monotonic()-started
            result['solver_statistics'] = solver.accum_stats()
            if answer is None:
                result['status'] = 'UNKNOWN; the fixed first design remains unresolved'
            elif answer:
                positive = {v for v in solver.get_model() if v > 0}
                chosen = [i for i in range(model['formula']['primary_variables']) if i+1 in positive]
                result['exterior_candidate'] = inspect(chosen, model['data'])
                result['status'] = 'SAT; exterior partial candidate checked, second shell missing'
            else:
                proof = solver.get_proof()
                assert proof is not None
                result['terminal_empty_clause_appended'] = not proof or proof[-1] != '0'
                if result['terminal_empty_clause_appended']:
                    proof.append('0')
                raw = args.directory/'raw.drat'
                raw.write_text('\n'.join(proof)+'\n')
                result.update(status='solver UNSAT; independent proof check pending',
                              raw_proof=portable(raw), raw_proof_sha256=digest(raw))
        save(output, result)
        if result['status'].startswith('solver UNSAT'):
            retained, trimmed = args.directory/'retained.cnf', args.directory/'retained.drat'
            log = args.directory/'direct-drat.log'
            checked = subprocess.run([str(args.checker), model['cnf'], str(ROOT/result['raw_proof']),
                '-t', '60', '-w', '-c', str(retained), '-l', str(trimmed)],
                capture_output=True, text=True, timeout=65, check=False)
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            inputs = list(read_clauses(retained))
            needed = {tuple(sorted(c)) for c in inputs}
            for clause in read_clauses(model['cnf']):
                needed.discard(tuple(sorted(clause)))
            assert not needed
            result['retained_certificate'] = {'cnf': portable(retained), 'cnf_sha256': digest(retained),
                'proof': portable(trimmed), 'proof_sha256': digest(trimmed), 'input_clauses': len(inputs),
                'checker_log': portable(log), 'checker_log_sha256': digest(log)}
            result['status'] = 'UNSAT with direct DRAT; cold complete rebuild and proof replay pending'
        result['elapsed_seconds'] = time.monotonic()-started
        result['peak_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        save(output, result)
    except Exception as error:
        result.update(status='error; no unchecked exclusion promoted', error=repr(error))
        save(output, result)
        raise
    print(json.dumps({k: v for k, v in result.items() if k != 'exterior_candidate'}, indent=2), flush=True)


def replay(args):
    assert not args.output.exists()
    model = checked_model(args.model)
    data = inputs()
    # JSON changes tuple edge pairs into lists; compare their serialization.
    assert json.loads(json.dumps(data)) == model['data']
    cnf, formula = build(data)
    assert formula == model['formula']
    with tempfile.TemporaryDirectory(prefix='conway-f0-first-exterior-replay-') as directory:
        path = Path(directory)/'rebuilt.cnf'
        cnf.to_file(path)
        assert digest(path) == model['cnf_sha256']
    report = {'status': 'complete domain and CNF rebuild PASS',
              'source_sha256': digest(__file__), 'model_sha256': digest(args.model),
              'cnf_sha256': model['cnf_sha256'], 'full_graph_constructed': False,
              'whole_component_or_split_case_excluded': False}
    if args.result:
        result = json.loads(args.result.read_text())
        assert result['source_sha256'] == digest(__file__)
        assert result['model_sha256'] == digest(args.model)
        assert result['cnf_sha256'] == model['cnf_sha256']
        if result['status'].startswith('SAT;'):
            assert inspect(result['exterior_candidate']['selected_edge_indices'], data) == result['exterior_candidate']
            report['status'] = 'cold full formula and exterior partial candidate replay PASS'
        elif result['status'].startswith('UNSAT with direct DRAT;'):
            certificate = result['retained_certificate']
            retained, proof = ROOT/certificate['cnf'], ROOT/certificate['proof']
            assert digest(retained) == certificate['cnf_sha256'] and digest(proof) == certificate['proof_sha256']
            retained_inputs = list(read_clauses(retained))
            assert len(retained_inputs) == certificate['input_clauses']
            needed = {tuple(sorted(c)) for c in retained_inputs}
            needed.difference_update(tuple(sorted(c)) for c in cnf.clauses)
            assert not needed
            checked = subprocess.run([str(args.checker), str(retained), str(proof), '-t', '60', '-w'],
                                     capture_output=True, text=True, timeout=65, check=False)
            log = args.output.with_suffix('.drat.log')
            log.write_text(checked.stdout+checked.stderr)
            assert checked.returncode == 0 and 's VERIFIED' in checked.stdout
            report.update(status='cold complete domain/CNF rebuild, retained inclusion and DRAT PASS',
                          excluded_scope='one fixed first-component incidence, with second incidence free',
                          retained_input_clauses=len(retained_inputs), checker_log=portable(log), checker_log_sha256=digest(log))
        else:
            assert result['status'].startswith('UNKNOWN;')
            report['status'] = 'cold formula and UNKNOWN binding PASS; no exclusion'
    save(args.output, report)
    print(json.dumps(report, indent=2), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode', choices=['prepare', 'solve', 'replay'])
    parser.add_argument('--model', type=Path, required=True)
    parser.add_argument('--cnf', type=Path)
    parser.add_argument('--directory', type=Path)
    parser.add_argument('--result', type=Path)
    parser.add_argument('--output', type=Path)
    parser.add_argument('--seconds', type=float, default=60)
    parser.add_argument('--checker', type=Path, default=Path('/tmp/conway99-drat-trim/drat-trim'))
    args = parser.parse_args()
    if args.mode == 'prepare':
        assert args.cnf
        prepare(args.model, args.cnf)
    elif args.mode == 'solve':
        assert args.directory
        solve(args)
    else:
        assert args.output
        replay(args)
