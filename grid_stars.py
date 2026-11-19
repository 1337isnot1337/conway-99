"""Exact extensions at one exposed vertex of a 27-vertex incomplete-grid core."""
from itertools import combinations
from collections import Counter
import argparse
import numpy as np
from pysat.solvers import Minicard
from broken_grid import canonical_cases,extensions


def star(A,S,center):
    target=(12*np.eye(len(A),dtype=int)+2-A-A@A)[center]
    D=[s for s in S if center in s and all(target[j]>0 for j in s)]
    # Every neighbor of a bridge touches that bridge, its one assigned core anchor
    # and at least one member of X, so no two such vertices can have identical signatures.
    assert min(len(s) for s in D)>=3
    with Minicard() as sat:
        groups=[[i+1 for i,s in enumerate(D) if j in s] for j in range(len(A))]
        for j,ids in enumerate(groups):
            h=int(target[j])
            if len(ids)<h:return
            if h<len(ids):sat.add_atmost(ids,h)
            if h:sat.add_atmost([-i for i in ids],len(ids)-h)
        # Exclude pairs with three known common neighbors.
        tr={}
        for i,s in enumerate(D,1):
            for h in combinations(s,3):tr.setdefault(h,[]).append(i)
        for ids in tr.values():
            if len(ids)>1:sat.add_atmost(ids,1)
        while sat.solve():
            selected=[i for i in sat.get_model() if 0<i<=len(D)]
            yield tuple(D[i-1] for i in selected)
            sat.add_clause([-i for i in selected])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--limit',type=int,default=1000);a=p.parse_args()
    for i,(pe,c,A) in enumerate(canonical_cases()):
        S,_,_=extensions(A)
        counts=[]
        for j in np.array(pe)+8:
            count=0
            for ss in star(A,S,j):
                count+=1
                if count==a.limit:break
            counts.append(count)
        print(i,counts,'capped at',a.limit,flush=True)
