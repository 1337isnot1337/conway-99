"""Solve finite integral edge and triangle marginal restrictions on one independent-pattern case."""
import argparse
from math import lcm
import numpy as np
import scipy.sparse as sp
from ortools.sat.python import cp_model
from power_two import solve
from triple_moments import tmp


def integral(A,sizes):
    order=lcm(*map(int,np.unique(sizes)))
    B=A.copy();B.data*=order//sizes[B.indices]
    h=np.gcd.reduceat(abs(B.data),B.indptr[:-1]);B.data//=np.repeat(h,np.diff(B.indptr))
    return B


def constraints(case):
    name='hemi-marginal-%d'%case
    E,G=[sp.load_npz(tmp/(name+'-'+suffix+'.npz')).tocsr() for suffix in ('eq','ge')]
    sizes=np.load(tmp/(name+'-size.npy'));E=integral(E,sizes);G=integral(G,sizes)
    keep=np.ones(len(sizes),bool)
    while True:
        R=E[:,keep].tocsr();S=G[:,keep].tocsr()
        sets=[]
        for A,ineq in ((R,False),(S,True)):
            pos=np.asarray((A>0).sum(axis=1)).ravel();neg=np.asarray((A<0).sum(axis=1)).ravel()
            active=(pos==0)&(neg>0) if ineq else (pos==0)^(neg==0)
            sets.append(A[active].indices)
        cols=np.unique(np.r_[*sets])
        if not len(cols):break
        keep[np.flatnonzero(keep)[cols]]=False
    if not keep[0]:raise ArithmeticError('forced constant zero')
    R=R[np.diff(R.indptr)>0];S=S[np.diff(S.indptr)>0]
    for A in (R,S):
        h=np.gcd.reduceat(abs(A.data),A.indptr[:-1]);A.data//=np.repeat(h,np.diff(A.indptr))
    return R,S,sizes[keep],keep


def run(case,seconds):
    R,S,sizes,keep=constraints(case)
    print('reduced integral variables',len(sizes),'constraints',R.shape[0],S.shape[0],flush=True)
    x=solve(R,3,True)
    if x is None:print('inconsistent modulo eight',flush=True);return
    model=cp_model.CpModel();vs=[model.new_int_var(1 if i==0 else 0,int(n),'') for i,n in enumerate(sizes)]
    for A,eq in ((R,True),(S,False)):
        for i in range(A.shape[0]):
            a,b=A.indptr[i:i+2];form=cp_model.LinearExpr.weighted_sum([vs[j] for j in A.indices[a:b]],A.data[a:b].tolist())
            if eq:model.add(form==0)
            else:model.add(form>=0)
    solver=cp_model.CpSolver();solver.parameters.num_workers=2;solver.parameters.max_time_in_seconds=seconds
    status=solver.solve(model);print(solver.status_name(status),'branches',solver.num_branches,'conflicts',solver.num_conflicts,flush=True)
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        x=np.array([solver.value(v) for v in vs]);assert np.all(R@x==0) and min(S@x)>=0 and np.all(x<=sizes)
        np.save(tmp/('hemi-marginal-%d-integer.npy'%case),x)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--case',type=int,default=0);p.add_argument('--seconds',type=int,default=180);a=p.parse_args();run(a.case,a.seconds)
