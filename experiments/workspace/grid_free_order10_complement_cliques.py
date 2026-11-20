"""Bounded complete clique-domain census for seven-root flag complements.

All root incompatibility graphs are induced subgraphs of one 99-vertex
intersection graph. Its maximal cliques are independently enumerated by
bitset Bron--Kerbosch and an explicit 477-family construction. Root
maximal cliques are maximal intersections with this universal list.
No moment matrix, optimizer or point scan is constructed here.
"""

import argparse
from collections import Counter
from functools import reduce
import gzip
import hashlib
from itertools import combinations
import json
from operator import and_
from pathlib import Path
import signal
import time


ROOT = Path(__file__).resolve().parents[2]
DOMAIN = ROOT/'experiments/logs/moments-and-counts/order10-complement-domains.json.gz'
DOMAIN_SHA = '67ab98b4e727c6de1a7e79fddec560942963b6c93fdc5901ede8b38dea5f2b30'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def members(mask):
    while mask:
        bit = mask & -mask
        mask ^= bit
        yield bit.bit_length()-1


def masks_of_size(size):
    return [sum(1 << i for i in subset) for subset in combinations(range(7), size)]


def bitset(values, positions):
    return sum(1 << positions[value] for value in values)


def universal_graph():
    masks = [mask for mask in range(128) if mask.bit_count() >= 3]
    adjacency = [sum(1 << j for j,b in enumerate(masks)
                     if i != j and (a & b).bit_count() >= 3)
                 for i,a in enumerate(masks)]
    assert len(masks) == 99
    return masks, adjacency


def bron_kerbosch(adjacency):
    result = []

    def visit(chosen, possible, excluded):
        if not possible and not excluded:
            result.append(chosen)
            return
        union = possible | excluded
        pivot = max(members(union), key=lambda i: (possible & adjacency[i]).bit_count())
        branches = possible & ~adjacency[pivot]
        while branches:
            bit = branches & -branches
            branches ^= bit
            i = bit.bit_length()-1
            visit(chosen | bit, possible & adjacency[i], excluded & adjacency[i])
            possible ^= bit
            excluded |= bit

    visit(0, (1 << len(adjacency))-1, 0)
    assert len(result) == len(set(result))
    return set(result)


def explicit_universe(masks, positions):
    result = set()
    kinds = Counter()
    for triple in masks_of_size(3):
        result.add(bitset([mask for mask in masks if mask & triple == triple], positions))
        kinds['contains_a_three_mask'] += 1
    four_families = [((), 'no_four_masks')]
    four_families.extend(((mask,), 'one_four_mask') for mask in masks_of_size(4))
    for triple in masks_of_size(3):
        outside = list(members(127 ^ triple))
        for size in (2,3,4):
            for selected in combinations(outside, size):
                four_families.append((tuple(triple | (1 << v) for v in selected),
                                      f'four_mask_star_of_size_{size}'))
    for five in masks_of_size(5):
        four_families.append((tuple(mask for mask in masks_of_size(4) if mask & five == mask),
                              'all_four_of_five'))
    for family, kind in four_families:
        clique = list(family)
        clique.extend(mask for mask in masks_of_size(5)
                      if all((mask & old).bit_count() >= 3 for old in family))
        clique.extend(masks_of_size(6))
        clique.extend(masks_of_size(7))
        code = bitset(clique, positions)
        assert code not in result
        result.add(code)
        kinds[kind] += 1
    assert sum(kinds.values()) == len(result) == 477
    return result, dict(sorted(kinds.items()))


def maximal(code, allowed, adjacency):
    common = allowed
    for i in members(code):
        assert (code ^ (1 << i)) & ~adjacency[i] == 0
        common &= adjacency[i]
    assert common == 0


def direct_allowed(rows):
    r = len(rows)
    allowed = []
    for mask in range(1 << r):
        graph = [row | (((mask >> i) & 1) << r) for i,row in enumerate(rows)]+[mask]
        if all((graph[i] & graph[j]).bit_count()+((graph[i] >> j) & 1) <= 2
               for i in range(r+1) for j in range(i)):
            allowed.append(mask)
    return allowed


def census():
    assert digest(DOMAIN) == DOMAIN_SHA
    ledger = json.loads(gzip.decompress(DOMAIN.read_bytes()))
    masks, adjacency = universal_graph()
    positions = {mask: i for i,mask in enumerate(masks)}
    enumerated = bron_kerbosch(adjacency)
    explicit, kinds = explicit_universe(masks, positions)
    assert enumerated == explicit
    universe = sorted(enumerated)
    all_nodes = (1 << 99)-1
    for clique in universe:
        maximal(clique, all_nodes, adjacency)
    root_records = []
    totals, clique_sizes, candidate_sizes = Counter(), Counter(), Counter()
    needed_lifts = set()
    for root in ledger['roots']:
        root_type, rows = root['root_type'], root['root_rows']
        allowed_masks = direct_allowed(rows)
        high = [mask for mask in allowed_masks if mask.bit_count() >= 3]
        assert allowed_masks == root['allowed_masks'] and high == root['high_masks']
        allowed = bitset(high, positions)
        projected = {clique & allowed for clique in universe}
        kept = []
        for clique in sorted(projected, key=lambda x: (-x.bit_count(),x)):
            if not any(clique & ~old == 0 for old in kept):
                kept.append(clique)
        kept.sort()
        for clique in kept:
            maximal(clique, allowed, adjacency)
        coverage = [next(i for i,old in enumerate(kept) if (clique & allowed) & ~old == 0)
                    for clique in universe]
        residuals = [(i,j,2-((rows[i] >> j) & 1)-(rows[i] & rows[j]).bit_count())
                     for i in range(7) for j in range(i)]
        records = []
        for clique in kept:
            selected = [masks[i] for i in members(clique)]
            common = reduce(and_, selected, 127)
            witness = next(([i,j,1] for i,j,q in residuals
                            if q == 1 and common >> i & 1 and common >> j & 1), None)
            if not selected:
                assert not high
                classification = 'constant_only_base'
            elif witness:
                classification = 'quota_one_redundant'
            else:
                classification = 'remaining_clique_complement'
            item = {'masks': selected,
                    'base_positions': [1+high.index(mask) for mask in selected],
                    'common_mask': common, 'classification': classification,
                    'quotient_order': len(high)+1-len(selected)}
            item['quotient_lower_entries'] = item['quotient_order']*(item['quotient_order']+1)//2
            if witness:
                pair = (1 << witness[0]) | (1 << witness[1])
                item['residual_pair_witness'] = witness
                item['other_allowed_masks_in_positive_sum'] = [mask for mask in allowed_masks
                    if mask & pair == pair and mask not in set(selected)]
            totals[classification] += 1
            clique_sizes[len(selected)] += 1
            if classification == 'remaining_clique_complement':
                totals['remaining_quotient_lower_entries'] += item['quotient_lower_entries']
                candidate_sizes[len(selected)] += 1
                needed_lifts.update((root_type, mask) for mask in selected)
            records.append(item)
        groups = []
        for triple in high:
            if triple.bit_count() != 3:
                continue
            contained = [(i,j,q) for i,j,q in residuals if triple >> i & 1 and triple >> j & 1]
            if any(q == 1 for _,_,q in contained):
                continue
            assert all(q == 2 for _,_,q in contained)
            selected = [mask for mask in high if mask & triple == triple]
            code = bitset(selected, positions)
            index = kept.index(code)
            assert records[index]['classification'] == 'remaining_clique_complement'
            groups.append({'triple_mask': triple, 'maximal_clique_index': index,
                           'all_allowed_superset_masks': selected,
                           'quotient_order': records[index]['quotient_order'],
                           'quotient_lower_entries': records[index]['quotient_lower_entries']})
            totals['triple_groups'] += 1
            totals['triple_quotient_lower_entries'] += records[index]['quotient_lower_entries']
        root_records.append({'root_type': root_type, 'root_rows': rows, 'high_masks': high,
                             'base_order': len(high)+1, 'maximal_cliques': records,
                             'universal_intersection_cover': coverage,
                             'triple_groups_with_pair_residuals_two': groups})
    assert len(root_records) == 208
    return {
        'status': 'complete intersection-clique and grouped-triple domain census',
        'source_sha256': digest(Path(__file__)), 'input_domain_sha256': DOMAIN_SHA,
        'universe_masks': masks,
        'universal_maximal_cliques': [[masks[i] for i in members(code)] for code in universe],
        'universal_independent_constructions_agree': True,
        'universal_classification_counts': kinds,
        'summary': {'universal_vertices': 99, 'universal_maximal_cliques': len(universe),
                    'root_types': len(root_records), **dict(sorted(totals.items())),
                    'root_maximal_cliques_total': sum(len(r['maximal_cliques']) for r in root_records),
                    'clique_size_histogram': dict(sorted(clique_sizes.items())),
                    'remaining_clique_size_histogram': dict(sorted(candidate_sizes.items())),
                    'distinct_conditional_lifts_needed_for_remaining_cliques': len(needed_lifts),
                    'roots_with_remaining_cliques': sum(any(c['classification']=='remaining_clique_complement' for c in r['maximal_cliques']) for r in root_records),
                    'roots_with_triple_groups': sum(bool(r['triple_groups_with_pair_residuals_two']) for r in root_records),
                    'largest_remaining_quotient_order': max(c['quotient_order'] for r in root_records for c in r['maximal_cliques'] if c['classification']=='remaining_clique_complement')},
        'roots': root_records,
        'complete_for_intersection_at_least_three_graphs': True,
        'other_incompatibility_edges_included': False,
        'new_product_tensors_generated': False, 'point_scanned': False, 'optimizer_called': False,
    }


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--seconds', type=int, default=10)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 10
    started = time.monotonic()

    def deadline(_signum, _frame):
        raise TimeoutError('bounded 99-mask clique census')

    previous = signal.signal(signal.SIGALRM, deadline)
    signal.setitimer(signal.ITIMER_REAL, args.seconds)
    try:
        result = census()
        result['timed_out'] = False
    except TimeoutError:
        result = {'status':'UNKNOWN: bounded clique preparation timed out',
                  'source_sha256':digest(Path(__file__)), 'timed_out':True,
                  'complete_for_intersection_at_least_three_graphs':False}
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, previous)
    result['seconds'] = time.monotonic()-started
    content = json.dumps(result,indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(content,compresslevel=9,mtime=0) if args.output.suffix == '.gz' else content)
    print(json.dumps({k:v for k,v in result.items() if k not in ('roots','universe_masks','universal_maximal_cliques')},indent=2),flush=True)
    print('output_sha256',digest(args.output),flush=True)
