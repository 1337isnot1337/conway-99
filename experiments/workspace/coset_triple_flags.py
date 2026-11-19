"""Three marked coordinates coupled by all four induced graph types on a triple."""
from itertools import product,permutations
from functools import cache
from math import isqrt
import z3
import numpy as np
canonical={0:(0,0,0),1:(1,0,0),2:(1,1,0),3:(1,1,1)}
perms=list(permutations(range(3)));ij=((0,1),(0,2),(1,2))
def matrix(code):
    A=np.zeros((3,3),dtype=int)
    for v,(i,j) in zip(code,ij):A[i,j]=A[j,i]=v
    return A
@cache
def tocanonical(code):
    A=matrix(code);return [p for p in perms if tuple(A[p[i],p[j]] for i,j in ij)==canonical[sum(code)]]
@cache
def geom(g):
    G=27*np.eye(3,dtype=int)+1-9*matrix(canonical[g]);det=int(round(np.linalg.det(G)))
    J=np.rint(det*np.linalg.inv(G)).astype(int);assert np.array_equal(G@J,det*np.eye(3,dtype=int))
    return G,J,det
@cache
def closest(g,u):
    G,J,det=geom(g);u=np.array(u);best=None
    for n in product(range(-1,3),repeat=3):
        x=u-G@n;q=int(x@J@x)
        if best is None or q<=best[0]:
            r=min(tuple(sign*int(x[i]) for i in p) for p in tocanonical(canonical[g]) for sign in (1,-1))
            item=q,r
            if best is None or item<best:best=item
    return best
@cache
def reduction(code,labels):
    g=sum(code);t=np.array([labels[i] for i in tocanonical(code)[0]]);G,J,det=geom(g)
    q=int(t@J@t);n=(J@t)//det;u=t-G@n
    low,rep=closest(g,tuple(map(int,u)));delta,rem=divmod(q-low,2*det);assert not rem
    return q,det,delta,rep
def add(s,side,n,rank,entry,flag,pair):
    scale=7 if side else 1;coeff=1 if side else 7;lookup={}
    for j in range(5):
        for d in range((5 if side else 8)*j*j%9,9*n+1,9):
            lim=isqrt(8*scale*d);ts=[t for t in range(-lim,lim+1) if t%9==j]
            def triple(code,t,u,v):
                q,det,delta,rep=reduction(code,(t,u,v))
                if coeff*q>2*det*d:return 0
                h=d-coeff*delta;g=sum(code)
                if h==0:return (590436,99792,16632,1386)[g] if rep==(0,0,0) else 0
                if h<0 or isinstance(entry(side,rep[0],h),int):return 0
                if any(isinstance(flag(h,z),int) and flag(h,z)==0 for z in rep):return 0
                ns=side
                if rank==42 and not side and h%7==0:ns=1;h//=7
                key=(ns,h,g)+rep
                if key not in lookup:
                    vv=z3.Real('t'+'_'.join(map(str,key)));lookup[key]=vv;s.add(vv>=0)
                return lookup[key]
            for e,cat in ((1,'edge'),(0,'nonedge')):
                for t in ts:
                    for u in ts:
                        if u<t:continue
                        p=pair[cat,d,t,u]
                        # Both endpoints and their common neighbors have calibrated degrees.
                        sums={};s1={}
                        for b,c in product((0,1),repeat=2):
                            vals=[triple((e,b,c),t,u,v) for v in ts]
                            sums[b,c]=sum(vals);s1[b,c]=sum(v*x for v,x in zip(ts,vals))
                        for k,size in [((1,1),2-e),((1,0),12),((0,1),12),((0,0),71+e)]:
                            s.add(sums[k]==size*p)
                        s.add(s1[1,1]+s1[1,0]==(-4*t-e*u)*p)
                        s.add(s1[1,1]+s1[0,1]==(-4*u-e*t)*p)
                        s.add(sum(s1.values())==(-t-u)*p)
    print('triple flag counts',side,len(lookup),flush=True)
