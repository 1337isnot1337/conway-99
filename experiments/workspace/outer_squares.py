"""Extend conditioned rooted triple counts by integer populations of induced outer squares."""
import argparse
import json
from itertools import combinations
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from hemisphere_marginals import construct
from hemisphere_integral import integral
from triangle_ball import golay
from triple_moments import tmp


def diagonals(labels):
    i,j=np.triu_indices(len(labels),1)
    use=(labels[i,:,None]!=labels[j,None,:]).all(axis=(1,2))
    return i[use],j[use]


def catalogue(X,Q,T,tr,sizes,labels,independent):
    a,b=diagonals(labels)
    sqrows=np.unique(Q[:,a,b])
    sqrows=sqrows[sqrows!=0]
    qindex=np.full(len(sizes),-1,int)
    qindex[sqrows]=np.arange(len(sqrows))
    assert len(sqrows)<65535
    special=np.isin(np.arange(len(labels)),independent)
    records=[]
    for i,(x,y) in enumerate(zip(a,b)):
        c,d=a[:i],b[:i]
        legal=(c!=x)&(c!=y)&(d!=x)&(d!=y)
        if special[x] or special[y]:
            legal&=~special[c]&~special[d]
        c,d=c[legal],d[legal]
        corners=np.stack([Q[c,x,y],Q[d,x,y],Q[x,c,d],Q[y,c,d]],axis=1)
        u=np.sort(qindex[corners],axis=1).astype(np.uint64)
        records.append((u[:,0]<<48)|(u[:,1]<<32)|(u[:,2]<<16)|u[:,3])
    keys,cap=np.unique(np.concatenate(records),return_counts=True)
    nc=len(keys);n=len(sizes)
    C=sp.coo_matrix((np.ones(4*nc,np.int64),
        (np.concatenate([((keys>>p)&65535).astype(int) for p in (48,32,16,0)]),np.tile(np.arange(nc),4))),
        shape=(len(sqrows),nc)).tocsr()
    # Each open wedge with disjoint endpoint labels accounts for one square corner.
    tri={}
    for t,(i,j,k) in zip(T,tr):
        for center,u,v in [(i,j,k),(j,k,i),(k,i,j)]:
            w=Q[center,u,v]
            if qindex[w]>=0:
                assert tri.setdefault(w,t)==t
    tcols=np.array([tri[q] for q in sqrows])
    assert not np.any(sizes[sqrows]%sizes[tcols])
    base=sp.coo_matrix((np.r_[-np.ones(len(sqrows),np.int64),sizes[sqrows]//sizes[tcols]],
        (np.tile(np.arange(len(sqrows)),2),np.r_[sqrows,tcols])),shape=(len(sqrows),n)).tocsr()
    return sp.hstack([base,C],format='csr'),cap,keys,sqrows


def graph_control(G):
    near=np.flatnonzero(G[0]);outer=np.flatnonzero((G[0]==0)&(np.arange(len(G))!=0))
    nearsets=[set(np.flatnonzero(G[x,near])) for x in outer]
    H=G[np.ix_(outer,outer)]
    square_incidence=set()
    for i,j in combinations(range(len(outer)),2):
        if H[i,j] or nearsets[i]&nearsets[j]:continue
        c,d=np.flatnonzero(H[i]*H[j])
        assert not H[c,d] and not nearsets[c]&nearsets[d]
        square_incidence.add(tuple(sorted(((i,j),(int(c),int(d))))))
    count=0
    for c in range(len(outer)):
        for i,j in combinations(np.flatnonzero(H[c]),2):
            if H[i,j] or nearsets[i]&nearsets[j]:continue
            d,=np.flatnonzero((np.arange(len(outer))!=c)&(H[i]*H[j]>0))
            assert tuple(sorted(((int(i),int(j)),tuple(sorted((c,int(d))))))) in square_incidence
            count+=1
    assert count==4*len(square_incidence)
    print('known graph',len(G),'outside',len(H),'induced outer squares',len(square_incidence),'corners',count,flush=True)


def run(case,rook):
    L=[(0,1)] if rook else json.loads((tmp/'hemisphere-cases.json').read_text())[case][0]
    E,G,s,(X,Q,T,tr,labels)=construct(L,2 if rook else 7)
    labelmap={tuple(p):i for i,p in enumerate(labels)}
    independent=[labelmap[2*i,2*j] for i,j in L]
    D,cap,keys,sqrows=catalogue(X,Q,T,tr,s,labels,independent)
    E=sp.block_diag((integral(E,s),sp.csr_matrix((0,len(cap)),dtype=np.int64)),format='csr')
    G=sp.hstack([integral(G,s),sp.csr_matrix((G.shape[0],len(cap)),dtype=np.int64)],format='csr')
    A=sp.vstack([E,D],format='csr')
    print('square types',len(cap),'eligible labelled squares',sum(cap),'corner types',len(sqrows),'combined',A.shape,flush=True)
    if rook:
        x=np.zeros(A.shape[1],np.int64);x[0]=1
        H=np.array([[int(i!=j and len(set(a)&set(b))==1) for j,b in enumerate(labels)] for i,a in enumerate(labels)])
        for i,j in combinations(range(4),2):x[X[i,j]]+=H[i,j]
        for t,(i,j,k) in zip(T,tr):
            for c,u,v in ((i,j,k),(j,k,i),(k,i,j)):x[Q[c,u,v]]+=H[c,u]*H[c,v]
            x[t]+=H[i,j]*H[i,k]*H[j,k]
        assert len(keys)==1
        x[-1]=1
        assert not np.any(A@x) and (G@x).min()>=0 and np.all(x<=np.r_[s,cap])
        print('full rook square population verified')
    else:
        prefix=tmp/('hemisphere-squares-%d'%case)
        sp.save_npz(str(prefix)+'-eq.npz',A);sp.save_npz(str(prefix)+'-ge.npz',G)
        np.save(str(prefix)+'-bounds.npy',np.r_[s,cap])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',type=int,default=0);p.add_argument('--control',action='store_true');a=p.parse_args()
    if a.control:
        graph_control(golay()[0]);run(0,True)
    else:run(a.case,False)
