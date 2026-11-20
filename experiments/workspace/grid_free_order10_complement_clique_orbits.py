"""Complete root-automorphism quotient of seven-root clique complements.

Root automorphisms are enumerated directly among all degree-preserving
vertex permutations. Their small generating sets are checked by explicit
closure. Every generator preserves the full high-mask domain, the
intersection graph and every recorded clique classification. Saved
transports cover all 3,939 remaining cliques. No host symmetry is assumed.
"""

import argparse
from collections import Counter, deque
import gzip
import hashlib
from itertools import permutations, product
import json
from pathlib import Path
import resource
import signal
import time

import grid_free_order10_complement_cliques as cliques


ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT/'experiments/logs/moments-and-counts/order10-complement-cliques.json.gz'
CENSUS_SHA = '365faacdf5144a85730aa03c1a2638ec782303051892d27bc6803790d058fdb4'
CENSUS_SOURCE_SHA = '765f0ca7ca7ffcb16e6c518d80c70ffca99ba2c0c46d682077f1027ae47fe912'
LIFTS = ROOT/'experiments/logs/moments-and-counts/order10-complement-clique-lifts.json.gz'
LIFTS_SHA = 'c92a8ad205545a75f67cdffc43011db21f687f14722109a03f2b34f6490c5c28'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def normalise(obj):
    return json.loads(json.dumps(obj))


def move_mask(mask, mapping):
    return sum(1 << mapping[i] for i in range(len(mapping)) if mask >> i & 1)


def automorphism(rows, mapping):
    return sorted(mapping) == list(range(len(rows))) and all(
        move_mask(row,mapping) == rows[mapping[i]] for i,row in enumerate(rows))


def all_automorphisms(rows):
    classes = {}
    for i,row in enumerate(rows):
        classes.setdefault(row.bit_count(),[]).append(i)
    blocks = [classes[d] for d in sorted(classes)]
    group = set()
    candidates = 0
    for targets in product(*(permutations(block) for block in blocks)):
        mapping = list(range(len(rows)))
        for source,target in zip(blocks,targets):
            for i,j in zip(source,target):
                mapping[i] = j
        candidates += 1
        if automorphism(rows,mapping):
            group.add(tuple(mapping))
    return group,candidates


def compose(left,right):
    return tuple(left[right[i]] for i in range(len(right)))


def closure(generators,n):
    identity = tuple(range(n))
    seen, pending = {identity},deque([identity])
    while pending:
        old = pending.popleft()
        for generator in generators:
            image = compose(generator,old)
            if image not in seen:
                seen.add(image)
                pending.append(image)
    return seen


def generators_for(group,n):
    generators, generated = [],{tuple(range(n))}
    for element in sorted(group):
        if element not in generated:
            generators.append(element)
            generated = closure(generators,n)
    assert generated == group
    return generators


def build():
    assert digest(CENSUS) == CENSUS_SHA and digest(LIFTS) == LIFTS_SHA
    assert digest(Path(cliques.__file__)) == CENSUS_SOURCE_SHA
    census = json.loads(gzip.decompress(CENSUS.read_bytes()))
    old = dict(census)
    assert old.pop('timed_out') is False
    old.pop('seconds')
    assert normalise(cliques.census()) == old
    lifts = json.loads(gzip.decompress(LIFTS.read_bytes()))
    assert lifts['all_7189_clique_selected_rows_vanish_coefficientwise']
    lifted = {r['root_type']:r for r in lifts['roots']}
    totals, orbit_sizes = Counter(),Counter()
    records = []
    peak_cells = peak_conditional_cells = peak_child_cells = 0
    peak_root = None
    for root in census['roots']:
        rows, high = root['root_rows'],root['high_masks']
        root_type, n = root['root_type'],root['base_order']
        group,candidate_count = all_automorphisms(rows)
        generators = generators_for(group,7)
        totals['degree_preserving_vertex_permutations_checked'] += candidate_count
        totals['root_automorphisms_enumerated'] += len(group)
        totals['generators_verified'] += len(generators)
        cases = root['maximal_cliques']
        index = {tuple(c['masks']):i for i,c in enumerate(cases)}
        assert len(index) == len(cases)
        triples = {g['triple_mask'] for g in root['triple_groups_with_pair_residuals_two']}
        actions = []
        for generator in generators:
            assert automorphism(rows,generator)
            move = [move_mask(mask,generator) for mask in range(128)]
            assert sorted(move[mask] for mask in high) == high
            assert {move[mask] for mask in triples} == triples
            for i,a in enumerate(high):
                for b in high[:i]:
                    assert ((a&b).bit_count()>=3) == ((move[a]&move[b]).bit_count()>=3)
            action = []
            for case in cases:
                image = index[tuple(sorted(move[mask] for mask in case['masks']))]
                assert cases[image]['classification'] == case['classification']
                action.append(image)
            assert sorted(action) == list(range(len(cases)))
            actions.append(action)
        remaining = {i for i,c in enumerate(cases) if c['classification']=='remaining_clique_complement'}
        unvisited = set(remaining)
        orbits = []
        needed = set()
        while unvisited:
            representative = min(unvisited)
            transports = {representative:tuple(range(7))}
            pending = deque([representative])
            while pending:
                case_index = pending.popleft()
                for generator,action in zip(generators,actions):
                    image = action[case_index]
                    assert image in remaining
                    if image not in transports:
                        transports[image] = compose(generator,transports[case_index])
                        pending.append(image)
            assert set(transports) <= unvisited
            unvisited -= set(transports)
            for image,mapping in transports.items():
                assert automorphism(rows,mapping)
                assert sorted(move_mask(mask,mapping) for mask in cases[representative]['masks']) == cases[image]['masks']
                assert cases[image]['quotient_order'] == cases[representative]['quotient_order']
            chosen = cases[representative]
            needed.update(chosen['masks'])
            size, q = len(chosen['masks']),chosen['quotient_order']
            totals['representative_quotient_lower_entries'] += q*(q+1)//2
            totals['representative_full_matrix_subtractions'] += size*n*n
            totals['representative_quotient_lower_subtractions'] += size*q*(q+1)//2
            totals['covered_remaining_cliques'] += len(transports)
            totals['remaining_clique_orbits'] += 1
            orbit_sizes[len(transports)] += 1
            orbits.append({'representative_clique_index':representative,
                'representative_masks':chosen['masks'],'orbit_size':len(transports),
                'quotient_order':q,'quotient_lower_entries':q*(q+1)//2,
                'members':[{'clique_index':i,'representative_to_member_vertex_map':list(transports[i])}
                           for i in sorted(transports)]})
        assert sum(o['orbit_size'] for o in orbits) == len(remaining)
        by_mask = {item['mask']:item for item in lifted[root_type]['conditional_lifts']}
        assert needed <= set(by_mask)
        child_orders = {by_mask[mask]['child_root_type']:by_mask[mask]['child_base_order'] for mask in needed}
        conditional_cells = len(needed)*n*n
        child_cells = sum(order*order for order in child_orders.values())
        cells = conditional_cells+child_cells+2*n*n
        if cells > peak_cells:
            peak_cells,peak_root = cells,root_type
        peak_conditional_cells = max(peak_conditional_cells,conditional_cells)
        peak_child_cells = max(peak_child_cells,child_cells)
        totals['representative_conditional_lifts'] += len(needed)
        for mask in needed:
            lengths = [len(row) for row in by_mask[mask]['sparse_rows']]
            totals['representative_conditional_lower_products_upper_bound'] += (sum(lengths)**2+sum(k*k for k in lengths))//2
        records.append({'root_type':root_type,'root_rows':rows,'base_order':n,
            'automorphism_order':len(group),'degree_preserving_permutations_checked':candidate_count,
            'generators':[list(g) for g in generators],
            'generator_closure_equals_all_enumerated_automorphisms':True,
            'all_generator_domains_incompatibilities_classifications_checked':True,
            'orbits':orbits,'conditional_masks_needed_for_representatives':sorted(needed),
            'conditional_matrix_object_cells':conditional_cells,'child_matrix_object_cells':child_cells,
            'two_working_matrix_object_cells':2*n*n})
    assert totals['covered_remaining_cliques'] == 3939 and len(records) == 208
    return {'status':'complete root-automorphism quotient of remaining clique complements',
        'source_sha256':digest(Path(__file__)),'census_source_sha256':CENSUS_SOURCE_SHA,
        'census_sha256':CENSUS_SHA,'coefficientwise_lifts_sha256':LIFTS_SHA,
        'complete_census_replayed':True,'summary':dict(sorted(totals.items())),
        'orbit_size_histogram':dict(sorted(orbit_sizes.items())),
        'largest_representative_quotient_order':max(o['quotient_order'] for r in records for o in r['orbits']),
        'per_root_cache_sizing':{'largest_conditional_matrix_object_cells':peak_conditional_cells,
            'largest_child_matrix_object_cells':peak_child_cells,'largest_joint_matrix_object_cells':peak_cells,
            'largest_joint_cache_root_type':peak_root,'illustrative_64_bytes_per_object_cell':64*peak_cells,
            'illustrative_bytes_are_not_a_runtime_RSS_guarantee':True},
        'roots':records,'complete_coverage_of_all_3939_remaining_cliques':True,
        'congruence_uses_only_relabeling_of_root_embeddings':True,
        'hypothetical_graph_automorphism_assumed':False,
        'point_dependent_pruning':False,'point_scanned':False,'new_product_tensors_generated':False,
        'dense_reduction_loaded':False,'optimizer_called':False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',type=Path)
    parser.add_argument('--seconds',type=int,default=15)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 15
    started = time.monotonic()
    def deadline(_signum,_frame):
        raise TimeoutError('bounded root-automorphism clique preparation')
    previous = signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        result = build()
        if args.replay:
            old = json.loads(gzip.decompress(args.replay.read_bytes()))
            old.pop('seconds')
            old.pop('max_rss_kib')
            assert old == normalise(result)
            result = {'status':'PASS: full clique orbit partition and transports replayed',
                'source_sha256':digest(Path(__file__)),'certificate_sha256':digest(args.replay),
                'summary':result['summary']}
    except TimeoutError:
        result = {'status':'UNKNOWN: bounded orbit preparation timed out',
                  'source_sha256':digest(Path(__file__)),'complete_coverage_of_all_3939_remaining_cliques':False}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    result['seconds'] = time.monotonic()-started
    result['max_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    content = json.dumps(result,indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(content,compresslevel=9,mtime=0) if args.output.suffix=='.gz' else content)
    print(json.dumps({key:value for key,value in result.items() if key!='roots'},indent=2),flush=True)
    print('output_sha256',digest(args.output),flush=True)
