"""Relate root-averaged cubic moments to ordinary induced subgraph populations."""
import argparse
from itertools import combinations
from math import perm
from pathlib import Path
import pickle
from functools import lru_cache
import numpy as np
from pynauty import certificate
from subgraph_counts import nauty
from triple_moments import Triples,tmp


def partial(model,edges):
    selected=sorted({int(x) for x in edges if x})
    outside=sorted({v for e in selected for v in model.pairs[e]})
    near=sorted({a for v in outside for a in model.labels[v]})
    n=1+len(near)+len(outside)
    vpos={v:1+len(near)+j for j,v in enumerate(outside)}
    apos={v:1+j for j,v in enumerate(near)}
    rows=[0]*n
    def edge(i,j):rows[i]|=1<<j;rows[j]|=1<<i
    for v,i in apos.items():
        edge(0,i)
        if v%2==0 and v+1 in apos:edge(i,apos[v+1])
    for v,i in vpos.items():
        for a in model.labels[v]:edge(apos[a],i)
    for e in selected:
        i,j=model.pairs[e];edge(vpos[i],vpos[j])
    unknown=[(i,j) for i,j in combinations(vpos.values(),2) if not rows[i]>>j&1]
    s=len({v//2 for v in near})
    return rows,unknown,s


def derive(t):
    g,levels,aut,cores,scale,inj,ind=pickle.load(open('moments-order9.pickle','rb'))
    ids={(len(h),certificate(nauty(h))):i for i,h in enumerate(g) if h}
    @lru_cache(maxsize=100000)
    def lookup(h):return ids.get((len(h),certificate(nauty(h))),-1)
    witnesses=[];H=[];den=[];sectors={}
    for j,rep in enumerate(t.reps):
        rows,unknown,s=partial(t.model,rep)
        if len(rows)>len(levels)-1:continue
        ds=99*2**s*perm(7,s)
        result=np.zeros(ind.shape[1],dtype=object)
        for mask in range(1<<len(unknown)):
            a=rows.copy()
            for b,(v,w) in enumerate(unknown):
                if mask>>b&1:a[v]|=1<<w;a[w]|=1<<v
            h=lookup(tuple(a))
            if h<0:continue
            result+=aut[h]*ind[h]
        witnesses.append(j);H.append(result);den.append(scale*ds)
        sectors[len(rows)]=sectors.get(len(rows),0)+1
    H=np.array(H,dtype=np.int64);den=np.array(den,dtype=np.int64)
    print('ordinary subgraph links',len(H),'by size',sectors,flush=True)
    assert H[0,0]==den[0] and not np.any(H[0,1:])
    return np.array(witnesses),H,den


def rook_check():
    t=Triples(4);m=t.model
    rook=np.array([[int(i!=j and (i//3==j//3 or i%3==j%3)) for j in range(9)] for i in range(9)])
    x=np.load(tmp/'outer3-4-point.npy')
    for k,rep in enumerate(t.reps):
        rows,unknown,s=partial(m,rep)
        # Count embeddings directly by backtracking through the nine vertices of the known graph.
        unset={tuple(sorted(e)) for e in unknown}
        def rec(taken):
            i=len(taken)
            if i==len(rows):return 1
            return sum(rec(taken+[v]) for v in range(9) if v not in taken and all((j,i) in unset or rook[z,v]==((rows[i]>>j)&1) for j,z in enumerate(taken)))
        count=rec([])
        assert count==round(x[k]*9*2**s*perm(2,s))
    print('all',t.d,'rooting identities match actual labeled embeddings of the rook graph')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rook',action='store_true');a=p.parse_args()
    if a.rook:rook_check()
    else:
        t=Triples(14);ids,H,den=derive(t)
        np.savez_compressed(tmp/'reroot-9.npz',ids=ids,H=H,den=den)
