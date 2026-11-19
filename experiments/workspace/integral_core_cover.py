"""Integral exterior incidence designs with no repeated triples of known neighbors."""
from collections import defaultdict
from itertools import combinations
import argparse
import numpy as np
from ortools.sat.python import cp_model
from broken_grid import canonical_cases,extensions
from signature_cover import system


def solve(A,Y,seconds):
    M,b=system(A,Y);cap=12*np.eye(len(A),dtype=int)+2-A@A-A
    model=cp_model.CpModel();vars=[];tr=defaultdict(list)
    for j,row in enumerate(Y):
        sel=np.flatnonzero(row)
        for a in combinations(sel,3):
            if all(cap[i,k]>=2 for i,k in combinations(a,2)):tr[a].append(j)
        upper=min(int(cap[i,k]) for i,k in combinations(sel,2))
        if len(sel)>=3:upper=min(upper,1)
        vars.append(model.new_bool_var('v%d'%j) if upper==1 else model.new_int_var(0,upper,'v%d'%j))
    for i in range(M.shape[0]):
        ix=M.indices[M.indptr[i]:M.indptr[i+1]];terms=[vars[j] for j in ix]
        model.add(sum(terms)==int(b[i]))
    for group in tr.values():
        if len(group)>1:model.add_at_most_one([vars[j] for j in group])
    solver=cp_model.CpSolver();solver.parameters.max_time_in_seconds=seconds;solver.parameters.num_search_workers=2
    res=solver.solve(model)
    z=None
    if res in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        z=np.array([solver.value(v) for v in vars])
        assert np.all(M@z==b)
        Q=Y.repeat(z,axis=0)
        assert np.all(Q.T@Q==cap)
        assert np.max(np.triu(Q@Q.T,1))<=2
    return solver.status_name(res),z


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seconds',type=int,default=35);p.add_argument('--core39',type=int,nargs='*');a=p.parse_args()
    from pathlib import Path
    tmp=Path('/tmp/conway99-tools')
    if a.core39 is not None:
        tasks=[('39-%d'%i,np.load(tmp/('grid-core39-0-%d.npy'%i)),np.load(tmp/('grid39-signatures-0-%d.npz'%i))['Y']) for i in a.core39]
    else:
        tasks=[]
        for i,(_,_,A) in enumerate(canonical_cases()):
            S,_,_=extensions(A);Y=np.zeros((len(S),len(A)),dtype=np.int16)
            for j,s in enumerate(S):Y[j,list(s)]=1
            tasks.append(('27-%d'%i,A,Y))
    for name,A,Y in tasks:
        status,z=solve(A,Y,a.seconds)
        print(name,'integral cover',status,flush=True)
        if z is not None:np.savez_compressed(tmp/('core-cover-'+name+'.npz'),B=Y.repeat(z,axis=0),A=A)
