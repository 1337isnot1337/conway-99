"""Incidence arrays for eleven disjoint triangles, using free ternary development on their points."""
import argparse
from itertools import combinations
import numpy as np
from ortools.sat.python import cp_model
from triple_moments import tmp


def supports(seed):
    rng=np.random.default_rng(seed)
    difference=[0,2,6,7,8,10]
    # Select a six-subset whose eleven shifts form a (11,6,3) design.
    difference=next(z for z in combinations(range(11),6) if all(len(set(z)&{(i+d)%11 for i in z})==3 for d in range(1,11)))
    rows=[sorted((x+d)%11 for x in difference) for d in range(11)]
    perm=np.arange(11) if not seed else rng.permutation(11)
    return rows+[sorted(int(perm[x]) for x in b) for b in rows]


def solve(seed,seconds):
    B=supports(seed);model=cp_model.CpModel()
    phase={};diff={};table=[(i,j,(j-i)%3) for i in range(3) for j in range(3)]
    for r,points in enumerate(B):
        for x in points:phase[r,x]=model.new_int_var(0,2,'')
        model.add(phase[r,points[0]]==0)
        for x,y in combinations(points,2):
            d=model.new_int_var(0,2,'');diff[r,x,y]=d
            model.add_allowed_assignments([phase[r,x],phase[r,y],d],table)
    # Point and block phase offsets gauge away a spanning tree of incidence entries.
    seen={B[0][0]}
    for r,p in enumerate(B):
        if p[0] not in seen:continue
        for x in p:
            if x not in seen:model.add(phase[r,x]==0);seen.add(x)
    for x,y in combinations(range(11),2):
        ds=[d for (r,i,j),d in diff.items() if (i,j)==(x,y)]
        assert len(ds)==6
        for v in range(3):
            indicator=[]
            for d in ds:
                t=model.new_bool_var('');model.add(d==v).only_enforce_if(t);model.add(d!=v).only_enforce_if(~t);indicator.append(t)
            model.add(sum(indicator)==2)
    # For an intersection of at least three point groups, no phase class may occur three times.
    for i,j in combinations(range(22),2):
        points=sorted(set(B[i])&set(B[j]))
        if len(points)<3:continue
        col=[]
        for x in points:
            d=model.new_int_var(0,2,'');col.append(d);model.add_allowed_assignments([phase[i,x],phase[j,x],d],table)
        for v in range(3):
            bits=[]
            for d in col:
                t=model.new_bool_var('');model.add(d==v).only_enforce_if(t);model.add(d!=v).only_enforce_if(~t);bits.append(t)
            model.add(sum(bits)<=2)
    solver=cp_model.CpSolver();solver.parameters.num_workers=2;solver.parameters.random_seed=100+seed;solver.parameters.max_time_in_seconds=seconds
    status=solver.solve(model);print('support permutation',seed,solver.status_name(status),'branches',solver.num_branches,flush=True)
    if status in (cp_model.OPTIMAL,cp_model.FEASIBLE):
        N=np.zeros((33,66),np.int16);R=np.kron(np.eye(11,dtype=np.int16),np.ones((3,3),np.int16))-np.eye(33,dtype=np.int16)
        for r,p in enumerate(B):
            for x in p:
                for s in range(3):N[3*x+(solver.value(phase[r,x])+s)%3,3*r+s]=1
        assert np.array_equal(R@R+R+N@N.T,12*np.eye(33)+2) and np.max(np.triu(N.T@N,1))<=2
        np.savez_compressed(tmp/('triple-phase-%d.npz'%seed),B=R,N=N)


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--seed',default=0,type=int);p.add_argument('--seconds',default=60,type=int);a=p.parse_args();solve(a.seed,a.seconds)
