"""Theta series of the 3-eigenspace joined to the binary lattice of determinant eleven."""
from functools import cache
from fractions import Fraction as F
from itertools import product
from math import isqrt
from pathlib import Path
import argparse,json,z3
import numpy as np
from harmonic_theta import basis,gegen
from level_seven_exact import expr
from core_counts import reduce_counts
from subgraph_counts import build
def floors(maxd):
    data=build(6);graphs,levels,*_=data
    cores,fac,_,ind=reduce_counts(data,99,14);assert len(cores)==1
    out={}
    for n in range(1,7):
        V=np.array([b for b in product((-3,-2,-1,1,2,3),repeat=n) if 0<=sum(b)<=5],dtype=int);m=V.sum(axis=1)
        for ix in levels[n]:
            G=np.array([[(r>>j)&1 for j in range(n)] for r in graphs[ix]])
            ds=11*((4*V+V@G)*V).sum(axis=1)//2-m*m
            assert np.all(ds>=0)
            good=ds<=maxd
            for key,f in zip(*np.unique(m[good]*10000+ds[good],return_counts=True)):
                j,d=divmod(int(key),10000);a,b=out.get((j,d),(0,0));A,B=ind[ix]
                out[j,d]=(a+int(A//fac)*int(f),b+int(B//fac)*int(f))
    return out
@cache
def binary(n,degree=0):
    # The coset representative is the second dual basis vector (-1,2)/11.
    masks=[{} for j in range(6)];limit=isqrt(11*n)+3
    for j in range(6):
        for u,v in product(range(-limit,limit+1),repeat=2):
            x,y=11*u-j,11*v+2*j;d,rem=divmod(x*x+x*y+3*y*y,11);assert not rem and d%11==j*j%11
            if d<=11*n:
                from math import comb
                h=sum(comb(degree,2*k)*(2*x+y)**(degree-2*k)*(-11*y*y)**k for k in range(degree//2+1))
                masks[j][d]=masks[j].get(d,0)+h
    return masks
def solve(r,n,moment,point_degree,output,aux_degree):
    s=z3.SolverFor('QF_LRA');C={};prism=z3.Real('prism');s.add(prism>=0,prism<=1386)
    def entry(side,j,d):
        j=min(j%11,(-j)%11)
        if d<0 or d%11!=((-1 if side else 1)*j*j)%11:return 0
        if d==0:return int(j==0)
        t=min((-2*j)%11,(2*j)%11) if side else j
        if (not side and j==0 and d<66) or 2*d*(7 if side else 1)<9*t*(11-t):return 0
        key=(side,j,d)
        if key not in C:
            z=z3.Real('c%d_%d_%d'%key);s.add(z>=0);C[key]=z
        return C[key]
    s.add(entry(0,0,66)<=6*prism,entry(0,0,77)<=99*14*42**2,entry(1,0,11)<=60000)
    for (j,d),(a,b) in floors(11*n).items():s.add(entry(1,j,d)>=a+b*prism)
    P=binary(n);angular={}
    for side in (0,1):
        fac=7 if side else 1;coef=1 if side else 7;vg={}
        def flag(d,t):
            k=min(t%42,(-t)%42);dd=d-coef*((t*t-k*k)//84)
            if dd<0:return 0
            if dd==0:return 99 if k==0 else 0
            if isinstance(entry(side,5*k if side else k,dd),int):return 0
            if (dd,k) not in vg:
                z=z3.Real('f%d_%d_%d'%(side,dd,k));s.add(z>=0);vg[dd,k]=z
            return vg[dd,k]
        for j in range(6):
            for d in range(((-1 if side else 1)*j*j)%11,11*n+1,11):
                count=entry(side,j,d);lim=isqrt(12*fac*d)
                ts=[t for t in range(-lim,lim+1) if t%11==((-2 if side else 1)*j)%11]
                vals=[flag(d,t) for t in ts]
                s.add(sum(vals)==99*count,sum(t*v for t,v in zip(ts,vals))==0,sum(t*t*v for t,v in zip(ts,vals))==22*fac*d*count)
                if j==0 and (not side and d in (66,77) or side and d==11):
                    for t,v in zip(ts,vals):
                        if abs(t)>11:s.add(v==0)
                for h in range(4,point_degree+1,2):
                    # Monic harmonic polynomials referred to dimension 54.
                    A=[F(1)];B=[F(0),F(1)]
                    for k in range(2,h+1):
                        beta=F((k-1)*(54+k-4),(54+2*k-4)*(54+2*k-6))*12*fac*d
                        N=[F(0)]+B
                        for i,a in enumerate(A):N[i]-=beta*a
                        A,B=B,N
                    co=[sum(a*t**i for i,a in enumerate(B)) for t in ts];angular[side,j,d,h]=sum(z3.RealVal(str(w))*v for w,v in zip(co,vals))
    for e in range(0,aux_degree+1,2):
        P=binary(n,e)
        for mode in ['scalar']+list(range(4,point_degree+1,2)):
            degree=0 if mode=='scalar' else mode
            if degree and e>6:continue
            for h in range((moment if not degree and not e else 0)+1):
                w=28+2*h+degree+e;b=basis(w-22,max(n,2*(w//3)));dim=len(b)-1
                u=z3.Reals(' '.join('t%d_%d_%dv%d'%(degree,e,h,i) for i in range(dim+1)))
                hp=[F(1)]
                for k in range(h):hp.append(-hp[-1]*F((h-k)*(2*(h-k)),(k+1)*(2*k+54)))
                for side in (0,1):
                    for i in range(n+1):
                        terms=[]
                        for j in range(6):
                            l=j if side else min((5*j)%11,(-5*j)%11);fac=1 if side else 7
                            for d,cv in P[l].items():
                                y=fac*d;x=11*i-y
                                if x<0:continue
                                mult=(1 if side else 7**(e//2))*(1+(j!=0))*cv*sum(v*x**k*y**(h-k) for k,v in enumerate(hp))
                                val=angular.get((side,j,x,degree),0) if degree else entry(side,j,x)
                                terms.append(z3.RealVal(str(mult))*val)
                        if side:
                            # The determinant on the larger eigenspace side is 7^(r+2), rank 56.
                            co=[(-1)**(h+degree//2+e//2)*F(7)**(r//2-13+dim-2*j+degree//2)*b[dim-j][i] for j in range(dim+1)]
                        else:co=[col[i] for col in b]
                        s.add(expr(co,u)==sum(terms))
    print('positive rank',r,'order',n,'shells',len(C),'constraints',len(s.assertions()),flush=True)
    from theta_linear import reduce_solver
    print(reduce_solver(s,0,output),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--rank',type=int);p.add_argument('--order',type=int,default=19);p.add_argument('--moments',type=int,default=3);p.add_argument('--degree',type=int,default=6);p.add_argument('--save');p.add_argument('--aux-degree',type=int,default=0);a=p.parse_args();solve(a.rank,a.order,a.moments,a.degree,a.save,a.aux_degree)
