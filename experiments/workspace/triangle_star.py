"""Form all one-vertex and adjacent-pair signature domains at a triangle core."""
from itertools import combinations
import argparse
import numpy as np
from triangle_ball import evaluate,local_ball,golay
from triple_moments import tmp

def make(seed):
    if seed==0:return np.load('triangle-example.npy')
    rng=np.random.default_rng(seed)
    while True:
        mats=[]
        for i in range(3):
            p=rng.permutation(12);v=p.copy();v[p]=p[np.arange(12)^1];mats.append(v)
        B=local_ball(12,mats,rng.permutation(12))
        if np.max(np.triu(B@B+B,1))<=2:return B

def domain(B,k):
    status,data=evaluate(B,k);E,D=data;idx=np.stack(np.nonzero(D),axis=1)
    six=np.column_stack([E[i][idx[:,i]] for i in range(3)])
    N=np.zeros((len(six),len(B)),dtype=np.int16);N[np.arange(len(six))[:,None],six]=1
    Q=N@(B+np.eye(len(B),dtype=np.int16))
    keep=np.all(Q<=2,axis=1);N=N[keep];Q=Q[keep]
    return N,Q

def vecs(B,N,k):
    v=k*k//2+1;r=int((np.sqrt(4*k-7)-1)/2);s=-1-r
    out=[]
    for d,a,c in ((r,-1,(k-r)/v),(-s,1,-(k-s)/v)):
        G=d*np.eye(len(B))+a*B+c
        ev,U=np.linalg.eigh(G);act=ev>1e-8
        F=(a*N+c)@(U[:,act]/np.sqrt(ev[act]))
        diag=d+c-np.einsum('ij,ij->i',F,F)
        out.append((a,c,F,diag))
    return out

def near(B,N,Q,F,x):
    overlap=N@N[x];ok=(overlap<=1)&np.all(Q+N[x]<=2,axis=1)&np.all(N+Q[x]<=2,axis=1)
    for a,c,U,L in F:
        g=a+c-U@U[x];ok&=g*g<=L*L[x]+1e-8
    return overlap,ok

def prepare(seed,trial):
    B=make(seed);N,Q=domain(B,14);F=vecs(B,N,14)
    good=np.flatnonzero(np.sum(N*(Q-N),axis=1)==0)
    rng=np.random.default_rng(trial);x=rng.choice(good)
    overlap,ok=near(B,N,Q,F,x);C=N[ok];need=2-Q[x,3:]
    fn=tmp/('triangle-star-%d-%d'%(seed,trial))
    with fn.with_suffix('.in').open('w') as fp:
        print(len(C),*need,file=fp);print(sum(1<<int(z) for z in np.flatnonzero(N[x,3:])),file=fp)
        for row in C[:,3:]:print(sum(1<<int(z) for z in np.flatnonzero(row)),file=fp)
    np.savez_compressed(fn.with_suffix('.npz'),B=B,x=N[x])
    print(seed,trial,'core candidates',len(N),'independent signature candidates',len(good),'row candidates',len(C),'overlap 0/1',np.bincount(overlap[ok]),flush=True)

def control():
    G,B,ids=golay();out=sorted(set(range(243))-set(ids));N=G[np.ix_(out,ids)]
    Q=N@(B+np.eye(len(B),dtype=np.int16));assert np.all(Q<=2)
    F=vecs(B,N,22);E,ok=evaluate(B,22)[1]
    index=[{tuple(v):i for i,v in enumerate(group)} for group in E]
    for row in N:
        groups=np.flatnonzero(row).reshape(3,2)
        assert ok[tuple(index[i][tuple(v)] for i,v in enumerate(groups))]
    for j in (0,17,91):
        overlap,ok=near(B,N,Q,F,j)
        assert np.all(ok[G[out[j],out].astype(bool)])
    print('all 180 true exterior signatures and three full neighbor sets retained on 243 control',flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=0);p.add_argument('--trial',type=int,nargs='*',default=[1]);p.add_argument('--control',action='store_true');a=p.parse_args()
    if a.control:control()
    else:
        for t in a.trial:prepare(a.seed,t)
