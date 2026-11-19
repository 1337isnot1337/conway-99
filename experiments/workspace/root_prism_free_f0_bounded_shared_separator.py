"""Bounded mixed-row potential search for one frozen shared-box UNKNOWN.

This is a different LP from the original feasibility query. It maximizes
the support-function gap with potentials in[-1,1] and positive capacities
in[0,6]. A numerical potential is only a proposal. Any separator must
pass exact integer arithmetic; every returned potential is saved even
when the optimizer status is nonoptimal. No dual ray is requested.
"""

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
import json
from math import gcd, isfinite
from pathlib import Path
import random
import time

import root_prism_free_f0_exterior_row_box_separation as box
import root_prism_free_f0_shared_deficit_separator as shared
import root_prism_free_f0_lazy_continuation_transcript_bundle as bundle


ROOT, LOGS = box.ROOT, box.LOGS
digest, canonical, portable, save = box.digest, box.canonical, box.portable, box.save
DEPENDENCIES = {
    'root_prism_free_f0_exterior_row_box_separation.py': '60366da662c74ee8d3ca367dc532c16b652952101fa5725a3248fc5a53a773bd',
    'root_prism_free_f0_shared_deficit_separator.py': '6bc6944ed00713d384251ab54e54684e6f5ea29300f9ff243df5282f522375bf',
    'root_prism_free_f0_lazy_continuation_transcript_bundle.py': '0152cfcc6d2b22be3714bd43a3b643301ec7a7fbf485a6728e66306ca16c10ec'}
RESULT = LOGS/'f0-lazy-continuation-run01/result.json'
RESULT_SHA = '3bb89930202266409acfce6ca52949b5c370928216ce64e9123e22daf5f9e593'
COLD = LOGS/'f0-lazy-continuation-run01-cold-replay.json'
COLD_SHA = '7bd045ab660f3aedd2bd9c514c9e2fa8a91a4f07f415cebba2c133adc73b2330'
TERMINAL_MANIFEST = LOGS/'f0-lazy-continuation-run01-terminal-manifest.json'
TERMINAL_MANIFEST_SHA = 'a71e03191ed2eee685f0992923e84ad6e9900aebfc40c9ad00f29a2d639caa0d'
MAXIMUM_SECONDS = 60


def read(path):
    data = path.read_bytes()
    return json.loads(gzip.decompress(data) if path.suffix == '.gz' else data)


def check_sources():
    for name, expected in DEPENDENCIES.items():
        assert digest(Path(__file__).with_name(name)) == expected
    bundle.verify(True)
    for path, expected in ((RESULT, RESULT_SHA), (COLD, COLD_SHA), (TERMINAL_MANIFEST, TERMINAL_MANIFEST_SHA)):
        assert digest(path) == expected
    for record in read(TERMINAL_MANIFEST)['files']:
        assert digest(ROOT/record['path']) == record['sha256']
    shared.check_sources()


def bound_record(record, key):
    path = ROOT/record[key]
    assert digest(path) == record[key+'_sha256']
    return read(path)


def load_target():
    check_sources()
    triples, targets, neighbors, _, actions, _ = box.load()
    assert len(triples) == len(targets) == 480
    assert all(len(h) == len(set(h)) == 3 for h in triples)
    assert all(len(q) == 18 and sum(q) == 24 and all(type(x) is int and x >= 0 for x in q) for q in targets)
    result = read(RESULT); last = result['iterations'][-1]
    assert last['iteration'] == 16 and result['status'].startswith('UNKNOWN: numerical infeasibility')
    candidate = bound_record(last, 'candidate')
    selected = candidate['selected_signature_ids']
    assert len(selected) == len(set(selected)) == 60 and selected == sorted(selected)
    raw = bound_record(last, 'shared_rows')
    shared.replay(raw, selected, triples, targets, neighbors)
    assert 'numerical_ray_hex' not in raw
    data, original_rows = shared.domain(selected, triples, targets, neighbors)
    assert shared.inventory(data, original_rows) == raw['inventory']
    n = len(data['edge_domain']); assert n == 1220
    # Recheck the entire component Gram and every visible motif conflict.
    domain = read(LOGS/'f0-exterior-row-domains02.json.gz')
    core = domain['component_core_rows']
    gram = [[12*int(i == j)+2-(core[i+3]&core[j+3]).bit_count()-(core[i+3] >> (j+3) & 1)
             for j in range(18)] for i in range(18)]
    assert [[sum(i in triples[a] and j in triples[a] for a in selected) for j in range(18)]
            for i in range(18)] == gram
    assert all(not {a, b} <= set(selected) for a, b in domain['motif_pairs'])
    old = read(LOGS/'f0-first-design-exterior-row-certificate.json.gz')['row_certificate']['transported_cuts']
    assert all(sum(w for b, w in cut['binary_capped_weights'] if b in selected)
               >= 2*int(cut['target_signature'] in selected) for cut in old)
    rows = bound_record(result, 'individual-registry')
    signed = bound_record(result, 'symmetric-registry')
    explanations = bound_record(result, 'explanation-registry')
    assert (len(rows), len(signed), len(explanations)) == (1188, 168, 2448)
    assert all(sum(w for b, w in cut['weights'] if b in selected)
               >= cut['demand']*int(cut['target'] in selected) for cut in rows)
    assert all(sum(c for a, c in cut['signed_coefficients'] if a in selected) <= 0 for cut in signed)
    assert all(any((lit > 0) == (abs(lit)-1 in selected) for lit in record['clause'])
               for record in explanations)
    # Prove degree-row redundancy using the actual matrix supports.
    for a in range(60):
        degree = original_rows[19*a]
        mixed = original_rows[19*a+1:19*a+19]
        assert degree['kind'] == 'degree' and degree['rhs'] == 8
        count = Counter(e for row in mixed for e in row['support'])
        assert count == Counter({e: 3 for e in degree['support']})
        assert sum(row['rhs'] for row in mixed) == 24
    checks = {'all480_signature_weights3_and_target_sums24': True,
        'all60_actual_degree_rows_exactly_one_third_sum_of_mixed_rows': True,
        'all324_component_Gram_entries_checked': True, 'all90_motif_conflicts_checked': True,
        'all1356_registry_inequalities_and2448_primary_explanations_hold': True,
        'candidate_sha256': last['candidate_sha256'], 'unknown_shared_record_sha256': last['shared_rows_sha256'],
        'original_shared_inventory': raw['inventory']}
    return data, original_rows, (triples, targets, neighbors, actions), checks


def model(data):
    h, q, edges = data['design'], data['targets'], data['edge_domain']
    count = len(h); m, n = 18*count, len(edges)
    assert len(q) == count and all(len(x) == 3 for x in h)
    assert all(len(x) == 18 and sum(x) == 24 for x in q)
    rows = []
    for e, (a, b) in enumerate(edges):
        assert 0 <= a < count and 0 <= b < count and a != b
        terms = [[18*a+i, 1] for i in h[b]]+[[18*b+i, 1] for i in h[a]]+[[m+e, -1]]
        terms.sort()
        assert len(terms) == len({j for j, _ in terms}) == 7
        rows.append(terms)
    return {'sense': 'minimize', 'variables': m+n, 'potential_variables': m, 'capacity_variables': n,
        'rows': rows, 'row_upper': [0]*n, 'row_lower': 'negative_infinity',
        'column_lower': [-1]*m+[0]*n, 'column_upper': [1]*m+[6]*n,
        'cost': [-value for vector in q for value in vector]+[1]*n,
        'nonzeros': 7*n, 'objective_constant': 0,
        'interpretation': 'minimize negative support gap; all constraints are edge_weight-capacity<=0'}


def exact_gap(data, potentials):
    assert len(potentials) == len(data['design'])
    assert all(len(v) == 18 and all(type(x) is int for x in v) for v in potentials)
    demand = sum(x*y for v, q in zip(potentials, data['targets']) for x, y in zip(v, q))
    weights = [sum(potentials[a][i] for i in data['design'][b])+
               sum(potentials[b][i] for i in data['design'][a]) for a, b in data['edge_domain']]
    capacity = sum(max(0, weight) for weight in weights)
    return {'integer_demand': demand, 'integer_positive_edge_capacity': capacity,
            'integer_support_gap': demand-capacity,
            'positive_edges': sum(weight > 0 for weight in weights),
            'integer_edge_weights_sha256': hashlib.sha256(canonical(weights)).hexdigest(),
            'maximum_absolute_potential': max((abs(x) for v in potentials for x in v), default=0)}


def check_normalized_point(data, lp, numerators, denominator):
    assert type(denominator) is int and denominator > 0
    assert all(abs(x) <= denominator for v in numerators for x in v)
    weights = [sum(numerators[a][i] for i in data['design'][b])+
               sum(numerators[b][i] for i in data['design'][a]) for a, b in data['edge_domain']]
    vector = [x for v in numerators for x in v]+[max(0, weight) for weight in weights]
    assert len(vector) == lp['variables']
    assert all(lo*denominator <= x <= hi*denominator
               for lo, x, hi in zip(lp['column_lower'], vector, lp['column_upper']))
    assert all(sum(coefficient*vector[j] for j, coefficient in row) <= 0 for row in lp['rows'])
    check = exact_gap(data, numerators)
    cost = sum(c*x for c, x in zip(lp['cost'], vector))
    assert cost == -check['integer_support_gap']
    return {'denominator': denominator, 'exact_cost_numerator': cost,
            'all_normalized_bounds_and_edge_rows_pass': True, **check}


def controls(context):
    triples, targets, neighbors, _ = context
    result = read(RESULT); step = result['iterations'][15]
    known = bound_record(step, 'shared_rows')
    selected = known['selected_signature_ids']
    shared.replay(known, selected, triples, targets, neighbors)
    assert known['exact_fixed_design_infeasibility']
    data, _ = shared.domain(selected, triples, targets, neighbors)
    vector = known['fixed_capacity_potentials']['integer_potentials60_by18']
    denominator = max(abs(x) for v in vector for x in v)
    positive = check_normalized_point(data, model(data), vector, denominator)
    assert positive['integer_support_gap'] > 0 and positive['exact_cost_numerator'] < 0
    # Synthetic exact feasible box: K10 minus a perfect matching is8-regular.
    h = [[a, a+1, a+2] for a in range(10)]
    edges = [[a, b] for a in range(10) for b in range(a)]
    y = [int(a//2 != b//2) for a, b in edges]
    q = [[0]*18 for _ in h]
    degrees = [0]*10
    for (a, b), weight in zip(edges, y):
        degrees[a] += weight; degrees[b] += weight
        for i in h[b]: q[a][i] += weight
        for i in h[a]: q[b][i] += weight
    assert degrees == [8]*10 and all(sum(v) == 24 for v in q)
    toy = {'design': h, 'targets': q, 'edge_domain': edges}
    toy_lp = model(toy)
    rng = random.Random(990214)
    identities = 0
    for _ in range(24):
        v = [[rng.randrange(-3, 4) for _ in range(18)] for _ in h]
        direct = sum(x*z for row, target in zip(v, q) for x, z in zip(row, target))
        edge = [sum(v[a][i] for i in h[b])+sum(v[b][i] for i in h[a]) for a, b in edges]
        assert direct == sum(w*weight for w, weight in zip(edge, y))
        check = check_normalized_point(toy, toy_lp, v, 3)
        assert check['integer_support_gap'] <= 0
        identities += 1
    return {'status': 'PASS: known exact separator, normalized signs/bounds and synthetic feasible-box identities',
        'known_shared_record': step['shared_rows'], 'known_shared_record_sha256': step['shared_rows_sha256'],
        'known_separator': positive, 'known_integer_potentials': vector,
        'synthetic_feasible_box': {'vertices': 10, 'edge_domain': 45, 'selected_edges': sum(y),
            'degree': 8, 'signature_weight': 3, 'exact_potential_identity_controls': identities,
            'toy_is_not_claimed_to_be_a_graph_completion': True},
        'optimizer_or_solver_called': False}


def calculate():
    data, rows, context, checks = load_target()
    lp = model(data)
    assert (lp['variables'], len(lp['rows']), lp['nonzeros']) == (2300, 1220, 8540)
    zero = check_normalized_point(data, lp, [[0]*18 for _ in range(60)], 1)
    assert zero['integer_support_gap'] == 0
    control = controls(context)
    specification = {'data': data, 'bounded_potential_LP': lp}
    summary = {'variables': 2300, 'potential_variables': 1080, 'positive_capacity_variables': 1220,
        'inequality_rows': 1220, 'nonzeros': 8540, 'all_coefficients_integer': True,
        'model_sha256': hashlib.sha256(canonical(specification)).hexdigest(),
        'zero_potential_is_an_exact_feasible_point': True}
    return specification, summary, checks, control, context


def prepare(output):
    assert not output.exists()
    started = time.monotonic()
    spec, summary, checks, control, _ = calculate()
    report = {'status': 'bounded shared separator prepared; no optimizer call',
        'source_sha256': digest(Path(__file__)), 'dependency_source_hashes': DEPENDENCIES,
        'parent_unknown_result_sha256': RESULT_SHA, 'parent_cold_replay_sha256': COLD_SHA,
        'parent_terminal_manifest_sha256': TERMINAL_MANIFEST_SHA,
        'specification': spec, 'model': summary, 'exact_domain_checks': checks, 'controls': control,
        'maximum_query_seconds': MAXIMUM_SECONDS, 'requested_optimizer': 'simplex', 'threads': 1,
        'save_returned_potentials_on_every_status': True,
        'strict_integer_support_gap_required': True, 'getDualRay_not_used': True,
        'original_feasibility_query_repeated': False, 'optimizer_or_solver_called': False,
        'seconds': time.monotonic()-started}
    output.write_bytes(gzip.compress(canonical(report)+b'\n', mtime=0))
    print(json.dumps({k: v for k, v in report.items() if k not in ('specification', 'controls')}, indent=2), flush=True)


def checked_preparation(path):
    check_sources()
    saved = read(path)
    assert saved['source_sha256'] == digest(Path(__file__)) and saved['dependency_source_hashes'] == DEPENDENCIES
    assert saved['parent_unknown_result_sha256'] == RESULT_SHA and saved['parent_cold_replay_sha256'] == COLD_SHA
    assert saved['maximum_query_seconds'] == MAXIMUM_SECONDS
    assert hashlib.sha256(canonical(saved['specification'])).hexdigest() == saved['model']['model_sha256']
    return saved


def proposals(data, numerical):
    assert len(numerical) == 1080 and all(isfinite(value) for value in numerical)
    rational = [Fraction(value) for value in numerical]
    maximum_denominator = max(value.denominator for value in rational)
    scales = list(dict.fromkeys([1, 2, 3, 4, 6, 12, 24, 60, 120, 720, 4096, maximum_denominator]))
    trials = []; accepted = None
    for scale in scales:
        flat = [round(scale*value) for value in rational]
        divisor = gcd(*(abs(x) for x in flat)) or 1
        flat = [x//divisor for x in flat]
        vector = [flat[18*a:18*a+18] for a in range(60)]
        check = exact_gap(data, vector)
        trial = {'scale': scale, 'removed_integer_gcd': divisor, **check}
        trials.append(trial)
        if check['integer_support_gap'] > 0:
            accepted = {'integer_potentials60_by18': vector, 'trial_index': len(trials)-1, 'check': check}
            break
    return trials, accepted


def query(preparation, output, seconds):
    assert not output.exists() and 0 < seconds <= MAXIMUM_SECONDS
    started = time.monotonic()
    report = {'status': 'RUNNING: one bounded potential separator',
        'source_sha256': digest(Path(__file__)), 'preparation': portable(preparation),
        'preparation_sha256': digest(preparation), 'requested_seconds_including_setup': seconds,
        'optimizer_calls': 0, 'exact_separator': False, 'exact_shared_box_feasibility': False,
        'original_feasibility_query_repeated': False, 'frozen_parent_UNKNOWN_unchanged': True,
        'whole_component_excluded': False, 'full_graph_constructed': False}
    save(output, report)
    try:
        saved = checked_preparation(preparation)
        spec = saved['specification']; data, lp = spec['data'], spec['bounded_potential_LP']
        report['model_sha256'] = saved['model']['model_sha256']
        import highspy
        import numpy as np
        from scipy import sparse
        rr, cc, values = [], [], []
        for i, row in enumerate(lp['rows']):
            for j, coefficient in row:
                rr.append(i); cc.append(j); values.append(coefficient)
        matrix = sparse.csc_matrix((np.asarray(values, dtype=float), (rr, cc)),
                                  shape=(len(lp['rows']), lp['variables']))
        assert matrix.nnz == lp['nonzeros']
        problem = highspy.HighsLp()
        problem.num_col_, problem.num_row_ = lp['variables'], len(lp['rows'])
        problem.col_cost_ = np.asarray(lp['cost'], dtype=float)
        problem.col_lower_, problem.col_upper_ = np.asarray(lp['column_lower'], dtype=float), np.asarray(lp['column_upper'], dtype=float)
        problem.row_lower_ = np.full(len(lp['rows']), -highspy.kHighsInf)
        problem.row_upper_ = np.zeros(len(lp['rows']))
        problem.a_matrix_.format_ = highspy.MatrixFormat.kColwise
        problem.a_matrix_.start_, problem.a_matrix_.index_, problem.a_matrix_.value_ = matrix.indptr, matrix.indices, matrix.data
        remaining = seconds-(time.monotonic()-started)
        if remaining <= 0:
            report['status'] = 'UNKNOWN: setup exhausted budget; no query'
        else:
            solver = highspy.Highs()
            for name, value in [('output_flag', False), ('threads', 1), ('solver', 'simplex'),
                                ('presolve', 'on'), ('time_limit', remaining)]:
                assert solver.setOptionValue(name, value) == highspy.HighsStatus.kOk
            assert solver.passModel(problem) == highspy.HighsStatus.kOk
            report.update(optimizer_calls=1, requested_optimizer_seconds=remaining)
            save(output, report)
            solver.run()
            report['numerical_status'] = str(solver.getModelStatus())
            report['optimizer_return_seconds'] = time.monotonic()-started
            solution = solver.getSolution()
            numeric = list(map(float, solution.col_value))
            report['returned_solution_length'] = len(numeric)
            report['returned_solution_value_valid'] = bool(getattr(solution, 'value_valid', False))
            report['returned_all_columns_hex'] = [x.hex() for x in numeric]
            # Persist the actual proposal before any reconstruction, on every status.
            report['numerical_potential_hex'] = [x.hex() for x in numeric[:1080]]
            save(output, report)
            if len(numeric) != lp['variables'] or not all(isfinite(x) for x in numeric[:1080]):
                report['status'] = 'UNKNOWN: no complete finite potential proposal'
            else:
                report['numerical_cost_hex'] = sum(c*x for c, x in zip(lp['cost'], numeric)).hex()
                trials, accepted = proposals(data, numeric[:1080])
                report['exact_integer_trials'] = trials
                if accepted is None:
                    report['status'] = 'UNKNOWN: no strict exact support gap from saved potential'
                else:
                    report.update(status='EXACT INTEGER SHARED SUPPORT SEPARATOR', exact_separator=True,
                                  certificate=accepted, validity_independent_of_optimizer_status=True)
    except Exception as error:
        report.update(status='ERROR: stopped without unchecked conclusion', error_type=type(error).__name__, error_message=str(error))
        raise
    finally:
        report['elapsed_seconds'] = time.monotonic()-started
        report['cooperative_budget_overrun_seconds'] = max(0, report['elapsed_seconds']-seconds)
        save(output, report)
    print(json.dumps({k: v for k, v in report.items() if k not in
        ('returned_all_columns_hex', 'numerical_potential_hex', 'certificate')}, indent=2), flush=True)


def reconstruct(preparation, result_path=None):
    saved = checked_preparation(preparation)
    spec, summary, checks, control, context = calculate()
    assert spec == saved['specification'] and summary == saved['model']
    assert checks == saved['exact_domain_checks'] and control == saved['controls']
    report = {'status': 'PASS: cold bounded-potential model, degree redundancy and controls',
        'source_sha256': digest(Path(__file__)), 'preparation_sha256': digest(preparation),
        'model_sha256': summary['model_sha256'], 'optimizer_or_solver_called': False}
    if result_path is None:
        return report, None
    result = read(result_path)
    assert result['source_sha256'] == digest(Path(__file__)) and result['preparation_sha256'] == digest(preparation)
    assert not result['status'].startswith(('RUNNING:', 'ERROR:'))
    assert result['optimizer_calls'] in (0, 1) and not result['original_feasibility_query_repeated']
    assert result['model_sha256'] == summary['model_sha256']
    if 'exact_integer_trials' in result:
        numeric = [float.fromhex(x) for x in result['numerical_potential_hex']]
        assert result['returned_all_columns_hex'][:1080] == result['numerical_potential_hex']
        trials, accepted = proposals(spec['data'], numeric)
        assert trials == result['exact_integer_trials']
        assert bool(accepted) == result['exact_separator']
        if accepted is not None:
            assert accepted == result['certificate'] and accepted['check']['integer_support_gap'] > 0
    else:
        assert not result['exact_separator']
    report.update(result_sha256=digest(result_path), exact_separator=result['exact_separator'],
                  exact_shared_box_feasibility=False, original_UNKNOWN_preserved=True)
    lifted = None
    if result['exact_separator']:
        triples, targets, neighbors, actions = context
        vector = result['certificate']['integer_potentials60_by18']
        lifted = shared.lift(spec['data']['selected_signature_ids'], vector, triples, targets, neighbors, actions)
        assert lifted['raw_gap'] == result['certificate']['check']['integer_support_gap']
        report['status'] = 'PASS: exact shared support gap and all12 universal selector transports'
        report['exact_support_gap'] = lifted['raw_gap']
    return report, lifted


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    prep = commands.add_parser('prepare'); prep.add_argument('--output', type=Path, required=True)
    execute = commands.add_parser('query')
    execute.add_argument('--preparation', type=Path, required=True); execute.add_argument('--output', type=Path, required=True)
    execute.add_argument('--seconds', type=float, default=60)
    check = commands.add_parser('replay')
    check.add_argument('--preparation', type=Path, required=True); check.add_argument('--result', type=Path)
    check.add_argument('--output', type=Path, required=True); check.add_argument('--lift-output', type=Path)
    args = parser.parse_args()
    if args.command == 'prepare':
        prepare(args.output.resolve())
    elif args.command == 'query':
        query(args.preparation.resolve(), args.output.resolve(), args.seconds)
    else:
        assert not args.output.exists()
        report, lifted = reconstruct(args.preparation.resolve(), args.result.resolve() if args.result else None)
        if lifted is not None:
            assert args.lift_output is not None and not args.lift_output.exists()
            save(args.lift_output, lifted)
            report.update(lift=portable(args.lift_output), lift_sha256=digest(args.lift_output))
        else:
            assert args.lift_output is None
        save(args.output, report); print(json.dumps(report, indent=2), flush=True)
