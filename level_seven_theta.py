"""Fourier coefficients at both cusps of level seven and primal/dual shell constraints."""
import argparse
import math
import numpy as np
from scipy.optimize import linprog

def series_basis(n):
    # The normalized eta quotient starts at 1. Its log derivative is an integral divisor sum.
    sigma = [sum(d for d in range(1,k+1) if k%d==0) for k in range(n+1)]
    theta=[0]*(n+1)
    lim=math.isqrt(2*n)+2
    for x in range(-lim,lim+1):
        for y in range(-lim,lim+1):
            k=x*x+x*y+2*y*y
            if k<=n:theta[k]+=1
    out=[]
    for j in range(15):
        a,b=49-4*j,4*j-7
        log=[-a*sigma[k]-(7*b*sigma[k//7] if k%7==0 else 0) for k in range(n+1)]
        e=[1]
        for k in range(1,n-j+1):
            total=sum(log[i]*e[k-i] for i in range(1,k+1))
            v,res=divmod(total,k)
            assert res==0
            e.append(v)
        out.append([0]*j+[sum(theta[i]*e[k-i] for i in range(k+1)) for k in range(n-j+1)])
    return np.array(out,dtype=object).T

def lp(r,n,minimum,rootfree,full,target):
    from fractions import Fraction
    B=series_basis(7*n if full else n); p=r//2
    D=B[:,::-1]*[Fraction(7)**(3+p-2*j) for j in range(15)]
    # Use low coefficients of L at infinity and of its adjoint at zero as coordinates.
    H=np.vstack((B[:8],D[:7]))
    from flint import fmpq, fmpq_mat
    exact=fmpq_mat([[fmpq(str(x)) for x in row] for row in H]).inv()
    U=np.array([[Fraction(str(x)) for x in row] for row in exact.tolist()],dtype=object)
    B,D=B@U,D@U
    eq=[]; eb=[]; le=[]; lb=[]
    def add(row,rhs,exact=False):
        v=np.array(row,dtype=np.float64); scale=max(1,abs(rhs),np.max(abs(v)))
        if exact:eq.append(v/scale);eb.append(rhs/scale)
        else:le.append(-v/scale);lb.append(-rhs/scale)
    add(B[0],1,True);add(D[0],1,True)
    for i in range(1,minimum//2):add(B[i],0,True)
    if rootfree:add(D[1],0,True)
    add(-D[1],-88);add(-B[7],-990);add(-B[8],-148995)
    for i in range(1,n+1):
        add(B[i],0);add(D[i],{2:462,3:24948,4:1386}.get(i,0))
        if full:
            add(B[7*i]-D[i],0,r==42);add(D[7*i]-B[i],0)
    # Coordinates differ widely in size. Rely on low-shell magnitudes as initial scales.
    scales=np.array([1]*8+[1,1,1e3,3e4,2e5,2e6,2e7])
    def rescale(mat,rhs):
        arr=np.array(mat)*scales
        norm=np.maximum(np.max(abs(arr),axis=1),np.abs(rhs));norm[norm==0]=1
        return arr/norm[:,None],np.array(rhs)/norm
    le,lb=rescale(le,lb);eq,eb=rescale(eq,eb)
    coeff=np.array(B[target] if target>=0 else D[-target],dtype=float)*scales
    res=linprog(coeff/max(1,np.max(abs(coeff))),A_ub=le,b_ub=lb,A_eq=eq,b_eq=eb,bounds=(None,None),method='highs')
    print('rank',r,'min',minimum,'rootfree',rootfree,'status',res.status,res.message,flush=True)
    if res.success:print('target',target,coeff@res.x,'primal',np.round(np.array(B[7:13],dtype=float)@(res.x*scales),1),'dual',np.round(res.x[9:]*scales[9:],1),flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--r',nargs='+',type=int,default=list(range(28,43,2)));p.add_argument('--order',type=int,default=16);p.add_argument('--minimum',type=int,default=14);p.add_argument('--rootfree',action='store_true');p.add_argument('--full',action='store_true');p.add_argument('--target',type=int,default=0);a=p.parse_args()
    for r in a.r:lp(r,a.order,a.minimum,a.rootfree,a.full,a.target)
