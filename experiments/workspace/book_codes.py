"""Generate exterior incidence designs for six grids sharing a triangle."""
import argparse
from itertools import combinations,permutations,product
from pathlib import Path
import numpy as np

from triangle_ball import local_ball
from triple_moments import tmp


def compose(a,b):return tuple(a[i] for i in b)


def icosahedral_action():
    ident=tuple(range(5));group=sorted(p for p in permutations(ident) if sum(p[i]>p[j] for i,j in combinations(ident,2))%2==0)
    cyclic=[tuple((i+k)%5 for i in ident) for k in ident]
    reverse=tuple((-i)%5 for i in ident)
    cosets={min(compose(g,h) for h in cyclic) for g in group}
    rep=lambda p:min(compose(p,h) for h in cyclic)
    axes=sorted({tuple(sorted((g,rep(compose(g,reverse))))) for g in cosets});points=sum((list(p) for p in axes),[])
    action=np.array([[points.index(rep(compose(g,h))) for h in points] for g in group],np.int16)
    assert action.shape==(60,12) and np.all(action[:,::2]^1==action[:,1::2])
    return action,group


def columns():
    # A signature is an increasing list of two signed entries in each of three arms.
    words=[]
    for a in combinations(range(6),2):
        rest=sorted(set(range(6))-set(a))
        for b in combinations(rest,2):
            c=sorted(set(rest)-set(b))
            pages=np.array([*a,*b,*c])
            for s in product(range(2),repeat=6):words.append(2*pages+s)
    return np.array(words,np.int16)


def orbits(words,action):
    key={tuple(w):i for i,w in enumerate(words)};seen=set();out=[]
    for idx,w in enumerate(words):
        if idx in seen:continue
        vals=action[:,w].reshape(-1,3,2);vals.sort(axis=2)
        orb=np.unique([key[tuple(v)] for v in vals.reshape(-1,6)])
        assert not seen.intersection(orb)
        seen.update(orb);out.append(orb)
    return out


def constraints(inc,B):
    # All columns have one symbol per grid, giving diagonal blocks automatically.
    target=12*np.eye(39,dtype=np.int16)+2-B-B@B
    a,b=np.triu_indices(39);use=target[a,b]>0
    assert np.all(target>=0)
    return a[use],b[use],target[a[use],b[use]]


def build(action):
    w=columns();K=np.arange(12)^1;B=local_ball(12,[K]*3,np.arange(12))
    I=np.zeros((len(w),39),np.int16)
    for j in range(6):I[np.arange(len(w)),3+12*(j//2)+w[:,j]]=1
    a,b,t=constraints(I,B);orbs=orbits(w,action);candidates=[];vectors=[]
    for orb in orbs:
        T=I[orb];M=T.T@T;v=M[a,b]
        if (v<=t).all() and np.max(np.triu(T@T.T,1),initial=0)<=2:
            candidates.append(orb);vectors.append(v)
    return B,I,candidates,np.array(vectors,np.int16).reshape(-1,len(t)),t


def group_of(kind):
    A,G=icosahedral_action();ident=tuple(range(5))
    if kind=='A5':return A
    if kind=='A4':return A[[g[0]==0 for g in G]]
    if kind=='D5':return A[[all((g[(i+1)%5]-g[i])%5 in [1,4] for i in range(5)) for g in G]]
    if kind=='D3':return A[[set(g[:2])=={0,1} for g in G]]
    if kind=='V4':return A[[g[0]==0 and compose(g,g)==ident for g in G]]
    if kind=='C5':return A[[all((g[(i+1)%5]-g[i])%5==1 for i in range(5)) for g in G]]
    if kind=='C3':return A[[g[0]==0 and g[1]==1 for g in G]]
    raise ValueError(kind)


def designs(kind,seconds,number):
    from ortools.sat.python import cp_model
    A=group_of(kind);B,I,orbs,M,t=build(A)
    print(kind,'group size',len(A),'eligible word orbits',len(orbs),'orbit sizes',np.unique([len(z) for z in orbs],return_counts=True),flush=True)
    if not orbs:return
    model=cp_model.CpModel();bits=[model.new_bool_var('') for _ in orbs]
    seen=set()
    for row,v in zip(M.T,t):
        key=row.tobytes(),v
        if key in seen:continue
        seen.add(key);idx=np.flatnonzero(row);model.add(sum(int(row[i])*bits[i] for i in idx)==int(v))
    solver=cp_model.CpSolver();solver.parameters.num_workers=2;solver.parameters.max_time_in_seconds=seconds
    found=cuts=0
    while found<number:
        status=solver.solve(model)
        if status not in (cp_model.OPTIMAL,cp_model.FEASIBLE):print(solver.status_name(status),'overlap cuts',cuts,'designs',found,flush=True);return
        selected=[i for i,p in enumerate(bits) if solver.value(p)]
        invalid=[]
        for i,j in combinations(selected,2):
            if (I[orbs[i]]@I[orbs[j]].T>2).any():invalid.append((i,j))
        if invalid:
            for i,j in invalid:model.add_bool_or([~bits[i],~bits[j]])
            cuts+=len(invalid);continue
        N=I[np.concatenate([orbs[i] for i in selected])].T.copy()
        assert N.shape==(39,60) and np.array_equal(B@B+B+N@N.T,12*np.eye(39,dtype=int)+2)
        np.savez_compressed(tmp/('book-%s-%d.npz'%(kind,found)),B=B,N=N)
        print('verified array',found,'cuts',cuts,flush=True);found+=1
        model.add_bool_or([~bits[i] for i in selected])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('group',nargs='?',default='A5');p.add_argument('--seconds',type=int,default=20);p.add_argument('--count',type=int,default=5);a=p.parse_args();designs(a.group,a.seconds,a.count)
