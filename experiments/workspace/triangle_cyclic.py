"""Construct cyclic interfaces for the three twelve-point fibers of a triangle."""
from itertools import product
from collections import Counter,defaultdict
import numpy as np
from triple_moments import tmp
from triangle_ball import local_ball

def designs(target):
    sol=[];curr=[]
    def visit(i,left,used):
        if i==6:
            assert not any(left);sol.append(tuple(curr));return
        for j in range(1,6):
            if used>>j&1:continue
            for a in range(12):
                diff=(a,(a+j)%12,(a-i)%12,(a+j-i)%12)
                if any(not left[d] for d in diff):continue
                for d in diff:left[d]-=1
                if min(left)>=0:
                    curr.append((j,a));visit(i+1,left,used|1<<j);curr.pop()
                for d in diff:left[d]+=1
    visit(1,target.copy(),0);return sol

def point_intersections(A):
    M=12*np.eye(39,dtype=int)+2-A-A@A
    return M

def solve(t):
    size=12;matching=[[(i+6)%12 for i in range(12)]]*3
    A=local_ball(12,matching,[(i+t)%12 for i in range(12)])
    M=point_intersections(A)
    def coords(y,z):return list(map(int,M[3+12*y,3+12*z:15+12*z]))
    targets=[coords(0,1),coords(0,2),coords(1,2)]
    if min(min(x) for x in targets)<0:return
    L=designs(targets[0]);R=designs(targets[1]);C=designs(targets[2])
    print('twist',t,'pair design counts',len(L),len(R),len(C),flush=True)
    # Compose interface maps from the first fiber's pairs to the other two.
    # A base pair {s,s+i} maps to {s+a,s+a+j} in the indicated fiber.
    # A (B,C) map is valid precisely when its five signed differences give target three.
    def key(f):return tuple(12*(j-1)+a for j,a in f)
    C={key(c) for c in C};candidates=Counter();examples=[]
    for l in L:
        for r in R:
            a=[0]*5
            for (j,b),(k,c) in zip(l,r):a[j-1]=12*(k-1)+(c-b)%12
            if tuple(a) not in C:continue
            candidates['pair identities']+=1
            words=np.array([[1<<s|1<<((s+i+1)%12),1<<((s+b)%12)|1<<((s+b+j)%12),1<<((s+c)%12)|1<<((s+c+k)%12)] for i,((j,b),(k,c)) in enumerate(zip(l,r)) for s in range(12)],dtype=np.int64)
            masks=words[:,0]|words[:,1]<<12|words[:,2]<<24
            if any((int(v)&int(w)).bit_count()>2 for x in range(0,60,12) for y,w in enumerate(masks) if y!=x for v in [masks[x]]):continue
            I=np.array([[(int(q)>>i)&1 for i in range(36)] for q in masks],dtype=np.int16)
            if np.any(I@(A[3:,3:]+np.eye(36,dtype=int))>2):continue
            assert np.array_equal(I.T@I,M[3:,3:])
            candidates['valid complete incidence']+=1;examples.append(masks)
    print(t,candidates,flush=True)
    np.savez_compressed(tmp/('triangle-cyclic-%d.npz'%t),A=A,masks=np.array(examples))

if __name__=='__main__':
    import sys
    for t in map(int,sys.argv[1:]):solve(t)
