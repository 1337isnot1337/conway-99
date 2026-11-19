"""Nine-coset Jacobi coefficients marked by one graph triangle."""
from math import isqrt
import z3

def line_flags(s,side,n,entry,rank):
    coeff=1 if side else 7;scale=7 if side else 1;V={}
    def flag(d,j,t):
        # Shift t into [-6,5], retaining the change of the point-residue class.
        k=(t+6)%12-6;h=(t-k)//12;dd=d-coeff*((t*t-k*k)//8)
        jj=(j-3*h)%9
        choices=[(jj,k),((-jj)%9,-k)]
        if k==-6:choices.extend([((jj+3)%9,6),((-jj-3)%9,-6)])
        jj,k=min(choices)
        if dd<0:return 0
        if dd==0:return 231 if k==0 and jj==0 else 0
        if isinstance(entry(side,jj,dd),int):return 0
        ns=side
        if rank==42 and not side and dd%7==0:ns=1;dd//=7
        key=ns,jj,dd,k
        if key not in V:
            x=z3.Real('l'+'_'.join(map(str,key)));s.add(x>=0);V[key]=x
        return V[key]
    tab={}
    for j in range(5):
        for d in range((5 if side else 8)*j*j%9,9*n+1,9):
            sz=entry(side,j,d);lim=isqrt((8*scale*d)//7)
            ts=[t for t in range(-lim,lim+1) if t%3==j%3];vs=[flag(d,j,t) for t in ts]
            for t,v in zip(ts,vs):tab[j,d,t]=v
            s.add(sum(vs)==231*sz,sum(t*v for t,v in zip(ts,vs))==0,sum(t*t*v for t,v in zip(ts,vs))==6*scale*d*sz)
            if j==0 and ((not side and d in (63,72)) or (side and d==9)):
                for t,v in zip(ts,vs):
                    if abs(t)>3:s.add(v==0)
    return tab
