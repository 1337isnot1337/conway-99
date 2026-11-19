"""Independent attribution and exact row obstruction for the first design.

No subject builder, graph canonicalizer, optimizer, or SAT solver is
imported. PySAT cardinality encoding is used only to identify retained
clauses with their mathematical input rows; the short contradiction and
all twelve transported incidence cuts are checked by integer arithmetic.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, product
import json
from pathlib import Path
import time


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/root-prism-free'
INPUTS = {
    'f0-pair-gram-certificate.json.gz':'edb85ff422222961e6bc9b36322b74bcfce455bca262d6e189d7768f9ac91c98',
    'f0-coupling-certificate.json.gz':'bbe73089b6ae19b25ebb43597195ee81682202e3139e627fbc75db427a5c4cc7',
    'f0-first-design-exterior-model.json':'d98d817a7e9410f6fd88186adacdf23b886e543f3e18f7a9ec98af07e6558078',
    'f0-first-design-exterior-run01/retained.cnf':'dffc02f25e8953c387be76661960bca0955a296b783b09959427e691105649fb',
    'f0-first-design-exterior-run01-cold-replay.json':'6240d173c5f15919a74e0062f8a81f3b25bd55a3928f3bd9e94b0531ed5a4847',
    'f0-exterior-row-domains02.json.gz':'665563b75fa6fc23caa9a002621cc4047809af28543b52b5c2a7ffa592d05dd4'}
VECTOR = [1,1,1,4,-5,0,1,1,4,-5,-5,0,-2,-2,4,-5,0,-2]
TARGET = 479
WITNESS = [0,9,72,82,259,397,420,429]


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def canonical(data):
    return json.dumps(data,sort_keys=True,separators=(',',':')).encode()


def load():
    saved = {}
    for name,value in INPUTS.items():
        path = LOGS/name
        assert digest(path) == value
        raw = path.read_bytes()
        if name.endswith('.cnf'):
            saved[name] = [list(map(int,line.split()[:-1])) for line in raw.decode().splitlines()
                           if line and line[0] not in 'cp']
        else:
            saved[name] = json.loads(gzip.decompress(raw) if name.endswith('.gz') else raw)
    assert saved['f0-first-design-exterior-run01-cold-replay.json']['status'].endswith('DRAT PASS')
    return saved


def reconstruct(saved):
    old = saved['f0-pair-gram-certificate.json.gz']
    full_core = list(map(int,old['joined_core_rows']))
    gram = [[12*int(i == j)+2-(full_core[i]&full_core[j]).bit_count()-(full_core[i] >> j & 1)
             for j in range(39)] for i in range(39)]
    assert gram == old['Gram']
    core = [row & ((1 << 21)-1) for row in full_core[:21]]
    adjacency = [(row >> 3)&((1 << 18)-1) for row in core[3:21]]
    local = [row[3:21] for row in gram[3:21]]
    triples = []
    for h in combinations(range(18),3):
        if max(sum(v//6 == f for v in h) for f in range(3)) > 2:
            continue
        if any(local[i][j] == 0 for i,j in combinations(h,2)):
            continue
        if any(sum(int(i == v or adjacency[i] >> v & 1) for v in h) > 2 for i in range(18)):
            continue
        triples.append(list(h))
    assert triples == old['component_triples'] and len(triples) == 480
    masks = [sum(1 << i for i in h) for h in triples]
    targets = [[2-int(mask >> i & 1)-(adjacency[i]&mask).bit_count() for i in range(18)] for mask in masks]
    assert all(sum(q) == 24 and min(q) >= 0 and max(q) <= 2 for q in targets)
    neighbors = [[] for _ in range(480)]
    for a,b in combinations(range(480),2):
        if (masks[a]&masks[b]).bit_count() > 1:
            continue
        if any(targets[a][i] == 0 for i in triples[b]) or any(targets[b][i] == 0 for i in triples[a]):
            continue
        neighbors[a].append(b)
        neighbors[b].append(a)
    domains = saved['f0-exterior-row-domains02.json.gz']
    assert core == domains['component_core_rows'] and adjacency == domains['component_adjacency_rows']
    assert triples == domains['signature_domain'] and targets == domains['row_targets']
    assert neighbors == domains['possible_neighbor_signature_ids']
    assert sum(map(len,neighbors)) == 2*68394
    selected = saved['f0-coupling-certificate.json.gz']['first_selected_domain_indices']
    design = [triples[i] for i in selected]
    assert design == saved['f0-coupling-certificate.json.gz']['fixed_design']
    assert [[sum(i in h and j in h for h in design) for j in range(18)] for i in range(18)] == local
    fixed_edges = [(u,v) for u in range(60) for v in range(u) if selected[v] in neighbors[selected[u]]]
    assert len(fixed_edges) == 1224
    model = saved['f0-first-design-exterior-model.json']['data']
    assert design == model['design'] and selected == model['design_source_indices']
    assert adjacency == model['component_adjacency_rows']
    assert [list(p) for p in fixed_edges] == model['edge_domain']
    assert [targets[i] for i in selected] == model['targets']
    return core,adjacency,triples,masks,targets,neighbors,selected,fixed_edges


def attribute(saved,data):
    from pysat.card import CardEnc, EncType
    from pysat.formula import IDPool
    core,adjacency,triples,masks,targets,neighbors,selected,edges = data
    retained = saved['f0-first-design-exterior-run01/retained.cnf']
    keys = [tuple(sorted(row)) for row in retained]
    assert len(keys) == len(set(keys)) == 120
    positions = {key:i for i,key in enumerate(keys)}
    origins = [[] for _ in keys]
    variables = {tuple(sorted(edge)):i+1 for i,edge in enumerate(edges)}
    pool = IDPool(start_from=len(edges)+1)
    clause_number = 0
    mathematical_rows = []
    for v in range(60):
        incident = [(w,variables[tuple(sorted((v,w)))]) for w in range(60)
                    if w != v and tuple(sorted((v,w))) in variables]
        rows = [('degree',None,[literal for w,literal in incident],8)]
        rows.extend(('mixed',i,[literal for w,literal in incident if i in triples[selected[w]]],targets[selected[v]][i])
                    for i in range(18))
        for kind,coordinate,literals,quota in rows:
            before = pool.top
            clauses = CardEnc.equals(literals,quota,vpool=pool,encoding=EncType.seqcounter).clauses
            found = []
            for local_index,clause in enumerate(clauses):
                key = tuple(sorted(clause))
                if key in positions:
                    index = positions[key]
                    origins[index].append({'kind':kind,'outside_vertex':v,'core_coordinate':coordinate,
                                           'quota':quota,'row_clause_index':local_index,
                                           'full_formula_clause_number':clause_number+local_index+1})
                    found.append(index)
            if found:
                mathematical_rows.append({'kind':kind,'outside_vertex':v,'core_coordinate':coordinate,
                    'quota':quota,'primary_literals':literals,'auxiliary_interval':[before+1,pool.top],
                    'retained_clause_indices':found})
            clause_number += len(clauses)
    assert pool.top == 46032
    packing = []
    for index,(key,origin) in enumerate(zip(keys,origins)):
        if origin:
            continue
        assert len(key) == 2 and all(-len(edges) <= literal < 0 for literal in key)
        left,right = [set(edges[-literal-1]) for literal in key]
        assert len(left&right) == 1
        center = next(iter(left&right))
        u,v = next(iter(left-{center})),next(iter(right-{center}))
        shared = sorted(set(triples[selected[u]])&set(triples[selected[v]]))
        assert len(shared) == 2
        quota_one = [i for i in shared if targets[selected[center]][i] == 1]
        assert quota_one
        detail = {'kind':'outside_pair_zero_capacity','outside_pair':sorted((u,v)),
                  'common_neighbor':center,'shared_first_core_points':shared,
                  'already_implied_by_mixed_quota_one_coordinates':quota_one}
        origins[index].append(detail)
        packing.append({'retained_clause_index':index,**detail})
    assert all(len(origin) == 1 for origin in origins)
    assert sum(len(row['retained_clause_indices']) for row in mathematical_rows) == 115
    assert len(packing) == 5
    assert {row['outside_vertex'] for row in mathematical_rows} == {59}
    assert {row['kind'] for row in mathematical_rows} == {'mixed'}
    assert all(row['common_neighbor'] == 59 for row in packing)
    return {'retained_input_clauses':120,'counter_clauses':115,'packing_clauses':5,
            'all_mathematical_rows_at_one_outside_vertex':59,
            'target_signature_index':selected[59],'target_triple':triples[selected[59]],
            'all_packing_clauses_redundant_from_same_mixed_rows':True,
            'mathematical_rows':mathematical_rows,'packing_sources':packing,
            'clause_attribution':[{'clause':row,'source':origin[0]} for row,origin in zip(retained,origins)],
            'full_CNF_assembled_or_solved':False,'DRAT_replayed_in_this_audit':False}


def threshold_clauses(target,one,two):
    # Signature ids are zero-based; CNF selector variables are id+1.
    assert len(set(one+two+[target])) == len(one)+len(two)+1
    return [[-(target+1)]+[b+1 for b in one+two]]+[
        [-(target+1),-(a+1)]+[b+1 for b in one if b != a]+[b+1 for b in two] for a in one]


def threshold_controls():
    checked = 0
    for n in range(5):
        for m in range(5):
            one,two = list(range(n)),list(range(n,n+m))
            target = n+m
            clauses = threshold_clauses(target,one,two)
            for bits in product((0,1),repeat=n+m+1):
                actual = all(any(bits[abs(lit)-1] == int(lit > 0) for lit in clause) for clause in clauses)
                expected = sum(bits[i] for i in one)+2*sum(bits[i] for i in two) >= 2*bits[target]
                assert actual == expected
                checked += 1
    truncation = 0
    for weights in product((1,2,3,4),repeat=4):
        for bits in product((0,1),repeat=4):
            assert (sum(a*b for a,b in zip(weights,bits)) >= 2) == (sum(min(2,a)*b for a,b in zip(weights,bits)) >= 2)
            truncation += 1
    return {'guarded_threshold_truth_assignments':checked,'binary_weight_truncation_controls':truncation}


def cut(target,vector,triples,targets,neighbors):
    demand = sum(a*b for a,b in zip(vector,targets[target]))
    assert demand == 6
    positive = [(b,sum(vector[i] for i in triples[b])) for b in neighbors[target]]
    positive = [(b,weight) for b,weight in positive if weight > 0]
    assert len(positive) == 55 and all(weight % 3 == 0 for b,weight in positive)
    normalized = [[b,weight//3] for b,weight in positive]
    capped = [[b,min(weight,2)] for b,weight in normalized]
    one = [b for b,weight in capped if weight == 1]
    two = [b for b,weight in capped if weight == 2]
    assert len(one) == 36 and len(two) == 19
    clauses = threshold_clauses(target,one,two)
    assert len(clauses) == 37 and set(map(len,clauses)) == {56}
    return {'target_signature':target,'target_triple':triples[target],'integer_vector':vector,
            'integer_target_value':demand,'positive_integer_weights':[[b,w] for b,w in positive],
            'divisor':3,'normalized_target_value':2,'normalized_weights':normalized,
            'binary_capped_weights':capped,'weight_one_signature_ids':one,'weight_two_signature_ids':two,
            'guarded_clauses':clauses}


def row_certificate(saved,data):
    core,adjacency,triples,masks,targets,neighbors,selected,edges = data
    assert triples[TARGET] == [11,16,17] and selected[59] == TARGET
    eligible = neighbors[TARGET]
    fixed = sorted(set(eligible)&set(selected))
    excluded = sorted(set(eligible)-set(selected))
    assert (len(eligible),len(fixed),len(excluded)) == (232,29,203)
    products = [[b,sum(VECTOR[i] for i in triples[b])] for b in fixed]
    assert max(value for b,value in products) == 0
    assert sum(a*b for a,b in zip(VECTOR,targets[TARGET])) == 6
    assert len(WITNESS) == 8 and len(set(WITNESS)) == 8 and set(WITNESS) <= set(eligible)
    assert [sum(i in triples[b] for b in WITNESS) for i in range(18)] == targets[TARGET]
    assert all((masks[a]&masks[b]).bit_count() <= 1 for a,b in combinations(WITNESS,2))
    base = cut(TARGET,VECTOR,triples,targets,neighbors)
    assert sum(weight for b,weight in base['binary_capped_weights'] if b in selected) == 0
    generators = saved['f0-exterior-row-domains02.json.gz']['core_generators']
    identity = tuple(range(21))
    group,frontier = {identity},[identity]
    while frontier:
        image = frontier.pop()
        for generator in generators:
            move = tuple(generator[image[i]] for i in range(21))
            assert sorted(move) == list(range(21)) and set(move[:3]) == set(range(3))
            assert all((core[i] >> j & 1) == (core[move[i]] >> move[j] & 1) for i in range(21) for j in range(21))
            if move not in group:
                group.add(move)
                frontier.append(move)
    assert len(group) == 12
    positions = {tuple(h):i for i,h in enumerate(triples)}
    transports = []
    for full_move in sorted(group):
        move = [full_move[i+3]-3 for i in range(18)]
        action = [positions[tuple(sorted(move[i] for i in h))] for h in triples]
        assert sorted(action) == list(range(480))
        a = action[TARGET]
        assert sorted(action[b] for b in neighbors[TARGET]) == neighbors[a]
        assert all(targets[TARGET][i] == targets[a][move[i]] for i in range(18))
        vector = [0]*18
        for i in range(18):
            vector[move[i]] = VECTOR[i]
        transported = cut(a,vector,triples,targets,neighbors)
        assert sorted([action[b],w] for b,w in base['normalized_weights']) == transported['normalized_weights']
        transported['component_relabeling'] = move
        transported['signature_action_sha256'] = hashlib.sha256(canonical(action)).hexdigest()
        transports.append(transported)
    transports.sort(key=lambda t:t['target_signature'])
    assert len({t['target_signature'] for t in transports}) == 12
    all_clauses = [clause for record in transports for clause in record['guarded_clauses']]
    assert len(all_clauses) == len({tuple(sorted(clause)) for clause in all_clauses}) == 444
    return {'status':'exact integer row contradiction and twelve universally necessary incidence cuts',
            'target_signature':TARGET,'target_triple':triples[TARGET],'target_quotas':targets[TARGET],
            'complete_eligible_neighbor_signature_ids':eligible,
            'saved_design_eligible_neighbor_signature_ids':fixed,
            'eligible_neighbor_signature_ids_outside_saved_design':excluded,
            'integer_vector':VECTOR,'integer_target_value':6,'saved_neighbor_dot_products':products,
            'saved_neighbor_dot_product_histogram':[[value,count] for value,count in sorted(Counter(v for b,v in products).items())],
            'nonnegative_row_LP_impossible_for_saved_design':True,
            'no_integrality_or_neighbor_packing_needed_for_contradiction':True,
            'full_domain_row_control':{'neighbor_signature_ids':WITNESS,'neighbor_triples':[triples[i] for i in WITNESS],
                'all18_quotas_checked':True,'neighbor_pair_overlap_at_most_one':True,
                'complete_incidence_or_graph_witness_claimed':False},
            'base_cut':base,'verified_core_relabeling_group_size':12,'transported_cuts':transports,
            'all_guarded_clauses':all_clauses,'all_guarded_clause_count':444,
            'guarded_clauses_sha256':hashlib.sha256(canonical(all_clauses)).hexdigest(),
            'second_component_or_alignment_assumed':False,
            'hypothetical_graph_automorphism_assumed':False,
            'whole_component_or_signature_excluded':False,
            'controls':threshold_controls()}


def calculate():
    started = time.monotonic()
    saved = load()
    data = reconstruct(saved)
    return {'status':'independent retained-row attribution and exact integer incidence-cut replay PASS',
            'source_sha256':digest(Path(__file__)),'input_hashes':INPUTS,
            'complete_domain_reconstructed':480,'complete_universal_neighbor_edges_reconstructed':68394,
            'attribution':attribute(saved,data),'row_certificate':row_certificate(saved,data),
            'subject_builder_imported':False,'optimizer_called':False,'SAT_solver_called':False,
            'elapsed_seconds_for_information_only':time.monotonic()-started}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--certificate',type=Path,required=True)
    parser.add_argument('--replay',action='store_true')
    args = parser.parse_args()
    actual = calculate()
    if args.replay:
        expected = json.loads(gzip.decompress(args.certificate.read_bytes()))
        actual['elapsed_seconds_for_information_only'] = expected['elapsed_seconds_for_information_only']
        assert actual == expected
    else:
        assert not args.certificate.exists()
        args.certificate.write_bytes(gzip.compress(canonical(actual)+b'\n',mtime=0))
    row = actual['row_certificate']
    print(json.dumps({'status':actual['status'],'source_sha256':actual['source_sha256'],
        'certificate_sha256':digest(args.certificate),'retained_clause_count':actual['attribution']['retained_input_clauses'],
        'mixed_row_attribution':[[item['core_coordinate'],len(item['retained_clause_indices'])] for item in actual['attribution']['mathematical_rows']],
        'universal_neighbors':len(row['complete_eligible_neighbor_signature_ids']),
        'saved_design_eligible_neighbors':len(row['saved_design_eligible_neighbor_signature_ids']),
        'integer_target_value':6,'positive_cut_support':55,'transported_cut_count':len(row['transported_cuts']),
        'new_guarded_clause_count':444,'full_domain_row_control':row['full_domain_row_control'],
        'controls':row['controls'],'elapsed_seconds':actual['elapsed_seconds_for_information_only']},indent=2),flush=True)
