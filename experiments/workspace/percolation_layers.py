"""Enumerate complete two-neighbor bootstrap layers from an induced seed."""
import argparse
from collections import Counter
from itertools import combinations
import json

import numpy as np
import pynauty

from triple_moments import tmp


def seed(kind):
    B=np.zeros((8,8),np.int16)
    for i in range(4):
        j=(i+1)%4
        for a,b in ((i,j),(i,i+4),(j,i+4)):B[a,b]=B[b,a]=1
    for i in range(kind):B[4+i,6+i]=B[6+i,4+i]=1
    return B


def signatures(B):
    n=len(B);cap=2-B-(B@B);np.fill_diagonal(cap,0)
    if np.any(cap<0):return None
    pairs=[(i,j) for i,j in combinations(range(n),2) if cap[i,j]]
    lookup={p:i for i,p in enumerate(pairs)}
    clique=[sum(1<<int(j) for j in np.flatnonzero(cap[i]>0)) for i in range(n)]
    masks=[];uses=[]
    def extend(S,candidates,lim):
        while candidates:
            bit=candidates&-candidates;candidates-=bit;i=bit.bit_length()-1
            newlim=lim+B[i];newlim[i]+=1
            if newlim.max()>2:continue
            T=S+(i,)
            if len(T)>=2:
                masks.append(sum(1<<k for k in T))
                uses.append(tuple(lookup[p] for p in combinations(T,2)))
            extend(T,candidates&clique[i],newlim)
    extend((),(1<<n)-1,np.zeros(n,np.int16))
    return pairs,np.array([cap[p] for p in pairs],int),masks,uses


def plans(B,k=14,v=99,limit=None):
    plan=signatures(B)
    if plan is None:return
    pairs,rem,masks,uses=plan
    supply=[[] for _ in pairs]
    for i,foot in enumerate(uses):
        for j in foot:supply[j].append(i)
    chosen=[];used=np.zeros(len(masks),np.uint8);degree=B.sum(axis=0).astype(int)
    def visit(steps):
        if limit is not None and steps[0]>=limit:return
        steps[0]+=1
        active=np.flatnonzero(rem);activebits=set(map(int,active))
        if not len(active):
            singles=k-degree
            if len(B)+len(chosen)+int(singles.sum())<=v:yield tuple(sorted(masks[j] for j in chosen))
            return
        eligible={}
        for j in active:
            opts=[z for z in supply[j] if used[z]<(2 if masks[z].bit_count()==2 else 1) and all(t in activebits for t in uses[z])]
            if not opts:return
            eligible[j]=opts
        j=min(active,key=lambda u:len(eligible[u]))
        # Fill this pair's entire remaining quota at once. Its deficit is one or two.
        options=eligible[j]
        from itertools import combinations_with_replacement
        for add in combinations_with_replacement(options,int(rem[j])):
            if len(add)==2 and add[0]==add[1] and (masks[add[0]].bit_count()>2 or used[add[0]]):continue
            consumed=Counter(t for z in add for t in uses[z])
            if any(rem[t]<n for t,n in consumed.items()):continue
            d=Counter(i for z in add for i in range(len(B)) if masks[z]>>i&1)
            if any(degree[i]+n>k for i,n in d.items()):continue
            for t,n in consumed.items():rem[t]-=n
            for i,n in d.items():degree[i]+=n
            for z in add:used[z]+=1
            chosen.extend(add);yield from visit(steps);del chosen[-len(add):]
            for z in add:used[z]-=1
            for t,n in consumed.items():rem[t]+=n
            for i,n in d.items():degree[i]-=n
    yield from visit([0])


def incidence(B,S):
    return np.array([[(s>>i)&1 for s in S] for i in range(len(B))],np.int16)


def canon(B,S):
    n=len(B);C=incidence(B,S);d={i:[int(j) for j in np.flatnonzero(B[i])]+[n+int(j) for j in np.flatnonzero(C[i])] for i in range(n)}
    for j in range(len(S)):d[n+j]=list(map(int,np.flatnonzero(C[:,j])))
    groups=[set(range(4)),set(range(4,8)),set(range(8,n)),set(range(n,n+len(S)))]
    return pynauty.certificate(pynauty.Graph(n+len(S),adjacency_dict=d,vertex_coloring=[g for g in groups if g]))


def check_actual():
    from triangle_ball import golay
    G=golay()[0];U=[0,1]
    if G[0,1]:U=[0,next(i for i in range(1,len(G)) if not G[0,i])]
    while True:
        more=[x for x in range(len(G)) if x not in U and G[x,U].sum()>=2]
        if not more:break
        B=G[np.ix_(U,U)]
        actual=tuple(sorted(sum(int(G[x,y])<<i for i,y in enumerate(U)) for x in more))
        assert actual in plans(B,22,243)
        U+=more
    assert len(U)==9
    print('243-vertex control recovers all three growth layers ending at a nine-grid',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--control',action='store_true');a=p.parse_args()
    if a.control:check_actual()
    catalog={}
    for kind in range(3):
        B=seed(kind);unique={};counts=Counter()
        for S in plans(B):
            key=canon(B,S);counts[len(S)]+=1
            unique.setdefault(key,S)
        print('tip links',kind,'labelled',sorted(counts.items()),'orbits',sorted(Counter(map(len,unique.values())).items()),flush=True)
        catalog[kind]=list(unique.values())
    (tmp/'percolation-layers.json').write_text(json.dumps(catalog))
