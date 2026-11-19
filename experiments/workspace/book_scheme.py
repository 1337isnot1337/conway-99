"""Two-point orbit algebra and pair marginals of the unsigned/signed book code."""
from itertools import combinations,permutations,product
from functools import lru_cache
from collections import Counter
import numpy as np
from scipy.optimize import linprog
from scipy.linalg import qr
from triple_moments import tmp

def orbit_tables():
    W=np.array([v for v in product(range(3),repeat=6) if all(v.count(i)==2 for i in range(3))],dtype=np.int16)
    group=list(permutations(range(3)))
    mappings=[[3*p[a]+p[b] for a,b in product(range(3),repeat=2)]+[9+x for x in p] for p in group]
    @lru_cache(None)
    def canon(x):return min(tuple(x[i] for i in p) for p in mappings)
    ids={};keys=[];O=np.zeros((90,90,64),dtype=np.int16)
    for i,u in enumerate(W):
        for j,v in enumerate(W):
            cc=tuple(map(int,np.bincount(3*u+v,minlength=9)))
            masks=[sum(1<<int(k) for k in np.flatnonzero((u==a)&(v==a))) for a in range(3)]
            for s in range(64):
                key=canon(cc+tuple((m&~s).bit_count() for m in masks))
                if key not in ids:ids[key]=len(ids);keys.append(key)
                O[i,j,s]=ids[key]
    return W,np.array(keys),O

def setup():
    fn=tmp/'book-scheme.npz'
    if fn.exists():return dict(np.load(fn))
    W,keys,O=orbit_tables();n=len(keys);oid=O[0].ravel();sizes=np.bincount(oid,minlength=n)
    reps=[np.flatnonzero(oid==i)[0] for i in range(n)]
    rev=np.array([O[r//64,0,r%64] for r in reps])
    full=np.zeros((n,n,n),dtype=np.int32)
    for i,r in enumerate(reps):
        vs=O[r//64][:,np.arange(64)^(r%64)].ravel()
        full[i]=np.bincount(oid*n+vs,minlength=n*n).reshape((n,n))
    ok=np.array([sum(k[9:])<=2 and max(k[9:])<=1 for k in keys]);ok[oid[0]]=True
    # Compress transposed pair-orbits to their common variable.
    ids=sorted({min(i,rev[i]) for i in np.flatnonzero(ok)});m=len(ids)
    convert=np.zeros((n,m),int)
    for i in np.flatnonzero(ok):convert[i,ids.index(min(i,rev[i]))]=1
    symbol=2*np.repeat(W,64,axis=0)+((np.arange(5760)%64)[:,None]>>np.arange(6)&1)
    rows=[];rhs=[]
    def add(eq,target):rows.append(eq@convert);rhs.append(target)
    identity=np.zeros(n,int);identity[oid[0]]=1;add(identity,1)
    for i,j in combinations(range(6),2):
        for a,b in product(range(6),repeat=2):
            sel=(symbol[:,i]==a)&(symbol[:,j]==b)
            add(np.bincount(oid[sel],minlength=n),1 if a//2==b//2 else 2)
    A=np.array(rows);b=np.array(rhs)
    Q,R,p=qr(A.T,mode='economic',pivoting=True);rank=sum(abs(R.diagonal())>1e-8)
    assert np.linalg.matrix_rank(np.column_stack((A,b)))==rank
    B=(full@convert)*sizes[:,None,None]
    assert np.all(B==B.swapaxes(0,1))
    out=dict(A=A[p[:rank]],b=b[p[:rank]],B=B,keys=keys,ids=ids,sizes=sizes,rev=rev,base=oid[0])
    np.savez_compressed(fn,**out);return out

def solve():
    data=setup();A,b,B=data['A'],data['b'],data['B']
    n=len(B);scale=np.sqrt(data['sizes']);B=B/scale[:,None,None]/scale[None,:,None]
    print('all orbitals',n,'symmetric allowed variables',A.shape[1],'marginal rank',len(A),flush=True)
    cuts=[];rng=np.random.default_rng(923)
    for i in range(400):
        lp=linprog(rng.normal(size=A.shape[1]) if i==0 else np.zeros(A.shape[1]),
                  A_eq=A,b_eq=b,A_ub=np.array(cuts) if cuts else None,b_ub=np.zeros(len(cuts)) if cuts else None,bounds=(0,1),method='highs')
        if not lp.success:print('LP',lp.status,'cuts',len(cuts),flush=True);return
        e,U=np.linalg.eigh(B@lp.x)
        if e[0]>-1e-6:print('PSD numerical, smallest eigenvalue',e[0],'iteration',i,flush=True);np.save(tmp/'book-scheme-point.npy',lp.x);return
        for v in U[:,e < -1e-6].T:cuts.append(-np.einsum('i,ijk,j->k',v,B,v))
    print('cut limit',len(cuts),'smallest eigenvalue',e[0],flush=True)
if __name__=='__main__':solve()
