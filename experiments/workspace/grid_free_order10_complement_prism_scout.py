"""Bounded prism-free pair-domain sizing, with no clique or point scan.

All old high-mask domains remain in the ledger. Absent roots/flags are
separated from new incompatibilities between prism-free single flags.
Every added conditional row is supported on structurally prism-containing
child flags. Such rows vanish only under the stated prism-zero assumption.
"""

import argparse
from collections import Counter
import gzip
from itertools import combinations
import json
from pathlib import Path
import pickle
import resource
import signal
import time

import audit_prism_zero_count_witness as independent
import grid_free_order10_complement_domains as domains
import grid_free_order10_projector_literal as literal
import grid_free_order10_scaled as files


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
VISIBLE = LOGS/'order10-complement-visible-domains.json.gz'
VISIBLE_SHA = 'b273c84d939cefbe61cfbb2ed77721fd81c9f9c61a203d9fdbe17e674e453d10'
CLOSURE = LOGS/'prism-zero-order10-zero-closure.json'
CLOSURE_SHA = 'cde1bd353eb39fe8aa713080a5acfb6ae78f3dd13244d9255c9217541060919c'
AUDIT_SOURCE_SHA = '5acb50547ba2f18a7dc7ad3f375c384131af7215cc84c4de07b1eddeaab93dcd'
DOMAIN_SOURCE_SHA = '4961411ec0f7671abb7e34c5dbd4ec257ac98f9bffcb745a408e979751179ed8'


def prism_witness(rows):
    triangles = [tuple(vertices) for vertices in combinations(range(len(rows)),3)
                 if all(rows[i] >> j & 1 for i,j in combinations(vertices,2))]
    for left,right in combinations(triangles,2):
        if set(left)&set(right):
            continue
        cross = [[j for j in right if rows[i] >> j & 1] for i in left]
        if all(len(neighbors)==1 for neighbors in cross) and len({neighbors[0] for neighbors in cross})==3:
            witness = {'left_triangle':list(left),'right_triangle':list(right),
                       'matching':[[i,neighbors[0]] for i,neighbors in zip(left,cross)]}
            assert all(sum((rows[i] >> j)&1 for i in left)==1 for j in right)
            return witness
    return None


def literal_controls():
    rows = [0]*6
    edges = [(0,1),(0,2),(1,2),(3,4),(3,5),(4,5),(0,3),(1,4),(2,5)]
    for i,j in edges:
        rows[i] |= 1 << j
        rows[j] |= 1 << i
    assert literal.valid(rows) and prism_witness(rows) is not None
    for i,j in edges:
        deleted = rows.copy()
        deleted[i] ^= 1 << j
        deleted[j] ^= 1 << i
        assert prism_witness(deleted) is None
    missing = [edge for edge in combinations(range(6),2) if edge not in edges]
    assert len(missing)==6
    for i,j in missing:
        added = rows.copy()
        added[i] |= 1 << j
        added[j] |= 1 << i
        assert not literal.valid(added)
    rook = [sum(1 << j for j in range(9) if i!=j and (i//3==j//3 or i%3==j%3)) for i in range(9)]
    assert literal.valid(rook) and prism_witness(rook) is not None
    assert prism_witness([0]*7) is None
    return {'prism_rows':rows,'prism_detected':True,'all_nine_edge_deletions_destroy_the_six_vertex_prism':True,
            'all_six_missing_edges_violate_caps':True,'nine_rook_positive_control':True,
            'empty_seven_root_negative_control':True}


def run(args):
    started = time.monotonic()
    assert files.digest(VISIBLE)==VISIBLE_SHA and files.digest(CLOSURE)==CLOSURE_SHA
    assert files.digest(Path(independent.__file__))==AUDIT_SOURCE_SHA
    assert files.digest(Path(domains.__file__))==DOMAIN_SOURCE_SHA
    assert files.digest(Path(__file__).with_name('grid_free_order10_r8s1.py'))==domains.TRANSPORT_SHA
    assert files.digest(args.catalogue)==domains.direct.CATALOGUE_SHA
    visible = json.loads(gzip.decompress(VISIBLE.read_bytes()))
    closure = json.loads(CLOSURE.read_text())
    assert visible['complete_root_family'] and visible['summary']['distinct_mask_pairs_checked']==104854
    assert closure['assumptions']['initial_zero_coordinates']==[1]
    assert closure['extension_DAG_reaches_exactly_induced_prism_types']
    assert closure['all_induced_prism_forms_vanish_after_prism_core_zeros']
    assert closure['induced_prism_count']==1443
    with args.catalogue.open('rb') as stream:
        data = pickle.load(stream)
    prefix = list(range(max(data[1][9])+1))
    assert len(prefix)==6535
    prefix_set = set(prefix)
    result = {'source_sha256':files.digest(Path(__file__)),
        'visible_domain_sha256':VISIBLE_SHA,'prism_zero_closure_sha256':CLOSURE_SHA,
        'independent_prism_detector_source_sha256':AUDIT_SOURCE_SHA,
        'conditional_lift_source_sha256':DOMAIN_SOURCE_SHA,
        'transport_source_sha256':domains.TRANSPORT_SHA,'catalogue_sha256':domains.direct.CATALOGUE_SHA,
        'assumption':'The ambient SRG(99,14,1,2) contains no triangular prism; ordinary core coordinate x1 is zero.',
        'new_zero_rows_are_conditional_on_prism_freeness':True,
        'unrestricted_coefficientwise_zero_row_claim':False,
        'literal_controls':literal_controls(),'prism_type_witnesses':{},'roots':[],
        'all_original_high_mask_domains_retained':True,'count_point_loaded':False,
        'clique_enumeration_performed':False,'point_scanned':False,
        'new_product_tensors_generated':False,'dense_reduction_loaded':False,'optimizer_called':False}
    counts = Counter()
    prism_types = set()
    timed_out,error,current = False,None,None
    def deadline(_signum,_frame):
        raise TimeoutError('bounded prism-free pair-domain sizing')
    previous = signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        expected = set(closure['prism_containing_induced_types']) & prefix_set
        for graph in prefix:
            current = ['prism_type',graph]
            rows = data[0][graph]
            witness = prism_witness(rows)
            assert (witness is not None)==independent.has_prism(rows)==(graph in expected)
            if witness is not None:
                prism_types.add(graph)
                result['prism_type_witnesses'][graph] = witness
                counts[f'prism_types_order_{len(rows)}'] += 1
            counts['catalogue_types_checked_through_order_nine'] += 1
        assert prism_types==expected and len(prism_types)==156
        child_domains = {root:([mask for mask,_ in data[3][root] if mask.bit_count()>=3],None)
                         for root in data[1][8]}
        lift_builder = domains.Lifts(data,child_domains)
        child_flag_types = {}
        for child,(masks,_) in child_domains.items():
            extensions = dict(data[3][child])
            child_flag_types[child] = [child]+[extensions[mask] for mask in masks]
        for root_record in visible['roots']:
            root = root_record['root_type']
            current = ['root_domain',root]
            rows,high = root_record['root_rows'],root_record['high_masks']
            n = len(high)
            extensions = dict(data[3][root])
            absent = {mask for mask in high if extensions[mask] in prism_types}
            root_absent = root in prism_types
            if root_absent:
                assert absent==set(high)
            lifts = {mask:lift_builder.build(root,mask,high) for mask in high}
            by_types = {mask:child_flag_types[lift['child_root_type']] for mask,lift in lifts.items()}
            adjacency = [0]*n
            genuine,local = [],Counter()
            for i,a in enumerate(high):
                for j,b in enumerate(high[:i]):
                    forward = [by_types[a][column] for column in lifts[a]['sparse_rows'][j+1]]
                    reverse = [by_types[b][column] for column in lifts[b]['sparse_rows'][i+1]]
                    assert Counter(forward)==Counter(reverse)
                    old_edge = bool(root_record['visible_incompatibility_adjacency'][i] >> j & 1)
                    assert old_edge==(not forward)
                    assert all(graph in prefix_set for graph in forward)
                    incompatible = all(graph in prism_types for graph in forward)
                    if incompatible:
                        adjacency[i] |= 1 << j
                        adjacency[j] |= 1 << i
                    local['mask_pairs_checked'] += 1
                    if incompatible and not old_edge:
                        assert forward and reverse
                        assert all(graph in prism_types for graph in forward+reverse)
                        local['added_pair_edges'] += 1
                        local['added_directed_conditional_rows_supported_only_on_prism_flags'] += 2
                        local['added_conditional_row_entries_supported_on_prism_flags'] += len(forward)+len(reverse)
                        if a in absent or b in absent:
                            local['added_edges_incident_with_absent_flag'] += 1
                        else:
                            assert not root_absent
                            actual_controls = []
                            for edge in (0,1):
                                host = literal.extend(rows,[a,b],edge)
                                if literal.valid(host):
                                    witness = prism_witness(host)
                                    assert witness is not None
                                    actual_controls.append({'mutual_edge':edge,'prism_witness':witness})
                            assert actual_controls and actual_controls[0]['mutual_edge']==0
                            genuine.append({'masks':[a,b],'canonical_continuation_types':forward,
                                            'literal_valid_edge_choice_witnesses':actual_controls})
                            local['genuine_added_edges_between_prism_free_single_flags'] += 1
                    elif a in absent or b in absent:
                        assert incompatible
            assert sum(row.bit_count() for row in adjacency)%2==0
            local['prism_incompatibility_edges'] = sum(row.bit_count() for row in adjacency)//2
            local['reconstructed_high_mask_lifts'] = n
            local['structurally_absent_high_flags'] = len(absent)
            local['structurally_active_high_flags'] = n-len(absent)
            local['absent_root_types'] = int(root_absent)
            saved = {'root_type':root,'root_rows':rows,'high_masks':high,
                'root_contains_prism':root_absent,
                'absent_high_masks':sorted(absent),'active_high_masks':[mask for mask in high if mask not in absent],
                'prism_free_pair_incompatibility_adjacency':adjacency,
                'genuine_new_pair_edges':genuine,'counts':dict(sorted(local.items()))}
            old_mask = signal.pthread_sigmask(signal.SIG_BLOCK,{signal.SIGALRM})
            try:
                result['roots'].append(saved)
                counts.update(local)
                current = None
            finally:
                signal.pthread_sigmask(signal.SIG_SETMASK,old_mask)
    except TimeoutError:
        timed_out = True
    except Exception as problem:
        error = repr(problem)
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    complete = len(result['roots'])==208
    if complete:
        assert counts['mask_pairs_checked']==104854 and counts['reconstructed_high_mask_lifts']==5215
        assert counts['absent_root_types']==3
        assert counts['added_pair_edges']==counts['added_edges_incident_with_absent_flag']+counts['genuine_added_edges_between_prism_free_single_flags']
        assert counts['added_directed_conditional_rows_supported_only_on_prism_flags']==2*counts['added_pair_edges']
    result.update(status='complete prism-free pair-domain sizing' if complete else 'UNKNOWN: incomplete prism-free pair-domain sizing',
        complete_root_family=complete,timed_out=timed_out,error=error,unfinished_case=current,
        summary=dict(sorted(counts.items())),
        largest_original_high_domain=max((len(r['high_masks']) for r in result['roots']),default=0),
        largest_active_high_domain=max((len(r['active_high_masks']) for r in result['roots']),default=0),
        roots_with_genuine_added_edges=sum(bool(r['genuine_new_pair_edges']) for r in result['roots']),
        seconds=time.monotonic()-started,max_rss_kib=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
    content = json.dumps(result,indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(content,compresslevel=9,mtime=0) if args.output.suffix=='.gz' else content)
    print(json.dumps({key:value for key,value in result.items() if key not in ('roots','prism_type_witnesses','literal_controls')},indent=2),flush=True)
    print('output_sha256',files.digest(args.output),flush=True)
    return 1 if error else 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--catalogue',type=Path,default=Path('/tmp/conway99-order10-catalogue.pickle'))
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--seconds',type=int,default=30)
    args = parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 30
    raise SystemExit(run(args))
