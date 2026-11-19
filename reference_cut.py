"""Keep a jointly consistent set of neighborhoods from a public near-graph and replace all others."""
import argparse
from itertools import combinations
import numpy as np
from ortools.sat.python import cp_model

from star_reconstruct import solve
from triple_moments import tmp


def select(A,seed,seconds,cap):
    n=len(A);model=cp_model.CpModel();x=[model.new_bool_var('') for i in range(n)]
    E=A@A+A-(12*np.eye(99,dtype=int)+2)
    for i,j in combinations(range(n),2):
        if E[i,j]:model.add_at_most_one(x[i],x[j])
        if E[i,j]>0:
            for p in combinations(np.flatnonzero(A[i]*A[j]),3):
                model.add_bool_or([~x[h] for h in p])
    if cap:model.add(sum(x)==cap)
    rng=np.random.default_rng(seed)
    w=rng.integers(1,100,size=n)
    model.maximize(sum((int(w[i])+(0 if cap else 10000))*x[i] for i in range(n)))
    solver=cp_model.CpSolver();solver.parameters.num_workers=1;solver.parameters.random_seed=seed;solver.parameters.max_time_in_seconds=seconds
    # The unique defect-free source row is often helpful, but varying the cuts does not require it.
    status=solver.solve(model)
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):return None
    core=[i for i in range(n) if solver.value(x[i])];outside=sorted(set(range(n))-set(core));B=A[np.ix_(core,core)];N=A[np.ix_(core,outside)]
    assert np.array_equal(B@B+B+N@N.T,12*np.eye(len(B),dtype=int)+2)
    assert np.all(np.triu(N.T@N,1)<=2)
    return B,N,core,outside


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=11);p.add_argument('--size',type=int,default=0);p.add_argument('--seconds',type=int,default=15);p.add_argument('--nodes',type=int,default=2000);p.add_argument('--rows',type=int,default=20);a=p.parse_args()
    A=np.load(tmp/'hog-58094.npy')
    res=select(A,a.seed,a.seconds,a.size)
    if res:
        B,N,core,outer=res;tag='reference-%d-%d'%(a.size,a.seed)
        np.savez_compressed(tmp/(tag+'.npz'),B=B,N=N,core=core,outer=outer)
        print('selected',len(B),'complete neighborhoods, outside signature sizes',np.unique(N.sum(axis=0),return_counts=True),flush=True)
        solve(B,N,np.zeros((len(outer),len(outer)),bool),tag,a.nodes,a.rows,a.seed,14)
    else:print('no cut returned',flush=True)
