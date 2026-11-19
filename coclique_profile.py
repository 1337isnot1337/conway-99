"""Integer block-size profiles and a conditional three-vertex census for each."""
import argparse
import numpy as np
import scipy.sparse as sp
from scipy.optimize import linprog
from coclique_flags import build
from triple_moments import tmp


def profiles(h):
    m=99-h;cost=(22-h)*(27-h)
    for a in range(cost//3+1):
        for b in range(cost-3*a+1):
            for g in range(1,(cost-3*a-b)//6+1):
                w=cost-3*a-b-6*g
                for f in range(w//3+1):
                    e=w-3*f;c=4*m-14*h-3*a-2*b+e+2*f+3*g;d=m-a-b-c-e-f-g
                    if min(c,d)<0 or e+2*f+3*(g-1)<max(0,2*h-35):continue
                    F=(a,b,c,d,e,f,g)
                    assert sum(F)==m and sum(j*v for j,v in enumerate(F,1))==14*h
                    assert sum(j*(j-1)*v for j,v in enumerate(F,1))==2*h*(h-1)
                    yield F


def run(h,seconds):
    for z,F in enumerate(profiles(h)):
        A,b,s,p,t=build(h,False,freq=F)
        if np.any((np.diff(A.indptr)==0)&(b!=0)):print(z,F,'inconsistent count',flush=True);continue
        # For every ordered class all counts are bounded by its available ordered vertices.
        cap=np.ones(A.shape[1])
        for d,j in s.items():cap[j]=F[d-1]
        for (a,d,u,e),j in p.items():cap[j]=F[a-1]*(F[d-1]-(a==d))
        for (a,d,g,*rest),j in t.items():cap[j]=F[a-1]*(F[d-1]-(a==d))*(F[g-1]-(a==g)-(d==g))
        assert min(cap)>0
        M=A.multiply(cap).tocsr().astype(float);norms=np.sqrt(np.asarray(M.power(2).sum(axis=1)).ravel());norms[norms==0]=1
        M=(sp.diags(1/norms)@M).tocsr()
        r=linprog(np.zeros(len(cap)),A_eq=M,b_eq=b/norms,bounds=(0,1),method='highs-ipm',options={'time_limit':seconds,'threads':1,'run_crossover':'off','ipm_optimality_tolerance':1e-10})
        err=None if r.x is None else max(abs(A@(r.x*cap)-b))
        print(h,z,F,A.shape,r.status,err,flush=True)
        if r.x is not None:np.save(tmp/('incidence-profile-%d-%d.npy'%(h,z)),r.x*cap)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('h',type=int);p.add_argument('--seconds',type=int,default=35);a=p.parse_args();run(a.h,a.seconds)
