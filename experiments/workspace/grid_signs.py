"""Classify mod-three orientation patterns for a coordinate line of an affine grid lift."""
from itertools import combinations,product
from collections import Counter
import json
import pynauty
from triple_moments import tmp


def enumerate_signs():
    n=10;classes={};nodes=0
    for fixed0 in range(n+1):
        for fixed3 in range(n-fixed0+1):
            for fixed6 in range(n-fixed0-fixed3+1):
                deg=[0]*fixed0+[3]*fixed3+[6]*fixed6+[9]*(n-fixed0-fixed3-fixed6)
                if sum(deg)%2:continue
                rows=[0]*n
                def run(i):
                    nonlocal nodes
                    nodes+=1
                    if i==n:
                        g=pynauty.Graph(n,adjacency_dict={j:[k for k in range(n) if rows[j]>>k&1] for j in range(n)})
                        classes.setdefault(pynauty.certificate(g),tuple(rows));return
                    buckets={}
                    for j in range(i+1,n):buckets.setdefault((deg[j],rows[j]),[]).append(j)
                    blocks=list(buckets.values());remaining=deg[i]-rows[i].bit_count()
                    if remaining<0:return
                    for counts in product(*(range(len(v)+1) for v in blocks)):
                        if sum(counts)!=remaining:continue
                        selected=[j for v,z in zip(blocks,counts) for j in v[:z]]
                        r=rows[i]+sum(1<<j for j in selected)
                        if any(((r&rows[j]).bit_count()+((r>>j)&1))%3 for j in range(i)):continue
                        if any(not (0<=deg[j]-(rows[j].bit_count()+(j in selected))<=n-i-2) for j in range(i+1,n)):continue
                        old=rows[i];rows[i]=r
                        for j in selected:rows[j]|=1<<i
                        run(i+1)
                        for j in selected:rows[j]^=1<<i
                        rows[i]=old
                run(0)
    print('signed-coordinate normalized graphs',len(classes),'nodes',nodes,flush=True)
    # Restore the normalized isolated vertex and classify the two-graph by its ternary odd-triangle hypergraph.
    types={}
    for r in classes.values():
        row=r+(0,);tris=[t for t in combinations(range(11),3) if sum((row[i]>>j)&1 for i,j in combinations(t,2))%2]
        g=pynauty.Graph(11+len(tris),adjacency_dict={11+j:list(t) for j,t in enumerate(tris)},vertex_coloring=[set(range(11)),set(range(11,11+len(tris)))])
        types.setdefault(pynauty.certificate(g),dict(rows=row,triangles=tris))
    print('full switching classes',len(types),'negative-triangle distribution',Counter(len(a['triangles']) for a in types.values()),flush=True)
    (tmp/'grid-sign-types.json').write_text(json.dumps(list(types.values())))
    return list(types.values())


if __name__=='__main__':enumerate_signs()
