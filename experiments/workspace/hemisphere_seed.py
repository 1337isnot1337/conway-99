"""Complete an initial group of independent outer rows while retaining the rooted 99-vertex labeling."""
import argparse
from itertools import combinations
import numpy as np
from ortools.sat.python import cp_model
from triple_moments import tmp


def make(L,seed=1,seconds=30,active=None):
    k=14;labels=[p for p in combinations(range(k),2) if p[0]^1!=p[1]]
    I=[labels.index(tuple(sorted((2*a,2*b)))) for a,b in L]
    f=len(I) if active is None else active
    fixed=I[:f];rest=[i for i in range(len(labels)) if i not in fixed]
    N0=np.zeros((15,84),dtype=np.int16)
    for j,(a,b) in enumerate(labels):N0[[a+1,b+1],j]=1
    C=np.zeros((15,15),dtype=np.int16);C[0,1:]=C[1:,0]=1
    for a in range(14):C[1+a,1+(a^1)]=1
    B=np.block([[C,N0[:,fixed]],[N0[:,fixed].T,np.zeros((f,f),np.int16)]])
    if not f:return B,N0,np.array(rest),I
    model=cp_model.CpModel()
    X=[[model.new_bool_var('') for j in rest] for i in fixed]
    for u,i in enumerate(fixed):
        for j in I[f:]:model.add(X[u][rest.index(j)]==0)
        for a in range(14):
            model.add(sum(X[u][j] for j,q in enumerate(rest) if a in labels[q])==2-int(a in labels[i])-int(a^1 in labels[i]))
    for u,v in combinations(range(f),2):
        terms=[]
        for j in range(len(rest)):
            d=model.new_bool_var('');model.add_multiplication_equality(d,[X[u][j],X[v][j]]);terms.append(d)
        model.add(sum(terms)==2-len(set(labels[fixed[u]])&set(labels[fixed[v]])))
    for j,q in enumerate(rest):
        for a in range(14):
            model.add(sum(X[u][j] for u,i in enumerate(fixed) if a in labels[i])<=2-int(a in labels[q])-int(a^1 in labels[q]))
    solver=cp_model.CpSolver();solver.parameters.num_workers=2;solver.parameters.max_time_in_seconds=seconds
    rng=np.random.default_rng(seed)
    # Random feasible row support, with no geometric symmetry imposed on a completion.
    for row in X:
        for x in row:
            if rng.integers(10)==0:model.add_hint(x,int(rng.integers(2)))
    solver.parameters.random_seed=seed;solver.parameters.randomize_search=True
    while True:
        status=solver.solve(model)
        if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):return None
        T=np.array([[solver.value(x) for x in row] for row in X],np.int16)
        N=np.vstack([N0[:,rest],T]);common=N.T@N
        violations=np.argwhere(np.triu(common,1)>2)
        if not len(violations):break
        for j,l in violations:
            limit=2-len(set(labels[rest[j]])&set(labels[rest[l]]))
            support=np.flatnonzero(T[:,j]*T[:,l])[:limit+1]
            model.add_bool_or([X[u][t].Not() for u in support for t in (j,l)])
    assert np.min(2-B@N-N)>=0
    assert np.array_equal(B@B+B+N@N.T,12*np.eye(len(B),dtype=int)+2)
    return B,N,np.array(rest),I


if __name__=='__main__':
    opts=argparse.ArgumentParser();opts.add_argument('--seed',type=int,default=1);opts.add_argument('--rows',type=int,default=7);a=opts.parse_args()
    rng=np.random.default_rng(a.seed)
    pairs=list(combinations(range(7),2));L=[pairs[i] for i in rng.choice(len(pairs),7,replace=False)]
    ans=make(L,a.seed,active=a.rows)
    if ans is None:print('no solution in time');raise SystemExit
    B,N,rest,I=ans;np.savez_compressed(tmp/('hemi-%d-%d.npz'%(a.seed,a.rows)),B=B,N=N,rest=rest,I=I);print('independent edge pattern',L,'specified rows',len(B),flush=True)
