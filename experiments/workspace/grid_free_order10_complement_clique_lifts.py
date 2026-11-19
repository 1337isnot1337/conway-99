"""Exact coefficientwise preparation for seven-root clique complements.

Every high-mask conditional lift is checked against its cached parent row.
Incompatible high-mask rows are empty in each conditional lift. Together
these facts prove every selected row of every recorded clique localizer
vanishes coefficientwise. Only lifts needed for the 3,939 remaining
cliques are retained. No count point, eigensystem or optimizer is used.
"""

import argparse
from collections import Counter
import gzip
import json
from pathlib import Path
import pickle
import resource
import signal
import time

import grid_free_order10_complement_cliques as cliques
import grid_free_order10_complement_domains as domains
import grid_free_order10_projector_literal as literal
import grid_free_order10_r8s1 as transport
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
CENSUS = ROOT/'experiments/logs/moments-and-counts/order10-complement-cliques.json.gz'
CENSUS_SHA = '365faacdf5144a85730aa03c1a2638ec782303051892d27bc6803790d058fdb4'
CENSUS_SOURCE_SHA = '765f0ca7ca7ffcb16e6c518d80c70ffca99ba2c0c46d682077f1027ae47fe912'
DOMAIN_SOURCE_SHA = '4961411ec0f7671abb7e34c5dbd4ec257ac98f9bffcb745a408e979751179ed8'


def literal_control(data, lift_builder, high, free_masks, selected_group):
    """Direct adjacency and class-count control on a nine-point host."""
    root = data[1][7][0]
    rows = tuple(data[0][root])
    assert rows == (0,)*7
    host = literal.extend(rows, free_masks, 0)
    assert literal.valid(host)
    actual = Counter(free_masks)
    X = [1]+[actual[mask] for mask in high]
    assert all(value <= 1 for value in X)
    selected = [mask for mask in free_masks if mask in selected_group]
    assert len(selected) <= 1
    conditional = [[0]*len(X) for _ in X]
    for mask in selected:
        outside = 7+free_masks.index(mask)
        lift = lift_builder.build(root, mask, high)
        mapping = lift['actual_to_child_vertex_map']
        positions = {mask:i+1 for i,mask in enumerate(lift['child_high_masks'])}
        Y = [1]+[0]*len(positions)
        for vertex in range(7,len(host)):
            if vertex == outside:
                continue
            old = host[vertex] & 127
            if host[vertex] >> outside & 1:
                old |= 128
            moved = transport.transported_mask(old, mapping)
            if moved in positions:
                Y[positions[moved]] += 1
        image = [sum(Y[column] for column in row) for row in lift['sparse_rows']]
        assert image == X
        for i,a in enumerate(image):
            for j,b in enumerate(image):
                conditional[i][j] += a*b
    localizer = [[a*b-conditional[i][j] for j,b in enumerate(X)] for i,a in enumerate(X)]
    assert localizer == [[(1-len(selected))*a*b for b in X] for a in X]
    positions = [i+1 for i,mask in enumerate(high) if mask in selected_group]
    assert all(localizer[i][j] == 0 for i in positions for j in range(len(X)))
    return {'root_type':root, 'host_rows':list(host), 'outside_masks':list(free_masks),
            'group_masks':list(selected_group), 'selected_group_size_at_embedding':len(selected),
            'nonzero_parent_coordinates':[i for i,value in enumerate(X) if value],
            'literal_conditional_lift_identity':True, 'literal_localizer_identity':True,
            'scope':'A cap-compatible nine-point host; no assertion that this host is SRG(99,14,1,2).'}


def build(catalogue):
    assert files.digest(CENSUS) == CENSUS_SHA
    assert files.digest(Path(cliques.__file__)) == CENSUS_SOURCE_SHA
    assert files.digest(Path(domains.__file__)) == DOMAIN_SOURCE_SHA
    assert files.digest(catalogue) == domains.direct.CATALOGUE_SHA
    assert files.digest(domains.BASE) == domains.BASE_SHA
    assert files.digest(domains.CHILD) == domains.CHILD_SHA
    assert files.digest(Path(transport.__file__)) == domains.TRANSPORT_SHA
    census = json.loads(gzip.decompress(CENSUS.read_bytes()))
    assert census['complete_for_intersection_at_least_three_graphs']
    assert not census['timed_out']
    with catalogue.open('rb') as stream:
        data = pickle.load(stream)
    bases = {root:(flags,tensor) for root,flags,tensor in pickle.loads(domains.BASE.read_bytes())}
    child_saved = pickle.loads(gzip.decompress(domains.CHILD.read_bytes()))
    assert child_saved['point_independent'] and child_saved['complete_root_family']
    assert not child_saved['zero_flags_or_roots_removed']
    assert child_saved['construction_source_sha256'] == domains.TRANSPORT_SHA
    children = {root:(masks,tensor) for root,masks,tensor in child_saved['blocks']}
    assert sorted(children) == data[1][8] and len(bases) == 203
    lift_builder = domains.Lifts(data, children)
    totals = Counter()
    root_records = []
    peak_conditional_cells = peak_child_cells = peak_joint_cells = 0
    peak_root = None
    for record in census['roots']:
        root, high = record['root_type'], record['high_masks']
        rows = tuple(data[0][root])
        assert list(rows) == record['root_rows']
        assert high == [mask for mask,child in data[3][root] if mask.bit_count() >= 3]
        n = len(high)+1
        if not high:
            assert root not in bases
            root_records.append({'root_type':root,'base_order':1,'conditional_lifts':[],
                                 'all_high_selected_rows_equal_coefficientwise':True,
                                 'incompatible_conditional_rows_empty':True})
            continue
        flags, tensor = bases[root]
        assert [tuple(flag) for flag in flags] == [rows]+[transport.attach(rows,mask) for mask in high]
        remaining = [item for item in record['maximal_cliques']
                     if item['classification'] == 'remaining_clique_complement']
        needed = set(mask for item in remaining for mask in item['masks'])
        lifts = {}
        checks = empty_checks = 0
        for position,mask in enumerate(high,1):
            lift = lift_builder.build(root,mask,high)
            assert lift['sparse_rows'][0] == lift['sparse_rows'][position] == [0]
            child_tensor = children[lift['child_root_type']][1]
            for j,sparse in enumerate(lift['sparse_rows']):
                conditional = Counter()
                for column in sparse:
                    conditional.update(domains.entry(child_tensor,0,column))
                assert dict(conditional) == domains.entry(tensor,position,j)
                checks += 1
            for j,other in enumerate(high,1):
                if other != mask and (other & mask).bit_count() >= 3:
                    assert lift['sparse_rows'][j] == []
                    empty_checks += 1
            lifts[mask] = {'mask':mask,'base_position':position,**lift}
        for item in record['maximal_cliques']:
            for mask in item['masks']:
                selected = lifts[mask]['base_position']
                for other in item['masks']:
                    expected = [0] if other == mask else []
                    assert lifts[other]['sparse_rows'][selected] == expected
                totals['clique_selected_row_instances'] += 1
        for item in record['triple_groups_with_pair_residuals_two']:
            assert item['all_allowed_superset_masks'] == [mask for mask in high
                if mask & item['triple_mask'] == item['triple_mask']]
            totals['triple_selected_row_instances'] += len(item['all_allowed_superset_masks'])
        totals['checked_high_mask_lifts'] += len(high)
        totals['coefficientwise_selected_row_entry_comparisons'] += checks
        totals['incompatible_ordered_rows_checked_empty'] += empty_checks
        totals['retained_conditional_lifts'] += len(needed)
        conditional_cells = len(needed)*n*n
        child_types = {lifts[mask]['child_root_type'] for mask in needed}
        child_cells = sum((len(children[child][0])+1)**2 for child in child_types)
        joint_cells = conditional_cells+child_cells+2*n*n
        if joint_cells > peak_joint_cells:
            peak_joint_cells,peak_root = joint_cells,root
        peak_conditional_cells = max(peak_conditional_cells,conditional_cells)
        peak_child_cells = max(peak_child_cells,child_cells)
        for mask in needed:
            lengths = [len(sparse) for sparse in lifts[mask]['sparse_rows']]
            totals['conditional_lower_entry_products_upper_bound'] += (sum(lengths)**2+sum(x*x for x in lengths))//2
        for item in remaining:
            size, q = len(item['masks']),item['quotient_order']
            totals['full_matrix_conditional_subtractions'] += size*n*n
            totals['quotient_lower_conditional_subtractions'] += size*q*(q+1)//2
            totals['remaining_quotient_lower_entries'] += q*(q+1)//2
        root_records.append({'root_type':root,'base_order':n,
            'all_high_selected_rows_equal_coefficientwise':True,
            'coefficientwise_selected_row_entry_comparisons':checks,
            'incompatible_conditional_rows_empty':True,
            'incompatible_ordered_rows_checked_empty':empty_checks,
            'conditional_lifts':[lifts[mask] for mask in sorted(needed)],
            'distinct_child_types_needed':sorted(child_types),
            'conditional_matrix_object_cells':conditional_cells,
            'child_matrix_object_cells':child_cells,
            'two_working_matrix_object_cells':2*n*n,
            'all_selected_clique_rows_vanish_coefficientwise':True})
    assert totals['checked_high_mask_lifts'] == 5215
    assert totals['retained_conditional_lifts'] == 1965
    assert totals['remaining_quotient_lower_entries'] == 9554663
    empty_high = census['roots'][0]['high_masks']
    assert census['roots'][0]['root_rows'] == [0]*7
    triple_group = [mask for mask in empty_high if mask & 7 == 7]
    large_group = [mask for mask in empty_high if mask.bit_count() >= 5]
    controls = [literal_control(data,lift_builder,empty_high,[7,56],triple_group),
                literal_control(data,lift_builder,empty_high,[7,56],large_group),
                literal_control(data,lift_builder,empty_high,[31,96],large_group)]
    return {'status':'complete coefficientwise clique-lift preparation',
        'source_sha256':files.digest(Path(__file__)), 'census_source_sha256':CENSUS_SOURCE_SHA,
        'census_sha256':CENSUS_SHA, 'domain_source_sha256':DOMAIN_SOURCE_SHA,
        'catalogue_sha256':domains.direct.CATALOGUE_SHA,
        'base_cache_sha256':domains.BASE_SHA,'child_cache_sha256':domains.CHILD_SHA,
        'transport_source_sha256':domains.TRANSPORT_SHA,
        'summary':dict(sorted(totals.items())),
        'per_root_cache_sizing':{'largest_conditional_matrix_object_cells':peak_conditional_cells,
            'largest_child_matrix_object_cells':peak_child_cells,
            'largest_joint_matrix_object_cells':peak_joint_cells,
            'largest_joint_cache_root_type':peak_root,
            'illustrative_64_bytes_per_object_cell':64*peak_joint_cells,
            'sizing_includes_two_working_matrices':True,
            'illustrative_bytes_are_not_a_runtime_RSS_guarantee':True},
        'roots':root_records,'literal_controls':controls,
        'all_7189_clique_selected_rows_vanish_coefficientwise':True,
        'all_530_triple_group_selected_rows_vanish_coefficientwise':True,
        'no_superset_removed_due_to_other_quota_one_witness':True,
        'new_product_tensors_generated':False,'count_point_loaded':False,
        'dense_reduction_loaded':False,'optimizer_called':False}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',type=Path)
    parser.add_argument('--seconds',type=int,default=30)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 30
    started = time.monotonic()
    def deadline(_signum,_frame):
        raise TimeoutError('bounded coefficientwise clique-lift preparation')
    previous = signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        result = build(args.catalogue)
        if args.replay:
            old = json.loads(gzip.decompress(args.replay.read_bytes()))
            for key in ('seconds','max_rss_kib'):
                old.pop(key,None)
            assert old == result
            result = {'status':'PASS: all clique lifts and coefficientwise zero rows replayed',
                      'source_sha256':files.digest(Path(__file__)),
                      'certificate_sha256':files.digest(args.replay),'summary':result['summary']}
    except TimeoutError:
        result = {'status':'UNKNOWN: bounded clique-lift preparation timed out',
                  'source_sha256':files.digest(Path(__file__))}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    result['seconds'] = time.monotonic()-started
    result['max_rss_kib'] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    content = json.dumps(result,indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(content,compresslevel=9,mtime=0) if args.output.suffix=='.gz' else content)
    print(json.dumps({key:value for key,value in result.items() if key not in ('roots','literal_controls')},indent=2),flush=True)
    print('output_sha256',files.digest(args.output),flush=True)
