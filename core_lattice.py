"""Short projected integer vectors in the incomplete-grid cores, checked by integer norm."""
from collections import Counter
from math import ceil,floor,sqrt
import numpy as np
from flint import fmpz_mat
from broken_grid import canonical_cases


def vectors(A,cut):
    D=27*np.eye(len(A),dtype=np.int64)-9*A+1
    # The one primitive relation has last coefficient -1.
    kernel=np.r_[np.full(4,7),np.full(4,6),np.ones(6,dtype=int),-np.ones(13,dtype=int)]
    assert np.all(D@kernel==0)
    H=fmpz_mat(D[:-1,:-1].tolist())
    L,T=H.lll(transform=True,rep='gram',gram='exact')
    assert L==T*H*T.transpose()
    reduced=np.array(L.tolist(),dtype=np.int64);trans=np.array(T.tolist(),dtype=np.int64)
    R=np.linalg.cholesky(reduced).T
    u=np.zeros(len(R),dtype=np.int64)
    def visit(i,left):
        if i<0:
            if np.any(u):
                v=np.r_[u@trans,0]
                n=int(v@D@v)
                if n<=cut:yield v,n
            return
        b=R[i,i+1:]@u[i+1:]
        span=sqrt(max(0,left))+1.e-8
        for j in range(ceil((-span-b)/R[i,i]),1+floor((span-b)/R[i,i])):
            u[i]=j
            yield from visit(i-1,left-(b+R[i,i]*j)**2)
    yield from visit(len(R)-1,cut)


if __name__=='__main__':
    for i,(pe,c,A) in enumerate(canonical_cases()):
        hist=Counter((n,int(v.sum())%9) for v,n in vectors(A,36))
        print(i,dict(sorted(hist.items())),flush=True)
