"""Check a generated two-coclique array and its full first exterior row independently."""
import numpy as np
from ortools.sat.python import cp_model
from triple_moments import tmp

def check(rec):
    known,dups,*columns=rec
    B=np.array([[(c>>i)&1 for i in range(29)] for c in columns],dtype=int)
    A=np.zeros((29,29),dtype=int)
    for i in range(7):
        for j in range(7):
            A[15+i,22+j]=A[22+j,15+i]=1-((dups>>((j-i)%7))&1)
    assert B.shape==(70,29) and np.all(B.sum(axis=1)==5)
    assert np.array_equal(B.T@B,12*np.eye(29,dtype=int)+2-A-A@A)
    T=B@B.T;assert max(T[np.triu_indices(70,1)])<=2
    for v in range(0,min(known+1,10)*7,7):
        model=cp_model.CpModel();u=[model.new_bool_var('') for _ in B]
        model.add(sum(u)==9)
        for i in range(29):
            model.add(sum(w for w,b in zip(u,B[:,i]) if b)==int(2-B[v,i]-(B[v]@A[:,i])))
        for j in range(70):
            if T[v,j]>=2:model.add(u[j]==0)
            for k in range(j):
                if T[j,k]>=2:model.add(u[j]+u[k]<=1)
        solver=cp_model.CpSolver();solver.parameters.num_workers=1;result=solver.solve(model)
        assert result in (cp_model.OPTIMAL,cp_model.INFEASIBLE)
        assert (result==cp_model.OPTIMAL)==(v//7<known)
    print('Verified full 29-by-29 anchor identity, pair caps and row outcome at orbit',known)

if __name__=='__main__':
    for line in (tmp/'fano-templates.txt').read_text().splitlines():check(list(map(int,line.split())))
