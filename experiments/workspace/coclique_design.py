"""Construct 22-point twofold block designs as candidate neighborhoods of a Hoffman coclique."""
import argparse
from itertools import combinations
from pathlib import Path
import numpy as np
from ortools.sat.python import cp_model
from triple_moments import tmp


def shift(B,s):return tuple(sorted((v//11)*11+(v+s)%11 for v in B))


def design(seed,seconds):
    pair=list(combinations(range(22),2));orbits={min(shift(p,s) for s in range(11)) for p in pair}
    pairs=sorted(orbits);idx={p:i for i,p in enumerate(pairs)}
    def typ(S):return min(shift(S,s) for s in range(11))
    typ2={p:idx[typ(p)] for p in pair};typ3={p:typ(p) for p in combinations(range(22),3)}
    blocks=[b for b in combinations(range(22),4) if b==typ(b)]
    cols=[];D=[];trips=[]
    for b in blocks:
        t={typ3[p] for p in combinations(b,3)}
        if len(t)!=4:continue
        d=np.bincount([typ2[p] for p in combinations(b,2)],minlength=len(idx))
        if max(d)>2:continue
        cols.append(b);D.append(d);trips.append(t)
    D=np.array(D)
    model=cp_model.CpModel();xs=[model.new_bool_var('') for b in cols]
    for i in range(len(pairs)):model.add(sum(int(D[j,i])*xs[j] for j in np.flatnonzero(D[:,i]))==2)
    for t in sorted(set.union(*trips)):model.add_at_most_one(xs[j] for j,tt in enumerate(trips) if t in tt)
    # Pick a seeded base block to vary independent realizations.
    rng=np.random.default_rng(seed);model.add(xs[rng.integers(len(xs))]==1)
    solver=cp_model.CpSolver();solver.parameters.num_workers=2;solver.parameters.max_time_in_seconds=seconds
    solver.parameters.random_seed=seed
    status=solver.solve(model)
    if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):return solver.status_name(status),None
    bs=[shift(b,s) for j,b in enumerate(cols) if solver.value(xs[j]) for s in range(11)]
    C=np.zeros((22,len(bs)),np.int16)
    for j,b in enumerate(bs):C[list(b),j]=1
    assert C.shape==(22,77) and np.all(C.sum(0)==4) and np.all(C.sum(1)==14)
    assert np.array_equal(C@C.T,12*np.eye(22,dtype=int)+2)
    assert np.max(np.triu(C.T@C,1))<=2
    return 'verified design',C


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',type=int,default=1);p.add_argument('--seconds',type=int,default=45);a=p.parse_args()
    status,C=design(a.seed,a.seconds);print(a.seed,status,flush=True)
    if C is not None:np.save(tmp/('coclique-design-%d.npy'%a.seed),C)
