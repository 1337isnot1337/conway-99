"""Construct complete root cuts from bootstrap-layer signatures and extend them."""
import argparse
from itertools import combinations
import json

import numpy as np

from percolation_layers import incidence, seed
from star_reconstruct import solve
from triple_moments import tmp


def cut(B,S,k=14,v=99):
    Y=incidence(B,S)
    singles=k-B.sum(axis=0)-Y.sum(axis=1)
    assert min(singles)>=0
    N=np.column_stack([Y,np.repeat(np.eye(len(B),dtype=np.int16),singles,axis=1)])
    N=np.column_stack([N,np.zeros((len(B),v-len(B)-N.shape[1]),np.int16)])
    assert np.array_equal(B@B+B+N@N.T,(k-2)*np.eye(len(B),dtype=int)+2)
    return N


def controls():
    G=np.array([[int(i!=j and (i//3==j//3 or i%3==j%3)) for j in range(9)] for i in range(9)],np.int16)
    seen=set()
    for size in range(1,5):
        for U in combinations(range(9),size):
            V=sorted(set(range(9))-set(U));B=G[np.ix_(U,U)];Z=G[np.ix_(U,V)]
            S=tuple(sorted(sum(int(v)<<i for i,v in enumerate(row)) for row in Z.T if row.sum()>=2))
            key=B.tobytes(),S
            if key in seen:continue
            seen.add(key);N=cut(B,S,4,9)
            assert solve(B,N,np.zeros((len(V),len(V)),bool),'rook-layer',3000,1000,240,4)
    print('rook cuts reconstructed',len(seen),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--control',action='store_true');p.add_argument('--nodes',type=int,default=500);p.add_argument('--cap',type=int,default=12);p.add_argument('--seed',type=int,default=147);p.add_argument('--kind',type=int,default=1);p.add_argument('--case',type=int);a=p.parse_args()
    if a.control:controls()
    else:
        cases=json.loads((tmp/'percolation-layers.json').read_text())[str(a.kind)]
        for i,S in enumerate(cases):
            if a.case is not None and a.case!=i:continue
            B=seed(a.kind);N=cut(B,S);n=N.shape[1]
            print('tip links',a.kind,'case',i,'activated vertices',len(S),flush=True)
            if solve(B,N,np.zeros((n,n),bool),'layer-%d-%d-%d'%(a.kind,i,a.seed),a.nodes,a.cap,a.seed,14):break
