"""One bounded60-row box-capacity separation pass on the new incidence.

Each numerical LP proposes a weight vector only. A cut is accepted after
direct integer verification against every eligible signature. Exact row
box witnesses are accepted only after rational reconstruction and full
equality/bound checks. Replay calls no optimizer or SAT solver.
"""

import argparse
from collections import Counter
from fractions import Fraction
import gzip
import hashlib
from itertools import combinations, product
import json
from math import gcd, isfinite, lcm
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
INPUTS = {
    'f0-exterior-row-domains02.json.gz':'665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4',
    'f0-exterior-row-cut-overlay-run01/result.json':'80daa535121c7c6c05b0b3ce90f65085b1e34236d8d53b143fe1e5ec01765bf3',
    'f0-exterior-row-cut-overlay-run01-cold-replay.json':'8a52272bc8ea40f6a79cded78d0b745e1107edcb451e10aa4285621b2d5a1a8e',
    'f0-first-design-exterior-row-certificate.json.gz':'3b5c302f9a9e3bfce6175de7c73cb835cc89f88e63148de15d59085b1da974c0'}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(data):
    return json.dumps(data,sort_keys=True,separators=(',',':')).encode()


def save(path,data):
    temporary = path.with_name(path.name+'.tmp')
    temporary.write_text(json.dumps(data,indent=2)+'\n')
    temporary.replace(path)


def portable(path):
    return str(path.resolve().relative_to(ROOT))


def load():
    loaded = {}
    for name,value in INPUTS.items():
        path = LOGS/name
        assert digest(path) == value
        raw = path.read_bytes()
        loaded[name] = json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
    domain = loaded['f0-exterior-row-domains02.json.gz']
    point = loaded['f0-exterior-row-cut-overlay-run01/result.json']
    cold = loaded['f0-exterior-row-cut-overlay-run01-cold-replay.json']
    assert point['status'].startswith('SAT;') and cold['status'].endswith('replay PASS')
    assert point['model_sha256'] == cold['model_sha256'] and point['cnf_sha256'] == cold['cnf_sha256']
    selected = point['incidence_candidate']['base_incidence_witness']['selected_columns']
    assert selected == sorted(set(selected)) and len(selected) == 60
    core = domain['component_core_rows']
    adjacency = [(row >> 3)&((1 << 18)-1) for row in core[3:21]]
    assert adjacency == domain['component_adjacency_rows']
    gram = [[12*int(i == j)+2-(core[3+i]&core[3+j]).bit_count()-(core[3+i] >> (3+j) & 1)
             for j in range(18)] for i in range(18)]
    triples = []
    for h in combinations(range(18),3):
        if max(sum(i//6 == f for i in h) for f in range(3)) > 2:
            continue
        if any(gram[i][j] == 0 for i,j in combinations(h,2)):
            continue
        if any(sum(int(i == j or adjacency[i] >> j & 1) for j in h) > 2 for i in range(18)):
            continue
        triples.append(list(h))
    assert triples == domain['signature_domain'] and len(triples) == 480
    assert [[sum(i in triples[a] and j in triples[a] for a in selected) for j in range(18)] for i in range(18)] == gram
    assert all(not {a,b} <= set(selected) for a,b in domain['motif_pairs'])
    targets = [[2-int(i in h)-sum(adjacency[i] >> j & 1 for j in h) for i in range(18)] for h in triples]
    assert targets == domain['row_targets']
    neighbors = [[] for _ in range(480)]
    masks = [sum(1 << i for i in h) for h in triples]
    for a,b in combinations(range(480),2):
        if (masks[a]&masks[b]).bit_count() > 1:
            continue
        if any(targets[a][i] == 0 for i in triples[b]) or any(targets[b][i] == 0 for i in triples[a]):
            continue
        neighbors[a].append(b)
        neighbors[b].append(a)
    assert neighbors == domain['possible_neighbor_signature_ids'] and sum(map(len,neighbors)) == 2*68394
    for cut in loaded['f0-first-design-exterior-row-certificate.json.gz']['row_certificate']['transported_cuts']:
        assert sum(w for b,w in cut['binary_capped_weights'] if b in selected) >= 2*int(cut['target_signature'] in selected)
    identity = tuple(range(21))
    group,frontier = {identity},[identity]
    while frontier:
        old = frontier.pop()
        for generator in domain['core_generators']:
            image = tuple(generator[old[i]] for i in range(21))
            assert sorted(image) == list(range(21)) and set(image[:3]) == set(range(3))
            assert all((core[i] >> j & 1) == (core[image[i]] >> image[j] & 1) for i in range(21) for j in range(21))
            if image not in group:
                group.add(image)
                frontier.append(image)
    assert len(group) == 12
    positions = {tuple(h):i for i,h in enumerate(triples)}
    actions = []
    for image in sorted(group):
        move = [image[i+3]-3 for i in range(18)]
        action = [positions[tuple(sorted(move[i] for i in h))] for h in triples]
        assert sorted(action) == list(range(480))
        for a in range(480):
            assert sorted(action[b] for b in neighbors[a]) == neighbors[action[a]]
            assert all(targets[a][i] == targets[action[a]][move[i]] for i in range(18))
        actions.append({'component_image':move,'signature_image':action})
    rows = [{'position':i,'target':a,'target_triple':triples[a],'demand':targets[a],
             'selected_eligible_neighbors':sorted(set(neighbors[a])&set(selected)),
             'complete_eligible_neighbor_count':len(neighbors[a])} for i,a in enumerate(selected)]
    return triples,targets,neighbors,selected,actions,rows


def controls():
    # A cone-feasible row can fail the upper-one capacities: two copies of
    # one unit vector are needed, but only one selected neighbor is present.
    assert 1*2-max(1*1,0) == 1
    assignments = 0
    examples = [([[1],[1]],[2],[1]),([[1,0],[0,1]],[1,0],[1,-1]),
                ([[1,1],[1,0],[0,1]],[1,1],[2,-1])]
    for columns,q,v in examples:
        demand = sum(a*b for a,b in zip(q,v))
        weights = [max(sum(x*y for x,y in zip(h,v)),0) for h in columns]
        for z in product((0,1),repeat=len(columns)):
            for y in product((0,1),repeat=len(columns)):
                if any(a>b for a,b in zip(y,z)):
                    continue
                if [sum(h[i]*value for h,value in zip(columns,y)) for i in range(len(q))] != q:
                    continue
                assert sum(w*value for w,value in zip(weights,z)) >= demand
                assignments += 1
    assert assignments > 0
    return {'binary_activation_weighted_cut_controls':assignments,
            'cone_feasible_but_box_infeasible_control':True,
            'optimizer_called':False,'SAT_solver_called':False}


def preparation():
    triples,targets,neighbors,selected,actions,rows = load()
    return {'status':'complete60-row box-separation preparation; no optimizer called',
        'source_sha256':digest(Path(__file__)),'input_hashes':INPUTS,
        'selected_signature_ids':selected,'rows':rows,'verified_core_actions':actions,
        'dual_LP':'minimize -q*v+sum(s); h_b*v-s_b<=0; -1<=v_i<=1; s_b>=0',
        'method':'scipy.optimize.linprog highs-ds','one_LP_per_selected_row':True,
        'row_order':'increasing selected signature index','maximum_total_seconds':60,
        'integer_reconstruction':'scales1..64 plus bounded-denominator rational fallback; direct exact gap acceptance',
        'cut_acceptance':'v*q > sum_selected_eligible max(v*h_b,0), exact integers only',
        'cover_clause':'negative target selector or any positive-weight eligible signature absent from the current design',
        'cover_transport_scope':'only twelve individually verified core relabelings',
        'row_box_witness_acceptance':'rational weights in[0,1], all18 exact equations, sum8',
        'neighbor_pair_packing_in_LP':False,'incidence_model_mutated':False,
        'controls':controls(),'solver_or_optimizer_called':False}


def primitive(vector):
    divisor = gcd(*(abs(value) for value in vector))
    return None if not divisor else [value//divisor for value in vector]


def integer_vector(numerical,triples,q,inside):
    candidates = set()
    for scale in range(1,65):
        vector = primitive([round(scale*value) for value in numerical])
        if vector is not None:
            candidates.add(tuple(vector))
    rationals = [Fraction(float(value)).limit_denominator(10000) for value in numerical]
    denominator = lcm(*(value.denominator for value in rationals))
    vector = primitive([int(value*denominator) for value in rationals])
    if vector is not None and max(map(abs,vector)) <= 10**6:
        candidates.add(tuple(vector))
    accepted = []
    for vector in candidates:
        demand = sum(x*y for x,y in zip(vector,q))
        capacity = sum(max(sum(vector[i] for i in triples[b]),0) for b in inside)
        if demand > capacity:
            accepted.append(vector)
    if not accepted:
        return None
    return list(min(accepted,key=lambda v:(max(map(abs,v)),sum(map(abs,v)),sum(bool(x) for x in v),v)))


def obstruction(target,vector,triples,targets,neighbors,selected,actions):
    assert len(vector) == 18 and all(type(v) is int for v in vector)
    inside = sorted(set(neighbors[target])&set(selected))
    demand = sum(x*y for x,y in zip(vector,targets[target]))
    products = [[b,sum(vector[i] for i in triples[b])] for b in neighbors[target]]
    capacity = sum(max(weight,0) for b,weight in products if b in selected)
    assert demand > capacity >= 0
    positive = [[b,w] for b,w in products if w > 0]
    outside = [b for b,w in positive if b not in selected]
    clause = [-(target+1)]+[b+1 for b in outside]
    assert all(b not in selected for b in outside) and target in selected
    transports = []
    for action_number,record in enumerate(actions):
        image,move = record['signature_image'],record['component_image']
        a = image[target]
        v = [0]*18
        for i in range(18):
            v[move[i]] = vector[i]
        assert sum(x*y for x,y in zip(v,targets[a])) == demand
        weighted = sorted([image[b],w] for b,w in positive)
        direct = [[b,sum(v[i] for i in triples[b])] for b in neighbors[a]]
        assert weighted == [[b,w] for b,w in direct if w > 0]
        cover = sorted(image[b] for b in outside)
        available_capacity = sum(w for b,w in weighted if b not in cover)
        assert available_capacity == capacity < demand
        transports.append({'core_action_index':action_number,'target':a,
            'integer_vector':v,'integer_demand':demand,'remaining_positive_capacity_if_clause_false':capacity,
            'positive_weighted_terms':weighted,'cover_clause':[-(a+1)]+[b+1 for b in cover]})
    assert len(transports) == 12
    return {'integer_vector':vector,'integer_demand':demand,'selected_positive_capacity':capacity,
        'strict_integer_gap':demand-capacity,'selected_eligible_neighbors':inside,
        'full_positive_weighted_terms':positive,'cover_clause':clause,
        'all12_verified_core_transports':transports,
        'current_incidence_violates_base_cover_clause':True,
        'universal_target_signature_exclusion':not outside,
        'binary_neighbor_row_or_graph_constructed':False}


def rational_box_witness(marginals,triples,q,inside):
    values = [Fraction(-float(value)).limit_denominator(1000000) for value in marginals]
    if any(value < 0 or value > 1 for value in values):
        return None
    if [sum(value for b,value in zip(inside,values) if i in triples[b]) for i in range(18)] != q:
        return None
    assert sum(values) == 8
    denominator = lcm(*(value.denominator for value in values))
    numerators = [int(value*denominator) for value in values]
    support = [b for b,value in zip(inside,numerators) if value]
    binary = all(value in (0,denominator) for value in numerators)
    packing = binary and all(len(set(triples[a])&set(triples[b])) <= 1 for a,b in combinations(support,2))
    return {'denominator':denominator,'numerators':numerators,'neighbor_signature_ids':inside,
        'all18_exact_equalities_checked':True,'all_weights_between_zero_and_one':True,
        'sum_weights':8,'binary_neighbor_weights':binary,'binary_neighbor_pair_packing_checked_and_passed':packing,
        'complete_exterior_graph_or_incidence_claimed':False}


def checked_preparation(path):
    saved = json.loads(gzip.decompress(path.read_bytes()))
    assert saved == preparation()
    return saved


def summarize(report):
    report['status_counts'] = dict(sorted(Counter(row['status'] for row in report['rows']).items()))
    clauses = {tuple(transport['cover_clause']) for row in report['rows'] if 'exact_obstruction' in row
               for transport in row['exact_obstruction']['all12_verified_core_transports']}
    report['deduplicated_exact_cover_clauses'] = [list(clause) for clause in sorted(clauses)]
    report['exact_cover_clause_count'] = len(clauses)
    report['exact_row_obstruction_count'] = sum('exact_obstruction' in row for row in report['rows'])
    report['exact_box_row_witness_count'] = sum('exact_box_witness' in row for row in report['rows'])
    report['processed_rows'] = sum(row['status'] not in ('PENDING','NOT RUN: total budget','NOT RUN: earlier error') for row in report['rows'])
    report['all60_selected_rows_processed'] = report['processed_rows'] == 60


def run(prepared_path,directory,seconds):
    assert not directory.exists() and 0 < seconds <= 60
    directory.mkdir(parents=True)
    started = time.monotonic()
    prepared = checked_preparation(prepared_path)
    triples,targets,neighbors,selected,actions,plans = load()
    report = {'status':'running one complete60-row bounded separation pass',
        'source_sha256':digest(Path(__file__)),'preparation':portable(prepared_path),
        'preparation_sha256':digest(prepared_path),'input_hashes':INPUTS,
        'requested_total_seconds':seconds,'rows':[{'position':row['position'],'target':row['target'],'status':'PENDING'} for row in plans],
        'incidence_model_or_CNF_mutated':False,'SAT_solver_called':False,
        'full_graph_completion':False,'whole_component_excluded':False}
    output = directory/'result.json'
    summarize(report)
    save(output,report)
    import numpy as np
    import scipy
    from scipy.optimize import linprog
    report['scipy_version'] = scipy.__version__
    stop_reason = 'total budget'
    for position,plan in enumerate(plans):
        remaining = seconds-(time.monotonic()-started)
        if remaining <= 0:
            break
        record = report['rows'][position]
        target,inside,q = plan['target'],plan['selected_eligible_neighbors'],plan['demand']
        count = len(inside)
        objective = np.array([-value for value in q]+[1]*count,dtype=float)
        matrix = np.zeros((count,18+count),dtype=float)
        for row,b in enumerate(inside):
            matrix[row,triples[b]] = 1
            matrix[row,18+row] = -1
        record.update(status='RUNNING',selected_neighbor_count=count,requested_remaining_seconds=remaining,
                      LP_variables=18+count,LP_inequalities=count)
        save(output,report)
        row_started = time.monotonic()
        try:
            answer = linprog(objective,A_ub=matrix,b_ub=np.zeros(count),
                bounds=[(-1,1)]*18+[(0,None)]*count,method='highs-ds',
                options={'time_limit':max(0.001,remaining),'presolve':True})
        except Exception as error:
            record.update(status='ERROR: numerical LP call',error=repr(error),seconds=time.monotonic()-row_started)
            stop_reason = 'earlier error'
            break
        record.update(numerical_status=int(answer.status),numerical_message=str(answer.message),
                      seconds=time.monotonic()-row_started,numerical_iterations=int(answer.nit))
        if answer.fun is not None and isfinite(float(answer.fun)):
            record['numerical_separation_value'] = -float(answer.fun)
        if answer.x is not None and all(isfinite(float(x)) for x in answer.x[:18]):
            numeric = [float(x) for x in answer.x[:18]]
            record['numerical_vector_hex'] = [x.hex() for x in numeric]
            vector = integer_vector(numeric,triples,q,inside)
        else:
            vector = None
        if vector is not None:
            record['exact_obstruction'] = obstruction(target,vector,triples,targets,neighbors,selected,actions)
            record['status'] = 'EXACT INTEGER ROW CAPACITY OBSTRUCTION'
        elif answer.status == 0:
            witness = rational_box_witness(answer.ineqlin.marginals,triples,q,inside)
            if witness is not None:
                record['exact_box_witness'] = witness
                record['status'] = 'EXACT RATIONAL BOX ROW WITNESS'
            else:
                record['status'] = 'NUMERICAL OPTIMUM ONLY: no exact certificate'
        elif answer.status == 1:
            record['status'] = 'UNKNOWN: numerical LP limit without exact certificate'
        else:
            record['status'] = 'ERROR: numerical dual LP did not reach expected status'
            stop_reason = 'earlier error'
        report['elapsed_seconds'] = time.monotonic()-started
        summarize(report)
        save(output,report)
        print(json.dumps({'position':position,'target':target,'status':record['status'],
            'gap':record.get('exact_obstruction',{}).get('strict_integer_gap'),
            'elapsed_seconds':report['elapsed_seconds']}),flush=True)
        if answer.status == 1 or stop_reason == 'earlier error':
            break
    for record in report['rows']:
        if record['status'] == 'PENDING':
            record['status'] = 'NOT RUN: '+stop_reason
    summarize(report)
    report['elapsed_seconds'] = time.monotonic()-started
    report['cooperative_budget_overrun_seconds'] = max(0,report['elapsed_seconds']-seconds)
    report['status'] = 'COMPLETE: all60 selected rows processed' if report['all60_selected_rows_processed'] else 'PARTIAL: honest selected-row prefix only'
    save(output,report)
    print(json.dumps({k:v for k,v in report.items() if k not in ('rows','deduplicated_exact_cover_clauses')},indent=2),flush=True)


def replay(prepared_path,result_path,output):
    assert not output.exists()
    checked_preparation(prepared_path)
    triples,targets,neighbors,selected,actions,plans = load()
    report = json.loads(result_path.read_text())
    assert report['status'].startswith(('COMPLETE:','PARTIAL:'))
    assert all(row['status'] not in ('PENDING','RUNNING') for row in report['rows'])
    assert report['source_sha256'] == digest(Path(__file__))
    assert report['preparation_sha256'] == digest(prepared_path) and report['input_hashes'] == INPUTS
    assert len(report['rows']) == 60
    exact,box = 0,0
    for position,(row,plan) in enumerate(zip(report['rows'],plans)):
        assert row['position'] == position and row['target'] == plan['target']
        if 'exact_obstruction' in row:
            saved = row['exact_obstruction']
            assert saved == obstruction(plan['target'],saved['integer_vector'],triples,targets,neighbors,selected,actions)
            assert row['status'] == 'EXACT INTEGER ROW CAPACITY OBSTRUCTION'
            exact += 1
        if 'exact_box_witness' in row:
            witness = row['exact_box_witness']
            den,nums = witness['denominator'],witness['numerators']
            assert type(den) is int and den > 0 and all(type(v) is int and 0 <= v <= den for v in nums)
            inside = plan['selected_eligible_neighbors']
            assert witness['neighbor_signature_ids'] == inside and len(nums) == len(inside)
            assert [sum(n for b,n in zip(inside,nums) if i in triples[b]) for i in range(18)] == [den*q for q in plan['demand']]
            assert sum(nums) == 8*den
            binary = all(n in (0,den) for n in nums)
            support = [b for b,n in zip(inside,nums) if n]
            packing = binary and all(len(set(triples[a])&set(triples[b])) <= 1 for a,b in combinations(support,2))
            assert witness['binary_neighbor_weights'] == binary and witness['binary_neighbor_pair_packing_checked_and_passed'] == packing
            assert row['status'] == 'EXACT RATIONAL BOX ROW WITNESS'
            box += 1
    check = json.loads(json.dumps(report))
    summarize(check)
    assert check == report
    actual = {'status':'exact complete-domain, row-capacity, rational-witness and cover-transport replay PASS',
        'source_sha256':digest(Path(__file__)),'preparation_sha256':digest(prepared_path),
        'result_sha256':digest(result_path),'processed_rows':report['processed_rows'],
        'all60_selected_rows_processed':report['all60_selected_rows_processed'],
        'exact_integer_obstructions':exact,'exact_rational_box_witnesses':box,
        'exact_cover_clause_count':report['exact_cover_clause_count'],
        'optimizer_or_SAT_solver_called':False,'whole_component_excluded':False}
    save(output,actual)
    print(json.dumps(actual,indent=2),flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command',required=True)
    prep = commands.add_parser('prepare')
    prep.add_argument('--output',type=Path,required=True)
    execute = commands.add_parser('run')
    execute.add_argument('--preparation',type=Path,required=True)
    execute.add_argument('--directory',type=Path,required=True)
    execute.add_argument('--seconds',type=float,default=60)
    check = commands.add_parser('replay')
    check.add_argument('--preparation',type=Path,required=True)
    check.add_argument('--result',type=Path,required=True)
    check.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.command == 'prepare':
        assert not args.output.exists()
        result = preparation()
        args.output.write_bytes(gzip.compress(canonical(result)+b'\n',mtime=0))
        print(json.dumps({'status':result['status'],'source_sha256':result['source_sha256'],
            'preparation_sha256':digest(args.output),'rows':len(result['rows']),
            'selected_neighbor_count_histogram':dict(sorted(Counter(len(r['selected_eligible_neighbors']) for r in result['rows']).items())),
            'controls':result['controls']},indent=2),flush=True)
    elif args.command == 'run':
        run(args.preparation.resolve(),args.directory.resolve(),args.seconds)
    else:
        replay(args.preparation.resolve(),args.result.resolve(),args.output.resolve())
