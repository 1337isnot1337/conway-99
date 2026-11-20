"""Complete visible pair-incompatibility domains and clique quotient.

The analytic incompatibility criterion is compared with both literal
two-free-vertex edge choices. Bron--Kerbosch and incremental maximal
clique enumeration must agree. All added empty conditional rows and
root-automorphism transports are checked. No point or tensor is built.
"""

import argparse
from collections import Counter, deque
from functools import reduce
import gzip
import json
from operator import and_
from pathlib import Path
import pickle
import resource
import signal
import time

import grid_free_order10_complement_cliques as old_graph
import grid_free_order10_complement_clique_orbits as group_tools
import grid_free_order10_complement_domains as domains
import grid_free_order10_projector_literal as literal
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
OLD_CENSUS = LOGS/'order10-complement-cliques.json.gz'
OLD_CENSUS_SHA = '365faacdf5144a85730aa03c1a2638ec782303051892d27bc6803790d058fdb4'
OLD_LIFTS = LOGS/'order10-complement-clique-lifts.json.gz'
OLD_LIFTS_SHA = 'c92a8ad205545a75f67cdffc43011db21f687f14722109a03f2b34f6490c5c28'
OLD_ORBITS = LOGS/'order10-complement-clique-orbits.json.gz'
OLD_ORBITS_SHA = 'fe31700fd6889150ad68265c66ed6c266e81be94da393d3b56fb63027a0f148e'
SOURCE_BINDINGS = {
    'grid_free_order10_complement_cliques.py':'765f0ca7ca7ffcb16e6c518d80c70ffca99ba2c0c46d682077f1027ae47fe912',
    'grid_free_order10_complement_clique_orbits.py':'5569a81838301fa54dc2401b98592a91fb302b7ed7a3110983a6f475a1107130',
    'grid_free_order10_complement_domains.py':'4961411ec0f7671abb7e34c5dbd4ec257ac98f9bffcb745a408e979751179ed8',
    'grid_free_order10_projector_literal.py':'ca302f44d051b4372e64b7c3a6353174c3b3880cff20b9c7055ad8343162d2b1',
}


def read(path):
    return json.loads(gzip.decompress(path.read_bytes()))


def incremental_cliques(adjacency,masks):
    """Independent complete construction by adding one vertex at a time."""
    order = sorted(range(len(adjacency)),
                   key=lambda i:(-adjacency[i].bit_count(),-masks[i].bit_count(),masks[i]))
    kept = {0}
    sizes = []
    for vertex in order:
        bit = 1 << vertex
        candidates = kept | {bit | (clique & adjacency[vertex]) for clique in kept}
        maximal = []
        for candidate in sorted(candidates,key=lambda x:(-x.bit_count(),x)):
            if not any(candidate & ~old == 0 for old in maximal):
                maximal.append(candidate)
        kept = set(maximal)
        sizes.append(len(kept))
    return kept,order,sizes


def exact_graph(rows,high):
    quota_one = [(1 << i)|(1 << j) for i in range(7) for j in range(i)
                 if 2-((rows[i] >> j)&1)-(rows[i]&rows[j]).bit_count() == 1]
    analytic = [0]*len(high)
    direct = [0]*len(high)
    controls = Counter()
    for i,a in enumerate(high):
        for j,b in enumerate(high[:i]):
            shared = a&b
            intersection_obstruction = shared.bit_count() >= 3
            quota_obstruction = any(shared & pair == pair for pair in quota_one)
            incompatible = intersection_obstruction or quota_obstruction
            nonedge_valid = literal.valid(literal.extend(rows,[a,b],0))
            edge_valid = literal.valid(literal.extend(rows,[a,b],1))
            assert not edge_valid or nonedge_valid
            assert incompatible == (not nonedge_valid and not edge_valid)
            assert incompatible == (not nonedge_valid)
            controls['literal_two_vertex_edge_choices_checked'] += 2
            controls['distinct_mask_pairs_checked'] += 1
            if incompatible:
                analytic[i] |= 1 << j
                analytic[j] |= 1 << i
                controls['visible_incompatibility_edges'] += 1
            if not nonedge_valid:
                direct[i] |= 1 << j
                direct[j] |= 1 << i
            if quota_obstruction and not intersection_obstruction:
                controls['new_quota_one_incompatibility_edges'] += 1
            if nonedge_valid:
                controls['both_edge_values_valid' if edge_valid else 'only_mutual_nonedge_valid'] += 1
            else:
                controls['neither_edge_value_valid'] += 1
    assert direct == analytic
    return analytic,direct,controls


def process_root(record,old_lifts,old_orbits,data,lift_builder):
    root,rows,high = record['root_type'],record['root_rows'],record['high_masks']
    assert data[0][root] == tuple(rows) or list(data[0][root]) == rows
    assert high == [mask for mask,_ in data[3][root] if mask.bit_count() >= 3]
    assert high == [mask for mask in old_graph.direct_allowed(rows) if mask.bit_count() >= 3]
    n = len(high)+1
    adjacency,direct,counts = exact_graph(rows,high)
    first = old_graph.bron_kerbosch(adjacency)
    second,addition_order,intermediate_sizes = incremental_cliques(direct,high)
    assert first == second
    codes = sorted(first)
    for clique in codes:
        old_graph.maximal(clique,(1 << len(high))-1,direct)
    residuals = [(i,j,2-((rows[i] >> j)&1)-(rows[i]&rows[j]).bit_count())
                 for i in range(7) for j in range(i)]
    allowed = [mask for mask,_ in data[3][root]]
    cases = []
    for clique in codes:
        selected = [high[i] for i in old_graph.members(clique)]
        common = reduce(and_,selected,127)
        witness = next(([i,j,1] for i,j,q in residuals
                        if q==1 and common >> i & 1 and common >> j & 1),None)
        classification = ('constant_only_base' if not selected else
                          'quota_one_redundant' if witness else 'remaining_clique_complement')
        if not selected:
            assert not high
        item = {'masks':selected,'base_positions':[i+1 for i in old_graph.members(clique)],
                'common_mask':common,'classification':classification,
                'quotient_order':n-len(selected)}
        item['quotient_lower_entries'] = item['quotient_order']*(item['quotient_order']+1)//2
        if witness:
            pair = (1 << witness[0])|(1 << witness[1])
            item['residual_pair_witness'] = witness
            item['other_allowed_masks_in_positive_sum'] = [mask for mask in allowed
                if mask & pair == pair and mask not in set(selected)]
        cases.append(item)
        counts[classification] += 1
        counts['all_clique_selected_row_instances'] += len(selected)
    positions = {mask:i for i,mask in enumerate(high)}
    old_covers = []
    for old in record['maximal_cliques']:
        code = sum(1 << positions[mask] for mask in old['masks'])
        old_covers.append(next(i for i,clique in enumerate(codes) if code & ~clique == 0))
    counts['old_intersection_cliques_covered'] = len(old_covers)
    index = {tuple(case['masks']):i for i,case in enumerate(cases)}
    triples = []
    for old in record['triple_groups_with_pair_residuals_two']:
        case_index = index[tuple(old['all_allowed_superset_masks'])]
        assert cases[case_index]['classification'] == 'remaining_clique_complement'
        triples.append({'triple_mask':old['triple_mask'],'maximal_clique_index':case_index,
                        'all_allowed_superset_masks':old['all_allowed_superset_masks']})
    counts['residual_two_triple_groups'] = len(triples)
    group,permutations_checked = group_tools.all_automorphisms(rows)
    generators = [tuple(g) for g in old_orbits['generators']]
    assert group_tools.closure(generators,7) == group
    assert len(group) == old_orbits['automorphism_order']
    assert permutations_checked == old_orbits['degree_preserving_permutations_checked']
    counts['root_automorphisms_enumerated'] = len(group)
    counts['degree_preserving_vertex_permutations_checked'] = permutations_checked
    counts['generators_verified'] = len(generators)
    actions = []
    for generator in generators:
        assert group_tools.automorphism(rows,generator)
        moved = {mask:group_tools.move_mask(mask,generator) for mask in high}
        assert sorted(moved.values()) == high
        mask_action = [positions[moved[mask]] for mask in high]
        for i,row in enumerate(adjacency):
            assert sum(1 << mask_action[j] for j in old_graph.members(row)) == adjacency[mask_action[i]]
        action = []
        for case in cases:
            image = index[tuple(sorted(moved[mask] for mask in case['masks']))]
            assert cases[image]['classification'] == case['classification']
            action.append(image)
        assert sorted(action) == list(range(len(cases)))
        actions.append(action)
    remaining = {i for i,case in enumerate(cases) if case['classification']=='remaining_clique_complement'}
    unvisited,orbits,needed = set(remaining),[],set()
    while unvisited:
        representative = min(unvisited)
        transports = {representative:tuple(range(7))}
        pending = deque([representative])
        while pending:
            old = pending.popleft()
            for generator,action in zip(generators,actions):
                image = action[old]
                assert image in remaining
                if image not in transports:
                    transports[image] = group_tools.compose(generator,transports[old])
                    pending.append(image)
        assert set(transports) <= unvisited
        unvisited -= set(transports)
        for image,mapping in transports.items():
            assert group_tools.automorphism(rows,mapping)
            assert sorted(group_tools.move_mask(mask,mapping) for mask in cases[representative]['masks']) == cases[image]['masks']
        case = cases[representative]
        q,size = case['quotient_order'],len(case['masks'])
        needed.update(case['masks'])
        counts['remaining_clique_orbits'] += 1
        counts['covered_remaining_cliques'] += len(transports)
        counts['representative_quotient_lower_entries'] += q*(q+1)//2
        counts['representative_full_matrix_subtractions'] += size*n*n
        counts['representative_quotient_lower_subtractions'] += size*q*(q+1)//2
        orbits.append({'representative_clique_index':representative,
            'representative_masks':case['masks'],'quotient_order':q,
            'quotient_lower_entries':q*(q+1)//2,'orbit_size':len(transports),
            'members':[{'clique_index':i,'representative_to_member_vertex_map':list(transports[i])}
                       for i in sorted(transports)]})
    assert counts['covered_remaining_cliques'] == len(remaining)
    old_by_mask = {item['mask']:item for item in old_lifts['conditional_lifts']}
    retained_lifts = []
    child_orders = {}
    for i,mask in enumerate(high):
        lift = {'mask':mask,'base_position':i+1,**lift_builder.build(root,mask,high)}
        assert lift['sparse_rows'][0] == lift['sparse_rows'][i+1] == [0]
        if mask in old_by_mask:
            assert lift == old_by_mask[mask]
            counts['retained_old_lifts_reconstructed_exactly'] += 1
        for j in old_graph.members(adjacency[i]):
            assert lift['sparse_rows'][j+1] == []
            counts['visible_incompatible_ordered_rows_checked_empty'] += 1
            if (mask&high[j]).bit_count() < 3:
                counts['new_incompatible_ordered_rows_checked_empty'] += 1
        counts['all_high_mask_lifts_reconstructed'] += 1
        if mask in needed:
            retained_lifts.append(lift)
            child_orders[lift['child_root_type']] = lift['child_base_order']
            lengths = [len(row) for row in lift['sparse_rows']]
            counts['representative_conditional_lower_products_upper_bound'] += (sum(lengths)**2+sum(v*v for v in lengths))//2
    counts['representative_conditional_lifts'] = len(retained_lifts)
    assert len(retained_lifts) == len(needed)
    conditional_cells = len(needed)*n*n
    child_cells = sum(order*order for order in child_orders.values())
    return {'root_type':root,'root_rows':rows,'high_masks':high,'base_order':n,
        'visible_incompatibility_adjacency':adjacency,
        'analytic_graph_equals_both_literal_edge_choice_domain':True,
        'bron_kerbosch_equals_incremental_enumeration':True,
        'incremental_vertex_order':addition_order,'incremental_maximal_clique_counts':intermediate_sizes,
        'maximal_cliques':cases,'old_intersection_clique_superset_indices':old_covers,
        'triple_groups_with_pair_residuals_two':triples,
        'automorphism_order':len(group),'generators':[list(g) for g in generators],
        'full_enumerated_automorphism_group_equals_generator_closure':True,
        'all_generator_domains_incompatibilities_classifications_checked':True,
        'orbits':orbits,'conditional_lifts':retained_lifts,
        'coefficientwise_individual_selected_row_identity_reused_from_full_5215_lift_certificate':True,
        'all_visible_incompatible_conditional_rows_checked_empty':True,
        'all_maximal_clique_selected_rows_vanish_coefficientwise':True,
        'conditional_matrix_object_cells':conditional_cells,'child_matrix_object_cells':child_cells,
        'two_working_matrix_object_cells':2*n*n,'counts':dict(sorted(counts.items()))}


def run(args):
    started = time.monotonic()
    for name,sha in SOURCE_BINDINGS.items():
        assert files.digest(Path(__file__).with_name(name)) == sha
    for path,sha in ((OLD_CENSUS,OLD_CENSUS_SHA),(OLD_LIFTS,OLD_LIFTS_SHA),(OLD_ORBITS,OLD_ORBITS_SHA)):
        assert files.digest(path) == sha
    assert files.digest(args.catalogue) == domains.direct.CATALOGUE_SHA
    census,lifts,orbits = read(OLD_CENSUS),read(OLD_LIFTS),read(OLD_ORBITS)
    assert census['complete_for_intersection_at_least_three_graphs']
    assert lifts['summary']['checked_high_mask_lifts'] == 5215
    assert lifts['all_7189_clique_selected_rows_vanish_coefficientwise']
    assert orbits['complete_coverage_of_all_3939_remaining_cliques']
    with args.catalogue.open('rb') as stream:
        data = pickle.load(stream)
    child_domains = {root:([mask for mask,_ in data[3][root] if mask.bit_count()>=3],None)
                     for root in data[1][8]}
    lift_builder = domains.Lifts(data,child_domains)
    old_lifts = {root['root_type']:root for root in lifts['roots']}
    old_orbits = {root['root_type']:root for root in orbits['roots']}
    result = {'source_sha256':files.digest(Path(__file__)),'source_bindings':SOURCE_BINDINGS,
        'old_intersection_census_sha256':OLD_CENSUS_SHA,'old_coefficientwise_lifts_sha256':OLD_LIFTS_SHA,
        'old_root_automorphism_ledger_sha256':OLD_ORBITS_SHA,
        'catalogue_sha256':domains.direct.CATALOGUE_SHA,
        'transport_source_sha256':domains.TRANSPORT_SHA,'roots':[],
        'point_scanned':False,'new_product_tensors_generated':False,
        'dense_reduction_loaded':False,'optimizer_called':False,
        'hypothetical_graph_automorphism_assumed':False}
    timed_out,error,current = False,None,None
    totals = Counter()
    peak_cells,peak_root,peak_conditional,peak_child = 0,None,0,0
    def deadline(_signum,_frame):
        raise TimeoutError('bounded complete visible-incompatibility preparation')
    previous = signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        for old in census['roots']:
            current = old['root_type']
            record = process_root(old,old_lifts[current],old_orbits[current],data,lift_builder)
            previous_mask = signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM})
            try:
                result['roots'].append(record)
                totals.update(record['counts'])
                cells = record['conditional_matrix_object_cells']+record['child_matrix_object_cells']+record['two_working_matrix_object_cells']
                if cells > peak_cells:
                    peak_cells,peak_root = cells,current
                peak_conditional = max(peak_conditional,record['conditional_matrix_object_cells'])
                peak_child = max(peak_child,record['child_matrix_object_cells'])
                current = None
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK,previous_mask)
    except TimeoutError:
        timed_out = True
    except Exception as problem:
        error = repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    complete = len(result['roots']) == 208
    if complete:
        assert totals['all_high_mask_lifts_reconstructed'] == 5215
        assert totals['retained_old_lifts_reconstructed_exactly'] == 1965
        assert totals['old_intersection_cliques_covered'] == 7189
        assert totals['residual_two_triple_groups'] == 530
        assert totals['new_incompatible_ordered_rows_checked_empty'] == 2*totals['new_quota_one_incompatibility_edges']
        assert totals['visible_incompatible_ordered_rows_checked_empty'] == 2*totals['visible_incompatibility_edges']
        assert totals['remaining_clique_complement'] == totals['covered_remaining_cliques']
    result.update(status='complete visible-incompatibility clique preparation' if complete else 'UNKNOWN: incomplete visible-incompatibility preparation',
        complete_root_family=complete,root_types_completed=len(result['roots']),timed_out=timed_out,error=error,
        unfinished_root_type=current,summary=dict(sorted(totals.items())),
        per_root_cache_sizing={'largest_joint_matrix_object_cells':peak_cells,'largest_joint_cache_root_type':peak_root,
            'largest_conditional_matrix_object_cells':peak_conditional,'largest_child_matrix_object_cells':peak_child,
            'illustrative_64_bytes_per_object_cell':64*peak_cells,
            'illustrative_bytes_are_not_a_runtime_RSS_guarantee':True},
        largest_representative_quotient_order=max((o['quotient_order'] for r in result['roots'] for o in r['orbits']),default=0))
    if args.replay:
        assert complete and not error and not timed_out
        old = read(args.replay)
        old.pop('seconds')
        old.pop('max_rss_kib')
        assert old == group_tools.normalise(result)
        result = {'status':'PASS: complete visible domains, both clique enumerations, lifts and orbits replayed',
            'source_sha256':files.digest(Path(__file__)),'certificate_sha256':files.digest(args.replay),
            'summary':dict(sorted(totals.items()))}
    result['seconds'] = time.monotonic()-started
    result['max_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    content = json.dumps(result,indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(content,compresslevel=9,mtime=0) if args.output.suffix=='.gz' else content)
    print(json.dumps({key:value for key,value in result.items() if key!='roots'},indent=2),flush=True)
    print('output_sha256',files.digest(args.output),flush=True)
    return 1 if error else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',type=Path)
    parser.add_argument('--seconds',type=int,default=30)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 30
    raise SystemExit(run(args))
