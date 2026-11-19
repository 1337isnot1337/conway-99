"""Explicit exact modular incidence projections on 99 vertices and their integer defects."""
from collections import Counter
from itertools import combinations,product
import numpy as np
from triple_moments import tmp


def rank2(A):
    p={}
    for xs in A:
        a=sum(1<<int(i) for i in np.flatnonzero(xs))
        while a:
            j=a.bit_length()-1
            if j not in p:p[j]=a;break
            a^=p[j]
    return len(p)


def group_seeds():
    points=list(product(range(3),range(3),range(11)));idx={p:i for i,p in enumerate(points)}
    unseen=set(points[1:]);orbits=[]
    while unseen:
        a=min(unseen);orb=set()
        while a not in orb:
            orb.add(a);a=(2*a[0]%3,2*a[1]%3,2*a[2]%11)
        assert all((-x%3,-y%3,-z%11) in orb for x,y,z in orb)
        unseen-=orb;orbits.append(orb)
    for big in orbits:
        if len(big)!=10:continue
        for x,y in combinations((o for o in orbits if len(o)==2),2):
            S=big|x|y;A=np.zeros((99,99),np.int16)
            for i,(a,b,c) in enumerate(points):
                for u,v,w in S:A[i,idx[(a+u)%3,(b+v)%3,(c+w)%11]]=1
            yield A


if __name__=='__main__':
    histogram=Counter();best={}
    for A in group_seeds():
        assert np.all(A==A.T) and np.all(A.sum(0)==14) and np.all((A@A-A)%2==0)
        r=rank2(A);q=A@A+A-12*np.eye(99,dtype=int)-2
        err=int(np.sum(q*q));histogram[r,err]+=1
        if r not in best or err<best[r][0]:best[r]=(err,A)
    print('rank and full squared defect, counts',histogram)
    for r,(_,A) in best.items():np.save(tmp/('binary-seed-%d.npy'%r),A)
