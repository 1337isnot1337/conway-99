"""Couple scalar and coordinate harmonic theta series to discrete moment inequalities."""
from functools import cache
from fractions import Fraction as F
from itertools import combinations
from math import isqrt
import argparse
from level_seven_exact import constraints,expr
import z3

@cache
def basis(h,n):
    weight=22+h;t=weight%3;g=weight//3
    sigma=[sum(j for j in range(1,i+1) if i%j==0) for i in range(n+1)]
    th=[0]*(n+1);lim=isqrt(2*n)+2
    for x in range(-lim,lim+1):
        for y in range(-lim,lim+1):
            k=x*x+x*y+2*y*y
            if k<=n:th[k]+=1
    theta=[1]+[0]*n
    for _ in range(t):theta=[sum(th[j]*theta[i-j] for j in range(i+1)) for i in range(n+1)]
    out=[]
    for j in range(2*g+1):
        a,b=7*g-4*j,4*j-g
        d=[-a*sigma[i]-(7*b*sigma[i//7] if i%7==0 else 0) for i in range(n+1)];e=[1]
        for i in range(1,n-j+1):
            v,rem=divmod(sum(d[k]*e[i-k] for k in range(1,i+1)),i);assert not rem;e.append(v)
        out.append([0]*j+[sum(theta[k]*e[i-k] for k in range(i+1)) for i in range(n-j+1)])
    return out

@cache
def coord_energy(t,maxN):
    # Norms are in units of 1/9; a coordinate t represents t/3.
    a=t;residue=t%3
    if t*t>9*maxN:return 9*maxN+1
    lim=isqrt(9*maxN)
    vals=[i for i in range(-lim,lim+1) if i%3==residue]
    def far_min(s):
        q,rem=divmod((s-12*residue)//3,12)
        return (12-rem)*(3*q+residue)**2+rem*(3*q+3+residue)**2
    pairs={}
    for i in vals:
        for j in vals:
            if i>j or i*i+j*j>9*maxN:continue
            cost=2*(i*i+j*j)+far_min(-4*i-a-j)+far_min(-4*j-a-i)
            pairs[i+j]=min(pairs.get(i+j,10**12),cost)
    dp={0:0}
    for _ in range(7):
        nd={}
        for k,c in dp.items():
            for v,w in pairs.items():
                y=w+c
                if y<=18*maxN:nd[k+v]=min(nd.get(k+v,10**12),y)
        dp=nd
    return a*a+(dp.get(-4*a,10**12)+1)//2

@cache
def support(N,maxN):
    # t>=0 suffices since the harmonic polynomials are even, and negation preserves the lattice.
    return [t*t for t in range(isqrt(4*N)+1)
            if (t%3==0 or N>=22) and (N not in (14,16,18,20) or t<=3)
            and coord_energy(t,maxN)<=9*N]

def gegen(h,n,alpha=4):
    # Polynomial in u=t² after evaluating the monic solid zonal harmonic at t.
    a=[F(1)];b=[F(0),F(1)]
    for k in range(2,h+1):
        f=F((k-1)*(44+k-4),(44+2*k-4)*(44+2*k-6))*alpha*n
        c=[F(0)]+b
        for j,v in enumerate(a):c[j]-=f*v
        a,b=b,c
    return b[::2] if h else a

FAMILIES={'point':(28,99,9),'triangle':(4,231,3),'nonedge':(6,4158,81),'edge':(8,693,18)}
def solve(r,n,H,families,timeout):
    import json
    from pathlib import Path
    s=z3.SolverFor('QF_LRA')
    if timeout:s.set(timeout=timeout*1000)
    S={};D={}
    def modular(f,h):
        B=basis(h,max(n,2*((22+h)//3)));v=z3.Reals(' '.join('%sh%dv%d'%(f,h,j) for j in range(len(B))))
        d=len(v)-1
        left=[expr([b[i] for b in B],v) for i in range(n+1)]
        right=[expr([(-1)**(h//2)*F(7)**(r//2-11+d-2*j+h//2)*B[d-j][i] for j in range(len(B))],v) for i in range(n+1)]
        if h:
            for i in range(7):s.add(left[i]==0)
            s.add(right[0]==0)
        else:
            for a,b in constraints(r,n,{7:990,8:148995},True).values():s.add(expr(a,v)>=z3.RealVal(str(b)))
        return left,right
    S[0],D[0]=modular('scalar',0)
    prism=z3.Real('prism_count');s.add(prism>=0)
    sparse={(i,t):(a,b) for i,t,a,b in json.loads(Path('sparse-theta-flags.json').read_text())}
    for f in families:
        a,num,frame=FAMILIES[f];alpha=F(a,7)
        for h in range(4,H+1,2):S[h],D[h]=modular(f,h)
        for dual,T in enumerate((S,D)):
            lookup={}
            def var(i,t):
                k=min(t%a,(-t)%a)
                j=i-(1 if dual else 7)*((t*t-k*k)//(2*a))
                if j<0 or j==0 and k or not dual and 0<j<7:return 0
                if j==0:return num
                if (j,k) not in lookup:
                    z=z3.Real('%s_%d_%d_%d'%(f,dual,j,k));s.add(z>=0);lookup[j,k]=z
                return lookup[j,k]
            for i in range(1,n+1):
                if not dual and i<7:continue
                N=(14 if dual else 2)*i
                ts=range(isqrt(int(alpha*N))+1)
                count={t:(1+(t>0))*var(i,t) for t in ts}
                if N in (14,16) and f=='triangle':
                    for t,v in count.items():
                        if t>=2:s.add(v==0)
                if N in (14,16) and f in ('edge','nonedge'):
                    h=N//2
                    s.add(count[2]==(4*h if f=='edge' else h*h-4*h)*T[0][i])
                    for t,v in count.items():
                        if t>2:s.add(v==0)
                if f=='point':
                    us=support(N,14*n if dual else 2*n)
                    for t,v in count.items():
                        if t*t not in us:s.add(v==0)
                        if dual and (i,t) in sparse:
                            b,c=sparse[i,t];s.add(v>=b+c*prism)
                    if dual:
                        for j,t in sparse.keys():
                            if i==j and t not in count:
                                b,c=sparse[i,t];s.add(b+c*prism<=0)
                    frac=[(t,v) for t,v in count.items() if t%3!=0]
                    s.add(sum((99*t*t-9*N)*v for t,v in frac)==0)
                    s.add(sum((1 if t%3==1 else -1)*t*v for t,v in frac)==0)
                M=[sum(t**(2*k)*v for t,v in count.items()) for k in range(H//2+1)]
                s.add(M[0]==num*T[0][i],M[1]==frame*N*T[0][i])
                for h in range(4,H+1,2):s.add(expr(gegen(h,N,alpha),M)==T[h][i])
    print('built',r,n,H,families,flush=True)
    result=s.check();print('rank',r,'order',n,'harmonic degree',H,'families',families,result,flush=True)
if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--r',type=int,nargs='+',default=[34]);p.add_argument('--order',type=int,default=16);p.add_argument('--degree',type=int,default=8);p.add_argument('--families',nargs='+',default=['triangle']);p.add_argument('--timeout',type=int,default=0);a=p.parse_args()
    for r in a.r:solve(r,a.order,a.degree,a.families,a.timeout)
