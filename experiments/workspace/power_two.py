"""Exact bit-plane elimination and solution lifting over Z/(2^e)."""
import argparse
from itertools import product
from pathlib import Path

import numpy as np
import scipy.sparse as sp

from relax_outer3 import setup
from triple_moments import tmp


def add(a,b):
    if len(a)==1:return (a[0]^b[0],)
    if len(a)==2:return (a[0]^b[0],a[1]^b[1]^(a[0]&b[0]))
    carry=0;out=[]
    for x,y in zip(a,b):
        out.append(x^y^carry)
        carry=(x&y)|((x^y)&carry)
    return tuple(out)


def solve(A,e,verbose=False):
    """Column zero has value one. Return an independently checked solution, or None."""
    A=A.copy().tocsr();A.sum_duplicates()
    pivots={};pending=[]
    for i in np.argsort(np.diff(A.indptr),kind='stable'):
        l,r=A.indptr[i:i+2];values=A.data[l:r];cols=A.indices[l:r]
        row=tuple(sum(1<<int(j) for j in cols[(values&(1<<s))!=0]) for s in range(e))
        if any(row):pending.append(row)
    for width in range(e,0,-1):
        deferred=[]
        for row in pending:
            while row[0]>1:
                j=row[0].bit_length()-1
                p=pivots.get(j)
                if p is None:
                    pivots[j]=row;break
                row=add(row,p[:width])
            else:
                if row[0]:return None
                if any(row[1:]):deferred.append(row[1:])
        if verbose:print('modulus at this stage',2**width,'pivots',len(pivots),'remaining rows',len(deferred),flush=True)
        pending=deferred
    # At bit s the odd coefficients give a triangular system in the new digits.
    planes=[]
    for s in range(e):
        candidate=int(s==0)
        for j,p in sorted(pivots.items()):
            if len(p)<=s:continue
            v=(candidate&p[0]).bit_count()
            for t,plane in enumerate(planes):
                for u,z in enumerate(p[:s-t+1]):
                    v+=(1<<(t+u))*(plane&z).bit_count()
            # The first term counts only yet assigned digits at position s.
            lower=v-(candidate&p[0]).bit_count()
            bit=((lower>>s)+(candidate&p[0]).bit_count())&1
            if bit:candidate|=1<<j
        planes.append(candidate)
    x=np.zeros(A.shape[1],dtype=np.int64)
    for s,z in enumerate(planes):
        buf=z.to_bytes((A.shape[1]+7)//8,'little')
        x+=np.unpackbits(np.frombuffer(buf,dtype=np.uint8),bitorder='little')[:len(x)].astype(np.int64)<<s
    assert x[0]==1 and not np.any((A@x)%(2**e))
    return x


def test():
    rng=np.random.default_rng(737)
    for e in (1,2,3,4):
        n=1<<e
        for _ in range(100):
            a=rng.integers(-9,10,(5,4));a[:,2]*=2;a[3,:]*=4
            if rng.integers(2):
                x=np.r_[1,rng.integers(n,size=3)];a[:,0]=-(a[:,1:]@x[1:])%n
            expected=any(not np.any((a@np.array([1,*w]))%n) for w in product(range(n),repeat=3))
            assert (solve(sp.csr_matrix(a),e) is not None)==expected
    print('400 finite ring controls passed',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--bits',type=int,default=2);p.add_argument('--test',action='store_true');p.add_argument('--matrix',type=Path);args=p.parse_args()
    if args.test:test()
    else:
        if args.matrix:A=sp.load_npz(args.matrix)
        else:
            _,_,live=setup();A=sp.load_npz(tmp/'outer3-14-integral.npz')[:,live].tocsr()
            A=A[np.diff(A.indptr)>0];g=np.gcd.reduceat(abs(A.data),A.indptr[:-1]);A.data//=np.repeat(g,np.diff(A.indptr))
        x=solve(A,args.bits,True);print('solution exists',x is not None,flush=True)
        if x is not None:np.save(tmp/('lift-%s-%d.npy'%(args.matrix.stem if args.matrix else 'root',args.bits)),x)
