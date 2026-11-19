"""Test the six independent orbits in the 27-triangle order-three quotient."""
from itertools import combinations,product
from collections import Counter
from fractions import Fraction
import numpy as np
from flint import fmpz_mat
from z3 import Int, Sum, Solver, sat, unsat

def principal_psd(M):
    n=len(M)
    for s in range(1,n+1):
        for I in combinations(range(n),s):
            if fmpz_mat(M[np.ix_(I,I)].tolist()).det()<0:return False
    return True

def check():
    n=6
    subsets=np.array(list(product((0,1),repeat=6)),dtype=np.int64)
    stat=Counter()
    for lengths in ((6,),(3,3)):
        D=np.zeros((n,n),dtype=np.int64);start=0
        for size in lengths:
            for i in range(size):
                a=start+i;b=start+(i+1)%size
                D[a,b]=D[b,a]=2
            start+=size
        slots=[e for e in combinations(range(n),2) if not D[e]]
        for t in range(4):
            for extra in combinations(slots,t):
                Q=D.copy()
                for a,b in extra:Q[a,b]=Q[b,a]=1
                stat['patterns']+=1
                M=9*np.eye(n,dtype=np.int64)-3*Q+1
                if not principal_psd(M):continue
                stat['psd']+=1
                C=12*np.eye(n,dtype=np.int64)+6-Q@Q-Q
                if np.any(C<0):continue
                # For a triangle orbit the diagonal of 3*(3I-Q+J/3) is 4.
                # Keep its possible patterns only if this larger Gram is PSD.
                poss=[]
                for u in subsets:
                    v=1-3*u
                    R=np.block([[M,v[:,None]],[v[None,:],np.array([[4]])]])
                    if principal_psd(R):poss.append(u)
                if not poss:continue
                stat['candidate columns']+=1
                X=[Int('x%d'%i) for i in range(len(poss))]
                solver=Solver()
                solver.add(Sum(X)==27,*[x>=0 for x in X])
                for i in range(n):
                    for j in range(i+1):
                        solver.add(Sum([x for x,u in zip(X,poss) if u[i] and u[j]])==int(C[i,j]))
                result=solver.check()
                if result==unsat:continue
                if result!=sat:raise RuntimeError(result)
                stat['integer profiles']+=1
                print('remaining configuration',lengths,extra,'number of columns',len(poss),flush=True)
    print(stat)
if __name__=='__main__':check()
