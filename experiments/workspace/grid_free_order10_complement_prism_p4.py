"""Independent P4 classification of the prism-free pair-domain additions.

Uses only standard-library graph operations and the saved root domains.
No child catalogue, transport, moment tensor or count point is loaded.
Prism absence of single flags is independently checked on six-subsets.
"""

import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path
import signal
import time


ROOT = Path(__file__).resolve().parents[2]
LOGS = ROOT/'experiments/logs/moments-and-counts'
SCOUT = LOGS/'order10-complement-prism-scout.json.gz'
SCOUT_SHA = '7547298a08a3ed7d735367e9b81a22c9e193f54da995c3cabd6032139cf70851'
VISIBLE = LOGS/'order10-complement-visible-domains.json.gz'
VISIBLE_SHA = 'b273c84d939cefbe61cfbb2ed77721fd81c9f9c61a203d9fdbe17e674e453d10'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def prism_six_set(rows):
    for vertices in combinations(range(len(rows)),6):
        mask = sum(1 << v for v in vertices)
        if not all((rows[v]&mask).bit_count()==3 for v in vertices):
            continue
        if any(rows[a] >> b & 1 and rows[a] >> c & 1 and rows[b] >> c & 1
               for a,b,c in combinations(vertices,3)):
            return list(vertices)
    return None


def attach(rows,mask):
    r = len(rows)
    return [row | (((mask >> i)&1) << r) for i,row in enumerate(rows)]+[mask]


def induced_p4s(rows):
    result = []
    for w,x,y,z in permutations(range(len(rows)),4):
        if w > z:
            continue
        if not all(rows[a] >> b & 1 for a,b in ((w,x),(x,y),(y,z))):
            continue
        if any(rows[a] >> b & 1 for a,b in ((w,y),(w,z),(x,z))):
            continue
        result.append((w,x,y,z))
    return result


def build():
    assert digest(SCOUT)==SCOUT_SHA and digest(VISIBLE)==VISIBLE_SHA
    scout = json.loads(gzip.decompress(SCOUT.read_bytes()))
    visible = json.loads(gzip.decompress(VISIBLE.read_bytes()))
    assert scout['complete_root_family'] and visible['complete_root_family']
    old_by_root = {root['root_type']:root for root in visible['roots']}
    totals = Counter()
    records = []
    for root in scout['roots']:
        root_type,rows,high = root['root_type'],root['root_rows'],root['high_masks']
        old = old_by_root[root_type]
        assert old['root_rows']==rows and old['high_masks']==high
        root_prism = prism_six_set(rows)
        assert (root_prism is not None)==root['root_contains_prism']
        absent = {}
        for mask in high:
            witness = prism_six_set(attach(rows,mask))
            if witness is not None:
                absent[mask] = witness
            totals['single_flag_prism_tests'] += 1
        assert sorted(absent)==root['absent_high_masks']
        active = [mask for mask in high if mask not in absent]
        positions = {mask:i for i,mask in enumerate(high)}
        paths = induced_p4s(rows)
        witnesses = {}
        for w,x,y,z in paths:
            left = (1 << w)|(1 << x)|(1 << z)
            right = (1 << w)|(1 << y)|(1 << z)
            for a in active:
                if a & left != left:
                    continue
                for b in active:
                    if b & right != right or a==b:
                        continue
                    i,j = positions[a],positions[b]
                    if old['visible_incompatibility_adjacency'][i] >> j & 1:
                        continue
                    key = tuple(sorted((a,b)))
                    path = (w,x,y,z) if a==key[0] else (z,y,x,w)
                    if key not in witnesses or path < witnesses[key]:
                        witnesses[key] = path
        expected = {tuple(sorted(item['masks'])) for item in root['genuine_new_pair_edges']}
        assert set(witnesses)==expected
        rebuilt = old['visible_incompatibility_adjacency'].copy()
        all_nodes = (1 << len(high))-1
        for mask in absent:
            i = positions[mask]
            rebuilt[i] |= all_nodes ^ (1 << i)
            for j in range(len(high)):
                if i!=j:
                    rebuilt[j] |= 1 << i
        saved = []
        for (a,b),(w,x,y,z) in sorted(witnesses.items()):
            endpoints = (1 << w)|(1 << z)
            assert a&b==endpoints
            assert not (rows[w] >> z & 1) and not (rows[w]&rows[z])
            assert a & (endpoints|(1 << x)) == endpoints|(1 << x)
            assert b & (endpoints|(1 << y)) == endpoints|(1 << y)
            assert not (a >> y & 1) and not (b >> x & 1)
            host = attach(attach(rows,a),b)
            assert all((host[i]&host[j]).bit_count()+((host[i] >> j)&1)<=2
                       for i in range(len(host)) for j in range(i))
            assert prism_six_set(host) is not None
            i,j = positions[a],positions[b]
            rebuilt[i] |= 1 << j
            rebuilt[j] |= 1 << i
            saved.append({'masks':[a,b],'induced_root_path':[w,x,y,z],
                          'shared_root_pair':[w,z],'shared_pair_residual_quota':2,
                          'mutual_nonedge_prism_vertices':[w,x,y,z,7,8]})
        assert rebuilt==root['prism_free_pair_incompatibility_adjacency']
        totals['root_types_checked'] += 1
        totals['root_induced_p4s'] += len(paths)
        totals['structurally_absent_roots'] += int(root_prism is not None)
        totals['structurally_absent_high_flags'] += len(absent)
        totals['genuine_prism_pair_edges_classified_by_p4'] += len(saved)
        totals['complete_prism_graph_edges_reconstructed'] += sum(row.bit_count() for row in rebuilt)//2
        records.append({'root_type':root_type,'root_prism_six_set':root_prism,
            'absent_high_flags':[{'mask':mask,'prism_six_set':absent[mask]} for mask in sorted(absent)],
            'all_induced_root_p4s':[list(path) for path in paths],
            'genuine_pair_p4_witnesses':saved,
            'full_prism_pair_graph_reconstructed_without_child_transports':True})
    assert totals['root_types_checked']==208 and totals['single_flag_prism_tests']==5215
    assert totals['structurally_absent_roots']==3 and totals['structurally_absent_high_flags']==81
    assert totals['genuine_prism_pair_edges_classified_by_p4']==1155
    assert totals['complete_prism_graph_edges_reconstructed']==34480
    return {'status':'PASS: complete P4 classification and independent prism pair-graph replay',
        'source_sha256':digest(Path(__file__)),'scout_sha256':SCOUT_SHA,'visible_domain_sha256':VISIBLE_SHA,
        'summary':dict(sorted(totals.items())),'roots':records,
        'scope':'Conditional on absence of a triangular prism in the ambient graph.',
        'catalogue_loaded':False,'child_transports_used':False,'moment_tensors_loaded':False,
        'point_scanned':False,'clique_enumeration_performed':False,'optimizer_called':False}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--replay',type=Path)
    parser.add_argument('--seconds',type=int,default=15)
    args=parser.parse_args()
    assert not args.output.exists() and 0 < args.seconds <= 15
    started=time.monotonic()
    def deadline(_signum,_frame):
        raise TimeoutError('bounded independent P4 replay')
    previous=signal.signal(signal.SIGALRM,deadline)
    signal.setitimer(signal.ITIMER_REAL,args.seconds)
    try:
        result=build()
        if args.replay:
            old=json.loads(gzip.decompress(args.replay.read_bytes()))
            old.pop('seconds')
            assert old==result
            result={'status':'PASS: full saved P4 certificate replayed',
                'source_sha256':digest(Path(__file__)),'certificate_sha256':digest(args.replay),
                'summary':result['summary']}
    except TimeoutError:
        result={'status':'UNKNOWN: bounded P4 replay timed out','source_sha256':digest(Path(__file__))}
    finally:
        signal.setitimer(signal.ITIMER_REAL,0)
        signal.signal(signal.SIGALRM,previous)
    result['seconds']=time.monotonic()-started
    content=json.dumps(result,indent=2).encode()+b'\n'
    args.output.write_bytes(gzip.compress(content,compresslevel=9,mtime=0) if args.output.suffix=='.gz' else content)
    print(json.dumps({key:value for key,value in result.items() if key!='roots'},indent=2),flush=True)
    print('output_sha256',digest(args.output),flush=True)
