"""Test pairs of complete bridge neighborhoods against 39-vertex Gram restrictions."""
import argparse
from collections import Counter
from pathlib import Path
import numpy as np
from broken_grid import canonical_cases


def run(n,case=0):
    pe,c,A=list(canonical_cases())[case];u,v=np.array(pe)+8
    src=Path('/tmp/conway99-tools')
    stars=[np.load(src/('grid-star-%d-%d.npy'%(case,p))) for p in (u,v)]
    rng=np.random.default_rng(55661);tot=Counter();eye=np.eye(27)
    G=3*eye-A+1/9;H=4*eye+A-2/11
    inverse=[np.linalg.pinv(X,hermitian=True) for X in (G,H)]
    I=np.eye(12);count=0;nwin=0
    cap=12*np.eye(27,dtype=int)+2-A@A-A
    for rep in range(n):
        picked=np.r_[stars[0][rng.integers(len(stars[0]))],stars[1][rng.integers(len(stars[1]))]]
        S=((picked[:,None]>>np.arange(27,dtype=np.uint32))&1).astype(np.int16)
        if np.any(S.T@S>cap):continue
        K=S@S.T
        if np.any(np.triu(K,1)>2):continue
        # A new vertex has either zero or one neighbors in each half. In its
        # own half each unpaired member is matched to another unpaired member.
        own=1-np.r_[S[:6]@A[u],S[6:]@A[v]]
        other=2-np.r_[S[:6]@A[v],S[6:]@A[u]]
        U=np.flatnonzero(other[:6]);V=6+np.flatnonzero(other[6:])
        if len(U)!=len(V) or len(U)>2 or np.any(other<0) or np.any(own<0):continue
        import itertools
        base=np.zeros((12,12),dtype=np.int16)
        for offset in (0,6):
            L=offset+np.flatnonzero(own[offset:offset+6])
            if len(L)==2:base[L[0],L[1]]=base[L[1],L[0]]=1
            else:assert len(L)==0
        for w in itertools.permutations(V):
            F=base.copy()
            for l,r in zip(U,w):F[l,r]=F[r,l]=1
            if np.any(np.triu(K+F@F+F,1)>2) or np.any(S@A+F@S+S>2):continue
            tot['common']+=1
            eig=[]
            for (diag,adj,const),inv in zip(((3,-1,1/9),(4,1,-2/11)),inverse):
                q=adj*S+const;res=diag*I+adj*F+const-q@inv@q.T
                eig.append(np.linalg.eigvalsh(res)[0])
            if min(eig)<-1e-8:continue
            tot['spectrum']+=1
            if nwin<25:
                np.save(src/('grid-core39-%d-%d.npy'%(case,nwin)),np.block([[A,S.T],[S,F]]));nwin+=1
    print('branch',case,'sampled pairs',n,'admissible gluings',dict(tot),flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--pairs',type=int,default=5000);p.add_argument('--case',type=int,default=0);a=p.parse_args();run(a.pairs,a.case)
