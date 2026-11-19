"""Can the possible exterior signatures meet all codegree quotas of a given core?"""
import argparse
from pathlib import Path
from math import gcd
from functools import reduce
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog


def system(A,Y):
    n=len(A);r,c=np.triu_indices(n);cap=12*np.eye(n,dtype=int)+2-A-A@A
    use=cap[r,c]>0;r=r[use];c=c[use]
    pieces=[sp.csr_matrix((Y[:,r[i:i+32]]*Y[:,c[i:i+32]]).T) for i in range(0,len(r),32)]
    return sp.vstack([*pieces,np.ones((1,len(Y)),dtype=np.int16)],format='csr'),np.r_[cap[r,c],99-n]


def phase(A,b):
    # min total absolute residual. Its LP dual is bounded in [-1,1] and may yield an exact separating row.
    n=A.shape[0];obj=np.r_[np.zeros(A.shape[1]),np.ones(2*n)]
    E=sp.hstack([A,sp.eye(n),-sp.eye(n)],format='csr')
    return linprog(obj,A_eq=E,b_eq=b,bounds=(0,None),method='highs',options={'time_limit':60})


def test(case,count):
    for j in range(count):
        stem=Path('/tmp/conway99-tools');B=np.load(stem/('grid-core39-%d-%d.npy'%(case,j)))
        name=stem/('grid39-signatures-%d-%d.npz'%(case,j))
        if not name.exists():continue
        Y=np.load(name)['Y'];M,b=system(B,Y)
        res=phase(M,b)
        if not res.success:print(j,'solver',res.message,flush=True);continue
        gap=res.fun
        if gap>1.e-7:
            for scale in (6,60,600,6000,60000,1000000):
                dual=np.rint(res.eqlin.marginals*scale).astype(np.int64)
                excess=max(0,int((dual@M).max()))
                dual[-1]-=excess
                if dual@b>0:
                    np.savez_compressed(stem/('grid39-dual-%d-%d.npz'%(case,j)),dual=dual)
                    print(j,'separating integer functional, gap',dual@b,'LP gap',gap,flush=True);break
            else:print(j,'unrounded dual',gap,flush=True)
        else:print(j,'fractional cover',gap,flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',type=int,default=0);p.add_argument('--count',type=int,default=25)
    a=p.parse_args();test(a.case,a.count)
