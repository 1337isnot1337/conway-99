"""Enumerate exterior signatures after complete neighborhoods have been added to a fixed core."""
from itertools import combinations
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
from broken_grid import canonical_cases,extensions


def lifts(A,B,old,centers,groups,k=14):
    n=len(A);N=len(B)
    assert n+sum(map(len,groups))==N and len(groups)==len(centers)
    r=3;parameters=[(r,-1,1/9),(4,1,-2/11)]
    cap=12*np.eye(N,dtype=int)+2-B-B@B
    if np.min(cap)<0:return np.empty((0,N),dtype=np.int16)
    decompositions=[]
    for d,adj,c in parameters:
        g=d*np.eye(N)+adj*B+c;e,U=np.linalg.eigh(g)
        if e[0]<-1e-7:return np.empty((0,N),dtype=np.int16)
        active=e>1e-7
        dimension=44 if adj==-1 else 54
        if sum(active)>dimension:return np.empty((0,N),dtype=np.int16)
        decompositions.append((d,c,adj,U[:,active]/np.sqrt(e[active]),U[:,~active],sum(active)==dimension))
    I=np.eye(N,dtype=np.int16);base=[]
    for s in old:
        if any(i in s for i in centers):continue
        if all(cap[a,b]>0 for a,b in combinations(s,2)):base.append(s)
    if not base:return np.empty((0,N),dtype=np.int16)
    mat=np.zeros((len(base),N),dtype=np.int16)
    for i,s in enumerate(base):mat[i,list(s)]=1
    # Each new exterior point must realize the exact counts against the already-complete centers.
    req=2-mat@(B+I)[:,centers]
    good=(req>=0).all(axis=1)&(req<=[len(g) for g in groups]).all(axis=1)
    req=req[good];mat=mat[good]
    results=[]
    for needs in np.unique(req,axis=0):
        Q=mat[(req==needs).all(axis=1)]
        choices=np.zeros((1,N),np.int16)
        for size,group in zip(needs,groups):
            picks=list(combinations(group,size))
            part=np.zeros((len(picks),N),np.int16)
            for i,p in enumerate(picks):part[i,list(p)]=1
            choices=(choices[:,None,:]+part[None,:,:]).reshape(-1,N)
        for start in range(0,len(Q),max(1,20000//len(choices))):
            q=Q[start:start+max(1,20000//len(choices))]
            Y=(q[:,None,:]+choices[None,:,:]).reshape(-1,N)
            ok=(Y@(B+I)<=2).all(axis=1)
            Y=Y[ok]
            # No two neighbors may already have exhausted their common-neighbor allowance.
            forbidden=(cap<=0).astype(np.int16);np.fill_diagonal(forbidden,0)
            Y=Y[(np.sum((Y@forbidden)*Y,axis=1)==0)]
            for d,c,adj,U,W,full in decompositions:
                if not len(Y):break
                y=adj*Y+c;sq=np.sum((y@U)**2,axis=1)
                ok=sq<=d+c+1e-8
                if full:ok&=sq>=d+c-1e-8
                if W.shape[1]:ok&=np.max(abs(y@W),axis=1)<1e-7
                Y=Y[ok]
            if len(Y):results.append(Y)
    return np.vstack(results) if results else np.empty((0,N),dtype=np.int16)


def cover(A,Y):
    n=len(A);r,c=np.triu_indices(n);cap=12*np.eye(n,dtype=int)+2-A-A@A
    use=cap[r,c]>0;r=r[use];c=c[use]
    t=cap[r,c]
    misses=0;mins=1e10
    for i in range(0,len(r),64):
        num=(Y[:,r[i:i+64]]*Y[:,c[i:i+64]]).sum(axis=0)
        misses+=sum(num<t[i:i+64]);mins=min(mins,min(num,default=1e10))
    return int(misses),int(mins)


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--case',type=int,default=0);p.add_argument('--count',type=int,default=3)
    a=p.parse_args();pe,c,A=list(canonical_cases())[a.case];S,_,_=extensions(A)
    for j in range(a.count):
        path='/tmp/conway99-tools/grid-core39-%d-%d.npy'%(a.case,j)
        B=np.load(path);Y=lifts(A,B,S,np.array(pe)+8,[range(27,33),range(33,39)])
        miss,mini=cover(B,Y)
        print(j,'candidate signatures',len(Y),'uncovered pair capacities',miss,'smallest supply',mini,flush=True)
        if len(Y) and not miss:
            np.savez_compressed('/tmp/conway99-tools/grid39-signatures-%d-%d.npz'%(a.case,j),Y=Y)
