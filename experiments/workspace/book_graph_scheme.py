"""Pair distributions of a complete triangle book, keeping its two page signs."""
from itertools import permutations,product,combinations
from functools import lru_cache
from book_scheme import tmp
import numpy as np

def tables():
    W=np.array([v for v in product(range(3),repeat=6) if all(v.count(i)==2 for i in range(3))],dtype=np.int16)
    maps=[[3*p[a]+p[b]+d for d in (0,9) for a,b in product(range(3),repeat=2)] for p in permutations(range(3))]
    @lru_cache(None)
    def canon(x):return min(tuple(x[i] for i in p) for p in maps)
    ids={};keys=[];O=np.zeros((90,90,64),dtype=np.int16)
    # Difference words of length six have at most six nonempty bins.
    for i,u in enumerate(W):
        for j,v in enumerate(W):
            seq=3*u+v
            k=np.bincount(seq,minlength=9)
            rows=np.zeros((64,9),dtype=np.int16)
            for a,c in enumerate(seq):rows[:,c]+=(np.arange(64)>>a)&1
            for s,part in enumerate(rows):
                key=canon(tuple(map(int,k-part))+tuple(map(int,part)))
                if key not in ids:ids[key]=len(ids);keys.append(key)
                O[i,j,s]=ids[key]
    n=len(keys);oid=O[0].ravel();sizes=np.bincount(oid,minlength=n);rep=[np.flatnonzero(oid==i)[0] for i in range(n)]
    rev=[O[r//64,0,r%64] for r in rep]
    np.savez_compressed(tmp/'book-graph-orbits.npz',O=O,W=W,keys=keys,sizes=sizes,rep=rep,rev=rev)
    print('signed core orbitals',n,flush=True)
if __name__=='__main__':tables()
