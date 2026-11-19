"""Signed, ordered two-coordinate theta counts transported by two projected vertex vectors."""
from functools import cache
from math import isqrt
import z3
@cache
def reduce_mark(c,t,u):
    det=28*28-c*c
    a0=(28*t-c*u)//det;b0=(28*u-c*t)//det
    def value(x,y):return 28*(x*x+y*y)-2*c*x*y
    best=None
    for a in range(a0-1,a0+3):
        for b in range(b0-1,b0+3):
            x=t-28*a-c*b;y=u-c*a-28*b
            p,q=min((x,y),(y,x),(-x,-y),(-y,-x))
            candidate=(value(p,q),p,q)
            if best is None or candidate<best:best=candidate
    v,x,y=best;dd,rem=divmod(value(t,u)-v,2*det);assert rem==0
    return dd,x,y

def add_pairs(s,entry,flag,dual,n,categories,rank=None):
    scale=7 if dual else 1;coef=1 if dual else 7
    allpairs={}
    for cat in categories:
        edge=cat=='edge';degree=14 if edge else 84;neighbor=-4 if edge else 3;c=-8 if edge else 1;det=28*28-c*c
        lookup={}
        def pair(d,t,u):
            if coef*(28*(t*t+u*u)-2*c*t*u)>2*det*d:return 0
            delta,a,b=reduce_mark(c,t,u);j=d-coef*delta
            if j<0:return 0
            if j==0:return 99*degree if a==b==0 else 0
            if isinstance(entry(dual,a,j),int):return 0
            # Each coordinate individually must be present at the reduced shell.
            if isinstance(flag(j,a),int) and flag(j,a)==0 or isinstance(flag(j,b),int) and flag(j,b)==0:return 0
            normside=dual
            if rank==42 and not dual and j%7==0:normside=1;j//=7
            if (normside,j,a,b) not in lookup:
                x=z3.Real('p%s_%d_%d_%d_%d'%(cat,normside,j,a,b));s.add(x>=0);lookup[normside,j,a,b]=x
            return lookup[normside,j,a,b]
        for j in range(5):
            for d in range((5 if dual else 8)*j*j%9,9*n+1,9):
                lim=isqrt(8*scale*d);ts=[t for t in range(-lim,lim+1) if t%9==j]
                for t in ts:
                    vals=[pair(d,t,u) for u in ts];g=flag(d,t)
                    for u,val in zip(ts,vals):
                        allpairs[cat,d,t,u]=val
                        if edge:
                            from local_energy import minimum
                            if minimum(t,9,18*9*n*scale,u)>18*d*scale:s.add(val==0)
                    s.add(sum(vals)==degree*g,sum(v*u for v,u in zip(vals,ts))==neighbor*t*g)
                    if j==0 and abs(t)==9 and ((not dual and d in (63,72)) or (dual and d==9)):
                        if edge:
                            s.add(pair(d,t,t)==0,pair(d,t,-t)==4*g)
        print('pair counts',cat,dual,len(lookup),flush=True)
    if set(categories)=={'edge','nonedge'}:
        for j in range(5):
            for d in range((5 if dual else 8)*j*j%9,9*n+1,9):
                size=entry(dual,j,d);lim=isqrt(8*scale*d);ts=[t for t in range(-lim,lim+1) if t%9==j]
                for t in ts:
                    f=flag(d,t)
                    s.add(sum(u*u*(allpairs['edge',d,t,u]+allpairs['nonedge',d,t,u]) for u in ts)==(18*d*scale-t*t)*f)
                    # Repeated occurrences at this one mark are counted by
                    # n_t(n_t-1). The norm and residue bound each multiplicity.
                    minother=min([u*u for u in ts if u!=t]+[10**9])
                    maxcount=99
                    if t*t>minother:maxcount=min(99,(18*d*scale-99*minother)//(t*t-minother))
                    diag=allpairs['edge',d,t,t]+allpairs['nonedge',d,t,t]
                    s.add(diag<=max(0,maxcount-1)*f)
                    for k in (1,2,3,4,6,8,12,16,24,32,48,64,80):
                        if k<=maxcount:s.add(diag-2*k*f+k*(k+1)*size>=0)
    return allpairs
