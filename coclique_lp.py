"""Scaled coclique flags, with a numerically independent row choice and full residual verification."""
import argparse
import numpy as np
import scipy.sparse as sp
from scipy.linalg.lapack import dpstrf
from scipy.optimize import linprog
from coclique_flags import build
from triple_moments import tmp


def run(h,secs):
    A,b,s,p,t=build(h,False);m=99-h
    factor=np.r_[np.full(len(s),m),np.full(len(p),m*(m-1)),np.full(len(t),m*(m-1)*(m-2))]
    M=A.multiply(factor).tocsr().astype(float)
    norms=np.sqrt(np.asarray(M.power(2).sum(axis=1)).ravel());norms[norms==0]=1.
    M=(sp.diags(1/norms)@M).tocsr();rhs=b/norms
    gram=(M@M.T).toarray(order='F')
    _,order,rank,_=dpstrf(gram,lower=1,tol=1e-12,overwrite_a=True)
    keep=np.sort(order[:rank]-1)
    bounds=[(1/m if j==s[7] else 0,None) for j in range(len(factor))]
    print(h,'independent row scout',rank,'of',len(b),flush=True)
    opt=linprog(np.zeros(len(factor)),A_eq=M[keep],b_eq=rhs[keep],bounds=bounds,method='highs-ipm',options={'time_limit':secs,'run_crossover':'off','threads':1})
    print(h,opt.message,flush=True)
    if opt.x is not None:
        x=factor*opt.x;print(h,'all equations max residual',max(abs(A@x-b)),'minimum',min(x),'point counts',np.round(x[:len(s)],4),flush=True)
        np.save(tmp/('coclique-flags-%d.npy'%h),x)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('h',type=int,nargs='+');p.add_argument('--seconds',type=int,default=45);a=p.parse_args()
    for h in a.h:run(h,a.seconds)
