"""Direct order-ten host controls for the core-triangle conditioned tensors.

This control imports no tensor constructor. It enumerates labelled roots
and ordered triangle pairs in selected literal ten-vertex hosts.
"""
import argparse
from collections import Counter
import gzip
import hashlib
from itertools import combinations, permutations
import json
from pathlib import Path
import pickle
import time
import pynauty

CATALOGUE_SHA='1e1afe93518b0b3707031eed987b19e49bb237ea85e9165ae0f25f2b07a82057'
MODEL_GZIP_SHA='8f398368e80ff36cba74969c8526b660c21155476b7d3cd58e0f0b7c81aeb9a0'
MODEL_RAW_SHA='8bd186531a14656a2ecf06857742532b26ff53fa3fb4f75cc2b6bd8322e51ef6'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def induced(rows,vertices):
    return tuple(sum(((rows[u]>>v)&1)<<j for j,v in enumerate(vertices)) for u in vertices)

def canonical(rows):
    graph=pynauty.Graph(len(rows),directed=False,adjacency_dict={i:[j for j in range(len(rows)) if rows[i]>>j&1] for i in range(len(rows))})
    return pynauty.certificate(graph)

def triangles(rows):
    return [t for t in combinations(range(len(rows)),3) if all(rows[a]>>b&1 for a,b in combinations(t,2))]

def q(rows,t,u):
    overlap=len(set(t)&set(u))
    if overlap==3:return 120
    if overlap==1:return -20
    assert overlap==0
    cross=sum(rows[a]>>b&1 for a in t for b in u)
    assert cross<=3
    return 7*cross-6

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--catalogue',type=Path,required=True)
    p.add_argument('--model',type=Path,required=True)
    args=p.parse_args();started=time.monotonic()
    raw=args.catalogue.read_bytes();assert digest(raw)==CATALOGUE_SHA
    graphs,levels,_,_=pickle.loads(raw)
    compressed=args.model.read_bytes();assert digest(compressed)==MODEL_GZIP_SHA
    raw=gzip.decompress(compressed);assert digest(raw)==MODEL_RAW_SHA
    spec=json.loads(raw)
    assert [b['root_type'] for b in spec['blocks']]==[14,15]
    selections={}
    for block in spec['blocks']:
        ids=sorted({t for _,t,c in block['terms'] if c and len(graphs[t])==10})
        assert ids
        selections[block['root_type']]=[ids[0],ids[len(ids)//2],ids[-1]]
    hosts=sorted({t for values in selections.values() for t in values})
    lookup={(n,canonical(graphs[t])):t for n in range(4,10) for t in levels[n]}
    reports=[]
    for host in hosts:
        assert time.monotonic()-started<30
        rows=graphs[host];assert len(rows)==10
        ts=triangles(rows)
        counts=Counter({host:1})
        for n in range(4,10):
            for subset in combinations(range(10),n):
                counts[lookup[n,canonical(induced(rows,subset))]]+=1
        root_reports=[]
        for domain,block in zip(spec['domains'],spec['blocks']):
            n=len(domain['classes'])
            labels={(c['root_intersection_mask'],tuple(c['outside_masks'])):i for i,c in enumerate(domain['classes'])}
            expected=[[0]*n for _ in range(n)]
            for entry,t,c in block['terms']:
                if not counts[t]:continue
                i=0
                while (i+1)*(i+2)//2<=entry:i+=1
                j=entry-i*(i+1)//2
                expected[i][j]+=c*counts[t]
                if i!=j:expected[j][i]+=c*counts[t]
            direct=[[0]*n for _ in range(n)]
            ordered_pairs=labelled_roots=0
            for root_set in combinations(range(10),4):
                fixed=[t for t in ts if set(t).issubset(root_set)]
                if len(fixed)!=1:continue
                fixed=fixed[0]
                for root in permutations(root_set):
                    if induced(rows,root)!=tuple(domain['root_rows']):continue
                    labelled_roots+=1
                    class_ids=[]
                    for t in ts:
                        inside=sum(1<<i for i,v in enumerate(root) if v in t)
                        outside=tuple(sorted(sum(((rows[v]>>u)&1)<<i for i,u in enumerate(root)) for v in t if v not in root))
                        class_ids.append(labels[inside,outside])
                    for i,t in enumerate(ts):
                        for j,u in enumerate(ts):
                            direct[class_ids[i]][class_ids[j]]+=120*q(rows,t,u)-q(rows,fixed,t)*q(rows,fixed,u)
                            ordered_pairs+=1
            assert direct==expected,(host,domain['root_type'])
            root_reports.append({'root_type':domain['root_type'],'order':n,'labelled_roots':labelled_roots,
                'ordered_triangle_pairs':ordered_pairs,'all_entries_match':True,
                'matrix_sha256':digest(json.dumps(direct,separators=(',',':')).encode())})
        reports.append({'host_type':host,'host_order':10,'all_induced_subsets_counted':sum(counts.values()),'roots':root_reports})
    assert all(any(r['host_type']==host for r in reports) for values in selections.values() for host in values)
    print(json.dumps({'status':'PASS_INDEPENDENT_LITERAL_ORDER_TEN_HOST_CONTROLS',
        'source_sha256':digest(Path(__file__).read_bytes()),'catalogue_sha256':CATALOGUE_SHA,
        'conditioned_model_raw_sha256':MODEL_RAW_SHA,'conditioned_model_gzip_sha256':MODEL_GZIP_SHA,
        'selection_by_root':selections,'hosts':reports,'constructor_imported':False,
        'count_point_loaded':False,'optimizer_called':False,
        'seconds':time.monotonic()-started},indent=2))
if __name__=='__main__':
    main()
