"""Fit the final fiber without any symmetry given a complete first two-fiber design."""
import argparse
from itertools import combinations
import numpy as np
from ortools.sat.python import cp_model
from triangle_cyclic import designs,point_intersections,tmp,local_ball

def instance(t,index):
    N=12
    A=local_ball(N,[[(i+6)%N for i in range(N)]]*3,[(i+t)%N for i in range(N)])
    M=point_intersections(A)
    L=designs(list(map(int,M[3,15:27])))[index];V=[]
    for i,(j,a) in enumerate(L,1):
        for x in range(N):V.append((x,(x+i)%N,12+(x+a)%N,12+(x+a+j)%N))
    V=np.array(V);T=np.zeros((60,24),np.int16);T[np.arange(60)[:,None],V]=1
    assert np.array_equal(T.T@T,M[3:27,3:27])
    return A,V,T

def fit(A,V,T,seconds,group=1):
    M=point_intersections(A);N=12
    model=cp_model.CpModel()
    matrix=[[model.new_bool_var('') for i in range(N)] for x in range(60)]
    for row in matrix:model.add(sum(row)==2)
    for i in range(N):
        for h in range(24):
            model.add(sum(matrix[x][i] for x in np.flatnonzero(T[:,h]))==int(M[27+i,3+h]))
    known=T@T.T
    for h in range(N):
        for x,y in combinations(range(60),2):
            if known[x,y]==2:model.add(matrix[x][h]+matrix[y][h]<=1)
    pairs=list(combinations(range(N),2))
    options=[[] for _ in range(60)]
    for i,j in pairs:
        if A[27+i,27+j]:continue
        use=[]
        for x in range(60):
            h=list(V[x]);c=h+[24+i,24+j]
            if np.max(np.sum(A[3:,3:][:,c],axis=1)+np.bincount(c,minlength=36))>2:continue
            if any(M[3+p,3+q]<=0 for p,q in combinations(c,2)):continue
            v=model.new_bool_var('');use.append(v);options[x].append((i,j,v))
        model.add_exactly_one(use)
    for x in range(60):
        model.add_exactly_one([v for i,j,v in options[x]])
        for h in range(N):model.add(sum(v for i,j,v in options[x] if h==i or h==j)==matrix[x][h])
    if group>1:
        shift=N//group
        for x in range(60):
            y=x//12*12+(x+shift)%12
            for h in range(12):model.add(matrix[x][h]==matrix[y][(h+shift)%12])
    solver=cp_model.CpSolver();solver.parameters.num_workers=1;solver.parameters.max_time_in_seconds=seconds
    result=solver.solve(model)
    W=None
    if result in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        W=np.column_stack((T,np.array([[solver.value(v) for v in row] for row in matrix],dtype=np.int16)))
        assert np.array_equal(W.T@W,M[3:,3:]) and np.max(np.triu(W@W.T,1))<=2
    return solver.status_name(result),W

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('t',type=int);p.add_argument('i',type=int,nargs='+');p.add_argument('--time',type=float,default=50);p.add_argument('--group',type=int,default=1);a=p.parse_args()
    for i in a.i:
        A,V,T=instance(a.t,i);s,W=fit(A,V,T,a.time,a.group)
        print(a.t,i,a.group,s,flush=True)
        if W is not None:np.savez_compressed(tmp/('triangle-fit-%d-%d-%d.npz'%(a.t,i,a.group)),A=A,W=W)
